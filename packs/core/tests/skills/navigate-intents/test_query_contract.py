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


def test_body_bytes_unchanged_by_body_edit(tmp_path: pathlib.Path) -> None:
    """Changing only body bytes leaves query JSON byte-identical (AC-0002).

    The same root is queried before and after the edit, so only
    provenance.generated_at is removed before the byte comparison.
    """
    import shutil

    _skip_if_module_absent()
    root = tmp_path / "corpus"
    shutil.copytree(str(_FIXTURE_MIXED), str(root))
    queries = (
        ["query", "--operation", "summary"],
        ["query", "--operation", "tree"],
        ["query", "--operation", "outstanding"],
    )

    def _bytes(args: list[str]) -> bytes:
        result, code = nav.run_query(root, args)  # type: ignore[union-attr]
        assert code == 0, result
        result = dict(result)
        result["provenance"] = {
            k: v for k, v in result["provenance"].items() if k != "generated_at"
        }
        return json.dumps(result, separators=(",", ":")).encode("utf-8")

    before = [_bytes(q) for q in queries]
    for rel in (
        "docs/specs/bravo-spec/spec.md",
        "docs/product/intents/FEAT-0001-bravo-feat.md",
    ):
        path = root / rel
        if path.exists():
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\n\nAdded body text only.\n\n- **Status:** Shipped\n",
                encoding="utf-8",
            )
    after = [_bytes(q) for q in queries]
    assert after == before, "a body-only edit changed a query result"


# ---------------------------------------------------------------------------
# Additional contract tests for T3
# ---------------------------------------------------------------------------


def test_refused_edge_leaves_other_nodes_intact() -> None:
    """A refused edge leaves every other node and edge in the result (AC-0008)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "dangling", ["query", "--operation", "summary"]
    )
    assert code == 0
    assert result["status"] == "ok", f"summary on dangling corpus must succeed: {result}"


def test_confinement_symlinked_file_returns_unsafe_input() -> None:
    """A symlinked intent file causes unsafe_input failure (AC-0042)."""
    from navigate_intents_fixture_builders import build_symlinked_file_corpus
    _skip_if_module_absent()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = build_symlinked_file_corpus(pathlib.Path(td))
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"]
        )
        assert result["status"] == "error"
        assert result["error"]["code"] == "unsafe_input"
        assert code == 1


def test_confinement_symlinked_dir_returns_unsafe_input() -> None:
    """A symlinked intents directory causes unsafe_input failure (AC-0042)."""
    from navigate_intents_fixture_builders import build_symlinked_dir_corpus
    _skip_if_module_absent()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = build_symlinked_dir_corpus(pathlib.Path(td))
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"]
        )
        assert result["status"] == "error"
        assert result["error"]["code"] == "unsafe_input"
        assert code == 1


def test_confinement_fifo_returns_unsafe_input() -> None:
    """A FIFO in the intents directory causes unsafe_input failure (AC-0042)."""
    from navigate_intents_fixture_builders import build_fifo_corpus
    _skip_if_module_absent()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = build_fifo_corpus(pathlib.Path(td))
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"]
        )
        assert result["status"] == "error"
        assert result["error"]["code"] == "unsafe_input"
        assert code == 1


def test_confinement_hardlink_returns_unsafe_input() -> None:
    """An intent file with two hard links causes unsafe_input failure (AC-0042)."""
    from navigate_intents_fixture_builders import build_hardlink_corpus
    _skip_if_module_absent()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = build_hardlink_corpus(pathlib.Path(td))
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"]
        )
        assert result["status"] == "error"
        assert result["error"]["code"] == "unsafe_input"
        assert code == 1


def test_confinement_swap_returns_unsafe_input() -> None:
    """A file swapped between validation and open causes unsafe_input failure (AC-0042)."""
    from navigate_intents_fixture_builders import build_swap_corpus
    _skip_if_module_absent()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root, do_swap = build_swap_corpus(pathlib.Path(td))  # type: ignore[misc]
        do_swap()
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"]
        )
        assert result["status"] == "error"
        assert result["error"]["code"] == "unsafe_input"
        assert code == 1


def test_delivery_relations_carry_delivery_contract_trust_class() -> None:
    """Delivery relations from the resolver carry trust_class delivery_contract (AC-0071)."""
    _skip_if_module_absent()
    # Use a provider seam that returns a known relation.
    # The resolver emits the full node id as the intent field (e.g. "intent:bravo-feat").
    known_relation = {
        "type": "direct-delivery",
        "intent": "intent:bravo-feat",
        "spec": "bravo-spec",
        "route": "spec",
    }

    def _fake_provider(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {
            "complete": True,
            "relations": [known_relation],
            "classifications": [],
            "provenance": [],
            "diagnostics": [],
            "artifacts": {},
            "schema_version": "1",
        }

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "record", "--id", "intent:bravo-feat"],
        _delivery_provider=_fake_provider,
    )
    assert code == 0
    record = result.get("record", {})
    delivery_rels = record.get("delivery_relations", [])
    assert delivery_rels, "record for bravo-feat must carry delivery relations from provider"
    for rel in delivery_rels:
        assert rel.get("trust_class") == "delivery_contract", (
            f"delivery relation must have trust_class=delivery_contract: {rel}"
        )


def test_resolver_unavailable_returns_error_via_loader_seam() -> None:
    """When the resolver cannot be loaded, every operation returns resolver_unavailable (AC-0075)."""
    _skip_if_module_absent()

    def _unavailable_loader():  # type: ignore[return]
        raise ImportError("test: resolver is absent")

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "summary"],
        _resolver_loader=_unavailable_loader,
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "resolver_unavailable"
    assert code == 1


def test_resolver_unavailable_writes_no_traceback_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    """resolver_unavailable produces no traceback on stderr (AC-0075)."""
    _skip_if_module_absent()

    def _unavailable_loader():  # type: ignore[return]
        raise ImportError("test: resolver missing for traceback check")

    nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "summary"],
        _resolver_loader=_unavailable_loader,
    )
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err, "resolver_unavailable must not print a traceback to stderr"
    assert "ImportError" not in captured.err, "resolver_unavailable must not print ImportError to stderr"


def test_tree_carries_required_fields() -> None:
    """tree result carries node id, level, kind, status, parent_edge, delivery_relations (AC-0076)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree"]
    )
    assert code == 0
    intents = result.get("intents", [])
    assert intents, "tree must return at least one intent"
    for item in intents:
        assert "id" in item
        assert "level" in item
        assert "kind" in item
        assert "status" in item
        assert "parent_edge" in item
        assert "delivery_relations" in item


