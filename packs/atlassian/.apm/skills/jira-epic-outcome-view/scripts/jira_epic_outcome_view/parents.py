"""Resolve each issue's parent chain to the Epic rung.

A flow per-issue row carries no Epic and no parent field, so the join has
to come from this view's own read. Jira Software nests Epic > Story >
Subtask, so a subtask's immediate parent is a Story and reaching its Epic
takes two hops.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping

#: A chain longer than this is treated as unresolvable. Jira's own
#: hierarchy is three rungs; a deeper walk means the data is cyclic or
#: the instance uses a hierarchy this view does not model, and either way
#: the honest answer is to surface the issue rather than guess an Epic.
MAX_HOPS = 8

#: Why a chain ended without reaching an in-scope Epic. The three cases
#: are distinguished here because this is the only place that still sees
#: the raw parent link: once the walk has returned ``None`` the reasons
#: are indistinguishable, and one of them would have to be guessed.
NO_PARENT_LINK = "no parent link was recorded for this issue"
PARENT_OUTSIDE_SCOPE = "the parent chain ends at {parent}, which is not an in-scope Epic"
CYCLE_OR_HOP_LIMIT = (
    "the parent chain loops, or is longer than the {max_hops}-hop limit, so it "
    "never reached an in-scope Epic"
)


def resolve_epics(
    parent_links: Mapping[str, str | None],
    epic_keys: Iterable[str],
    *,
    max_hops: int = MAX_HOPS,
) -> dict[str, str | None]:
    """Map each issue key to its in-scope Epic, or ``None``.

    ``parent_links`` is the raw immediate-parent read: issue key to its
    immediate parent's key. The returned mapping is what the row builder
    consumes -- issue key to Epic key, whatever the depth. ``None`` means
    the chain never reached an in-scope Epic, which the view renders
    rather than drops. ``chain_end_reasons`` says why, for each of those.
    """
    epics = set(epic_keys)
    return {key: _walk(key, parent_links, epics, max_hops)[0] for key in parent_links}


def chain_end_reasons(
    parent_links: Mapping[str, str | None],
    epic_keys: Iterable[str],
    *,
    max_hops: int = MAX_HOPS,
) -> dict[str, str]:
    """Why each unresolved issue's chain ended, keyed by issue.

    Only issues whose walk reached no in-scope Epic appear. The reason is
    carried out of this module rather than re-derived from the resolved
    mapping: by then a parent outside the scope and a parent in a cycle
    are both ``None``, and any statement about which one happened would
    be a guess rendered as a fact.
    """
    epics = set(epic_keys)
    reasons: dict[str, str] = {}
    for key in parent_links:
        epic, reason = _walk(key, parent_links, epics, max_hops)
        if epic is None and reason is not None:
            reasons[key] = reason
    return reasons


def _walk(
    key: str,
    parent_links: Mapping[str, str | None],
    epics: set[str],
    max_hops: int,
) -> tuple[str | None, str | None]:
    """The issue's Epic, or ``None`` and the reason the chain ended."""
    if key in epics:
        return key, None
    seen = {key}
    current = key
    for _ in range(max_hops):
        parent = parent_links.get(current)
        if parent is None:
            # The first hop finding nothing is an issue with no parent
            # link at all; a later one is a chain that walked out of the
            # queried scope and stopped at a key this read never saw.
            if current == key:
                return None, NO_PARENT_LINK
            return None, PARENT_OUTSIDE_SCOPE.format(parent=current)
        if parent in seen:
            return None, CYCLE_OR_HOP_LIMIT.format(max_hops=max_hops)
        if parent in epics:
            return parent, None
        seen.add(parent)
        current = parent
    return None, CYCLE_OR_HOP_LIMIT.format(max_hops=max_hops)
