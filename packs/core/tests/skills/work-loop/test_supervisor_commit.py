"""The commit builder's guards and the CLI's refusal contract.

The HEAD compare-and-swap and the step-id skip, foreign `delivery/` edits,
Git failures surfacing as one JSON refusal, and a replan that returns to
earlier content.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tarfile
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


def _started(tmp_path: Path) -> tuple[Path, Any, str]:
    repo = h.make_repo(tmp_path)
    code, out = h.start(repo)
    assert code == 0, out
    return repo, h.workspace(repo), out["run_id"]


def test_a_head_move_during_the_build_refuses_the_swap_and_keeps_the_user_commit(
        tmp_path: Path) -> None:
    repo, ws, run_id = _started(tmp_path)

    def user_commits(name: str) -> None:
        if name == "commit-built":
            (repo / "USER.md").write_text("user\n", "utf-8")
            h.git(repo, "add", "USER.md")
            h.git(repo, "commit", "-q", "-m", "user work")

    h.commit_module.set_kill_hook(user_commits)
    try:
        with h.git_identity(), pytest.raises(h.commit_module.SupervisorGitError):
            ws.git.build_commit(run_id=run_id, step="probe:1", operation="replan")
    finally:
        h.commit_module.set_kill_hook(None)
    assert h.git(repo, "log", "-1", "--format=%s").strip() == "user work"
    assert "probe:1" not in {c.step for c in h.workspace(repo).git.supervisor_commits(run_id)}


def test_a_reachable_step_is_skipped(tmp_path: Path) -> None:
    repo, ws, run_id = _started(tmp_path)
    with h.git_identity():
        first = ws.git.build_commit(run_id=run_id, step="probe:2", operation="replan")
    head = h.git(repo, "rev-parse", "HEAD")
    with h.git_identity():
        second = h.workspace(repo).git.build_commit(run_id=run_id, step="probe:2",
                                                    operation="replan")
    assert first is not None and second is None
    assert h.git(repo, "rev-parse", "HEAD") == head


def _first_request(repo: Path) -> dict[str, Any]:
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0, payload
    return payload["request"]


def test_a_foreign_delivery_edit_is_refused_by_next_and_report(tmp_path: Path) -> None:
    repo, _ws, _run = _started(tmp_path)
    controller = h.Controller(repo, tmp_path / "effects.log")
    request = _first_request(repo)
    result = controller.work(request)
    approvals = repo / SPEC / "delivery" / "approvals.jsonl"
    approvals.write_text(approvals.read_text("utf-8").replace("owner", "forged"), "utf-8")
    head = h.git(repo, "rev-parse", "HEAD")
    code, refused = h.run_cli(repo, "next", SPEC)
    assert code == 1 and refused["refusal"]["code"] == "foreign-delivery-edit"
    code, refused = controller.report(result)
    assert code == 1 and refused["refusal"]["code"] == "foreign-delivery-edit"
    assert h.git(repo, "rev-parse", "HEAD") == head


def test_a_lagging_delivery_copy_is_rewritten_from_head(tmp_path: Path) -> None:
    repo, ws, _run = _started(tmp_path)
    approvals = repo / SPEC / "delivery" / "approvals.jsonl"
    committed = approvals.read_bytes()
    approvals.write_bytes(committed[: len(committed) // 2])
    _first_request(repo)
    assert approvals.read_bytes() == committed


def test_a_git_failure_is_one_json_refusal(tmp_path: Path) -> None:
    repo, _ws, _run = _started(tmp_path)
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/missing\n", "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1
    assert payload["refusal"]["code"] == "denied-git-failed"
    assert payload["refusal"]["owner"] == "controller"


def test_a_malformed_record_is_one_json_refusal(tmp_path: Path) -> None:
    repo, _ws, _run = _started(tmp_path)
    approvals = repo / SPEC / "delivery" / "approvals.jsonl"
    approvals.write_text('{"run_id": "run-0000000000000000"}\n', "utf-8")
    h.git(repo, "commit", "-qam", "damage the approval line")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "malformed-record"


def test_an_internal_fault_is_not_blamed_on_the_records(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ws, _run = _started(tmp_path)

    def broken(_ws: Any) -> dict[str, Any]:
        return {}["missing"]

    monkeypatch.setattr(h.loop, "next_request", broken)
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1
    assert payload["refusal"]["code"] == "internal-error"
    assert "test_supervisor_commit.py:" in payload["refusal"]["detail"]


def test_status_check_prints_its_view(tmp_path: Path) -> None:
    repo, _ws, _run = _started(tmp_path)
    code, payload = h.run_cli(repo, "status", SPEC, "--check")
    assert code == 0 and payload["run"]["stage"] in ("admitted", "implementing")


def test_returning_to_earlier_spec_content_is_a_new_replan(tmp_path: Path) -> None:
    repo, _ws, _run = _started(tmp_path)
    spec = repo / SPEC / "spec.md"
    original = spec.read_text("utf-8")
    for text in (original.replace("that answers.", "that answers fast."), original):
        spec.write_text(text, "utf-8")
        code, payload = h.run_cli(repo, "next", SPEC)
        assert code == 0 and payload["request"]["kind"] != "human-decision", payload
        assert h.git(repo, "status", "--porcelain", "--", f"{SPEC}/spec.md") == ""
    spec.write_text(original.replace("that answers.", "that answers fast."), "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and h.git(repo, "status", "--porcelain", "--", f"{SPEC}/spec.md") == ""
    subjects = h.git(repo, "log", "--format=%s").splitlines()
    assert sum("replan" in s for s in subjects) == 3


def test_run_json_records_a_refusal(tmp_path: Path) -> None:
    repo, _ws, _run = _started(tmp_path)
    spec = repo / SPEC / "spec.md"
    spec.write_text(spec.read_text("utf-8").replace("answers 42.", "answers 43."), "utf-8")
    h.run_cli(repo, "next", SPEC)
    run = json.loads((repo / SPEC / ".supervisor" / "run.json").read_text("utf-8"))
    assert run["refusal"]["code"] == "criteria-changed"


# ── red-proof safety and the run lock ───────────────────────────────────────

tdd = h.cli._supervisor("_supervisor_tdd.py")


def _refusal_code(call: Any) -> str:
    with pytest.raises(h.admission.Refusal) as info:
        call()
    return str(info.value.code)


def test_a_head_link_escaping_the_scratch_root_refuses_red_proof(tmp_path: Path) -> None:
    repo, ws, _run = _started(tmp_path)
    Path(repo / "escape").symlink_to("/etc/hosts")
    h.git(repo, "add", "escape")
    h.git(repo, "commit", "-q", "-m", "an escaping link")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    assert _refusal_code(lambda: tdd._scratch_tree(h.workspace(repo), scratch)) == (
        "red-proof-extraction-refused")


def test_scratch_extraction_needs_the_data_filter(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    repo, ws, _run = _started(tmp_path)
    monkeypatch.delattr(tarfile, "data_filter")
    assert _refusal_code(lambda: tdd._scratch_tree(ws, tmp_path)) == "red-proof-unsafe-extraction"


@pytest.mark.parametrize("linked", ["file", "parent"])
def test_an_overlay_write_never_follows_a_link(tmp_path: Path, linked: str) -> None:
    root = tmp_path / "scratch"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    if linked == "file":
        Path(root / "test_calc.py").symlink_to(outside / "target.py")
        rel = "test_calc.py"
    else:
        Path(root / "tests").symlink_to(outside)
        rel = "tests/test_calc.py"
    assert _refusal_code(lambda: tdd._write_inside(root, rel, b"x")) == "red-proof-link-refused"
    assert list(outside.iterdir()) == []


def test_a_held_run_lock_is_a_run_locked_refusal(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _ws, _run = _started(tmp_path)
    policy = h.admission.load_policy()
    monkeypatch.setattr(h.admission, "load_policy",
                        lambda: {**policy, "run_lock_timeout_seconds": 0.2})
    with h.workspace(repo).run_lock():
        code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "run-locked"


@pytest.mark.parametrize(("budget", "stale"), [(1800, 1800), (2400, 2400), (1800, 2000)])
def test_a_policy_whose_red_proof_outlasts_the_lock_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget: int, stale: int) -> None:
    policy = json.loads(h.admission._POLICY_PATH.read_text("utf-8"))
    policy.update({"red_proof_budget_seconds": budget, "run_lock_stale_seconds": stale})
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), "utf-8")
    monkeypatch.setattr(h.admission, "_POLICY_PATH", path)
    assert _refusal_code(h.admission.load_policy) == "invalid-policy"


def test_an_oversized_event_log_does_not_stop_next(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo, _ws, _run = _started(tmp_path)
    limit = h.cli._supervisor("_supervisor_journal.py")._MAX_LOCAL_BYTES
    with (repo / ".loop-run" / "events.jsonl").open("ab") as events:
        events.truncate(limit + 1)  # sparse: past the read bound without writing it
    capsys.readouterr()
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and "request" in payload, payload
    assert ".loop-run/events.jsonl was not updated" in capsys.readouterr().err


@pytest.mark.skipif(not hasattr(os, "geteuid") or os.geteuid() == 0,
                    reason="needs a user that a read-only file stops")
def test_an_unwritable_event_log_changes_no_verb_outcome(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo, _ws, _run = _started(tmp_path)
    events = repo / ".loop-run" / "events.jsonl"
    events.chmod(0o444)
    capsys.readouterr()
    controller = h.Controller(repo, tmp_path / "effects.log")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and "request" in payload, payload
    code, admitted = controller.report(controller.work(payload["request"]))
    assert code == 0 and "admitted" in admitted, admitted
    assert ".loop-run/events.jsonl was not updated" in capsys.readouterr().err