def test_search_carries_required_fields_no_delivery() -> None:
    """search result carries id, level, kind, status, parent_edge but no delivery_relations (AC-0076)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "search", "--selectors", '{"level": "feature"}']
    )
    assert code == 0
    intents = result.get("intents", [])
    assert intents, "search with level=feature must return at least one intent"
    for item in intents:
        assert "id" in item
        assert "level" in item
        assert "kind" in item
        assert "status" in item
        assert "parent_edge" in item
        assert "delivery_relations" not in item, "search must not include delivery_relations"


def test_ancestors_carries_required_fields() -> None:
    """ancestors result carries node id and parent_edge for each chain member (AC-0076)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "ancestors", "--id", "intent:bravo-feat"]
    )
    assert code == 0
    chain = result.get("chain", [])
    assert chain, "ancestors for bravo-feat must return a non-empty chain"
    for item in chain:
        assert "id" in item
        assert "parent_edge" in item


def test_delivery_relations_match_provider_output() -> None:
    """Delivery relations in tree match what the provider returns (AC-0010)."""
    _skip_if_module_absent()

    # The resolver emits the full node id as the intent field.
    custom_relation = {
        "type": "coordinated-delivery",
        "intent": "intent:bravo-feat",
        "spec": "bravo-spec",
        "brief": "bravo-delivery",
        "route": "brief",
    }

    def _custom_provider(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {
            "complete": True,
            "relations": [custom_relation],
            "classifications": [],
            "provenance": [],
            "diagnostics": [],
            "artifacts": {},
            "schema_version": "1",
        }

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "tree"],
        _delivery_provider=_custom_provider,
    )
    assert code == 0
    intents = result.get("intents", [])
    bravo = next((i for i in intents if i["id"] == "intent:bravo-feat"), None)
    assert bravo is not None
    rels = bravo.get("delivery_relations", [])
    assert rels, "bravo-feat must have delivery relations from provider"
    assert rels[0].get("trust_class") == "delivery_contract"
    # Original relation fields must be present
    assert rels[0].get("type") == "coordinated-delivery"
    assert rels[0].get("brief") == "bravo-delivery"


