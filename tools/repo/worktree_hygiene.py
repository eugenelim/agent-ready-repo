#!/usr/bin/env python3
"""Inspect registered Git worktrees and perform explicitly selected safe cleanup.

This repository-local command deliberately makes the useful operation the dry run.
It never guesses worktree roots from names and never follows links while traversing.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable


def _configure_stream(stream: object, errors: str) -> None:
    """Configure a standard stream when the host stream supports reconfiguration."""
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors=errors)


_configure_stream(sys.stdout, "strict")
_configure_stream(sys.stderr, "backslashreplace")

SCHEMA_VERSION = 2
IMPORT_SENTINEL = "__AGENTBUNDLE_IMPORT_RESOLUTION__="
IMPORT_TIMEOUT_SECONDS = 10
IMPORT_PROBE = (
    "import json\n"
    "try:\n"
    "    import agentbundle\n"
    "except ModuleNotFoundError as error:\n"
    "    if error.name != 'agentbundle':\n"
    "        raise\n"
    "    result = {'state': 'absent'}\n"
    "else:\n"
    "    path = getattr(agentbundle, '__file__', None)\n"
    "    if not isinstance(path, str):\n"
    "        raise RuntimeError('agentbundle has no import path')\n"
    "    result = {'state': 'resolved', 'path': path}\n"
    f"print({IMPORT_SENTINEL!r} + json.dumps(result, sort_keys=True))\n"
)
CATEGORIES = ("dependencies", "generated", "test_artifacts")
CLEANABLE_CATEGORIES = frozenset(CATEGORIES)
EXPENSIVE = {"dependencies"}
PROTECTED_ROOTS = {".loop-run", ".context"}
PLAYWRIGHT_EVIDENCE_DIRECTORY = ".playwright-failure-evidence"
PLAYWRIGHT_EVIDENCE_PIN = ".pinned"
DEFAULT_PLAYWRIGHT_EVIDENCE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
PLAYWRIGHT_ARCHIVE_NAME_ATTEMPTS = 64
NAMES = {
    "node_modules": "dependencies",
    ".venv": "dependencies",
    "venv": "dependencies",
    "env": "dependencies",
    "build": "generated",
    "dist": "generated",
    ".astro": "generated",
    "test-results": "test_artifacts",
    "playwright-report": "test_artifacts",
    ".pytest_cache": "test_artifacts",
    ".coverage": "test_artifacts",
    ".ruff_cache": "test_artifacts",
    ".mypy_cache": "test_artifacts",
    "__pycache__": "test_artifacts",
    ".local-browsers": "shared_caches",
}
Runner = Callable[..., subprocess.CompletedProcess[str]]
MountCheck = Callable[[Path], bool]


@dataclass(frozen=True)
class Worktree:
    path: Path
    head: str = ""
    branch: str = ""
    bare: bool = False
    detached: bool = False
    prunable: str = ""

    def __post_init__(self) -> None:
        """Keep every root comparison in one canonical path namespace."""
        object.__setattr__(self, "path", self.path.resolve())


@dataclass
class Candidate:
    path: Path
    category: str
    bytes: int
    is_dir: bool
    ignored: bool = False
    protected: bool = False
    git_admin: bool = False
    canonical_path: Path = field(init=False)

    def __post_init__(self) -> None:
        """Retain the lexical path for link checks and a canonical comparison path."""
        self.canonical_path = self.path.resolve()


@dataclass
class ScanResult:
    worktree: Worktree
    candidates: list[Candidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    traversals: int = 0


@dataclass(frozen=True)
class GitPathsResult:
    paths: set[Path]
    error: str = ""


@dataclass(frozen=True)
class GitStatus:
    ignored: set[Path]
    tracked: set[Path]
    error: str = ""


@dataclass(frozen=True)
class PlaywrightEvidenceResult:
    """Account for lifecycle mutations made for browser-gate evidence."""

    archived: int = 0
    cleaned: int = 0
    pruned: int = 0
    skipped: int = 0
    refused: bool = False
    receipt: tuple[str, ...] = ()


@dataclass(frozen=True)
class LifecycleResult:
    """Report an optional worktree lifecycle hook without mutating Git state."""

    code: int
    lines: tuple[str, ...]


def _run(
    argv: list[str],
    *,
    input: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        input=input,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _call(
    runner: Runner,
    argv: list[str],
    *,
    input: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return runner(argv, input=input, env=env)


def _run_import_probe(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    """Run the isolated import measurement without writing worktree bytecode."""
    return subprocess.run(  # nosec B603  # fixed interpreter and inline probe
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=IMPORT_TIMEOUT_SECONDS,
    )


def _import_provenance(worktree: Path) -> dict[str, object]:
    """Describe the process context used for the isolated import probe."""
    return {
        "interpreter": sys.executable,
        "cwd": str(worktree.resolve()),
        "removed_environment_inputs": [
            "PYTHONPATH",
            "cwd sys.path entry (-P)",
        ],
    }


def _agentbundle_import_resolution(
    worktree: Path,
    import_runner: Callable[..., subprocess.CompletedProcess[str]] = _run_import_probe,
) -> dict[str, object]:
    """Measure where agentbundle resolves without this worktree's PYTHONPATH."""
    provenance = _import_provenance(worktree)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = import_runner(
            [sys.executable, "-P", "-c", IMPORT_PROBE],
            cwd=worktree,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return {
            **provenance,
            "status": "inconclusive",
            "detail": "isolated import probe timed out",
        }
    except OSError as error:
        return {
            **provenance,
            "status": "inconclusive",
            "detail": f"isolated import probe could not run: {error}",
        }
    if result.returncode:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        return {
            **provenance,
            "status": "inconclusive",
            "detail": f"isolated import probe failed: {detail}",
        }
    records = [
        line.removeprefix(IMPORT_SENTINEL)
        for line in result.stdout.splitlines()
        if line.startswith(IMPORT_SENTINEL)
    ]
    if len(records) != 1:
        return {
            **provenance,
            "status": "inconclusive",
            "detail": "isolated import probe produced no unambiguous result",
        }
    try:
        record = json.loads(records[0])
    except json.JSONDecodeError:
        record = None
    if not isinstance(record, dict):
        return {
            **provenance,
            "status": "inconclusive",
            "detail": "isolated import probe produced an invalid result",
        }
    if record.get("state") == "absent":
        return {**provenance, "status": "absent"}
    path = record.get("path")
    if record.get("state") != "resolved" or not isinstance(path, str):
        return {
            **provenance,
            "status": "inconclusive",
            "detail": "isolated import probe produced an invalid result",
        }
    resolved = Path(path).resolve()
    return {
        **provenance,
        "status": "inside" if _under(resolved, worktree) else "outside",
        "path": str(resolved),
    }


def _unregistered_worktree_resolution(repository: Path) -> dict[str, object]:
    """State why an import probe cannot use a registered worktree."""
    return {
        **_import_provenance(repository),
        "status": "inconclusive",
        "detail": "no registered worktree contains the invocation directory",
    }


def _import_resolution_warning(resolution: dict[str, object]) -> str | None:
    """Render only the measured import-resolution fact for scan warnings."""
    context = (
        f"interpreter: {resolution['interpreter']}; "
        f"cwd: {resolution['cwd']}; removed environment inputs: "
        f"{', '.join(resolution['removed_environment_inputs'])}"
    )
    status = resolution["status"]
    if status == "outside":
        return (
            "agentbundle resolves outside this worktree, at "
            f"{resolution['path']} ({context})"
        )
    if status == "absent":
        return f"agentbundle is absent in isolated import measurement ({context})"
    if status == "inconclusive":
        return (
            "agentbundle isolated import measurement is inconclusive: "
            f"{resolution['detail']} ({context})"
        )
    return None


def _import_resolution_human_line(resolution: dict[str, object]) -> str:
    """Render the measured import-resolution fact for the human report."""
    warning = _import_resolution_warning(resolution)
    if warning:
        return warning
    context = (
        f"interpreter: {resolution['interpreter']}; "
        f"cwd: {resolution['cwd']}; removed environment inputs: "
        f"{', '.join(resolution['removed_environment_inputs'])}"
    )
    return (
        "agentbundle resolves inside this worktree, at "
        f"{resolution['path']} ({context})"
    )


def _parse_porcelain(text: str) -> list[Worktree]:
    records: list[dict[str, str]] = []
    record: dict[str, str] = {}
    for entry in text.split("\0"):
        if not entry:
            if record:
                records.append(record)
                record = {}
            continue
        key, _, value = entry.partition(" ")
        record[key] = value
    if record:
        records.append(record)
    return [
        Worktree(
            Path(item["worktree"]),
            item.get("HEAD", ""),
            item.get("branch", ""),
            "bare" in item,
            "detached" in item,
            item.get("prunable", ""),
        )
        for item in records
        if "worktree" in item
    ]


def discover_worktrees(
    repository: Path,
    runner: Runner = _run,
) -> tuple[Path, Path | None, list[Worktree], list[str]]:
    """Return repository identity, common dir, porcelain records, and warnings."""
    warnings: list[str] = []
    listed = _call(
        runner,
        [
            "git",
            "-C",
            str(repository),
            "worktree",
            "list",
            "--porcelain",
            "-z",
        ],
    )
    if listed.returncode:
        return (
            repository.resolve(),
            repository.resolve() / ".git",
            [],
            [listed.stderr.strip() or "git worktree list failed"],
        )
    common = _call(
        runner,
        ["git", "-C", str(repository), "rev-parse", "--git-common-dir"],
    )
    if common.returncode:
        detail = common.stderr.strip() or f"exit {common.returncode}"
        warnings.append(f"git common directory unavailable: {detail}")
        return repository.resolve(), None, _parse_porcelain(listed.stdout), warnings
    common_dir = Path(common.stdout.strip())
    if not common_dir.is_absolute():
        common_dir = repository / common_dir
    return (
        repository.resolve(),
        common_dir.resolve(),
        _parse_porcelain(listed.stdout),
        warnings,
    )


def _measurement_name() -> str:
    return "allocated" if hasattr(os.stat_result, "st_blocks") else "logical"


def _size(path: Path, warnings: list[str]) -> tuple[int, str]:
    """Measure a path without following a link; tolerate concurrent removal."""
    try:
        stat = path.stat(follow_symlinks=False)
    except (FileNotFoundError, PermissionError) as exc:
        warnings.append(f"cannot stat {path}: {exc.__class__.__name__}")
        return 0, _measurement_name()
    blocks = getattr(stat, "st_blocks", None)
    if blocks is not None:
        return int(blocks) * 512, "allocated"
    return int(stat.st_size), "logical"


def _tree_size(
    path: Path,
    warnings: list[str],
    protected_entries: list[Path] | None = None,
    git_entries: list[Path] | None = None,
) -> tuple[int, str]:
    total, measurement = _size(path, warnings)
    if not path.is_dir() or path.is_symlink():
        return total, measurement
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except (FileNotFoundError, PermissionError) as exc:
            warnings.append(f"cannot read {current}: {exc.__class__.__name__}")
            continue
        for entry in entries:
            child = Path(entry.path)
            if entry.name == ".git":
                if git_entries is not None:
                    git_entries.append(child)
                continue
            if protected_entries is not None and (
                entry.name in PROTECTED_ROOTS
                or entry.name.endswith((".lock", ".lease"))
            ):
                protected_entries.append(child)
            try:
                if entry.is_symlink():
                    size, measurement = _size(child, warnings)
                    total += size
                elif entry.is_dir(follow_symlinks=False):
                    stack.append(child)
                else:
                    size, measurement = _size(child, warnings)
                    total += size
            except (FileNotFoundError, PermissionError) as exc:
                warnings.append(f"cannot inspect {child}: {exc.__class__.__name__}")
    return total, measurement


def scan_worktree(worktree: Worktree) -> ScanResult:
    """Classify candidates in one walk, stopping at each candidate root."""
    result = ScanResult(worktree=worktree, traversals=1)
    if worktree.prunable or not worktree.path.exists() or worktree.bare:
        if not worktree.path.exists() and not worktree.bare:
            result.warnings.append(
                f"registered worktree is missing: {worktree.path}"
            )
        return result
    stack = [worktree.path]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except (FileNotFoundError, PermissionError) as exc:
            result.warnings.append(
                f"cannot read {current}: {exc.__class__.__name__}"
            )
            continue
        for entry in entries:
            child = Path(entry.path)
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                is_symlink = entry.is_symlink()
            except (FileNotFoundError, PermissionError) as exc:
                result.warnings.append(
                    f"cannot inspect {child}: {exc.__class__.__name__}"
                )
                continue
            if entry.name == ".git":
                continue
            if entry.name in PROTECTED_ROOTS:
                size, _ = _tree_size(child, result.warnings)
                result.candidates.append(
                    Candidate(
                        child,
                        "protected",
                        size,
                        is_dir,
                        protected=True,
                    )
                )
                continue
            category = NAMES.get(entry.name)
            if category:
                protected_entries: list[Path] = []
                git_entries: list[Path] = []
                size, _ = _tree_size(
                    child,
                    result.warnings,
                    protected_entries,
                    git_entries,
                )
                result.candidates.append(
                    Candidate(
                        child,
                        category,
                        size,
                        is_dir,
                        protected=bool(protected_entries),
                        git_admin=bool(git_entries),
                    )
                )
                continue
            if is_dir and not is_symlink:
                stack.append(child)
    result.candidates.sort(key=lambda item: (str(item.path), item.category))
    return result


def _under(path: Path, root: Path) -> bool:
    """Return whether *path* resolves beneath *root* without raising."""
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _containing_worktree(
    directory: Path, worktrees: list[Worktree]
) -> Path | None:
    """Return the most-specific registered worktree containing a directory."""
    current = directory.resolve()
    matches = [
        worktree.path
        for worktree in worktrees
        if _under(current, worktree.path)
    ]
    return max(matches, key=lambda path: len(path.parts), default=None)


def _default_branch_ref(
    repository: Path, runner: Runner
) -> tuple[str | None, str | None]:
    """Determine one remote-tracking default branch without guessing."""
    remotes = _call(runner, ["git", "-C", str(repository), "remote"])
    if remotes.returncode:
        detail = remotes.stderr.strip() or f"exit {remotes.returncode}"
        return None, f"could not determine default branch: {detail}"
    remote_names = [name for name in remotes.stdout.splitlines() if name]
    if len(remote_names) != 1:
        return None, "could not determine default branch: expected exactly one remote"
    default = _call(
        runner,
        [
            "git",
            "-C",
            str(repository),
            "symbolic-ref",
            "--quiet",
            f"refs/remotes/{remote_names[0]}/HEAD",
        ],
    )
    if default.returncode or not default.stdout.strip():
        detail = default.stderr.strip() or f"exit {default.returncode}"
        return None, f"could not determine default branch: {detail}"
    return default.stdout.strip(), None


def _merged_branches(
    repository: Path, runner: Runner
) -> tuple[set[str] | None, str | None]:
    """Read branches merged into the Git-determined default branch once."""
    default_branch, default_warning = _default_branch_ref(repository, runner)
    if default_warning:
        return None, default_warning
    assert default_branch is not None
    result = _call(
        runner,
        [
            "git",
            "-C",
            str(repository),
            "for-each-ref",
            "--format=%(refname)",
            "--merged",
            default_branch,
            "refs/heads",
        ],
    )
    if result.returncode:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        return None, f"could not determine merged worktrees: {detail}"
    return set(result.stdout.splitlines()), None


def _lifecycle_report(
    repository: Path,
    worktrees: list[Worktree],
    warnings: list[str],
    runner: Runner = _run,
) -> list[str]:
    """Classify registered worktrees from Git facts and the invocation directory."""
    current = _containing_worktree(repository, worktrees)
    merged, merged_warning = _merged_branches(repository, runner)
    default_branch, _ = _default_branch_ref(repository, runner)
    default_local = (
        "refs/heads/" + "/".join(default_branch.split("/")[3:])
        if default_branch
        else None
    )
    if merged_warning:
        warnings.append(merged_warning)
    prune_signal = [worktree.path for worktree in worktrees if worktree.prunable]
    currently_active = [current] if current is not None else []
    merged_paths = [
        worktree.path
        for worktree in worktrees
        if (
            merged is not None
            and worktree.branch
            and worktree.branch in merged
            and worktree.path != current
            # "merged into the default branch" is vacuous for the default
            # branch itself; keep the primary checkout out of this bucket.
            # The porcelain reports refs/heads/<name> while the default is a
            # remote-tracking refs/remotes/<remote>/<name>, so compare the
            # local form -- a bare != never matches.
            and worktree.branch != default_local
        )
    ]
    no_merge_or_prune_signal = [
        worktree.path
        for worktree in worktrees
        if worktree.path not in prune_signal
        and worktree.path not in currently_active
        and worktree.path not in merged_paths
    ]
    lines = [
        "lifecycle report:",
        "currently-active observation: registered worktree containing the "
        "invocation directory; no liveness claim",
        "prune-signal observation: Git reported the worktree record as prunable; "
        "this does not assert that its path has been removed",
        "no-merge-or-prune-signal observation: registered worktree without a "
        "prune signal, default-branch merge signal, or current-invocation "
        "containment; no activity or liveness inference",
    ]
    categories: list[tuple[str, list[Path] | None]] = [
        ("merged", merged_paths if merged is not None else None),
        ("prune-signal", prune_signal),
        ("no-merge-or-prune-signal", no_merge_or_prune_signal),
        ("currently-active", currently_active),
    ]
    for label, paths in categories:
        if paths is None:
            lines.append(f"{label}: undetermined")
            continue
        if paths:
            lines.extend(f"{label}: {path}" for path in paths)
        else:
            lines.append(f"{label}: none")
    lines.extend(f"warning: {warning}" for warning in sorted(set(warnings)))
    return lines


def lifecycle_hook(
    command: str,
    repository: Path,
    *,
    protected: set[Path] | None = None,
    runner: Runner = _run,
    import_runner: Callable[..., subprocess.CompletedProcess[str]] = _run_import_probe,
) -> LifecycleResult:
    """Run an optional hook and refuse unsafe removal without removing anything."""
    _, _, worktrees, warnings = discover_worktrees(repository, runner)
    lines = _lifecycle_report(repository, worktrees, warnings, runner)
    if command != "before-remove":
        return LifecycleResult(0, tuple(lines))
    current = _containing_worktree(repository, worktrees)
    resolution = (
        _agentbundle_import_resolution(current, import_runner)
        if current is not None
        else _unregistered_worktree_resolution(repository)
    )
    lines.append("import resolution: " + _import_resolution_human_line(resolution))
    if current is not None and current in (protected or set()):
        lines.append(f"refusing worktree removal: protected worktree: {current}")
        return LifecycleResult(2, tuple(lines))
    if resolution["status"] != "inside":
        lines.append(
            "refusing worktree removal: agentbundle import resolution is "
            f"{resolution['status']}, not inside this worktree"
        )
        return LifecycleResult(2, tuple(lines))
    lines.append(
        "before-remove passed: this hook does not remove worktrees or branches"
    )
    return LifecycleResult(0, tuple(lines))


def _protected_paths(values: Iterable[str]) -> set[Path]:
    paths = {Path(value).resolve() for value in values if value}
    environment_values = os.environ.get(
        "WORKTREE_HYGIENE_PROTECT_WORKTREES",
        "",
    ).split(os.pathsep)
    paths.update(Path(value).resolve() for value in environment_values if value)
    return paths


def _parse_mountinfo(text: str) -> set[Path]:
    """Return decoded mount points from Linux procfs mount information."""
    replacements = {
        "\\040": " ",
        "\\011": "\t",
        "\\012": "\n",
        "\\134": "\\",
    }
    mount_points: set[Path] = set()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 5:
            continue
        value = fields[4]
        for escaped, decoded in replacements.items():
            value = value.replace(escaped, decoded)
        mount_points.add(Path(value).resolve())
    return mount_points


def _linux_mount_points() -> set[Path] | None:
    """Read the current Linux mount table once, when procfs is available."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        text = Path("/proc/self/mountinfo").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return _parse_mountinfo(text)


def _default_mount_check() -> MountCheck:
    """Compose portable mount detection with one Linux mount-table snapshot."""
    mount_points = _linux_mount_points()

    def is_mount(path: Path) -> bool:
        return os.path.ismount(path) or (
            mount_points is not None and path.resolve() in mount_points
        )

    return is_mount


def _git_paths(
    runner: Runner,
    argv: list[str],
    paths: list[Path],
) -> GitPathsResult:
    """Run check-ignore, where exits zero and one are both successful."""
    if not paths:
        return GitPathsResult(set())
    payload = "\0".join(str(path) for path in paths) + "\0"
    result = _call(runner, argv, input=payload)
    if result.returncode not in {0, 1}:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        return GitPathsResult(set(), detail)
    parsed = {Path(value) for value in result.stdout.split("\0") if value}
    return GitPathsResult(parsed)


def _mark_git_status(
    root: Path,
    candidates: list[Candidate],
    runner: Runner,
) -> GitStatus:
    if not candidates:
        return GitStatus(set(), set())
    paths: list[Path] = []
    for candidate in candidates:
        if _under(candidate.canonical_path, root):
            paths.append(candidate.canonical_path.relative_to(root))
    if not paths:
        return GitStatus(set(), set())
    ignored_result = _git_paths(
        runner,
        [
            "git",
            "-C",
            str(root),
            "check-ignore",
            "-z",
            "--stdin",
        ],
        paths,
    )
    if ignored_result.error:
        return GitStatus(
            set(),
            set(),
            f"git check-ignore failed: {ignored_result.error}",
        )
    result = _call(
        runner,
        [
            "git",
            "--literal-pathspecs",
            "-C",
            str(root),
            "ls-files",
            "-z",
            "--",
            *map(str, paths),
        ],
    )
    if result.returncode:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        return GitStatus(set(), set(), f"git ls-files failed: {detail}")
    tracked = {Path(value) for value in result.stdout.split("\0") if value}
    return GitStatus(ignored_result.paths, tracked)


def _mark_scan_ignored(result: ScanResult, runner: Runner) -> None:
    """Attach ignored status with one batched query for a scanned worktree."""
    relative_candidates: list[tuple[Candidate, Path]] = []
    for candidate in result.candidates:
        try:
            relative = candidate.path.relative_to(result.worktree.path)
        except ValueError:
            continue
        relative_candidates.append((candidate, relative))
    ignored_result = _git_paths(
        runner,
        [
            "git",
            "-C",
            str(result.worktree.path),
            "check-ignore",
            "-z",
            "--stdin",
        ],
        [relative for _, relative in relative_candidates],
    )
    if ignored_result.error:
        result.warnings.append(
            f"git check-ignore failed: {ignored_result.error}"
        )
        return
    for candidate, relative in relative_candidates:
        candidate.ignored = relative in ignored_result.paths


def _installed_distribution_locations() -> list[Path]:
    """Return resolved locations used by distributions in this interpreter."""
    locations: set[Path] = set()
    for distribution in importlib.metadata.distributions():
        try:
            locations.add(Path(str(distribution.locate_file(""))).resolve())
        except (FileNotFoundError, OSError):
            continue
    return sorted(locations, key=str)


def _default_playwright_path() -> Path:
    """Return Playwright's documented default without importing Playwright."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    if os.name == "nt":
        default = Path.home() / "AppData" / "Local"
        base = os.environ.get("LOCALAPPDATA", str(default))
        return Path(base) / "ms-playwright"
    return Path.home() / ".cache" / "ms-playwright"


def _cache_diagnostics(
    worktrees: list[Worktree],
    runner: Runner,
    warnings: list[str],
) -> list[dict[str, object]]:
    roots = [worktree.path for worktree in worktrees]
    configured = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    browser_path = Path(configured).expanduser() if configured else _default_playwright_path()
    mode = "documented_platform_default"
    if configured:
        mode = "hermetic" if configured == "0" else "explicitly_shared"
    result: list[dict[str, object]] = []
    if configured != "0":
        resolved = browser_path.resolve()
        result.append(
            {
                "kind": "playwright",
                "path": str(resolved),
                "mode": mode,
                "revisions": _browser_revisions(resolved, warnings),
                "beneath_worktree": any(
                    _under(resolved, root) for root in roots
                ),
            }
        )
    npm = _call(runner, ["npm", "config", "get", "cache"])
    if npm.returncode == 0 and npm.stdout.strip():
        cache = Path(npm.stdout.strip()).expanduser().resolve()
        result.append(
            {
                "kind": "npm",
                "path": str(cache),
                "mode": "effective",
                "beneath_worktree": any(
                    _under(cache, root) for root in roots
                ),
            }
        )
    return result


def _browser_revisions(path: Path, warnings: list[str]) -> list[str]:
    """List browser revision directories without following links."""
    if not path.is_dir() or path.is_symlink():
        return []
    try:
        entries = sorted(os.scandir(path), key=lambda entry: entry.name)
    except (FileNotFoundError, PermissionError) as exc:
        warnings.append(f"cannot read browser cache {path}: {exc.__class__.__name__}")
        return []
    revisions: list[str] = []
    for entry in entries:
        try:
            if entry.is_dir(follow_symlinks=False) and not entry.is_symlink():
                revisions.append(entry.name)
        except (FileNotFoundError, PermissionError) as exc:
            child = Path(entry.path)
            warnings.append(
                f"cannot inspect browser revision {child}: {exc.__class__.__name__}"
            )
    return revisions


def _duplicate_browser_revisions(
    caches: list[dict[str, object]],
) -> list[dict[str, object]]:
    locations: defaultdict[str, set[str]] = defaultdict(set)
    for cache in caches:
        if cache.get("kind") not in {"playwright", "playwright-local"}:
            continue
        path = str(cache["path"])
        revisions = cache.get("revisions")
        if not isinstance(revisions, list):
            continue
        for revision in revisions:
            locations[str(revision)].add(path)
    duplicates: list[dict[str, object]] = []
    for revision, paths in sorted(locations.items()):
        if len(paths) > 1:
            ordered = sorted(paths)
            duplicates.append(
                {
                    "kind": "playwright-duplicate-revision",
                    "path": ", ".join(ordered),
                    "mode": "duplicate",
                    "revision": revision,
                    "paths": ordered,
                }
            )
    return duplicates


def _candidate_data(candidate: Candidate) -> dict[str, object]:
    return {
        "path": str(candidate.path),
        "category": candidate.category,
        "bytes": candidate.bytes,
        "ignored": candidate.ignored,
        "protected": candidate.protected,
        "git_admin": candidate.git_admin,
    }


def scan(
    repository: Path,
    selected: list[Path] | None = None,
    runner: Runner = _run,
    *,
    include_ignore_status: bool = True,
    include_import_resolution: bool = True,
    import_runner: Callable[..., subprocess.CompletedProcess[str]] = _run_import_probe,
) -> dict[str, Any]:
    repo, common, worktrees, warnings = discover_worktrees(repository, runner)
    worktree_root = _containing_worktree(repo, worktrees)
    if include_import_resolution:
        import_resolution = (
            _agentbundle_import_resolution(worktree_root, import_runner)
            if worktree_root is not None
            else _unregistered_worktree_resolution(repo)
        )
        import_warning = _import_resolution_warning(import_resolution)
        if import_warning:
            warnings.append(import_warning)
    else:
        import_resolution = _import_provenance(worktree_root or repo)
    selected_roots = {path.resolve() for path in selected or []}
    if selected_roots:
        registered = {worktree.path for worktree in worktrees}
        for path in sorted(selected_roots - registered, key=str):
            warnings.append(f"selected worktree is not registered: {path}")
        worktrees = [
            worktree
            for worktree in worktrees
            if worktree.path in selected_roots
        ]
    results = [
        scan_worktree(worktree)
        for worktree in sorted(worktrees, key=lambda item: str(item.path))
    ]
    if include_ignore_status:
        for result in results:
            _mark_scan_ignored(result, runner)
    worktree_data: list[dict[str, Any]] = []
    for result in results:
        category_totals: defaultdict[str, int] = defaultdict(int)
        for candidate in result.candidates:
            if candidate.category != "shared_caches":
                category_totals[candidate.category] += candidate.bytes
        worktree_data.append(
            {
                "path": str(result.worktree.path),
                "head": result.worktree.head,
                "branch": result.worktree.branch,
                "bare": result.worktree.bare,
                "detached": result.worktree.detached,
                "prunable": result.worktree.prunable,
                "categories": dict(sorted(category_totals.items())),
                "total_local": sum(category_totals.values()),
                "candidates": [
                    _candidate_data(candidate)
                    for candidate in result.candidates
                ],
            }
        )
        warnings.extend(result.warnings)
    shared: list[dict[str, object]] = []
    local_browsers = [
        candidate
        for result in results
        for candidate in result.candidates
        if candidate.path.name == ".local-browsers"
    ]
    for candidate in local_browsers:
        shared.append(
            {
                "kind": "playwright-local",
                "path": str(candidate.path),
                "mode": "hermetic",
                "revisions": _browser_revisions(candidate.path, warnings),
                "beneath_worktree": True,
            }
        )
    shared.extend(_cache_diagnostics(worktrees, runner, warnings))
    shared.extend(_duplicate_browser_revisions(shared))
    totals: defaultdict[str, int] = defaultdict(int)
    for data in worktree_data:
        for category, count in data["categories"].items():
            totals[category] += count
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repo),
        "git_common_dir": str(common) if common is not None else None,
        "measurement": _measurement_name(),
        "agentbundle_import": import_resolution,
        "worktrees": worktree_data,
        "shared_caches": shared,
        "warnings": sorted(set(warnings)),
        "totals": dict(sorted(totals.items())),
    }


