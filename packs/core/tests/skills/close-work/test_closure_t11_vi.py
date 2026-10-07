"""VI-2102, VI-2103, VI-2104 coverage for close-work AC-0020 refusal sets (T11).

All AC-0020 rows are exercised with the broken artifact placed on an UNRELATED
spec or brief (not the feature's own delivery artifact).  Each VI-2104 test
drives ``_run_resolver`` through a stub script via the ``_resolver_path`` seam
and asserts that the returned reason is exactly ``delivery-resolver-unavailable``
with no stub output present.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

APM = Path(__file__).resolve().parents[3] / ".apm"


def _load_module(name: str, path: Path) -> Any:
    """Load a Python file as a module under a unique ``sys.modules`` key."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_resolver = _load_module(
    "_core_intent_delivery_relations_t11vi",
    APM / "adapter-root-bins" / "intent_delivery_relations.py",
)
_ci = _load_module(
    "_core_close_work_closure_index_t11vi",
    APM / "skills" / "close-work" / "scripts" / "closure_index.py",
)


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _write(path: Path, text: str) -> None:
    """Write text to path, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_intent(
    root: Path,
    slug: str,
    *,
    status: str = "Accepted",
    decomposed: str = "spec",
) -> None:
    _write(
        root / "docs" / "product" / "intents" / f"{slug}.md",
        f"# {slug}\n\n"
        f"- **Slug:** `{slug}`\n"
        f"- **Level:** feature\n"
        f"- **Status:** {status}\n"
        f"- **Decomposed:** 2026-10-06 {decomposed}\n",
    )


def _write_brief(
    root: Path,
    slug: str,
    *,
    parent: str,
    status: str = "Executing",
) -> None:
    _write(
        root / "docs" / "product" / "briefs" / f"{slug}.md",
        f"# {slug}\n\n"
        f"- **Slug:** `{slug}`\n"
        f"- **Status:** {status}\n"
        f"- **Parent intent:** intent:{parent}\n",
    )


def _write_spec(
    root: Path,
    slug: str,
    *,
    status: str = "Shipped",
    discovery: str | None = None,
    brief: str | None = None,
) -> None:
    lines = [f"# Spec: {slug}", "", f"- **Status:** {status}"]
    if discovery is not None:
        lines.append(f"- **Discovery:** `{discovery}`")
    if brief is not None:
        lines.append(f"- **Brief:** `{brief}`")
    _write(root / "docs" / "specs" / slug / "spec.md", "\n".join(lines) + "\n")


def _check(
    slug: str,
    terminus: str,
    root: Path,
    *,
    status: str = "Accepted",
) -> Any:
    """Call ``check_ancestor_closure`` with a live snapshot provider."""
    return _ci.check_ancestor_closure(
        slug,
        status,
        terminus,
        root,
        _freshness_checker=lambda: True,
        _snapshot_provider=_resolver.resolve_repository,
    )


# ── VI-2102: real-resolver snapshots, broken artifact on an unrelated artifact ─


class TestVI2102AmbiguousDiscoverySpecRoute:
    """Ambiguous spec Discovery: names targets; refuses each named spec-route feature."""

    def test_named_feature_is_refused(self, tmp_path: Path) -> None:
        """A spec-route feature named in ambiguous Discovery: targets is refused."""
        _write_intent(tmp_path, "gamma", decomposed="spec")
        _write_intent(tmp_path, "other", decomposed="spec")
        _write_spec(tmp_path, "gamma-delivery", discovery="intent:gamma")
        _write_spec(tmp_path, "other-delivery", discovery="intent:other")
        # Unrelated broken spec: two Discovery: values → ambiguous
        _write(
            tmp_path / "docs" / "specs" / "broken" / "spec.md",
            "# Broken\n\n"
            "- **Status:** Draft\n"
            "- **Discovery:** `intent:gamma`\n"
            "- **Discovery:** `intent:other`\n",
        )

        verdict = _check("gamma", "spec", tmp_path)

        assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
        assert "delivery-relation-ambiguous" in verdict.reason


class TestVI2102AmbiguousDiscoveryBriefRoute:
    """Ambiguous spec Discovery: refuses a named brief-route feature."""

    def test_named_brief_route_feature_is_refused(self, tmp_path: Path) -> None:
        """Brief-route feature named in ambiguous Discovery: targets is refused."""
        _write_intent(tmp_path, "gamma", decomposed="brief")
        _write_intent(tmp_path, "other", decomposed="spec")
        _write_brief(tmp_path, "gamma-brief", parent="gamma")
        _write_spec(tmp_path, "gamma-spec", brief="brief:gamma-brief")
        _write_spec(tmp_path, "other-delivery", discovery="intent:other")
        # Unrelated broken spec: ambiguous Discovery: names gamma (brief-route)
        _write(
            tmp_path / "docs" / "specs" / "broken" / "spec.md",
            "# Broken\n\n"
            "- **Status:** Draft\n"
            "- **Discovery:** `intent:gamma`\n"
            "- **Discovery:** `intent:other`\n",
        )

        verdict = _check("gamma", "brief", tmp_path)

        assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
        assert "delivery-relation-ambiguous" in verdict.reason


class TestVI2102AmbiguousBriefField:
    """Ambiguous spec Brief: refuses features named by the listed briefs' Parent intent:."""

    def test_named_features_refused_via_coordinated_delivery(
        self, tmp_path: Path
    ) -> None:
        """Ambiguous Brief: refuses gamma and other, each named by their brief."""
        _write_intent(tmp_path, "gamma", decomposed="brief")
        _write_intent(tmp_path, "other", decomposed="brief")
        _write_brief(tmp_path, "gamma-brief", parent="gamma")
        _write_brief(tmp_path, "other-brief", parent="other")
        _write_spec(tmp_path, "gamma-spec", brief="brief:gamma-brief")
        _write_spec(tmp_path, "other-spec", brief="brief:other-brief")
        # Unrelated broken spec: two Brief: values → ambiguous
        _write(
            tmp_path / "docs" / "specs" / "broken" / "spec.md",
            "# Broken\n\n"
            "- **Status:** Draft\n"
            "- **Brief:** `brief:gamma-brief`\n"
            "- **Brief:** `brief:other-brief`\n",
        )

        for slug in ("gamma", "other"):
            verdict = _check(slug, "brief", tmp_path)
            assert isinstance(verdict, _ci.ClosureRefuse), f"{slug}: {verdict!r}"
            assert "delivery-relation-ambiguous" in verdict.reason

    def test_no_resolving_target_refuses_every_brief_route_feature(
        self, tmp_path: Path
    ) -> None:
        """Ambiguous Brief: with non-existent targets refuses every brief-route feature."""
        _write_intent(tmp_path, "gamma", decomposed="brief")
        _write_brief(tmp_path, "gamma-brief", parent="gamma")
        _write_spec(tmp_path, "gamma-spec", brief="brief:gamma-brief")
        # Unrelated broken spec: two Brief: values for non-existent briefs
        _write(
            tmp_path / "docs" / "specs" / "broken" / "spec.md",
            "# Broken\n\n"
            "- **Status:** Draft\n"
            "- **Brief:** `brief:nonexistent1`\n"
            "- **Brief:** `brief:nonexistent2`\n",
        )

        verdict = _check("gamma", "brief", tmp_path)

        assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
        assert "delivery-relation-ambiguous" in verdict.reason


