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
PRE_APPROVAL_BOUND = "corrects in place only\n> before approval"
COMPLETION_GATE_CLAIM = "`Touches`, `Tests` and `Done when` are what a\n> completion gate reads, and they are pinned."
LEDGER_ROUTE = "`no stub (implementation-discovered)` goes to the\n> verification ledger"
AMENDMENT_ROUTE = "settled design decision that execution falsified is a\n> plan error that follows the controlled-amendment procedure"


def _working_material_paragraph(text: str) -> str:
    """Return the template's working-material blockquote paragraph."""
    paragraph = WORKING_MATERIAL.search(text)
    assert paragraph is not None, "plan template must retain its working-material paragraph"
    return paragraph.group(0)


def _assert_working_material_lifecycle(text: str) -> None:
    """Assert the lifecycle boundary and post-approval routes stay explicit."""
    paragraph = _working_material_paragraph(text)

    assert PRE_APPROVAL_BOUND in paragraph
    assert COMPLETION_GATE_CLAIM in paragraph
    assert LEDGER_ROUTE in paragraph
    assert AMENDMENT_ROUTE in paragraph


def test_working_material_is_bounded_before_approval() -> None:
    _assert_working_material_lifecycle(PLAN_ASSET.read_text(encoding="utf-8"))


def test_working_material_rejects_removing_the_pre_approval_bound() -> None:
    text = PLAN_ASSET.read_text(encoding="utf-8")
    mutated = text.replace(" only\n> before approval", "", 1)

    with pytest.raises(AssertionError):
        _assert_working_material_lifecycle(mutated)
