"""Command-contract tests for the catalogue CI contract guide.

Verifies that the exit codes and JSON output shapes documented in
guides/_shared/reference/catalogue-ci-contract.md match HEAD CLI behaviour.
All tests use subprocess invocation to exercise the real CLI surface, not
internal imports.

Verification modes per plan.md:
  T7 — TDD: JSON output, exit codes, package layout
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.defaults import write_defaults

from tests._support import stage_installable_pack

# The autouse _isolate_user_config_dir fixture in conftest.py redirects HOME and
# XDG_CONFIG_HOME to a tmp sandbox; subprocess calls inherit this env. All calls
# below pass --root explicitly so no command reads user config from the sandbox.


@pytest.fixture
def working_catalogue_root(tmp_path: Path) -> Path:
    """Create the smallest clean catalogue accepted by all three commands."""
    (tmp_path / "catalogue.toml").write_text(
        """\
schema = 1
[catalogue]
name = "test"
display-name = "Test"
description = "Test catalogue"
minimum-agentbundle-version = "0.14.0"
[catalogue.paths]
packs = "packs"
profiles = "profiles"
contracts = "contracts"
marketplace = ".claude-plugin/marketplace.json"
build-output = "dist"
[catalogue.build]
recipes = ["default"]
self-host = false
claude-plugin-branch = "main"
marketplace-description = "Test"
[catalogue.package]
include = ["packs/core"]
required = ["packs/core"]
[distribution.agentbundle]
install-defaults-output = "agentbundle/_data/install-defaults.toml"
preferred-adapter = "claude-code"
default-source = "git+https://github.com/example/catalogue"
[distribution.agentbundle.artifactory]
enabled = false
""",
        encoding="utf-8",
    )
    stage_installable_pack(
        tmp_path,
        "core",
        """\
[pack]
name = "core"
version = "0.1.0"
[pack.adapter-contract]
version = "0.8"
[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
""",
    )
    marketplace = tmp_path / ".claude-plugin" / "marketplace.json"
    marketplace.parent.mkdir()
    marketplace.write_text(
        '{"name":"test","owner":{"name":"test"},"plugins":[]}\n',
        encoding="utf-8",
    )
    # Installable catalogue archives deliberately omit catalogue.toml, so a
    # shipped root marker must remain for archive verification and discovery.
    (tmp_path / "AGENTS.md").write_text("# Test catalogue\n", encoding="utf-8")
    (tmp_path / "LICENSE-APACHE").write_text("Fixture license.\n", encoding="utf-8")
    (tmp_path / "LICENSE-MIT").write_text("Fixture license.\n", encoding="utf-8")
    result = write_defaults(tmp_path)
    assert result.ok
    return tmp_path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentbundle", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Catalogue lint --format json → parseable JSON, stdout-only
# ---------------------------------------------------------------------------


def test_catalogue_lint_json_output_parses(working_catalogue_root: Path) -> None:
    """Lint --format json stdout json.loads() cleanly with required keys."""
    result = _run(
        "catalogue", "lint",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    # json.loads on raw (unstripped) stdout — no non-JSON lines mixed in
    doc = json.loads(result.stdout)
    for key in ("schema_version", "command", "ok", "diagnostics"):
        assert key in doc, f"missing key {key!r} in lint JSON output"


# ---------------------------------------------------------------------------
# Catalogue verify --format json → parseable JSON, stdout-only
# ---------------------------------------------------------------------------


def test_catalogue_verify_json_output_parses(working_catalogue_root: Path) -> None:
    """Verify --format json stdout json.loads() cleanly with required keys."""
    result = _run(
        "catalogue", "verify",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    doc = json.loads(result.stdout)
    for key in ("schema_version", "command", "ok", "diagnostics"):
        assert key in doc, f"missing key {key!r} in verify JSON output"


# ---------------------------------------------------------------------------
# Exit 0 on clean catalogue
# ---------------------------------------------------------------------------


def test_catalogue_lint_exits_0_on_clean(working_catalogue_root: Path) -> None:
    """Lint returns 0 on a clean catalogue."""
    result = _run(
        "catalogue", "lint",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    assert result.returncode == 0, (
        f"catalogue lint exited {result.returncode}; stderr: {result.stderr[:400]}"
    )


def test_catalogue_verify_exits_0_on_clean(working_catalogue_root: Path) -> None:
    """Verify returns 0 on a clean catalogue."""
    result = _run(
        "catalogue", "verify",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    assert result.returncode == 0, (
        f"catalogue verify exited {result.returncode}; stderr: {result.stderr[:400]}"
    )


# ---------------------------------------------------------------------------
# Exit 1 on an invalid catalogue
# ---------------------------------------------------------------------------


def _write_invalid_catalogue(tmp_path: Path) -> Path:
    """Write a catalogue directory that lint and verify will reject."""
    # A catalogue.toml that is missing required fields (name, version, schema).
    (tmp_path / "catalogue.toml").write_text("[catalogue]\n", encoding="utf-8")
    return tmp_path


def test_catalogue_lint_exits_1_on_errors(tmp_path: Path) -> None:
    """Lint returns 1 when the catalogue has errors."""
    root = _write_invalid_catalogue(tmp_path)
    result = _run("catalogue", "lint", "--root", str(root), "--format", "json")
    assert result.returncode == 1, (
        f"expected exit 1 for invalid catalogue, got {result.returncode}"
    )


def test_catalogue_verify_exits_1_on_errors(tmp_path: Path) -> None:
    """Verify returns 1 when the catalogue has errors."""
    root = _write_invalid_catalogue(tmp_path)
    result = _run("catalogue", "verify", "--root", str(root), "--format", "json")
    assert result.returncode == 1, (
        f"expected exit 1 for invalid catalogue, got {result.returncode}"
    )


# ---------------------------------------------------------------------------
# Catalogue package exit 0 + output layout
# ---------------------------------------------------------------------------


def test_catalogue_package_exits_0_and_layout(
    working_catalogue_root: Path, tmp_path: Path
) -> None:
    """Package with required flags exits 0 and writes the documented layout."""
    bundle = "test-ci-contract"
    release = "0.0.1-ci"
    channel = "stable"

    result = _run(
        "catalogue", "package",
        "--root", str(working_catalogue_root),
        "--bundle", bundle,
        "--release", release,
        "--channel", channel,
        "--output", str(tmp_path),
    )
    assert result.returncode == 0, (
        f"catalogue package exited {result.returncode}; stderr: {result.stderr[:400]}"
    )

    releases_dir = tmp_path / "catalogues" / bundle / "releases" / release
    assert (releases_dir / f"catalogue-{release}.tar.gz").exists(), (
        "archive missing from output layout"
    )
    assert (releases_dir / f"catalogue-{release}.tar.gz.sha256").exists(), (
        "SHA256 sidecar missing from output layout"
    )
    channels_dir = tmp_path / "catalogues" / bundle / "channels"
    assert (channels_dir / f"{channel}.json").exists(), (
        "channel descriptor missing from output layout"
    )


# ---------------------------------------------------------------------------
# Catalogue package exits 2 on missing required flags
# ---------------------------------------------------------------------------


def test_catalogue_package_exits_2_on_missing_flags() -> None:
    """Package with no flags exits 2 (argparse usage error, standard convention)."""
    result = _run("catalogue", "package")
    assert result.returncode == 2, (
        f"expected exit 2 for missing required flags, got {result.returncode}"
    )
