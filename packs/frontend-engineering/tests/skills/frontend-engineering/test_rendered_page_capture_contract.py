"""Contract tests for the rendered-page capture set, record, and step split.

Like the severity suite next to this one, these read
`references/rendered-page-inspection.md` and derive their expectations from its
tables. The evaluators in the shared reader implement the rules *as the tables
state them* — a table change moves the outcome, which is what makes these checks
able to fail.
"""

from __future__ import annotations

import re

import pytest
from frontend_engineering_rendered_page_rules import (
    REQUIRED_RULE_ROWS,
    capture_record_fields,
    capture_set_rules,
    capture_tables_agree,
    channel_basis,
    channel_capture_width,
    channel_rules,
    discarded_breakpoints,
    evaluate_capture_set,
    evaluate_record,
    fallback_channels,
    findings_for,
    inspection_result,
    is_completed_inspection_result,
    judgement_request_fields,
    minimum_in_force,
    normalize_predicate,
    read_rules,
    read_skill,
    required_channels,
    skill_capture_table,
    step_rules,
    width_in_channel,
    worked_example_snippet,
)

REQUIRED = [
    "route",
    "viewport-width",
    "viewport-height",
    "scroll-position",
    "page-scrollable",
]


@pytest.fixture(scope="module")
def rules_markdown() -> str:
    return read_rules()


def _names(missing: list[str], requirement: str) -> bool:
    """Whether `missing` reports `requirement`.

    Entries carry the route they belong to — "short-at-rest (route /a)" — because
    completeness is evaluated per route, so this matches on the requirement name
    rather than on the whole entry.
    """
    return any(requirement in entry for entry in missing)


NARROW, WIDE = 390, 1280


def _capture(
    route: str,
    height: int,
    scroll: int,
    scrollable: str = "yes",
    width: int = NARROW,
) -> dict[str, int | str]:
    """Width and height are independent arguments; width used to be derived from
    height, which is the coupling the channel axis exists to remove."""
    return {
        "route": route,
        "viewport-width": width,
        "viewport-height": height,
        "scroll-position": scroll,
        "page-scrollable": scrollable,
    }


def complete_set(route: str = "/a") -> list[dict[str, int | str]]:
    """The four height-and-scroll captures in each of the two fallback channels.

    Eight, not four. The four-capture version of this fixture wrote one width per
    height, so it covered the narrow channel only at 600 and the wide one only at
    900 — which is exactly the set the channel axis must reject.
    """
    return [
        _capture(route, height, scroll, width=width)
        for width in (NARROW, WIDE)
        for height in (600, 900)
        for scroll in (0, 800)
    ]


# ── capture-set completeness ────────────────────────────────────────────────

def test_a_set_without_a_short_viewport_capture_is_rejected(rules_markdown: str) -> None:
    """Verifies: the capture set contains a capture at a viewport height of at
    most 600 CSS pixels."""
    captures = [c for c in complete_set() if int(c["viewport-height"]) > 600]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", "a set with no short-viewport capture was accepted"
    assert _names(missing, "short-at-rest") and _names(missing, "short-scrolled")


def test_a_set_without_a_tall_viewport_capture_is_rejected(rules_markdown: str) -> None:
    """Verifies: the capture set contains a capture at a viewport height of at
    least 900 CSS pixels."""
    captures = [c for c in complete_set() if int(c["viewport-height"]) < 900]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", "a set with no tall-viewport capture was accepted"
    assert _names(missing, "tall-at-rest") and _names(missing, "tall-scrolled")


@pytest.mark.parametrize(
    ("height", "dropped_scroll", "expected_missing"),
    [
        (600, 0, "short-at-rest"),
        (600, 800, "short-scrolled"),
        (900, 0, "tall-at-rest"),
        (900, 800, "tall-scrolled"),
    ],
)
def test_a_set_missing_a_scroll_position_at_a_height_is_rejected(
    rules_markdown: str, height: int, dropped_scroll: int, expected_missing: str
) -> None:
    """Verifies: for each viewport height captured, the set contains one capture
    at scroll position 0 and one at a non-zero scroll position.

    Driven at both heights rather than one, so dropping the rule for either
    height is caught.
    """
    captures = [
        c
        for c in complete_set()
        if not (
            int(c["viewport-height"]) == height
            and int(c["scroll-position"]) == dropped_scroll
        )
    ]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", (
        f"a set missing the {height}px capture at scroll {dropped_scroll} was accepted"
    )
    assert _names(missing, expected_missing)


def test_a_complete_set_is_accepted(rules_markdown: str) -> None:
    """The green path. Without it, an implementation that rejects every capture
    set would satisfy all three rejection assertions above."""
    status, missing = evaluate_capture_set(rules_markdown, complete_set())
    assert status == "complete", f"a complete set was rejected; missing={missing}"
    assert missing == []


def test_a_rejected_set_records_an_incomplete_result(rules_markdown: str) -> None:
    """Verifies the recorded half of: a capture set missing any required capture
    yields an incomplete result that cannot satisfy a completed inspection."""
    status, missing = evaluate_capture_set(rules_markdown, complete_set()[:1])
    assert status == "incomplete"
    assert status != "complete", "an incomplete result must not read as completed"
    assert missing, "an incomplete result must name what is missing"
    assert "incomplete" in rules_markdown.lower(), (
        "the reference no longer names the incomplete result the rule produces"
    )


# ── capture state ───────────────────────────────────────────────────────────

def test_the_capture_record_names_every_required_field(rules_markdown: str) -> None:
    """Verifies: every capture carries the route, the viewport width, the
    viewport height, and the scroll position."""
    assert sorted(capture_record_fields(rules_markdown)) == sorted(REQUIRED)


