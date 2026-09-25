#!/usr/bin/env python3
"""Area inference for spec-retirement eligibility projection.

Pure functions that derive a top-level namespace set from a tracked file list
and attribute a spec body to one of those namespaces (or to ``"unscoped"``).

This module contains no I/O. Callers supply already-read data: a list of
repository-relative file paths as returned by ``git ls-files``, and spec body
text as a string. File reads must go through the skill's own confinement helper
before the text reaches these functions.

Spec: docs/specs/spec-retirement-eligibility/spec.md  § Area attribution
Plan: docs/specs/spec-retirement-eligibility/plan.md  § T3
"""
from __future__ import annotations

import re
from collections.abc import Iterable

if False:  # pragma: no cover — type-checking import only
    pass


def infer_namespaces(tracked_files: Iterable[str]) -> frozenset[str]:
    """Derive the set of top-level namespace directories from tracked file paths.

    Each path whose first ``/``-separated component is non-empty names a
    top-level directory.  Files at the repository root (no ``/``) contribute no
    namespace.

    The return type is ``frozenset`` so that two calls over the same input
    always compare equal and the result is safely hashable.

    Args:
        tracked_files: Repository-relative file paths, e.g. from ``git ls-files``.

    Returns:
        A frozenset of top-level directory names such as ``{"packs", "docs",
        "tools"}``.  Never contains empty strings.
    """
    namespaces: set[str] = set()
    for path in tracked_files:
        # Only the first component before the first slash names a directory.
        # A path with no slash is a root file and contributes nothing.
        slash = path.find("/")
        if slash > 0:
            namespaces.add(path[:slash])
    return frozenset(namespaces)


def attribute_spec(body: str, namespaces: frozenset[str]) -> str:
    """Attribute a spec body to a top-level namespace, or to ``"unscoped"``.

    Searches *body* for occurrences of ``<namespace>/`` patterns.  Returns the
    namespace that appears most often.  Ties are broken alphabetically so the
    result is deterministic.  Returns ``"unscoped"`` when no namespace appears.

    The algorithm treats a namespace as named when its directory prefix (i.e.
    the string ``<namespace>/``) occurs anywhere in the text.  This matches
    repository path references in spec prose such as ``"packs/core/..."`` or
    ``"widgets/foo"``.

    Args:
        body:       Spec body text (and optionally concatenated plan text).
        namespaces: The frozenset produced by :func:`infer_namespaces`.

    Returns:
        A namespace string from *namespaces*, or ``"unscoped"``.
    """
    counts: dict[str, int] = {}
    for ns in namespaces:
        # Match the namespace as a path prefix: "<namespace>/"
        pattern = re.compile(re.escape(ns) + r"/")
        n = len(pattern.findall(body))
        if n > 0:
            counts[ns] = n

    if not counts:
        return "unscoped"

    # Most-cited namespace wins; alphabetical order breaks ties deterministically.
    return min(counts, key=lambda ns: (-counts[ns], ns))
