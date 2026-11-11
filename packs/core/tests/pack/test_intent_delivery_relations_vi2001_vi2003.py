"""VI-2001 extension, VI-2002, and VI-2003 tests for T10.

VI-2001 extension: canonical target forms for ambiguous Discovery and Decomposed.
VI-2002: provenance records carry the resolved intent identifier; absolute
         provenance targets are suppressed for both Contract: and Discovery:.
VI-2003: both consumers reject a diagnostic field outside the closed field set
         and a target outside canonical forms; unhashable values raise ValueError,
         not TypeError; one malformed-record table run against both consumers.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

CORE = Path(__file__).resolve().parents[2]
BINS = CORE / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
_CLOSE_WORK_SCRIPTS = CORE / ".apm" / "skills" / "close-work" / "scripts"
_CLOSURE_INDEX = _CLOSE_WORK_SCRIPTS / "closure_index.py"
_LINT_TRACEABILITY = CORE / ".apm" / "skills" / "work-loop" / "scripts" / "lint-traceability.py"


# ---------------------------------------------------------------------------
# Module loaders (unique names to avoid caching collisions)
# ---------------------------------------------------------------------------


def _load_resolver(suffix: str) -> Any:
    key = f"_vi2001_v2003_resolver_{suffix}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, SOURCE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_closure(suffix: str) -> Any:
    key = f"_vi2001_vi2003_closure_{suffix}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _CLOSURE_INDEX)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_lint(suffix: str) -> Any:
    key = f"_vi2001_vi2003_lint_{suffix}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _LINT_TRACEABILITY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# VI-2001 extension: canonical target validation for Discovery and Decomposed
# ---------------------------------------------------------------------------


def _write(path: Path, text: str) -> None:
    """Write text to path, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_vi2001_ambiguous_discovery_targets_are_canonical(tmp_path: Path) -> None:
    """Ambiguous Discovery: targets are always emitted as canonical identifiers.

    Both a slug-form (`intent:<slug>`) and a path-form
    (`docs/product/intents/<name>.md`) Discovery value that each resolve to a
    different feature intent are emitted as canonical identifiers (form a),
    not as raw artifact values.  All emitted targets must be printable.
    """
    resolver = _load_resolver("vi2001_disc")
    intents = tmp_path / "docs" / "product" / "intents"
    specs = tmp_path / "docs" / "specs"
    intents.mkdir(parents=True)

    _write(
        intents / "feat-a.md",
        "# A\n\n- **Slug:** `feat-a`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\n",
    )
    _write(
        intents / "feat-b.md",
        "# B\n\n- **Slug:** `feat-b`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\n",
    )
    # spec-1 references feat-a by slug form; feat-b by path form.
    # Both resolve to different feature intents → ambiguous Discovery.
    _write(
        specs / "s1" / "spec.md",
        "# S1\n\n- **Status:** Draft\n"
        "- **Discovery:** `intent:feat-a`\n"
        "- **Discovery:** `docs/product/intents/feat-b.md`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    diag_targets = [
        target
        for d in snapshot["diagnostics"]
        if d.get("field") == "Discovery"
        for target in d.get("targets", [])
    ]
    # All emitted targets must be printable canonical identifiers
    assert all(t.isprintable() for t in diag_targets), (
        f"Non-printable targets: {[t for t in diag_targets if not t.isprintable()]}"
    )
    # Both resolved features must appear as canonical identifiers, not raw paths
    assert "intent:feat-a" in diag_targets, (
        "intent:feat-a should appear as canonical identifier target"
    )
    assert "intent:feat-b" in diag_targets, (
        "intent:feat-b should appear as canonical identifier target (not path form)"
    )
    # The raw path form must not appear as a target
    assert not any("feat-b.md" in t and t != "intent:feat-b" for t in diag_targets), (
        "Raw path form must not appear; only canonical identifiers"
    )


