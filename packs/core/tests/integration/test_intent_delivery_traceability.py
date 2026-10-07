"""Integration tests for intent delivery traceability (VI-1401, VI-1402, VI-1802).

**VI-1401** — ``test_vi1401_resolver_and_consumers_share_delivery_snapshot``
Runs 12 delivery fixture cases — direct, coordinated, explicit-empty,
dual-provenance, missing-direct, missing-brief, direct-projection-mismatch,
brief-projection-mismatch, broken-spec-reference, unsafe-corpus, resource-limit,
and resolver-unavailable — through the canonical resolver CLI, close-work's
``check_ancestor_closure``, and lint-traceability (as a subprocess or in-process).
For positive cases, asserts each consumer's delivery edge or descendant set equals
the set derived from the resolver snapshot. For fail-closed cases, asserts
``delivery-resolver-unavailable`` or the correct diagnostic code.

**VI-1402** — ``test_vi1402_only_canonical_delivery_inverter_exists``
Inventories every production ``.py`` source under ``packs/core/.apm/`` and
asserts:

- Only ``adapter-root-bins/intent_delivery_relations.py`` produces the
  relation-type literals ``"direct-delivery"`` and ``"coordinated-delivery"``
  as dict *values* (i.e., implements feature-delivery parsing+inversion).
- Both consumers (``closure_index.py`` and ``lint-traceability.py``) reference
  ``.agentbundle/bin/intent_delivery_relations.py`` — the installed resolver.
- The retired consumer-local delivery inversion entry points are absent:
  ``_resolve_discovery_path`` from the pre-T2 ``closure_index.py`` (present
  at commit ``a2b0f6140``) and ``"Discovery"`` in lint-traceability's
  ``_SPEC_UP_FIELDS`` (present at commit ``a2b0f6140``).

**VI-1802** — ``test_vi1802_real_projection_installs_and_matches_source``
Uses the in-tree ``agentbundle.build.adapter_root_bins.apply_projection`` to
project the resolver to a clean temporary repository's ``.agentbundle/bin/``,
then invokes the projected binary with ``sys.executable -I -S`` (no
``agentbundle`` import path) and asserts its JSON equals
``serialize(resolve_repository(fixture))`` byte-for-byte. Also asserts that a
symlinked corpus entry forces exit 1.

Justification for the static markers used in VI-1402:
  The string literals ``"direct-delivery"`` and ``"coordinated-delivery"`` are
  the only relation types the canonical resolver *produces*. Any source that
  assigns either as a value in a dict (the form ``"type": "direct-delivery"``)
  would be reimplementing the resolver's relation-building logic.
  ``_resolve_discovery_path`` was the pre-T2 private function that inverted the
  ``Discovery:`` field from spec files back to an intent path — exactly the
  inversion the resolver now owns. ``"Discovery"`` in ``_SPEC_UP_FIELDS`` was
  the pre-T3 mechanism by which lint-traceability derived feature-delivery edges
  locally; its removal proves the old fallback parser is gone.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# ── Source locations ──────────────────────────────────────────────────────────

_PACK_ROOT = Path(__file__).resolve().parents[2]  # packs/core/
_APM = _PACK_ROOT / ".apm"
_RESOLVER_SRC = _APM / "adapter-root-bins" / "intent_delivery_relations.py"
_CLOSURE_INDEX_SRC = _APM / "skills" / "close-work" / "scripts" / "closure_index.py"
_LINT_TRACEABILITY_SRC = _APM / "skills" / "work-loop" / "scripts" / "lint-traceability.py"


# ── Module loaders ────────────────────────────────────────────────────────────


def _load_resolver() -> Any:
    """Load the resolver source under a unique module name."""
    key = "_integration_t4_core_intent_delivery_relations"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _RESOLVER_SRC)
    assert spec and spec.loader, f"resolver not found at {_RESOLVER_SRC}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_closure_index() -> Any:
    """Load closure_index.py under a unique module name (pack + skill prefix)."""
    key = "_integration_t4_core_close_work_closure_index"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _CLOSURE_INDEX_SRC)
    assert spec and spec.loader, f"closure_index not found at {_CLOSURE_INDEX_SRC}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_lint_traceability() -> Any:
    """Load lint-traceability.py under a unique module name (pack + skill prefix)."""
    key = "_integration_t8_core_work_loop_lint_traceability"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _LINT_TRACEABILITY_SRC)
    assert spec and spec.loader, f"lint-traceability not found at {_LINT_TRACEABILITY_SRC}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


# Load once for the session.
_resolver_mod = _load_resolver()
_ci_mod = _load_closure_index()
_lint_mod = _load_lint_traceability()


# ── Delivery edge and descendant helpers ──────────────────────────────────────


def _delivery_edges_from_snapshot(snapshot: dict[str, Any]) -> set[tuple[str, str]]:
    """Compute expected (producer, consumer) delivery edges from a snapshot.

    Mirrors the edge-building logic in lint-traceability's build_standalone:
    - direct-delivery: (intent_id, spec_id)
    - coordinated-delivery: (brief_id, spec_id) and (intent_id, brief_id)
    """
    edges: set[tuple[str, str]] = set()
    for rel in snapshot.get("relations", []):
        rtype = rel.get("type", "")
        intent_id = rel.get("intent", "")
        spec_id = rel.get("spec", "")
        brief_id = rel.get("brief", "")
        if rtype == "direct-delivery" and intent_id and spec_id:
            edges.add((intent_id, spec_id))
        elif rtype == "coordinated-delivery" and brief_id and spec_id:
            edges.add((brief_id, spec_id))
            if intent_id:
                edges.add((intent_id, brief_id))
    return edges


def _lint_delivery_edges(root: Path, snapshot: dict[str, Any]) -> set[tuple[str, str]]:
    """Run lint build_standalone with an injected snapshot; return g.edges.

    Uses the lint's Graph directly so the result reflects exactly the edges the
    lint wires from the resolver snapshot, without spawning a subprocess.
    """
    lint = _lint_mod
    layout = lint.load_layout(root)
    g = lint.Graph()
    rollup = lint.load_rollup_ids(root, layout)
    lint.build_standalone(root, layout, g, rollup, snapshot_provider=lambda _: snapshot)
    return set(g.edges)


def _expected_descendants_from_snapshot(
    snapshot: dict[str, Any],
    intent_slug: str,
    terminus: str,
) -> set[str]:
    """Compute expected descendant slugs for close-work from the snapshot.

    Returns the set of slug strings (without the type prefix) that the resolver
    snapshot's relations would produce as descendants for the given feature.
    """
    intent_id = f"intent:{intent_slug}"
    descendants: set[str] = set()
    for rel in snapshot.get("relations", []):
        if rel.get("intent") != intent_id:
            continue
        rtype = rel.get("type", "")
        if terminus == "spec" and rtype == "direct-delivery":
            spec_id = rel.get("spec", "")
            if spec_id.startswith("spec:"):
                descendants.add(spec_id[5:])
        elif terminus == "brief" and rtype == "coordinated-delivery":
            brief_id = rel.get("brief", "")
            spec_id = rel.get("spec", "")
            if brief_id.startswith("brief:"):
                descendants.add(brief_id[6:])
            if spec_id.startswith("spec:"):
                descendants.add(spec_id[5:])
    return descendants


# ── Fixture builders ──────────────────────────────────────────────────────────


def _make_intent(
    root: Path,
    slug: str,
    *,
    level: str = "feature",
    decomposed: str | None = None,
    status: str = "Accepted",
) -> None:
    d = root / "docs" / "product" / "intents"
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"- **Slug:** `{slug}`",
        f"- **Level:** {level}",
        f"- **Status:** {status}",
    ]
    if decomposed:
        lines.append(f"- **Decomposed:** {decomposed}")
    (d / f"{slug}.md").write_text(
        "\n".join(lines) + "\n\n## Outcome\nbody\n",
        encoding="utf-8",
    )


def _make_brief(
    root: Path,
    slug: str,
    *,
    parent: str | None = None,
    status: str = "Shipped",
) -> None:
    d = root / "docs" / "product" / "briefs"
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"- **Slug:** `{slug}`", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** {parent}")
    (d / f"{slug}.md").write_text(
        "\n".join(lines) + "\n\n## Outcome\nbody\n",
        encoding="utf-8",
    )


def _make_spec(
    root: Path,
    dir_name: str,
    *,
    discovery: str | None = None,
    brief: str | None = None,
    status: str = "Shipped",
) -> None:
    d = root / "docs" / "specs" / dir_name
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"- **Status:** {status}"]
    if discovery:
        lines.append(f"- **Discovery:** `{discovery}`")
    if brief:
        lines.append(f"- **Brief:** `{brief}`")
    (d / "spec.md").write_text(
        "\n".join(lines) + "\n\n## Outcome\nbody\n",
        encoding="utf-8",
    )


def _install_resolver(root: Path) -> None:
    """Install the resolver source and its co-located helper at root/.agentbundle/bin/."""
    dest_dir = root / ".agentbundle" / "bin"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_RESOLVER_SRC, dest_dir / "intent_delivery_relations.py")
    _helper_src = _APM / "adapter-root-bins" / "_file_safety.py"
    shutil.copy2(_helper_src, dest_dir / "_file_safety.py")


def _run_resolver_cli(root: Path) -> tuple[int, dict[str, Any]]:
    """Run the installed resolver CLI and return (exit_code, snapshot)."""
    resolver_path = root / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    proc = subprocess.run(
        [sys.executable, str(resolver_path), "--root", str(root)],
        capture_output=True,
        timeout=60,
    )
    data = json.loads(proc.stdout.decode("utf-8"))
    return proc.returncode, data


def _run_lint_traceability(root: Path, *, strict: bool = False) -> tuple[int, str, str]:
    """Run lint-traceability.py as a subprocess; return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(_LINT_TRACEABILITY_SRC), "--root", str(root), "--verbose"]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, capture_output=True, timeout=60)
    return (
        proc.returncode,
        proc.stdout.decode("utf-8", errors="replace"),
        proc.stderr.decode("utf-8", errors="replace"),
    )