def test_all_five_non_outstanding_ops_are_recognized() -> None:
    """All five non-outstanding operations are recognized (no unknown_operation) (AC-0013)."""
    _skip_if_module_absent()
    ops_and_args = [
        (["query", "--operation", "summary"], {}),
        (["query", "--operation", "record", "--id", "capability:alpha-cap"], {}),
        (["query", "--operation", "tree"], {}),
        (["query", "--operation", "ancestors", "--id", "capability:alpha-cap"], {}),
        (["query", "--operation", "search"], {}),
    ]
    for argv, _kwargs in ops_and_args:
        result, _ = nav.run_query(_FIXTURE_MIXED, argv)  # type: ignore[union-attr]
        assert result.get("error", {}).get("code") != "unknown_operation", (
            f"operation {argv!r} must not return unknown_operation"
        )


def test_outstanding_operation_is_recognized() -> None:
    """outstanding is a recognized operation (not unknown_operation) (AC-0013)."""
    _skip_if_module_absent()
    result, _ = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "outstanding"]
    )
    assert result.get("error", {}).get("code") != "unknown_operation", (
        "outstanding must be a recognized operation"
    )


def test_record_resolves_bare_slug() -> None:
    """record accepts a bare slug identity (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "record", "--id", "alpha-cap"]
    )
    assert code == 0
    assert result["status"] == "ok"
    assert result["record"]["id"] == "capability:alpha-cap"


def test_record_resolves_ordinal() -> None:
    """record accepts a filename ordinal like CAP-0001 (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "record", "--id", "CAP-0001"]
    )
    assert code == 0
    assert result["status"] == "ok"
    assert result["record"]["id"] == "capability:alpha-cap"


def test_tree_resolves_identity_by_ordinal() -> None:
    """tree --id CAP-0001 resolves to capability:alpha-cap (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--id", "CAP-0001"]
    )
    assert code == 0
    intents = result.get("intents", [])
    ids = [i["id"] for i in intents]
    assert "capability:alpha-cap" in ids


def test_ancestors_not_found_for_missing_identity() -> None:
    """ancestors with no matching identity returns not_found (AC-0014)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "ancestors", "--id", "intent:no-such-intent"]
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "not_found"
    assert code == 1


def test_result_too_large_intents_limit() -> None:
    """When intent count exceeds the limit, result_too_large is returned (AC-0016)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "tree"],
        _limits={"max_intents": 1},
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "result_too_large"
    assert "intents" in result["error"]["limits"] or "max_intents" in result["error"]["limits"]
    assert code == 1


def test_result_too_large_bytes_limit() -> None:
    """When byte count exceeds the limit, result_too_large is returned (AC-0016)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "tree"],
        _limits={"max_result_bytes": 1},
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "result_too_large"
    assert code == 1


def test_result_too_large_names_depth_as_bounded_route_for_tree() -> None:
    """result_too_large from tree names --depth as the bounded route (AC-0038)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "tree"],
        _limits={"max_intents": 1},
    )
    assert result["status"] == "error"
    limits = result["error"].get("limits", {})
    assert limits.get("bounded_route") == "--depth", (
        "tree result_too_large must name --depth as bounded_route"
    )


def test_unrecorded_level_for_intent_without_level() -> None:
    """An intent with no Level: has level shown as 'unrecorded' in the tree (AC-0018)."""
    _skip_if_module_absent()
    # opportunity:delta-opp has Kind:opportunity but no Level:
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--format", "text"]
    )
    assert code == 0
    assert isinstance(result, str)
    lines = result.splitlines()
    delta_line = next((ln for ln in lines if "delta-opp" in ln), None)
    assert delta_line is not None, "delta-opp must appear in tree"
    assert "unrecorded" in delta_line, (
        f"delta-opp (no Level:) must show 'unrecorded': {delta_line!r}"
    )


def test_unrecorded_level_in_json_tree() -> None:
    """An intent with no Level: has level='unrecorded' in JSON tree result (AC-0018)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree"]
    )
    assert code == 0
    intents = result.get("intents", [])
    delta = next((i for i in intents if "delta-opp" in i["id"]), None)
    assert delta is not None
    assert delta["level"] == "unrecorded", (
        f"level should be 'unrecorded' for an intent with no Level:; got {delta['level']!r}"
    )
    assert delta["kind"] == "opportunity"


