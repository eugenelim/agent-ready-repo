"""Content pins for work-loop's conditional preservation-evidence reference.

The reference's behavior is proved by graded runs; these pins catch a later edit
that drops a family, a rule, a citation, or the routing row.
"""

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm/skills/work-loop"
SKILL = SKILL_ROOT / "SKILL.md"
REFERENCE_NAME = "references/preservation-evidence.md"
REFERENCE = SKILL_ROOT / REFERENCE_NAME

RULES = (
    ("conservation family", "conservation"),
    ("equivalence family", "equivalence"),
    ("full and alternate construction", "full and incremental"),
    ("lifecycle family", "lifecycle"),
    ("compatibility family", "compatibility"),
    ("bounded work family", "bounded work"),
    ("failing mutation rule", "fails on a named mutation"),
    ("missing evidence", "missing"),
    ("stale evidence", "stale"),
    ("tautological evidence", "tautological"),
    ("feature-only evidence", "feature-only"),
    ("shared-substrate link", "](../../new-spec/references/shared-substrate-preservation.md)"),
    ("mutation-proof link", "](mutation-proof.md)"),
)


def _reference_text() -> str:
    """Read the reference, failing with a clear message when it is missing."""
    assert REFERENCE.is_file(), f"missing {REFERENCE_NAME}"
    return REFERENCE.read_text(encoding="utf-8")


def _routing_rows() -> list[str]:
    """Return the routing-table rows that link the reference."""
    text = SKILL.read_text(encoding="utf-8")
    section = text[text.index("## Conditional-reference routing") :]
    return [
        line
        for line in section.splitlines()
        if line.startswith("|") and f"]({REFERENCE_NAME})" in line
    ]


def test_routing_row_loads_the_reference() -> None:
    """Exactly one routing row links the reference, keyed on a preservation property."""
    rows = _routing_rows()
    assert len(rows) == 1
    predicate = rows[0].split("|")[1].lower()
    assert "preservation property" in predicate
    assert "accepted criteria" in predicate


@pytest.mark.parametrize(("rule", "phrase"), RULES, ids=[rule for rule, _ in RULES])
def test_reference_states_rule(rule: str, phrase: str) -> None:
    """Each family, rule, kind, or citation the reference owns is present."""
    assert phrase in " ".join(_reference_text().lower().split()) or phrase in _reference_text(), rule


def test_reference_carries_no_repository_only_paths() -> None:
    """Shipped guidance stays portable: no catalogue-internal docs paths."""
    assert not re.search(r"\bdocs/", _reference_text())
