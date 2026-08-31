from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
PROJECT_KNOWLEDGE_SKILL = (
    PACK_ROOT / ".apm" / "skills" / "project-knowledge" / "SKILL.md"
)
WORK_LOOP_EVALS = WORK_LOOP_SKILL.parent / "evals" / "evals.json"

CORE_2_5_9_QUESTION_BYTES = (
    b"Before the PR is opened: *What would have made this work materially better \xe2\x80\x94\n"
    b"more correct, complete, reliable, recoverable, secure, privacy-preserving,\n"
    b"deterministic, reproducible, operable, maintainable, reviewable, efficient, or\n"
    b"independent of hidden context?*\n"
)


def _skill_text() -> str:
    return WORK_LOOP_SKILL.read_text(encoding="utf-8")


def closeout_question_bytes() -> bytes:
    raw = WORK_LOOP_SKILL.read_bytes()
    start = raw.index(b"Before the PR is opened:")
    end = raw.index(b"\n\nSpeed is one useful signal", start)
    return raw[start:end] + b"\n"


def test_work_loop_keeps_semantic_gate_boundaries() -> None:
    text = _skill_text()
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "spec-approved" in section
    assert "plan-locked" in section
    assert "capture" in section
    assert "Distil only receipts returned by this gate" in section


def test_ac28_missing_core_creates_no_fallback_file() -> None:
    text = _skill_text()
    assert "project-knowledge unavailable" in text
    assert "create no fallback file" in text
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
    text = _skill_text()
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "This gate captures but does not distil" in section
    assert "Normative scope, boundaries, tests, and acceptance criteria remain solely in `spec.md`" in section
    assert "Normative strategy remains solely in `plan.md`" in section


def test_approval_gate_uses_public_producer_profile() -> None:
    text = _skill_text()
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "public `project-knowledge` producer profile" in section
    assert "request shape, confinement, privacy refusal, freshness, receipts, storage" in section
    assert "project-knowledge unavailable" in section
    assert "create no fallback file" in section


def test_work_loop_declares_its_file_boundaries() -> None:
    text = _skill_text()
    assert re.search(r"boundaries:\s*\n\s*- filesystem_write", text)
    assert re.search(r"boundaries:[\s\S]*?- filesystem_read_untrusted", text)


def test_approval_gate_authority_and_enquiry_remain_bounded() -> None:
    text = _skill_text()
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "Project knowledge is never authority and enquiry is never automatic" in section
    # Review-time enquiry left the active work-loop in #1180, so this block must
    # not name CQ-REVIEW or the evidence envelope; the surviving enquiry gates
    # are CQ-CHANGE before scope approval and CQ-VERIFY at construction tests.
    assert "CQ-REVIEW" not in section
    assert "CQ-CHANGE" in section
    assert "CQ-VERIFY" in section
    assert "journal diff returns through the next applicable verification and review barrier" in section
    assert "a named no-diff outcome needs no extra review" in section


def test_work_loop_evals_retain_semantic_gate_sequences() -> None:
    """Keep semantic timing and receipt eligibility out of profile-only evals."""

    cases = {
        case["id"]: case
        for case in json.loads(WORK_LOOP_EVALS.read_text(encoding="utf-8"))["evals"]
    }
    spec = cases["spec-approved-capture-only-boundary"]
    plan = cases["plan-locked-receipt-scoped-terminal-gate"]
    assert "Status: Approved" in spec["prompt"]
    assert "successful spec-approved transition" in spec["expected_output"]
    assert "never distils" in spec["expected_output"]
    assert "stale-or-failed-baseline" in spec["expected_output"]
    assert "approve-plan seals an unchanged baseline" in plan["prompt"]
    assert "spec-approved receipts are ineligible" in plan["expected_output"]
    assert "stale or failed baseline seal" in plan["expected_output"]
