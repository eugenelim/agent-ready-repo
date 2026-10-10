"""Delivery-snapshot consumer tests for the closure index (VI-1101, VI-1103).

T2 verification tests for AC-0012, AC-0014, AC-0017, AC-0018 of
``docs/specs/intent-delivery-traceability/``.

**VI-1101 — snapshot-based descendant membership (AC-0012, AC-0014):**
An injected canonical snapshot supplies delivery descendants for ``spec`` and
``brief`` termini. The old directory-inversion code paths (scanning specs for
Discovery: and briefs for Parent intent:) are unreachable when the snapshot
provider succeeds. Tests confirm that:

- A direct-delivery relation finds exactly the named spec and no others.
- A coordinated-delivery relation finds the named brief and its spec(s).
- A delivery diagnostic for a feature intent causes a ``ClosureRefuse`` with
  the stable code and nothing leaked to user-visible output.

**VI-1103 — fail-closed error handling (AC-0017, AC-0018):**
Every resolver invocation failure and invalid snapshot produces
``delivery-resolver-unavailable`` — the only stable user-visible code — with
no captured stderr, traceback, absolute path, or raw hostile content.
One test runs the real subprocess (VI-1103 subprocess arm).

Verification mode: TDD integration (implementation-discovered seam).
"""

from __future__ import annotations

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
_RESOLVER_SRC = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "adapter-root-bins" / "intent_delivery_relations.py"
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


ci = _load("closure_index", "closure_index__delivery_snap_t2")

_fx_spec = importlib.util.spec_from_file_location(
    "closure_graph_fixture__delivery_snap",
    Path(__file__).resolve().parent / "closure_graph_fixture.py",
)
assert _fx_spec and _fx_spec.loader
_fx = importlib.util.module_from_spec(_fx_spec)
sys.modules["closure_graph_fixture__delivery_snap"] = _fx
_fx_spec.loader.exec_module(_fx)

# ── Fake root paths ────────────────────────────────────────────────────────────

ROOT = Path("/fake/root")
INTENTS_DIR = ROOT / "docs" / "product" / "intents"
BRIEFS_DIR = ROOT / "docs" / "product" / "briefs"
SPECS_DIR = ROOT / "docs" / "specs"


# ── Preamble content builders ─────────────────────────────────────────────────


def _intent_text(slug: str, status: str = "Accepted", decomposed: str | None = None) -> str:
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if decomposed:
        lines.append(f"- **Decomposed:** 2026-09-01 {decomposed}")
    lines.append("")
    return "\n".join(lines)


def _brief_text(slug: str, status: str = "Executing") -> str:
    return f"- **Slug:** {slug}\n- **Status:** {status}\n"


def _spec_text(status: str = "Implementing") -> str:
    return f"- **Status:** {status}\n"


# ── Snapshot helpers ──────────────────────────────────────────────────────────


