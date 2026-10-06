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

    def test_path_form_target_is_normalized(self, tmp_path: Path) -> None:
        """Path-form Discovery: targets are normalized to identifiers before matching."""
        _write_intent(tmp_path, "alpha", decomposed="spec")
        _write_intent(tmp_path, "beta", decomposed="spec")
        _write_spec(tmp_path, "alpha-delivery", discovery="intent:alpha")
        _write_spec(tmp_path, "beta-delivery", discovery="intent:beta")
        _write(
            tmp_path / "docs" / "specs" / "broken" / "spec.md",
            "# Broken\n\n"
            "- **Status:** Draft\n"
            "- **Discovery:** `intent:alpha`\n"
            "- **Discovery:** `docs/product/intents/beta.md`\n",
        )

        verdict = _check("beta", "spec", tmp_path)

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
    """A sleeping resolver that exceeds the lowered timeout yields delivery-resolver-unavailable."""
    stub = tmp_path / "sleeping_resolver.py"
    stub.write_text("import time; time.sleep(60)\n", encoding="utf-8")
    monkeypatch.setattr(_ci, "_RESOLVER_TIMEOUT", 1)

    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(stub),
    )
    _assert_unavailable(verdict)


def test_vi2104_oversized_stdout_yields_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resolver writing stdout beyond the size limit yields delivery-resolver-unavailable."""
    monkeypatch.setattr(_ci, "_MAX_SNAPSHOT_BYTES", 100)
    stub = tmp_path / "oversized_resolver.py"
    stub.write_text(
        "import sys; sys.stdout.write('x' * 102)\n",
        encoding="utf-8",
    )

    verdict = _ci.check_ancestor_closure(
        "gamma", "Accepted", "spec", tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=_make_provider(stub),
    )
    _assert_unavailable(verdict)


def test_vi2104_non_utf8_stdout_yields_unavailable(tmp_path: Path) -> None:
    """A resolver writing non-UTF-8 bytes to stdout yields delivery-resolver-unavailable."""
    stub = tmp_path / "bad_utf8_resolver.py"
    stub.write_text(
        "import sys; sys.stdout.buffer.write(b'\\xff\\xfe invalid utf8')\n",
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