def _human(report: dict[str, Any]) -> str:
    lines = [
        f"measurement: {report['measurement']} bytes",
        "worktree  dependencies  generated  tests  protected  total local",
    ]
    import_resolution = report["agentbundle_import"]
    import_warning: str | None = None
    if "status" in import_resolution:
        import_warning = _import_resolution_warning(import_resolution)
        lines.append(
            "import resolution: "
            + _import_resolution_human_line(import_resolution)
        )
    for worktree_data in report["worktrees"]:
        categories = worktree_data["categories"]
        values = (
            worktree_data["path"],
            categories.get("dependencies", 0),
            categories.get("generated", 0),
            categories.get("test_artifacts", 0),
            categories.get("protected", 0),
            worktree_data["total_local"],
        )
        lines.append("{}  {}  {}  {}  {}  {}".format(*values))
    lines.append("shared storage:")
    lines.extend(
        f"  {cache['kind']}: {cache['path']} ({cache['mode']})"
        for cache in report["shared_caches"]
    )
    lines.append("largest cleanup candidates:")
    display_candidates: list[dict[str, Any]] = sorted(
        (
            candidate_data
            for worktree_data in report["worktrees"]
            for candidate_data in worktree_data["candidates"]
        ),
        key=lambda data: (-data["bytes"], data["path"]),
    )[:10]
    for data in display_candidates:
        recovery = (
            "expensive" if data["category"] in EXPENSIVE else "cheap"
        )
        ignored = "yes" if data["ignored"] else "no"
        protected = "yes" if data["protected"] else "no"
        category_flag = str(data["category"]).replace("_", "-")
        description = (
            "  {path} [{category}] {bytes} ignored? {ignored} "
            "protected? {protected} recover: {recovery}".format(
                path=data["path"],
                category=data["category"],
                bytes=data["bytes"],
                ignored=ignored,
                protected=protected,
                recovery=recovery,
            )
        )
        if data["category"] in CATEGORIES:
            description += f"; dry-run: clean --{category_flag}"
        else:
            description += "; cleanup: report only"
        lines.append(description)
    lines.extend(
        f"warning: {warning}"
        for warning in report["warnings"]
        if warning != import_warning
    )
    return "\n".join(lines)


