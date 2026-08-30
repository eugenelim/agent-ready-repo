"""No-follow filesystem primitives for committed build projections."""

from __future__ import annotations

import contextlib
import errno
import json
import os
import secrets
import shutil
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Literal

from agentbundle.safety import _is_reparse_point as _safety_is_reparse_point
from agentbundle.safety import _secure_dir_fd_available as _safety_secure_dir_fd_available
from agentbundle.safety import _write_all as _safety_write_all


class ProjectionTypeError(OSError):
    """A projected target exists but is not a regular file."""


MetadataPolicy = Literal["mode", "stat"]
_MAX_IN_PLACE_BYTES = 64 * 1024 * 1024


def render_diagnostic_path(path: Path) -> str:
    """Render an untrusted path reversibly on exactly one log line."""
    return json.dumps(path.as_posix(), ensure_ascii=True)


def _secure_dir_fd_available() -> bool:
    """Re-exported from ``agentbundle.safety`` — see that module for the rule.

    Kept as a module-level name so tests can monkeypatch it here.
    """
    return _safety_secure_dir_fd_available()


def _validate_relative(relative: Path) -> None:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"projection path must stay relative to its base: {relative}")


_is_reparse_point = _safety_is_reparse_point


def _validate_fallback_path(
    base: Path,
    relative: Path,
    *,
    allow_missing_leaf: bool,
) -> None:
    """Refuse links, junctions, and escapes when descriptor walks are absent."""
    _validate_relative(relative)
    base_resolved = base.resolve(strict=True)
    current = base
    for part in relative.parts:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            if allow_missing_leaf:
                return
            raise
        if stat.S_ISLNK(current_stat.st_mode) or _is_reparse_point(current_stat):
            raise ProjectionTypeError("path contains a link or reparse point")
        try:
            current.resolve(strict=True).relative_to(base_resolved)
        except ValueError:
            raise ProjectionTypeError("path escapes the projection root") from None


def ensure_directory_no_follow(base: Path, relative: Path) -> None:
    """Create/repair an owned directory tree without following links."""
    _validate_relative(relative)
    base.mkdir(parents=True, exist_ok=True)
    if not _secure_dir_fd_available():
        _validate_fallback_path(base, Path(), allow_missing_leaf=False)
        current = base
        for part in relative.parts:
            current /= part
            try:
                current_stat = current.lstat()
            except FileNotFoundError:
                current.mkdir()
                continue
            if _is_reparse_point(current_stat):
                raise ProjectionTypeError("path contains a reparse point")
            if stat.S_ISDIR(current_stat.st_mode):
                continue
            current.unlink()
            current.mkdir()
        return

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(
        os, "O_CLOEXEC", 0
    )
    base_fd = os.open(base, flags & ~os.O_NOFOLLOW)
    current_fd = base_fd
    try:
        for part in relative.parts:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except FileNotFoundError:
                os.mkdir(part, dir_fd=current_fd)
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except NotADirectoryError:
                os.unlink(part, dir_fd=current_fd)
                os.mkdir(part, dir_fd=current_fd)
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except OSError as exc:
                if exc.errno != errno.ELOOP:
                    raise
                os.unlink(part, dir_fd=current_fd)
                os.mkdir(part, dir_fd=current_fd)
                next_fd = os.open(part, flags, dir_fd=current_fd)
            if current_fd != base_fd:
                os.close(current_fd)
            current_fd = next_fd
    finally:
        if current_fd != base_fd:
            os.close(current_fd)
        os.close(base_fd)


@contextmanager
def open_directory_no_follow(base: Path, relative: Path) -> Iterator[int | None]:
    """Hold ``base/relative`` open while refusing symlink components.

    POSIX callers receive a directory descriptor suitable for ``dir_fd`` APIs.
    Windows callers receive ``None`` and retain path-based behavior; Windows
    symlink creation already requires separate privilege.
    """
    _validate_relative(relative)
    if not _secure_dir_fd_available():
        _validate_fallback_path(base, relative, allow_missing_leaf=False)
        yield None
        return

    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
    base_fd = os.open(base, flags)
    current_fd = base_fd
    try:
        for part in relative.parts:
            next_fd = os.open(
                part,
                flags | os.O_NOFOLLOW,
                dir_fd=current_fd,
            )
            if current_fd != base_fd:
                os.close(current_fd)
            current_fd = next_fd
        yield current_fd
    finally:
        if current_fd != base_fd:
            os.close(current_fd)
        os.close(base_fd)


_write_all = _safety_write_all


