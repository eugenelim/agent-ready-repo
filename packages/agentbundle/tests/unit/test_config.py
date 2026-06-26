"""T1b: TOML loaders for the CLI's persistent on-disk artifacts."""

from __future__ import annotations

import pytest
from pathlib import Path

from agentbundle import config


def test_load_pack_toml_returns_dict_for_core_pack(tmp_path):
    pack_toml = tmp_path / "pack.toml"
    pack_toml.write_text(
        """
[pack]
name = "core"
version = "0.1.0"

[pack.adapter-contract]
version = "0.1"
""",
        encoding="utf-8",
    )
    parsed = config.load_pack_toml(pack_toml)
    assert parsed["pack"]["name"] == "core"
    assert config.pack_spec_version(parsed) == "0.1"


def test_load_pack_toml_raises_typed_error_on_malformed(tmp_path):
    pack_toml = tmp_path / "pack.toml"
    pack_toml.write_text("this = is = not toml", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="not valid TOML"):
        config.load_pack_toml(pack_toml)


def test_load_pack_toml_raises_on_missing_file(tmp_path):
    with pytest.raises(config.ConfigError, match="not found"):
        config.load_pack_toml(tmp_path / "nope.toml")


def test_load_state_returns_empty_state_for_absent_file(tmp_path):
    state = config.load_state(tmp_path / ".agentbundle-state.toml")
    assert state.schema_version == config.STATE_SCHEMA_VERSION
    assert state.packs == {}


def test_state_round_trip_preserves_per_pack_files(tmp_path):
    state_toml = tmp_path / ".agentbundle-state.toml"
    state_toml.write_text(
        """
schema-version = "0.4"

[pack.core.adapters.claude-code]
installed-version = "0.2.0"
source = "agent-ready-repo"
install-route = "cli"
scope = "repo"
primitives = ["skill", "agent", "hook-body", "hook-wiring", "command"]

[pack.core.adapters.claude-code.files]
"AGENTS.md" = { sha = "abc123", from-pack-version = "0.2.0" }
"docs/CHARTER.md" = { sha = "def456", from-pack-version = "0.2.0" }
""",
        encoding="utf-8",
    )

    state = config.load_state(state_toml)
    assert state.schema_version == "0.4"
    assert state.has_pack("core")
    core = state.row("core", "claude-code")
    assert core.installed_version == "0.2.0"
    assert core.install_route == "cli"
    assert set(core.primitives) == {"skill", "agent", "hook-body", "hook-wiring", "command"}
    assert core.file_sha("AGENTS.md") == "abc123"
    assert core.file_sha("docs/CHARTER.md") == "def456"

    # Dump and reload round-trip — fields preserved.
    serialised = config.dump_state(state)
    re_state = config.load_state(_write(tmp_path / "again.toml", serialised))
    assert re_state.row("core", "claude-code").file_sha("AGENTS.md") == "abc123"
    assert re_state.row("core", "claude-code").file_sha("docs/CHARTER.md") == "def456"


def test_state_round_trip_preserves_mixed_version_primitives(tmp_path):
    state_toml = tmp_path / ".agentbundle-state.toml"
    state_toml.write_text(
        """
schema-version = "0.4"

[pack.core.adapters.claude-code]
installed-version = "0.2.0"
source = "agent-ready-repo"
install-route = "cli"
scope = "repo"
primitives = ["skill"]

[pack.core.adapters.claude-code.files]
"x" = { sha = "0", from-pack-version = "0.2.0" }

[pack.core.adapters.claude-code.skill.work-loop]
version = "0.3.0"
""",
        encoding="utf-8",
    )
    state = config.load_state(state_toml)
    assert state.row("core", "claude-code").primitive_versions == {
        "skill": {"work-loop": "0.3.0"}
    }
    # Round-trip preserves the override.
    again = config.load_state(_write(tmp_path / "again.toml", config.dump_state(state)))
    assert again.row("core", "claude-code").primitive_versions == {
        "skill": {"work-loop": "0.3.0"}
    }


def test_load_state_raises_on_malformed_toml(tmp_path):
    p = tmp_path / "state.toml"
    p.write_text("not = = toml", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="not valid TOML"):
        config.load_state(p)


def test_load_values_from_returns_string_dict(tmp_path):
    p = tmp_path / "values.toml"
    p.write_text(
        """
[values]
PROJECT_NAME = "demo"
OWNER = "octocat"
""",
        encoding="utf-8",
    )
    values = config.load_values_from(p)
    assert values == {"PROJECT_NAME": "demo", "OWNER": "octocat"}


def test_load_values_from_rejects_non_string(tmp_path):
    p = tmp_path / "values.toml"
    p.write_text(
        """
[values]
COUNT = 3
""",
        encoding="utf-8",
    )
    with pytest.raises(config.ConfigError, match="must be a string"):
        config.load_values_from(p)


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# State-file corruption tests (Concern 3 from quality-engineer review)
# ---------------------------------------------------------------------------


def test_load_state_rejects_non_string_schema_version(tmp_path):
    p = tmp_path / "state.toml"
    p.write_text("schema-version = 42\n", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="schema-version"):
        config.load_state(p)


def test_load_state_rejects_pack_not_a_table(tmp_path):
    p = tmp_path / "state.toml"
    p.write_text(
        'schema-version = "0.1"\n[pack]\nlooks-like-a-table-but-isnt = "nope"\n[pack.x]\ninstalled-version = ""\n',
        encoding="utf-8",
    )
    # The above IS a valid TOML structure; for an actually-broken case:
    p.write_text(
        'schema-version = "0.4"\n[pack.x.adapters.claude-code]\n'
        'installed-version = ""\nfiles = "not-a-table"\n',
        encoding="utf-8",
    )
    with pytest.raises(config.ConfigError, match="files"):
        config.load_state(p)
