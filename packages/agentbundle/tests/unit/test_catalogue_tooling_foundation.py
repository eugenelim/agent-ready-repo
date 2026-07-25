"""Foundation tests for catalogue_tooling package (T1–T4).

Verification modes per plan.md:
  T1 — TDD: import, result-type structure, stub raises
  T2 — TDD: config loading and all 13 validation failure paths
  T3 — Goal-based: schema drift check + repo catalogue.toml valid
  T4 — Goal-based: CLI subcommand groups registered
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# T1: Package skeleton + result types
# ---------------------------------------------------------------------------


def test_catalogue_tooling_imports():
    """AC1: all 11 modules import without ImportError."""
    modules = [
        "agentbundle.catalogue_tooling",
        "agentbundle.catalogue_tooling.config",
        "agentbundle.catalogue_tooling.diagnostics",
        "agentbundle.catalogue_tooling.results",
        "agentbundle.catalogue_tooling.lint",
        "agentbundle.catalogue_tooling.verify",
        "agentbundle.catalogue_tooling.build",
        "agentbundle.catalogue_tooling.self_host",
        "agentbundle.catalogue_tooling.package",
        "agentbundle.catalogue_tooling.archive",
        "agentbundle.catalogue_tooling.defaults",
    ]
    import importlib

    for name in modules:
        importlib.import_module(name)


def test_result_types_structure():
    """AC3: result types export required fields and subtype relationships."""
    from agentbundle.catalogue_tooling.results import (
        BuildResult,
        CommandResult,
        Diagnostic,
        LintResult,
        PackageResult,
        SelfHostResult,
        Severity,
        SyncDefaultsResult,
        VerifyResult,
    )

    # Severity has ERROR, WARN, INFO
    assert hasattr(Severity, "ERROR")
    assert hasattr(Severity, "WARN")
    assert hasattr(Severity, "INFO")

    # Diagnostic has all 9 fields
    import dataclasses

    diag_fields = {f.name for f in dataclasses.fields(Diagnostic)}
    # Diagnostic has 8 fields per spec AC3 and results.py
    for field in ("code", "severity", "pack", "path", "line", "col", "message", "remediation"):
        assert field in diag_fields, f"Diagnostic missing field: {field}"

    # CommandResult has ok, diagnostics, schema_version, command, operation,
    # agentbundle_version, catalogue_schema_version
    cr_fields = {f.name for f in dataclasses.fields(CommandResult)}
    for field in (
        "ok",
        "diagnostics",
        "schema_version",
        "command",
        "operation",
        "agentbundle_version",
        "catalogue_schema_version",
    ):
        assert field in cr_fields, f"CommandResult missing field: {field}"

    # Subtypes are subclasses of CommandResult
    for subtype in (LintResult, VerifyResult, BuildResult, SelfHostResult, PackageResult, SyncDefaultsResult):
        assert issubclass(subtype, CommandResult), f"{subtype.__name__} not subclass of CommandResult"


def test_stub_raises_not_implemented():
    """AC2: stub functions raise NotImplementedError."""
    from agentbundle.catalogue_tooling.lint import lint_catalogue
    from agentbundle.catalogue_tooling.verify import verify_catalogue
    from agentbundle.catalogue_tooling.build import build_catalogue
    from agentbundle.catalogue_tooling.package import package_catalogue

    with pytest.raises(NotImplementedError):
        lint_catalogue(Path("."))
    with pytest.raises(NotImplementedError):
        verify_catalogue(Path("."))
    with pytest.raises(NotImplementedError):
        build_catalogue(Path("."), Path("."))
    with pytest.raises(NotImplementedError):
        package_catalogue(Path("."))


# ---------------------------------------------------------------------------
# T2: config.py validation
# ---------------------------------------------------------------------------


def _minimal_valid_toml(overrides: dict | None = None) -> str:
    """Build a minimal valid catalogue.toml TOML string."""
    base = {
        "schema": 1,
        "catalogue": {
            "name": "test-catalogue",
            "display-name": "Test Catalogue",
            "description": "A test catalogue",
            "minimum-agentbundle-version": "0.14.0",
            "paths": {
                "packs": "packs",
                "profiles": "profiles",
                "contracts": "docs/contracts",
                "marketplace": ".claude-plugin/marketplace.json",
                "build-output": "dist",
            },
            "build": {
                "recipes": ["default"],
                "self-host": False,
                "claude-plugin-branch": "main",
                "marketplace-description": "Test",
            },
            "package": {
                "include": ["packs/core"],
                "required": ["packs/core"],
            },
        },
        "distribution": {
            "agentbundle": {
                "install-defaults-output": "agentbundle/_data/install-defaults.toml",
                "preferred-adapter": "claude-code",
                "default-source": "git+https://github.com/example/catalogue",
                "artifactory": {
                    "enabled": False,
                },
            }
        },
    }
    if overrides:
        _deep_merge(base, overrides)
    import tomllib as _tl  # noqa: F401 — stdlib write is not available; build via string
    # Build TOML manually for the base case
    return _dict_to_toml(base)


def _deep_merge(base: dict, overrides: dict) -> None:
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def _dict_to_toml(d: dict, prefix: str = "") -> str:
    """Minimal TOML serializer for test fixture generation (no arrays of tables)."""
    scalars: list[str] = []
    subsections: list[str] = []

    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            inner = _dict_to_toml(v, prefix=key)
            subsections.append(f"\n[{key}]\n{inner}")
        elif isinstance(v, bool):
            scalars.append(f"{k} = {'true' if v else 'false'}")
        elif isinstance(v, int):
            scalars.append(f"{k} = {v}")
        elif isinstance(v, str):
            scalars.append(f"{k} = {v!r}")
        elif isinstance(v, list):
            items = ", ".join(repr(i) if isinstance(i, str) else str(i) for i in v)
            scalars.append(f"{k} = [{items}]")

    return "\n".join(scalars) + "".join(subsections)


def _write_toml(tmp_path: Path, content: str) -> Path:
    f = tmp_path / "catalogue.toml"
    f.write_text(content, encoding="utf-8")
    return tmp_path


def test_config_absent_returns_none(tmp_path):
    """AC5: absent catalogue.toml returns None."""
    from agentbundle.catalogue_tooling.config import load_catalogue_config

    result = load_catalogue_config(tmp_path)
    assert result is None


def test_config_valid_public(tmp_path):
    """AC5/AC6: valid minimal public config parses without error."""
    from agentbundle.catalogue_tooling.config import load_catalogue_config

    content = _minimal_valid_toml()
    _write_toml(tmp_path, content)
    result = load_catalogue_config(tmp_path)
    assert result is not None
    assert result.name == "test-catalogue"


def test_config_valid_enterprise(tmp_path):
    """AC6: valid enterprise config with Artifactory enabled parses without error."""
    from agentbundle.catalogue_tooling.config import load_catalogue_config

    # Build enterprise config with Artifactory enabled
    content = (
        "schema = 1\n"
        "\n"
        "[catalogue]\n"
        "name = 'my-catalogue'\n"
        "display-name = 'My Catalogue'\n"
        "description = 'Enterprise catalogue'\n"
        "minimum-agentbundle-version = '0.14.0'\n"
        "\n"
        "[catalogue.paths]\n"
        "packs = 'packs'\n"
        "profiles = 'profiles'\n"
        "contracts = 'docs/contracts'\n"
        "marketplace = '.claude-plugin/marketplace.json'\n"
        "build-output = 'dist'\n"
        "\n"
        "[catalogue.build]\n"
        "recipes = ['default']\n"
        "self-host = false\n"
        "claude-plugin-branch = 'main'\n"
        "marketplace-description = 'Ent'\n"
        "\n"
        "[catalogue.package]\n"
        "include = ['packs/core']\n"
        "required = ['packs/core']\n"
        "\n"
        "[distribution.agentbundle]\n"
        "install-defaults-output = 'agentbundle/_data/install-defaults.toml'\n"
        "preferred-adapter = 'claude-code'\n"
        "default-source = 'git+https://github.com/example/repo'\n"
        "\n"
        "[distribution.agentbundle.artifactory]\n"
        "enabled = true\n"
        "base-url = 'https://art.example.com'\n"
        "repository = 'my-repo'\n"
        "bundle = 'engineering'\n"
    )
    _write_toml(tmp_path, content)
    result = load_catalogue_config(tmp_path)
    assert result is not None


def test_config_bad_schema_integer(tmp_path):
    """AC6: non-integer schema field raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = (
        "schema = 2\n"  # only 1 is valid
        "[catalogue]\n"
        "name = 'x'\n"
        "display-name = 'X'\n"
        "description = 'x'\n"
        "minimum-agentbundle-version = '0.14.0'\n"
        "[catalogue.paths]\n"
        "packs = 'packs'\nprofiles = 'profiles'\ncontracts = 'docs/contracts'\n"
        "marketplace = '.claude-plugin/marketplace.json'\nbuild-output = 'dist'\n"
        "[catalogue.build]\n"
        "recipes = ['default']\nself-host = false\nclaude-plugin-branch = 'main'\n"
        "marketplace-description = 'x'\n"
        "[catalogue.package]\n"
        "include = ['packs/core']\nrequired = ['packs/core']\n"
        "[distribution.agentbundle]\n"
        "install-defaults-output = 'agentbundle/_data/install-defaults.toml'\n"
        "preferred-adapter = 'claude-code'\n"
        "default-source = 'git+https://github.com/example/repo'\n"
        "[distribution.agentbundle.artifactory]\nenabled = false\n"
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="schema"):
        load_catalogue_config(tmp_path)


