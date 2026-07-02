#!/usr/bin/env python3
"""Activation-collision check for a migrated skill's description (RFC-0059,
spec "Target-state craft conformance" — activation + no collision).

When assimilation rewrites a skill's `description`, that description must not
collide with an existing skill's — two skills fighting for the same natural
phrasing degrade activation for both. This is a *screen*, not a proof: it flags
high-overlap pairs for the operator to disambiguate (name the colliding skill),
never silently lands. Pure-stdlib, deterministic.
"""

from __future__ import annotations

import re

_STOP = frozenset("""
a an the to of for and or in on with use used using this that do not when it
your you our their its as at by from into is are be than then use-when
""".split())


def tokens(desc: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", desc.lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)  # Jaccard


def collisions(new_desc: str, existing: dict[str, str], *, threshold: float = 0.5) -> list[tuple[str, float]]:
    """Return (skill-name, score) pairs whose description overlaps `new_desc` at
    or above `threshold`, most-similar first. Non-empty ⇒ surface to the operator
    with the colliding skill named; do not land silently."""
    scored = [(name, round(similarity(new_desc, desc), 3)) for name, desc in existing.items()]
    hits = [(n, s) for n, s in scored if s >= threshold]
    return sorted(hits, key=lambda t: t[1], reverse=True)
