#!/usr/bin/env python3
"""Shared path-confinement helper for record-directory scripts.

Loaded by path via importlib.util.spec_from_file_location; never imported by
bare name.  Entry points used by the sibling record-directory scripts:

  list_candidate_entries(directory) -> list[os.DirEntry[str]]
    Returns entries sorted by name.  Refuses a symlinked supplied directory;
    accepts one under a symlinked ancestor (macOS resolves /var through one).
    Raises EntryRefused when the directory is itself a symlink, and OSError
    when the directory cannot be scanned.

  classify_entry(entry) -> "regular" | "symlink" | "directory" | "other"
    Uses stat(follow_symlinks=False) so a symlink is never misclassified as a
    regular file.  Raises OSError when the entry cannot be statted.

  read_confined(root, path) -> bytes
    Reads path using O_NOFOLLOW and a before/after (st_dev, st_ino) comparison
    so a symlink at the final component or a replacement race cannot redirect
    the read.  Refuses hard links (st_nlink > 1).
    Raises EntryRefused on a confinement failure and OSError on a read failure.

Derives confinement semantics from
packs/core/.apm/skills/work-loop/scripts/file_safety.py: O_NOFOLLOW on the
final component (and on parent directories when the platform supports dir_fd),
plus the before/after inode comparison and hard-link refusal.  Not imported
from there: file_safety.py belongs to another pack's skill, and these scripts
run standalone from their own projection.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


class EntryRefused(Exception):
    """An entry was refused by the confinement checks."""


def list_candidate_entries(directory: Path) -> list[os.DirEntry[str]]:
    """Return all entries in *directory*, sorted by name.

    Refuses a symlinked supplied directory; accepts one nested under a
    symlinked ancestor.  Only the supplied directory itself is checked: macOS
    resolves /var through a symlink and refusing ancestor symlinks would reject
    every normal invocation under a temp or home path.

    Raises:
        EntryRefused: the supplied directory is itself a symlink.
        OSError: the directory cannot be scanned.
    """
    if directory.is_symlink():
        raise EntryRefused(
            f"{directory}: supplied directory is a symlink; refusing"
        )
    with os.scandir(directory) as it:
        return sorted(it, key=lambda e: e.name)


def classify_entry(entry: os.DirEntry[str]) -> str:
    """Return "regular", "symlink", "directory", or "other".

    Uses entry.stat(follow_symlinks=False) — never is_symlink()/is_file() —
    so an entry removed between listing and classification is not silently
    dropped (those helpers return False on any OSError instead of raising).

    Raises:
        OSError: the entry cannot be statted.
    """
    mode = entry.stat(follow_symlinks=False).st_mode
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISREG(mode):
        return "regular"
    if stat.S_ISDIR(mode):
        return "directory"
    return "other"


def _validate_regular_stat(inspected: os.stat_result, relative: str) -> None:
    """Raise EntryRefused when the stat result is not a single-link regular file."""
    if not stat.S_ISREG(inspected.st_mode):
        raise EntryRefused(f"{relative}: not a regular file")
    if inspected.st_nlink > 1:
        raise EntryRefused(f"{relative}: hard link not allowed")


def read_confined(root: Path, path: Path) -> bytes:
    """Read *path* using O_NOFOLLOW and a before/after (st_dev, st_ino) comparison.

    Derives semantics from file_safety.py: O_NOFOLLOW on the final component,
    a before/after inode comparison to detect a replacement between
    classification and read, and hard-link refusal (st_nlink > 1).  On
    platforms where dir_fd is supported, each parent directory is also opened
    with O_NOFOLLOW | O_DIRECTORY so no path component can redirect the walk
    through a symlink.

    The confinement root is *root*; every path component is validated to remain
    within it.

    Raises:
        EntryRefused: a confinement check failed (symlink, hard link, race, or
            path outside root).
        OSError: the file cannot be opened or read.
    """
    try:
        relative = path.relative_to(root).as_posix()
        relative_parts = path.relative_to(root).parts
    except ValueError as exc:
        raise EntryRefused("path is outside its declared root") from exc

    if not relative_parts:
        raise EntryRefused("path does not name a file")

    file_flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        file_flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        file_flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        file_flags |= os.O_NONBLOCK

    use_dir_fd = (
        os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    )

    fd = -1
    parent_fd = -1
    try:
        if use_dir_fd:
            dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            if hasattr(os, "O_CLOEXEC"):
                dir_flags |= os.O_CLOEXEC
            parent_fd = os.open(str(root), dir_flags)
            for part in relative_parts[:-1]:
                next_fd = os.open(part, dir_flags, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
            before = os.stat(
                relative_parts[-1], dir_fd=parent_fd, follow_symlinks=False
            )
            _validate_regular_stat(before, relative)
            fd = os.open(relative_parts[-1], file_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = -1
        else:
            # Fallback path for platforms without dir_fd support: lstat before
            # open plus O_NOFOLLOW on the file itself (when available).
            before = path.lstat()
            _validate_regular_stat(before, relative)
            fd = os.open(str(path), file_flags)

        after = os.fstat(fd)
        _validate_regular_stat(after, relative)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise EntryRefused(f"{relative}: file changed identity while opening")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read()
    except EntryRefused:
        raise
    except OSError as exc:
        raise OSError(f"cannot read {relative}: {exc}") from exc
    finally:
        if parent_fd >= 0:
            os.close(parent_fd)
        if fd >= 0:
            os.close(fd)
