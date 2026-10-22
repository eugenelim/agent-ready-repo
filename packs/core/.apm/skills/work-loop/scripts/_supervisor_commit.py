"""_supervisor_commit — the supervisor's Git port and commit builder.

Every supervisor step is one commit built in a private index from ``HEAD``, the
admitted change-set paths, and appended ``delivery/`` lines. ``HEAD`` then moves
by compare-and-swap, and only after that are the ``delivery/`` working copies
written and the real index refreshed. A step whose id is already reachable from
``HEAD`` is skipped, so a crash at any point converges on the next call.

The working tree's ``delivery/`` files are never read as input. At entry, a
working copy that is a strict prefix of its ``HEAD`` version is lagging and is
rewritten from ``HEAD``; any other difference is a foreign edit.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import stat
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

__all__ = [
    "Commit",
    "supervisor_module",
    "GitPort",
    "SupervisorGitError",
    "kill_point",
    "set_kill_hook",
]

_SCRIPTS_DIR = Path(__file__).resolve().parent
_MAX_DELIVERY_BYTES = 64 * 1024 * 1024

_TRAILER_VALUE_RE = re.compile(r"[\x21-\x7e][\x20-\x7e]{0,511}")
_MAX_MADE_BYTES = 16 * 1024 * 1024
_RUN_ID_RE = re.compile(r"run-[0-9a-f]{16}")
_COMMIT_ID_RE = re.compile(r"[0-9a-f]{40,64}")

_KILL_HOOK: Callable[[str], None] | None = None


def set_kill_hook(hook: Callable[[str], None] | None) -> None:
    """Install a callable run at each named kill point; tests use it to crash."""
    global _KILL_HOOK
    _KILL_HOOK = hook


def kill_point(name: str) -> None:
    """Mark a crash boundary. A no-op unless a test installed a hook."""
    if _KILL_HOOK is not None:
        _KILL_HOOK(name)


@dataclass(frozen=True)
class Commit:
    """One supervisor commit reachable from HEAD."""

    sha: str
    committed_at: str
    trailers: dict[str, str]

    @property
    def step(self) -> str:
        return self.trailers.get("Supervisor-Step", "")

    @property
    def operation(self) -> str:
        return self.trailers.get("Supervisor-Operation", "")


def supervisor_module(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module.

    Registered under a name unique to this scripts directory, so two installed
    copies of the skill never share an instance.
    """
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


_git = supervisor_module("_supervisor_git.py")
SupervisorGitError = _git.SupervisorGitError

_SIBLINGS: dict[str, ModuleType] = {}


def sibling(filename: str) -> ModuleType:
    """Load a sibling script by path, once, unregistered in ``sys.modules``."""
    cached = _SIBLINGS.get(filename)
    if cached is not None:
        return cached
    path = _SCRIPTS_DIR / filename
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        alias = "_supervisor_commit_" + filename.removesuffix(".py").lstrip("_").replace("-", "_")
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path.name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    _SIBLINGS[filename] = module
    return module


def ensure_directory(root: Path, relative: str) -> Path:
    """Create *relative* under *root* one component at a time, refusing links."""
    current = root
    for part in relative.split("/"):
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            Path(current).mkdir(mode=0o755)
            info = os.lstat(current)
        if not stat.S_ISDIR(info.st_mode):
            raise SupervisorGitError(
                "denied-not-a-directory", f"{relative} is not a plain directory"
            )
    return current