def _snapshot(
    *,
    relations: list[dict[str, Any]] | None = None,
    provenance: list[dict[str, Any]] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
    artifacts: dict[str, str] | None = None,
    classifications: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid delivery snapshot for test injection.

    When *artifacts* is omitted, the dict is auto-populated from the spec and
    brief identifiers present in *relations* using the canonical path grammar,
    so callers only need to supply explicit artifacts for edge-case tests.
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


def _diagnostic(subject_slug: str, code: str) -> dict[str, Any]:
    """Build a delivery diagnostic record."""
    return {"subject": f"intent:{subject_slug}", "code": code}


# ── In-memory filesystem ──────────────────────────────────────────────────────


class FakeFS:
    """Minimal in-memory filesystem for reader injection."""

    def __init__(self, files: dict[str, str]):
        self.files = files

    def reader(self, path: Path) -> str:
        key = str(path)
        if key not in self.files:
            raise FileNotFoundError(path)
        return self.files[key]


def _build(
    fs: FakeFS,
    ancestor_slug: str,
    ancestor_terminus: str,
    snapshot_provider=None,
) -> dict:
    """Invoke the module-private closure builder with injected seams."""
    return ci._build_descendant_closure(
        ancestor_slug,
        ancestor_terminus,
        ROOT,
        _reader=fs.reader,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
        _snapshot_provider=snapshot_provider,
    )


# ── VI-1101: snapshot-based descendant membership ─────────────────────────────


def test_vi1101_direct_delivery_spec_terminus_finds_named_spec() -> None:
    """A direct-delivery relation in the snapshot supplies the spec descendant.

    The snapshot names one spec for the feature intent. No other spec appears
    in the result even if it exists in FakeFS (it is excluded by not being named
    in the snapshot). This is the core AC-0012 property: close-work no longer
    inverts Discovery: itself.
    """
    feat_slug = "my-feature"
    spec_slug = "my-spec"
    other_slug = "other-spec"

    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="spec"),
        str(SPECS_DIR / spec_slug / "spec.md"): _spec_text(status="Implementing"),
        str(SPECS_DIR / other_slug / "spec.md"): _spec_text(status="Implementing"),
    }
    snap = _snapshot(relations=[_direct(feat_slug, spec_slug)])
    fs = FakeFS(files)

    result = _build(fs, feat_slug, "spec", snapshot_provider=lambda _r: snap)

    assert ("spec", spec_slug) in result, "named spec must appear in closure"
    assert ("spec", other_slug) not in result, "unnamed spec must not appear"
    assert result[("spec", spec_slug)].kind == "spec"


def test_vi1101_coordinated_delivery_brief_terminus_finds_brief_and_spec() -> None:
    """A coordinated-delivery relation supplies both the brief and its spec.

    The snapshot carries one coordinated-delivery record with a brief and a spec.
    Both appear in the closure; a spec not named in the snapshot does not.
    """
    feat_slug = "my-feature"
    brief_slug = "my-brief"
    spec_slug = "my-spec"
    unrelated_slug = "unrelated-spec"

    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="brief"),
        str(BRIEFS_DIR / f"{brief_slug}.md"): _brief_text(brief_slug, status="Executing"),
        str(SPECS_DIR / spec_slug / "spec.md"): _spec_text(status="Implementing"),
        str(SPECS_DIR / unrelated_slug / "spec.md"): _spec_text(status="Implementing"),
    }
    snap = _snapshot(relations=[_coord(feat_slug, brief_slug, spec_slug)])
    fs = FakeFS(files)

    result = _build(fs, feat_slug, "brief", snapshot_provider=lambda _r: snap)

    assert ("brief", brief_slug) in result, "brief named in snapshot must appear"
    assert ("spec", spec_slug) in result, "spec named in snapshot must appear"
    assert ("spec", unrelated_slug) not in result, "spec not in snapshot must not appear"
    assert result[("brief", brief_slug)].kind == "brief"
    assert result[("spec", spec_slug)].kind == "spec"


def test_vi1101_multiple_coordinated_delivery_finds_all_specs() -> None:
    """Multiple coordinated-delivery records (same brief, different specs) find all specs."""
    feat_slug = "multi-spec-feature"
    brief_slug = "multi-brief"
    spec_slugs = ["spec-alpha", "spec-beta", "spec-gamma"]

    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="brief"),
        str(BRIEFS_DIR / f"{brief_slug}.md"): _brief_text(brief_slug),
    }
    for s in spec_slugs:
        files[str(SPECS_DIR / s / "spec.md")] = _spec_text()

    snap = _snapshot(relations=[_coord(feat_slug, brief_slug, s) for s in spec_slugs])
    fs = FakeFS(files)

    result = _build(fs, feat_slug, "brief", snapshot_provider=lambda _r: snap)

    assert ("brief", brief_slug) in result
    for s in spec_slugs:
        assert ("spec", s) in result, f"spec '{s}' must appear via coordinated-delivery"
    # 1 brief + 3 specs = 4 descendants
    assert len(result) == 4, f"expected 4 descendants, got {sorted(result)}"


