"""Contract tests for the rendered-page capture set, record, and step split.

Like the severity suite next to this one, these read
`references/rendered-page-inspection.md` and derive their expectations from its
tables. The evaluators in the shared reader implement the rules *as the tables
state them* — a table change moves the outcome, which is what makes these checks
able to fail.
"""

from __future__ import annotations

import pytest

from frontend_engineering_rendered_page_rules import (
    capture_record_fields,
    evaluate_capture_set,
    evaluate_record,
    findings_for,
    judgement_request_fields,
    read_rules,
    step_rules,
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


def complete_set() -> list[dict[str, int | str]]:
    """One capture at each of the four required combinations."""
    return [
        {"route": "/a", "viewport-width": 390, "viewport-height": 600, "scroll-position": 0, "page-scrollable": "yes"},
        {"route": "/a", "viewport-width": 390, "viewport-height": 600, "scroll-position": 800, "page-scrollable": "yes"},
        {"route": "/a", "viewport-width": 1280, "viewport-height": 900, "scroll-position": 0, "page-scrollable": "yes"},
        {"route": "/a", "viewport-width": 1280, "viewport-height": 900, "scroll-position": 800, "page-scrollable": "yes"},
    ]


# ── capture-set completeness ────────────────────────────────────────────────

def test_a_set_without_a_short_viewport_capture_is_rejected(rules_markdown: str) -> None:
    """Verifies: the capture set contains a capture at a viewport height of at
    most 600 CSS pixels."""
    captures = [c for c in complete_set() if int(c["viewport-height"]) > 600]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", "a set with no short-viewport capture was accepted"
    assert "short-at-rest" in missing and "short-scrolled" in missing


def test_a_set_without_a_tall_viewport_capture_is_rejected(rules_markdown: str) -> None:
    """Verifies: the capture set contains a capture at a viewport height of at
    least 900 CSS pixels."""
    captures = [c for c in complete_set() if int(c["viewport-height"]) < 900]
    status, missing = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", "a set with no tall-viewport capture was accepted"
    assert "tall-at-rest" in missing and "tall-scrolled" in missing


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
    assert expected_missing in missing


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
    assert sorted(stated) == sorted(REQUIRED)
    assert sorted(judgement_request_fields(rules_markdown)) == sorted(
        capture_record_fields(rules_markdown)
    ), "the judgement request and the capture record no longer carry the same fields"


@pytest.mark.parametrize("absent_field", REQUIRED)
def test_a_record_missing_a_field_yields_no_finding(
    rules_markdown: str, absent_field: str
) -> None:
    """Verifies: a capture missing any required field produces no finding."""
    record: dict[str, object] = {f: 1 for f in REQUIRED}
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
    record: dict[str, object] = {f: 1 for f in REQUIRED}
    del record[absent_field]
    status, absent = evaluate_record(rules_markdown, record)
    assert status == "unusable", f"a record with no {absent_field} was not unusable"
    assert absent == [absent_field]


def test_a_complete_record_is_usable_and_can_carry_a_finding(
    rules_markdown: str,
) -> None:
    """The green path for the record shape, for the same reason the capture-set
    green path exists."""
    record: dict[str, object] = {f: 1 for f in REQUIRED}
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