def _is_tracked(relative: Path, tracked: set[Path]) -> bool:
    return any(
        path == relative or relative in path.parents
        for path in tracked
    )


def _is_in_use(candidate: Candidate, locations: list[Path]) -> bool:
    return any(
        _under(location, candidate.canonical_path)
        for location in locations
    )


def _candidate_from_data(data: dict[str, Any]) -> Candidate:
    path = Path(data["path"])
    return Candidate(
        path,
        str(data["category"]),
        int(data["bytes"]),
        path.is_dir(),
        ignored=bool(data.get("ignored", False)),
        protected=bool(data.get("protected", False)),
        git_admin=bool(data.get("git_admin", False)),
    )


def _path_component_reason(
    candidate: Candidate,
    root: Path,
    mount_check: MountCheck,
) -> str:
    """Re-stat the candidate path from its registered root without following links."""
    try:
        relative = candidate.path.relative_to(root)
    except ValueError:
        return "link or root escape"
    current = root
    for part in relative.parts:
        current /= part
        try:
            mode = current.lstat().st_mode
        except OSError:
            return "path changed or cannot be verified"
        if stat.S_ISLNK(mode):
            return "link or root escape"
        if mount_check(current):
            return "mount point"
        junction_check = getattr(current, "is_junction", None)
        if callable(junction_check) and junction_check():
            return "junction or root escape"
    try:
        resolved = candidate.path.resolve()
    except OSError:
        return "path changed or cannot be verified"
    if resolved != candidate.canonical_path:
        return "path changed or cannot be verified"
    if not _under(candidate.canonical_path, root):
        return "link or root escape"
    return ""


