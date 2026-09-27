#!/usr/bin/env python3
"""Decide whether an artifact's status is terminal, for the closure check.

**These are read-side projections, not defining homes.** A closure verdict rests
on terminality, and the surfaces that own it sit in sibling skills that this one
may not reach: a cross-skill relative import is not portable across adapter
projections, copying a module between skill ``scripts/`` directories is banned,
and a new ``shared-libs`` boundary is outside this change. A projection pinned by
a parity assertion is the only remaining shape, so each declaration names the
upstream it derives from and a gate-chain step re-checks the agreement against
the live corpus on every pull request.

Three asymmetries are deliberate.

**Intents are enumerated; briefs are derived; specs are partially enumerated.**
No shipped surface marks an intent status terminal — ``intent_shape.STATUS_VALUES``
is a flat tuple and its state-coherence table constrains which *records* a status
requires, not whether the status ends anything. So the intent set is written out
here and pinned against the parent intent's prose table. Briefs are the opposite:
terminality is already derivable from the shipped transition table's
no-outgoing-edge property, so it is derived rather than restated. Specs are
between the two: the vocabulary has a shipped home
(``lint-spec-status.py :: CANONICAL_STATUSES``), and this projection is pinned
against it; but no transition table exists for specs, so the terminal subset
(``Shipped``, ``Archived``) is enumerated here because no upstream carries it.

Do not confuse any of these with ``workspace_status_engine._TERMINAL_STATUS_BY_KIND``,
which maps ``intent`` to ``{Accepted, Fulfilled}`` and ``spec`` to ``{Shipped}``
only. That is collection-routing terminality — the status at which a kind rests
in its current collection — and reusing it here would make ``Accepted`` terminal
for intents and omit ``Archived`` for specs. Both are wrong: ``Accepted`` is live
work, and ``Archived`` is a lifecycle-terminal spec status carried by 6 specs in
the live corpus (measured 2026-09-27).

**An unknown status is live, never terminal.** ``eligible`` authorises a
terminal write, so the direction that refuses to authorise is the safe one. This
matters most for briefs: a typo and an upstream addition both have no outgoing
edge, so the edge table alone would call them terminal.
"""

from __future__ import annotations

from typing import Iterable, Mapping, NamedTuple


class UpstreamPin(NamedTuple):
    """The surface a projection is parity-checked against.

    ``slug`` locates the artifact by its declared identity rather than by a
    filename stem, because an intent is reissued at a new ordinal prefix when
    its altitude changes and a stem-keyed pin would then resolve to a tombstone.
    """

    slug: str
    section: str


INTENT_TERMINALITY_UPSTREAM = UpstreamPin(
    slug="lifecycle-and-closure",
    section="The lifecycle > Intent states, Terminal column",
)

BRIEF_TERMINALITY_UPSTREAM = UpstreamPin(
    slug="author-delivery-brief/scripts/brief_shape.py",
    section="BRIEF_TRANSITIONS, no-outgoing-edge property",
)


# ── Intents: enumerated, because no shipped surface carries this ──────────────

INTENT_STATUS_VOCABULARY: tuple[str, ...] = (
    "Draft",
    "Accepted",
    "Fulfilled",
    "Withdrawn",
    "Cancelled",
    "Superseded",
)

TERMINAL_INTENT_STATUSES: frozenset[str] = frozenset(
    {"Fulfilled", "Withdrawn", "Cancelled", "Superseded"}
)


def is_intent_terminal(status: str) -> bool:
    """True when this intent status ends the intent's lifecycle."""
    return status in TERMINAL_INTENT_STATUSES


# ── Briefs: derived, because a shipped surface carries this ───────────────────

BRIEF_STATUS_VOCABULARY: tuple[str, ...] = (
    "Draft",
    "Ready",
    "Executing",
    "Shipped",
    "Withdrawn",
    "Cancelled",
)

BRIEF_TRANSITIONS_PROJECTION: frozenset[tuple[str, str]] = frozenset(
    {
        ("Draft", "Ready"),
        ("Draft", "Withdrawn"),
        ("Ready", "Draft"),
        ("Ready", "Executing"),
        ("Ready", "Withdrawn"),
        ("Executing", "Ready"),
        ("Executing", "Shipped"),
        ("Executing", "Cancelled"),
    }
)


