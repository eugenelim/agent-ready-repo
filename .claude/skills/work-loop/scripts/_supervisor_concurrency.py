"""_supervisor_concurrency — the pure and ingestion pieces of concurrent attempts.

Four parts, none of which spawns a launcher:

* ``meets`` and ``tasks_meet`` decide whether one task's declared or attested
  accesses meet another's writes, so admission keeps meeting tasks apart.
* ``create_attempt_directory`` makes the plain directory one attempt works in,
  outside the Git directory, the common directory, the run store, and the work
  tree, filled from a source commit with a private index and ``checkout-index``.
  It is never a Git worktree and holds no ``.git`` entry.
* ``ingest_attempt_directory`` turns that directory into a Git tree id. It
  checks every cap, name, and link from the no-follow listing before any object
  is written, streams each file into ``hash-object`` in bounded chunks, and
  applies the same ignore rules the sequential change set applies.
* ``git_floor_reason`` and ``merge_config_floor_reason`` name why a repository
  keeps its tasks on the sequential floor.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import stat
import sys
import tempfile
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module."""
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
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


_git = _supervisor("_supervisor_git.py")
_entries = _supervisor("_confined_entries.py")
SupervisorGitError = _git.SupervisorGitError

__all__ = [
    "Access",
    "AttemptRefused",
    "GIT_FLOOR",
    "Ingested",
    "MAX_PATHS",
    "MAX_TOTAL_BYTES",
    "create_attempt_directory",
    "declared_reads",
    "declared_writes",
    "git_floor_reason",
    "ingest_attempt_directory",
    "is_dot_git_name",
    "is_repository_path",
    "meets",
    "merge_config_floor_reason",
    "remove_attempt_directory",
    "tasks_meet",
]

GIT_FLOOR = (2, 41)
MAX_PATHS = 100_000
MAX_TOTAL_BYTES = 10 * 1024**3
MAX_LINK_HOPS = 40
_PROTECT = ("core.protectHFS=true", "core.protectNTFS=true")


class AttemptRefused(Exception):
    """An attempt directory or its location failed a check; *code* is a stable token.

    Codes: ``attempt-location``, ``attempt-too-large``, ``attempt-special-file``,
    ``attempt-hard-link``, ``attempt-bad-path``, ``attempt-git-name``,
    ``attempt-unsafe-link``, ``attempt-changed``, ``attempt-unreadable``.
    """

    def __init__(self, code: str, detail: str, *, path: str | None = None) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.path = path


# ── repository paths ────────────────────────────────────────────────────────


def is_repository_path(path: str) -> bool:
    """Whether *path* is a repository path: relative, ``/``-separated, with clean components.

    No empty, ``.`` or ``..`` component, and no NUL, control character, or backslash.
    """
    if not path or any(ord(c) < 32 or ord(c) == 127 or c == "\\" for c in path):
        return False
    return all(part not in ("", ".", "..") for part in path.split("/"))


def _key(path: str, ignore_case: bool) -> str:
    """The form in which two repository paths compare: NFC, folded when case is ignored."""
    text = unicodedata.normalize("NFC", path)
    return text.casefold() if ignore_case else text


# ── the meets relation ──────────────────────────────────────────────────────

_READ_KINDS = frozenset({"file", "missing", "listing", "walk"})
_WRITE_KINDS = frozenset({"write", "delete", "rename-from", "rename-to", "mode"})
_CREATING = frozenset({"write", "rename-to"})


@dataclass(frozen=True)
class Access:
    """One read or write of a repository path.

    Reads are ``file``, ``missing``, ``listing``, ``walk``; writes are ``write``,
    ``delete``, ``rename-from``, ``rename-to``, ``mode``. *subtree* marks a declared
    ``root/**`` write: it writes every path at or under *path*.
    """

    kind: str
    path: str
    subtree: bool = False

    def __post_init__(self) -> None:
        if self.kind not in _READ_KINDS | _WRITE_KINDS:
            raise ValueError(f"unknown access kind: {self.kind}")
        if self.subtree and self.kind != "write":
            raise ValueError("only a write can cover a subtree")

    @property
    def is_write(self) -> bool:
        return self.kind in _WRITE_KINDS


def declared_reads(entries: Iterable[str]) -> list[Access]:
    """``Reads:`` entries as accesses: a file, a ``/`` listing, or a ``/**`` walk."""
    found = []
    for entry in entries:
        if entry.endswith("/**"):
            found.append(Access("walk", entry[:-3]))
        elif entry.endswith("/"):
            found.append(Access("listing", entry[:-1]))
        else:
            found.append(Access("file", entry))
    return found


