"""_subject_source — legacy worktree subject-source provider for delivery-subject.v1.

Implements the legacy-worktree-snapshot subject-source.v1 port.

Parity invariant: the legacy provider and the runtime-neutral projector emit
identical canonical manifests, product fingerprints, exclusions, spec identity,
and plan provenance for the same acknowledged product tree.

Exclusion invariant: ambient, ignored, untracked, excluded, unreadable,
link-like, non-regular, unacknowledged, and drifting paths cannot enter a
delivery subject; an unresolved traversal bound emits no partial subject.

The acknowledged boundary is the cohort's ``approved_spec_hash`` and
``approved_plan_hash`` fields.  Drift is detected by comparing those stored
hashes with the current spec and plan digests (using ``sha256_canonical_contract``
from ``_loop_guards`` — the canonical implementation is not duplicated here)
and by checking for uncommitted tracked-file changes (``git status``).

Traversal limits are the canonical numeric values for this module.  Test code
must import them from here rather than repeating the numbers.

All Git subprocess calls go through ``_process_safety.launch_safe_process``.
All file reads for hashing go through ``_hash_file_with_budget``, a local helper
that opens each file without following its final-component symlink, reads the byte
count from the open descriptor via ``os.fstat``, and refuses before reading past
the declared byte budget.

Standard library only.  Loads sibling modules by path using the
``importlib.util.spec_from_file_location`` pattern.
Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import secrets
import shutil
import stat
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    # Exception
    "SubjectRefused",
    # Schema constant
    "SUPPORTED_SCHEMA_VERSION",
    # Traversal limits (tests must read these constants, not duplicate the numbers)
    "MAX_PRODUCT_PATHS",
    "MAX_PRODUCT_BYTES",
    "MAX_TRAVERSAL_S",
    # Provider identity constants
    "LEGACY_PROVIDER_IDENTITY",
    "LEGACY_PROJECTION_VERSION",
    # Denial codes
    "DENIAL_CODES",
    # Public entry points
    "project_legacy_subject",
    # Parity validation (delegates to _subject_projection.validate_subject_dict)
    "validate_subject_dict",
]

# ── Traversal limits ──────────────────────────────────────────────────────────
#
# Canonical numeric values for this module.
# Tests must read these constants and must not reproduce the numbers elsewhere.

MAX_PRODUCT_PATHS: Final[int] = 100_000
MAX_PRODUCT_BYTES: Final[int] = 10 * 1024 * 1024 * 1024  # 10 GiB
MAX_TRAVERSAL_S: Final[int] = 60

# ── Provider identity ─────────────────────────────────────────────────────────

LEGACY_PROVIDER_IDENTITY: Final[str] = "legacy-worktree-snapshot"
LEGACY_PROJECTION_VERSION: Final[str] = "1.0"

SUPPORTED_SCHEMA_VERSION: Final[int] = 1

# ── Stable denial codes ───────────────────────────────────────────────────────

DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-git-unavailable",
    "denied-git-call-failed",
    "denied-spec-drift",
    "denied-plan-drift",
    "denied-product-drift",
    "denied-path-bound-exceeded",
    "denied-byte-bound-exceeded",
    "denied-time-bound-exceeded",
    "denied-path-violation",
    "denied-unreadable-path",
    "denied-no-approved-boundary",
})

# ── Scripts directory ─────────────────────────────────────────────────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent

# ── Lazy sibling module cache ─────────────────────────────────────────────────

_file_safety_module: ModuleType | None = None
_proc_safety_module: ModuleType | None = None
_guards_module: ModuleType | None = None
_projection_module: ModuleType | None = None


def _load_sibling(name: str, filename: str) -> ModuleType:
    """Load a sibling module by path, unregistered in sys.modules.

    Uses the ``importlib.util.spec_from_file_location`` pattern established in
    ``_confined_mutation.py`` and ``_policy_import.py``.  ``sys.modules[name]``
    is set temporarily so dataclass resolution works on Python 3.13 (where
    ``dataclasses._is_type`` looks up the module via ``sys.modules``).
    """
    path = _SCRIPTS_DIR / filename
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"cannot locate {filename}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        ispec = importlib.util.spec_from_file_location(name, str(path))
        if ispec is None or ispec.loader is None:
            raise ImportError(f"no import spec for {path}")
        mod = importlib.util.module_from_spec(ispec)
        sys.modules[name] = mod
        try:
            ispec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(name, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


def _file_safety() -> ModuleType:
    """Lazily load the work-loop skill's local file_safety.py."""
    global _file_safety_module
    if _file_safety_module is None:
        _file_safety_module = _load_sibling("_ss_file_safety", "file_safety.py")
    return _file_safety_module


