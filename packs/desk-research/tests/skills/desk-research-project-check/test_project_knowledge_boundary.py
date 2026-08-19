from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "desk-research-project-check"
    / "SKILL.md"
)


def test_project_check_is_a_check_only_knowledge_non_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")
    section = " ".join(text.split("## Project-knowledge non-gate", 1)[1].split())

    assert "check-only" in section
    assert "optional `verdict_status`" in section
    assert "desk-research-owned" in section
    assert "no capture, distillation, or enquiry" in section
    assert "never advances `phase`" in section
    assert "human owns the decision" in section
    assert "does not create fallback storage" in section
