"""Shared harness for the view's read-only, outbound and coupling checks.

Every check in this directory's `test_*.py` guarantee files asserts an
*absence* over a whole run — no file changed, no write verb issued, no
bridge reached, no process left behind. That class of assertion passes for
free when the run it observes never happened, so the harness is built to
make the run real and the observation specific:

- a **recording transport** stands in for each sibling client at the
  process boundary, so what the run asked each one for is recorded rather
  than inferred;
- the transport lives inside a **simulated installed skills tree**, so a
  spawn can be resolved back to the skill directory it targets;
- the flow skill itself is the real one, reached through a symlink, so the
  composition under test is the shipped composition rather than a mock of
  it.

The helper module is named for its pack and skill, as the catalogue
authoring standards require of a shared test helper: a bare
`guarantees.py` would collide across packs on the prepended test path.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import os
import re
import subprocess
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = PACK_ROOT / ".apm" / "skills"
VIEW_SKILL = "jira-epic-outcome-view"
VIEW_SKILL_DIR = SKILLS_ROOT / VIEW_SKILL
VIEW_SCRIPTS_DIR = VIEW_SKILL_DIR / "scripts"
VIEW_MANIFEST = VIEW_SKILL_DIR / "manifest.json"
PACK_TOML = PACK_ROOT / "pack.toml"

#: The flow skill's per-issue cache directory, relative to the working
#: directory it is run from. Seeded before a read-only run because an empty
#: directory cannot tell a suppressed cache operation from an absent one.
CACHE_RELATIVE_DIR = Path(".context") / "flow-metrics" / "cache"

#: Older than the flow skill's own stale-temp threshold by a clear margin.
STALE_TMP_AGE_SECONDS = 2 * 60 * 60


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------
def declared_dependency_skills() -> set[str]:
    """The sibling skills `manifest.json` declares under `deps.skills`.

    Read as a declaration only. It is never the enumeration source for a
    traversal here: an undeclared invocation is exactly what a declaration
    fails to mention, so deriving the traversal from it would make every
    downstream check self-reported.
    """
    manifest = json.loads(VIEW_MANIFEST.read_text(encoding="utf-8"))
    return {entry["name"] for entry in manifest["deps"]["skills"]}


def declared_bridge_skills(pack_toml: Path = PACK_TOML) -> set[str]:
    """The skills the pack declares as bridges, from `[pack.metadata]`."""
    import tomllib

    with pack_toml.open("rb") as handle:
        manifest = tomllib.load(handle)
    return set(manifest["pack"]["metadata"].get("bridge-skills", []))


def sibling_skill_names(skills_root: Path = SKILLS_ROOT) -> set[str]:
    return {path.name for path in skills_root.iterdir() if path.is_dir()}


# ---------------------------------------------------------------------------
# Deriving the invocation set from the sources
# ---------------------------------------------------------------------------
def _python_sources(skill_dir: Path) -> Iterator[Path]:
    for path in sorted(skill_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _docstring_constant_ids(tree: ast.AST) -> set[int]:
    """Identify docstrings so prose cannot be read as an invocation.

    A docstring never executes, so a sibling's name inside one is a mention
    rather than a call. Everything else — including a name assembled into a
    path at module scope — stays in scope for the derivation.
    """
    ids: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        scopes = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        if not isinstance(node, scopes):
            continue
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            ids.add(id(body[0].value))
    return ids


def derive_invoked_siblings(
    skill_dir: Path, *, skills_root: Path | None = None
) -> set[str]:
    """The sibling skills this skill's executable sources address.

    Derived from the sources, never from a declaration. A skill is addressed
    by name — the harness resolves that name to an install location — so an
    invocation shows up as a string constant that is exactly a sibling skill
    directory name, or that name in its Python module spelling
    (`flow-metrics` as `flow_metrics`). Matching whole constants rather than
    substrings is what keeps `jira` out of `jira-epic-outcome-view`.

    This over-approximates in the safe direction: a name built in a
    non-docstring constant counts even if the call site is conditional. It
    cannot see a name assembled at run time from fragments, which is stated
    as a limit rather than papered over.
    """
    root = skills_root if skills_root is not None else skill_dir.parent
    names = sibling_skill_names(root)
    module_spelling = {name.replace("-", "_"): name for name in names}
    found: set[str] = set()
    for source in _python_sources(skill_dir):
        tree = ast.parse(source.read_text(encoding="utf-8", errors="ignore"))
        docstrings = _docstring_constant_ids(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            value = node.value.strip()
            resolved = value if value in names else module_spelling.get(value)
            if resolved and resolved != skill_dir.name:
                found.add(resolved)
    return found


def derive_referenced_siblings(
    skill_dir: Path, *, skills_root: Path | None = None
) -> set[str]:
    """Every sibling this skill's whole tree names, prose included.

    Used for the transitive hops away from the view, where the reachable
    skill may be a conversational one whose "invocation" is an instruction
    in `SKILL.md` rather than a call in a script. Over-approximating is the
    safe direction for an absence assertion: a hop this finds that is only a
    mention costs a false alarm, while a hop it misses costs the guarantee.

    `manifest.json` is excluded so the traversal never re-enters a
    declaration it exists to check.
    """
    root = skills_root if skills_root is not None else skill_dir.parent
    names = sorted(sibling_skill_names(root), key=len, reverse=True)
    found: set[str] = set()
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.name == "manifest.json":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name in names:
            if name == skill_dir.name:
                continue
            if re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", text):
                found.add(name)
    return found


def invocation_closure(
    start: str, *, skills_root: Path = SKILLS_ROOT
) -> dict[str, set[str]]:
    """Walk the invocation graph transitively from one skill.

    The first hop is derived from the starting skill's executable sources;
    every later hop uses the broader whole-tree derivation, because a skill
    further out may be conversational. Returns every visited skill mapped to
    what it reaches, so a caller can name the path that found a bridge.
    """
    edges: dict[str, set[str]] = {}
    pending = [start]
    while pending:
        current = pending.pop()
        if current in edges:
            continue
        skill_dir = skills_root / current
        if not skill_dir.is_dir():
            edges[current] = set()
            continue
        if current == start:
            reached = derive_invoked_siblings(skill_dir, skills_root=skills_root)
        else:
            reached = derive_referenced_siblings(skill_dir, skills_root=skills_root)
        edges[current] = reached
        pending.extend(sorted(reached))
    return edges


# ---------------------------------------------------------------------------
# Tree hashing
# ---------------------------------------------------------------------------
def hash_tree(root: Path) -> dict[str, str]:
    """Fingerprint every regular file under `root`, by relative path.

    Paths and contents both, so a deleted file, an added file and a rewritten
    file are each a different result. "Creates no new file" would pass a run
    that rewrote a cache entry or unlinked a stale temporary.

    The modification time is part of the fingerprint, which is stricter than
    byte-identity and deliberately so. A write that replaces a file with the
    same bytes is still a write, and content alone cannot see it — nor can it
    see a second run rewriting what a first run already left behind, which is
    how an ordering accident inside one test session can hide a real defect.
    """
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            digests[str(path.relative_to(root))] = "symlink:" + str(path.readlink())
            continue
        if not path.is_file():
            continue
        stat = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digests[str(path.relative_to(root))] = f"{digest}:{stat.st_size}:{stat.st_mtime_ns}"
    return digests


# ---------------------------------------------------------------------------
# The recording transport
# ---------------------------------------------------------------------------
RECORDER_SOURCE = '''#!/usr/bin/env python3
"""Recording transport standing in for a sibling client's CLI.

