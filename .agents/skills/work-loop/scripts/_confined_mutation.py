"""_confined_mutation — atomic file-mutation primitives for the work-loop skill.

Builds on the work-loop skill's local ``file_safety.py`` copy (left unchanged).

Read operations remain safe with the path-check fallback that ``file_safety``
already provides.  Mutation operations (create, append, atomic-replace) run in
one of three host modes, chosen by ``_host_mode()``:

  descriptor    the descriptor-bound parent walk that
                ``file_safety._supports_descriptor_walk`` gates; race-free.
  path-checked  no descriptor walk, but ``os.lstat`` reports reparse-point
                attributes (Windows).  Each write is checked by path before the
                bytes are committed and again after; a difference seen after the
                commit raises ``denied-rollback-failed`` and the caller treats
                the state as unknown.  One race stays open: an ancestor swapped
                for a link between the last pre-write check and the commit call
                can redirect that one write.  ``race_free_mutation()`` is False
                here so callers can refuse untrusted work.
  unsafe        neither; mutations refuse with ``denied-unsafe-host`` before
                staging any bytes.

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
from collections.abc import Callable
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
    "race_free_mutation",
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


def _host_mode() -> str:
    """The write mode this host supports; the one host-capability point.

    ``"descriptor"`` when each path component can be bound to a directory
    descriptor, ``"path-checked"`` when it cannot but ``os.lstat`` reports
    reparse-point attributes, otherwise ``"unsafe"``.  Makes no filesystem call.
    """
    if _fs._supports_descriptor_walk():
        return "descriptor"
    if hasattr(os.stat_result, "st_file_attributes"):
        return "path-checked"
    return "unsafe"


def race_free_mutation() -> bool:
    """Whether this host's mutations are free of the path-check race window."""
    return _host_mode() == "descriptor"


def _prepare(
    root: Path, path: Path, content: bytes, max_bytes: int | None
) -> tuple[str, Path, str]:
    """Choose the host mode once for a call, and return ``(mode, root, relative)``.

    Refuses before staging any bytes on a host with neither descriptor walking
    nor reparse attributes.  Reads remain safe with the path-check fallback;
    mutations do not there because any path component between the confinement
    check and the OS write is a race window.
    """
    mode = _host_mode()
    if mode == "path-checked":
        root, relative = _pc_relative(root, path)
    elif mode == "descriptor":
        relative = _validate_relative_path(root, path)
    else:
        raise MutationDenied(
            "denied-unsafe-host",
            "confined mutation requires descriptor-bound parent walk; "
            "reads remain safe on this host but mutations are not",
        )
    _check_size(content, max_bytes, relative=relative)
    return mode, root, relative


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
            # parent_fd is guaranteed non-None: the descriptor mode was chosen.
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
                    # Link succeeded; remove the temp name so the target has
                    # exactly one hard link.  If the removal fails, roll back
                    # by unlinking the target and refusing with a stable code,
                    # so a successful create never leaves a multiply-linked file.
                    committed = True
                    try:
                        os.unlink(temp_name, dir_fd=parent_fd)
                    except OSError as _unlink_exc:
                        # Rollback: remove the target so no two-link file is
                        # left reachable at the intended path.  Set
                        # committed=False so the outer handler can attempt to
                        # clean the temp name by absolute path as a last resort.
                        with contextlib.suppress(OSError):
                            os.unlink(leaf, dir_fd=parent_fd)
                        committed = False
                        raise MutationDenied(
                            "denied-rollback-failed",
                            f"exclusive create cleanup failed for {relative}: {_unlink_exc}",
                        ) from _unlink_exc
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


# ── Path-checked mode ─────────────────────────────────────────────────────────
#
# Used only where descriptor walking is unavailable and ``os.lstat`` reports
# reparse points.  Every check is by path, so each one narrows the window in
# which a same-user process could swap an ancestor, and none closes it; the
# checks after the commit detect a swap that is still in place, but cannot
# undo the write.

# Test seam, settable only in-process: called with the target path just before
# each commit call (the replace, the link, or the append's write).
_PRE_COMMIT_HOOK: Callable[[Path], None] | None = None