def test_vi1101_delivery_diagnostic_causes_closure_refuse() -> None:
    """A delivery diagnostic for the feature intent causes ClosureRefuse.

    When the snapshot names a delivery diagnostic (e.g. delivery-target-missing)
    for the feature intent, ``check_ancestor_closure`` must return a
    ``ClosureRefuse`` with the stable diagnostic code.  No leaked content
    (stderr, traceback, path) may appear in the reason string.
    """
    feat_slug = "missing-spec-feature"
    code = "delivery-target-missing"

    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="spec"),
    }
    snap = _snapshot(diagnostics=[_diagnostic(feat_slug, code)])
    fs = FakeFS(files)

    verdict = ci.check_ancestor_closure(
        feat_slug,
        "Accepted",
        "spec",
        ROOT,
        _freshness_checker=lambda: True,
        _reader=fs.reader,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
        _snapshot_provider=lambda _r: snap,
    )

    assert isinstance(verdict, ci.ClosureRefuse), (
        f"Expected ClosureRefuse, got {verdict!r}"
    )
    assert f"delivery-diagnostic: {code}" in verdict.reason, (
        f"Reason must contain 'delivery-diagnostic: {code}', got: {verdict.reason!r}"
    )
    # Security: no leakage of hostile content.
    assert "traceback" not in verdict.reason.lower()
    assert "/Users" not in verdict.reason
    assert "/home" not in verdict.reason


@pytest.mark.parametrize("code", [
    "delivery-target-missing",
    "delivery-projection-mismatch",
    "delivery-relation-ambiguous",
    "delivery-reference-malformed",
])
def test_vi1101_all_diagnostic_codes_cause_closure_refuse(code: str) -> None:
    """Every admitted delivery diagnostic code causes ClosureRefuse (AC-0018)."""
    feat_slug = "diag-feature"

    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="spec"),
    }
    snap = _snapshot(diagnostics=[_diagnostic(feat_slug, code)])
    fs = FakeFS(files)

    verdict = ci.check_ancestor_closure(
        feat_slug,
        "Accepted",
        "spec",
        ROOT,
        _freshness_checker=lambda: True,
        _reader=fs.reader,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
        _snapshot_provider=lambda _r: snap,
    )

    assert isinstance(verdict, ci.ClosureRefuse)
    assert f"delivery-diagnostic: {code}" in verdict.reason


# ── VI-1103: fail-closed error handling ──────────────────────────────────────


def test_vi1103_snapshot_provider_exception_yields_delivery_resolver_unavailable() -> None:
    """A snapshot provider that raises causes ClosureRefuse with delivery-resolver-unavailable."""
    feat_slug = "err-feature"
    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="spec"),
    }
    fs = FakeFS(files)

    def _failing_provider(_r):
        raise RuntimeError("simulated subprocess failure\nwith multiple lines")

    verdict = ci.check_ancestor_closure(
        feat_slug,
        "Accepted",
        "spec",
        ROOT,
        _freshness_checker=lambda: True,
        _reader=fs.reader,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
        _snapshot_provider=_failing_provider,
    )

    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable", (
        f"Expected stable code, got: {verdict.reason!r}"
    )
    # No hostile content from the exception.
    assert "simulated" not in verdict.reason
    assert "subprocess" not in verdict.reason
    assert "multiple" not in verdict.reason


