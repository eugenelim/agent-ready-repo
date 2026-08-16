from __future__ import annotations

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
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