def _has_outgoing_edge(status: str, edges: Iterable[tuple[str, str]]) -> bool:
    return any(src == status for src, _ in edges)


def is_brief_terminal(status: str) -> bool:
    """True when this brief status ends the brief's lifecycle.

    Two parts, and the vocabulary check comes first. A status outside the
    vocabulary has no outgoing edge either, so testing the edge table alone
    would call an unrecognised value terminal.
    """
    if status not in BRIEF_STATUS_VOCABULARY:
        return False
    return not _has_outgoing_edge(status, BRIEF_TRANSITIONS_PROJECTION)


# ── The parity assertions, which make the projections checkable ───────────────


def intent_parity_disagreements(upstream: Mapping[str, bool]) -> list[str]:
    """Statuses where this projection and the upstream table disagree.

    ``upstream`` maps each status to the upstream's Terminal verdict. Iterating
    the vocabulary rather than the upstream's keys means a status present in one
    and missing from the other is reported instead of skipped.
    """
    disagreements: list[str] = []
    for status in INTENT_STATUS_VOCABULARY:
        if status not in upstream or upstream[status] != is_intent_terminal(status):
            disagreements.append(status)
    for status in upstream:
        if status not in INTENT_STATUS_VOCABULARY:
            disagreements.append(status)
    return disagreements


def brief_parity_disagreements(upstream_edges: Iterable[tuple[str, str]]) -> list[str]:
    """Statuses where terminality derived from upstream edges disagrees here."""
    edges = frozenset(upstream_edges)
    disagreements: list[str] = []
    for status in BRIEF_STATUS_VOCABULARY:
        upstream_terminal = not _has_outgoing_edge(status, edges)
        if upstream_terminal != is_brief_terminal(status):
            disagreements.append(status)
    return disagreements


# ── Specs: vocabulary pinned, terminal subset enumerated ─────────────────────
# Vocabulary upstream: packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py
# :: CANONICAL_STATUSES
# The vocabulary is parity-pinned against that symbol (spec_parity_disagreements).
# No transition table exists for specs, so the terminal subset (Shipped, Archived)
# is enumerated here: no upstream carries lifecycle terminality for this kind.
# See the module docstring for the _TERMINAL_STATUS_BY_KIND distinction.

SPEC_TERMINALITY_UPSTREAM = UpstreamPin(
    slug="work-loop/scripts/lint-spec-status.py",
    section="CANONICAL_STATUSES, vocabulary membership",
)

SPEC_STATUS_VOCABULARY: tuple[str, ...] = (
    "Draft",
    "Approved",
    "Implementing",
    "Shipped",
    "Archived",
)

TERMINAL_SPEC_STATUSES: frozenset[str] = frozenset({"Shipped", "Archived"})


def is_spec_terminal(status: str) -> bool:
    """True when this spec status ends the spec's lifecycle.

    Lifecycle-terminal statuses: Shipped and Archived. An unknown status is live
    — safe direction: eligible authorises a terminal write.

    Note: this is **not** ``workspace_status_engine._TERMINAL_STATUS_BY_KIND``
    for specs, which maps to ``{"Shipped"}`` only (collection-routing terminality).
    ``Archived`` is lifecycle-terminal: 6 specs in the live corpus carry it
    (measured 2026-09-27) and it ends a spec's own progression.
    """
    return status in TERMINAL_SPEC_STATUSES


def spec_parity_disagreements(upstream_vocabulary: Iterable[str]) -> list[str]:
    """Statuses where the spec vocabulary projection and the upstream disagree.

    ``upstream_vocabulary`` is the full set of statuses the upstream home
    declares (``lint-spec-status.py :: CANONICAL_STATUSES``). Any status present
    in one and absent from the other is reported.

    This checks vocabulary membership only. The terminal subset has no upstream
    table to compare against, so its correctness rests on the module docstring
    and reviewer attention rather than a mechanical parity check.
    """
    upstream = frozenset(upstream_vocabulary)
    disagreements: list[str] = []
    for status in SPEC_STATUS_VOCABULARY:
        if status not in upstream:
            disagreements.append(status)
    for status in upstream:
        if status not in SPEC_STATUS_VOCABULARY:
            disagreements.append(status)
    return disagreements