Records every invocation it receives -- the client it stands for and the
full argv -- then answers with the smallest payload that lets the run
continue. Recording at the process boundary is what makes "read methods
only" an observation rather than a claim: the caller cannot reach the
client without this file seeing the verb.

It also drives the credential-broker seam, so a write under the broker's
own root is attributed to the broker and not to the caller.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EPIC_DESCRIPTION = "## Outcome\\nCustomers resolve a return without contacting support.\\n"

ISSUES = [
    {
        "key": "PROJ-100",
        "fields": {
            "issuetype": {"name": "Epic"},
            "summary": "Self-serve returns",
            "created": "2026-08-01T09:00:00.000+0000",
            "status": {"name": "In Progress", "statusCategory": {"name": "In Progress"}},
            "statuscategorychangedate": "2026-09-01T09:00:00+00:00",
            "description": EPIC_DESCRIPTION,
        },
        "changelog": {"histories": []},
    },
    {
        "key": "PROJ-1",
        "fields": {
            "issuetype": {"name": "Story"},
            "summary": "Returns portal",
            "created": "2026-08-01T09:00:00.000+0000",
            "parent": {"key": "PROJ-100"},
            "status": {"name": "Done", "statusCategory": {"name": "Done"}},
            "statuscategorychangedate": "2026-09-02T09:00:00+00:00",
        },
        "changelog": {"histories": []},
    },
]


