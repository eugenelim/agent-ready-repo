"""_supervisor_loop — derive the current request, commit steps, and recover.

Every identity is derived from committed facts reachable from ``HEAD``:
completion is an ``implement`` commit for a task's current revision, red proof
is a ``stub`` or ``red`` commit for its stub digest, and the implementation
retry count is the number of run-wide ``gate-fail`` receipts. The journal is
advisory and never read. Request ids are deterministic, so ``next`` re-issues
the current request until it is reported or superseded.

``next`` derives with no writes and refuses on a missing pair, a protected
edit, or a malformed plan, writing only ``run.json``. Otherwise it syncs
lagging ``delivery/`` copies, reconciles events, commits pending controller
edits to the spec, plan, or cited records as one ``replan`` step, and derives
the current request: the retry cap, the first incomplete task, the open effects
of completed tasks, gates and review, finish effects, then terminal.

``report`` re-derives, refuses a result that is not for the current request, a
foreign ``delivery/`` edit, or a change set touching the spec directory or a
cited record, then commits through the builder. A refused ``report`` writes
nothing.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
from dataclasses import dataclass, field
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
_admission = _supervisor("_supervisor_admission.py")
_projector = _supervisor("_supervisor_projector.py")
Refusal = _admission.Refusal
Workspace = _admission.Workspace
sibling = _commit.sibling

__all__ = ["State", "derive", "next_request", "report", "status", "commit_terminal"]

PRODUCER_CLASS = "work-supervisor"
SCHEMA_VERSION = 1
_STAGE_OF_KIND = {
    "implement-task": "implementing",
    "write-stub": "implementing",
    "external-effect": "implementing",
    "effect-query": "implementing",
    "run-gates": "gating",
    "regenerate": "gating",
    "review-role": "reviewing",
    "assess-finding": "reviewing",
    "human-decision": "awaiting-human",
}


@dataclass
class State:
    """Facts derived from HEAD and the working spec and plan; no writes."""

    refusal: Refusal | None = None
    run_id: str = ""
    approvals: list[dict[str, Any]] = field(default_factory=list)
    head: str = ""
    commits: list[Any] = field(default_factory=list)
    steps: set[str] = field(default_factory=set)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    finish_effects: list[str] = field(default_factory=list)
    cited_paths: tuple[str, ...] = ()
    completed: dict[tuple[str, str], str] = field(default_factory=dict)
    red: set[tuple[str, str]] = field(default_factory=set)
    receipts: list[dict[str, Any]] = field(default_factory=list)
    effects: list[dict[str, Any]] = field(default_factory=list)

    @property
    def latest(self) -> dict[str, Any]:
        return self.approvals[-1]

    @property
    def intent(self) -> str:
        return str(self.latest["terminal_intent"])

    @property
    def base(self) -> str:
        return str(self.approvals[0]["base"])

    def task_gate_receipts(self, outcome: str) -> list[dict[str, Any]]:
        return [
            r
            for r in self.receipts
            if r["observation"]["type"] == "task-gate"
            and r["outcome"] == outcome
            and r["producer"]["identity"] == self.run_id
        ]

    @property
    def retry_count(self) -> int:
        return len(self.task_gate_receipts("fail"))

    def attempt(self, task: dict[str, Any]) -> int:
        term = f"gate:{task['task_id']}:{task['revision']}"
        return 1 + sum(1 for r in self.task_gate_receipts("fail") if r["selector"]["term"] == term)

    def is_complete(self, task: dict[str, Any]) -> bool:
        return (task["task_id"], task["revision"]) in self.completed


def _evidence_receipts(ws: Workspace) -> list[dict[str, Any]]:
    es = sibling("_evidence_store.py")
    raw = ws.evidence_bytes()
    try:
        replay = es.replay_admitted_frames(raw[: raw.rfind(b"\n") + 1])
    except es.EvidenceStoreError as exc:
        raise Refusal(
            "malformed-record", "controller", "delivery/evidence.jsonl does not replay"
        ) from exc
    receipts = []
    for _tx, records in replay["frames"]:
        for record in records:
            if isinstance(record, dict) and "receipt_id" in record and "observation" in record:
                receipts.append(record)
    return receipts


def derive(ws: Workspace) -> State:
    """Derive the run's state. Never writes."""
    state = State()
    state.approvals = ws.approvals()
    if not state.approvals:
        state.refusal = Refusal("no-approval", "owner", "no approval pair; run start")
        return state
    state.run_id = state.approvals[0]["run_id"]
    try:
        spec_text, plan_text = ws.spec_text(), ws.plan_text()
        refs, state.cited_paths = ws.envelope(spec_text)
        intent = _projector.terminal_intent(spec_text)
        change = _projector.classify_replan(
            approved_envelope=state.latest["envelope"],
            approved_intent=state.intent,
            current_refs=refs,
            current_intent=intent,
        )
        if change is not None:
            raise Refusal(change[0], change[1], "a protected reference changed after review")
        projection = (
            _projector.project_plan(plan_text)
            if state.intent == "code"
            else _projector.PlanProjection([], [])
        )
    except _projector.ProjectionRefused as exc:
        state.refusal = Refusal(exc.code, exc.owner, exc.detail)
        return state
    except Refusal as exc:
        state.refusal = exc
        return state
    except OSError as exc:
        state.refusal = Refusal("unreadable-reference", "controller", str(exc))
        return state
    state.tasks = projection.tasks
    state.finish_effects = projection.finish_effects
    state.head = ws.git.head()
    state.commits = ws.git.supervisor_commits(state.run_id)
    state.steps = {c.step for c in state.commits}
    for c in state.commits:
        task_key = (
            c.trailers.get("Supervisor-Task", ""),
            c.trailers.get("Supervisor-Task-Revision", ""),
        )
        if c.operation == "implement":
            state.completed[task_key] = c.sha
        elif c.operation in ("stub", "red"):
            state.red.add((task_key[0], c.trailers.get("Supervisor-Stub-Digest", "")))
    state.receipts = _evidence_receipts(ws)
    state.effects = ws.records("effect-resolutions.jsonl")
    return state


