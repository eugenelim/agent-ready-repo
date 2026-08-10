"""No-follow filesystem primitives for committed build projections."""

from __future__ import annotations

import contextlib
import errno
import json
import os
import secrets
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class ProjectionTypeError(OSError):
    """A projected target exists but is not a regular file."""


def render_diagnostic_path(path: Path) -> str:
    """Render an untrusted path reversibly on exactly one log line."""
    return json.dumps(path.as_posix(), ensure_ascii=True)


def _secure_dir_fd_available() -> bool:
    return os.name == "posix" and all(
        hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")
    )


def _validate_relative(relative: Path) -> None:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"projection path must stay relative to its base: {relative}")


def ensure_directory_no_follow(base: Path, relative: Path) -> None:
    """Create/repair an owned directory tree without following links."""
    _validate_relative(relative)
    if not _secure_dir_fd_available():
        current = base
        for part in relative.parts:
            current /= part
            try:
                current_stat = current.lstat()
            except FileNotFoundError:
                current.mkdir()
                continue
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