@pytest.mark.parametrize(
    "code,brief_value",
    [
        ("delivery-reference-unsafe", "/absolute/path.md"),
        ("delivery-reference-malformed", "not-a-valid-form"),
    ],
)
def test_vi2102_broken_spec_brief_field_refuses_brief_route_feature(
    tmp_path: Path, code: str, brief_value: str
) -> None:
    """Unsafe or malformed spec Brief: on an unrelated spec refuses brief-route feature."""
    _write_intent(tmp_path, "gamma", decomposed="brief")
    _write_brief(tmp_path, "gamma-brief", parent="gamma")
    _write_spec(tmp_path, "gamma-spec", brief="brief:gamma-brief")
    # Unrelated broken spec with unsafe/malformed Brief: value
    _write(
        tmp_path / "docs" / "specs" / "broken" / "spec.md",
        f"# Broken\n\n- **Status:** Draft\n- **Brief:** `{brief_value}`\n",
    )

    verdict = _check("gamma", "brief", tmp_path)

    assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
    assert code in verdict.reason


def test_vi2102_missing_target_spec_brief_refuses_brief_route_feature(
    tmp_path: Path,
) -> None:
    """Missing-target spec Brief: on an unrelated spec refuses brief-route feature."""
    _write_intent(tmp_path, "gamma", decomposed="brief")
    _write_brief(tmp_path, "gamma-brief", parent="gamma")
    _write_spec(tmp_path, "gamma-spec", brief="brief:gamma-brief")
    # Unrelated broken spec: Brief: points to a non-existent brief (single value)
    _write(
        tmp_path / "docs" / "specs" / "broken" / "spec.md",
        "# Broken\n\n- **Status:** Draft\n- **Brief:** `brief:nonexistent`\n",
    )

    verdict = _check("gamma", "brief", tmp_path)

    assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
    assert "delivery-target-missing" in verdict.reason