def _check_ancestor_with_real_resolver(
    ci: Any,
    slug: str,
    status: str,
    terminus: str,
    root: Path,
) -> Any:
    """Call check_ancestor_closure using the production subprocess resolver."""
    return ci.check_ancestor_closure(
        slug,
        status,
        terminus,
        root,
        _freshness_checker=lambda: True,
        _snapshot_provider=ci._run_resolver,
        _decider="integration-test",
    )


def _check_ancestor_with_stub_provider(
    ci: Any,
    slug: str,
    status: str,
    terminus: str,
    root: Path,
    stub_provider: Any,
) -> Any:
    """Call check_ancestor_closure with an injected stub snapshot provider."""
    return ci.check_ancestor_closure(
        slug,
        status,
        terminus,
        root,
        _freshness_checker=lambda: True,
        _snapshot_provider=stub_provider,
        _decider="integration-test",
    )


# ── Per-case sub-tests ────────────────────────────────────────────────────────


def _subtest_direct(root: Path) -> None:
    """Direct-delivery: intent(spec) → spec.

    Resolver returns a complete snapshot with a direct-delivery relation.
    close-work finds exactly the declared spec in its closure (equality check).
    lint-traceability exits 0 with delivery edges matching the snapshot (equality check).
    """
    _make_intent(root, "feat-direct", decomposed="2026-10-05 spec")
    _make_spec(root, "feat-direct-spec", discovery="intent:feat-direct", status="Shipped")
    # Brief is the anchor for lint-traceability's delivery check.
    _make_brief(root, "anchor-brief")
    _install_resolver(root)

    # Resolver snapshot — spawned once per case.
    rc, snapshot = _run_resolver_cli(root)
    assert rc == 0, f"direct: resolver should succeed; got exit {rc}"
    assert snapshot["complete"] is True
    direct_rels = [r for r in snapshot["relations"] if r["type"] == "direct-delivery"]
    assert any(r["spec"] == "spec:feat-direct-spec" for r in direct_rels), (
        "direct: spec must appear in direct-delivery relations"
    )

    # close-work: ClosureEligible with descendant set equal to snapshot relations.
    # Feed the single snapshot to the in-process seam (resolver already spawned once).
    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-direct", "Accepted", "spec", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"direct: expected ClosureEligible, got {verdict!r}"
    )
    assert verdict.packet is not None
    descendant_slugs = {v[0] for v in verdict.packet.per_descendant_verdicts}
    expected_descendants = _expected_descendants_from_snapshot(snapshot, "feat-direct", "spec")
    assert descendant_slugs == expected_descendants, (
        f"direct: close-work descendants {descendant_slugs!r} != "
        f"expected from snapshot {expected_descendants!r}"
    )

    # lint-traceability: in-process with the same snapshot (resolver already spawned once).
    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"direct: lint-traceability must exit 0; got {exit_hint}\nhard={hard!r}"
    )
    assert not any("delivery-resolver-unavailable" in h for h in hard), (
        f"direct: delivery-resolver-unavailable must not appear: {hard!r}"
    )
    expected_edges = _delivery_edges_from_snapshot(snapshot)
    actual_edges = _lint_delivery_edges(root, snapshot)
    assert actual_edges == expected_edges, (
        f"direct: lint delivery edges {actual_edges!r} != "
        f"expected from snapshot {expected_edges!r}"
    )


