"""_supervisor_integration — held results and their ordered integration onto the product ref.

A finished concurrent attempt is recorded by its result identity (the tree the supervisor
ingested and the sha256 of the access line) as a *held result*: a record in the run store's
``held/`` directory and a ref ``refs/agentbundle/delivery/<run>/<token>/held/<attempt>`` that
names the tree. A held result is not an open attempt and its task is not complete.

Integration runs under one cross-process ``integration.lock`` in the run store, in the order
the sequential floor would have issued the tasks. Under the lock it reads the tip once and
uses that one read for the authority check, the check of the result's attested reads and
writes against what changed since its source commit, the three-way apply, the
compare-and-swap, and the records it writes:

1. a result whose source is the tip lands as it is;
2. otherwise a result without a complete access attestation is refused, and any other result
   is checked against the rename-aware changes from its source to the tip, then merged by
   ``git merge-tree --write-tree`` with its merge base pinned to the source, attributes read
   only from the empty tree, and no strategy option;
3. the merged tree must differ from the tip only at the paths the result changed, and every
   symbolic link in it must still pass the attempt-directory link rule;
4. the commit carries the attempt's trailer, and ``HEAD`` and the product ref move together
   from the observed tip.

Every refusal leaves the product ref, ``HEAD``, the index, and ``delivery/`` as they were,
writes one ``integration-conflict.v1``, and closes the attempt so its task is projected again
from the new tip. A kill at any write point converges through the next verb: a commit
carrying the attempt's trailer on the tip's first-parent chain since the source commit is
the landed operation, and the verb records it without a second commit.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from collections.abc import Generator, Iterable
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


_commit = _supervisor("_supervisor_commit.py")
_conc = _supervisor("_supervisor_concurrency.py")
sibling = _commit.sibling
kill_point = _commit.kill_point
SupervisorGitError = _commit.SupervisorGitError

__all__ = [
    "ALGORITHM",
    "INTEGRATE_IN_COMPLETION_ORDER",
    "MAX_CONFLICT_PATHS",
    "Refused",
    "apply_result",
    "drop_held",
    "finalize_landing",
    "find_landed",
    "hold",
    "integrate_ready",
    "list_held",
    "materialize",
    "recover_landed",
]

ALGORITHM = "git-merge-tree-write-tree"
SCHEMA_VERSION = 1
MAX_CONFLICT_PATHS = 1000  # the integration-diagnostic profile's path cap
MAX_PATH_BYTES = 1024
MAX_RECORD_BYTES = 1024 * 1024
_SHA_RE = re.compile(r"[0-9a-f]{40,64}")
_ATTEMPT_RE = re.compile(r"att-[0-9a-f]{16}")

# The completion-order seam: a test sets this by assignment to integrate in the order results
# finish instead of floor order. No environment variable, flag, policy key, or file reads it.
INTEGRATE_IN_COMPLETION_ORDER = False

_ACCESS_STATUS = {"A": "write", "D": "delete", "M": "mode", "T": "mode"}


class Refused(Exception):
    """An integration refusal: *reason* is a conflict-record reason, *paths* its cause."""

    def __init__(self, reason: str, paths: Iterable[str] = ()) -> None:
        super().__init__(reason)
        self.reason = reason
        self.paths = list(paths)


def _concurrent() -> ModuleType:
    return _supervisor("_supervisor_concurrent.py")


def _loop() -> ModuleType:
    return _supervisor("_supervisor_loop.py")


# ── the run store's records ─────────────────────────────────────────────────


def _store(ws: Any, run_id: str) -> Path:
    return Path(ws.git._store_dir(run_id))


def _put(ws: Any, run_id: str, directory: str, name: str, record: dict[str, Any]) -> None:
    folder = _concurrent()._directory(ws, run_id, directory)
    body = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sibling("_confined_mutation.py").confined_atomic_replace(
        _store(ws, run_id), folder / name, body
    )


def _get(ws: Any, run_id: str, directory: str, name: str) -> dict[str, Any] | None:
    store = _store(ws, run_id)
    path = store / directory / name
    if not os.path.lexists(path):
        return None
    fs = sibling("_file_safety.py")
    try:
        raw = fs.read_confined_regular_file(store, path, max_bytes=MAX_RECORD_BYTES)
        record = json.loads(bytes(raw))
    except (ValueError, OSError, fs.UnsafeContentError):
        return None
    return record if isinstance(record, dict) else None


def _remove(ws: Any, run_id: str, directory: str, name: str) -> None:
    (_store(ws, run_id) / directory / name).unlink(missing_ok=True)


@contextlib.contextmanager
def lock(ws: Any, run_id: str) -> Generator[None]:
    """The run store's cross-process ``integration.lock``, held across one integration."""
    store = ws.git.ensure_store(run_id)
    with sibling("_statelock.py").exclusive(
        Path(store) / "integration",
        timeout=float(ws.policy["run_lock_timeout_seconds"]),
        stale_after=float(ws.policy["run_lock_stale_seconds"]),
    ):
        yield


