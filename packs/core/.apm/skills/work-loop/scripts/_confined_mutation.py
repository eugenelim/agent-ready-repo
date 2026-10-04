"""_confined_mutation — atomic file-mutation primitives for the work-loop skill.

Builds on the work-loop skill's local ``file_safety.py`` copy (left unchanged).

Read operations remain safe with the path-check fallback that ``file_safety``
already provides.  Mutation operations (create, append, atomic-replace) require
the descriptor-bound parent-walk that ``file_safety._supports_descriptor_walk``
gates: without it, any path component between the confinement check and the
OS write could be replaced by an adversary, so mutations refuse with the stable
denial code ``denied-unsafe-host`` before staging any bytes.

Denial codes (stable, no payload bytes):
  denied-unsafe-host      — descriptor walk not supported; mutation unsafe.
  denied-path-violation   — path outside root, dot-segment, link, or special file.
  denied-size-exceeded    — content exceeds the declared byte limit.
  denied-staging-failed   — temp creation, write, or rename failed.
  denied-not-found        — target must exist but does not (append, replace).
  denied-already-exists   — target must not exist but does (create).

Standard library only. No third-party imports, no packaging, no installation.
Python 3.11+.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import secrets
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "MutationDenied",
    "confined_create",
    "confined_append",
    "confined_atomic_replace",
    "DENIAL_CODES",
    "validate_confined_file_dict",
]

# Stable denial codes — callers may match against these strings.
DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-unsafe-host",
    "denied-path-violation",
    "denied-size-exceeded",
    "denied-staging-failed",
    "denied-not-found",
    "denied-already-exists",
    "denied-rollback-failed",
})

# ── Sibling file_safety loader ────────────────────────────────────────────────
#
# The local file_safety.py is loaded once at module import and stored as ``_fs``.
# Tests may monkeypatch ``_fs._supports_descriptor_walk`` to simulate the
# fallback host condition without skipping.

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent


def _load_file_safety() -> ModuleType:
    """Load the work-loop skill's local file_safety.py as an unregistered module."""
    fs_path = _SCRIPTS_DIR / "file_safety.py"
    try:
        info = os.lstat(fs_path)
    except OSError as exc:
        raise ImportError(f"cannot locate file_safety.py: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError("file_safety.py is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("_wl_file_safety", str(fs_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {fs_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module
    finally:
        sys.dont_write_bytecode = previous


# Module-level reference; tests may monkeypatch attributes on this object.
_fs: ModuleType = _load_file_safety()


# ── Exception ─────────────────────────────────────────────────────────────────


class MutationDenied(Exception):
    """A confined mutation was refused with a stable denial code.

    ``denial_code`` is one of the strings in ``DENIAL_CODES`` and carries no
    sensitive payload bytes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ── Internal helpers ──────────────────────────────────────────────────────────


def _require_descriptor_walk() -> None:
    """Refuse before staging any bytes if descriptor walk is unavailable.

    Reads remain safe with path-check fallback; mutations do not because any
    path component between confinement check and OS write is a race window.
    """
    if not _fs._supports_descriptor_walk():
        raise MutationDenied(
            "denied-unsafe-host",
            "confined mutation requires descriptor-bound parent walk; "
            "reads remain safe on this host but mutations are not",
        )


def _check_size(content: bytes, max_bytes: int | None, *, relative: str) -> None:
    """Refuse before staging when content exceeds the declared byte cap."""
    if max_bytes is not None and len(content) > max_bytes:
        raise MutationDenied(
            "denied-size-exceeded",
            f"content ({len(content)} bytes) exceeds limit ({max_bytes}) for {relative}",
        )


def _validate_relative_path(root: Path, path: Path) -> str:
    """Return the root-relative POSIX path, or raise MutationDenied."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        raise MutationDenied(
            "denied-path-violation",
            f"path {str(path)!r} is outside declared root {str(root)!r}",
        ) from None


def _write_all(fd: int, content: bytes, *, relative: str) -> None:
    """Write all bytes to an open descriptor, raising MutationDenied on error."""
    view = memoryview(content)
    pos = 0
    while pos < len(content):
        try:
            n = os.write(fd, view[pos:])
        except OSError as exc:
            raise MutationDenied(
                "denied-staging-failed", f"write failed for {relative}: {exc}"
            ) from exc
        if n == 0:
            raise MutationDenied(
                "denied-staging-failed", f"write returned 0 for {relative}"
            )
        pos += n


def _rollback_append(fd: int, pre_len: int, relative: str) -> None:
    """Truncate *fd* back to *pre_len* bytes after a failed append.

    If truncation fails, the file is in an unknown state. Callers must fail
    closed — refusing further appends until the store is reopened — rather
    than layering new bytes onto unknown content.

    Raises:
        MutationDenied: with ``denied-rollback-failed`` when truncation fails.
    """
    try:
        os.ftruncate(fd, pre_len)
    except OSError as exc:
        raise MutationDenied(
            "denied-rollback-failed",
            f"partial write and rollback truncation failed for {relative}: {exc}",
        ) from exc


def _try_unlink_by_dir_fd(name: str, dir_fd: int) -> None:
    """Best-effort unlink of a temp file using the parent dir descriptor."""
    with contextlib.suppress(OSError):
        os.unlink(name, dir_fd=dir_fd)


def _do_temp_write_rename(
    root: Path,
    path: Path,
    content: bytes,
    *,
    relative: str,
    exclusive: bool,
) -> None:
    """Stage *content* to a temp file in the same directory and rename atomically.

    On any failure the temp file is removed (best-effort) and the original
    file is left intact.  ``exclusive=True`` refuses if the target already
    exists.
    """
    temp_name = f".wl-tmp-{secrets.token_hex(8)}"
    write_flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_EXCL
    for flag in ("O_CLOEXEC",):
        if hasattr(os, flag):
            write_flags |= getattr(os, flag)

    temp_fd = -1
    committed = False

    try:
        with _fs._open_confined_parent(root, path, relative=relative) as (parent_fd, leaf):
            # parent_fd is guaranteed non-None: _require_descriptor_walk() passed.
            if parent_fd is None:
                # Defensive: should be unreachable; the descriptor-walk gate caught it.
                raise MutationDenied(
                    "denied-unsafe-host",
                    "unexpected path-check fallback inside atomic mutation",
                )

            # Exclusive-create check: refuse if target already exists.
            # Non-exclusive (replace): if target exists it must be a clean regular
            # file — refuse links (symlinks, hard links), reparse points, and
            # special files.  This matches file_safety._validate_regular_file_stat
            # and prevents replacing a symlink, a FIFO, or a multiply-linked file.
            try:
                existing_stat = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                # Target exists.
                if exclusive:
                    raise MutationDenied(
                        "denied-already-exists",
                        f"file already exists: {relative}",
                    )
                # Non-exclusive: validate the existing target is a safe regular file.
                try:
                    _fs._validate_regular_file_stat(existing_stat, relative)
                except _fs.UnsafeContentError as exc:
                    raise MutationDenied("denied-path-violation", str(exc)) from exc
            except FileNotFoundError:
                if exclusive:
                    pass  # target absent — proceed with create.
                # Non-exclusive: target absent is OK; we'll create it via rename.
            except MutationDenied:
                raise
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed",
                    f"cannot stat target {relative}: {exc}",
                ) from exc

            # Create the temp file exclusively in the same directory.
            try:
                temp_fd = os.open(temp_name, write_flags, 0o600, dir_fd=parent_fd)
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed",
                    f"cannot create temp file for {relative}: {exc}",
                ) from exc

            # Write content and flush.
            try:
                _write_all(temp_fd, content, relative=relative)
                try:
                    os.fsync(temp_fd)
                except OSError:
                    # fsync failure is treated as a staging failure.
                    raise MutationDenied(
                        "denied-staging-failed",
                        f"fsync failed for temp file of {relative}",
                    ) from None
            except MutationDenied:
                _try_unlink_by_dir_fd(temp_name, parent_fd)
                raise
            finally:
                if temp_fd >= 0:
                    with contextlib.suppress(OSError):
                        os.close(temp_fd)
                    temp_fd = -1

            # Commit the staged content to the target name.
            if exclusive:
                # Use os.link so that a target created between the earlier
                # existence check and this point causes FileExistsError
                # atomically, instead of being silently replaced by rename.
                # OSError with EPERM/ENOTSUP/EXDEV means the filesystem does
                # not support hard links; fail closed rather than fall back to
                # rename, which would violate the exclusive-create contract.
                try:
                    os.link(temp_name, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                except FileExistsError:
                    _try_unlink_by_dir_fd(temp_name, parent_fd)
                    raise MutationDenied(
                        "denied-already-exists",
                        f"file already exists: {relative}",
                    ) from None
                except OSError as exc:
                    _try_unlink_by_dir_fd(temp_name, parent_fd)
                    raise MutationDenied(
                        "denied-staging-failed",
                        f"exclusive create failed for {relative}: {exc}",
                    ) from exc
                else:
                    # Link succeeded: the content is at leaf; remove the temp name.
                    committed = True
                    _try_unlink_by_dir_fd(temp_name, parent_fd)
            else:
                # Non-exclusive atomic replace: rename replaces an existing target.
                try:
                    os.rename(temp_name, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                    committed = True
                except OSError as exc:
                    _try_unlink_by_dir_fd(temp_name, parent_fd)
                    raise MutationDenied(
                        "denied-staging-failed",
                        f"rename failed for {relative}: {exc}",
                    ) from exc

    except MutationDenied:
        if not committed and temp_fd < 0:
            # temp_fd is already closed here; unlink by path as last resort.
            with contextlib.suppress(OSError):
                (path.parent / temp_name).unlink(missing_ok=True)
        raise
    except _fs.UnsafeContentError as exc:
        if not committed:
            with contextlib.suppress(OSError):
                (path.parent / temp_name).unlink(missing_ok=True)
        raise MutationDenied("denied-path-violation", str(exc)) from exc
    except OSError as exc:
        if not committed:
            with contextlib.suppress(OSError):
                (path.parent / temp_name).unlink(missing_ok=True)
        raise MutationDenied("denied-staging-failed", str(exc)) from exc
    finally:
        if temp_fd >= 0:
            with contextlib.suppress(OSError):
                os.close(temp_fd)


# ── Public API ────────────────────────────────────────────────────────────────


def confined_create(
    root: Path,
    path: Path,
    content: bytes,
    *,
    max_bytes: int | None = None,
) -> None:
    """Create a new confined file with *content*.

    Refuses if the target already exists.  Refuses before staging any bytes
    when the host cannot bind the parent directory to a descriptor.

    Args:
        root:      The canonical root directory; all paths are confined to it.
        path:      Absolute target path inside *root*.
        content:   Bytes to write.
        max_bytes: Optional byte ceiling; refusal is recorded before staging.

    Raises:
        MutationDenied: with a stable denial code on any refusal.
    """
    _require_descriptor_walk()
    relative = _validate_relative_path(root, path)
    _check_size(content, max_bytes, relative=relative)
    _do_temp_write_rename(root, path, content, relative=relative, exclusive=True)


def confined_append(
    root: Path,
    path: Path,
    content: bytes,
    *,
    max_bytes: int | None = None,
) -> None:
    """Append *content* to an existing confined file.

    Uses ``O_APPEND`` with identity verification to avoid a read-then-write
    race.  Refuses before staging any bytes when descriptor walk is unavailable.

    On a failed write, truncates the file back to its pre-append size so that
    no partial bytes remain (rollback).  If the rollback truncation itself
    fails, raises with ``denied-rollback-failed``; callers must treat the file
    as being in an unknown state and fail closed.

    On a successful write, fsyncs the file descriptor before returning so that
    the appended bytes are durable before the caller is notified.

    Args:
        root:      The canonical root directory.
        path:      Absolute target path inside *root*.
        content:   Bytes to append.
        max_bytes: Optional ceiling on the appended bytes (not the total file).

    Raises:
        MutationDenied: with a stable denial code on any refusal.
    """
    _require_descriptor_walk()
    relative = _validate_relative_path(root, path)
    _check_size(content, max_bytes, relative=relative)

    append_flags = os.O_WRONLY | os.O_APPEND
    for flag in ("O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        if hasattr(os, flag):
            append_flags |= getattr(os, flag)

    fd = -1
    try:
        with _fs._open_confined_parent(root, path, relative=relative) as (parent_fd, leaf):
            if parent_fd is None:
                raise MutationDenied(
                    "denied-unsafe-host",
                    "unexpected path-check fallback inside confined_append",
                )

            # Pre-open identity check: file must be a confined regular file.
            try:
                before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                raise MutationDenied(
                    "denied-not-found", f"target does not exist: {relative}"
                ) from None
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed", f"cannot stat target {relative}: {exc}"
                ) from exc
            try:
                _fs._validate_regular_file_stat(before, relative)
            except _fs.UnsafeContentError as exc:
                raise MutationDenied("denied-path-violation", str(exc)) from exc

            # Open for append.
            try:
                fd = os.open(leaf, append_flags, dir_fd=parent_fd)
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed", f"cannot open for append {relative}: {exc}"
                ) from exc

            # Post-open identity check.
            try:
                after = os.fstat(fd)
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed", f"fstat after open failed {relative}: {exc}"
                ) from exc
            try:
                _fs._validate_regular_file_stat(after, relative)
            except _fs.UnsafeContentError as exc:
                raise MutationDenied("denied-path-violation", str(exc)) from exc
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                raise MutationDenied(
                    "denied-path-violation",
                    f"identity changed between stat and open: {relative}",
                )

            # Record the pre-append file size for rollback on partial failure.
            try:
                pre_len = os.fstat(fd).st_size
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed",
                    f"fstat pre-append failed for {relative}: {exc}",
                ) from exc

            # Write all content; roll back to pre_len if the write fails.
            try:
                _write_all(fd, content, relative=relative)
            except MutationDenied:
                _rollback_append(fd, pre_len, relative)
                raise

            # Fsync before reporting success so appended bytes are durable.
            try:
                os.fsync(fd)
            except OSError:
                _rollback_append(fd, pre_len, relative)
                raise MutationDenied(
                    "denied-staging-failed",
                    f"fsync failed for append to {relative}",
                ) from None

    except MutationDenied:
        raise
    except _fs.UnsafeContentError as exc:
        raise MutationDenied("denied-path-violation", str(exc)) from exc
    except OSError as exc:
        raise MutationDenied("denied-staging-failed", str(exc)) from exc
    finally:
        if fd >= 0:
            with contextlib.suppress(OSError):
                os.close(fd)