# ── requests ────────────────────────────────────────────────────────────────


def _task_ref(task: dict[str, Any]) -> dict[str, str]:
    return {"task_id": task["task_id"], "title": task["title"], "revision": task["revision"]}


def make_request(
    ws: Workspace, state: State, kind: str, request_id: str, **fields: Any
) -> dict[str, Any]:
    """An execution-request.v1 record."""
    return {
        "schema_version": 1,
        "request_id": request_id,
        "run_id": state.run_id,
        "spec": ws.spec_rel,
        "kind": kind,
        "stage": _STAGE_OF_KIND[kind],
        **fields,
    }


def human_decision(
    ws: Workspace, state: State, reason: str, question: str, key: str = ""
) -> dict[str, Any]:
    digest = hashlib.sha256(f"{reason}\0{key}\0{state.head}".encode()).hexdigest()[:16]
    return make_request(
        ws, state, "human-decision", f"decide:{reason}:{digest}", reason=reason, question=question
    )


def receipt(
    state: State,
    step: str,
    *,
    criterion: str,
    term: str,
    observation: str,
    outcome: str,
    fingerprint: str,
    revision: str | None = None,
) -> dict[str, Any]:
    """An evidence-receipt.v1 the supervisor produces."""
    record = {
        "schema_version": 1,
        "receipt_id": f"{state.run_id}:{step}:{criterion}",
        "acceptance_fingerprint": fingerprint,
        "lineage": {"criterion_ref": criterion},
        "selector": {"term": term},
        "freshness_mode": "exact-subject",
        "observation": {"type": observation},
        "outcome": outcome,
        "producer": {"class": PRODUCER_CLASS, "identity": state.run_id},
    }
    if revision is not None:
        record["task_projection_revision"] = revision
    return record