def _proc_safety() -> ModuleType:
    """Lazily load _process_safety.py."""
    global _proc_safety_module
    if _proc_safety_module is None:
        _proc_safety_module = _load_sibling("_ss_proc_safety", "_process_safety.py")
    return _proc_safety_module


def _guards() -> ModuleType:
    """Lazily load _loop_guards.py for sha256_canonical_contract."""
    global _guards_module
    if _guards_module is None:
        _guards_module = _load_sibling("_ss_loop_guards", "_loop_guards.py")
    return _guards_module


def _projection() -> ModuleType:
    """Lazily load _subject_projection.py for pure projection."""
    global _projection_module
    if _projection_module is None:
        _projection_module = _load_sibling("_ss_subject_proj", "_subject_projection.py")
    return _projection_module


# ── Exception ─────────────────────────────────────────────────────────────────


class SubjectRefused(Exception):
    """A subject-projection was refused with a stable denial code.

    ``denial_code`` is one of the strings in ``DENIAL_CODES`` and carries no
    sensitive payload bytes, excerpts, or content-derived hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ── Git executable helpers ────────────────────────────────────────────────────


def _find_git() -> str:
    """Return the absolute path to the git executable.

    Raises SubjectRefused when git is not found on PATH.
    """
    candidate = shutil.which("git")
    if candidate is None:
        raise SubjectRefused("denied-git-unavailable", "git executable not found on PATH")
    return str(Path(candidate).resolve())


def _hash_binary_file(path: str) -> str:
    """SHA-256 hex digest of a binary file (for executable identity pinning)."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_file_with_budget(
    repo_root: Path,
    abs_path: Path,
    remaining_budget: int,
) -> tuple[int, str]:
    """Open *abs_path* without following symlinks and hash it within the byte budget.

    Opens the file through the skill's confined regular-file opener, which walks
    every parent directory without following links and refuses a link, a
    non-regular file, or a file replaced while opening, and reads the file size
    from the open descriptor via ``os.fstat`` before any content is read.  The
    size is never obtained via a separate ``stat()`` call — a file whose size cannot
    be established from the descriptor is refused, not admitted with a synthetic zero
    size.  The file is refused before reading any content when its size would exceed
    *remaining_budget*.

    Args:
        repo_root: Absolute path to the repository root (confinement boundary).
        abs_path: Absolute path to the file to hash; must resolve within *repo_root*.
        remaining_budget: Maximum bytes still permitted before the traversal byte
            budget is exhausted.  A file whose ``fstat`` size exceeds this value is
            refused without reading its content.

    Returns:
        A ``(file_size, sha256_hexdigest)`` pair.  *file_size* comes from ``os.fstat``
        on the open descriptor; *sha256_hexdigest* is the hex-encoded SHA-256 of the
        file content streamed in 1 MiB chunks.

    Raises:
        SubjectRefused: ``"denied-path-violation"`` when the path is outside
            *repo_root*, any component is a link, or the file is not a regular
            file or changed while opening.
        SubjectRefused: ``"denied-unreadable-path"`` when the file cannot be
            opened or its size cannot be established from the descriptor.
        SubjectRefused: ``"denied-byte-bound-exceeded"`` when the ``fstat`` size
            exceeds *remaining_budget*, or the file grows past the budget during a
            streaming read.
    """
    fs = _file_safety()
    try:
        rel = abs_path.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise SubjectRefused(
            "denied-path-violation", f"path {abs_path!r} is outside repo root"
        ) from exc
    try:
        with fs._open_confined_regular_file(  # noqa: SLF001 - this skill's own helper
            repo_root, abs_path, max_bytes=remaining_budget
        ) as handle:
            file_size = os.fstat(handle.fileno()).st_size
            # Stream and hash the content, capped against the budget in case the
            # file grows during the read (e.g. an active log file tracked by git).
            digest = hashlib.sha256()
            bytes_read = 0
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                bytes_read += len(chunk)
                if bytes_read > remaining_budget:
                    raise SubjectRefused(
                        "denied-byte-bound-exceeded",
                        f"path {rel!r} grew past byte budget during streaming read",
                    )
                digest.update(chunk)
    except fs.BoundExceeded as exc:
        raise SubjectRefused(
            "denied-byte-bound-exceeded",
            f"path {rel!r} would exceed remaining byte budget ({remaining_budget} B)",
        ) from exc
    except fs.UnsafeContentError as exc:
        raise SubjectRefused(
            "denied-path-violation", f"path {rel!r} cannot be opened safely"
        ) from exc
    except OSError as exc:
        raise SubjectRefused(
            "denied-unreadable-path",
            f"path {rel!r} cannot be read or its size cannot be established",
        ) from exc
    return file_size, digest.hexdigest()