def test_config_unsafe_name(tmp_path):
    """AC6: catalogue name with unsafe characters raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = (
        "schema = 1\n"
        "[catalogue]\n"
        "name = 'my catalogue!'\n"  # space and ! are invalid
        "display-name = 'X'\ndescription = 'x'\nminimum-agentbundle-version = '0.14.0'\n"
        "[catalogue.paths]\n"
        "packs = 'packs'\nprofiles = 'profiles'\ncontracts = 'docs/contracts'\n"
        "marketplace = '.claude-plugin/marketplace.json'\nbuild-output = 'dist'\n"
        "[catalogue.build]\n"
        "recipes = ['default']\nself-host = false\nclaude-plugin-branch = 'main'\n"
        "marketplace-description = 'x'\n"
        "[catalogue.package]\n"
        "include = ['packs/core']\nrequired = ['packs/core']\n"
        "[distribution.agentbundle]\n"
        "install-defaults-output = 'agentbundle/_data/install-defaults.toml'\n"
        "preferred-adapter = 'claude-code'\n"
        "default-source = 'git+https://github.com/example/repo'\n"
        "[distribution.agentbundle.artifactory]\nenabled = false\n"
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="name"):
        load_catalogue_config(tmp_path)


_VALID_BASE = (
    "schema = 1\n"
    "[catalogue]\n"
    "name = 'test'\ndisplay-name = 'T'\ndescription = 't'\n"
    "minimum-agentbundle-version = '0.14.0'\n"
    "[catalogue.paths]\n"
    "packs = 'packs'\nprofiles = 'profiles'\ncontracts = 'docs/contracts'\n"
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


def test_config_absolute_path(tmp_path):
    """AC6: absolute path in catalogue.paths raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace("packs = 'packs'", "packs = '/absolute/packs'")
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="absolute|path"):
        load_catalogue_config(tmp_path)