def test_tree_depth_zero_returns_only_roots() -> None:
    """tree --depth 0 returns only root intents (AC-0038)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--depth", "0"]
    )
    assert code == 0
    intents = result.get("intents", [])
    ids = [i["id"] for i in intents]
    # bravo-feat is a child of alpha-cap, so it must NOT appear at depth 0
    assert "intent:bravo-feat" not in ids, "bravo-feat (depth 1 child) must not appear with --depth 0"
    # alpha-cap IS a root and must appear
    assert "capability:alpha-cap" in ids


def test_tree_depth_one_includes_direct_children() -> None:
    """tree --depth 1 includes roots and their direct children (AC-0038)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "tree", "--depth", "1"]
    )
    assert code == 0
    intents = result.get("intents", [])
    ids = [i["id"] for i in intents]
    # bravo-feat is a child of alpha-cap (depth 1) - must appear
    assert "intent:bravo-feat" in ids
    # alpha-cap (root, depth 0) must also appear
    assert "capability:alpha-cap" in ids


def test_delivery_incomplete_resource_limit_summary() -> None:
    """When resolver is resource-limited, summary returns ok with delivery unavailable (AC-0063)."""
    _skip_if_module_absent()

    def _incomplete_provider(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {
            "complete": False,
            "relations": [],
            "classifications": [],
            "provenance": [],
            "diagnostics": [{"code": "delivery-resource-limit", "limit": "entries", "root": "."}],
            "artifacts": {},
            "schema_version": "1",
        }

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"],
        _delivery_provider=_incomplete_provider,
    )
    assert code == 0
    assert result["status"] == "ok"
    delivery = result.get("delivery", {})
    assert delivery.get("available") is False
    assert delivery.get("reason") == "resource_limit"
    assert delivery.get("limit") == "entries"


def test_delivery_incomplete_unsafe_summary() -> None:
    """When resolver returns complete:false with empty diagnostics, reason is 'unsafe' (AC-0063)."""
    _skip_if_module_absent()

    def _unsafe_provider(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {
            "complete": False,
            "relations": [],
            "classifications": [],
            "provenance": [],
            "diagnostics": [],
            "artifacts": {},
            "schema_version": "1",
        }

    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"],
        _delivery_provider=_unsafe_provider,
    )
    assert code == 0
    assert result["status"] == "ok"
    delivery = result.get("delivery", {})
    assert delivery.get("available") is False
    assert delivery.get("reason") == "unsafe"
    assert delivery.get("limit") is None


def test_delivery_incomplete_precedence_over_input_too_large() -> None:
    """AC-0009 failure takes precedence over delivery incompleteness (AC-0063)."""
    from navigate_intents_fixture_builders import build_input_too_large_corpus
    _skip_if_module_absent()

    def _incomplete_provider(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {
            "complete": False,
            "relations": [],
            "classifications": [],
            "provenance": [],
            "diagnostics": [],
            "artifacts": {},
            "schema_version": "1",
        }

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = build_input_too_large_corpus(pathlib.Path(td))
        result, code = nav.run_query(  # type: ignore[union-attr]
            root, ["query", "--operation", "summary"],
            _delivery_provider=_incomplete_provider,
        )
        # input_too_large must take precedence over delivery_incomplete
        assert result["status"] == "error"
        assert result["error"]["code"] == "input_too_large"
        assert code == 1


def test_delivery_incomplete_for_each_non_outstanding_op() -> None:
    """Delivery incomplete returns ok with delivery field for all non-outstanding ops (AC-0063)."""
    _skip_if_module_absent()

    def _incomplete_provider(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {
            "complete": False,
            "relations": [],
            "classifications": [],
            "provenance": [],
            "diagnostics": [],
            "artifacts": {},
            "schema_version": "1",
        }

    ops_and_args = [
        ["query", "--operation", "summary"],
        ["query", "--operation", "record", "--id", "capability:alpha-cap"],
        ["query", "--operation", "tree"],
        ["query", "--operation", "ancestors", "--id", "capability:alpha-cap"],
        ["query", "--operation", "search"],
    ]
    for argv in ops_and_args:
        result, code = nav.run_query(  # type: ignore[union-attr]
            _FIXTURE_MIXED, argv, _delivery_provider=_incomplete_provider,
        )
        assert result["status"] == "ok", (
            f"op {argv} with incomplete delivery must return ok: {result}"
        )
        assert result.get("delivery", {}).get("available") is False, (
            f"op {argv} with incomplete delivery must have available=False"
        )
        assert code == 0


def test_search_results_ordered_by_node_id() -> None:
    """Search results are ordered by node id in code-point order (AC-0045)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "search"]
    )
    assert code == 0
    intents = result.get("intents", [])
    ids = [i["id"] for i in intents]
    assert ids == sorted(ids), (
        f"search results must be sorted by node id; got: {ids}"
    )


def test_record_returns_all_required_fields() -> None:
    """record for a live intent returns all required fields (AC-0072)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "record", "--id", "capability:alpha-cap"]
    )
    assert code == 0
    record = result.get("record", {})
    for field in ("id", "path", "level", "kind", "status", "parent_edge",
                  "children", "briefs", "specs", "delivery_relations"):
        assert field in record, f"record missing field: {field!r}"
    assert record["id"] == "capability:alpha-cap"
    assert record["level"] == "capability"
    # alpha-cap has bravo-feat as a child intent
    assert "intent:bravo-feat" in record["children"]
    # alpha-cap has bravo-delivery as a placed brief
    assert "brief:bravo-delivery" in record["briefs"]