def _read_bounded(
    file_descriptor: int,
    *,
    maximum_bytes: int,
    target: Path,
    kind: str,
) -> bytes:
    """Read at most ``maximum_bytes`` from an open descriptor."""
    chunks: list[bytes] = []
    total = 0
    while chunk := os.read(
        file_descriptor,
        min(1024 * 1024, maximum_bytes - total + 1),
    ):
        chunks.append(chunk)
        total += len(chunk)
        if total > maximum_bytes:
            raise OSError(
                errno.EFBIG,
                f"{kind} {render_diagnostic_path(target)} exceeds "
                f"{maximum_bytes} bytes",
            )
    return b"".join(chunks)


def _read_source_no_follow(source: Path) -> tuple[bytes, os.stat_result]:
    """Read a bounded regular source while refusing final-component races."""
    source_stat = source.lstat()
    _require_regular(source_stat)
    if source_stat.st_size > _MAX_IN_PLACE_BYTES:
        raise OSError(
            errno.EFBIG,
            f"projection source {render_diagnostic_path(source)} exceeds "
            f"{_MAX_IN_PLACE_BYTES} bytes",
        )
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    source_fd = os.open(source, flags)
    with os.fdopen(source_fd, "rb", closefd=True) as handle:
        opened_stat = os.fstat(handle.fileno())
        _require_regular(opened_stat)
        if not _same_file_identity(source_stat, opened_stat):
            raise ProjectionTypeError("source changed identity while opening")
        content = _read_bounded(
            handle.fileno(),
            maximum_bytes=_MAX_IN_PLACE_BYTES,
            target=source,
            kind="projection source",
        )
        current_stat = source.lstat()
        _require_regular(current_stat)
        if not _same_file_identity(opened_stat, current_stat):
            raise ProjectionTypeError("source changed identity while reading")
        return content, opened_stat


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _require_regular(target_stat: os.stat_result) -> None:
    if stat.S_ISLNK(target_stat.st_mode):
        raise ProjectionTypeError("is a symlink")
    if _is_reparse_point(target_stat):
        raise ProjectionTypeError("is a reparse point")
    if not stat.S_ISREG(target_stat.st_mode):
        raise ProjectionTypeError("is not a regular file")


def _require_single_link_target(target_stat: os.stat_result) -> None:
    _require_regular(target_stat)
    if target_stat.st_nlink != 1:
        raise ProjectionTypeError("has multiple hard links")


def _replace_open_file(
    file_descriptor: int,
    content: bytes,
    original: bytes,
) -> None:
    """Replace bytes in place, restoring the original on a write failure."""
    try:
        os.lseek(file_descriptor, 0, os.SEEK_SET)
        os.ftruncate(file_descriptor, 0)
        _write_all(file_descriptor, content)
        os.ftruncate(file_descriptor, len(content))
    except Exception as write_error:
        try:
            os.lseek(file_descriptor, 0, os.SEEK_SET)
            os.ftruncate(file_descriptor, 0)
            _write_all(file_descriptor, original)
            os.ftruncate(file_descriptor, len(original))
        except Exception as restore_error:
            raise ExceptionGroup(
                "projection write failed and original bytes could not be restored",
                [write_error, restore_error],
            ) from write_error
        raise


def _replace_open_file_without_rollback(
    file_descriptor: int,
    content: bytes,
) -> None:
    """Replace bytes when the writable target cannot be read for rollback."""
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    os.ftruncate(file_descriptor, 0)
    _write_all(file_descriptor, content)
    os.ftruncate(file_descriptor, len(content))