def _subtest_coordinated(root: Path) -> None:
    """Coordinated-delivery: intent(brief) → brief → spec.

    Resolver returns coordinated-delivery relations.
    close-work descendant set equals snapshot relations (equality check).
    lint-traceability exits 0 with delivery edges matching the snapshot (equality check).
    """
    _make_intent(root, "feat-coord", decomposed="2026-10-05 brief")
    _make_brief(root, "coord-b", parent="intent:feat-coord", status="Shipped")
    _make_spec(root, "coord-spec", brief="brief:coord-b", status="Shipped")
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert rc == 0, f"coordinated: resolver should succeed; got exit {rc}"
    assert snapshot["complete"] is True
    coord_rels = [r for r in snapshot["relations"] if r["type"] == "coordinated-delivery"]
    assert coord_rels, "coordinated: snapshot must have coordinated-delivery"
    assert any(r["intent"] == "intent:feat-coord" for r in coord_rels)
    assert any(r["spec"] == "spec:coord-spec" for r in coord_rels)

    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-coord", "Accepted", "brief", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"coordinated: expected ClosureEligible, got {verdict!r}"
    )
    assert verdict.packet is not None
    descendant_slugs = {v[0] for v in verdict.packet.per_descendant_verdicts}
    expected_descendants = _expected_descendants_from_snapshot(snapshot, "feat-coord", "brief")
    assert descendant_slugs == expected_descendants, (
        f"coordinated: close-work descendants {descendant_slugs!r} != "
        f"expected from snapshot {expected_descendants!r}"
    )

    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"coordinated: lint-traceability must exit 0; got {exit_hint}\nhard={hard!r}"
    )
    assert not any("delivery-resolver-unavailable" in h for h in hard), (
        f"coordinated: delivery-resolver-unavailable must not appear: {hard!r}"
    )
    expected_edges = _delivery_edges_from_snapshot(snapshot)
    actual_edges = _lint_delivery_edges(root, snapshot)
    assert actual_edges == expected_edges, (
        f"coordinated: lint delivery edges {actual_edges!r} != "
        f"expected from snapshot {expected_edges!r}"
    )


def _subtest_explicit_empty(root: Path) -> None:
    """Explicit-empty: direct-light classification produces no-durable-child.

    Resolver returns no-durable-child classification.
    close-work returns ClosureEligible immediately (no snapshot needed for direct-light).
    lint-traceability exits 0.
    """
    _make_intent(root, "feat-empty", decomposed="2026-10-05 direct-light")
    _make_brief(root, "anchor-brief")
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert rc == 0
    assert snapshot["complete"] is True
    cls_list = snapshot.get("classifications", [])
    no_durable = [c for c in cls_list if c.get("classification") == "no-durable-child"]
    assert any(c["intent"] == "intent:feat-empty" for c in no_durable), (
        f"explicit-empty: no-durable-child classification expected; got {cls_list!r}"
    )

    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-empty", "Accepted", "direct-light", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"explicit-empty: expected ClosureEligible, got {verdict!r}"
    )
    assert verdict.basis == "direct-light"

    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"explicit-empty: lint-traceability must exit 0; got {exit_hint}\nhard={hard!r}"
    )
    expected_edges = _delivery_edges_from_snapshot(snapshot)
    actual_edges = _lint_delivery_edges(root, snapshot)
    assert actual_edges == expected_edges, (
        f"explicit-empty: lint delivery edges {actual_edges!r} != "
        f"expected from snapshot {expected_edges!r}"
    )