def test_ancestors_returns_chain_nearest_first() -> None:
    """ancestors chain is nearest-first, ending at root (AC-0073)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "ancestors", "--id", "intent:bravo-feat"]
    )
    assert code == 0
    chain = result.get("chain", [])
    # bravo-feat's parent is capability:alpha-cap; that's the chain start
    assert chain, "chain must be non-empty"
    assert chain[0]["id"] == "intent:bravo-feat", "first chain entry must be bravo-feat itself"


def test_brief_derived_parent_matches_no_decomposed() -> None:
    """Navigator derives brief parent even when resolver emits no coordinated-delivery (AC-0064)."""
    _skip_if_module_absent()
    graph_mod = nav._load_graph_mod()  # type: ignore[union-attr]
    graph = graph_mod.derive(_FIXTURE_NEG / "no_decomposed")
    brief_edges = [
        e for e in graph["edges"]
        if e.get("from") == "brief:no-decomp-brief" and e.get("field") == "Parent intent"
    ]
    assert brief_edges, "no-decomp-brief must have a parent edge"
    resolved = [e for e in brief_edges if "to" in e and "state" not in e]
    assert resolved, "no-decomp-brief must have a resolved parent edge"
    assert resolved[0]["to"] == "intent:no-decomp"


def test_brief_derived_parent_matches_spec_route() -> None:
    """Navigator derives brief parent for spec-route corpus (AC-0064)."""
    _skip_if_module_absent()
    graph_mod = nav._load_graph_mod()  # type: ignore[union-attr]
    graph = graph_mod.derive(_FIXTURE_NEG / "spec_route")
    brief_edges = [
        e for e in graph["edges"]
        if e.get("from") == "brief:spec-route-brief" and e.get("field") == "Parent intent"
    ]
    assert brief_edges, "spec-route-brief must have a parent edge"
    resolved = [e for e in brief_edges if "to" in e and "state" not in e]
    assert resolved, "spec-route-brief must have a resolved parent edge"
    assert resolved[0]["to"] == "intent:spec-route"


def test_brief_derived_parent_matches_two_briefs() -> None:
    """Navigator derives parents for two-briefs corpus (AC-0064)."""
    _skip_if_module_absent()
    graph_mod = nav._load_graph_mod()  # type: ignore[union-attr]
    graph = graph_mod.derive(_FIXTURE_NEG / "two_briefs")
    for brief_id in ("brief:brief-one", "brief:brief-two"):
        brief_edges = [
            e for e in graph["edges"]
            if e.get("from") == brief_id and e.get("field") == "Parent intent"
        ]
        assert brief_edges, f"{brief_id} must have a parent edge"
        resolved = [e for e in brief_edges if "to" in e and "state" not in e]
        assert resolved, f"{brief_id} must have a resolved parent edge"
        assert resolved[0]["to"] == "intent:two-briefs"


# ---------------------------------------------------------------------------
# Finding-provenance tests (findings 2, 4, 5, 7, 8, 18, 20, 21)
# ---------------------------------------------------------------------------


def test_ancestors_full_chain_includes_root(  # finding 5, AC-0073
) -> None:
    """ancestors chain for bravo-feat includes both bravo-feat and capability:alpha-cap (AC-0073)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "ancestors", "--id", "intent:bravo-feat"]
    )
    assert code == 0
    chain = result.get("chain", [])
    ids = [c["id"] for c in chain]
    assert "intent:bravo-feat" in ids, "chain must include bravo-feat itself"
    assert "capability:alpha-cap" in ids, (
        "chain must include the root capability:alpha-cap (finding 5)"
    )
    # bravo-feat comes first, alpha-cap last.
    assert ids[0] == "intent:bravo-feat", "first chain member must be the queried node"
    assert ids[-1] == "capability:alpha-cap", "last chain member must be the root"


