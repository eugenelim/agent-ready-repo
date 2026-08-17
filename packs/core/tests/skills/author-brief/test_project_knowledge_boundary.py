from __future__ import annotations

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "author-brief"
    / "SKILL.md"
)


def test_draft_completion_is_an_explicit_project_knowledge_non_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Project-knowledge non-gate" in text
    section = text.split("## Project-knowledge non-gate", 1)[1]
    assert "Status: Draft" in section
    assert re.search(r"does not\s+call\s+`project-knowledge --capture`", section)
    assert "does not persist scratch" in section
    assert "`receive-brief` owns the first stable gate" in section
