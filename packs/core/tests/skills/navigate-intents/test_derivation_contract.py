"""Contract tests for intent_graph derivation.

These tests encode the graph derivation contract (spec.md § Derivation and
resolution). They are frozen red in T1 and turned green when T2 implements
intent_graph.derive().

Every test that calls intent_graph must fail ONLY because the module is absent
(ImportError / ModuleNotFoundError). No syntax errors, no fixture-builder
errors, and no fixture-shape failures are acceptable red states in T1.

Module loaded by path following the loader precedent in
packs/governance-extras/tests/skills/navigate-decisions/test_query_contract.py
and packs/core/tests/skills/close-work/test_closure_terminality.py.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"

_HERE = pathlib.Path(__file__).resolve().parent
_FIXTURE_MIXED = _HERE / "fixtures" / "mixed"
_FIXTURE_NEG = _HERE / "fixtures" / "negative"


# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load_intent_graph():
    """Load intent_graph by path under a pack-and-skill-qualified name."""
    module_path = _SCRIPTS / "intent_graph.py"
    spec = importlib.util.spec_from_file_location(
        "core_navigate_intents_intent_graph", module_path
    )
    if spec is None or spec.loader is None:
        pytest.fail(
            f"intent_graph.py not found at {module_path}. "
            "Expected: module absent (red in T1)."
        )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["core_navigate_intents_intent_graph"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# Load module once at collection time. This import-time failure is the
# expected red state for T1: every test in this file that uses `ig` will
# error with the same message, which is the correct failure mode.
try:
    ig = _load_intent_graph()
    _IMPORT_ERROR: Exception | None = None
except Exception as exc:  # noqa: BLE001
    ig = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc


def _skip_if_module_absent() -> None:
    """Fail the test with a clear message when the module is absent.

    Tests that call the seam must fail (not skip) in T1, showing the missing
    module as the failure reason. Fixture-shape validators do not call this.
    """
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"intent_graph.py not found at {_SCRIPTS / 'intent_graph.py'} — "
            f"expected red in T1 (module absent): {_IMPORT_ERROR}"
        )


# ---------------------------------------------------------------------------
# Fixture-shape validators — must PASS in T1 (do not call the seam)
# ---------------------------------------------------------------------------


def test_mixed_fixture_root_exists() -> None:
    """The mixed/ corpus root exists with all three artifact directories."""
    assert _FIXTURE_MIXED.is_dir(), f"missing: {_FIXTURE_MIXED}"
    assert (_FIXTURE_MIXED / "docs" / "product" / "intents").is_dir()
    assert (_FIXTURE_MIXED / "docs" / "product" / "briefs").is_dir()
    assert (_FIXTURE_MIXED / "docs" / "specs").is_dir()


def test_mixed_capability_intent_present() -> None:
    """mixed/ has a capability intent (CAP-0001-alpha-cap.md)."""
    p = _FIXTURE_MIXED / "docs" / "product" / "intents" / "CAP-0001-alpha-cap.md"
    assert p.is_file(), f"missing: {p}"
    text = p.read_text(encoding="utf-8")
    assert "**Slug:**" in text
    assert "capability" in text.lower()


def test_mixed_kind_wins_over_level() -> None:
    """mixed/ has an intent with Level: capability and Kind: outcome (Kind wins)."""
    p = _FIXTURE_MIXED / "docs" / "product" / "intents" / "FEAT-0002-echo-crosstype.md"
    assert p.is_file(), f"missing: {p}"
    text = p.read_text(encoding="utf-8")
    assert "**Level:** capability" in text
    assert "**Kind:** outcome" in text


def test_mixed_tombstone_with_reissued_as() -> None:
    """mixed/ has a tombstone intent with Reissued as: field."""
    p = _FIXTURE_MIXED / "docs" / "product" / "intents" / "FEAT-0003-foxtrot-tomb.md"
    assert p.is_file(), f"missing: {p}"
    text = p.read_text(encoding="utf-8")
    assert "**Tombstone:**" in text
    assert "**Reissued as:**" in text


def test_mixed_seeded_brief_template_not_a_node() -> None:
    """mixed/ briefs include _template.md which starts with underscore (not admitted)."""
    p = _FIXTURE_MIXED / "docs" / "product" / "briefs" / "_template.md"
    assert p.is_file(), f"missing: {p}"
    # File exists but must not be admitted: _ARTIFACT_FILE_RE requires [A-Za-z0-9] start.
    assert p.name.startswith("_"), "seeded brief template must start with underscore"


def test_mixed_brief_parent_inside_html_comment() -> None:
    """mixed/ has a brief whose Parent intent: is inside a multi-line HTML comment."""
    p = _FIXTURE_MIXED / "docs" / "product" / "briefs" / "hidden-parent.md"
    assert p.is_file(), f"missing: {p}"
    text = p.read_text(encoding="utf-8")
    assert "<!--" in text
    assert "**Parent intent:**" in text


def test_mixed_status_with_text_after_word() -> None:
    """mixed/ has intents with 'Fulfilled — date' and 'Fulfilled (date)' status values."""
    hotel = _FIXTURE_MIXED / "docs" / "product" / "intents" / "CAP-0003-hotel-done.md"
    juliet = _FIXTURE_MIXED / "docs" / "product" / "intents" / "FEAT-0006-juliet-done.md"
    assert hotel.is_file() and juliet.is_file()
    assert "Fulfilled — 2026-01-01" in hotel.read_text(encoding="utf-8")
    assert "Fulfilled (2026-01-01)" in juliet.read_text(encoding="utf-8")


def test_mixed_none_parents_both_forms() -> None:
    """mixed/ has 'none' parent without and with trailing comment."""
    india = _FIXTURE_MIXED / "docs" / "product" / "intents" / "FEAT-0005-india-none.md"
    juliet = _FIXTURE_MIXED / "docs" / "product" / "intents" / "FEAT-0006-juliet-done.md"
    assert india.is_file() and juliet.is_file()
    india_text = india.read_text(encoding="utf-8")
    juliet_text = juliet.read_text(encoding="utf-8")
    assert "**Parent intent:** none" in india_text
    assert "**Parent intent:** none <!--" in juliet_text


def test_mixed_cross_type_slug_collision() -> None:
    """mixed/ has same slug 'golf-new' for both an intent and a spec directory."""
    intent = _FIXTURE_MIXED / "docs" / "product" / "intents" / "FEAT-0004-golf-new.md"
    spec_dir = _FIXTURE_MIXED / "docs" / "specs" / "golf-new"
    assert intent.is_file(), f"missing intent: {intent}"
    assert spec_dir.is_dir(), f"missing spec dir: {spec_dir}"
    assert "**Slug:** `golf-new`" in intent.read_text(encoding="utf-8")


def test_mixed_spec_with_typed_discovery() -> None:
    """mixed/ has a spec with typed Discovery: (intent:bravo-feat)."""
    p = _FIXTURE_MIXED / "docs" / "specs" / "bravo-spec" / "spec.md"
    assert p.is_file()
    assert "**Discovery:** intent:bravo-feat" in p.read_text(encoding="utf-8")


def test_mixed_spec_with_path_discovery() -> None:
    """mixed/ has a spec with path-form Discovery:."""
    p = _FIXTURE_MIXED / "docs" / "specs" / "charlie-spec" / "spec.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "**Discovery:** docs/product/intents/" in text


def test_mixed_spec_with_markdown_link_discovery() -> None:
    """mixed/ has a spec with markdown-link Discovery:."""
    p = _FIXTURE_MIXED / "docs" / "specs" / "golf-new" / "spec.md"
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "**Discovery:** [" in text


def test_mixed_spec_with_brief() -> None:
    """mixed/ has a spec with a Brief: field."""
    p = _FIXTURE_MIXED / "docs" / "specs" / "bravo-spec" / "spec.md"
    assert p.is_file()
    assert "**Brief:** brief:bravo-delivery" in p.read_text(encoding="utf-8")


def test_mixed_expected_outstanding_exists() -> None:
    """mixed/ has expected-outstanding.json with non-empty outstanding list."""
    import json
    p = _FIXTURE_MIXED / "expected-outstanding.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "outstanding" in data
    assert len(data["outstanding"]) > 0


def test_negative_fixture_dirs_exist() -> None:
    """All required negative fixture directories are present."""
    required = [
        "dangling",
        "retired_target",
        "kind_mismatch",
        "out_of_type",
        "multiple_values",
        "cycle",
        "unparseable",
        "malformed_record_utf8",
        "malformed_record_bad_slug",
        "duplicate_identity",
        "brief_parent_malformed",
        "brief_parent_unsafe",
        "brief_parent_ambiguous",
        "brief_parent_repair",
        "brief_parent_unrecognized",
        "no_decomposed",
        "spec_route",
        "two_briefs",
    ]
    for name in required:
        d = _FIXTURE_NEG / name
        assert d.is_dir(), f"missing negative fixture directory: {name}"


def test_all_negative_fixtures_have_expected_outstanding() -> None:
    """Every negative fixture directory has an expected-outstanding.json file."""
    import json
    for d in sorted(_FIXTURE_NEG.iterdir()):
        if not d.is_dir():
            continue
        manifest = d / "expected-outstanding.json"
        assert manifest.is_file(), f"missing expected-outstanding.json in {d.name}"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert "outstanding" in data, f"expected-outstanding.json in {d.name} missing 'outstanding' key"


def test_cycle_fixture_has_self_parent_and_two_member_cycle() -> None:
    """cycle/ fixture has both a self-parent intent and a 2-member cycle."""
    intents_dir = _FIXTURE_NEG / "cycle" / "docs" / "product" / "intents"
    assert intents_dir.is_dir()
    names = {p.name for p in intents_dir.iterdir() if p.is_file()}
    assert "FEAT-0001-self-cycle.md" in names, "cycle/ missing self-cycle intent"
    assert "FEAT-0002-cycle-a.md" in names, "cycle/ missing cycle-a intent"
    assert "FEAT-0003-cycle-b.md" in names, "cycle/ missing cycle-b intent"


def test_unparseable_fixture_covers_all_three_sub_cases() -> None:
    """unparseable/ covers absolute path, .. segment, and backslash."""
    intents_dir = _FIXTURE_NEG / "unparseable" / "docs" / "product" / "intents"
    assert intents_dir.is_dir()
    texts = [p.read_text(encoding="utf-8") for p in sorted(intents_dir.iterdir()) if p.is_file()]
    combined = "\n".join(texts)
    assert "/absolute/path" in combined, "unparseable/ missing absolute path case"
    assert ".." in combined, "unparseable/ missing .. segment case"
    assert "\\" in combined, "unparseable/ missing backslash case"


def test_malformed_record_utf8_fixture_has_invalid_bytes() -> None:
    """malformed_record_utf8/ has a file with invalid UTF-8 bytes."""
    intents_dir = _FIXTURE_NEG / "malformed_record_utf8" / "docs" / "product" / "intents"
    assert intents_dir.is_dir()
    for p in intents_dir.iterdir():
        if p.is_file():
            raw = p.read_bytes()
            try:
                raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                return  # Found one — good.
    pytest.fail("malformed_record_utf8/ has no file with invalid UTF-8 bytes")


# ---------------------------------------------------------------------------
# Contract tests — call the seam; fail only because module is absent in T1
# ---------------------------------------------------------------------------


def test_derive_nodes_admission_over_mixed() -> None:
    """derive() admits every live non-tombstone intent, brief, and spec from mixed/.

    AC-0001: live intents + live briefs + specs matching the patterns.
    The seeded brief template (_template.md) must not be a node.
    Tombstone FEAT-0003-foxtrot-tomb.md must not be a node.
    """
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_MIXED)  # type: ignore[union-attr]
    node_ids = {n["id"] for n in result["nodes"]}
    # Must be present.
    assert "capability:alpha-cap" in node_ids, "alpha-cap missing from nodes"
    assert "intent:bravo-feat" in node_ids, "bravo-feat missing from nodes"
    # Kind: outcome wins over Level: capability.
    assert "outcome:charlie-out" in node_ids, "charlie-out missing from nodes"
    assert "opportunity:delta-opp" in node_ids, "delta-opp missing from nodes"
    # Level: capability + Kind: outcome → outcome wins.
    assert "outcome:echo-crosstype" in node_ids, "echo-crosstype missing from nodes"
    # Cross-type collision: intent:golf-new exists.
    assert "intent:golf-new" in node_ids, "golf-new missing from nodes"
    # Briefs.
    assert "brief:bravo-delivery" in node_ids, "bravo-delivery brief missing"
    assert "brief:charlie-delivery" in node_ids, "charlie-delivery brief missing"
    # Specs.
    assert "spec:bravo-spec" in node_ids, "bravo-spec missing from nodes"
    # Must NOT be present.
    assert all(
        "foxtrot" not in nid for nid in node_ids
    ), "tombstone foxtrot-tomb must not be a node"
    assert all(
        "_template" not in nid for nid in node_ids
    ), "seeded brief template must not be a node"


def test_derive_kind_wins_over_level_for_node_id() -> None:
    """derive() assigns outcome:echo-crosstype, not capability:echo-crosstype (AC-0004)."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_MIXED)  # type: ignore[union-attr]
    node_ids = {n["id"] for n in result["nodes"]}
    assert "outcome:echo-crosstype" in node_ids
    assert "capability:echo-crosstype" not in node_ids


