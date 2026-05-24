"""T2: CLI ``agentbundle adapt`` schema-migration tests (AC8, AC14, AC16).

Covers:
  - Canonical ``[markers]`` table substitutes (AC8 happy-path).
  - Legacy ``[accepted]`` table refused with ``adapt: `` prefix (AC8).
  - Unknown ``discovery-schema-version`` refused with ``adapt: `` prefix
    naming ``0.1`` (AC16).
  - Lowercase-hyphen markers substitute (AC14 widened regex).
  - UPPER_SNAKE markers leave-and-warn (AC14 narrowed regex).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from agentbundle.commands import adapt
from agentbundle.config import PackState, State, dump_state
from agentbundle.safety import sha256_bytes


def _seed_repo(root: Path, files: dict[str, str]) -> None:
    """Write *files* under *root* and seed a v0.2 state file recording them."""
    state = State()
    file_entries: dict[str, dict[str, str]] = {}
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        p.write_bytes(data)
        file_entries[rel] = {
            "sha": sha256_bytes(data),
            "from-pack-version": "0.1.0",
        }
    state.packs["core"] = PackState(installed_version="0.1.0", files=file_entries)
    (root / ".agent-ready-state.toml").write_text(dump_state(state), encoding="utf-8")


def _ns(root: Path, values_from: Path | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        root=str(root),
        values_from=str(values_from) if values_from else None,
        ci=False,
    )


def test_markers_table_substitutes(tmp_path):
    """A repo-scope ``[markers]`` table substitutes via --values-from."""
    _seed_repo(tmp_path, {"AGENTS.md": "owner: <adapt:owner>\n"})
    (tmp_path / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n[markers]\nowner = "octocat"\n',
        encoding="utf-8",
    )
    rc = adapt.run(_ns(tmp_path, values_from=tmp_path / ".adapt-discovery.toml"))
    assert rc == 0
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == "owner: octocat\n"


def test_legacy_accepted_refused_with_prefix(tmp_path, capsys):
    """Legacy top-level ``[accepted]`` refused with stderr ``adapt: `` prefix."""
    _seed_repo(tmp_path, {"AGENTS.md": "x\n"})
    (tmp_path / ".adapt-discovery.toml").write_text(
        '[accepted]\nowner = "octocat"\n', encoding="utf-8"
    )
    rc = adapt.run(_ns(tmp_path))
    assert rc == 1
    err = capsys.readouterr().err
    first_line = err.splitlines()[0]
    assert first_line == (
        "adapt: legacy [accepted] table; migrate to [markers] per "
        "docs/specs/adapt-to-project/spec.md"
    )


def test_unknown_schema_version_refused_with_prefix(tmp_path, capsys):
    """Unknown ``discovery-schema-version`` refused with ``adapt: `` prefix
    naming ``0.1`` (AC16)."""
    _seed_repo(tmp_path, {"AGENTS.md": "x\n"})
    (tmp_path / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "9.9"\n[markers]\nowner = "x"\n',
        encoding="utf-8",
    )
    rc = adapt.run(_ns(tmp_path))
    assert rc == 1
    first_line = capsys.readouterr().err.splitlines()[0]
    assert first_line.startswith("adapt: ")
    assert "0.1" in first_line


def test_lowercase_hyphen_markers_match(tmp_path):
    """``<adapt:project-name>`` substitutes (canonical form, AC14)."""
    _seed_repo(tmp_path, {"AGENTS.md": "project=<adapt:project-name>\n"})
    values = tmp_path / "values.toml"
    values.write_text('[markers]\nproject-name = "demo"\n', encoding="utf-8")
    rc = adapt.run(_ns(tmp_path, values_from=values))
    assert rc == 0
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == "project=demo\n"


def test_upper_snake_markers_no_longer_substituted(tmp_path, capsys):
    """Legacy ``<adapt:PROJECT_NAME>`` is left in place with a warning (AC14)."""
    _seed_repo(tmp_path, {"AGENTS.md": "project=<adapt:PROJECT_NAME>\n"})
    values = tmp_path / "values.toml"
    # Provide an UPPER value AND a lowercase value. The UPPER form
    # should NOT be substituted; the file should be unchanged.
    values.write_text(
        '[markers]\nPROJECT_NAME = "WRONG"\nproject-name = "demo"\n',
        encoding="utf-8",
    )
    rc = adapt.run(_ns(tmp_path, values_from=values))
    assert rc == 0
    # Marker left in place.
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == (
        "project=<adapt:PROJECT_NAME>\n"
    )
    # Single warning on stderr naming the legacy form.
    err = capsys.readouterr().err
    assert "legacy UPPER_SNAKE marker" in err