def declared_writes(entries: Iterable[str]) -> list[Access]:
    """``Writes:`` entries as accesses: a file write, or a ``/**`` subtree write."""
    return [
        Access("write", e[:-3], subtree=True) if e.endswith("/**") else Access("write", e)
        for e in entries
    ]


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def _ancestors(path: str) -> list[str]:
    parts = path.split("/")
    return ["/".join(parts[:i]) for i in range(1, len(parts))]


def _write_reaches(write: Access, wpath: str, query: str) -> bool:
    """Whether *query* is the write's path, in its subtree, or an ancestor it brings in or out."""
    if query == wpath or (write.subtree and _under(query, wpath)):
        return True
    return write.kind != "mode" and query in _ancestors(wpath)


def meets(read_or_write: Access, write: Access, *, ignore_case: bool = False) -> bool:
    """Whether *read_or_write* meets *write*, by the one closed list of rows.

    A missing-path lookup meets a write creating that path; a listing meets a write
    adding, removing, or renaming an entry directly in the directory; a walk meets any
    write at or under its root; any other read or write meets a write to the same path.
    A write also reaches each ancestor directory it brings into or out of existence, and a
    ``root/**`` write reaches every path at or under ``root``. Paths compare in NFC, and
    folded when *ignore_case* is set. A mode change adds or removes no entry.
    """
    if not write.is_write:
        raise ValueError("the second argument must be a write")
    wpath = _key(write.path, ignore_case)
    rpath = _key(read_or_write.path, ignore_case)
    kind = read_or_write.kind
    if kind == "missing":
        creating = write.kind in _CREATING
        return creating and _write_reaches(write, wpath, rpath)
    if kind == "listing":
        if write.kind == "mode":
            return False
        if write.subtree and _under(rpath, wpath):
            return True
        direct = [wpath, *_ancestors(wpath)]
        return any(p.rpartition("/")[0] == rpath for p in direct)
    if kind == "walk":
        return _under(wpath, rpath) or (write.subtree and _under(rpath, wpath))
    if kind == "file":
        return _write_reaches(write, wpath, rpath)
    # A write against a write: either one's own path reaches the other's.
    return _write_reaches(write, wpath, rpath) or _write_reaches(read_or_write, rpath, wpath)


def tasks_meet(
    reads_a: Iterable[Access],
    writes_a: Iterable[Access],
    reads_b: Iterable[Access],
    writes_b: Iterable[Access],
    *,
    ignore_case: bool = False,
) -> bool:
    """Whether either task's reads or writes meet the other's writes."""
    first_reads, first_writes = list(reads_a), list(writes_a)
    second_reads, second_writes = list(reads_b), list(writes_b)
    return any(
        meets(access, write, ignore_case=ignore_case)
        for accesses, writes in (
            ([*first_reads, *first_writes], second_writes),
            ([*second_reads, *second_writes], first_writes),
        )
        for access in accesses
        for write in writes
    )


# ── Git gates ───────────────────────────────────────────────────────────────


def git_floor_reason(version: tuple[int, int]) -> str | None:
    """``git-version`` when *version* is older than the concurrent path needs, else None."""
    return "git-version" if version < GIT_FLOOR else None


def merge_config_floor_reason(entries: list[Any]) -> str | None:
    """``merge-config`` when repository or worktree config holds any non-driver ``merge.*`` key.

    A ``merge.<name>.driver`` key is refused at ``start`` and never reaches this check.
    """
    return "merge-config" if _git.merge_config_keys(entries) else None


# ── attempt directories ─────────────────────────────────────────────────────


def create_attempt_directory(
    git: Any,
    source: str,
    *,
    forbidden: Iterable[Path] = (),
    parent: Path | None = None,
) -> Path:
    """A new attempt directory holding the tree of commit *source*.

    The directory is a fresh ``agentbundle-attempt-`` directory (mode 0700) under *parent*
    or the system temporary directory. It must lie outside the Git directory, the common
    directory, the work tree, and every *forbidden* path (the run store), and none of
    those may lie inside it; otherwise it is removed and ``AttemptRefused`` is raised.
    Files come from the source tree through a private index and ``checkout-index``.
    """
    created = Path(tempfile.mkdtemp(prefix="agentbundle-attempt-", dir=parent)).resolve()
    try:
        pins = git.pins
        for denied in (pins.git_dir, pins.common_dir, pins.root, *map(Path, forbidden)):
            resolved = Path(os.path.realpath(denied))
            if created == resolved or resolved in created.parents or created in resolved.parents:
                raise AttemptRefused(
                    "attempt-location", "the attempt directory overlaps a protected location"
                )
        index_dir = Path(tempfile.mkdtemp(prefix="work-supervisor-index-"))
        try:
            env = {"GIT_INDEX_FILE": str(index_dir / "index")}
            git.run("read-tree", source, env=env)
            git.run("checkout-index", "-a", f"--prefix={created}/", env=env)
        finally:
            shutil.rmtree(index_dir, ignore_errors=True)
    except BaseException:
        shutil.rmtree(created, ignore_errors=True)
        raise
    return created