def test_derive_dangling_parent_is_refused_edge() -> None:
    """derive() over dangling/ returns a refused edge with state 'dangling' (AC-0007)."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "dangling")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "dangling"]
    assert refused, "expected at least one dangling refused edge"


def test_derive_retired_target_is_refused_edge() -> None:
    """derive() over retired_target/ returns a refused edge with state 'retired_target'."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "retired_target")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "retired_target"]
    assert refused, "expected at least one retired_target refused edge"


def test_derive_kind_mismatch_is_refused_edge() -> None:
    """derive() over kind_mismatch/ returns a refused edge with state 'kind_mismatch'."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "kind_mismatch")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "kind_mismatch"]
    assert refused, "expected at least one kind_mismatch refused edge"


def test_derive_out_of_type_is_refused_edge() -> None:
    """derive() over out_of_type/ returns a refused edge with state 'out_of_type'."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "out_of_type")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "out_of_type"]
    assert refused, "expected at least one out_of_type refused edge"


def test_derive_multiple_values_is_refused_edge() -> None:
    """derive() over multiple_values/ returns a refused edge with state 'multiple_values'."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "multiple_values")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "multiple_values"]
    assert refused, "expected at least one multiple_values refused edge"


def test_derive_cycle_is_refused_edge() -> None:
    """derive() over cycle/ returns refused edges with state 'cycle' (AC-0043)."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "cycle")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "cycle"]
    # At minimum: self-cycle and one from the 2-member cycle.
    assert len(refused) >= 2, f"expected at least 2 cycle refused edges, got {refused}"


