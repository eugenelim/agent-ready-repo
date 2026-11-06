"""The step loop derives, commits, and recovers (T4).

VI-4030 (AC-0008), VI-4031 (AC-0010, AC-0011), VI-4034 (AC-0026),
VI-4035 (AC-0030, AC-0031), VI-4036 (AC-0032).
"""

from __future__ import annotations

import importlib.util
import json
import os
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


# ── --json after any verb is accepted and changes nothing ────────────────────


def _run_main(repo: Path, argv: list[str]) -> int:
    """``main`` in-process with the harness's fixed clock; stdout and stderr stay on the real streams."""
    original = h.admission.CLOCK[0]
    h.admission.CLOCK[0] = lambda: h.FIXED_TIME
    try:
        return int(h.cli.main(argv, cwd=repo))
    finally:
        h.admission.CLOCK[0] = original


def _verb_calls(repo: Path, tmp_path: Path) -> dict[str, tuple[str, ...]]:
    """One argv per verb, without ``--json``, valid for a fresh harness repository."""
    result = tmp_path / "result.json"
    result.write_text("{}", encoding="utf-8")
    return {
        "park": ("park", SPEC, "--gate", "spec-approved", "--intent", "code",
                 "--code-trust", "trusted"),
        "gates": ("gates",),
        "start": ("start", SPEC, "--intent", "code", "--code-trust", "trusted",
                  "--authority-ref", "owner:0123456789ab",
                  "--review-authority-ref", "plan-reviewer:0123456789ab",
                  *h.digest_args(repo)),
        "next": ("next", SPEC),
        "report": ("report", SPEC, str(result)),
        "status": ("status", SPEC),
        "resolve-effect": ("resolve-effect", SPEC, "--operation", "op-1",
                           "--decision", "do-not-retry",
                           "--authority-ref", "effect-authority:0123456789ab"),
    }


@pytest.mark.parametrize(
    "verb", ["park", "gates", "start", "next", "report", "status", "resolve-effect"]
)
def test_json_after_the_verb_changes_neither_output_nor_exit_code(
    tmp_path: Path, verb: str, capsys: pytest.CaptureFixture[str]
) -> None:
    seen: list[tuple[int, str, str]] = []
    for name, extra in (("plain", ()), ("json", ("--json",))):
        root = tmp_path / name
        root.mkdir()
        repo = h.make_repo(root)
        argv = _verb_calls(repo, root)[verb]
        capsys.readouterr()
        with h.git_identity():
            code = _run_main(repo, [*argv, *extra])
        captured = capsys.readouterr()
        seen.append((code, captured.out.replace(str(root), "<root>"),
                     captured.err.replace(str(root), "<root>")))
    assert seen[0] == seen[1], seen
    assert "unrecognized arguments" not in seen[1][2]


# ── `route` on status and next follows the routing table ─────────────────────

_RESUMPTION_MD = (sup.SCRIPTS.parent / "references" / "session-resumption.md")
_CAP_KEY = ("1", "status, next")
_REFUSED_KEY = ("3", "status, next")


