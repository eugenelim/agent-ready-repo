from __future__ import annotations

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "author-delivery-brief"
    / "SKILL.md"
)


def test_draft_completion_is_an_explicit_project_knowledge_non_gate() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Project-knowledge non-gate" in text
    section = text.split("## Project-knowledge non-gate", 1)[1]
    assert "Status: Draft" in section
    assert re.search(r"does not\s+call\s+`project-knowledge --capture`", section)
    assert "does not persist scratch" in section
    assert "`author-delivery-brief continue` owns the first stable gate" in section


def test_safe_incomplete_multi_slice_input_can_create_a_draft_with_named_gaps() -> None:
    normalized = " ".join(SKILL.read_text(encoding="utf-8").split())

    assert "Continue this skill only with the validated normalized envelope" in normalized
    assert "terminal confidentiality and redaction refusal" in normalized
    assert "intended multi-slice outcome is identifiable, or when the missing outcome is explicitly recorded as a blocking gap" in normalized
    assert "A safe source reference is required" in normalized
    assert "clearly name every missing field that a later Ready review must resolve" in normalized
    assert "including safe source provenance and a clearly labelled Ready-gaps note" in normalized


def test_draft_creation_requires_neither_appetite_nor_a_rabbit_hole() -> None:
    normalized = " ".join(SKILL.read_text(encoding="utf-8").split())

    assert "Offer, never require, readiness detail." in normalized
    assert "neither is required to create a Draft" in normalized
    assert "required for the DoR gate" not in normalized
    assert "Appetite is required to create a Draft" not in normalized
    assert "Insist on Outcome" not in normalized


def test_create_mode_never_stamps_ready() -> None:
    normalized = " ".join(SKILL.read_text(encoding="utf-8").split())

    assert "does not set `Status: Ready`" in normalized
    assert "continue is the only mode that sets `Status: Ready`" in normalized
    assert "Set `Status: Draft`" in normalized


def test_single_direct_light_change_does_not_create_a_brief() -> None:
    normalized = " ".join(SKILL.read_text(encoding="utf-8").split())

    assert "coherent multi-slice or cross-repository outcome" in normalized
    assert "rather than a single direct-light change" in normalized
    assert "Creating a brief for a single direct-light change is refused" in normalized
    assert "route a single change to `new-spec`" in normalized