def test_the_judgement_request_restates_every_recorded_field(rules_markdown: str) -> None:
    """Verifies: the judgement request states the route, viewport width, viewport
    height, and scroll position recorded with that capture — every one of them,
    not just the scroll position."""
    # The four the criterion names, asserted individually so dropping any one is
    # caught on its own terms rather than as a set-equality diff.
    stated = judgement_request_fields(rules_markdown)
    for field in ("route", "viewport-width", "viewport-height", "scroll-position"):
        assert field in stated, f"the judgement request omits {field}"
    # Every recorded field is restated to the judge. The request may carry MORE
    # than the record — since the amendment it also declares the capture
    # untrusted evidence — so this is containment, not equality.
    recorded = set(capture_record_fields(rules_markdown))
    assert recorded <= set(stated), (
        f"the judgement request omits recorded field(s) {sorted(recorded - set(stated))}"
    )
    assert set(REQUIRED) <= set(stated)


@pytest.mark.parametrize("absent_field", REQUIRED)
def test_a_record_missing_a_field_yields_no_finding(
    rules_markdown: str, absent_field: str
) -> None:
    """Verifies: a capture missing any required field produces no finding."""
    record: dict[str, object] = dict.fromkeys(REQUIRED, 1)
    del record[absent_field]
    assert findings_for(rules_markdown, record) == [], (
        f"a record with no {absent_field} still produced a finding"
    )


@pytest.mark.parametrize("absent_field", REQUIRED)
def test_a_record_missing_a_field_is_reported_as_unusable(
    rules_markdown: str, absent_field: str
) -> None:
    """Verifies: that same record is reported as unusable.

    Asserted separately from the no-finding check: a run that emits no finding
    and no status would otherwise pass that one while failing this.
    """
    record: dict[str, object] = dict.fromkeys(REQUIRED, 1)
    del record[absent_field]
    status, absent = evaluate_record(rules_markdown, record)
    assert status == "unusable", f"a record with no {absent_field} was not unusable"
    assert absent == [absent_field]


def test_a_complete_record_is_usable_and_can_carry_a_finding(
    rules_markdown: str,
) -> None:
    """The green path for the record shape, for the same reason the capture-set
    green path exists."""
    record: dict[str, object] = dict.fromkeys(REQUIRED, 1)
    assert evaluate_record(rules_markdown, record) == ("usable", [])
    assert findings_for(rules_markdown, record) != []


# ── step separation ─────────────────────────────────────────────────────────

def test_capture_completes_without_invoking_the_judge(rules_markdown: str) -> None:
    """Verifies: the capture step completes without invoking the judge."""
    rules = step_rules(rules_markdown)
    assert rules.get("capture-step-invokes-judge") == "no"
    assert rules.get("capture-step-produces") == "capture-set"


def test_judgement_consumes_a_capture_set_it_did_not_produce(
    rules_markdown: str,
) -> None:
    """Verifies: the judgement step consumes a capture set it did not produce."""
    rules = step_rules(rules_markdown)
    assert rules.get("judgement-step-input") == "capture-set"
    assert rules.get("judgement-step-produces-captures") == "no"


# ── completeness is per route, and per height actually captured ─────────────

def test_two_routes_cannot_cover_each_others_required_heights(
    rules_markdown: str,
) -> None:
    """Verifies the "for each inspected route" half of the capture criteria.

    A flat scan over every capture accepts this set: the short band is present
    and so is the tall one, just never on the same route. Neither route was
    actually inspected at both heights.
    """
    captures = [
        _capture("/a", 600, 0),
        _capture("/a", 600, 400),
        _capture("/b", 900, 0),
        _capture("/b", 900, 400),
    ]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", (
        "one route covering the short band and another the tall band was "
        "accepted as a complete inspection of both"
    )
    assert _names(missing, "tall-at-rest"), missing
    assert any("/a" in entry for entry in missing)
    assert any("/b" in entry for entry in missing)


def test_an_extra_captured_height_needs_its_scrolled_counterpart(
    rules_markdown: str,
) -> None:
    """Verifies the "for each viewport width and height captured" half.

    The criterion is not limited to the required channels and bands. An adopter
    who adds a third size has captured that size, so it owes the same at-rest and
    scrolled pair — and a rule that only walks the table's named rows never looks
    at it. The obligation is keyed on the width-and-height pair, so the extra
    capture below owes a counterpart even though 390 already carries pairs at
    other heights.
    """
    captures = complete_set() + [_capture("/a", 750, 0)]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", (
        "a 390x750 at-rest capture with no scrolled counterpart was accepted"
    )
    assert _names(missing, "scrolled at 390x750"), missing


def test_an_extra_captured_height_is_accepted_once_it_is_paired(
    rules_markdown: str,
) -> None:
    """The green path for the rule above: extra heights are welcome, they just
    carry the same obligation. Without this, a rule rejecting every extra height
    would pass the check above."""
    captures = complete_set() + [_capture("/a", 750, 0), _capture("/a", 750, 400)]
    assert evaluate_capture_set(rules_markdown, captures) == ("complete", [])


def test_two_fully_captured_routes_are_accepted(rules_markdown: str) -> None:
    """The green path for per-route evaluation."""
    captures = complete_set("/a") + complete_set("/b")
    assert evaluate_capture_set(rules_markdown, captures) == ("complete", [])


def test_an_empty_capture_set_is_incomplete(rules_markdown: str) -> None:
    """True on empty state: a set with no captures at all is not a pass."""
    status, missing = evaluate_capture_set(rules_markdown, [])
    assert status == "incomplete"
    assert missing