class GitPort:
    """Git plumbing for one repository and one spec directory."""

    def __init__(self, root: Path, spec_rel: str, *, clock: Callable[[], str]) -> None:
        self.root = root
        self.spec_rel = spec_rel
        self.delivery_rel = f"{spec_rel}/delivery"
        self.clock = clock
        self.hardened = _git.HardenedGit(root)
        # Read-only lookups are cached for one invocation, which holds the run
        # lock; only this port's own HEAD move invalidates the HEAD-relative ones.
        self._head: str | None = None
        self._trees: dict[str, dict[str, str]] = {}
        self._blobs: dict[str, bytes] = {}
        self._commits: dict[tuple[str, str], list[Commit]] = {}
        self._touched: dict[str, list[str]] = {}

    # ── process boundary ────────────────────────────────────────────────────

    def run(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        stdin: bytes | None = None,
        check: bool = True,
        literal_pathspecs: bool = False,
    ) -> bytes:
        """Run ``git <args>`` through the hardened helper and return stdout bytes."""
        return self.hardened.run(
            *args, env=env, stdin=stdin, check=check, literal_pathspecs=literal_pathspecs
        )

    # ── the commits the supervisor made ─────────────────────────────────────

    def _store_rel(self, run_id: str) -> str:
        """The run's store directory, relative to the Git directory; the run id is checked here."""
        if not _RUN_ID_RE.fullmatch(run_id):
            raise SupervisorGitError("denied-invalid-run-id", "the run id is not a run id")
        return f"agentbundle-supervisor/{run_id}"

    def _store_dir(self, run_id: str) -> Path:
        return self.hardened.pins.git_dir / self._store_rel(run_id)

    def made_commits(self, run_id: str) -> set[str]:
        """Ids of the commits this run's supervisor built, from the store in the Git directory."""
        path = self._store_dir(run_id) / "made-commits"
        if not os.path.lexists(path):
            return set()
        fs = sibling("_file_safety.py")
        try:
            data = fs.read_confined_regular_file(path.parent, path, max_bytes=_MAX_MADE_BYTES)
        except fs.UnsafeContentError as exc:
            raise SupervisorGitError("denied-unsafe-path", f"made-commits: {exc}") from exc
        words = bytes(data).decode("ascii", "replace").split()
        return {w for w in words if _COMMIT_ID_RE.fullmatch(w)}

    def ensure_store(self, run_id: str) -> Path:
        """The run's store directory, created with a ``spec`` file naming this spec.

        Written when the directory is first created, before anything else is, so a
        run that never pinned can be tied to its spec without reading Git.
        """
        directory = ensure_directory(self.hardened.pins.git_dir, self._store_rel(run_id))
        record = directory / "spec"
        if not os.path.lexists(record):
            cm = sibling("_confined_mutation.py")
            try:
                cm.confined_create(directory, record, self.spec_rel.encode("utf-8"))
            except cm.MutationDenied as exc:
                if exc.denial_code != "denied-already-exists":
                    raise
        return directory

    def record_made(self, run_id: str, sha: str) -> None:
        """Append *sha* to the run's made-commit list, before the commit can become HEAD."""
        directory = self.ensure_store(run_id)
        cm = sibling("_confined_mutation.py")
        path = directory / "made-commits"
        if not os.path.lexists(path):
            cm.confined_create(directory, path, b"")
        cm.confined_append(directory, path, f"{sha}\n".encode("ascii"), max_bytes=_MAX_MADE_BYTES)

    def text(self, *args: str, **kwargs: object) -> str:
        return self.run(*args, **kwargs).decode("utf-8", "replace")  # type: ignore[arg-type]

    # ── reads ───────────────────────────────────────────────────────────────

    def head(self) -> str:
        if self._head is None:
            self._head = self.text("rev-parse", "--verify", "HEAD^{commit}").strip()
        return self._head

    def resolve(self, rev: str) -> str:
        """The commit id *rev* names: ``HEAD``, a commit id, or ``<commit>^``."""
        if rev == "HEAD":
            return self.head()
        if re.fullmatch(r"[0-9a-f]{40,64}", rev):
            return rev
        out = self.run("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}", check=False)
        return out.decode().strip()

    def _tree(self, rev: str) -> dict[str, str]:
        sha = self.resolve(rev)
        if not sha:
            return {}
        cached = self._trees.get(sha)
        if cached is None:
            out = self.run("ls-tree", "-r", "-z", "--full-tree", sha)
            cached = {}
            for record in out.split(b"\0"):
                if record:
                    meta, _, path = record.partition(b"\t")
                    cached[path.decode("utf-8", "surrogateescape")] = meta.split()[2].decode()
            self._trees[sha] = cached
        return cached

    def show(self, path: str, rev: str = "HEAD") -> bytes | None:
        """Return the bytes of *path* at *rev*, or None when it is absent."""
        oid = self._tree(rev).get(path)
        if oid is None:
            return None
        blob = self._blobs.get(oid)
        if blob is None:
            blob = self._blobs[oid] = self.run("cat-file", "blob", oid)
        return blob

    def tree_entries(self, rev: str = "HEAD") -> list[tuple[str, str]]:
        """``(path, object id)`` for every file at *rev*."""
        return sorted(self._tree(rev).items())

    def product_tree(self, rev: str = "HEAD") -> str:
        """A digest of the tree at *rev* without the spec directory."""
        prefix = self.spec_rel + "/"
        digest = hashlib.sha256()
        for path, oid in self.tree_entries(rev):
            if not path.startswith(prefix):
                digest.update(f"{path}\0{oid}\n".encode("utf-8", "surrogateescape"))
        return digest.hexdigest()

    def delivery_names(self, rev: str = "HEAD") -> list[str]:
        prefix = self.delivery_rel + "/"
        return sorted(
            p[len(prefix) :]
            for p in self._tree(rev)
            if p.startswith(prefix) and "/" not in p[len(prefix) :]
        )

    def supervisor_commits(self, run_id: str) -> list[Commit]:
        """Supervisor commits of *run_id* reachable from HEAD, oldest first."""
        if not _RUN_ID_RE.fullmatch(run_id):
            raise SupervisorGitError("denied-invalid-run-id", "run id is malformed")
        key = (run_id, self.head())
        if key in self._commits:
            return list(self._commits[key])
        out = self.run(
            "log",
            "--reverse",
            "-E",
            f"--grep=^Supervisor-Run: {run_id}$",
            "--format=%H%x1f%cI%x1f%(trailers:only=true,unfold=true)%x1e",
            "HEAD",
        )
        commits = []
        for record in out.decode("utf-8", "replace").split("\x1e"):
            record = record.strip("\n")
            if not record:
                continue
            sha, committed, trailer_text = record.split("\x1f", 2)
            trailers: dict[str, str] = {}
            for line in trailer_text.splitlines():
                key, sep, value = line.partition(": ")
                if sep and key.startswith("Supervisor-") and key not in trailers:
                    trailers[key] = value.strip()
            if trailers.get("Supervisor-Run") == run_id:
                commits.append(Commit(sha, committed, trailers))
        self._commits[key] = commits
        return list(commits)

    def touched_paths(self, sha: str) -> list[str]:
        cached = self._touched.get(sha)
        if cached is None:
            out = self.run("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "--root", sha)
            cached = [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]
            self._touched[sha] = cached
        return list(cached)

    # ── the change set ──────────────────────────────────────────────────────

    def change_set(self) -> list[str]:
        """What ``git add -A`` would stage against the current HEAD.

        Ignored files stay out, and so do the supervisor's own local and
        durable directories, whatever the ignore rules say.
        """
        excluded = (f"{self.spec_rel}/.supervisor/", ".loop-run/", f"{self.delivery_rel}/")
        with self._private_index() as env:
            self.run("add", "-A", env=env)
            out = self.run(
                "diff", "--cached", "--name-only", "-z", "--no-renames", "HEAD", env=env
            )
        paths = [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]
        return sorted(p for p in paths if not p.startswith(excluded))

    # ── the commit builder ──────────────────────────────────────────────────

    class _PrivateIndex:
        def __init__(self, port: GitPort) -> None:
            self.port = port
            self.path = ""

        def __enter__(self) -> dict[str, str]:
            fd, self.path = tempfile.mkstemp(prefix="work-supervisor-index-")
            os.close(fd)
            Path(self.path).unlink()
            env = {"GIT_INDEX_FILE": self.path}
            self.port.run("read-tree", "HEAD", env=env)
            return env

        def __exit__(self, *exc: object) -> None:
            for suffix in ("", ".lock"):
                Path(self.path + suffix).unlink(missing_ok=True)

    def _private_index(self) -> GitPort._PrivateIndex:
        return GitPort._PrivateIndex(self)

    @staticmethod
    def _stamp(when: str) -> str:
        """A commit timestamp, ``<epoch> <offset>``, from the clock's RFC 3339 text."""
        moment = datetime.fromisoformat(when.replace("Z", "+00:00"))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        offset = moment.utcoffset()
        minutes = int(offset.total_seconds() // 60) if offset is not None else 0
        sign = "-" if minutes < 0 else "+"
        return f"{int(moment.timestamp())} {sign}{abs(minutes) // 60:02d}{abs(minutes) % 60:02d}"

    def build_commit(
        self,
        *,
        run_id: str,
        step: str,
        operation: str,
        trailers: dict[str, str] | None = None,
        paths: Iterable[str] = (),
        appends: dict[str, bytes] | None = None,
        summary: str = "",
        known_steps: set[str] | None = None,
    ) -> str | None:
        """Commit one supervisor step, or return None when it is already reachable.

        *paths* are working-tree paths taken into the commit; *appends* maps a
        ``delivery/`` file name to bytes appended to its HEAD version.
        """
        steps = (
            known_steps
            if known_steps is not None
            else {c.step for c in self.supervisor_commits(run_id)}
        )
        if step in steps:
            return None
        all_trailers = {
            "Supervisor-Run": run_id,
            "Supervisor-Step": step,
            "Supervisor-Operation": operation,
            **(trailers or {}),
        }
        for key, value in all_trailers.items():
            if not _TRAILER_VALUE_RE.fullmatch(value):
                raise SupervisorGitError(
                    "denied-invalid-trailer", f"{key} value is not one safe line"
                )
        old = self.head()
        appended: dict[str, bytes] = {}
        with self._private_index() as env:
            path_list = sorted(set(paths))
            if path_list:
                self.run(
                    "add",
                    "-A",
                    "--pathspec-from-file=-",
                    "--pathspec-file-nul",
                    env=env,
                    literal_pathspecs=True,
                    stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in path_list),
                )
            for name, extra in sorted((appends or {}).items()):
                rel = f"{self.delivery_rel}/{name}"
                content = (self.show(rel) or b"") + extra
                blob = self.text("hash-object", "-w", "--stdin", stdin=content).strip()
                self.run("update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}", env=env)
                appended[rel] = content
            tree = self.text("write-tree", env=env).strip()
        message = f"work-supervisor: {operation}{(' ' + summary) if summary else ''}\n\n"
        message += "".join(f"{k}: {v}\n" for k, v in all_trailers.items())
        name, email = self.hardened.commit_identity()
        stamp = self._stamp(self.clock())
        body = (
            f"tree {tree}\nparent {old}\nauthor {name} <{email}> {stamp}\n"
            f"committer {name} <{email}> {stamp}\n\n{message}"
        )
        new = self.text(
            "hash-object", "-t", "commit", "-w", "--stdin", stdin=body.encode("utf-8")
        ).strip()
        self.record_made(run_id, new)
        kill_point("commit-built")
        try:
            self.run("update-ref", "-m", f"work-supervisor: {step}", "HEAD", new, old)
        finally:
            self._head = None
        kill_point("head-moved")
        self.write_delivery(appended)
        self.refresh_index(path_list + sorted(appended))
        kill_point("synced")
        return new

    # ── working copies ──────────────────────────────────────────────────────

    def write_delivery(self, files: dict[str, bytes]) -> None:
        """Write delivery working copies through the confined mutation port."""
        if not files:
            return
        cm = sibling("_confined_mutation.py")
        ensure_directory(self.root, self.delivery_rel)
        for rel, content in sorted(files.items()):
            cm.confined_atomic_replace(
                self.root, self.root / rel, content, max_bytes=_MAX_DELIVERY_BYTES
            )

    def refresh_index(self, paths: list[str]) -> None:
        """Make the real index match HEAD for *paths*."""
        if not paths:
            return
        self.run(
            "reset",
            "-q",
            "--pathspec-from-file=-",
            "--pathspec-file-nul",
            "HEAD",
            literal_pathspecs=True,
            stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in sorted(set(paths))),
        )

    def read_working(self, rel: str) -> bytes | None:
        """Read a working-tree file through the confined reader, or None if absent."""
        fs = sibling("_file_safety.py")
        if not os.path.lexists(self.root / rel):
            return None
        try:
            return bytes(
                fs.read_confined_regular_file(
                    self.root, self.root / rel, max_bytes=_MAX_DELIVERY_BYTES
                )
            )
        except FileNotFoundError:
            return None
        except fs.UnsafeContentError as exc:
            raise SupervisorGitError("denied-unsafe-path", f"{rel}: {exc}") from exc

    def delivery_lag(self) -> tuple[dict[str, bytes], list[str]]:
        """Return ``(lagging files to rewrite, foreign files)`` for ``delivery/``."""
        lagging: dict[str, bytes] = {}
        foreign: list[str] = []
        head_names = set(self.delivery_names())
        for name in sorted(head_names):
            rel = f"{self.delivery_rel}/{name}"
            committed = self.show(rel) or b""
            working = self.read_working(rel)
            if working == committed:
                continue
            if working is None or committed.startswith(working):
                lagging[rel] = committed
            else:
                foreign.append(rel)
        directory = self.root / self.delivery_rel
        if directory.is_dir() and not directory.is_symlink():
            for entry in sorted(e.name for e in directory.iterdir()):
                if entry not in head_names:
                    foreign.append(f"{self.delivery_rel}/{entry}")
        return lagging, foreign

    def sync(self, last_commit: str | None) -> list[str]:
        """Rewrite lagging delivery copies and refresh the index for the last step.

        Returns the foreign delivery paths, which the caller refuses on.
        """
        lagging, foreign = self.delivery_lag()
        if foreign:
            return foreign
        self.write_delivery(lagging)
        if last_commit is not None:
            self.refresh_index(self.touched_paths(last_commit))
        return []
