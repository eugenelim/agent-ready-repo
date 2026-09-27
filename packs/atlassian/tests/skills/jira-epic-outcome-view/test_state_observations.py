"""The four state observations: age, blocked, since when, and what moved.

Every one is asserted against a fixture that carries an in-flight issue,
a flagged issue, an instance exposing no flagged field at all, and an
Epic with no in-flight work. The last two are the cases a passing
implementation is most likely to render as a silent zero.
"""
from __future__ import annotations

import pytest

WINDOW = {"from": "2026-08-25", "to": "2026-09-24"}
FLOW_MOMENT = "2026-09-24T11:30:00Z"
JIRA_MOMENT = "2026-09-24T11:30:12Z"

IN_FLIGHT_SINCE = "2026-09-10T09:00:00+00:00"
FLAGGED_SINCE = "2026-09-12T09:00:00+00:00"
BEFORE_WINDOW = "2026-06-01T09:00:00+00:00"
AFTER_WINDOW = "2026-09-25T09:00:00+00:00"

# 2026-09-10T09:00:00Z to 2026-09-24T11:30:12Z is 14 days, 2 hours, 30
# minutes and 12 seconds: 336 + 2.503333 hours, rounded to two places.
EXPECTED_AGE_HOURS = 338.5


@pytest.fixture
def view(load_module):
    return load_module("view")


def _row(key, *, delivered=False, wip=False, bucket="feature"):
    return {
        "key": key,
        "issue_created": "2026-08-01T09:00:00+00:00",
        "first_commitment_at": "2026-08-02T09:00:00+00:00",
        "first_delivery_at": "2026-08-06T09:00:00+00:00" if delivered else None,
        "cycle_eligible": delivered,
        "cycle_time_hours": 96.0 if delivered else None,
        "lead_time_hours": 96.0 if delivered else None,
        "flow_efficiency": 0.5,
        "rework_count": 0,
        "issuetype_at_delivery": "Story",
        "issuetype_bucket": bucket,
        "team": "Atlas",
        "delivered_in_window": delivered,
        "cancelled_in_window": False,
        "wip_at_to": wip,
    }


@pytest.fixture
def rows():
    return [
        _row("PROJ-1", delivered=True),
        # PROJ-2 and PROJ-5 belong to the same Epic as PROJ-1 and sit either
        # side of the window. They are what make the window bounds load-
        # bearing: without them, dropping a bound changes no assertion.
        _row("PROJ-2", delivered=True),
        _row("PROJ-3", wip=True),
        _row("PROJ-5", delivered=True),
        _row("PROJ-9", delivered=True),
    ]


@pytest.fixture
def parents():
    return {
        "PROJ-1": "PROJ-100",
        "PROJ-2": "PROJ-100",
        "PROJ-3": "PROJ-100",
        "PROJ-5": "PROJ-100",
        "PROJ-9": "PROJ-200",
    }


def _state(*, flagged_supported: bool):
    """Jira state for the scope.

    ``flagged`` is ``None`` on an instance with no flagged field, and a
    boolean on one that has it. That is the distinction the blocked
    observation turns on.
    """
    def flag(value):
        return value if flagged_supported else None

    return {
        "PROJ-1": {
            "status_category": "Done",
            "status_category_changed_at": IN_FLIGHT_SINCE,
            "flagged": flag(False),
            "flagged_changed_at": None,
        },
        "PROJ-3": {
            "status_category": "In Progress",
            "status_category_changed_at": IN_FLIGHT_SINCE,
            "flagged": flag(True),
            "flagged_changed_at": FLAGGED_SINCE if flagged_supported else None,
        },
        "PROJ-2": {
            "status_category": "Done",
            "status_category_changed_at": BEFORE_WINDOW,
            "flagged": flag(False),
            "flagged_changed_at": None,
        },
        "PROJ-5": {
            "status_category": "Done",
            "status_category_changed_at": AFTER_WINDOW,
            "flagged": flag(False),
            "flagged_changed_at": None,
        },
        # PROJ-9 last moved well before the window opened, so its Epic has
        # nothing in flight and nothing that moved.
        "PROJ-9": {
            "status_category": "Done",
            "status_category_changed_at": BEFORE_WINDOW,
            "flagged": flag(False),
            "flagged_changed_at": None,
        },
    }


