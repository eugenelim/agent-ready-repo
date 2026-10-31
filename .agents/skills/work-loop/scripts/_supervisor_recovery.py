"""_supervisor_recovery — recovery after a not-red stub, and product-ref integration.

A ``write-stub`` result refused as not red closes its attempt. This module owns
what follows: it observes and discards the files the attempt and its launch left,
records in the supervisor store that a named human's confirmation is owed, and
turns the next change to a trusted file into a ``human-decision`` that carries the
diff and binds a digest of the exact bytes. The ``replan`` commits only when a human
confirms, the change set is exactly the bound files, and the commit holds the very
bytes the digest covered. A decline is recorded with its digest and commits nothing:
``next`` refuses until the trusted files match ``HEAD`` again, whatever they hold in
between. The restore brings back the fence that was not red, so ``next`` reissues
``write-stub`` and the stub runs again; only once that attempt is refused and closed
again does a different fence edit open a new confirmation. A path the discard could
not remove is recorded, shown in ``status``, and blocks every step until the
controller removes it or restores it to ``HEAD``; rewriting it to other bytes does not
clear it.

The second half of this module classifies how ``HEAD`` and the run's product ref
relate before every verb derives anything. It completes a transaction that moved
one ref, creates the ref for a run that has none, moves ``HEAD`` forward over
commits the supervisor made, refuses a ref that is not at its recorded value, and
turns any other difference into an owner decision, ``history-adoption``, whose
answer commits one ``reanchor`` step.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
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


_commit = _supervisor("_supervisor_commit.py")
_loop = _supervisor("_supervisor_loop.py")
Refusal = _loop.Refusal
Action = _loop.Action

__all__ = [
    "Divergence",
    "adoption_action",
    "close_not_red",
    "decisions",
    "gate",
    "is_adoption",
    "is_confirmation",
    "leftovers",
    "read_contents",
    "reconcile",
    "report_adoption",
    "replan_digest",
    "report_confirmation",
    "settle",
]

REASON = "replan-confirmation"
# The request schema's ``diff`` maxLength; a diff over it is refused, never cut.
MAX_DIFF_CHARS = 4 * 1024 * 1024

Contents = dict[str, bytes | None]
# Names a surviving launch child chose are shown printable and bounded, like every other refusal.
_named = _loop._attempt._named


def is_confirmation(request: dict[str, Any]) -> bool:
    """Whether *request* is a replan confirmation."""
    return request.get("kind") == "human-decision" and request.get("reason") == REASON


def read_contents(ws: Any, paths: list[str]) -> Contents:
    """The working bytes of *paths* (``None`` when absent), read once."""
    return {p: ws.git.read_working(p) for p in sorted(paths)}


def replan_digest(head: str, contents: Contents) -> str:
    """A digest of *head* and the exact bytes, so returning to earlier content is a new step."""
    digest = hashlib.sha256(head.encode() + b"\0")
    for path, content in sorted(contents.items()):
        digest.update(
            path.encode() + b"\0" + (b"\0absent" if content is None else content) + b"\0"
        )
    return digest.hexdigest()


def _diff(ws: Any, contents: Contents) -> str:
    """The unified diff against ``HEAD``; refused, never truncated, when it is too large."""

    def lines(data: bytes | None) -> list[str]:
        return [] if data is None else data.decode("utf-8", "replace").splitlines(True)

    text = "".join(
        "".join(
            difflib.unified_diff(
                lines(ws.git.show(path)), lines(data), f"a/{path}", f"b/{path}"
            )
        )
        for path, data in sorted(contents.items())
    )
    if len(text) > MAX_DIFF_CHARS:
        raise Refusal(
            "replan-diff-too-large",
            "plan author",
            f"the change to {', '.join(sorted(contents))[:500]} is too large to show a human "
            "in one confirmation; split it into smaller changes",
        )
    return text


# ── the store record ────────────────────────────────────────────────────────


def _landed(stored: dict[str, Any], state: Any) -> dict[str, Any]:
    """*stored* with a confirmation that reached ``HEAD`` before its store write finished."""
    pending = stored["confirming"]
    if pending is not None and pending.get("step") in state.steps:
        return {
            **stored,
            "owed": False,
            "declined": "",
            "confirming": None,
            "decisions": [*stored["decisions"], pending["record"]],
        }
    return stored


def _effective(ws: Any, state: Any) -> dict[str, Any]:
    return _landed(ws.attempts.recovery(state.run_id), state)  # type: ignore[no-any-return]


def settle(ws: Any, state: Any, pending: list[str]) -> bool:
    """Finish an interrupted confirmation and drop a stale decline; True when none is owed.

    *pending* is the uncommitted trusted-file change set. A decline ends once the
    trusted files match ``HEAD`` again.
    """
    stored = ws.attempts.recovery(state.run_id)
    record = _landed(stored, state)
    if record["declined"] and not pending:
        record = {**record, "declined": ""}
    live = _live_leftovers(ws, record)
    if live != record["leftovers"]:
        record = {**record, "leftovers": live}
    if record != stored:
        ws.attempts.update_recovery(state.run_id, **record)
    return not record["owed"]


def _at_head(ws: Any, root: Path, rel: str) -> bool:
    """Whether *rel* holds ``HEAD``'s bytes, or is absent where ``HEAD`` has no file."""
    committed = ws.git.show(rel)
    now = _fingerprint(root, rel)
    if committed is None:
        return now is None
    return now == "file:" + hashlib.sha256(committed).hexdigest()


