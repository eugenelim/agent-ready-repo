"""Contract tests for text-tree output format.

These tests encode the tree --format text contract (spec.md § AC-0017, AC-0045,
AC-0046). They are frozen red in T1 and turned green when T3 implements
navigate_intents.run_query() with text tree support.

Every test that calls run_query must fail ONLY because the module is absent.
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


def _load_navigate_intents():
    module_path = _SCRIPTS / "navigate_intents.py"
    spec = importlib.util.spec_from_file_location(
        "core_navigate_intents_navigate_intents_tt", module_path
    )
    if spec is None or spec.loader is None:
        pytest.fail(f"navigate_intents.py not found at {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["core_navigate_intents_navigate_intents_tt"] = mod
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


# ---------------------------------------------------------------------------
# Fixture-shape validators — must PASS in T1
# ---------------------------------------------------------------------------


def test_cycle_fixture_suitable_for_tree_test() -> None:
    """cycle/ fixture has the intent files for tree ordering tests."""
    intents = _FIXTURE_NEG / "cycle" / "docs" / "product" / "intents"
    assert intents.is_dir()
    names = {p.name for p in intents.iterdir() if p.is_file()}
    assert "FEAT-0001-self-cycle.md" in names
    assert "FEAT-0002-cycle-a.md" in names
    assert "FEAT-0003-cycle-b.md" in names


# ---------------------------------------------------------------------------
# Contract tests — fail only because module is absent in T1
# ---------------------------------------------------------------------------


def test_tree_text_first_line_shape_over_mixed() -> None:
    """tree --format text first line is '<depth spaces><node-id> · <Level>' (AC-0017).

    Each root intent is at depth 0 (no leading spaces). The format is:
    '<indent><node-id> · <Level> · [<Kind> · ]<Status>'
    """
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str), "text format must return a string"
    first_line = result.splitlines()[0]
    # First line is a root intent (depth 0 → no leading spaces).
    # Must contain ' · ' separator.
    assert " · " in first_line, f"first line missing ' · ' separator: {first_line!r}"
    # Must not start with spaces (depth 0 intent).
    assert not first_line.startswith(" "), (
        f"first line must not start with spaces (root intent): {first_line!r}"
    )


def test_tree_text_child_intent_indented_two_spaces() -> None:
    """A child intent is indented by two spaces per depth level (AC-0017)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    lines = result.splitlines()
    # bravo-feat's parent is capability:alpha-cap, so bravo-feat is at depth 1 (2 spaces).
    bravo_lines = [ln for ln in lines if "bravo-feat" in ln]
    assert bravo_lines, "bravo-feat must appear in tree output"
    # At depth 1: two leading spaces.
    assert bravo_lines[0].startswith("  "), (
        f"bravo-feat must be indented 2 spaces (depth 1): {bravo_lines[0]!r}"
    )


def test_tree_text_refused_parent_edge_format() -> None:
    """A refused parent edge prints '! refused <state>' one depth deeper (AC-0017)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "dangling", ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    refused_lines = [ln for ln in result.splitlines() if "! refused" in ln]
    assert refused_lines, "tree text must include '! refused' lines for refused edges"


def test_tree_text_ordering_roots_by_node_id() -> None:
    """Roots are ordered by node id in code-point order (AC-0045)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    # Collect root-level lines (no leading spaces, contain ' · ').
    root_lines = [ln for ln in result.splitlines() if ln and not ln.startswith(" ") and " · " in ln]
    # Extract node ids (first token before ' · ').
    root_ids = [ln.split(" · ")[0].strip() for ln in root_lines]
    assert root_ids == sorted(root_ids), (
        f"root intents must be sorted by node id in code-point order; got: {root_ids}"
    )


def test_tree_cycle_fixture_each_intent_appears_once() -> None:
    """In the whole-forest tree, every live intent appears exactly once (AC-0045)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "cycle", ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    lines = result.splitlines()
    # Count occurrences of each intent's slug in the tree lines (not in '! refused').
    for slug in ("self-cycle", "cycle-a", "cycle-b"):
        count = sum(1 for ln in lines if slug in ln and "! refused" not in ln)
        assert count == 1, (
            f"intent {slug} must appear exactly once in tree; appeared {count} times"
        )


# ---------------------------------------------------------------------------
# Additional T3 contract tests
# ---------------------------------------------------------------------------


def test_tree_text_byte_for_byte_mixed() -> None:
    """tree --format text over mixed/ matches expected output byte-for-byte (AC-0017)."""
    _skip_if_module_absent()
    expected = (
        "capability:alpha-cap · capability · Accepted\n"
        "  intent:bravo-feat · feature · Draft\n"
        "capability:hotel-done · capability · Fulfilled — 2026-01-01\n"
        "intent:golf-new · feature · Draft\n"
        "intent:india-none · feature · Accepted\n"
        "intent:juliet-done · feature · Fulfilled (2026-01-01)\n"
        "opportunity:delta-opp · unrecorded · opportunity · Draft\n"
        "outcome:charlie-out · capability · outcome · Accepted\n"
        "outcome:echo-crosstype · capability · outcome · Draft"
    )
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert result == expected, (
        f"text tree does not match expected byte-for-byte.\n"
        f"Got:\n{result!r}\n\nExpected:\n{expected!r}"
    )


def test_tree_text_bidi_controls_escaped() -> None:
    """Bidi and control characters are escaped as [U+XXXX] in text tree output (AC-0017)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "bidi_controls",
        ["query", "--operation", "tree", "--format", "text"],
    )
    assert code == 0
    assert isinstance(result, str)
    # No raw bidi characters must appear in the output
    for char, name in (
        ("‮", "U+202E RLO"),
        ("‎", "U+200E LRM"),
        ("⁦", "U+2066 LRI"),
    ):
        assert char not in result, (
            f"Raw {name} must not appear in text tree output; got: {result!r}"
        )
    # The escaped form must appear
    assert "[U+202E]" in result, f"[U+202E] escape must appear in text tree; got: {result!r}"
    # Full expected line
    expected_line = (
        "intent:bidi-test · feature[U+200E] · outcome[U+2066] · Draft[U+202E]"
    )
    assert result.strip() == expected_line, (
        f"bidi_controls tree line does not match.\nGot:      {result.strip()!r}\nExpected: {expected_line!r}"
    )


def test_tree_text_byte_limit_returns_error() -> None:
    """tree --format text respects the byte limit and returns result_too_large (AC-0046)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "tree", "--format", "text"],
        _limits={"max_result_bytes": 1},
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "result_too_large"
    assert code == 1


def test_tree_text_not_limited_by_intent_count() -> None:
    """tree --format text is exempt from intent/edge count limits (AC-0046)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "tree", "--format", "text"],
        _limits={"max_intents": 1},
    )
    # Setting max_intents=1 on text format must NOT trigger result_too_large
    assert code == 0
    assert isinstance(result, str), (
        "text tree must succeed even when max_intents=1 (text exempt from count limits)"
    )