def _subtest_dual_provenance(root: Path) -> None:
    """Dual-provenance: one spec participates in both direct and coordinated delivery.

    AC-0006: a spec with Discovery: (direct) and Brief: (coordinated) returns both
    relation types from two different feature intents.
    close-work for each intent separately finds the spec in its delivery closure.
    """
    # feat-dual1 declares spec route; feat-dual2 declares brief route.
    _make_intent(root, "feat-dual1", decomposed="2026-10-05 spec")
    _make_intent(root, "feat-dual2", decomposed="2026-10-05 brief")
    _make_brief(root, "dual-b", parent="intent:feat-dual2", status="Shipped")
    # Spec points to both intents via Discovery: (feat-dual1) and Brief: (dual-b→feat-dual2).
    _make_spec(
        root,
        "dual-spec",
        discovery="intent:feat-dual1",
        brief="brief:dual-b",
        status="Shipped",
    )
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert rc == 0
    assert snapshot["complete"] is True
    direct_rels = [
        r for r in snapshot["relations"]
        if r["type"] == "direct-delivery" and r["spec"] == "spec:dual-spec"
    ]
    coord_rels = [
        r for r in snapshot["relations"]
        if r["type"] == "coordinated-delivery" and r["spec"] == "spec:dual-spec"
    ]
    assert direct_rels, "dual-provenance: direct-delivery relation for dual-spec expected"
    assert coord_rels, "dual-provenance: coordinated-delivery relation for dual-spec expected"
    assert direct_rels[0]["intent"] == "intent:feat-dual1"
    assert coord_rels[0]["intent"] == "intent:feat-dual2"

    ci = _ci_mod
    # feat-dual1 (spec terminus): descendant set equals snapshot relations.
    # Feed the single snapshot to the in-process seam (resolver spawned once above).
    v1 = _check_ancestor_with_stub_provider(
        ci, "feat-dual1", "Accepted", "spec", root, lambda _r: snapshot
    )
    assert isinstance(v1, ci.ClosureEligible)
    assert v1.packet is not None
    desc1 = {x[0] for x in v1.packet.per_descendant_verdicts}
    expected_desc1 = _expected_descendants_from_snapshot(snapshot, "feat-dual1", "spec")
    assert desc1 == expected_desc1, (
        f"dual-provenance: feat-dual1 descendants {desc1!r} != "
        f"expected from snapshot {expected_desc1!r}"
    )

    # feat-dual2 (brief terminus): descendant set equals snapshot relations.
    v2 = _check_ancestor_with_stub_provider(
        ci, "feat-dual2", "Accepted", "brief", root, lambda _r: snapshot
    )
    assert isinstance(v2, ci.ClosureEligible)
    assert v2.packet is not None
    desc2 = {x[0] for x in v2.packet.per_descendant_verdicts}
    expected_desc2 = _expected_descendants_from_snapshot(snapshot, "feat-dual2", "brief")
    assert desc2 == expected_desc2, (
        f"dual-provenance: feat-dual2 descendants {desc2!r} != "
        f"expected from snapshot {expected_desc2!r}"
    )

    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"dual-provenance: lint-traceability must exit 0; got {exit_hint}\nhard={hard!r}"
    )
    expected_edges = _delivery_edges_from_snapshot(snapshot)
    actual_edges = _lint_delivery_edges(root, snapshot)
    assert actual_edges == expected_edges, (
        f"dual-provenance: lint delivery edges {actual_edges!r} != "
        f"expected from snapshot {expected_edges!r}"
    )


def _subtest_missing_direct(root: Path) -> None:
    """Missing-direct: intent has spec route but no spec points to it.

    Resolver reports delivery-target-missing for the feature intent.
    close-work returns ClosureRefuse (delivery-diagnostic blocks closure).
    lint-traceability: diagnostic is informational in default mode (exit 0).
    """
    _make_intent(root, "feat-missing", decomposed="2026-10-05 spec")
    _make_brief(root, "anchor-brief")  # anchor only
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    # Exit 0: snapshot is complete even when diagnostics exist.
    assert snapshot["complete"] is True
    diag_codes = [d["code"] for d in snapshot["diagnostics"]]
    assert "delivery-target-missing" in diag_codes, (
        f"missing-direct: delivery-target-missing expected; got {diag_codes!r}"
    )
    missing_diags = [
        d for d in snapshot["diagnostics"]
        if d["code"] == "delivery-target-missing" and d.get("subject") == "intent:feat-missing"
    ]
    assert missing_diags

    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-missing", "Accepted", "spec", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"missing-direct: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason, (
        f"missing-direct: reason must name delivery-diagnostic; got {verdict.reason!r}"
    )

    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    # delivery-target-missing for an intent subject is informational (not hard).
    assert exit_hint == 0, (
        f"missing-direct: lint-traceability must exit 0 in default mode; "
        f"got {exit_hint}\nhard={hard!r}"
    )
    assert any("delivery-target-missing" in ln for ln in out_lines), (
        f"missing-direct: delivery-target-missing must appear in lint output: {out_lines!r}"
    )


