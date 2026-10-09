"""Contract tests for the outstanding-work view.

These tests encode the outstanding-work contract (spec.md §§ Outstanding work
and AC-0058). They are frozen red in T1 and turned green when T4 implements
the outstanding operation in navigate_intents.run_query().

Every test that calls run_query must fail ONLY because the module is absent.

AC-0058: over every corpus on which no AC-0009, AC-0042, or AC-0061 failure
applies, the returned outstanding set equals the fixture manifest exactly.
For corpora where these failures apply, the test skips the comparison.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"

_HERE = pathlib.Path(__file__).resolve().parent
_FIXTURE_MIXED = _HERE / "fixtures" / "mixed"
_FIXTURE_NEG = _HERE / "fixtures" / "negative"
_FIXTURES = _HERE / "fixtures"

# Corpora where the whole operation fails (AC-0009/AC-0042 apply).
# Outstanding comparison is skipped for these per AC-0058.
_WHOLE_OP_FAIL_CORPORA = frozenset({
    "malformed_record_utf8",
    "malformed_record_bad_slug",
    "duplicate_identity",
})


# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load_navigate_intents():
    module_path = _SCRIPTS / "navigate_intents.py"
    spec = importlib.util.spec_from_file_location(
        "core_navigate_intents_navigate_intents_os", module_path
    )
    if spec is None or spec.loader is None:
        pytest.fail(f"navigate_intents.py not found at {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["core_navigate_intents_navigate_intents_os"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


try:
    nav = _load_navigate_intents()
    _IMPORT_ERROR: Exception | None = None
except Exception as exc:  # noqa: BLE001
    nav = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc


def _skip_if_module_absent() -> None:
    """Fail the test with a clear message when the module is absent (expected in T1)."""
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"navigate_intents.py not found at {_SCRIPTS / 'navigate_intents.py'} — "
            f"expected red in T1 (module absent): {_IMPORT_ERROR}"
        )


def _read_manifest(corpus_path: pathlib.Path) -> list[str]:
    manifest = corpus_path / "expected-outstanding.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return sorted(data["outstanding"])


def _all_outstanding_items(result: dict) -> list:
    """Return the combined list of outstanding items from placed + no_parent groups."""
    return result.get("placed", []) + result.get("no_parent", [])


# ---------------------------------------------------------------------------
# Fixture-shape validators — must PASS in T1
# ---------------------------------------------------------------------------


def test_mixed_manifest_ids_are_valid_node_ids() -> None:
    """expected-outstanding.json in mixed/ contains valid node id formats."""
    manifest = json.loads(
        (_FIXTURE_MIXED / "expected-outstanding.json").read_text(encoding="utf-8")
    )
    valid_prefixes = ("capability:", "outcome:", "opportunity:", "intent:", "brief:", "spec:")
    for node_id in manifest["outstanding"]:
        assert any(node_id.startswith(p) for p in valid_prefixes), (
            f"invalid node id in mixed/ manifest: {node_id!r}"
        )


def test_mixed_manifest_terminal_statuses_excluded() -> None:
    """Terminal intents (hotel-done: Fulfilled, juliet-done: Fulfilled) not in mixed/ manifest."""
    manifest = json.loads(
        (_FIXTURE_MIXED / "expected-outstanding.json").read_text(encoding="utf-8")
    )
    outstanding = set(manifest["outstanding"])
    assert "capability:hotel-done" not in outstanding, "hotel-done (Fulfilled) must not be outstanding"
    assert "intent:juliet-done" not in outstanding, "juliet-done (Fulfilled) must not be outstanding"
    assert "spec:golf-new" not in outstanding, "golf-new spec (Shipped) must not be outstanding"


def test_mixed_manifest_tombstone_excluded() -> None:
    """Tombstone foxtrot-tomb must not appear in mixed/ manifest."""
    manifest = json.loads(
        (_FIXTURE_MIXED / "expected-outstanding.json").read_text(encoding="utf-8")
    )
    outstanding = manifest["outstanding"]
    assert all("foxtrot" not in oid for oid in outstanding), (
        "tombstone foxtrot-tomb must not be in outstanding"
    )


def test_mixed_manifest_seeded_template_excluded() -> None:
    """Seeded brief template must not appear in mixed/ manifest."""
    manifest = json.loads(
        (_FIXTURE_MIXED / "expected-outstanding.json").read_text(encoding="utf-8")
    )
    outstanding = manifest["outstanding"]
    assert all("template" not in oid for oid in outstanding), (
        "seeded brief template must not be in outstanding"
    )


# ---------------------------------------------------------------------------
# Contract tests — fail only because module is absent in T1
# ---------------------------------------------------------------------------


# Corpora where an integrity failure fails the whole operation, so no
# outstanding set exists to compare. Every other corpus with a manifest is
# compared, so a corpus added later cannot be left out of AC-0058.
_WHOLE_OPERATION_FAILURES = frozenset(
    {
        "negative/duplicate_identity",
        "negative/duplicate_slug",
        "negative/malformed_record_bad_slug",
        "negative/malformed_record_utf8",
    }
)
_MANIFEST_CORPORA = sorted(
    path.parent.relative_to(_FIXTURES).as_posix()
    for path in _FIXTURES.glob("**/expected-outstanding.json")
    if path.parent.relative_to(_FIXTURES).as_posix() != "mixed"
)


def test_manifest_corpus_discovery_is_not_vacuous() -> None:
    """Every declared whole-operation failure exists, and the compared set is non-trivial."""
    assert set(_MANIFEST_CORPORA) >= _WHOLE_OPERATION_FAILURES
    assert len(set(_MANIFEST_CORPORA) - _WHOLE_OPERATION_FAILURES) >= 20


@pytest.mark.parametrize(
    "corpus",
    [
        manifest.parent
        for manifest in sorted(_FIXTURES.glob("**/expected-outstanding.json"))
        if manifest.parent.relative_to(_FIXTURES).as_posix()
        in set(_MANIFEST_CORPORA) - _WHOLE_OPERATION_FAILURES
    ],
    ids=lambda path: path.relative_to(_FIXTURES).as_posix(),
)
def test_outstanding_matches_manifest_over_negative_corpus(corpus: pathlib.Path) -> None:
    """outstanding set equals expected-outstanding.json for non-failing negative corpora (AC-0058)."""
    _skip_if_module_absent()
    expected = _read_manifest(corpus)
    result, code = nav.run_query(  # type: ignore[union-attr]
        corpus, ["query", "--operation", "outstanding"]
    )
    assert code == 0, f"outstanding failed for {corpus.name}: {result}"
    assert result["status"] == "ok"
    # Extract outstanding node ids from result.
    items = _all_outstanding_items(result)
    returned_ids = sorted(item["id"] for item in items)
    assert returned_ids == expected, (
        f"outstanding mismatch for {corpus.name}:\n"
        f"  expected: {expected}\n"
        f"  returned: {returned_ids}"
    )


def test_outstanding_matches_manifest_over_mixed() -> None:
    """outstanding set equals mixed/ expected-outstanding.json exactly (AC-0058)."""
    _skip_if_module_absent()
    expected = _read_manifest(_FIXTURE_MIXED)
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding"]
    )
    assert code == 0
    assert result["status"] == "ok"
    items = _all_outstanding_items(result)
    returned_ids = sorted(item["id"] for item in items)
    assert returned_ids == expected, (
        f"outstanding mismatch for mixed/:\n"
        f"  expected: {expected}\n"
        f"  returned: {returned_ids}"
    )


def test_outstanding_fails_for_whole_op_failure_corpus() -> None:
    """outstanding returns status:error for a corpus that triggers AC-0009 (AC-0058 skip)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "malformed_record_utf8",
        ["query", "--operation", "outstanding"],
    )
    # AC-0009 takes precedence; outstanding never returns partial results.
    assert result["status"] == "error"
    assert code == 1


