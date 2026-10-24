"""_supervisor_git — the one hardened Git helper every supervisor ``git`` call uses.

A call passes the pinned Git and work-tree directories as arguments, runs with
system and global config switched off and every ``GIT_*`` variable cleared but
the private index, and carries only the line-ending and ``core.excludesFile``
settings read once from the effective config. It turns off hooks, fsmonitor,
external diff, textconv, replace refs, signing, and every filter the
repository's own config defines, so no configured program runs.

Before each call it checks Git control state by direct file reads: the work
tree's ``.git`` entry and ``commondir`` must still resolve to the directories
pinned on first use, and no ``info/grafts`` file may exist. ``control_check`` is
the seam for the stronger comparison against an open attempt's manifest.

Two config reads run outside the helper, and no other ``git`` call may: the
read of the effective config (the carried settings, the filter definitions, and
the code-running keys admission refuses) and the read of ``user.name`` and
``user.email`` for the commit identity. Each passes the pinned ``--git-dir``,
runs no configured code, and sees the user's own global and system config.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import atexit
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ConfigEntry",
    "HardenedGit",
    "Pins",
    "SupervisorGitError",
    "attribute_filters",
    "code_running_keys",
    "defined_filters",
    "discover",
]

GIT_TIMEOUT_S = 60.0
_MAX_SMALL_FILE_BYTES = 4096
_MAX_ATTRIBUTES_BYTES = 8 * 1024 * 1024
_FILTER_NAME_RE = re.compile(r"[A-Za-z0-9_.-]+")
_BOOLEANS = frozenset({"true", "false", "yes", "no", "on", "off", "0", "1", ""})

# The variables a Git child inherits; everything else, ``GIT_*`` included, is dropped.
_INHERITED_ENV = ("PATH", "HOME", "LANG", "TMPDIR")
_INHERITED_ENV_WINDOWS = ("SYSTEMROOT", "TEMP", "TMP", "PATHEXT", "COMSPEC")
# Where the user's own config lives; only the two config reads below pass them on.
_CONFIG_LOCATION_ENV = (
    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM", "XDG_CONFIG_HOME",
)
_CONFIG_LOCATION_ENV_WINDOWS = ("USERPROFILE", "HOMEDRIVE", "HOMEPATH")

_DIFFING = frozenset({"diff", "log", "show", "diff-tree", "diff-index", "diff-files"})
_FILTER_SETTINGS = ("clean", "smudge", "process")
_CODE_RUNNING_FIXED = frozenset({
    "diff.external",
    "core.sshcommand",
    "core.fsmonitor",
    "core.hookspath",
    "gpg.program",
    "gpg.ssh.defaultkeycommand",
    "include.path",
})


class SupervisorGitError(Exception):
    """A Git operation failed or Git state is not what the supervisor pinned.

    *unverifiable* marks a refusal whose check could not be made at all, as
    opposed to one that ran and found a forbidden state; only the former is
    written to the security-event log.
    """

    def __init__(self, code: str, message: str = "", *, unverifiable: bool = False) -> None:
        super().__init__(message or code)
        self.code = code
        self.unverifiable = unverifiable


@dataclass(frozen=True)
class Pins:
    """The directories one run's Git calls are pinned to."""

    root: Path
    git_dir: Path
    common_dir: Path


@dataclass(frozen=True)
class ConfigEntry:
    """One effective config line: the scope that supplied it, its key, and its value."""

    scope: str
    key: str
    value: str


# ── environment and flags ───────────────────────────────────────────────────

_EMPTY_HOOKS: list[str] = []


def _empty_hooks_dir() -> str:
    """An empty directory, made once per process, that stands in for the hooks path."""
    if not _EMPTY_HOOKS:
        directory = tempfile.mkdtemp(prefix="work-supervisor-nohooks-")
        atexit.register(shutil.rmtree, directory, ignore_errors=True)
        _EMPTY_HOOKS.append(directory)
    return _EMPTY_HOOKS[0]


def _inherited_env() -> dict[str, str]:
    names = _INHERITED_ENV + (_INHERITED_ENV_WINDOWS if os.name == "nt" else ())
    return {name: os.environ[name] for name in names if name in os.environ}


def hardened_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """The environment of a helper call; *env* may carry only ``GIT_INDEX_FILE``."""
    extra = dict(env or {})
    if not set(extra) <= {"GIT_INDEX_FILE"}:
        raise ValueError("only GIT_INDEX_FILE may be passed to a supervisor git call")
    return {
        **_inherited_env(),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "",
        **extra,
    }