def _live_leftovers(ws: Any, record: dict[str, Any]) -> dict[str, str]:
    """The recorded leftovers that do not yet match ``HEAD``; any other state still blocks."""
    root = Path(os.path.realpath(ws.root))
    return {rel: seen for rel, seen in record["leftovers"].items() if not _at_head(ws, root, rel)}


def leftovers(ws: Any, state: Any) -> dict[str, str]:
    """The paths a discard left behind that the controller has not yet removed or restored."""
    return _live_leftovers(ws, _effective(ws, state))


def decisions(ws: Any, state: Any) -> list[dict[str, Any]]:
    """Every recovery decision recorded: its decision, authority reference, and digest."""
    return list(_effective(ws, state)["decisions"])


# ── the confirmation ────────────────────────────────────────────────────────


def gate(ws: Any, state: Any) -> Any:
    """The confirmation request or refusal owed before a trusted-file change; ``None`` if none."""
    record = _effective(ws, state)
    left = _live_leftovers(ws, record)
    if left:
        return Action(
            "refusal",
            refusal=Refusal(
                "recovery-leftovers",
                "controller",
                "a closed stub attempt left files the supervisor could not discard; remove or "
                "restore them to HEAD before the run continues: " + _named(left),
            ),
        )
    if not record["owed"]:
        return None
    paths = _loop._pending_replan(ws, state)
    if not paths:
        return None
    contents = read_contents(ws, paths)
    digest = replan_digest(state.head, contents)
    if record["declined"]:
        return Action(
            "refusal",
            refusal=Refusal(
                "replan-declined",
                "plan author",
                "a named human declined a change to the trusted files; none is committed. "
                "Restore " + ", ".join(paths)[:500] + " to HEAD: that brings back the fence "
                "that was not red, so the stub runs again, and the next change after "
                "that attempt closes opens a new confirmation",
            ),
        )
    try:
        diff = _diff(ws, contents)
    except Refusal as exc:
        return Action("refusal", refusal=exc)
    return Action(
        "request",
        _loop.human_decision(
            ws,
            state,
            REASON,
            "A stub attempt was refused as not red and closed. Confirm or decline "
            "committing this change to " + ", ".join(paths)[:1500] + " as a replan; the "
            "diff is in the request, and selection_key binds its exact bytes.",
            key=digest,
            selection_key=digest,
            diff=diff,
        ),
    )


