from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "desk-research-project-digest"
    / "SKILL.md"
)


def test_project_digest_is_an_intermediate_knowledge_non_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")
    section = " ".join(text.split("## Project-knowledge non-gate", 1)[1].split())

    assert "intermediate" in section
    assert "synthesis-matrix.md" in section
    assert "memos.md" in section
    assert "no capture, distillation, or enquiry" in section
    assert "partial, complete, stale, skipped, or interrupted" in section
    assert "does not locate journals" in section
    assert "does not create fallback storage" in section
    assert "never mines transcripts or copies raw source corpora" in section