def test_vi2102_brief_subject_diagnostic_on_unrelated_brief_refuses_feature(
    tmp_path: Path,
) -> None:
    """A diagnostic on an unrelated brief refuses every brief-route feature."""
    _write_intent(tmp_path, "gamma", decomposed="brief")
    _write_brief(tmp_path, "gamma-brief", parent="gamma")
    _write_spec(tmp_path, "gamma-spec", brief="brief:gamma-brief")
    # Unrelated broken brief with an unsafe Parent intent: (produces brief-subject diagnostic)
    _write(
        tmp_path / "docs" / "product" / "briefs" / "broken-brief.md",
        "# Broken brief\n\n"
        "- **Slug:** `broken-brief`\n"
        "- **Status:** Draft\n"
        "- **Parent intent:** `/absolute/escape`\n",
    )

    verdict = _check("gamma", "brief", tmp_path)

    assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
    assert "delivery-reference-unsafe" in verdict.reason


def test_vi2102_cross_route_control_spec_keeps_eligible(tmp_path: Path) -> None:
    """A clean spec-route snapshot keeps the feature ClosureEligible."""
    _write_intent(tmp_path, "gamma", decomposed="spec")
    _write_spec(tmp_path, "gamma-delivery", status="Shipped", discovery="intent:gamma")

    verdict = _check("gamma", "spec", tmp_path)

    assert isinstance(verdict, _ci.ClosureEligible), repr(verdict)


def test_vi2102_cross_route_control_brief_keeps_eligible(tmp_path: Path) -> None:
    """A clean brief-route snapshot keeps the feature ClosureEligible."""
    _write_intent(tmp_path, "gamma", decomposed="brief")
    _write_brief(tmp_path, "gamma-brief", parent="gamma", status="Withdrawn")
    _write_spec(tmp_path, "gamma-spec", status="Shipped", brief="brief:gamma-brief")

    verdict = _check("gamma", "brief", tmp_path)

    assert isinstance(verdict, _ci.ClosureEligible), repr(verdict)


# ── VI-2103: path form and intent: form of Discovery: give the same ancestor ──