def _record(entry: dict) -> None:
    log = os.environ.get("ATLASSIAN_RECORDER_LOG")
    if not log:
        return
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\\n")


def _broker_resolve() -> None:
    """The credential broker's own write: an SSO session becomes a cookie jar.

    Every path it touches is recorded, so a write under the broker root that
    this seam did not make has no attribution and fails the check.
    """
    root = os.environ.get("ATLASSIAN_BROKER_ROOT")
    if not root:
        return
    jar = Path(root) / "sso" / "cookies.json"
    jar.parent.mkdir(parents=True, exist_ok=True)
    jar.write_text(json.dumps({"session": "refreshed-by-the-broker"}), encoding="utf-8")
    _record({"broker_write": str(jar.resolve())})


def main(argv: list[str]) -> int:
    client = os.environ.get("ATLASSIAN_RECORDER_CLIENT", "unknown")
    _record({"client": client, "argv": list(argv)})
    _broker_resolve()

    fmt = "json"
    output = None
    rest = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--format":
            fmt = argv[index + 1]
            index += 2
            continue
        if token == "--output":
            output = argv[index + 1]
            index += 2
            continue
        rest.append(token)
        index += 1

    verb = rest[0] if rest else ""
    if verb == "raw":
        path = rest[2] if len(rest) > 2 else ""
        payload = [] if path == "field" else {}
    elif verb == "search":
        payload = {"issues": ISSUES}
    elif verb == "whoami":
        payload = {"accountId": "recording-transport", "displayName": "Recording Transport"}
    elif verb == "get-issue":
        payload = dict(ISSUES[0])
    else:
        payload = {}

    if fmt == "jsonl":
        rows = payload.get("issues", []) if isinstance(payload, dict) else []
        text = "".join(json.dumps(row) + "\\n" for row in rows)
        if output in (None, "-"):
            sys.stdout.write(text)
        else:
            Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''


