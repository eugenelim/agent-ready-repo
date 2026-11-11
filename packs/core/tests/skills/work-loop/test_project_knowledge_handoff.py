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
CAPTURE_REFERENCE = WORK_LOOP_SKILL.parent / "references" / "capture.md"

CORE_2_5_9_QUESTION_BYTES = (
    b"Before the PR is opened: *What would have made this work materially better \xe2\x80\x94\n"
    b"more correct, complete, reliable, recoverable, secure, privacy-preserving,\n"
    b"deterministic, reproducible, operable, maintainable, reviewable, efficient, or\n"
    b"independent of hidden context?*\n"
)


def _skill_text() -> str:
    return WORK_LOOP_SKILL.read_text(encoding="utf-8")


def closeout_question_bytes() -> bytes:
    """The closeout question, byte-exact, from wherever the skill keeps it.

    It lived in `SKILL.md` until the section that carried it exceeded the
    1000-line cap `tests/roster/test_wave4_durable_outputs_and_release.py`
    enforces. The writing guidance -- this question, the
    lesson-not-the-incident rule, and the semantic-gate routing -- moved to
    `references/capture.md`, which is the relocation that cap exists to
    encourage; `SKILL.md` keeps the routing and links the reference.

    The pin follows the prose rather than the prose coming back: this
    assertion is still byte-exact and still fails on any edit to the
    question. What changed is where it looks, not how strong it is.
    """
    raw = CAPTURE_REFERENCE.read_bytes()
    start = raw.index(b"Before the PR is opened:")
    end = raw.index(b"\n\nSpeed is one useful signal", start)
    return raw[start:end] + b"\n"


def test_work_loop_integration_names_no_capture_gate() -> None:
    text = _skill_text()
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "spec-approved" not in section
    assert "plan-locked" not in section
    assert "capture" not in section.lower()


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


def test_integration_uses_public_enquiry_only_producer_profile() -> None:
    """The profile owns only the enquiry envelope; no capture duty is listed."""
    text = _skill_text()
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "public `project-knowledge` producer profile" in section
    assert "It owns the enquiry envelope." in section
    assert "receipts" not in section
    assert "storage" not in section
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
    assert "journal diff" not in section


def test_work_loop_evals_drop_the_removed_capture_gates() -> None:
    """No eval tests, or expects, a spec-approved or plan-locked capture."""

    cases = {
        case["id"]: case
        for case in json.loads(WORK_LOOP_EVALS.read_text(encoding="utf-8"))["evals"]
    }
    assert "spec-approved-capture-only-boundary" not in cases
    assert "plan-locked-receipt-scoped-terminal-gate" not in cases
    resumption = json.dumps(cases["approved-without-start-resumption"])
    assert "plan-locked" not in resumption
    assert "capture" not in resumption