def confined_atomic_replace(
    root: Path,
    path: Path,
    content: bytes,
    *,
    max_bytes: int | None = None,
) -> None:
    """Atomically replace a confined file with *content*.

    Stages to a temporary file in the same directory, then renames.  On any
    failure the original file is intact and the temp file is removed.  Refuses
    before staging any bytes when descriptor walk is unavailable.

    Args:
        root:      The canonical root directory.
        path:      Absolute target path inside *root*.
        content:   Replacement bytes.
        max_bytes: Optional byte ceiling; refusal is recorded before staging.

    Raises:
        MutationDenied: with a stable denial code on any refusal.
    """
    _require_descriptor_walk()
    relative = _validate_relative_path(root, path)
    _check_size(content, max_bytes, relative=relative)
    _do_temp_write_rename(root, path, content, relative=relative, exclusive=False)


# ── In-code schema validation ─────────────────────────────────────────────────

_REQUIRED_CONFINED_FILE_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "canonical_root",
    "relative_path",
})

_ALLOWED_CONFINED_FILE_KEYS: Final[frozenset[str]] = _REQUIRED_CONFINED_FILE_KEYS


def validate_confined_file_dict(d: dict) -> tuple[bool, str]:
    """Validate a confined-file.v1 record dict in code.

    Checks schema_version, required fields, and absence of unknown
    authority-shaped fields.  Does not import jsonschema at runtime.

    Returns:
        (True, "ok") when the record is schema-valid.
        (False, denial_code) when the record is invalid; denial_code is one of:
          denied-unknown-schema-version — unknown or wrong schema_version.
          denied-missing-required-field — a required field is absent.
          denied-unknown-authority-field — an authority-shaped field not in the schema.
    """
    if not isinstance(d, dict):
        return False, "denied-missing-required-field"

    version = d.get("schema_version")
    if not isinstance(version, int) or version != 1:
        return False, "denied-unknown-schema-version"

    missing = _REQUIRED_CONFINED_FILE_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    # confined-file.v1 is closed: additionalProperties = false.
    unknown = set(d.keys()) - _ALLOWED_CONFINED_FILE_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    return True, "ok"
