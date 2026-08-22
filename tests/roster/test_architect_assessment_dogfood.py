"""Contract checks for the guide-driven architecture assessment captures."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOGFOOD = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "architect-assessment"
    / "notes"
    / "guide-driven-dogfood.md"
)


def test_generic_prompt_runs_cover_three_shapes_and_enterprise_modes() -> None:
    text = DOGFOOD.read_text(encoding="utf-8")
    assert text.count("Assess architecture and provide an action plan") >= 1
    for shape in (
        "small Python library",
        "layered web/worker application",
        "agentic knowledge platform",
    ):
        assert shape in text
    for enterprise_mode in (
        "none detected",
        "in-repo `docs/architecture/reference.md`",
        "authorized connector-shaped fixture",
    ):
        assert enterprise_mode in text


def test_each_capture_preserves_method_and_evidence_boundaries() -> None:
    text = DOGFOOD.read_text(encoding="utf-8")
    assert text.count("Map checkpoint correction") == 3
    assert text.count("Focus checkpoint correction") == 3
    assert text.count("Attention heat map") == 3
    assert text.count("### Action waves") == 3
    assert "Target evidence" in text
    assert "Enterprise context" in text
    assert "Pack knowledge" in text
    assert "does not prove a defect" in text
    assert "What remains documented but not exercised" in text