def test_config_traversal_path(tmp_path):
    """AC6: traversal path raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace("packs = 'packs'", "packs = '../outside'")
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="traversal|outside|path"):
        load_catalogue_config(tmp_path)


def test_config_symlink_escape(tmp_path):
    """AC6: symlink escaping catalogue root raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    # Create a symlink pointing outside tmp_path
    target = tmp_path.parent / "outside_dir"
    target.mkdir(exist_ok=True)
    link = tmp_path / "escape_link"
    link.symlink_to(target)

    content = _VALID_BASE.replace("packs = 'packs'", "packs = 'escape_link'")
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="escape|symlink|outside|path"):
        load_catalogue_config(tmp_path)


def test_config_required_not_in_include(tmp_path):
    """AC6: required ⊄ include raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "include = ['packs/core']\nrequired = ['packs/core']",
        "include = ['packs/core']\nrequired = ['packs/enterprise']",
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="required|include"):
        load_catalogue_config(tmp_path)


def test_config_unknown_recipe(tmp_path):
    """AC6: unknown recipe raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace("recipes = ['default']", "recipes = ['nonexistent-recipe-xyz']")
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="recipe"):
        load_catalogue_config(tmp_path)


def test_config_unsafe_recipe_path(tmp_path):
    """AC6: unsafe recipe relative path raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "recipes = ['default']", "recipes = ['../outside/recipe.toml']"
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="recipe|path|outside"):
        load_catalogue_config(tmp_path)


def test_config_unknown_preferred_adapter(tmp_path):
    """AC6: unknown preferred-adapter raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "preferred-adapter = 'claude-code'", "preferred-adapter = 'nonexistent-adapter'"
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="adapter"):
        load_catalogue_config(tmp_path)


