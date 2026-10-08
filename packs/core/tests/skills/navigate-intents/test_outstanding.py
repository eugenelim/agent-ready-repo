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


@pytest.mark.parametrize(
    "corpus_name",
    [
        "dangling",
        "retired_target",
        "kind_mismatch",
        "out_of_type",
        "multiple_values",
        "cycle",
        "unparseable",
        "brief_parent_malformed",
        "brief_parent_unsafe",
        "brief_parent_ambiguous",
        "brief_parent_repair",
        "brief_parent_unrecognized",
        "no_decomposed",
        "spec_route",
        "two_briefs",
    ],
)
def test_outstanding_matches_manifest_over_negative_corpus(corpus_name: str) -> None:
    """outstanding set equals expected-outstanding.json for non-failing negative corpora (AC-0058)."""
    _skip_if_module_absent()
    corpus = _FIXTURE_NEG / corpus_name
    expected = _read_manifest(corpus)
    result, code = nav.run_query(  # type: ignore[union-attr]
        corpus, ["query", "--operation", "outstanding"]
    )
    assert code == 0, f"outstanding failed for {corpus_name}: {result}"
    assert result["status"] == "ok"
    # Extract outstanding node ids from result.
    items = result.get("items", [])
    returned_ids = sorted(item["id"] for item in items)
    assert returned_ids == expected, (
        f"outstanding mismatch for {corpus_name}:\n"
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
    items = result.get("items", [])
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
    items = result.get("items", [])
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
    items = result.get("items", [])
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
