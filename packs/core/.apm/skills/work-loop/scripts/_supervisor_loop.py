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

After a ``write-stub`` result is refused as not red, the next change to a trusted
file is not committed on the controller's word. ``decide`` opens a
``human-decision`` carrying the diff and a digest of the exact bytes; ``report``
commits the ``replan`` only when a named human confirms it, the uncommitted change
set is exactly the files that digest binds, and their bytes still match it. This
confirmation is the one ``human-decision`` ``report`` accepts over uncommitted
trusted-file edits. A decline commits nothing, and ``next`` refuses until the
trusted files match ``HEAD`` again, whatever they hold meanwhile. The restore brings
back the fence that was not red, so ``next`` reissues ``write-stub`` and the stub runs
again; only after that attempt closes again does a different edit open a new
confirmation. A file the discard could not remove blocks every step until the
controller removes it or restores it to ``HEAD``.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import stat
import sys
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
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
_attempt = _supervisor("_supervisor_attempt.py")
Refusal = _admission.Refusal
Workspace = _admission.Workspace
sibling = _commit.sibling

__all__ = [
    "State",
    "derive",
    "next_request",
    "execute_gates",
    "commit_record",
    "correct_task",
    "report",
    "status",
    "commit_terminal",
    "untrusted_blocked",
    "accept_facts",
]

PRODUCER_CLASS = "work-supervisor"
SCHEMA_VERSION = 1
_STAGE_OF_KIND = {
    "implement-task": "implementing",
    "run-concurrent": "implementing",
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
    corrections: list[dict[str, Any]] = field(default_factory=list)
    review_budget: dict[str, Any] = field(default_factory=dict)

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

    def task_epoch(self, task_id: str) -> int:
        """Latest invalidation epoch for a task, including dependencies removed by replan."""
        for correction in reversed(self.corrections):
            if task_id in _correction_tasks(self, correction["task_id"]) or any(
                r["receipt_id"] in correction["affected_receipt_ids"]
                and r["lineage"]["criterion_ref"] == f"task:{task_id}" for r in self.receipts
            ):
                return int(correction["invalidation_epoch"])
        return 0

    def failed_attempts(self, task: dict[str, Any]) -> int:
        """Count failures without treating owner corrections as gate failures."""
        term = f"gate:{task['task_id']}:{task['revision']}"
        return sum(1 for r in self.task_gate_receipts("fail") if r["selector"]["term"] == term)

    def attempt(self, task: dict[str, Any]) -> int:
        """Reserve fresh attempts after correction without resetting the failure count."""
        return 1 + self.failed_attempts(task) + self.task_epoch(task["task_id"])

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
    state.review_budget = load_review_budget(ws, state.run_id)
    # Budget evidence belongs to the run even when a replan refuses the spec.
    state.receipts = _evidence_receipts(ws)
    _project_review_budget(ws, state)
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
            _projector.project_plan(plan_text, spec_dir=ws.spec_rel)
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
    state.corrections = ws.records("task-corrections.jsonl")
    es = sibling("_evidence_store.py")
    epochs: dict[str, int] = {}
    for epoch, record in enumerate(state.corrections, 1):
        valid, code = es.validate_task_correction(record)
        if not valid or record["run_id"] != state.run_id or record["invalidation_epoch"] != epoch:
            raise Refusal("malformed-record", "controller", f"invalid task correction: {code}")
        marker = next((i for i, c in enumerate(state.commits)
                       if c.step == record["correction_id"]), None)
        if marker is None:
            raise Refusal("malformed-record", "controller", "correction commit is absent")
        affected = _correction_tasks(state, record["task_id"])
        # Keep the dependent task identities invalid even if a later replan drops an edge.
        affected.update(r["lineage"]["criterion_ref"].removeprefix("task:")
                        for r in state.receipts
                        if r["receipt_id"] in record["affected_receipt_ids"]
                        and r["lineage"]["criterion_ref"].startswith("task:"))
        for identity in affected:
            epochs[identity] = marker
    for index, c in enumerate(state.commits):
        task_key = (
            c.trailers.get("Supervisor-Task", ""),
            c.trailers.get("Supervisor-Task-Revision", ""),
        )
        if c.operation == "implement" and index > epochs.get(task_key[0], -1):
            state.completed[task_key] = c.sha
        elif c.operation in ("stub", "red"):
            state.red.add((task_key[0], c.trailers.get("Supervisor-Stub-Digest", "")))
    state.effects = ws.records("effect-resolutions.jsonl")
    return state


def load_review_budget(ws: Workspace, run_id: str) -> dict[str, Any]:
    """Read the enduring budget before any spec classification can refuse state."""
    artifact = _supervisor("review-artifact.py")
    directory = ws.git._store_dir(run_id)
    fs = sibling("_file_safety.py")
    if not os.path.lexists(directory / "review-budget.json"):
        if os.path.lexists(directory / _attempt.PINS_FILE):
            raise Refusal("invalid-review-budget", "controller", "budget record is missing")
        # A clone or interrupted first admission has no local snapshot yet.
        budget = copy.deepcopy(ws.approvals()[0].get("review_budget"))
        if budget is None:
            budget = artifact.new_review_budget(run_id)
        try:
            artifact.validate_review_budget(budget)
        except artifact.ArtifactError as exc:
            raise Refusal(
                "invalid-review-budget", "controller", "approval budget is malformed",
            ) from exc
        return budget
    try:
        raw = fs.read_confined_regular_file(
            directory, directory / "review-budget.json", max_bytes=1024 * 1024,
        )
    except (OSError, fs.UnsafeContentError) as exc:
        raise Refusal("invalid-review-budget", "controller", "budget is unreadable") from exc
    try:
        budget = json.loads(raw)
        artifact.validate_review_budget(budget)
    except (ValueError, artifact.ArtifactError) as exc:
        raise Refusal("invalid-review-budget", "controller", "budget record is malformed") from exc
    return budget


def prepare_review_budget(ws: Workspace, review_run_id: str | None) -> dict[str, Any]:
    """Validate the review binding before admission can move either ref."""
    approvals = ws.approvals()
    if approvals:
        budget = load_review_budget(ws, approvals[0]["run_id"])
        if review_run_id is not None and budget["review_run_id"] != review_run_id:
            raise Refusal(
                "invalid-review-budget", "controller", "review identity is already bound",
            )
        return budget
    artifact = _supervisor("review-artifact.py")
    if review_run_id is None:
        run_id = "run-" + hashlib.sha256(
            f"{ws.spec_rel}\0{ws.git.head()}".encode(),
        ).hexdigest()[:16]
        return artifact.new_review_budget(str(uuid.uuid5(uuid.NAMESPACE_URL, run_id)))  # type: ignore[no-any-return]
    try:
        return artifact.load_review_budget(ws.root, review_run_id)  # type: ignore[no-any-return]
    except (ValueError, artifact.ArtifactError, artifact.UsageError) as exc:
        raise Refusal(
            "invalid-review-budget", "controller", "review budget cannot be imported",
        ) from exc


def save_review_budget(ws: Workspace, state: State) -> None:
    """Atomically checkpoint the budget apart from replaceable status and recovery state."""
    if not state.review_budget:
        return
    directory = ws.git.ensure_store(state.run_id)
    sibling("_confined_mutation.py").confined_atomic_replace(
        directory, directory / "review-budget.json",
        _admission.canonical_line(state.review_budget),
    )


def _project_review_budget(ws: Workspace, state: State) -> None:
    """Refresh numbered review snapshots without resetting saved counts or identity."""
    artifact = _supervisor("review-artifact.py")
    previous = state.review_budget
    budget = copy.deepcopy(previous)
    try:
        review_run_id = artifact._parse_run_id(previous["review_run_id"])
    except artifact.UsageError:
        # A stored identity may predate numbered review artifacts.
        review_run_id = None
    if review_run_id is not None:
        try:
            latest = artifact.load_review_budget(ws.root, review_run_id)
        except (ValueError, artifact.ArtifactError) as exc:
            raise Refusal(
                "invalid-review-budget", "controller", "review artifacts are unreadable",
            ) from exc
        if sum(latest["rounds"].values()) > sum(previous["rounds"].values()):
            budget = latest
    budget["failed_task_gates"] = max(budget["failed_task_gates"], state.retry_count)
    # Temporary artifact cleanup and adopted history cannot refund a saved count.
    for key in ("rounds", "repairs", "code_review_rounds"):
        for name, count in previous[key].items():
            budget[key][name] = max(budget[key].get(name, 0), count)
    for key in ("active_hours", "retries", "finding_records", "failed_task_gates"):
        budget[key] = max(budget[key], previous[key])
    # Owner grants are committed with the decision, so a crash before the
    # local checkpoint cannot lose one or turn replay into another grant.
    for commit in ws.git.supervisor_commits(state.run_id):
        target = commit.trailers.get("Supervisor-Review-Budget-Round")
        if target is not None:
            extension = {
                "phase": "implementation", "round": int(target),
                "authority_ref": commit.trailers.get("Supervisor-Authority-Ref"),
            }
            if budget["extension"] is None or budget["extension"]["round"] < extension["round"]:
                budget["extension"] = extension
    imported = ws.approvals()[0].get("review_budget", {}).get("active_hours", 0)
    measured = _active_report_times(ws, state.run_id)
    for commit in ws.git.supervisor_commits(state.run_id):
        seconds = commit.trailers.get("Supervisor-Active-Seconds")
        if seconds is not None:
            identity = commit.trailers.get("Supervisor-Active-Request", commit.step)
            measured[identity] = max(measured.get(identity, 0.0), float(seconds))
    budget["active_hours"] = max(budget["active_hours"], imported + sum(measured.values()) / 3600)
    artifact.validate_review_budget(budget)
    state.review_budget = budget


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
    ws: Workspace, state: State, reason: str, question: str, key: str = "", **fields: Any
) -> dict[str, Any]:
    digest = hashlib.sha256(f"{reason}\0{key}\0{state.head}".encode()).hexdigest()[:16]
    return make_request(
        ws,
        state,
        "human-decision",
        f"decide:{reason}:{digest}",
        reason=reason,
        question=question,
        **fields,
    )


