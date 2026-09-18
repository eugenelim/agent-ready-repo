#!/usr/bin/env python3
"""Shared path-confinement helper for record-directory scripts.

Loaded by path via importlib.util.spec_from_file_location; never imported by
bare name.  Entry points used by the sibling record-directory scripts:

  list_candidate_entries(directory) -> list[CandidateEntry]
    Returns entries sorted by name, each carrying the (st_dev, st_ino) seen
    while the directory was held open.  Refuses a symlinked supplied directory
    by opening it with O_NOFOLLOW | O_DIRECTORY rather than by testing and then
    scanning, so no window separates the check from the listing.  Accepts a
    directory under a symlinked ancestor (macOS resolves /var through one).
    Raises EntryRefused when the directory is itself a symlink, and OSError
    when the directory cannot be scanned.

  classify_entry(entry) -> "regular" | "symlink" | "directory" | "other"
    Uses stat(follow_symlinks=False) so a symlink is never misclassified as a
    regular file.  Raises OSError when the entry cannot be statted.

  read_confined(root, path, expect=None) -> bytes
    Reads path using O_NOFOLLOW and a before/after (st_dev, st_ino) comparison
    so a symlink at the final component or a replacement race cannot redirect
    the read.  Pass expect=entry.identity to bind the read to the entry that
    was listed and classified, which the before/after pair alone cannot do.
    Refuses hard links (st_nlink > 1).
    Raises EntryRefused on a confinement failure and OSError on a read failure.

Derives confinement semantics from
packs/core/.apm/skills/work-loop/scripts/file_safety.py: O_NOFOLLOW on the
final component (and on parent directories when the platform supports dir_fd),
plus the before/after inode comparison and hard-link refusal.  Not imported
from there: file_safety.py belongs to another pack's skill, and these scripts
run standalone from their own projection.
"""
from __future__ import annotations

import errno
import os
import stat
from pathlib import Path


class EntryRefused(Exception):
    """An entry was refused by the confinement checks."""


class CandidateEntry:
    """A listed entry, carrying the identity observed at listing time.

    Exposes ``name`` and ``path`` so it substitutes for the ``os.DirEntry``
    this helper used to return.  It additionally carries ``identity`` — the
    ``(st_dev, st_ino)`` pair seen while the listing directory was held open —
    which the caller hands to :func:`read_confined` so a substitution between
    classification and read is detected rather than silently followed.
    """

    __slots__ = ("name", "path", "_stat", "_error")

    def __init__(self, name: str, path: Path,
                 stat_result: os.stat_result | None,
                 error: OSError | None = None):
        self.name = name
        self.path = path
        self._stat = stat_result
        self._error = error

    @property
    def identity(self) -> tuple[int, int] | None:
        """The ``(st_dev, st_ino)`` observed at listing time, if it was."""
        if self._stat is None:
            return None
        return (self._stat.st_dev, self._stat.st_ino)

    def stat(self, *, follow_symlinks: bool = False) -> os.stat_result:
        """Return the listing-time lstat.

        Deliberately cached rather than re-taken: re-statting by name would
        open a fresh window between this call and the read that follows it,
        which is the gap the identity carried here exists to close.
        ``follow_symlinks=True`` is refused because no caller needs it and
        honouring it would resolve the symlink this helper exists to catch.
        """
        if follow_symlinks:
            raise ValueError("follow_symlinks=True is not supported")
        if self._error is not None:
            # Re-raised here, not at listing time. Statting every entry while
            # the directory is held open is what makes the identity
            # trustworthy, but a single unstattable entry must not abort the
            # scan: the caller classifies entry by entry and accounts each one,
            # and an entry that fails here is reported and bucketed rather
            # than taking the other candidates down with it.
            raise self._error
        assert self._stat is not None
        return self._stat

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"CandidateEntry({self.name!r})"