def test_config_invalid_source(tmp_path):
    """AC6: invalid default-source raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "default-source = 'git+https://github.com/example/repo'",
        "default-source = 'ftp://invalid-scheme.example.com'",
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="source"):
        load_catalogue_config(tmp_path)


def test_config_bad_artifactory_fields(tmp_path):
    """AC6: Artifactory enabled with missing required fields raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "[distribution.agentbundle.artifactory]\nenabled = false\n",
        "[distribution.agentbundle.artifactory]\nenabled = true\n",
        # no base-url, repository, bundle
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="artifactory|base-url|required"):
        load_catalogue_config(tmp_path)


def test_config_credential_url(tmp_path):
    """AC6: credential-bearing URL in default-source raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "default-source = 'git+https://github.com/example/repo'",
        "default-source = 'git+https://user:token@github.com/example/repo'",
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="credential|source"):
        load_catalogue_config(tmp_path)


def test_config_bad_version_string(tmp_path):
    """AC6: non-comparable minimum-agentbundle-version raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE.replace(
        "minimum-agentbundle-version = '0.14.0'",
        "minimum-agentbundle-version = 'not-a-version!!'",
    )
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="version"):
        load_catalogue_config(tmp_path)


def test_config_unknown_top_level_key(tmp_path):
    """AC6: unknown top-level key raises CatalogueConfigError."""
    from agentbundle.catalogue_tooling.config import CatalogueConfigError, load_catalogue_config

    content = _VALID_BASE + "\n[unknown-section]\nfoo = 'bar'\n"
    _write_toml(tmp_path, content)
    with pytest.raises(CatalogueConfigError, match="additional property"):
        load_catalogue_config(tmp_path)


# ---------------------------------------------------------------------------
# T3: schema drift + repo catalogue.toml
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]  # packages/agentbundle/tests/unit -> repo root


def test_schema_copies_byte_equal():
    """AC4: both schema copies are byte-identical."""
    src = _REPO_ROOT / "docs" / "contracts" / "catalogue.schema.json"
    dst = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "catalogue.schema.json"
    assert src.exists(), f"Schema missing at {src}"
    assert dst.exists(), f"Schema copy missing at {dst}"
    assert src.read_bytes() == dst.read_bytes(), "Schema copies are not byte-identical"


def test_repo_catalogue_toml_valid():
    """AC7: repo-root catalogue.toml passes load_catalogue_config validation."""
    from agentbundle.catalogue_tooling.config import load_catalogue_config

    result = load_catalogue_config(_REPO_ROOT)
    assert result is not None, "load_catalogue_config returned None for repo root"


# ---------------------------------------------------------------------------
# T4: CLI stub subcommand groups
# ---------------------------------------------------------------------------


def _run_agentbundle(*args: str) -> tuple[int, str, str]:
    """Run agentbundle as a subprocess; return (rc, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", *args],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT / "packages" / "agentbundle"),
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_catalogue_group_help():
    """AC9: agentbundle catalogue --help exits non-zero and lists subcommands."""
    rc, stdout, stderr = _run_agentbundle("catalogue", "--help")
    combined = stdout + stderr
    assert rc != 0, f"Expected non-zero exit for catalogue stub, got {rc}"
    for sub in ("lint", "verify", "build", "self-host", "package", "sync-defaults"):
        assert sub in combined, f"'{sub}' not found in catalogue --help output"


def test_cli_lint_packs_help():
    """AC10: agentbundle lint packs --help exits non-zero and shows --root."""
    rc, stdout, stderr = _run_agentbundle("lint", "packs", "--help")
    combined = stdout + stderr
    assert rc != 0, f"Expected non-zero exit for lint packs stub, got {rc}"
    assert "--root" in combined, "--root not found in lint packs --help output"