def test_derive_unparseable_is_refused_edge() -> None:
    """derive() over unparseable/ returns refused edges with state 'unparseable'."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "unparseable")  # type: ignore[union-attr]
    refused = [e for e in result["edges"] if e.get("state") == "unparseable"]
    assert len(refused) >= 3, f"expected at least 3 unparseable refused edges, got {refused}"


def test_derive_refused_edge_leaves_other_nodes_intact() -> None:
    """A refused edge leaves every other node and edge in the result (AC-0008)."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_NEG / "dangling")  # type: ignore[union-attr]
    # The intent node must still be present even though its parent edge is refused.
    node_ids = {n["id"] for n in result["nodes"]}
    assert "intent:dangling-test" in node_ids, "dangling-test node missing"


def test_derive_fails_with_code_on_malformed_utf8() -> None:
    """derive() raises an exception with .code == 'malformed_record' for invalid UTF-8."""
    _skip_if_module_absent()
    with pytest.raises(Exception) as exc_info:
        ig.derive(_FIXTURE_NEG / "malformed_record_utf8")  # type: ignore[union-attr]
    exc = exc_info.value
    assert hasattr(exc, "code"), f"exception must carry .code; got: {exc}"
    assert exc.code == "malformed_record", f"expected malformed_record, got: {exc.code}"