def test_vi2001_hostile_discovery_target_is_omitted(tmp_path: Path) -> None:
    """A Discovery: value with embedded control chars is not a canonical target
    and must not appear in any diagnostic target list (decoded values checked).
    """
    resolver = _load_resolver("vi2001_hostile")
    intents = tmp_path / "docs" / "product" / "intents"
    intents.mkdir(parents=True)

    _write(
        intents / "feat.md",
        "# Feat\n\n- **Slug:** `feat`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\n",
    )
    specs = tmp_path / "docs" / "specs"
    # One valid, one hostile (control char in intent slug area)
    _write(
        specs / "broken" / "spec.md",
        "# Broken\n\n- **Status:** Draft\n"
        "- **Discovery:** `intent:feat`\n"
        # The second Discovery value carries an ESC sequence; it resolves to
        # 'not-found' via valid-intent path since the slug won't match.
        "- **Discovery:** `intent:feat\x1b[31m`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    all_targets = [
        t
        for d in snapshot["diagnostics"]
        for t in d.get("targets", [])
    ]
    assert all(t.isprintable() for t in all_targets), (
        f"Non-printable targets in diagnostics: "
        f"{[t for t in all_targets if not t.isprintable()]}"
    )


def test_vi2001_ambiguous_decomposed_targets_are_canonical_clean(
    tmp_path: Path,
) -> None:
    """Two distinct clean Decomposed: values produce canonical 'YYYY-MM-DD <route>'
    targets with exactly one space separator.
    """
    resolver = _load_resolver("vi2001_dec_clean")
    intents = tmp_path / "docs" / "product" / "intents"
    intents.mkdir(parents=True)
    _write(
        intents / "alpha.md",
        "# Alpha\n\n"
        "- **Slug:** `alpha`\n"
        "- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\n"
        "- **Decomposed:** 2026-10-06 brief\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    diag = [
        d for d in snapshot["diagnostics"]
        if d.get("code") == "delivery-relation-ambiguous"
        and d.get("subject") == "intent:alpha"
    ]
    assert diag, "Expected delivery-relation-ambiguous for alpha"
    targets = diag[0].get("targets", [])
    assert all(t.isprintable() for t in targets)
    assert "2026-10-06 spec" in targets
    assert "2026-10-06 brief" in targets
    for t in targets:
        parts = t.split(" ")
        assert len(parts) == 2, f"Target '{t!r}' has unexpected extra parts"


def test_vi2001_ambiguous_decomposed_hostile_targets_are_dropped(
    tmp_path: Path,
) -> None:
    """Decomposed: values that carry control or bidi characters after the route
    token are NOT canonical targets and are omitted from the diagnostic.

    The diagnostic is still emitted (the ambiguity is detected), but with an
    empty targets list since neither value reconstructs to a canonical form.
    """
    resolver = _load_resolver("vi2001_dec_hostile")
    intents = tmp_path / "docs" / "product" / "intents"
    intents.mkdir(parents=True)
    _write(
        intents / "alpha.md",
        "# Alpha\n\n"
        "- **Slug:** `alpha`\n"
        "- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\x1b[31m\n"
        "- **Decomposed:** 2026-10-06 brief‮\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    diag = [
        d for d in snapshot["diagnostics"]
        if d.get("code") == "delivery-relation-ambiguous"
        and d.get("subject") == "intent:alpha"
    ]
    assert diag, "Ambiguity diagnostic must still be emitted"
    targets = diag[0].get("targets", [])
    # No hostile content reaches the target list
    assert all(t.isprintable() for t in targets), (
        f"Non-printable targets: {[t for t in targets if not t.isprintable()]}"
    )
    # Neither hostile value (with control/bidi) is emitted as a target
    assert "spec\x1b" not in str(targets)
    assert "brief‮" not in str(targets)


# ---------------------------------------------------------------------------
# Security: ambiguous brief Parent intent: emits canonical targets only
# ---------------------------------------------------------------------------


