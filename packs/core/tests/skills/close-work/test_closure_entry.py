"""Entry point, ancestor resolver, and differential fixture for the closure check.

T4: Mode TDD. Tests for the production entry point (AC-0001), ancestor
resolution from every declared up-edge type (AC-0002, AC-0003), the closed
verdict-type set (AC-0004), the differential fixture (AC-0016, AC-0017), and
the caller-enumeration guard (AC-0026).

Two failure shapes avoided here:
1. Green suite over a dead branch: the differential tests (AC-0016, AC-0017)
   use ``tmp_path`` with no injected seams, so ``_make_confined_reader`` and
   ``_default_dir_lister`` run against real on-disk files.
2. A differential that does not discriminate: both AC-0016 (eligible) and
   AC-0017 (not-eligible) are asserted through the same entry point on copies
   of the same fixture, so the test fails if the branch does not exist or does
   not discriminate.

Covers AC-0001, AC-0002, AC-0003, AC-0004, AC-0016, AC-0017, AC-0026 of
``docs/specs/closure-eligibility-check/``.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

# ── Module loader ─────────────────────────────────────────────────────────────

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "close-work" / "scripts"
)

# Literal paths: the pack-boundary lint cannot prove a computed join stays
# inside the owning pack, and it is right not to try.
_MODULE_PATHS = {
    "closure_index": _SCRIPTS / "closure_index.py",
    "closure_terminality": _SCRIPTS / "closure_terminality.py",
}


def _load(name: str, key: str):
    """Load a close-work script by absolute path under a unique sys.modules key."""
    spec = importlib.util.spec_from_file_location(key, _MODULE_PATHS[name])
    assert spec and spec.loader, f"no module at {_MODULE_PATHS[name]}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


# Unique keys keep this suite isolated from T2 and T3 module caches.
ci = _load("closure_index", "closure_index__entry_t4")
ct = _load("closure_terminality", "closure_terminality__entry_t4")


# ── Snapshot helpers for _snapshot_provider injection ─────────────────────────


def _snapshot(
    *,
    relations: list[dict[str, Any]] | None = None,
    provenance: list[dict[str, Any]] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid delivery snapshot for test injection."""
    return {
        "schema_version": 1,
        "complete": True,
        "relations": relations or [],
        "classifications": [],
        "provenance": provenance or [],
        "diagnostics": diagnostics or [],
    }


def _direct(intent_slug: str, spec_slug: str) -> dict[str, Any]:
    """Build a direct-delivery relation record."""
    return {
        "type": "direct-delivery",
        "route": "spec",
        "intent": f"intent:{intent_slug}",
        "spec": f"spec:{spec_slug}",
        "basis": {"intent": "Decomposed", "spec": "Discovery"},
    }


def _coord(intent_slug: str, brief_slug: str, spec_slug: str) -> dict[str, Any]:
    """Build a coordinated-delivery relation record."""
    return {
        "type": "coordinated-delivery",
        "route": "brief",
        "intent": f"intent:{intent_slug}",
        "brief": f"brief:{brief_slug}",
        "spec": f"spec:{spec_slug}",
        "basis": {"brief": "Parent intent", "intent": "Decomposed", "spec": "Brief"},
    }


def _prov(spec_slug: str, intent_slug: str) -> dict[str, Any]:
    """Build a contextual-provenance record for a Discovery: reference."""
    return {
        "subject": f"spec:{spec_slug}",
        "field": "Discovery",
        "target": f"intent:{intent_slug}",
    }


# ── Fixture helpers ───────────────────────────────────────────────────────────

ROOT = Path("/fake/root")
INTENTS_DIR = ROOT / "docs" / "product" / "intents"
BRIEFS_DIR = ROOT / "docs" / "product" / "briefs"
SPECS_DIR = ROOT / "docs" / "specs"


def _intent(
    slug: str,
    status: str = "Accepted",
    parent: str | None = None,
    decomposed: str | None = None,
) -> str:
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    if decomposed:
        lines.append(f"- **Decomposed:** 2026-09-01 {decomposed}")
    lines.append("")
    return "\n".join(lines)


def _brief(slug: str, status: str = "Executing", parent: str | None = None) -> str:
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    lines.append("")
    return "\n".join(lines)