def report_confirmation(
    ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any], changed: list[str]
) -> str:
    """Admit a confirmation: commit the replan or record the decline; else refuse, writing nothing.

    The change set must be exactly the bound files. The commit holds the bytes read
    here and covered by the digest, never a second read of the working tree.
    """
    decision = result.get("decision")
    if not isinstance(decision, dict) or set(decision) != {
        "decision",
        "authority_ref",
        "selection_key",
    }:
        raise Refusal(
            "invalid-result", "controller", "a confirmation needs decision, ref, and key"
        )
    kind, ref = decision["decision"], decision["authority_ref"]
    role = ws.policy["authority_roles"]["confirm_replan"]
    check = _loop._admission.check_authority_ref
    if kind not in ("confirm-replan", "decline-replan") or not check(ref, role):
        raise Refusal(
            "authority-refused",
            "owner",
            f"a replan confirmation needs a {role} authority reference",
        )
    paths = _loop._pending_replan(ws, state)
    contents = read_contents(ws, paths)
    digest = replan_digest(state.head, contents)
    if decision["selection_key"] != request["selection_key"] or digest != request["selection_key"]:
        raise Refusal("invalid-result", "controller", "the decision names other bytes")
    if sorted(changed) != sorted(paths):
        raise Refusal(
            "unexpected-change",
            "controller",
            "a confirmation may be reported only over its own files; the change set is "
            + _named(changed),
        )
    record = {
        "request_id": request["request_id"],
        "decision": kind,
        "authority_ref": ref,
        "selection_key": digest,
    }
    stored = ws.attempts.recovery(state.run_id)
    history = [*stored["decisions"], record]
    if kind == "decline-replan":
        ws.attempts.update_recovery(state.run_id, declined=digest, decisions=history)
        return "declined"
    _commit.kill_point("replan-verified")
    if read_contents(ws, paths) != contents:
        raise Refusal("replan-changed", "controller", "the trusted files changed while confirming")
    step = f"replan:{digest[:24]}"
    ws.attempts.update_recovery(state.run_id, confirming={"step": step, "record": record})
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="replan",
        trailers={"Supervisor-Authority-Ref": ref},
        contents=contents,
        summary="replan",
        known_steps=state.steps,
    )
    _commit.kill_point("replan-committed")
    ws.attempts.update_recovery(
        state.run_id, owed=False, declined="", confirming=None, decisions=history
    )
    return "replan"


# ── closing the attempt ─────────────────────────────────────────────────────


def _entry(fd: int | None, path: Path, name: str) -> str | None:
    """A fingerprint of one entry without following a link; ``None`` when absent."""
    target: Any = name if fd is not None else path
    kw: dict[str, Any] = {} if fd is None else {"dir_fd": fd}
    try:
        info = os.stat(target, follow_symlinks=False, **kw)  # noqa: PTH116 - needs dir_fd
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode):
        return "link:" + hashlib.sha256(os.fsencode(os.readlink(target, **kw))).hexdigest()
    if not stat.S_ISREG(info.st_mode):
        return "special"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(target, flags, **kw), "rb") as handle:
        return "file:" + hashlib.sha256(handle.read()).hexdigest()


def _fingerprint(root: Path, rel: str) -> str | None:
    """The entry's fingerprint through a no-follow walk of its parents; ``"unsafe"`` if refused."""
    fs = _commit.sibling("_file_safety.py")
    try:
        with fs._open_confined_parent(root, root / rel, relative=rel) as (fd, name):
            return _entry(fd, root / rel, name)
    except (fs.UnsafeContentError, OSError):
        return "unsafe"


def _observe(ws: Any, paths: list[str]) -> dict[str, str | None]:
    """The fingerprint of every path the attempt or its launch changed, right after the launch."""
    root = Path(os.path.realpath(ws.root))
    return {rel: _fingerprint(root, rel) for rel in sorted(set(paths))}