def _subtree_safety_reason(path: Path, mount_check: MountCheck) -> str:
    """Find protected state or Git administration without following links."""
    if mount_check(path):
        return "mount point"
    try:
        root_stat = path.lstat()
    except OSError:
        return "candidate changed or cannot be verified"
    if stat.S_ISLNK(root_stat.st_mode):
        return "link inside candidate"
    if not stat.S_ISDIR(root_stat.st_mode):
        return ""
    root_device = root_stat.st_dev
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except OSError:
            return "candidate changed or cannot be verified"
        for entry in entries:
            if entry.name == ".git":
                return "git administration"
            if entry.name in PROTECTED_ROOTS or entry.name.endswith(
                (".lock", ".lease")
            ):
                return "protected state or lock"
            child = Path(entry.path)
            try:
                child_stat = child.lstat()
                if child_stat.st_dev != root_device:
                    return "filesystem boundary"
                if stat.S_ISLNK(child_stat.st_mode):
                    return "link inside candidate"
                if mount_check(child):
                    return "mount point"
                junction_check = getattr(child, "is_junction", None)
                if callable(junction_check) and junction_check():
                    return "junction inside candidate"
                if stat.S_ISDIR(child_stat.st_mode):
                    stack.append(child)
            except OSError:
                return "candidate changed or cannot be verified"
    return ""