def _spec(
    slug: str,
    status: str = "Implementing",
    discovery: str | None = None,
    brief: str | None = None,
) -> str:
    # A spec carries no ``Slug:``: 0 of 487 in the corpus do. Its
    # identity is its directory name, per the shipped convention.
    lines = [f"- **Status:** {status}"]
    if discovery:
        lines.append(f"- **Discovery:** {discovery}")
    if brief is not None:
        lines.append(f"- **Brief:** {brief}")
    lines.append("")
    return "\n".join(lines)


# ── Terminality helper for deriving expected live sets ────────────────────────


def _is_terminal(kind: str, status: str) -> bool:
    """Route to the kind-appropriate terminality predicate."""
    if kind == "intent":
        return bool(ct.is_intent_terminal(status))
    if kind == "brief":
        return bool(ct.is_brief_terminal(status))
    if kind == "spec":
        return bool(ct.is_spec_terminal(status))
    return False


# ── AC-0004: closed verdict-type set ─────────────────────────────────────────


def test_ac0004_verdict_types_are_a_closed_set() -> None:
    """The three verdict types are a closed set of frozen dataclasses."""
    verdict_types = (ci.ClosureEligible, ci.ClosureNotEligible, ci.ClosureRefuse)
    assert len(verdict_types) == 3
    for t in verdict_types:
        assert dataclasses.is_dataclass(t), f"{t} is not a dataclass"
        assert t.__dataclass_params__.frozen, f"{t} is not frozen"  # type: ignore[attr-defined]


def test_ac0004_verdict_types_are_distinct() -> None:
    """Each verdict type is distinct; no two share an identity."""
    assert ci.ClosureEligible is not ci.ClosureNotEligible
    assert ci.ClosureEligible is not ci.ClosureRefuse
    assert ci.ClosureNotEligible is not ci.ClosureRefuse


# ── AC-0026: caller enumeration ───────────────────────────────────────────────


def test_ac0026_only_check_ancestor_closure_calls_build_descendant_closure() -> None:
    """Only check_ancestor_closure calls _build_descendant_closure (module-private).

    This test fails when a second caller is added — the invariant AC-0026 asserts.
    """
    source = (_SCRIPTS / "closure_index.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Walk the AST. For each top-level FunctionDef, record which ones contain
    # a call to _build_descendant_closure in their body (including nested scopes).
    caller_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == "_build_descendant_closure"
                ):
                    caller_names.add(node.name)

    assert caller_names == {"check_ancestor_closure"}, (
        f"Expected only check_ancestor_closure to call _build_descendant_closure; "
        f"found: {sorted(caller_names)!r}"
    )


# ── AC-0001: terminal transition fires the check on ancestors ─────────────────


def test_ac0001_terminal_transition_fires_check_on_ancestor(tmp_path: Path) -> None:
    """Resolving ancestors then calling check_ancestor_closure exercises the production path.

    Uses real filesystem (tmp_path, no seams) so the production path is reached
    rather than a dead branch covered only by an injected seam.
    """
    intents_dir = tmp_path / "docs" / "product" / "intents"
    specs_dir = tmp_path / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    # An Accepted ancestor with closed-empty terminus (no artifact children expected).
    ancestor_slug = "my-ancestor"
    (intents_dir / "my-ancestor.md").write_text(
        f"- **Slug:** {ancestor_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-01 closed-empty\n"
    )

    # A spec in terminal state (Shipped) with Discovery: pointing to the ancestor.
    spec_slug = "my-spec"
    spec_dir = specs_dir / spec_slug
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(
        f"- **Slug:** {spec_slug}\n"
        f"- **Status:** Shipped\n"
        f"- **Discovery:** docs/product/intents/my-ancestor.md\n"
    )

    spec_fields = {
        "Slug": spec_slug,
        "Status": "Shipped",
        "Discovery": "docs/product/intents/my-ancestor.md",
    }
    # Step 1: resolve intent ancestors from the transitioning spec.
    # The ancestor has Decomposed: closed-empty (not a delivery intent), so the
    # resolver would produce a contextual-provenance record. Inject a snapshot
    # with that provenance record; the ancestor has no tracking branch so
    # _snapshot_provider is required for resolve_intent_ancestors.
    snap = _snapshot(provenance=[_prov(spec_slug, ancestor_slug)])
    ancestors = ci.resolve_intent_ancestors(
        spec_slug, "spec", spec_fields, tmp_path, _snapshot_provider=lambda _r: snap
    )
    assert len(ancestors) == 1
    ancestor_slug_found, ancestor_status, ancestor_terminus = ancestors[0]
    assert ancestor_slug_found == ancestor_slug
    assert ancestor_status == "Accepted"
    assert ancestor_terminus == "closed-empty"

    # Step 2: fire the check on each ancestor — the production entry point.
    # Inject _freshness_checker=lambda: True because tmp_path is not a git
    # repository; this test's purpose is AC-0001 (production entry point fires
    # on a terminal transition), not AC-0022 (freshness). The T6 real-path test
    # (test_ac0022_real_git_repo_does_not_refuse) covers the production freshness path.
    verdict = ci.check_ancestor_closure(
        ancestor_slug_found, ancestor_status, ancestor_terminus, tmp_path,
        _freshness_checker=lambda: True,
    )
    # closed-empty terminus with empty descendant set → eligible (no sweep, no schedule).
    assert isinstance(verdict, ci.ClosureEligible)