def _discard(ws: Any, observed: dict[str, str | None]) -> dict[str, str]:
    """Undo each observed change that still matches its observation; return those left behind.

    A file in ``HEAD`` goes back to its committed bytes and any other is removed. Every
    parent is walked without following a link, so a path swapped for a link since the
    observation is not touched. Each path that could not be undone, or that changed
    since it was observed, is returned with its fingerprint now.
    """
    _commit.kill_point("recovery-discard")
    fs = _commit.sibling("_file_safety.py")
    cm = _commit.sibling("_confined_mutation.py")
    root = Path(os.path.realpath(ws.root))
    left: dict[str, str] = {}
    for rel, seen in observed.items():
        if seen is None:
            continue
        if seen in ("unsafe", "special"):
            left[rel] = seen
            continue
        committed = ws.git.show(rel)
        try:
            with fs._open_confined_parent(root, root / rel, relative=rel) as (fd, name):
                now = _entry(fd, root / rel, name)
                if now != seen:
                    if now is not None:
                        left[rel] = now
                    continue
                if committed is None:
                    kw: dict[str, Any] = {} if fd is None else {"dir_fd": fd}
                    os.unlink(name if fd is not None else root / rel, **kw)
                    continue
            cm.confined_atomic_replace(root, root / rel, committed)
        except (fs.UnsafeContentError, cm.MutationDenied, OSError):
            now = _fingerprint(root, rel)
            if now is not None:
                left[rel] = now
    return left


def close_not_red(
    ws: Any, state: Any, request_id: str, changed: list[str]
) -> dict[str, str]:
    """Close the open ``write-stub`` attempt: observe what it and its launch left, then discard it.

    *changed* is the change set checked before the launch, which was exactly the stub files.
    Returns the paths the discard left behind.
    """
    observed = _observe(ws, [*changed, *ws.git.change_set()])
    return ws.attempts.close_not_red(  # type: ignore[no-any-return]
        state, request_id, lambda: _discard(ws, observed)
    )


# ── the product ref ─────────────────────────────────────────────────────────

ADOPTION_REASON = "history-adoption"
_SHOWN_PATHS = 20
_admission = _loop._admission
_REF_EVENT = "supervisor-product-ref-check"


@dataclass
class Divergence:
    """How ``HEAD`` differs from the anchor in a way only the owner can admit."""

    head: str
    anchor: str
    paths: list[str]
    spec_dir_changed: bool
    spec_files_changed: bool
    delivery_changed: bool

    @property
    def changed(self) -> str:
        """Whether adoption changes the product, the spec directory's files, both, or neither."""
        hits = (("product", self.paths), ("spec", self.spec_files_changed))
        kinds = [kind for kind, hit in hits if hit]
        return "+".join(kinds) or "none"


def is_adoption(request: dict[str, Any]) -> bool:
    """Whether *request* is a history-adoption decision."""
    return request.get("kind") == "human-decision" and request.get("reason") == ADOPTION_REASON


def unadopted(ws: Any) -> Any:
    """The refusal a verb that must commit raises while ``HEAD`` holds history not yet adopted."""
    return Refusal(
        "history-adoption-required",
        "controller",
        "HEAD holds history this run did not make, so nothing can be committed on top of it. "
        "Run next and put its history-adoption decision to the owner, or restore the branch "
        "to the run's last commit.",
    )


def _diverged(ws: Any, record: Any, kind: str, value: str, *, log: bool = True) -> Any:
    if log:
        ws.attempts.log_denial("product-ref-diverged", _REF_EVENT)
    shown = f"commit {value}" if kind == "commit" else kind
    restore = ws.git.restore_command(record.name, kind, record.recorded or record.pending)
    return Refusal(
        "product-ref-diverged",
        "controller",
        f"the product ref {record.name} is {shown}, not its recorded value "
        f"{record.recorded or record.pending}; restore it with: {restore}",
    )


def _divergence(ws: Any, head: str, anchor: str) -> Divergence:
    out = ws.git.run("diff", "--name-only", "-z", "--no-renames", anchor, head)
    paths = [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]
    spec = ws.spec_rel + "/"
    delivery = ws.git.delivery_rel + "/"
    return Divergence(
        head=head,
        anchor=anchor,
        paths=sorted(p for p in paths if not p.startswith(spec)),
        spec_dir_changed=any(p.startswith(spec) for p in paths),
        spec_files_changed=any(p.startswith(spec) and not p.startswith(delivery) for p in paths),
        delivery_changed=any(p.startswith(delivery) for p in paths),
    )


