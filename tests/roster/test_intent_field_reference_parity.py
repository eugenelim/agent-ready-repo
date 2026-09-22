"""The adopter-facing field reference and the validator agree, both ways.

Covers T9's parity obligation in
`docs/specs/intent-metadata-shape-contract/plan.md`. It reads `guides/` and
`packs/core/`, so it is a repository-level assertion and lives here per
`tests/AGENTS.md`.

One direction alone is not enough. Checking only that the page covers the
validator lets a deleted field leave a stale row behind; checking only that
every row is real lets a new field ship undocumented. The page's own tier
column is the comparand, so a field that moves between tiers fails here rather
than drifting quietly.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (
    ROOT
    / "guides"
    / "product-engineering"
    / "reference"
    / "intent-fields-and-modes.md"
)
VALIDATOR = (
    ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intent_shape.py"
)

REQUIRED = "required"
CONSTRAINED = "constrained when present"
UNCONSTRAINED = "unconstrained"
RETIRED = "retired"

# `| `Field` | tier | value |` — the first cell is a backticked field name.
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|", re.M)


def _load_validator():
    name = "roster_intent_shape_parity"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR)
    assert spec and spec.loader, VALIDATOR
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _field_section(text: str) -> str:
    """The `## Intent fields` section only.

    Bounded so the body-section table below it, and the level-conditional
    tables further down, do not read as preamble-field rows.
    """
    start = text.index("## Intent fields")
    end = text.index("## Body sections", start)
    return text[start:end]


def _documented() -> dict[str, str]:
    rows = ROW.findall(_field_section(PAGE.read_text(encoding="utf-8")))
    documented = {name.strip(): tier.strip().lower() for name, tier in rows}
    assert documented, "no field rows parsed — the table shape changed"
    return documented


def _expected_tier(shape, field: str) -> str:
    if field in shape.REQUIRED_FIELDS:
        return REQUIRED
    if field in shape.VALUE_RULES:
        return CONSTRAINED
    if field in shape.RETIRED_FIELDS:
        return RETIRED
    return UNCONSTRAINED


def _decided(shape) -> set[str]:
    """Every field the validator decides on, by name."""
    return (
        set(shape.REQUIRED_FIELDS)
        | set(shape.VALUE_RULES)
        | set(shape.RETIRED_FIELDS)
        | set(shape.PROGRESS_FIELDS)
    )


def test_every_field_the_validator_decides_on_is_documented() -> None:
    """Direction one: a new field cannot ship undocumented."""
    shape = _load_validator()
    documented = _documented()

    missing = sorted(_decided(shape) - set(documented))
    assert missing == [], missing


def test_every_documented_field_row_is_one_the_validator_knows() -> None:
    """Direction two: a deleted field cannot leave a stale row.

    An `unconstrained` row is exempt, because the validator accepts an
    unrecognized name by design — that is what keeps an adopter's own field
    working, so such a row asserts no rule for the validator to hold.
    """
    shape = _load_validator()
    documented = _documented()
    decided = _decided(shape)

    orphans = sorted(
        field
        for field, tier in documented.items()
        if tier != UNCONSTRAINED and field not in decided
    )
    assert orphans == [], orphans


def test_every_documented_tier_matches_the_validator() -> None:
    """A field that moves between tiers fails here rather than drifting."""
    shape = _load_validator()
    documented = _documented()

    mismatched = {
        field: (tier, _expected_tier(shape, field))
        for field, tier in documented.items()
        if tier != _expected_tier(shape, field)
    }
    assert mismatched == {}, mismatched


def test_the_page_states_the_four_tiers() -> None:
    """The tier vocabulary is the page's own contract with its reader."""
    section = _field_section(PAGE.read_text(encoding="utf-8")).lower()
    for tier in (REQUIRED, CONSTRAINED, UNCONSTRAINED, RETIRED):
        assert tier in section, tier


def test_the_page_does_not_claim_only_two_fields_are_load_bearing() -> None:
    """The sentence this contract replaced, asserted absent.

    It said only Outcome and Opportunity were load-bearing and the rest were
    offered, never required. Four fields are now required, so leaving it would
    contradict the table directly above it.
    """
    text = PAGE.read_text(encoding="utf-8")
    assert "offered, never required" not in text
    assert "Only Outcome and Opportunity are load-bearing" not in text