# ── AC-0002: ancestor resolution from every up-edge type ─────────────────────


def test_ac0002_intent_parent_intent_resolves_ancestor(tmp_path: Path) -> None:
    """An intent's Parent intent: resolves the parent intent as ancestor."""
    intents_dir = tmp_path / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True)

    parent_slug = "parent-intent"
    child_slug = "child-intent"
    (intents_dir / "parent-intent.md").write_text(
        f"- **Slug:** {parent_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-01 closed-empty\n"
    )
    child_fields = {
        "Slug": child_slug,
        "Status": "Accepted",
        "Parent intent": f"intent:{parent_slug}",
    }
    ancestors = ci.resolve_intent_ancestors(child_slug, "intent", child_fields, tmp_path)
    assert len(ancestors) == 1
    assert ancestors[0][0] == parent_slug


def test_ac0002_brief_parent_intent_resolves_ancestor(tmp_path: Path) -> None:
    """A brief's Parent intent: resolves the parent intent as ancestor."""
    intents_dir = tmp_path / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True)

    parent_slug = "brief-parent"
    brief_slug = "my-brief"
    (intents_dir / "brief-parent.md").write_text(
        f"- **Slug:** {parent_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-01 closed-empty\n"
    )
    brief_fields = {
        "Slug": brief_slug,
        "Status": "Executing",
        "Parent intent": f"intent:{parent_slug}",
    }
    ancestors = ci.resolve_intent_ancestors(brief_slug, "brief", brief_fields, tmp_path)
    assert len(ancestors) == 1
    assert ancestors[0][0] == parent_slug


def test_ac0002_spec_brief_field_resolves_ancestor_via_brief(tmp_path: Path) -> None:
    """A spec's Brief: resolves the intent ancestor via the brief's Parent intent:."""
    intents_dir = tmp_path / "docs" / "product" / "intents"
    briefs_dir = tmp_path / "docs" / "product" / "briefs"
    intents_dir.mkdir(parents=True)
    briefs_dir.mkdir(parents=True)

    parent_slug = "spec-parent"
    brief_slug = "my-brief"
    spec_slug = "my-spec"

    (intents_dir / "spec-parent.md").write_text(
        f"- **Slug:** {parent_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-01 brief\n"
    )
    (briefs_dir / "my-brief.md").write_text(
        f"- **Slug:** {brief_slug}\n"
        f"- **Status:** Executing\n"
        f"- **Parent intent:** intent:{parent_slug}\n"
    )
    spec_fields = {
        "Slug": spec_slug,
        "Status": "Implementing",
        "Brief": f"brief:{brief_slug}",
        "Discovery": "",
    }
    # Inject a snapshot with a coordinated-delivery relation for this spec.
    snap = _snapshot(relations=[_coord(parent_slug, brief_slug, spec_slug)])
    ancestors = ci.resolve_intent_ancestors(
        spec_slug, "spec", spec_fields, tmp_path, _snapshot_provider=lambda _r: snap
    )
    assert any(a[0] == parent_slug for a in ancestors), (
        f"Expected {parent_slug!r} in ancestors, got {ancestors!r}"
    )