_REPARSE_POINT: Final[int] = 0x400
_O_BINARY: Final[int] = getattr(os, "O_BINARY", 0)
_RESERVED_DEVICES: Final[frozenset[str]] = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"COM{n}" for n in range(1, 10)}
    | {f"LPT{n}" for n in range(1, 10)}
)


def _violation(message: str) -> MutationDenied:
    return MutationDenied("denied-path-violation", message)


def _rollback_failed(message: str) -> MutationDenied:
    return MutationDenied("denied-rollback-failed", message)


_INVALID_NAME_CHARS: Final[frozenset[str]] = frozenset('<>:"|?*')


def _check_component(part: str, whole: str) -> None:
    """Refuse one path component that is a Windows stream, device, or invalid name."""
    if part in ("", ".", ".."):
        raise _violation(f"empty or dot segment in {whole!r}")
    if part.startswith("\\\\"):
        raise _violation(f"UNC or device path form refused: {whole!r}")
    if ":" in part:
        raise _violation(f"stream or drive form refused: {whole!r}")
    if _INVALID_NAME_CHARS & set(part) or any(ord(c) < 32 for c in part):
        raise _violation(f"invalid character in a name refused: {whole!r}")
    if part.endswith((".", " ")):
        raise _violation(f"trailing dot or space refused: {whole!r}")
    if part.split(".", 1)[0].rstrip(" ").upper() in _RESERVED_DEVICES:
        raise _violation(f"reserved device name refused: {whole!r}")


def _lexical_target(root: Path, path: Path) -> None:
    """Check the target's components below the root, with no filesystem call.

    When the target's text sits under the root's text those are the
    ``relative_to`` parts.  Otherwise (a root given in another form, such as a
    short-name alias) they are the target's components after the longest
    case-folded prefix it shares with the root; a target that shares none and
    starts with two backslashes is a UNC, device, or extended-length form and
    is refused.  The root's own components are never judged.
    """
    try:
        below = list(path.relative_to(root).parts)
    except ValueError:
        have, given = root.parts, path.parts
        shared = 0
        while (
            shared < min(len(have), len(given))
            and have[shared].casefold() == given[shared].casefold()
        ):
            shared += 1
        if shared == 0 and os.fspath(path).startswith("\\\\"):
            raise _violation(
                f"UNC or device path form refused: {os.fspath(path)!r}"
            ) from None
        below = list(given[shared:] if shared or not path.anchor else given[1:])
    for part in below:
        _check_component(part, os.fspath(path))


def _lexical_parts(relative: str) -> list[str]:
    """Split a root-relative path into components, refusing Windows-special forms.

    Runs before any filesystem call.  Refuses a UNC, device, or extended-length
    prefix, an absolute or drive-relative form, a stream (``:``), a reserved
    device name with or without an extension, and a trailing dot or space.
    """
    if relative.startswith("\\\\"):
        raise _violation(f"UNC or device path form refused: {relative!r}")
    parts = relative.replace("\\", "/").split("/")
    for part in parts:
        _check_component(part, relative)
    return parts


def _is_link(info: os.stat_result) -> bool:
    """A symlink or a reparse point (junction, mount point, or Windows symlink)."""
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & _REPARSE_POINT
    )


def _identity(info: os.stat_result) -> tuple[int, int]:
    return (info.st_dev, info.st_ino)