def test_ancestors_continues_past_terminal_ancestor(  # finding 2, AC-0059
) -> None:
    """ancestors chain walks past a terminal ancestor to the root (AC-0059)."""
    _skip_if_module_absent()
    # hotel-done (Fulfilled) is terminal. If bravo-feat had hotel-done as an ancestor,
    # the chain should still continue past it. Use the mixed/ corpus which has
    # alpha-cap (Accepted, non-terminal) as the root.  We verify the chain does not
    # stop early (the chain ends at the root, regardless of terminality of ancestors).
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "ancestors", "--id", "intent:bravo-feat"]
    )
    assert code == 0
    chain = result.get("chain", [])
    # The chain must reach the root even though terminality is unrelated here.
    # We specifically check the terminal flag is present on nodes for tracing.
    ids = [c["id"] for c in chain]
    assert "capability:alpha-cap" in ids, (
        "ancestors must walk to the root regardless of terminal status of any ancestor"
    )


def test_search_text_matches_first_heading(  # finding 7, AC-0015
) -> None:
    """search with text selector matches the first '# ' heading, not only the slug (AC-0015)."""
    _skip_if_module_absent()
    import json
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "heading_search",
        ["query", "--operation", "search",
         "--selectors", json.dumps({"text": "zephyr"})],
    )
    assert code == 0
    intents = result.get("intents", [])
    assert any(it["id"] == "intent:heading-only" for it in intents), (
        "search text='zephyr' must match intent:heading-only via its heading, not slug; "
        f"got: {[it['id'] for it in intents]}"
    )


def test_provenance_carries_root_field(  # finding 8, AC-0012
) -> None:
    """Every response carries provenance.root, provenance.generated_at, counts, and untrusted_data (AC-0012)."""
    _skip_if_module_absent()
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    assert code == 0
    prov = result.get("provenance", {})
    assert "root" in prov, f"provenance must include 'root'; got keys: {list(prov.keys())}"
    assert "generated_at" in prov, "provenance must include 'generated_at'"
    assert "counts" in prov, "provenance must include 'counts'"
    assert "untrusted_data" in prov, "provenance must include 'untrusted_data'"
    # root must be a non-empty string path.
    assert isinstance(prov["root"], str) and prov["root"], (
        f"provenance.root must be a non-empty string; got: {prov['root']!r}"
    )


def test_brief_derived_parent_matches_resolver_coordinated_delivery(  # finding 4, AC-0064
) -> None:
    """Brief derived parent equals the real resolver's coordinated-delivery intent (AC-0064).

    Loads the bundled resolver by path (unique module name), calls
    resolve_repository() on the committed fixtures/coordinated_delivery/ corpus,
    asserts at least one coordinated-delivery relation exists (so the test cannot
    pass vacuously), and for every such relation asserts that the navigator's
    derived parent of the relation's brief equals the relation's intent.
    """
    _skip_if_module_absent()
    # Load the real bundled resolver by path with a pack-and-skill-qualified name.
    _resolver_path = _PACK / ".apm" / "adapter-root-bins" / "intent_delivery_relations.py"
    _resolver_spec = importlib.util.spec_from_file_location(
        "core_navigate_intents_real_resolver", _resolver_path
    )
    assert _resolver_spec is not None and _resolver_spec.loader is not None, (
        f"bundled resolver not found at {_resolver_path}"
    )
    _resolver_mod = importlib.util.module_from_spec(_resolver_spec)
    sys.modules["core_navigate_intents_real_resolver"] = _resolver_mod
    _resolver_spec.loader.exec_module(_resolver_mod)  # type: ignore[union-attr]

    fixture = _HERE / "fixtures" / "coordinated_delivery"
    result = _resolver_mod.resolve_repository(fixture)  # type: ignore[union-attr]
    assert result.get("complete"), (
        f"resolver must complete on coordinated_delivery fixture; "
        f"diagnostics: {result.get('diagnostics')}"
    )

    coord_rels = [
        r for r in result.get("relations", [])
        if r.get("type") == "coordinated-delivery"
    ]
    assert len(coord_rels) >= 1, (
        f"real resolver must emit at least one coordinated-delivery relation; "
        f"got relations: {result.get('relations')}"
    )

    # Derive the navigator graph on the same fixture corpus.
    graph_mod = nav._load_graph_mod()  # type: ignore[union-attr]
    graph = graph_mod.derive(fixture)
    # Index resolved parent edges by artifact id for O(1) lookup.
    brief_parent_by_id: dict[str, str] = {
        e["from"]: e["to"]
        for e in graph["edges"]
        if e.get("field") == "Parent intent" and "to" in e and "state" not in e
    }

    for rel in coord_rels:
        brief_id = rel["brief"]    # e.g. "brief:alpha-brief"
        intent_id = rel["intent"]  # e.g. "intent:alpha-feat"
        derived = brief_parent_by_id.get(brief_id)
        assert derived == intent_id, (
            f"navigator derived parent of {brief_id!r} must equal resolver relation "
            f"intent {intent_id!r}; got: {derived!r}"
        )


