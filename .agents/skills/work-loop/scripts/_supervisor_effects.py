"""_supervisor_effects — external effects that never repeat.

Each declared effect is one operation with a durable key: the run and the
plan-unique effect name for a task effect, and additionally the HEAD commit
when terminal was first reached for that tree for a finish effect. Replans,
later commits, and rebases never reopen a task effect.

The first dispatch is recorded as an intent before the controller runs it.
From then on ``next`` asks the controller to query the effect source before
anything else happens. A receipt ends the operation for good. A source that
shows the effect never happened allows another dispatch, up to the policy's
dispatch cap in all; past that, or when the source cannot tell, the operation
waits for a named-human ``effect-resolution.v1`` decision: confirmed, do not
retry, or one authorized retry claimed under the run lock and compare-and-swap.

A query outcome that needs a decision is kept as an evidence receipt, so the
human-decision request re-derives after a crash.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
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


_loop = _supervisor("_supervisor_loop.py")
_admission = _supervisor("_supervisor_admission.py")
Refusal = _loop.Refusal

__all__ = ["Operation", "commit_intent", "effect_action", "report_effect", "resolve_effect"]

DECISIONS = ("effect-confirmed", "do-not-retry", "retry-authorized")
QUERY_OUTCOMES = ("running", "present", "absent", "unknowable")


class Operation:
    """The durable lines of one effect operation, in commit order."""

    def __init__(self, key: str, lines: list[dict[str, Any]]) -> None:
        self.key = key
        self.lines = [line for line in lines if line.get("operation_key") == key]

    def entries(self, entry: str) -> list[dict[str, Any]]:
        return [line for line in self.lines if line["entry"] == entry]

    @property
    def started(self) -> bool:
        return bool(self.entries("intent"))

    @property
    def received(self) -> bool:
        return bool(self.entries("receipt"))

    @property
    def dispatches(self) -> int:
        return max((int(line["dispatch"]) for line in self.lines if "dispatch" in line), default=0)

    @property
    def decision(self) -> dict[str, Any] | None:
        decisions = self.entries("decision")
        return decisions[-1] if decisions else None

    @property
    def claimed(self) -> bool:
        decision = self.decision
        return decision is not None and any(
            c["resolution_id"] == decision["resolution_id"] for c in self.entries("claim")
        )

    @property
    def ended(self) -> bool:
        decision = self.decision
        return self.received or (decision is not None and decision["decision"] == "do-not-retry")

    @property
    def epoch(self) -> str:
        """Changes whenever a dispatch or decision is recorded."""
        return f"{self.dispatches}.{len(self.entries('decision'))}"

    @property
    def first(self) -> dict[str, Any]:
        return self.entries("intent")[0]


def _finish_key(ws: Any, state: Any, name: str) -> tuple[str, str]:
    """The finish key: run, name, and the HEAD when terminal was first reached for this tree.

    An intent whose recorded HEAD is no longer readable (a rebase dropped it and
    the object was pruned) cannot be matched to this tree, so it is skipped.
    """
    commit = _supervisor("_supervisor_commit.py")
    tree = ws.git.product_tree()
    for line in state.effects:
        if line["entry"] != "intent" or line["scope"] != "finish" or line["effect"] != name:
            continue
        try:
            same_tree = ws.git.product_tree(line["terminal_head"]) == tree
        except commit.SupervisorGitError:
            same_tree = False
        if same_tree:
            return line["operation_key"], line["terminal_head"]
    return f"{state.run_id}:{name}:{state.head}", state.head


def operation_key(ws: Any, state: Any, name: str, scope: str) -> tuple[str, str | None]:
    if scope == "task":
        return f"{state.run_id}:{name}", None
    return _finish_key(ws, state, name)


def _needs_decision(state: Any, op: Operation) -> dict[str, Any] | None:
    """The query receipt that, at the current epoch, needs a human decision."""
    term = f"effect-query:{op.key}:{op.epoch}"
    for receipt in state.receipts:
        if receipt["selector"]["term"] == term and receipt["producer"]["identity"] == state.run_id:
            return receipt
    return None


def _effect_ref(op: Operation, name: str, scope: str, dispatch: int) -> dict[str, Any]:
    return {"operation_key": op.key, "name": name, "scope": scope, "dispatch": max(dispatch, 1)}


def effect_action(
    ws: Any, state: Any, name: str, *, scope: str, task: dict[str, Any] | None
) -> Any:
    """The current action for one effect, or None when it needs nothing."""
    key, terminal_head = operation_key(ws, state, name, scope)
    op = Operation(key, state.effects)
    if op.ended:
        return None
    if not op.started:
        return _loop.Action(
            "effect-intent",
            detail={
                "key": key,
                "name": name,
                "scope": scope,
                "task_id": task["task_id"] if task else None,
                "terminal_head": terminal_head,
            },
        )
    waiting = _needs_decision(state, op)
    if waiting is not None:
        return _loop.Action(
            "request",
            _loop.human_decision(
                ws,
                state,
                "effect-unresolved",
                f"Effect {name} ({key}) {waiting['outcome']}: record effect-confirmed, "
                "do-not-retry, or retry-authorized with resolve-effect.",
                key=f"{key}:{op.epoch}",
            ),
        )
    return _loop.Action(
        "request",
        _loop.make_request(
            ws,
            state,
            "effect-query",
            f"query:{key}:{op.epoch}",
            effect=_effect_ref(op, name, scope, op.dispatches),
        ),
    )


def _line(
    state: Any, ws: Any, entry: str, key: str, name: str, scope: str, **fields: Any
) -> dict[str, Any]:
    record = {
        "schema_version": 1,
        "entry": entry,
        "operation_key": key,
        "run_id": state.run_id,
        "effect": name,
        "scope": scope,
        "at": ws.clock(),
        **fields,
    }
    return {k: v for k, v in record.items() if v is not None}


def _scope_fields(op: Operation) -> dict[str, Any]:
    first = op.first
    return {"task_id": first.get("task_id"), "terminal_head": first.get("terminal_head")}


def _append(
    ws: Any, state: Any, step: str, operation: str, lines: list[dict[str, Any]], summary: str
) -> None:
    payload = b"".join(_admission.canonical_line(line) for line in lines)
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation=operation,
        appends={"effect-resolutions.jsonl": payload},
        summary=summary,
        known_steps=state.steps,
    )


def _dispatch_request(
    ws: Any, state: Any, op_key: str, name: str, scope: str, dispatch: int
) -> dict[str, Any]:
    return _loop.make_request(
        ws,
        state,
        "external-effect",
        f"effect:{op_key}:{dispatch}",
        effect={"operation_key": op_key, "name": name, "scope": scope, "dispatch": dispatch},
    )


def commit_intent(ws: Any, state: Any, detail: dict[str, Any]) -> dict[str, Any]:
    """Record the intent (the first dispatch), then hand out the dispatch."""
    key, name, scope = detail["key"], detail["name"], detail["scope"]
    line = _line(
        state,
        ws,
        "intent",
        key,
        name,
        scope,
        dispatch=1,
        task_id=detail["task_id"],
        terminal_head=detail["terminal_head"],
    )
    _append(ws, state, f"effect-intent:{key}", "effect-intent", [line], f"intend {name}")
    return _dispatch_request(ws, state, key, name, scope, 1)


def _query_receipt(ws: Any, state: Any, op: Operation, outcome: str) -> None:
    step = f"effect-query:{op.key}:{op.epoch}"
    evidence = ws.evidence_append([
        _loop.receipt(
            state,
            step,
            criterion=f"effect:{op.key}",
            term=step,
            observation="effect-query",
            outcome=outcome,
            fingerprint=op.key,
        )
    ])
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="evidence",
        appends={"evidence.jsonl": evidence},
        summary=f"effect source says {outcome}",
        known_steps=state.steps,
    )


def _receipt(ws: Any, state: Any, op: Operation, receipt_ref: str | None) -> str:
    first = op.first
    line = _line(
        state,
        ws,
        "receipt",
        op.key,
        first["effect"],
        first["scope"],
        receipt_ref=receipt_ref,
        **_scope_fields(op),
    )
    _append(
        ws,
        state,
        f"effect-receipt:{op.key}",
        "effect-receipt",
        [line],
        f"receipt for {first['effect']}",
    )
    return "effect-receipt"


def _find_open(state: Any, key: str) -> Operation:
    op = Operation(key, state.effects)
    if not op.started or op.ended:
        raise Refusal("no-open-effect", "controller", f"{key} has no open operation")
    return op


def report_effect(ws: Any, state: Any, result: dict[str, Any]) -> dict[str, Any] | str:
    """Apply an external-effect or effect-query result through the Effect truth table."""
    effect = result.get("effect")
    if not isinstance(effect, dict) or effect.get("outcome") not in (
        "completed",
        "not-executed",
        *QUERY_OUTCOMES,
    ):
        raise Refusal("invalid-result", "controller", "an effect result needs effect.outcome")
    request_id = result["request_id"]
    prefix = "effect:" if result["kind"] == "external-effect" else "query:"
    if not request_id.startswith(prefix):
        raise Refusal("not-current-attempt", "controller", "the result names another request")
    key, _, suffix = request_id[len(prefix) :].rpartition(":")
    op = _find_open(state, key)
    receipt_ref = effect.get("receipt_ref")
    if receipt_ref is not None and (
        not isinstance(receipt_ref, str) or not 0 < len(receipt_ref) <= 512
    ):
        raise Refusal("invalid-result", "controller", "receipt_ref must be a short string")
    first = op.first
    name, scope = first["effect"], first["scope"]
    if result["kind"] == "external-effect":
        if not suffix.isdigit() or not 1 <= int(suffix) <= op.dispatches:
            raise Refusal("not-current-attempt", "controller", "no such dispatch was recorded")
        if effect["outcome"] == "completed":
            return _receipt(ws, state, op, receipt_ref)
        if effect["outcome"] == "not-executed":
            return "not-executed"
        raise Refusal(
            "invalid-result",
            "controller",
            "an external-effect result is completed or not-executed",
        )
    if suffix != op.epoch or _needs_decision(state, op) is not None:
        raise Refusal(
            "not-current-attempt", "controller", "the query is not for the current request"
        )
    outcome = effect["outcome"]
    if outcome not in QUERY_OUTCOMES:
        raise Refusal(
            "invalid-result", "controller", "an effect-query result reports a query outcome"
        )
    decision = op.decision["decision"] if op.decision else None
    cap = int(ws.policy["effect_dispatch_cap"])
    if outcome == "running":
        return "running"
    if outcome == "present":
        return _receipt(ws, state, op, receipt_ref)
    if decision == "do-not-retry":
        return "ended"
    if decision == "retry-authorized":
        if op.claimed:
            _query_receipt(ws, state, op, outcome)
            return "decision-required"
        dispatch = op.dispatches + 1
        resolution_id = op.decision["resolution_id"]  # type: ignore[index]
        lines = [
            _line(
                state,
                ws,
                "claim",
                op.key,
                name,
                scope,
                resolution_id=resolution_id,
                **_scope_fields(op),
            ),
            _line(
                state, ws, "dispatch", op.key, name, scope, dispatch=dispatch, **_scope_fields(op)
            ),
        ]
        _append(ws, state, f"claim:{resolution_id}", "claim", lines, f"claim retry of {name}")
        return {"request": _dispatch_request(ws, state, op.key, name, scope, dispatch)}
    if outcome == "unknowable":
        if decision == "effect-confirmed":
            return _receipt(ws, state, op, receipt_ref)
        _query_receipt(ws, state, op, outcome)
        return "decision-required"
    # outcome == "absent"
    if decision is None and op.dispatches < cap:
        dispatch = op.dispatches + 1
        line = _line(
            state, ws, "dispatch", op.key, name, scope, dispatch=dispatch, **_scope_fields(op)
        )
        _append(
            ws,
            state,
            f"effect-dispatch:{op.key}:{dispatch}",
            "effect-dispatch",
            [line],
            f"dispatch {name} again",
        )
        return {"request": _dispatch_request(ws, state, op.key, name, scope, dispatch)}
    _query_receipt(ws, state, op, outcome)
    return "decision-required"


def resolve_effect(
    ws: Any, *, operation: str, decision: str, authority_ref: str
) -> dict[str, Any]:
    """Commit one named-human ``effect-resolution.v1`` decision for an open operation."""
    role = ws.policy["authority_roles"]["resolve_effect_authority_ref"]
    if not _admission.check_authority_ref(authority_ref, role):
        raise Refusal("invalid-authority-ref", "owner", f"--authority-ref must be {role}[:<hex>]")
    if decision not in DECISIONS:
        raise Refusal(
            "invalid-argument", "owner", f"--decision must be one of {', '.join(DECISIONS)}"
        )
    with ws.run_lock():
        state = _loop.derive(ws)
        if state.refusal is not None:
            raise state.refusal
        op = _find_open(state, operation)
        sequence = len(op.entries("decision")) + 1
        resolution_id = (
            "res-"
            + hashlib.sha256(
                json.dumps([operation, sequence, decision, authority_ref]).encode()
            ).hexdigest()[:16]
        )
        first = op.first
        line = _line(
            state,
            ws,
            "decision",
            op.key,
            first["effect"],
            first["scope"],
            resolution_id=resolution_id,
            decision=decision,
            authority_ref=authority_ref,
            **_scope_fields(op),
        )
        _append(
            ws,
            state,
            f"resolution:{resolution_id}",
            "resolution",
            [line],
            f"{decision} for {first['effect']}",
        )
        after = _loop.derive(ws)
        ws.local.reconcile_events(after.run_id, after.commits)
        return {"resolution_id": resolution_id, "operation_key": operation, "decision": decision}