def _lstat(path: Path, *, relative: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise MutationDenied(
            "denied-staging-failed", f"cannot stat {relative}: {exc}"
        ) from exc


def _record_chain(
    root: Path, directories: list[str], *, relative: str
) -> list[tuple[Path, tuple[int, int]]]:
    """Record ``(path, identity)`` for the root and each ancestor, refusing links."""
    chain: list[tuple[Path, tuple[int, int]]] = []
    current = root
    for name in [None, *directories]:
        if name is not None:
            current = current / name
        try:
            info = _lstat(current, relative=relative)
        except FileNotFoundError:
            raise MutationDenied(
                "denied-staging-failed", f"directory does not exist for {relative}"
            ) from None
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise _violation(f"link or non-directory in the path of {relative}")
        chain.append((current, _identity(info)))
    return chain


def _recheck_chain(chain: list[tuple[Path, tuple[int, int]]], *, relative: str) -> None:
    """After the write: every recorded directory must be the same, unlinked directory."""
    for path, recorded in chain:
        try:
            info = os.lstat(path)
        except OSError as exc:
            raise _rollback_failed(
                f"a directory changed during the write to {relative}: {exc}"
            ) from exc
        if _is_link(info) or _identity(info) != recorded:
            raise _rollback_failed(f"a directory changed during the write to {relative}")


def _inside(root: Path, candidate: Path) -> bool:
    base = os.path.normcase(os.path.realpath(root))
    other = os.path.normcase(os.path.realpath(candidate))
    return other == base or other.startswith(base.rstrip(os.sep) + os.sep)


def _regular_clean(info: os.stat_result) -> bool:
    return stat.S_ISREG(info.st_mode) and not _is_link(info) and info.st_nlink == 1


def _check_existing_target(target: Path, *, relative: str) -> os.stat_result | None:
    """The target's lstat, or None when absent; refuses a link, special file, or extra link."""
    try:
        info = _lstat(target, relative=relative)
    except FileNotFoundError:
        return None
    if not _regular_clean(info):
        raise _violation(f"target is a link, special file, or multiply linked: {relative}")
    return info


def _pc_relative(root: Path, path: Path) -> tuple[Path, str]:
    """The effective root and the target's root-relative path.

    The target's own text is never resolved, so a link inside it stays visible to
    the directory checks. Only when the text does not sit under *root* as given
    is *root* resolved, which lets a root passed as a short-name alias match a
    target written in long form. A root that is itself a link is refused.
    """
    _lexical_target(root, path)
    try:
        return root, path.relative_to(root).as_posix()
    except ValueError:
        pass
    outside = _violation(f"path {str(path)!r} is outside declared root {str(root)!r}")
    try:
        info = os.lstat(root)
    except OSError:
        raise outside from None
    if _is_link(info):
        raise _violation(f"root is a link: {str(root)!r}")
    resolved = Path(os.path.realpath(root))
    try:
        return resolved, path.relative_to(resolved).as_posix()
    except ValueError:
        raise outside from None


def _remove_if_ours(path: Path, created: tuple[int, int] | None) -> None:
    """Remove *path* only while it is still the file this call created."""
    if created is None:
        return
    with contextlib.suppress(OSError):
        info = os.lstat(path)
        if _identity(info) == created and stat.S_ISREG(info.st_mode):
            path.unlink()


def _call_hook(target: Path) -> None:
    if _PRE_COMMIT_HOOK is not None:
        _PRE_COMMIT_HOOK(target)


def _pc_create_or_replace(
    root: Path, path: Path, content: bytes, *, relative: str, exclusive: bool
) -> None:
    """Stage, then commit, with the checks before the first byte and after the commit."""
    parts = _lexical_parts(relative)
    chain = _record_chain(root, parts[:-1], relative=relative)
    parent = chain[-1][0]
    target = parent / parts[-1]
    if not _inside(root, parent):
        raise _violation(f"parent resolves outside the root: {relative}")
    existing = _check_existing_target(target, relative=relative)
    if existing is not None and exclusive:
        raise MutationDenied("denied-already-exists", f"file already exists: {relative}")

    stage = parent / f".wl-tmp-{secrets.token_hex(8)}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_BINARY | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(stage, flags, 0o600)
    except OSError as exc:
        raise MutationDenied(
            "denied-staging-failed", f"cannot create temp file for {relative}: {exc}"
        ) from exc

    committed = False
    stage_identity: tuple[int, int] = (0, 0)
    created: tuple[int, int] | None = None
    try:
        try:
            opened = os.fstat(fd)
            created = _identity(opened)
            by_path = os.lstat(stage)
            if (
                _identity(opened) != _identity(by_path)
                or not _regular_clean(opened)
                or not _regular_clean(by_path)
                or not _inside(root, stage)
            ):
                raise _violation(f"staging file failed its checks for {relative}")
            stage_identity = _identity(opened)
            _write_all(fd, content, relative=relative)
            try:
                os.fsync(fd)
            except OSError:
                raise MutationDenied(
                    "denied-staging-failed", f"fsync failed for temp file of {relative}"
                ) from None
        except OSError as exc:
            raise MutationDenied("denied-staging-failed", str(exc)) from exc
        finally:
            with contextlib.suppress(OSError):
                os.close(fd)

        _call_hook(target)
        if exclusive:
            try:
                os.link(stage, target)
            except FileExistsError:
                raise MutationDenied(
                    "denied-already-exists", f"file already exists: {relative}"
                ) from None
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed", f"exclusive create failed for {relative}: {exc}"
                ) from exc
            committed = True
            try:
                stage.unlink()
            except OSError as exc:
                _remove_if_ours(target, stage_identity)
                raise _rollback_failed(
                    f"exclusive create cleanup failed for {relative}: {exc}"
                ) from exc
        else:
            try:
                stage.replace(target)
            except OSError as exc:
                raise MutationDenied(
                    "denied-staging-failed", f"replace failed for {relative}: {exc}"
                ) from exc
            committed = True
    except BaseException:
        if not committed:
            _remove_if_ours(stage, created)
        raise

    try:
        after = os.lstat(target)
    except OSError as exc:
        raise _rollback_failed(f"target not readable after commit: {relative}: {exc}") from exc
    if not _regular_clean(after) or _identity(after) != stage_identity:
        raise _rollback_failed(f"target differs from the file written: {relative}")
    _recheck_chain(chain, relative=relative)