def remove_attempt_directory(path: Path) -> None:
    """Remove an attempt directory made by ``create_attempt_directory``; links are not followed."""
    if path.name.startswith("agentbundle-attempt-"):
        shutil.rmtree(path, ignore_errors=True)


# ── ingestion ───────────────────────────────────────────────────────────────

# Code points HFS+ ignores when it compares names (Git's ``is_hfs_dotgit``).
_HFS_IGNORABLE = frozenset(
    {0x200C, 0x200D, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x206A, 0x2070), 0xFEFF}
)


def is_dot_git_name(component: str) -> bool:
    """Whether Git refuses *component* as ``.git`` with the HFS and NTFS protections on.

    Case-insensitive ``.git``, ``.git`` with HFS-ignorable code points inside, and the NTFS
    forms: trailing dots and spaces, an alternate data stream suffix, and ``git~1``.
    """
    name = "".join(c for c in component if ord(c) not in _HFS_IGNORABLE).lower()
    base = name.split(":", 1)[0].rstrip(". ")
    return base in (".git", "git~1")


@dataclass(frozen=True)
class Ingested:
    """What ingestion admitted: the tree id, the attempt's admitted and ignored paths."""

    tree: str
    admitted: tuple[str, ...]
    ignored: tuple[str, ...]


def _refuse_walk(error: Exception) -> AttemptRefused:
    """Translate a walk refusal into an ``AttemptRefused``."""
    path = getattr(error, "path", None)
    if isinstance(error, _entries.BoundExceeded):
        return AttemptRefused("attempt-too-large", str(error), path=path)
    codes = {
        "special-file": "attempt-special-file",
        "hard-link": "attempt-hard-link",
        "changed": "attempt-changed",
    }
    code = codes.get(getattr(error, "reason", ""), "attempt-unreadable")
    return AttemptRefused(code, str(error), path=path)


def _check_names(paths: Iterable[str]) -> None:
    for path in paths:
        try:
            path.encode("utf-8")
        except UnicodeEncodeError:
            raise AttemptRefused("attempt-bad-path", f"not valid UTF-8: {path!r}") from None
        if not is_repository_path(path):
            raise AttemptRefused("attempt-bad-path", f"not a repository path: {path!r}", path=path)
        if any(is_dot_git_name(part) for part in path.split("/")):
            raise AttemptRefused("attempt-git-name", f"names a .git entry: {path}", path=path)


def _resolve_link(
    link: str,
    keyed: dict[str, str],
    *,
    root: str,
    ignore_case: bool,
) -> list[str]:
    """The lexical product path *link* resolves to, through every link in *keyed*.

    *keyed* maps each listed link's folded path to its target text. Raises
    ``AttemptRefused`` when the result leaves the work tree, passes a ``.git`` entry, or
    needs more than ``MAX_LINK_HOPS`` hops; the link itself is the first hop.
    """

    def refuse(why: str) -> AttemptRefused:
        return AttemptRefused("attempt-unsafe-link", f"{link} {why}", path=link)

    current = link.split("/")[:-1]
    hops = 0
    pending = [link.split("/")[-1]]
    while pending:
        part = pending.pop()
        if part in ("", "."):
            continue
        if part == "..":
            if not current:
                raise refuse("leaves the work tree")
            current.pop()
            continue
        if is_dot_git_name(part):
            raise refuse("reaches a .git entry")
        current.append(part)
        target = keyed.get(_key("/".join(current), ignore_case))
        if target is None:
            continue
        hops += 1
        if hops > MAX_LINK_HOPS:
            raise refuse(f"needs more than {MAX_LINK_HOPS} link hops")
        current.pop()
        if target.startswith("/"):
            prefix = root.rstrip("/") + "/"
            if not (target + "/").startswith(prefix):
                raise refuse("points outside the work tree")
            current = []
            target = target[len(prefix):]
        pending.extend(reversed(target.split("/")))
    return current


def _check_links(
    links: dict[str, str],
    admitted: Iterable[str],
    *,
    trusted_paths: Iterable[str],
    protected_prefixes: Iterable[str],
    product_root: str,
    ignore_case: bool,
) -> None:
    denied = [_key(p.rstrip("/"), ignore_case) for p in (*trusted_paths, *protected_prefixes)]
    keyed = {_key(path, ignore_case): target for path, target in links.items()}
    for link in admitted:
        if link not in links:
            continue
        final = "/".join(_resolve_link(link, keyed, root=product_root, ignore_case=ignore_case))
        folded = _key(final, ignore_case)
        if any(_under(folded, d) for d in denied):
            raise AttemptRefused(
                "attempt-unsafe-link", f"{link} points at a trusted or protected path", path=link
            )


