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

  confine_destination(root, relative, new_file=None, read_file=None) -> str
    Confines a repository-relative destination directory (or a new or existing
    file inside it) to the repository root and returns the absolute, fully
    resolved path the caller must use verbatim.  Raises EntryRefused on a
    refusal and EntryAbsent when a named read_file does not exist.

  confine_root_file(root, name) -> str
    The same check for an existing regular file directly under the root.

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
import unicodedata
from pathlib import Path


class EntryRefused(Exception):
    """An entry was refused by the confinement checks."""


class EntryAbsent(Exception):
    """A named file does not exist in a directory that passed every rule."""


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
    equal.  This is not hypothetical — on Linux, unlink-then-create commonly
    reissues the same inode, so that substitution shape is *not* detected
    there, while a rename over the target is.  The check catches substitution
    by rename and by any allocation that lands elsewhere; it does not make the
    read atomic, which nothing short of holding the descriptor from listing
    through read would.

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


_MAX_PATH_CHARS = 1000


def _has_control(value: str) -> bool:
    """Return True when *value* holds a Unicode Cc character, U+2028 or U+2029."""
    return any(
        unicodedata.category(c) == "Cc" or c in "\u2028\u2029" for c in value
    )


def _check_input(value: object, label: str, *, single: bool) -> list[str]:
    """Validate one input string against the segment grammar; return its segments.

    Raises:
        EntryRefused: the string is not 1-1000 characters, starts with ``/``,
            carries a drive prefix, a backslash or a control character, or has
            an empty, ``.`` or ``..`` segment (or, when *single*, any ``/``).
    """
    if not isinstance(value, str) or not 1 <= len(value) <= _MAX_PATH_CHARS:
        raise EntryRefused(f"{label}: must be 1-{_MAX_PATH_CHARS} characters")
    if value.startswith("/"):
        raise EntryRefused(f"{label}: absolute path")
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise EntryRefused(f"{label}: drive-letter path")
    if "\\" in value:
        raise EntryRefused(f"{label}: backslash")
    if _has_control(value):
        raise EntryRefused(f"{label}: control character")
    segments = value.split("/")
    if single and len(segments) != 1:
        raise EntryRefused(f"{label}: must be a single path segment")
    if any(seg in ("", ".", "..") for seg in segments):
        raise EntryRefused(f"{label}: empty, '.' or '..' segment")
    return segments


def _resolve_root(root: Path | str) -> Path:
    """Return the strictly resolved root, which must be a directory."""
    resolved = Path(root).resolve(strict=True)
    if not resolved.is_dir():
        raise EntryRefused("root is not a directory")
    return resolved


def _final_path(path: Path) -> str:
    """Validate and return the string form of the final resolved path."""
    text = str(path)
    if len(text) > _MAX_PATH_CHARS:
        raise EntryRefused(f"resolved path longer than {_MAX_PATH_CHARS} characters")
    if _has_control(text):
        raise EntryRefused("resolved path contains a control character")
    # Enforces the UTF-8 output rule: a path that cannot be encoded (for
    # example a surrogate-escaped name) is refused here, not at print time.
    text.encode("utf-8")
    return text


def _check_existing_file(directory: Path, name: str) -> Path:
    """Return directory/name when it is a regular, singly linked, non-symlink file.

    Raises:
        EntryAbsent: the name does not exist.
        EntryRefused: it exists but is a symlink, hard-linked or not regular.
    """
    candidate = directory / name
    try:
        info = os.lstat(candidate)
    except FileNotFoundError as exc:
        raise EntryAbsent(name) from exc
    if stat.S_ISLNK(info.st_mode):
        raise EntryRefused(f"{name}: symlink")
    if not stat.S_ISREG(info.st_mode):
        raise EntryRefused(f"{name}: not a regular file")
    if info.st_nlink != 1:
        raise EntryRefused(f"{name}: hard link not allowed")
    return candidate


def _confine_directory(root: Path | str, relative: str) -> tuple[Path, Path]:
    """Return ``(resolved_root, candidate_directory)`` for a relative directory."""
    segments = _check_input(relative, "relative path", single=False)
    resolved_root = _resolve_root(root)
    current = resolved_root
    for index, segment in enumerate(segments):
        final = index == len(segments) - 1
        nxt = current / segment
        try:
            info = os.lstat(nxt)
        except FileNotFoundError:
            # Nothing further exists, so no further link can redirect the walk.
            current = nxt.joinpath(*segments[index + 1:])
            break
        if stat.S_ISLNK(info.st_mode):
            if final:
                raise EntryRefused(f"{segment}: final component is a symlink")
            target = nxt.resolve(strict=True)
            if not target.is_relative_to(resolved_root):
                raise EntryRefused(f"{segment}: symlink resolves outside the root")
            if not target.is_dir():
                raise EntryRefused(f"{segment}: not a directory")
            current = target
        elif stat.S_ISDIR(info.st_mode):
            current = nxt
        else:
            raise EntryRefused(f"{segment}: not a directory")
    # Containment is decided on the resolved location, not on path text, so a
    # junction, reparse point or swapped component cannot pass.
    resolved = current.resolve(strict=False)
    if resolved == resolved_root or not resolved.is_relative_to(resolved_root):
        raise EntryRefused("path does not resolve strictly inside the root")
    return resolved_root, resolved


def confine_destination(
    root: Path | str,
    relative: str,
    new_file: str | None = None,
    read_file: str | None = None,
) -> str:
    """Confine *relative* under *root* and return the resolved absolute path.

    Returns the directory, or with *new_file* or *read_file* the file inside
    it.  Every in-root prefix symlink is replaced by its target.  Only stats
    and resolves; writes nothing.

    Raises:
        EntryRefused: any rule fails, or the path cannot be resolved.
        EntryAbsent: *read_file* names a file that does not exist.
    """
    try:
        if new_file is not None and read_file is not None:
            raise EntryRefused("new_file and read_file are exclusive")
        _, directory = _confine_directory(root, relative)
        result = directory
        if new_file is not None:
            _check_input(new_file, "new file name", single=True)
            if not new_file.endswith(".md") or new_file == ".md":
                raise EntryRefused("new file name must end in .md")
            try:
                os.lstat(directory / new_file)
            except FileNotFoundError:
                pass
            else:
                raise EntryRefused(f"{new_file}: already exists")
            result = directory / new_file
        elif read_file is not None:
            _check_input(read_file, "file name", single=True)
            result = _check_existing_file(directory, read_file)
        return _final_path(result)
    except (EntryRefused, EntryAbsent):
        raise
    except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
        # RuntimeError: older Pythons raise it for a symlink loop in resolve().
        raise EntryRefused(f"cannot confine path: {exc}") from exc


def confine_root_file(root: Path | str, name: str) -> str:
    """Return the resolved path of an existing regular file directly under *root*.

    Raises:
        EntryRefused: the name or the file fails a rule, or cannot be resolved.
        EntryAbsent: the file does not exist.
    """
    try:
        _check_input(name, "file name", single=True)
        resolved_root = _resolve_root(root)
        return _final_path(_check_existing_file(resolved_root, name))
    except (EntryRefused, EntryAbsent):
        raise
    except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
        # RuntimeError: older Pythons raise it for a symlink loop in resolve().
        raise EntryRefused(f"cannot confine path: {exc}") from exc
