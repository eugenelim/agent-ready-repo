"""The TDD guard admits only red-proven stubs (T5).

VI-4040 (AC-0013, AC-0014) over the TDD corpus: a one-stub task, a two-stub
task, a `no stub` task, a task revised after its stub commit, a revised
completed TDD task, and an attempt that changes a production file before red.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
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
SECOND_STUB = "import calc\nassert calc.answer() > 41\n"


def _commits(repo: Path) -> list[Any]:
    ws = h.workspace(repo)
    return ws.git.supervisor_commits(ws.approvals()[0]["run_id"])


def _product_paths(repo: Path, sha: str) -> list[str]:
    paths = h.git(repo, "show", "--name-only", "--format=", sha).split()
    return sorted(p for p in paths if not p.startswith(f"{SPEC}/delivery/"))


def _operations(repo: Path) -> list[str]:
    return [c.operation for c in _commits(repo)]


def _red_receipts(repo: Path) -> list[dict]:
    ws = h.workspace(repo)
    frames = h.loop.sibling("_evidence_store.py").replay_admitted_frames(ws.evidence_bytes())
    return [r for _tx, records in frames["frames"] for r in records
            if r.get("observation", {}).get("type") == "red"]


def _run(tmp_path: Path, plan: str, controller_cls: type = h.Controller) -> tuple[Path, dict]:
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    end = controller_cls(repo, tmp_path / "effects.log").drive()
    return repo, end


def _calc_plan(tests: str, *, mode: str = "TDD") -> str:
    return sup.plan(sup.task("T1", "Calculator answers", mode=mode, tests=tests),
                    sup.TASKS["push"](), sup.TASKS["plain"]())


def test_one_stub_task_is_red_before_its_production_change(tmp_path: Path) -> None:
    repo, end = _run(tmp_path, sup.PLAN)
    assert end.get("terminal")
    ops = _operations(repo)
    assert ops.index("stub") < ops.index("implement")
    stub = next(c for c in _commits(repo) if c.operation == "stub")
    assert _product_paths(repo, stub.sha) == ["test_calc.py"]
    assert h.git(repo, "show", f"{stub.sha}:test_calc.py") == sup.STUB
    assert len(_red_receipts(repo)) == 1


def test_two_stub_task_needs_both_stubs_red(tmp_path: Path) -> None:
    tests = ("- **VI-1:** both stubs.\n\n" + sup.stub_fence(indent="  ") + "\n\n"
             + sup.stub_fence(path="test_calc_two.py", body=SECOND_STUB, indent="  "))
    repo, end = _run(tmp_path, _calc_plan(tests))
    assert end.get("terminal")
    stub = next(c for c in _commits(repo) if c.operation == "stub")
    assert _product_paths(repo, stub.sha) == ["test_calc.py", "test_calc_two.py"]


def test_no_stub_task_completes_without_red_proof(tmp_path: Path) -> None:
    repo, end = _run(tmp_path, _calc_plan("no stub (implementation-discovered)"))
    assert end.get("terminal")
    assert "stub" not in _operations(repo) and "red" not in _operations(repo)
    assert _red_receipts(repo) == []


def _stepper(tmp_path: Path, plan: str = sup.PLAN) -> tuple[Path, h.Controller]:
    repo = h.make_repo(tmp_path, plan=plan)
    assert h.start(repo)[0] == 0
    return repo, h.Controller(repo, tmp_path / "effects.log")


def _do(repo: Path, controller: h.Controller) -> dict[str, Any]:
    _, payload = h.run_cli(repo, "next", SPEC)
    request = payload["request"]
    code, admitted = controller.report(controller.work(request))
    assert code == 0, admitted
    return request


def test_task_revised_after_its_stub_commit_gets_a_supervisor_red(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    assert _do(repo, controller)["kind"] == "write-stub"
    # Same stub bytes, a new fence: the stub digest moves and the bytes are in HEAD.
    revised = sup.plan(sup.task("T1", "Calculator answers", tests="- **VI-1:** x\n\n"
                                + sup.stub_fence(red_exit="1,2", indent="  ")),
                       sup.TASKS["push"](), sup.TASKS["plain"]())
    (repo / SPEC / "plan.md").write_text(revised, "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "implement-task"
    assert _operations(repo)[-2:] == ["replan", "red"]
    assert len(_red_receipts(repo)) == 2


def test_revised_completed_tdd_task_is_refused_until_a_no_stub_replan(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    _do(repo, controller)
    assert _do(repo, controller)["kind"] == "implement-task"
    revised = sup.plan(sup.task("T1", "Calculator answers", tests="- **VI-1:** x\n\n"
                                + sup.stub_fence(red_exit="1,2", indent="  ")),
                       sup.TASKS["push"](), sup.TASKS["plain"]())
    (repo / SPEC / "plan.md").write_text(revised, "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "stub-not-red"
    assert "no stub" in payload["refusal"]["detail"]
    assert _operations(repo)[-1] == "replan"
    head = h.git(repo, "rev-parse", "HEAD")
    replanned = sup.plan(sup.task("T1", "Calculator answers",
                                  tests="no stub (already covered by test_calc.py)"),
                         sup.TASKS["push"](), sup.TASKS["plain"]())
    (repo / SPEC / "plan.md").write_text(replanned, "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "implement-task"
    assert payload["request"]["task"]["title"] == "Calculator answers"
    code, admitted = controller.report(controller.work(payload["request"]))
    assert code == 0 and admitted["admitted"] == "implement"
    assert head != h.git(repo, "rev-parse", "HEAD")
    assert h.Controller(repo, tmp_path / "effects.log").drive().get("terminal")


def test_production_change_before_red_is_refused(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    _, payload = h.run_cli(repo, "next", SPEC)
    request = payload["request"]
    assert request["kind"] == "write-stub"
    result = controller.work(request)
    (repo / "calc.py").write_text("def answer():\n    return 42\n", "utf-8")
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "not-exactly-stub"
    assert h.git(repo, "rev-parse", "HEAD") == head
    assert _red_receipts(repo) == []


def test_altered_stub_bytes_are_refused(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    _, payload = h.run_cli(repo, "next", SPEC)
    result = controller.work(payload["request"])
    (repo / "test_calc.py").write_text(sup.STUB + "# extra\n", "utf-8")
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "stub-bytes-differ"


def test_a_stub_failing_with_an_undeclared_exit_is_not_red(tmp_path: Path) -> None:
    tests = "- **VI-1:** x\n\n" + sup.stub_fence(red_exit="3", indent="  ")
    repo, controller = _stepper(tmp_path, _calc_plan(tests))
    _, payload = h.run_cli(repo, "next", SPEC)
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    assert "exited 1" in refused["refusal"]["detail"]


def test_a_spent_red_proof_budget_runs_no_further_stub(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The first stub outlasts a one-second budget shared by both stubs, so the
    # second must never start: a per-stub budget would launch it.
    slow = sup.stub_fence(body="import time\ntime.sleep(10)\n", indent="  ")
    tests = ("- **VI-1:** both stubs.\n\n" + slow + "\n\n"
             + sup.stub_fence(path="test_calc_two.py", body=SECOND_STUB, indent="  "))
    repo, controller = _stepper(tmp_path, _calc_plan(tests))
    policy = h.admission.load_policy()
    monkeypatch.setattr(h.admission, "load_policy",
                        lambda: {**policy, "red_proof_budget_seconds": 1})
    tdd = h.cli._supervisor("_supervisor_tdd.py")
    launched: list[str] = []

    class _Recording:
        TimeoutExpired = subprocess.TimeoutExpired

        @staticmethod
        def run(argv: list[str], **kwargs: Any) -> Any:
            launched.append(argv[-1])
            return subprocess.run(argv, **kwargs)

    monkeypatch.setattr(tdd, "subprocess", _Recording)
    _, payload = h.run_cli(repo, "next", SPEC)
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    assert "test_calc_two.py exited None" in refused["refusal"]["detail"]
    assert launched == ["test_calc.py"], launched