# ── held results ────────────────────────────────────────────────────────────


def held_ref_name(ws: Any, run_id: str, attempt_id: str) -> str:
    """The ref that names a held result's tree, beside the run's product ref."""
    product = ws.git.product_record(run_id)
    if product is None:
        raise SupervisorGitError("denied-product-record", "the run has no product ref yet")
    name = product.name.rsplit("/", 1)[0] + f"/held/{attempt_id}"
    if not _commit.HELD_REF_RE.fullmatch(name):
        raise SupervisorGitError("denied-product-record", "not a held ref name")
    return name


def _valid_held(record: dict[str, Any]) -> bool:
    return (
        record.get("schema_version") == SCHEMA_VERSION
        and isinstance(record.get("attempt_id"), str)
        and _ATTEMPT_RE.fullmatch(record["attempt_id"]) is not None
        and all(
            isinstance(record.get(k), str) and _SHA_RE.fullmatch(record[k])
            for k in ("source", "result_tree")
        )
        and isinstance(record.get("access_attestation_sha256"), str)
        and all(isinstance(record.get(k), str) for k in ("task_id", "revision", "request_id"))
        and isinstance(record.get("reads"), list)
        and isinstance(record.get("writes"), list)
        and isinstance(record.get("seq"), int)
    )


def list_held(ws: Any, run_id: str) -> list[dict[str, Any]]:
    """Every held result of the run, in the order they were recorded."""
    store = _store(ws, run_id)
    directory = store / "held"
    if not os.path.lexists(directory):
        return []
    fs = sibling("_file_safety.py")
    try:
        files = fs.list_confined_regular_files(store, directory, max_files=10_000)
    except (OSError, fs.UnsafeContentError):
        return []
    found = []
    for path in sorted(files):
        record = _get(ws, run_id, "held", path.name)
        if record and _valid_held(record) and path.name == record["attempt_id"] + ".json":
            found.append(record)
    return sorted(found, key=lambda r: r["seq"])


def hold(
    ws: Any, run_id: str, attempt: dict[str, Any], result: Any, step: str
) -> dict[str, Any]:
    """Record a finished attempt's result by its identity and name its tree by a ref.

    *attempt* is the attempt's consumed record. The held record carries the tree id, the access
    line's sha256, the attested sets, and the source commit; integration reads nothing else.
    """
    existing = list_held(ws, run_id)
    held = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "attempt_id": attempt["attempt_id"],
        "request_id": attempt["request_id"],
        "task_id": attempt["task_id"],
        "revision": attempt["revision"],
        "attempt": attempt["attempt"],
        "step": step,
        "source": attempt["source"],
        "result_tree": result.tree,
        "access_attestation_sha256": result.access_sha,
        "access_defect": result.access_defect,
        "reads": list(result.attested_reads),
        "writes": list(result.attested_writes),
        "seq": 1 + max((h["seq"] for h in existing), default=0),
    }
    name = attempt["attempt_id"] + ".json"
    _put(ws, run_id, "held", name, held)
    ref = held_ref_name(ws, run_id, attempt["attempt_id"])
    ws.git.run(
        "update-ref", "--no-deref", "-m", "work-supervisor: hold result", ref, result.tree,
        "0" * len(result.tree),
    )
    return held


