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
    """The text under `heading`, up to the next heading at the same level."""
    level = heading.split(" ", 1)[0]
    start = re.search(rf"^{re.escape(heading)}$", body, re.MULTILINE)
    assert start is not None, f"missing heading: {heading}"
    rest = body[start.end() :]
    nxt = re.search(rf"^{re.escape(level)} ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def _sentence_containing(body: str, anchor: str) -> str:
    """The one sentence holding `anchor`, whitespace-normalised.

    Sentence scope is what makes these checks real. The names under test appear
    on other sentences of the same files already.
    """
    flat = _flat(body)
    assert anchor in flat, f"missing anchor: {anchor}"
    where = flat.index(anchor)
    start = flat.rfind(". ", 0, where)
    start = 0 if start == -1 else start + 2
    end = flat.find(". ", where)
    end = len(flat) if end == -1 else end + 1
    return flat[start:end]


# --- T1: the two slot types carry a name, a field set, a starting level ------


def test_each_new_slot_type_is_named_and_shaped() -> None:
    """AC1, AC4 -- the `type` row lists each kind and its field set is stated.

    Read as two surfaces, not one grep: a kind named in the field table but
    never shaped is exactly the drift this catches.
    """
    body = SIDECAR_SCHEMA.read_text(encoding="utf-8")
    type_row = next(
        line for line in body.splitlines() if line.startswith("| `type` |")
    )
    for slot_type in NEW_SLOT_TYPES:
        assert f"`{slot_type}`" in type_row, slot_type

    flat = _flat(body)
    assumption = _sentence_containing(flat, "An `assumption-test` slot carries")
    for field in (
        "riskiest assumption",
        "kill condition",
        "prototype-approach",
        "`validation_hook`",
    ):
        assert field in assumption, field

    delivery = _sentence_containing(flat, "A `delivery-contract` slot carries")
    assert "G3 leaf projection" in delivery


def test_the_classification_section_states_the_starting_level() -> None:
    """AC2 -- `internal` is the level a controller starts from for both."""
    section = _flat(
        _section(
            SIDECAR_SCHEMA.read_text(encoding="utf-8"),
            "## Data classification & handling",
        )
    )
    starting = _sentence_containing(section, "The controller starts from")
    for slot_type in NEW_SLOT_TYPES:
        assert f"`{slot_type}`" in starting, slot_type
    assert starting.count("`internal`") == 2, starting


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
    floor = _sentence_containing(section, "is a **floor**")
    assert "starting level named for a slot type" in floor
    assert "may raise it" in floor
    assert "Levels are assigned per instance" in section


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
    for gate, skill in (
        ("G0 intake (`frame-intent`)", "frame-intent"),
        ("G1 strategy (`de-risk-intent`", "de-risk-intent"),
        ("G3 handoff (`decompose-intent`)", "decompose-intent"),
    ):
        assert gate in walk, (gate, skill)
    # `decompose-intent` holds two ladder positions, G1 and G3.
    assert "then `decompose-intent`)" in walk
    assert walk.count("`decompose-intent`") == 2, walk


def test_the_standalone_exclusion_keeps_two_names_and_drops_one() -> None:
    """AC6 -- the exclusion names the two standalone-authorable skills only."""
    description = re.search(
        r"^description: (.*)$",
        DISCOVERY_LOOP.read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    exclusion = _sentence_containing(description, "author one discovery artifact")
    assert "frame-domain" in exclusion
    assert "explore-options" in exclusion
    assert "frame-intent" not in exclusion
    assert len(description) <= 1024, len(description)


# --- T3: the Core-absent branch names `work-intake` on all three surfaces ---


def test_the_skill_fallback_sentence_names_work_intake() -> None:
    """AC7 -- the `portable rendered` sentence names the invocation."""
    handoff = _section(
        DISCOVERY_LOOP.read_text(encoding="utf-8"),
        "### Capability-negotiated G3 handoff",
    )
    fallback = _sentence_containing(handoff, "portable rendered")
    assert "`work-intake`" in fallback, fallback


def test_the_decompose_skill_core_absent_sentence_names_work_intake() -> None:
    """AC8 -- the `If Core is absent` sentence names the invocation."""
    fallback = _sentence_containing(
        DECOMPOSE_INTENT.read_text(encoding="utf-8"), "If Core is absent"
    )
    assert "`work-intake`" in fallback, fallback


def test_the_recursive_decomposition_fallback_sentence_names_work_intake() -> None:
    """AC9 -- the `Otherwise render` sentence names the invocation."""
    fallback = _sentence_containing(
        RECURSIVE_DECOMPOSITION.read_text(encoding="utf-8"), "Otherwise render"
    )
    assert "`work-intake`" in fallback, fallback


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
    routes = [line for line in menu.splitlines() if line.startswith("- **")]
    assert len(routes) == 3, routes

    bullets = re.split(r"^- \*\*", menu, flags=re.MULTILINE)[1:]
    expected = (
        ("frame-intent", "de-risk-intent", "decompose-intent"),
        ("discovery-loop",),
        ("frame-situation",),
    )
    for bullet, names in zip(bullets, expected, strict=True):
        flat = _flat(bullet)
        # The bolded lead is the situation; the skills follow it.
        situation, _, remainder = flat.partition("**")
        assert situation.strip(), flat
        assert remainder.strip(), flat
        for name in names:
            assert f"`{name}`" in flat, (name, flat)


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
