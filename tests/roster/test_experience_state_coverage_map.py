"""The shared state-coverage map is complete, total over the screen brief, and
never lets a tier drop an accessibility-bearing state.

Three artifacts have to agree and none of them can see the others:

* ``frontend-engineering/SKILL.md`` enumerates the eighteen states the frontend
  quality floor recognises.
* ``user-flow/assets/screen-brief-template.md`` carries the state lines a
  per-screen brief asks a designer to fill, in the design pack's own wording.
* The Digital Experience Contract carries the map that relates the two.

A reviewer cannot check completeness by eye without recounting eighteen rows
against eighteen table cells, which is the property this module exists to hold.

The accessibility assertion reads the flag the map *records*; it never judges
whether a state is accessibility-bearing. That is what makes the predicate
decidable — a wrong flag is a review finding, and a test that tried to judge
accessibility would be a test nobody could make green.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CONTRACT = (
    ROOT / "packs" / "frontend-engineering" / ".apm" / "skills"
    / "frontend-engineering" / "references" / "digital-experience-contract.md"
)
SKILL = (
    ROOT / "packs" / "frontend-engineering" / ".apm" / "skills"
    / "frontend-engineering" / "SKILL.md"
)
BRIEF = (
    ROOT / "packs" / "experience-design" / ".apm" / "skills" / "user-flow"
    / "assets" / "screen-brief-template.md"
)

TIER_BANDS = ("explore", "pilot", "production")
CONDITIONAL = "conditional"

# The one brief line that names two states. Recorded here rather than inferred:
# the map resolves it explicitly, and this constant is what makes the totality
# assertion able to say *which* line is allowed to resolve to more than one.
COMPOUND_BRIEF_LINE = "success/default"


def _rows(markdown: str, heading: str) -> list[list[str]]:
    """Return the body rows of the first Markdown table under *heading*."""
    after = markdown.split(heading, 1)
    assert len(after) == 2, f"{heading!r} is gone"
    rows: list[list[str]] = []
    seen_header = False
    for line in after[1].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    assert rows, f"no table body under {heading!r}"
    return rows


def _unbacktick(cell: str) -> str:
    return cell.strip().strip("`").strip()


def map_rows(contract: str) -> list[list[str]]:
    return _rows(contract, "#### Shared state-coverage map")


def floor_states(skill: str) -> list[str]:
    """The eighteen state names, read from the skill's own state matrix."""
    return [_unbacktick(r[0]) for r in _rows(skill, "### 3. State matrix")]


def brief_state_lines(brief: str) -> list[str]:
    """The state lines a per-screen brief carries, as the template words them."""
    section = brief.split("## States", 1)
    assert len(section) == 2, "the brief template has no States section"
    body = section[1].split("\n## ", 1)[0]
    lines = []
    for raw in body.splitlines():
        m = re.match(r"^- ([^:]+):", raw)
        if m:
            lines.append(m.group(1).strip())
    assert lines, "the brief template's States section lists no state lines"
    return lines


@pytest.fixture(scope="module")
def contract() -> str:
    return CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skill() -> str:
    return SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def brief() -> str:
    return BRIEF.read_text(encoding="utf-8")


# ── completeness ────────────────────────────────────────────────────────────


def test_the_map_covers_every_floor_state_exactly_once(
    contract: str, skill: str
) -> None:
    """Verifies: the map's state set equals the floor's, with no duplicates.

    Both halves matter and fail differently: a state added to the skill and not
    to the map is an unmapped state, and a state in the map that the skill
    dropped is a map that promises coverage of something that no longer exists.
    """
    mapped = [_unbacktick(r[0]) for r in map_rows(contract)]
    floor = floor_states(skill)

    duplicates = sorted({s for s in mapped if mapped.count(s) > 1})
    assert not duplicates, f"the map lists these states more than once: {duplicates}"

    missing = sorted(set(floor) - set(mapped))
    extra = sorted(set(mapped) - set(floor))
    assert not missing, f"the map does not cover: {missing}"
    assert not extra, f"the map covers states the quality floor does not name: {extra}"


def test_the_map_is_the_size_the_floor_states(contract: str, skill: str) -> None:
    """Verifies: eighteen rows for eighteen states.

    Asserted separately from set equality: two sets can match while the skill's
    own table has grown a duplicate row, which would make the floor's stated
    count wrong rather than the map's.
    """
    floor = floor_states(skill)
    assert len(floor) == 18, (
        f"the quality floor enumerates {len(floor)} states, not the eighteen "
        f"every artifact in this change names"
    )
    assert len(map_rows(contract)) == 18


# ── totality over the screen brief ──────────────────────────────────────────


def test_every_brief_state_line_resolves_in_the_map(
    contract: str, brief: str
) -> None:
    """Verifies: a designer filling a per-screen brief can find every line they
    are asked to fill somewhere in the map.

    Runs brief → map and never map → brief: a floor state with no brief
    counterpart is frontend-owned, which the map records with `-` rather than
    treating as a gap.
    """
    resolved = {
        _unbacktick(r[1]) for r in map_rows(contract) if _unbacktick(r[1]) != "-"
    }
    unresolved = [line for line in brief_state_lines(brief) if line not in resolved]
    assert not unresolved, (
        f"these screen-brief state lines resolve to no state in the map: "
        f"{unresolved}"
    )