def drop_held(ws: Any, run_id: str, attempt_id: str) -> None:
    """Remove a held result's ref and record once its operation has an outcome."""
    with contextlib.suppress(SupervisorGitError):
        ref = held_ref_name(ws, run_id, attempt_id)
        if ws.git.read_ref(ref)[0] != "missing":
            ws.git.run("update-ref", "--no-deref", "-d", ref)
    _remove(ws, run_id, "held", attempt_id + ".json")


# ── the pieces of the apply ─────────────────────────────────────────────────


def _byte_order(paths: Iterable[str]) -> list[str]:
    return sorted(set(paths), key=lambda p: p.encode("utf-8", "surrogateescape"))


def _empty_tree(git: Any) -> str:
    return git.run("hash-object", "-t", "tree", "--stdin", stdin=b"").decode().strip()


def _intervening(git: Any, source: str, tip: str, delivery: str) -> list[tuple[str, str]]:
    """``(access kind, path)`` for every end of every change from *source* to *tip*.

    Rename-aware: a rename contributes both its ends. The supervisor's own ``delivery/``
    records are left out, as they change with every integration.
    """
    out = git.run("diff", "--name-status", "-M", "-z", source, tip)
    parts = out.split(b"\0")
    ends: list[tuple[str, str]] = []
    index = 0
    while index < len(parts) and parts[index]:
        status = parts[index].decode("ascii", "replace")
        if status[0] in "RC":
            old, new = (p.decode("utf-8", "surrogateescape") for p in parts[index + 1 : index + 3])
            ends += [("rename-from", old), ("rename-to", new)]
            index += 3
            continue
        path = parts[index + 1].decode("utf-8", "surrogateescape")
        ends.append((_ACCESS_STATUS.get(status[0], "write"), path))
        index += 2
    prefix = delivery + "/"
    return [(kind, path) for kind, path in ends if not path.startswith(prefix)]


def _meeting(
    held: dict[str, Any], changes: list[tuple[str, str]], *, ignore_case: bool
) -> list[str]:
    """The changed paths that an attested read or write of *held* meets."""
    try:
        accesses = [
            *(_conc.Access(r["kind"], r["path"]) for r in held["reads"]),
            *(_conc.Access(w["kind"], w["path"]) for w in held["writes"]),
        ]
    except (ValueError, KeyError, TypeError) as exc:
        raise Refused("incomplete-attestation") from exc
    hit = []
    for kind, path in changes:
        change = _conc.Access(kind, path)
        if any(_conc.meets(a, change, ignore_case=ignore_case) for a in accesses):
            hit.append(path)
    return _byte_order(hit)


def _check_attributes(git: Any, paths: list[str]) -> None:
    """Refuse a ``merge`` attribute other than unspecified from any source an attempt controls."""
    if not paths:
        return
    out = git.run(
        "check-attr", f"--source={_empty_tree(git)}", "merge", "-z", "--stdin",
        stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in paths) + b"\0",
    )
    fields = out.split(b"\0")
    odd = [
        fields[i].decode("utf-8", "surrogateescape")
        for i in range(0, len(fields) - 2, 3)
        if fields[i + 2] != b"unspecified"
    ]
    if odd:
        raise Refused("merge-attribute", odd)


def _result_commit(ws: Any, source: str, tree: str) -> str:
    """A commit for the result tree with its source as parent, to name the merge side."""
    git = ws.git
    name, email = git.hardened.commit_identity()
    stamp = git._stamp(ws.clock())
    body = (
        f"tree {tree}\nparent {source}\nauthor {name} <{email}> {stamp}\n"
        f"committer {name} <{email}> {stamp}\n\nwork-supervisor: result\n"
    )
    return git.text("hash-object", "-t", "commit", "-w", "--stdin", stdin=body.encode()).strip()