@dataclass
class Action:
    """What the step loop does next: issue a request, or commit a step itself."""

    kind: str  # request | refusal | terminal | auto-red | effect-intent
    request: dict[str, Any] | None = None
    refusal: Refusal | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def _first_incomplete(state: State) -> tuple[dict[str, Any] | None, bool]:
    """The first incomplete task whose dependencies are complete, and whether any is incomplete."""
    complete_ids = {t["task_id"] for t in state.tasks if state.is_complete(t)}
    pending = [t for t in state.tasks if not state.is_complete(t)]
    for task in pending:
        if all(dep in complete_ids for dep in task["depends_on"]):
            return task, True
    return None, bool(pending)


def decide(ws: Workspace, state: State) -> Action:
    """The single current action. Never writes."""
    tdd = _supervisor("_supervisor_tdd.py")
    effects = _supervisor("_supervisor_effects.py")
    readiness = _supervisor("_supervisor_readiness.py")
    if is_terminal(ws, state):
        return Action("terminal")
    if state.intent == "spec-plan":
        return Action("terminal")
    cap = int(ws.policy["implementation_retry_cap"])
    if state.retry_count >= cap:
        return Action(
            "request",
            human_decision(
                ws,
                state,
                "retry-cap",
                f"The implementation retry count reached {cap}. The run is stopped: no "
                "replan, amendment, or re-approval resets the count.",
            ),
        )
    task, any_pending = _first_incomplete(state)
    if task is not None:
        return tdd.task_action(ws, state, task)
    if any_pending:
        return Action(
            "refusal",
            refusal=Refusal(
                "dependency-cycle",
                "plan author",
                "no incomplete task has its dependencies complete",
            ),
        )
    dirty = ws.git.change_set()
    if dirty:
        return Action(
            "request",
            human_decision(
                ws,
                state,
                "uncommitted-changes",
                "The working tree holds changes no task admitted: " + ", ".join(dirty[:20]),
                key="\0".join(dirty),
            ),
        )
    for task in state.tasks:
        for name in task["effects"]:
            action = effects.effect_action(ws, state, name, scope="task", task=task)
            if action is not None:
                return action
    action = readiness.readiness_action(ws, state)
    if action is not None:
        return action
    for name in state.finish_effects:
        action = effects.effect_action(ws, state, name, scope="finish", task=None)
        if action is not None:
            return action
    return Action("terminal")


def is_terminal(ws: Workspace, state: State) -> bool:
    """True when a terminal step for the current product tree is reachable."""
    return f"terminal:{ws.git.product_tree()}" in state.steps


def commit_terminal(ws: Workspace, run_id: str) -> None:
    """Commit the terminal step with its terminal receipt; idempotent."""
    state = State(run_id=run_id)
    tree = ws.git.product_tree()
    step = f"terminal:{tree}"
    if step in {c.step for c in ws.git.supervisor_commits(run_id)}:
        return
    evidence = ws.evidence_append([
        receipt(
            state,
            step,
            criterion="run:terminal",
            term="terminal",
            observation="terminal",
            outcome="terminal",
            fingerprint=tree,
        )
    ])
    ws.git.build_commit(
        run_id=run_id,
        step=step,
        operation="terminal",
        appends={"evidence.jsonl": evidence},
        summary="reach terminal",
    )


# ── status projection ───────────────────────────────────────────────────────


def run_status(ws: Workspace, state: State, action: Action | None) -> dict[str, Any]:
    """The ``run.json`` fields for the current derivation."""
    refusal = state.refusal or (action.refusal if action and action.kind == "refusal" else None)
    request = action.request if action and action.kind == "request" else None
    terminal = action is not None and action.kind == "terminal"
    if terminal:
        stage = "terminal"
    elif refusal is not None:
        stage = "awaiting-human"
    elif request is not None:
        stage = request["stage"]
    else:
        stage = "admitted"
    gate = request is not None and request["kind"] == "human-decision"
    return {
        "run_id": state.run_id,
        "active": bool(state.run_id) and not terminal,
        "stage": stage,
        "gate_pending": gate,
        "gate_question": request["question"] if gate and request else "",
        "refusal": refusal.as_dict() if refusal is not None else {},
    }