def _subtest_missing_brief(root: Path) -> None:
    """Missing-brief: intent has brief route but no brief points to it.

    Resolver reports delivery-target-missing.
    close-work returns ClosureRefuse.
    lint-traceability: diagnostic is informational (exit 0).
    """
    _make_intent(root, "feat-missingbrief", decomposed="2026-10-05 brief")
    # A sibling intent and its brief supply the anchor for lint-traceability.
    # feat-other has no delivery route so it creates no diagnostics; other-brief
    # points to it and gives lint-traceability a valid edge without dangling.
    _make_intent(root, "feat-other")
    _make_brief(root, "other-brief", parent="intent:feat-other")
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert snapshot["complete"] is True
    missing_diags = [
        d for d in snapshot["diagnostics"]
        if d["code"] == "delivery-target-missing"
        and d.get("subject") == "intent:feat-missingbrief"
    ]
    assert missing_diags, (
        f"missing-brief: delivery-target-missing for feat-missingbrief expected; "
        f"diagnostics={snapshot['diagnostics']!r}"
    )

    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-missingbrief", "Accepted", "brief", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"missing-brief: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason

    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"missing-brief: lint-traceability must exit 0 in default mode; "
        f"got {exit_hint}\nhard={hard!r}"
    )
    assert any("delivery-target-missing" in ln for ln in out_lines), (
        f"missing-brief: delivery-target-missing must appear in lint output: {out_lines!r}"
    )


def _subtest_direct_projection_mismatch(root: Path) -> None:
    """Direct-projection-mismatch: two specs claim the same feature intent.

    Resolver reports delivery-projection-mismatch.
    close-work returns ClosureRefuse.
    lint-traceability: strict exit 1, normal mode exit 0 (informational).
    """
    _make_intent(root, "feat-multimatch", decomposed="2026-10-05 spec")
    _make_spec(root, "match-spec-a", discovery="intent:feat-multimatch")
    _make_spec(root, "match-spec-b", discovery="intent:feat-multimatch")
    _make_brief(root, "anchor-brief")
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert snapshot["complete"] is True
    proj_diags = [
        d for d in snapshot["diagnostics"]
        if d["code"] == "delivery-projection-mismatch"
        and d.get("subject") == "intent:feat-multimatch"
    ]
    assert proj_diags, (
        f"direct-mismatch: delivery-projection-mismatch expected; "
        f"diagnostics={snapshot['diagnostics']!r}"
    )

    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-multimatch", "Accepted", "spec", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"direct-mismatch: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason

    lint = _lint_mod
    # Normal mode: delivery-projection-mismatch is informational (exit 0).
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"direct-mismatch: normal mode must exit 0; "
        f"got {exit_hint}\nhard={hard!r}"
    )
    assert any("delivery-projection-mismatch" in ln for ln in out_lines), (
        f"direct-mismatch: delivery-projection-mismatch must appear in lint output: {out_lines!r}"
    )

    # Strict mode: delivery-projection-mismatch is a strict-fail (exit 1).
    _, hard_strict, exit_strict = lint.check(
        root, True, snapshot_provider=lambda _r: snapshot
    )
    assert exit_strict == 1, (
        f"direct-mismatch: strict mode must exit 1 for delivery-projection-mismatch; "
        f"got {exit_strict}"
    )


def _subtest_brief_projection_mismatch(root: Path) -> None:
    """Brief-projection-mismatch: two briefs point to the same feature intent.

    Resolver reports delivery-projection-mismatch.
    close-work returns ClosureRefuse.
    lint-traceability: diagnostic is informational in default mode.
    """
    _make_intent(root, "feat-briefmatch", decomposed="2026-10-05 brief")
    _make_brief(root, "briefmatch-a", parent="intent:feat-briefmatch")
    _make_brief(root, "briefmatch-b", parent="intent:feat-briefmatch")
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert snapshot["complete"] is True
    proj_diags = [
        d for d in snapshot["diagnostics"]
        if d["code"] == "delivery-projection-mismatch"
        and d.get("subject") == "intent:feat-briefmatch"
    ]
    assert proj_diags, (
        f"brief-mismatch: delivery-projection-mismatch for feat-briefmatch expected; "
        f"diagnostics={snapshot['diagnostics']!r}"
    )

    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-briefmatch", "Accepted", "brief", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"brief-mismatch: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason

    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"brief-mismatch: lint-traceability must exit 0 in default mode; "
        f"got {exit_hint}\nhard={hard!r}"
    )
    assert any("delivery-projection-mismatch" in ln for ln in out_lines), (
        f"brief-mismatch: delivery-projection-mismatch must appear in output: {out_lines!r}"
    )