def _merge(ws: Any, held: dict[str, Any], tip: str) -> str:
    """The pinned apply: ``merge-tree --write-tree`` with the base pinned and attributes empty."""
    git = ws.git
    source = held["source"]
    commit = _result_commit(ws, source, held["result_tree"])
    code, out = git.hardened.run_with_status(
        "merge-tree", "--write-tree", "-z", "--name-only", f"--merge-base={source}", tip, commit,
        config=(f"attr.tree={_empty_tree(git)}",), ok_codes=(0, 1),
    )
    fields = out.split(b"\0")
    merged = fields[0].decode("ascii", "replace")
    if code == 1:
        names = []
        for field in fields[1:]:
            if not field:
                break
            names.append(field.decode("utf-8", "surrogateescape"))
        raise Refused("content", names)
    if not _SHA_RE.fullmatch(merged):
        raise SupervisorGitError("denied-git-failed", "git merge-tree gave no tree")
    return merged


def _tree_links(git: Any, tree: str) -> dict[str, str]:
    """``path -> target text`` for every symbolic link in *tree*."""
    out = git.run("ls-tree", "-r", "-z", "--full-tree", tree)
    found: dict[str, str] = {}
    wanted: list[tuple[str, str]] = []
    for record in out.split(b"\0"):
        if not record:
            continue
        meta, _, raw = record.partition(b"\t")
        mode, _kind, oid = meta.decode().split()
        if mode == "120000":
            wanted.append((raw.decode("utf-8", "surrogateescape"), oid))
    if not wanted:
        return found
    request = b"".join(oid.encode() + b"\n" for _p, oid in wanted)
    data = git.run("cat-file", "--batch", stdin=request)
    position = 0
    for path, _oid in wanted:
        end = data.index(b"\n", position)
        size = int(data[position:end].split()[2])
        found[path] = data[end + 1 : end + 1 + size].decode("utf-8", "surrogateescape")
        position = end + 1 + size + 1
    return found


def apply_result(ws: Any, state: Any, held: dict[str, Any], tip: str) -> str:
    """The merged tree for *held* onto *tip*, or ``Refused`` with the reason; writes no ref.

    *tip* is the one read of the product ref the whole integration uses.
    """
    git = ws.git
    conc = _concurrent()
    source, tree = held["source"], held["result_tree"]
    ignore_case = conc._ignore_case(ws)
    changed = conc._changed(ws, source, tree)
    if tip != source:
        if held.get("access_defect"):
            raise Refused("incomplete-attestation")
        ends = _intervening(git, source, tip, git.delivery_rel)
        hit = _meeting(held, ends, ignore_case=ignore_case)
        if hit:
            raise Refused("meets", hit)
        entries = git.hardened.fresh_config_entries()
        if _commit._git.merge_config_keys(entries) or _commit._git.merge_driver_keys(entries):
            raise Refused("merge-config")
        _check_attributes(git, _byte_order([*(p for _k, p in ends), *changed]))
        merged = _merge(ws, held, tip)
    else:
        merged = tree
    listing = git.run("diff-tree", "-r", "-z", "--no-renames", "--name-only", tip, merged)
    differing = [p.decode("utf-8", "surrogateescape") for p in listing.split(b"\0") if p]
    outside = [p for p in differing if p not in changed]
    if outside:
        raise Refused("outside-changed-paths", _byte_order(outside))
    links = _tree_links(git, merged)
    try:
        _conc._check_links(
            links, list(links), trusted_paths=ws.attempts.trusted_paths(state),
            protected_prefixes=(git.delivery_rel, "delivery"), product_root=str(ws.root),
            ignore_case=ignore_case,
        )
    except _conc.AttemptRefused as exc:
        raise Refused("link-target", [exc.path] if exc.path else []) from exc
    return merged


