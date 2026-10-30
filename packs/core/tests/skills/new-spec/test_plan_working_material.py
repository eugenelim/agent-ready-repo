"""Working-material lifecycle contracts for the new-spec plan template."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
PLAN_ASSET = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"

WORKING_MATERIAL = re.compile(
    r"^> \*\*Not every field is contract\.\*\*(?P<body>.*?)(?=^\s*$)",
    re.MULTILINE | re.DOTALL,
)
# Flattened: the paragraph is a blockquote wrapped at 80 columns.
WORKING_MATERIAL_BOUND = "the controller corrects in place, before or after approval, while no attempt is open"
COMPLETION_GATE_CLAIM = "`Touches`, `Tests` and `Done when` are what a completion gate reads."
DESIGN_ROUTE = "is a controller edit of the plan's `## Design (LLD)`, never a ledger line"
AMENDMENT_ROUTE = "settled design decision that execution falsified is a plan error the owner agrees to, corrected the same way unless it reaches a protected section"


def _flatten(paragraph: str) -> str:
    """Drop blockquote markers and collapse whitespace."""
    return " ".join(re.sub(r"^>[ ]?", "", paragraph, flags=re.MULTILINE).split())


def _working_material_paragraph(text: str) -> str:
    """Return the template's working-material blockquote paragraph."""
    paragraph = WORKING_MATERIAL.search(text)
    assert paragraph is not None, "plan template must retain its working-material paragraph"
    return paragraph.group(0)


def _assert_working_material_lifecycle(text: str) -> None:
    """Assert the working-material bound and its post-approval routes stay explicit."""
    paragraph = _flatten(_working_material_paragraph(text))

    assert WORKING_MATERIAL_BOUND in paragraph
    assert COMPLETION_GATE_CLAIM in paragraph
    assert DESIGN_ROUTE in paragraph
    assert AMENDMENT_ROUTE in paragraph
    assert "goes to the verification ledger" not in paragraph


def test_working_material_is_bounded_by_the_open_attempt() -> None:
    _assert_working_material_lifecycle(PLAN_ASSET.read_text(encoding="utf-8"))


def test_working_material_rejects_removing_the_open_attempt_bound() -> None:
    text = PLAN_ASSET.read_text(encoding="utf-8")
    mutated = text.replace("while no\n> attempt is open", "at any time", 1)
    assert mutated != text

    with pytest.raises(AssertionError):
        _assert_working_material_lifecycle(mutated)
