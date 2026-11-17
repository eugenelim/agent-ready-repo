"""The step loop derives, commits, and recovers (T4).

VI-4030 (AC-0008), VI-4031 (AC-0010, AC-0011), VI-4034 (AC-0026),
VI-4035 (AC-0030, AC-0031), VI-4036 (AC-0032).
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


def _next(repo: Path) -> tuple[int, dict[str, Any]]:
    return h.run_cli(repo, "next", SPEC)


def _step(repo: Path, controller: h.Controller) -> dict[str, Any]:
    """Issue the current request, do the work, and report it."""
    code, payload = _next(repo)
    assert code == 0, payload
    request = payload["request"]
    code, admitted = controller.report(controller.work(request))
    assert code == 0, admitted
    return request


def _through_calculator(tmp_path: Path, plan: str = sup.PLAN) -> tuple[Path, h.Controller]:
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    assert _step(repo, controller)["kind"] == "write-stub"
    assert _step(repo, controller)["task"]["title"] == "Calculator answers"
    return repo, controller


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text("utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), "utf-8")


def test_review_budget_enters_run_store_and_status(tmp_path: Path, capsys: Any) -> None:
    """Admission carries the pre-admission identity and all counters into status."""
    repo = h.make_repo(tmp_path)
    artifact = h.cli._supervisor("review-artifact.py")
    review_run = "55555555-5555-4555-8555-555555555555"
    assert artifact.main(["record", "--root", str(repo), "--run-id", review_run,
                          "--fingerprint", "a" * 64]) == 0
    capsys.readouterr()
    expected = artifact.load_review_budget(repo, review_run)
    code, started = h.run_cli(
        repo, "start", SPEC, "--intent", "code", "--code-trust", "trusted",
        "--authority-ref", "owner", "--review-authority-ref", "plan-reviewer",
        "--review-run-id", review_run, *h.digest_args(repo),
    )
    assert code == 0, started
    ws = h.workspace(repo)
    saved = json.loads((ws.git._store_dir(started["run_id"]) / "review-budget.json").read_text())
    assert saved == expected
    code, status = h.run_cli(repo, "status", SPEC, "--json")
    assert code == 0, status
    assert status["run"]["review_budget"] == expected
    assert status["readiness"]["review_budget"] == expected
    assert h.start(repo)[0] == 0
    assert h.run_cli(repo, "status", SPEC, "--json")[1]["run"]["review_budget"] == expected
    assert artifact.main(["record", "--root", str(repo), "--run-id", review_run,
                          "--phase", "implementation", "--subject", "product-1",
                          "--fingerprint", "b" * 64]) == 0
    capsys.readouterr()
    expected = artifact.load_review_budget(repo, review_run)
    assert _next(repo)[0] == 0
    assert json.loads((ws.git._store_dir(started["run_id"]) / "review-budget.json").read_text()) == expected
    assert h.run_cli(repo, "status", SPEC, "--json")[1]["run"]["review_budget"] == expected


@pytest.mark.parametrize("mutation", [
    "version", "missing", "extra", "invalid-json", "symlink", "absent",
])
def test_review_budget_store_refuses_malformed_records(tmp_path: Path, mutation: str) -> None:
    """A broken stored budget cannot silently become a fresh zero-count budget."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    ws = h.workspace(repo)
    path = ws.git._store_dir(h.loop.derive(ws).run_id) / "review-budget.json"
    budget = json.loads(path.read_text())
    if mutation == "version":
        budget["schema_version"] = 2
    elif mutation == "missing":
        del budget["rounds"]
    elif mutation == "extra":
        budget["unknown"] = 1
    if mutation in ("symlink", "absent"):
        path.unlink()
        if mutation == "symlink":
            path.symlink_to(repo / "README.md")
    else:
        path.write_text("{" if mutation == "invalid-json" else json.dumps(budget))
    before = h.git(repo, "for-each-ref")
    code, payload = h.run_cli(repo, "status", SPEC, "--json")
    assert code == 1 and payload["refusal"]["code"] == "invalid-review-budget", payload
    assert h.git(repo, "for-each-ref") == before


