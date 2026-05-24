"""T3: self-host consumer schema-migration tests (AC9, AC14, AC16).

The `run_self_host` orchestrator reads `.adapt-discovery.toml` via the
typed `load_adapt_discovery_typed` loader. Legacy `[adapt]` table,
unknown `discovery-schema-version`, and other invalid shapes refuse
with the `self-host: ` prefix per spec.

Tests are lightweight: each crafts a minimal `working_tree` with a
crafted `.adapt-discovery.toml`, invokes `run_self_host(..., dry_run=
True, force=True)`, and asserts on the first stderr line. Dry-run
sidesteps the full projection.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.build import self_host


def _minimal_contract() -> dict:
    """Return a contract object that lets dry-run reach the discovery read.

    The minimum shape needed by `run_self_host` before it touches
    discovery is the existence of the dict; downstream steps may fail,
    but every test here returns at the discovery-read fork.
    """
    return {"primitive": {}, "adapter": {"claude-code": {"projection": []}}}


def _seed(working_tree: Path, discovery_body: str) -> None:
    """Write the discovery file and a stub packs dir for the run."""
    (working_tree / ".adapt-discovery.toml").write_text(
        discovery_body, encoding="utf-8"
    )


def test_legacy_adapt_refused_with_prefix(tmp_path, capsys):
    """Legacy top-level ``[adapt]`` refused with ``self-host: `` prefix
    naming the spec migration path."""
    _seed(
        tmp_path,
        '[adapt]\nproject-name = "x"\n',
    )
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    rc = self_host.run_self_host(
        working_tree=tmp_path,
        packs_dir=packs_dir,
        dry_run=True,
        force=True,
        contract=_minimal_contract(),
    )
    assert rc == 3
    first_line = capsys.readouterr().err.splitlines()[0]
    assert first_line == (
        "self-host: legacy [adapt] table; migrate to [markers] per "
        "docs/specs/adapt-to-project/spec.md"
    )


def test_unknown_schema_version_refused_with_prefix(tmp_path, capsys):
    """Unknown ``discovery-schema-version`` refused with the
    ``self-host: `` prefix and names ``0.1`` as the known version."""
    _seed(
        tmp_path,
        'discovery-schema-version = "9.9"\n[markers]\nx = "y"\n',
    )
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    rc = self_host.run_self_host(
        working_tree=tmp_path,
        packs_dir=packs_dir,
        dry_run=True,
        force=True,
        contract=_minimal_contract(),
    )
    assert rc == 3
    first_line = capsys.readouterr().err.splitlines()[0]
    assert first_line.startswith("self-host: ")
    assert "0.1" in first_line


def test_canonical_markers_table_loads(tmp_path, capsys):
    """Canonical ``[markers]`` shape loads cleanly past the discovery read."""
    _seed(
        tmp_path,
        'discovery-schema-version = "0.1"\n'
        '[markers]\nproject-name = "demo"\nowner = "octocat"\n',
    )
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    rc = self_host.run_self_host(
        working_tree=tmp_path,
        packs_dir=packs_dir,
        dry_run=True,
        force=True,
        contract=_minimal_contract(),
    )
    # Downstream steps may fail (no real packs), but the discovery
    # read must have succeeded — no `self-host:` prefix on the first
    # stderr line if any.
    err = capsys.readouterr().err
    if err:
        first = err.splitlines()[0]
        # If a `self-host:` line is emitted, it must NOT name the
        # legacy or unknown-schema-version paths.
        assert "legacy [adapt]" not in first
        assert "unknown discovery-schema-version" not in first


def test_lowercase_hyphen_marker_substitutes(tmp_path):
    """``resolve_markers`` substitutes ``<adapt:project-name>`` (AC14)."""
    target = tmp_path / "AGENTS.md"
    target.write_text("name: <adapt:project-name>\n", encoding="utf-8")
    modified = self_host.resolve_markers(
        tmp_path, {"project-name": "demo"}, extra_paths=[Path("AGENTS.md")]
    )
    assert modified == 1
    assert target.read_text(encoding="utf-8") == "name: demo\n"


def test_upper_snake_marker_left_in_place_with_warning(tmp_path, capsys):
    """Legacy ``<adapt:PROJECT_NAME>`` is left in place; warning emitted."""
    target = tmp_path / "AGENTS.md"
    target.write_text("name: <adapt:PROJECT_NAME>\n", encoding="utf-8")
    modified = self_host.resolve_markers(
        tmp_path,
        {"PROJECT_NAME": "WRONG", "project-name": "demo"},
        extra_paths=[Path("AGENTS.md")],
    )
    assert modified == 0
    assert target.read_text(encoding="utf-8") == "name: <adapt:PROJECT_NAME>\n"
    err = capsys.readouterr().err
    assert "legacy UPPER_SNAKE marker" in err
