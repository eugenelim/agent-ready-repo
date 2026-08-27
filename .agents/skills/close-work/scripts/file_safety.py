"""Shared filesystem-read checks for catalogue shipping surfaces."""

from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import BinaryIO, Iterator, Literal, overload


class UnsafeContentError(ValueError):
    """A source entry is not a confined, single-link regular file."""


def _is_reparse_point(inspected: os.stat_result) -> bool:
    attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(inspected, "st_file_attributes", 0) & attribute)


def validate_confined_directory(root: Path, path: Path) -> None:
    """Reject directory paths that escape *root* or cross link-like entries."""
    try:
        relative_path = path.relative_to(root)
    except ValueError as exc:
        raise UnsafeContentError("directory path is outside its declared root") from exc
    try:
        resolved_root = root.resolve(strict=True)
        current = root
        for part in relative_path.parts:
            current /= part
            inspected = current.lstat()
            if (
                not stat.S_ISDIR(inspected.st_mode)
                or stat.S_ISLNK(inspected.st_mode)
                or _is_reparse_point(inspected)
            ):
                relative = current.relative_to(root).as_posix()
                raise UnsafeContentError(
                    f"directory boundary is unsafe: {relative}"
                )
        path.resolve(strict=True).relative_to(resolved_root)
    except UnsafeContentError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        relative = relative_path.as_posix() or "."
        raise UnsafeContentError(
            f"directory boundary cannot be inspected safely: {relative}"
        ) from exc


def list_confined_regular_files(
    root: Path,
    directory: Path,
    *,
    max_files: int | None = None,
    max_depth: int | None = None,
) -> list[Path]:
    """List regular files without following link-like directory entries.

    When ``max_files`` or ``max_depth`` is supplied, refuse during traversal as
    soon as the next entry would exceed the bound.  Callers can therefore
    apply source-tree limits without first walking or materialising an
    attacker-controlled unbounded tree.  Depth is relative to ``directory``.
    """
    if max_files is not None and (
        isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 0
    ):
        raise ValueError("max_files must be a non-negative integer or None")
    if max_depth is not None and (
        isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0
    ):
        raise ValueError("max_depth must be a non-negative integer or None")
    validate_confined_directory(root, directory)
    files: list[Path] = []
    pending = [directory]
    while pending:
        current = pending.pop()
        validate_confined_directory(root, current)
        try:
            with os.scandir(current) as iterator:
                for entry in iterator:
                    entry_path = Path(entry.path)
                    relative = entry_path.relative_to(root).as_posix()
                    source_relative = entry_path.relative_to(directory)
                    if max_depth is not None and len(source_relative.parts) > max_depth:
                        raise UnsafeContentError(
                            "source tree exceeds path-depth limit"
                        )
                    try:
                        inspected = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        raise UnsafeContentError(
                            f"source entry cannot be inspected: {relative}"
                        ) from exc
                    if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(
                        inspected
                    ):
                        raise UnsafeContentError(
                            f"source entry is not a regular file: {relative}"
                        )
                    if stat.S_ISDIR(inspected.st_mode):
                        pending.append(entry_path)
                    elif stat.S_ISREG(inspected.st_mode):
                        if max_files is not None and len(files) >= max_files:
                            raise UnsafeContentError(
                                "source tree exceeds file-count limit"
                            )
                        files.append(entry_path)
                    else:
                        raise UnsafeContentError(
                            f"source entry is not a regular file: {relative}"
                        )
        except OSError as exc:
            relative = current.relative_to(root).as_posix()
            raise UnsafeContentError(
                f"directory boundary cannot be traversed safely: {relative}"
            ) from exc
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def list_confined_directories(root: Path, directory: Path) -> list[Path]:
    """List direct child directories while rejecting link-like entries."""
    validate_confined_directory(root, directory)
    try:
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda entry: entry.name)
    except OSError as exc:
        relative = directory.relative_to(root).as_posix()
        raise UnsafeContentError(
            f"directory boundary cannot be traversed safely: {relative}"
        ) from exc
    directories: list[Path] = []
    for entry in entries:
        entry_path = Path(entry.path)
        relative = entry_path.relative_to(root).as_posix()
        try:
            inspected = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise UnsafeContentError(
                f"source entry cannot be inspected: {relative}"
            ) from exc
        if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(inspected):
            raise UnsafeContentError(f"source entry is link-like: {relative}")
        if stat.S_ISDIR(inspected.st_mode):
            directories.append(entry_path)
    return directories


