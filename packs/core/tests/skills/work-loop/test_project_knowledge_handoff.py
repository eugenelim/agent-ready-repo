from __future__ import annotations

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
APPROVAL_GATES_REFERENCE = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "work-loop"
    / "references"
    / "project-knowledge-approval-gates.md"
)
PROJECT_KNOWLEDGE_SKILL = (
    PACK_ROOT / ".apm" / "skills" / "project-knowledge" / "SKILL.md"
)

CORE_2_5_9_QUESTION_BYTES = (
    b"Before the PR is opened: *What would have made this work materially better \xe2\x80\x94\n"
    b"more correct, complete, reliable, recoverable, secure, privacy-preserving,\n"
    b"deterministic, reproducible, operable, maintainable, reviewable, efficient, or\n"
    b"independent of hidden context?*\n"
)


def _skill_text() -> str:
    return WORK_LOOP_SKILL.read_text(encoding="utf-8")


def _approval_gates_text() -> str:
    skill = _skill_text()
    step_one = skill[skill.index("## Step 1. PLAN") : skill.index("## Step 2. EXECUTE")]
    assert (
        "[`references/project-knowledge-approval-gates.md`]"
        "(references/project-knowledge-approval-gates.md)" in step_one
    )
    return APPROVAL_GATES_REFERENCE.read_text(encoding="utf-8")


def closeout_question_bytes() -> bytes:
    raw = WORK_LOOP_SKILL.read_bytes()
    start = raw.index(b"Before the PR is opened:")
    end = raw.index(b"\n\nSpeed is one useful signal", start)
    return raw[start:end] + b"\n"


def test_ac22_work_loop_calls_capture_then_terminal_distill() -> None:
    text = _skill_text()
    capture = text.index("project-knowledge --capture")
    distill = text.index("project-knowledge --distill --pending", capture)
    assert capture < distill
    assert '"selection_mode":"workflow-receipts"' in text
    assert '"receipts":[{"capture_id":"<capture-id>","partition":' in text
    assert "receipt_ids" not in text
    assert "only the capture IDs and partitions returned by that gate" in text
    assert "direct-maintainer-pending" in text
    assert "must refuse guessed capture IDs" in text
    assert re.search(r"unresolved observations\s+remain\s+pending", text, re.IGNORECASE)


def test_ac28_missing_core_creates_no_fallback_file() -> None:
    text = _skill_text()
    assert "project-knowledge unavailable" in text
    assert "creates no fallback file" in text
    assert "patterns.jsonl" not in text
    assert "append-knowledge.py" not in text


def test_ac30_closeout_question_is_unchanged() -> None:
    assert closeout_question_bytes() == CORE_2_5_9_QUESTION_BYTES


def test_project_knowledge_skill_is_the_public_handoff_target() -> None:
    if not PROJECT_KNOWLEDGE_SKILL.exists():
        pytest.fail("project-knowledge skill is missing; work-loop cannot use the public seam")
    project_knowledge = PROJECT_KNOWLEDGE_SKILL.read_text(encoding="utf-8")
    assert "name: project-knowledge" in project_knowledge
    assert "--capture" in project_knowledge
    assert "--distill" in project_knowledge


def test_spec_and_plan_approval_gates_are_distinct_and_exact() -> None:
    text = _approval_gates_text()
    spec_gate = text.index("## `spec-approved`")
    plan_gate = text.index("## `plan-locked`")

    assert spec_gate < plan_gate
    spec_section = text[spec_gate:plan_gate]
    plan_section = text[plan_gate:]
    assert "capture only" in spec_section
    assert "must not transfer" in spec_section
    assert "workflow-receipts" in plan_section
    assert "only receipts returned at this `plan-locked` gate" in plan_section
    assert "spec-approved" in plan_section
    assert "direct-maintainer-pending" in plan_section


def test_approval_gate_requests_use_public_typed_capture_only() -> None:
    section = _approval_gates_text()

    for field in (
        "contract_version",
        "lesson",
        "kind",
        "project_scope",
        "competency_facets",
        "destination_hint",
        "producer",
        "semantic_gate",
        "provenance",
        "freshness_anchor",
        "observed_at",
        "privacy_attestation",
    ):
        assert f"`{field}`" in section
    assert "`semantic_gate.name: spec-approved`" in section
    assert "`semantic_gate.name: plan-locked`" in section
    assert "`producer.workflow_version`" in section
    assert "repository-relative `spec.md` as the artifact" in section
    assert "repository-relative `plan.md`" in section
    assert "project-knowledge unavailable" in section
    assert "no fallback file" in section
    assert "native real-path" in section
    assert "Git relocation variables removed" in section
    assert "lexical dot-segment" in section
    for refusal in ("link", "junction", "reparse-point", "non-file", "I/O", "containment uncertainty"):
        assert refusal in section
    assert "committed Git blob" in section
    assert "must not import the private writer" in section
    assert "redacted diagnostic" in section
    assert section.count("verification and review barrier") >= 2


def test_work_loop_declares_its_file_boundaries() -> None:
    text = _skill_text()
    assert re.search(r"boundaries:\s*\n\s*- filesystem_write", text)
    assert re.search(r"boundaries:[\s\S]*?- filesystem_read_untrusted", text)


def test_approval_gate_authority_and_enquiry_remain_bounded() -> None:
    section = _approval_gates_text()

    assert "objective, boundaries, testing strategy, or acceptance criteria" in section
    assert re.search(
        r"task\s+ordering,\s+design\s+choices,\s+rollout,\s+or\s+risks",
        section,
        re.IGNORECASE,
    )
    assert "No automatic enquiry" in section
    assert "CQ-CHANGE" in section
    assert "CQ-VERIFY" in section
    assert "one query plus at most one refinement" in section
    assert "untrusted evidence" in section
    assert re.search(
        r"cannot\s+change\s+tools,\s+permissions,\s+scope,\s+status,\s+or\s+repository\s+instructions",
        section,
    )
