"""Admission to the concurrent path: the closed condition set, the floor, and its reasons."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SUPPORT = Path(__file__).resolve().parent / "launcher_support.py"


def _support() -> ModuleType:
    alias = "core_work_loop_launcher_support"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _SUPPORT)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


ls = _support()
sup = ls.sup
harness = ls.harness
integration = sup.INTEGRATION
pytestmark = integration


def _first(env: Any) -> dict[str, Any]:
    code, started = env.start()
    assert code == 0, started
    payload = env.next()
    assert "request" in payload, payload
    return payload["request"]  # type: ignore[no-any-return]


def _floor_reason(env: Any) -> str | None:
    return ls.journal(env.repo)[-1].get("floor_reason")


def test_the_shipped_policy_issues_no_run_concurrent_and_changes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = harness.make_repo(tmp_path)
    assert json.loads(harness.admission._POLICY_PATH.read_text("utf-8"))["concurrency"] == "sequential"
    code, started = harness.start(repo)
    assert code == 0, started
    controller = harness.Controller(repo, tmp_path / "effects.log")
    final = controller.drive()
    assert final.get("terminal"), final
    kinds = {entry["request"]["kind"] for entry in controller.log if "request" in entry}
    assert "run-concurrent" not in kinds
    assert all("floor_reason" not in line for line in ls.journal(repo))
    view = harness.run_cli(repo, "status", harness.SPEC_DIR)[1]
    assert "concurrency" not in view


def test_meeting_tasks_are_never_named_in_one_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=ls.TWO_TASKS)
    request = _first(env)
    assert request["kind"] == "run-concurrent"
    assert request["tasks"] == [request["task"]["task_id"]]
    assert len(request["tasks"]) == 1  # the declared writes meet, so one task runs alone
    assert _floor_reason(env) is None


def _task(reads: str | None, writes: str | None, *, fence: bool = False) -> str:
    return sup.plan(
        sup.task(
            "T1", "Calculator answers", mode="goal-based", touches="`calc.py`",
            tests=("- **VI-1:** the test.\n\n" + sup.stub_fence(indent="  ")) if fence
            else "no stub (goal-based)",
            reads=reads, writes=writes,
        )
    )


@pytest.mark.parametrize(
    ("label", "plan", "reason", "kind"),
    [
        ("reads", _task(None, "`calc.py`"), "reads-missing", "implement-task"),
        ("writes", _task("`README.md`", None), "writes-missing", "implement-task"),
        ("protected", _task("`README.md`", "`delivery/x`"), "protected-path", "implement-task"),
        ("glob", _task("`READ*.md`", "`calc.py`"), "invalid-glob", "implement-task"),
        ("stub", _task("`README.md`", "`calc.py`", fence=True), "stub-fence", "write-stub"),
    ],
)
def test_a_task_missing_one_plan_member_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, plan: str, reason: str, kind: str
) -> None:
    env = ls.Env(tmp_path, monkeypatch, plan=plan)
    request = _first(env)
    assert request["kind"] == kind
    assert _floor_reason(env) == reason
    assert reason in ls.concurrent_module.CLOSED_REASONS
    view = env.run("status", harness.SPEC_DIR)[1]
    assert view["concurrency"]["floor_reason"] == reason


def test_a_sequential_policy_is_the_opt_in_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, mode="sequential")
    assert _first(env)["kind"] == "implement-task"


def test_a_spent_reprojection_bound_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, policy={"reprojection_bound": 0})
    assert _first(env)["kind"] == "implement-task"
    assert _floor_reason(env) == "reprojection-bound"


def test_a_non_posix_host_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ls.concurrent_module, "_posix_host", lambda: False)
    env = ls.Env(tmp_path, monkeypatch)
    assert _first(env)["kind"] == "implement-task"
    assert _floor_reason(env) == "non-posix-host"


def test_an_old_git_goes_to_the_floor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git_module = ls.cli._supervisor("_supervisor_git.py")
    monkeypatch.setattr(git_module.HardenedGit, "git_version", property(lambda self: (2, 40)))
    env = ls.Env(tmp_path, monkeypatch)
    assert _first(env)["kind"] == "implement-task"
    assert _floor_reason(env) == "git-version"


def test_a_non_driver_merge_key_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    env.git("config", "merge.default", "union")
    assert _first(env)["kind"] == "implement-task"
    assert _floor_reason(env) == "merge-config"


def test_no_launcher_pin_goes_to_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, name=False)
    assert _first(env)["kind"] == "implement-task"
    assert _floor_reason(env) == "launcher-pin"


def test_a_floor_request_issues_only_while_no_attempt_is_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch)
    request = _first(env)
    run_id = request["run_id"]
    record = {
        "schema_version": 1, "run_id": run_id, "request_id": request["request_id"],
        "task_id": request["task"]["task_id"], "revision": request["task"]["revision"],
        "attempt": 1, "state": "running", "source": env.git("rev-parse", "HEAD").strip(),
        "verb_pid": __import__("os").getpid(),
        "verb_start": ls.launcher_module.process_start(__import__("os").getpid()),
    }
    ws = harness.workspace(env.repo)
    ls.concurrent_module._write(ws, run_id, record, create=True)
    # The verb is alive: the same request is issued again, never a floor request beside it.
    again = env.next()["request"]
    assert again["request_id"] == request["request_id"]
    assert again["kind"] == "run-concurrent"
    # The verb is gone: recovery closes the attempt and the floor issues the task.
    record["verb_start"] = "gone"
    ls.concurrent_module._write(ws, run_id, record)
    floor = env.next()["request"]
    assert floor["kind"] == "implement-task"
    assert _floor_reason(env) == "attempt-lost"
    assert env.records()[0]["state"] == "cancelled"


def test_a_floor_attempt_that_is_open_is_never_replaced_by_a_concurrent_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = ls.Env(tmp_path, monkeypatch, mode="sequential")
    request = _first(env)
    assert request["kind"] == "implement-task"
    # The policy now opts in, and every admission member holds: the open floor attempt stays.
    other = tmp_path / "other-policy"
    other.mkdir()
    monkeypatch.setattr(
        harness.admission, "_POLICY_PATH",
        ls.write_policy(other, concurrency="enforced-allowlist"),
    )
    again = env.next()["request"]
    assert again["request_id"] == request["request_id"] and again["kind"] == "implement-task"
    (env.repo / "calc.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    code, admitted = env.report(request, gate={"passed": True})
    assert code == 0 and admitted["admitted"] == "implement"
