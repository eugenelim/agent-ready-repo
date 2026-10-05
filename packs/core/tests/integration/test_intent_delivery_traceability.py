"""Integration tests for intent delivery traceability (VI-1401, VI-1402).

**VI-1401** — ``test_vi1401_resolver_and_consumers_share_delivery_snapshot``
Runs 11 delivery fixture cases — direct, coordinated, explicit-empty,
dual-provenance, missing-direct, missing-brief, direct-projection-mismatch,
brief-projection-mismatch, unsafe-corpus, resource-limit, and
resolver-unavailable — through the canonical resolver CLI, close-work's
``check_ancestor_closure``, and lint-traceability (as a subprocess). Asserts
that both consumers' delivery subsets and fail-closed diagnostics match the
resolver's snapshot for every case.

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
import textwrap
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


# Load once for the session.
_resolver_mod = _load_resolver()
_ci_mod = _load_closure_index()


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
    close-work finds exactly the declared spec in its closure.
    lint-traceability exits 0 (no dangling, delivery edge wired from snapshot).
    VI-1302: CLI stdout matches in-process serialization byte-for-byte.
    """
    _make_intent(root, "feat-direct", decomposed="2026-10-05 spec")
    _make_spec(root, "feat-direct-spec", discovery="intent:feat-direct", status="Shipped")
    # Brief is the anchor for lint-traceability's delivery check.
    _make_brief(root, "anchor-brief")
    _install_resolver(root)

    # Resolver snapshot.
    rc, snapshot = _run_resolver_cli(root)
    assert rc == 0, f"direct: resolver should succeed; got exit {rc}"
    assert snapshot["complete"] is True
    rel_types = {r["type"] for r in snapshot["relations"]}
    assert "direct-delivery" in rel_types, "direct: snapshot must have direct-delivery"
    direct_rels = [r for r in snapshot["relations"] if r["type"] == "direct-delivery"]
    spec_ids = {r["spec"] for r in direct_rels}
    assert "spec:feat-direct-spec" in spec_ids, "direct: spec must be in relations"

    # VI-1302: compare installed CLI stdout with in-process serialization.
    # The installed copy is byte-identical to the source loaded as _resolver_mod,
    # so in-process calls use _resolver_mod directly. Both scan the same root.
    installed_path = root / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    in_process_snap = _resolver_mod.resolve_repository(root)
    in_process_json = _resolver_mod.serialize(in_process_snap)
    proc_stdout = subprocess.run(
        [sys.executable, str(installed_path), "--root", str(root)],
        capture_output=True,
        timeout=60,
    ).stdout.decode("utf-8")
    assert proc_stdout == in_process_json, (
        "VI-1302: installed CLI stdout must be byte-identical to in-process serialization"
    )

    # close-work: ClosureEligible with spec in descendants.
    ci = _ci_mod
    verdict = _check_ancestor_with_real_resolver(ci, "feat-direct", "Accepted", "spec", root)
    assert isinstance(verdict, ci.ClosureEligible), (
        f"direct: expected ClosureEligible, got {verdict!r}"
    )
    assert verdict.packet is not None
    descendant_slugs = {v[0] for v in verdict.packet.per_descendant_verdicts}
    assert "feat-direct-spec" in descendant_slugs, (
        f"direct: spec must be in descendants; got {descendant_slugs!r}"
    )

    # lint-traceability: exit 0 (delivery edge from snapshot, no dangling).
    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 0, (
        f"direct: lint-traceability must exit 0; got {lt_rc}\n"
        f"stdout={lt_out}\nstderr={lt_err}"
    )
    # Verify no delivery-resolver-unavailable in output.
    assert "delivery-resolver-unavailable" not in lt_out + lt_err, (
        "direct: delivery-resolver-unavailable must not appear when resolver is present"
    )