@dataclass
class RecordingTransport:
    """A simulated installed skills tree whose clients record what they see."""

    skills_root: Path
    log: Path
    jira_script: Path
    jira_align_script: Path
    flow_scripts: Path
    broker_root: Path | None = None

    def invocations(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def client_calls(self) -> list[dict[str, Any]]:
        return [entry for entry in self.invocations() if "client" in entry]

    def broker_writes(self) -> set[str]:
        return {entry["broker_write"] for entry in self.invocations() if "broker_write" in entry}


def build_recording_transport(tmp_path: Path) -> RecordingTransport:
    """Lay out a skills tree whose sibling clients are recorders.

    The flow skill is the real one, symlinked rather than copied: the
    composition under test has to be the shipped composition, and a copy
    would let the check pass against code the pack does not ship. Its
    siblings are recorders, so nothing reaches a real Jira instance and the
    checks stay offline and deterministic.
    """
    skills_root = tmp_path / "installed-skills"
    log = tmp_path / "transport.jsonl"

    jira_scripts = skills_root / "jira" / "scripts"
    jira_scripts.mkdir(parents=True)
    jira_script = jira_scripts / "jira.py"
    jira_script.write_text(RECORDER_SOURCE, encoding="utf-8")

    align_scripts = skills_root / "jira-align" / "scripts"
    align_scripts.mkdir(parents=True)
    align_script = align_scripts / "jira_align.py"
    align_script.write_text(RECORDER_SOURCE, encoding="utf-8")

    flow_dir = skills_root / "flow-metrics"
    flow_dir.mkdir(parents=True)
    flow_scripts = flow_dir / "scripts"
    flow_scripts.symlink_to(SKILLS_ROOT / "flow-metrics" / "scripts", target_is_directory=True)

    return RecordingTransport(
        skills_root=skills_root,
        log=log,
        jira_script=jira_script,
        jira_align_script=align_script,
        flow_scripts=flow_scripts,
    )


# ---------------------------------------------------------------------------
# Spawn recording
# ---------------------------------------------------------------------------
@dataclass
class Spawn:
    """One subprocess started by the view's own code, and its handle."""

    argv: list[str]
    kwargs: dict[str, Any]
    process: subprocess.Popen

    @property
    def reaped(self) -> bool:
        """True once the child has been waited on and its status collected."""
        return self.process.returncode is not None

    @property
    def detached(self) -> bool:
        return bool(self.kwargs.get("start_new_session")) or bool(
            self.kwargs.get("creationflags")
        )


@dataclass
class SpawnLog:
    spawns: list[Spawn] = field(default_factory=list)


@contextlib.contextmanager
def recording_spawns(monkeypatch) -> Iterator[SpawnLog]:
    """Record every subprocess started *in this process* during the block.

    `subprocess.run` builds its child through the module-global `Popen`, so
    replacing that name observes the real spawn rather than a stand-in for
    it: the child really starts, really runs, and is really waited on by the
    code under test. Only spawns the view's own code makes are visible here
    — one a sibling makes happens in the sibling's own process, which is the
    limit AC56 records rather than hides.
    """
    log = SpawnLog()
    real_popen = subprocess.Popen

    class RecordingPopen(real_popen):
        def __init__(self, args, **kwargs):
            super().__init__(args, **kwargs)
            log.spawns.append(
                Spawn(
                    argv=[str(part) for part in args],
                    kwargs=dict(kwargs),
                    process=self,
                )
            )

    monkeypatch.setattr(subprocess, "Popen", RecordingPopen)
    yield log


def spawn_target_skill(spawn: Spawn, permitted: Iterable[str]) -> str | None:
    """Which declared sibling skill directory this spawn's target resolves in.

    Two packaging shapes reach a skill, and both are the shipped shape for a
    skill in this pack, so both are resolved rather than one being treated as
    the only legitimate form:

    - a script path in the argv (`python .../jira/scripts/jira.py search`);
    - `-m <package>` with the package's directory on the child's PYTHONPATH
      (`python -m flow_metrics`, PYTHONPATH `.../flow-metrics/scripts`),
      which is how a skill shipping a package rather than a single file is
      run without losing its package context.

    Returns the permitted skill name the target sits under, or `None` when
    the spawn targets something outside every permitted skill — which is the
    answer a leaked or unrelated process gives.
    """
    permitted = set(permitted)
    candidates: list[Path] = []
    argv = spawn.argv
    for index, token in enumerate(argv):
        if token == "-m" and index + 1 < len(argv):
            env = spawn.kwargs.get("env") or {}
            for entry in (env.get("PYTHONPATH") or "").split(os.pathsep):
                if entry:
                    candidates.append(Path(entry))
            continue
        if token.startswith("-"):
            continue
        candidates.append(Path(token))

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:  # pragma: no cover - defensive
            continue
        for part in (resolved, *resolved.parents):
            if part.name in permitted:
                return part.name
    return None


# ---------------------------------------------------------------------------
# Cache seeding
# ---------------------------------------------------------------------------
def seed_flow_cache(working_dir: Path) -> dict[str, Path]:
    """Populate the flow skill's cwd-relative cache, stale temporary included.

    The stale temporary is the discriminating seed. The flow skill's plain
    bypass flag unlinks a `*.tmp` older than an hour from an existing cache
    directory before the flag's own branch is reached, and deleting a file is
    a write — so a run composed through that flag changes this tree while
    creating nothing.
    """
    cache_dir = working_dir / CACHE_RELATIVE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    entry = cache_dir / "9f86d081.jsonl"
    entry.write_text('{"key": "PROJ-1"}\n', encoding="utf-8")
    stale = cache_dir / "9f86d081.jsonl.4242.tmp"
    stale.write_text("{}\n", encoding="utf-8")
    old = time.time() - STALE_TMP_AGE_SECONDS
    os.utime(stale, (old, old))
    return {"cache_dir": cache_dir, "entry": entry, "stale_tmp": stale}


# ---------------------------------------------------------------------------
# Running the view
# ---------------------------------------------------------------------------
def view_environment(
    transport: RecordingTransport, *, broker_root: Path | None = None
) -> dict[str, str]:
    """The environment that points the view at the recording transport."""
    env = {
        "JIRA_EPIC_OUTCOME_VIEW_JIRA_SCRIPT": str(transport.jira_script),
        "JIRA_EPIC_OUTCOME_VIEW_FLOW_METRICS_SCRIPTS": str(transport.flow_scripts),
        "FLOW_METRICS_JIRA_SCRIPT": str(transport.jira_script),
        "FLOW_METRICS_JIRAALIGN_SCRIPT": str(transport.jira_align_script),
        "ATLASSIAN_RECORDER_LOG": str(transport.log),
        "ATLASSIAN_RECORDER_CLIENT": "jira",
    }
    if broker_root is not None:
        env["ATLASSIAN_BROKER_ROOT"] = str(broker_root)
    return env


VIEW_ARGV = ["--project", "PROJ", "--from", "2026-08-25", "--to", "2026-09-24"]


def apply_environment(monkeypatch, env: dict[str, str]) -> None:
    for name, value in env.items():
        monkeypatch.setenv(name, value)


def assert_answer_is_correct_and_non_empty(document: dict[str, Any]) -> None:
    """The run returned an answer, not merely an exit code.

    Every artifact-free and read-only check runs this: a view that returned
    an empty document would satisfy every absence assertion here trivially,
    so the answer is asserted before anything about what the run did not do.
    """
    assert document["project"] == "PROJ"
    assert document["epics"], "the run produced no Epic rows, so it answered nothing"
    epic = document["epics"][0]
    assert epic["epic"] == "PROJ-100"
    assert epic["outcome"]["recorded"] is True
    assert "Customers resolve a return without contacting support." in epic["outcome"]["text"]
    assert document["coverage"].strip()


def parse_stdout_document(captured: str) -> dict[str, Any]:
    return json.loads(captured)


def python_source_text(skill_dir: Path) -> dict[Path, str]:
    """Every executable source of one skill, by path."""
    return {
        path: path.read_text(encoding="utf-8")
        for path in _python_sources(skill_dir)
    }


def shipped_source_text(skill_dir: Path) -> dict[Path, str]:
    """Every shipped file of one skill, by path, scripts and prose alike."""
    texts: dict[Path, str] = {}
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return texts


__all__ = [
    "CACHE_RELATIVE_DIR",
    "PACK_ROOT",
    "RecordingTransport",
    "SKILLS_ROOT",
    "Spawn",
    "VIEW_ARGV",
    "VIEW_MANIFEST",
    "VIEW_SCRIPTS_DIR",
    "VIEW_SKILL",
    "VIEW_SKILL_DIR",
    "apply_environment",
    "assert_answer_is_correct_and_non_empty",
    "build_recording_transport",
    "declared_bridge_skills",
    "declared_dependency_skills",
    "derive_invoked_siblings",
    "derive_referenced_siblings",
    "hash_tree",
    "invocation_closure",
    "parse_stdout_document",
    "python_source_text",
    "recording_spawns",
    "seed_flow_cache",
    "shipped_source_text",
    "sibling_skill_names",
    "spawn_target_skill",
    "view_environment",
]

# ---------------------------------------------------------------------------
# Denying an adopter repository, and watching where a run reads
# ---------------------------------------------------------------------------
#: Written into a directory the run puts on its child interpreters' import
#: path. CPython imports `sitecustomize` at start-up when it finds one, so a
#: denial installed here reaches every process the run starts, not only the
#: one the check is executing in. A run is every process it starts.
DENIAL_GUARD_SOURCE = '''"""Refuse reads under a denied root, and watch where reads go.

Two jobs, because the criteria ask two different questions.

*Denial* refuses any path under a denied root, records the attempt and
raises. That is how "with every adopter-repository path denied" is made a
fact about the run rather than a description of the fixture.

*Watching* records any path opened outside an allowed set without refusing
it. Naming three absent artifacts would let a hidden dependency pass; a
record of everywhere a run actually read cannot, because a repository file
anywhere would be in it.
"""
from __future__ import annotations

import builtins
import io
import os

_ORIGINALS: dict = {}
_STATE: dict = {}


def _under(path: str, roots) -> bool:
    return any(path == root or path.startswith(root + os.sep) for root in roots)


def _resolve(path) -> str | None:
    try:
        return os.path.realpath(os.fspath(path))
    except (TypeError, ValueError, OSError):
        return None


def _append(log: str | None, line: str) -> None:
    if not log:
        return
    try:
        with _ORIGINALS["open"](log, "a", encoding="utf-8") as handle:
            handle.write(line + "\\n")
    except OSError:
        pass


def _inspect(path) -> None:
    resolved = _resolve(path)
    if resolved is None:
        return
    if _under(resolved, _STATE["deny"]):
        _append(_STATE["deny_log"], resolved)
        raise PermissionError(f"denied repository path: {resolved}")
    allow = _STATE["allow"]
    if allow and not _under(resolved, allow):
        _append(_STATE["stray_log"], resolved)


def install(*, deny=(), allow=(), deny_log=None, stray_log=None) -> None:
    """Wrap the read entry points. Idempotent, and undone by `uninstall`."""
    if _ORIGINALS:
        return
    _STATE.update(
        deny=[os.path.realpath(entry) for entry in deny],
        allow=[os.path.realpath(entry) for entry in allow],
        deny_log=deny_log,
        stray_log=stray_log,
    )
    _ORIGINALS["open"] = builtins.open
    _ORIGINALS["io_open"] = io.open
    _ORIGINALS["os_open"] = os.open

    def guarded_open(file, *args, **kwargs):
        _inspect(file)
        return _ORIGINALS["open"](file, *args, **kwargs)

    def guarded_os_open(path, *args, **kwargs):
        _inspect(path)
        return _ORIGINALS["os_open"](path, *args, **kwargs)

    builtins.open = guarded_open
    io.open = guarded_open
    os.open = guarded_os_open


def install_from_environment() -> None:
    """The child-process entry point: denial only, never watching.

    A child is watched by nothing here on purpose. Its interpreter start-up
    reads its own installation, which says nothing about the view.
    """
    deny = [
        entry
        for entry in (os.environ.get("ATLASSIAN_DENY_ROOTS") or "").split(os.pathsep)
        if entry
    ]
    if deny:
        install(deny=deny, deny_log=os.environ.get("ATLASSIAN_DENY_LOG"))


def uninstall() -> None:
    if not _ORIGINALS:
        return
    builtins.open = _ORIGINALS["open"]
    io.open = _ORIGINALS["io_open"]
    os.open = _ORIGINALS["os_open"]
    _ORIGINALS.clear()
    _STATE.clear()
'''

SITECUSTOMIZE_SOURCE = '''"""Carry the denial into every child interpreter the run starts."""
import atlassian_repo_denial

atlassian_repo_denial.install_from_environment()
'''


@dataclass
class DenialGuard:
    """The guard's files, its environment, and the logs it writes."""

    module: Path
    guard_dir: Path
    deny_log: Path
    stray_log: Path
    env: dict[str, str]

    def denied_attempts(self) -> list[str]:
        return _read_log(self.deny_log)

    def reads_outside_the_allowed_set(self) -> list[str]:
        return _read_log(self.stray_log)


def _read_log(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(set(path.read_text(encoding="utf-8").split()))


def build_denial_guard(tmp_path: Path, *, deny: Iterable[Path]) -> DenialGuard:
    """Write the guard and hand back what a run needs to install it."""
    guard_dir = tmp_path / "denial-guard"
    guard_dir.mkdir(exist_ok=True)
    module = guard_dir / "atlassian_repo_denial.py"
    module.write_text(DENIAL_GUARD_SOURCE, encoding="utf-8")
    (guard_dir / "sitecustomize.py").write_text(SITECUSTOMIZE_SOURCE, encoding="utf-8")
    deny_log = tmp_path / "denied-reads.log"
    stray_log = tmp_path / "reads-outside-the-allowed-set.log"
    return DenialGuard(
        module=module,
        guard_dir=guard_dir,
        deny_log=deny_log,
        stray_log=stray_log,
        env={
            "ATLASSIAN_DENY_ROOTS": os.pathsep.join(
                str(Path(entry).resolve()) for entry in deny
            ),
            "ATLASSIAN_DENY_LOG": str(deny_log),
            "PYTHONPATH": str(guard_dir),
        },
    )


def load_denial_guard(guard: DenialGuard):
    """Load the guard in this process, under a pack-and-skill-qualified name."""
    import importlib.util

    name = "atlassian_jira_epic_outcome_view_repo_denial"
    spec = importlib.util.spec_from_file_location(name, guard.module)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_adopter_repository(root: Path) -> Path:
    """A stand-in for the repository an adopter runs the view inside.

    Carries the artifacts a coupled skill would reach for, so denying this
    tree denies the dependency rather than a directory that happens to be
    empty.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").mkdir(exist_ok=True)
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# the adopter's own agent context\n", encoding="utf-8")
    (root / "workspace.toml").write_text('[workspace]\nname = "an adopter"\n', encoding="utf-8")
    product = root / "docs" / "product"
    product.mkdir(parents=True, exist_ok=True)
    (product / "changelog.md").write_text("# Changelog\n", encoding="utf-8")
    intents = root / "docs" / "product" / "intents"
    intents.mkdir(parents=True, exist_ok=True)
    (intents / "an-intent.md").write_text("# An intent\n", encoding="utf-8")
    return root