def _candidate_safety_reason(
    candidate: Candidate,
    root: Path,
    common: Path,
    protected: set[Path],
    mount_check: MountCheck,
) -> str:
    """Return the complete local safety rejection reason for one candidate."""
    effective_protection = protected | _protected_paths([])
    if root in effective_protection:
        return "protected worktree"
    if candidate.protected or candidate.path.name in PROTECTED_ROOTS:
        return "protected state or lock"
    if candidate.git_admin:
        return "git administration"
    path_reason = _path_component_reason(candidate, root, mount_check)
    if path_reason:
        return path_reason
    if (
        _under(candidate.canonical_path, common)
        or _under(common, candidate.canonical_path)
        or ".git" in candidate.path.parts
    ):
        return "git administration"
    subtree_reason = _subtree_safety_reason(candidate.path, mount_check)
    if subtree_reason:
        return subtree_reason
    return _path_component_reason(candidate, root, mount_check)


def _registered_current_worktree(
    repository: Path,
    runner: Runner,
) -> Path | None:
    """Resolve the registered worktree containing an invocation, if known."""
    _, _, worktrees, _ = discover_worktrees(repository, runner)
    return _containing_worktree(repository, worktrees)


def _current_worktree(repository: Path, runner: Runner) -> Path:
    """Resolve the clean target, retaining clean's established fallback."""
    return _registered_current_worktree(repository, runner) or repository.resolve()


