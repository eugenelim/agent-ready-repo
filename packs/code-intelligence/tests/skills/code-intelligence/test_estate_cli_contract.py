"""Execute the real `wicked-estate` CLI and assert the shapes the pack documents.

Every other suite in this pack is static: it compares the pack's prose to an
allowlist the same author transcribed, which cannot catch a transcription
error. This suite closes that loop by running the binary against a real index
and reading what actually comes back.

It is skipped when `wicked-estate` is absent, so it self-declares as unrun
rather than passing vacuously. To run it:

    cargo install wicked-estate --version 0.21.0 --locked
    pytest packs/code-intelligence/tests/skills/code-intelligence/

The index is built once per session into a temp directory from a purpose-built
three-file micro-repository, so assertions stay deterministic as this
repository changes. Every probe runs against a **copy** of that graph, so a
verb that mutates cannot corrupt the shared fixture.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]

#: A purpose-built micro-repository, written into a temp directory and indexed
#: for real. Two properties make it a better fixture than pointing the indexer
#: at this repository: the assertions do not drift when unrelated files move,
#: and `handle` is deliberately defined twice so the ambiguity `resolve` must
#: report is a property of the fixture rather than a lucky collision.
#:
#: Indexing the pack's own tree was the first attempt and does not work: its
#: runtime payload lives under `.apm/`, and the indexer skips dot-prefixed
#: directories, so only the test files would be seen.
FIXTURE_SOURCES = {
    "core.py": (
        "def helper():\n"
        "    return 1\n"
        "\n"
        "def handle():\n"
        "    return helper()\n"
    ),
    "other.py": (
        "def handle():\n"
        "    return 2\n"
    ),
    "caller.py": (
        "from core import handle\n"
        "\n"
        "def entry():\n"
        "    return handle()\n"
        "\n"
        "def second_caller():\n"
        "    return handle()\n"
    ),
}

BINARY = shutil.which("wicked-estate")

pytestmark = pytest.mark.skipif(
    BINARY is None,
    reason="wicked-estate not installed; run `cargo install wicked-estate --version 0.21.0 --locked`",
)


def run(*args: str, db: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI against a given graph and return the completed process."""
    return subprocess.run(
        [BINARY, *args, "--db", str(db)],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


@pytest.fixture(scope="session")
def indexed_graph(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Write the micro-repository and index it once for the whole session."""
    workspace = tmp_path_factory.mktemp("estate")
    source = workspace / "src"
    source.mkdir()
    for name, body in FIXTURE_SOURCES.items():
        (source / name).write_text(body, encoding="utf-8")

    db = workspace / "graph.db"
    completed = subprocess.run(
        [BINARY, "index", str(source), "--db", str(db)],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stderr
    assert db.exists()
    return db


@pytest.fixture
def graph(indexed_graph: Path, tmp_path: Path) -> Path:
    """A disposable copy, so a mutating verb cannot touch the session fixture."""
    copy = tmp_path / "graph.db"
    shutil.copy(indexed_graph, copy)
    return copy


@pytest.fixture(scope="session")
def known_symbol(indexed_graph: Path) -> dict:
    """A real symbol resolved from the real index."""
    completed = run("resolve", "handle", "--json", db=indexed_graph)
    hits = json.loads(completed.stdout)
    assert hits, "fixture symbol not found; the indexed subtree may have moved"
    return hits[0]


# ── resolve ────────────────────────────────────────────────────────────────


def test_resolve_json_carries_the_documented_fields(known_symbol: dict) -> None:
    """capability-map.md promises {symbol_id, name, kind, file, line}."""
    assert set(known_symbol) >= {"symbol_id", "name", "kind", "file", "line"}


def test_resolve_reports_ambiguity_rather_than_collapsing_it(graph: Path) -> None:
    """The pack tells agents several hits are a finding; the CLI must give them."""
    hits = json.loads(run("resolve", "handle", "--json", db=graph).stdout)
    assert len(hits) == 2, "`handle` is defined twice in the fixture"


# ── blast radius ───────────────────────────────────────────────────────────


def test_blast_radius_json_top_level_keys(graph: Path, known_symbol: dict) -> None:
    """blast-radius --json carries the eight documented top-level keys including the confidence object.

    0.21.0 adds a ``confidence`` object with ``min``, ``avg``, and ``edge_count``
    over the edges that admitted rows into the result.  The seven structural keys
    from 0.18.0 remain.
    """
    payload = json.loads(run("blast-radius", known_symbol["name"], "--json", db=graph).stdout)
    assert set(payload) == {
        "target",
        "dependents",
        "unresolved",
        "truncated_dependents",
        "searched_depth",
        "depth_horizon_reached",
        "node_cap_reached",
        "confidence",
    }
    conf = payload["confidence"]
    assert set(conf) >= {"min", "avg", "edge_count"}, (
        f"confidence object must carry min, avg, edge_count; got {set(conf)}"
    )


def test_blast_radius_text_evidence_line(graph: Path) -> None:
    """blast-radius text output prints a line starting 'evidence:'.

    The evidence line summarises the edges and confidence used for the result,
    giving a text caller the same signal that --json carries in the confidence
    object.
    """
    result = run("blast-radius", "helper", db=graph)
    assert result.returncode == 0
    assert any(
        line.startswith("evidence:") for line in result.stdout.splitlines()
    ), "blast-radius text output must contain a line starting 'evidence:'"


def test_blast_radius_dependents_have_no_depth_or_confidence(
    graph: Path, known_symbol: dict
) -> None:
    """gaps.md §Impact and §Confidence claim the CLI form omits both. Hold them to it."""
    payload = json.loads(run("blast-radius", known_symbol["name"], "--json", db=graph).stdout)
    assert payload["dependents"], "fixture symbol has no dependents"
    row = payload["dependents"][0]
    assert set(row) == {"id", "name", "kind", "file", "line"}
    assert "depth" not in row
    assert "confidence" not in row


def test_blast_radius_suppresses_staleness_under_json(
    graph: Path, known_symbol: dict
) -> None:
    """evidence.md warns the STALENESS line never reaches a --json caller."""
    stdout = run("blast-radius", known_symbol["name"], "--json", db=graph).stdout
    assert "STALENESS" not in stdout
    json.loads(stdout)  # and the document stays parseable, which is the reason


# ── nodes ──────────────────────────────────────────────────────────────────


def test_nodes_symbol_flag_rejected_and_blast_radius_bogus_rejected(
    graph: Path, known_symbol: dict
) -> None:
    """nodes exits non-zero for an unknown flag, and blast-radius exits non-zero for an unknown flag.

    Strict flag parsing means a command exits 1 on any flag it does not read.
    The pack teaches agents to use resolve for single-symbol lookup, not nodes.
    """
    # nodes does not accept --symbol; in 0.21.0 it exits non-zero
    nodes_result = run("nodes", "--symbol", known_symbol["symbol_id"], "--json", db=graph)
    assert nodes_result.returncode != 0, (
        "nodes must exit non-zero when given --symbol (strict flag parsing)"
    )

    # blast-radius does not accept --bogus; must exit non-zero
    bogus_result = run("blast-radius", "helper", "--bogus", "1", db=graph)
    assert bogus_result.returncode != 0, (
        "blast-radius must exit non-zero for an unknown flag"
    )


# ── rank ───────────────────────────────────────────────────────────────────


def test_rank_json_shape(graph: Path) -> None:
    """rank --json returns a document with hotspots, total, and truncated; each hotspot carries the documented fields."""
    result = run("rank", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert set(payload) >= {"hotspots", "total", "truncated"}, (
        f"rank --json must carry hotspots, total, truncated; got {set(payload)}"
    )
    assert payload["hotspots"], "fixture graph must have at least one hotspot"
    row = payload["hotspots"][0]
    assert set(row) >= {"symbol", "name", "kind", "file", "line_1based", "score"}, (
        f"hotspot must carry symbol, name, kind, file, line_1based, score; got {set(row)}"
    )


def test_rank_limit(graph: Path) -> None:
    """rank --limit 2 --json returns exactly two hotspots."""
    result = run("rank", "--limit", "2", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert len(payload["hotspots"]) == 2, (
        f"rank --limit 2 must return 2 hotspots, got {len(payload['hotspots'])}"
    )


def test_rank_seeds(graph: Path) -> None:
    """rank --seeds with the entry id exits 0 and its hotspots include the other.py handle; an ambiguous seed name exits non-zero."""
    entry_result = run("resolve", "entry", "--json", db=graph)
    entry_id = json.loads(entry_result.stdout)[0]["symbol_id"]

    result = run("rank", "--seeds", entry_id, "--json", db=graph)
    assert result.returncode == 0, "rank --seeds with an exact id must exit 0"
    payload = json.loads(result.stdout)
    symbols = {h["symbol"] for h in payload["hotspots"]}
    # Seeded PageRank biases toward the seed's neighbourhood but ranks the whole
    # graph; other.py/handle() — which entry cannot reach — should still appear.
    other_handle = "ts-python . . . other/handle()."
    assert other_handle in symbols, (
        f"rank --seeds (entry id) must include other.py handle ({other_handle!r}); "
        f"got {sorted(symbols)}"
    )

    # An ambiguous seed name exits non-zero because it names two symbols.
    ambiguous = run("rank", "--seeds", "handle", "--json", db=graph)
    assert ambiguous.returncode != 0, (
        "rank --seeds with an ambiguous name must exit non-zero"
    )


# ── annotations ────────────────────────────────────────────────────────────


def test_annotations_name_form_returns_an_array_of_entries(
    graph: Path, known_symbol: dict
) -> None:
    """The pack documents the array shape for the <name> form."""
    run(
        "annotate", known_symbol["name"],
        "--key", "probe", "--value", "1",
        "--confidence", "0.8", "--provenance", "test", "--author", "suite",
        db=graph,
    )
    payload = json.loads(run("annotations", known_symbol["name"], "--json", db=graph).stdout)
    assert isinstance(payload, list)
    assert set(payload[0]) == {"symbol", "annotations"}


def test_annotation_json_has_ts_and_no_last_verified(
    graph: Path, known_symbol: dict
) -> None:
    """The correction that started this suite: there is no `last_verified`."""
    run(
        "annotate", known_symbol["name"],
        "--key", "probe", "--value", "1", "--author", "suite",
        db=graph,
    )
    payload = json.loads(run("annotations", known_symbol["name"], "--json", db=graph).stdout)
    annotation = payload[0]["annotations"][0]
    assert set(annotation) == {
        "advisory", "author", "confidence", "key", "provenance", "ts", "type", "value",
    }
    assert "last_verified" not in annotation


def test_stale_annotations_cutoff_is_unix_seconds(graph: Path) -> None:
    """A date string is rejected — the pack now says so."""
    assert run("stale-annotations", "2026-01-01", "--json", db=graph).returncode != 0
    assert run("stale-annotations", "9999999999", "--json", db=graph).returncode == 0


# ── other documented verbs ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "verb", ["entrypoints", "leaves", "dead-code"]
)
def test_edge_population_verbs_emit_json_arrays(graph: Path, verb: str) -> None:
    assert isinstance(json.loads(run(verb, "--json", db=graph).stdout), list)


def test_context_rows_lack_symbol_id(graph: Path, known_symbol: dict) -> None:
    """capability-map.md warns the context payload carries no symbol_id."""
    rows = json.loads(
        run("context", known_symbol["name"], "--budget", "1200", "--json", db=graph).stdout
    )
    assert rows and "symbol_id" not in rows[0]
    assert set(rows[0]) == {"file", "kind", "line", "name"}


def test_undocumented_but_dispatched_verbs_are_accepted(graph: Path) -> None:
    """gaps.md §Capability discovery claims three verbs work despite being absent from --help."""
    assert run("by-requirement", "REQ-NONEXISTENT", db=graph).returncode == 0
    assert run("graph-view", "--limit", "5", db=graph).returncode == 0
    # `semantics` with no symbol prints its own usage rather than the banner,
    # which is itself proof the arm exists.
    semantics = run("semantics", db=graph)
    assert "usage: wicked-estate semantics" in (semantics.stdout + semantics.stderr)


def test_no_version_flag_falls_through_to_the_usage_banner() -> None:
    """The preflight parses this banner because no version flag exists."""
    completed = subprocess.run(
        [BINARY, "--version"], capture_output=True, text=True, check=False, timeout=60
    )
    combined = completed.stdout + completed.stderr
    assert "usage:" in combined
    assert len(combined.splitlines()) > 10, "expected the full banner, not a version line"


def test_stats_reports_counts(graph: Path) -> None:
    """The pack's documented freshness-and-readiness probe."""
    completed = run("stats", db=graph)
    assert completed.returncode == 0
    assert "nodes" in completed.stdout.lower()


# ── the vocabulary allowlist, checked against the binary ───────────────────


def test_every_allowlisted_cli_verb_is_accepted_by_the_binary(graph: Path) -> None:
    """Close the circularity: the static guard's allowlist must match reality.

    An unknown verb falls through to the dispatcher's default arm and prints
    the usage banner. Every name the pack may use must do something else.

    Verbs are probed with no arguments: one that needs a positional errors with
    its own usage string, which still proves the arm exists. `watch` is
    excluded because it does not terminate.
    """
    import importlib.util  # noqa: PLC0415
    import sys  # noqa: PLC0415

    # Loaded under a pack- and skill-qualified name rather than imported by
    # bare name: `test_estate_surface_vocabulary` would otherwise bind
    # positionally via sys.path, which this catalogue's authoring standards
    # forbid for exactly this reason.
    spec = importlib.util.spec_from_file_location(
        "wicked_estate_tests_surface_vocabulary",
        PACK_ROOT / "tests" / "pack" / "test_estate_surface_vocabulary.py",
    )
    assert spec and spec.loader
    vocabulary = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = vocabulary
    spec.loader.exec_module(vocabulary)
    CLI_VERBS = vocabulary.CLI_VERBS

    banner = "— usage:"
    unrecognised = []
    for verb in sorted(CLI_VERBS - {"watch"}):
        completed = run(verb, db=graph)
        if banner in (completed.stdout + completed.stderr):
            unrecognised.append(verb)
    assert not unrecognised, (
        f"allowlisted verbs the binary does not recognise: {unrecognised}"
    )


# ── the `source` selector trap ─────────────────────────────────────────────


def test_source_text_mode_honours_symbol_selector(graph: Path, known_symbol: dict) -> None:
    """source text mode exits 0 and prints exactly one body when --symbols narrows to one match.

    In 0.21.0, the text path honours its selectors. A --symbols selector with a
    single exact id narrows the output to that one symbol.  Also, --max-total-chars
    is a JSON-only flag and exits non-zero without --json.
    """
    # `handle` is defined twice in the fixture; --symbols with one id gives one match.
    both = json.loads(run("resolve", "handle", "--json", db=graph).stdout)
    assert len(both) == 2
    one_id = both[0]["symbol_id"]

    result = run("source", "--symbols", one_id, db=graph)
    assert result.returncode == 0, "source text mode with --symbols must exit 0"
    assert "1 match" in result.stdout, (
        "source text mode with one id must report exactly one match"
    )

    # --max-total-chars is a JSON-only flag; text mode exits non-zero.
    result_max = run("source", "helper", "--max-total-chars", "10", db=graph)
    assert result_max.returncode != 0, (
        "--max-total-chars without --json must exit non-zero"
    )


def test_signatures_only_requires_json(graph: Path, known_symbol: dict) -> None:
    """`--signatures-only` drops `source` and keeps `signature`."""
    bundle = json.loads(
        run(
            "source", "--symbols", known_symbol["symbol_id"],
            "--json", "--signatures-only", db=graph,
        ).stdout
    )
    assert bundle["nodes"], "fixture symbol produced no node"
    trimmed = bundle["nodes"][0]
    assert trimmed["source"] is None
    assert trimmed["signature"], "the signature must survive the trim"

    with_body = json.loads(
        run("source", "--symbols", known_symbol["symbol_id"], "--json", db=graph).stdout
    )
    assert with_body["nodes"][0]["source"]


# ── 0.21.0: lineage ───────────────────────────────────────────────────────────


def test_lineage_json_shape(graph: Path) -> None:
    """lineage --symbol <entry id> --json returns content and diagnostics; searched_depth is 8; handle at depth 1, helper at depth 2; helper's line is one less than resolve reports."""
    entry_id = "ts-python . . . caller/entry()."
    result = run("lineage", "--symbol", entry_id, "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert set(payload) >= {"content", "diagnostics"}, (
        f"lineage --json must carry content and diagnostics; got {set(payload)}"
    )
    content = payload["content"]
    assert content["searched_depth"] == 8, (
        f"lineage default searched_depth must be 8, got {content['searched_depth']}"
    )
    deps = {d["name"]: d for d in content["dependencies"]}
    assert "handle" in deps and deps["handle"]["depth"] == 1, (
        "handle must appear at depth 1"
    )
    assert "helper" in deps and deps["helper"]["depth"] == 2, (
        "helper must appear at depth 2"
    )

    # helper's lineage line (0-based) must be one less than resolve's line (1-based).
    resolve_result = run("resolve", "helper", "--json", db=graph)
    resolve_line = json.loads(resolve_result.stdout)[0]["line"]
    lineage_line = deps["helper"]["line"]
    assert lineage_line == resolve_line - 1, (
        f"helper lineage line {lineage_line} must be resolve line {resolve_line} - 1"
    )


def test_lineage_name_exits_zero_with_empty_deps(graph: Path) -> None:
    """lineage --symbol entry (a name, not an id) exits 0 with an empty dependencies list."""
    result = run("lineage", "--symbol", "entry", "--json", db=graph)
    assert result.returncode == 0, "lineage with a name must exit 0"
    payload = json.loads(result.stdout)
    assert payload["content"]["dependencies"] == [], (
        "lineage with a name must return empty dependencies (no resolution)"
    )


def test_lineage_depth_ceiling_and_bad_relation(graph: Path) -> None:
    """lineage --depth 25 exits non-zero; lineage --relation flow_to exits non-zero."""
    entry_id = "ts-python . . . caller/entry()."
    assert (
        run("lineage", "--symbol", entry_id, "--depth", "25", db=graph).returncode != 0
    ), "lineage --depth 25 must exit non-zero (ceiling is 24)"
    assert (
        run("lineage", "--symbol", entry_id, "--relation", "flow_to", db=graph).returncode != 0
    ), "lineage --relation flow_to must exit non-zero (only flows_to is accepted)"


# ── 0.21.0: traverse ──────────────────────────────────────────────────────────


def test_traverse_json_shape_and_edge_keys(graph: Path) -> None:
    """traverse helper --direction dependents --json returns the documented keys; each edge carries kind, confidence, provenance, resolved_by."""
    result = run("traverse", "helper", "--direction", "dependents", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert set(payload) >= {
        "nodes",
        "edges",
        "depths",
        "truncated",
        "searched_depth",
        "depth_horizon_reached",
        "node_cap_reached",
    }, f"traverse --json missing keys; got {set(payload)}"
    if payload["edges"]:
        edge = payload["edges"][0]
        assert set(edge) >= {"kind", "confidence", "provenance", "resolved_by"}, (
            f"edge missing required keys; got {set(edge)}"
        )


def test_traverse_clamping_and_staleness(graph: Path) -> None:
    """traverse with over-ceiling depth or max-nodes writes CLAMPED: to stderr while stdout still parses; traverse sideways exits non-zero; rank --json writes STALENESS: to stderr."""
    # Invalid direction exits non-zero.
    sideways = run("traverse", "helper", "--direction", "sideways", "--json", db=graph)
    assert sideways.returncode != 0, "--direction sideways must exit non-zero"

    # Over-ceiling --depth is clamped: CLAMPED on stderr, valid JSON on stdout.
    depth_result = run("traverse", "helper", "--depth", "99", "--json", db=graph)
    assert depth_result.returncode == 0
    assert any(
        line.startswith("CLAMPED:") for line in depth_result.stderr.splitlines()
    ), "traverse --depth 99 must write a CLAMPED: line to stderr"
    json.loads(depth_result.stdout)  # stdout must still parse

    # Over-ceiling --max-nodes is clamped: CLAMPED on stderr, valid JSON on stdout.
    nodes_result = run("traverse", "helper", "--max-nodes", "999999", "--json", db=graph)
    assert nodes_result.returncode == 0
    assert any(
        line.startswith("CLAMPED:") for line in nodes_result.stderr.splitlines()
    ), "traverse --max-nodes 999999 must write a CLAMPED: line to stderr"
    json.loads(nodes_result.stdout)

    # rank --json writes STALENESS: to stderr; stdout must parse.
    rank_result = run("rank", "--json", db=graph)
    assert rank_result.returncode == 0
    assert any(
        line.startswith("STALENESS:") for line in rank_result.stderr.splitlines()
    ), "rank --json must write a STALENESS: line to stderr"
    json.loads(rank_result.stdout)


# ── 0.21.0: rules ─────────────────────────────────────────────────────────────


def test_rules_inventory_and_recall_json(graph: Path) -> None:
    """rules-inventory --json and rules-recall --json each exit 0 with stdout that parses as JSON; rules-recall --bogus exits non-zero."""
    inv = run("rules-inventory", "--json", db=graph)
    assert inv.returncode == 0, "rules-inventory --json must exit 0"
    json.loads(inv.stdout)  # must parse

    recall = run("rules-recall", "--json", db=graph)
    assert recall.returncode == 0, "rules-recall --json must exit 0"
    json.loads(recall.stdout)  # must parse

    bogus = run("rules-recall", "--bogus", "x", db=graph)
    assert bogus.returncode != 0, "rules-recall --bogus must exit non-zero"


# ── 0.21.0: missing db ────────────────────────────────────────────────────────


def test_traverse_missing_db_exits_nonzero_without_creating_file(
    tmp_path: Path,
) -> None:
    """traverse with a missing --db exits non-zero and does not create the file."""
    missing_db = tmp_path / "no_such_dir" / "graph.db"
    assert not missing_db.exists()

    result = subprocess.run(
        [BINARY, "traverse", "helper", "--db", str(missing_db)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode != 0, (
        "traverse must exit non-zero when the --db path does not exist"
    )
    assert not missing_db.exists(), (
        "traverse must not create the missing --db file"
    )


# ── 0.21.0: graph-view edge shape ─────────────────────────────────────────────


def test_graph_view_json_edge_shape(graph: Path) -> None:
    """graph-view --limit 5 stdout parses as JSON and every edge carries kind, confidence, provenance, resolved_by."""
    result = run("graph-view", "--limit", "5", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "edges" in payload, "graph-view stdout must be a JSON object with an 'edges' key"
    for edge in payload["edges"]:
        assert set(edge) >= {"kind", "confidence", "provenance", "resolved_by"}, (
            f"graph-view edge missing required keys; got {set(edge)}"
        )


# ── 0.18.0: blast-radius --depth and searched_depth ───────────────────────────


@pytest.fixture(scope="session")
def helper_symbol(indexed_graph: Path) -> dict:
    """The resolved symbol for `helper` in the fixture (defined exactly once in core.py)."""
    completed = run("resolve", "helper", "--json", db=indexed_graph)
    hits = json.loads(completed.stdout)
    assert len(hits) == 1, "helper should be defined exactly once in the fixture"
    return hits[0]


def test_blast_radius_default_searched_depth(graph: Path) -> None:
    """blast-radius with no --depth reports searched_depth of 12.

    See gaps.md §Completeness for the default traversal depth that 0.18.0 now
    reports explicitly via searched_depth.
    """
    payload = json.loads(run("blast-radius", "helper", "--json", db=graph).stdout)
    assert payload["searched_depth"] == 12


def test_blast_radius_depth_sets_horizon_reached_and_searched(graph: Path) -> None:
    """--depth 1 reports depth_horizon_reached true and searched_depth 1.

    See gaps.md §Completeness: depth_horizon_reached distinguishes a cut result
    from a complete one.
    """
    payload = json.loads(
        run("blast-radius", "helper", "--depth", "1", "--json", db=graph).stdout
    )
    assert payload["depth_horizon_reached"] is True
    assert payload["searched_depth"] == 1


def test_blast_radius_depth_ceiling_is_24(graph: Path) -> None:
    """--depth 24 exits 0 and --depth 25 exits non-zero.

    See gaps.md §Completeness: the maximum depth is 24; values above it are
    refused rather than silently clamped.
    """
    assert run("blast-radius", "helper", "--depth", "24", db=graph).returncode == 0
    assert run("blast-radius", "helper", "--depth", "25", db=graph).returncode != 0


def test_blast_radius_text_cut_line(graph: Path) -> None:
    """--depth 1 in text mode prints a line containing 'CUT AT depth=1'.

    See gaps.md §Completeness: the text output now surfaces the depth horizon
    so an agent without --json can still see that output was cut.
    """
    stdout = run("blast-radius", "helper", "--depth", "1", db=graph).stdout
    assert "CUT AT depth=1" in stdout


# ── 0.18.0: path command ──────────────────────────────────────────────────────


def test_path_entry_to_helper_found_with_two_hops(graph: Path) -> None:
    """path entry helper --json returns found true and exactly two hops.

    Each hop must carry kind, confidence, provenance, resolved_by, source, and
    target.  The fixture path is entry -> handle (core.py) -> helper.
    See gaps.md §Paths for the capability that 0.18.0 adds.
    """
    payload = json.loads(
        run("path", "entry", "helper", "--json", db=graph).stdout
    )
    assert payload["found"] is True
    assert len(payload["hops"]) == 2, (
        f"expected 2 hops, got {len(payload['hops'])}"
    )
    required_hop_keys = {"kind", "confidence", "provenance", "resolved_by", "source", "target"}
    for hop in payload["hops"]:
        assert required_hop_keys <= set(hop), (
            f"hop missing keys: {required_hop_keys - set(hop)}"
        )


def test_path_helper_to_entry_not_found_unbounded(graph: Path) -> None:
    """path helper entry --json returns found false with both bounds false.

    The dependency direction is entry->handle->helper, so the reverse walk
    finds no path.  Both depth_bounded and node_bounded must be false because
    the walk was not cut short.  See gaps.md §Paths.
    """
    payload = json.loads(
        run("path", "helper", "entry", "--json", db=graph).stdout
    )
    assert payload["found"] is False
    assert payload["depth_bounded"] is False
    assert payload["node_bounded"] is False


def test_path_entry_helper_depth_bounded_absence(graph: Path) -> None:
    """path entry helper --max-depth 1 returns found false with depth_bounded true.

    The path from entry to helper takes 2 hops; with max-depth 1 the walk
    touches its frontier without finding the target.  See gaps.md §Paths.
    """
    payload = json.loads(
        run("path", "entry", "helper", "--max-depth", "1", "--json", db=graph).stdout
    )
    assert payload["found"] is False
    assert payload["depth_bounded"] is True


def test_path_entry_helper_found_with_depth_bounded(graph: Path) -> None:
    """path entry helper --max-depth 2 returns found true with depth_bounded true.

    depth_bounded is true whenever the walk touches its frontier, even when a
    route is found.  The 2-hop path from entry to helper exactly reaches the
    max-depth frontier.  See gaps.md §Paths.
    """
    payload = json.loads(
        run("path", "entry", "helper", "--max-depth", "2", "--json", db=graph).stdout
    )
    assert payload["found"] is True
    assert payload["depth_bounded"] is True


def test_path_unresolved_from_side(graph: Path) -> None:
    """path nope helper --json exits 0 and returns unresolved 'from'.

    An unresolved input on the from side exits 0 so that a workflow can handle
    it gracefully.  See gaps.md §Paths.
    """
    result = run("path", "nope", "helper", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["unresolved"] == "from"
    # The trap the pack warns about: an unknown name looks like a searched absence
    # unless `unresolved` is read first.
    assert payload["found"] is False
    assert payload["depth_bounded"] is False
    assert payload["node_bounded"] is False


def test_path_unresolved_to_side(graph: Path) -> None:
    """path entry nope --json exits 0 and returns unresolved 'to'.

    An unresolved input on the to side exits 0 so that a workflow can handle
    it gracefully.  See gaps.md §Paths.
    """
    result = run("path", "entry", "nope", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["unresolved"] == "to"


def test_path_above_16_max_depth_accepted(graph: Path) -> None:
    """path entry helper --max-depth 17 exits 0 and returns found true.

    Values above 16 are accepted by the shared parser (clamped to 16 internally
    per source-read, but accepted without error).  See gaps.md §Paths.
    """
    result = run("path", "entry", "helper", "--max-depth", "17", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["found"] is True


def test_path_hop_endpoints_line_numbering(graph: Path) -> None:
    """Every path endpoint has line_1based equal to line + 1.

    The path command reports line as 0-based (unlike resolve and blast-radius),
    and provides line_1based as the 1-based equivalent.  See gaps.md §Paths for
    the note on the 0-based line caveat.
    """
    payload = json.loads(
        run("path", "entry", "helper", "--json", db=graph).stdout
    )
    assert payload["found"] is True
    for hop in payload["hops"]:
        for endpoint_key in ("source", "target"):
            endpoint = hop[endpoint_key]
            assert endpoint["line_1based"] == endpoint["line"] + 1, (
                f"{endpoint_key} endpoint: line_1based {endpoint['line_1based']} "
                f"!= line {endpoint['line']} + 1"
            )


def test_path_helper_endpoint_matches_resolve_line(
    graph: Path, indexed_graph: Path, helper_symbol: dict
) -> None:
    """The 'helper' endpoint in path entry helper has line_1based matching resolve's line.

    resolve reports 1-based line numbers; path reports 0-based line plus
    line_1based.  They must agree: path.line_1based == resolve.line.  See
    gaps.md §Paths for the line-numbering caveat.
    """
    resolve_line = helper_symbol["line"]

    payload = json.loads(
        run("path", "entry", "helper", "--json", db=graph).stdout
    )
    assert payload["found"] is True

    # Find the endpoint named "helper" among all hop endpoints.
    helper_endpoint: dict | None = None
    for hop in payload["hops"]:
        for ep_key in ("source", "target"):
            if hop[ep_key].get("name") == "helper":
                helper_endpoint = hop[ep_key]
                break
        if helper_endpoint is not None:
            break

    assert helper_endpoint is not None, (
        "no endpoint named 'helper' found in path hops"
    )
    assert helper_endpoint["line_1based"] == resolve_line, (
        f"path endpoint line_1based {helper_endpoint['line_1based']} "
        f"!= resolve line {resolve_line}"
    )