# ── the channel axis ────────────────────────────────────────────────────────
#
# A channel is a band of viewport widths. These read the bands and the rules out
# of the reference rather than restating them, so deleting a row moves these
# tests instead of leaving them asserting a rule the pack no longer ships.


def _cap(width: int, height: int, scroll: int, route: str = "/a") -> dict[str, int | str]:
    """`_capture` with width first, for the channel cases that vary width most.

    The two builders were separate while `_capture` still derived width from
    height; they no longer differ in what they can express, only in argument
    order.
    """
    return _capture(route, height, scroll, width=width)


def _matrix(width: int, route: str = "/a") -> list[dict[str, int | str]]:
    """The four height-and-scroll captures, all at one width."""
    return [_cap(width, h, s, route) for h in (600, 900) for s in (0, 800)]


def test_fallback_channels_are_the_two_shipped_bands(rules_markdown: str) -> None:
    """Verifies: with no declared breakpoints the required channels are the two
    bands the reference states, and a width between them satisfies neither."""
    channels = required_channels(rules_markdown)
    assert channels == fallback_channels(rules_markdown)
    assert [name for name, _, _ in channels] == ["narrow", "wide"]
    by_name = {name: (name, lo, hi) for name, lo, hi in channels}
    assert width_in_channel(by_name["narrow"], 480)
    assert not width_in_channel(by_name["wide"], 480)
    assert not width_in_channel(by_name["narrow"], 768)
    assert not width_in_channel(by_name["wide"], 768)
    assert width_in_channel(by_name["wide"], 1024)
    assert not width_in_channel(by_name["narrow"], 1024)


def test_declared_breakpoints_bound_the_required_channels(rules_markdown: str) -> None:
    """Verifies: declared breakpoints bound the bands, each boundary value
    belonging to the wider band."""
    assert required_channels(rules_markdown, [1152]) == [
        ("below-1152", "", "<1152"),
        ("from-1152", ">=1152", ""),
    ]
    three = required_channels(rules_markdown, [480, 768, 1024])
    assert [name for name, _, _ in three] == [
        "below-480", "480-to-768", "768-to-1024", "from-1024",
    ]
    # The boundary value belongs to the wider band, not the narrower one.
    assert width_in_channel(three[1], 480) and not width_in_channel(three[0], 480)


def test_a_declared_breakpoint_must_be_a_positive_whole_number(
    rules_markdown: str,
) -> None:
    """Verifies: a band's bound cells hold whole numbers, so a run refuses a
    fractional or non-positive breakpoint rather than emitting a cell the
    predicate parser raises on."""
    # `True` is the clause's only non-obvious case: isinstance(True, int) is
    # True and True > 0, so without the explicit bool exclusion a boolean
    # reaches the band cells and `satisfies("<True", ...)` raises instead.
    for bad in (767.98, 0, -320, True, False):
        with pytest.raises(AssertionError, match="positive whole number"):
            required_channels(rules_markdown, [bad])


def test_declared_breakpoints_are_ordered_and_deduplicated(
    rules_markdown: str,
) -> None:
    """Verifies: the bands do not depend on the order or uniqueness of the input.

    Declared breakpoints are an optional adopter-supplied input, so an unsorted
    or duplicated list is reachable rather than hypothetical, and AC-0001's
    premise is stated over `b1 < ... < bn`. The normalization that makes that
    premise true was load-bearing and untested: without it `[1024, 480]` derives
    the band `>=1024 <480` and `[480, 480]` derives `>=480 <480`, neither
    satisfiable by any width, so `evaluate_capture_set` could never return
    complete and no run could reach a `completed` state.
    """
    canonical = required_channels(rules_markdown, [480, 1024])
    assert required_channels(rules_markdown, [1024, 480]) == canonical
    assert required_channels(rules_markdown, [480, 1024, 480]) == canonical
    assert required_channels(rules_markdown, [480, 480]) == required_channels(
        rules_markdown, [480]
    )
    # Every band a reordered or duplicated list yields is satisfiable, which is
    # the property the unsatisfiable ones above would break.
    for declared in ([1024, 480], [480, 480], [768, 480, 1024, 768]):
        for channel in required_channels(rules_markdown, declared):
            width = channel_capture_width(rules_markdown, channel[1], channel[2])
            assert width_in_channel(channel, width), (
                f"{declared} yields {channel}, which no width satisfies"
            )


def test_every_channel_yields_a_capture_width_inside_itself(
    rules_markdown: str,
) -> None:
    """Verifies: the shipped rule answers for every band the contract produces —
    one unbounded on either side, and one whose upper bound is exclusive."""
    for declared in (None, [1152], [480, 768, 1024]):
        for channel in required_channels(rules_markdown, declared):
            name, lower, upper = channel
            width = channel_capture_width(rules_markdown, lower, upper)
            assert width_in_channel(channel, width), (
                f"{name} yields {width}, which is outside its own band"
            )
    # A declared breakpoint puts its two captures either side of the boundary,
    # which is the pair a breakpoint-scoped rule changes behaviour across.
    widths = [
        channel_capture_width(rules_markdown, lo, hi)
        for _, lo, hi in required_channels(rules_markdown, [1152])
    ]
    assert widths == [1151, 1152]


def test_every_required_channel_carries_the_height_and_scroll_matrix(
    rules_markdown: str,
) -> None:
    """Verifies: a route needs all four height-and-scroll captures in every
    required channel, so the floor is eight with the fallback bands."""
    full = _matrix(390) + _matrix(1280)
    assert len(full) == 8
    assert evaluate_capture_set(rules_markdown, full) == ("complete", [])