def test_outstanding_no_parent_group_comes_last() -> None:
    """In outstanding --format text, (no parent) group comes last (AC-0045)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    lines = result.splitlines()
    no_parent_lines = [i for i, line in enumerate(lines) if "(no parent)" in line]
    if no_parent_lines:
        # (no parent) group must come after all placed items.
        last_np = max(no_parent_lines)
        # All lines after it must be in the no_parent group (indented) or blank.
        for line in lines[last_np + 1:]:
            assert line.startswith("  ") or not line.strip(), (
                f"Line after '(no parent)' must be indented or blank: {line!r}"
            )


def test_outstanding_from_filters_to_subtree() -> None:
    """outstanding --from <identity> returns only items under that intent (AC-0066)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding", "--from", "capability:alpha-cap"],
    )
    assert code == 0
    assert result["status"] == "ok"
    items = _all_outstanding_items(result)
    # bravo-feat is under alpha-cap, so it should appear.
    ids = {item["id"] for item in items}
    assert "intent:bravo-feat" in ids or "capability:alpha-cap" in ids, (
        "outstanding --from alpha-cap must include bravo-feat or alpha-cap itself"
    )
    # delta-opp is not under alpha-cap, so it must not appear.
    assert "opportunity:delta-opp" not in ids, (
        "outstanding --from alpha-cap must not include delta-opp (different subtree)"
    )


