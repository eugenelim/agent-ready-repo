"""The commit builder's guards and the CLI's refusal contract.

The HEAD compare-and-swap and the step-id skip, foreign `delivery/` edits,
Git failures surfacing as one JSON refusal, and a replan that returns to
earlier content.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import supervisor_harness as h  # noqa: E402

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
