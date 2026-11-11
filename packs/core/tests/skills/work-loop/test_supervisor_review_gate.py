"""The reviewer-selection exchange and the reselect-review decision through a real run (T2).

VI-6012 (AC-0009, AC-0010, AC-0011) and VI-6013 (AC-0021): a git-backed fixture
run asks for a selection, commits it as a `review` step, reaches
`review-not-eligible` through a supported finding left open, refuses a
non-owner `reselect-review`, admits the owner's, and asks again. The pure
resolver cases are in ``test_supervisor_review.py``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

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
review = h.cli._supervisor("_supervisor_review.py")

pytestmark = sup.INTEGRATION

SPEC = h.SPEC_DIR
OWNER = "owner:0123456789ab"
RISK_OWNER = "risk-owner:0123456789ab"


def _until_review(repo: Path, controller: h.Controller) -> dict[str, Any]:
    """Drive the tasks and gates; return the first review-role request, unreported."""
    for _ in range(60):
        code, payload = h.run_cli(repo, "next", SPEC)
        assert code == 0, payload
        request = payload["request"]
        if request["kind"] == "review-role":
            return request
        if request["kind"] == "external-effect":
            controller.handle_effect(request)
            continue
        code, admitted = controller.report(controller.work(request))
        assert code == 0, admitted
    raise AssertionError("no review-role request")


def _next(repo: Path) -> dict[str, Any]:
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0, payload
    return payload["request"]


def _result(request: dict[str, Any], **fields: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": request["kind"],
        **fields,
    }


def _last_commit(repo: Path) -> tuple[str, str]:
    message = h.git(repo, "log", "-1", "--format=%B")
    operation = next(
        line.split(": ", 1)[1]
        for line in message.splitlines()
        if line.startswith("Supervisor-Operation: ")
    )
    return operation, h.git(repo, "show", "HEAD", "--stat", "--format=")


def test_vi6012_vi6013_selection_then_reselection_through_a_run(tmp_path: Path) -> None:
    """VI-6012 and VI-6013: the selection request, its commit, and the reselection path."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")

    # VI-6013: no record for the current key yields the selection request, with no role.
    selection_request = _until_review(repo, controller)
    assert "role" not in selection_request
    assert selection_request["candidates"] == review.candidates(review.load_rules())
    key = selection_request["selection_key"]
    assert selection_request["request_id"] == f"select:{key[:24]}:1"

    # AC-0011: the selection commits as a `review` step that appends the record file.
    selection = h.select_none(selection_request)
    code, admitted = controller.report(_result(selection_request, selection=selection))
    assert code == 0, admitted
    operation, stat = _last_commit(repo)
    assert operation == "review" and "review-selections.jsonl" in stat
    written = json.loads(
        h.git(repo, "show", f"HEAD:{SPEC}/delivery/review-selections.jsonl").splitlines()[0]
    )
    assert written["selection_key"] == key and written["selected"] == []

    # The answered selection request is no longer current.
    code, stale = controller.report(_result(selection_request, selection=selection))
    assert code == 1 and stale["refusal"]["code"] == "not-current-attempt"

    # The resolved policy replaces the static one: adversarial-reviewer, mandatory.
    role_request = _next(repo)
    assert role_request["role"] == "adversarial-reviewer" and "candidates" not in role_request
    first_fingerprint = role_request["review_subject"]["review_policy_fingerprint"]
    code, view = h.run_cli(repo, "status", SPEC, "--json")
    assert view["readiness"]["selection"]["required"] is False

    # A supported material finding left open makes readiness ineligible.
    report = h.report_review("adversarial-reviewer", role_request["review_subject"], 1)
    report["findings"][0]["material"] = True
    assert controller.report(_result(role_request, report=report))[0] == 0
    assess = _next(repo)
    assert assess["kind"] == "assess-finding"
    supported = {**h.assessment(assess), "assessment": "supported"}
    assert controller.report(_result(assess, assessment=supported))[0] == 0
    decision_request = _next(repo)
    assert decision_request["kind"] == "human-decision"
    assert decision_request["reason"] == "review-not-eligible"
    assert "reselect-review" in decision_request["question"]
    assert decision_request["selection_key"] == key

    # A non-owner reselect-review, a wrong key, and another decision all refuse and write nothing.
    head = h.git(repo, "rev-parse", "HEAD")
    for answer in (
        {"decision": "reselect-review", "authority_ref": RISK_OWNER, "selection_key": key},
        {"decision": "reselect-review", "authority_ref": OWNER, "selection_key": "0" * 64},
        {"decision": "accept-risk", "authority_ref": OWNER, "finding_ids": ["finding-1"]},
    ):
        code, refused = controller.report(_result(decision_request, decision=answer))
        assert code == 1, answer
        assert refused["refusal"]["code"] in {"authority-refused", "invalid-result"}, refused
    assert h.git(repo, "rev-parse", "HEAD") == head

    # The owner's reselect-review is admitted as a `review` step.
    owner = {"decision": "reselect-review", "authority_ref": OWNER, "selection_key": key}
    code, admitted = controller.report(_result(decision_request, decision=owner))
    assert code == 0, admitted
    operation, stat = _last_commit(repo)
    assert operation == "review" and "review-decisions.jsonl" in stat

    # Readiness asks again, as selection number 2 for the same key.
    again = _next(repo)
    assert again["request_id"] == f"select:{key[:24]}:2" and again["selection_key"] == key
    assert "role" not in again
    chosen = h.select_none(again, selected=("experience-reviewer",))
    assert controller.report(_result(again, selection=chosen))[0] == 0

    # AC-0009: the new selection resolves to another fingerprint, so the subject changes.
    follow = _next(repo)
    assert follow["role"] == "adversarial-reviewer"
    second_fingerprint = follow["review_subject"]["review_policy_fingerprint"]
    assert second_fingerprint != first_fingerprint
    lines = h.git(repo, "show", f"HEAD:{SPEC}/delivery/review-selections.jsonl").splitlines()
    assert [json.loads(x)["sequence"] for x in lines] == [1, 2]
    assert json.loads(lines[1])["authorized_by"] == decision_request["request_id"]


def test_vi6013_a_rules_defect_stops_the_review_stage(tmp_path: Path, monkeypatch: Any) -> None:
    """VI-6013: with the rules file missing the run refuses review-rules-invalid and never closes."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    _until_review(repo, controller)
    monkeypatch.setattr(review, "RULES_PATH", tmp_path / "absent.json")
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 1 and payload["refusal"]["code"] == "review-rules-invalid"
    assert not payload.get("terminal")