def test_review_budget_counts_survive_protected_replan_before_checkpoint(
    tmp_path: Path, capsys: Any,
) -> None:
    """A protected edit cannot hide review rounds observed by read-only status."""
    repo = h.make_repo(tmp_path)
    artifact = h.cli._supervisor("review-artifact.py")
    review_run = "66666666-6666-4666-8666-666666666666"
    assert artifact.main(["record", "--root", str(repo), "--run-id", review_run,
                          "--fingerprint", "a" * 64]) == 0
    capsys.readouterr()
    assert h.run_cli(
        repo, "start", SPEC, "--intent", "code", "--code-trust", "trusted",
        "--authority-ref", "owner", "--review-authority-ref", "plan-reviewer",
        "--review-run-id", review_run, *h.digest_args(repo),
    )[0] == 0
    assert artifact.main(["record", "--root", str(repo), "--run-id", review_run,
                          "--phase", "implementation", "--subject", "product-1",
                          "--fingerprint", "b" * 64]) == 0
    capsys.readouterr()
    before = h.run_cli(repo, "status", SPEC)[1]["run"]["review_budget"]
    assert before["rounds"] == {"spec-stage": 1, "implementation": 1}
    _edit(repo / SPEC / "spec.md", "answers 42.", "answers 42 every time.")
    status = h.run_cli(repo, "status", SPEC)[1]
    assert status["refusal"]
    assert status["run"]["review_budget"] == before
    h.git(repo, "commit", "-qam", "controller amendment")
    _adopt(repo, tmp_path)
    assert h.run_cli(repo, "status", SPEC)[1]["run"]["review_budget"] == before


@pytest.mark.parametrize("change", ["replan", "adopt-history", "protected-adoption"])
def test_review_budget_survives_state_rebuild(tmp_path: Path, change: str) -> None:
    """Rebuilt state keeps nonzero counts even when the spec projection refuses."""
    repo, _controller = _through_calculator(tmp_path)
    ws = h.workspace(repo)
    budget = h.cli._supervisor("review-artifact.py").new_review_budget("review-before-admission")
    budget.update(rounds={"spec-stage": 2, "implementation": 1},
                  repairs={"rule-1": 1}, active_hours=0.25, retries=2,
                  finding_records=2, failed_task_gates=1, code_review_rounds={"unit-1": 1})
    path = ws.git._store_dir(h.loop.derive(ws).run_id) / "review-budget.json"
    path.write_text(json.dumps(budget))
    before = h.run_cli(repo, "status", SPEC, "--json")[1]["run"]["review_budget"]
    if change == "replan":
        _edit(repo / SPEC / "plan.md", "Build it.", "Build it carefully.")
        assert _next(repo)[0] == 0
    else:
        if change == "protected-adoption":
            _edit(repo / SPEC / "spec.md", "answers 42.", "answers 42 every time.")
        else:
            (repo / "README.md").write_text("Adopted notes.\n")
        h.git(repo, "commit", "-qam", "controller update")
        _adopt(repo, tmp_path)
    after = h.run_cli(repo, "status", SPEC, "--json")[1]["run"]["review_budget"]
    assert after == before == budget
    assert json.loads(path.read_text()) == budget


def _snapshot(repo: Path) -> tuple[str, ...]:
    local = repo / SPEC / ".supervisor" / "journal.jsonl"
    events = repo / ".loop-run" / "events.jsonl"
    return (
        h.git(repo, "rev-parse", "HEAD"),
        h.git(repo, "for-each-ref"),
        h.git(repo, "status", "--porcelain"),
        h.git(repo, "diff"),
        local.read_text("utf-8") if local.exists() else "",
        events.read_text("utf-8") if events.exists() else "",
    )


# ── VI-4030: refusal rows write nothing but run.json ─────────────────────────

ADR = "docs/adr/0001-calculators-answer.md"
REFUSALS: dict[str, tuple[str, str, str, str, str]] = {
    # name: (file, old, new, code, owner)
    "criteria": (f"{SPEC}/spec.md", "answers 42.", "answers 43.",
                 "criteria-changed", "spec-amendment owner"),
    "scope": (f"{SPEC}/spec.md", "no user interface.", "a small interface.",
              "scope-changed", "spec-amendment owner"),
    "decision": (ADR, "The calculator answers 42.", "The calculator answers 43.",
                 "authority-changed", "decision owner"),
    "contract": (f"{SPEC}/spec.md", "`contracts/calc/`", "`contracts/calc/v2/`",
                 "contract-changed", "contract owner"),
    "durable-outputs": (f"{SPEC}/spec.md", "| changelog |", "| release notes |",
                        "durable-outputs-changed", "spec-amendment owner"),
    "accepted-risk": (f"{SPEC}/spec.md", "## Accepted Risk\n\nnone", "## Accepted Risk\n\nDrift.",
                      "accepted-risk-changed", "risk owner"),
    "terminal-intent": (f"{SPEC}/spec.md", "`code` — build", "`spec-plan` — build",
                        "terminal-intent-changed", "plan-review authority"),
    "ambiguous": (f"{SPEC}/spec.md", "## Assumptions", "## Scope and Non-goals\n\nx\n\n## Assumptions",
                  "ambiguous-reference", "Scope and Non-goals"),
    "unreadable": (f"{SPEC}/spec.md", "- **Constrained by:** ADR-0001",
                   "- **Constrained by:** ADR-0001, ADR-0042",
                   "unreadable-reference", "ADR-0042"),
}