def test_a_single_channel_set_is_incomplete(rules_markdown: str) -> None:
    """Verifies: a set that never leaves one channel is incomplete, and names
    each channel-and-capture it is short of."""
    state, missing = evaluate_capture_set(rules_markdown, _matrix(1280))
    assert state == "incomplete"
    assert sorted(missing) == sorted(
        f"{name} in narrow (route /a)"
        for name in ("short-at-rest", "short-scrolled", "tall-at-rest", "tall-scrolled")
    )


def test_one_width_per_height_misses_four_requirements(rules_markdown: str) -> None:
    """Verifies: the shipped fixture shape — width written as a function of
    height — is incomplete under the channel axis.

    This is the defect the axis exists to remove. The set below covers both
    heights and both scroll positions and was `complete` under the height-only
    contract, while having tested one channel at one height and the other at the
    other.
    """
    one_per_height = [_cap(390, 600, 0), _cap(390, 600, 800),
                      _cap(1280, 900, 0), _cap(1280, 900, 800)]
    state, missing = evaluate_capture_set(rules_markdown, one_per_height)
    assert state == "incomplete"
    assert sorted(missing) == sorted([
        "tall-at-rest in narrow (route /a)",
        "tall-scrolled in narrow (route /a)",
        "short-at-rest in wide (route /a)",
        "short-scrolled in wide (route /a)",
    ])


def test_every_captured_width_and_height_needs_the_scroll_pair(
    rules_markdown: str,
) -> None:
    """Verifies: the pair obligation groups on the width-and-height pair, not on
    the height alone.

    Grouping on the height alone would let two widths at one height each carry
    half a pair and read as coverage, which is why the extra at-rest capture
    below has to be reported even though its height already carries a pair.
    """
    full = _matrix(390) + _matrix(1280)
    extra = full + [_cap(900, 600, 0)]
    state, missing = evaluate_capture_set(rules_markdown, extra)
    assert state == "incomplete"
    assert "scrolled at 900x600 (route /a)" in missing


def test_an_unscrollable_third_size_satisfies_the_pair(rules_markdown: str) -> None:
    """Verifies: the recorded unscrollable branch answers at a third size too."""
    full = _matrix(390) + _matrix(1280)
    flat = dict(_cap(900, 600, 0), **{"page-scrollable": "no"})
    assert evaluate_capture_set(rules_markdown, full + [flat]) == ("complete", [])


def test_the_channel_basis_is_recorded_not_inferred(rules_markdown: str) -> None:
    """Verifies: the basis comes from the run input, not from the captures.

    A fallback run and a run declaring the fallback bands' own bounds can hand
    over identical captures; only the input tells them apart.
    """
    assert channel_rules(rules_markdown).get("channel-basis-recorded") == "required"
    assert channel_basis(rules_markdown, None) == "fallback"
    assert channel_basis(rules_markdown, [1152]) == "declared-breakpoints"
    assert channel_basis(rules_markdown, []) == "fallback"

    # The row gates the answer rather than sitting inert beside it: deleting it
    # raises, and switching it off refuses rather than guessing a basis.
    row = "| channel-basis-recorded | required |\n"
    assert row in rules_markdown
    with pytest.raises(AssertionError, match="channel-basis-recorded"):
        channel_basis(rules_markdown.replace(row, "", 1), [1152])
    off = rules_markdown.replace(row, "| channel-basis-recorded | not-required |\n", 1)
    with pytest.raises(AssertionError, match="does not record its basis"):
        channel_basis(off, [1152])


def test_the_channel_requirement_is_shipped_content(rules_markdown: str) -> None:
    """Verifies: removing the channel requirement from the reference reds the
    capture-set checks rather than leaving them green.

    The mutation is on shipped content, not on the module. A module that skipped
    the rule when its row went missing would report this one-channel set as
    complete, which is the fail-open shape this criterion exists to close.
    """
    one_channel = _matrix(1280)
    assert evaluate_capture_set(rules_markdown, one_channel)[0] == "incomplete"

    off = rules_markdown.replace(
        "| every-required-channel-needs-the-matrix | required |",
        "| every-required-channel-needs-the-matrix | not-required |",
        1,
    )
    assert off != rules_markdown
    assert evaluate_capture_set(off, one_channel)[0] == "complete", (
        "the evaluator still required every channel after the reference switched "
        "the rule off — the check is authoring its own rule"
    )

    # Deleting the ROW, which is the mutation the criterion actually names. The
    # first version of this test deleted the whole `## Channels` section instead
    # — that raises via the section reader, so it passed while the row itself
    # stayed fail-open and a one-channel set reported complete.
    row = "| every-required-channel-needs-the-matrix | required |\n"
    assert row in rules_markdown
    without_row = rules_markdown.replace(row, "", 1)
    with pytest.raises(AssertionError, match="every-required-channel-needs-the-matrix"):
        evaluate_capture_set(without_row, one_channel)

    # And deleting the section it lives in.
    gone = rules_markdown.replace("\n## Channels\n", "\n## Removed\n", 1)
    with pytest.raises(AssertionError, match="Channels"):
        evaluate_capture_set(gone, one_channel)


@pytest.mark.parametrize(
    "row_key", [k for keys in REQUIRED_RULE_ROWS.values() for k in keys]
)
def test_every_required_rule_row_raises_when_deleted(
    rules_markdown: str, row_key: str
) -> None:
    """Derived from the rows `evaluate_capture_set` declares it requires present.

    The first version hand-listed two keys while claiming to cover every row, and
    picked the two that already had coverage: deleting `channel-derivation`,
    `channel-boundary-belongs-to` or `channel-basis-recorded` left the walk
    returning `complete`, because those rows are only consulted on paths a
    fallback-basis run never takes. `REQUIRED_RULE_ROWS` is still a hand-written
    list; the control below is what makes a newly shipped row reach it.
    """
    full = _matrix(390) + _matrix(1280)
    assert evaluate_capture_set(rules_markdown, full) == ("complete", [])
    row = next(
        line for line in rules_markdown.splitlines()
        if line.strip().startswith(f"| {row_key} |")
    )
    without = rules_markdown.replace(row + "\n", "", 1)
    assert without != rules_markdown
    with pytest.raises(AssertionError, match=row_key):
        evaluate_capture_set(without, full)