def test_vi2103_path_form_and_intent_form_give_same_ancestor(
    tmp_path: Path,
) -> None:
    """Both Discovery: reference forms resolve to the same ancestor via provenance.

    A spec whose Discovery: names a direct-light feature goes to provenance (not
    relations) because the feature has a non-delivery route.  The resolver stores
    the resolved intent identifier in the ``intent`` field of the provenance
    record regardless of whether the raw value was ``intent:<slug>`` or
    ``docs/product/intents/<slug>.md``.  ``resolve_intent_ancestors`` follows
    only the ``intent`` field, so both forms give the same ancestor chain.
    """
    # A feature with a direct-light route: Discovery: on its specs goes to provenance.
    _write(
        tmp_path / "docs" / "product" / "intents" / "dl-feature.md",
        "# DL Feature\n\n"
        "- **Slug:** `dl-feature`\n"
        "- **Level:** feature\n"
        "- **Status:** Accepted\n"
        "- **Decomposed:** 2026-10-06 direct-light\n",
    )
    # Two specs with the same ancestor expressed in different forms.
    _write_spec(tmp_path, "child-intent-form", status="Draft",
                discovery="intent:dl-feature")
    _write_spec(tmp_path, "child-path-form", status="Draft",
                discovery="docs/product/intents/dl-feature.md")

    ancestors_intent = _ci.resolve_intent_ancestors(
        "child-intent-form", "spec", {}, tmp_path,
        _snapshot_provider=_resolver.resolve_repository,
    )
    ancestors_path = _ci.resolve_intent_ancestors(
        "child-path-form", "spec", {}, tmp_path,
        _snapshot_provider=_resolver.resolve_repository,
    )

    assert any(s == "dl-feature" for s, _, _ in ancestors_intent), (
        f"intent: form must resolve dl-feature; got {ancestors_intent!r}"
    )
    assert any(s == "dl-feature" for s, _, _ in ancestors_path), (
        f"path form must resolve dl-feature; got {ancestors_path!r}"
    )
    assert ancestors_intent == ancestors_path, (
        f"both forms must give identical chains; "
        f"intent={ancestors_intent!r} path={ancestors_path!r}"
    )


# ── VI-2104: _run_resolver failure paths through stub scripts ─────────────────


def _make_provider(resolver_path: Path):
    """Return a ``_snapshot_provider`` that calls ``_run_resolver`` with a stub path."""
    def _provider(root: Path) -> dict[str, Any]:
        return _ci._run_resolver(root, _resolver_path=resolver_path)
    return _provider


def _assert_unavailable(verdict: Any) -> None:
    """Assert the verdict is a ClosureRefuse with exactly delivery-resolver-unavailable."""
    assert isinstance(verdict, _ci.ClosureRefuse), repr(verdict)
    assert verdict.reason == "delivery-resolver-unavailable", (
        f"unexpected reason: {verdict.reason!r}"
    )


def test_vi2104_linked_resolver_yields_unavailable(tmp_path: Path) -> None:
    """A symlinked resolver path yields delivery-resolver-unavailable."""
    symlink = tmp_path / "linked_resolver.py"
    symlink.symlink_to(_ci._RESOLVER_PATH)

    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(symlink),
    )
    _assert_unavailable(verdict)