def _exists(ws: Any, sha: str) -> bool:
    found = ws.git.text("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}", check=False)
    return found.strip() == sha


def _latest_made(ws: Any, run_id: str, *, clean: bool) -> str | None:
    """The run's latest made commit that exists, and with *clean* that sits on a made-only chain.

    A made commit has landed, so none is a refused step; a commit with a foreign
    commit between it and the run's first step never anchors a run.
    """
    git = ws.git
    made = git.made_list(run_id)
    for sha in reversed(made):
        if not _exists(ws, sha):
            continue
        if not clean or (made and git.made_only(run_id, made[0], sha)):
            return sha
    return None


def _create(ws: Any, run_id: str, head: str) -> Any:
    """Give a run that records no product ref one at its latest made commit, or report why not."""
    git = ws.git
    latest = _latest_made(ws, run_id, clean=True)
    if latest is None or (latest != head and not git.made_only(run_id, head, latest)):
        anchor = latest or _latest_made(ws, run_id, clean=False)
        return None if anchor is None else _divergence(ws, head, anchor)
    record = _commit.ProductRecord(git.new_product_name(run_id), None, latest)
    git.write_product_record(run_id, record)
    _commit.kill_point("pending-recorded")
    git.create_ref(record.name, latest)
    _commit.kill_point("repaired")
    done = _commit.ProductRecord(record.name, latest, None)
    git.write_product_record(run_id, done)
    return done


def _complete(ws: Any, run_id: str, record: Any, value: str, head: str) -> Any:
    """Finish a transaction that moved the product ref, and clear the pending commit.

    Only the product ref at the pending commit with ``HEAD`` at the commit before it
    completes: the ref moves only inside the supervisor's transaction. When ``HEAD`` alone
    names the pending commit, nothing is moved: the ref's own value becomes the recorded
    one, and the usual comparison with ``HEAD`` makes that history foreign.
    """
    git = ws.git
    if value == record.pending and head == record.recorded:
        git.move_head(value, head, "work-supervisor: complete step")
    _commit.kill_point("repaired")
    done = _commit.ProductRecord(record.name, value, None)
    git.write_product_record(run_id, done)
    return done


def reconcile(ws: Any) -> Divergence | None:
    """Classify ``HEAD`` against the product ref before a verb derives; repair or refuse.

    Returns a ``Divergence`` when only the owner can admit the difference; the
    caller issues the adoption decision, or refuses a verb that cannot. Refuses
    ``product-ref-diverged`` when the ref is not at its recorded or pending value, and
    ``projection-blocked`` when forward projection would overwrite a file. With an
    attempt open, the attempt guard has already answered and only an interrupted
    transaction is completed.
    """
    _admission.refuse_unsupported_ref_storage(ws)
    ws.divergence = None
    try:
        approvals = ws.approvals()
    except Refusal:
        return None
    if not approvals:
        return None
    run_id = approvals[0]["run_id"]
    git = ws.git
    open_attempt = ws.attempts.open is not None
    # A step a crash cut off is recorded as made, or forgotten, before anything reads the list.
    git.settle_pending(run_id)
    head = git.head()
    record = git.product_record(run_id)
    if record is None:
        if open_attempt:
            return None
        made = _create(ws, run_id, head)
        if isinstance(made, Divergence):
            ws.divergence = made
            return made
        if made is None:
            return None
        record = made
    kind, value, trusted = git.product_ref_view(record)
    if kind == "missing" and trusted:
        git.create_ref(record.name, record.pending)
        kind, value = "commit", record.pending
    if not trusted:
        if open_attempt:
            return None
        raise _diverged(ws, record, kind, value)
    if record.pending is not None:
        record = _complete(ws, run_id, record, value, head)
        head = git.head()
        git.settle_pending(run_id)  # the finished move may be the pending step's landing
    anchor = record.recorded
    assert anchor is not None
    if head == anchor or open_attempt:
        return None
    if git.made_only(run_id, head, anchor):
        _project_forward(ws, head, anchor)
        return None
    ws.divergence = _divergence(ws, head, anchor)
    return ws.divergence  # type: ignore[no-any-return]


