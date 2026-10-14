"""External effects never repeat (T7).

VI-4050 (AC-0020), VI-4051 (AC-0033), and VI-4902 (AC-0019): every Effect
truth-table row, then the effect corpus — a later task's commit after a
receipt, a rebase after a push, a finish push, and a revision, renumbering,
retitle, replacement, split, and merge of the effect task before and after its
receipt.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")

pytestmark = sup.INTEGRATION

SPEC = h.SPEC_DIR


class Run:
    """A stepwise controller around one fixture repository."""

    def __init__(self, tmp_path: Path, plan: str = sup.PLAN) -> None:
        self.tmp = tmp_path
        self.repo = h.make_repo(tmp_path, plan=plan)
        assert h.start(self.repo)[0] == 0
        self.controller = h.Controller(self.repo, tmp_path / "effects.log")

    def next(self) -> dict[str, Any]:
        code, payload = h.run_cli(self.repo, "next", SPEC)
        assert code == 0, payload
        return payload

    def until(self, kind: str) -> dict[str, Any]:
        for _ in range(60):
            payload = self.next()
            if payload.get("terminal"):
                raise AssertionError(f"terminal before {kind}")
            request = payload["request"]
            if request["kind"] == kind:
                return request
            assert request["kind"] not in ("external-effect", "effect-query", "human-decision"), request
            code, admitted = self.controller.report(self.controller.work(request))
            assert code == 0, admitted
        raise AssertionError(kind)

    def effect_result(self, request: dict[str, Any], outcome: str) -> tuple[int, dict]:
        result = {"schema_version": 1, "request_id": request["request_id"],
                  "run_id": request["run_id"], "kind": request["kind"],
                  "effect": {"outcome": outcome}}
        if outcome in ("completed", "present"):
            result["effect"]["receipt_ref"] = "remote:abc"
        return self.controller.report(result)

    def resolve(self, decision: str, key: str) -> None:
        code, out = h.run_cli(self.repo, "resolve-effect", SPEC, "--operation", key,
                              "--decision", decision, "--authority-ref",
                              "effect-authority:0123456789ab")
        assert code == 0, out

    def lines(self, entry: str) -> list[dict[str, Any]]:
        return [r for r in h.workspace(self.repo).records("effect-resolutions.jsonl")
                if r["entry"] == entry]

    def head(self) -> str:
        return h.git(self.repo, "rev-parse", "HEAD")

    def finish(self) -> dict[str, Any]:
        return h.Controller(self.repo, self.tmp / "effects.log").drive()


def _query(run: Run) -> dict[str, Any]:
    payload = run.next()
    assert payload["request"]["kind"] == "effect-query", payload
    return payload["request"]


@pytest.fixture
def run(tmp_path: Path) -> Run:
    return Run(tmp_path)


def _dispatched(run: Run) -> dict[str, Any]:
    """Reach the first dispatch: the intent is recorded and the request handed out."""
    request = run.until("external-effect")
    assert request["effect"]["dispatch"] == 1
    assert len(run.lines("intent")) == 1
    return request


# ── the Effect truth table ───────────────────────────────────────────────────


def test_receipt_means_done_and_never_repeated(run: Run) -> None:
    request = _dispatched(run)
    assert run.effect_result(request, "completed")[1]["admitted"] == "effect-receipt"
    assert run.next()["request"]["kind"] == "run-gates"
    code, refused = run.effect_result(request, "completed")
    assert code == 1 and refused["refusal"]["code"] == "no-open-effect"
    assert run.finish().get("terminal") and len(run.lines("receipt")) == 1


def test_an_effect_result_with_a_changed_spec_directory_is_refused(run: Run) -> None:
    # AC-0031 covers every result kind: no effect line commits over a dirty spec.
    request = _dispatched(run)
    spec = run.repo / SPEC / "spec.md"
    spec.write_text(spec.read_text("utf-8") + "\nAn edit the attempt made.\n", "utf-8")
    head = run.head()
    code, refused = run.effect_result(request, "completed")
    assert code == 1 and refused["refusal"]["code"] == "protected-path-changed"
    assert run.head() == head and run.lines("receipt") == []


def test_no_record_records_the_intent_then_dispatches(run: Run) -> None:
    request = _dispatched(run)
    assert request["kind"] == "external-effect"
    assert request["effect"]["operation_key"] == run.lines("intent")[0]["operation_key"]


def test_running_dispatches_nothing(run: Run) -> None:
    _dispatched(run)
    query = _query(run)
    head = run.head()
    assert run.effect_result(query, "running")[1]["admitted"] == "running"
    assert run.head() == head
    assert _query(run)["request_id"] == query["request_id"]


def test_present_records_the_receipt(run: Run) -> None:
    _dispatched(run)
    assert run.effect_result(_query(run), "present")[1]["admitted"] == "effect-receipt"
    assert len(run.lines("receipt")) == 1


def test_absent_below_the_cap_dispatches_again(run: Run) -> None:
    _dispatched(run)
    code, admitted = run.effect_result(_query(run), "absent")
    assert admitted["admitted"]["request"]["effect"]["dispatch"] == 2
    assert [line["dispatch"] for line in run.lines("dispatch")] == [2]


def test_absent_at_the_cap_asks_a_human(run: Run) -> None:
    _dispatched(run)
    for expected in (2, 3):
        admitted = run.effect_result(_query(run), "absent")[1]["admitted"]
        assert admitted["request"]["effect"]["dispatch"] == expected
    head_before = run.head()
    assert run.effect_result(_query(run), "absent")[1]["admitted"] == "decision-required"
    assert run.lines("dispatch")[-1]["dispatch"] == 3
    assert run.head() != head_before  # the query outcome is kept as evidence
    payload = run.next()
    assert payload["request"]["kind"] == "human-decision"
    assert payload["request"]["reason"] == "effect-unresolved"
    assert payload["run"]["gate_pending"] is True


@pytest.mark.parametrize("outcome", ["absent", "unknowable"])
def test_retry_authorized_unclaimed_claims_one_retry(run: Run, outcome: str) -> None:
    request = _dispatched(run)
    run.resolve("retry-authorized", request["effect"]["operation_key"])
    admitted = run.effect_result(_query(run), outcome)[1]["admitted"]
    assert admitted["request"]["kind"] == "external-effect"
    assert len(run.lines("claim")) == 1


@pytest.mark.parametrize("outcome", ["absent", "unknowable"])
def test_retry_already_claimed_needs_a_new_decision(run: Run, outcome: str) -> None:
    request = _dispatched(run)
    run.resolve("retry-authorized", request["effect"]["operation_key"])
    run.effect_result(_query(run), outcome)
    assert run.effect_result(_query(run), outcome)[1]["admitted"] == "decision-required"
    assert len(run.lines("claim")) == 1
    assert run.next()["request"]["kind"] == "human-decision"


@pytest.mark.parametrize("outcome", ["absent", "unknowable"])
def test_do_not_retry_ends_the_operation(run: Run, outcome: str) -> None:
    request = _dispatched(run)
    key = request["effect"]["operation_key"]
    # Reach "Intent, no receipt" with this query outcome needing a decision.
    for _ in range(3 if outcome == "absent" else 1):
        admitted = run.effect_result(_query(run), outcome)[1]["admitted"]
    assert admitted == "decision-required"
    dispatches = len(run.lines("dispatch"))
    run.resolve("do-not-retry", key)
    assert run.next()["request"]["kind"] == "run-gates"
    assert run.finish().get("terminal")
    assert run.lines("receipt") == [] and len(run.lines("dispatch")) == dispatches


def test_absent_with_effect_confirmed_asks_a_human(run: Run) -> None:
    request = _dispatched(run)
    run.resolve("effect-confirmed", request["effect"]["operation_key"])
    assert run.effect_result(_query(run), "absent")[1]["admitted"] == "decision-required"
    assert run.next()["request"]["kind"] == "human-decision"


def test_unknowable_without_a_decision_asks_a_human(run: Run) -> None:
    _dispatched(run)
    assert run.effect_result(_query(run), "unknowable")[1]["admitted"] == "decision-required"
    payload = run.next()
    assert payload["request"]["kind"] == "human-decision"
    _forget = run.repo / SPEC / ".supervisor"
    for child in _forget.iterdir():
        if child.is_file():
            child.unlink()
    assert run.next()["request"]["request_id"] == payload["request"]["request_id"]


def test_unknowable_with_effect_confirmed_records_the_receipt(run: Run) -> None:
    request = _dispatched(run)
    run.resolve("effect-confirmed", request["effect"]["operation_key"])
    assert run.effect_result(_query(run), "unknowable")[1]["admitted"] == "effect-receipt"


def test_resolution_refuses_a_wrong_role_and_a_closed_operation(run: Run) -> None:
    request = _dispatched(run)
    key = request["effect"]["operation_key"]
    code, out = h.run_cli(run.repo, "resolve-effect", SPEC, "--operation", key, "--decision",
                          "do-not-retry", "--authority-ref", "owner:0123456789ab")
    assert code == 1 and out["refusal"]["code"] == "invalid-authority-ref"
    run.effect_result(request, "completed")
    code, out = h.run_cli(run.repo, "resolve-effect", SPEC, "--operation", key, "--decision",
                          "do-not-retry", "--authority-ref", "effect-authority")
    assert code == 1 and out["refusal"]["code"] == "no-open-effect"


# ── VI-4051: effect names are plan-unique ────────────────────────────────────


def test_duplicate_effect_names_are_refused_at_projection(tmp_path: Path) -> None:
    plan = sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](),
                    sup.TASKS["plain"](effects="push"))
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "duplicate-effect-name"


def test_finish_and_task_effects_share_one_namespace(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path, plan=sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](),
                                               header_effects="push"))
    assert h.start(repo)[0] == 0
    assert h.run_cli(repo, "next", SPEC)[1]["refusal"]["code"] == "duplicate-effect-name"


# ── VI-4902: the effect corpus executes each effect exactly once ─────────────


def _plan_with(push: str, *, number: str = "T2", extra: tuple[str, ...] = ()) -> str:
    return sup.plan(sup.TASKS["calc"](), push, sup.TASKS["plain"]("T3"), *extra)


REPLANS: dict[str, Callable[[], str]] = {
    "revision": lambda: _plan_with(sup.TASKS["push"](done="release.txt says ready now")),
    "renumber": lambda: sup.plan(sup.TASKS["calc"]("T4"), sup.TASKS["push"]("T9", depends="T4"),
                                 sup.TASKS["plain"]("T1")),
    "retitle": lambda: _plan_with(sup.task("T2", "Release ships", touches="`release.txt`",
                                           mode="goal-based", tests="no stub (goal-based)",
                                           effects="push")),
    "replacement": lambda: _plan_with(sup.task("T2", "Release note is published",
                                               touches="`notes.txt`", effects="push")),
    "split": lambda: _plan_with(sup.task("T2", "Release is prepared", touches="`release.txt`"),
                                extra=(sup.task("T4", "Release is pushed out",
                                                touches="`release.txt`", effects="push"),)),
    "merge": lambda: sup.plan(sup.TASKS["calc"](),
                              sup.task("T2", "Release and note ship",
                                       touches="`release.txt`, `plain.txt`", effects="push")),
}


class Worker(h.Controller):
    """Also answers the replan corpus's new task titles."""

    def work(self, request: dict[str, Any]) -> dict[str, Any]:
        if request["kind"] == "implement-task" and not request["task"]["title"].startswith(
                ("Calculator", "Release is pushed", "Plain")):
            (self.repo / "release.txt").write_text("ready\n", "utf-8")
            (self.repo / "notes.txt").write_text(request["task"]["title"] + "\n", "utf-8")
            return {"schema_version": 1, "request_id": request["request_id"],
                    "run_id": request["run_id"], "kind": request["kind"],
                    "gate": {"passed": True}}
        return super().work(request)


