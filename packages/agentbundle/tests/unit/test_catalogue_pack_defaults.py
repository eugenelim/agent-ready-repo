"""Tests for catalogue-pack-defaults spec (RFC-0074, ADR-0058, ADR-0059).

Covers:
  - T1: catalogue.schema.json accepts user-dir and [pack-defaults.*]
  - T2: CatalogueConfig.user_dir / pack_defaults parsing and validation
  - T3: compile_defaults sorted [pack-defaults.*] sections
  - T4: check_defaults drift detection (via byte comparison) including pack-defaults
  - T5: PackState.user_root serialization round-trip
  - T6: install user-root plumbing (data-flow; full integration test deferred)
"""

from __future__ import annotations

import json
from pathlib import Path

import agentbundle.catalogue_tooling.defaults as _defaults_module
import pytest
from agentbundle.catalogue_tooling.config import (
    AgentbundleDistribution,
    ArtifactoryConfig,
    CatalogueBuild,
    CatalogueConfig,
    CatalogueConfigError,
    CataloguePackage,
    CataloguePaths,
    DistributionConfig,
)
from agentbundle.catalogue_tooling.defaults import compile_defaults

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    user_dir: str = "~/.agentbundle",
    pack_defaults: dict | None = None,
) -> CatalogueConfig:
    return CatalogueConfig(
        schema=1,
        name="test-catalogue",
        display_name="Test",
        description="A test catalogue.",
        minimum_agentbundle_version="0.1.0",
        paths=CataloguePaths(
            packs="packs",
            profiles="profiles",
            contracts="contracts",
            marketplace="marketplace.json",
            build_output="build",
        ),
        build=CatalogueBuild(
            recipes=["default"],
            self_host=False,
            claude_plugin_branch="main",
            marketplace_description="",
        ),
        package=CataloguePackage(include=[], required=[]),
        distribution=DistributionConfig(
            agentbundle=AgentbundleDistribution(
                install_defaults_output="agentbundle/_data/install-defaults.toml",
                preferred_adapter="claude-code",
                default_source="",
                artifactory=ArtifactoryConfig(enabled=False),
            )
        ),
        user_dir=user_dir,
        pack_defaults=pack_defaults or {},
    )


def _schema() -> dict:
    here = Path(__file__).resolve()
    # tests/unit/ -> tests/ -> packages/agentbundle/ -> agentbundle/_data/
    schema_path = here.parents[2] / "agentbundle" / "_data" / "catalogue.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# T1: JSON schema accepts new fields
# ---------------------------------------------------------------------------


def test_schema_accepts_user_dir():
    from agentbundle.build.validate import validate

    schema = _schema()
    raw = {
        "schema": 1,
        "catalogue": {
            "name": "test",
            "display-name": "T",
            "description": "D",
            "minimum-agentbundle-version": "0.1.0",
            "user-dir": "~/custom",
            "paths": {
                "packs": "p", "profiles": "r", "contracts": "c",
                "marketplace": "m.json", "build-output": "b",
            },
            "build": {
                "recipes": ["default"], "self-host": False,
                "claude-plugin-branch": "main", "marketplace-description": "",
            },
            "package": {"include": [], "required": []},
        },
        "distribution": {
            "agentbundle": {
                "install-defaults-output": "x.toml",
                "preferred-adapter": "claude-code",
                "default-source": "",
                "artifactory": {"enabled": False},
            }
        },
    }
    errors = validate(raw, schema)
    assert not errors, f"Schema rejected valid user-dir: {errors}"


def test_schema_accepts_pack_defaults():
    from agentbundle.build.validate import validate

    schema = _schema()
    raw = {
        "schema": 1,
        "pack-defaults": {
            "atlassian": {"url": "https://jira.example.com/"},
        },
        "catalogue": {
            "name": "test",
            "display-name": "T",
            "description": "D",
            "minimum-agentbundle-version": "0.1.0",
            "paths": {
                "packs": "p", "profiles": "r", "contracts": "c",
                "marketplace": "m.json", "build-output": "b",
            },
            "build": {
                "recipes": ["default"], "self-host": False,
                "claude-plugin-branch": "main", "marketplace-description": "",
            },
            "package": {"include": [], "required": []},
        },
        "distribution": {
            "agentbundle": {
                "install-defaults-output": "x.toml",
                "preferred-adapter": "claude-code",
                "default-source": "",
                "artifactory": {"enabled": False},
            }
        },
    }
    errors = validate(raw, schema)
    assert not errors, f"Schema rejected valid pack-defaults: {errors}"


