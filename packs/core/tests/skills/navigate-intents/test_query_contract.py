"""Contract tests for the navigate-intents query surface.

These tests encode the query envelope and operation contract (spec.md §§ Query
surface and Derivation and resolution). They are frozen red in T1 and turned
green when T3 implements navigate_intents.run_query().

Every test that calls run_query must fail ONLY because the module is absent.
No syntax errors, no fixture errors, and no fixture-shape failures are acceptable.

run_query interface (as the plan's CLI maps to):
  navigate_intents.run_query(root: pathlib.Path, argv: list[str]) -> tuple[dict | str, int]

Exit codes: 0 on status:ok, 1 on status:error, 2 for argument-parse errors.
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
    """Load navigate_intents by path under a pack-and-skill-qualified name."""
    module_path = _SCRIPTS / "navigate_intents.py"
    spec = importlib.util.spec_from_file_location(
        "core_navigate_intents_navigate_intents", module_path
    )
    if spec is None or spec.loader is None:
        pytest.fail(f"navigate_intents.py not found at {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["core_navigate_intents_navigate_intents"] = mod
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
# Contract tests — fail only because module is absent in T1
# ---------------------------------------------------------------------------


def test_summary_envelope_has_required_fields() -> None:
    """summary response carries schema, boundary, query, provenance, status (AC-0012)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    assert code == 0
    for field in ("schema", "boundary", "query", "provenance", "status"):
        assert field in result, f"summary response missing '{field}'"
    assert result["schema"] == "intent-navigation.query.v1"
    assert result["status"] == "ok"


def test_summary_has_delivery_field_when_ok() -> None:
    """A status:ok response carries a delivery field (AC-0012)."""
    _skip_if_module_absent()
    result, _ = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    assert "delivery" in result, "status:ok response must carry 'delivery'"


def test_error_response_has_no_delivery_field() -> None:
    """A status:error response carries no delivery field (AC-0012)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "unknown_operation_xyz"]
    )
    assert result["status"] == "error"
    assert "delivery" not in result, "status:error response must not carry 'delivery'"


def test_unknown_operation_returns_error() -> None:
    """An unrecognized operation name returns error with unknown_operation code (AC-0013)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "not_a_real_op"]
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "unknown_operation"
    assert code == 1


def test_record_not_found_returns_error() -> None:
    """record with a non-existent identity returns not_found (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "record", "--id", "intent:doesnt-exist"]
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "not_found"
    assert code == 1


def test_record_returns_intent_node_fields() -> None:
    """record for a live intent returns node id, path, Level, Kind, Status (AC-0072)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "record", "--id", "capability:alpha-cap"]
    )
    assert code == 0
    assert result["status"] == "ok"


def test_ancestors_from_bravo_feat() -> None:
    """ancestors for bravo-feat returns capability:alpha-cap in the chain (AC-0073)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "ancestors", "--id", "intent:bravo-feat"]
    )
    assert code == 0
    assert result["status"] == "ok"


def test_search_with_invalid_selector_key_returns_error() -> None:
    """search with an unknown selector key returns invalid_selector (AC-0015)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "search", "--selectors", '{"not_a_key": "x"}'],
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_selector"
    assert code == 1


def test_tree_depth_below_zero_returns_error() -> None:
    """tree with --depth -1 returns invalid_depth (AC-0038)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--depth", "-1"]
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_depth"
    assert code == 1


def test_query_input_too_large_whole_operation_fails() -> None:
    """An intent over 1 MB causes the operation to fail with input_too_large (AC-0009)."""
    from navigate_intents_fixture_builders import build_input_too_large_corpus
    _skip_if_module_absent()

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_path = pathlib.Path(td)
        root = build_input_too_large_corpus(tmp_path)
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"]
        )
        assert result["status"] == "error"
        assert result["error"]["code"] == "input_too_large"
        assert code == 1


def test_query_duplicate_identity_whole_operation_fails() -> None:
    """Duplicate node identity causes summary to fail with duplicate_identity (AC-0009)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "duplicate_identity", ["query", "--operation", "summary"]
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "duplicate_identity"
    assert code == 1


def test_query_malformed_record_utf8_whole_operation_fails() -> None:
    """Invalid UTF-8 causes summary to fail with malformed_record (AC-0009)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "malformed_record_utf8", ["query", "--operation", "summary"]
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "malformed_record"
    assert code == 1


def test_body_bytes_unchanged_by_body_edit() -> None:
    """Changing only body bytes leaves query JSON byte-identical (AC-0002)."""
    import shutil
    import tempfile

    _skip_if_module_absent()

    def _stripped(result: dict) -> dict:
        """Remove provenance.generated_at for comparison."""
        import copy
        r = copy.deepcopy(result)
        if "provenance" in r:
            r["provenance"].pop("generated_at", None)
        return r

    with tempfile.TemporaryDirectory() as td:
        root1 = pathlib.Path(td) / "corpus1"
        root2 = pathlib.Path(td) / "corpus2"
        shutil.copytree(str(_FIXTURE_MIXED), str(root1))
        shutil.copytree(str(_FIXTURE_MIXED), str(root2))

        # Append body text to one spec file in corpus2 (below the ## heading).
        spec2 = root2 / "docs" / "specs" / "bravo-spec" / "spec.md"
        original = spec2.read_text(encoding="utf-8")
        spec2.write_text(original + "\n\nAdded body text only.\n", encoding="utf-8")

        r1, _ = nav.run_query(root1, ["query", "--operation", "summary"])  # type: ignore[union-attr]
        r2, _ = nav.run_query(root2, ["query", "--operation", "summary"])  # type: ignore[union-attr]

        assert _stripped(r1) == _stripped(r2), (
            "Query results differ after body-only edit; preamble parsing must stop at '## '"
        )