# ── landing, replay, and the records ────────────────────────────────────────


def find_landed(ws: Any, run_id: str, held: dict[str, Any], tip: str) -> str | None:
    """The landed commit of *held*, found by its trailer on the tip's first-parent chain."""
    git = ws.git
    chain = git.text("rev-list", "--first-parent", f"{held['source']}..{tip}", "--").split()
    if not chain:
        return None
    on_chain = set(chain)
    for commit in git.supervisor_commits(run_id):
        if commit.sha in on_chain and (
            commit.trailers.get("Supervisor-Attempt") == held["attempt_id"]
        ):
            return str(commit.sha)
    return None


def recover_landed(ws: Any, run_id: str, sha: str) -> None:
    """Record, in the run store, a step this run built and moved the refs to but never recorded.

    That is the state a kill between the compare-and-swap and its record leaves: ``HEAD`` and
    the product ref name *sha*, whose parent is the recorded value. Anything else is left to
    the ref reconciliation.
    """
    git = ws.git
    record = git.product_record(run_id)
    if record is None or record.recorded == sha:
        return
    kind, value = git.read_ref(record.name)
    parent = git.text("rev-parse", "--verify", "--quiet", f"{sha}^", check=False).strip()
    if (kind, value) == ("commit", sha) and git.fresh_head() == sha and parent == record.recorded:
        git._record_landing(run_id, sha, None, False)


def _integration_record(
    ws: Any, held: dict[str, Any], tip: str, sha: str
) -> dict[str, Any]:
    version = ".".join(str(n) for n in ws.git.hardened.git_version)
    return {
        "schema_version": SCHEMA_VERSION,
        "operation_key": f"integrate:{held['attempt_id']}",
        "run_id": held["run_id"],
        "attempt_id": held["attempt_id"],
        "task_id": held["task_id"],
        "source_commit": held["source"],
        "observed_tip": tip,
        "result_commit": sha,
        "result_tree": held["result_tree"],
        "access_attestation_sha256": held["access_attestation_sha256"],
        "algorithm": {"name": ALGORITHM, "git_version": version},
    }


def materialize(ws: Any, sha: str) -> None:
    """Bring the index and working tree to commit *sha* (the tip), idempotently.

    Only the paths the commit changed outside ``delivery/`` are written; a path the commit
    removed is removed from the working tree, a link anywhere on its way refused.
    """
    git = ws.git
    prefix = git.delivery_rel + "/"
    paths = [p for p in git.touched_paths(sha) if not p.startswith(prefix)]
    held = git.tree_modes(sha)
    adds = sorted(p for p in paths if p in held)
    git.refresh_index(paths)
    kill_point("integration-materializing")
    if adds:
        git.hardened.run(
            "checkout-index", "-f", "-z", "--stdin",
            stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in adds) + b"\0",
        )
    for rel in sorted(p for p in paths if p not in held):
        _remove_working_file(Path(ws.root), rel)


