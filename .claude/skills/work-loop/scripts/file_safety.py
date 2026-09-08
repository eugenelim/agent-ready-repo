"""Shared filesystem-read checks for catalogue shipping surfaces."""

from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import BinaryIO, Iterator, Literal, NamedTuple, overload


class UnsafeContentError(ValueError):
    """A source entry is not a confined, single-link regular file.

    ``path`` carries the offending root-relative path as data when one is
    known, so a caller can name it without parsing the message.  It is
    optional and defaults to ``None``: several refusals happen before any
    path is established, and every existing single-argument construction and
    ``str(exc)`` result is unchanged.
    """

    def __init__(self, message: str, *, path: str | None = None) -> None:
        super().__init__(message)
        self.path = path


class BoundExceeded(UnsafeContentError):
    """A declared traversal or read bound was exceeded.

    Carries the breached budget as data so a caller can attribute the refusal
    without parsing the message.  That distinction is load-bearing: an
    integrity refusal (link-like, special, non-regular, uninspectable) and a
    budget breach both surface as ``UnsafeContentError``, and only the budget
    breach is a bound.  Catching ``UnsafeContentError`` still catches this, so
    existing callers are unaffected.

    ``budget`` is a plain string from a small stable set — ``entries``,
    ``depth``, ``files``, ``selected-skills``, ``per-file-bytes``,
    ``total-bytes`` — deliberately not an enum, because this module is mirrored
    byte-for-byte into trees where the diagnostic registry is unimportable.
    """

    def __init__(
        self,
        message: str,
        *,
        budget: str,
        limit: int,
        observed: int | None = None,
        path: str | None = None,
    ) -> None:
        super().__init__(message, path=path)
        self.budget = budget
        self.limit = limit
        self.observed = observed


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
        root_inspected = root.lstat()
        if (
            not stat.S_ISDIR(root_inspected.st_mode)
            or stat.S_ISLNK(root_inspected.st_mode)
            or _is_reparse_point(root_inspected)
        ):
            raise UnsafeContentError("declared root is link-like or not a directory")
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


class ConfinedWalk(NamedTuple):
    """One bounded traversal's files and the directory entries it consumed.

    ``entries_seen`` is what a caller needs to thread a shared entry allowance
    across several directories.  The file list alone cannot do it: a tree made
    entirely of directories consumes entries while contributing no files, so a
    caller counting returned files under-counts and lets a multi-directory
    source exceed a shared bound.  Under-counting is the unsafe direction.
    """

    files: list[Path]
    entries_seen: int


def walk_confined_regular_files(
    root: Path,
    directory: Path,
    *,
    max_files: int | None = None,
    max_depth: int | None = None,
    max_entries: int | None = None,
) -> ConfinedWalk:
    """List regular files and report the directory entries consumed.

    When ``max_files``, ``max_depth`` or ``max_entries`` is supplied, refuse
    during traversal as soon as the next entry would exceed the bound.  Callers
    can therefore apply source-tree limits without first walking or
    materialising an attacker-controlled unbounded tree.  Depth is relative to
    ``directory``.

    ``max_files`` bounds only the regular files collected, so a tree made
    entirely of directories is unbounded under it; ``max_entries`` bounds every
    directory entry visited, which is what a caller needs when a concurrent
    local writer can grow the tree between a preflight measurement and this
    traversal.
    """
    if max_files is not None and (
        isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 0
    ):
        raise ValueError("max_files must be a non-negative integer or None")
    if max_depth is not None and (
        isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0
    ):
        raise ValueError("max_depth must be a non-negative integer or None")
    if max_entries is not None and (
        isinstance(max_entries, bool)
        or not isinstance(max_entries, int)
        or max_entries < 0
    ):
        raise ValueError("max_entries must be a non-negative integer or None")
    validate_confined_directory(root, directory)
    files: list[Path] = []
    entries_seen = 0
    pending = [directory]
    while pending:
        current = pending.pop()
        validate_confined_directory(root, current)
        try:
            with os.scandir(current) as iterator:
                for entry in iterator:
                    entries_seen += 1
                    if max_entries is not None and entries_seen > max_entries:
                        raise BoundExceeded(
                            "source tree exceeds entry-count limit",
                            budget="entries",
                            limit=max_entries,
                            observed=entries_seen,
                        )
                    entry_path = Path(entry.path)
                    relative = entry_path.relative_to(root).as_posix()
                    source_relative = entry_path.relative_to(directory)
                    if max_depth is not None and len(source_relative.parts) > max_depth:
                        raise BoundExceeded(
                            "source tree exceeds path-depth limit",
                            budget="depth",
                            limit=max_depth,
                            observed=len(source_relative.parts),
                        )
                    try:
                        inspected = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        raise UnsafeContentError(
                            f"source entry cannot be inspected: {relative}",
                            path=relative,
                        ) from exc
                    if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(
                        inspected
                    ):
                        raise UnsafeContentError(
                            f"source entry is not a regular file: {relative}",
                            path=relative,
                        )
                    if stat.S_ISDIR(inspected.st_mode):
                        pending.append(entry_path)
                    elif stat.S_ISREG(inspected.st_mode):
                        if max_files is not None and len(files) >= max_files:
                            raise BoundExceeded(
                                "source tree exceeds file-count limit",
                                budget="files",
                                limit=max_files,
                                observed=len(files) + 1,
                            )
                        files.append(entry_path)
                    else:
                        raise UnsafeContentError(
                            f"source entry is not a regular file: {relative}",
                            path=relative,
                        )
        except OSError as exc:
            relative = current.relative_to(root).as_posix()
            raise UnsafeContentError(
                f"directory boundary cannot be traversed safely: {relative}"
            ) from exc
    return ConfinedWalk(
        sorted(files, key=lambda path: path.relative_to(root).as_posix()),
        entries_seen,
    )