def test_ac0002_spec_brief_none_uses_discovery(tmp_path: Path) -> None:
    """A spec with Brief: none reaches its ancestor only through Discovery:.

    Covers the 12 of 24 decomposed intents whose termini are 'spec' —
    these specs carry Brief: none and use Discovery: as the sole up-edge.
    """
    intents_dir = tmp_path / "docs" / "product" / "intents"
    specs_dir = tmp_path / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    parent_slug = "disc-parent"
    spec_slug = "disc-spec"

    (intents_dir / "disc-parent.md").write_text(
        f"- **Slug:** {parent_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-01 spec\n"
    )
    spec_dir = specs_dir / spec_slug
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(
        f"- **Slug:** {spec_slug}\n"
        f"- **Status:** Implementing\n"
        f"- **Brief:** none\n"
        f"- **Discovery:** docs/product/intents/disc-parent.md\n"
    )
    spec_fields = {
        "Slug": spec_slug,
        "Status": "Implementing",
        "Brief": "none",
        "Discovery": "docs/product/intents/disc-parent.md",
    }
    # disc-parent has Decomposed: spec → direct-delivery relation for disc-spec.
    snap = _snapshot(relations=[_direct(parent_slug, spec_slug)])
    ancestors = ci.resolve_intent_ancestors(
        spec_slug, "spec", spec_fields, tmp_path, _snapshot_provider=lambda _r: snap
    )
    assert len(ancestors) == 1
    assert ancestors[0][0] == parent_slug


# ── AC-0003: Discovery: in three corpus forms ─────────────────────────────────


@pytest.mark.parametrize(
    "discovery_value",
    [
        "docs/product/intents/form-ancestor.md",
        "`docs/product/intents/form-ancestor.md`",
        "[intent](docs/product/intents/form-ancestor.md)",
    ],
    ids=["bare-path", "backtick-path", "markdown-link"],
)
def test_ac0003_discovery_three_forms_resolve_same_ancestor(
    tmp_path: Path, discovery_value: str
) -> None:
    """Discovery: in all three corpus forms resolves to the same intent ancestor."""
    intents_dir = tmp_path / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True)

    parent_slug = "form-ancestor"
    (intents_dir / "form-ancestor.md").write_text(
        f"- **Slug:** {parent_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-01 closed-empty\n"
    )
    # form-ancestor has Decomposed: closed-empty → contextual-provenance record.
    # resolve_intent_ancestors looks up provenance records for spec→intent edges.
    spec_fields = {"Slug": "test-spec", "Discovery": discovery_value}
    snap = _snapshot(provenance=[_prov("test-spec", parent_slug)])
    ancestors = ci.resolve_intent_ancestors(
        "test-spec", "spec", spec_fields, tmp_path, _snapshot_provider=lambda _r: snap
    )
    assert len(ancestors) == 1
    assert ancestors[0][0] == parent_slug


# ── Defect regression: resolver failure (AC-0018 fail-closed) ─────────────────


def test_resolver_failure_in_resolve_intent_ancestors_surfaces_code(tmp_path: Path) -> None:
    """A failing _snapshot_provider must surface delivery-resolver-unavailable.

    AC-0018: resolver invocation failure yields delivery-resolver-unavailable
    without a fallback.  Returning an empty-ancestor success is forbidden.
    """
    spec_fields = {"Slug": "my-spec", "Discovery": "docs/product/intents/cap.md"}

    def _failing_provider(_root: Path) -> dict:
        raise RuntimeError("connection refused")

    with pytest.raises(ci._ClosureDeliveryRefusal) as exc_info:
        ci.resolve_intent_ancestors(
            "my-spec", "spec", spec_fields, tmp_path,
            _snapshot_provider=_failing_provider,
        )
    assert exc_info.value.reason == "delivery-resolver-unavailable"


# ── Defect regression: path-form Discovery provenance target ──────────────────


