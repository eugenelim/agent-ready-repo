from __future__ import annotations

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "new-spec"
    / "SKILL.md"
)


def test_draft_spec_and_plan_are_explicit_project_knowledge_non_gates() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Project-knowledge non-gate" in text
    section = text.split("## Project-knowledge non-gate", 1)[1]
    assert "Status: Draft" in section
    assert "Status: Drafting" in section
    assert re.search(r"does not\s+call\s+`project-knowledge --capture`", section)
    assert "does not persist scratch" in section
    assert re.search(
        r"`work-loop`\s+owns\s+`spec-approved`\s+and\s+`plan-locked`",
        section,
    )
