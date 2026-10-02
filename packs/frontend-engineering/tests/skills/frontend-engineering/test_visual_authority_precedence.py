"""The precedence rule: its shape, its bindings, and what it must not name.

Every assertion reads the rule tables rather than restating them, so changing
a rule moves `references/visual-observation.md` and not this file.
"""

from __future__ import annotations

import re

import pytest
from frontend_engineering_visual_authority_rules import (
    OBSERVATION,
    THIS_SKILL_AND_AGENTS,
    WHOLE_EXPORT_TREE,
    observation_rows,
    observation_table,
    preflight,
    read,
    rule,
    rule_table_headings,
    shipped_files,
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
UPSTREAM_IDENTIFIERS = ("experience-design", "creative-direction", "design-system")
UPSTREAM_ENUM = ("proposed", "selected")
ANCHORS = ("Linear", "Stripe", "Vercel", "Raycast", "Arc", "Notion", "Toss")
STRANDED = ("canonical set", "canonical product-reference set", "canonical reference set")
# Cells that name a rung condition. A rung keyed on another pack's template
# vocabulary goes wrong at that template's next edit, and no declared-dependency
# check can see it.
CONDITION_COLUMNS = ("requires", "falls to", "falls-to")


def test_the_precedence_table_fixes_the_rung_order() -> None:
    assert [row[0] for row in observation_rows("Authority precedence")] == RUNGS


def test_every_rung_names_the_source_that_supplies_it() -> None:
    """Without this the table is four keys bound to nothing, and the claim that
    any tool writing the adopter's addresses satisfies the rule is unverified."""
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
    assert rule("Authority precedence", "approved-visual-target") is not None
    assert observation_table("Authority precedence")["approved-visual-target"][2] == (
        "visual_target: confirmed"
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
    found = [name for name in UPSTREAM_IDENTIFIERS if name in read(OBSERVATION)]
    assert not found, f"the reference names an upstream producer: {found}"


def test_no_condition_cell_in_any_rule_table_carries_an_upstream_enum() -> None:
    """Driven from every rule table the reference states, not from one of them.

    The criterion says "any rule table". Checking only the precedence table is
    equivalent today and stops being equivalent the moment a later table adds a
    condition column — which would then arrive unguarded.
    """
    for heading in rule_table_headings():
        rows = observation_rows(heading)
        header = read(OBSERVATION).split(f"\n## {heading}\n", 1)[1]
        header_cells = [
            cell.strip().lower()
            for cell in next(
                line for line in header.splitlines() if line.strip().startswith("|")
            ).strip("|").split("|")
        ]
        for index, name in enumerate(header_cells):
            if name not in CONDITION_COLUMNS:
                continue
            for row in rows:
                if index < len(row):
                    assert row[index].strip().lower() not in UPSTREAM_ENUM, (
                        f"'## {heading}' row {row[0]!r} has a {name!r} cell "
                        f"carrying the upstream enum member {row[index]!r}"
                    )


@pytest.mark.parametrize("anchor", ANCHORS)
def test_no_shipped_file_names_an_aesthetic_anchor(anchor: str) -> None:
    """Case-sensitive, and scoped to this skill and the agent: a sibling skill
    legitimately says "linear interpolation"."""
    pattern = re.compile(rf"\b{re.escape(anchor)}\b")
    hits = [
        str(f) for f in shipped_files(THIS_SKILL_AND_AGENTS)
        if pattern.search(read(f))
    ]
    assert not hits, f"{anchor!r} survives as an aesthetic anchor in {hits}"


@pytest.mark.parametrize("phrase", STRANDED)
def test_no_shipped_file_points_at_the_deleted_reference_set(phrase: str) -> None:
    """Case-insensitive and whitespace-normalized across the whole export tree:
    one live pointer wrapped mid-phrase and one was a capitalised heading."""
    hits = [
        str(f) for f in shipped_files(WHOLE_EXPORT_TREE)
        if phrase in re.sub(r"\s+", " ", read(f)).lower()
    ]
    assert not hits, f"{phrase!r} still points at the deleted set in {hits}"


def test_the_preflight_states_the_precedence_and_routes_to_the_reference() -> None:
    """Scoped to the PLAN pre-flight, bounded at the first mode subsection.

    The evidence-manifest row further down lists all four rung keys in order as
    the field's vocabulary, so a whole-file search passes even with the
    pre-flight contract deleted — which is exactly the hole this closes.
    """
    window = preflight()
    positions = [window.find(rung) for rung in RUNGS]
    assert all(pos >= 0 for pos in positions), (
        f"the PLAN pre-flight is missing rung keys: "
        f"{[r for r, pos in zip(RUNGS, positions, strict=True) if pos < 0]}"
    )
    assert positions == sorted(positions), "the rungs are not in precedence order"
    assert OBSERVATION.name in window, (
        "the pre-flight does not route to the reference that holds its rules"
    )


def test_the_terminal_rung_carries_a_mechanism_not_a_reference_list() -> None:
    """The fallback must produce a different answer per surface.

    A shipped list of named references is a shared library, and shared
    libraries converge the work that uses them — which is the failure the whole
    precedence exists to prevent. The check has to close both doors: a premise
    guessable from the category is a default, and so is one guessable from the
    category plus the obvious reaction against it. Deriving the premise from the surface's own
    subject matter, then testing it against what any similar brief would have
    produced, yields a different answer by construction. It cannot become a
    default because it ships no default.
    """
    rung = preflight().split("**`local-premise`**", 1)[1].split("\n\n", 1)[0].lower()
    assert "subject matter" in rung, (
        "the terminal rung does not say where a premise comes from, so it has "
        "no way to differ between surfaces"
    )
    assert "category alone" in rung, (
        "the terminal rung has no check against the category's default premise"
    )
    assert "reaction against it" in rung, (
        "the check catches the category default but not the predictable "
        "reaction to it — and an anti-default becomes its own default, which "
        "is how the obvious escape routes got used up"
    )
    assert "never a product" in rung


def test_the_top_rung_requires_a_confirmed_visual_target() -> None:
    # OBSERVATION, not VISUAL_OBSERVATION: this module imports the former from
    # frontend_engineering_visual_authority_rules. The latter is defined only in
    # the sibling test_visual_authority_slice_two.py and would raise NameError
    # here — a red indistinguishable from a criterion failure.
    text = read(OBSERVATION)
    row = next(
        line
        for line in text.splitlines()
        if line.strip().startswith("| approved-visual-target")
    )
    assert "visual_target: confirmed" in row, "AC-0001"
    for identifier in UPSTREAM_IDENTIFIERS:
        assert identifier not in text, f"AC-0002: {identifier}"