@pytest.mark.parametrize(
    "discovery_value,prov_target",
    [
        # Bare-path form: resolver stores the path as-is in provenance target.
        (
            "docs/product/intents/my-cap.md",
            "docs/product/intents/my-cap.md",
        ),
        # Backtick-path form: resolver strips backticks → same bare-path target.
        (
            "`docs/product/intents/my-cap.md`",
            "docs/product/intents/my-cap.md",
        ),
    ],
    ids=["bare-path", "backtick-path"],
)
def test_path_form_provenance_target_reaches_non_feature_ancestor(
    tmp_path: Path,
    discovery_value: str,
    prov_target: str,
) -> None:
    """Provenance target in docs/product/intents/*.md form resolves to ancestor.

    Before T2, _resolve_discovery_path handled bare-path and backtick-path
    Discovery: values pointing to non-feature intents.  After T2 these arrive
    as path-form provenance targets.  close-work must follow them.
    """
    intents_dir = tmp_path / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True)

    cap_slug = "my-cap"
    (intents_dir / "my-cap.md").write_text(
        f"- **Slug:** {cap_slug}\n"
        "- **Status:** Accepted\n"
        "- **Decomposed:** 2026-09-01 closed-empty\n"
    )
    spec_fields = {"Slug": "test-spec", "Discovery": discovery_value}
    # Provenance record whose target is the repository-relative path (path form).
    prov_record = {
        "subject": "spec:test-spec",
        "field": "Discovery",
        "target": prov_target,
    }
    snap = _snapshot(provenance=[prov_record])
    ancestors = ci.resolve_intent_ancestors(
        "test-spec", "spec", spec_fields, tmp_path,
        _snapshot_provider=lambda _r: snap,
    )
    assert len(ancestors) == 1, f"Expected 1 ancestor, got {ancestors!r}"
    assert ancestors[0][0] == cap_slug


def test_ac0003_non_intent_discovery_contributes_no_edge(tmp_path: Path) -> None:
    """A Discovery: pointing to a non-intent (e.g. a spec file) contributes no edge."""
    intents_dir = tmp_path / "docs" / "product" / "intents"
    specs_dir = tmp_path / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    # The Discovery: target is a spec, not an intent.
    other_spec_dir = specs_dir / "other-spec"
    other_spec_dir.mkdir()
    (other_spec_dir / "spec.md").write_text(
        "- **Slug:** other-spec\n- **Status:** Implementing\n"
    )
    spec_fields = {
        "Slug": "my-spec",
        "Discovery": "docs/specs/other-spec/spec.md",
    }
    # Empty snapshot: no delivery relations or provenance records for my-spec,
    # so no ancestor is found regardless of the Discovery: value.
    snap = _snapshot()
    ancestors = ci.resolve_intent_ancestors(
        "my-spec", "spec", spec_fields, tmp_path, _snapshot_provider=lambda _r: snap
    )
    assert ancestors == [], (
        f"Expected no ancestors from empty snapshot, got {ancestors!r}"
    )


# ── Differential fixture builder ──────────────────────────────────────────────
#
# Models the work-item-capture-and-disposition tree (measured 2026-09-26):
# one Accepted ancestor with children terminus, four Accepted child intents each
# with spec terminus, and five grandchild specs reached through Discovery:.
# Nine descendants total: eight live, one (work-item-capture, Shipped) terminal.
#
# See plan.md § Design (LLD) › Verification fixtures — that sub-section is the
# single description of this fixture; this code follows it.


_ANCESTOR_SLUG = "work-item-capture-and-disposition"
_CHILD_SLUGS = ["wic-child-a", "wic-child-b", "wic-child-c", "wic-child-d"]
_SPEC_SLUGS = ["spec-a", "spec-b", "spec-c", "spec-d", "work-item-capture"]
# Distribution: child-d owns two specs (spec-d and work-item-capture).
_SPEC_TO_CHILD: dict[str, str] = {
    "spec-a": "wic-child-a",
    "spec-b": "wic-child-b",
    "spec-c": "wic-child-c",
    "spec-d": "wic-child-d",
    "work-item-capture": "wic-child-d",
}


def _write_differential_fixture(tmp_path: Path, *, all_terminal: bool) -> dict[str, tuple[str, str]]:
    """Write the differential fixture to tmp_path.

    Returns ``{slug: (kind, status)}`` for every descendant written.
    ``all_terminal=True`` produces the eligible arm; ``False`` the not-eligible arm.
    """
    intents_dir = tmp_path / "docs" / "product" / "intents"
    specs_dir = tmp_path / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    # Ancestor
    (intents_dir / f"{_ANCESTOR_SLUG}.md").write_text(
        f"- **Slug:** {_ANCESTOR_SLUG}\n"
        f"- **Status:** Accepted\n"
        f"- **Decomposed:** 2026-09-19 children\n"
    )

    # Child intents
    child_status = "Fulfilled" if all_terminal else "Accepted"
    descendants: dict[str, tuple[str, str]] = {}
    for slug in _CHILD_SLUGS:
        (intents_dir / f"{slug}.md").write_text(
            f"- **Slug:** {slug}\n"
            f"- **Status:** {child_status}\n"
            f"- **Parent intent:** intent:{_ANCESTOR_SLUG}\n"
            f"- **Decomposed:** 2026-09-19 spec\n"
        )
        descendants[slug] = ("intent", child_status)

    # Grandchild specs
    for spec_slug in _SPEC_SLUGS:
        child_slug = _SPEC_TO_CHILD[spec_slug]
        # Not-eligible arm: work-item-capture is Shipped (terminal); others live.
        # Eligible arm: all specs are Shipped.
        if all_terminal:
            spec_status = "Shipped"
        else:
            spec_status = "Shipped" if spec_slug == "work-item-capture" else "Implementing"
        spec_dir = specs_dir / spec_slug
        spec_dir.mkdir(exist_ok=True)
        (spec_dir / "spec.md").write_text(
            f"- **Slug:** {spec_slug}\n"
            f"- **Status:** {spec_status}\n"
            f"- **Discovery:** docs/product/intents/{child_slug}.md\n"
        )
        descendants[spec_slug] = ("spec", spec_status)

    return descendants