def test_ambiguous_brief_parent_intent_canonical_targets_accepted_by_consumers(
    tmp_path: Path,
) -> None:
    """A brief with two valid Parent intent: values of any kind emits a
    delivery-relation-ambiguous diagnostic with canonical ``intent:<slug>``
    targets; both consumers accept the resulting snapshot.

    This covers the case where the kind is not ``intent`` (e.g. ``outcome``
    or ``capability``): the raw ``outcome:a`` and ``capability:b`` values
    must be normalised to ``intent:a`` and ``intent:b`` before being placed
    in ``targets`` so the snapshot passes both consumers' validation.
    """
    resolver = _load_resolver("sec1_canonical_parents")
    ci = _load_closure("sec1_canonical_parents")
    lint = _load_lint("sec1_canonical_parents")

    briefs_dir = tmp_path / "docs" / "product" / "briefs"
    briefs_dir.mkdir(parents=True)
    _write(
        briefs_dir / "multi-parent.md",
        "# Multi parent\n\n"
        "- **Slug:** `multi-parent`\n"
        "- **Status:** Draft\n"
        "- **Parent intent:** outcome:alpha\n"
        "- **Parent intent:** capability:beta\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    # Diagnostic must be emitted.
    diag = [
        d for d in snapshot["diagnostics"]
        if d.get("code") == "delivery-relation-ambiguous"
        and d.get("subject") == "brief:multi-parent"
        and d.get("field") == "Parent intent"
    ]
    assert diag, (
        "Expected delivery-relation-ambiguous for brief:multi-parent Parent intent"
    )
    targets = diag[0].get("targets", [])
    # All targets must be canonical intent identifiers.
    assert all(t.startswith("intent:") for t in targets), (
        f"Targets must be canonical intent: identifiers; got {targets!r}"
    )

    # Both consumers must accept the snapshot without raising.
    for consumer_label, module in [("close-work", ci), ("lint", lint)]:
        try:
            module._validate_snapshot_dict(dict(snapshot))
        except (ValueError, TypeError) as exc:
            pytest.fail(
                f"[{consumer_label}] snapshot with non-intent Parent intent: "
                f"kinds was rejected: {exc}"
            )


# ---------------------------------------------------------------------------
# VI-2002: provenance carries intent identifier; absolute targets suppressed
# ---------------------------------------------------------------------------


def test_vi2002_provenance_carries_intent_for_direct_light_route(
    tmp_path: Path,
) -> None:
    """A spec Discovery: that resolves to a direct-light feature intent yields
    a provenance record that carries the resolved intent identifier.
    """
    resolver = _load_resolver("vi2002_direct_light")
    intents = tmp_path / "docs" / "product" / "intents"
    specs = tmp_path / "docs" / "specs"
    intents.mkdir(parents=True)

    _write(
        intents / "lite.md",
        "# Lite\n\n- **Slug:** `lite`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 direct-light\n",
    )
    _write(
        specs / "lite-spec" / "spec.md",
        "# Lite spec\n\n- **Status:** Draft\n- **Discovery:** `intent:lite`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    prov = [
        p for p in snapshot["provenance"]
        if p.get("subject") == "spec:lite-spec" and p.get("field") == "Discovery"
    ]
    assert prov, "Expected a provenance record for spec:lite-spec Discovery"
    assert prov[0].get("intent") == "intent:lite", (
        "Provenance record must carry 'intent' for a direct-light feature"
    )


def test_vi2002_provenance_carries_intent_for_closed_empty_route(
    tmp_path: Path,
) -> None:
    """A spec Discovery: that resolves to a closed-empty feature intent yields
    a provenance record with the resolved intent identifier.
    """
    resolver = _load_resolver("vi2002_closed_empty")
    intents = tmp_path / "docs" / "product" / "intents"
    specs = tmp_path / "docs" / "specs"
    intents.mkdir(parents=True)

    _write(
        intents / "empty.md",
        "# Empty\n\n- **Slug:** `empty`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 closed-empty\n",
    )
    _write(
        specs / "empty-spec" / "spec.md",
        "# Empty spec\n\n- **Status:** Draft\n- **Discovery:** `intent:empty`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    prov = [
        p for p in snapshot["provenance"]
        if p.get("subject") == "spec:empty-spec" and p.get("field") == "Discovery"
    ]
    assert prov, "Expected provenance record for closed-empty feature"
    assert prov[0].get("intent") == "intent:empty", (
        "Provenance record must carry 'intent' for a closed-empty feature"
    )


def test_vi2002_absolute_contract_target_suppressed(tmp_path: Path) -> None:
    """An absolute path in Contract: is emitted without a 'target' field.

    Covers leading slash, drive letter (C:/...), and UNC-style backslash forms.
    """
    resolver = _load_resolver("vi2002_abs_contract")
    specs = tmp_path / "docs" / "specs"
    _write(
        specs / "abs-spec" / "spec.md",
        "# Abs spec\n\n- **Status:** Draft\n"
        "- **Contract:** /absolute/path\n"
        "- **Contract:** C:/windows/path\n"
        r"- **Contract:** \unc\share" + "\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    contract_prov = [
        p for p in snapshot["provenance"]
        if p.get("subject") == "spec:abs-spec" and p.get("field") == "Contract"
    ]
    assert contract_prov, "Absolute Contract: values should yield provenance records"
    for rec in contract_prov:
        assert "target" not in rec, (
            f"Absolute Contract: target must be suppressed, got {rec!r}"
        )


def test_vi2002_absolute_discovery_non_intent_target_suppressed(
    tmp_path: Path,
) -> None:
    """A non-intent-shaped Discovery: that is an absolute path is emitted as
    contextual provenance without a 'target' field.
    """
    resolver = _load_resolver("vi2002_abs_disc")
    specs = tmp_path / "docs" / "specs"
    _write(
        specs / "abs-disc" / "spec.md",
        "# Abs disc\n\n- **Status:** Draft\n"
        "- **Discovery:** /absolute/context-doc\n"
        r"- **Discovery:** C:\windows\thing" + "\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)

    disc_prov = [
        p for p in snapshot["provenance"]
        if p.get("subject") == "spec:abs-disc" and p.get("field") == "Discovery"
    ]
    assert disc_prov, "Absolute non-intent Discovery: values should yield provenance"
    for rec in disc_prov:
        assert "target" not in rec, (
            f"Absolute Discovery: target must be suppressed, got {rec!r}"
        )


# ---------------------------------------------------------------------------
# VI-2003: both consumers reject bad field / bad targets / unhashable values
# ---------------------------------------------------------------------------

# A minimal valid snapshot that both consumers accept.
_VALID_SNAPSHOT: dict[str, Any] = {
    "schema_version": 1,
    "complete": True,
    "relations": [],
    "classifications": [],
    "provenance": [],
    "diagnostics": [],
    "artifacts": {},
}


def _snapshot_with_diag(diag: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the valid snapshot with one diagnostic entry injected."""
    snap = copy.deepcopy(_VALID_SNAPSHOT)
    snap["diagnostics"] = [diag]
    return snap


def _snapshot_with_relation(rel: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the valid snapshot with one relation entry injected."""
    snap = copy.deepcopy(_VALID_SNAPSHOT)
    snap["relations"] = [rel]
    return snap


def _snapshot_with_classification(cls: dict[str, Any]) -> dict[str, Any]:
    snap = copy.deepcopy(_VALID_SNAPSHOT)
    snap["classifications"] = [cls]
    return snap


# Parametrized table: (description, bad_snapshot_factory, marker_to_exclude)
# Each snapshot must be rejected by both validators.
_VALID_DIAG_BASE = {
    "code": "delivery-target-missing",
    "subject": "intent:alpha",
}

_MALFORMED_RECORD_CASES = [
    # --- unhashable values in closed-set fields ---
    (
        "unhashable_relation_type",
        _snapshot_with_relation({
            "type": ["list-is-unhashable"],
            "route": "spec",
            "intent": "intent:alpha",
            "spec": "spec:alpha-delivery",
            "basis": {},
        }),
        "list-is-unhashable",
    ),
    (
        "unhashable_relation_route",
        _snapshot_with_relation({
            "type": "direct-delivery",
            "route": {"dict": "unhashable"},
            "intent": "intent:alpha",
            "spec": "spec:alpha-delivery",
            "basis": {},
        }),
        "unhashable",
    ),
    (
        "unhashable_classification_value",
        _snapshot_with_classification({
            "classification": [1, 2, 3],
            "intent": "intent:alpha",
            "route": "spec",
        }),
        None,
    ),
    (
        "unhashable_diagnostic_field",
        _snapshot_with_diag({
            **_VALID_DIAG_BASE,
            "field": ["list-field"],
        }),
        "list-field",
    ),
    (
        "unhashable_diagnostic_code",
        _snapshot_with_diag({
            **{k: v for k, v in _VALID_DIAG_BASE.items() if k != "code"},
            "code": {"dict": "code"},
        }),
        None,
    ),
    # --- hostile field outside closed set ---
    (
        "hostile_field_value",
        _snapshot_with_diag({
            **_VALID_DIAG_BASE,
            "field": "INJECTED_HOSTILE_FIELD",
        }),
        "INJECTED_HOSTILE_FIELD",
    ),
    # --- hostile targets ---
    (
        "control_char_target",
        _snapshot_with_diag({
            **_VALID_DIAG_BASE,
            "targets": ["2026-10-06 spec\x1b[31m"],
        }),
        None,
    ),
    (
        "bidi_target",
        _snapshot_with_diag({
            **_VALID_DIAG_BASE,
            "targets": ["2026-10-06 spec\u202e"],
        }),
        None,
    ),
    (
        "absolute_path_target",
        _snapshot_with_diag({
            **_VALID_DIAG_BASE,
            "targets": ["/absolute/path"],
        }),
        "/absolute/path",
    ),
    (
        "token_equals_target",
        _snapshot_with_diag({
            **_VALID_DIAG_BASE,
            "targets": ["TOKEN=abc"],
        }),
        "TOKEN=abc",
    ),
]


@pytest.mark.parametrize("description,bad_snap,hostile_marker", _MALFORMED_RECORD_CASES)
def test_vi2003_both_consumers_reject_malformed_record(
    description: str,
    bad_snap: dict[str, Any],
    hostile_marker: str | None,
) -> None:
    """Both consumer validators reject each malformed record with
    delivery-resolver-unavailable; no TypeError escapes; no hostile marker
    appears in the reason.
    """
    ci = _load_closure(f"vi2003_{description}")
    lint = _load_lint(f"vi2003_{description}")

    for label, module in [("close-work", ci), ("lint", lint)]:
        reason = ""
        try:
            module._validate_snapshot_dict(copy.deepcopy(bad_snap))
            pytest.fail(
                f"[{label}] {description}: _validate_snapshot_dict did not raise"
            )
        except ValueError as exc:
            reason = str(exc)
        except TypeError as exc:
            pytest.fail(
                f"[{label}] {description}: unhashable value escaped as TypeError: {exc}"
            )
        assert "delivery-resolver-unavailable" in reason, (
            f"[{label}] {description}: reason must start with delivery-resolver-unavailable, "
            f"got: {reason!r}"
        )
        if hostile_marker is not None:
            assert hostile_marker not in reason, (
                f"[{label}] {description}: hostile marker {hostile_marker!r} must not "
                f"appear in the reason, got: {reason!r}"
            )


def test_vi2003_lint_exits_1_for_hostile_field(tmp_path: Path) -> None:
    """The lint exits 1 for a hostile diagnostic field injected via snapshot_provider.

    Confirms the full check() path rejects the malformed record and that no
    hostile field value appears in the output.
    """
    lint = _load_lint("vi2003_lint_check")

    hostile_snap: dict[str, Any] = {
        **_VALID_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-target-missing",
            "subject": "intent:alpha",
            "field": "INJECTED_HOSTILE",
        }],
    }

    # Write a minimal brief anchor so the lint invokes the resolver.
    _write(
        tmp_path / "docs" / "product" / "briefs" / "anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    _out, _err, exit_hint = lint.check(
        tmp_path,
        strict=False,
        snapshot_provider=lambda _r: hostile_snap,
    )
    assert exit_hint == 1, "lint must exit 1 when snapshot has hostile field"
    combined = "\n".join(_out + _err)
    assert "delivery-resolver-unavailable" in combined, (
        "delivery-resolver-unavailable must appear in lint output"
    )
    assert "INJECTED_HOSTILE" not in combined, (
        "Hostile field value must not appear in lint output"
    )


def test_vi2003_lint_label_prints_closed_set_field_and_canonical_targets(
    tmp_path: Path,
) -> None:
    """Lint delivery lines print code, subject, closed-set field, and canonical
    targets only.  A valid snapshot with a target-missing diagnostic for a
    spec yields a label containing the stable code and subject.
    """
    lint = _load_lint("vi2003_label")

    valid_snap: dict[str, Any] = {
        **_VALID_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-target-missing",
            "subject": "spec:alpha-delivery",
            "field": "Discovery",
        }],
    }

    _write(
        tmp_path / "docs" / "product" / "briefs" / "anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    _out, _err, _exit = lint.check(
        tmp_path,
        strict=False,
        snapshot_provider=lambda _r: valid_snap,
    )
    combined = "\n".join(_out + _err)
    # The label must contain the stable code
    assert "delivery-target-missing" in combined
    # The field must appear in the label
    assert "field=Discovery" in combined
    # No hostile content (the snapshot is clean, so no escapes needed)
    assert "\x1b" not in combined


