"""Readiness and counts derive from durable facts (T6).

VI-4045 (AC-0022, AC-0023), VI-4046 (AC-0024, AC-0025), VI-4047 (AC-0034).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import supervisor_harness as h  # noqa: E402
import supervisor_support as sup  # noqa: E402

pytestmark = sup.INTEGRATION

SPEC = h.SPEC_DIR


def _until(repo: Path, controller: h.Controller, kind: str) -> dict[str, Any]:
    """Drive until the current request has *kind*; return it unreported."""
    for _ in range(60):
        code, payload = h.run_cli(repo, "next", SPEC)
        assert code == 0, payload
        request = payload["request"]
        if request["kind"] == kind:
            return request
        if request["kind"] == "external-effect":
            controller.handle_effect(request)
            continue
        code, admitted = controller.report(controller.work(request))
        assert code == 0, admitted
    raise AssertionError(f"no {kind} request")


def _status(repo: Path) -> dict[str, Any]:
    code, view = h.run_cli(repo, "status", SPEC, "--json")
    return view


def _forget_local_state(repo: Path) -> None:
    shutil.rmtree(repo / SPEC / ".supervisor", ignore_errors=True)
    shutil.rmtree(repo / ".loop-run", ignore_errors=True)


def _started(tmp_path: Path) -> tuple[Path, h.Controller]:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    return repo, h.Controller(repo, tmp_path / "effects.log")


# ── VI-4045: one fixture per Readiness row ───────────────────────────────────


def test_row_ready(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    assert controller.drive().get("terminal")
    view = _status(repo)
    assert view["readiness"]["ready"] is True
    assert set(view["readiness"]["criteria"].values()) == {"supported"}
    _forget_local_state(repo)
    assert _status(repo)["readiness"] == view["readiness"]


def test_row_criterion_insufficient_projects_evidence_work(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    request = _until(repo, controller, "run-gates")
    view = _status(repo)
    assert view["readiness"]["ready"] is False
    assert set(view["readiness"]["criteria"].values()) == {"insufficient"}
    assert view["request"]["kind"] == "run-gates" == request["kind"]
    _forget_local_state(repo)
    assert _status(repo)["readiness"] == view["readiness"]


def test_row_criterion_contradicted_projects_repair_work(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    request = _until(repo, controller, "run-gates")
    result = controller.work(request)
    result["criteria"][0]["outcome"] = "fail"
    result["gate"] = {"passed": False}
    assert controller.report(result)[0] == 0
    view = _status(repo)
    assert view["readiness"]["criteria"]["AC-0001"] == "contradicted"
    assert view["request"]["kind"] == "human-decision"
    assert view["request"]["reason"] == "criteria-unsupported"


def test_row_review_not_eligible_projects_review_work(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    _until(repo, controller, "review-role")
    view = _status(repo)
    assert set(view["readiness"]["criteria"].values()) == {"supported"}
    assert view["readiness"]["review"]["acceptance_eligible"] is False
    assert view["readiness"]["ready"] is False
    assert view["request"]["kind"] == "review-role"
    _forget_local_state(repo)
    assert _status(repo)["readiness"] == view["readiness"]


def test_row_no_pair_refuses(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "no-approval"


def test_row_envelope_mismatch_refuses_per_the_replan_table(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    assert controller.drive().get("terminal")
    spec = repo / SPEC / "spec.md"
    spec.write_text(spec.read_text("utf-8").replace("no user interface.", "an interface."),
                    "utf-8")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "scope-changed"


def test_a_stored_verdict_or_readiness_answer_is_not_read(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    _until(repo, controller, "run-gates")
    before = _status(repo)["readiness"]
    forged = {"schema_version": 1, "evaluation_fingerprint": "forged", "verdict": "supported",
              "criteria_refs": ["AC-0001", "AC-0002"], "receipt_refs": [], "ready": True,
              "acceptance_eligible": True}
    (repo / SPEC / "delivery" / "verdicts.json").write_text(json.dumps(forged), "utf-8")
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "forge a stored verdict")
    after = _status(repo)["readiness"]
    assert after["ready"] is False
    assert after["criteria"] == before["criteria"]


def test_no_stored_verdict_or_readiness_answer_exists(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    assert controller.drive().get("terminal")
    delivery = b"".join(p.read_bytes() for p in (repo / SPEC / "delivery").iterdir())
    for marker in (b"evaluation_fingerprint", b"acceptance_eligible", b'"verdict"', b'"ready"'):
        assert marker not in delivery


# ── VI-4046: the retry cap and status --check exit codes ─────────────────────


class AlwaysFails(h.Controller):
    def work(self, request: dict[str, Any]) -> dict[str, Any]:
        result = super().work(request)
        if request["kind"] == "implement-task" and request["task"]["title"].startswith("Plain"):
            result["gate"] = {"passed": False}
        return result


def _check(repo: Path) -> int:
    return h.run_cli(repo, "status", SPEC, "--check")[0]


def _fail_plain(repo: Path, controller: h.Controller, times: int) -> None:
    for _ in range(times):
        request = _until(repo, controller, "implement-task")
        while not request["task"]["title"].startswith("Plain"):
            assert controller.report(controller.work(request))[0] == 0
            request = _until(repo, controller, "implement-task")
        assert controller.report(controller.work(request))[1]["admitted"] == "gate-fail"


def test_cap_fires_at_the_count_and_survives_journal_deletion(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = AlwaysFails(repo, tmp_path / "effects.log")
    _fail_plain(repo, controller, 4)
    assert _status(repo)["retry_count"] == 4 and _check(repo) == 0
    _forget_local_state(repo)
    assert _check(repo) == 0
    _fail_plain(repo, controller, 1)
    assert _status(repo)["retry_count"] == 5 and _check(repo) == 3
    _forget_local_state(repo)
    assert _check(repo) == 3
    code, payload = h.run_cli(repo, "next", SPEC)
    assert payload["request"]["kind"] == "human-decision"
    assert payload["request"]["reason"] == "retry-cap"


def test_cap_counts_across_a_split(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = AlwaysFails(repo, tmp_path / "effects.log")
    _fail_plain(repo, controller, 4)
    split = sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](),
                     sup.task("T3", "Plain note is drafted", touches="`plain.txt`"),
                     sup.task("T4", "Plain note is finished", touches="`plain.txt`"))
    (repo / SPEC / "plan.md").write_text(split, "utf-8")
    h.run_cli(repo, "next", SPEC)
    assert _status(repo)["retry_count"] == 4 and _check(repo) == 0


def test_refusal_exits_1_and_the_cap_wins_over_it(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = AlwaysFails(repo, tmp_path / "effects.log")
    spec = repo / SPEC / "spec.md"
    original = spec.read_text("utf-8")
    spec.write_text(original.replace("answers 42.", "answers 43."), "utf-8")
    assert _check(repo) == 1
    spec.write_text(original, "utf-8")
    _fail_plain(repo, controller, 5)
    spec.write_text(original.replace("answers 42.", "answers 43."), "utf-8")
    assert _check(repo) == 3


def test_usage_error_exits_2_and_a_terminal_run_exits_0(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    assert h.run_cli(repo, "status", "docs/specs/missing", "--check")[0] == 2
    assert h.run_cli(repo, "status", SPEC, "--bogus")[0] == 2
    assert controller.drive().get("terminal")
    assert _check(repo) == 0


# ── VI-4047: Slice 3's replay reads the supervisor's evidence log ────────────


def test_replay_admitted_frames_returns_every_frame_the_run_wrote(tmp_path: Path) -> None:
    repo, controller = _started(tmp_path)
    assert controller.drive().get("terminal")
    raw = (repo / SPEC / "delivery" / "evidence.jsonl").read_bytes()
    es = h.loop.sibling("_evidence_store.py")
    frames = es.replay_admitted_frames(raw)["frames"]
    written = [json.loads(line) for line in raw.splitlines()]
    assert len(frames) == len(written) > 0
    assert [tx["transaction_id"] for tx, _ in frames] == [w["tx"]["transaction_id"]
                                                         for w in written]
    kinds = {r.get("observation", {}).get("type") for _tx, records in frames for r in records}
    assert {"red", "task-gate", "gate", "terminal"} <= kinds
