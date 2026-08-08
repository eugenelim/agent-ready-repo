"""Construction stubs for the claude-plugin-route-scope spec.

STUB: every test below is intentionally red until the publish filter lands.
Materialised at PLAN per docs/CONVENTIONS.md — a stub that will not compile or
that cannot be written is the signal that a criterion is under-specified.

Traces to docs/specs/claude-plugin-route-scope/spec.md.
"""

from __future__ import annotations

import pytest


# STUB: AC1 — one predicate, four sites
@pytest.mark.xfail(reason="STUB: publish filter not implemented", strict=True)
def test_predicate_applies_at_all_four_sites() -> None:
    raise AssertionError("not implemented")


# STUB: AC2 — resolution reuses _allowed_scopes; the gate is adapter-contract
@pytest.mark.xfail(reason="STUB: publish filter not implemented", strict=True)
@pytest.mark.parametrize("contract_version", [None, "0.1", "0.2", "0.3", "0.17"])
@pytest.mark.parametrize("declared", [None, ["repo"], ["user"], ["repo", "user"]])
def test_predicate_matrix(contract_version, declared) -> None:
    raise AssertionError("not implemented")


# STUB: AC5/AC6 — three-surface equality both directions, plus the seven by name
@pytest.mark.xfail(reason="STUB: publish filter not implemented", strict=True)
def test_three_surfaces_equal_the_derived_set() -> None:
    raise AssertionError("not implemented")


# STUB: AC6 — scope-widening-equals-publication tripwire.
# Do NOT "fix" a failure here by deleting a name: after this spec, widening a
# pack's allowed-scopes publishes its code to a public marketplace, and this
# assertion is what turns red.
@pytest.mark.xfail(reason="STUB: publish filter not implemented", strict=True)
def test_repo_only_packs_absent_by_name() -> None:
    raise AssertionError("not implemented")


# STUB: AC7 — envelope name/owner/description survive the filter
@pytest.mark.xfail(reason="STUB: publish filter not implemented", strict=True)
def test_marketplace_envelope_survives() -> None:
    raise AssertionError("not implemented")


# STUB: AC12 — three-way emptiness behaviour, discriminated by aggregate_scope
@pytest.mark.xfail(reason="STUB: publish filter not implemented", strict=True)
@pytest.mark.parametrize(
    "aggregate_scope,discovered_empty,expect_nonzero",
    [
        ("catalogue", False, True),    # filter emptied a non-empty set
        ("catalogue", True, False),    # blank catalogue is valid
        ("single-pack", False, False), # empty plugins list, success
    ],
)
def test_empty_set_behaviour(aggregate_scope, discovered_empty, expect_nonzero) -> None:
    raise AssertionError("not implemented")


# STUB: AC21 — user-membership implication, NOT subset.
# Subset is false on schema-valid input: contract absent + allowed-scopes=["user"]
# gives _allowed_scopes -> ["repo"] while both siblings give ["user"].
@pytest.mark.xfail(reason="STUB: property not implemented", strict=True)
def test_user_membership_implication_across_resolvers() -> None:
    raise AssertionError("not implemented")