def test_outstanding_item_with_terminal_status_excluded() -> None:
    """Terminal status intents (Fulfilled — date, Fulfilled (date)) are not outstanding."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding"]
    )
    assert code == 0
    items = _all_outstanding_items(result)
    ids = {item["id"] for item in items}
    assert "capability:hotel-done" not in ids, (
        "hotel-done (Fulfilled — date) must not be outstanding"
    )
    assert "intent:juliet-done" not in ids, (
        "juliet-done (Fulfilled (date)) must not be outstanding"
    )


def test_outstanding_text_format_spec_includes_status() -> None:
    """outstanding --format text shows brief:<slug> · <Status> for placed specs/briefs (AC-0062)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    # At least one line should have ' · ' for a brief or spec.
    brief_lines = [ln for ln in result.splitlines() if "brief:" in ln and " · " in ln]
    assert brief_lines, "outstanding text must include brief: lines with ' · ' status separator"


# ---------------------------------------------------------------------------
# AC-0013: outstanding is a valid operation
# ---------------------------------------------------------------------------


def test_outstanding_is_valid_operation() -> None:
    """outstanding is a valid query operation; invalid ops return unknown_operation (AC-0013)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding"]
    )
    assert code == 0
    assert result["status"] == "ok"
    # Confirm the operation set: an unknown operation returns unknown_operation.
    r2, c2 = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "not_a_real_operation"]
    )
    assert c2 == 1
    assert r2["error"]["code"] == "unknown_operation"


# ---------------------------------------------------------------------------
# AC-0014: outstanding --from accepts node id, bare slug, ordinal; not_found
# and ambiguous_identity for unresolvable identities
# ---------------------------------------------------------------------------


def test_outstanding_from_bare_slug() -> None:
    """outstanding --from accepts a bare intent slug (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding", "--from", "alpha-cap"],
    )
    assert code == 0
    assert result["status"] == "ok"
    ids = {item["id"] for item in _all_outstanding_items(result)}
    assert "capability:alpha-cap" in ids, (
        "--from alpha-cap (bare slug) must include capability:alpha-cap itself"
    )
    assert "opportunity:delta-opp" not in ids, (
        "--from alpha-cap must not include delta-opp (different subtree)"
    )


def test_outstanding_from_ordinal() -> None:
    """outstanding --from accepts a filename ordinal such as CAP-0001 (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding", "--from", "CAP-0001"],
    )
    assert code == 0
    assert result["status"] == "ok"
    ids = {item["id"] for item in _all_outstanding_items(result)}
    # CAP-0001 resolves to capability:alpha-cap
    assert "capability:alpha-cap" in ids, (
        "--from CAP-0001 (ordinal) must resolve to capability:alpha-cap"
    )


def test_outstanding_from_not_found() -> None:
    """outstanding --from returns not_found for an unknown identity (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding", "--from", "intent:no-such-slug"],
    )
    assert code == 1
    assert result["error"]["code"] == "not_found"


def test_outstanding_from_ambiguous_identity() -> None:
    """outstanding --from returns ambiguous_identity when ordinal matches multiple files (AC-0014)."""
    _skip_if_module_absent()
    # ambiguous_ordinal corpus has two files sharing FEAT-0001 prefix.
    corpus = _FIXTURE_NEG / "ambiguous_ordinal"
    result, code = nav.run_query(  # type: ignore[union-attr]
        corpus,
        ["query", "--operation", "outstanding", "--from", "FEAT-0001"],
    )
    assert code == 1
    assert result["error"]["code"] == "ambiguous_identity"