def test_derive_fails_with_code_on_bad_slug() -> None:
    """derive() raises an exception with .code == 'malformed_record' for bad Slug."""
    _skip_if_module_absent()
    with pytest.raises(Exception) as exc_info:
        ig.derive(_FIXTURE_NEG / "malformed_record_bad_slug")  # type: ignore[union-attr]
    exc = exc_info.value
    assert hasattr(exc, "code"), f"exception must carry .code; got: {exc}"
    assert exc.code == "malformed_record", f"expected malformed_record, got: {exc.code}"


def test_derive_fails_with_code_on_duplicate_identity() -> None:
    """derive() raises an exception with .code == 'duplicate_identity'."""
    _skip_if_module_absent()
    with pytest.raises(Exception) as exc_info:
        ig.derive(_FIXTURE_NEG / "duplicate_identity")  # type: ignore[union-attr]
    exc = exc_info.value
    assert hasattr(exc, "code"), f"exception must carry .code; got: {exc}"
    assert exc.code == "duplicate_identity", f"expected duplicate_identity, got: {exc.code}"


def test_derive_none_parent_produces_no_edge() -> None:
    """A 'none' Parent intent: (with or without comment) produces no edge (AC-0006)."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_MIXED)  # type: ignore[union-attr]
    # india-none and juliet-done both have 'none' parents; neither should have a parent edge.
    for node in result["nodes"]:
        nid = node.get("id", "")
        if nid in ("intent:india-none", "intent:juliet-done"):
            parent_edges = [
                e for e in result["edges"]
                if e.get("from") == nid and e.get("field") == "Parent intent"
            ]
            assert not parent_edges, (
                f"{nid} must have no parent edge for 'none' value; got: {parent_edges}"
            )


def test_derive_brief_parent_inside_html_comment_is_read() -> None:
    """Brief Parent intent: inside multi-line HTML comment is parsed by the resolver's rule."""
    _skip_if_module_absent()
    result = ig.derive(_FIXTURE_MIXED)  # type: ignore[union-attr]
    # brief:hidden-parent's parent should be resolved (outcome:charlie-out).
    edges = [
        e for e in result["edges"]
        if e.get("from") == "brief:hidden-parent"
    ]
    assert edges, "brief:hidden-parent must have a parent edge (Parent intent: in HTML comment)"
    assert any(e.get("to") == "outcome:charlie-out" for e in edges), (
        "brief:hidden-parent's parent must resolve to outcome:charlie-out"
    )