# ── Git subprocess via _process_safety ───────────────────────────────────────


def _run_git(
    repo_root: Path,
    argv: list[str],
    audit_sink: object,
    *,
    timeout_s: int = 30,
    output_bytes: int = 32 * 1024 * 1024,
) -> bytes:
    """Run a git subcommand in *repo_root* via ``_process_safety.launch_safe_process``.

    Passes ``HOME`` and ``PATH`` from the current environment so git can read
    its configuration.  Returns stdout bytes on success.
    Raises ``SubjectRefused`` on any failure.
    """
    try:
        git_path = _find_git()
        git_hash = _hash_binary_file(git_path)
    except SubjectRefused:
        raise
    except OSError as exc:
        raise SubjectRefused(
            "denied-git-unavailable",
            f"cannot stat git executable: {exc}",
        ) from exc

    # Build the environment: only HOME and PATH, no ambient inheritance.
    passthrough: dict[str, str] = {}
    home = os.environ.get("HOME", "")
    path_env = os.environ.get("PATH", "")
    if home:
        passthrough["HOME"] = home
    if path_env:
        passthrough["PATH"] = path_env

    spec_dict: dict = {
        "schema_version": 1,
        "executable": git_path,
        "executable_identity": git_hash,
        "argv": argv,
        "grant_id": secrets.token_hex(16),
        "cwd": str(repo_root),
        "environment_allowlist": sorted(passthrough.keys()),
        "stdin_mode": "closed",
        "process_tree_timeout_s": timeout_s,
        "output_bound_bytes": output_bytes,
    }

    ps = _proc_safety()
    try:
        result = ps.launch_safe_process(
            spec_dict,
            cwd_roots=(str(repo_root),),
            env_values=passthrough,
            audit_sink=audit_sink,
        )
    except ps.ProcessDenied as exc:  # type: ignore[attr-defined]
        raise SubjectRefused(
            "denied-git-call-failed",
            f"git call denied: {exc.denial_code}",
        ) from exc

    if result.exit_code != 0:
        verb = argv[0] if argv else ""
        raise SubjectRefused(
            "denied-git-call-failed",
            f"git {verb!r} exited {result.exit_code}",
        )
    return result.stdout_redacted


# ── Acknowledged boundary checks ─────────────────────────────────────────────


def _check_approved_digests(
    spec_path: Path,
    plan_path: Path,
    approved_spec_hash: str,
    approved_plan_hash: str,
) -> None:
    """Raise SubjectRefused when spec or plan hashes deviate from the approved boundary.

    Calls ``sha256_canonical_contract`` from ``_loop_guards``; the canonical
    normalization lives in one place and is not duplicated here.
    """
    g = _guards()
    try:
        current_spec = g.sha256_canonical_contract(spec_path)
    except Exception as exc:
        raise SubjectRefused(
            "denied-spec-drift",
            f"cannot compute spec digest: {exc}",
        ) from exc
    try:
        current_plan = g.sha256_canonical_contract(plan_path)
    except Exception as exc:
        raise SubjectRefused(
            "denied-plan-drift",
            f"cannot compute plan digest: {exc}",
        ) from exc
    if current_spec != approved_spec_hash:
        raise SubjectRefused(
            "denied-spec-drift",
            "spec digest does not match the approved boundary; refusing projection",
        )
    if current_plan != approved_plan_hash:
        raise SubjectRefused(
            "denied-plan-drift",
            "plan digest does not match the approved boundary; refusing projection",
        )