def test_vi2003_both_consumers_accept_base_records_unchanged() -> None:
    """Both consumer validators accept each base diagnostic, relation, and
    classification unchanged.

    This accepting-control ensures the malformed-record table's base rows are
    themselves valid: a row could only be rejected because of its mutated field,
    not because the base row was already broken.
    """
    ci = _load_closure("vi2003_accept_base")
    lint = _load_lint("vi2003_accept_base")

    # Base diagnostic (used as the template in _MALFORMED_RECORD_CASES).
    diag_snap = _snapshot_with_diag(copy.deepcopy(_VALID_DIAG_BASE))

    # Base relation (direct-delivery, spec route — the minimal valid form).
    rel_snap = _snapshot_with_relation({
        "type": "direct-delivery",
        "route": "spec",
        "intent": "intent:alpha",
        "spec": "spec:alpha-delivery",
        "basis": {},
    })

    # Base classification.
    cls_snap = _snapshot_with_classification({
        "classification": "direct-delivery",
        "intent": "intent:alpha",
        "route": "spec",
    })

    for label, snap in [
        ("base diagnostic", diag_snap),
        ("base relation", rel_snap),
        ("base classification", cls_snap),
    ]:
        for consumer_label, module in [("close-work", ci), ("lint", lint)]:
            try:
                module._validate_snapshot_dict(copy.deepcopy(snap))
            except (ValueError, TypeError) as exc:
                pytest.fail(
                    f"[{consumer_label}] {label}: _validate_snapshot_dict "
                    f"rejected a valid base record: {exc}"
                )