# ---------------------------------------------------------------------------
# AC-0045: outstanding items in code-point order; (no parent) comes last
# ---------------------------------------------------------------------------


def test_outstanding_root_items_ordered_by_node_id() -> None:
    """Root-level outstanding items are ordered by node id in code-point order (AC-0045)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding", "--format", "text"],
    )
    assert code == 0
    assert isinstance(result, str)
    # Root-level lines have no leading spaces and are not the (no parent) header.
    root_lines = [
        ln for ln in result.splitlines()
        if ln and not ln.startswith(" ") and "(no parent)" not in ln
    ]
    root_ids = [ln.split(" · ")[0].strip() for ln in root_lines]
    assert root_ids == sorted(root_ids), (
        f"Root outstanding items must be in code-point order; got: {root_ids}"
    )


# ---------------------------------------------------------------------------
# AC-0059: spec items carry a placements list with pointer_field and parent_edge
# ---------------------------------------------------------------------------


def test_outstanding_spec_has_placements_structure() -> None:
    """Spec items carry a placements list; bravo-spec has Brief + Discovery placements (AC-0059)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding"]
    )
    assert code == 0
    items = _all_outstanding_items(result)
    bravo = next((it for it in items if it["id"] == "spec:bravo-spec"), None)
    assert bravo is not None, "spec:bravo-spec must be in outstanding"
    placements = bravo.get("placements", [])
    assert len(placements) == 2, (
        f"bravo-spec must have 2 placements (Brief + Discovery); got {len(placements)}"
    )
    pointer_fields = {p["pointer_field"] for p in placements}
    assert pointer_fields == {"Brief", "Discovery"}, (
        f"placements must cover Brief and Discovery; got {pointer_fields}"
    )
    for p in placements:
        assert "parent_edge" in p, f"placement missing parent_edge: {p}"
        assert "ancestors" in p, f"placement missing ancestors: {p}"
        assert "_in_no_parent" not in p, "internal _in_no_parent must not appear in JSON output"


# ---------------------------------------------------------------------------
# AC-0060: (no parent) group appears for refused parent edges
# ---------------------------------------------------------------------------


def test_outstanding_no_parent_group_in_dangling_corpus() -> None:
    """(no parent) group appears in outstanding text when a refused parent edge exists (AC-0060)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "dangling",
        ["query", "--operation", "outstanding", "--format", "text"],
    )
    assert code == 0
    assert isinstance(result, str)
    assert "(no parent)" in result, (
        "outstanding text must include '(no parent)' group when a refused parent edge exists"
    )
    # dangling-test is placed under (no parent) group.
    after_no_parent = result.split("(no parent)", 1)[1]
    assert "dangling-test" in after_no_parent, (
        "intent:dangling-test must appear under the (no parent) group"
    )


# ---------------------------------------------------------------------------
# AC-0065: (no parent) group carries no parent edge; items in it have refused edges
# ---------------------------------------------------------------------------


def test_outstanding_no_parent_items_have_refused_parent_edges() -> None:
    """Items in the (no parent) group have refused parent edges; ancestors is empty (AC-0065)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "dangling", ["query", "--operation", "outstanding"]
    )
    assert code == 0
    items = _all_outstanding_items(result)
    dangling_item = next((it for it in items if it["id"] == "intent:dangling-test"), None)
    assert dangling_item is not None, "intent:dangling-test must be in outstanding items"
    parent_edge = dangling_item.get("parent_edge", {})
    # Refused edge: has state, not to.
    assert "state" in parent_edge, (
        "dangling-test's parent_edge must have state (refused edge, not resolved)"
    )
    assert "to" not in parent_edge, (
        "dangling-test's parent_edge must not have to (refused edges carry no to)"
    )
    # No resolved parent chain.
    assert dangling_item.get("ancestors", []) == [], (
        "dangling-test must have empty ancestors (no resolved parent)"
    )


# ---------------------------------------------------------------------------
# AC-0061 / AC-0063: delivery_incomplete when resolver is incomplete;
# other operations return ok with delivery:available=false
# ---------------------------------------------------------------------------


