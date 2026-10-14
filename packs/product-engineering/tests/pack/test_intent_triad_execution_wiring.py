"""The intent triad is executed by the loop's surfaces, not implied by them.

Every assertion here reads a shipped artifact inside this pack. Each one slices
to the sentence or section that carries the obligation before asserting, because
the names these criteria are about -- `work-intake`, the frame skill,
`identify-opportunities` -- already appear elsewhere in the same files for
unrelated and legitimate reasons. A file-scoped assertion would be green before
the edit that satisfies it landed.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PACK_ROOT / ".apm" / "skills"
# Retired source skills; no discovery surface may name them.
RETIRED_SHAPING_SKILLS = (
    "frame-intent",
    "de-risk-intent",
    "decompose-intent",
)

SIDECAR_SCHEMA = (
    SKILLS / "discovery-loop" / "references" / "sidecar-schema.md"
)
DISCOVERY_LEAD = PACK_ROOT / ".apm" / "agents" / "discovery-lead.md"
DISCOVERY_LOOP = SKILLS / "discovery-loop" / "SKILL.md"
INTENT_DECOMPOSE_MODE = SKILLS / "intent" / "references" / "decompose.md"
INTENT_RECURSIVE_DECOMPOSITION = (
    SKILLS / "intent" / "references" / "recursive-decomposition.md"
)

NEW_SLOT_TYPES = ("assumption-test", "delivery-contract")

# The schema's classification vocabulary. Held here rather than parsed from the
# table under test, so a mutation to that table reds the premise check instead
# of quietly redefining what the assertions mean.
CLASSIFICATION_LEVELS = ("public", "internal", "sensitive", "regulated")


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


def _clause_containing(body: str, anchor: str) -> str:
    """The one clause holding `anchor`, whitespace-normalised.

    Clause scope is what makes these checks more than a grep: the names under
    test appear on neighbouring clauses of the same files already.

    Limit: the bound is punctuation, so re-punctuating around the anchor moves
    it, and a sentence-internal abbreviation would split a clause early. Both
    are recorded as accepted in the verification ledger.
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

    Limit: this models a single-paragraph `- ` bullet. A multi-paragraph item,
    a nested list, or an ordered `1. ` list reds rather than widens, so such a
    red is this helper's shape assumption showing, not a missing obligation.
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


def _clause_from(flat: str, where: int) -> str:
    """The text from `where` to the end of the clause it opens."""
    end_match = re.search(r"[.;]\s", flat[where:])
    return flat[where : where + end_match.start() + 1] if end_match else flat[where:]


