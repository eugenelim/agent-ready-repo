"""The TDD guard admits only red-proven stubs (T5).

VI-4040 (AC-0013, AC-0014) over the TDD corpus: a one-stub task, a two-stub
task, a `no stub` task, a task revised after its stub commit, a revised
completed TDD task, and an attempt that changes a production file before red.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
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


def test_revised_completed_tdd_task_is_refused_until_the_fence_is_removed(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    _do(repo, controller)
    assert _do(repo, controller)["kind"] == "implement-task"
    revised = sup.plan(sup.task("T1", "Calculator answers", tests="- **VI-1:** x\n\n"
                                + sup.stub_fence(red_exit="1,2", indent="  ")),
                       sup.TASKS["push"](), sup.TASKS["plain"]())
    (repo / SPEC / "plan.md").write_text(revised, "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "stub-not-red"
    assert "remove it" in payload["refusal"]["detail"]
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


# ── not-red recovery: a stub that is not red closes its attempt ─────────────

OWNER = "owner:0123456789ab"
PASSING_STUB = "assert True\n"
MOVED_STUB = "test_calc_moved.py"
REVISED_STUB = "import calc\nassert calc.answer() == 42\nassert calc.answer() > 41\n"


def _stub_plan(path: str = "test_calc.py", body: str = PASSING_STUB) -> str:
    return _calc_plan("- **VI-1:** x\n\n" + sup.stub_fence(path=path, body=body, indent="  "))


def _plan_path(repo: Path) -> Path:
    return repo / SPEC / "plan.md"


def _store(repo: Path) -> Path:
    run_id = h.workspace(repo).approvals()[0]["run_id"]
    return repo / ".git" / "agentbundle-supervisor" / run_id


def _closed(tmp_path: Path, plan: str | None = None) -> tuple[Path, h.Controller, str]:
    """A run whose write-stub result was refused as not red; returns the HEAD it left."""
    repo, controller = _stepper(tmp_path, plan or _stub_plan())
    _, payload = h.run_cli(repo, "next", SPEC)
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red", refused
    return repo, controller, h.git(repo, "rev-parse", "HEAD").strip()


def _confirmation(repo: Path) -> dict[str, Any]:
    _, payload = h.run_cli(repo, "next", SPEC)
    assert "request" in payload, payload
    request = payload["request"]
    assert request["kind"] == "human-decision" and request["reason"] == "replan-confirmation"
    return request


def _answer(request: dict[str, Any], decision: str = "confirm-replan",
            ref: str = OWNER) -> dict[str, Any]:
    return {"schema_version": 1, "request_id": request["request_id"],
            "run_id": request["run_id"], "kind": "human-decision",
            "decision": {"decision": decision, "authority_ref": ref,
                         "selection_key": request["selection_key"]}}


def _wipe_local_state(repo: Path) -> None:
    for name in ("journal.jsonl", "run.json", "security-events.jsonl"):
        (repo / SPEC / ".supervisor" / name).unlink(missing_ok=True)


def _tracked(repo: Path) -> list[str]:
    return h.git(repo, "ls-files").split()


def test_a_stub_that_is_not_red_closes_its_attempt_and_commits_nothing(tmp_path: Path) -> None:
    repo, _controller, head = _closed(tmp_path)
    assert _operations(repo) == ["approval"]
    assert "test_calc.py" not in _tracked(repo)
    # The refused result's file is gone, so nothing later can commit it.
    assert not (repo / "test_calc.py").exists()
    assert h.git(repo, "status", "--porcelain", "--", ".").split() == []
    # The attempt is closed: a plan edit now is not residue.
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "human-decision", payload
    assert h.git(repo, "rev-parse", "HEAD").strip() == head


def _fence_fixes() -> dict[str, tuple[str, str]]:
    return {
        "removed": (_calc_plan("no stub (covered elsewhere)"), "implement-task"),
        "moved": (_stub_plan(MOVED_STUB, sup.STUB), "write-stub"),
        "same-path": (_stub_plan("test_calc.py", sup.STUB), "write-stub"),
    }


@pytest.mark.parametrize("fix", ["removed", "moved", "same-path"])
def test_a_fence_fix_waits_for_a_human_then_commits_as_one_replan(
        tmp_path: Path, fix: str) -> None:
    repo, controller, head = _closed(tmp_path)
    fixed, follow_kind = _fence_fixes()[fix]
    _plan_path(repo).write_text(fixed, "utf-8")
    request = _confirmation(repo)
    assert "attempt-residue" not in json.dumps(request)
    assert request["diff"].count("\n") > 0 and "stub" in request["diff"]
    # status returns the same request, diff included.
    _, status = h.run_cli(repo, "status", SPEC)
    assert status["request"] == request
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    code, admitted = controller.report(_answer(request))
    assert code == 0, admitted
    assert _operations(repo) == ["approval", "replan"]
    trailers = h.git(repo, "log", "-1", "--format=%B")
    assert f"Supervisor-Authority-Ref: {OWNER}" in trailers
    assert _plan_path(repo).read_text("utf-8") == fixed
    # The gate ends with the confirmation: the next trusted-file change is a plain replan.
    _plan_path(repo).write_text(fixed + "\n- 2026-10-15: a note\n", "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == follow_kind, payload
    assert _operations(repo) == ["approval", "replan", "replan"]
    # The next admitted step holds none of the refused result's files.
    code, admitted = controller.report(controller.work(payload["request"]))
    assert code == 0, admitted
    step = _commits(repo)[-1]
    if fix == "removed":
        assert step.operation == "implement"
        assert _product_paths(repo, step.sha) == ["calc.py"]
        assert "test_calc.py" not in _tracked(repo)
    else:
        assert step.operation == "stub"
        expected = MOVED_STUB if fix == "moved" else "test_calc.py"
        assert _product_paths(repo, step.sha) == [expected]
        assert ("test_calc.py" in _tracked(repo)) == (fix == "same-path")


def test_a_not_red_launch_that_also_writes_the_plan_stays_refused(tmp_path: Path) -> None:
    plan_file = tmp_path / "repo" / SPEC / "plan.md"
    body = f"open({str(plan_file)!r}, 'a').write('<!-- touched -->')\n"
    repo, controller = _stepper(tmp_path, _stub_plan(body=body))
    original = _plan_path(repo).read_bytes()
    _, payload = h.run_cli(repo, "next", SPEC)
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "attempt-refused", refused
    code, again = h.run_cli(repo, "next", SPEC)
    assert code == 1 and again["refusal"]["code"] == "attempt-residue"
    assert not list((_store(repo) / "attempts").glob("*.reported"))
    assert not (_store(repo) / "recovery.json").exists()
    # Restoring the plan clears the refusal; the attempt was never closed, so the
    # stale result is still not admitted.
    _plan_path(repo).write_bytes(original)
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue"


def test_deleting_local_state_neither_forges_nor_reopens_the_closure(tmp_path: Path) -> None:
    repo, controller, _head = _closed(tmp_path)
    _wipe_local_state(repo)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    request = _confirmation(repo)
    _wipe_local_state(repo)
    # Still owed after a decline, and the refusal survives the wipe.
    code, declined = controller.report(_answer(request, "decline-replan"))
    assert code == 0, declined
    _wipe_local_state(repo)
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "replan-declined"
    h.git(repo, "checkout", "--", f"{SPEC}/plan.md")
    _wipe_local_state(repo)
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "write-stub"


def test_deleting_local_state_does_not_close_an_open_attempt(tmp_path: Path) -> None:
    repo, _controller = _stepper(tmp_path, _stub_plan())
    _, payload = h.run_cli(repo, "next", SPEC)
    assert payload["request"]["kind"] == "write-stub"
    _wipe_local_state(repo)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    code, refused = h.run_cli(repo, "next", SPEC)
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue"


def test_a_trusted_write_after_the_diff_is_shown_commits_nothing_and_opens_a_new_decision(
        tmp_path: Path) -> None:
    repo, controller, head = _closed(tmp_path)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    first = _confirmation(repo)
    sneaky = _stub_plan(body=sup.STUB) + "\n- 2026-10-14: surprise\n"
    _plan_path(repo).write_text(sneaky, "utf-8")
    code, refused = controller.report(_answer(first))
    assert code == 1 and refused["refusal"]["code"] == "not-current-attempt", refused
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    second = _confirmation(repo)
    assert second["request_id"] != first["request_id"]
    assert second["selection_key"] != first["selection_key"]
    assert "surprise" in second["diff"]
    code, admitted = controller.report(_answer(second))
    assert code == 0, admitted
    assert h.git(repo, "show", f"HEAD:{SPEC}/plan.md") == sneaky


def test_a_decline_commits_nothing_and_the_next_edit_needs_a_new_confirmation(
        tmp_path: Path) -> None:
    repo, controller, head = _closed(tmp_path)
    fixed = _stub_plan(body=sup.STUB)
    _plan_path(repo).write_text(fixed, "utf-8")
    request = _confirmation(repo)
    code, declined = controller.report(_answer(request, "decline-replan"))
    assert code == 0, declined
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "replan-declined"
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    h.git(repo, "checkout", "--", f"{SPEC}/plan.md")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "write-stub"
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    _plan_path(repo).write_text(fixed, "utf-8")
    again = _confirmation(repo)
    assert again["selection_key"] == request["selection_key"]
    assert h.git(repo, "rev-parse", "HEAD").strip() == head


def test_a_confirmation_needs_an_owner_reference_and_its_own_digest(tmp_path: Path) -> None:
    repo, controller, head = _closed(tmp_path)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    request = _confirmation(repo)
    for bad in (_answer(request, ref="risk-owner:0123456789ab"),
                {**_answer(request), "decision": {**_answer(request)["decision"],
                                                  "selection_key": "0" * 64}}):
        code, refused = controller.report(bad)
        assert code == 1, refused
        assert h.git(repo, "rev-parse", "HEAD").strip() == head


def test_a_confirmation_with_an_extra_changed_path_is_refused(tmp_path: Path) -> None:
    repo, controller, head = _closed(tmp_path)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    request = _confirmation(repo)
    (repo / "stray.txt").write_text("extra\n", "utf-8")
    code, refused = controller.report(_answer(request))
    assert code == 1 and refused["refusal"]["code"] == "unexpected-change", refused
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    (repo / "stray.txt").unlink()
    code, admitted = controller.report(_answer(request))
    assert code == 0, admitted


def test_another_decision_kind_over_uncommitted_plan_edits_is_refused(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path, plan=_stub_plan())
    code, _ = h.run_cli(repo, "start", SPEC, "--intent", "code", "--code-trust", "untrusted",
                        "--authority-ref", OWNER, "--review-authority-ref",
                        "plan-reviewer:0123456789ab")
    assert code == 0
    _, payload = h.run_cli(repo, "next", SPEC)
    request = payload["request"]
    assert request["kind"] == "human-decision" and request["reason"] == "untrusted-code"
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    controller = h.Controller(repo, tmp_path / "effects.log")
    result = {"schema_version": 1, "request_id": request["request_id"],
              "run_id": request["run_id"], "kind": "human-decision",
              "decision": {"decision": "reselect-review", "authority_ref": OWNER,
                           "selection_key": "k"}}
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "protected-path-changed", refused


# ── recovery hardening ──────────────────────────────────────────────────────


def _with_hook(hook: Any) -> Any:
    """Install a kill-point hook for one block."""
    import contextlib

    @contextlib.contextmanager
    def scope() -> Any:
        h.commit_module.set_kill_hook(hook)
        try:
            yield
        finally:
            h.commit_module.set_kill_hook(None)

    return scope()


def _recovery_record(repo: Path) -> dict[str, Any]:
    return json.loads((_store(repo) / "recovery.json").read_text("utf-8"))


def test_a_trusted_write_between_the_digest_check_and_staging_commits_nothing(
        tmp_path: Path) -> None:
    repo, controller, head = _closed(tmp_path)
    fixed = _stub_plan(body=sup.STUB)
    _plan_path(repo).write_text(fixed, "utf-8")
    first = _confirmation(repo)

    def swap(name: str) -> None:
        if name == "replan-verified":
            _plan_path(repo).write_text(fixed + "\n- 2026-10-14: swapped\n", "utf-8")

    with _with_hook(swap):
        code, refused = controller.report(_answer(first))
    assert code == 1 and refused["refusal"]["code"] == "replan-changed", refused
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    second = _confirmation(repo)
    assert second["selection_key"] != first["selection_key"] and "swapped" in second["diff"]


def test_discard_leaves_a_path_changed_after_the_observation(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path, _stub_plan())
    _, payload = h.run_cli(repo, "next", SPEC)
    result = controller.work(payload["request"])

    def unrelated(name: str) -> None:
        if name == "recovery-discard":
            (repo / "test_calc.py").write_text("# someone else's edit\n", "utf-8")
            (repo / "other.txt").write_text("unrelated\n", "utf-8")

    with _with_hook(unrelated):
        code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    assert (repo / "test_calc.py").read_text("utf-8") == "# someone else's edit\n"
    assert (repo / "other.txt").read_text("utf-8") == "unrelated\n"


def test_discard_does_not_follow_a_parent_swapped_for_a_link(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path, _stub_plan("d/test_calc.py"))
    _, payload = h.run_cli(repo, "next", SPEC)
    result = controller.work(payload["request"])

    def swap(name: str) -> None:
        if name == "recovery-discard":
            shutil.rmtree(repo / "d")
            (repo / "real").mkdir()
            (repo / "real" / "test_calc.py").write_text(PASSING_STUB, "utf-8")
            (repo / "d").symlink_to("real")

    with _with_hook(swap):
        code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    assert (repo / "real" / "test_calc.py").read_text("utf-8") == PASSING_STUB


def test_a_crash_after_the_replan_commits_recovers_without_a_human(tmp_path: Path) -> None:
    repo, controller, _head = _closed(tmp_path)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    request = _confirmation(repo)

    def crash(name: str) -> None:
        if name == "replan-committed":
            raise h.Crash(name)

    with _with_hook(crash), pytest.raises(h.Crash):
        controller.report(_answer(request))
    assert _operations(repo)[-1] == "replan" and _recovery_record(repo)["owed"] is True
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "write-stub", payload
    record = _recovery_record(repo)
    assert record["owed"] is False and record["confirming"] is None
    assert [d["authority_ref"] for d in record["decisions"]] == [OWNER]


def test_a_different_edit_after_a_decline_is_refused_until_restored_to_head(
        tmp_path: Path) -> None:
    repo, controller, head = _closed(tmp_path)
    fixed = _stub_plan(body=sup.STUB)
    _plan_path(repo).write_text(fixed, "utf-8")
    first = _confirmation(repo)
    assert controller.report(_answer(first, "decline-replan"))[0] == 0
    issued = sorted(p.name for p in (_store(repo) / "attempts").iterdir())
    _plan_path(repo).write_text(fixed + "\n- 2026-10-15: another take\n", "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "replan-declined", payload
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    assert sorted(p.name for p in (_store(repo) / "attempts").iterdir()) == issued
    # Restoring brings the fence that was not red back: the stub runs again and closes again.
    h.git(repo, "checkout", "--", f"{SPEC}/plan.md")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "write-stub", payload
    code, refused = controller.report(controller.work(payload["request"]))
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    _plan_path(repo).write_text(fixed + "\n- 2026-10-15: another take\n", "utf-8")
    second = _confirmation(repo)
    assert second["selection_key"] != first["selection_key"]
    assert controller.report(_answer(second))[0] == 0


class _FailingUnlink:
    """``os`` with an ``unlink`` that fails, to force a discard failure."""

    def __getattr__(self, name: str) -> Any:
        return getattr(os, name)

    @staticmethod
    def unlink(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("forced")


def test_a_file_the_discard_cannot_remove_is_reported_and_blocks_the_next_step(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, controller = _stepper(tmp_path, _stub_plan())
    _, payload = h.run_cli(repo, "next", SPEC)
    result = controller.work(payload["request"])
    recovery = h.cli._supervisor("_supervisor_recovery.py")
    with monkeypatch.context() as patch:
        patch.setattr(recovery, "os", _FailingUnlink())
        code, refused = controller.report(result)
    detail = refused["refusal"]["detail"]
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    assert "test_calc.py" in detail and "could not be discarded" in detail
    assert "Its files are discarded" not in detail
    assert (repo / "test_calc.py").exists()
    assert list(_recovery_record(repo)["leftovers"]) == ["test_calc.py"]
    _, status = h.run_cli(repo, "status", SPEC)
    assert list(status["recovery_leftovers"]) == ["test_calc.py"]
    head = h.git(repo, "rev-parse", "HEAD").strip()
    code, blocked = h.run_cli(repo, "next", SPEC)
    assert code == 1 and blocked["refusal"]["code"] == "recovery-leftovers", blocked
    assert "test_calc.py" in blocked["refusal"]["detail"]
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    (repo / "test_calc.py").unlink()
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "write-stub", payload
    _, status = h.run_cli(repo, "status", SPEC)
    assert status["recovery_leftovers"] == {}


def test_rewriting_a_leftover_does_not_unblock_the_run(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, controller = _stepper(tmp_path, _stub_plan())
    _, payload = h.run_cli(repo, "next", SPEC)
    result = controller.work(payload["request"])
    with monkeypatch.context() as patch:
        patch.setattr(h.cli._supervisor("_supervisor_recovery.py"), "os", _FailingUnlink())
        assert controller.report(result)[0] == 1
    head = h.git(repo, "rev-parse", "HEAD").strip()
    (repo / "test_calc.py").write_text("# rewritten in place\n", "utf-8")
    code, blocked = h.run_cli(repo, "next", SPEC)
    assert code == 1 and blocked["refusal"]["code"] == "recovery-leftovers", blocked
    assert "HEAD" in blocked["refusal"]["detail"]
    _, status = h.run_cli(repo, "status", SPEC)
    assert list(status["recovery_leftovers"]) == ["test_calc.py"]
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    assert "test_calc.py" not in h.git(repo, "log", "--all", "--name-only", "--format=")
    (repo / "test_calc.py").unlink()
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "write-stub", payload
    assert "test_calc.py" not in h.git(repo, "log", "--all", "--name-only", "--format=")


def _leftover_run(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, plan: str) -> tuple[Path, dict[str, Any]]:
    """A run whose refused stub file could not be discarded."""
    repo, controller = _stepper(tmp_path, plan)
    _, payload = h.run_cli(repo, "next", SPEC)
    result = controller.work(payload["request"])
    with monkeypatch.context() as patch:
        patch.setattr(h.cli._supervisor("_supervisor_recovery.py"), "os", _FailingUnlink())
        code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "stub-not-red"
    return repo, refused


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs named pipes")
def test_a_leftover_turned_into_a_special_file_keeps_blocking(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, refused = _leftover_run(tmp_path, monkeypatch, _stub_plan())
    (repo / "test_calc.py").unlink()
    os.mkfifo(repo / "test_calc.py")
    code, blocked = h.run_cli(repo, "next", SPEC)
    assert code == 1 and blocked["refusal"]["code"] == "recovery-leftovers", blocked


def test_a_leftover_behind_a_swapped_parent_keeps_blocking(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, refused = _leftover_run(tmp_path, monkeypatch, _stub_plan("d/test_calc.py"))
    shutil.rmtree(repo / "d")
    (repo / "elsewhere").mkdir()
    (repo / "d").symlink_to("elsewhere")
    code, blocked = h.run_cli(repo, "next", SPEC)
    assert code == 1 and blocked["refusal"]["code"] == "recovery-leftovers", blocked


def test_a_leftover_name_is_shown_escaped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evil = tmp_path / "repo" / ("ev" + chr(7) + "il.txt")
    body = f"open({str(evil)!r}, 'w').write('x')\n"
    repo, refused = _leftover_run(tmp_path, monkeypatch, _stub_plan(body=body))
    _, blocked = h.run_cli(repo, "next", SPEC)
    assert blocked["refusal"]["code"] == "recovery-leftovers"
    for detail in (refused["refusal"]["detail"], blocked["refusal"]["detail"]):
        assert "ev?il.txt" in detail and chr(7) not in detail


def test_status_surfaces_the_recorded_decisions(tmp_path: Path) -> None:
    repo, controller, _head = _closed(tmp_path)
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB), "utf-8")
    request = _confirmation(repo)
    ref = "owner:feedfacefeed"
    assert controller.report(_answer(request, "decline-replan", ref))[0] == 0
    _, status = h.run_cli(repo, "status", SPEC)
    assert status["recovery_decisions"] == [{
        "request_id": request["request_id"], "decision": "decline-replan",
        "authority_ref": ref, "selection_key": request["selection_key"],
    }]


def test_a_diff_too_large_to_show_is_refused_not_truncated(tmp_path: Path) -> None:
    def filler(tag: str) -> str:
        return "".join(f"{tag} {n:06d} " + "x" * 64 + "\n" for n in range(30000))

    base = _stub_plan().replace("Build it.\n", filler("a"), 1)
    repo, controller, head = _closed(tmp_path, base)
    fixed = _stub_plan(body=sup.STUB).replace("Build it.\n", filler("b"), 1)
    _plan_path(repo).write_text(fixed, "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "replan-diff-too-large", payload
    assert h.git(repo, "rev-parse", "HEAD").strip() == head
    _plan_path(repo).write_text(_stub_plan(body=sup.STUB).replace("Build it.\n", filler("a"), 1),
                                "utf-8")
    request = _confirmation(repo)
    assert len(request["diff"]) <= 4 * 1024 * 1024


# ── VI-7023: who may add a stub fence, and when the plan may change ───────────

DESIGN_NOTE = (
    "## Design (LLD)\n\n"
    "- The calculator is one function, `answer()`, in `calc.py`.\n\n"
)
FENCED = "- **VI-1:** x\n\n" + sup.stub_fence(indent="  ")


def _with_design(plan: str) -> str:
    """*plan* with a design note ahead of its tasks: an edit outside every task."""
    return plan.replace("## Tasks", DESIGN_NOTE + "## Tasks", 1)


def _approvals(repo: Path) -> int:
    return len(h.workspace(repo).approvals())


def _completed(repo: Path) -> list[str]:
    _, status = h.run_cli(repo, "status", SPEC, "--json")
    return [t["title"] for t in status["tasks"] if t["complete"]]


def test_a_controller_added_fence_replans_then_stubs_then_implements(
        tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path, _calc_plan("no stub (implementation-discovered)"))
    approvals = _approvals(repo)
    # The controller adds the fence after the last result and before the first request.
    _plan_path(repo).write_text(_calc_plan(FENCED), "utf-8")
    assert _do(repo, controller)["kind"] == "write-stub"
    assert _operations(repo) == ["approval", "replan", "stub"]
    assert _do(repo, controller)["kind"] == "implement-task"
    assert _operations(repo) == ["approval", "replan", "stub", "implement"]
    assert _approvals(repo) == approvals
    assert "Calculator answers" in _completed(repo)
    assert len(_red_receipts(repo)) == 1


def test_a_worker_added_fence_is_refused_and_commits_nothing(tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path, _calc_plan("no stub (implementation-discovered)"))
    _, payload = h.run_cli(repo, "next", SPEC)
    assert payload["request"]["kind"] == "implement-task"
    result = controller.work(payload["request"])
    _plan_path(repo).write_text(_calc_plan(FENCED), "utf-8")
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "attempt-refused", refused
    assert h.git(repo, "rev-parse", "HEAD") == head
    assert _operations(repo) == ["approval"]
    assert _approvals(repo) == 1
    assert _completed(repo) == []
    assert "calc.py" not in _tracked(repo)


def test_a_design_only_edit_between_attempts_is_one_replan_and_keeps_completed_tasks(
        tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    _do(repo, controller)
    _do(repo, controller)
    assert _completed(repo) == ["Calculator answers"]
    approvals = _approvals(repo)
    _plan_path(repo).write_text(_with_design(_plan_path(repo).read_text("utf-8")), "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload["request"]["kind"] == "implement-task", payload
    assert _operations(repo).count("replan") == 1 and _operations(repo)[-1] == "replan"
    assert _completed(repo) == ["Calculator answers"]
    assert _approvals(repo) == approvals


def test_the_same_design_edit_while_an_attempt_is_open_is_attempt_residue(
        tmp_path: Path) -> None:
    repo, controller = _stepper(tmp_path)
    _, payload = h.run_cli(repo, "next", SPEC)
    assert payload["request"]["kind"] == "write-stub"
    result = controller.work(payload["request"])
    _plan_path(repo).write_text(_with_design(_plan_path(repo).read_text("utf-8")), "utf-8")
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = h.run_cli(repo, "next", SPEC)
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue", refused
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "attempt-residue", refused
    assert h.git(repo, "rev-parse", "HEAD") == head
    assert _operations(repo) == ["approval"]
    assert _approvals(repo) == 1