def list_candidate_entries(directory: Path) -> list[CandidateEntry]:
    """Return all entries in *directory*, sorted by name.

    Refuses a symlinked supplied directory; accepts one nested under a
    symlinked ancestor.  Only the supplied directory itself is checked: macOS
    resolves /var through a symlink and refusing ancestor symlinks would reject
    every normal invocation under a temp or home path.

    The refusal is made by opening the directory with ``O_NOFOLLOW |
    O_DIRECTORY`` rather than by testing ``is_symlink()`` and then scanning by
    name.  The test-then-scan form left a window in which the directory could
    be replaced by a symlink after passing the test, so the scan could walk a
    different tree than the one that was checked.  Here the descriptor that
    fails to open on a symlink is the same descriptor the listing reads, so
    there is no window between the two.

    Each entry's ``(st_dev, st_ino)`` is captured through that same descriptor
    and travels with the entry, so a later read can verify it is opening the
    file that was listed.

    Raises:
        EntryRefused: the supplied directory is itself a symlink.
        OSError: the directory cannot be scanned.
    """
    dir_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        dir_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        dir_flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        dir_flags |= os.O_CLOEXEC

    supports_fd = (
        os.scandir in os.supports_fd
        and os.stat in os.supports_dir_fd
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_DIRECTORY")
    )
    if not supports_fd:
        # Fallback for a platform without descriptor-relative listing. The
        # check-then-act window is unavoidable here, so it is named rather
        # than papered over.
        if directory.is_symlink():
            raise EntryRefused(
                f"{directory}: supplied directory is a symlink; refusing"
            )
        with os.scandir(directory) as it:
            names = sorted(e.name for e in it)
        out: list[CandidateEntry] = []
        for name in names:
            target = directory / name
            try:
                out.append(CandidateEntry(name, target, target.lstat()))
            except OSError as exc:
                out.append(CandidateEntry(name, target, None, exc))
        return out

    try:
        dir_fd = os.open(str(directory), dir_flags)
    except OSError as exc:
        # O_NOFOLLOW on a symlink raises ELOOP; O_DIRECTORY on a symlink to a
        # non-directory can surface as ENOTDIR first. Both mean the supplied
        # name did not resolve to a real directory here, which is the refusal.
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise EntryRefused(
                f"{directory}: supplied directory is a symlink; refusing"
            ) from exc
        raise

    try:
        with os.scandir(dir_fd) as it:
            names = sorted(e.name for e in it)
        entries: list[CandidateEntry] = []
        for name in names:
            try:
                inspected = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
            except OSError as exc:
                entries.append(
                    CandidateEntry(name, directory / name, None, exc))
                continue
            entries.append(CandidateEntry(name, directory / name, inspected))
        return entries
    finally:
        os.close(dir_fd)


def classify_entry(entry: os.DirEntry[str]) -> str:
    """Return "regular", "symlink", "directory", or "other".

    Uses entry.stat(follow_symlinks=False) — never is_symlink()/is_file() —
    so an entry removed between listing and classification is not silently
    dropped (those helpers return False on any OSError instead of raising).

    Raises:
        OSError: the entry cannot be statted.
    """
    mode = entry.stat(follow_symlinks=False).st_mode  # cached for CandidateEntry
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


def read_confined(
    root: Path, path: Path, expect: tuple[int, int] | None = None
) -> bytes:
    """Read *path* using O_NOFOLLOW and a before/after (st_dev, st_ino) comparison.

    Derives semantics from file_safety.py: O_NOFOLLOW on the final component,
    a before/after inode comparison to detect a replacement between
    classification and read, and hard-link refusal (st_nlink > 1).  On
    platforms where dir_fd is supported, each parent directory is also opened
    with O_NOFOLLOW | O_DIRECTORY so no path component can redirect the walk
    through a symlink.

    The confinement root is *root*; every path component is validated to remain
    within it.

    *expect* is the ``(st_dev, st_ino)`` the caller observed when it listed and
    classified the entry.  When given, the opened file must still have that
    identity.  Without it the before/after comparison below proves only that
    the file did not change between this function's own stat and open — it
    cannot see a substitution that happened earlier, between classification
    and this call, because the fresh stat would simply observe the replacement
    and agree with itself.  Passing *expect* is what makes the classification
    binding on the read.

    Limit, stated rather than implied: identity is ``(st_dev, st_ino)``, and an
    inode freed by an unlink can be reissued to the file created next.  A
    substitution that happens to land on the reused inode therefore compares
    equal.  This narrows the window to an attacker who can also win that race;
    it does not make the read atomic, which nothing short of holding the
    descriptor from listing through read would.

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
        if expect is not None and (after.st_dev, after.st_ino) != expect:
            raise EntryRefused(
                f"{relative}: file was replaced after it was listed"
            )
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