def test_vi2104_timeout_yields_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sleeping resolver that exceeds the lowered timeout yields delivery-resolver-unavailable.

    The stub writes a valid complete snapshot after sleeping 5 s, so removing
    the timeout guard would let the subprocess finish and the snapshot succeed.
    The test lowers _RESOLVER_TIMEOUT to 1 s; the elapsed wall-clock must be
    less than the stub's sleep to prove the timeout fired rather than the stub
    completing normally.
    """
    stub = tmp_path / "sleeping_resolver.py"
    stub.write_text(
        "import time, sys, json\n"
        "time.sleep(5)\n"
        "snap = {\n"
        "    'schema_version': 1, 'complete': True,\n"
        "    'relations': [], 'classifications': [], 'provenance': [],\n"
        "    'diagnostics': [], 'artifacts': {},\n"
        "}\n"
        "sys.stdout.write(json.dumps(snap) + '\\n')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_ci, "_RESOLVER_TIMEOUT", 1)

    import time as _time
    _t0 = _time.monotonic()
    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(stub),
    )
    _elapsed = _time.monotonic() - _t0

    _assert_unavailable(verdict)
    assert _elapsed < 4, (
        f"timeout must fire before stub finishes (stub sleeps 5 s), "
        f"elapsed={_elapsed:.2f}s"
    )


def test_vi2104_oversized_stdout_yields_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resolver writing stdout beyond the size limit yields delivery-resolver-unavailable.

    The stub writes a structurally valid complete snapshot (~122 bytes).  The
    test lowers _MAX_SNAPSHOT_BYTES to 50 so the valid payload exceeds the cap.
    Without the size guard the snapshot would parse and validate successfully.
    """
    monkeypatch.setattr(_ci, "_MAX_SNAPSHOT_BYTES", 50)
    stub = tmp_path / "oversized_resolver.py"
    stub.write_text(
        "import sys, json\n"
        "snap = {\n"
        "    'schema_version': 1, 'complete': True,\n"
        "    'relations': [], 'classifications': [], 'provenance': [],\n"
        "    'diagnostics': [], 'artifacts': {},\n"
        "}\n"
        "# Serialised snapshot is ~122 bytes — over the 50-byte test limit.\n"
        "sys.stdout.write(json.dumps(snap) + '\\n')\n",
        encoding="utf-8",
    )

    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(stub),
    )
    _assert_unavailable(verdict)


def test_vi2104_non_utf8_stdout_yields_unavailable(tmp_path: Path) -> None:
    """A resolver writing non-UTF-8 bytes to stdout yields delivery-resolver-unavailable.

    The stub writes a structurally valid complete snapshot where a provenance
    record's optional ``target`` field holds a raw ``\\xff`` byte.  Decoded with
    ``errors='replace'`` the byte becomes U+FFFD, which is a valid Unicode
    string that passes ``_validate_snapshot_dict``'s ``isinstance(target, str)``
    check.  The strict ``errors='strict'`` UTF-8 guard turns it into
    ``delivery-resolver-unavailable`` instead.
    """
    stub = tmp_path / "bad_utf8_resolver.py"
    stub.write_text(
        "import sys, json\n"
        "snap = {\n"
        "    'schema_version': 1, 'complete': True,\n"
        "    'relations': [], 'classifications': [],\n"
        "    'provenance': [{\n"
        "        'subject': 'spec:anchor', 'field': 'Contract',\n"
        "        'target': 'PLACEHOLDER',\n"
        "    }],\n"
        "    'diagnostics': [], 'artifacts': {},\n"
        "}\n"
        "data = json.dumps(snap).encode('utf-8')\n"
        "# Replace placeholder with a raw non-UTF-8 byte.  With errors='replace'\n"
        "# this becomes U+FFFD (a valid string); with errors='strict' it raises.\n"
        "data = data.replace(b'PLACEHOLDER', b'\\xff')\n"
        "sys.stdout.buffer.write(data)\n",
        encoding="utf-8",
    )

    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(stub),
    )
    _assert_unavailable(verdict)


def test_vi2104_hostile_stderr_not_in_reason(tmp_path: Path) -> None:
    """Hostile stderr content never appears in the refusal reason."""
    hostile = "HOSTILE_INJECTED_CONTENT_12345"
    stub = tmp_path / "hostile_stderr_resolver.py"
    stub.write_text(
        f"import sys\n"
        f"sys.stderr.write('{hostile}')\n"
        f"sys.exit(1)\n",
        encoding="utf-8",
    )

    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(stub),
    )
    _assert_unavailable(verdict)
    assert hostile not in verdict.reason


# ── Three AC-0020 real-resolver tests (one per path, each with a control) ─────


