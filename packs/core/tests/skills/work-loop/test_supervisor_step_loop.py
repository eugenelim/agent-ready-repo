"""The step loop derives, commits, and recovers (T4).

VI-4030 (AC-0008), VI-4031 (AC-0010, AC-0011), VI-4034 (AC-0026),
VI-4035 (AC-0030, AC-0031), VI-4036 (AC-0032).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import supervisor_harness as h  # noqa: E402
import supervisor_support as sup  # noqa: E402

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


@pytest.mark.parametrize("committed", [False, True], ids=["uncommitted", "committed"])
@pytest.mark.parametrize("name", sorted(REFUSALS))
def test_refusal_row_writes_nothing(tmp_path: Path, name: str, committed: bool) -> None:
    repo, _controller = _through_calculator(tmp_path)
    rel, old, new, code_expected, owner = REFUSALS[name]
    _edit(repo / rel, old, new)
    if committed:
        h.git(repo, "commit", "-qam", f"protected edit: {name}")
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
    code, second = h.start(repo)
    assert code == 0 and second["run_id"] == first["run_id"] and second["sequence"] == 2
    _, after = h.run_cli(repo, "status", SPEC, "--json")
    assert after["run"]["run_id"] == before["run"]["run_id"]
    assert [t["complete"] for t in after["tasks"]] == [True, True, True]
    assert after["retry_count"] == before["retry_count"] == 1
    assert [r for r in h.workspace(repo).records("effect-resolutions.jsonl")
            if r["entry"] == "receipt"] == receipts


@pytest.mark.parametrize(("rel", "old", "new", "code_expected"), [
    (ADR, "Callers need an answer.", "Callers need a better answer.", "protected-path-changed"),
    (ADR, "The calculator answers 42.", "The calculator answers 7.", "authority-changed"),
    (f"{SPEC}/spec.md", "calculator that answers.", "calculator that sings.",
     "protected-path-changed"),
    (f"{SPEC}/plan.md", "Build it.", "Build it fast.", "protected-path-changed"),
])
def test_worker_edit_to_a_trusted_file_is_refused_before_any_commit(
        tmp_path: Path, rel: str, old: str, new: str, code_expected: str) -> None:
    repo, controller = _through_calculator(tmp_path)
    _, payload = _next(repo)
    request = payload["request"]
    result = controller.work(request)
    _edit(repo / rel, old, new)
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == code_expected
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