def inspect(ws: Any) -> Any:
    """What ``reconcile`` would refuse, found without writing anything; ``None`` if nothing.

    For ``status``: the ref's trust and, when ``HEAD`` could be moved forward, whether
    that would overwrite a file.
    """
    try:
        approvals = ws.approvals()
    except Refusal:
        return None
    if not approvals:
        return None
    git = ws.git
    record = git.product_record(approvals[0]["run_id"])
    if record is None:
        return None
    kind, value, trusted = git.product_ref_view(record)
    if not trusted:
        return _diverged(ws, record, kind, value, log=False)
    anchor = record.pending or record.recorded
    head = git.head()
    if anchor and anchor != head and git.made_only(approvals[0]["run_id"], head, anchor):
        paths, blocked = _projection(ws, head, anchor)
        if blocked:
            return _blocked_refusal(blocked)
    return None


def peek(ws: Any) -> Divergence | None:
    """The history-adoption ``reconcile`` would issue, found without writing; for ``status``.

    Nothing is reported while an attempt is open, as ``reconcile`` does.
    """
    try:
        approvals = ws.approvals()
    except Refusal:
        return None
    if not approvals or ws.attempts.has_open_issuance():
        return None
    git = ws.git
    run_id = approvals[0]["run_id"]
    head = git.head()
    record = git.product_record(run_id)
    if record is None:
        latest = _latest_made(ws, run_id, clean=True)
        if latest is not None and (latest == head or git.made_only(run_id, head, latest)):
            return None
        anchor = latest or _latest_made(ws, run_id, clean=False)
        return None if anchor is None else _divergence(ws, head, anchor)
    if not git.product_ref_view(record)[2]:
        return None  # ``inspect`` reports an untrusted ref
    anchors = {v for v in (record.recorded, record.pending) if v is not None}
    if head in anchors or any(git.made_only(run_id, head, a) for a in anchors):
        return None
    return _divergence(ws, head, record.recorded or record.pending or head)


def _index_oids(ws: Any, paths: list[str]) -> dict[str, str | None]:
    """The index's object id for each path (``None`` when absent, ``"conflict"`` when unmerged)."""
    out = ws.git.run("ls-files", "-s", "-z", "--", *paths, literal_pathspecs=True)
    found: dict[str, str | None] = dict.fromkeys(paths)
    for entry in out.split(b"\0"):
        if not entry:
            continue
        meta, _, path = entry.partition(b"\t")
        _mode, oid, stage = meta.decode().split()
        name = path.decode("utf-8", "surrogateescape")
        found[name] = oid if stage == "0" and found.get(name) is None else "conflict"
    return found


def _projection(ws: Any, head: str, target: str) -> tuple[list[str], list[str]]:
    """The paths moving ``HEAD`` to *target* changes, and those that hold neither version.

    ``delivery/`` is left to the lag sync. A path is safe when its working-tree bytes
    and its index entry each match ``HEAD``'s or the target's version.
    """
    git = ws.git
    out = git.run("diff", "--name-only", "-z", "--no-renames", head, target)
    delivery = git.delivery_rel + "/"
    paths = sorted(
        p
        for p in (x.decode("utf-8", "surrogateescape") for x in out.split(b"\0") if x)
        if not p.startswith(delivery)
    )
    if not paths:
        return [], []
    indexed = _index_oids(ws, paths)
    blocked = []
    for rel in paths:
        try:
            working = git.read_working(rel)
        except _commit.SupervisorGitError:
            blocked.append(rel)
            continue
        if working not in (git.show(rel, head), git.show(rel, target)) or indexed[rel] not in (
            git.object_id(rel, head),
            git.object_id(rel, target),
        ):
            blocked.append(rel)
    return paths, blocked


def _blocked_refusal(blocked: list[str]) -> Any:
    return Refusal(
        "projection-blocked",
        "controller",
        "these files differ from both HEAD and the product ref, so the run cannot "
        "move HEAD forward to the product ref without overwriting them; restore or "
        "move them aside: " + _named(blocked),
    )