def test_the_declared_breakpoint_basis_drives_the_completeness_walk(
    rules_markdown: str,
) -> None:
    """The basis AC-0001 defines, and the one the end-to-end run actually used.

    Every other completeness fixture uses the fallback bands, so the derived-band
    path through the walk had no test at all, while AC-0005 and AC-0006 are stated
    over "every required channel".
    """
    state, missing = evaluate_capture_set(rules_markdown, _matrix(1280), [1152])
    assert state == "incomplete"
    assert sorted(missing) == sorted(
        f"{name} in below-1152 (route /a)"
        for name in ("short-at-rest", "short-scrolled", "tall-at-rest", "tall-scrolled")
    ), missing

    # The two widths the shipped capture-width rule derives for those bands:
    # 1151 and 1152, the pair straddling the declared breakpoint.
    straddling = _matrix(1151) + _matrix(1152)
    assert evaluate_capture_set(rules_markdown, straddling, [1152]) == ("complete", [])

    # The same set is incomplete under the fallback basis, because neither width
    # is inside `narrow` or `wide`. The basis changes the answer, which is why it
    # is recorded rather than inferred.
    assert evaluate_capture_set(rules_markdown, straddling)[0] == "incomplete"


# ── the two copies of the capture contract ──────────────────────────────────


@pytest.fixture(scope="module")
def skill_markdown() -> str:
    return read_skill()


def test_both_copies_of_the_capture_contract_agree(
    rules_markdown: str, skill_markdown: str
) -> None:
    """Verifies: the reference and § 5a state the same required-capture set.

    They are restatements of one contract and drift apart in silence, which is
    why the check reads both rather than one.
    """
    assert capture_tables_agree(rules_markdown, skill_markdown)


@pytest.mark.parametrize(
    ("name", "field", "replacement"),
    [
        ("changed numeric bound", "height", "≤700 CSS px"),
        ("changed operator", "height", "≥600 CSS px"),
        ("dropped unscrollable branch", "scroll", "0"),
    ],
)
def test_the_drift_guard_distinguishes_what_it_must(
    rules_markdown: str, skill_markdown: str, name: str, field: str, replacement: str
) -> None:
    """Verifies: the normalization is presentation-only.

    A normalization that compared the capture names alone would pass every one of
    these, and could never fail on the predicate drift the guard exists to catch.
    """
    row = "short-scrolled" if field == "scroll" else "short-at-rest"
    original = skill_capture_table(skill_markdown)[row][field]
    perturbed = skill_markdown.replace(original, replacement, 1)
    assert perturbed != skill_markdown, f"{name}: the mutation did not apply"
    assert not capture_tables_agree(rules_markdown, perturbed), (
        f"the guard did not notice a {name}"
    )


def test_the_drift_guard_notices_a_changed_capture_name(
    rules_markdown: str, skill_markdown: str
) -> None:
    """The fourth distinction: a renamed row is a different required set."""
    perturbed = skill_markdown.replace("| short-at-rest |", "| brief-at-rest |", 1)
    assert perturbed != skill_markdown
    assert not capture_tables_agree(rules_markdown, perturbed)


def test_the_normalization_only_touches_presentation() -> None:
    """Verifies: exactly the three presentation forms, and nothing else."""
    assert normalize_predicate("≤600 CSS px") == "<=600"
    assert normalize_predicate("≥900 CSS px") == ">=900"
    assert normalize_predicate(">0, or `page-scrollable: no`") == ">0, or page-scrollable: no"
    # A bound, an operator and the branch all survive.
    assert normalize_predicate("≤600") != normalize_predicate("≤700")
    assert normalize_predicate("≤600") != normalize_predicate("≥600")
    assert normalize_predicate(">0, or `page-scrollable: no`") != normalize_predicate(">0")


# ── the worked example ──────────────────────────────────────────────────────


def test_the_worked_example_binds_width_to_the_channel(skill_markdown: str) -> None:
    """Verifies: the snippet an adopter copies iterates channels and takes its
    width from the one it is on.

    The snippet used to open one hard-coded 390px viewport, so an adopter copying
    it captured a single channel however many rows of the table they worked
    through — teaching single-width capture by example whatever the rules said.
    """
    snippet = worked_example_snippet(skill_markdown)
    channels = re.search(r"const channels = \[(.+?)\];", snippet, re.S)
    assert channels, "the snippet no longer declares a channel list"
    assert channels.group(1).count("width:") >= 2, (
        "the snippet iterates fewer than two channels, so copying it captures one"
    )
    viewport = re.search(r"viewport:\s*\{([^}]*)\}", snippet)
    assert viewport, "the snippet no longer opens a viewport"
    width_clause = re.search(r"width:\s*([^,\n]+)", viewport.group(1))
    assert width_clause, "the viewport sets no width"
    assert not re.fullmatch(r"\d+", width_clause.group(1).strip()), (
        f"the viewport width is the literal {width_clause.group(1).strip()!r}; it "
        f"must come from the channel being iterated"
    )
    assert "channel." in width_clause.group(1)