def _table_route(order: str, verb: str) -> str:
    """The route string the routing table gives one row, backticks stripped."""
    for line in _RESUMPTION_MD.read_text("utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] == order and cells[1] == verb:
            return cells[3].replace("`", "")
    raise AssertionError(f"no routing table row {order} for {verb}")


def _refused_route(code: str, owner: str) -> str:
    return (_table_route(*_REFUSED_KEY).replace("<code>", code).replace("<owner>", owner))


def _status(repo: Path, *flags: str) -> tuple[int, dict[str, Any]]:
    return h.run_cli(repo, "status", SPEC, *flags)


class _FailingGate(h.Controller):
    """A controller whose implementation attempts never pass their gate."""

    def work(self, request: dict[str, Any]) -> dict[str, Any]:
        result = super().work(request)
        if request["kind"] == "implement-task":
            result["gate"] = {"passed": False}
        return result


def _capped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A run whose retry count has reached a cap of one, with no refusal standing."""
    policy = h.admission.load_policy()
    monkeypatch.setattr(h.admission, "load_policy",
                        lambda: {**policy, "implementation_retry_cap": 1})
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    _FailingGate(repo, tmp_path / "effects.log").drive()
    return repo


def test_status_and_next_route_a_fresh_run_to_the_request_rows(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    code, status = _status(repo)
    assert code == 0 and status["request"] is not None and status["refusal"] == {}
    assert status["route"] == _table_route("7", "status")
    code, issued = _next(repo)
    assert code == 0 and issued["request"]["kind"] != "human-decision"
    assert issued["route"] == _table_route("7", "next")


def test_status_with_nothing_open_routes_to_run_next(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    real = h.loop.status

    def idle(ws: Any) -> dict[str, Any]:
        return {**real(ws), "request": None, "refusal": {}, "terminal": False}

    monkeypatch.setattr(h.loop, "status", idle)
    assert _status(repo)[1]["route"] == _table_route("8", "status")


def test_status_with_a_pending_regenerate_step_routes_to_run_next(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0

    class Plan:
        entries = {"skills/work-loop/x": object()}

    attempts = type(h.workspace(repo).attempts)
    monkeypatch.setattr(attempts, "regenerate_plan", lambda _self, _run_id: Plan())
    code, status = _status(repo)
    assert code == 0 and status["pending_step"]["operation"] == "regenerate"
    assert status["route"] == _table_route("4", "status")


def test_status_and_next_route_a_terminal_run(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")
    code, status = _status(repo, "--check")
    assert code == 0 and status["terminal"] is True
    assert status["route"] == _table_route("5", "status, next")
    code, done = _next(repo)
    assert code == 0 and done["terminal"] is True
    assert done["route"] == _table_route("5", "status, next")


def test_status_and_next_route_an_open_human_decision(tmp_path: Path) -> None:
    repo, _controller = _through_calculator(tmp_path)
    (repo / "NOTE.md").write_text("note\n", "utf-8")
    h.git(repo, "add", "NOTE.md")
    h.git(repo, "commit", "-qm", "controller commit")  # history the run did not make
    code, status = _status(repo)
    assert code == 0 and status["request"]["kind"] == "human-decision"
    assert status["request"]["reason"] == "history-adoption"
    assert status["route"] == _table_route("6", "status, next")
    code, asked = _next(repo)
    assert code == 0 and asked["request"]["reason"] == "history-adoption"
    assert asked["route"] == _table_route("6", "status, next")


def test_a_capped_run_with_no_refusal_routes_both_verbs_to_the_cap_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _capped(tmp_path, monkeypatch)
    code, status = _status(repo, "--check")
    assert code == h.cli.EXIT_CAP and status["refusal"] == {}
    assert status["retry_count"] >= 1 and status["terminal"] is False
    assert status["route"] == _table_route(*_CAP_KEY)
    code, issued = _next(repo)
    assert code == 0 and issued["request"]["reason"] == "retry-cap"
    assert issued["route"] == _table_route(*_CAP_KEY)


def test_a_capped_run_with_a_standing_refusal_names_the_cap_on_status_only(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _capped(tmp_path, monkeypatch)
    rel, old, new, code_expected, owner = REFUSALS["criteria"]
    _edit(repo / rel, old, new)
    code, status = _status(repo, "--check")
    assert code == h.cli.EXIT_CAP and status["refusal"]["code"] == code_expected
    assert status["route"] == _table_route(*_CAP_KEY)
    code, refused = _next(repo)
    assert code == 1 and refused["refusal"]["code"] == code_expected
    assert refused["route"] == _refused_route(code_expected, owner)


@pytest.mark.parametrize("name", ["criteria", "scope"])
def test_status_and_next_route_a_refusal_with_its_own_code_and_owner(
        tmp_path: Path, name: str) -> None:
    repo, _controller = _through_calculator(tmp_path)
    rel, old, new, code_expected, owner = REFUSALS[name]
    _edit(repo / rel, old, new)
    expected = _refused_route(code_expected, owner)
    code, status = _status(repo, "--check")
    assert code == 1 and status["refusal"]["code"] == code_expected
    assert status["route"] == expected
    code, refused = _next(repo)
    assert code == 1 and refused["route"] == expected
    assert refused["refusal"]["detail"] not in refused["route"]


class _FailingUnlink:
    """``os`` with an ``unlink`` that fails, to force a discard failure."""

    def __getattr__(self, name: str) -> Any:
        return getattr(os, name)

    @staticmethod
    def unlink(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("forced")


def test_live_recovery_leftovers_route_both_verbs_to_the_leftovers_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    passing = "- **VI-1:** x\n\n" + sup.stub_fence(body="assert True\n", indent="  ")
    plan = sup.plan(sup.task("T1", "Calculator answers", tests=passing),
                    sup.TASKS["push"](), sup.TASKS["plain"]())
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    request = _next(repo)[1]["request"]
    result = controller.work(request)
    with monkeypatch.context() as patch:
        patch.setattr(h.cli._supervisor("_supervisor_recovery.py"), "os", _FailingUnlink())
        code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    code, status = _status(repo)
    assert status["refusal"]["code"] == "recovery-leftovers"
    assert status["route"] == _table_route("2", "status, next")
    code, blocked = _next(repo)
    assert code == 1 and blocked["refusal"]["code"] == "recovery-leftovers"
    assert blocked["route"] == _table_route("2", "status, next")


def _pin_refused(*_args: Any, **_kwargs: Any) -> Any:
    raise h.cli._PinRefused("the installed supervisor differs from its pinned digests")


@pytest.mark.parametrize("verb", ["status", "next"])
def test_the_pin_check_refusal_routes_to_the_refusal_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verb: str) -> None:
    repo = h.make_repo(tmp_path)
    monkeypatch.setattr(h.cli, "_preflight", _pin_refused)
    code, out = h.run_cli(repo, verb, SPEC)
    assert code == 1 and out["refusal"]["code"] == "supervisor-changed"
    assert out["route"] == _refused_route("supervisor-changed", "controller")


def test_the_unsupported_ref_storage_refusal_routes_status_to_the_refusal_row(
        tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    config = repo / ".git" / "config"
    original = config.read_text("utf-8")
    config.write_text(original.replace("repositoryformatversion = 0",
                                       "repositoryformatversion = 1")
                      + "[extensions]\n\trefStorage = reftable\n", "utf-8")
    try:
        code, out = _status(repo, "--check")
    finally:
        config.write_text(original, "utf-8")
    assert code == 1 and out["refusal"]["code"] == "unsupported-ref-storage", out
    assert "retry_count" not in out
    assert out["route"] == _refused_route("unsupported-ref-storage", out["refusal"]["owner"])


@pytest.mark.parametrize(("fault", "code_expected", "owner"), [
    ("lock", "run-locked", "controller"),
    ("internal", "internal-error", "skill maintainer"),
])
def test_a_forced_fault_on_status_routes_to_the_refusal_row(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        fault: str, code_expected: str, owner: str) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    lock_error = h.commit_module.sibling("_statelock.py").StateLockError

    def broken(_ws: Any) -> dict[str, Any]:
        if fault == "lock":
            raise lock_error("forced")
        return {}["missing"]

    monkeypatch.setattr(h.loop, "status", broken)
    code, out = _status(repo)
    assert code == 1 and out["refusal"]["code"] == code_expected
    assert out["route"] == _refused_route(code_expected, owner)


# ── other verbs never carry `route`, and no routing context outlives a call ──


def test_status_check_exit_codes_are_unchanged(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    assert _status(repo, "--check")[0] == 0


def test_other_verbs_carry_no_route_even_right_after_a_status_call(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    fresh = h.make_repo(tmp_path / "fresh")
    assert h.start(repo)[0] == 0
    bad_result = tmp_path / "bad-result.json"
    bad_result.write_text("{}", "utf-8")
    assert "route" in _status(repo)[1]  # the routing context was live in this very process
    code, out = h.run_cli(repo, "report", SPEC, str(bad_result))
    assert code == 1 and out["refusal"]["code"] == "invalid-result" and "route" not in out
    code, out = h.run_cli(repo, "report", SPEC, str(bad_result))
    assert "route" not in out
    code, out = h.run_cli(repo, "resolve-effect", SPEC, "--operation", "op-missing",
                          "--decision", "do-not-retry",
                          "--authority-ref", "effect-authority:0123456789ab")
    assert code == 1 and "refusal" in out and "route" not in out
    digests = h.digest_args(fresh)
    digests[1] = digests[1][:-1] + ("0" if digests[1][-1] != "0" else "1")  # a spec nobody approved
    code, out = h.run_cli(fresh, "start", SPEC, "--intent", "code", "--code-trust", "trusted",
                          "--authority-ref", "owner:0123456789ab",
                          "--review-authority-ref", "plan-reviewer:0123456789ab", *digests)
    assert code == 1 and "refusal" in out and "route" not in out