def test_vi1103_resolver_unavailable_never_falls_back_to_old_scanner() -> None:
    """When the snapshot provider fails, no spec is found via directory inversion.

    AC-0014: only one production implementation of delivery inversion may exist.
    This test confirms close-work does NOT fall back to Discovery:-scanning when
    the snapshot provider raises. The spec exists on the FakeFS and has a
    Discovery: pointing to the ancestor, so an old-style scanner would find it.
    """
    feat_slug = "fallback-test-feature"
    spec_slug = "fallback-test-spec"

    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="spec"),
        str(SPECS_DIR / spec_slug / "spec.md"): (
            f"- **Status:** Implementing\n"
            f"- **Discovery:** docs/product/intents/{feat_slug}.md\n"
        ),
    }
    fs = FakeFS(files)

    def _failing_provider(_r):
        raise ValueError("resolver not installed")

    verdict = ci.check_ancestor_closure(
        feat_slug,
        "Accepted",
        "spec",
        ROOT,
        _freshness_checker=lambda: True,
        _reader=fs.reader,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
        _snapshot_provider=_failing_provider,
    )

    # Must refuse, not return ClosureNotEligible with the spec as a live descendant.
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"Expected ClosureRefuse (no fallback), got {verdict!r}"
    )
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1103_parse_validates_incomplete_snapshot() -> None:
    """_parse_and_validate_snapshot raises ValueError for complete=False."""
    import json

    bad_text = json.dumps({
        "schema_version": 1,
        "complete": False,  # incomplete
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    })
    with pytest.raises(ValueError, match="incomplete snapshot"):
        ci._parse_and_validate_snapshot(bad_text)


def test_vi1103_parse_validates_wrong_schema_version() -> None:
    """_parse_and_validate_snapshot raises ValueError for schema_version != 1."""
    import json

    bad_text = json.dumps({
        "schema_version": 99,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    })
    with pytest.raises(ValueError, match="unsupported schema_version"):
        ci._parse_and_validate_snapshot(bad_text)


def test_vi1103_parse_validates_missing_key() -> None:
    """_parse_and_validate_snapshot raises ValueError when a required key is absent."""
    import json

    bad_text = json.dumps({
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        # 'diagnostics' intentionally omitted
    })
    with pytest.raises(ValueError, match="wrong keys"):
        ci._parse_and_validate_snapshot(bad_text)


def test_vi1103_provider_raising_value_error_yields_delivery_resolver_unavailable() -> None:
    """A snapshot provider raising ValueError causes ClosureRefuse with the stable code.

    This exercises the exact path that _run_resolver takes when validation fails:
    _parse_and_validate_snapshot raises ValueError → propagates to _get_snapshot
    → _ClosureDeliveryRefusal → ClosureRefuse.
    """
    feat_slug = "invalid-snap-feature"
    files = {
        str(INTENTS_DIR / f"{feat_slug}.md"): _intent_text(feat_slug, decomposed="spec"),
    }
    fs = FakeFS(files)

    def _invalid_provider(_r):
        raise ValueError("delivery-resolver-unavailable: wrong keys")

    verdict = ci.check_ancestor_closure(
        feat_slug,
        "Accepted",
        "spec",
        ROOT,
        _freshness_checker=lambda: True,
        _reader=fs.reader,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
        _snapshot_provider=_invalid_provider,
    )

    assert isinstance(verdict, ci.ClosureRefuse)
    assert verdict.reason == "delivery-resolver-unavailable"


def test_vi1103_parse_and_validate_snapshot_rejects_nan() -> None:
    """_parse_and_validate_snapshot rejects a JSON text containing NaN.

    NaN/Infinity can appear in attacker-supplied resolver output. The validator
    re-encodes with allow_nan=False to catch these before they reach the walk.
    """
    import json

    # Valid JSON with NaN (Python's json module can decode it from 'NaN')
    # The validator must reject this before the walk sees it.
    bad_text = json.dumps({
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    }).replace('"relations": []', '"relations": [{"value": NaN}]')
    # NaN in JSON is non-standard; json.loads on CPython may accept it.
    # Confirm the validator raises ValueError.
    with pytest.raises(ValueError):
        ci._parse_and_validate_snapshot(bad_text)


# ── VI-1103: real subprocess path ────────────────────────────────────────────


