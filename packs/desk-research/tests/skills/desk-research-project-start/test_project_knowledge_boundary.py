from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "desk-research-project-start"
    / "SKILL.md"
)


def test_project_start_is_a_scaffold_only_knowledge_non_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")
    section = " ".join(text.split("## Project-knowledge non-gate", 1)[1].split())

    assert "scaffold-only" in section
    assert "project folder" in section
    assert "overview.md" in section
    assert "sources/" in section
    assert "no capture, distillation, or enquiry" in section
    assert "does not discover the project-knowledge provider" in section
    assert "creates no fallback file" in section
    assert "does not persist transient scratch" in section
    assert "does not change output-directory resolution" in section
