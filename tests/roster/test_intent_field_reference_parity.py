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


# `| `Field` | tier | value |` — the third cell, for a named field. Uses the
# same tolerant spacing as ROW: a check that recognises only one spelling of a
# valid table row is a check the next author defeats by reformatting.
VALUE_CELL = re.compile(r"^\|\s*`([^`]+)`\s*\|[^|]*\|\s*(.+?)\s*\|\s*$", re.M)


def _value_cells(section: str, field: str) -> list[str]:
    """Every value cell documented for ``field``, in order.

    A list rather than one value on purpose: taking the first silently ignores
    a second row documenting something different.

    The field name is matched after the same ``.strip()`` ``_documented`` applies,
    not as a literal. A check that recognises one spelling of a name its own
    parser normalizes is a check the next author defeats with a space.
    """
    return [
        value
        for name, value in VALUE_CELL.findall(section)
        if name.strip() == field
    ]


def test_each_documented_field_has_exactly_one_row() -> None:
    """A duplicate row is a second answer, and readers get whichever they hit."""
    names = [
        name.strip()
        for name, _ in ROW.findall(_field_section(PAGE.read_text(encoding="utf-8")))
    ]
    duplicated = sorted({name for name in names if names.count(name) > 1})
    assert duplicated == [], duplicated


def test_the_supersession_and_lifecycle_records_carry_their_documented_tier() -> None:
    """Named rows, because the tier checks above cannot see these three.

    `Superseded by` is `unconstrained`, and direction-two exempts every
    unconstrained row by design — so deleting it leaves the rest of this file
    green. `Accepted` and `Fulfilled` are in `VALUE_RULES`, so direction-one
    catches their deletion but not a tier rewrite.
    """
    documented = _documented()

    assert documented.get("Superseded by") == UNCONSTRAINED
    for field in ("Accepted", "Fulfilled"):
        assert documented.get(field) == CONSTRAINED, field


def test_the_status_row_names_exactly_the_validators_vocabulary() -> None:
    """The one thing on this page a test can settle, settled exactly.

    Every backticked run in the value cell, compared as a set against the
    module. Not a membership check, which passes once a further token is
    documented; not a parse scoped to the first sentence, which passes once one
    is documented in the second; and not a character class, which passed
    `Draft2`. The cell is kept free of any backticked name that is not a member
    — the row names the pointer field in prose — so this needs no exclusion
    list and has nowhere left to hide.
    """
    shape = _load_validator()
    cells = _value_cells(_field_section(PAGE.read_text(encoding="utf-8")), "Status")
    assert len(cells) == 1, cells

    documented = set(re.findall(r"`([^`]+)`", cells[0]))
    assert documented == set(shape.STATUS_VALUES), documented ^ set(shape.STATUS_VALUES)
    assert "Superseded by <slug>" not in cells[0]


# ── What this file deliberately does not check ────────────────────────────────
#
# Whether each row's prose *describes its rule correctly* is not asserted here,
# and three rounds of trying is why. A keyword check cannot tell "resolution is
# one hop" from "resolution is not one hop", and every tightening moved the
# blind spot rather than closing it: a scoped parse, then a character class,
# then a literal row spelling. A predicate welded to prose has no convergent
# form, so asserting one produces a check that reads green while the page says
# the opposite of the contract.
#
# What is mechanizable lives above: which fields are documented, at which tier,
# with exactly one row each, and the `Status` vocabulary as an exact set derived
# from the module. Whether the prose is *true* is a human closeout condition,
# and the owning spec's Durable Outputs says so rather than pretending a test
# covers it.


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