def ingest_attempt_directory(
    git: Any,
    attempt_dir: Path,
    *,
    source: str,
    trusted_paths: Iterable[str] = (),
    protected_prefixes: Iterable[str] = ("delivery",),
    excluded_prefixes: Sequence[str] = (),
    product_root: str | None = None,
    ignore_case: bool = False,
    max_paths: int = MAX_PATHS,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> Ingested:
    """The Git tree of *attempt_dir*, under the floor's change-set rules.

    Every refusal (caps, names, links) happens from the no-follow listing before any
    object is written. Files stream into ``hash-object`` in bounded chunks from one
    no-follow open that must match the listing. Paths under *excluded_prefixes* and
    gitlinks keep the source commit's entries; paths the ignore rules cover (untracked at
    *source*) are left out, as ``git add -A`` leaves them. *product_root* is the work
    tree's absolute path, against which an absolute link target is read.
    """
    try:
        listing = _entries.list_confined_entries(
            attempt_dir, max_paths=max_paths, max_directories=max_paths,
            max_bytes=max_total_bytes,
        )
    except _entries.UnsafeContentError as error:
        raise _refuse_walk(error) from error
    _check_names(entry.path for entry in listing)
    excluded = tuple(excluded_prefixes)
    live = [e for e in listing if not e.path.startswith(excluded)]
    index_dir = Path(tempfile.mkdtemp(prefix="work-supervisor-index-"))
    try:
        env = {"GIT_INDEX_FILE": str(index_dir / "index")}
        git.run("read-tree", source, env=env)
        ignored: set[str] = set()
        if live:
            try:
                out = git.run(
                    "check-ignore", "--stdin", "-z", env=env, work_tree=attempt_dir,
                    stdin=b"\0".join(e.path.encode("utf-8") for e in live) + b"\0",
                    ok_codes=(0, 1),
                )
            except SupervisorGitError as error:
                if "beyond a symbolic link" not in str(error):
                    raise
                raise AttemptRefused(
                    "attempt-changed", "a directory became a link after it was listed"
                ) from error
            ignored = {p.decode("utf-8") for p in out.split(b"\0") if p}
        admitted = [e for e in live if e.path not in ignored]
        links = {e.path: e.target or "" for e in listing if e.kind == "link"}
        _check_links(
            links,
            (e.path for e in admitted),
            trusted_paths=trusted_paths,
            protected_prefixes=protected_prefixes,
            product_root=product_root or os.path.realpath(attempt_dir),
            ignore_case=ignore_case,
        )
        kept = _source_entries(git, source, excluded, {e.path for e in admitted})
        lines: list[bytes] = []
        for mode, oid, path in kept:
            lines.append(f"{mode} {oid}\t{path}".encode("utf-8", "surrogateescape"))
        try:
            for entry in admitted:
                if entry.kind == "link":
                    oid = git.run(
                        "hash-object", "-w", "--no-filters", "--stdin",
                        stdin=(entry.target or "").encode("utf-8", "surrogateescape"),
                    ).decode().strip()
                    mode = "120000"
                else:
                    oid = git.run_streaming(
                        "hash-object", "-w", "--no-filters", "--stdin",
                        chunks=_entries.iter_confined_entry_chunks(attempt_dir, entry),
                    ).decode().strip()
                    mode = "100755" if entry.mode & stat.S_IXUSR else "100644"
                lines.append(f"{mode} {oid}\t{entry.path}".encode())
        except _entries.UnsafeContentError as error:
            raise _refuse_walk(error) from error
        # A second, empty index: the source's entries were only for the ignore check.
        env = {"GIT_INDEX_FILE": str(index_dir / "result-index")}
        git.run(
            "update-index", "-z", "--index-info", env=env, config=_PROTECT,
            stdin=b"".join(line + b"\0" for line in lines),
        )
        tree = git.run("write-tree", env=env, config=_PROTECT).decode().strip()
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)
    return Ingested(
        tree,
        tuple(sorted(e.path for e in admitted)),
        tuple(sorted(ignored)),
    )


def _source_entries(
    git: Any, source: str, excluded: tuple[str, ...], admitted: set[str]
) -> list[tuple[str, str, str]]:
    """``(mode, object id, path)`` the source commit keeps in the result.

    Entries under an excluded prefix, and gitlinks no admitted path overlaps.
    """
    out = git.run("ls-tree", "-r", "-z", "--full-tree", source)
    kept = []
    for record in out.split(b"\0"):
        if not record:
            continue
        meta, _, raw = record.partition(b"\t")
        mode, _kind, oid = meta.decode().split()
        path = raw.decode("utf-8", "surrogateescape")
        overlapped = any(a == path or a.startswith(path + "/") for a in admitted)
        if path.startswith(excluded) or (mode == "160000" and not overlapped):
            kept.append((mode, oid, path))
    return kept