def _adopt(repo: Path, tmp_path: Path) -> None:
    """Answer the history-adoption decision that a controller's commit on the run raises."""
    code, asked = _next(repo)
    request = asked["request"]
    assert code == 0 and request["reason"] == "history-adoption"
    result = tmp_path / "adopt.json"
    result.write_text(json.dumps({
        "schema_version": 1, "request_id": request["request_id"], "run_id": request["run_id"],
        "kind": "human-decision",
        "decision": {"decision": "adopt-history", "authority_ref": "owner:0123456789ab",
                     "commit": request["head_commit"]},
    }), "utf-8")
    assert h.run_cli(repo, "report", SPEC, str(result))[0] == 0


@pytest.mark.parametrize("committed", [False, True], ids=["uncommitted", "committed"])
@pytest.mark.parametrize("name", sorted(REFUSALS))
def test_refusal_row_writes_nothing(tmp_path: Path, name: str, committed: bool) -> None:
    repo, _controller = _through_calculator(tmp_path)
    rel, old, new, code_expected, owner = REFUSALS[name]
    _edit(repo / rel, old, new)
    if committed:
        h.git(repo, "commit", "-qam", f"protected edit: {name}")
        _adopt(repo, tmp_path)
    before = _snapshot(repo)
    code, payload = _next(repo)
    assert code == 1
    assert payload["refusal"]["code"] == code_expected
    assert payload["refusal"]["owner"] == owner
    assert _snapshot(repo) == before
    run = json.loads((repo / SPEC / ".supervisor" / "run.json").read_text("utf-8"))
    assert run["refusal"]["code"] == code_expected and run["refusal"]["owner"] == owner
    assert run["stage"] == "awaiting-human"


def test_bookkeeping_edit_is_committed_as_a_replan_without_approval(tmp_path: Path) -> None:
    repo, _controller = _through_calculator(tmp_path)
    _edit(repo / SPEC / "spec.md", "- [ ] **AC-0001.**", "- [x] **AC-0001.**")
    code, payload = _next(repo)
    assert code == 0 and payload["request"]["kind"] == "implement-task"
    subjects = h.git(repo, "log", "--format=%s", "-1")
    assert "replan" in subjects
    approvals = h.workspace(repo).approvals()
    assert len(approvals) == 1


# ── VI-4031: completed tasks re-run only when their own content changes ──────


def _requested_title(repo: Path) -> str:
    code, payload = _next(repo)
    assert code == 0, payload
    return payload["request"]["task"]["title"]


@pytest.mark.parametrize("plan_factory", [
    lambda: sup.plan(sup.TASKS["plain"]("T1"), sup.TASKS["calc"]("T2"),
                     sup.TASKS["push"]("T3", depends="T2")),
    lambda: sup.plan(sup.TASKS["calc"]("T5"), sup.TASKS["push"]("T6", depends="T7"),
                     sup.TASKS["plain"]("T7")),
], ids=["renumber-and-reorder", "rewrite-depends-on"])
def test_renumbering_never_re_requests_a_completed_task(
        tmp_path: Path, plan_factory: Callable[[], str]) -> None:
    repo, _controller = _through_calculator(tmp_path)
    (repo / SPEC / "plan.md").write_text(plan_factory(), "utf-8")
    assert _requested_title(repo) == "Plain note is written"


def _calc_commits(repo: Path) -> list[str]:
    return [line for line in h.git(repo, "log", "--format=%H %s").splitlines()
            if "T1 Calculator" in line]


def test_content_edit_re_requests_the_task_and_keeps_history(tmp_path: Path) -> None:
    repo, _controller = _through_calculator(tmp_path)
    old = _calc_commits(repo)
    revised = sup.plan(sup.TASKS["calc"](done="the calculator test passes twice"),
                       sup.TASKS["push"](), sup.TASKS["plain"]())
    (repo / SPEC / "plan.md").write_text(revised, "utf-8")
    code, payload = _next(repo)
    assert code == 0 and payload["request"]["kind"] == "implement-task"
    assert payload["request"]["task"]["title"] == "Calculator answers"
    assert old and set(old) <= set(_calc_commits(repo))