def _config_read_env() -> dict[str, str]:
    """The environment of an out-of-helper config read: the user's config stays visible."""
    names = _CONFIG_LOCATION_ENV + (_CONFIG_LOCATION_ENV_WINDOWS if os.name == "nt" else ())
    return {
        **_inherited_env(),
        **{name: os.environ[name] for name in names if name in os.environ},
    }


def _fixed_flags(*, literal_pathspecs: bool = False) -> list[str]:
    flags = ["--no-replace-objects"]
    if literal_pathspecs:
        flags.append("--literal-pathspecs")
    settings = {
        "core.hooksPath": _empty_hooks_dir(),
        "core.fsmonitor": "false",
        "diff.external": "",
        "commit.gpgSign": "false",
        "tag.gpgSign": "false",
        "core.attributesFile": os.devnull,
    }
    for key, value in settings.items():
        flags += ["-c", f"{key}={value}"]
    return flags


def _launch(
    argv: list[str], *, cwd: Path | None, env: dict[str, str], stdin: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    """The one place a supervisor ``git`` process starts."""
    try:
        return subprocess.run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            input=stdin,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SupervisorGitError(
            "denied-git-unavailable", f"git could not run: {exc}", unverifiable=True
        ) from exc


# ── discovery ───────────────────────────────────────────────────────────────


def discover(cwd: Path | None) -> Pins:
    """The repository root, Git directory, and common directory that *cwd* belongs to.

    Runs before any directory is pinned, so it cannot pass ``--git-dir``; it
    uses the helper's environment and flags instead.
    """
    done = _launch(
        [
            "git",
            *_fixed_flags(),
            "rev-parse",
            "--path-format=absolute",
            "--show-toplevel",
            "--absolute-git-dir",
            "--git-common-dir",
        ],
        cwd=cwd,
        env=hardened_env(),
    )
    lines = done.stdout.decode("utf-8", "surrogateescape").split("\n")
    if done.returncode != 0 or len(lines) != 4 or not all(lines[:3]):
        raise SupervisorGitError("denied-git-discovery", "run from inside a Git repository")
    root, git_dir, common_dir = (Path(line).resolve() for line in lines[:3])
    return Pins(root, git_dir, common_dir)


# ── config reads that run outside the helper ────────────────────────────────


def _parse_config(raw: bytes) -> list[ConfigEntry]:
    """Parse ``-z --show-scope`` output: ``scope NUL key NL value NUL`` per entry."""
    tokens = raw.decode("utf-8", "replace").split("\0")
    entries = []
    for scope, record in zip(tokens[0::2], tokens[1::2], strict=False):
        key, _, value = record.partition("\n")
        entries.append(ConfigEntry(scope, key, value))
    return entries


def _read_config(pins: Pins, *selector: str) -> list[ConfigEntry]:
    done = _launch(
        ["git", f"--git-dir={pins.git_dir}", "config", "-z", "--show-scope", *selector],
        cwd=pins.root,
        env=_config_read_env(),
    )
    if done.returncode not in (0, 1):
        raise SupervisorGitError(
            "denied-git-failed", "git config could not be read", unverifiable=True
        )
    return _parse_config(done.stdout)


def _is_code_running(key: str, value: str) -> bool:
    """True when Git runs the value of *key* (lower-cased section and variable) as a command."""
    parts = key.split(".")
    variable = parts[-1]
    if key in _CODE_RUNNING_FIXED:
        return not (key == "core.fsmonitor" and value.strip().lower() in _BOOLEANS)
    if len(parts) >= 3 and (
        (parts[0] == "filter" and variable in _FILTER_SETTINGS)
        or (parts[0] == "diff" and variable in ("textconv", "command"))
        or (parts[0] == "gpg" and variable == "program")
        or (parts[0] == "includeif" and variable == "path")
    ):
        return True
    return variable.endswith(("command", "program"))


def code_running_keys(entries: list[ConfigEntry]) -> list[ConfigEntry]:
    """Entries from repository or worktree config whose value Git runs as a program."""
    return [
        e
        for e in entries
        if e.scope in ("local", "worktree") and _is_code_running(e.key, e.value)
    ]


def defined_filters(entries: list[ConfigEntry]) -> dict[str, ConfigEntry]:
    """The first config entry that defines each ``filter.<name>.*``, in any scope."""
    found: dict[str, ConfigEntry] = {}
    for entry in entries:
        parts = entry.key.split(".")
        if parts[0] == "filter" and len(parts) >= 3:
            found.setdefault(".".join(parts[1:-1]), entry)
    return found


def _filters_named_in(text: str) -> set[str]:
    names = set()
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        names.update(t[len("filter="):] for t in line.split() if t.startswith("filter=") and t[7:])
    return names


def attribute_filters(pins: Pins) -> dict[str, str]:
    """Each ``filter=<name>`` that an attributes file Git reads for the work tree uses.

    Maps the name to the first file that uses it: every ``.gitattributes`` in
    the work tree, nested ones included, and ``info/attributes``. Links are not
    followed, as Git does not follow them.
    """
    used: dict[str, str] = {}

    def scan(path: Path, label: str) -> None:
        try:
            info = os.lstat(path)
        except OSError:
            return
        if not stat.S_ISREG(info.st_mode):
            return
        if info.st_size > _MAX_ATTRIBUTES_BYTES:
            raise SupervisorGitError("denied-git-config", f"{label} is too large to check")
        with path.open("rb") as handle:
            text = handle.read(_MAX_ATTRIBUTES_BYTES).decode("utf-8", "replace")
        for name in _filters_named_in(text):
            used.setdefault(name, label)

    for directory in sorted({pins.git_dir, pins.common_dir}):
        scan(directory / "info" / "attributes", "info/attributes")
    pending = [pins.root]
    while pending:
        current = pending.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda e: e.name)
        except OSError:
            continue
        for entry in entries:
            if entry.name == ".git":
                continue
            if entry.is_dir(follow_symlinks=False):
                pending.append(Path(entry.path))
            elif entry.name == ".gitattributes":
                scan(Path(entry.path), Path(entry.path).relative_to(pins.root).as_posix())
    return used


