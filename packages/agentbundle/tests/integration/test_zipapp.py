"""T13: zipapp distribution behavior.

The fixture stages the installed `agentbundle/` package, then uses
the standard-library zipapp builder to produce a single-file bundle at
`dist/agentbundle.pyz`. The bundle imports `agentbundle.cli:main` as
its entry point and reads the spec version at startup from the
bundled `agentbundle/_data/adapter.toml`.

These tests pin the two ship-time invariants for the zipapp:

  1. The engine package produces a runnable `.pyz`.
  2. `python dist/agentbundle.pyz --version` exits 0 and prints both
     the CLI version and the spec version.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipapp
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def zipapp_path(tmp_path_factory) -> Path:
    """Build the zipapp into a tmpdir; yield its path. Module-scoped so
    the multi-second build runs once for all tests in this file."""
    workspace = tmp_path_factory.mktemp("zipapp_build")
    staging = workspace / "staging"
    shutil.copytree(
        PACKAGE_ROOT / "agentbundle",
        staging / "agentbundle",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    pyz = workspace / "agentbundle.pyz"
    zipapp.create_archive(staging, pyz, main="agentbundle.cli:main")
    assert pyz.exists(), f"expected zipapp at {pyz}"
    return pyz


def test_zipapp_version_prints_cli_and_spec_versions(zipapp_path: Path):
    proc = subprocess.run(
        [sys.executable, str(zipapp_path), "--version"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    combined = proc.stdout + proc.stderr
    assert "agentbundle" in combined
    # Spec version 0.1 ships at v1 of the CLI.
    assert "0.1" in combined


def test_zipapp_list_targets_runs_standalone(zipapp_path: Path):
    """Smoke test that the zipapp's bundled registry surfaces the four
    reference adapters with no PYTHONPATH and no installed copy of
    agentbundle on the path."""
    # Restrict PATH to a Unix-only minimal set to verify the zipapp has no
    # dependency on an installed agentbundle. On Windows sys.executable is
    # passed directly so PATH doesn't matter for finding Python; we still
    # need the Windows env vars (USERPROFILE, SYSTEMROOT, TEMP) so that
    # Path.home() and tempfile work inside the subprocess.
    if sys.platform == "win32":
        env = {k: v for k, v in os.environ.items()
               if k in ("USERPROFILE", "HOMEDRIVE", "HOMEPATH", "SYSTEMROOT", "TEMP", "TMP")}
    else:
        env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    proc = subprocess.run(
        [sys.executable, str(zipapp_path), "list-targets"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    for adapter in ("claude_code", "codex", "copilot", "kiro"):
        assert adapter in proc.stdout, f"missing adapter {adapter} in {proc.stdout!r}"


def test_zipapp_is_a_single_file_under_a_reasonable_size(zipapp_path: Path):
    """No third-party deps means the bundle should be small. The guard is a
    bloat tripwire (catch a stray dependency or a vendored binary), not a tight
    budget: the pure-stdlib bundle had grown to ~1.02 MiB and brushed the old
    1 MiB ceiling, so the guard is 2 MiB — still ~2x headroom over the current
    size, which a real regression (a bundled wheel) would blow straight past."""
    size = zipapp_path.stat().st_size
    assert 0 < size < 2_097_152, f"zipapp size {size} bytes outside reasonable range"