FIRST_ROW_REPLANS: dict[str, Callable[[], str]] = {
    "local-method": lambda: sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](approach="by hand"),
                                     sup.TASKS["plain"](approach="from a template")),
    "delete": lambda: sup.plan(sup.TASKS["calc"](), sup.TASKS["push"]()),
    "replace": lambda: sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](),
                                sup.task("T3", "Something else entirely", mode="goal-based",
                                         tests="no stub (goal-based)")),
    "change-tests": lambda: sup.plan(
        sup.TASKS["calc"](), sup.TASKS["push"](),
        sup.task("T3", "Plain note is written", touches="`plain.txt`", mode="goal-based",
                 tests="no stub (checked by reading the file)", done="plain.txt says done")),
    "change-stubs": lambda: sup.plan(
        sup.task("T1", "Calculator answers",
                 tests="- **VI-1:** x\n\n" + sup.stub_fence(
                     body=sup.STUB + "assert calc.answer() > 41\n", indent="  ")),
        sup.TASKS["push"](), sup.TASKS["plain"]()),
    "change-effects": lambda: sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](effects="publish"),
                                       sup.TASKS["plain"]()),
}


@pytest.mark.parametrize("name", sorted(FIRST_ROW_REPLANS))
def test_first_row_replan_mid_run_needs_no_approval(tmp_path: Path, name: str) -> None:
    repo, _controller = _through_calculator(tmp_path)
    (repo / SPEC / "plan.md").write_text(FIRST_ROW_REPLANS[name](), "utf-8")
    code, payload = _next(repo)
    assert code == 0, payload
    assert payload["request"]["kind"] in ("implement-task", "write-stub")
    assert len(h.workspace(repo).approvals()) == 1
    assert "replan" in h.git(repo, "log", "-1", "--format=%s")


@pytest.mark.parametrize("tasks", [
    lambda: [sup.task("T1", "Calculator adds", touches="`calc.py`"),
             sup.task("T2", "Calculator answers forty-two", touches="`calc.py`")],
    lambda: [sup.task("T1", "Calculator and release ship", touches="`calc.py`, `release.txt`")],
], ids=["split", "merge"])
def test_split_or_merge_re_requests_the_work(tmp_path: Path,
                                            tasks: Callable[[], list[str]]) -> None:
    repo, _controller = _through_calculator(tmp_path)
    old = _calc_commits(repo)
    (repo / SPEC / "plan.md").write_text(sup.plan(*tasks()), "utf-8")
    title = _requested_title(repo)
    assert title.startswith("Calculator") and title != "Calculator answers"
    assert old and set(old) <= set(_calc_commits(repo))


# ── VI-4034: run.json fields and the open human decision ─────────────────────


