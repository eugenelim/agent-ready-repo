"""T5: Complete verdict coverage for the closure eligibility check.

TDD mode. Tests for:
- One case per refusal — AC-0008 through AC-0013, each asserting the named
  precondition appears in the verdict.
- Eligible controls — AC-0014 (closed-empty + empty) and AC-0015
  (direct-light + empty) — keeping the empty-set refusals from passing for
  an implementation that refuses every empty set.
- A table-driven cross-product over the shipped TERMINUS_VOCABULARY ×
  {empty, non-empty}; fails when a terminus is added with no verdict mapped.
- Verdict precedence — AC-0018, one case per refusal ground so a precedence
  hole in any single one reds.

The classifier ``_classify_ancestor`` is a pure function with no I/O. T3
established reachability through the production entry point; per the plan's
§ Construction tests, later tasks may assert against the classifier directly.

Failure shapes avoided:
1. No I/O seam concern for ``_classify_ancestor``: it takes pre-built
   descendants and a pre-loaded terminality module; there is no filesystem
   path to exercise or leave dead.
2. Refusal tests are paired with eligible controls (AC-0014/AC-0015) so an
   implementation that refuses every input cannot satisfy both sets.
3. Cross-product derives the terminus list from TERMINUS_VOCABULARY so a new
   unmapped entry fails the table rather than being silently skipped.
4. Precedence tests are one per refusal ground; a hole in any single one reds
   that case.

Covers AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014,
AC-0015, AC-0018 of ``docs/specs/closure-eligibility-check/``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ── Module loader ─────────────────────────────────────────────────────────────

_SCRIPTS = (
    Path(__file__).resolve().parents[4]
    / "core" / ".apm" / "skills" / "close-work" / "scripts"
)


def _load(name: str, key: str) -> object:
    """Load a close-work script by absolute path under a unique sys.modules key."""
    spec = importlib.util.spec_from_file_location(key, _SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"no module at {_SCRIPTS / f'{name}.py'}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# Unique keys keep this suite isolated from T2/T3/T4 module caches.
ci = _load("closure_index", "closure_index__verdict_t5")
ct = _load("closure_terminality", "closure_terminality__verdict_t5")


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _dr(
    slug: str,
    *,
    kind: str = "spec",
    status: str = "Implementing",
    terminus: str = "",
) -> object:
    """Return a live DescendantRecord (Implementing spec by default)."""
    return ci.DescendantRecord(slug=slug, kind=kind, status=status, terminus=terminus)  # type: ignore[attr-defined]


def _terminal_dr(slug: str, kind: str = "spec") -> object:
    """Return a terminal DescendantRecord for the given kind."""
    terminal: dict[str, str] = {"intent": "Fulfilled", "brief": "Shipped", "spec": "Shipped"}
    return ci.DescendantRecord(  # type: ignore[attr-defined]
        slug=slug, kind=kind, status=terminal[kind], terminus=""
    )


def _classify(
    slug: str = "anc",
    *,
    status: str = "Accepted",
    terminus: str = "closed-empty",
    descendants: dict | None = None,
) -> object:
    """Call _classify_ancestor with the real terminality module."""
    return ci._classify_ancestor(  # type: ignore[attr-defined]
        slug, status, terminus, descendants if descendants is not None else {}, ct
    )


# ── Per-refusal tests (AC-0008 through AC-0013) ───────────────────────────────


def test_ac0008_refuse_when_not_accepted_and_not_terminal() -> None:
    """AC-0008: status is not Accepted and not terminal → refuse naming the unreached Accepted precondition."""
    verdict = _classify(status="Draft", terminus="closed-empty", descendants={})
    assert isinstance(verdict, ci.ClosureRefuse), f"Expected ClosureRefuse, got {verdict!r}"  # type: ignore[attr-defined]
    assert "not-accepted" in verdict.reason, (  # type: ignore[union-attr]
        f"Expected 'not-accepted' in reason; got {verdict.reason!r}"  # type: ignore[union-attr]
    )


def test_ac0009_refuse_when_already_terminal() -> None:
    """AC-0009: ancestor has already reached a terminal state → refuse naming it is already closed."""
    verdict = _classify(status="Fulfilled", terminus="closed-empty", descendants={})
    assert isinstance(verdict, ci.ClosureRefuse), f"Expected ClosureRefuse, got {verdict!r}"  # type: ignore[attr-defined]
    assert "already-closed" in verdict.reason, (  # type: ignore[union-attr]
        f"Expected 'already-closed' in reason; got {verdict.reason!r}"  # type: ignore[union-attr]
    )


def test_ac0010_refuse_when_decomposed_absent() -> None:
    """AC-0010: Decomposed absent or 'no' → refuse naming the absent ratified delivery set."""
    verdict = _classify(status="Accepted", terminus="", descendants={})
    assert isinstance(verdict, ci.ClosureRefuse), f"Expected ClosureRefuse, got {verdict!r}"  # type: ignore[attr-defined]
    assert "no-decomposed" in verdict.reason, (  # type: ignore[union-attr]
        f"Expected 'no-decomposed' in reason; got {verdict.reason!r}"  # type: ignore[union-attr]
    )


def test_ac0011_refuse_when_collection_terminus_and_empty_set() -> None:
    """AC-0011: collection terminus (children) with empty descendant set → refuse naming the empty set."""
    verdict = _classify(status="Accepted", terminus="children", descendants={})
    assert isinstance(verdict, ci.ClosureRefuse), f"Expected ClosureRefuse, got {verdict!r}"  # type: ignore[attr-defined]
    assert "empty-descendant-set" in verdict.reason, (  # type: ignore[union-attr]
        f"Expected 'empty-descendant-set' in reason; got {verdict.reason!r}"  # type: ignore[union-attr]
    )


def test_ac0012_refuse_when_closed_empty_has_descendants() -> None:
    """AC-0012: closed-empty terminus with non-empty descendants → refuse naming those descendants."""
    desc = {"child-a": _dr("child-a")}
    verdict = _classify(status="Accepted", terminus="closed-empty", descendants=desc)
    assert isinstance(verdict, ci.ClosureRefuse), f"Expected ClosureRefuse, got {verdict!r}"  # type: ignore[attr-defined]
    assert "closed-empty-has-descendants" in verdict.reason, (  # type: ignore[union-attr]
        f"Expected 'closed-empty-has-descendants' in reason; got {verdict.reason!r}"  # type: ignore[union-attr]
    )


def test_ac0013_refuse_when_direct_light_has_descendants() -> None:
    """AC-0013: direct-light terminus with non-empty descendants → refuse naming those descendants."""
    desc = {"child-a": _dr("child-a")}
    verdict = _classify(status="Accepted", terminus="direct-light", descendants=desc)
    assert isinstance(verdict, ci.ClosureRefuse), f"Expected ClosureRefuse, got {verdict!r}"  # type: ignore[attr-defined]
    assert "direct-light-has-descendants" in verdict.reason, (  # type: ignore[union-attr]
        f"Expected 'direct-light-has-descendants' in reason; got {verdict.reason!r}"  # type: ignore[union-attr]
    )


# ── Eligible control tests (AC-0014, AC-0015) ─────────────────────────────────
#
# These exist so empty-set refusals (AC-0011, AC-0012, AC-0013) cannot pass for
# an implementation that refuses every empty set.


def test_ac0014_eligible_when_closed_empty_and_empty() -> None:
    """AC-0014: closed-empty terminus with empty descendants → eligible on that ground."""
    verdict = _classify(status="Accepted", terminus="closed-empty", descendants={})
    assert isinstance(verdict, ci.ClosureEligible), (  # type: ignore[attr-defined]
        f"Expected ClosureEligible (AC-0014), got {verdict!r}"
    )
    assert verdict.basis == "closed-empty", f"Unexpected basis: {verdict.basis!r}"  # type: ignore[union-attr]


def test_ac0015_eligible_when_direct_light_and_empty() -> None:
    """AC-0015: direct-light terminus with empty descendants → eligible on that ground."""
    verdict = _classify(status="Accepted", terminus="direct-light", descendants={})
    assert isinstance(verdict, ci.ClosureEligible), (  # type: ignore[attr-defined]
        f"Expected ClosureEligible (AC-0015), got {verdict!r}"
    )
    assert verdict.basis == "direct-light", f"Unexpected basis: {verdict.basis!r}"  # type: ignore[union-attr]


# ── Cross-product table: TERMINUS_VOCABULARY × {empty, non-empty} ─────────────
#
# The terminus list is derived from TERMINUS_VOCABULARY so a new unmapped entry
# fails this test rather than being silently skipped.
#
# For the non-empty case, a live descendant (Implementing spec) is used so that
# collection termini produce ClosureNotEligible rather than ClosureEligible —
# that is the discriminating input for the not-eligible branch.

_CROSS_PRODUCT_EXPECTED: dict[tuple[str, bool], type] = {
    # Collection termini: empty → refuse (AC-0011); non-empty live → not-eligible (AC-0017).
    ("children", False): ci.ClosureRefuse,  # type: ignore[attr-defined]
    ("children", True): ci.ClosureNotEligible,  # type: ignore[attr-defined]
    ("brief", False): ci.ClosureRefuse,  # type: ignore[attr-defined]
    ("brief", True): ci.ClosureNotEligible,  # type: ignore[attr-defined]
    ("spec", False): ci.ClosureRefuse,  # type: ignore[attr-defined]
    ("spec", True): ci.ClosureNotEligible,  # type: ignore[attr-defined]
    # Non-collection termini: empty or non-empty each produces a deterministic verdict.
    ("direct-light", False): ci.ClosureEligible,  # AC-0015  # type: ignore[attr-defined]
    ("direct-light", True): ci.ClosureRefuse,  # AC-0013  # type: ignore[attr-defined]
    ("closed-empty", False): ci.ClosureEligible,  # AC-0014  # type: ignore[attr-defined]
    ("closed-empty", True): ci.ClosureRefuse,  # AC-0012  # type: ignore[attr-defined]
}


@pytest.mark.parametrize(
    "terminus,has_descendants",
    [(t, d) for t in ci.TERMINUS_VOCABULARY for d in (False, True)],  # type: ignore[attr-defined]
    ids=[
        f"{t}-{'nonempty' if d else 'empty'}"
        for t in ci.TERMINUS_VOCABULARY  # type: ignore[attr-defined]
        for d in (False, True)
    ],
)
def test_cross_product_terminus_vocabulary_verdict(terminus: str, has_descendants: bool) -> None:
    """Every (terminus, empty/non-empty) cell maps to a deterministic verdict type.

    Derives the terminus list from TERMINUS_VOCABULARY so a new unmapped terminus
    fails this test rather than passing silently. The parametrize list is built at
    collection time from the live vocabulary; adding a terminus expands the list
    and the new cell's KeyError in _CROSS_PRODUCT_EXPECTED fails the run.
    """
    assert (terminus, has_descendants) in _CROSS_PRODUCT_EXPECTED, (
        f"No verdict mapped for (terminus={terminus!r}, has_descendants={has_descendants}). "
        "Add an entry to _CROSS_PRODUCT_EXPECTED to cover the new terminus."
    )
    expected_type = _CROSS_PRODUCT_EXPECTED[(terminus, has_descendants)]

    descendants = {}
    if has_descendants:
        # A live descendant so collection-terminus cases produce not-eligible, not eligible.
        descendants = {"child-a": _dr("child-a", status="Implementing")}

    verdict = _classify(status="Accepted", terminus=terminus, descendants=descendants)
    assert isinstance(verdict, expected_type), (  # type: ignore[arg-type]
        f"For terminus={terminus!r}, has_descendants={has_descendants}: "
        f"expected {expected_type.__name__}, got {type(verdict).__name__} ({verdict!r})"
    )


# ── AC-0018: verdict precedence — one case per refusal ground ─────────────────
#
# Per refusal ground: input satisfies BOTH a refusal criterion AND a non-refusal
# ground; assert the refusal wins. A precedence hole in any single ground reds
# that case.
#
# Non-refusal ground used as the contrasting ground in each pair:
#   AC-0009 vs AC-0016 (all-descendants-terminal → eligible)
#   AC-0008 vs AC-0014 (closed-empty + empty → eligible)
#   AC-0010 vs AC-0016 (vacuously: absent terminus + all-terminal falls to eligible)
#   AC-0011 vs AC-0016 (vacuously: empty set + no live → eligible)
#   AC-0012 vs AC-0016 (all-terminal descendant → eligible, but closed-empty-has-desc fires)
#   AC-0013 vs AC-0016 (all-terminal descendant → eligible, but direct-light-has-desc fires)


def test_ac0018_precedence_ac0009_outranks_eligible() -> None:
    """AC-0018/AC-0009: terminal ancestor status outranks eligible (all-descendants-terminal).

    Contrasting ground: children terminus, all-terminal descendant → AC-0016 eligible.
    With AC-0009: refuse because status is already terminal (Fulfilled).
    """
    desc = {"child-a": _terminal_dr("child-a", kind="spec")}
    verdict = _classify(status="Fulfilled", terminus="children", descendants=desc)
    assert isinstance(verdict, ci.ClosureRefuse), (  # type: ignore[attr-defined]
        f"Expected ClosureRefuse (AC-0009 precedence), got {verdict!r}"
    )
    assert "already-closed" in verdict.reason  # type: ignore[union-attr]


def test_ac0018_precedence_ac0008_outranks_eligible() -> None:
    """AC-0018/AC-0008: not-accepted outranks eligible (closed-empty + empty → AC-0014).

    Contrasting ground: closed-empty terminus, empty descendants → AC-0014 eligible.
    With AC-0008: refuse because status is Draft (not Accepted, not terminal).
    """
    verdict = _classify(status="Draft", terminus="closed-empty", descendants={})
    assert isinstance(verdict, ci.ClosureRefuse), (  # type: ignore[attr-defined]
        f"Expected ClosureRefuse (AC-0008 precedence), got {verdict!r}"
    )
    assert "not-accepted" in verdict.reason  # type: ignore[union-attr]


def test_ac0018_precedence_ac0010_outranks_eligible() -> None:
    """AC-0018/AC-0010: absent terminus outranks eligible (all-descendants-terminal).

    Contrasting ground: all-terminal descendant; without AC-0010 the classifier
    would fall past the non-collection-terminus blocks and reach the all-terminal
    eligible path (AC-0016 vacuously via empty live set).
    With AC-0010: refuse because terminus is absent.
    """
    desc = {"child-a": _terminal_dr("child-a", kind="spec")}
    verdict = _classify(status="Accepted", terminus="", descendants=desc)
    assert isinstance(verdict, ci.ClosureRefuse), (  # type: ignore[attr-defined]
        f"Expected ClosureRefuse (AC-0010 precedence), got {verdict!r}"
    )
    assert "no-decomposed" in verdict.reason  # type: ignore[union-attr]


def test_ac0018_precedence_ac0011_outranks_eligible() -> None:
    """AC-0018/AC-0011: empty-descendant-set outranks eligible (vacuously all-terminal).

    Contrasting ground: children terminus, empty descendants; without AC-0011 the
    classifier would find no live descendants and return eligible (AC-0016 vacuously).
    With AC-0011: refuse because a collection terminus expects artifact children.
    """
    verdict = _classify(status="Accepted", terminus="children", descendants={})
    assert isinstance(verdict, ci.ClosureRefuse), (  # type: ignore[attr-defined]
        f"Expected ClosureRefuse (AC-0011 precedence), got {verdict!r}"
    )
    assert "empty-descendant-set" in verdict.reason  # type: ignore[union-attr]


def test_ac0018_precedence_ac0012_outranks_eligible() -> None:
    """AC-0018/AC-0012: closed-empty-has-descendants outranks eligible (all-terminal).

    Contrasting ground: all-terminal descendant satisfies AC-0016; but
    closed-empty terminus + non-empty descendants triggers AC-0012 refusal first.
    """
    desc = {"child-a": _terminal_dr("child-a", kind="spec")}
    verdict = _classify(status="Accepted", terminus="closed-empty", descendants=desc)
    assert isinstance(verdict, ci.ClosureRefuse), (  # type: ignore[attr-defined]
        f"Expected ClosureRefuse (AC-0012 precedence), got {verdict!r}"
    )
    assert "closed-empty-has-descendants" in verdict.reason  # type: ignore[union-attr]


def test_ac0018_precedence_ac0013_outranks_eligible() -> None:
    """AC-0018/AC-0013: direct-light-has-descendants outranks eligible (all-terminal).

    Contrasting ground: all-terminal descendant satisfies AC-0016; but
    direct-light terminus + non-empty descendants triggers AC-0013 refusal first.
    """
    desc = {"child-a": _terminal_dr("child-a", kind="spec")}
    verdict = _classify(status="Accepted", terminus="direct-light", descendants=desc)
    assert isinstance(verdict, ci.ClosureRefuse), (  # type: ignore[attr-defined]
        f"Expected ClosureRefuse (AC-0013 precedence), got {verdict!r}"
    )
    assert "direct-light-has-descendants" in verdict.reason  # type: ignore[union-attr]