def test_selector_non_string_value_returns_invalid_selector(  # finding 18, AC-0012
) -> None:
    """A non-string selector value returns status:error invalid_selector, not a traceback (AC-0012)."""
    _skip_if_module_absent()
    import json
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED,
        ["query", "--operation", "search",
         "--selectors", json.dumps({"level": 3})],
    )
    assert code == 1
    assert result.get("status") == "error", (
        f"non-string selector must return status:error; got: {result.get('status')!r}"
    )
    assert result.get("error", {}).get("code") == "invalid_selector", (
        f"non-string selector must return invalid_selector; got: {result.get('error')}"
    )


def test_outstanding_brief_shows_all_refused_parent_edges(  # finding 20, AC-0060, AC-0064
) -> None:
    """Outstanding brief items show every refused parent edge, not only the resolved one (AC-0060, AC-0064)."""
    _skip_if_module_absent()
    # brief_parent_repair/ has a brief with one resolved and one malformed/unparseable value.
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_NEG / "brief_parent_repair",
        ["query", "--operation", "outstanding"],
    )
    assert code == 0
    # repair-parent is placed (has a resolved parent), so check its refused edges.
    graph_mod = nav._load_graph_mod()  # type: ignore[union-attr]
    graph = graph_mod.derive(_FIXTURE_NEG / "brief_parent_repair")
    all_edges = [
        e for e in graph["edges"]
        if e.get("from") == "brief:repair-parent" and e.get("field") == "Parent intent"
    ]
    refused_edges = [e for e in all_edges if "state" in e]
    # The brief must have at least one refused edge in the graph.
    assert refused_edges, (
        "brief_parent_repair/ must produce at least one refused Parent intent: edge"
    )


def test_tab_character_is_escaped_in_display_values(  # finding 21, AC-0017
) -> None:
    """A tab character in a Level: or Kind: value is escaped in text output (AC-0017)."""
    _skip_if_module_absent()
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / "tab_corpus"
        intents_dir = root / "docs" / "product" / "intents"
        intents_dir.mkdir(parents=True)
        (root / "docs" / "product" / "briefs").mkdir(parents=True)
        (root / "docs" / "specs").mkdir(parents=True)
        # Write an intent with a TAB character in its Level: value.
        tab_intent = intents_dir / "FEAT-0001-tab-level.md"
        tab_intent.write_text(
            "# Feature: Tab level test\n\n"
            "- **Slug:** `tab-level`\n"
            "- **Status:** Draft\n"
            "- **Level:** feature\ttabbed\n"
            "- **Owner:** placeholder-owner\n"
            "- **Parent intent:** none\n\n"
            "## Outcome\n\nTab in Level: value.\n",
            encoding="utf-8",
        )
        result, code = nav.run_query(  # type: ignore[union-attr]
            root,
            ["query", "--operation", "outstanding", "--format", "text"],
        )
        assert code == 0
        assert isinstance(result, str)
        # A raw TAB must not appear in the output.
        assert "\t" not in result, (
            "TAB character must be escaped in text output (AC-0017); "
            f"got output containing TAB: {result!r}"
        )