def _build(view, rows, parents, *, flagged_supported=True):
    built = view.build_epic_rows(
        per_issue_rows=rows,
        parents=parents,
        jira_state=_state(flagged_supported=flagged_supported),
        outcomes={"PROJ-100": None, "PROJ-200": None},
        window=WINDOW,
        flow_taken_at=FLOW_MOMENT,
        jira_taken_at=JIRA_MOMENT,
    )
    return {row["epic"]: row for row in built}


def test_age_is_now_minus_the_status_category_change_per_in_flight_issue(
    view, rows, parents
):
    """Age is anchored to the stated Jira-read moment, not to wall clock:
    the view states two moments and an age measured against a third would
    belong to neither."""
    age = _build(view, rows, parents)["PROJ-100"]["delivery"]["observations"]["age_in_flight"]

    assert age["none"] is False
    assert set(age["issues"]) == {"PROJ-3"}
    assert age["issues"]["PROJ-3"]["since"] == IN_FLIGHT_SINCE
    assert age["issues"]["PROJ-3"]["hours"] == EXPECTED_AGE_HOURS


def test_blocked_reads_the_flagged_field_and_says_since_when(view, rows, parents):
    """Blocked is the flagged field, and since-when is that field's own
    last-changed moment -- not the status change, which is a different
    fact about a different field."""
    blocked = _build(view, rows, parents)["PROJ-100"]["delivery"]["observations"]["blocked"]

    assert blocked["supported"] is True
    assert blocked["none"] is False
    assert set(blocked["issues"]) == {"PROJ-3"}
    assert blocked["issues"]["PROJ-3"]["since"] == FLAGGED_SINCE


def test_an_instance_with_no_flagged_field_says_so_rather_than_reporting_none(
    view, rows, parents
):
    """"Nothing is flagged" and "this instance cannot tell you" are
    different answers. Reporting the first for the second is the failure
    this pins: a reader would conclude nothing is blocked."""
    blocked = _build(view, rows, parents, flagged_supported=False)["PROJ-100"][
        "delivery"
    ]["observations"]["blocked"]

    assert blocked["supported"] is False
    assert blocked["none"] is False
    assert "no flagged field" in blocked["statement"].lower()


def test_what_moved_is_the_status_category_changes_inside_the_flow_window(
    view, rows, parents
):
    """The same window the throughput count uses. Both bounds bite: PROJ-2
    moved before it opened and PROJ-5 after it closed, and both belong to
    the Epic under assertion, so dropping either bound changes the list."""
    observations = _build(view, rows, parents)["PROJ-100"]["delivery"]["observations"]
    moved = observations["what_moved"]

    assert moved["none"] is False
    assert moved["issues"] == ["PROJ-1", "PROJ-3"]
    assert "PROJ-2" not in moved["issues"]
    assert "PROJ-5" not in moved["issues"]
    assert moved["window"] == WINDOW


def test_an_epic_with_nothing_in_flight_renders_each_observation_as_an_explicit_none(
    view, rows, parents
):
    """A blank is indistinguishable from an unrendered field. PROJ-200 has
    one delivered issue, nothing in flight, and nothing that moved inside
    the window, so all three observations must state that in words."""
    observations = _build(view, rows, parents)["PROJ-200"]["delivery"]["observations"]

    for name in ("age_in_flight", "blocked", "what_moved"):
        assert observations[name]["none"] is True, name
        assert observations[name]["statement"].strip() != "", name
    assert observations["age_in_flight"]["issues"] == {}
    assert observations["blocked"]["issues"] == {}
    assert observations["what_moved"]["issues"] == []
