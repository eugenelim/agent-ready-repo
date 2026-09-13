"""T6a: a page that cannot scroll is recorded, not marked incomplete.

The end-to-end run measured 17 of 32 captures unable to reach a non-zero scroll
position, because the fixture is shorter than the viewport. Under the original
rule every such page was permanently `incomplete`, which would have marked every
ordinary short surface — a sign-in form, a 404, a settings panel — as never
inspectable.

The amended rule admits a recorded `page-scrollable: no`. These tests hold the
amendment to its narrow meaning: it excuses the unscrollable case and nothing
else.
"""

from __future__ import annotations

import pytest
from frontend_engineering_rendered_page_rules import (
    capture_record_fields,
    evaluate_capture_set,
    evaluate_record,
    inspection_section,
    read_rules,
    read_skill,
    required_captures,
)

REQUIRED = ["route", "viewport-width", "viewport-height", "scroll-position", "page-scrollable"]


@pytest.fixture(scope="module")
def rules_markdown() -> str:
    return read_rules()


def _capture(height: int, scroll: int, scrollable: str) -> dict[str, int | str]:
    return {
        "route": "/a",
        "viewport-width": 390 if height <= 600 else 1280,
        "viewport-height": height,
        "scroll-position": scroll,
        "page-scrollable": scrollable,
    }


def unscrollable_set() -> list[dict[str, int | str]]:
    """What the run actually produced for a short page: at-rest only, at both
    heights, each recorded as not scrollable."""
    return [_capture(600, 0, "no"), _capture(900, 0, "no")]


def scrollable_but_missing_set() -> list[dict[str, int | str]]:
    """A page that *can* scroll, where the scrolled captures were simply not
    taken. This is the case the amendment must NOT excuse."""
    return [_capture(600, 0, "yes"), _capture(900, 0, "yes")]


def test_an_unscrollable_page_yields_a_complete_set(rules_markdown: str) -> None:
    """Verifies the amended criterion's new branch: the scrolled requirement is
    satisfied at a height where the page does not scroll."""
    status, missing = evaluate_capture_set(rules_markdown, unscrollable_set())
    assert status == "complete", (
        f"a short page that cannot scroll was still incomplete; missing={missing}"
    )
    assert missing == []


def test_a_scrollable_page_missing_its_scrolled_captures_is_still_incomplete(
    rules_markdown: str,
) -> None:
    """The amendment's limit. Without this it would excuse every missing scrolled
    capture rather than only the unscrollable ones, which is a strictly weaker
    contract than the one before the amendment."""
    status, missing = evaluate_capture_set(rules_markdown, scrollable_but_missing_set())
    assert status == "incomplete", (
        "a scrollable page with no scrolled capture was accepted as complete"
    )
    # Entries carry their route now that completeness is evaluated per route.
    assert any("short-scrolled" in entry for entry in missing), missing
    assert any("tall-scrolled" in entry for entry in missing), missing


def test_the_branch_is_not_inferred_from_a_zero_scroll_position(
    rules_markdown: str,
) -> None:
    """`page-scrollable` has to be recorded. A capture with no such value sitting
    at scroll 0 is indistinguishable from one nobody scrolled, and must not pass."""
    unrecorded = [
        {k: v for k, v in c.items() if k != "page-scrollable"}
        for c in unscrollable_set()
    ]
    status, missing = evaluate_capture_set(rules_markdown, unrecorded)
    assert status == "incomplete", (
        "an unrecorded page-scrollable was inferred from a scroll position of 0"
    )
    assert missing


@pytest.mark.parametrize("value", ["yes", "YES", "true", "maybe", ""])
def test_only_a_recorded_no_satisfies_the_branch(
    rules_markdown: str, value: str
) -> None:
    captures = [_capture(600, 0, value), _capture(900, 0, value)]
    status, _ = evaluate_capture_set(rules_markdown, captures)
    assert status == "incomplete", f"page-scrollable={value!r} satisfied the branch"


def test_page_scrollable_is_a_required_capture_record_field(
    rules_markdown: str,
) -> None:
    """Verifies the amended capture-state criterion."""
    assert "page-scrollable" in capture_record_fields(rules_markdown)
    assert sorted(capture_record_fields(rules_markdown)) == sorted(REQUIRED)


def test_a_record_without_page_scrollable_is_unusable(rules_markdown: str) -> None:
    """It is unusable on the same terms as the other required fields, not a
    special case with a softer outcome."""
    record: dict[str, object] = dict.fromkeys(REQUIRED, 1)
    del record["page-scrollable"]
    status, absent = evaluate_record(rules_markdown, record)
    assert status == "unusable"
    assert absent == ["page-scrollable"]


def test_both_scrolled_rules_carry_the_alternative_branch(
    rules_markdown: str,
) -> None:
    """Both heights, not one. Fixing only the short height would leave every tall
    short-page capture incomplete, which is most of what the run measured."""
    captures = required_captures(rules_markdown)
    for name in ("short-scrolled", "tall-scrolled"):
        assert "page-scrollable: no" in captures[name][1], (
            f"{name} does not carry the unscrollable branch"
        )
    for name in ("short-at-rest", "tall-at-rest"):
        assert "page-scrollable" not in captures[name][1], (
            f"{name} is an at-rest capture and must not carry the branch"
        )


def test_the_skill_states_the_rule() -> None:
    section = inspection_section(read_skill())
    assert "page-scrollable" in section, (
        "the skill's capture section does not carry the unscrollable rule"
    )