def _subtest_coordinated(root: Path) -> None:
    """Coordinated-delivery: intent(brief) → brief → spec.

    Resolver returns coordinated-delivery relations.
    close-work finds brief + spec in its closure.
    lint-traceability exits 0 with edges from snapshot.
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
    verdict = _check_ancestor_with_real_resolver(ci, "feat-coord", "Accepted", "brief", root)
    assert isinstance(verdict, ci.ClosureEligible), (
        f"coordinated: expected ClosureEligible, got {verdict!r}"
    )
    assert verdict.packet is not None
    descendant_slugs = {v[0] for v in verdict.packet.per_descendant_verdicts}
    assert "coord-b" in descendant_slugs, (
        f"coordinated: brief must be in descendants; got {descendant_slugs!r}"
    )
    assert "coord-spec" in descendant_slugs, (
        f"coordinated: spec must be in descendants; got {descendant_slugs!r}"
    )

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 0, (
        f"coordinated: lint-traceability must exit 0; got {lt_rc}\n"
        f"stdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-resolver-unavailable" not in lt_out + lt_err


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
    verdict = _check_ancestor_with_real_resolver(
        ci, "feat-empty", "Accepted", "direct-light", root
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"explicit-empty: expected ClosureEligible, got {verdict!r}"
    )
    assert verdict.basis == "direct-light"

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 0, (
        f"explicit-empty: lint-traceability must exit 0; got {lt_rc}\n"
        f"stdout={lt_out}\nstderr={lt_err}"
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
    # feat-dual1 (spec terminus): spec must be a descendant.
    v1 = _check_ancestor_with_real_resolver(ci, "feat-dual1", "Accepted", "spec", root)
    assert isinstance(v1, ci.ClosureEligible)
    assert v1.packet is not None
    assert "dual-spec" in {x[0] for x in v1.packet.per_descendant_verdicts}

    # feat-dual2 (brief terminus): brief and spec must be descendants.
    v2 = _check_ancestor_with_real_resolver(ci, "feat-dual2", "Accepted", "brief", root)
    assert isinstance(v2, ci.ClosureEligible)
    assert v2.packet is not None
    desc2 = {x[0] for x in v2.packet.per_descendant_verdicts}
    assert "dual-b" in desc2
    assert "dual-spec" in desc2

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 0, (
        f"dual-provenance: lint-traceability must exit 0; got {lt_rc}\n"
        f"stdout={lt_out}\nstderr={lt_err}"
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
    verdict = _check_ancestor_with_real_resolver(ci, "feat-missing", "Accepted", "spec", root)
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"missing-direct: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason, (
        f"missing-direct: reason must name delivery-diagnostic; got {verdict.reason!r}"
    )

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    # delivery-target-missing for an intent subject is informational (not hard).
    assert lt_rc == 0, (
        f"missing-direct: lint-traceability must exit 0 in default mode; "
        f"got {lt_rc}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-target-missing" in lt_out, (
        "missing-direct: delivery-target-missing must appear in lint output"
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
    verdict = _check_ancestor_with_real_resolver(
        ci, "feat-missingbrief", "Accepted", "brief", root
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"missing-brief: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 0, (
        f"missing-brief: lint-traceability must exit 0 in default mode; "
        f"got {lt_rc}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-target-missing" in lt_out


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
    verdict = _check_ancestor_with_real_resolver(
        ci, "feat-multimatch", "Accepted", "spec", root
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"direct-mismatch: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason

    # Normal mode: delivery-projection-mismatch is informational (exit 0).
    lt_rc_normal, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc_normal == 0, (
        f"direct-mismatch: normal mode must exit 0; "
        f"got {lt_rc_normal}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-projection-mismatch" in lt_out

    # Strict mode: delivery-projection-mismatch is a strict-fail (exit 1).
    lt_rc_strict, _, _ = _run_lint_traceability(root, strict=True)
    assert lt_rc_strict == 1, (
        f"direct-mismatch: strict mode must exit 1 for delivery-projection-mismatch; "
        f"got {lt_rc_strict}"
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
    verdict = _check_ancestor_with_real_resolver(
        ci, "feat-briefmatch", "Accepted", "brief", root
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"brief-mismatch: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-diagnostic" in verdict.reason

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 0, (
        f"brief-mismatch: lint-traceability must exit 0 in default mode; "
        f"got {lt_rc}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-projection-mismatch" in lt_out


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

    # lint-traceability subprocess with a stub resolver that outputs incomplete JSON + exit 1.
    stub_resolver_content = textwrap.dedent(
        """\
        import json, sys
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps({
            "schema_version": 1, "complete": False,
            "relations": [], "classifications": [], "provenance": [],
            "diagnostics": [{"code": "delivery-resource-limit",
                             "limit": "entries", "root": "."}]
        }))
        sys.exit(1)
        """
    )
    dest = root / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(stub_resolver_content, encoding="utf-8")

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 1, (
        f"resource-limit: lint-traceability must exit 1 when resolver exits non-zero; "
        f"got {lt_rc}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-resolver-unavailable" in lt_err, (
        "resource-limit: delivery-resolver-unavailable must appear in lint stderr"
    )


def _subtest_resolver_unavailable(root: Path) -> None:
    """Resolver-unavailable: no resolver installed at .agentbundle/bin/.

    Both consumers report delivery-resolver-unavailable and do not fall back.
    """
    _make_intent(root, "feat-unavail", decomposed="2026-10-05 spec")
    _make_brief(root, "anchor-brief")
    # Do NOT install resolver.

    ci = _ci_mod
    verdict = _check_ancestor_with_real_resolver(ci, "feat-unavail", "Accepted", "spec", root)
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"resolver-unavailable: expected ClosureRefuse, got {verdict!r}"
    )
    assert "delivery-resolver-unavailable" in verdict.reason, (
        f"resolver-unavailable: reason must name delivery-resolver-unavailable; "
        f"got {verdict.reason!r}"
    )

    lt_rc, lt_out, lt_err = _run_lint_traceability(root)
    assert lt_rc == 1, (
        f"resolver-unavailable: lint-traceability must exit 1; "
        f"got {lt_rc}\nstdout={lt_out}\nstderr={lt_err}"
    )
    assert "delivery-resolver-unavailable" in lt_err, (
        "resolver-unavailable: delivery-resolver-unavailable must appear in lint stderr"
    )


# ── Main integration test ─────────────────────────────────────────────────────


def test_vi1401_resolver_and_consumers_share_delivery_snapshot(
    tmp_path: Path,
) -> None:
    """VI-1401 — For 11 fixture cases, the resolver CLI, close-work's closure check,
    and lint-traceability all derive their delivery subsets and fail-closed diagnostics
    from the same canonical snapshot.

    Fixture cases: direct, coordinated, explicit-empty, dual-provenance,
    missing-direct, missing-brief, direct-projection-mismatch,
    brief-projection-mismatch, unsafe-corpus, resource-limit,
    resolver-unavailable.

    AC-0012, AC-0013, AC-0014, AC-0016, AC-0017, AC-0018, AC-0019.
    """
    _subtest_direct(tmp_path / "direct")
    _subtest_coordinated(tmp_path / "coordinated")
    _subtest_explicit_empty(tmp_path / "explicit-empty")
    _subtest_dual_provenance(tmp_path / "dual-provenance")
    _subtest_missing_direct(tmp_path / "missing-direct")
    _subtest_missing_brief(tmp_path / "missing-brief")
    _subtest_direct_projection_mismatch(tmp_path / "direct-mismatch")
    _subtest_brief_projection_mismatch(tmp_path / "brief-mismatch")
    _subtest_unsafe_corpus(tmp_path / "unsafe-corpus")
    _subtest_resource_limit(tmp_path / "resource-limit")
    _subtest_resolver_unavailable(tmp_path / "resolver-unavailable")


# ── Caller inventory ──────────────────────────────────────────────────────────


def test_vi1402_only_canonical_delivery_inverter_exists() -> None:
    """VI-1402 — Only adapter-root-bins/intent_delivery_relations.py implements
    feature-delivery parsing and inversion.

    Static markers for delivery production (assigning relation type as a value):
    - A source that assigns ``"direct-delivery"`` or ``"coordinated-delivery"``
      as a string value in source code is producing delivery relations.
      Only the canonical resolver does this.

    Retired consumer-local entry points that must be absent:
    - ``closure_index.py`` must NOT define ``_resolve_discovery_path`` (the
      pre-T2 function that inverted Discovery: from spec files; present at
      commit ``a2b0f6140``).
    - ``lint-traceability.py`` must NOT include ``"Discovery"`` in
      ``_SPEC_UP_FIELDS`` (the pre-T3 local delivery inversion path; present
      at commit ``a2b0f6140``).

    Both consumers must reference the installed resolver path
    ``.agentbundle/bin/intent_delivery_relations.py``.

    AC-0014.
    """
    # Collect all production .py files under packs/core/.apm/
    apm_root = _APM
    assert apm_root.is_dir(), f"APM root not found: {apm_root}"

    production_files = sorted(
        p for p in apm_root.rglob("*.py")
        if p.is_file() and not any(part.startswith("__") for part in p.parts)
    )
    assert production_files, "No production .py files found under .apm/"

    # ── Assertion 1: Only the canonical resolver produces delivery relation types ──
    # A "producer" of delivery relations assigns "direct-delivery" or
    # "coordinated-delivery" as a string value in source code.
    # We identify this by looking for ast.Constant nodes with these values
    # that appear as values in a dict (i.e., dict key "type" → value "direct-delivery").
    _DELIVERY_TYPE_LITERALS = {"direct-delivery", "coordinated-delivery"}
    producers: list[Path] = []

    for path in production_files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            # Look for dict literals: {"type": "direct-delivery", ...} or
            # assignments: d["type"] = "direct-delivery"
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

    resolver_rel = _RESOLVER_SRC.relative_to(_APM)
    non_resolver_producers = [
        p for p in producers
        if p.relative_to(_APM) != resolver_rel
    ]
    assert not non_resolver_producers, (
        "VI-1402: Only the canonical resolver may produce delivery relation types "
        "('direct-delivery', 'coordinated-delivery'); "
        "non-resolver producers found: "
        + ", ".join(str(p.relative_to(_APM)) for p in non_resolver_producers)
    )
    assert any(p.relative_to(_APM) == resolver_rel for p in producers), (
        "VI-1402: The canonical resolver must produce delivery relation types "
        "(sanity check: resolver source should contain these literals)"
    )

    # ── Assertion 2: Both consumers reference the installed resolver binary ──
    # Both files construct the path as root / ".agentbundle" / "bin" /
    # "intent_delivery_relations.py", so the filename string is the verifiable
    # marker for each; the ".agentbundle" and "bin" segments are also present.
    resolver_binary = "intent_delivery_relations.py"
    resolver_dir_segment = ".agentbundle"

    closure_source = _CLOSURE_INDEX_SRC.read_text(encoding="utf-8")
    assert resolver_binary in closure_source, (
        f"VI-1402: closure_index.py must reference '{resolver_binary}'"
    )
    assert resolver_dir_segment in closure_source, (
        "VI-1402: closure_index.py must reference the '.agentbundle' install prefix"
    )

    lint_source = _LINT_TRACEABILITY_SRC.read_text(encoding="utf-8")
    assert resolver_binary in lint_source, (
        f"VI-1402: lint-traceability.py must reference '{resolver_binary}'"
    )
    assert resolver_dir_segment in lint_source, (
        "VI-1402: lint-traceability.py must reference the '.agentbundle' install prefix"
    )

    # ── Assertion 3: Retired consumer-local inversion entry points are absent ──

    # 3a: _resolve_discovery_path was in pre-T2 closure_index.py (commit a2b0f6140).
    # It was the module-level function that inverted Discovery: from spec files.
    # After T2, this function was removed — delivery inversion is the resolver's job.
    assert "_resolve_discovery_path" not in closure_source, (
        "VI-1402: _resolve_discovery_path (retired pre-T2 local inversion function) "
        "must not be present in closure_index.py"
    )

    # 3b: "Discovery" was in _SPEC_UP_FIELDS in pre-T3 lint-traceability.py (commit
    # a2b0f6140). Its removal prevents the local winner-selection path from wiring
    # feature-delivery Discovery: edges. After T3, "Discovery" is NOT in _SPEC_UP_FIELDS.
    # We check the source for the specific assignment pattern.
    # The pre-T3 form was: _SPEC_UP_FIELDS = ("Contract", "Discovery", "Brief", "Parent intent")
    # The post-T3 form is: _SPEC_UP_FIELDS = ("Contract", "Brief", "Parent intent")
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
            # Check if "Discovery" is in the tuple/list assigned.
            if isinstance(node.value, (ast.Tuple, ast.List)):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and elt.value == "Discovery":
                        spec_up_fields_has_discovery = True
            break

    assert not spec_up_fields_has_discovery, (
        "VI-1402: 'Discovery' must not be in _SPEC_UP_FIELDS in lint-traceability.py "
        "(retired pre-T3 local delivery-inversion path)"
    )