def _coordination_lease_module() -> Any:
    """Import the optional lease participant without creating an import cycle."""
    if __package__:
        from . import coordination_lease
    else:
        import coordination_lease

    return coordination_lease


def _claim_holder_names(claims: Iterable[Any]) -> str:
    """Render only the safe holder identity fields for a refusal receipt."""
    holders = []
    for claim in claims:
        pid = claim.pid if isinstance(claim.pid, int) else "unknown"
        worktree = claim.worktree.name if claim.worktree is not None else "unknown"
        holders.append(f"pid {pid} in {worktree}")
    return ", ".join(holders) or "unknown holder"


def _append_receipt_summary(
    lines: list[str],
    *,
    selected: int,
    skipped: int,
    reclaimed: int,
    failures: int,
    remaining: list[tuple[int, Path, str]],
) -> None:
    lines.append(
        f"summary: selected={selected} skipped={skipped} "
        f"reclaimed={reclaimed} failures={failures}"
    )
    lines.append("remaining largest candidates:")
    ordered = sorted(remaining, key=lambda item: (-item[0], str(item[1])))[:10]
    if not ordered:
        lines.append("  none")
    for size, path, reason in ordered:
        lines.append(f"  {path}: {size} bytes ({reason})")


def _playwright_evidence_local_safety_reason(
    path: Path,
    root: Path,
    common: Path,
    mount_check: MountCheck,
) -> str:
    """Re-establish the local portion of the evidence safety predicate."""
    web = root / "web"
    archive = web / PLAYWRIGHT_EVIDENCE_DIRECTORY
    allowed = {web / "test-results", web / "playwright-report", archive}
    if path not in allowed and path.parent != archive:
        return "outside Playwright evidence surface"
    if path == archive and not path.exists():
        return ""
    candidate = Candidate(path, "test_artifacts", 0, path.is_dir())
    return _candidate_safety_reason(candidate, root, common, set(), mount_check)


def _playwright_evidence_candidates(root: Path) -> tuple[Path, Path, Path]:
    """Return the two live Playwright outputs and retained-failure root."""
    web = root / "web"
    return (
        web / "test-results",
        web / "playwright-report",
        web / PLAYWRIGHT_EVIDENCE_DIRECTORY,
    )


def _playwright_archive_time_ns(entry: Path) -> int | None:
    """Return the creation time recorded in a lifecycle-owned archive name."""
    prefix = "failed-"
    if not entry.name.startswith(prefix):
        return None
    try:
        timestamp = int(entry.name.removeprefix(prefix))
    except ValueError:
        return None
    return timestamp if timestamp >= 0 else None


def _playwright_archive_destination(archive: Path) -> Path:
    """Return an unused lifecycle-owned archive path for one failed run.

    `time.time_ns()` is not a uniqueness guarantee: two failures inside the same
    nanosecond, or a directory that already carries the generated name, made
    `copytree` raise and lost the failure it was archiving.
    """
    for suffix in range(PLAYWRIGHT_ARCHIVE_NAME_ATTEMPTS):
        stamp = time.time_ns()
        name = f"failed-{stamp}" if suffix == 0 else f"failed-{stamp + suffix}"
        destination = archive / name
        if not destination.exists():
            return destination
    raise FileExistsError(
        f"could not allocate an unused archive name under {archive}"
    )


def _playwright_retention_actions(
    archive: Path, max_age_seconds: int
) -> tuple[list[tuple[str, Path, tuple[Path, ...]]], list[tuple[Path, str]]]:
    """Select retained evidence from its explicit archive creation time."""
    entries = (
        [
            entry
            for entry in archive.iterdir()
            if entry.is_dir() and not entry.is_symlink()
        ]
        if archive.is_dir()
        else []
    )
    selected_at = time.time_ns()
    # The archive name is ordinary worktree-local state: a stray directory, or a
    # clock stepped backwards by NTP, can carry a timestamp in the future. Such a
    # name would hold "newest" indefinitely and, under a zero budget, get the
    # genuine newest run pruned instead. Refuse to read it as a time at all;
    # unrecognized archives fall into the retained bucket, never the pruned one.
    creation_times = {
        entry: timestamp
        for entry in entries
        if (timestamp := _playwright_archive_time_ns(entry)) is not None
        and timestamp <= selected_at
    }
    newest = max(creation_times, key=creation_times.__getitem__, default=None)
    cutoff = selected_at - max_age_seconds * 1_000_000_000
    actions: list[tuple[str, Path, tuple[Path, ...]]] = []
    retained: list[tuple[Path, str]] = []
    for entry in entries:
        pin = entry / PLAYWRIGHT_EVIDENCE_PIN
        if entry not in creation_times:
            retained.append((entry, "unrecognized archive time"))
        elif entry == newest:
            retained.append((entry, "newest failed run"))
        elif pin.exists() and not pin.is_symlink():
            retained.append((entry, "pinned"))
        elif creation_times[entry] >= cutoff:
            retained.append((entry, "within age budget"))
        else:
            actions.append(("prune", entry, (entry,)))
    return actions, retained


