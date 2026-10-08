# STUB: AC-0020
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

MODULE = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "close-work"
    / "scripts"
    / "closure_index.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_core_close_work_closure_index_ac0020", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ci = _load()


# ── Snapshot fixture helpers ──────────────────────────────────────────────────


def _snap(
    *,
    relations: list[dict[str, Any]] | None = None,
    classifications: list[dict[str, Any]] | None = None,
    provenance: list[dict[str, Any]] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
    artifacts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a valid snapshot dict for provider injection.

    Auto-populates ``artifacts`` from relation spec/brief identifiers when not
    supplied, using the canonical path grammar.
    """
    _rels = relations or []
    if artifacts is None:
        _arts: dict[str, str] = {}
        for _rel in _rels:
            for _id_key, _prefix, _path_tmpl in (
                ("spec", "spec:", "docs/specs/{slug}/spec.md"),
                ("brief", "brief:", "docs/product/briefs/{slug}.md"),
            ):
                _val = _rel.get(_id_key, "")
                if _val.startswith(_prefix) and _val not in _arts:
                    _slug = _val[len(_prefix):]
                    _arts[_val] = _path_tmpl.format(slug=_slug)
    else:
        _arts = artifacts
    return {
        "schema_version": 1,
        "complete": True,
        "relations": _rels,
        "classifications": classifications or [],
        "provenance": provenance or [],
        "diagnostics": diagnostics or [],
        "artifacts": _arts,
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


def _diag(
    code: str,
    subject: str,
    field: str | None = None,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """Build a diagnostic record."""
    d: dict[str, Any] = {"code": code, "subject": subject}
    if field is not None:
        d["field"] = field
    if targets is not None:
        d["targets"] = targets
    return d


# ── Helpers to build real on-disk fixtures ────────────────────────────────────


def _write_spec(root: Path, slug: str, status: str = "Shipped") -> None:
    """Write a minimal spec.md at the canonical artifacts path."""
    spec_dir = root / "docs" / "specs" / slug
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(
        f"- **Status:** {status}\n", encoding="utf-8"
    )


def _write_intent(root: Path, slug: str, status: str = "Accepted", decomposed: str = "spec") -> None:
    """Write a minimal intent file."""
    intents_dir = root / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True, exist_ok=True)
    (intents_dir / f"{slug}.md").write_text(
        f"- **Slug:** {slug}\n"
        f"- **Status:** {status}\n"
        f"- **Decomposed:** 2026-09-01 {decomposed}\n",
        encoding="utf-8",
    )


def _write_brief(root: Path, slug: str, status: str = "Executing", parent: str | None = None) -> None:
    """Write a minimal brief file."""
    briefs_dir = root / "docs" / "product" / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    lines.append("")
    (briefs_dir / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")


# ── VI-1601: AC-0020 refusal table ───────────────────────────────────────────


def test_ac0020_broken_spec_reference_refuses_closure(tmp_path: Path) -> None:
    ci = _load()
    spec_dir = tmp_path / "docs" / "specs" / "done-spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text("# Spec\n\n- **Status:** Shipped\n", encoding="utf-8")
    snapshot = {
        "schema_version": 1,
        "complete": True,
        "relations": [
            {
                "basis": {"intent": "Decomposed", "spec": "Discovery"},
                "intent": "intent:alpha",
                "route": "spec",
                "spec": "spec:done-spec",
                "type": "direct-delivery",
            }
        ],
        "classifications": [
            {"classification": "direct-delivery", "intent": "intent:alpha", "route": "spec"}
        ],
        "provenance": [],
        "diagnostics": [
            {"code": "delivery-reference-unsafe", "field": "Discovery", "subject": "spec:broken-spec"}
        ],
        "artifacts": {"spec:done-spec": "docs/specs/done-spec/spec.md"},
    }

    verdict = ci.check_ancestor_closure(
        "alpha",
        "Accepted",
        "spec",
        tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _root: snapshot,
    )

    assert isinstance(verdict, ci.ClosureRefuse)
    assert "delivery-reference-unsafe" in verdict.reason


@pytest.mark.parametrize("code", [
    "delivery-reference-malformed",
    "delivery-target-missing",
])
def test_ac0020_unsafe_malformed_missing_spec_discovery_refuses(
    tmp_path: Path, code: str
) -> None:
    """Unsafe, malformed, or missing-target spec Discovery: refuses every spec-route feature.

    These diagnostic codes are indeterminate: the spec's real Discovery: target
    is unknown, so every feature that could be associated with this spec must be
    refused.
    """
    _write_spec(tmp_path, "done-spec")
    snapshot = _snap(
        relations=[_direct("alpha", "done-spec")],
        classifications=[{"classification": "direct-delivery", "intent": "intent:alpha", "route": "spec"}],
        diagnostics=[_diag(code, "spec:some-broken-spec", field="Discovery")],
    )

    verdict = ci.check_ancestor_closure(
        "alpha", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )

    assert isinstance(verdict, ci.ClosureRefuse), f"code={code}: expected ClosureRefuse"
    assert code in verdict.reason, "reason must name the diagnostic code"


def test_ac0020_ambiguous_spec_discovery_refuses_named_feature_intent(
    tmp_path: Path,
) -> None:
    """Ambiguous spec Discovery: refuses only the feature intents named as targets.

    When delivery-relation-ambiguous names specific feature intents, only those
    features are refused.  Other spec-route features that are not named are
    allowed to proceed.
    """
    _write_spec(tmp_path, "done-spec")
    _write_spec(tmp_path, "other-spec")
    snapshot = _snap(
        relations=[
            _direct("alpha", "done-spec"),
            _direct("beta", "other-spec"),
        ],
        classifications=[
            {"classification": "direct-delivery", "intent": "intent:alpha", "route": "spec"},
            {"classification": "direct-delivery", "intent": "intent:beta", "route": "spec"},
        ],
        diagnostics=[
            _diag(
                "delivery-relation-ambiguous",
                "spec:ambig-spec",
                field="Discovery",
                targets=["intent:alpha"],
            )
        ],
    )

    # alpha is named in targets → refused.
    verdict_alpha = ci.check_ancestor_closure(
        "alpha", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict_alpha, ci.ClosureRefuse), "alpha named in targets must be refused"
    assert "delivery-relation-ambiguous" in verdict_alpha.reason

    # beta is not named in targets → not refused for this diagnostic.
    verdict_beta = ci.check_ancestor_closure(
        "beta", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    # beta has other-spec (status "Shipped" = terminal) → ClosureEligible.
    assert isinstance(verdict_beta, ci.ClosureEligible), (
        "beta not named in targets must not be refused by this diagnostic"
    )


def test_ac0020_ambiguous_no_named_feature_targets_refuses_all(
    tmp_path: Path,
) -> None:
    """Ambiguous spec Discovery: with no named feature targets refuses every spec-route feature.

    When targets list non-feature identifiers (or is empty), the population is
    indeterminate, so every spec-route feature is refused.
    """
    _write_spec(tmp_path, "done-spec")
    snapshot = _snap(
        relations=[_direct("alpha", "done-spec")],
        classifications=[{"classification": "direct-delivery", "intent": "intent:alpha", "route": "spec"}],
        diagnostics=[
            _diag(
                "delivery-relation-ambiguous",
                "spec:ambig-spec",
                field="Discovery",
                targets=["spec:some-other-spec"],  # no feature intents named
            )
        ],
    )

    verdict = ci.check_ancestor_closure(
        "alpha", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert "delivery-relation-ambiguous" in verdict.reason


def test_ac0020_clean_spec_snapshot_keeps_eligible_verdict(tmp_path: Path) -> None:
    """A snapshot without spec-subject diagnostics keeps the ClosureEligible verdict.

    Control: AC-0020 must not refuse features when no broken-spec diagnostics
    are present.
    """
    _write_spec(tmp_path, "clean-spec", status="Shipped")
    snapshot = _snap(
        relations=[_direct("clean-feature", "clean-spec")],
        classifications=[{"classification": "direct-delivery", "intent": "intent:clean-feature", "route": "spec"}],
        diagnostics=[],
    )

    verdict = ci.check_ancestor_closure(
        "clean-feature", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"clean snapshot must not refuse; got {verdict!r}"
    )


def test_ac0020_brief_subject_diagnostic_refuses_brief_route_feature(
    tmp_path: Path,
) -> None:
    """Any delivery diagnostic on a brief subject refuses every brief-route feature.

    A brief with a diagnostic cannot be validated; the associated feature cannot
    be closed.
    """
    _write_brief(tmp_path, "my-brief", parent="brief-feature")
    _write_spec(tmp_path, "brief-spec")
    snapshot = _snap(
        relations=[_coord("brief-feature", "my-brief", "brief-spec")],
        diagnostics=[_diag("delivery-target-missing", "brief:my-brief")],
    )

    verdict = ci.check_ancestor_closure(
        "brief-feature", "Accepted", "brief", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert "delivery-target-missing" in verdict.reason


def test_ac0020_spec_brief_field_unsafe_refuses_brief_route_feature(
    tmp_path: Path,
) -> None:
    """An unsafe spec Brief: refuses the associated brief-route feature."""
    _write_brief(tmp_path, "target-brief", parent="brief-feature")
    _write_spec(tmp_path, "target-spec")
    snapshot = _snap(
        relations=[_coord("brief-feature", "target-brief", "target-spec")],
        diagnostics=[_diag("delivery-reference-unsafe", "spec:target-spec", field="Brief")],
    )

    verdict = ci.check_ancestor_closure(
        "brief-feature", "Accepted", "brief", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert "delivery-reference-unsafe" in verdict.reason


def test_ac0020_clean_brief_snapshot_keeps_eligible_verdict(tmp_path: Path) -> None:
    """A brief-route snapshot without diagnostics keeps the ClosureEligible verdict.

    Control: AC-0020 must not refuse brief-route features when no broken
    diagnostics are present.
    """
    _write_brief(tmp_path, "clean-brief", parent="clean-brief-feature", status="Withdrawn")
    _write_spec(tmp_path, "clean-brief-spec", status="Shipped")
    snapshot = _snap(
        relations=[_coord("clean-brief-feature", "clean-brief", "clean-brief-spec")],
        diagnostics=[],
    )

    verdict = ci.check_ancestor_closure(
        "clean-brief-feature", "Accepted", "brief", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict, ci.ClosureEligible), (
        f"clean brief snapshot must not refuse; got {verdict!r}"
    )


# ── VI-1602: Snapshot shape validation ───────────────────────────────────────


def test_vi1602_non_dict_relation_item_yields_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """A non-dict relation item in the snapshot yields delivery-resolver-unavailable."""
    bad_snap = {
        "schema_version": 1,
        "complete": True,
        "relations": ["not-a-dict"],  # invalid item
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    }

    verdict = ci.check_ancestor_closure(
        "some-feature", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: bad_snap,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1602_non_string_relation_field_yields_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """A relation item whose consumed field is not a string yields delivery-resolver-unavailable."""
    bad_snap = {
        "schema_version": 1,
        "complete": True,
        "relations": [{"type": 99, "route": "spec", "intent": "intent:x", "spec": "spec:y"}],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    }

    verdict = ci.check_ancestor_closure(
        "x", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: bad_snap,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1602_artifacts_escaping_path_yields_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """An artifacts path with a dotdot segment yields delivery-resolver-unavailable."""
    bad_snap = {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {"spec:my-spec": "../../etc/passwd"},
    }

    verdict = ci.check_ancestor_closure(
        "my-feature", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: bad_snap,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1602_artifacts_grammar_mismatch_yields_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """An artifacts path that does not match the canonical grammar yields delivery-resolver-unavailable."""
    bad_snap = {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {"spec:my-spec": "some/other/path.md"},
    }

    verdict = ci.check_ancestor_closure(
        "my-feature", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: bad_snap,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1602_non_dict_diagnostic_item_yields_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """A non-dict diagnostic item yields delivery-resolver-unavailable."""
    bad_snap = {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": ["not-a-dict"],
        "artifacts": {},
    }

    verdict = ci.check_ancestor_closure(
        "my-feature", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: bad_snap,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


# ── VI-1603: Descendant status from artifacts path ────────────────────────────


def test_vi1603_spec_status_read_from_artifacts_path(tmp_path: Path) -> None:
    """Descendant spec Status is read from the snapshot's artifacts path, not a slug-based path.

    The snapshot maps spec:my-spec to docs/specs/my-spec/spec.md.  The test
    writes a real file at that path with a known Status; close-work must read
    it from the artifacts path and return the correct closure verdict.
    """
    _write_spec(tmp_path, "my-spec", status="Implementing")
    snapshot = _snap(
        relations=[_direct("spec-feature", "my-spec")],
        classifications=[{"classification": "direct-delivery", "intent": "intent:spec-feature", "route": "spec"}],
    )

    verdict = ci.check_ancestor_closure(
        "spec-feature", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    # Implementing is live → ClosureNotEligible
    assert isinstance(verdict, ci.ClosureNotEligible), (
        f"live spec must block closure; got {verdict!r}"
    )
    live_slugs = {slug for slug, _ in verdict.live_descendants}
    assert "my-spec" in live_slugs


def test_vi1603_missing_artifacts_entry_yields_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """A spec named in a relation but absent from artifacts yields delivery-resolver-unavailable."""
    snapshot = {
        "schema_version": 1,
        "complete": True,
        "relations": [_direct("feat", "missing-spec")],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},  # spec:missing-spec not in artifacts
    }

    verdict = ci.check_ancestor_closure(
        "feat", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1603_brief_status_read_from_artifacts_path(tmp_path: Path) -> None:
    """Brief Status is read from the snapshot's artifacts path, not a slug-based path."""
    _write_brief(tmp_path, "my-brief", parent="brief-feature", status="Executing")
    _write_spec(tmp_path, "my-spec", status="Shipped")
    snapshot = _snap(
        relations=[_coord("brief-feature", "my-brief", "my-spec")],
    )

    verdict = ci.check_ancestor_closure(
        "brief-feature", "Accepted", "brief", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _r: snapshot,
    )
    # Executing brief is live → ClosureNotEligible
    assert isinstance(verdict, ci.ClosureNotEligible), (
        f"live brief must block closure; got {verdict!r}"
    )
    live_slugs = {slug for slug, _ in verdict.live_descendants}
    assert "my-brief" in live_slugs


def test_vi1603_provenance_uses_intent_field_not_path(tmp_path: Path) -> None:
    """Provenance ancestor resolution uses the ``intent`` field, not a path-form target.

    The resolver stores the canonical identifier in ``intent``; close-work must
    prefer that field to find the ancestor slug without reading a file path.
    """
    intents_dir = tmp_path / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True)
    (intents_dir / "cap.md").write_text(
        "- **Slug:** cap\n- **Status:** Accepted\n- **Decomposed:** 2026-09-01 closed-empty\n",
        encoding="utf-8",
    )
    prov_record = {
        "subject": "spec:my-spec",
        "field": "Discovery",
        "intent": "intent:cap",
        "target": "intent:cap",
    }
    snapshot = _snap(provenance=[prov_record])
    ancestors = ci.resolve_intent_ancestors(
        "my-spec", "spec", {"Slug": "my-spec"}, tmp_path,
        _snapshot_provider=lambda _r: snapshot,
    )
    assert len(ancestors) == 1
    assert ancestors[0][0] == "cap"


