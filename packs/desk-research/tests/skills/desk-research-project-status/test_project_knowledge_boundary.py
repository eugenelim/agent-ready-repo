from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "desk-research-project-status"
    / "SKILL.md"
)


def test_project_status_is_a_read_only_knowledge_non_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")
    section = " ".join(text.split("## Project-knowledge non-gate", 1)[1].split())

    assert "status-only" in section
    assert "read-only" in section
    assert "no capture, distillation, or enquiry" in section
    assert "does not discover the project-knowledge provider" in section
    assert "does not create fallback storage" in section
    assert "does not persist its rendering context" in section