@contextmanager
def _open_confined_regular_file(
    root: Path,
    path: Path,
    *,
    max_bytes: int | None = None,
) -> Iterator[BinaryIO]:
    """Open *path* only when it is a bounded, confined regular file.

    The link count is checked both before and after opening so a hard-linked
    file, or a file replaced between discovery and use, cannot be shipped.
    ``O_NOFOLLOW`` closes the final-component symlink race on platforms that
    provide it; the post-open inode comparison supplies the portable fallback.
    ``O_NONBLOCK`` prevents a FIFO or device replacement from hanging before
    the post-open regular-file check can reject it.
    """
    if max_bytes is not None and (isinstance(max_bytes, bool) or max_bytes < 0):
        raise ValueError("max_bytes must be a non-negative integer or None")
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise UnsafeContentError("declared root cannot be resolved safely") from exc
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise UnsafeContentError("source path is outside its declared root") from exc

    try:
        before = path.lstat()
    except OSError as exc:
        raise UnsafeContentError(f"source file cannot be inspected: {relative}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise UnsafeContentError(f"source entry is not a regular file: {relative}")
    if _is_reparse_point(before):
        raise UnsafeContentError(f"reparse point not allowed: {relative}")
    if before.st_nlink > 1:
        raise UnsafeContentError(f"hard link not allowed: {relative}")
    try:
        path.resolve(strict=True).relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise UnsafeContentError(f"source path escapes its declared root: {relative}") from exc

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise UnsafeContentError(f"source file cannot be opened safely: {relative}") from exc
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode):
            raise UnsafeContentError(f"source entry is not a regular file: {relative}")
        if _is_reparse_point(after):
            raise UnsafeContentError(f"reparse point not allowed: {relative}")
        if after.st_nlink > 1:
            raise UnsafeContentError(f"hard link not allowed: {relative}")
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise UnsafeContentError(f"source file changed while opening: {relative}")
        if max_bytes is not None and after.st_size > max_bytes:
            raise UnsafeContentError(f"source file exceeds byte limit: {relative}")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            yield handle
    finally:
        if descriptor >= 0:
            os.close(descriptor)


@overload
def read_confined_regular_file(
    root: Path,
    path: Path,
    *,
    max_bytes: int | None = None,
    include_mode: Literal[False] = False,
) -> bytes: ...


@overload
def read_confined_regular_file(
    root: Path,
    path: Path,
    *,
    max_bytes: int | None = None,
    include_mode: Literal[True],
) -> tuple[bytes, int]: ...


def read_confined_regular_file(
    root: Path,
    path: Path,
    *,
    max_bytes: int | None = None,
    include_mode: bool = False,
) -> bytes | tuple[bytes, int]:
    """Read a bounded, confined, no-follow, single-link regular file.

    ``include_mode=True`` returns the permission mode sampled from the same
    validated descriptor as the bytes.  Projection callers must not combine a
    confined read with a later path stat, which could observe a replacement.
    """
    with _open_confined_regular_file(root, path, max_bytes=max_bytes) as handle:
        data = handle.read() if max_bytes is None else handle.read(max_bytes + 1)
        if max_bytes is not None and len(data) > max_bytes:
            relative = path.relative_to(root).as_posix()
            raise UnsafeContentError(
                f"source file changed beyond byte limit: {relative}"
            )
        if include_mode:
            try:
                mode = stat.S_IMODE(os.fstat(handle.fileno()).st_mode)
            except OSError as exc:
                relative = path.relative_to(root).as_posix()
                raise UnsafeContentError(
                    f"source file mode cannot be inspected: {relative}"
                ) from exc
            return data, mode
        return data


def sha256_confined_regular_file(root: Path, path: Path) -> str:
    """Hash a confined regular file without loading it wholly into memory."""
    digest = sha256()
    with _open_confined_regular_file(root, path) as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