def _write_status(ws: Workspace, state: State, action: Action | None) -> dict[str, Any]:
    status = run_status(ws, state, action)
    ws.local.write_run(status)
    return status


# ── next ────────────────────────────────────────────────────────────────────


def _pending_replan(ws: Workspace, state: State) -> list[str]:
    """Controller edits to the spec, its plan, or a cited record not yet committed."""
    trusted = {f"{ws.spec_rel}/spec.md", f"{ws.spec_rel}/plan.md", *state.cited_paths}
    return [p for p in ws.git.change_set() if p in trusted]


def _prepare(ws: Workspace) -> tuple[State, Refusal | None]:
    """Derive, then sync, reconcile events, and commit a pending replan."""
    state = derive(ws)
    if state.refusal is not None:
        return state, state.refusal
    foreign = ws.git.sync(state.commits[-1].sha if state.commits else None)
    if foreign:
        return state, Refusal(
            "foreign-delivery-edit",
            "controller",
            "delivery records differ from HEAD: " + ", ".join(foreign),
        )
    ws.local.reconcile_events(state.run_id, state.commits)
    replan = _pending_replan(ws, state)
    if replan:
        # Bound to HEAD as well as content, so returning to earlier content is a
        # new step rather than a skipped one.
        digest = hashlib.sha256(state.head.encode() + b"\0")
        for path in replan:
            digest.update(path.encode() + b"\0" + (ws.git.read_working(path) or b"") + b"\0")
        ws.git.build_commit(
            run_id=state.run_id,
            step=f"replan:{digest.hexdigest()[:24]}",
            operation="replan",
            paths=replan,
            summary="replan",
            known_steps=state.steps,
        )
        state = derive(ws)
        ws.local.reconcile_events(state.run_id, state.commits)
    return state, None


def _act(ws: Workspace, state: State) -> tuple[State, Action]:
    """Run supervisor-internal steps until the current action is for the controller."""
    tdd = _supervisor("_supervisor_tdd.py")
    effects = _supervisor("_supervisor_effects.py")
    for _ in range(64):
        action = decide(ws, state)
        if action.kind == "auto-red":
            refusal = tdd.commit_supervisor_red(ws, state, action.detail["task"])
            if refusal is not None:
                return state, Action("refusal", refusal=refusal)
        elif action.kind == "effect-intent":
            request = effects.commit_intent(ws, state, action.detail)
            state = derive(ws)
            ws.local.reconcile_events(state.run_id, state.commits)
            return state, Action("request", request=request)
        elif action.kind == "terminal":
            commit_terminal(ws, state.run_id)
            state = derive(ws)
            ws.local.reconcile_events(state.run_id, state.commits)
            return state, Action("terminal")
        else:
            return state, action
        state = derive(ws)
        ws.local.reconcile_events(state.run_id, state.commits)
    raise Refusal("no-progress", "skill maintainer", "the step loop did not settle")


def next_request(ws: Workspace) -> dict[str, Any]:
    """The ``next`` verb: the current request, a refusal, or terminal."""
    with ws.run_lock():
        state, refusal = _prepare(ws)
        if refusal is not None:
            state.refusal = refusal
            return {"refusal": refusal.as_dict(), "run": _write_status(ws, state, None)}
        state, action = _act(ws, state)
        status = _write_status(ws, state, action)
        if action.kind == "refusal" and action.refusal is not None:
            return {"refusal": action.refusal.as_dict(), "run": status}
        if action.kind == "terminal":
            ws.local.append_journal({
                "run_id": state.run_id,
                "at": ws.clock(),
                "head": state.head,
                "stage": "terminal",
                "kind": "terminal",
                "request_id": None,
            })
            return {"terminal": True, "run": status}
        request = action.request or {}
        ws.local.append_journal({
            "run_id": state.run_id,
            "at": ws.clock(),
            "head": state.head,
            "stage": request["stage"],
            "kind": request["kind"],
            "request_id": request["request_id"],
        })
        return {"request": request, "run": status}