def test_schema_rejects_unknown_top_level():
    from agentbundle.build.validate import validate

    schema = _schema()
    raw = {
        "schema": 1,
        "unknown-section": {},
        "catalogue": {
            "name": "test",
            "display-name": "T",
            "description": "D",
            "minimum-agentbundle-version": "0.1.0",
            "paths": {
                "packs": "p", "profiles": "r", "contracts": "c",
                "marketplace": "m.json", "build-output": "b",
            },
            "build": {
                "recipes": ["default"], "self-host": False,
                "claude-plugin-branch": "main", "marketplace-description": "",
            },
            "package": {"include": [], "required": []},
        },
        "distribution": {
            "agentbundle": {
                "install-defaults-output": "x.toml",
                "preferred-adapter": "claude-code",
                "default-source": "",
                "artifactory": {"enabled": False},
            }
        },
    }
    errors = validate(raw, schema)
    assert errors, "Schema should reject unknown-section"


# ---------------------------------------------------------------------------
# T2: CatalogueConfig parsing
# ---------------------------------------------------------------------------


def test_user_dir_default():
    config = _make_config()
    assert config.user_dir == "~/.agentbundle"


def test_user_dir_custom():
    config = _make_config(user_dir="~/custom-dir")
    assert config.user_dir == "~/custom-dir"


def test_pack_defaults_populated():
    config = _make_config(pack_defaults={"atlassian": {"url": "https://jira.example.com/"}})
    assert config.pack_defaults == {"atlassian": {"url": "https://jira.example.com/"}}


def test_load_catalogue_config_user_dir(tmp_path):
    """load_catalogue_config parses user-dir."""

    toml_content = """\
schema = 1

[catalogue]
name = "test-catalogue"
display-name = "T"
description = "D"
minimum-agentbundle-version = "0.1.0"
user-dir = "~/custom"

[catalogue.paths]
packs = "packs"
profiles = "profiles"
contracts = "contracts"
marketplace = "marketplace.json"
build-output = "build"

[catalogue.build]
recipes = ["default"]
self-host = false
claude-plugin-branch = "main"
marketplace-description = ""

[catalogue.package]
include = []
required = []

[distribution.agentbundle]
install-defaults-output = "x.toml"
preferred-adapter = "claude-code"
default-source = "git+https://github.com/example/catalogue"

[distribution.agentbundle.artifactory]
enabled = false
"""
    (tmp_path / "catalogue.toml").write_text(toml_content, encoding="utf-8")

    from agentbundle.catalogue_tooling.config import load_catalogue_config

    config = load_catalogue_config(tmp_path)
    assert config is not None
    assert config.user_dir == "~/custom"


def test_load_catalogue_config_rejects_absolute_user_dir(tmp_path):
    toml_content = """\
schema = 1

[catalogue]
name = "test-catalogue"
display-name = "T"
description = "D"
minimum-agentbundle-version = "0.1.0"
user-dir = "/opt/shared"

[catalogue.paths]
packs = "packs"
profiles = "profiles"
contracts = "contracts"
marketplace = "marketplace.json"
build-output = "build"

[catalogue.build]
recipes = ["default"]
self-host = false
claude-plugin-branch = "main"
marketplace-description = ""

[catalogue.package]
include = []
required = []

[distribution.agentbundle]
install-defaults-output = "x.toml"
preferred-adapter = "claude-code"
default-source = "git+https://github.com/example/catalogue"

[distribution.agentbundle.artifactory]
enabled = false
"""
    (tmp_path / "catalogue.toml").write_text(toml_content, encoding="utf-8")

    from agentbundle.catalogue_tooling.config import load_catalogue_config

    with pytest.raises(CatalogueConfigError, match="user-dir"):
        load_catalogue_config(tmp_path)


