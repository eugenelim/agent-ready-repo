"""Upstream skill wrappers — discovery, allowlist, subprocess.

T3 substrate: every downstream task reads Jira / Jira Align data through
this module. The wrapper enforces the read-only allowlist from
docs/specs/flow-metrics.md § "Read-only contract — upstream-skill
allowlist" — verbs and ``raw GET`` paths are validated against exact
regex patterns before any subprocess is spawned.

Architectural invariants (load-bearing; do not relax):

- Only ``subprocess.run`` (non-streaming) and ``subprocess.Popen``
  (streaming ``search`` only) — both list-form, never ``shell=True``.
- The wrapper never reads ``~/.agentbundle/credentials.env``;
  credentials live with the upstream skill's process.
- Subprocess env is ``os.environ.copy()`` (inherited unfiltered) so the
  upstream skill can find ``JIRA_*`` / ``JIRA_ALIGN_*`` credentials.
- Upstream stderr is forwarded to this skill's stderr regardless of
  exit code (diagnostic notes reach the user even on success).

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator, List, Mapping, Optional, Tuple


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class AllowlistError(Exception):
    """Caller asked for a verb / path the read-only allowlist forbids.

    Mapped to exit 2 (validation) by ``main``; the offending call never
    reaches the upstream subprocess.
    """


class JiraError(Exception):
    """Upstream ``jira`` / ``jira-align`` subprocess returned non-zero.

    Carries the raw return code and stderr payload so ``main`` can map
    to exit 3 (upstream-skill error) and relay the stderr verbatim.
    """

    def __init__(self, returncode: int, stderr: bytes, *, argv: Optional[List[str]] = None) -> None:
        self.returncode = returncode
        self.stderr = stderr or b""
        self.argv = list(argv) if argv is not None else []
        msg = "upstream returned exit {}".format(returncode)
        if self.stderr:
            msg += ": " + self.stderr.decode("utf-8", errors="replace").strip()
        super().__init__(msg)


class UpstreamNotFoundError(Exception):
    """Discovery probe found no candidate for the named upstream skill.

    Mapped to exit 2 by ``main``; carries the candidate paths so the
    error message can name each one tried.
    """

    def __init__(self, name: str, tried: List[Path]) -> None:
        self.name = name
        self.tried = list(tried)
        msg = (
            "upstream skill {name!r} not found. "
            "Install the {name} skill from the atlassian pack. "
            "Discovery searched: {tried}."
        ).format(name=name, tried=", ".join(str(p) for p in tried))
        super().__init__(msg)


# Map exception classes to CLI exit codes. Used by ``flow_metrics.main``
# to translate wrapper-boundary failures into the spec's exit-code
# discipline (2 = validation / refusal, 3 = upstream-skill failure).
EXIT_VALIDATION = 2
EXIT_UPSTREAM = 3


def exit_code_for(exc: BaseException) -> int:
    if isinstance(exc, JiraError):
        return EXIT_UPSTREAM
    if isinstance(exc, (AllowlistError, UpstreamNotFoundError)):
        return EXIT_VALIDATION
    raise TypeError("exit_code_for: unsupported exception type {}".format(type(exc).__name__))


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
# This file lives at <skill-root>/scripts/flow_metrics/upstream.py, so the
# skill root is two parents up.
_THIS_SKILL_DIR = Path(__file__).resolve().parent.parent.parent


def _env_var_name(name: str) -> str:
    """Per spec/plan: FLOW_METRICS_<NAME>_SCRIPT with hyphens stripped.

    Matches the literals in docs/specs/flow-metrics-plan.md
    (``FLOW_METRICS_JIRA_SCRIPT`` / ``FLOW_METRICS_JIRAALIGN_SCRIPT``).
    """
    return "FLOW_METRICS_{}_SCRIPT".format(name.upper().replace("-", ""))


def _module_name_for_script(name: str) -> str:
    """``jira-align`` ships as ``scripts/jira_align.py`` (Python module-name
    convention); ``jira`` ships as ``scripts/jira.py``. Replace hyphens
    with underscores.
    """
    return name.replace("-", "_")


_USER_SCOPE_CAPABLE_ADAPTER_DIRS: Tuple[str, ...] = (".claude", ".kiro", ".agents")


def discover_skill_path(name: str, *, env: Optional[Mapping[str, str]] = None, cwd: Optional[Path] = None) -> Path:
    """Locate the upstream skill's CLI entry script.

    Probe order:

    1. ``$FLOW_METRICS_<NAME>_SCRIPT`` env var (testing override).
    2. ``<this-skill-dir>/../<name>/scripts/<name>.py`` (sibling layout —
       covers same-adapter user-scope installs *and* in-pack development).
    3. ``~/<adapter-dir>/skills/<name>/scripts/<name>.py`` (user scope),
       walked across every user-scope-capable adapter directory:
       ``.claude`` (claude-code), ``.kiro`` (kiro), ``.agents`` (codex —
       per Codex's upstream skills documentation, skills land under the
       shared ``$HOME/.agents/skills/`` not under ``~/.codex/``).
    4. ``<cwd>/<adapter-dir>/skills/<name>/scripts/<name>.py`` (project
       scope), same three adapter directories.

    First hit wins. None match → :class:`UpstreamNotFoundError` naming
    every candidate.

    **Multi-root precedence.** When the same upstream skill is installed
    under more than one adapter root (e.g. both ``~/.claude/skills/jira/``
    and ``~/.kiro/skills/jira/``), priority 3's declared order is
    ``claude → kiro → codex`` — claude wins by default. Adopters who
    want a specific adapter set the priority-1 env override
    ``FLOW_METRICS_<NAME>_SCRIPT`` to the exact script path; that's the
    documented runtime escape valve. The install-time analogue lives in
    ``agentbundle install --scope user --adapter <name>``.
    """
    e = env if env is not None else os.environ
    base_cwd = cwd if cwd is not None else Path.cwd()
    script = "{}.py".format(_module_name_for_script(name))

    candidates: List[Tuple[str, Path]] = []

    # 1. Env override appended as a candidate. The `is_file()` check
    #    below means a typo'd override falls through to the next
    #    candidate rather than silently failing later.
    env_value = e.get(_env_var_name(name))
    if env_value:
        candidates.append(("env:" + _env_var_name(name), Path(env_value)))

    # 2. Sibling layout under this skill's parent dir. This already
    #    handles the common case where flow-metrics and its upstream
    #    sibling skill are co-installed under the same adapter root
    #    (the sibling walk lands one level above flow-metrics' own dir,
    #    so it works for any adapter the install put us under).
    candidates.append(("sibling", _THIS_SKILL_DIR.parent / name / "scripts" / script))

    # 3. User scope — walked across all three user-scope-capable adapter
    #    directories. Order is claude/kiro/codex, matching the probe
    #    order in `_resolve_user_scope_target_adapter`.
    for adapter_dir in _USER_SCOPE_CAPABLE_ADAPTER_DIRS:
        candidates.append(
            ("user:" + adapter_dir, Path.home() / adapter_dir / "skills" / name / "scripts" / script)
        )

    # 4. Project scope — same three adapter directories.
    for adapter_dir in _USER_SCOPE_CAPABLE_ADAPTER_DIRS:
        candidates.append(
            ("project:" + adapter_dir, base_cwd / adapter_dir / "skills" / name / "scripts" / script)
        )

    for _kind, path in candidates:
        if path.is_file():
            return path

    raise UpstreamNotFoundError(name, [p for _, p in candidates])


# ---------------------------------------------------------------------------
# Subprocess plumbing (shared by both clients)
# ---------------------------------------------------------------------------
def _decode_stderr(b: bytes) -> str:
    return b.decode("utf-8", errors="replace") if b else ""


def _forward_stderr(b: bytes) -> None:
    if b:
        sys.stderr.write(_decode_stderr(b))
        sys.stderr.flush()


def _run_capture(argv: List[str]) -> Tuple[int, bytes, bytes]:
    """Run argv to completion, capture stdout+stderr. List-form only.

    No ``shell=True``; ``env`` is the full inherited ``os.environ`` per
    spec (the upstream skill needs ``JIRA_*`` / ``HOME`` etc. unfiltered).
    """
    result = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        env=os.environ.copy(),
    )
    return result.returncode, result.stdout or b"", result.stderr or b""


def _parse_json_or_none(payload: bytes) -> Any:
    if not payload:
        return None
    text = payload.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    return json.loads(text)


# ---------------------------------------------------------------------------
# Jira client
# ---------------------------------------------------------------------------
class JiraClient:
    """Wrapper around the ``jira`` skill's CLI, enforcing the allowlist.

    Public verbs match the spec exactly:
    ``check``, ``whoami``, ``get-issue``, ``search``, ``get-project``,
    ``raw`` (GET only, with a strict path allowlist).
    """

    _ALLOWED_VERBS: frozenset = frozenset(
        {"check", "whoami", "get-issue", "search", "get-project", "raw"}
    )

    # Exact regex patterns; not prefixes. ``project/PROJ/components`` is
    # rejected even though it starts with ``project/``.
    _ALLOWED_RAW_PATTERNS: Tuple[re.Pattern, ...] = (
        re.compile(r"^field$"),
        re.compile(r"^project/[A-Z][A-Z0-9_]+/statuses$"),
        re.compile(r"^issue/[A-Z][A-Z0-9_]+-[0-9]+/changelog$"),
    )

    def __init__(self, script_path: Path) -> None:
        self._script = Path(script_path)

    # ------------------------------------------------------------------
    # Public verb methods (one per allowlisted verb)
    # ------------------------------------------------------------------
    def check(self) -> Any:
        return self._invoke(["check"])

    def whoami(self) -> Any:
        return self._invoke(["whoami"])

    def get_issue(self, key: str, fields: Optional[str] = None, expand: Optional[str] = None) -> Any:
        sub = ["get-issue", key]
        if fields is not None:
            sub += ["--fields", fields]
        if expand is not None:
            sub += ["--expand", expand]
        return self._invoke(sub)

    def get_project(self, key: str) -> Any:
        return self._invoke(["get-project", key])

    def raw_get(self, path: str, params: Optional[Mapping[str, str]] = None) -> Any:
        self._validate_raw_get(path)
        sub = ["raw", "GET", path]
        for k, v in (params or {}).items():
            sub += ["--param", "{}={}".format(k, v)]
        return self._invoke(sub)

    def search(
        self,
        jql: str,
        fields: Optional[str] = None,
        expand: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Iterator[dict]:
        """Stream ``jira: search`` rows one at a time via ``Popen``.

        Returns a generator. ``subprocess.run(capture_output=True)``
        would buffer all rows in memory before returning, defeating the
        bounded-memory streaming contract; this path always uses
        ``Popen`` with ``--format jsonl --output -``.
        """
        sub = ["search", jql]
        if fields is not None:
            sub += ["--fields", fields]
        if expand is not None:
            sub += ["--expand", expand]
        if page_size is not None:
            sub += ["--page-size", str(page_size)]
        return self._stream(sub)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _validate_verb(self, verb: str) -> None:
        if verb not in self._ALLOWED_VERBS:
            raise AllowlistError(
                "jira verb {!r} is not in the read-only allowlist".format(verb)
            )

    def _validate_raw_get(self, path: str) -> None:
        for pat in self._ALLOWED_RAW_PATTERNS:
            if pat.match(path):
                return
        raise AllowlistError(
            "jira raw GET path {!r} is not in the read-only allowlist".format(path)
        )

    def _argv(self, sub_argv: List[str], *, fmt: str = "json", output: Optional[str] = None) -> List[str]:
        # jira.py expects ``--format`` and ``--output`` as global flags
        # BEFORE the subcommand, per its argparse layout.
        argv = [sys.executable, str(self._script), "--format", fmt]
        if output is not None:
            argv += ["--output", output]
        argv += sub_argv
        return argv

    def _invoke(self, sub_argv: List[str]) -> Any:
        verb = sub_argv[0]
        self._validate_verb(verb)
        argv = self._argv(sub_argv, fmt="json")
        rc, stdout, stderr = _run_capture(argv)
        _forward_stderr(stderr)
        if rc != 0:
            raise JiraError(rc, stderr, argv=argv)
        return _parse_json_or_none(stdout)

    def _stream(self, sub_argv: List[str]) -> Iterator[dict]:
        verb = sub_argv[0]
        self._validate_verb(verb)
        argv = self._argv(sub_argv, fmt="jsonl", output="-")
        return _popen_stream(argv)


# ---------------------------------------------------------------------------
# Jira Align client
# ---------------------------------------------------------------------------
class JiraAlignClient:
    """Wrapper around the ``jira-align`` skill's CLI. Allowlist: ``raw GET``
    on four exact nested-resource patterns only.
    """

    _ALLOWED_VERBS: frozenset = frozenset({"raw"})

    _ALLOWED_RAW_PATTERNS: Tuple[re.Pattern, ...] = (
        re.compile(r"^programs/[0-9]+$"),
        re.compile(r"^programs/[0-9]+/teams$"),
        re.compile(r"^portfolios/[0-9]+$"),
        re.compile(r"^portfolios/[0-9]+/programs$"),
    )

    def __init__(self, script_path: Path) -> None:
        self._script = Path(script_path)

    def raw_get(self, path: str, params: Optional[Mapping[str, str]] = None) -> Any:
        self._validate_raw_get(path)
        sub = ["raw", "GET", path]
        for k, v in (params or {}).items():
            sub += ["--param", "{}={}".format(k, v)]
        return self._invoke(sub)

    def _validate_verb(self, verb: str) -> None:
        if verb not in self._ALLOWED_VERBS:
            raise AllowlistError(
                "jira-align verb {!r} is not in the read-only allowlist".format(verb)
            )

    def _validate_raw_get(self, path: str) -> None:
        for pat in self._ALLOWED_RAW_PATTERNS:
            if pat.match(path):
                return
        raise AllowlistError(
            "jira-align raw GET path {!r} is not in the read-only allowlist".format(path)
        )

    def _argv(self, sub_argv: List[str]) -> List[str]:
        return [sys.executable, str(self._script), "--format", "json"] + sub_argv

    def _invoke(self, sub_argv: List[str]) -> Any:
        verb = sub_argv[0]
        self._validate_verb(verb)
        argv = self._argv(sub_argv)
        rc, stdout, stderr = _run_capture(argv)
        _forward_stderr(stderr)
        if rc != 0:
            raise JiraError(rc, stderr, argv=argv)
        return _parse_json_or_none(stdout)


# ---------------------------------------------------------------------------
# Streaming helper (top-level so the search() generator below it remains
# a single function call rather than nesting Popen inside the generator).
# ---------------------------------------------------------------------------
def _popen_stream(argv: List[str]) -> Iterator[dict]:
    """Spawn ``argv`` and yield one JSON dict per line of stdout.

    Stderr is captured to a temporary file rather than a pipe to avoid
    the classic ``stderr=PIPE`` deadlock: a verbose upstream subprocess
    can fill the OS pipe buffer (typically 16-64 KiB) and block on its
    next stderr write, in turn deadlocking ``proc.wait()`` in this
    process. The tempfile is bounded only by disk, so the upstream can
    emit arbitrary diagnostic output without back-pressuring us.

    On EOF, waits for the subprocess. Non-zero exit raises
    :class:`JiraError` with the drained stderr. Stderr is always
    forwarded to this process's stderr regardless of exit code so that
    permission-undercount and similar diagnostic notes reach the user.
    """
    stderr_file = tempfile.TemporaryFile()
    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            env=os.environ.copy(),
        )
    except BaseException:
        stderr_file.close()
        raise

    try:
        if proc.stdout is not None:
            for raw_line in proc.stdout:
                # Line-delimited JSON; skip blank / whitespace-only
                # lines rather than letting ``json.loads("")`` error.
                line = raw_line.strip()
                if not line:
                    continue
                if isinstance(line, bytes):
                    text = line.decode("utf-8", errors="replace")
                else:
                    text = line
                yield json.loads(text)
    finally:
        # Close stdout BEFORE wait() so an upstream still trying to
        # emit rows after the consumer aborted gets SIGPIPE / EPIPE
        # and exits, instead of blocking our wait() forever.
        if proc.stdout is not None:
            try:
                proc.stdout.close()
            except Exception:
                pass

        # wait() should never raise on POSIX; on Windows it can if the
        # handle is invalid. Capture and re-raise after we've drained
        # stderr so the tempfile doesn't leak.
        wait_error: Optional[BaseException] = None
        try:
            proc.wait()
        except BaseException as exc:
            wait_error = exc

        try:
            stderr_file.seek(0)
            stderr = stderr_file.read() or b""
        except Exception:
            stderr = b""
        try:
            stderr_file.close()
        except Exception:
            pass

        _forward_stderr(stderr)

        if wait_error is not None:
            raise wait_error
        if proc.returncode is not None and proc.returncode != 0:
            raise JiraError(proc.returncode, stderr, argv=argv)


__all__ = [
    "AllowlistError",
    "JiraError",
    "UpstreamNotFoundError",
    "JiraClient",
    "JiraAlignClient",
    "discover_skill_path",
    "exit_code_for",
]
