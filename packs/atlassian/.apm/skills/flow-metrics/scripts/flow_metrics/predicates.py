"""Core population predicates from docs/specs/flow-metrics.md §
"Metric definitions" → "Core population predicates".

Each predicate is a pure function of a :class:`Timeline` and a window.
The four predicates are intentionally independent — an issue can satisfy
:func:`cancelled_in_window` AND :func:`wip_at_to` simultaneously (the
cancel-then-reopen-still-active case, Decision #29).

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .timeline import Timeline


def _in_window(instant: datetime, window: Any) -> bool:
    """Half-open membership: ``[from_utc, to_exclusive_utc)``."""
    return window.from_utc <= instant < window.to_exclusive_utc


def wip_instant(window: Any) -> datetime:
    """Spec-defined WIP-instant: the last representable instant of the
    inclusive window — ``(to + 1 day) 00:00 UTC − 1 microsecond``.

    Both :func:`wip_at_to` and Flow Load (T6) sample at this anchor so
    the last Flow Load sample is identical to the WIP count.
    """
    return window.to_exclusive_utc - timedelta(microseconds=1)


def delivered_in_window(timeline: Timeline, window: Any) -> bool:
    """First-ever transition into ``delivery_state`` falls in window.

    Reopen-and-redeliver does NOT create a second delivery — the second
    transition into ``delivery_state`` is rework, not throughput.
    """
    first = timeline.first_canonical_transition_into(timeline.config.delivery_state)
    if first is None:
        return False
    return _in_window(first, window)


def cycle_eligible(timeline: Timeline, window: Any) -> bool:
    """Delivered-in-window AND has a commitment_state transition at or
    before first-ever delivery.

    An issue delivered without ever entering ``commitment_state``
    (e.g. ``Backlog → Done`` directly) is delivered-in-window but NOT
    cycle-eligible.
    """
    if not delivered_in_window(timeline, window):
        return False
    delivery_ts = timeline.first_canonical_transition_into(timeline.config.delivery_state)
    if delivery_ts is None:
        return False
    commitment = timeline.config.commitment_state
    for t in timeline.status_transitions:
        if t.timestamp > delivery_ts:
            break
        if t.to_canonical == commitment:
            return True
    return False


def cancelled_in_window(timeline: Timeline, window: Any) -> bool:
    """At least one transition INTO a terminal_non_delivery state in
    window AND the issue is NOT delivered-in-window.

    Cancellation followed by a reopen still counts — the team's act of
    cancelling is what shows up in ``notes``. An issue that's
    cancel-then-reopen-and-still-active-at-`--to` satisfies BOTH this
    predicate AND :func:`wip_at_to`; both signals are reported.
    """
    if delivered_in_window(timeline, window):
        return False
    terminal = timeline.config.terminal_non_delivery_states
    for t in timeline.status_transitions:
        if t.to_canonical in terminal and _in_window(t.timestamp, window):
            return True
    return False


def wip_at_to(timeline: Timeline, window: Any) -> bool:
    """Canonical state at the WIP-instant ∈ ``active_states`` AND NOT
    delivered-in-window.

    Cancelled-in-window membership is intentionally NOT part of this
    predicate — a cancel-then-reopen issue whose state at the
    WIP-instant is active is BOTH cancelled-in-window AND wip_at_to,
    per Decision #29.
    """
    if delivered_in_window(timeline, window):
        return False
    state = timeline.state_at(wip_instant(window))
    return state in timeline.config.active_states


__all__ = [
    "cancelled_in_window",
    "cycle_eligible",
    "delivered_in_window",
    "wip_at_to",
    "wip_instant",
]
