"""The intent triad is executed by the loop's surfaces, not implied by them.

Every assertion here reads a shipped artifact inside this pack. Each one slices
to the sentence or section that carries the obligation before asserting, because
the names these criteria are about -- `work-intake`, `frame-intent`,
`identify-opportunities` -- already appear elsewhere in the same files for
unrelated and legitimate reasons. A file-scoped assertion would be green before
the edit that satisfies it landed.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PACK_ROOT / ".apm" / "skills"

SIDECAR_SCHEMA = (
    SKILLS / "discovery-loop" / "references" / "sidecar-schema.md"
)
DISCOVERY_LEAD = PACK_ROOT / ".apm" / "agents" / "discovery-lead.md"
DISCOVERY_LOOP = SKILLS / "discovery-loop" / "SKILL.md"
DECOMPOSE_INTENT = SKILLS / "decompose-intent" / "SKILL.md"
RECURSIVE_DECOMPOSITION = (
    SKILLS / "decompose-intent" / "references" / "recursive-decomposition.md"
)
FRAME_INTENT = SKILLS / "frame-intent" / "SKILL.md"

NEW_SLOT_TYPES = ("assumption-test", "delivery-contract")


def _flat(text: str) -> str:
    """Collapse whitespace so an assertion survives a mid-phrase line wrap."""
    return re.sub(r"\s+", " ", text)


def _section(body: str, heading: str) -> str:
    """The text under `heading`, up to the next heading at the same level or shallower.

    Deriving the terminator from the heading's own level alone is not enough: a
    `###` slice would then run past every following `##` to end of file, and a
    section-scoped assertion would silently be reading the rest of the document.
    """
    depth = len(heading.split(" ", 1)[0])
    start = re.search(rf"^{re.escape(heading)}$", body, re.MULTILINE)
    assert start is not None, f"missing heading: {heading}"
    rest = body[start.end() :]
    nxt = re.search(rf"^#{{1,{depth}}} ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


# The condition that marks the *negotiated* branch. Two of the three G3 surfaces
# name `work-intake` on that branch already, so a span that reaches this word may
# prove nothing about the Core-absent one. The G3 checks assert its absence from
# the clause to show the boundary really resolved -- and assert its presence in
# the body first, because an absence is only evidence while the thing being
# looked for still exists to be found.
NEGOTIATED_MARKER = "advertis"


def _clause_containing(body: str, anchor: str) -> str:
    """The one clause holding `anchor`, whitespace-normalised.

    Clause scope is what makes these checks real: the names under test appear on
    neighbouring clauses of the same files already. Bounding on `". "` alone is
    too weak, because re-punctuating the preceding sentence with a semicolon
    would merge the two and hand the assertion a span that satisfies it for the
    wrong reason -- so `;` terminates a clause here too.
    """
    flat = _flat(body)
    assert anchor in flat, f"missing anchor: {anchor}"
    where = flat.index(anchor)
    starts = [m.end() for m in re.finditer(r"[.;]\s", flat) if m.end() <= where]
    start = starts[-1] if starts else 0
    end_match = re.search(r"[.;]\s", flat[where:])
    end = where + end_match.start() + 1 if end_match else len(flat)
    return flat[start:end]


def _list_item_containing(body: str, anchor: str) -> str:
    """The `- ` bullet holding `anchor`, whitespace-normalised.

    Bounding on sentence punctuation alone would widen here: between this
    anchor and the previous sentence end sit a fenced JSON example and a
    Markdown table whose cells end in `)` or a code span, so the span would
    silently cover both.
    """
    assert anchor in body, f"missing anchor: {anchor}"
    where = body.index(anchor)
    start = body.rfind("\n- ", 0, where)
    assert start != -1, f"anchor is not inside a list item: {anchor}"
    # The premise: that bullet must be the anchor's OWN item. An unbounded
    # backward search finds the nearest bullet anywhere in the file, so a
    # de-listed anchor would silently return a span opening hundreds of lines
    # earlier -- across the JSON fence and the field table this bound exists to
    # exclude. A blank line ends a list item, so one between the bullet and the
    # anchor means the anchor has left it.
    assert "\n\n" not in body[start:where], (
        f"anchor is not inside its own list item: {anchor!r} -- the nearest "
        "preceding bullet is separated from it by a blank line"
    )
    nxt = re.search(r"\n(?:- |\n)", body[where:])
    end = where + nxt.start() if nxt else len(body)
    return _flat(body[start:end])


def _assert_core_absent_clause_names_work_intake(body: str, anchor: str) -> None:
    """The Core-absent clause at `anchor` names `work-intake`, and is its own clause."""
    # The premise first: the differential below is only meaningful while the
    # negotiated branch is still marked by this word. Rewording it to a synonym
    # would otherwise turn the absence assertion into a vacuous one, which is
    # exactly how the previous form of this guard was defeated.
    assert NEGOTIATED_MARKER in _flat(body), (
        f"differential premise gone: no {NEGOTIATED_MARKER!r} marks the "
        "negotiated branch, so this clause's boundary can no longer be told "
        "from it -- re-anchor this check before trusting it"
    )
    clause = _clause_containing(body, anchor)
    assert "`work-intake`" in clause, clause
    assert NEGOTIATED_MARKER not in clause, (
        "clause boundary did not resolve -- this span reaches the negotiated "
        f"branch, which may name `work-intake` regardless: {clause}"
    )


# --- T1: the two slot types carry a name, a field set, a starting level ------


def test_each_new_slot_type_is_named_and_shaped() -> None:
    """AC1, AC4 -- the `type` row lists each kind and its field set is stated.

    Read as two surfaces, not one grep: a kind named in the field table but
    never shaped is exactly the drift this catches.
    """
    body = SIDECAR_SCHEMA.read_text(encoding="utf-8")
    type_row = next(
        (line for line in body.splitlines() if line.startswith("| `type` |")),
        None,
    )
    assert type_row is not None, (
        f"{SIDECAR_SCHEMA.name}: no blackboard field-table row starting `| \u0060type\u0060 |`"
    )
    for slot_type in NEW_SLOT_TYPES:
        assert f"`{slot_type}`" in type_row, slot_type

    assumption = _list_item_containing(body, "An `assumption-test` slot carries")
    for field in (
        "riskiest assumption",
        "kill condition",
        "prototype-approach",
        "`validation_hook`",
    ):
        assert field in assumption, field

    delivery = _list_item_containing(body, "A `delivery-contract` slot carries")
    assert "G3 leaf projection" in delivery


def test_the_classification_section_states_the_starting_level() -> None:
    """AC2 -- `internal` is the level a controller starts from for both."""
    section = _flat(
        _section(
            SIDECAR_SCHEMA.read_text(encoding="utf-8"),
            "## Data classification & handling",
        )
    )
    starting = _clause_containing(section, "The controller starts from")
    # AC2 pairs a level with each type, so bind the two halves rather than
    # counting occurrences of the level word: a rewrite naming `internal` once
    # for both types satisfies the criterion and must not red.
    for slot_type in NEW_SLOT_TYPES:
        pairing = re.search(
            rf"`internal`(?:(?!`internal`).)*?`{re.escape(slot_type)}`"
            rf"|`{re.escape(slot_type)}`(?:(?!`{re.escape(slot_type)}`).)*?`internal`",
            starting,
        )
        assert pairing is not None, (slot_type, starting)


def test_the_classification_section_states_the_floor_rule() -> None:
    """AC3 -- a starting level is a floor a write-time assessment may raise.

    Asserts only the floor rule. The section's opening sentence about write-time
    assignment is shipped text; asserting it too would make half this guard
    green before the edit it exists to check landed.
    """
    section = _flat(
        _section(
            SIDECAR_SCHEMA.read_text(encoding="utf-8"),
            "## Data classification & handling",
        )
    )
    floor = _clause_containing(section, "is a **floor**")
    assert "starting level named for a slot type" in floor
    assert "may raise it" in floor
    assert "Levels are assigned per instance" in section

    # AC3 is positional: the floor rule must sit BENEATH the section's existing
    # opening sentence. Asserting the floor rule alone would stay green if that
    # anchor were deleted, and the ordering half cannot be satisfied pre-edit,
    # so guarding it costs nothing the criterion did not already ask for.
    anchor = (
        "Each slot carries — or the skill assigns at write time — "
        "a **data-classification level**"
    )
    assert anchor in section, section[:200]
    assert section.index(anchor) < section.index("is a **floor**")


# --- T2: the walk names the triad, the exclusion stops routing it away ------


def test_the_gate_ladder_walk_pairs_each_triad_skill_with_its_gate() -> None:
    """AC5 -- each triad skill sits beside the gate it runs at.

    Sliced to the walk: a bare mention in any other section of the agent file
    would satisfy a whole-file assertion without the walk naming anything.
    """
    walk = _flat(
        _section(
            DISCOVERY_LEAD.read_text(encoding="utf-8"),
            "## How you run the loop",
        )
    )
    # Each literal is a gate paired with the skill that runs at it. The G1
    # fragment is deliberately truncated before its closing parenthesis
    # because that gate carries two skills in one parenthetical, and
    # `decompose-intent` is the second of them.
    for pairing in (
        "G0 intake (`frame-intent`)",
        "G1 strategy (`de-risk-intent`",
        "then `decompose-intent`)",
        "G3 handoff (`decompose-intent`)",
    ):
        assert pairing in walk, (pairing, walk)


def test_the_standalone_exclusion_keeps_two_names_and_drops_one() -> None:
    """AC6 -- the exclusion names the two standalone-authorable skills only."""
    description = re.search(
        r"^description: (.*)$",
        DISCOVERY_LOOP.read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    exclusion = _clause_containing(description, "author one discovery artifact")
    assert "frame-domain" in exclusion
    assert "explore-options" in exclusion
    assert "frame-intent" not in exclusion


# --- T3: the Core-absent branch names `work-intake` on all three surfaces ---


def test_the_skill_fallback_sentence_names_work_intake() -> None:
    """AC7 -- the `portable rendered` sentence names the invocation."""
    handoff = _section(
        DISCOVERY_LOOP.read_text(encoding="utf-8"),
        "### Capability-negotiated G3 handoff",
    )
    _assert_core_absent_clause_names_work_intake(handoff, "portable rendered")


def test_the_decompose_skill_core_absent_sentence_names_work_intake() -> None:
    """AC8 -- the `If Core is absent` sentence names the invocation."""
    _assert_core_absent_clause_names_work_intake(
        DECOMPOSE_INTENT.read_text(encoding="utf-8"), "If Core is absent"
    )


def test_the_recursive_decomposition_fallback_sentence_names_work_intake() -> None:
    """AC9 -- the `Otherwise render` sentence names the invocation."""
    _assert_core_absent_clause_names_work_intake(
        RECURSIVE_DECOMPOSITION.read_text(encoding="utf-8"), "Otherwise render"
    )


# --- T5: the cross-sequence route menu -------------------------------------


def test_frame_intent_carries_the_pick_a_route_section() -> None:
    """AC10 -- the menu sits between `When to invoke` and `Procedure`."""
    body = FRAME_INTENT.read_text(encoding="utf-8")
    order = [
        re.search(rf"^{re.escape(heading)}$", body, re.MULTILINE)
        for heading in ("## When to invoke", "## Pick a route", "## Procedure")
    ]
    assert all(match is not None for match in order), order
    positions = [match.start() for match in order]
    assert positions == sorted(positions), positions


def test_the_route_menu_names_three_routes_with_a_fit_line() -> None:
    """AC11 -- three routes, each stating the situation it fits."""
    menu = _section(FRAME_INTENT.read_text(encoding="utf-8"), "## Pick a route")
    bullets = [_flat(b) for b in re.split(r"^- \*\*", menu, flags=re.MULTILINE)[1:]]
    assert len(bullets) == 3, bullets

    # AC11 requires three routes and states no order, so each expected route is
    # matched to whichever bullet names it rather than to a position.
    expected = (
        ("frame-intent", "de-risk-intent", "decompose-intent"),
        ("discovery-loop",),
        ("frame-situation",),
    )
    matched: list[str] = []
    for names in expected:
        hits = [b for b in bullets if all(f"`{n}`" in b for n in names)]
        assert len(hits) == 1, (names, hits)
        matched.append(hits[0])
    assert len(set(matched)) == 3, "two expected routes matched the same bullet"

    for bullet in bullets:
        # The bolded lead is the situation the route fits; the skills follow it.
        situation, _, remainder = bullet.partition("**")
        assert situation.strip(), bullet
        assert remainder.strip(), bullet


def test_the_menu_names_no_six_step_skill_but_frame_situation() -> None:
    """AC12 -- the menu names the sequence's opener and no later step.

    The slice is what makes this safe rather than destructive:
    `identify-opportunities` is named legitimately in `frame-intent`'s step 5
    opportunity-scoring pointer, which this delivery does not touch.
    """
    menu = _section(FRAME_INTENT.read_text(encoding="utf-8"), "## Pick a route")
    assert "frame-situation" in menu
    for later_step in (
        "identify-opportunities",
        "diverge-solutions",
        "place-bet",
        "map-capabilities",
    ):
        assert later_step not in menu, later_step


def test_discovery_loop_points_at_the_menu() -> None:
    """AC13 -- `When to invoke` routes an unsure reader to the menu."""
    when = _flat(
        _section(DISCOVERY_LOOP.read_text(encoding="utf-8"), "## When to invoke")
    )
    assert "`frame-intent`" in when
    assert "## Pick a route" in when