# ── the helper ──────────────────────────────────────────────────────────────


def _same(left: Path, right: Path) -> bool:
    """Whether two paths name the same file; a path that is missing is a mismatch.

    A path that exists but cannot be stated is not a mismatch: the check could
    not be made, so it refuses as unverifiable.
    """
    try:
        return left.samefile(right)
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError as exc:
        raise SupervisorGitError(
            "denied-git-control-state", "a pinned directory cannot be read", unverifiable=True
        ) from exc


def _small_text(path: Path) -> str | None:
    """A short regular file's text, or None when it is absent or not a regular file."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return None
        with path.open("rb") as handle:
            return handle.read(_MAX_SMALL_FILE_BYTES).decode("utf-8", "replace")
    except OSError:
        return None


class HardenedGit:
    """The only way the supervisor runs ``git`` against one work tree."""

    def __init__(self, root: Path) -> None:
        self.root = root
        # Seam for the open-attempt comparison against the attempt's manifest.
        self.control_check: Callable[[HardenedGit], None] | None = None
        self._pins: Pins | None = None
        self._config: list[ConfigEntry] | None = None
        self._carried: list[str] | None = None
        self._identity: tuple[str, str] | None = None

    # ── pinning ─────────────────────────────────────────────────────────────

    @property
    def pins(self) -> Pins:
        """The directories pinned on first use."""
        if self._pins is None:
            found = discover(self.root)
            if not _same(found.root, self.root):
                raise SupervisorGitError(
                    "denied-git-control-state", "the work tree is not a repository root"
                )
            self._pins = found
        return self._pins

    def verify_control_state(self) -> None:
        """Refuse unless the gitfile and ``commondir`` still resolve to the pinned directories."""
        pins = self.pins
        dot_git = pins.root / ".git"
        try:
            kind = os.lstat(dot_git).st_mode
        except OSError as exc:
            raise self._control("the work tree has no .git entry", unverifiable=True) from exc
        if stat.S_ISDIR(kind):
            target: Path | None = dot_git
        elif stat.S_ISREG(kind):
            text = _small_text(dot_git)
            if text is None:
                raise self._control("the work tree's .git file cannot be read", unverifiable=True)
            match = re.fullmatch(r"gitdir: (.+?)\r?\n?", text)
            target = pins.root / match.group(1) if match else None
        else:
            target = None
        if target is None or not _same(target, pins.git_dir):
            raise self._control("the work tree's .git no longer names the pinned Git directory")
        commondir = pins.git_dir / "commondir"
        if os.path.lexists(commondir):
            text = _small_text(commondir)
            if text is None:
                raise self._control("commondir cannot be read", unverifiable=True)
            common = pins.git_dir / text.strip()
        else:
            common = pins.git_dir
        if common is None or not _same(common, pins.common_dir):
            raise self._control("commondir no longer names the pinned common directory")
        for directory in {pins.git_dir, pins.common_dir}:
            if os.path.lexists(directory / "info" / "grafts"):
                raise self._control("a graft file is present")
        if self.control_check is not None:
            self.control_check(self)

    @staticmethod
    def _control(detail: str, *, unverifiable: bool = False) -> SupervisorGitError:
        return SupervisorGitError("denied-git-control-state", detail, unverifiable=unverifiable)

    # ── the config reads that run outside the helper ────────────────────────

    def config_entries(self) -> list[ConfigEntry]:
        """The effective config, read once: carried settings, filters, and refused keys."""
        if self._config is None:
            self.verify_control_state()
            self._config = _read_config(self.pins, "--get-regexp", ".")
        return self._config

    def commit_identity(self) -> tuple[str, str]:
        """``user.name`` and ``user.email``, read once, or the supervisor's own identity."""
        if self._identity is None:
            self.verify_control_state()
            found = {
                e.key: e.value
                for e in _read_config(self.pins, "--get-regexp", r"^user\.(name|email)$")
            }
            clean = [re.sub(r"[<>\x00-\x1f]", "", found.get(k, "")).strip() for k in
                     ("user.name", "user.email")]
            self._identity = (
                (clean[0], clean[1])
                if all(clean)
                else ("work-supervisor", "work-supervisor@localhost.invalid")
            )
        return self._identity

    def _carried_flags(self) -> list[str]:
        """The carried settings and the neutralized filters, from the one config read."""
        if self._carried is None:
            latest = {e.key: e.value for e in self.config_entries()}
            flags: list[str] = []
            autocrlf, eol = latest.get("core.autocrlf"), latest.get("core.eol")
            if autocrlf is not None and autocrlf.lower() in ("true", "false", "input"):
                flags += ["-c", f"core.autocrlf={autocrlf.lower()}"]
            if eol is not None and eol.lower() in ("lf", "crlf", "native"):
                flags += ["-c", f"core.eol={eol.lower()}"]
            flags += ["-c", f"core.excludesFile={latest.get('core.excludesfile') or os.devnull}"]
            for name in sorted(self.repository_filters()):
                for setting in _FILTER_SETTINGS:
                    flags += ["-c", f"filter.{name}.{setting}="]
                flags += ["-c", f"filter.{name}.required=false"]
            self._carried = flags
        return self._carried

    def repository_filters(self) -> set[str]:
        """Names of filters that repository or worktree config defines."""
        names = set()
        for entry in self.config_entries():
            parts = entry.key.split(".")
            if entry.scope in ("local", "worktree") and parts[0] == "filter" and len(parts) >= 3:
                name = ".".join(parts[1:-1])
                if not _FILTER_NAME_RE.fullmatch(name):
                    raise SupervisorGitError(
                        "denied-git-config", "a filter name cannot be neutralized"
                    )
                names.add(name)
        return names

    # ── the helper call ─────────────────────────────────────────────────────

    def run(
        self,
        *args: str,
        env: Mapping[str, str] | None = None,
        stdin: bytes | None = None,
        check: bool = True,
        literal_pathspecs: bool = False,
    ) -> bytes:
        """Run ``git <args>`` against the pinned directories and return stdout bytes."""
        environment = hardened_env(env)
        self.verify_control_state()
        pins = self.pins
        diffing = ["--no-ext-diff", "--no-textconv"] if args[0] in _DIFFING else []
        argv = [
            "git",
            f"--git-dir={pins.git_dir}",
            f"--work-tree={pins.root}",
            *_fixed_flags(literal_pathspecs=literal_pathspecs),
            *self._carried_flags(),
            args[0],
            *diffing,
            *args[1:],
        ]
        result = _launch(argv, cwd=pins.root, env=environment, stdin=stdin)
        if check and result.returncode != 0:
            detail = result.stderr.decode("utf-8", "replace").strip().splitlines()
            raise SupervisorGitError(
                "denied-git-failed", f"git {args[0]} failed: {detail[-1] if detail else ''}"
            )
        return result.stdout
