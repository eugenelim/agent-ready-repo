from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
REVIEW_ENQUIRY_REFERENCE = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "work-loop"
    / "references"
    / "review-planning-enquiry.md"
)
EVALS = PACK_ROOT / ".apm" / "skills" / "work-loop" / "evals" / "evals.json"


def _review_enquiry_section() -> str:
    text = WORK_LOOP_SKILL.read_text(encoding="utf-8")
    assert "[its protocol](references/review-planning-enquiry.md)" in text
    return REVIEW_ENQUIRY_REFERENCE.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_review_enquiry_precedes_first_dispatch_and_reuses_one_envelope() -> None:
    text = WORK_LOOP_SKILL.read_text(encoding="utf-8")
    section = _flat(_review_enquiry_section())

    assert text.index("[its protocol](references/review-planning-enquiry.md)") < text.index(
        "select a subagent matching `adversarial-reviewer`"
    )
    assert '"caller":"skill"' in section
    assert '"question_id":"CQ-REVIEW"' in section
    assert '"risk":"consequential"' in section
    assert '"task_summary":"work-loop review:' in section
    assert '"scope":"<repository-relative project or subproject path>"' in section
    assert "one query and no refinement" in section
    assert "same delimited envelope" in section
    assert "materially changed target or review scope" in section
    assert "new explicit declaration" in section


def test_review_enquiry_has_named_degradation_and_no_write_fallback() -> None:
    section = _flat(_review_enquiry_section())

    assert "project-knowledge not requested" in section
    assert "project-knowledge unavailable" in section
    assert "zero candidate checks" in section
    assert "`abstained: true`" in section
    assert "creates no fallback file" in section
    assert "project-knowledge --enquire" in section
    assert "project-knowledge --capture" not in section
    assert "project-knowledge --distill" not in section
    assert "capture_id" not in section
    assert "selection_mode" not in section
    assert "workflow-receipts" not in section
    assert "direct-maintainer-pending" not in section


def test_review_enquiry_is_untrusted_and_cannot_change_review_authority() -> None:
    section = _flat(_review_enquiry_section())

    assert '<knowledge-evidence version="knowledge-evidence.v1">' in section
    assert "candidate checks only" in section
    for authority in (
        "instructions",
        "tool permissions",
        "review scope",
        "severity",
        "verdict",
        "suppress findings",
    ):
        assert authority in section
    assert "current review target" in section
    assert "governing rubric or checklist" in section
    assert "current canonical source" in section
    assert "cannot corroborate itself" in section


def test_review_enquiry_behavior_evals_cover_hostile_and_degraded_evidence() -> None:
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    evals = {entry["id"]: entry for entry in payload["evals"]}

    required = {
        "review-enquiry-relevant-candidate",
        "review-enquiry-unavailable-or-abstaining",
        "review-enquiry-hostile-authority-manipulation",
        "review-enquiry-misleading-counterclaim",
        "review-enquiry-rerun-budget",
    }
    assert required <= evals.keys()
    combined = json.dumps([evals[key] for key in sorted(required)]).lower()
    for behavior in (
        "prompt injection",
        "scope",
        "permission",
        "severity",
        "suppress",
        "self-validating",
        "misleading counterclaim",
        "stale",
        "quarantined",
    ):
        assert behavior in combined
