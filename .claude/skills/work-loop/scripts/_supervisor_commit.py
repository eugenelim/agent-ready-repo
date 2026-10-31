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

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

__all__ = [
    "Commit",
    "append_note",
    "PRODUCT_REF_RE",
    "ProductRecord",
    "set_update_hook",
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
PRODUCT_REF_RE = re.compile(r"refs/agentbundle/delivery/run-[0-9a-f]{16}/[0-9a-f]{16}/product")
_VOID_REF_RE = re.compile(r"refs/agentbundle/delivery/run-[0-9a-f]{16}/voided")
_PRODUCT_FILE = "product-ref"
_PENDING_FILE = "pending-commit"
_VOID_FILE = "pending-void"
_VOID_ANY = "*"
_SYMREF_RE = re.compile(r"ref: (\S+)\s*")

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
class ProductRecord:
    """The run store's record of the product ref: its name, recorded value, and pending value.

    *recorded* is ``None`` while the approval step that creates the ref is being
    committed; *pending* is the commit a step's transaction is moving both refs to.
    """

    name: str
    recorded: str | None
    pending: str | None


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
set_update_hook = _git.set_update_hook

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


def append_note(error: BaseException, note: str) -> None:
    """Show *note* beside the refusal *error* carries, never instead of it."""
    if hasattr(error, "detail"):
        error.detail = f"{error.detail}; {note}"
    elif error.args:
        error.args = (f"{error.args[0]}; {note}", *error.args[1:])


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
        """Ids of the commits this run's supervisor built that landed in its history."""
        return set(self.made_list(run_id))

    def _made_entries(self, run_id: str) -> list[str]:
        """The made-commit file's entries, in order."""
        path = self._store_dir(run_id) / "made-commits"
        if not os.path.lexists(path):
            return []
        fs = sibling("_file_safety.py")
        try:
            data = fs.read_confined_regular_file(path.parent, path, max_bytes=_MAX_MADE_BYTES)
        except fs.UnsafeContentError as exc:
            raise SupervisorGitError("denied-unsafe-path", f"made-commits: {exc}") from exc
        words = bytes(data).decode("ascii", "replace").split()
        return [w for w in words if _COMMIT_ID_RE.fullmatch(w)]

    def made_list(self, run_id: str) -> list[str]:
        """The run's landed commits in the order they were built.

        A commit becomes made only once its transaction has moved the refs. A step cut
        off between that move and the append is still pending in the store, and counts
        here only when the product ref names it: the ref moves only inside the
        supervisor's transaction, so it alone proves the step landed. ``HEAD`` naming
        a pending commit proves nothing, and a run with no product ref has no proof,
        so that commit is foreign history. A refused step is neither made nor pending.
        """
        entries = self._made_entries(run_id)
        pending = self.pending_commit(run_id)
        if pending is not None and pending not in entries and self._ref_names(run_id, pending):
            entries.append(pending)
        return entries

    def _ref_names(self, run_id: str, sha: str) -> bool:
        """Whether the run's product ref names *sha*, by direct file reads."""
        record = self.product_record(run_id)
        return record is not None and self.read_ref(record.name) == ("commit", sha)

    def pending_commit(self, run_id: str, *, masked: bool = True) -> str | None:
        """The commit a step's transaction is moving the refs to, while it is in flight.

        Never honored while the store holds a void mark for it.
        """
        directory = self._store_dir(run_id)
        path = directory / _PENDING_FILE
        if not os.path.lexists(path):
            return None
        fs = sibling("_file_safety.py")
        try:
            data = fs.read_confined_regular_file(directory, path, max_bytes=256)
        except fs.UnsafeContentError as exc:
            raise SupervisorGitError("denied-unsafe-path", f"pending-commit: {exc}") from exc
        sha = bytes(data).decode("ascii", "replace").strip()
        if not _COMMIT_ID_RE.fullmatch(sha):
            return None
        if masked and self._void_covers(run_id, sha):
            return None
        return sha

    def _write_pending(self, run_id: str, sha: str) -> None:
        directory = self.ensure_store(run_id)
        sibling("_confined_mutation.py").confined_atomic_replace(
            directory, directory / _PENDING_FILE, f"{sha}\n".encode("ascii")
        )

    def clear_pending(self, run_id: str) -> None:
        """Forget the in-flight commit; a failure here is not hidden."""
        (self._store_dir(run_id) / _PENDING_FILE).unlink(missing_ok=True)

    def settle_pending(self, run_id: str) -> None:
        """Resolve a step a crash cut off: record it as made if the product ref names it.

        Otherwise it never landed and is forgotten, except while the product ref record
        still names it pending, because ``reconcile`` finishes that move first.
        """
        pending = self.pending_commit(run_id)
        if pending is None:
            return
        with self.settle_writes(run_id):
            if self._ref_names(run_id, pending):
                if pending not in self._made_entries(run_id):
                    self.record_made(run_id, pending)
                self.clear_pending(run_id)
                return
            record = self.product_record(run_id)
            if record is None or record.pending != pending:
                self.clear_pending(run_id)

    # ── the one guard for run-store writes on a refusal, clear, or settle path ──

    def _void_ref(self, run_id: str) -> str:
        return f"refs/agentbundle/delivery/{run_id}/voided"

    def voided(self, run_id: str) -> str | None:
        """The pending commit the store has voided, ``"*"`` for any, or ``None``.

        The mark is a store file; when the store cannot take it, a ref beside the product
        ref, which Git writes elsewhere. Direct reads only.
        """
        path = self._store_dir(run_id) / _VOID_FILE
        if os.path.lexists(path):
            fs = sibling("_file_safety.py")
            try:
                data = fs.read_confined_regular_file(path.parent, path, max_bytes=256)
            except (fs.UnsafeContentError, OSError):
                return _VOID_ANY
            sha = bytes(data).decode("ascii", "replace").strip()
            return sha if _COMMIT_ID_RE.fullmatch(sha) else _VOID_ANY
        kind, value = self.read_ref(self._void_ref(run_id))
        if kind == "commit":
            return value
        return _VOID_ANY if kind != "missing" else None

    def _void_covers(self, run_id: str, sha: str) -> bool:
        void = self.voided(run_id)
        return void is not None and void in (_VOID_ANY, sha)

    def _mark_void(self, run_id: str, sha: str) -> None:
        """Make the voiding durable before anything else is cleaned up."""
        try:
            directory = self.ensure_store(run_id)
            sibling("_confined_mutation.py").confined_atomic_replace(
                directory, directory / _VOID_FILE, f"{sha}\n".encode("ascii")
            )
        except Exception:  # noqa: BLE001 - fall back to the other medium
            self.run("update-ref", "--no-deref", "-m", "work-supervisor: void a refused step",
                     self._void_ref(run_id), sha)

    def _unmark_void(self, run_id: str) -> None:
        (self._store_dir(run_id) / _VOID_FILE).unlink(missing_ok=True)
        if self.read_ref(self._void_ref(run_id))[0] != "missing":
            self.run("update-ref", "--no-deref", "-d", self._void_ref(run_id))

    def void_step(
        self, run_id: str, sha: str, reset: ProductRecord | None, refusal: BaseException
    ) -> None:
        """Void a refused step: mark it, reset the record, clear pending; fail closed.

        The mark goes first and stays until every cleanup has succeeded, so while the
        store is inconsistent no trust check honors the step's pending value and every
        verb but ``status`` refuses ``denied-product-record``. A failure never replaces
        *refusal*: it is shown beside it.
        """
        failures: list[BaseException] = []
        for action in (
            lambda: self._mark_void(run_id, sha),
            lambda: reset is not None and self.write_product_record(run_id, reset),
            lambda: self.clear_pending(run_id),
        ):
            try:
                action()
            except Exception as failure:  # noqa: BLE001 - noted beside the refusal
                failures.append(failure)
        if not failures:
            try:
                self._unmark_void(run_id)
                return
            except Exception as failure:  # noqa: BLE001 - the next verb removes it
                failures.append(failure)
        kinds = ", ".join(sorted({type(f).__name__ for f in failures}))
        append_note(
            refusal,
            f"the run store could not be cleaned up ({kinds}); every verb but status refuses "
            "denied-product-record until it is repaired",
        )

    @contextlib.contextmanager
    def settle_writes(self, run_id: str) -> Generator[None]:
        """Run store writes that clear or settle a step; a failure refuses, closed.

        The step stays recoverable (its pending value is honored only while the product ref
        names it), and the next verb settles it again.
        """
        try:
            yield
        except (SupervisorGitError, KeyboardInterrupt):
            raise
        except Exception as failure:
            if hasattr(failure, "owner"):  # a Refusal passes through
                raise
            raise SupervisorGitError(
                "denied-product-record",
                f"the run store could not be written ({type(failure).__name__}); make "
                f"{self._store_dir(run_id)} writable and run any verb: the supervisor settles "
                "the step it was committing",
            ) from failure

    def repair_voided(self) -> None:
        """Before any verb but ``status``: finish the cleanup of a voided step, or refuse.

        A run store of this spec that holds a void mark is repaired from the mark: the
        voided pending value leaves the product record and the pending file, and the mark
        goes. When the store still cannot be written, every verb refuses
        ``denied-product-record`` and names the restore.
        """
        base = self.hardened.pins.git_dir / "agentbundle-supervisor"
        if not base.is_dir():
            return
        for entry in sorted(base.iterdir()):
            if not _RUN_ID_RE.fullmatch(entry.name):
                continue
            try:
                spec = bytes(sibling("_file_safety.py").read_confined_regular_file(
                    entry, entry / "spec", max_bytes=4096)).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001 - the entry point already refuses a bad store
                continue
            void = self.voided(entry.name) if spec == self.spec_rel else None
            if void is None:
                continue
            try:
                record = self.product_record(entry.name, masked=False)
                if record is not None and record.pending is not None and void in (
                    _VOID_ANY, record.pending
                ):
                    self.write_product_record(
                        entry.name, ProductRecord(record.name, record.recorded, None)
                    )
                pending = self.pending_commit(entry.name, masked=False)
                if pending is not None and void in (_VOID_ANY, pending):
                    self.clear_pending(entry.name)
                self._unmark_void(entry.name)
            except Exception as failure:
                raise SupervisorGitError(
                    "denied-product-record",
                    f"the run store {entry} could not be repaired after a refused step "
                    f"({type(failure).__name__}); make it writable, then run any verb: the "
                    f"supervisor clears the voided pending commit {void}. Until then every "
                    "verb but status refuses",
                ) from failure

    # ── the product ref ─────────────────────────────────────────────────────

    @staticmethod
    def new_product_name(run_id: str) -> str:
        """A product ref name for a run admission; the token is fresh each time."""
        if not _RUN_ID_RE.fullmatch(run_id):
            raise SupervisorGitError("denied-invalid-run-id", "the run id is not a run id")
        return f"refs/agentbundle/delivery/{run_id}/{secrets.token_hex(8)}/product"

    def product_record(self, run_id: str, *, masked: bool = True) -> ProductRecord | None:
        """The run's recorded product ref, or ``None`` when the run has none.

        A pending value the store has voided (its step was refused) reads as none, so no
        trust check honors it.
        """
        directory = self._store_dir(run_id)
        path = directory / _PRODUCT_FILE
        if not os.path.lexists(path):
            return None
        fs = sibling("_file_safety.py")
        try:
            raw = json.loads(
                bytes(fs.read_confined_regular_file(directory, path, max_bytes=65536))
            )
        except (ValueError, fs.UnsafeContentError, OSError) as exc:
            raise SupervisorGitError(
                "denied-product-record", "the product ref record is unreadable", unverifiable=True
            ) from exc
        ok = (
            isinstance(raw, dict)
            and raw.get("run_id") == run_id
            and isinstance(raw.get("name"), str)
            and PRODUCT_REF_RE.fullmatch(raw["name"]) is not None
            and all(
                v is None or (isinstance(v, str) and _COMMIT_ID_RE.fullmatch(v) is not None)
                for v in (raw.get("recorded"), raw.get("pending"))
            )
        )
        if not ok:
            raise SupervisorGitError(
                "denied-product-record", "the product ref record is malformed", unverifiable=True
            )
        pending = raw.get("pending")
        if masked and pending is not None and self._void_covers(run_id, pending):
            pending = None
        return ProductRecord(raw["name"], raw.get("recorded"), pending)

    def write_product_record(self, run_id: str, record: ProductRecord) -> None:
        """Replace the run's product ref record atomically, in the confined store."""
        if not PRODUCT_REF_RE.fullmatch(record.name):
            raise SupervisorGitError("denied-product-record", "not a product ref name")
        directory = self.ensure_store(run_id)
        body = json.dumps(
            {
                "schema_version": 1,
                "run_id": run_id,
                "name": record.name,
                "recorded": record.recorded,
                "pending": record.pending,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        sibling("_confined_mutation.py").confined_atomic_replace(
            directory, directory / _PRODUCT_FILE, body
        )

    def read_ref(self, name: str) -> tuple[str, str]:
        """A product ref by direct file reads, never echoing what the file holds.

        Returns ``("commit", id)``, or a fixed kind label with an empty value:
        ``symbolic``, ``malformed`` (including a duplicated packed entry), or
        ``missing``. A loose ref wins over ``packed-refs``, as in Git. No Git
        process runs.
        """
        if not (PRODUCT_REF_RE.fullmatch(name) or _VOID_REF_RE.fullmatch(name)):
            raise SupervisorGitError("denied-product-record", "not a product ref name")
        fs = sibling("_file_safety.py")
        common = self.hardened.pins.common_dir
        path = common.joinpath(*name.split("/"))
        try:
            info = os.lstat(path)
        except (FileNotFoundError, NotADirectoryError):
            info = None
        if info is not None:
            if not stat.S_ISREG(info.st_mode):
                return "malformed", ""
            try:
                text = bytes(fs.read_confined_regular_file(common, path, max_bytes=4096))
            except (fs.UnsafeContentError, OSError):
                return "malformed", ""
            body = text.decode("utf-8", "replace").strip()
            if _COMMIT_ID_RE.fullmatch(body):
                return "commit", body
            return ("symbolic", "") if _SYMREF_RE.fullmatch(body) else ("malformed", "")
        packed = common / "packed-refs"
        if os.path.lexists(packed):
            try:
                data = bytes(
                    fs.read_confined_regular_file(common, packed, max_bytes=_MAX_DELIVERY_BYTES)
                )
            except (fs.UnsafeContentError, OSError) as exc:
                raise SupervisorGitError(
                    "denied-git-control-state", "packed-refs cannot be read", unverifiable=True
                ) from exc
            # Split as Git does, on newlines only; any other framing or a repeated
            # entry for this name is a state Git might read differently.
            found_ids = []
            for line in data.split(b"\n"):
                sha, _, found = line.decode("utf-8", "replace").partition(" ")
                if found == name:
                    found_ids.append(sha)
            if len(found_ids) > 1 or (found_ids and not _COMMIT_ID_RE.fullmatch(found_ids[0])):
                return "malformed", ""
            if found_ids:
                return "commit", found_ids[0]
        return "missing", ""

    def product_ref_view(self, record: ProductRecord) -> tuple[str, str, bool]:
        """The record's ref as ``(kind, value, trusted)``: the one rule for what is trusted.

        The ref is trusted at its recorded or pending value; while the approval step
        that creates it is in flight, a missing ref with a pending value is trusted too.
        """
        kind, value = self.read_ref(record.name)
        trusted = (kind == "commit" and value in (record.recorded, record.pending)) or (
            kind == "missing" and record.recorded is None and record.pending is not None
        )
        return kind, value, trusted

    @staticmethod
    def restore_command(name: str, kind: str, value: str | None) -> str:
        """The command that puts a product ref back to *value* (or removes it when it has none).

        A symbolic or malformed ref is deleted without following it first, so the ref
        is replaced, never written through.
        """
        if not value:
            return f"git update-ref --no-deref -d {name}"
        if kind in ("symbolic", "malformed"):
            return (
                f"git update-ref --no-deref -d {name} && git update-ref --no-deref {name} {value}"
            )
        return f"git update-ref --no-deref {name} {value}"

    def create_ref(self, name: str, commit: str) -> None:
        """Create the product ref at *commit*, replacing and never following a symbolic ref."""
        self.run("update-ref", "--no-deref", "-m", "work-supervisor: create product ref",
                 name, commit, "0" * len(commit))

    def move_head(self, new: str, old: str, message: str) -> None:
        """Move ``HEAD`` (through the branch it names) from *old* to *new* by compare-and-swap."""
        try:
            self.run("update-ref", "-m", message, "HEAD", new, old)
        finally:
            self._head = None

    def object_id(self, path: str, rev: str) -> str | None:
        """The object id of *path* at *rev*, or ``None`` when it is absent there."""
        return self._tree(rev).get(path)

    def is_ancestor(self, older: str, newer: str) -> bool:
        """Whether commit *older* is *newer* or reachable from it."""
        if older == newer:
            return True
        out = self.run("merge-base", older, newer, check=False)
        return out.decode().strip() == older

    def rev_list(self, older: str, newer: str) -> list[str]:
        """The commits reachable from *newer* and not from *older*, newest first."""
        return self.text("rev-list", f"{older}..{newer}").split()

    def made_only(self, run_id: str, older: str, newer: str) -> bool:
        """Whether *newer* descends from *older* through commits this run made only."""
        if not self.is_ancestor(older, newer):
            return False
        made = self.made_commits(run_id)
        return all(sha in made for sha in self.rev_list(older, newer))

    def update_refs(self, new: str, old: str, name: str, product_old: str | None) -> None:
        """Move ``HEAD`` (through the branch it names) and the product ref in one transaction.

        A stale expected value on either ref refuses both. The product ref is
        written with ``no-deref``, so a symbolic ref is replaced, never followed.
        """
        zero = "0" * len(new)
        record = (
            b"start\0"
            + f"update HEAD\0{new}\0{old}\0".encode("ascii")
            + b"option no-deref\0"
            + f"update {name}\0{new}\0{product_old or zero}\0".encode("ascii")
            + b"prepare\0commit\0"
        )
        self.run("update-ref", "-z", "--stdin", "-m", "work-supervisor: step", stdin=record)

    def ensure_store(self, run_id: str) -> Path:
        """The run's store directory, born whole with a ``spec`` file naming this spec.

        A new directory is built under a temporary sibling name (which no run id
        matches), its spec record written inside, and then renamed into place, so a
        crash never leaves a run directory without its spec record. When another
        process won the rename, or the directory already stood, its spec record is
        verified instead.
        """
        relative = self._store_rel(run_id)
        git_dir = self.hardened.pins.git_dir
        base = ensure_directory(git_dir, relative.rsplit("/", 1)[0])
        final = base / run_id
        if not os.path.lexists(final):
            temp = base / f".tmp-{run_id}-{secrets.token_hex(8)}"
            temp.mkdir(mode=0o755)
            try:
                cm = sibling("_confined_mutation.py")
                cm.confined_create(temp, temp / "spec", self.spec_rel.encode("utf-8"))
                kill_point("store-built")
                temp.rename(final)
            except Exception:
                # A process kill leaves the temporary directory, which is harmless:
                # no run id matches its name.
                shutil.rmtree(temp, ignore_errors=True)
                if not os.path.lexists(final):  # not a lost race: another process won it
                    raise
        directory = ensure_directory(git_dir, relative)
        self._verify_store_spec(directory)
        return directory

    def _verify_store_spec(self, directory: Path) -> None:
        """Refuse a store directory whose spec record is absent or names another spec."""
        fs = sibling("_file_safety.py")
        try:
            data = fs.read_confined_regular_file(directory, directory / "spec", max_bytes=4096)
        except (fs.UnsafeContentError, OSError) as exc:
            raise SupervisorGitError(
                "denied-store-spec", f"the run's store has no readable spec record: {exc}"
            ) from exc
        if bytes(data).decode("utf-8", "replace") != self.spec_rel:
            raise SupervisorGitError(
                "denied-store-spec", "the run's store records another spec"
            )

    def _append_id(self, run_id: str, name: str, sha: str) -> None:
        directory = self.ensure_store(run_id)
        cm = sibling("_confined_mutation.py")
        path = directory / name
        if not os.path.lexists(path):
            cm.confined_create(directory, path, b"")
        cm.confined_append(directory, path, f"{sha}\n".encode("ascii"), max_bytes=_MAX_MADE_BYTES)

    def record_made(self, run_id: str, sha: str) -> None:
        """Append *sha* to the run's made-commit list, once its transaction has moved the refs."""
        self._append_id(run_id, "made-commits", sha)

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
        contents: dict[str, bytes | None] | None = None,
        appends: dict[str, bytes] | None = None,
        summary: str = "",
        known_steps: set[str] | None = None,
        product_source: str | None = None,
        create_ref: str | None = None,
        adopting: bool = False,
        product_old: str | None = None,
    ) -> str | None:
        """Commit one supervisor step, or return None when it is already reachable.

        *paths* are working-tree paths taken into the commit; *contents* maps a path
        to the exact bytes to commit there (``None`` removes it), staged without
        reading the working tree again; *appends* maps a ``delivery/`` file name to
        bytes appended to its HEAD version.

        A run with a recorded product ref moves it with ``HEAD`` in one transaction.
        *product_source* is the commit a product result was issued against: the
        transaction expects the product ref to still name it. *create_ref* names a
        product ref that the transaction creates. *adopting* lets ``HEAD`` differ
        from the product ref, which is expected to name *product_old*.
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
        exact = contents or {}
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
            for rel, data in sorted(exact.items()):
                if data is None:
                    self.run("update-index", "--force-remove", "--", rel, env=env)
                    continue
                blob = self.text("hash-object", "-w", "--stdin", stdin=data).strip()
                self.run("update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}", env=env)
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
        # Pending until the refs move: a refused or interrupted step is never history.
        before = self.product_record(run_id)
        reset = (
            ProductRecord(create_ref, None, None)
            if create_ref is not None
            else (ProductRecord(before.name, before.recorded, None) if before else None)
        )
        with self.settle_writes(run_id):
            self._write_pending(run_id, new)
        kill_point("commit-built")
        try:
            self._move(run_id, new, old, step, create_ref, product_source, adopting, product_old)
        except Exception as refusal:
            self.void_step(run_id, new, reset, refusal)
            raise
        kill_point("refs-moved")
        with self.settle_writes(run_id):
            self._settle_record(run_id, new)
            if new not in self._made_entries(run_id):
                self.record_made(run_id, new)
            self.clear_pending(run_id)
        kill_point("made-recorded")
        self.write_delivery(appended)
        self.refresh_index(path_list + sorted(exact) + sorted(appended))
        kill_point("synced")
        return new

    def _move(
        self,
        run_id: str,
        new: str,
        old: str,
        step: str,
        create_ref: str | None,
        source: str | None,
        adopting: bool,
        product_old: str | None,
    ) -> None:
        """Move ``HEAD`` and, when the run records one, the product ref to *new*."""
        record = self.product_record(run_id)
        try:
            if create_ref is None and record is None:
                kill_point("pending-recorded")
                self.move_head(new, old, f"work-supervisor: {step}")
                return
            if create_ref is not None:
                name, expected = create_ref, None
                recorded = None
            else:
                assert record is not None
                name, recorded = record.name, record.recorded
                if record.pending is not None or (recorded != old and not adopting):
                    raise SupervisorGitError(
                        "denied-integration-state",
                        "HEAD and the product ref are not reconciled; run next",
                    )
                expected = product_old if adopting else (source or recorded)
            with self.settle_writes(run_id):
                self.write_product_record(run_id, ProductRecord(name, recorded, new))
            kill_point("pending-recorded")
            try:
                self.update_refs(new, old, name, expected)
            except SupervisorGitError as exc:
                self._diagnose(exc, name, expected, recorded)
                raise
        finally:
            self._head = None

    def _diagnose(
        self, exc: SupervisorGitError, name: str, expected: str | None, recorded: str | None
    ) -> None:
        """Turn a failed compare-and-swap on the product ref into ``integration-conflict``.

        Read by direct file reads: a Git call here would meet the attempt's control
        check, which refuses the very ref move being reported.
        """
        if exc.code != "denied-git-failed":
            return
        kind, value = self.read_ref(name)
        if (kind, value) == (("commit", expected) if expected else ("missing", "")):
            return
        was = f"commit {expected}" if expected else "absent"
        if kind == "commit" and value == recorded:
            # A supervisor step moved the ref: nothing is wrong, the request is just old.
            detail = (
                f"{name} moved to commit {value}, which the run recorded, after this "
                f"result's request was issued against {was}. Nothing was committed and your "
                "files are kept; run next, which issues the request again"
            )
        else:
            now = f"commit {value}" if kind == "commit" else kind
            detail = (
                f"{name} is {now}, not the run's recorded value {recorded}. Nothing was "
                "committed and your files are kept; restore it with: "
                f"{self.restore_command(name, kind, recorded)}"
            )
        raise supervisor_module("_supervisor_admission.py").Refusal(
            "integration-conflict", "controller", detail
        ) from exc

    def _settle_record(self, run_id: str, new: str) -> None:
        """Record *new* as the product ref's value and clear the pending commit."""
        record = self.product_record(run_id)
        if record is not None and record.pending == new:
            self.write_product_record(run_id, ProductRecord(record.name, new, None))

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