def _overwrite_existing_no_follow(
    target: Path,
    content: bytes,
    *,
    base: Path,
    source_stat: os.stat_result | None = None,
    metadata: MetadataPolicy | None = None,
) -> bool:
    """Overwrite an existing regular target in place, or report it absent."""
    relative = target.relative_to(base)
    _validate_relative(relative)
    with open_directory_no_follow(base, relative.parent) as parent_fd:
        if parent_fd is None:
            _validate_fallback_path(base, relative, allow_missing_leaf=False)
            try:
                target_stat = target.lstat()
            except FileNotFoundError:
                return False
            _require_single_link_target(target_stat)
            flags = os.O_RDWR | getattr(os, "O_BINARY", 0)
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                target_fd = os.open(target, flags)
                can_rollback = True
            except PermissionError as read_write_error:
                write_flags = (flags & ~os.O_RDWR) | os.O_WRONLY
                try:
                    target_fd = os.open(target, write_flags)
                except PermissionError as write_error:
                    raise read_write_error from write_error
                except FileNotFoundError:
                    return False
                can_rollback = False
            except FileNotFoundError:
                return False
        else:
            try:
                target_stat = os.stat(
                    relative.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                return False
            _require_single_link_target(target_stat)
            try:
                target_fd = os.open(
                    relative.name,
                    os.O_RDWR | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
                    dir_fd=parent_fd,
                )
                can_rollback = True
            except PermissionError as read_write_error:
                try:
                    target_fd = os.open(
                        relative.name,
                        os.O_WRONLY
                        | os.O_NOFOLLOW
                        | getattr(os, "O_CLOEXEC", 0),
                        dir_fd=parent_fd,
                    )
                except PermissionError as write_error:
                    raise read_write_error from write_error
                except FileNotFoundError:
                    return False
                can_rollback = False
            except FileNotFoundError:
                return False

        with os.fdopen(target_fd, "rb+" if can_rollback else "wb", closefd=True) as handle:
            opened_stat = os.fstat(handle.fileno())
            _require_single_link_target(opened_stat)
            if opened_stat.st_size > _MAX_IN_PLACE_BYTES:
                raise OSError(
                    errno.EFBIG,
                    f"existing projection {render_diagnostic_path(target)} exceeds "
                    f"{_MAX_IN_PLACE_BYTES} bytes",
                )
            if not _same_file_identity(target_stat, opened_stat):
                raise ProjectionTypeError("changed identity while opening")
            original = None
            if can_rollback:
                original = _read_bounded(
                    handle.fileno(),
                    maximum_bytes=_MAX_IN_PLACE_BYTES,
                    target=target,
                    kind="existing projection",
                )
            try:
                if parent_fd is None:
                    _validate_fallback_path(
                        base,
                        relative,
                        allow_missing_leaf=False,
                    )
                    current_stat = target.lstat()
                else:
                    current_stat = os.stat(
                        relative.name,
                        dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
            except FileNotFoundError as exc:
                raise ProjectionTypeError("disappeared after opening") from exc
            _require_single_link_target(current_stat)
            if not _same_file_identity(opened_stat, current_stat):
                raise ProjectionTypeError("changed identity after opening")
            if original is None:
                _replace_open_file_without_rollback(handle.fileno(), content)
            else:
                _replace_open_file(handle.fileno(), content, original)
            if source_stat is not None:
                assert metadata is not None
                _apply_new_file_metadata(handle.fileno(), source_stat, metadata)
        return True


def _apply_new_file_metadata(
    file_descriptor: int,
    source_stat: os.stat_result,
    metadata: MetadataPolicy,
) -> None:
    """Apply source metadata while the newly-created file is still held."""
    if os.name != "posix":
        return
    os.fchmod(file_descriptor, stat.S_IMODE(source_stat.st_mode))
    if metadata == "stat":
        os.utime(
            file_descriptor,
            ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns),
        )


def _create_new_no_follow(
    target: Path,
    content: bytes,
    source_stat: os.stat_result,
    *,
    base: Path,
    metadata: MetadataPolicy,
) -> bool:
    """Create a target exclusively; return false if another writer won."""
    relative = target.relative_to(base)
    _validate_relative(relative)
    target_mode = stat.S_IMODE(source_stat.st_mode)
    with open_directory_no_follow(base, relative.parent) as parent_fd:
        if parent_fd is None:
            _validate_fallback_path(
                base,
                relative,
                allow_missing_leaf=True,
            )
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            if parent_fd is None:
                target_fd = os.open(target, flags, target_mode)
            else:
                target_fd = os.open(
                    relative.name,
                    flags,
                    target_mode,
                    dir_fd=parent_fd,
                )
        except FileExistsError:
            return False

        created_stat = os.fstat(target_fd)
        try:
            if parent_fd is None:
                _validate_fallback_path(
                    base,
                    relative,
                    allow_missing_leaf=False,
                )
                current_stat = target.lstat()
                if not _same_file_identity(created_stat, current_stat):
                    raise ProjectionTypeError("changed identity after creation")
            _write_all(target_fd, content)
            os.ftruncate(target_fd, len(content))
            _apply_new_file_metadata(
                target_fd,
                source_stat,
                metadata,
            )
        except Exception:
            try:
                if parent_fd is None:
                    current_stat = target.lstat()
                    if _same_file_identity(created_stat, current_stat):
                        target.unlink()
                else:
                    current_stat = os.stat(
                        relative.name,
                        dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                    if _same_file_identity(created_stat, current_stat):
                        os.unlink(relative.name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            raise
        finally:
            os.close(target_fd)
        return True


def copy_projected_file(
    source: Path,
    target: Path,
    *,
    base: Path,
    metadata: MetadataPolicy,
    preserve_existing_metadata: bool = False,
    transform: Callable[[bytes], bytes] | None = None,
) -> None:
    """Copy one projected file using the selected existing-target policy.

    Ordinary projections retain their historical ``shutil.copy`` / ``copy2``
    behavior. Self-host real writes update existing regular files through a
    held descriptor, preserving inode, ownership, and mode without attempting
    owner-only metadata operations. Newly-created files still inherit the
    source metadata selected by ``metadata``. ``transform`` changes the
    confined source bytes while retaining the source file's metadata policy.
    """
    relative = target.relative_to(base)
    _validate_relative(relative)
    if metadata not in ("mode", "stat"):
        raise ValueError(f"unsupported projection metadata policy: {metadata}")
    if transform is None and not preserve_existing_metadata:
        if not _secure_dir_fd_available():
            _validate_fallback_path(
                base,
                relative.parent,
                allow_missing_leaf=True,
            )
        ensure_directory_no_follow(base, relative.parent)
        copier = shutil.copy if metadata == "mode" else shutil.copy2
        copier(source, target, follow_symlinks=False)
        return

    source_bytes, source_stat = _read_source_no_follow(source)
    if transform is not None:
        source_bytes = transform(source_bytes)
    if not _secure_dir_fd_available():
        _validate_fallback_path(
            base,
            relative.parent,
            allow_missing_leaf=True,
        )
    ensure_directory_no_follow(base, relative.parent)
    while True:
        if _overwrite_existing_no_follow(
            target,
            source_bytes,
            base=base,
            source_stat=None if preserve_existing_metadata else source_stat,
            metadata=None if preserve_existing_metadata else metadata,
        ):
            return
        if _create_new_no_follow(
            target,
            source_bytes,
            source_stat,
            base=base,
            metadata=metadata,
        ):
            return


def copy_file_atomic_no_follow(
    source: Path,
    target: Path,
    *,
    base: Path,
    mode: int | None = None,
) -> None:
    """Atomically replace ``target`` without following target-side links."""
    relative = target.relative_to(base)
    _validate_relative(relative)
    source_bytes = source.read_bytes()
    target_mode = (
        stat.S_IMODE(source.stat().st_mode) if mode is None else stat.S_IMODE(mode)
    )

    with open_directory_no_follow(base, relative.parent) as parent_fd:
        if parent_fd is None:
            fd, temporary_name = tempfile.mkstemp(
                prefix=".agentbundle-projection-",
                dir=target.parent,
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(source_bytes)
                    if os.name == "posix":
                        os.fchmod(handle.fileno(), target_mode)
                temporary.replace(target)
            finally:
                with contextlib.suppress(FileNotFoundError):
                    temporary.unlink()
            return

        temporary_name = f".agentbundle-projection-{secrets.token_hex(8)}.tmp"
        temporary_created = False
        try:
            temporary_fd = os.open(
                temporary_name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0),
                target_mode,
                dir_fd=parent_fd,
            )
            temporary_created = True
            with os.fdopen(temporary_fd, "wb") as handle:
                handle.write(source_bytes)
                os.fchmod(handle.fileno(), target_mode)
            os.replace(
                temporary_name,
                relative.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            temporary_created = False
        finally:
            if temporary_created:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(temporary_name, dir_fd=parent_fd)


def unlink_file_no_follow(target: Path, *, base: Path) -> None:
    """Unlink an owned non-directory entry through a held parent descriptor."""
    relative = target.relative_to(base)
    _validate_relative(relative)
    with open_directory_no_follow(base, relative.parent) as parent_fd:
        if parent_fd is None:
            target.unlink()
            return
        os.unlink(relative.name, dir_fd=parent_fd)


def read_regular_file_no_follow(
    target: Path, *, base: Path
) -> tuple[bytes, os.stat_result]:
    """Read one regular target through held descriptors without link following."""
    relative = target.relative_to(base)
    _validate_relative(relative)
    with open_directory_no_follow(base, relative.parent) as parent_fd:
        if parent_fd is None:
            target_stat = target.lstat()
            if stat.S_ISLNK(target_stat.st_mode):
                raise ProjectionTypeError("is a symlink")
            if not stat.S_ISREG(target_stat.st_mode):
                raise ProjectionTypeError("is not a regular file")
            return target.read_bytes(), target_stat

        target_stat = os.stat(
            relative.name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if stat.S_ISLNK(target_stat.st_mode):
            raise ProjectionTypeError("is a symlink")
        if not stat.S_ISREG(target_stat.st_mode):
            raise ProjectionTypeError("is not a regular file")
        target_fd = os.open(
            relative.name,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        with os.fdopen(target_fd, "rb") as handle:
            opened_stat = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened_stat.st_mode):
                raise ProjectionTypeError("changed type while opening")
            return handle.read(), opened_stat