def _check_product_drift(repo_root: Path, audit_sink: object) -> None:
    """Raise SubjectRefused when any tracked file has uncommitted changes.

    Uses ``git status --porcelain --untracked-files=no`` which lists only tracked
    file changes (not untracked files).  Any output indicates drift.
    """
    raw = _run_git(
        repo_root,
        ["status", "--porcelain", "--untracked-files=no"],
        audit_sink,
        timeout_s=30,
        output_bytes=4 * 1024 * 1024,
    )
    text = raw.decode("utf-8", errors="replace").strip()
    if text:
        raise SubjectRefused(
            "denied-product-drift",
            "tracked product files have uncommitted changes; "
            "legacy-worktree-snapshot requires an acknowledged (clean) result",
        )


# ── Tracked-file enumeration ──────────────────────────────────────────────────


def _list_tracked_files(repo_root: Path, audit_sink: object) -> list[str]:
    """Return tracked file paths relative to *repo_root*.

    Uses ``git ls-files --cached -z`` (NUL-delimited) to avoid quoting edge
    cases.  Raises ``SubjectRefused`` on any git failure or non-UTF-8 path.
    """
    # Generous per-path budget: MAX_PRODUCT_PATHS paths × 512 bytes/path.
    raw = _run_git(
        repo_root,
        ["ls-files", "--cached", "-z"],
        audit_sink,
        timeout_s=MAX_TRAVERSAL_S,
        output_bytes=MAX_PRODUCT_PATHS * 512,
    )
    if not raw:
        return []
    paths: list[str] = []
    for entry in raw.split(b"\x00"):
        if not entry:
            continue
        try:
            paths.append(entry.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise SubjectRefused(
                "denied-path-violation",
                f"non-UTF-8 path in git ls-files output: {exc}",
            ) from exc
    return paths


def _get_head_sha(repo_root: Path, audit_sink: object) -> str:
    """Return the HEAD commit SHA for *repo_root*."""
    raw = _run_git(
        repo_root,
        ["rev-parse", "HEAD"],
        audit_sink,
        timeout_s=10,
        output_bytes=100,
    )
    return raw.decode("utf-8", errors="replace").strip()


# ── Path exclusion ────────────────────────────────────────────────────────────


def _is_excluded(
    rel_path: str,
    spec_dir_prefix: str,
    extra_prefixes: frozenset[str],
) -> bool:
    """Return True when *rel_path* is excluded from the product manifest.

    Always excludes paths that start with ``.git/`` or equal ``.git``.
    Excludes paths under the spec directory (spec enters acceptance identity
    through its fingerprint, not by its file paths).
    Excludes caller-supplied extra prefixes.
    """
    # Always exclude .git
    if rel_path == ".git" or rel_path.startswith(".git/"):
        return True
    # Exclude spec directory (and all files within it)
    if rel_path.startswith(spec_dir_prefix):
        return True
    # Caller-supplied exclusions (strip trailing slash before prefix matching)
    for prefix in extra_prefixes:
        p = prefix.rstrip("/")
        if rel_path == p or rel_path.startswith(p + "/"):
            return True
    return False


# ── Main entry point ──────────────────────────────────────────────────────────


def project_legacy_subject(
    *,
    repo_root: Path,
    spec_dir: Path,
    approved_spec_hash: str,
    approved_plan_hash: str,
    audit_sink: object,
    subject_id: str,
    evidence_policy_ref: str,
    extra_exclusions: tuple[str, ...] = (),
    task_projection_revision: str | None = None,
) -> dict:
    """Project a ``delivery-subject.v1`` record from the legacy worktree.

    Sequence:

    1. Validate the approved boundary inputs are non-empty.
    2. Verify the current spec and plan digests match ``approved_spec_hash``
       and ``approved_plan_hash`` respectively (using ``sha256_canonical_contract``
       from ``_loop_guards``).
    3. Detect uncommitted tracked-file changes (``git status``); refuse on drift.
    4. List tracked files (``git ls-files --cached``).
    5. Get the HEAD commit SHA as ``result_ref`` and ``base_ref``.
    6. For each tracked file: check exclusions, check confinement, compute
       SHA-256, accumulate byte count, check all traversal limits.
    7. Build a sorted canonical manifest (path → sha256 tuple pairs).
    8. Call ``_subject_projection.project_delivery_subject`` with the manifest
       and metadata to produce the final record.

    Raises ``SubjectRefused`` (with a stable denial code) on any failure.
    Never emits a partial manifest.
    """
    # Step 1 — validate approved boundary inputs
    if not approved_spec_hash or not approved_plan_hash:
        raise SubjectRefused(
            "denied-no-approved-boundary",
            "approved_spec_hash and approved_plan_hash must be non-empty; "
            "run approve-plan before projecting a legacy subject",
        )

    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"

    # Step 2 — verify acknowledged boundary (raises on mismatch)
    _check_approved_digests(spec_path, plan_path, approved_spec_hash, approved_plan_hash)

    # Step 3 — detect uncommitted product drift (raises on dirty working tree)
    _check_product_drift(repo_root, audit_sink)

    # Step 4 — list tracked files
    tracked = _list_tracked_files(repo_root, audit_sink)

    # Step 5 — get HEAD SHA for product references
    head_sha = _get_head_sha(repo_root, audit_sink)

    # Compute spec directory prefix for exclusion matching
    try:
        spec_dir_rel = spec_dir.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise SubjectRefused(
            "denied-path-violation",
            f"spec_dir is outside repo_root: {exc}",
        ) from exc
    spec_dir_prefix = spec_dir_rel.rstrip("/") + "/"

    extra_set: frozenset[str] = frozenset(extra_exclusions)

    # Build the effective exclusions list for the delivery-subject record
    effective_exclusions: tuple[str, ...] = (".git", spec_dir_rel) + tuple(
        sorted(extra_exclusions)
    )

    # Step 6 — traverse tracked files, apply exclusions, enforce limits
    manifest_pairs: list[tuple[str, str]] = []
    total_bytes = 0
    start_time = time.monotonic()

    for rel_path in tracked:
        # Time-bound check (before any per-file I/O)
        elapsed = time.monotonic() - start_time
        if elapsed >= MAX_TRAVERSAL_S:
            raise SubjectRefused(
                "denied-time-bound-exceeded",
                f"product traversal exceeded {MAX_TRAVERSAL_S}s limit "
                "(refusing before partial manifest)",
            )

        # Skip excluded paths
        if _is_excluded(rel_path, spec_dir_prefix, extra_set):
            continue

        # Path count limit (checked before hashing)
        if len(manifest_pairs) >= MAX_PRODUCT_PATHS:
            raise SubjectRefused(
                "denied-path-bound-exceeded",
                f"product traversal exceeded {MAX_PRODUCT_PATHS} path limit "
                "(refusing before partial manifest)",
            )

        abs_path = repo_root / rel_path

        # Open without following symlinks, read size from fstat, check budget,
        # then hash.  _hash_file_with_budget refuses before reading any content
        # when the file size would exceed the remaining budget.
        remaining = MAX_PRODUCT_BYTES - total_bytes
        file_size, file_hash = _hash_file_with_budget(repo_root, abs_path, remaining)
        total_bytes += file_size

        manifest_pairs.append((rel_path, file_hash))

    # Step 7 — build sorted canonical manifest
    sorted_manifest: tuple[tuple[str, str], ...] = tuple(sorted(manifest_pairs))

    # Step 8 — produce delivery-subject.v1 via the pure projector
    proj = _projection()
    spec_path_rel = spec_dir_rel + "/spec.md"
    return proj.project_delivery_subject(
        subject_id=subject_id,
        base_ref=head_sha,
        result_ref=head_sha,
        spec_path=spec_path_rel,
        spec_fingerprint=approved_spec_hash,
        evidence_policy_ref=evidence_policy_ref,
        exclusions=effective_exclusions,
        provider=LEGACY_PROVIDER_IDENTITY,
        projection_version=LEGACY_PROJECTION_VERSION,
        manifest_pairs=sorted_manifest,
        task_projection_revision=task_projection_revision,
        task_projection_hash=approved_plan_hash,
    )


# ── Parity validation ─────────────────────────────────────────────────────────


def validate_subject_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``delivery-subject.v1`` contract in code.

    Delegates to ``_subject_projection.validate_subject_dict`` to ensure both
    modules agree on the schema invariants.  Returns ``(True, "ok")`` on success
    or ``(False, denial_code)`` on failure.
    """
    return _projection().validate_subject_dict(record)