def _remove_working_file(root: Path, rel: str) -> None:
    """Remove *rel* under *root* when every directory on its way is a plain directory."""
    current = root
    for part in rel.split("/")[:-1]:
        current = current / part
        try:
            if not stat.S_ISDIR(os.lstat(current).st_mode):
                return
        except OSError:
            return
    target = root.joinpath(*rel.split("/"))
    try:
        target.unlink()
    except FileNotFoundError:
        return
    parent = target.parent
    while parent != root:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def finalize_landing(ws: Any, held: dict[str, Any], sha: str) -> None:
    """Record a landed operation and bring the work tree to it; every step is idempotent.

    Runs after the compare-and-swap in the verb that made it, and again from the next verb
    when a kill cut it off, so the same steps converge to the same state either way.
    """
    run_id = held["run_id"]
    conc = _concurrent()
    parent = ws.git.text("rev-parse", "--verify", "--quiet", f"{sha}^", check=False).strip()
    kill_point("integration-before-record")
    if _get(ws, run_id, "integrations", held["attempt_id"] + ".json") is None:
        _put(
            ws, run_id, "integrations", held["attempt_id"] + ".json",
            _integration_record(ws, held, parent, sha),
        )
    materialize(ws, sha)
    record = conc.read_record(ws, run_id, held["request_id"])
    if record is not None:
        record.update(state="landed", commit=sha, result_tree=held["result_tree"])
        # An integration by exact source keeps the access check it rested on as its reason.
        if held.get("access_defect"):
            record["reason"] = held["access_defect"]
        else:
            record.pop("reason", None)
        conc._write(ws, run_id, record)
        if record.get("attempt_dir"):
            _conc.remove_attempt_directory(Path(record["attempt_dir"]))
    drop_held(ws, run_id, held["attempt_id"])
    if record is not None:
        conc._journal_outcome(ws, run_id, record, "landed")
    state = _loop().derive(ws)
    if state.refusal is None:
        ws.local.reconcile_events(state.run_id, state.commits)


def _diagnostic(ws: Any, held: dict[str, Any], tip: str, reason: str, paths: list[str]) -> bytes:
    """The ``integration-conflict.v1`` body: repository paths only, capped, and profile-checked."""
    ordered = [
        p for p in _byte_order(paths)
        if _conc.is_repository_path(p)
        and len(p.encode("utf-8", "surrogateescape")) <= MAX_PATH_BYTES
    ]
    total = len(set(paths))

    def body(listed: list[str]) -> bytes:
        record = {
            "schema_version": SCHEMA_VERSION,
            "operation_key": f"integrate:{held['attempt_id']}",
            "run_id": held["run_id"],
            "attempt_id": held["attempt_id"],
            "task_id": held["task_id"],
            "source_commit": held["source"],
            "observed_tip": tip,
            "reason": reason,
            "paths": listed,
            "path_count": total,
            "truncated": len(listed) < total,
        }
        return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")

    listed = ordered[:MAX_CONFLICT_PATHS]
    payload = body(listed)
    safety = sibling("_content_safety.py")
    verdict = safety.check_content_safety(
        "integration-diagnostic", payload, source_record_id=held["attempt_id"]
    )
    if not getattr(verdict, "accepted", False):
        payload = body([])  # a path the profile rejects never lands in the record
    return payload


def _refuse(
    ws: Any, held: dict[str, Any], tip: str, reason: str, paths: list[str]
) -> dict[str, Any]:
    """The refusal outcome: refs, index, and ``delivery/`` untouched; the task projects again."""
    run_id = held["run_id"]
    conc = _concurrent()
    folder = conc._directory(ws, run_id, "conflicts")
    sibling("_confined_mutation.py").confined_atomic_replace(
        _store(ws, run_id), folder / (held["attempt_id"] + ".json"),
        _diagnostic(ws, held, tip, reason, paths),
    )
    record = conc.read_record(ws, run_id, held["request_id"])
    if record is not None:
        record.update(state="conflict", reason=reason)
        conc._write(ws, run_id, record)
        if record.get("attempt_dir"):
            _conc.remove_attempt_directory(Path(record["attempt_dir"]))
        conc._journal_outcome(ws, run_id, record, "conflict")
    drop_held(ws, run_id, held["attempt_id"])
    return {"outcome": "conflict", "task": held["task_id"], "reason": reason}


def _task_of(state: Any, held: dict[str, Any]) -> dict[str, Any] | None:
    return next(
        (
            t for t in state.tasks
            if t["task_id"] == held["task_id"] and t["revision"] == held["revision"]
        ),
        None,
    )


def _cas_lost(ws: Any, run_id: str, tip: str) -> bool:
    """Whether ``HEAD`` or the product ref no longer names *tip*; direct reads."""
    git = ws.git
    record = git.product_record(run_id)
    kind, value = git.read_ref(record.name) if record is not None else ("missing", "")
    return git.fresh_head() != tip or (kind, value) != ("commit", tip)