def test_load_catalogue_config_rejects_reserved_slug(tmp_path):
    toml_content = """\
schema = 1

[catalogue]
name = "test-catalogue"
display-name = "T"
description = "D"
minimum-agentbundle-version = "0.1.0"

[catalogue.paths]
packs = "packs"
profiles = "profiles"
contracts = "contracts"
marketplace = "marketplace.json"
build-output = "build"

[catalogue.build]
recipes = ["default"]
self-host = false
claude-plugin-branch = "main"
marketplace-description = ""

[catalogue.package]
include = []
required = []

[distribution.agentbundle]
install-defaults-output = "x.toml"
preferred-adapter = "claude-code"
default-source = "git+https://github.com/example/catalogue"

[distribution.agentbundle.artifactory]
enabled = false

[pack-defaults.bin]
something = "value"
"""
    (tmp_path / "catalogue.toml").write_text(toml_content, encoding="utf-8")

    from agentbundle.catalogue_tooling.config import load_catalogue_config

    with pytest.raises(CatalogueConfigError, match="reserved"):
        load_catalogue_config(tmp_path)


# ---------------------------------------------------------------------------
# T3: compile_defaults sorted pack-defaults sections
# ---------------------------------------------------------------------------


def test_compile_defaults_pack_defaults_sorted_by_pack():
    config = _make_config(pack_defaults={
        "github": {"org": "example-org"},
        "atlassian": {"url": "https://jira.example.com/"},
    })
    output = compile_defaults(config)
    idx_atlassian = output.index("[pack-defaults.atlassian]")
    idx_github = output.index("[pack-defaults.github]")
    assert idx_atlassian < idx_github, "atlassian should appear before github (alphabetical)"


def test_compile_defaults_pack_defaults_keys_sorted():
    config = _make_config(pack_defaults={
        "atlassian": {"url": "https://jira.example.com/", "project": "PROJ"},
    })
    output = compile_defaults(config)
    idx_project = output.index("project =")
    idx_url = output.index("url =")
    assert idx_project < idx_url, "project should appear before url (alphabetical)"


def test_compile_defaults_idempotent():
    config = _make_config(pack_defaults={
        "github": {"org": "example-org"},
        "atlassian": {"url": "https://jira.example.com/"},
    })
    first = compile_defaults(config)
    second = compile_defaults(config)
    assert first == second, "compile_defaults must be idempotent"


def test_compile_defaults_no_pack_defaults():
    config = _make_config()
    output = compile_defaults(config)
    assert "pack-defaults" not in output


# ---------------------------------------------------------------------------
# T5: PackState.user_root round-trip
# ---------------------------------------------------------------------------


def test_packstate_user_root_default():
    from agentbundle.config import PackState

    ps = PackState(installed_version="1.0.0")
    assert ps.user_root == "~/.agentbundle"


def test_packstate_user_root_serialization():
    from agentbundle.config import PackState, State, dump_state

    ps = PackState(installed_version="1.0.0", user_root="~/custom")
    state = State()
    state.packs[("atlassian", "claude-code")] = ps
    output = dump_state(state)
    assert 'user-root = "~/custom"' in output


def test_packstate_user_root_deserialization():
    import tempfile

    from agentbundle.config import STATE_SCHEMA_VERSION, load_state

    toml = f"""\
schema-version = "{STATE_SCHEMA_VERSION}"

[pack.atlassian.adapters.claude-code]
installed-version = "1.0.0"
install-route = "cli"
scope = "user"
user-root = "~/custom"
primitives = []

[pack.atlassian.adapters.claude-code.files]
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, encoding="utf-8"
    ) as f:
        f.write(toml)
        fpath = f.name
    try:
        state = load_state(Path(fpath))
        ps = state.packs[("atlassian", "claude-code")]
        assert ps.user_root == "~/custom"
    finally:
        Path(fpath).unlink()


def test_packstate_user_root_default_on_missing_key():
    import tempfile

    from agentbundle.config import STATE_SCHEMA_VERSION, load_state

    toml = f"""\
schema-version = "{STATE_SCHEMA_VERSION}"

[pack.atlassian.adapters.claude-code]
installed-version = "1.0.0"
install-route = "cli"
scope = "user"
primitives = []

[pack.atlassian.adapters.claude-code.files]
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, encoding="utf-8"
    ) as f:
        f.write(toml)
        fpath = f.name
    try:
        state = load_state(Path(fpath))
        ps = state.packs[("atlassian", "claude-code")]
        assert ps.user_root == "~/.agentbundle"
    finally:
        Path(fpath).unlink()


# ---------------------------------------------------------------------------
# T2 additions: traversal check and e2e pack_defaults parse
# ---------------------------------------------------------------------------