def _exactly_once(run: Run) -> None:
    end = Worker(run.repo, run.tmp / "effects.log").drive()
    assert end.get("terminal"), end
    log = (run.tmp / "effects.log").read_text("utf-8").split()
    assert len(log) == len(set(log)), log
    assert sum(1 for key in log if key.endswith(":push")) == 1


@pytest.mark.parametrize("when", ["before-receipt", "after-receipt"])
@pytest.mark.parametrize("name", sorted(REPLANS))
def test_replanning_the_effect_task_never_repeats_it(tmp_path: Path, name: str,
                                                     when: str) -> None:
    run = Run(tmp_path)
    request = _dispatched(run)
    run.controller.dispatch(request)
    if when == "after-receipt":
        run.effect_result(request, "completed")
    (run.repo / SPEC / "plan.md").write_text(REPLANS[name](), "utf-8")
    if when == "before-receipt":
        # AC-0031: no receipt commits over the uncommitted replan. The next step
        # commits the replan, and the effect query then finds the push done.
        code, refused = run.effect_result(request, "completed")
        assert code == 1 and refused["refusal"]["code"] == "protected-path-changed"
    _exactly_once(run)
    assert len(run.lines("receipt")) == 1


def test_a_later_task_commit_after_the_receipt_does_not_reopen_it(tmp_path: Path) -> None:
    run = Run(tmp_path)
    request = _dispatched(run)
    run.controller.dispatch(request)
    run.effect_result(request, "completed")
    later = sup.task("T4", "Changelog is written", touches="`notes.txt`")
    (run.repo / SPEC / "plan.md").write_text(_plan_with(sup.TASKS["push"](), extra=(later,)),
                                             "utf-8")
    _exactly_once(run)
    assert "notes.txt" in h.git(run.repo, "ls-files")