def _subtest_unsafe_corpus(root: Path) -> None:
    """Unsafe-corpus: a symlinked entry in the intents directory.

    The resolver cannot open the symlink and returns an incomplete snapshot.
    Both consumers report delivery-resolver-unavailable (incomplete snapshot).

    This test skips outside CI when symlink creation is unavailable.
    """
    _make_intent(root, "feat-safe")  # a real intent so the corpus is non-empty
    _make_brief(root, "anchor-brief")

    # Plant a symlink in the intents directory.
    intents_dir = root / "docs" / "product" / "intents"
    link_target = root / "docs" / "product" / "intents" / "real-target.md"
    link_target.write_text("- **Slug:** `real-target`\n", encoding="utf-8")
    symlink_path = intents_dir / "symlinked.md"
    try:
        symlink_path.symlink_to(link_target)
    except (OSError, NotImplementedError) as exc:
        if os.environ.get("CI"):
            pytest.fail(f"unsafe-corpus: CI must support symlinks: {exc}")
        pytest.skip(f"unsafe-corpus: symlink creation unavailable ({exc})")

    _install_resolver(root)

    # Resolver must return an incomplete snapshot for unsafe corpus.
    rc, snapshot = _run_resolver_cli(root)
    assert rc == 1, f"unsafe-corpus: resolver must exit 1 for incomplete snapshot; got {rc}"
    assert snapshot["complete"] is False, "unsafe-corpus: snapshot must be incomplete"

    # close-work: _run_resolver raises ValueError (incomplete → delivery-resolver-unavailable).
    ci = _ci_mod
    verdict = _check_ancestor_with_real_resolver(ci, "feat-safe", "Accepted", "spec", root)
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"unsafe-corpus: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-resolver-unavailable" in verdict.reason, (
        f"unsafe-corpus: reason must name delivery-resolver-unavailable; got {verdict.reason!r}"
    )

    # lint-traceability: exits 1 with delivery-resolver-unavailable.
    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 1, (
        f"unsafe-corpus: lint-traceability must exit 1; "
        f"got {lt_rc}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-resolver-unavailable" in lt_err, (
        "unsafe-corpus: delivery-resolver-unavailable must appear in lint stderr"
    )


def _subtest_resource_limit(root: Path) -> None:
    """Resource-limit: resolver returns an incomplete delivery-resource-limit snapshot.

    Resolver side: calling resolve_repository with limits={"entries": 0} on a
    non-empty corpus returns an incomplete snapshot with delivery-resource-limit.

    Consumer side: both consumers report delivery-resolver-unavailable when the
    resolver subprocess exits non-zero (an incomplete snapshot causes exit 1).
    """
    # Resolver side — in-process with limits override.
    _make_intent(root, "feat-limit")
    snap = _resolver_mod.resolve_repository(root, limits={"entries": 0})
    assert snap["complete"] is False, "resource-limit: in-process snapshot must be incomplete"
    assert any(
        d["code"] == "delivery-resource-limit" for d in snap["diagnostics"]
    ), f"resource-limit: delivery-resource-limit diagnostic expected; got {snap['diagnostics']!r}"

    # Consumer side — inject a stub provider that raises (simulating incomplete snapshot).
    def _stub_provider(r: Path) -> dict[str, Any]:
        raise ValueError("delivery-resolver-unavailable: incomplete snapshot")

    _make_brief(root, "anchor-brief")
    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-limit", "Accepted", "spec", root, _stub_provider
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"resource-limit: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-resolver-unavailable" in verdict.reason

    # lint-traceability in-process: inject the same stub provider that raises.
    # After T9 the linter finds its resolver beside its own scripts/ directory;
    # the only way to inject a failing resolver is through the snapshot_provider seam.
    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=_stub_provider
    )
    assert exit_hint == 1, (
        f"resource-limit: lint-traceability must signal exit 1 when resolver raises; "
        f"got {exit_hint}\nhard={hard!r}"
    )
    assert any("delivery-resolver-unavailable" in h for h in hard), (
        f"resource-limit: delivery-resolver-unavailable must appear in hard violations; "
        f"got {hard!r}"
    )


def _subtest_broken_spec_reference(root: Path) -> None:
    """Broken-spec-reference: a spec carries a traversing Discovery: field.

    The feature also has one valid, shipped spec, so it resolves cleanly and
    would be closable on its own; only the broken spec's own
    delivery-reference-unsafe diagnostic (AC-0020) can refuse it.
    lint-traceability: the diagnostic is informational in default mode (exit 0),
    and the informational line appears in stdout.
    """
    _make_intent(root, "feat-broken", decomposed="2026-10-05 spec")
    # Traversing Discovery: reference — contains product/intents/ AND ..
    _make_spec(
        root,
        "broken-ref-spec",
        discovery="../product/intents/feat-broken.md",
        status="Shipped",
    )
    _make_spec(root, "good-spec", discovery="intent:feat-broken", status="Shipped")
    _make_brief(root, "anchor-brief")
    _install_resolver(root)

    rc, snapshot = _run_resolver_cli(root)
    assert rc == 0, f"broken-spec-ref: resolver should succeed; got exit {rc}"
    assert not [
        d for d in snapshot["diagnostics"] if d.get("subject") == "intent:feat-broken"
    ], "broken-spec-ref: the feature itself must resolve cleanly"
    assert snapshot["complete"] is True
    unsafe_diags = [
        d for d in snapshot["diagnostics"]
        if d.get("code") == "delivery-reference-unsafe"
        and d.get("subject") == "spec:broken-ref-spec"
        and d.get("field") == "Discovery"
    ]
    assert unsafe_diags, (
        f"broken-spec-ref: delivery-reference-unsafe (spec subject) expected; "
        f"diagnostics={snapshot['diagnostics']!r}"
    )

    # close-work: AC-0020 refuses the spec-route feature on the broken spec's
    # own diagnostic, although its only resolved descendant is terminal.
    # Feed the single snapshot to the in-process seam (resolver spawned once above).
    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-broken", "Accepted", "spec", root, lambda _r: snapshot
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"broken-spec-ref: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-reference-unsafe" in verdict.reason, (
        f"broken-spec-ref: reason must name the broken spec's code; got {verdict.reason!r}"
    )

    # lint-traceability: informational in default mode (exit 0); line appears in output.
    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=lambda _r: snapshot
    )
    assert exit_hint == 0, (
        f"broken-spec-ref: lint-traceability must exit 0 in default mode; "
        f"got {exit_hint}\nhard={hard!r}"
    )
    assert any("delivery-reference-unsafe" in ln for ln in out_lines), (
        f"broken-spec-ref: delivery-reference-unsafe must appear in lint output: {out_lines!r}"
    )