# ── report ──────────────────────────────────────────────────────────────────


def _validate_result(result: object) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("schema_version") != SCHEMA_VERSION:
        raise Refusal("invalid-result", "controller", "result must be an execution-result.v1")
    for key in ("request_id", "run_id", "kind"):
        if not isinstance(result.get(key), str) or not result[key]:
            raise Refusal("invalid-result", "controller", f"result {key} is missing")
    return result


def report(ws: Workspace, result: object) -> dict[str, Any]:
    """The ``report`` verb: admit a result for the current request, or refuse it."""
    tdd = _supervisor("_supervisor_tdd.py")
    effects = _supervisor("_supervisor_effects.py")
    readiness = _supervisor("_supervisor_readiness.py")
    checked = _validate_result(result)
    with ws.run_lock():
        state = derive(ws)
        if state.refusal is not None:
            raise state.refusal
        if checked["run_id"] != state.run_id:
            raise Refusal("not-current-run", "controller", "the result names another run")
        _lagging, foreign = ws.git.delivery_lag()
        if foreign:
            raise Refusal("foreign-delivery-edit", "controller", ", ".join(foreign))
        if checked["kind"] in ("external-effect", "effect-query"):
            outcome = effects.report_effect(ws, state, checked)
        else:
            action = decide(ws, state)
            current = action.request if action.kind == "request" else None
            if (
                current is None
                or current["request_id"] != checked["request_id"]
                or current["kind"] != checked["kind"]
            ):
                raise Refusal(
                    "not-current-attempt",
                    "controller",
                    "the result is not for the current request",
                )
            changed = ws.git.change_set()
            protected = [
                p for p in changed if p.startswith(ws.spec_rel + "/") or p in state.cited_paths
            ]
            if protected:
                raise Refusal(
                    "protected-path-changed",
                    "controller",
                    "the attempt changed trusted files: " + ", ".join(protected),
                )
            kind = checked["kind"]
            if kind in ("implement-task", "write-stub"):
                outcome = tdd.report_task(ws, state, current, checked, changed)
            elif kind in ("run-gates", "review-role", "assess-finding"):
                if changed:
                    raise Refusal(
                        "unexpected-change",
                        "controller",
                        "the attempt changed files: " + ", ".join(changed[:20]),
                    )
                outcome = readiness.report_readiness(ws, state, current, checked)
            else:
                raise Refusal(
                    "unsupported-result",
                    "controller",
                    f"a {kind} result is not admitted through report",
                )
        after = derive(ws)
        ws.local.reconcile_events(after.run_id, after.commits)
        return {"admitted": outcome}


def status(ws: Workspace) -> dict[str, Any]:
    """Stage, readiness, projection, decisions, and the retry count; never commits."""
    state = derive(ws)
    if state.refusal is not None:
        return {
            "run": run_status(ws, state, None),
            "refusal": state.refusal.as_dict(),
            "terminal": False,
            "retry_count": _safe_count(ws, state),
        }
    action = decide(ws, state)
    readiness = _supervisor("_supervisor_readiness.py")
    return {
        "run": run_status(ws, state, action),
        "terminal": action.kind == "terminal",
        "retry_count": state.retry_count,
        "retry_cap": int(ws.policy["implementation_retry_cap"]),
        "readiness": readiness.readiness(ws, state),
        "tasks": [
            {
                "task_id": t["task_id"],
                "position": t["position"],
                "title": t["title"],
                "complete": state.is_complete(t),
            }
            for t in state.tasks
        ],
        "request": action.request,
        "refusal": action.refusal.as_dict() if action.refusal else {},
    }


def _safe_count(ws: Workspace, state: State) -> int:
    """The retry count even when the working spec is refused."""
    if not state.approvals:
        return 0
    state.run_id = state.approvals[0]["run_id"]
    state.receipts = _evidence_receipts(ws)
    return state.retry_count


def dump(record: dict[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True)
