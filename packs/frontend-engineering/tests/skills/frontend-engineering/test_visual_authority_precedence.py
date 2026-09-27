"""The precedence rule: its shape, its bindings, and what it must not name.

Every assertion reads the rule tables rather than restating them, so changing
a rule moves `references/visual-observation.md` and not this file.
"""

from __future__ import annotations

import re

import pytest
from frontend_engineering_visual_authority_rules import (
    ANCHOR_ROOTS,
    OBSERVATION,
    SKILL,
    STRANDED_ROOTS,
    observation_rows,
    observation_table,
)

RUNGS = [
    "approved-visual-target",
    "direction-and-taxonomy",
    "incumbent-system",
    "local-premise",
]
LIMITS = [
    "product-behaviour",
    "accessibility",
    "content-correctness",
    "data-and-state",
    "security",
    "component-contracts",
    "platform-constraints",
]
READ_PATHS = ("direction/<slug>.md", "screens/<slug>/<screen>.md", "tokens/<slug>.md")
# Identifiers that would name an upstream producer. Naming one would make the
# rule depend on a particular writing tool rather than on the addresses.
UPSTREAM_IDENTIFIERS = ("experience-design", "creative-direction", "design-system")
# Enum members owned by an upstream template. Banned as rule-cell VALUES only:
# ordinary prose such as "the selected viewport" stays legal.
UPSTREAM_ENUM = ("proposed", "selected")
ANCHORS = ("Linear", "Stripe", "Vercel", "Raycast", "Arc", "Notion", "Toss")
STRANDED = ("canonical set", "canonical product-reference set", "canonical reference set")

SWEPT_SUFFIXES = {".md", ".json", ".toml", ".html", ".txt", ".css", ".js"}


def _shipped_files(roots=ANCHOR_ROOTS):
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in SWEPT_SUFFIXES:
                yield path


def test_the_precedence_table_fixes_the_rung_order() -> None:
    rows = observation_rows("Authority precedence")
    assert [row[0] for row in rows] == RUNGS


def test_every_rung_names_the_source_that_supplies_it() -> None:
    """Without this the table is four keys bound to nothing, and the claim
    that any tool writing the adopter's addresses satisfies the rule is
    unverified."""
    table = observation_table("Authority precedence")
    for rung in RUNGS[:2]:
        source = table[rung][1]
        assert any(path in source for path in READ_PATHS), (
            f"{rung} names no adopter read path; it reads {source!r}"
        )
    assert "repository" in table["incumbent-system"][1].lower()
    assert table["local-premise"][1].startswith("none")


def test_every_rung_carries_a_requires_and_a_falls_to_cell() -> None:
    table = observation_table("Authority precedence")
    for rung in RUNGS:
        assert table[rung][2].strip(), f"{rung} has an empty requires cell"
        assert table[rung][3].strip(), f"{rung} has an empty falls-to cell"


def test_the_top_rung_requires_a_recorded_confirmation() -> None:
    assert observation_table("Authority precedence")["approved-visual-target"][2] == (
        "recorded-human-confirmation"
    )


def test_each_rung_demotes_to_the_next_and_the_last_is_terminal() -> None:
    """Pins every demotion edge, not just the chain's ends: a cell naming no
    rung, or an upward demotion, reds here."""
    table = observation_table("Authority precedence")
    for rung, following in zip(RUNGS[:-1], RUNGS[1:], strict=True):
        assert table[rung][3] == following, (
            f"{rung} demotes to {table[rung][3]!r}, not {following!r}"
        )
    assert table["local-premise"][3] == "none — terminal"


def test_the_authority_limits_enumerate_what_it_never_controls() -> None:
    assert [row[0] for row in observation_rows("Authority limits")] == LIMITS


def test_the_reference_names_no_upstream_producer() -> None:
    """The rule is expressed over adopter-owned addresses. Naming a producer
    would make an independently installable pack depend on another one."""
    text = OBSERVATION.read_text(encoding="utf-8")
    found = [name for name in UPSTREAM_IDENTIFIERS if name in text]
    assert not found, f"the reference names an upstream producer: {found}"


def test_no_rule_cell_carries_an_upstream_enum_member() -> None:
    """Scoped to rule cells, not to the words. A rung keyed on a token owned by
    another pack's template goes wrong at that template's next edit, and no
    declared-dependency check can see it."""
    table = observation_table("Authority precedence")
    for rung in RUNGS:
        for column, cell in (("requires", table[rung][2]), ("falls-to", table[rung][3])):
            assert cell.strip().lower() not in UPSTREAM_ENUM, (
                f"{rung}'s {column} cell is the upstream enum member {cell!r}"
            )


@pytest.mark.parametrize("anchor", ANCHORS)
def test_no_shipped_file_names_an_aesthetic_anchor(anchor: str) -> None:
    """Case-sensitive, and scoped to this skill and the agent: a sibling skill
    legitimately says "linear interpolation", and this slice does not touch it."""
    pattern = re.compile(rf"\b{re.escape(anchor)}\b")
    hits = [str(f) for f in _shipped_files() if pattern.search(f.read_text(errors="ignore"))]
    assert not hits, f"{anchor!r} survives as an aesthetic anchor in {hits}"


@pytest.mark.parametrize("phrase", STRANDED)
def test_no_shipped_file_points_at_the_deleted_reference_set(phrase: str) -> None:
    """Case-insensitive and whitespace-normalized: one live pointer wrapped
    mid-phrase across a line break and one was a capitalised heading."""
    hits = []
    for f in _shipped_files(STRANDED_ROOTS):
        normalized = re.sub(r"\s+", " ", f.read_text(errors="ignore")).lower()
        if phrase in normalized:
            hits.append(str(f))
    assert not hits, f"{phrase!r} still points at the deleted set in {hits}"


def test_the_entrypoint_states_the_precedence_and_routes_to_the_reference() -> None:
    """The rules live in the reference; this asserts the always-loaded skill
    actually carries the contract and points at them.

    **Scoped to the PLAN pre-flight section**, not to the whole file. The
    evidence-manifest row further down lists all four rung keys in order as the
    field's vocabulary, so a whole-file search passes even with the pre-flight
    contract deleted — which is exactly the hole this assertion exists to
    close.
    """
    text = SKILL.read_text(encoding="utf-8")
    preflight = text.split("## PLAN phase", 1)[1].split("\n## ", 1)[0]
    positions = [preflight.find(rung) for rung in RUNGS]
    assert all(pos >= 0 for pos in positions), (
        f"the PLAN pre-flight is missing rung keys: "
        f"{[r for r, pos in zip(RUNGS, positions, strict=True) if pos < 0]}"
    )
    assert positions == sorted(positions), "the rungs are not in precedence order"
    assert "references/visual-observation.md" in preflight, (
        "the pre-flight does not route to the reference that holds its rules"
    )
