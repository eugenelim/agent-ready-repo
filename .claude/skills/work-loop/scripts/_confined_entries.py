"""_confined_entries — a link-recording, no-follow, descriptor-relative directory walk.

``list_confined_entries`` lists the regular files and symbolic links under one
root without following any link. It refuses a FIFO, socket, device node, or
reparse point, and a regular file with more than one link. Every directory is
opened relative to its parent's descriptor with ``O_NOFOLLOW``, and the
descriptor's identity is compared with the entry that named it, so a directory
swapped for a link during the walk is refused.

``iter_confined_entry_chunks`` reads one listed file back in bounded chunks from
one no-follow open whose device, inode, and size must still match the listing.

The module reuses ``UnsafeContentError`` and ``BoundExceeded`` from the
work-loop's ``_file_safety`` copy, which stays byte-pinned to the blessed helper.

Standard library only. POSIX only: a runtime without descriptor-relative opens
refuses rather than falling back to path walking. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Literal, NamedTuple

__all__ = [
    "CHUNK_BYTES",
    "ConfinedEntry",
    "EntryRefused",
    "iter_confined_entry_chunks",
    "list_confined_entries",
]

_SCRIPTS_DIR = Path(__file__).resolve().parent
CHUNK_BYTES = 1024 * 1024
DEFAULT_MAX_DEPTH = 64


def _load(filename: str) -> ModuleType:
    """The work-loop's ``_file_safety`` copy, shared with every supervisor module."""
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_fs = _load("_file_safety.py")
UnsafeContentError = _fs.UnsafeContentError
BoundExceeded = _fs.BoundExceeded


class EntryRefused(UnsafeContentError):  # type: ignore[misc,valid-type]
    """An entry the walk or a read refused; ``reason`` is a short stable token.

    ``special-file``, ``hard-link``, ``reparse-point``, ``changed``, or ``unopenable``.
    """

    def __init__(self, message: str, *, path: str | None, reason: str) -> None:
        super().__init__(message, path=path)
        self.reason = reason


class ConfinedEntry(NamedTuple):
    """One regular file or symbolic link found by the walk.

    ``path`` is root-relative with ``/`` separators. ``target`` is the link's
    target text for a link and ``None`` for a file; ``size`` is the file's byte
    count (a link's target length in bytes).
    """

    path: str
    kind: Literal["file", "link"]
    size: int
    device: int
    inode: int
    mode: int
    target: str | None


def _require_descriptor_walk() -> None:
    if not (
        os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
        and os.readlink in os.supports_dir_fd
        and os.scandir in os.supports_fd
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    ):
        raise UnsafeContentError("this host cannot walk a directory by descriptor")


def _flags(*, directory: bool) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    for name in ("O_CLOEXEC", "O_NONBLOCK"):
        flags |= getattr(os, name, 0)
    return flags | (os.O_DIRECTORY if directory else 0)


