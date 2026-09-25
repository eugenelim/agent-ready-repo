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
    rather than drops.
    """
    epics = set(epic_keys)
    resolved: dict[str, str | None] = {}
    for key in parent_links:
        resolved[key] = _walk(key, parent_links, epics, max_hops)
    return resolved


def _walk(
    key: str,
    parent_links: Mapping[str, str | None],
    epics: set[str],
    max_hops: int,
) -> str | None:
    if key in epics:
        return key
    seen = {key}
    current: str | None = key
    for _ in range(max_hops):
        current = parent_links.get(current) if current is not None else None
        if current is None or current in seen:
            return None
        if current in epics:
            return current
        seen.add(current)
    return None