def test_run_json_tracks_an_open_human_decision(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    run = json.loads((repo / SPEC / ".supervisor" / "run.json").read_text("utf-8"))
    assert run["stage"] == "admitted" and run["active"] is True and run["gate_pending"] is False

    class Failing(h.Controller):
        def work(self, request: dict[str, Any]) -> dict[str, Any]:
            result = super().work(request)
            if request["kind"] == "implement-task":
                result["gate"] = {"passed": False}
            return result

    end = Failing(repo, tmp_path / "effects.log").drive()
    assert end["request"]["kind"] == "human-decision"
    run = json.loads((repo / SPEC / ".supervisor" / "run.json").read_text("utf-8"))
    assert run["stage"] == "awaiting-human"
    assert run["gate_pending"] is True and run["gate_question"] == end["request"]["question"]
    assert run["refusal"] == {}


# ── VI-4035: amendment keeps the run; worker edits to trusted files refuse ───


def test_amendment_and_second_start_keep_run_facts(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    code, first = h.start(repo)
    end = h.Controller(repo, tmp_path / "effects.log").drive()
    assert end.get("terminal")
    _, before = h.run_cli(repo, "status", SPEC, "--json")
    receipts = [r for r in h.workspace(repo).records("effect-resolutions.jsonl")
                if r["entry"] == "receipt"]
    _edit(repo / SPEC / "spec.md", "answers 42.", "answers 42 every time.")
    code, refused = _next(repo)
    assert code == 1 and refused["refusal"]["code"] == "criteria-changed"
    h.git(repo, "commit", "-qam", "amend AC-0001")
    _adopt(repo, tmp_path)  # the controller's commit is history the run did not make
    code, second = h.start(repo)
    assert code == 0 and second["run_id"] == first["run_id"] and second["sequence"] == 2
    _, after = h.run_cli(repo, "status", SPEC, "--json")
    assert after["run"]["run_id"] == before["run"]["run_id"]
    assert [t["complete"] for t in after["tasks"]] == [True, True, True]
    assert after["retry_count"] == before["retry_count"] == 1
    assert [r for r in h.workspace(repo).records("effect-resolutions.jsonl")
            if r["entry"] == "receipt"] == receipts


# The attempt check refuses a worker edit to a trusted file first, so core's own
# protected-path refusal stays as the second line of defence.
@pytest.mark.parametrize(("rel", "old", "new"), [
    (ADR, "Callers need an answer.", "Callers need a better answer."),
    (ADR, "The calculator answers 42.", "The calculator answers 7."),
    (f"{SPEC}/spec.md", "calculator that answers.", "calculator that sings."),
    (f"{SPEC}/plan.md", "Build it.", "Build it fast."),
])
def test_worker_edit_to_a_trusted_file_is_refused_before_any_commit(
        tmp_path: Path, rel: str, old: str, new: str) -> None:
    repo, controller = _through_calculator(tmp_path)
    _, payload = _next(repo)
    request = payload["request"]
    result = controller.work(request)
    _edit(repo / rel, old, new)
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "attempt-refused"
    assert h.git(repo, "rev-parse", "HEAD") == head


def test_result_for_another_request_is_refused(tmp_path: Path) -> None:
    repo, controller = _through_calculator(tmp_path)
    _, payload = _next(repo)
    result = controller.work(payload["request"])
    result["request_id"] = result["request_id"].rsplit(":", 1)[0] + ":9"
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "not-current-attempt"
    assert h.git(repo, "rev-parse", "HEAD") == head


# ── VI-4036: the index matches HEAD after every commit and sync ──────────────


def test_index_is_clean_after_every_commit_and_sync(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    staged: list[str] = []

    def hook(name: str) -> None:
        if name == "synced":
            staged.extend(h.git(repo, "diff", "--cached", "--name-only").split())

    h.commit_module.set_kill_hook(hook)
    try:
        h.start(repo)
        assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")
    finally:
        h.commit_module.set_kill_hook(None)
    assert staged == []
    assert h.git(repo, "diff", "--cached", "--name-only") == ""


# ── scheduling in dependency order ────────────────────────────────────────────


def _goal(number: str, title: str, depends: str) -> str:
    return sup.task(number, title, depends=depends, mode="goal-based", tests="no stub (goal-based)")


def test_tasks_are_issued_in_dependency_order_not_plan_order(tmp_path: Path) -> None:
    plan = sup.plan(_goal("T1", "Third in order", "T2"), _goal("T2", "Second in order", "T3"),
                    _goal("T3", "First in order", "none"))
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    titles: list[str] = []
    for _ in range(12):  # a plain task retries once before its gate passes
        request = _step(repo, controller)
        if request["kind"] == "implement-task" and request["task"]["title"] not in titles:
            titles.append(request["task"]["title"])
        if len(titles) == 3:
            break
    assert titles == ["First in order", "Second in order", "Third in order"]


def test_a_dependency_cycle_is_refused_and_commits_nothing(tmp_path: Path) -> None:
    plan = sup.plan(_goal("T1", "First", "T2"), _goal("T2", "Second", "T1"))
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    head = h.git(repo, "rev-parse", "HEAD")
    code, payload = _next(repo)
    assert code == 1 and payload["refusal"]["code"] == "dependency-cycle", payload
    assert payload["refusal"]["owner"] == "plan author"
    assert h.git(repo, "rev-parse", "HEAD") == head


def _correction(repo: Path) -> dict[str, Any]:
    """Open an owner decision for the admitted calculator task."""
    task = h.loop.derive(h.workspace(repo)).tasks[0]
    cli = Path(__file__).resolve().parents[3] / ".apm/skills/work-loop/scripts/work-supervisor.py"
    completed = subprocess.run(
        [sys.executable, str(cli), "correct-task", SPEC, "--task", task["task_id"],
         "--reason", "The admitted implementation needs correction."],
        cwd=repo, env={**os.environ, **h.GIT_ENV}, capture_output=True, text=True, check=False,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0, payload
    return payload["request"]


def _confirm_correction(controller: h.Controller, request: dict[str, Any],
                        authority: str | None) -> tuple[int, dict[str, Any]]:
    """Answer through the same human-decision report port as history adoption."""
    return controller.report({
        "schema_version": 1, "run_id": request["run_id"],
        "request_id": request["request_id"], "kind": "human-decision",
        "decision": {"decision": "correct-task",
                     **({"authority_ref": authority} if authority is not None else {}),
                     "commit": request["target_commit"]},
    })


@pytest.mark.parametrize("authority", [None, "", "controller:0123456789ab"])
def test_correction_waits_for_owner_without_appending(
        tmp_path: Path, authority: str | None) -> None:
    """An unconfirmed correction remains the current request and changes no ledger."""
    repo, controller = _through_calculator(tmp_path)
    request = _correction(repo)
    before = _snapshot(repo)
    code, payload = _confirm_correction(controller, request, authority)
    assert code == 1 and payload["refusal"]["code"] == "correction-refused", payload
    assert _snapshot(repo) == before
    assert _next(repo)[1]["request"] == request
    assert h.workspace(repo).records("task-corrections.jsonl") == []


def test_owner_correction_reopens_task_and_invalidates_dependent_evidence(tmp_path: Path) -> None:
    """Even an unchanged repair must rerun dependent tasks, gates and reviews."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    assert controller.drive().get("terminal")
    ws = h.workspace(repo)
    before = h.loop.derive(ws)
    evidence = ws.evidence_bytes()
    readiness = h.cli._supervisor("_supervisor_readiness.py")
    old_subject = readiness.delivery_subject(ws, before)
    old_reports = ws.open_evidence().get_semantic_records("review-report.v1")
    old_commits = h.git(repo, "rev-list", "HEAD").splitlines()
    request = _correction(repo)
    code, payload = _confirm_correction(controller, request, "owner:0123456789ab")
    assert code == 0, payload
    ws = h.workspace(repo)
    records = ws.records("task-corrections.jsonl")
    assert len(records) == 1
    record = records[0]
    assert record["type"] == "task-correction.v1" and record["schema_version"] == 1
    assert record["target_commit"] == before.completed[(before.tasks[0]["task_id"],
                                                        before.tasks[0]["revision"])]
    after = h.loop.derive(ws)
    assert [after.is_complete(t) for t in after.tasks] == [False, False, True]
    assert ws.evidence_bytes().startswith(evidence)
    assert set(old_commits) <= set(h.git(repo, "rev-list", "HEAD").splitlines())
    store = ws.open_evidence()
    assert store.get_semantic_records("review-report.v1") == old_reports
    assert record["affected_receipt_ids"]
    for criterion in {r["lineage"]["criterion_ref"] for r in before.receipts
                      if r["receipt_id"] in record["affected_receipt_ids"]}:
        assert not store.get_active_receipts(criterion)
    assert readiness.delivery_subject(ws, after)["acceptance_fingerprint"] != old_subject[
        "acceptance_fingerprint"]
    assert not readiness.readiness(ws, after)["ready"]
    code, issued = _next(repo)
    assert code == 0 and issued["request"]["kind"] == "implement-task", issued
    assert issued["request"]["task"] == request["task"]
    assert controller.report(controller.work(issued["request"]))[0] == 0
    code, issued = _next(repo)
    assert code == 0 and issued["request"]["task"]["title"] == "Release is pushed"
    assert controller.report(controller.work(issued["request"]))[0] == 0
    code, issued = _next(repo)
    assert code == 0 and issued["request"]["kind"] == "run-gates", issued
    # Identical product bytes still need fresh gate proof and a new reviewer selection.
    assert controller.report(controller.work(issued["request"]))[0] == 0
    code, issued = _next(repo)
    assert code == 0 and issued["request"]["kind"] == "review-role", issued
    assert "candidates" in issued["request"]
    assert controller.report(controller.work(issued["request"]))[0] == 0
    fresh = readiness.readiness(h.workspace(repo), h.loop.derive(h.workspace(repo)))
    assert not fresh["ready"]
    assert fresh["flow"]["tier"] == "full"


@pytest.mark.parametrize("mutation", ["version", "missing", "extra", "epoch", "ids"])
def test_correction_record_schema_is_closed(mutation: str) -> None:
    """Unknown versions and malformed correction records cannot be read as authority."""
    record = {
        "schema_version": 1, "type": "task-correction.v1", "correction_id": "correction-1",
        "run_id": "run-1", "task_id": "task-1", "task_revision": "a" * 64,
        "target_commit": "b" * 40, "affected_receipt_ids": ["receipt-1"],
        "reason": "The task was falsely admitted.", "authority_ref": "owner:0123456789ab",
        "invalidation_epoch": 1,
    }
    validator = h.loop.sibling("_evidence_store.py").validate_task_correction
    assert validator(record) == (True, "ok")
    if mutation == "version":
        record["schema_version"] = 2
    elif mutation == "missing":
        del record["target_commit"]
    elif mutation == "extra":
        record["worker_override"] = True
    elif mutation == "epoch":
        record["invalidation_epoch"] = True
    else:
        record["affected_receipt_ids"] = ["receipt-1", "receipt-1"]
    assert not validator(record)[0]


def test_review_budget_measures_request_time_with_supervisor_clock(tmp_path: Path) -> None:
    """A real issuance/report survives reload as measured hours, without worker input."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    now = ["2026-01-01T00:00:00Z"]

    def workspace() -> Any:
        """Use fresh Git caches with the same controllable supervisor clock."""
        return h.admission.Workspace(repo, SPEC, clock=lambda: now[0])

    with h.git_identity():
        request = h.loop.next_request(workspace())["request"]
        assert request["kind"] == "write-stub"
        now[0] = "2026-01-01T01:00:00Z"
        assert h.loop.next_request(workspace())["request"] == request
        result = h.Controller(repo, tmp_path / "effects").work(request)
        now[0] = "2026-01-01T01:30:00Z"
        assert h.loop.report(workspace(), result)["admitted"] == "stub"
    ws = workspace()
    state = h.loop.derive(ws)
    saved = json.loads((ws.git._store_dir(state.run_id) / "review-budget.json").read_text())
    assert saved["active_hours"] == state.review_budget["active_hours"] == 1.5
    assert "Supervisor-Active-Seconds: 5400.0" in h.git(repo, "log", "-1")
    # A repeated read and another request cannot count this report twice.
    assert h.loop.derive(workspace()).review_budget["active_hours"] == 1.5


def test_review_budget_measures_report_without_commit(tmp_path: Path) -> None:
    """An accepted no-op effect report still checkpoints its measured active time."""
    repo, controller = _through_calculator(
        tmp_path, plan=sup.plan(sup.TASKS["calc"](), sup.TASKS["push"]()),
    )
    assert _step(repo, controller)["kind"] == "implement-task"
    now = ["2026-01-01T00:00:00Z"]

    def workspace() -> Any:
        """Use a fresh workspace for each invocation of the fake supervisor clock."""
        return h.admission.Workspace(repo, SPEC, clock=lambda: now[0])

    with h.git_identity():
        request = h.loop.next_request(workspace())["request"]
        assert request["kind"] == "external-effect"
        before = h.git(repo, "rev-parse", "HEAD")
        now[0] = "2026-01-01T01:30:00Z"
        result = {
            "schema_version": 1, "run_id": request["run_id"],
            "request_id": request["request_id"], "kind": "external-effect",
            "effect": {"outcome": "not-executed"},
        }
        assert h.loop.report(workspace(), result)["admitted"] == "not-executed"
        assert h.git(repo, "rev-parse", "HEAD") == before
    assert h.loop.derive(workspace()).review_budget["active_hours"] == 1.5
    store = workspace().git._store_dir(request["run_id"])
    assert json.loads((store / "review-budget.json").read_text())["active_hours"] == 1.5


@pytest.mark.parametrize("occupied", [False, True])
def test_terminal_correction_reacquires_checkout(tmp_path: Path, occupied: bool) -> None:
    """Reopening holds the checkout or refuses before any correction state changes."""
    import shutil

    repo = h.make_repo(tmp_path)
    other = "docs/specs/other"
    shutil.copytree(repo / SPEC, repo / other)
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-qm", "second spec")
    assert h.start(repo)[0] == 0

    class CorrectionController(h.Controller):
        """Mint fresh worker record IDs for each request in both delivery cycles."""

        def work(self, request: dict[str, Any]) -> dict[str, Any]:
            result = super().work(request)
            if "report" in result:
                result["report"]["report_id"] = "report:" + request["request_id"]
                result["report"]["lineage"]["source_event_id"] = "event:" + request["request_id"]
            if "assessment" in result:
                result["assessment"]["assessment_id"] = "assessment:" + request["request_id"]
            return result

    controller = CorrectionController(repo, tmp_path / "effects")
    assert controller.drive().get("terminal")
    if occupied:
        assert h.run_cli(repo, "start", other, "--intent", "code", "--code-trust", "trusted",
                            "--authority-ref", "owner:0123456789ab",
                            "--review-authority-ref", "plan-reviewer:0123456789ab",
                            *h.digest_args(repo, other))[0] == 0
    ws = h.workspace(repo)
    reservation = h.admission._checkout_path(ws)
    before = reservation.read_bytes()
    refs = h.git(repo, "show-ref")
    records = ws.records("task-corrections.jsonl")
    task = h.loop.derive(ws).tasks[0]
    code, result = h.run_cli(repo, "correct-task", SPEC, "--task", task["task_id"],
                             "--reason", "Repair admitted task")
    if occupied:
        assert code == 1 and result["refusal"]["code"] == "checkout-reserved", result
        assert reservation.read_bytes() == before
        assert h.git(repo, "show-ref") == refs
        assert ws.records("task-corrections.jsonl") == records
        assert not (ws.git.ensure_store(h.loop.derive(ws).run_id)
                    / "task-correction-request.json").exists()
        return
    assert code == 0, result
    assert json.loads(reservation.read_bytes())["run_id"] == result["request"]["run_id"]
    code, refused = h.run_cli(repo, "start", other, "--intent", "code", "--code-trust", "trusted",
                            "--authority-ref", "owner:0123456789ab",
                            "--review-authority-ref", "plan-reviewer:0123456789ab",
                            *h.digest_args(repo, other))
    assert code == 1 and refused["refusal"]["code"] == "checkout-reserved", refused
    assert _confirm_correction(controller, result["request"], "owner:0123456789ab")[0] == 0
    code, refused = h.run_cli(repo, "start", other, "--intent", "code", "--code-trust", "trusted",
                            "--authority-ref", "owner:0123456789ab",
                            "--review-authority-ref", "plan-reviewer:0123456789ab",
                            *h.digest_args(repo, other))
    assert code == 1 and refused["refusal"]["code"] == "checkout-reserved", refused
    assert controller.drive().get("terminal")
    assert h.run_cli(repo, "start", other, "--intent", "code", "--code-trust", "trusted",
                            "--authority-ref", "owner:0123456789ab",
                            "--review-authority-ref", "plan-reviewer:0123456789ab",
                            *h.digest_args(repo, other))[0] == 0


@pytest.mark.parametrize("checkpoint", ["absent", "malformed"])
def test_old_shape_budget_import_is_missing_only(tmp_path: Path, checkpoint: str) -> None:
    """A real old record layout imports numbered counts but never repairs corrupt bytes."""
    import uuid
    from types import SimpleNamespace

    artifact = h.cli._supervisor("review-artifact.py")
    run_id = "run-0123456789abcdef"
    review_id = str(uuid.uuid5(uuid.NAMESPACE_URL, run_id))
    store = tmp_path / "store"
    store.mkdir()
    pins = {"schema_version": 1, "run_id": run_id, "spec": SPEC, "digests": {"old": "a" * 64}}
    (store / "pins.json").write_text(json.dumps(pins))
    records = tmp_path / ".context" / "reviews" / review_id
    records.mkdir(parents=True)
    (records / "1-record.md").write_text(json.dumps({
        "record_version": artifact.RECORD_VERSION, "run_id": review_id, "round": 1,
        "form": "findings", "fingerprints": ["b" * 64], "review_round_count": 1,
        "review_retry_count": 1, "max_review_retries": 5, "override": False, "stdout": "",
    }))
    ws = SimpleNamespace(
        root=tmp_path, git=SimpleNamespace(_store_dir=lambda run: store),
        attempts=SimpleNamespace(_store_record=lambda run, name: json.loads((store / name).read_text())),
        approvals=lambda: [{"run_id": run_id}],
        policy={"run_lock_timeout_seconds": 1, "run_lock_stale_seconds": 2400},
    )
    path = store / "review-budget.json"
    if checkpoint == "malformed":
        path.write_bytes(b"{")
        with pytest.raises(h.admission.Refusal) as caught:
            h.loop.load_review_budget(ws, run_id)
        assert caught.value.code == "invalid-review-budget"
        assert path.read_bytes() == b"{"
    else:
        budget = h.loop.load_review_budget(ws, run_id)
        assert budget["rounds"] == {"spec-stage": 1, "implementation": 0}
        assert budget["finding_records"] == budget["retries"] == 1
        assert json.loads(path.read_text()) == budget
        assert h.loop.load_review_budget(ws, run_id) == budget
        assert json.loads((store / "pins.json").read_text()) == pins