# ── AC-0017: not-eligible names every live descendant ────────────────────────


def test_ac0017_not_eligible_names_all_live_descendants(tmp_path: Path) -> None:
    """The not-eligible fixture names every live descendant; expected set derived from fixture.

    Uses the real filesystem (no injected seams) to exercise the production path.
    """
    descendants = _write_differential_fixture(tmp_path, all_terminal=False)

    # Derive the expected live set from the fixture, not from hard-coded slugs.
    expected_live = sorted(
        (slug, status)
        for slug, (kind, status) in descendants.items()
        if not _is_terminal(kind, status)
    )
    # Sanity: the fixture should have 8 live and 1 terminal descendant.
    assert len(expected_live) == 8, f"Fixture setup error: expected 8 live, got {expected_live}"

    # The children have Decomposed: spec, so the snapshot is needed for the
    # spec-terminus sub-walk. wic-child-d has two specs (projection-mismatch in
    # the real resolver), but the test uses a synthetic snapshot so both are found.
    snap = _snapshot(relations=[
        _direct("wic-child-a", "spec-a"),
        _direct("wic-child-b", "spec-b"),
        _direct("wic-child-c", "spec-c"),
        _direct("wic-child-d", "spec-d"),
        _direct("wic-child-d", "work-item-capture"),
    ])
    # Inject _freshness_checker=lambda: True because tmp_path is not a git
    # repository; this test targets AC-0017, not AC-0022.
    verdict = ci.check_ancestor_closure(
        _ANCESTOR_SLUG, "Accepted", "children", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snap,
    )
    assert isinstance(verdict, ci.ClosureNotEligible), (
        f"Expected ClosureNotEligible, got {verdict!r}"
    )
    assert set(verdict.live_descendants) == set(expected_live), (
        f"Live descendants mismatch.\n"
        f"  expected: {sorted(expected_live)}\n"
        f"  verdict:  {sorted(verdict.live_descendants)}"
    )


# ── AC-0016: eligible when all descendants terminal ───────────────────────────


def test_ac0016_eligible_when_all_descendants_terminal(tmp_path: Path) -> None:
    """A copy of the fixture with every descendant terminal returns eligible.

    Uses the real filesystem (no injected seams) through the same entry point
    as the not-eligible arm (AC-0017), proving both arms discriminate.
    """
    descendants = _write_differential_fixture(tmp_path, all_terminal=True)

    # All descendants should be terminal.
    live = [
        (slug, status)
        for slug, (kind, status) in descendants.items()
        if not _is_terminal(kind, status)
    ]
    assert live == [], f"Fixture setup error: expected all terminal, found live: {live}"

    # Same snapshot shape as AC-0017: same children, same spec mapping.
    snap = _snapshot(relations=[
        _direct("wic-child-a", "spec-a"),
        _direct("wic-child-b", "spec-b"),
        _direct("wic-child-c", "spec-c"),
        _direct("wic-child-d", "spec-d"),
        _direct("wic-child-d", "work-item-capture"),
    ])
    # Inject _freshness_checker=lambda: True because tmp_path is not a git
    # repository; this test targets AC-0016, not AC-0022.
    verdict = ci.check_ancestor_closure(
        _ANCESTOR_SLUG, "Accepted", "children", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snap,
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"Expected ClosureEligible, got {verdict!r}"
    )
