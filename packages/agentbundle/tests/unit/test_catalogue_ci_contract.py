"""Command-contract tests for the catalogue CI contract guide.

Verifies that the exit codes and JSON output shapes documented in
guides/_shared/reference/catalogue-ci-contract.md match HEAD CLI behaviour.
All tests use subprocess invocation to exercise the real CLI surface, not
internal imports.

Verification modes per plan.md:
  T7 — TDD: AC16–AC21 (JSON output, exit codes, package layout)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# The autouse _isolate_user_config_dir fixture in conftest.py redirects HOME and
# XDG_CONFIG_HOME to a tmp sandbox; subprocess calls inherit this env. All calls
# below pass --root explicitly so no command reads user config from the sandbox.

_REPO_ROOT = Path(__file__).resolve().parents[4]  # packages/agentbundle/tests/unit -> repo root


@pytest.fixture
def working_catalogue_root() -> Path:
    """Return the working-tree catalogue root (this repo)."""
    return _REPO_ROOT


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentbundle", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# AC16 / AC18: catalogue lint --format json → parseable JSON, stdout-only
# ---------------------------------------------------------------------------


def test_catalogue_lint_json_output_parses(working_catalogue_root: Path) -> None:
    """AC16: lint --format json stdout json.loads() cleanly with required keys."""
    result = _run(
        "catalogue", "lint",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    # AC18: json.loads on raw (unstripped) stdout — no non-JSON lines mixed in
    doc = json.loads(result.stdout)
    for key in ("schema_version", "command", "ok", "diagnostics"):
        assert key in doc, f"missing key {key!r} in lint JSON output"


# ---------------------------------------------------------------------------
# AC17 / AC18: catalogue verify --format json → parseable JSON, stdout-only
# ---------------------------------------------------------------------------


def test_catalogue_verify_json_output_parses(working_catalogue_root: Path) -> None:
    """AC17: verify --format json stdout json.loads() cleanly with required keys."""
    result = _run(
        "catalogue", "verify",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    doc = json.loads(result.stdout)
    for key in ("schema_version", "command", "ok", "diagnostics"):
        assert key in doc, f"missing key {key!r} in verify JSON output"


# ---------------------------------------------------------------------------
# AC19: exit 0 on clean catalogue
# ---------------------------------------------------------------------------


def test_catalogue_lint_exits_0_on_clean(working_catalogue_root: Path) -> None:
    """AC19a: lint returns 0 on a clean catalogue."""
    result = _run(
        "catalogue", "lint",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    assert result.returncode == 0, (
        f"catalogue lint exited {result.returncode}; stderr: {result.stderr[:400]}"
    )


def test_catalogue_verify_exits_0_on_clean(working_catalogue_root: Path) -> None:
    """AC19a: verify returns 0 on a clean catalogue."""
    result = _run(
        "catalogue", "verify",
        "--root", str(working_catalogue_root),
        "--format", "json",
    )
    assert result.returncode == 0, (
        f"catalogue verify exited {result.returncode}; stderr: {result.stderr[:400]}"
    )


# ---------------------------------------------------------------------------
# AC19: exit 1 on an invalid catalogue
# ---------------------------------------------------------------------------


def _write_invalid_catalogue(tmp_path: Path) -> Path:
    """Write a catalogue directory that lint and verify will reject."""
    # A catalogue.toml that is missing required fields (name, version, schema).
    (tmp_path / "catalogue.toml").write_text("[catalogue]\n", encoding="utf-8")
    return tmp_path


def test_catalogue_lint_exits_1_on_errors(tmp_path: Path) -> None:
    """AC19b: lint returns 1 when the catalogue has errors."""
    root = _write_invalid_catalogue(tmp_path)
    result = _run("catalogue", "lint", "--root", str(root), "--format", "json")
    assert result.returncode == 1, (
        f"expected exit 1 for invalid catalogue, got {result.returncode}"
    )


def test_catalogue_verify_exits_1_on_errors(tmp_path: Path) -> None:
    """AC19b: verify returns 1 when the catalogue has errors."""
    root = _write_invalid_catalogue(tmp_path)
    result = _run("catalogue", "verify", "--root", str(root), "--format", "json")
    assert result.returncode == 1, (
        f"expected exit 1 for invalid catalogue, got {result.returncode}"
    )


# ---------------------------------------------------------------------------
# AC20: catalogue package exit 0 + output layout
# ---------------------------------------------------------------------------


def test_catalogue_package_exits_0_and_layout(
    working_catalogue_root: Path, tmp_path: Path
) -> None:
    """AC20: package with required flags exits 0 and writes the documented layout."""
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
# AC21: catalogue package exits 2 on missing required flags
# ---------------------------------------------------------------------------


def test_catalogue_package_exits_2_on_missing_flags() -> None:
    """AC21: package with no flags exits 2 (argparse usage error, standard convention)."""
    result = _run("catalogue", "package")
    assert result.returncode == 2, (
        f"expected exit 2 for missing required flags, got {result.returncode}"
    )
