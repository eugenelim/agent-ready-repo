"""Execute the real `wicked-estate` CLI and assert the shapes the pack documents.

Every other suite in this pack is static: it compares the pack's prose to an
allowlist the same author transcribed, which cannot catch a transcription
error. This suite closes that loop by running the binary against a real index
and reading what actually comes back.

It is skipped when `wicked-estate` is absent, so it self-declares as unrun
rather than passing vacuously. To run it:

    cargo install wicked-estate --version 0.18.0 --locked
    pytest packs/code-intelligence/tests/skills/code-intelligence/

The index is built once per session into a temp directory from a purpose-built
three-file micro-repository, so assertions stay deterministic as this
repository changes. Every probe runs against a **copy** of that graph, so a
verb that mutates cannot corrupt the shared fixture.
"""

from __future__ import annotations

import json
import re
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
    reason="wicked-estate not installed; run `cargo install wicked-estate --version 0.18.0 --locked`",
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
    """The seven CLI keys the pack's completeness guidance depends on.

    0.18.0 adds searched_depth, depth_horizon_reached, and node_cap_reached
    to the existing four, enabling the agent to distinguish a depth-cut result
    from a complete one.  See gaps.md §Completeness for the gap this closes.
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
    }


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


def test_nodes_has_no_symbol_filter(graph: Path, known_symbol: dict) -> None:
    """The pack forbids `nodes` for single-symbol lookup; prove it cannot do it."""
    filtered = json.loads(run("nodes", "--symbol", known_symbol["symbol_id"], "--json", db=graph).stdout)
    unfiltered = json.loads(run("nodes", "--json", db=graph).stdout)
    assert len(filtered) == len(unfiltered) > 1, "--symbol was silently ignored"


# ── rank ───────────────────────────────────────────────────────────────────


def test_rank_ignores_json_and_is_fixed_width(graph: Path) -> None:
    """capability-map.md says rank is text-only and capped at 25 rows.

    The cap is a maximum, not a fixed count: a graph smaller than 25 symbols
    prints however many it has.
    """
    stdout = run("rank", "--json", db=graph).stdout
    with pytest.raises(json.JSONDecodeError):
        json.loads(stdout)
    assert re.match(r"top \d+ symbols by PageRank", stdout)
    assert int(re.match(r"top (\d+)", stdout).group(1)) <= 25


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


def test_source_selectors_require_json(graph: Path, known_symbol: dict) -> None:
    """`--symbols` narrows only on the JSON path; the text path ignores it.

    Found by running the pack's own documented Pattern 1 against a real index:
    the text form returned every name match while appearing to be pinned to
    one symbol. The references now require `--json` with any selector, and
    this is what holds them to it.
    """
    # `handle` is defined twice in the fixture, so a working selector narrows
    # two matches to one.
    both = json.loads(run("resolve", "handle", "--json", db=graph).stdout)
    assert len(both) == 2
    one_id = both[0]["symbol_id"]

    bundle = json.loads(
        run("source", "--symbols", one_id, "--json", db=graph).stdout
    )
    assert len(bundle["nodes"]) == 1, "--json path must honour --symbols"

    # Text path: the selector alone is refused outright.
    assert run("source", "--symbols", one_id, db=graph).returncode != 0


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


# ── 0.18.0: blast-radius --depth and searched_depth ───────────────────────────


@pytest.fixture(scope="session")
def helper_symbol(indexed_graph: Path) -> dict:
    """The resolved symbol for `helper` in the fixture (defined exactly once in core.py)."""
    completed = run("resolve", "helper", "--json", db=indexed_graph)
    hits = json.loads(completed.stdout)
    assert len(hits) == 1, "helper should be defined exactly once in the fixture"
    return hits[0]


def test_blast_radius_default_searched_depth(graph: Path) -> None:
    """AC-0014: blast-radius with no --depth reports searched_depth of 12.

    See gaps.md §Completeness for the default traversal depth that 0.18.0 now
    reports explicitly via searched_depth.
    """
    payload = json.loads(run("blast-radius", "helper", "--json", db=graph).stdout)
    assert payload["searched_depth"] == 12


def test_blast_radius_depth_sets_horizon_reached_and_searched(graph: Path) -> None:
    """AC-0015: --depth 1 reports depth_horizon_reached true and searched_depth 1.

    See gaps.md §Completeness: depth_horizon_reached distinguishes a cut result
    from a complete one.
    """
    payload = json.loads(
        run("blast-radius", "helper", "--depth", "1", "--json", db=graph).stdout
    )
    assert payload["depth_horizon_reached"] is True
    assert payload["searched_depth"] == 1


def test_blast_radius_depth_ceiling_is_24(graph: Path) -> None:
    """AC-0016: --depth 24 exits 0 and --depth 25 exits non-zero.

    See gaps.md §Completeness: the maximum depth is 24; values above it are
    refused rather than silently clamped.
    """
    assert run("blast-radius", "helper", "--depth", "24", db=graph).returncode == 0
    assert run("blast-radius", "helper", "--depth", "25", db=graph).returncode != 0


def test_blast_radius_text_cut_line(graph: Path) -> None:
    """AC-0017: --depth 1 in text mode prints a line containing 'CUT AT depth=1'.

    See gaps.md §Completeness: the text output now surfaces the depth horizon
    so an agent without --json can still see that output was cut.
    """
    stdout = run("blast-radius", "helper", "--depth", "1", db=graph).stdout
    assert "CUT AT depth=1" in stdout


# ── 0.18.0: path command ──────────────────────────────────────────────────────


def test_path_entry_to_helper_found_with_two_hops(graph: Path) -> None:
    """AC-0018: path entry helper --json returns found true and exactly two hops.

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
    """AC-0019: path helper entry --json returns found false with both bounds false.

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
    """AC-0020: path entry helper --max-depth 1 returns found false with depth_bounded true.

    The path from entry to helper takes 2 hops; with max-depth 1 the walk
    touches its frontier without finding the target.  See gaps.md §Paths.
    """
    payload = json.loads(
        run("path", "entry", "helper", "--max-depth", "1", "--json", db=graph).stdout
    )
    assert payload["found"] is False
    assert payload["depth_bounded"] is True


def test_path_entry_helper_found_with_depth_bounded(graph: Path) -> None:
    """AC-0021: path entry helper --max-depth 2 returns found true with depth_bounded true.

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
    """AC-0022: path nope helper --json exits 0 and returns unresolved 'from'.

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
    """AC-0023: path entry nope --json exits 0 and returns unresolved 'to'.

    An unresolved input on the to side exits 0 so that a workflow can handle
    it gracefully.  See gaps.md §Paths.
    """
    result = run("path", "entry", "nope", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["unresolved"] == "to"


def test_path_above_16_max_depth_accepted(graph: Path) -> None:
    """AC-0024: path entry helper --max-depth 17 exits 0 and returns found true.

    Values above 16 are accepted by the shared parser (clamped to 16 internally
    per source-read, but accepted without error).  See gaps.md §Paths.
    """
    result = run("path", "entry", "helper", "--max-depth", "17", "--json", db=graph)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["found"] is True


def test_path_hop_endpoints_line_numbering(graph: Path) -> None:
    """AC-0025: every path endpoint has line_1based equal to line + 1.

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
    """AC-0026: the 'helper' endpoint in path entry helper has line_1based matching resolve.

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