def manage_playwright_failure_evidence(
    repository: Path,
    *,
    gate_returncode: int,
    max_age_seconds: int,
    runner: Runner = _run,
    mount_check: MountCheck | None = None,
) -> PlaywrightEvidenceResult:
    """Retain bounded failed runs and remove artifacts from successful gates."""
    _, common, worktrees, _ = discover_worktrees(repository, runner)
    root = _containing_worktree(repository, worktrees)
    if root is None or common is None:
        return PlaywrightEvidenceResult(
            refused=True,
            receipt=("warning: skipped Playwright evidence: current worktree is not registered",),
        )
    common = common.resolve()
    effective_mount_check = mount_check or _default_mount_check()
    test_results, playwright_report, archive = _playwright_evidence_candidates(root)
    initial_actions: list[tuple[str, Path, tuple[Path, ...]]] = []
    if gate_returncode:
        if test_results.exists():
            initial_actions.append(("archive", test_results, (test_results, archive)))
    else:
        for path in (test_results, playwright_report):
            if not path.exists():
                continue
            initial_actions.append(("clean", path, (path,)))

    def recheck_local(paths: tuple[Path, ...]) -> str:
        """Recheck the local predicate after selection and before mutation."""
        fresh_mount_check = mount_check or _default_mount_check()
        for item in paths:
            reason = _playwright_evidence_local_safety_reason(
                item, root, common, fresh_mount_check
            )
            if reason:
                return reason
        return ""

    archived = cleaned = pruned = skipped = failures = reclaimed = selected = 0
    lines: list[str] = []

    def apply_actions(actions: list[tuple[str, Path, tuple[Path, ...]]]) -> None:
        """Apply one selected lifecycle phase after its safety proof."""
        nonlocal archived, cleaned, failures, pruned, reclaimed, selected, skipped
        if not actions:
            return
        candidates: dict[Path, Candidate] = {}
        reasons: dict[Path, str] = {}
        for _, _, paths in actions:
            for path in paths:
                if path in candidates:
                    continue
                candidate = Candidate(path, "test_artifacts", 0, path.is_dir())
                candidates[path] = candidate
                reasons[path] = _playwright_evidence_local_safety_reason(
                    path, root, common, effective_mount_check
                )
        git_candidates = [
            candidate for path, candidate in candidates.items() if not reasons[path]
        ]
        git_status = _mark_git_status(root, git_candidates, runner)
        if git_status.error:
            for path in candidates:
                if not reasons[path]:
                    reasons[path] = git_status.error
        else:
            for path, candidate in candidates.items():
                if reasons[path]:
                    continue
                relative = candidate.canonical_path.relative_to(root)
                if _is_tracked(relative, git_status.tracked):
                    reasons[path] = "tracked"
                elif relative not in git_status.ignored:
                    reasons[path] = "not ignored"

        for kind, path, paths in actions:
            reason = next((reasons[item] for item in paths if reasons[item]), "")
            if reason:
                lines.append(f"warning: skipped {path}: {reason}")
                skipped += 1
                continue
            bytes_, _ = _tree_size(path, [])
            lines.append(f"selected {path}: {bytes_} bytes")
            selected += 1
            reason = recheck_local(paths)
            if reason:
                lines.append(f"aborted {path}: safety changed: {reason}")
                skipped += 1
                continue
            try:
                if kind == "archive":
                    archive.mkdir(parents=True, exist_ok=True)
                    reason = recheck_local(paths)
                    if reason:
                        lines.append(f"aborted {path}: safety changed: {reason}")
                        skipped += 1
                        continue
                    destination = _playwright_archive_destination(archive)
                    shutil.copytree(path, destination)
                    lines.append(f"archived {path}: {bytes_} bytes to {destination}")
                    archived += 1
                else:
                    shutil.rmtree(path)
                    verb = "cleaned" if kind == "clean" else "pruned"
                    lines.append(f"{verb} {path}: {bytes_} bytes")
                    if kind == "clean":
                        cleaned += 1
                    else:
                        pruned += 1
                    reclaimed += bytes_
            except OSError as exc:
                lines.append(f"failure {path}: {exc}")
                failures += 1

    apply_actions(initial_actions)
    retention_actions, retained = _playwright_retention_actions(
        archive, max_age_seconds
    )
    for path, reason in retained:
        lines.append(f"warning: skipped {path}: {reason}")
        skipped += 1
    apply_actions(retention_actions)
    _append_receipt_summary(
        lines,
        selected=selected,
        skipped=skipped,
        reclaimed=reclaimed,
        failures=failures,
        remaining=[],
    )
    return PlaywrightEvidenceResult(
        archived=archived,
        cleaned=cleaned,
        pruned=pruned,
        skipped=skipped,
        receipt=tuple(lines),
    )