def _subtest_resolver_unavailable(root: Path) -> None:
    """Resolver-unavailable: both consumers fail closed when the resolver raises.

    After T9 the resolver copy ships beside each consumer, so the "absent binary"
    case is exercised through the snapshot-provider seam (VI-1902 in the copies
    test file proves the binary-absent path directly).  Here we inject a provider
    that raises ValueError to prove neither consumer falls back.
    """
    _make_intent(root, "feat-unavail", decomposed="2026-10-05 spec")
    _make_brief(root, "anchor-brief")

    def _unavail(_root: Any) -> dict[str, Any]:
        raise ValueError("delivery-resolver-unavailable: simulated unavailable")

    # close-work: ClosureRefuse with delivery-resolver-unavailable.
    ci = _ci_mod
    verdict = _check_ancestor_with_stub_provider(
        ci, "feat-unavail", "Accepted", "spec", root, _unavail
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"resolver-unavailable: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-resolver-unavailable" in verdict.reason, (
        f"resolver-unavailable: reason must name delivery-resolver-unavailable; "
        f"got {verdict.reason!r}"
    )

    # lint-traceability: delivery-resolver-unavailable DANGLING, exit 1.
    lint = _lint_mod
    out_lines, hard, exit_hint = lint.check(
        root, False, snapshot_provider=_unavail
    )
    assert exit_hint == 1, (
        f"resolver-unavailable: lint must signal exit 1; got {exit_hint}\n"
        f"hard={hard!r}"
    )
    assert any("delivery-resolver-unavailable" in h for h in hard), (
        f"resolver-unavailable: delivery-resolver-unavailable must appear in hard "
        f"violations; got {hard!r}"
    )


# ── Main integration test ─────────────────────────────────────────────────────


def test_vi1401_resolver_and_consumers_share_delivery_snapshot(
    tmp_path: Path,
) -> None:
    """VI-1401 — For 12 fixture cases, the resolver CLI, close-work's closure check,
    and lint-traceability all derive their delivery subsets and fail-closed diagnostics
    from the same canonical snapshot. For positive cases, consumer edge and descendant
    sets are asserted equal to the sets derived from the resolver snapshot's relations.

    Fixture cases: direct, coordinated, explicit-empty, dual-provenance,
    missing-direct, missing-brief, direct-projection-mismatch,
    brief-projection-mismatch, broken-spec-reference, unsafe-corpus,
    resource-limit, resolver-unavailable.

    AC-0012, AC-0013, AC-0014, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020.
    """
    _subtest_direct(tmp_path / "direct")
    _subtest_coordinated(tmp_path / "coordinated")
    _subtest_explicit_empty(tmp_path / "explicit-empty")
    _subtest_dual_provenance(tmp_path / "dual-provenance")
    _subtest_missing_direct(tmp_path / "missing-direct")
    _subtest_missing_brief(tmp_path / "missing-brief")
    _subtest_direct_projection_mismatch(tmp_path / "direct-mismatch")
    _subtest_brief_projection_mismatch(tmp_path / "brief-mismatch")
    _subtest_broken_spec_reference(tmp_path / "broken-spec-ref")
    _subtest_unsafe_corpus(tmp_path / "unsafe-corpus")
    _subtest_resource_limit(tmp_path / "resource-limit")
    _subtest_resolver_unavailable(tmp_path / "resolver-unavailable")


# ── Caller inventory ──────────────────────────────────────────────────────────


def test_vi1402_only_canonical_delivery_inverter_exists() -> None:
    """VI-1402 — After T9, only the adapter-root-bins source and its two
    byte-identical skill copies produce delivery-relation types.  Each consumer
    locates the resolver beside its own file via ``_RESOLVER_PATH``.  Retired
    consumer-local inversion entry points are absent.

    Static markers for delivery production (assigning relation type as a value):
    - A source that assigns ``"direct-delivery"`` or ``"coordinated-delivery"``
      as a string value is producing delivery relations.
    - Accepted: adapter-root-bins source + close-work copy + work-loop copy
      (each byte-identical to the source).

    Retired consumer-local entry points that must be absent:
    - ``closure_index.py`` must NOT define ``_resolve_discovery_path``.
    - ``lint-traceability.py`` must NOT include ``"Discovery"`` in
      ``_SPEC_UP_FIELDS``.

    AC-0014.
    """
    apm_root = _APM
    assert apm_root.is_dir(), f"APM root not found: {apm_root}"

    production_files = sorted(
        p for p in apm_root.rglob("*.py")
        if p.is_file() and not any(part.startswith("__") for part in p.parts)
    )
    assert production_files, "No production .py files found under .apm/"

    # ── Assertion 1: Only the source + two byte-identical copies produce ────────
    _DELIVERY_TYPE_LITERALS = {"direct-delivery", "coordinated-delivery"}
    producers: list[Path] = []

    for path in production_files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, val in zip(node.keys, node.values, strict=False):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "type"
                        and isinstance(val, ast.Constant)
                        and val.value in _DELIVERY_TYPE_LITERALS
                    ):
                        producers.append(path)
                        break

    # Accepted: source + 2 byte-identical skill copies.
    _cw_copy = _APM / "skills" / "close-work" / "scripts" / "intent_delivery_relations.py"
    _wl_copy = _APM / "skills" / "work-loop" / "scripts" / "intent_delivery_relations.py"
    accepted_relpaths = {
        _RESOLVER_SRC.relative_to(_APM),
        _cw_copy.relative_to(_APM),
        _wl_copy.relative_to(_APM),
    }
    non_accepted = [
        p for p in producers
        if p.relative_to(_APM) not in accepted_relpaths
    ]
    assert not non_accepted, (
        "VI-1402: Only the source and its two skill copies may produce delivery "
        "relation types; unexpected producers: "
        + ", ".join(str(p.relative_to(_APM)) for p in non_accepted)
    )
    assert any(
        p.relative_to(_APM) == _RESOLVER_SRC.relative_to(_APM) for p in producers
    ), "VI-1402: canonical resolver source must produce delivery relation types"

    # Byte identity of each skill copy.
    source_bytes = _RESOLVER_SRC.read_bytes()
    for copy_path in (_cw_copy, _wl_copy):
        assert copy_path.read_bytes() == source_bytes, (
            f"VI-1402: {copy_path.relative_to(_APM)} must be byte-identical to source"
        )

    # ── Assertion 2: Each consumer locates resolver via _RESOLVER_PATH ──────────
    closure_source = _CLOSURE_INDEX_SRC.read_text(encoding="utf-8")
    lint_source = _LINT_TRACEABILITY_SRC.read_text(encoding="utf-8")

    assert "_RESOLVER_PATH" in closure_source, (
        "VI-1402: closure_index.py must define _RESOLVER_PATH"
    )
    assert "_RESOLVER_PATH" in lint_source, (
        "VI-1402: lint-traceability.py must define _RESOLVER_PATH"
    )

    # ── Assertion 3: Retired consumer-local inversion entry points are absent ──
    assert "_resolve_discovery_path" not in closure_source, (
        "VI-1402: _resolve_discovery_path (retired pre-T2 local inversion function) "
        "must not be present in closure_index.py"
    )
    try:
        lint_tree = ast.parse(lint_source, filename=str(_LINT_TRACEABILITY_SRC))
    except SyntaxError as exc:
        pytest.fail(f"VI-1402: lint-traceability.py has a syntax error: {exc}")

    spec_up_fields_has_discovery = False
    for node in ast.walk(lint_tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_SPEC_UP_FIELDS"
        ):
            if isinstance(node.value, (ast.Tuple, ast.List)):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and elt.value == "Discovery":
                        spec_up_fields_has_discovery = True
            break
    assert not spec_up_fields_has_discovery, (
        "VI-1402: 'Discovery' must not be in _SPEC_UP_FIELDS in lint-traceability.py "
        "(retired pre-T3 local delivery-inversion path)"
    )