def test_ac0020_brief_route_brief_parent_intent_maps_to_feature(
    tmp_path: Path,
) -> None:
    """AC-0020 path (a): ambiguous spec Brief: refuses the feature named by the
    brief's Parent intent:, not every brief-route feature.

    The feature under test (intent-a) has a brief (brief-a) whose Parent intent:
    points to it.  An unrelated spec has an ambiguous Brief: that names brief-a
    and a non-existent brief.  Because there is no coordinated-delivery relation
    for brief-a (the ambiguous spec creates none), the fix must derive the
    feature mapping by reading brief-a's Parent intent: from the snapshot's
    artifacts map.

    The control feature (intent-d) has its own clean brief delivery and must
    not be refused.
    """
    # Feature A: brief-route delivery via brief-a and spec-a.
    _write_intent(tmp_path, "intent-a", decomposed="brief")
    _write_brief(tmp_path, "brief-a", parent="intent-a")
    _write_spec(tmp_path, "spec-a", brief="brief:brief-a")

    # Control feature D: brief-route delivery, clean setup.  Use Shipped so the
    # brief is terminal and the assertion can be ClosureEligible.
    _write_intent(tmp_path, "intent-d", decomposed="brief")
    _write_brief(tmp_path, "brief-d", parent="intent-d", status="Shipped")
    _write_spec(tmp_path, "spec-d", brief="brief:brief-d")

    # Unrelated broken spec: ambiguous Brief: naming brief-a and a missing brief.
    # No coordinated-delivery relation is produced for this spec.
    _write(
        tmp_path / "docs" / "specs" / "broken" / "spec.md",
        "# Broken\n\n"
        "- **Status:** Draft\n"
        "- **Brief:** `brief:brief-a`\n"
        "- **Brief:** `brief:nonexistent`\n",
    )

    # Feature A must be refused because brief-a's Parent intent: maps to it.
    verdict_a = _check("intent-a", "brief", tmp_path)
    assert isinstance(verdict_a, _ci.ClosureRefuse), repr(verdict_a)
    assert "delivery-relation-ambiguous" in verdict_a.reason

    # Control: feature D must not be refused (it is unrelated).
    verdict_d = _check("intent-d", "brief", tmp_path)
    assert isinstance(verdict_d, _ci.ClosureEligible), repr(verdict_d)


def test_ac0020_spec_route_brief_field_refuses_via_parent_intent(
    tmp_path: Path,
) -> None:
    """AC-0020 path (b): ambiguous spec Brief: also refuses a spec-route feature
    named by one of the listed briefs' Parent intent:.

    The spec carries both a Discovery: (linking the spec-route feature) and an
    ambiguous Brief: (two brief values).  One of those briefs has a Parent
    intent: pointing to the spec-route feature.  The spec branch must read the
    brief's Parent intent: and refuse the feature.

    The control feature (intent-d) has a clean spec delivery and must not be
    refused.
    """
    # Feature A: spec-route delivery via spec-a.
    _write_intent(tmp_path, "intent-a", decomposed="spec")
    # brief-a's Parent intent: links it to feature A.
    _write_brief(tmp_path, "brief-a", parent="intent-a")
    # spec-a has a Discovery: (linking A) and two Brief: values (ambiguous).
    _write(
        tmp_path / "docs" / "specs" / "spec-a" / "spec.md",
        "# Spec A\n\n"
        "- **Status:** Shipped\n"
        "- **Discovery:** `intent:intent-a`\n"
        "- **Brief:** `brief:brief-a`\n"
        "- **Brief:** `brief:brief-x`\n",
    )

    # Control feature D: spec-route, clean.
    _write_intent(tmp_path, "intent-d", decomposed="spec")
    _write_spec(tmp_path, "spec-d", discovery="intent:intent-d")

    # Feature A must be refused because spec-a's Brief: is ambiguous and
    # brief-a's Parent intent: maps to intent-a.
    verdict_a = _check("intent-a", "spec", tmp_path)
    assert isinstance(verdict_a, _ci.ClosureRefuse), repr(verdict_a)
    assert "delivery-relation-ambiguous" in verdict_a.reason

    # Control: feature D must not be refused.
    verdict_d = _check("intent-d", "spec", tmp_path)
    assert isinstance(verdict_d, _ci.ClosureEligible), repr(verdict_d)