def test_a_rebase_after_the_push_does_not_reopen_it(tmp_path: Path) -> None:
    run = Run(tmp_path)
    request = _dispatched(run)
    run.controller.dispatch(request)
    run.effect_result(request, "completed")
    root = h.git(run.repo, "rev-list", "--max-parents=0", "HEAD").strip()
    h.git(run.repo, "checkout", "-q", "-b", "upstream", root)
    (run.repo / "OTHER.md").write_text("upstream\n", "utf-8")
    h.git(run.repo, "add", "OTHER.md")
    h.git(run.repo, "commit", "-q", "-m", "upstream")
    h.git(run.repo, "checkout", "-q", "main")
    h.git(run.repo, "rebase", "-q", "upstream")
    _exactly_once(run)


def test_a_finish_push_runs_once_and_survives_a_rewrite(tmp_path: Path) -> None:
    plan = sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](), sup.TASKS["plain"](),
                    header_effects="ship")
    run = Run(tmp_path, plan=plan)
    end = run.finish()
    assert end.get("terminal")
    first = run.lines("intent")
    finish = [line for line in first if line["scope"] == "finish"]
    assert len(finish) == 1 and finish[0]["terminal_head"]
    # A rebase that rewrites every commit but keeps the tree keeps the same push,
    # even once the old HEAD the intent recorded is pruned away.
    root = h.git(run.repo, "rev-list", "--max-parents=0", "HEAD").strip()
    h.git(run.repo, "rebase", "-q", "--force-rebase", root)
    h.git(run.repo, "reflog", "expire", "--expire=now", "--all")
    h.git(run.repo, "gc", "-q", "--prune=now")
    assert run.finish().get("terminal")
    log = (run.tmp / "effects.log").read_text("utf-8").split()
    assert sorted(key.rsplit(":", 2)[-2] if key.count(":") > 1 else key.split(":")[-1]
                  for key in log) == ["push", "ship"]


