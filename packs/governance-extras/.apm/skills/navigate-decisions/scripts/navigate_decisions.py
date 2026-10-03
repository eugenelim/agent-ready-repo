"""navigate-decisions query seam.

Exposes ``run_query(root, query)`` as the single callable boundary for all
decision-navigation queries.  T1 materially implements only this stub so the
contract test suite can be frozen red before the query behaviour is built in T2.

Spec: docs/specs/decision-navigation/spec.md
Plan task: T1 — Decision contract fixtures fail for the absent capability
"""
from __future__ import annotations

import pathlib


def run_query(root: pathlib.Path, query: dict) -> dict:
    """Execute a decision-navigation query against the corpus at *root*.

    Args:
        root: Repository root whose ``docs/adr/`` and ``docs/rfc/`` subtrees
            form the admitted corpus. Must be an absolute path to an ordinary
            directory that has passed confined-filesystem validation.
        query: Operation descriptor.  The required ``"operation"`` key selects
            one of the five semantic operations defined by the spec's Corpus and
            query contract: ``"summary"``, ``"search"``, ``"record"``,
            ``"lineage"``, or ``"context"``.  Additional keys depend on the
            operation; key names are not fixed by the spec and were chosen here
            to match the spec's semantic descriptions.

    Returns:
        A dict conforming to ``decision-navigation.query.v1``.  Every response
        carries ``schema``, ``status``, normalized ``query``, ``boundary``, and
        ``provenance``.  Success responses add ``records``, ``relationships``,
        ``omissions``, and (for ``summary``) ``summary``.  Refusals add
        ``error`` with a stable code, message, limits, and observed values, and
        return no partial records.

    Raises:
        NotImplementedError: always — query behaviour is not yet implemented.
    """
    raise NotImplementedError("navigate-decisions query behavior is not implemented")