# ── Real-corpus artifact shapes ───────────────────────────────────────────────


def _corpus_shape_snapshot(intent_path: str, spec_id: str) -> dict[str, Any]:
    """A seven-key snapshot naming one intent file and one spec directory."""
    slug = spec_id.removeprefix("spec:")
    return {
        "schema_version": 1,
        "complete": True,
        "relations": [
            {
                "basis": {"intent": "Decomposed", "spec": "Discovery"},
                "intent": "intent:alpha",
                "route": "spec",
                "spec": spec_id,
                "type": "direct-delivery",
            }
        ],
        "classifications": [
            {"classification": "direct-delivery", "intent": "intent:alpha", "route": "spec"}
        ],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {
            "intent:alpha": intent_path,
            spec_id: f"docs/specs/{slug}/spec.md",
        },
    }


def test_ordinal_prefixed_intent_file_and_capitalised_spec_dir_are_accepted(
    tmp_path: Path,
) -> None:
    """An intent's file name need not equal its slug; a spec dir may carry capitals."""
    _write_spec(tmp_path, "spec-A-alpha-delivery")
    snapshot = _corpus_shape_snapshot(
        "docs/product/intents/FEAT-0012-alpha.md", "spec:spec-A-alpha-delivery"
    )

    verdict = ci.check_ancestor_closure(
        "alpha",
        "Accepted",
        "spec",
        tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _root: snapshot,
    )

    assert isinstance(verdict, ci.ClosureEligible)


@pytest.mark.parametrize(
    "intent_path",
    [
        "docs/product/intents/alpha\x1b[31m.md",
        "docs/product/intents/sub/alpha.md",
        "docs/product/briefs/alpha.md",
    ],
    ids=["control-character", "subdirectory", "wrong-root"],
)
def test_artifacts_path_outside_its_type_grammar_is_unavailable(
    tmp_path: Path, intent_path: str
) -> None:
    """An artifacts path that breaks its type's file grammar fails closed."""
    _write_spec(tmp_path, "alpha-delivery")
    snapshot = _corpus_shape_snapshot(intent_path, "spec:alpha-delivery")

    verdict = ci.check_ancestor_closure(
        "alpha",
        "Accepted",
        "spec",
        tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _root: snapshot,
    )

    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"
    assert "\x1b" not in verdict.reason