def _project_forward(ws: Any, head: str, target: str) -> None:
    """Bring the working tree and index to *target*'s tree, then move ``HEAD`` to it.

    Git writes the target's version, and only then does ``HEAD`` move by
    compare-and-swap, so a crash before the move repeats on the same inputs.
    """
    git = ws.git
    paths, blocked = _projection(ws, head, target)
    if blocked:
        raise _blocked_refusal(blocked)
    if paths:
        present = {p for p, _oid in git.tree_entries(target)}
        writes = [p for p in paths if p in present]
        removes = [p for p in paths if p not in present]
        if writes:
            git.run(
                "restore", "--source", target, "--staged", "--worktree",
                "--pathspec-from-file=-", "--pathspec-file-nul",
                literal_pathspecs=True,
                stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in writes),
            )
        if removes:
            git.run(
                "rm", "-q", "-f", "--ignore-unmatch",
                "--pathspec-from-file=-", "--pathspec-file-nul",
                literal_pathspecs=True,
                stdin=b"\0".join(p.encode("utf-8", "surrogateescape") for p in removes),
            )
    _commit.kill_point("projection-updated")
    git.move_head(target, head, "work-supervisor: project product ref")
    _commit.kill_point("repaired")


# ── owner adoption of history the supervisor did not make ───────────────────


def adoption_action(ws: Any, state: Any, div: Divergence) -> Any:
    """The ``history-adoption`` decision for a ``HEAD`` the owner has not admitted."""
    shown = div.paths[:_SHOWN_PATHS]
    where = "and would change files in the spec directory" if div.spec_dir_changed else (
        "and would change no file in the spec directory"
    )
    return Action(
        "request",
        _loop.human_decision(
            ws,
            state,
            ADOPTION_REASON,
            f"HEAD is {div.head}, which holds history this run did not make. Adopting it "
            f"changes {len(div.paths)} product path(s) from the run's product ref "
            f"({', '.join(shown)[:1200] or 'none'}) {where}. Answer adopt-history with an owner "
            "authority reference and that commit id, or restore HEAD to the run's last commit.",
            key=div.head,
            head_commit=div.head,
            changed_path_count=len(div.paths),
            changed_paths=shown,
            spec_dir_changed=div.spec_dir_changed,
        ),
    )


def report_adoption(
    ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any]
) -> str:
    """Admit an ``adopt-history`` answer as one ``reanchor`` step, or refuse and commit nothing."""
    div = ws.divergence
    decision = result.get("decision")
    if (
        div is None
        or not isinstance(decision, dict)
        or set(decision) != {"decision", "authority_ref", "commit"}
        or decision["decision"] != "adopt-history"
    ):
        raise Refusal(
            "invalid-result",
            "controller",
            "an adoption answer needs decision, authority_ref, and commit",
        )
    role = ws.policy["authority_roles"]["adopt_history"]
    if not _admission.check_authority_ref(decision["authority_ref"], role):
        raise Refusal(
            "adoption-refused",
            "controller",
            f"adopting history needs a {role} authority reference",
        )
    if decision["commit"] != div.head or ws.git.head() != div.head:
        raise Refusal(
            "adoption-refused",
            "controller",
            f"the answer must name the current HEAD, {div.head}",
        )
    if div.delivery_changed:
        raise Refusal(
            "adoption-refused",
            "controller",
            "the history changes files under delivery/, which only the supervisor writes; "
            "restore them before adopting",
        )
    git = ws.git
    record = git.product_record(state.run_id)
    name = None if record is not None else git.new_product_name(state.run_id)
    trailers = {
        "Supervisor-Reanchor-From": div.anchor,
        "Supervisor-Reanchor-Changed": div.changed,
        "Supervisor-Authority-Ref": decision["authority_ref"],
    }
    if name is not None:
        trailers["Supervisor-Product-Ref"] = name
    git.build_commit(
        run_id=state.run_id,
        step=f"reanchor:{div.head}",
        operation="reanchor",
        trailers=trailers,
        summary="adopt history",
        known_steps=state.steps,
        create_ref=name,
        adopting=True,
        product_old=div.anchor if record is not None else None,
    )
    ws.divergence = None
    return "reanchor"
