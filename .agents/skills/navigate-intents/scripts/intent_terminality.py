"""Decide whether an artifact's status is terminal, for the outstanding-work view.

These projections match the leading-word rule and terminal sets in
close-work's terminality module; the parity tool checks them on every
pull request.

Three asymmetries are deliberate.

Intents are enumerated; briefs are derived; specs are partially enumerated.
No shipped surface marks an intent status terminal, so the intent set is
written out here and pinned against the parent intent's prose table.
Briefs are derived from the transition projection rather than restated,
because the transition table already implies the member set. Specs: the
vocabulary has a shipped home in lint-spec-status.py, and the terminal
subset (Shipped, Archived) is enumerated here because no upstream carries
lifecycle terminality for that kind.

An unknown status is live, never terminal. The safe direction is to
refuse to authorise — eligible authorises a terminal write.
"""

from __future__ import annotations

from typing import Any


def _extract_status_token(raw: str) -> str:
    """Return the leading word after truncating at ' (', ' →', or '<!--'.

    Matches the rule in close-work's terminality module and in
    work-loop's lint-spec-status.py.
    """
    text = raw
    for delim in (" (", " →", "<!--"):
        idx = text.find(delim)
        if idx != -1:
            text = text[:idx]
    return text.strip().split()[0] if text.strip() else ""


# ── Intents: enumerated, because no shipped surface carries this ──────────────

TERMINAL_INTENT_STATUSES: frozenset[str] = frozenset(
    {"Fulfilled", "Withdrawn", "Cancelled", "Superseded"}
)


def is_intent_terminal(status: str) -> bool:
    """True when this intent status ends the intent's lifecycle."""
    return _extract_status_token(status) in TERMINAL_INTENT_STATUSES


# ── Briefs: derived, because a shipped surface carries this ───────────────────

_BRIEF_TRANSITIONS: frozenset[tuple[str, str]] = frozenset({
    ("Draft", "Ready"),
    ("Draft", "Withdrawn"),
    ("Ready", "Draft"),
    ("Ready", "Executing"),
    ("Ready", "Withdrawn"),
    ("Executing", "Ready"),
    ("Executing", "Shipped"),
    ("Executing", "Cancelled"),
})

_BRIEF_STATUS_VOCABULARY: frozenset[str] = frozenset(
    s for pair in _BRIEF_TRANSITIONS for s in pair
)


def is_brief_terminal(status: str) -> bool:
    """True when this brief status ends the brief's lifecycle.

    Two parts: vocabulary check first. A status outside the vocabulary has no
    outgoing edge either, so testing the edge table alone would call an
    unrecognised value terminal.
    """
    token = _extract_status_token(status)
    if token not in _BRIEF_STATUS_VOCABULARY:
        return False
    return not any(src == token for src, _ in _BRIEF_TRANSITIONS)


# ── Specs: vocabulary pinned, terminal subset enumerated ─────────────────────
# Vocabulary upstream: work-loop/scripts/lint-spec-status.py :: CANONICAL_STATUSES
# No transition table exists for specs, so the terminal subset is enumerated.

TERMINAL_SPEC_STATUSES: frozenset[str] = frozenset({"Shipped", "Archived"})


def is_spec_terminal(status: str) -> bool:
    """True when this spec status ends the spec's lifecycle.

    Lifecycle-terminal statuses: Shipped and Archived. An unknown status is
    live.
    """
    return _extract_status_token(status) in TERMINAL_SPEC_STATUSES


# ── Unified interface ─────────────────────────────────────────────────────────


def is_node_terminal(node: dict[str, Any]) -> bool:
    """True when this graph node's recorded status is terminal."""
    node_type = node.get("type", "")
    status = node.get("status", "")
    if node_type == "intent":
        return is_intent_terminal(status)
    if node_type == "brief":
        return is_brief_terminal(status)
    if node_type == "spec":
        return is_spec_terminal(status)
    return False