def test_ac0020_closed_empty_ambiguous_discovery_refuses_named_feature(
    tmp_path: Path,
) -> None:
    """AC-0020 path (c): an ambiguous spec Discovery: refuses a named feature
    intent even when that feature's terminus is closed-empty.

    An unrelated spec has an ambiguous Discovery: that names intent-a (a
    closed-empty feature) and intent-d (another closed-empty feature).  Because
    closed-empty features skip the collection loop, the fix checks the snapshot
    at the start of _build_descendant_closure for these termini.

    The control feature (intent-z) has a clean closed-empty terminus and no
    broken spec naming it; it must not be refused.
    """
    # Feature A: closed-empty terminus.
    _write_intent(tmp_path, "intent-a", decomposed="closed-empty")
    # Control feature Z: closed-empty, not named in any broken spec.
    _write_intent(tmp_path, "intent-z", decomposed="closed-empty")

    # Unrelated broken spec: ambiguous Discovery: names both intent-a and intent-d.
    _write(
        tmp_path / "docs" / "specs" / "broken" / "spec.md",
        "# Broken\n\n"
        "- **Status:** Draft\n"
        "- **Discovery:** `intent:intent-a`\n"
        "- **Discovery:** `intent:intent-d`\n",
    )

    # Feature A must be refused because the ambiguous Discovery: names it.
    verdict_a = _check("intent-a", "closed-empty", tmp_path)
    assert isinstance(verdict_a, _ci.ClosureRefuse), repr(verdict_a)
    assert "delivery-relation-ambiguous" in verdict_a.reason

    # Control: feature Z must not be refused.
    verdict_z = _check("intent-z", "closed-empty", tmp_path)
    assert isinstance(verdict_z, _ci.ClosureEligible), repr(verdict_z)


def test_ambiguous_brief_named_brief_is_read_from_its_matched_file(
    tmp_path: Path,
) -> None:
    """A named brief whose file name differs from its slug still maps to its feature.

    The brief ``alpha-brief`` lives in ``BRF-0007-alpha.md`` and has no child spec
    other than the spec that names it ambiguously, so no coordinated relation
    reaches it. Close-work must read its ``Parent intent:`` from the exact path the
    resolver matched, refuse ``intent-alpha``, and leave the unrelated
    ``intent-ctrl`` closable. Rebuilding ``docs/product/briefs/alpha-brief.md`` from
    the slug would find no file and wrongly refuse every brief-route feature.
    """
    _write_intent(tmp_path, "intent-alpha", decomposed="brief")
    _write(
        tmp_path / "docs" / "product" / "briefs" / "BRF-0007-alpha.md",
        "# alpha-brief\n\n"
        "- **Slug:** `alpha-brief`\n"
        "- **Status:** Executing\n"
        "- **Parent intent:** intent:intent-alpha\n",
    )
    _write_intent(tmp_path, "intent-ctrl", decomposed="brief")
    _write_brief(tmp_path, "ctrl-brief", parent="intent-ctrl", status="Shipped")
    _write_spec(tmp_path, "ctrl-spec", brief="brief:ctrl-brief")
    _write(
        tmp_path / "docs" / "specs" / "broken" / "spec.md",
        "# Broken\n\n"
        "- **Status:** Draft\n"
        "- **Brief:** `brief:alpha-brief`\n"
        "- **Brief:** `brief:missing-brief`\n",
    )

    verdict_alpha = _check("intent-alpha", "brief", tmp_path)
    verdict_ctrl = _check("intent-ctrl", "brief", tmp_path)

    assert isinstance(verdict_alpha, _ci.ClosureRefuse), repr(verdict_alpha)
    assert "delivery-relation-ambiguous" in verdict_alpha.reason
    assert isinstance(verdict_ctrl, _ci.ClosureEligible), repr(verdict_ctrl)