def test_outstanding_delivery_incomplete_when_resolver_incomplete() -> None:
    """outstanding returns delivery_incomplete when the delivery resolver is incomplete (AC-0061)."""
    _skip_if_module_absent()

    def _fake_incomplete(root: pathlib.Path) -> dict:
        return {"complete": False, "diagnostics": []}

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding"],
        _delivery_provider=_fake_incomplete,
    )
    assert code == 1
    assert result["error"]["code"] == "delivery_incomplete"


def test_summary_still_ok_when_delivery_incomplete() -> None:
    """summary returns ok with delivery:available=false when resolver incomplete (AC-0063)."""
    _skip_if_module_absent()

    def _fake_incomplete(root: pathlib.Path) -> dict:
        return {"complete": False, "diagnostics": []}

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "summary"],
        _delivery_provider=_fake_incomplete,
    )
    assert code == 0
    assert result["status"] == "ok"
    assert result["delivery"]["available"] is False


def test_outstanding_ac0009_takes_precedence_over_delivery_incomplete() -> None:
    """AC-0009 failure takes precedence over delivery_incomplete for outstanding (AC-0063)."""
    _skip_if_module_absent()

    def _fake_incomplete(root: pathlib.Path) -> dict:
        return {"complete": False, "diagnostics": []}

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "malformed_record_utf8",
        ["query", "--operation", "outstanding"],
        _delivery_provider=_fake_incomplete,
    )
    assert code == 1
    # AC-0009 takes precedence; error code must not be delivery_incomplete.
    assert result["error"]["code"] != "delivery_incomplete", (
        "AC-0009 failure must take precedence over delivery_incomplete"
    )


# ---------------------------------------------------------------------------
# AC-0062: byte-for-byte text output for mixed/ corpus
# ---------------------------------------------------------------------------

_MIXED_OUTSTANDING_TEXT = (
    "(no parent)\n"
    "  capability:alpha-cap · capability · Accepted\n"
    "    brief:bravo-delivery · Executing\n"
    "      spec:bravo-spec · Implementing\n"
    "    intent:bravo-feat · feature · Draft\n"
    "      spec:bravo-spec · Implementing\n"
    "      spec:charlie-spec · Draft\n"
    "  intent:golf-new · feature · Draft\n"
    "  intent:india-none · feature · Accepted\n"
    "  opportunity:delta-opp · unrecorded · opportunity · Draft\n"
    "  outcome:charlie-out · capability · outcome · Accepted\n"
    "    brief:charlie-delivery · Draft\n"
    "    brief:hidden-parent · Draft\n"
    "  outcome:echo-crosstype · capability · outcome · Draft"
)


def test_outstanding_mixed_text_byte_for_byte() -> None:
    """outstanding --format text on mixed/ matches the expected text byte-for-byte (AC-0062)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding", "--format", "text"],
    )
    assert code == 0
    assert isinstance(result, str)
    assert result == _MIXED_OUTSTANDING_TEXT, (
        f"Text output mismatch.\n"
        f"Expected:\n{_MIXED_OUTSTANDING_TEXT!r}\n\n"
        f"Got:\n{result!r}"
    )


# ---------------------------------------------------------------------------
# AC-0066: result_too_large above 512 KiB; --from as bounded route
# ---------------------------------------------------------------------------


def test_outstanding_result_too_large_with_lowered_limit() -> None:
    """outstanding returns result_too_large when byte limit is exceeded (AC-0066)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "outstanding"],
        _limits={"max_result_bytes": 1},
    )
    assert code == 1
    assert result["error"]["code"] == "result_too_large"
    assert result["error"]["limits"].get("bounded_route") == "--from", (
        "result_too_large must name --from as the bounded route"
    )


# ---------------------------------------------------------------------------
# AC-0074: summary.outstanding equals the count of live non-terminal nodes
# ---------------------------------------------------------------------------


def test_summary_outstanding_count_matches_outstanding_items() -> None:
    """summary.outstanding matches len(outstanding items) over mixed/ (AC-0074)."""
    _skip_if_module_absent()
    r_sum, _ = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    r_out, _ = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding"]
    )
    all_items = _all_outstanding_items(r_out)
    assert r_sum["summary"]["outstanding"] == len(all_items), (
        f"summary.outstanding ({r_sum['summary']['outstanding']}) must equal "
        f"len(outstanding items) ({len(all_items)})"
    )