# ── Real-projection test ──────────────────────────────────────────────────────


def test_vi1802_real_projection_installs_and_matches_source(tmp_path: Path) -> None:
    """VI-1802 — apply_projection delivers the resolver to .agentbundle/bin/;
    the installed binary invoked with ``sys.executable -I -S`` (isolated mode,
    no site-packages — so ``agentbundle`` is not importable) produces JSON
    byte-identical to ``serialize(resolve_repository(fixture))``.

    Proves the projected resolver is self-contained via its co-located
    ``_file_safety.py`` helper (decision 1) and does not silently import
    ``agentbundle`` from the environment.

    Also asserts a symlinked corpus entry forces exit 1 (incomplete snapshot).
    """
    from agentbundle.build.adapter_root_bins import apply_projection  # type: ignore[import]

    # Minimal fixture repository.
    _make_intent(tmp_path, "feat-proj", decomposed="2026-10-05 spec")
    _make_spec(tmp_path, "proj-spec", discovery="intent:feat-proj", status="Shipped")
    _make_brief(tmp_path, "anchor-brief")

    # Project adapter-root-bins from the real packs tree to tmp_path.
    packs_dir = _PACK_ROOT.parent  # packs/core/ → packs/
    apply_projection(tmp_path, packs_dir)

    projected = tmp_path / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    assert projected.exists(), f"VI-1802: projected resolver not found at {projected}"
    helper = tmp_path / ".agentbundle" / "bin" / "_file_safety.py"
    assert helper.exists(), f"VI-1802: projected _file_safety.py not found at {helper}"

    # Invoke with -I -S: isolated (no user site-packages, no PYTHONPATH) and
    # no site module — agentbundle must not be importable.
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(projected), "--root", str(tmp_path)],
        capture_output=True,
        timeout=60,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, (
        f"VI-1802: projected CLI must exit 0 for a complete snapshot; "
        f"got {result.returncode}\n"
        f"stderr={result.stderr.decode('utf-8', errors='replace')}"
    )

    # Byte-identical comparison with in-process serialization.
    in_process_snap = _resolver_mod.resolve_repository(tmp_path)
    expected_json = _resolver_mod.serialize(in_process_snap)
    actual_json = result.stdout.decode("utf-8")
    assert actual_json == expected_json, (
        "VI-1802: projected CLI stdout must be byte-identical to "
        "serialize(resolve_repository(fixture))"
    )

    # Symlinked corpus entry forces exit 1 (incomplete snapshot).
    intents_dir = tmp_path / "docs" / "product" / "intents"
    real_file = tmp_path / "real_intent_for_symlink.md"
    real_file.write_text(
        "# Real\n\n- **Slug:** `real-sl`\n- **Level:** feature\n", encoding="utf-8"
    )
    try:
        (intents_dir / "symlinked.md").symlink_to(real_file)
    except OSError:
        pytest.skip("VI-1802: symlinks unavailable on this platform")

    result2 = subprocess.run(
        [sys.executable, "-I", "-S", str(projected), "--root", str(tmp_path)],
        capture_output=True,
        timeout=60,
        cwd=str(tmp_path),
    )
    assert result2.returncode == 1, (
        f"VI-1802: projected CLI must exit 1 for incomplete snapshot; "
        f"got {result2.returncode}"
    )
    snap2 = json.loads(result2.stdout.decode("utf-8"))
    assert snap2["complete"] is False, (
        "VI-1802: snapshot must be incomplete when corpus contains a symlink"
    )
