"""Shared filesystem-read checks for catalogue shipping surfaces."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class UnsafeContentError(ValueError):
    """A source entry is not a confined, single-link regular file."""


def read_confined_regular_file(root: Path, path: Path) -> bytes:
    """Read *path* only when it is a regular file confined below *root*.

    The link count is checked both before and after opening so a hard-linked
    file, or a file replaced between discovery and use, cannot be shipped.
    ``O_NOFOLLOW`` closes the final-component symlink race on platforms that
    provide it; the post-open inode comparison supplies the portable fallback.
    """
    resolved_root = root.resolve()
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
    if before.st_nlink > 1:
        raise UnsafeContentError(f"hard link not allowed: {relative}")
    try:
        path.resolve(strict=True).relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise UnsafeContentError(f"source path escapes its declared root: {relative}") from exc

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise UnsafeContentError(f"source file cannot be opened safely: {relative}") from exc
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode):
            raise UnsafeContentError(f"source entry is not a regular file: {relative}")
        if after.st_nlink > 1:
            raise UnsafeContentError(f"hard link not allowed: {relative}")
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise UnsafeContentError(f"source file changed while opening: {relative}")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            return handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)
