"""Roster coverage for the work-intake drain procedure section (§ 8).

Spec: ``docs/specs/work-item-promotion-handoff`` — task T7. The section must
state the attended rule (every route and closure confirmed; an unattended
drain reports and holds, writing no disposition), the disposition-last
ordering with its recovery, and route through the existing classify and
transaction seams while registering nothing — readable without the spec.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-intake" / "SKILL.md"


def _drain_section() -> str:
    """The § 8 section, with runs of whitespace collapsed so line wrapping
    does not change what the text asserts."""
    text = SKILL.read_text(encoding="utf-8")
    start = text.index("### 8. Drain captured work items")
    end = text.index("## Boundaries", start)
    return " ".join(text[start:end].split())


def test_section_states_the_attended_rule() -> None:
    section = _drain_section()
    assert "Every route and every closure is attended" in section
    assert "the operator confirms each item's disposition before any effect" in section
    assert "reports the offers and holds every item" in section
    assert "records no terminal disposition" in section


def test_section_states_the_disposition_last_ordering_and_recovery() -> None:
    section = _drain_section()
    assert "The terminal disposition is written only after every effect" in section
    assert "A crash at any point ahead of the disposition leaves the capture open" in section
    assert "without a second artifact or a second terminal event" in section
    assert "a held item records nothing" in section


def test_section_routes_through_the_existing_seams_and_registers_nothing() -> None:
    section = _drain_section()
    assert "promotion_drain.py" in section
    assert "scripts/intake_transaction.py" in section
    assert "§ 4 table" in section
    assert "The drain registers nothing" in section
    assert "workspace.toml" in section
