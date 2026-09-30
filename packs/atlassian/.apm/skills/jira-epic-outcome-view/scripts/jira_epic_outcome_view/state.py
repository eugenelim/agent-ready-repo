"""State observations for one Epic, read from the same Jira pass that
supplies the parent links.

Nothing here derives a duration that the flow skill already defines. Age,
blocked and what-moved are direct reads of Jira fields against two
anchors the caller states: the moment of the Jira read, and the flow
window. Keeping them here rather than in the row builder makes the one
rule that varies by instance -- whether a flagged field exists at all --
visible in a single place.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

# An instance without a flagged field must say so rather than report zero
# blocked: "none flagged" and "cannot tell" are different facts, and a
# reader acts on them differently.
NO_FLAGGED_FIELD = (
    "This Jira instance exposes no flagged field, so blocked work cannot be "
    "read here. This is not a report of zero blocked work."
)
NO_WORK_IN_FLIGHT_AGE = "No work is in flight for this Epic, so there is no age to state."
NO_FLAGGED_WORK = "No work in flight for this Epic is flagged."
NOTHING_MOVED = "No work for this Epic changed status category inside the window."

_HOURS_PRECISION = 2

# Jira Cloud writes its offset without a colon -- `2026-09-12T09:00:00.000+0000`
# -- which `datetime.fromisoformat` rejects on Python 3.10, the oldest
# interpreter this skill supports. Normalising it here is what keeps a
# Cloud timestamp a comparable instant rather than an unreadable string.
_OFFSET_WITHOUT_COLON = re.compile(r"([+-])(\d{2})(\d{2})$")


def parse_moment(value: str | None) -> datetime | None:
    """Parse a Jira instant into a timezone-aware UTC ``datetime``.

    Accepts a trailing ``Z``, an offset with or without its colon, and a
    timestamp with no offset at all, which is read as UTC. Returns
    ``None`` for anything unparseable rather than raising: a single
    malformed Jira timestamp must not withhold the whole view.

    The result is always aware, so two instants from two offsets compare
    as moments. Comparing their strings instead orders two entries either
    side of a daylight-saving change by their local clock faces.
    """
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    match = _OFFSET_WITHOUT_COLON.search(text)
    if match is not None:
        text = f"{text[: match.start()]}{match.group(1)}{match.group(2)}:{match.group(3)}"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def window_bounds(window: Mapping[str, str]) -> tuple[datetime | None, datetime | None]:
    """Resolve the flow window's inclusive ``YYYY-MM-DD`` bounds to instants.

    The upper bound is the start of the day after ``to``, so the whole of
    the final day counts -- an exclusive end is the only form that admits
    a timestamp at 23:59 on that day.
    """
    start = _start_of_day(window.get("from"))
    end_day = _start_of_day(window.get("to"))
    end = end_day + timedelta(days=1) if end_day is not None else None
    return start, end


def _start_of_day(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        day = date.fromisoformat(value)
    except ValueError:
        return None
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def flagged_field_available(jira_state: Mapping[str, Mapping[str, Any]]) -> bool:
    """Whether this instance exposes a flagged field at all.

    The reader resolves the field from the instance catalogue, so a state
    record carries a boolean when the field exists and ``None`` when it
    does not. One record answering the question answers it for the
    instance, which is why this is a global read rather than a per-Epic one.
    """
    return any(isinstance(record.get("flagged"), bool) for record in jira_state.values())


def observe(
    *,
    issue_keys: Sequence[str],
    in_flight_keys: Sequence[str],
    jira_state: Mapping[str, Mapping[str, Any]],
    window: Mapping[str, str],
    jira_taken_at: str,
    flagged_supported: bool,
) -> dict[str, Any]:
    """The four state observations for one Epic.

    ``jira_taken_at`` is the "now" every age is measured against: the view
    states two moments rather than implying one snapshot, so age has to be
    anchored to the pass that read the timestamp, not to wall clock at
    render time.
    """
    now = parse_moment(jira_taken_at)
    return {
        "age_in_flight": _age(in_flight_keys, jira_state, now),
        "blocked": _blocked(in_flight_keys, jira_state, flagged_supported),
        "what_moved": _what_moved(issue_keys, jira_state, window),
    }


def _age(
    in_flight_keys: Sequence[str],
    jira_state: Mapping[str, Mapping[str, Any]],
    now: datetime | None,
) -> dict[str, Any]:
    issues: dict[str, Any] = {}
    for key in in_flight_keys:
        changed_at = (jira_state.get(key) or {}).get("status_category_changed_at")
        moment = parse_moment(changed_at)
        hours = None
        if moment is not None and now is not None:
            hours = round((now - moment).total_seconds() / 3600, _HOURS_PRECISION)
        issues[key] = {"since": changed_at, "hours": hours}
    if not issues:
        return {"none": True, "statement": NO_WORK_IN_FLIGHT_AGE, "issues": {}}
    return {"none": False, "statement": "", "issues": issues}


def _blocked(
    in_flight_keys: Sequence[str],
    jira_state: Mapping[str, Mapping[str, Any]],
    flagged_supported: bool,
) -> dict[str, Any]:
    if not flagged_supported:
        return {"supported": False, "none": False, "statement": NO_FLAGGED_FIELD, "issues": {}}
    issues = {
        key: {"since": (jira_state.get(key) or {}).get("flagged_changed_at")}
        for key in in_flight_keys
        if (jira_state.get(key) or {}).get("flagged") is True
    }
    if not issues:
        return {"supported": True, "none": True, "statement": NO_FLAGGED_WORK, "issues": {}}
    return {"supported": True, "none": False, "statement": "", "issues": issues}


def _what_moved(
    issue_keys: Iterable[str],
    jira_state: Mapping[str, Mapping[str, Any]],
    window: Mapping[str, str],
) -> dict[str, Any]:
    start, end = window_bounds(window)
    moved = []
    for key in issue_keys:
        moment = parse_moment((jira_state.get(key) or {}).get("status_category_changed_at"))
        if moment is None:
            continue
        if start is not None and moment < start:
            continue
        if end is not None and moment >= end:
            continue
        moved.append(key)
    moved.sort()
    if not moved:
        return {"none": True, "statement": NOTHING_MOVED, "issues": [], "window": dict(window)}
    return {"none": False, "statement": "", "issues": moved, "window": dict(window)}
