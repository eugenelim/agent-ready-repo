"""Terminality predicates the closure check decides verdicts on.

Portable: this suite uses only the module's own declarations, never the
repository's governance corpus. The live-corpus parity assertion is a separate
gate-chain step, for the reason the spec's notes/verification-ledger.md records.

Covers AC-0005, AC-0006 and AC-0007 of `docs/specs/closure-eligibility-check/`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[4]
    / "core" / ".apm" / "skills" / "close-work" / "scripts"
)


def _load(name: str):
    """Load a close-work script by path.

    Skill directories are not packages and are not importable by name; every
    loader in this pack resolves its own sibling directory the same way.
    """
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"no module at {_SCRIPTS / f'{name}.py'}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ct = _load("closure_terminality")


# ── AC-0005: the intent projection ────────────────────────────────────────────


def test_intent_terminal_set_is_exactly_the_four_declared_states() -> None:
    expected = frozenset({"Fulfilled", "Withdrawn", "Cancelled", "Superseded"})
    assert expected == ct.TERMINAL_INTENT_STATUSES


@pytest.mark.parametrize("status", ["Fulfilled", "Withdrawn", "Cancelled", "Superseded"])
def test_a_terminal_intent_status_is_terminal(status: str) -> None:
    assert ct.is_intent_terminal(status) is True


@pytest.mark.parametrize("status", ["Draft", "Accepted"])
def test_a_live_intent_status_is_not_terminal(status: str) -> None:
    assert ct.is_intent_terminal(status) is False


def test_the_intent_projection_covers_every_member_of_its_vocabulary() -> None:
    """Iterated from the vocabulary, so a status added upstream reds here.

    A hand-written list would pass unchanged while the vocabulary grew, which is
    the failure this assertion exists to catch.
    """
    undecided = [s for s in ct.INTENT_STATUS_VOCABULARY
                 if ct.is_intent_terminal(s) not in (True, False)]
    assert undecided == []
    assert set(ct.TERMINAL_INTENT_STATUSES) <= set(ct.INTENT_STATUS_VOCABULARY)


# ── AC-0006: the brief predicate, two parts ───────────────────────────────────


@pytest.mark.parametrize("status", ["Shipped", "Withdrawn", "Cancelled"])
def test_a_brief_status_with_no_outgoing_edge_is_terminal(status: str) -> None:
    assert ct.is_brief_terminal(status) is True


@pytest.mark.parametrize("status", ["Draft", "Ready", "Executing"])
def test_a_brief_status_with_an_outgoing_edge_is_live(status: str) -> None:
    assert ct.is_brief_terminal(status) is False


@pytest.mark.parametrize("status", ["Shpped", "", "Complete", "None"])
def test_a_brief_status_outside_the_vocabulary_is_live(status: str) -> None:
    """The unsafe direction is terminal: eligible authorises a terminal write.

    A typo and an upstream addition both have no outgoing edge, so deriving
    terminality from the edge table alone would call them terminal. The
    vocabulary check is what stops that.
    """
    assert ct.is_brief_terminal(status) is False


def test_the_brief_predicate_covers_every_member_of_its_vocabulary() -> None:
    undecided = [s for s in ct.BRIEF_STATUS_VOCABULARY
                 if ct.is_brief_terminal(s) not in (True, False)]
    assert undecided == []


# ── AC-0007: the projections are pinned, and the pin can red ──────────────────


def test_each_projection_declares_the_upstream_it_derives_from() -> None:
    """A projection with no named upstream cannot be parity-checked at all."""
    for pin in (
        ct.INTENT_TERMINALITY_UPSTREAM,
        ct.BRIEF_TERMINALITY_UPSTREAM,
        ct.SPEC_TERMINALITY_UPSTREAM,
    ):
        assert pin.slug, "upstream pin carries no locator"
        assert pin.section, "upstream pin names no section or symbol"


def test_the_intent_parity_check_reds_on_a_mutated_upstream() -> None:
    """Mutation, not presence: a gutted parity test passes a presence guard."""
    honest = {"Fulfilled": True, "Withdrawn": True, "Cancelled": True,
              "Superseded": True, "Draft": False, "Accepted": False}
    assert ct.intent_parity_disagreements(honest) == []
    mutated = dict(honest, Accepted=True)
    assert ct.intent_parity_disagreements(mutated) == ["Accepted"]


def test_the_brief_parity_check_reds_on_a_mutated_edge_table() -> None:
    honest = frozenset(ct.BRIEF_TRANSITIONS_PROJECTION)
    assert ct.brief_parity_disagreements(honest) == []
    mutated = honest | {("Shipped", "Draft")}
    assert ct.brief_parity_disagreements(mutated) == ["Shipped"]


# ── Spec vocabulary and terminality ──────────────────────────────────────────


def test_spec_terminal_set_is_shipped_and_archived() -> None:
    assert frozenset({"Shipped", "Archived"}) == ct.TERMINAL_SPEC_STATUSES


@pytest.mark.parametrize("status", ["Shipped", "Archived"])
def test_a_terminal_spec_status_is_terminal(status: str) -> None:
    assert ct.is_spec_terminal(status) is True


@pytest.mark.parametrize("status", ["Draft", "Approved", "Implementing"])
def test_a_live_spec_status_is_not_terminal(status: str) -> None:
    assert ct.is_spec_terminal(status) is False


@pytest.mark.parametrize("status", ["", "Shpped", "shipped", "None"])
def test_an_unknown_spec_status_is_live(status: str) -> None:
    """Unknown status is live — safe direction: eligible authorises a terminal write."""
    assert ct.is_spec_terminal(status) is False


def test_spec_vocabulary_covers_five_declared_statuses() -> None:
    expected = frozenset({"Draft", "Approved", "Implementing", "Shipped", "Archived"})
    assert frozenset(ct.SPEC_STATUS_VOCABULARY) == expected


def test_spec_vocabulary_contains_the_terminal_subset() -> None:
    assert frozenset(ct.SPEC_STATUS_VOCABULARY) >= ct.TERMINAL_SPEC_STATUSES


def test_spec_parity_check_passes_on_honest_upstream() -> None:
    """The projection agrees with its own vocabulary — a self-consistency check."""
    honest = frozenset(ct.SPEC_STATUS_VOCABULARY)
    assert ct.spec_parity_disagreements(honest) == []


def test_spec_parity_check_reds_when_upstream_adds_a_status() -> None:
    """Mutation: upstream gains a new status the projection does not declare.

    Presence is not the guard — a gutted parity function still passes if the
    caller only checks the list exists. This asserts the content.
    """
    honest = frozenset(ct.SPEC_STATUS_VOCABULARY)
    assert ct.spec_parity_disagreements(honest) == []
    # Simulate upstream adding a new status this projection does not carry.
    mutated = honest | {"Planned"}
    disagreements = ct.spec_parity_disagreements(mutated)
    assert "Planned" in disagreements, (
        f"Expected 'Planned' in disagreements after upstream mutation, got {disagreements}"
    )


def test_spec_parity_check_reds_when_projection_adds_a_status() -> None:
    """Mutation: projection declares a status the upstream does not carry.

    This is the inverse direction: a projection drift that adds a status.
    """
    upstream_missing_archived = frozenset(ct.SPEC_STATUS_VOCABULARY) - {"Archived"}
    disagreements = ct.spec_parity_disagreements(upstream_missing_archived)
    assert "Archived" in disagreements, (
        f"Expected 'Archived' in disagreements when upstream omits it, got {disagreements}"
    )


# ── The terminus vocabulary projection, pinned like the three status ones ─────

ci = _load("closure_index")


def test_the_terminus_projection_agrees_with_its_upstream() -> None:
    """The live check: this is what the gate chain runs on every pull request."""
    import importlib.util

    upstream_path = (
        _SCRIPTS.parents[1] / "work-intake" / "scripts" / "intent_shape.py"
    )
    spec = importlib.util.spec_from_file_location("_upstream_shape", upstream_path)
    assert spec and spec.loader
    upstream = importlib.util.module_from_spec(spec)
    sys.modules["_upstream_shape"] = upstream
    spec.loader.exec_module(upstream)

    assert ci.terminus_parity_disagreements(upstream.DECOMPOSITION_TERMINI) == []


def test_the_terminus_parity_check_reds_when_upstream_adds_a_terminus() -> None:
    """Mutation, not presence.

    A terminus added upstream and missing here is the live risk: the
    cross-product coverage table is generated from ``TERMINUS_VOCABULARY``, so
    the new terminus would produce no case and reach no verdict with every test
    still green.
    """
    grown = tuple(ci.TERMINUS_VOCABULARY) + ("retired",)
    assert ci.terminus_parity_disagreements(grown) == ["retired"]


def test_the_terminus_parity_check_reds_on_an_invented_terminus() -> None:
    """The other direction: a terminus this projection has and upstream does not."""
    shrunk = tuple(t for t in ci.TERMINUS_VOCABULARY if t != "direct-light")
    assert ci.terminus_parity_disagreements(shrunk) == ["direct-light"]