def test_the_worked_example_widths_satisfy_the_bands_they_name(
    rules_markdown: str, skill_markdown: str
) -> None:
    """Verifies: each channel in the snippet is captured at a width inside itself.

    Checking only that the list has two entries and no literal in the viewport
    left the widths free: rewriting them to 768 and 900 kept every test green and
    handed an adopter a set `evaluate_capture_set` reports incomplete in both
    channels.
    """
    snippet = worked_example_snippet(skill_markdown)
    pairs = re.findall(r"name:\s*'([^']+)'\s*,\s*width:\s*(\d+)", snippet)
    assert pairs, "the snippet's channel list states no name-and-width pairs"
    bands = {name: (name, lo, hi) for name, lo, hi in fallback_channels(rules_markdown)}
    for name, width in pairs:
        assert name in bands, f"the snippet names a channel {name!r} the reference does not declare"
        assert width_in_channel(bands[name], int(width)), (
            f"the snippet captures {name!r} at {width}, which is outside its own band"
        )
        assert int(width) == channel_capture_width(
            rules_markdown, bands[name][1], bands[name][2]
        ), (
            f"the snippet captures {name!r} at {width}, not the width the shipped "
            f"capture-width rule derives for that band"
        )


# ── the evidence manifest records channels ──────────────────────────────────


def _manifest_viewports_row(skill_markdown: str) -> str:
    for line in skill_markdown.splitlines():
        if line.strip().startswith("| viewports |"):
            return line
    raise AssertionError("SKILL.md carries no evidence-manifest `viewports` row")


def test_manifest_viewports_field_records_channels(
    rules_markdown: str, skill_markdown: str
) -> None:
    """Verifies AC-0011: the row states channels as width predicates, and the
    basis AC-0003 requires the run to record.

    The criterion named this test for a whole review round while no test of the
    name existed, and the only reader of the row asserted the absence of device
    tokens — which passes on a row reading `| viewports | none |`.
    """
    row = _manifest_viewports_row(skill_markdown)
    assert "channel" in row.lower(), "the row does not say it records channels"
    assert re.search(r"[<>]=?\d+", row), (
        "the row states no width predicate, so an adopter cannot tell what shape "
        "the value takes"
    )
    assert "basis" in row.lower() or "fallback" in row.lower(), (
        "the row does not record which channel basis the run used"
    )


def test_the_manifest_example_is_a_band_set_the_derivation_produces(
    rules_markdown: str, skill_markdown: str
) -> None:
    """The row's worked example is the only one of declared-breakpoint predicates
    in shipped adopter content, and nothing read it.

    It gave `<=480, >=480 <1152, >=1152`, where 480 satisfies both the first and
    the second band — the overlap the boundary convention exists to prevent.
    """
    row = _manifest_viewports_row(skill_markdown)
    predicates = re.findall(r"`([<>]=?\d+(?:\s+[<>]=?\d+)?)`", row)
    assert predicates, "the row carries no example predicates"
    breakpoints = sorted({int(n) for n in re.findall(r"[<>]=?(\d+)", " ".join(predicates))})
    # Compared against what the derivation produces for the breakpoints the
    # example itself names. A non-overlap check alone would pass on
    # `<480, >=600 <1152, >=1152` -- a set with a 120px gap no breakpoint list
    # can yield -- and its 0..2000 sweep bound was a bare literal that would miss
    # a boundary above it.
    stated = []
    for predicate in predicates:
        parts = predicate.split()
        lower = next((x for x in parts if x.startswith(">")), "")
        upper = next((x for x in parts if x.startswith("<")), "")
        stated.append((lower, upper))
    derived = [(lo, hi) for _, lo, hi in required_channels(rules_markdown, breakpoints)]
    assert stated == derived, (
        f"the example states {stated}, but the shipped derivation yields "
        f"{derived} for the breakpoints it names, {breakpoints}"
    )


def test_the_required_rule_rows_match_what_the_tables_state(rules_markdown: str) -> None:
    """The equality control that settles the hand-written-list question.

    `REQUIRED_RULE_ROWS` is a literal, and three review rounds argued over whether
    a per-row delete-and-red check derived from it "inherits" a newly shipped row.
    It does not, on its own: a row added to either shipped table is read by
    nothing and covered by nothing, and the whole suite stays green. This compares
    the constant against the keys the shipped tables actually state, so the
    divergence is what reds rather than the argument.
    """
    assert set(REQUIRED_RULE_ROWS["Channels"]) == set(channel_rules(rules_markdown)), (
        "the Channels rule table and REQUIRED_RULE_ROWS state different row sets; "
        "a row shipped without being required here is read by nothing"
    )
    assert set(REQUIRED_RULE_ROWS["Required captures"]) == set(
        capture_set_rules(rules_markdown)
    ), (
        "the Required captures rule rows and REQUIRED_RULE_ROWS state different "
        "row sets"
    )


def test_a_newly_shipped_rule_row_reds_until_it_is_required(
    rules_markdown: str,
) -> None:
    """The mutation the control above exists for, driven rather than described."""
    extra = rules_markdown.replace(
        "| channel-basis-recorded | required |",
        "| channel-basis-recorded | required |\n| channel-min-captures | required |",
        1,
    )
    assert extra != rules_markdown, "the mutation did not apply"
    # Through the control itself, not a copy of its comparison. Re-implementing
    # the `==` here left weakening that control to `<=` -- exactly the drift that
    # re-admits a shipped-but-unrequired row -- passing 290 green.
    with pytest.raises(AssertionError, match="state different row sets"):
        test_the_required_rule_rows_match_what_the_tables_state(extra)


# ── declared minimum width ──────────────────────────────────────────────────