# ── VI-2404: Parent intent provenance records ────────────────────────────────


def _write_vi2404(path: Any, text: str) -> None:
    """Write text to path, creating parents as needed."""
    from pathlib import Path as _Path
    p = _Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_vi2404_resolver_emits_parent_intent_provenance_for_ambiguous_brief(
    tmp_path: Any,
) -> None:
    """Resolver emits one Parent intent provenance record per feature intent named
    by a brief that an ambiguous spec Brief: targets.

    A brief with two valid Parent intent: values (intent:alpha and intent:beta)
    is named in a two-value spec Brief: (ambiguous).  The resolver emits one
    provenance record for each feature the brief names.  The brief's own
    delivery-relation-ambiguous diagnostic (from its two distinct Parent intent:
    slugs) is also present; the provenance records are emitted regardless.
    """
    resolver = _load_resolver("vi2404_prov")
    _write_vi2404(
        tmp_path / "docs/product/intents/alpha.md",
        "# alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-07 spec\n",
    )
    _write_vi2404(
        tmp_path / "docs/product/intents/beta.md",
        "# beta\n\n- **Slug:** `beta`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-07 spec\n",
    )
    _write_vi2404(
        tmp_path / "docs/product/briefs/shared-brief.md",
        "# Shared\n\n- **Slug:** `shared`\n- **Status:** Executing\n"
        "- **Parent intent:** intent:alpha\n"
        "- **Parent intent:** intent:beta\n",
    )
    _write_vi2404(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:shared`\n"
        "- **Brief:** `brief:missing`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)
    assert snapshot["complete"] is True

    pi_provs = [
        p for p in snapshot["provenance"]
        if p.get("field") == "Parent intent"
    ]
    assert len(pi_provs) == 2, (
        f"expected 2 Parent intent records, got {pi_provs!r}"
    )
    subjects = {p["subject"] for p in pi_provs}
    intents = {p["intent"] for p in pi_provs}
    assert subjects == {"brief:shared"}, f"wrong subjects: {subjects!r}"
    assert intents == {"intent:alpha", "intent:beta"}, f"wrong intents: {intents!r}"


def test_vi2404_consumers_accept_parent_intent_provenance(tmp_path: Any) -> None:
    """Both consumers' _validate_snapshot_dict accept Parent intent provenance records."""
    ci = _load_closure("vi2404_ci")
    lint = _load_lint("vi2404_lint")

    snapshot = {
        "schema_version": 1,
        "complete": True,
        "relations": [],
        "classifications": [],
        "provenance": [
            {
                "subject": "brief:shared",
                "field": "Parent intent",
                "intent": "intent:alpha",
            },
        ],
        "diagnostics": [],
        "artifacts": {},
    }
    for consumer_label, module in [("close-work", ci), ("lint", lint)]:
        try:
            module._validate_snapshot_dict(copy.deepcopy(snapshot))
        except (ValueError, TypeError) as exc:
            pytest.fail(
                f"[{consumer_label}] _validate_snapshot_dict rejected "
                f"Parent intent provenance: {exc}"
            )


def test_vi2404_same_slug_different_kind_yields_one_record_no_ambiguity(
    tmp_path: Any,
) -> None:
    """Parent intent: values of different kinds sharing one slug form one record
    and no ambiguity diagnostic (AC-0008 deduplication by slug).
    """
    resolver = _load_resolver("vi2404_dedup")
    _write_vi2404(
        tmp_path / "docs/product/intents/x.md",
        "# X\n\n- **Slug:** `x`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-07 spec\n",
    )
    _write_vi2404(
        tmp_path / "docs/product/briefs/dup-brief.md",
        "# Dup\n\n- **Slug:** `dup`\n- **Status:** Executing\n"
        "- **Parent intent:** outcome:x\n"
        "- **Parent intent:** capability:x\n",
    )
    # Ambiguous spec Brief: so the provenance records are emitted
    _write_vi2404(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:dup`\n"
        "- **Brief:** `brief:other`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)
    assert snapshot["complete"] is True

    pi_provs = [
        p for p in snapshot["provenance"]
        if p.get("field") == "Parent intent"
        and p.get("subject") == "brief:dup"
    ]
    assert len(pi_provs) == 1, (
        f"same-slug different-kind values must yield one record; got {pi_provs!r}"
    )
    assert pi_provs[0]["intent"] == "intent:x"

    # No ambiguity diagnostic for the brief
    brief_ambig = [
        d for d in snapshot["diagnostics"]
        if d.get("subject") == "brief:dup"
        and d.get("code") == "delivery-relation-ambiguous"
    ]
    assert not brief_ambig, (
        f"same-slug deduplication must prevent ambiguity: {brief_ambig!r}"
    )


def test_vi2404_lint_results_unchanged_by_parent_intent_provenance(
    tmp_path: Any,
) -> None:
    """lint-traceability results are unchanged when Parent intent provenance
    records are present versus when they are absent from the snapshot.

    The resolver runs on a fixture with an ambiguous spec Brief: that names a
    brief with Parent intent: values.  The lint receives that real snapshot via
    snapshot_provider and also receives a copy with the Parent intent records
    removed.  Both runs must produce the same violations and exit code.
    """
    resolver = _load_resolver("vi2404_lint_unchanged")
    lint = _load_lint("vi2404_lint_unchanged")

    _write_vi2404(
        tmp_path / "docs/product/intents/alpha.md",
        "# alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-07 spec\n",
    )
    _write_vi2404(
        tmp_path / "docs/product/briefs/linked.md",
        "# Linked\n\n- **Slug:** `linked`\n- **Status:** Executing\n"
        "- **Parent intent:** intent:alpha\n",
    )
    _write_vi2404(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:linked`\n"
        "- **Brief:** `brief:missing`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)
    assert snapshot["complete"] is True

    # Confirm Parent intent records are present
    pi_records = [p for p in snapshot["provenance"] if p.get("field") == "Parent intent"]
    assert pi_records, "resolver must emit Parent intent provenance for this fixture"

    # Snapshot without Parent intent records
    snapshot_no_pi = {
        **snapshot,
        "provenance": [p for p in snapshot["provenance"] if p.get("field") != "Parent intent"],
    }

    # Run lint on both snapshots
    out1, hard1, exit1 = lint.check(
        tmp_path, False, snapshot_provider=lambda _: copy.deepcopy(snapshot)
    )
    out2, hard2, exit2 = lint.check(
        tmp_path, False, snapshot_provider=lambda _: copy.deepcopy(snapshot_no_pi)
    )

    assert exit1 == exit2, (
        f"exit codes must match: with PI={exit1}, without PI={exit2}"
    )
    assert set(hard1) == set(hard2), (
        f"hard violations must match:\n  with PI: {hard1}\n  without PI: {hard2}"
    )
    assert set(out1) == set(out2), (
        f"informational output must match:\n  with PI: {out1}\n  without PI: {out2}"
    )


def test_vi2404_cross_spec_dedup_emits_one_record_per_intent(
    tmp_path: Any,
) -> None:
    """When two ambiguous spec Brief: diagnostics name the same brief, the
    resolver emits exactly one Parent intent record per distinct feature intent
    for that brief.

    The _emitted_pi_prov guard prevents duplicate (brief, intent) pairs.  If
    the guard is removed (replaced by 'if True:'), two records would be emitted
    for each intent, and the length assertion here would fail.
    """
    resolver = _load_resolver("vi2404_cross_spec_dedup")

    _write_vi2404(
        tmp_path / "docs/product/intents/alpha.md",
        "# alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-07 spec\n",
    )
    _write_vi2404(
        tmp_path / "docs/product/intents/beta.md",
        "# beta\n\n- **Slug:** `beta`\n- **Level:** feature\n"
        "- **Decomposed:** 2026-10-07 spec\n",
    )
    # One brief named by two different specs' ambiguous Brief: fields
    _write_vi2404(
        tmp_path / "docs/product/briefs/shared.md",
        "# Shared\n\n- **Slug:** `shared`\n- **Status:** Executing\n"
        "- **Parent intent:** intent:alpha\n"
        "- **Parent intent:** intent:beta\n",
    )
    # Spec 1: ambiguous Brief: naming brief:shared and brief:missing1
    _write_vi2404(
        tmp_path / "docs/specs/spec-one/spec.md",
        "# Spec One\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:shared`\n"
        "- **Brief:** `brief:missing1`\n",
    )
    # Spec 2: ambiguous Brief: also naming brief:shared and brief:missing2
    _write_vi2404(
        tmp_path / "docs/specs/spec-two/spec.md",
        "# Spec Two\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:shared`\n"
        "- **Brief:** `brief:missing2`\n",
    )

    snapshot = resolver.resolve_repository(tmp_path)
    assert snapshot["complete"] is True

    pi_provs = [
        p for p in snapshot["provenance"]
        if p.get("field") == "Parent intent" and p.get("subject") == "brief:shared"
    ]
    # Exactly one record per distinct admitted feature intent (alpha and beta),
    # regardless of how many specs named this brief.
    assert len(pi_provs) == 2, (
        f"expected exactly 2 Parent intent records for brief:shared, got {pi_provs!r}"
    )
    intents = {p["intent"] for p in pi_provs}
    assert intents == {"intent:alpha", "intent:beta"}, (
        f"wrong intents: {intents!r}"
    )