def _pc_append(root: Path, path: Path, content: bytes, *, relative: str) -> None:
    """Append by path, checking the open file against the path before and after."""
    parts = _lexical_parts(relative)
    chain = _record_chain(root, parts[:-1], relative=relative)
    parent = chain[-1][0]
    target = parent / parts[-1]
    if not _inside(root, parent):
        raise _violation(f"parent resolves outside the root: {relative}")
    before = _check_existing_target(target, relative=relative)
    if before is None:
        raise MutationDenied("denied-not-found", f"target does not exist: {relative}")

    flags = os.O_WRONLY | os.O_APPEND | _O_BINARY
    for flag in ("O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, flag, 0)
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        raise MutationDenied(
            "denied-staging-failed", f"cannot open for append {relative}: {exc}"
        ) from exc
    try:
        try:
            opened = os.fstat(fd)
        except OSError as exc:
            raise MutationDenied(
                "denied-staging-failed", f"fstat after open failed {relative}: {exc}"
            ) from exc
        if not _regular_clean(opened) or _identity(opened) != _identity(before):
            raise _violation(f"identity changed between stat and open: {relative}")
        if not _inside(root, target):
            raise _violation(f"target resolves outside the root: {relative}")
        pre_len = opened.st_size

        _call_hook(target)
        try:
            _write_all(fd, content, relative=relative)
        except MutationDenied:
            _rollback_append(fd, pre_len, relative)
            raise
        try:
            os.fsync(fd)
        except OSError:
            _rollback_append(fd, pre_len, relative)
            raise MutationDenied(
                "denied-staging-failed", f"fsync failed for append to {relative}"
            ) from None

        try:
            now = os.lstat(target)
        except OSError as exc:
            raise _rollback_failed(f"target not readable after append: {relative}: {exc}") from exc
        if _is_link(now) or _identity(now) != _identity(opened):
            raise _rollback_failed(f"target differs from the file appended to: {relative}")
        _recheck_chain(chain, relative=relative)
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)


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
    mode, root, relative = _prepare(root, path, content, max_bytes)
    if mode == "path-checked":
        _pc_create_or_replace(root, path, content, relative=relative, exclusive=True)
        return
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
    mode, root, relative = _prepare(root, path, content, max_bytes)
    if mode == "path-checked":
        _pc_append(root, path, content, relative=relative)
        return

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
    mode, root, relative = _prepare(root, path, content, max_bytes)
    if mode == "path-checked":
        _pc_create_or_replace(root, path, content, relative=relative, exclusive=False)
        return
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