# ── VI-4050: two processes race to claim one authorized retry ────────────────


def test_two_processes_claim_one_retry_and_dispatch_at_most_once(tmp_path: Path) -> None:
    run = Run(tmp_path)
    request = _dispatched(run)
    key = request["effect"]["operation_key"]
    run.resolve("retry-authorized", key)
    query = _query(run)
    results = []
    for index in range(2):
        path = tmp_path / f"race-{index}.json"
        path.write_text(json.dumps({"schema_version": 1, "request_id": query["request_id"],
                                    "run_id": query["run_id"], "kind": "effect-query",
                                    "effect": {"outcome": "absent"}}), "utf-8")
        results.append(path)
    script = str(sup.SCRIPTS / "work-supervisor.py")
    env = {**os.environ, **h.GIT_ENV}
    procs = [subprocess.Popen([sys.executable, script, "report", SPEC, str(path)],
                              cwd=run.repo, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) for path in results]
    outs = [p.communicate(timeout=300) for p in procs]
    payloads = [json.loads(out) for out, _err in outs]
    dispatches = [p for p in payloads
                  if isinstance(p.get("admitted"), dict) and "request" in p["admitted"]]
    assert len(run.lines("claim")) == 1
    assert len(dispatches) <= 1
    assert len(dispatches) == 1, payloads
