"""_supervisor_recovery — recovery after a stub result that is not red.

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

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import os
import stat
import sys
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
    "close_not_red",
    "decisions",
    "gate",
    "is_confirmation",
    "leftovers",
    "read_contents",
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