def _value_cell(markdown: str, key: str, replacement: str) -> str:
    """The reference with one rule row's **value** rewritten, the row still present.

    Deletion cannot serve AC-0015 or AC-0016: `evaluate_capture_set` proves every
    `REQUIRED_RULE_ROWS` key present before the walk runs, so a deleted row reds
    through that presence loop whether or not anything reads it. Only a value-cell
    mutation separates *read* from *present*.
    """
    row = next(
        line for line in markdown.splitlines()
        if line.strip().startswith(f"| {key} |")
    )
    mutated = markdown.replace(row, f"| {key} | {replacement} |", 1)
    assert mutated != markdown, f"the value cell for {key} did not change"
    assert f"| {key} |" in mutated, f"{key} must stay present; this is not a deletion"
    return mutated


@pytest.mark.parametrize("breakpoints", [None, [768]], ids=["fallback", "declared"])
@pytest.mark.parametrize(
    "bad", [1.5, 0, -480, True], ids=["fractional", "zero", "negative", "boolean"]
)
def test_a_declared_minimum_must_be_a_positive_whole_number(
    rules_markdown: str, bad: object, breakpoints: list[int] | None
) -> None:
    """Verifies AC-0001: refused in both breakpoint states, absence admitted.

    Both states, because the shipped breakpoint validation loop sits *after* the
    `if not declared_breakpoints` early return. A minimum validated beside that
    loop is checked on the declared path and skipped on the fallback path — the
    surface this input exists for.

    `True` is in the set because `isinstance(True, int)` is true, so a bool would
    otherwise clamp a band to `>=1`.
    """
    with pytest.raises(AssertionError, match="positive whole number"):
        required_channels(rules_markdown, breakpoints, bad)  # type: ignore[arg-type]
    # Absence is admitted: *Always do* keeps the minimum optional, and a refusal
    # contract stated only on one side would read as refusing absence too.
    assert required_channels(rules_markdown, breakpoints, None) == required_channels(
        rules_markdown, breakpoints
    )


def test_a_band_wholly_below_the_minimum_is_dropped(rules_markdown: str) -> None:
    """Verifies AC-0002, asserting full band lists rather than counts or widths.

    Three fixtures each kill a cheaper filter. `[400, 800]` at 1280 drops a band
    bounded on *both* sides, which a filter keyed on an absent lower bound would
    keep. 480 against the fallback bands keeps `<=480`, which a filter comparing
    the bound's value without its operator would drop. And `[768, 1024]` at 768 is
    the only input separating `u <= minimum` from `u < minimum` for an exclusive
    upper bound.
    """
    assert required_channels(rules_markdown, None, 1280) == [("wide", ">=1280", "")]
    assert required_channels(rules_markdown, [768], 1280) == [
        ("from-1280", ">=1280", "")
    ]
    assert required_channels(rules_markdown, [400, 800], 1280) == [
        ("from-1280", ">=1280", "")
    ]
    assert required_channels(rules_markdown, [768, 1024], 768) == [
        ("768-to-1024", ">=768", "<1024"),
        ("from-1024", ">=1024", ""),
    ]
    # The clamped *fallback* band keeps the name its table row gives it; only a
    # breakpoint-derived name is rebuilt from the post-clamp bounds.
    assert required_channels(rules_markdown, None, 480) == [
        ("narrow", ">=480", "<=480"),
        ("wide", ">=1024", ""),
    ]


def test_the_clamp_raises_a_lower_bound_and_never_lowers_one(
    rules_markdown: str,
) -> None:
    """Verifies AC-0003: a surviving band's lower bound is the greater of the two.

    The 600 fixture is the one that bites. Assigning the minimum would lower
    `wide >=1024` to `>=600` and demand a capture at 600 — a width the reference
    states satisfies neither fallback channel by deliberate design.
    """
    assert required_channels(rules_markdown, None, 1280) == [("wide", ">=1280", "")]
    assert required_channels(rules_markdown, None, 600) == [("wide", ">=1024", "")]
    assert required_channels(rules_markdown, [400, 800], 100) == [
        ("100-to-400", ">=100", "<400"),
        ("400-to-800", ">=400", "<800"),
        ("from-800", ">=800", ""),
    ]
    widths = [
        channel_capture_width(rules_markdown, lo, up)
        for _, lo, up in required_channels(rules_markdown, [400, 800], 100)
    ]
    assert widths == [100, 400, 800]


def test_a_breakpoint_above_the_minimum_keeps_its_band(rules_markdown: str) -> None:
    """Verifies AC-0004: a minimum cannot collapse a surface below its own
    breakpoints above that minimum."""
    assert required_channels(rules_markdown, [1536], 1280) == [
        ("1280-to-1536", ">=1280", "<1536"),
        ("from-1536", ">=1536", ""),
    ]
    assert required_channels(rules_markdown, [1440, 1920], 1280) == [
        ("1280-to-1440", ">=1280", "<1440"),
        ("1440-to-1920", ">=1440", "<1920"),
        ("from-1920", ">=1920", ""),
    ]


def test_the_minimum_is_recorded_beside_the_basis(rules_markdown: str) -> None:
    """Verifies AC-0006: a separate field, and the basis vocabulary unwidened.

    Exact equality on the whole basis value, not a prefix match: a reader
    returning `declared-breakpoints+1280` would satisfy a looser check, and that
    is the third-vocabulary-value shape *Ask first* gates.
    """
    assert channel_basis(rules_markdown, None) == "fallback"
    assert minimum_in_force(rules_markdown, 1280) == "1280"
    assert channel_basis(rules_markdown, [768]) == "declared-breakpoints"
    assert minimum_in_force(rules_markdown, None) == "none-declared"
    assert minimum_in_force(rules_markdown, None) != ""