def review_cap_decision(
    ws: Workspace,
    state: State,
    question: str,
    *,
    round_count: int,
    selection_key: str,
    answered: int,
    open_findings: list[dict[str, Any]],
    budget_limit: str | None = None,
) -> dict[str, Any]:
    """The ``review-cap`` human decision.

    Its id comes from the run, the round count, the selection key, how many ``review-cap``
    answers the unit has admitted, and the sorted cap finding references: no ``HEAD`` salt,
    so an unrelated commit never reissues it, and an answered request's id never returns.
    """
    refs = sorted(f["cap_ref"] for f in open_findings)
    identity = "\0".join(
        [state.run_id, str(round_count), selection_key, str(answered), *refs]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return make_request(
        ws,
        state,
        "human-decision",
        f"decide:review-cap:{digest}",
        reason="review-cap",
        question=question,
        round_count=round_count,
        selection_key=selection_key,
        open_findings=sorted(open_findings, key=lambda f: f["cap_ref"]),
        **({"budget_reason": "review-budget-exhausted", "budget_limit": budget_limit}
           if budget_limit is not None else {}),
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

    kind: str  # request | refusal | terminal | auto-red | effect-intent | review-carry
    request: dict[str, Any] | None = None
    refusal: Refusal | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def untrusted_blocked(state: State) -> bool:
    """True when the run is ``untrusted`` and the host supplies no verified containment.

    The supervisor then launches no repository code and issues no ``implement-task``,
    ``run-gates``, or ``regenerate`` request: no task, gate, red proof, scratch
    receipt, or regeneration.
    """
    if state.latest["code_trust"] != "untrusted":
        return False
    containment = _supervisor("_containment.py")
    return not containment.report_host_containment_axes().get("verified_sandbox")


def untrusted_decision(ws: Workspace, state: State) -> Action:
    """The ``human-decision`` that asks for trust or containment before code runs."""
    return Action(
        "request",
        human_decision(
            ws,
            state,
            "untrusted-code",
            "The run's code trust is untrusted and this host supplies no verified "
            "containment, so the supervisor will not run tasks, gates, red proofs, "
            "scratch receipts, or a regeneration of the installed skill. Re-approve the run as "
            "trusted with an owner authority reference (start --code-trust trusted), or "
            "supply verified containment.",
        ),
    )


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
    if ws.divergence is not None:
        return _supervisor("_supervisor_recovery.py").adoption_action(ws, state, ws.divergence)
    pending = _pending_correction(ws, state)
    if pending is not None:
        return Action("request", pending)
    if is_terminal(ws, state):
        return Action("terminal")
    if state.intent == "spec-plan":
        return Action("terminal")
    gate = _supervisor("_supervisor_recovery.py").gate(ws, state)
    if gate is not None:
        return gate
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
        if ws.policy["concurrency"] == "sequential" or untrusted_blocked(state):
            return tdd.task_action(ws, state, task)
        concurrent = _supervisor("_supervisor_concurrent.py")
        admitted, reason = concurrent.admit(ws, state, task)
        if admitted is not None:
            return admitted
        floor = tdd.task_action(ws, state, task)
        floor.detail = {**floor.detail, "floor_reason": reason}
        return floor
    if any_pending:
        return Action(
            "refusal",
            refusal=Refusal(
                "dependency-cycle",
                "plan author",
                "no incomplete task has its dependencies complete",
            ),
        )
    if _supervisor("_supervisor_concurrent.py").results_pending(ws, state):
        # No gate, review, or evidence beside an open attempt or a held result; a held result
        # whose task is complete cannot be integrated, so nothing may go on past it.
        return Action(
            "refusal",
            refusal=Refusal(
                "no-progress",
                "skill maintainer",
                "a held result or an open attempt remains with every task complete, so no "
                "gate, review, or evidence is issued",
            ),
        )
    dirty = ws.git.change_set(rehash=state.cited_paths)
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
    try:
        action = readiness.readiness_action(ws, state)
    except Refusal as exc:
        # A rules or selection defect: the stage stays unsatisfied and names its code.
        return Action("refusal", refusal=exc)
    if action is not None:
        gates = action.request is not None and action.request["kind"] == "run-gates"
        return untrusted_decision(ws, state) if gates and untrusted_blocked(state) else action
    source = ws.attempts.pending_regeneration()
    if source is not None:
        if untrusted_blocked(state):
            return untrusted_decision(ws, state)
        return Action(
            "request",
            make_request(ws, state, "regenerate", _attempt.regenerate_request_id(source)),
            detail={"source_digests": source},
        )
    for name in state.finish_effects:
        action = effects.effect_action(ws, state, name, scope="finish", task=None)
        if action is not None:
            return action
    return Action("terminal")


def _terminal_step(ws: Workspace, state: State) -> str:
    """Bind terminal completion to the current correction epoch as well as the tree."""
    step = f"terminal:{ws.git.product_tree()}"
    return f"{step}:correction:{len(state.corrections)}" if state.corrections else step


def is_terminal(ws: Workspace, state: State) -> bool:
    """True when a terminal step for the current product tree is reachable."""
    return (_terminal_step(ws, state) in state.steps
            and _pending_correction(ws, state) is None)


def commit_terminal(ws: Workspace, run_id: str) -> None:
    """Commit the terminal step with its terminal receipt; idempotent."""
    state = derive(ws)
    tree = ws.git.product_tree()
    step = _terminal_step(ws, state)
    if step in state.steps:
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
        "review_budget": state.review_budget,
    }


def _write_status(ws: Workspace, state: State, action: Action | None) -> dict[str, Any]:
    save_review_budget(ws, state)
    status = run_status(ws, state, action)
    ws.local.write_run(status)
    return status


# ── next ────────────────────────────────────────────────────────────────────


def _pending_replan(ws: Workspace, state: State) -> list[str]:
    """Controller edits to the spec, its plan, or a cited record not yet committed."""
    trusted = {f"{ws.spec_rel}/spec.md", f"{ws.spec_rel}/plan.md", *state.cited_paths}
    return [p for p in ws.git.change_set(rehash=state.cited_paths) if p in trusted]


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
    recovery = _supervisor("_supervisor_recovery.py")
    unowed = recovery.settle(ws, state, replan)
    if replan and unowed:
        # Bound to HEAD as well as content, so returning to earlier content is a
        # new step rather than a skipped one.
        digest = recovery.replan_digest(state.head, recovery.read_contents(ws, replan))
        ws.git.build_commit(
            run_id=state.run_id,
            step=f"replan:{digest[:24]}",
            operation="replan",
            paths=replan,
            summary="replan",
            known_steps=state.steps,
        )
        state = derive(ws)
        ws.local.reconcile_events(state.run_id, state.commits)
        _supervisor("_supervisor_concurrent.py").discard_stale(ws, state.run_id)
    plan = ws.attempts.regenerate_plan(state.run_id)
    if plan is not None:
        # A tracked install the regeneration rebuilt is the pack source the repository
        # already holds, so the supervisor commits the pack source's own entries as its step
        # (never the working tree's bytes), and a controller commit of it stays foreign history.
        key = hashlib.sha256(f"{state.head}\0{plan.digest}".encode()).hexdigest()[:24]
        ws.git.build_commit(
            run_id=state.run_id,
            step=f"regenerate:{key}",
            operation="regenerate",
            entries=plan.entries,
            verify_tree=lambda tree: plan.verify(ws.git, tree),
            summary="regenerate",
            known_steps=state.steps,
        )
        state = derive(ws)
        ws.local.reconcile_events(state.run_id, state.commits)
    return state, None


def _act(ws: Workspace, state: State) -> tuple[State, Action]:
    """Run supervisor-internal steps until the current action is for the controller."""
    tdd = _supervisor("_supervisor_tdd.py")
    effects = _supervisor("_supervisor_effects.py")
    readiness = _supervisor("_supervisor_readiness.py")
    for _ in range(64):
        action = decide(ws, state)
        if action.kind in ("auto-red", "effect-intent", "terminal", "review-carry"):
            # Nothing commits on top of a regenerate step the install does not match.
            ws.attempts.confirm_admitted(state.run_id)
        if action.kind == "auto-red":
            refusal = tdd.commit_supervisor_red(ws, state, action.detail["task"])
            if refusal is not None:
                return state, Action("refusal", refusal=refusal)
        elif action.kind == "review-carry":
            readiness.commit_carries(ws, state)
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
        ws.attempts.guard("next")
        recovery = _supervisor("_supervisor_recovery.py")
        _supervisor("_supervisor_concurrent.py").recover(ws)
        try:
            diverged = recovery.reconcile(ws)
        except Refusal as exc:
            # The ref check refused: leave run.json in the refused shape the controller reads.
            state = _adoption_state(ws)
            state.refusal = exc
            return {"refusal": exc.as_dict(), "run": _write_status(ws, state, None)}
        if diverged is not None:
            return _adoption_request(ws)
        _supervisor("_supervisor_integration.py").integrate_ready(ws)
        state, refusal = _prepare(ws)
        if refusal is not None:
            state.refusal = refusal
            return {"refusal": refusal.as_dict(), "run": _write_status(ws, state, None)}
        state, action = _act(ws, state)
        ws.attempts.issue(state, action)
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
        _record_request_time(ws, state.run_id, request)
        reason = action.detail.get("floor_reason")
        ws.local.append_journal({
            "run_id": state.run_id,
            "at": ws.clock(),
            "head": state.head,
            "stage": request["stage"],
            "kind": request["kind"],
            "request_id": request["request_id"],
            **({"floor_reason": reason} if reason else {}),
        })
        return {"request": request, "run": status}


def _adoption_state(ws: Workspace) -> State:
    """The run's state, or just its identity when the working spec is refused.

    A controller's amendment commit is history the run did not make, so the
    adoption decision comes before the refusal that amendment would raise.
    """
    state = derive(ws)
    if state.refusal is None:
        return state
    state.refusal = None
    state.head = ws.git.head()
    state.commits = ws.git.supervisor_commits(state.run_id)
    state.steps = {c.step for c in state.commits}
    return state


def _adoption_request(ws: Workspace) -> dict[str, Any]:
    """The ``history-adoption`` request for a ``HEAD`` the run has not admitted; no commit."""
    state = _adoption_state(ws)
    action = decide(ws, state)
    status = _write_status(ws, state, action)
    request = action.request or {}
    _record_request_time(ws, state.run_id, request)
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


# The facts each request kind's result may assert (the Result acceptance table).
_RESULT_FACTS: dict[str, frozenset[str]] = {
    "implement-task": frozenset({"gate"}),
    "run-concurrent": frozenset(),
    "write-stub": frozenset(),
    "review-role": frozenset({"report", "selection"}),
    "assess-finding": frozenset({"assessment"}),
    "run-gates": frozenset({"gate", "criteria"}),
    "external-effect": frozenset({"effect"}),
    "effect-query": frozenset({"effect"}),
    "regenerate": frozenset(),
    "human-decision": frozenset({"decision"}),
}
_RESULT_ENVELOPE = frozenset({"schema_version", "request_id", "run_id", "kind"})


def accept_facts(result: dict[str, Any]) -> None:
    """Refuse a result that asserts a fact its request kind's row does not list.

    An unknown kind asserts nothing. Runs before any state is read or written.
    """
    kind = result["kind"]
    allowed = _RESULT_FACTS.get(kind)
    if allowed is None:
        raise Refusal(
            "result-kind-refused", "controller", f"a {kind!r} result is not a request kind"
        )
    extra = sorted(set(result) - _RESULT_ENVELOPE - allowed)
    if extra:
        raise Refusal(
            "result-fact-refused",
            "controller",
            f"a {kind} result may not assert: " + ", ".join(extra),
        )
    if kind == "review-role" and {"report", "selection"} <= set(result):
        raise Refusal(
            "result-fact-refused",
            "controller",
            "a review-role result asserts a report or a selection, not both",
        )


def _refuse_protected_change(ws: Workspace, state: State, *, exempt: bool = False) -> list[str]:
    """Return the change set, refusing one that touches the spec directory or a cited record.

    *exempt* skips that refusal for a replan confirmation, which checks its own change set.
    """
    changed = ws.git.change_set(rehash=state.cited_paths)
    protected = [p for p in changed if p.startswith(ws.spec_rel + "/") or p in state.cited_paths]
    if protected and not exempt:
        raise Refusal(
            "protected-path-changed",
            "controller",
            "the attempt changed trusted files: "
            + ", ".join(protected)
            + ". Restore them; a spec-directory deliverable lands by your own commit, "
            "which the owner adopts through history-adoption, or use commit-record for "
            "an exact path declared in the approved record-paths block.",
        )
    ws.attempts.check_change_set(state, changed)
    return changed


def _record_manifest(ws: Workspace, filename: str) -> dict[str, Any]:
    """Read the controller's closed manifest; no worker result enters this path.

    ``kind`` is a bounded descriptive record category, not an authority claim.
    Entries add or replace files; removals have no new digest and are not admitted.
    """
    execution = _supervisor("_supervisor_execution.py")
    try:
        path = Path(filename).absolute()
        root = path.parent.resolve(strict=True)
        raw = sibling("_file_safety.py").read_confined_regular_file(
            root, root / path.name, max_bytes=1024 * 1024)
        record = execution.load_json(raw)
        fields = {"schema_version", "type", "run_id", "base_commit",
                  "envelope_fingerprint", "entries"}
        if (not isinstance(record, dict) or set(record) != fields
                or type(record["schema_version"]) is not int or record["schema_version"] != 1
                or record["type"] != "record-manifest.v1"
                or not execution._text(record["run_id"])
                or not execution._text(record["base_commit"])
                or not execution._digest(record["envelope_fingerprint"])
                or not isinstance(record["entries"], list) or not record["entries"]):
            raise ValueError("manifest fields differ from record-manifest.v1")
        seen: set[str] = set()
        for entry in record["entries"]:
            if (not isinstance(entry, dict)
                    or set(entry) != {"path", "kind", "old_sha256", "new_sha256"}
                    or not execution._text(entry["kind"]) or len(entry["kind"]) > 128
                    or not execution._digest(entry["new_sha256"])
                    or (entry["old_sha256"] is not None
                        and not execution._digest(entry["old_sha256"]))):
                raise ValueError("invalid record entry")
            if not _projector.exact_record_path(entry["path"]):
                raise Refusal("record-path-refused", "controller", "an exact path is required")
            if entry["path"] in seen:
                raise ValueError("duplicate record path")
            seen.add(entry["path"])
    except Refusal:
        raise
    except (OSError, ValueError, RuntimeError) as exc:
        raise Refusal("record-manifest-invalid", "controller", str(exc)) from exc
    return record  # type: ignore[no-any-return]


def _check_record_paths(ws: Workspace, state: State, manifest: dict[str, Any]) -> list[str]:
    """Apply the approved allowlist without weakening worker path protections."""
    try:
        declared = _projector.record_paths(ws.spec_text())
    except _projector.ProjectionRefused as exc:
        raise Refusal(exc.code, exc.owner, exc.detail) from exc
    if not declared:
        raise Refusal("record-paths-disabled", "spec author", "no approved record paths")

    def folded(path: str) -> str:
        return unicodedata.normalize("NFC", path).casefold()

    protected = {folded(p) for p in [*state.cited_paths, ws.spec_rel + "/spec.md",
                                    ws.spec_rel + "/plan.md"]}
    controls = {".git", ".supervisor", "delivery", ".agents", ".claude", ".codex",
                ".cursor", ".gemini", ".kiro", ".apm", ".github"}
    installed = ws.attempts._tracked_skill_prefix()
    paths = [e["path"] for e in manifest["entries"]]
    for path in paths:
        normalized = folded(path)
        if (path not in declared or normalized in protected
                or controls.intersection(normalized.split("/"))
                or (installed is not None and normalized.startswith(folded(installed)))):
            raise Refusal("record-path-refused", "controller",
                          "record path is undeclared or protected: " + path)
    return paths


def commit_record(ws: Workspace, filename: str) -> dict[str, Any]:
    """Commit exact controller record bytes and one audit row under the run lock.

    The builder compares HEAD and the product ref in one Git transaction. Its
    existing post-move store write intentionally retains history-adoption on a
    crash; a path name or a commit trailer never proves controller authorship.
    """
    with ws.run_lock():
        if ws.attempts.guard("commit-record") is not None:
            raise Refusal("record-attempt-open", "controller", "settle the open attempt first")
        recovery = _supervisor("_supervisor_recovery.py")
        if recovery.reconcile(ws, require_recorded_head=True) is not None:
            raise recovery.unadopted(ws)
        state = derive(ws)
        if state.refusal is not None:
            raise state.refusal
        if (recovery.leftovers(ws, state)
                or ws.attempts.recovery(state.run_id)["owed"]
                or _supervisor("_supervisor_concurrent.py").results_pending(ws, state)):
            raise Refusal("record-attempt-open", "controller", "settle attempts and residue first")
        manifest = _record_manifest(ws, filename)
        paths = _check_record_paths(ws, state, manifest)
        fingerprint = state.latest["envelope"]["envelope_fingerprint"]
        if (manifest["run_id"] != state.run_id
                or manifest["envelope_fingerprint"] != fingerprint):
            raise Refusal("record-manifest-invalid", "controller",
                          "manifest run or envelope differs")
        digest = hashlib.sha256(_admission.canonical_line(manifest)).hexdigest()
        step = "record:" + digest
        audit_fields = {"schema_version", "type", "manifest_digest", "run_id", "base_commit",
                        "envelope_fingerprint", "entries"}
        for row in ws.records("record-commits.jsonl"):
            if (set(row) != audit_fields or type(row["schema_version"]) is not int
                    or row["schema_version"] != 1 or row["type"] != "record-commit.v1"
                    or row["run_id"] != state.run_id):
                raise Refusal("malformed-record", "controller", "invalid record-commit.v1 audit")
            if row["manifest_digest"] == digest:
                expected = {**manifest, "type": "record-commit.v1", "manifest_digest": digest}
                if row != expected or step not in state.steps:
                    raise Refusal("malformed-record", "controller",
                          "record commit binding differs")
                return {"record_commit": {"manifest_digest": digest, "already_committed": True}}
        product = ws.git.product_record(state.run_id)
        if (product is None or state.head != product.recorded
                or manifest["base_commit"] != state.head):
            raise Refusal("record-base-mismatch", "controller",
                          "manifest base must equal recorded HEAD")
        frozen: dict[str, tuple[str, str] | None] = {}
        modes = ws.git.tree_modes(state.head)
        for entry in manifest["entries"]:
            path = entry["path"]
            before = ws.git.show(path, state.head)
            old_digest = None if before is None else hashlib.sha256(before).hexdigest()
            data = ws.git.read_working(path)
            if (old_digest != entry["old_sha256"] or data is None
                    or hashlib.sha256(data).hexdigest() != entry["new_sha256"]):
                raise Refusal("record-content-mismatch", "controller",
                          "record bytes differ: " + path)
            oid = ws.git.text("hash-object", "-w", "--stdin", stdin=data).strip()
            mode = modes[path][0] if path in modes else "100644"
            if mode not in ("100644", "100755"):
                raise Refusal("record-path-refused", "controller", "record must be a regular file")
            frozen[path] = (mode, oid)
        lagging, foreign = ws.git.delivery_lag()
        if (set(ws.git.change_set(rehash=[*state.cited_paths, *paths])) != set(paths)
                or lagging or foreign):
            raise Refusal("record-unexpected-change", "controller",
                          "changes exceed manifest paths")
        audit = {**manifest, "type": "record-commit.v1", "manifest_digest": digest}
        commit = ws.git.build_commit(
            run_id=state.run_id, step=step, operation="commit-record", entries=frozen,
            appends={"record-commits.jsonl": _admission.canonical_line(audit)},
            summary="controller records", known_steps=state.steps, parent=state.head,
            product_source=product.recorded, base_tree=state.head,
        )
        return {"record_commit": {"commit": commit, "manifest_digest": digest,
                                   "already_committed": False}}


def _correction_tasks(state: State, task_id: str) -> set[str]:
    """The task and all transitive dependents in the current plan."""
    affected = {task_id}
    while True:
        added = {t["task_id"] for t in state.tasks if affected.intersection(t["depends_on"])}
        if added <= affected:
            return affected
        affected |= added


def _pending_correction(ws: Workspace, state: State) -> dict[str, Any] | None:
    """Read the supervisor-opened owner request; committed answers close it."""
    store = ws.git._store_dir(state.run_id)
    path = store / "task-correction-request.json"
    if not os.path.lexists(path):
        return None
    try:
        raw = sibling("_file_safety.py").read_confined_regular_file(store, path, max_bytes=65536)
        request = _supervisor("_supervisor_execution.py").load_json(bytes(raw))
        fields = {"schema_version", "request_id", "run_id", "spec", "kind", "stage", "reason",
                  "question", "task", "target_commit", "correction_reason"}
        if (not isinstance(request, dict) or set(request) != fields
                or type(request.get("schema_version")) is not int or request["schema_version"] != 1
                or request.get("spec") != ws.spec_rel
                or request.get("stage") != "awaiting-human"
                or request.get("run_id") != state.run_id
                or request.get("kind") != "human-decision"
                or request.get("reason") != "task-correction"
                or not isinstance(request.get("task"), dict)
                or not all(isinstance(request.get(k), str) and request[k]
                           for k in ("request_id", "target_commit", "correction_reason"))):
            raise ValueError("invalid correction request")
    except Exception as exc:
        raise Refusal("malformed-record", "controller", "unreadable correction request") from exc
    if any(c["correction_id"] == request["request_id"] for c in state.corrections):
        return None
    task = next((t for t in state.tasks if _task_ref(t) == request["task"]), None)
    if task is None or state.completed.get((task["task_id"], task["revision"])) != request[
            "target_commit"]:
        raise Refusal("correction-refused", "owner", "the correction target changed")
    return request


def correct_task(ws: Workspace, task_id: str, reason: str) -> dict[str, Any]:
    """Open an owner human decision; only its confirmed report appends a correction."""
    with _admission.checkout_admission(
        ws, allow_primary_checkout=True, reserve=False,
    ), ws.run_lock():
        ws.attempts.guard("correct-task")
        recovery = _supervisor("_supervisor_recovery.py")
        if recovery.reconcile(ws) is not None:
            raise recovery.unadopted(ws)
        state = derive(ws)
        if state.refusal is not None:
            raise state.refusal
        if (not isinstance(reason, str) or not reason.strip() or "\0" in reason
                or len(reason.encode()) > 8192):
            raise Refusal("correction-refused", "controller",
                          "a bounded correction reason is required")
        if ws.git.change_set(rehash=state.cited_paths):
            raise Refusal("unexpected-change", "controller", "correction needs a clean tree")
        if _supervisor("_supervisor_concurrent.py").results_pending(ws, state):
            raise Refusal("correction-refused", "controller",
                          "settle concurrent attempts and held results before correction")
        task = next((t for t in state.tasks if t["task_id"] == task_id
                     or t["position"] == task_id), None)
        if task is None or not state.is_complete(task):
            raise Refusal("correction-refused", "controller", "correction needs an admitted task")
        pending = _pending_correction(ws, state)
        if pending is not None:
            if (pending["task"]["task_id"] != task["task_id"]
                    or pending["correction_reason"] != reason):
                raise Refusal("correction-refused", "owner", "answer the open correction first")
            return {"request": pending,
                    "run": _write_status(ws, state, Action("request", pending))}
        _admission._write_checkout(_admission._checkout_path(ws), {
            "schema_version": 1, "run_id": state.run_id, "spec_rel": ws.spec_rel,
        })
        request = human_decision(
            ws, state, "task-correction",
            "Confirm correct-task with an owner authority reference and the target commit. "
            "The reference attributes this decision; it does not authenticate the owner.",
            key=f"{task['task_id']}:{task['revision']}:{reason}", task=_task_ref(task),
            target_commit=state.completed[(task["task_id"], task["revision"])],
            correction_reason=reason,
        )
        store = ws.git.ensure_store(state.run_id)
        sibling("_confined_mutation.py").confined_atomic_replace(
            store, store / "task-correction-request.json", _admission.canonical_line(request))
        action = Action("request", request)
        ws.attempts.issue(state, action)
        return {"request": request, "run": _write_status(ws, state, action)}


def _report_correction(ws: Workspace, state: State, request: dict[str, Any],
                       result: dict[str, Any]) -> str:
    """Append correction and receipt supersession atomically, keeping all prior records."""
    decision = result.get("decision")
    if (not isinstance(decision, dict)
            or set(decision) != {"decision", "authority_ref", "commit"}
            or decision["decision"] != "correct-task"
            or not _admission.check_authority_ref(decision["authority_ref"], "owner")
            or decision["commit"] != request["target_commit"]):
        raise Refusal("correction-refused", "owner",
                      "correct-task needs an owner authority reference and the target commit")
    affected = _correction_tasks(state, request["task"]["task_id"])
    ids = [r["receipt_id"] for r in state.receipts
           if r["producer"]["identity"] == state.run_id
           and (r["lineage"]["criterion_ref"].startswith(("run:", "AC-"))
                or r["lineage"]["criterion_ref"] in {f"task:{t}" for t in affected})]
    record = {
        "schema_version": 1, "type": "task-correction.v1",
        "correction_id": request["request_id"], "run_id": state.run_id,
        "task_id": request["task"]["task_id"], "task_revision": request["task"]["revision"],
        "target_commit": request["target_commit"], "affected_receipt_ids": ids,
        "reason": request["correction_reason"], "authority_ref": decision["authority_ref"],
        "invalidation_epoch": len(state.corrections) + 1,
    }
    valid, code = sibling("_evidence_store.py").validate_task_correction(record)
    if not valid:
        raise Refusal("malformed-record", "controller", code)

    def supersede(store: Any, issuer: Any, grant: Any, sink: Any) -> None:
        """Use the existing append-only supersession port for invalidated receipts."""
        if ids:
            store.append_supersession({
                "schema_version": 1, "supersession_id": f"supersede:{record['correction_id']}",
                "superseded_receipt_ids": ids,
                "authority": {"identity": decision["authority_ref"], "role": "owner"},
                "provenance": {"reason_code": "task-correction",
                               "source_ref": record["correction_id"]},
            }, transaction_id=f"tx:{record['correction_id']}",
                acceptance_fingerprint=ws.git.product_tree(), issuer=issuer, grant=grant,
                audit_sink=sink)

    ws.git.build_commit(
        run_id=state.run_id, step=record["correction_id"], operation="correction",
        appends={"task-corrections.jsonl": _admission.canonical_line(record),
                 "evidence.jsonl": ws.evidence_append(writer=supersede)},
        summary="correct admitted task", known_steps=state.steps,
    )
    return "correction"


def execute_gates(ws: Workspace, request_id: str) -> dict[str, Any]:
    """Observe the currently issued task or run gates under the exclusive run lock."""
    execution = _supervisor("_supervisor_execution.py")
    try:
        with ws.run_lock(), execution.lock_budget(ws) as lock_started:
            ws.attempts.guard("execute-gates")
            recovery = _supervisor("_supervisor_recovery.py")
            if recovery.reconcile(ws) is not None:
                raise recovery.unadopted(ws)
            state = derive(ws)
            if state.refusal is not None:
                raise state.refusal
            if untrusted_blocked(state):
                raise Refusal(
                    "gate-execution-untrusted", "controller", "untrusted code cannot run gates",
                )
            action = decide(ws, state)
            request = action.request if action.kind == "request" else None
            if (request is None or request["request_id"] != request_id
                    or request["kind"] not in ("implement-task", "run-gates")):
                raise Refusal(
                    "not-current-attempt", "controller", "gates need the current request",
                )
            ws.attempts.require_open_issuance(request)
            _refuse_protected_change(ws, state)
            try:
                return {"execution": execution.execute(ws, state, request, ws.attempts.open,
                                                        sys.modules[__name__], lock_started)}
            except _projector.ProjectionRefused as exc:
                raise Refusal(exc.code, exc.owner, exc.detail) from exc
    except execution.ExecutionRefused as exc:
        raise Refusal(exc.code, "controller", str(exc)) from exc


def _active_report_times(ws: Workspace, run_id: str) -> dict[str, float]:
    """Load accepted report timings, including reports which make no commit."""
    record = ws.attempts._store_record(run_id, "report-times.json")
    if record is None:
        return {}
    times = record.get("seconds")
    if (set(record) != {"schema_version", "run_id", "seconds"}
            or not isinstance(times, dict)
            or not all(isinstance(key, str) and key
                       and type(value) in (int, float) and math.isfinite(value) and value >= 0
                       for key, value in times.items())):
        raise Refusal("invalid-review-budget", "controller", "report clocks are malformed")
    return times


def _save_report_time(ws: Workspace, run_id: str) -> None:
    """Checkpoint an accepted report under the run lock, once per request identity."""
    timing = ws.git.report_timing
    if timing is None:
        return
    request_id, seconds = timing
    times = _active_report_times(ws, run_id)
    times[request_id] = max(times.get(request_id, 0.0), float(seconds))
    ws.attempts._put(run_id, "report-times.json", _admission.canonical_line({
        "schema_version": 1, "run_id": run_id, "seconds": times,
    }), replace=True)


def _request_time_name(request_id: str) -> str:
    """Keep opaque request identifiers out of filesystem locators."""
    return "request-time-" + hashlib.sha256(request_id.encode()).hexdigest() + ".json"


def _record_request_time(ws: Workspace, run_id: str, request: dict[str, Any]) -> None:
    """Retain a worker request's first issuance time across repeated next calls.

    A human decision measures a person's wait, not active work, and a verb that only
    reads a waiting decision leaves the run store unchanged.
    """
    if request.get("kind") == "human-decision" or not request.get("request_id"):
        return
    name = _request_time_name(request["request_id"])
    if ws.attempts._store_record(run_id, name) is None:
        ws.attempts._put(run_id, name, _admission.canonical_line({
            "schema_version": 1, "run_id": run_id, "issued_at": ws.clock(),
        }))


def _report_active_seconds(ws: Workspace, run_id: str, request_id: str) -> str | None:
    """Measure issued-to-reported time; requests from older runs have no timer."""
    record = ws.attempts._store_record(run_id, _request_time_name(request_id))
    if record is None:
        return None
    try:
        issued = datetime.fromisoformat(record["issued_at"].replace("Z", "+00:00"))
        reported = datetime.fromisoformat(ws.clock().replace("Z", "+00:00"))
        return str(max(0.0, (reported - issued).total_seconds()))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise Refusal("invalid-review-budget", "controller", "request clock is malformed") from exc


def report(ws: Workspace, result: object) -> dict[str, Any]:
    """The ``report`` verb: admit a result for the current request, or refuse it."""
    tdd = _supervisor("_supervisor_tdd.py")
    effects = _supervisor("_supervisor_effects.py")
    readiness = _supervisor("_supervisor_readiness.py")
    checked = _validate_result(result)
    accept_facts(checked)
    with ws.run_lock():
        ws.attempts.guard("report")
        recovery = _supervisor("_supervisor_recovery.py")
        _supervisor("_supervisor_concurrent.py").recover(ws)
        if recovery.reconcile(ws) is not None and checked["kind"] != "human-decision":
            raise recovery.unadopted(ws)
        state = derive(ws) if ws.divergence is None else _adoption_state(ws)
        if state.refusal is not None:
            raise state.refusal
        if checked["run_id"] != state.run_id:
            raise Refusal("not-current-run", "controller", "the result names another run")
        _lagging, foreign = ws.git.delivery_lag()
        if foreign:
            raise Refusal("foreign-delivery-edit", "controller", ", ".join(foreign))
        if checked["kind"] in _attempt.ATTEMPT_KINDS and checked["kind"] != "regenerate":
            ws.attempts.require_open_issuance(checked)
        seconds = _report_active_seconds(ws, state.run_id, checked["request_id"])
        ws.git.report_timing = (checked["request_id"], seconds) if seconds is not None else None
        if checked["kind"] in ("external-effect", "effect-query"):
            _refuse_protected_change(ws, state)
            outcome = effects.report_effect(ws, state, checked)
        elif checked["kind"] == "regenerate":
            ws.attempts.admit_regeneration(checked)
            outcome = "regenerate"
        elif checked["kind"] == "run-concurrent":
            outcome = _supervisor("_supervisor_concurrent.py").report_completion(
                ws, state, checked
            )
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
            kind = checked["kind"]
            recovery = _supervisor("_supervisor_recovery.py")
            confirming = recovery.is_confirmation(current)
            adopting = recovery.is_adoption(current)
            changed = _refuse_protected_change(ws, state, exempt=confirming or adopting)
            if kind in ("implement-task", "write-stub"):
                outcome = tdd.report_task(ws, state, current, checked, changed)
            elif confirming:
                outcome = recovery.report_confirmation(ws, state, current, checked, changed)
            elif recovery.is_adoption(current):
                outcome = recovery.report_adoption(ws, state, current, checked)
            elif current.get("reason") == "task-correction":
                if changed:
                    raise Refusal("unexpected-change", "controller",
                                  "correction needs a clean tree")
                outcome = _report_correction(ws, state, current, checked)
            elif kind == "human-decision":
                if changed:
                    raise Refusal(
                        "unexpected-change",
                        "controller",
                        "the attempt changed files: " + ", ".join(changed[:20]),
                    )
                outcome = _report_decision(ws, state, current, checked)
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
        _save_report_time(ws, state.run_id)
        if isinstance(outcome, dict) and "request" in outcome:
            _record_request_time(ws, state.run_id, outcome["request"])
        ws.attempts.close(checked)
        if checked["kind"] in ("implement-task", "run-concurrent"):
            # A floor result has landed: every held result now next in floor order follows it.
            _supervisor("_supervisor_integration.py").integrate_ready(ws)
        after = derive(ws)
        save_review_budget(ws, after)
        ws.local.reconcile_events(after.run_id, after.commits)
        return {"admitted": outcome}


def _report_decision(
    ws: Workspace, state: State, request: dict[str, Any], result: dict[str, Any]
) -> str:
    """Admit a ``human-decision`` result and commit it as one ``review`` step."""
    review = _supervisor("_supervisor_review.py")
    record = review.admit_decision(ws, state, request, result)
    appends = {review.DECISIONS_FILE: _admission.canonical_line(record)}
    trailers: dict[str, str] = {}
    if record["decision"] == "extend-review":
        budget = _supervisor("review-artifact.py").extend_review_budget(
            state.review_budget, phase="implementation", authority_ref=record["authority_ref"],
        )
        trailers = {
            "Supervisor-Review-Budget-Round": str(budget["extension"]["round"]),
            "Supervisor-Authority-Ref": record["authority_ref"],
        }
    if record["decision"] == "accept-risk":
        # The dispositions are built before the commit, so a finding that is not
        # open and supported refuses with nothing written.
        appends["evidence.jsonl"] = review.accept_risk_evidence(ws, state, record)
    ws.git.build_commit(
        run_id=state.run_id,
        step=f"decision:{request['request_id']}",
        operation="review",
        appends=appends,
        summary=f"record {record['decision']}",
        trailers=trailers,
        known_steps=state.steps,
    )
    return "review"


def status(ws: Workspace) -> dict[str, Any]:
    """Stage, readiness, projection, and retries; also reclaim orphan gate scratch."""
    _supervisor("_supervisor_execution.py").recover(ws)
    state = derive(ws)
    if state.refusal is None:
        # What the next verb's ref check would refuse, found without repairing anything.
        recovery = _supervisor("_supervisor_recovery.py")
        # What the next verb would answer: the attempt guard first, then the ref check.
        state.refusal = ws.attempts.standing_refusal() or recovery.inspect(ws)
        if state.refusal is None:
            ws.divergence = recovery.peek(ws)  # shown as the pending decision, nothing is issued
    if state.refusal is not None:
        return {
            "run": run_status(ws, state, None),
            "refusal": state.refusal.as_dict(),
            "terminal": False,
            "retry_count": _safe_count(ws, state),
        }
    readiness = _supervisor("_supervisor_readiness.py")
    pending = ws.attempts.regenerate_plan(state.run_id)  # a damaged record refuses, as it should
    if pending is not None and ws.divergence is None:
        # The next verb commits the install first and then asks for whatever follows; until
        # then nothing is terminal, no gate is open, and the run is gating.
        return {
            "run": {**run_status(ws, state, None), "stage": "gating", "active": True},
            "pending_step": {
                "operation": "regenerate",
                "paths": sorted(pending.entries)[:20],
                "path_count": len(pending.entries),
            },
            "terminal": False,
            "retry_count": state.retry_count,
            "retry_cap": int(ws.policy["implementation_retry_cap"]),
            "recovery_decisions": [],
            "recovery_leftovers": [],
            "tasks": [
                {
                    "task_id": t["task_id"],
                    "position": t["position"],
                    "title": t["title"],
                    "complete": state.is_complete(t),
                    "failed_attempts": state.failed_attempts(t),
                }
                for t in state.tasks
            ],
            "request": None,
            "refusal": {},
        }
    action = decide(ws, state)
    view: dict[str, Any] = {
        "run": run_status(ws, state, action),
        "terminal": action.kind == "terminal",
        "retry_count": state.retry_count,
        "retry_cap": int(ws.policy["implementation_retry_cap"]),
        "recovery_decisions": _supervisor("_supervisor_recovery.py").decisions(ws, state),
        "recovery_leftovers": _supervisor("_supervisor_recovery.py").leftovers(ws, state),
        "readiness": _status_readiness(ws, state, readiness),
        "tasks": [
            {
                "task_id": t["task_id"],
                "position": t["position"],
                "title": t["title"],
                "complete": state.is_complete(t),
                "failed_attempts": state.failed_attempts(t),
            }
            for t in state.tasks
        ],
        "request": action.request,
        "refusal": action.refusal.as_dict() if action.refusal else {},
    }
    concurrency = _supervisor("_supervisor_concurrent.py").status_view(ws, state, action)
    if concurrency is not None:
        view["concurrency"] = concurrency
    return view


def _status_readiness(ws: Workspace, state: State, readiness: ModuleType) -> dict[str, Any]:
    """The readiness view, or the refusal that stopped it (a rules or selection defect)."""
    try:
        return readiness.readiness(ws, state)  # type: ignore[no-any-return]
    except Refusal as exc:
        return {"ready": False, "refusal": exc.as_dict()}


def _safe_count(ws: Workspace, state: State) -> int:
    """The retry count even when the working spec is refused."""
    if not state.approvals:
        return 0
    state.run_id = state.approvals[0]["run_id"]
    state.receipts = _evidence_receipts(ws)
    return state.retry_count


def dump(record: dict[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True)
