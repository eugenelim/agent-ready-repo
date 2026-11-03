"""workspace-status suggests no first-in-list work item.

Verification mode: goal-based check. The skill keeps no Next-actions section,
because it answers only the repair; these tests read the source `SKILL.md`.
"""
from __future__ import annotations

from pathlib import Path

_SKILL = Path(__file__).resolve().parents[3] / ".apm/skills/workspace-status/SKILL.md"


def _text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def test_ac0001_no_first_in_list_suggestions() -> None:
    """Neither first-in-list suggestion, nor a Next-actions section, remains."""
    assert "next_queue" not in _text()
    assert "next_shape" not in _text()
    assert "### Next-actions" not in _text()