def clean(
    repository: Path,
    categories: set[str],
    *,
    apply: bool,
    include_dependencies: bool,
    protected: set[Path],
    force_without_lease: bool = False,
    selected: list[Path] | None = None,
    runner: Runner = _run,
    mount_check: MountCheck | None = None,
) -> tuple[int, list[str]]:
    """Print a receipt; delete only candidates passing every safety guard."""
    lines = ["clean receipt: apply" if apply else "clean receipt: dry run"]
    selected_count = 0
    skipped_count = 0
    reclaimed = 0
    failure_count = 0
    remaining: list[tuple[int, Path, str]] = []
    unsupported = categories - CLEANABLE_CATEGORIES
    if unsupported:
        names = ", ".join(sorted(unsupported))
        lines.append(f"refusing cleanup: unsupported categories: {names}")
        _append_receipt_summary(
            lines,
            selected=0,
            skipped=0,
            reclaimed=0,
            failures=0,
            remaining=[],
        )
        return 2, lines
    if selected is not None and len(selected) > 1:
        lines.append("refusing deletion: select exactly one worktree")
        _append_receipt_summary(
            lines,
            selected=0,
            skipped=0,
            reclaimed=0,
            failures=0,
            remaining=[],
        )
        return 2, lines
    effective_mount_check = mount_check or _default_mount_check()
    # Scan is safely repository-wide by default. Clean deliberately is not: an
    # unqualified mutation may inspect only the worktree containing the invocation.
    invocation_root = _current_worktree(repository, runner)
    clean_selection = selected or [invocation_root]
    report = scan(
        repository,
        clean_selection,
        runner,
        include_ignore_status=False,
        include_import_resolution=False,
    )
    lines.extend(f"warning: {warning}" for warning in report["warnings"])
    common_value = report["git_common_dir"]
    if not isinstance(common_value, str) or not common_value:
        lines.append("refusing cleanup: git common directory unavailable")
        _append_receipt_summary(
            lines,
            selected=0,
            skipped=0,
            reclaimed=0,
            failures=0,
            remaining=[],
        )
        return 2, lines
    if apply and not categories:
        lines.append("refusing deletion: select at least one category")
        _append_receipt_summary(
            lines,
            selected=0,
            skipped=0,
            reclaimed=0,
            failures=0,
            remaining=[],
        )
        return 2, lines
    if "dependencies" in categories and not include_dependencies:
        lines.append("refusing dependency cleanup without --include-dependencies")
        _append_receipt_summary(
            lines,
            selected=0,
            skipped=0,
            reclaimed=0,
            failures=0,
            remaining=[],
        )
        return 2, lines
    if "dependencies" in categories:
        protected.add(invocation_root)
    common = Path(common_value).resolve()
    exclusive_claim: Any | None = None
    try:
        if apply:
            lease = _coordination_lease_module()
            try:
                exclusive_claim = lease.acquire_exclusive(common, clean_selection[0].resolve())
            except lease.ClaimContentionError as error:
                lines.append("WORKTREE_LEASE_DID_NOT_RUN")
                lines.append(
                    "clean did not run: live activity claim held by "
                    f"{_claim_holder_names(error.claims)}"
                )
                _append_receipt_summary(
                    lines,
                    selected=0,
                    skipped=0,
                    reclaimed=0,
                    failures=0,
                    remaining=[],
                )
                return 75, lines
            except lease.ClaimStoreUnavailable:
                if not force_without_lease:
                    # A participant unable to publish cannot trust its read of this store.
                    lines.append("WORKTREE_LEASE_DID_NOT_RUN")
                    lines.append(
                        "clean did not run: exclusive claim store is unavailable; "
                        "use --force-without-lease only when cleanup must proceed"
                    )
                    _append_receipt_summary(
                        lines,
                        selected=0,
                        skipped=0,
                        reclaimed=0,
                        failures=0,
                        remaining=[],
                    )
                    return 75, lines
                lines.append(
                    "warning: proceeding without an exclusive claim because "
                    "--force-without-lease was supplied"
                )
            else:
                lines.append("lease: acquired exclusive claim")
        in_use_locations = _installed_distribution_locations()
        for worktree_data in report["worktrees"]:
            root = Path(worktree_data["path"]).resolve()
            candidates = [
                _candidate_from_data(data)
                for data in worktree_data["candidates"]
                if data["category"] in categories
            ]
            if root in protected:
                lines.append(f"skipped protected worktree: {root}")
                lines.extend(
                    f"warning: skipped {candidate.path}: protected worktree"
                    for candidate in candidates
                )
                skipped_count += len(candidates)
                remaining.extend(
                    (candidate.bytes, candidate.path, "protected worktree")
                    for candidate in candidates
                )
                continue
            decisions: list[tuple[Candidate, Path | None, str]] = []
            git_candidates: list[Candidate] = []
            for candidate in candidates:
                reason = _candidate_safety_reason(
                    candidate,
                    root,
                    common,
                    protected,
                    effective_mount_check,
                )
                if reason:
                    decisions.append((candidate, None, reason))
                    continue
                relative = candidate.canonical_path.relative_to(root)
                git_candidates.append(candidate)
                decisions.append((candidate, relative, ""))
            git_status = _mark_git_status(root, git_candidates, runner)
            if git_status.error:
                lines.append(f"warning: skipped worktree {root}: {git_status.error}")
                lines.extend(
                    f"warning: skipped {candidate.path}: {git_status.error}"
                    for candidate in candidates
                )
                skipped_count += len(candidates)
                remaining.extend(
                    (candidate.bytes, candidate.path, git_status.error)
                    for candidate in candidates
                )
                continue
            for candidate, relative, reason in decisions:
                if not reason and relative is not None:
                    if _is_tracked(relative, git_status.tracked):
                        reason = "tracked"
                    elif relative not in git_status.ignored:
                        reason = "not ignored"
                    elif _is_in_use(candidate, in_use_locations):
                        reason = "installed distribution resolves into target"
                if reason:
                    lines.append(f"warning: skipped {candidate.path}: {reason}")
                    skipped_count += 1
                    remaining.append((candidate.bytes, candidate.path, reason))
                    continue
                lines.append(f"selected {candidate.path}: {candidate.bytes} bytes")
                selected_count += 1
                if not apply:
                    remaining.append((candidate.bytes, candidate.path, "dry run"))
                    continue
                predelete_mount_check = mount_check or _default_mount_check()
                recheck_reason = _candidate_safety_reason(
                    candidate,
                    root,
                    common,
                    protected,
                    predelete_mount_check,
                )
                if recheck_reason:
                    lines.append(
                        f"aborted {candidate.path}: safety changed: {recheck_reason}"
                    )
                    skipped_count += 1
                    remaining.append(
                        (candidate.bytes, candidate.path, recheck_reason)
                    )
                    continue
                try:
                    if candidate.is_dir:
                        shutil.rmtree(candidate.path)
                    else:
                        candidate.path.unlink()
                except OSError as exc:
                    lines.append(f"failure {candidate.path}: {exc}")
                    failure_count += 1
                    remaining.append((candidate.bytes, candidate.path, str(exc)))
                else:
                    reclaimed += candidate.bytes
        _append_receipt_summary(
            lines,
            selected=selected_count,
            skipped=skipped_count,
            reclaimed=reclaimed,
            failures=failure_count,
            remaining=remaining,
        )
        return 0, lines
    finally:
        if exclusive_claim is not None:
            try:
                exclusive_claim.release()
            finally:
                lines.append("lease: released exclusive claim")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan_parser = subparsers.add_parser(
        "scan",
        help="Inspect all registered worktrees without changing them.",
    )
    scan_parser.add_argument(
        "--worktree",
        type=Path,
        help="Inspect only this registered worktree.",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit deterministic JSON instead of the human report.",
    )
    clean_parser = subparsers.add_parser(
        "clean",
        help="Preview or apply cleanup in exactly one worktree.",
    )
    clean_parser.add_argument(
        "--worktree",
        type=Path,
        help="Clean this registered worktree instead of the current one.",
    )
    clean_parser.add_argument(
        "--protect-worktree",
        action="append",
        type=Path,
        default=[],
        help=(
            "Protect a worktree; repeatable and supplemented by "
            "WORKTREE_HYGIENE_PROTECT_WORKTREES."
        ),
    )
    clean_parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete selected safe candidates; otherwise print a dry run.",
    )
    clean_parser.add_argument(
        "--force-without-lease",
        action="store_true",
        help=(
            "Proceed only when the exclusive claim store is unavailable; this may "
            "delete while an uncoordinated peer is active."
        ),
    )
    clean_parser.add_argument(
        "--include-dependencies",
        action="store_true",
        help="Acknowledge expensive dependency cleanup.",
    )
    clean_parser.add_argument(
        "--dependencies",
        action="store_true",
        help="Select local dependency directories.",
    )
    clean_parser.add_argument(
        "--generated",
        action="store_true",
        help="Select reproducible generated output.",
    )
    clean_parser.add_argument(
        "--test-artifacts",
        action="store_true",
        help="Select test, coverage, lint, and bytecode artifacts.",
    )
    for command in ("after-create", "before-run", "after-run", "before-remove"):
        hook_parser = subparsers.add_parser(
            command,
            help="Report optional worktree lifecycle state without removing worktrees.",
        )
        if command == "before-remove":
            hook_parser.add_argument(
                "--protect-worktree",
                action="append",
                type=Path,
                default=[],
                help=(
                    "Protect a worktree; repeatable and supplemented by "
                    "WORKTREE_HYGIENE_PROTECT_WORKTREES."
                ),
            )
    args = parser.parse_args(argv)
    if args.command == "scan":
        selected = [args.worktree] if args.worktree else None
        report = scan(Path.cwd(), selected)
        if args.json:
            print(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        else:
            print(_human(report))
        return 0
    if args.command in {"after-create", "before-run", "after-run", "before-remove"}:
        protected = _protected_paths(
            str(path) for path in getattr(args, "protect_worktree", [])
        )
        result = lifecycle_hook(args.command, Path.cwd(), protected=protected)
        print("\n".join(result.lines))
        return result.code
    categories = {
        category for category in CATEGORIES if getattr(args, category)
    }
    protected = _protected_paths(
        str(path) for path in args.protect_worktree
    )
    current = Path.cwd().resolve()
    code, lines = clean(
        current,
        categories,
        apply=args.apply,
        include_dependencies=args.include_dependencies,
        protected=protected,
        force_without_lease=args.force_without_lease,
        selected=[args.worktree] if args.worktree else None,
    )
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