def test_vi1103_real_subprocess_produces_valid_snapshot(tmp_path: Path) -> None:
    """Running the real resolver subprocess returns a valid delivery snapshot.

    This is the one test that exercises the actual subprocess path from
    ``_run_resolver``. After T9 the resolver copy ships beside the consumer
    script; ``_run_resolver`` finds it via ``_RESOLVER_PATH`` without any
    installation step.

    The close-work walk then uses the same snapshot via the seam to find the
    spec descendant — confirming the real end-to-end path from resolver
    subprocess to closure membership.

    Satisfies the plan requirement: 'at least one test running through the real
    subprocess path.'
    """
    # ── Write a minimal fixture: one feature intent (spec terminus), one spec ─
    intents_dir = tmp_path / "docs" / "product" / "intents"
    specs_dir = tmp_path / "docs" / "specs"
    briefs_dir = tmp_path / "docs" / "product" / "briefs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)
    briefs_dir.mkdir(parents=True)

    feat_slug = "subprocess-feature"
    spec_slug = "subprocess-spec"

    # The resolver requires Level: feature to identify a feature intent.
    (intents_dir / f"{feat_slug}.md").write_text(
        f"- **Slug:** {feat_slug}\n"
        f"- **Status:** Accepted\n"
        f"- **Level:** feature\n"
        f"- **Decomposed:** 2026-09-01 spec\n",
        encoding="utf-8",
    )
    (specs_dir / spec_slug).mkdir()
    (specs_dir / spec_slug / "spec.md").write_text(
        f"- **Status:** Implementing\n"
        f"- **Discovery:** docs/product/intents/{feat_slug}.md\n",
        encoding="utf-8",
    )

    # ── Call _run_resolver directly to confirm it returns a valid snapshot ────
    snap = ci._run_resolver(tmp_path)

    # Validate snapshot shape.
    assert snap["schema_version"] == 1
    assert snap["complete"] is True
    for key in ("relations", "classifications", "provenance", "diagnostics"):
        assert isinstance(snap[key], list), f"'{key}' must be a list"

    # The fixture should yield exactly one direct-delivery relation.
    direct = [
        r for r in snap["relations"]
        if r.get("type") == "direct-delivery"
        and r.get("intent") == f"intent:{feat_slug}"
        and r.get("spec") == f"spec:{spec_slug}"
    ]
    assert len(direct) == 1, (
        f"Expected one direct-delivery relation, got: {snap['relations']}"
    )

    # ── Use the snapshot via the seam to confirm close-work reads the same data
    result = ci._build_descendant_closure(
        feat_slug,
        "spec",
        tmp_path,
        _snapshot_provider=lambda _r: snap,
    )

    assert ("spec", spec_slug) in result, "spec must appear in closure via real subprocess snapshot"
    assert result[("spec", spec_slug)].kind == "spec"


# ---------------------------------------------------------------------------
# VI-2404 negative validator tests for close-work closure_index
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_record,label",
    [
        (
            {"subject": "spec:foo", "field": "Parent intent", "intent": "intent:alpha"},
            "subject-not-brief-typed",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent"},
            "missing-intent",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent", "intent": "brief:alpha"},
            "non-intent-typed-intent",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent", "intent": "intent:"},
            "prefix-only-intent",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent", "intent": "intent:A/../b"},
            "path-like-intent",
        ),
    ],
    ids=[
        "subject-not-brief-typed",
        "missing-intent",
        "non-intent-typed-intent",
        "prefix-only-intent",
        "path-like-intent",
    ],
)
def test_vi2404_closure_rejects_malformed_parent_intent_provenance(
    bad_record: dict,
    label: str,
) -> None:
    """closure_index _validate_snapshot_dict raises delivery-resolver-unavailable
    for a malformed Parent intent provenance record; each case goes red when its
    specific check is removed from the validator."""
    snapshot = {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [bad_record],
        "diagnostics": [],
        "artifacts": {},
    }
    with pytest.raises(ValueError, match="delivery-resolver-unavailable"):
        ci._validate_snapshot_dict(snapshot)