def test_discarded_breakpoints_are_recorded(rules_markdown: str) -> None:
    """Verifies AC-0007: exactly those strictly below the minimum.

    The mixed fixture is what bites — under the all-discarded one alone,
    recording the input list verbatim is indistinguishable from recording the
    discarded set. The 768 fixture pins `b < minimum` against `b <= minimum`,
    and agrees with AC-0002's own `[768, 1024]` case, which requires 768 to
    still bound a surviving channel.
    """
    assert discarded_breakpoints(rules_markdown, [768, 1536], 1280) == [768]
    assert discarded_breakpoints(rules_markdown, [768, 1024, 1440], 12800) == [
        768,
        1024,
        1440,
    ]
    assert discarded_breakpoints(rules_markdown, [768, 1024], 768) == []


@pytest.mark.parametrize("breakpoints", [None, [768]], ids=["fallback", "declared"])
@pytest.mark.parametrize("minimum", [None, 1280], ids=["no-minimum", "minimum"])
def test_the_derivation_refuses_an_unknown_minimum_rule(
    rules_markdown: str, breakpoints: list[int] | None, minimum: int | None
) -> None:
    """Verifies AC-0015: all four calls across both axes, row present throughout.

    Crossing the basis axis is what makes this bite: the derivation returns the
    fallback bands before it validates `channel-derivation`, so a check placed
    beside that sibling leaves the no-breakpoints path ungated.
    """
    mutated = _value_cell(rules_markdown, "channel-minimum-derivation", "keep-everything")
    with pytest.raises(AssertionError, match="channel-minimum-derivation"):
        required_channels(mutated, breakpoints, minimum)


@pytest.mark.parametrize("breakpoints", [None, [768]], ids=["fallback", "declared"])
def test_the_recording_refuses_when_switched_off(
    rules_markdown: str, breakpoints: list[int] | None
) -> None:
    """Verifies AC-0016: **both** readers, in both breakpoint states.

    Per reader, because one raising satisfies a row-level claim while the other
    stays fail-open; and with no breakpoints declared, because the discarded
    reader most naturally returns `[]` before consulting the switch.
    """
    off = _value_cell(rules_markdown, "channel-minimum-recorded", "not-required")
    with pytest.raises(AssertionError, match="channel-minimum-recorded"):
        minimum_in_force(off, 1280)
    with pytest.raises(AssertionError, match="channel-minimum-recorded"):
        discarded_breakpoints(off, breakpoints, 1280)


def test_no_two_required_channels_admit_a_common_width(rules_markdown: str) -> None:
    """Verifies AC-0017, swept wider than the fixtures its siblings pin.

    On an input where AC-0002, AC-0003 or AC-0004 asserts the full band list by
    exact equality, disjointness follows from that equality and this adds nothing.
    Its value is the combinations no fixture enumerates. It is what a clamp that
    widened the upper bound away fails: dropping `<=480` while raising the lower
    bound to 480 yields `>=480` and `>=1024`, which both admit 1024.
    """
    minima = [None, 100, 480, 600, 768, 1280, 12800]
    breakpoint_lists = [
        None, [768], [400, 800], [768, 1024], [1536], [1440, 1920],
        [768, 1536], [768, 1024, 1440],
    ]
    for minimum in minima:
        for breakpoints in breakpoint_lists:
            channels = required_channels(rules_markdown, breakpoints, minimum)
            probes = {1, 100, 399, 400, 479, 480, 481, 600, 767, 768, 1023, 1024,
                      1151, 1152, 1279, 1280, 1439, 1440, 1535, 1536, 1919, 1920,
                      12799, 12800, 20000}
            for width in probes:
                covering = [c for c in channels if width_in_channel(c, width)]
                assert len(covering) <= 1, (
                    f"width {width} satisfies {[c[0] for c in covering]} under "
                    f"minimum={minimum} breakpoints={breakpoints}"
                )


def test_the_walk_honours_the_declared_minimum(rules_markdown: str) -> None:
    """Verifies AC-0019: the completeness walk, not the derivation helper.

    Every derivation criterion asserts `required_channels` in isolation, so an
    implementation can satisfy all of them while the walk still derives its bands
    without the minimum and reports a supported surface incomplete.

    The 480 pair is the discriminating one. A no-minimum run over this set is
    already asserted by `test_a_single_channel_set_is_incomplete`, so pairing
    against it would add no observation; 480 drops nothing, so a walk that treats
    any declared minimum as one channel fails here.
    """
    four = _matrix(1280)
    assert evaluate_capture_set(rules_markdown, four, None, 1280) == ("complete", [])
    state, missing = evaluate_capture_set(rules_markdown, four, None, 480)
    assert state == "incomplete"
    assert _names(missing, "short-at-rest")
    assert evaluate_capture_set(rules_markdown, four, [768], 1280) == ("complete", [])


def test_the_inspection_result_honours_the_declared_minimum(
    rules_markdown: str,
) -> None:
    """Verifies AC-0020: the outermost observable an adopter records.

    `inspection_result` forwards to the walk, so AC-0019 stops one call frame
    short of what an adopter sees. A run recorded as incomplete for a surface
    captured at every width it supports is the outcome the Objective removes.
    """
    four = _matrix(1280)
    with_minimum = inspection_result(rules_markdown, four, [], None, 1280)
    assert with_minimum == {"state": "completed", "verdict": "pass"}
    assert is_completed_inspection_result(rules_markdown, with_minimum) is True
    without = inspection_result(rules_markdown, four, [], None, None)
    assert without["state"] == "incomplete"
    assert is_completed_inspection_result(rules_markdown, without) is False