def _assert_core_absent_clause_names_work_intake(body: str, anchor: str) -> None:
    """From the Core-absent anchor forward, its own clause names `work-intake`.

    Reading forward rather than around the anchor is what keeps this honest at
    no extra cost: the negotiated branch names `work-intake` on its own
    account, and it lies behind the anchor on all three surfaces, so it cannot
    satisfy a forward span.

    This catches an editor dropping the obligation, which is the regression
    that matters. It does not catch an editor who also re-punctuates the
    surrounding prose; that bar was weighed and declined, and the verification
    ledger records what is no longer guarded.
    """
    flat = _flat(body)
    assert anchor in flat, f"missing anchor: {anchor}"
    clause = _clause_from(flat, flat.index(anchor))
    assert "`work-intake`" in clause, (
        f"the Core-absent clause opening at {anchor!r} does not name "
        f"`work-intake`: {clause!r}"
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
    # The premise: these are the schema's classification levels. Asserting the
    # level table still lists exactly them is what lets the absence check below
    # mean something -- a level added to the schema and not here would let a
    # slot be pinned to it unnoticed.
    section_raw = _section(
        SIDECAR_SCHEMA.read_text(encoding="utf-8"),
        "## Data classification & handling",
    )
    tabled = {
        m.group(1)
        for m in re.finditer(r"^\| `([^`]+)` \|", section_raw, re.MULTILINE)
    }
    assert tabled == set(CLASSIFICATION_LEVELS), (tabled, CLASSIFICATION_LEVELS)

    starting = _clause_containing(section, "The controller starts from")

    # AC2 pairs a level WITH each type. Asserting the two merely co-occur lets a
    # type carry a rival level, or none at all, so parse the pairings: each
    # `from <level> for <types>` unit must give `internal`, and between them the
    # units must cover both slot types.
    units = re.split(r"\bfrom\b", starting)[1:]
    assert units, starting
    covered: set[str] = set()
    for unit in units:
        types = [s for s in NEW_SLOT_TYPES if f"`{s}`" in unit]
        if not types:
            continue
        levels = {
            lvl
            for lvl in CLASSIFICATION_LEVELS
            if re.search(rf"(?:`{lvl}`|\b{lvl}\b)", unit)
        }
        assert levels == {"internal"}, (
            f"slot type(s) {types} are given starting level(s) {levels or '{}'} "
            f"rather than exactly `internal`: {unit!r}"
        )
        covered.update(types)
    assert covered == set(NEW_SLOT_TYPES), (covered, starting)


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
    # the decompose skill is the second of them.
    for pairing in (
        "G0 intake (`intent frame`)",
        "G1 strategy (`intent de-risk`",
        "then `intent decompose`)",
        "G3 handoff (`intent decompose`)",
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
    assert RETIRED_SHAPING_SKILLS[0] not in exclusion
    assert "intent frame" not in exclusion


def test_the_description_hands_off_through_work_intake_not_work_loop() -> None:
    """AC-0015 -- the G3 handoff in the description is `work-intake`."""
    description = re.search(
        r"^description: (.*)$",
        DISCOVERY_LOOP.read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    assert len(description) <= 1024, len(description)
    assert "hands off through work-intake at G3" in description
    assert "work-loop" not in description


def test_the_discovery_surfaces_name_intent_modes_at_each_gate() -> None:
    """AC-0014 -- the skill and agent name the `intent` modes, not the sources."""
    for path in (DISCOVERY_LOOP, DISCOVERY_LEAD):
        body = path.read_text(encoding="utf-8")
        for retired in RETIRED_SHAPING_SKILLS:
            assert retired not in body, (path.name, retired)
    table = _flat(DISCOVERY_LOOP.read_text(encoding="utf-8"))
    for row in (
        "| **G0** | Intake | `intent frame`",
        "| **G1** | Strategy | `intent de-risk`",
        "`intent decompose` → child",
        "| **G3** | Handoff | `intent decompose`",
        "*product* (`intent decompose`)",
    ):
        assert row in table, row


# --- T3: the Core-absent branch names `work-intake` on all three surfaces ---


def test_the_skill_fallback_sentence_names_work_intake() -> None:
    """AC7 -- the `portable rendered` sentence names the invocation."""
    handoff = _section(
        DISCOVERY_LOOP.read_text(encoding="utf-8"),
        "### Capability-negotiated G3 handoff",
    )
    _assert_core_absent_clause_names_work_intake(handoff, "portable rendered")


def test_the_intent_decompose_mode_core_absent_sentence_names_work_intake() -> None:
    """AC8, retargeted -- the same sentence holds in the `intent` decompose mode."""
    _assert_core_absent_clause_names_work_intake(
        INTENT_DECOMPOSE_MODE.read_text(encoding="utf-8"), "If Core is absent"
    )


def test_the_intent_recursive_decomposition_fallback_names_work_intake() -> None:
    """AC9, retargeted -- the same sentence holds under `intent/references`."""
    _assert_core_absent_clause_names_work_intake(
        INTENT_RECURSIVE_DECOMPOSITION.read_text(encoding="utf-8"), "Otherwise render"
    )


# --- T5: the cross-sequence route menu -------------------------------------


def test_discovery_loop_points_at_the_menu() -> None:
    """AC13 -- `When to invoke` routes an unsure reader to the menu."""
    when = _flat(
        _section(DISCOVERY_LOOP.read_text(encoding="utf-8"), "## When to invoke")
    )
    assert "`intent`" in when
    assert "## Route mode" in when


# --- The G3 handoff and requirements ingest name the right Core skills ------

REQUIREMENTS_CROSSWALK = (
    SKILLS / "discovery-loop" / "references" / "requirements-crosswalk.md"
)
_HANDOFF_TO_WORK_LOOP = re.compile(r"hand(?:s|ed)? (?:off )?to `?work-loop")


def test_no_discovery_surface_hands_off_to_work_loop() -> None:
    """The loop hands off through `work-intake`; `work-loop` is only its peer.

    Matching the handoff verb, not the name, leaves the legitimate peer
    mentions of `work-loop` free.
    """
    for path in (DISCOVERY_LOOP, DISCOVERY_LEAD):
        flat = _flat(path.read_text(encoding="utf-8"))
        assert not _HANDOFF_TO_WORK_LOOP.search(flat), (
            path.name,
            _HANDOFF_TO_WORK_LOOP.search(flat),
        )
    lead = _flat(DISCOVERY_LEAD.read_text(encoding="utf-8"))
    assert "hands off through work-intake at G3" in lead
    assert "hand off through `work-intake` at **G3**" in lead


def test_requirements_ingest_creates_a_new_brief() -> None:
    """An outside BRD/PRD/SRS becomes a new Draft brief, so ingest uses `create`.

    `continue` reviews an existing repository brief, which an outside
    requirements document is not.
    """
    skill = _list_item_containing(
        DISCOVERY_LOOP.read_text(encoding="utf-8"), "**Requirements as input**"
    )
    crosswalk = _list_item_containing(
        REQUIREMENTS_CROSSWALK.read_text(encoding="utf-8"),
        "**Requirements as input (ingest).**",
    )
    for item in (skill, crosswalk):
        assert "`author-delivery-brief create`" in item, item
        assert "author-delivery-brief continue" not in item, item