def _reparse(info: os.stat_result) -> bool:
    return bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def list_confined_entries(
    root: Path,
    *,
    max_paths: int | None = None,
    max_directories: int | None = None,
    max_bytes: int | None = None,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> list[ConfinedEntry]:
    """Every regular file and symbolic link under *root*, sorted by path.

    Links are recorded, never followed. The walk refuses as soon as a bound
    would be exceeded (``BoundExceeded``: ``entries`` counts files and links,
    ``directories``, ``total-bytes`` sums file sizes, ``depth``), and refuses a
    FIFO, socket, device node, reparse point, or hard-linked file
    (``UnsafeContentError``, with the offending path attached).
    """
    _require_descriptor_walk()
    found: list[ConfinedEntry] = []
    totals = {"directories": 0, "bytes": 0}

    def refuse(message: str, relative: str, reason: str) -> EntryRefused:
        return EntryRefused(f"{message}: {relative}", path=relative, reason=reason)

    def visit(descriptor: int, prefix: str, depth: int) -> None:
        if depth > max_depth:
            raise BoundExceeded(
                "attempt directory is nested too deeply",
                budget="depth", limit=max_depth, observed=depth, path=prefix or None,
            )
        with os.scandir(descriptor) as iterator:
            names = sorted(entry.name for entry in iterator)
        for name in names:
            relative = f"{prefix}{name}"
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if _reparse(info):
                raise refuse("reparse point not allowed", relative, "reparse-point")
            if stat.S_ISDIR(info.st_mode):
                totals["directories"] += 1
                if max_directories is not None and totals["directories"] > max_directories:
                    raise BoundExceeded(
                        "attempt directory holds too many directories",
                        budget="directories", limit=max_directories,
                        observed=totals["directories"], path=relative,
                    )
                try:
                    child = os.open(name, _flags(directory=True), dir_fd=descriptor)
                except OSError as exc:
                    raise refuse("directory cannot be opened safely", relative, "changed") from exc
                try:
                    opened = os.fstat(child)
                    if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        raise refuse("directory changed while walking", relative, "changed")
                    visit(child, relative + "/", depth + 1)
                finally:
                    os.close(child)
                continue
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink > 1:
                    raise refuse("hard link not allowed", relative, "hard-link")
                kind: Literal["file", "link"] = "file"
                target = None
                size = info.st_size
                totals["bytes"] += size
                if max_bytes is not None and totals["bytes"] > max_bytes:
                    raise BoundExceeded(
                        "attempt directory holds too many file bytes",
                        budget="total-bytes", limit=max_bytes,
                        observed=totals["bytes"], path=relative,
                    )
            elif stat.S_ISLNK(info.st_mode):
                kind = "link"
                target = os.readlink(name, dir_fd=descriptor)
                size = len(os.fsencode(target))
            else:
                raise refuse("special file not allowed", relative, "special-file")
            if max_paths is not None and len(found) >= max_paths:
                raise BoundExceeded(
                    "attempt directory holds too many paths",
                    budget="entries", limit=max_paths, observed=len(found) + 1, path=relative,
                )
            found.append(ConfinedEntry(
                relative, kind, size, info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode), target
            ))

    try:
        top = os.open(root, _flags(directory=True))
    except OSError as exc:
        raise UnsafeContentError("attempt directory cannot be opened safely") from exc
    try:
        if _reparse(os.fstat(top)):
            raise UnsafeContentError("attempt directory is link-like")
        visit(top, "", 0)
    except OSError as exc:
        raise UnsafeContentError(
            f"attempt directory cannot be walked safely: {exc.strerror}"
        ) from exc
    finally:
        os.close(top)
    return sorted(found, key=lambda entry: entry.path.encode("utf-8", "surrogateescape"))


def iter_confined_entry_chunks(
    root: Path, entry: ConfinedEntry, *, chunk_bytes: int = CHUNK_BYTES
) -> Iterator[bytes]:
    """The bytes of a listed file in chunks of at most *chunk_bytes*.

    Opens the file once, no-follow, relative to its parent's descriptor, and
    refuses unless the opened descriptor is a single-link regular file with the
    listed device, inode, and size. A file that grows or shrinks while read is
    refused. A parent directory or file swapped for a link fails the open.
    """
    _require_descriptor_walk()
    if entry.kind != "file":
        raise UnsafeContentError("only a listed regular file can be read", path=entry.path)
    parts = entry.path.split("/")
    held: list[int] = []

    def refuse(message: str, reason: str = "changed") -> EntryRefused:
        return EntryRefused(f"{message}: {entry.path}", path=entry.path, reason=reason)

    try:
        try:
            held.append(os.open(root, _flags(directory=True)))
            for part in parts[:-1]:
                held.append(os.open(part, _flags(directory=True), dir_fd=held[-1]))
            descriptor = os.open(parts[-1], _flags(directory=False), dir_fd=held[-1])
        except OSError as exc:
            raise refuse("source file cannot be opened safely") from exc
        held.append(descriptor)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or _reparse(info) or info.st_nlink > 1:
            raise refuse("source file is not a single-link regular file", "hard-link")
        if (info.st_dev, info.st_ino) != (entry.device, entry.inode) or info.st_size != entry.size:
            raise refuse("source file changed since it was listed")
        remaining = entry.size
        while remaining > 0:
            chunk = os.read(descriptor, min(chunk_bytes, remaining))
            if not chunk:
                raise refuse("source file shrank while read")
            remaining -= len(chunk)
            yield chunk
        if os.read(descriptor, 1):
            raise refuse("source file grew while read")
    finally:
        for fd in reversed(held):
            os.close(fd)