def test_the_compound_brief_line_resolves_to_two_states(contract: str) -> None:
    """Verifies: the one line naming two states is mapped to both.

    The totality assertion above is satisfied by a single match, so without this
    the compound line could silently lose half its meaning.
    """
    carriers = [
        _unbacktick(r[0])
        for r in map_rows(contract)
        if _unbacktick(r[1]) == COMPOUND_BRIEF_LINE
    ]
    assert len(carriers) == 2, (
        f"`{COMPOUND_BRIEF_LINE}` names two states but the map resolves it to "
        f"{carriers}"
    )


# ── assignment ──────────────────────────────────────────────────────────────


def test_every_state_is_assigned_to_one_band_or_marked_conditional(
    contract: str,
) -> None:
    """Verifies: exactly one assignment per state, from a closed set."""
    allowed = {*TIER_BANDS, CONDITIONAL}
    wrong = {
        _unbacktick(r[0]): _unbacktick(r[2])
        for r in map_rows(contract)
        if _unbacktick(r[2]) not in allowed
    }
    assert not wrong, f"states assigned outside {sorted(allowed)}: {wrong}"


def test_every_band_carries_at_least_one_unconditional_state(
    contract: str,
) -> None:
    """Verifies: no tier is empty.

    An empty band is the signal that the partition is wrong, not that the
    criterion is — a ladder with a rung nobody stands on is not a ladder.
    """
    assigned = [_unbacktick(r[2]) for r in map_rows(contract)]
    empty = [band for band in TIER_BANDS if band not in assigned]
    assert not empty, f"these tier bands carry no unconditional state: {empty}"


def test_a_conditional_state_names_its_trigger(contract: str) -> None:
    """Verifies: `conditional` is never bare.

    A conditional assignment with no trigger is an unassigned state wearing a
    label, and it would pass the assignment check above.
    """
    untriggered = [
        _unbacktick(r[0])
        for r in map_rows(contract)
        if _unbacktick(r[2]) == CONDITIONAL and "Trigger:" not in r[4]
    ]
    assert not untriggered, (
        f"these states are conditional on nothing named: {untriggered}"
    )


# ── accessibility preservation ──────────────────────────────────────────────


def test_every_state_records_a_wcag_flag(contract: str) -> None:
    """Verifies: the flag the accessibility assertion reads is always present.

    Without this a missing flag reads as `no` to the assertion below, which is
    the fail-open shape that check exists to prevent.
    """
    unflagged = {
        _unbacktick(r[0]): r[3]
        for r in map_rows(contract)
        if _unbacktick(r[3]) not in {"yes", "no"}
    }
    assert not unflagged, (
        f"these states record no yes/no WCAG 2.2 AA flag: {unflagged}"
    )


def test_the_map_flags_at_least_one_accessibility_bearing_state(contract: str) -> None:
    """Verifies: the three accessibility assertions cannot go vacuous together.

    `test_every_state_records_a_wcag_flag` admits a column of all `no`, and the
    two assertions below it then filter on `yes` and iterate an empty set — so a
    map recording no accessibility-bearing state at all would satisfy every one
    of them. The sibling journey module has a non-emptiness guard, but the
    property belongs to this module, and a guard that lives somewhere else is a
    guard the next reader of this file will not find.
    """
    flagged = [r[0] for r in map_rows(contract) if r[3].strip().lower() == "yes"]
    assert flagged, (
        "no state in the map is flagged as failing WCAG 2.2 AA when absent; "
        "the accessibility assertions below would all pass over an empty set"
    )


def test_no_tier_drops_an_accessibility_bearing_state(contract: str) -> None:
    """Verifies: a state whose absence fails WCAG 2.2 AA is owed at every tier.

    Two assignments satisfy that. `explore` is the lowest band and the bands are
    cumulative, so an explore state is owed everywhere. A `conditional` state is
    owed at every tier its trigger reaches, which is the same guarantee for a
    state that only exists on some surfaces. Any other band means a cheaper tier
    may ship without it, which the repository treats as non-waivable.
    """
    dropped = {
        _unbacktick(r[0]): _unbacktick(r[2])
        for r in map_rows(contract)
        if _unbacktick(r[3]) == "yes"
        and _unbacktick(r[2]) not in {"explore", CONDITIONAL}
    }
    assert not dropped, (
        f"these states fail WCAG 2.2 AA when absent but are not owed until a "
        f"tier above explore: {dropped}"
    )


def test_an_accessibility_bearing_state_names_its_success_criterion(
    contract: str,
) -> None:
    """Verifies: a `yes` flag cites the criterion it rests on.

    The flag is a recorded judgement, so the record has to say what the
    judgement was made against; otherwise a reviewer cannot check it and the
    assertion above is reading an opinion.
    """
    uncited = [
        _unbacktick(r[0])
        for r in map_rows(contract)
        if _unbacktick(r[3]) == "yes"
        and not re.search(r"\b\d+\.\d+\.\d+\b", r[4])
    ]
    assert not uncited, (
        f"these states are flagged WCAG-bearing but cite no success criterion: "
        f"{uncited}"
    )
