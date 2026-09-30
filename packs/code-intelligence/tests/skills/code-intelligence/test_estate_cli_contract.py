"""Execute the real `wicked-estate` CLI and assert the shapes the pack documents.

Every other suite in this pack is static: it compares the pack's prose to an
allowlist the same author transcribed, which cannot catch a transcription
error. This suite closes that loop by running the binary against a real index
and reading what actually comes back.

It is skipped when `wicked-estate` is absent, so it self-declares as unrun
rather than passing vacuously. To run it:

    cargo install wicked-estate --version 0.16.7 --locked
    pytest packs/wicked-estate/tests/skills/code-intelligence/

The index is built once per session into a temp directory from this
repository's own `packages/` tree — a real Python codebase, small enough to
index in seconds. Every probe runs against a **copy** of that graph, so a verb
that mutates cannot corrupt the shared fixture.
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
    reason="wicked-estate not installed; run `cargo install wicked-estate --version 0.16.7 --locked`",
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
    """The four CLI keys the pack's completeness guidance depends on."""
    payload = json.loads(run("blast-radius", known_symbol["name"], "--json", db=graph).stdout)
    assert set(payload) == {"target", "dependents", "unresolved", "truncated_dependents"}


def test_blast_radius_dependents_have_no_depth_or_confidence(
    graph: Path, known_symbol: dict
) -> None:
    """gaps.md #7 and #11 claim the CLI form omits both. Hold them to it."""
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
    """gaps.md #14 claims three verbs work despite being absent from --help."""
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