_FIXTURE_TOML_BASE = """\
schema = 1

[catalogue]
name = "test-catalogue"
display-name = "T"
description = "D"
minimum-agentbundle-version = "0.1.0"

[catalogue.paths]
packs = "packs"
profiles = "profiles"
contracts = "contracts"
marketplace = "marketplace.json"
build-output = "build"

[catalogue.build]
recipes = ["default"]
self-host = false
claude-plugin-branch = "main"
marketplace-description = ""

[catalogue.package]
include = []
required = []

[distribution.agentbundle]
install-defaults-output = "x.toml"
preferred-adapter = "claude-code"
default-source = "git+https://github.com/example/catalogue"

[distribution.agentbundle.artifactory]
enabled = false
"""


def test_load_catalogue_config_rejects_traversal_user_dir(tmp_path):
    """user-dir = ~/../../etc is rejected at load time (path traversal)."""
    toml_content = _FIXTURE_TOML_BASE.replace(
        "[catalogue.paths]",
        'user-dir = "~/../../etc"\n\n[catalogue.paths]',
    )
    (tmp_path / "catalogue.toml").write_text(toml_content, encoding="utf-8")

    from agentbundle.catalogue_tooling.config import load_catalogue_config

    with pytest.raises(CatalogueConfigError, match=r"\.\."):
        load_catalogue_config(tmp_path)


def test_load_catalogue_config_pack_defaults_parsed(tmp_path):
    """load_catalogue_config returns correct pack_defaults from catalogue.toml."""
    toml_content = (
        _FIXTURE_TOML_BASE
        + "\n[pack-defaults.atlassian]\nurl = \"https://jira.example.com/\"\n"
    )
    (tmp_path / "catalogue.toml").write_text(toml_content, encoding="utf-8")

    from agentbundle.catalogue_tooling.config import load_catalogue_config

    config = load_catalogue_config(tmp_path)
    assert config is not None
    assert config.pack_defaults == {"atlassian": {"url": "https://jira.example.com/"}}


# ---------------------------------------------------------------------------
# T4: check_defaults catches pack-defaults drift
# ---------------------------------------------------------------------------


def test_check_defaults_pack_defaults_drift(tmp_path, monkeypatch):
    """check_defaults exits non-zero when baked file has hand-edited pack-defaults key."""
    from agentbundle.catalogue_tooling.defaults import check_defaults

    config = _make_config(pack_defaults={"atlassian": {"url": "https://jira.example.com/"}})
    monkeypatch.setattr(_defaults_module, "load_catalogue_config", lambda root: config)

    # Write a baked file with a hand-edited extra key — drifted from compile_defaults output.
    correct = compile_defaults(config)
    drifted = correct + "\nextra-key = \"injected\"\n"
    (tmp_path / "install-defaults.toml").write_text(drifted, encoding="utf-8")

    result = check_defaults(tmp_path)
    assert result.ok is False


# ---------------------------------------------------------------------------
# T6: install user-root plumbing (data-flow unit test)
# ---------------------------------------------------------------------------


def test_install_user_root_plumbing(tmp_path):
    """Catalogue user-dir flows correctly to PackState.user_root.

    Tests the data-flow that install.py implements (load catalogue config →
    _catalogue_user_dir → PackState(user_root=...)).  A full integration test
    that runs agentbundle install against a real pack is deferred.
    """
    toml_content = _FIXTURE_TOML_BASE.replace(
        "[catalogue.paths]",
        'user-dir = "~/custom-install"\n\n[catalogue.paths]',
    )
    (tmp_path / "catalogue.toml").write_text(toml_content, encoding="utf-8")

    from agentbundle.catalogue_tooling.config import load_catalogue_config
    from agentbundle.config import PackState, State, dump_state

    # Step 1: load catalogue config — simulates install.py lines 280-292
    config = load_catalogue_config(tmp_path)
    assert config is not None
    assert config.user_dir == "~/custom-install"

    # Step 2: PackState receives user_root — simulates install.py line 1140
    ps = PackState(installed_version="1.0.0", user_root=config.user_dir)
    assert ps.user_root == "~/custom-install"

    # Step 3: serialization round-trip verifies the value survives dump
    state = State()
    state.packs[("atlassian", "claude-code")] = ps
    serialized = dump_state(state)
    assert 'user-root = "~/custom-install"' in serialized