def list_confined_regular_files(
    root: Path,
    directory: Path,
    *,
    max_files: int | None = None,
    max_depth: int | None = None,
    max_entries: int | None = None,
) -> list[Path]:
    """List regular files, discarding the entry count.

    The established surface, unchanged for every existing caller. Callers
    that thread a shared entry allowance want `walk_confined_regular_files`.
    """
    return walk_confined_regular_files(
        root,
        directory,
        max_files=max_files,
        max_depth=max_depth,
        max_entries=max_entries,
    ).files


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


def _supports_descriptor_walk() -> bool:
    """Return whether this runtime can bind each path component to a directory fd."""
    return (
        os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    )


@contextmanager
def _open_confined_parent(
    root: Path, path: Path, *, relative: str
) -> Iterator[tuple[int | None, str]]:
    """Hold the target's parent open without following path components."""
    try:
        relative_path = path.relative_to(root)
    except ValueError as exc:
        raise UnsafeContentError("source path is outside its declared root") from exc
    if not relative_path.parts:
        raise UnsafeContentError("source path does not name a file")
    if any(part in {"", ".", ".."} for part in relative_path.parts):
        raise UnsafeContentError("source path contains a dot segment")

    if not _supports_descriptor_walk():
        validate_confined_directory(root, path.parent)
        yield None, path.name
        return

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
    if hasattr(os, "O_NONBLOCK"):
        directory_flags |= os.O_NONBLOCK

    descriptor = -1
    try:
        descriptor = os.open(root, directory_flags)
        inspected = os.fstat(descriptor)
        if not stat.S_ISDIR(inspected.st_mode) or _is_reparse_point(inspected):
            raise UnsafeContentError("declared root is link-like or not a directory")
        for part in relative_path.parts[:-1]:
            try:
                next_descriptor = os.open(part, directory_flags, dir_fd=descriptor)
            except OSError as exc:
                raise UnsafeContentError(
                    f"directory boundary cannot be opened safely: {relative}"
                ) from exc
            os.close(descriptor)
            descriptor = next_descriptor
            inspected = os.fstat(descriptor)
            if not stat.S_ISDIR(inspected.st_mode) or _is_reparse_point(inspected):
                raise UnsafeContentError(
                    f"directory boundary is unsafe: {relative}"
                )
        yield descriptor, relative_path.parts[-1]
    except UnsafeContentError:
        raise
    except OSError as exc:
        raise UnsafeContentError(
            f"directory boundary cannot be opened safely: {relative}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _validate_regular_file_stat(inspected: os.stat_result, relative: str) -> None:
    """Reject unsafe file metadata before or after a descriptor is opened."""
    if not stat.S_ISREG(inspected.st_mode):
        raise UnsafeContentError(f"source entry is not a regular file: {relative}")
    if _is_reparse_point(inspected):
        raise UnsafeContentError(f"reparse point not allowed: {relative}")
    if inspected.st_nlink > 1:
        raise UnsafeContentError(f"hard link not allowed: {relative}")


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

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    descriptor = -1
    with _open_confined_parent(root, path, relative=relative) as (parent_fd, leaf):
        try:
            if parent_fd is None:
                before = path.lstat()
                _validate_regular_file_stat(before, relative)
                path.resolve(strict=True).relative_to(resolved_root)
                descriptor = os.open(path, flags)
            else:
                before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                _validate_regular_file_stat(before, relative)
                descriptor = os.open(leaf, flags, dir_fd=parent_fd)
        except UnsafeContentError:
            raise
        except (OSError, RuntimeError, ValueError) as exc:
            raise UnsafeContentError(
                f"source file cannot be opened safely: {relative}"
            ) from exc
        try:
            after = os.fstat(descriptor)
            _validate_regular_file_stat(after, relative)
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                raise UnsafeContentError(
                    f"source file changed while opening: {relative}"
                )
            if max_bytes is not None and after.st_size > max_bytes:
                raise BoundExceeded(
                    f"source file exceeds byte limit: {relative}",
                    budget="per-file-bytes",
                    limit=max_bytes,
                    observed=after.st_size,
                )
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
            raise BoundExceeded(
                f"source file changed beyond byte limit: {relative}",
                budget="per-file-bytes",
                limit=max_bytes,
                observed=len(data),
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