def integrate_one(ws: Any, state: Any, held: dict[str, Any]) -> dict[str, Any]:
    """Integrate one held result onto the tip it reads once; the caller holds both locks."""
    git = ws.git
    run_id = state.run_id
    task = _task_of(state, held)
    if task is None:
        raise Refused("stale-authority")
    tip = git.fresh_head()
    kill_point("integration-start")
    try:
        record = git.product_record(run_id)
        if record is None or not git.product_ref_view(record)[2] or record.recorded != tip:
            raise Refused("stale-authority")
        merged = apply_result(ws, state, held, tip)
        tdd = _supervisor("_supervisor_tdd.py")
        evidence = ws.evidence_append([
            _loop().receipt(
                state, held["step"], criterion=f"task:{task['task_id']}",
                term=f"gate:{task['task_id']}:{task['revision']}", observation="task-gate",
                outcome="pass", fingerprint=git.product_tree(), revision=task["revision"],
            )
        ])
        try:
            sha = git.build_commit(
                run_id=run_id,
                step=held["step"],
                operation="implement",
                trailers={**tdd._trailers(task), "Supervisor-Attempt": held["attempt_id"]},
                appends={"evidence.jsonl": evidence},
                summary=f"{task['position']} {task['title']}"[:200],
                known_steps=state.steps,
                product_source=tip,
                base_tree=merged,
                parent=tip,
            )
        except (SupervisorGitError, _supervisor("_supervisor_admission.py").Refusal):
            if _cas_lost(ws, run_id, tip):
                raise Refused("cas-lost") from None
            raise
    except Refused as refused:
        return _refuse(ws, held, tip, refused.reason, refused.paths)
    if sha is None:
        raise _supervisor("_supervisor_admission.py").Refusal(
            "integration-conflict", "controller", "the step is already reachable"
        )
    finalize_landing(ws, held, sha)
    return {"outcome": "landed", "task": held["task_id"], "commit": str(sha)}


def _blocked(ws: Any) -> bool:
    """Whether a floor attempt is open: nothing moves the product ref beneath it."""
    issuance = ws.attempts.open
    return issuance is not None and issuance.kind != "run-concurrent"


def _next_step(ws: Any, run_id: str) -> dict[str, Any] | None:
    loop = _loop()
    state = loop.derive(ws)
    if state.refusal is not None or state.run_id != run_id:
        return None
    held = list_held(ws, run_id)
    if not held:
        return None
    tip = ws.git.fresh_head()
    for each in held:
        landed = find_landed(ws, run_id, each, tip)
        if landed is not None:
            recover_landed(ws, run_id, landed)
            finalize_landing(ws, each, landed)
            return {"outcome": "landed", "task": each["task_id"], "commit": landed}
    if _blocked(ws) or ws.git.change_set():
        return None
    first, _pending = loop._first_incomplete(state)
    for each in held:
        task = _task_of(state, each)
        if task is None:
            continue
        if INTEGRATE_IN_COMPLETION_ORDER or (
            first is not None and first["task_id"] == task["task_id"]
            and first["revision"] == task["revision"]
        ):
            return integrate_one(ws, state, each)
    return None


def integrate_ready(ws: Any) -> list[dict[str, Any]]:
    """Land every held result that is next in floor order, and record any that already landed.

    Takes ``integration.lock`` (the caller holds the run lock). Returns one outcome per
    result settled, in the order they were.
    """
    try:
        approvals = ws.approvals()
    except _supervisor("_supervisor_admission.py").Refusal:
        return []
    if not approvals:
        return []
    run_id = approvals[0]["run_id"]
    if not os.path.lexists(_store(ws, run_id) / "held"):
        return []
    outcomes: list[dict[str, Any]] = []
    with lock(ws, run_id):
        while True:
            step = _next_step(ws, run_id)
            if step is None:
                return outcomes
            outcomes.append(step)
