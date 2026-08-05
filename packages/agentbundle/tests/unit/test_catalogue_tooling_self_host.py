"""Unit tests for agentbundle.catalogue_tooling.self_host.

Tests check_self_host and write_self_host.
"""

from __future__ import annotations

from unittest.mock import patch

from agentbundle.catalogue_tooling.results import SelfHostResult
from agentbundle.catalogue_tooling.self_host import check_self_host, write_self_host

# Canonical patch target: run_self_host is imported lazily inside each
# function via ``from agentbundle.build.self_host import run_self_host``.
# Patching the module-level attribute on the source module is the correct
# approach; the lazy from-import picks up the patched object each call.
_RUN_SELF_HOST = "agentbundle.build.self_host.run_self_host"

# Minimal valid catalogue.toml for tests that need load_catalogue_config to
# succeed. Mirrors _VALID_BASE in test_catalogue_tooling_foundation.py.
_VALID_CATALOGUE_TOML = (
    "schema = 1\n"
    "[catalogue]\n"
    "name = 'test'\ndisplay-name = 'T'\ndescription = 't'\n"
    "minimum-agentbundle-version = '0.14.0'\n"
    "[catalogue.paths]\n"
    "packs = 'packs'\nprofiles = 'profiles'\ncontracts = 'contracts'\n"
    "marketplace = '.claude-plugin/marketplace.json'\nbuild-output = 'dist'\n"
    "[catalogue.build]\n"
    "recipes = ['default']\nself-host = false\nclaude-plugin-branch = 'main'\n"
    "marketplace-description = 't'\n"
    "[catalogue.package]\n"
    "include = ['packs/core']\nrequired = ['packs/core']\n"
    "[distribution.agentbundle]\n"
    "install-defaults-output = 'agentbundle/_data/install-defaults.toml'\n"
    "preferred-adapter = 'claude-code'\n"
    "default-source = 'git+https://github.com/example/repo'\n"
    "[distribution.agentbundle.artifactory]\nenabled = false\n"
)


# ---------------------------------------------------------------------------
# check_self_host
# ---------------------------------------------------------------------------


def test_check_self_host_no_catalogue_toml(tmp_path):
    """No catalogue.toml: check_self_host returns SelfHostResult with ok=False."""
    with patch(_RUN_SELF_HOST, return_value=1):
        result = check_self_host(tmp_path)

    assert isinstance(result, SelfHostResult)
    assert result.ok is False


def test_check_delegates_to_run_self_host(tmp_path):
    """check_self_host calls run_self_host with dry_run=True and force=False."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        check_self_host(tmp_path)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("dry_run") is True
    assert kwargs.get("force") is False


# ---------------------------------------------------------------------------
# write_self_host
# ---------------------------------------------------------------------------


def test_write_self_host_no_catalogue_toml(tmp_path):
    """No catalogue.toml: write_self_host returns SelfHostResult with ok=False."""
    with patch(_RUN_SELF_HOST, return_value=1):
        result = write_self_host(tmp_path)

    assert isinstance(result, SelfHostResult)
    assert result.ok is False


def test_write_delegates_to_run_self_host(tmp_path):
    """write_self_host calls run_self_host with dry_run=False."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        write_self_host(tmp_path)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("dry_run") is False


def test_write_force_propagated(tmp_path):
    """write_self_host(root, force=True) passes force=True to run_self_host."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        write_self_host(tmp_path, force=True)

    _, kwargs = mock_run.call_args
    assert kwargs.get("force") is True


# ---------------------------------------------------------------------------
# preferred_adapter propagation (AC3)
# ---------------------------------------------------------------------------


def _write_catalogue_toml(tmp_path, preferred_adapter: str) -> None:
    content = _VALID_CATALOGUE_TOML.replace(
        "preferred-adapter = 'claude-code'",
        f"preferred-adapter = '{preferred_adapter}'",
    )
    (tmp_path / "catalogue.toml").write_text(content)


def test_check_passes_preferred_adapter_to_run_self_host(tmp_path):
    """check_self_host reads preferred-adapter from catalogue.toml and passes it through."""
    _write_catalogue_toml(tmp_path, "kiro-ide")
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        check_self_host(tmp_path)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("preferred_adapter") == "kiro-ide"


def test_write_passes_preferred_adapter_to_run_self_host(tmp_path):
    """write_self_host reads preferred-adapter from catalogue.toml and passes it through."""
    _write_catalogue_toml(tmp_path, "kiro-ide")
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        write_self_host(tmp_path)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("preferred_adapter") == "kiro-ide"


def test_check_no_catalogue_toml_passes_none_preferred_adapter(tmp_path):
    """No catalogue.toml: preferred_adapter=None is passed to run_self_host."""
    with patch(_RUN_SELF_HOST, return_value=0) as mock_run:
        check_self_host(tmp_path)

    _, kwargs = mock_run.call_args
    assert kwargs.get("preferred_adapter") is None


# ---------------------------------------------------------------------------
# _effective_adapters unit tests (AC1 + AC2)
# ---------------------------------------------------------------------------


def test_effective_adapters_unknown_adapter_uses_only_preferred():
    """AC1: preferred_adapter not in SELF_HOST_ADAPTERS → singleton set."""
    from agentbundle.build.self_host import SELF_HOST_ADAPTERS, _effective_adapters

    # kiro-ide is not in SELF_HOST_ADAPTERS for this repo's recipe.
    assert "kiro-ide" not in SELF_HOST_ADAPTERS
    result = _effective_adapters("kiro-ide")
    assert result == ("kiro-ide",)


def test_effective_adapters_known_adapter_uses_full_list():
    """AC2: preferred_adapter in SELF_HOST_ADAPTERS → full allow-list unchanged."""
    from agentbundle.build.self_host import SELF_HOST_ADAPTERS, _effective_adapters

    assert "claude-code" in SELF_HOST_ADAPTERS
    result = _effective_adapters("claude-code")
    assert result == SELF_HOST_ADAPTERS


def test_effective_adapters_none_uses_full_list():
    """AC2: preferred_adapter=None → full allow-list unchanged."""
    from agentbundle.build.self_host import SELF_HOST_ADAPTERS, _effective_adapters

    assert _effective_adapters(None) == SELF_HOST_ADAPTERS


# ---------------------------------------------------------------------------
# _project_all_adapters direct verification (AC1)
# ---------------------------------------------------------------------------


def test_project_all_adapters_restricts_to_preferred_when_outside_self_host_adapters(tmp_path):
    """AC1: _project_all_adapters with kiro-ide preferred_adapter calls only kiro-ide,
    not claude-code or codex, even when all three are present in the contract."""
    from unittest.mock import MagicMock

    from agentbundle.build.self_host import SELF_HOST_ADAPTERS, _project_all_adapters

    assert "kiro-ide" not in SELF_HOST_ADAPTERS

    output_root = tmp_path / "output"
    output_root.mkdir()
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    # Contract lists all three adapters; only kiro-ide should be projected.
    contract = {"adapter": {"claude-code": {}, "codex": {}, "kiro-ide": {}}}

    mock_kiro = MagicMock()
    mock_claude = MagicMock()
    mock_codex = MagicMock()
    patched_registry = {
        "kiro_ide": mock_kiro,
        "claude_code": mock_claude,
        "codex": mock_codex,
    }

    with patch("agentbundle.build.self_host.registry", patched_registry):
        _project_all_adapters(output_root, packs_dir, contract, preferred_adapter="kiro-ide")

    mock_kiro.project_packs.assert_called_once()
    mock_claude.project_packs.assert_not_called()
    mock_codex.project_packs.assert_not_called()
