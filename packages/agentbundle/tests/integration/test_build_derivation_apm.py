"""Integration tests for the build-pipeline APM derivation (T4 / AC11).

Goal-based check: run ``agentbundle build`` against the fixture packs and
verify, under ``dist/apm/<pack>/``:

  (a) ``.apm/hooks/install-marker.py`` is byte-identical to the canonical
      template (AC11 b)
  (b) ``.apm/hooks/install-marker.json`` carries the synthesised
      SessionStart block with the canonical APM-route command (AC7 / AC11 a)
  (c) ``pack.toml`` is projected byte-for-byte from the source (AC11 c)
  (d) the SessionStart command string survives a space-in-PLUGIN_ROOT
      path (AC7 shlex sub-assertion)
  (e) the build is idempotent — running twice produces byte-identical
      output at the APM projection (Concern-6 parallel of the
      claude-plugins derivation)

Spec: docs/specs/apm-install-route-parity/spec.md
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES_PACKS = (
    Path(__file__).resolve().parents[2]
    / "agentbundle"
    / "build"
    / "tests"
    / "fixtures"
    / "packs"
)
TEMPLATE_PATH = REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py"

# AC7's canonical command — match the build pipeline's _SESSION_START_COMMAND_APM.
EXPECTED_APM_COMMAND = (
    'python3 "${PLUGIN_ROOT}/.apm/hooks/install-marker.py"'
    ' --install-route apm'
)

FIXTURE_PACK_NAMES = [
    p.name
    for p in sorted(FIXTURES_PACKS.iterdir())
    if p.is_dir() and (p / "pack.toml").exists()
]


def _run_build(packs_dir: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle.build",
            "build",
            "--packs-dir",
            str(packs_dir),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


# ---------------------------------------------------------------------------
# AC11: per-pack artifact projection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_apm_derivation_projects_install_marker_py(tmp_path, pack_name):
    """AC11 (b): install-marker.py is projected byte-identical to the canonical template."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    derived = (
        tmp_path / "apm" / pack_name / ".apm" / "hooks" / "install-marker.py"
    )
    assert derived.exists(), f"[{pack_name}] APM install-marker.py missing at {derived}"
    assert derived.read_bytes() == TEMPLATE_PATH.read_bytes(), (
        f"[{pack_name}] APM install-marker.py is not byte-identical to "
        "packages/agentbundle/templates/install-marker.py"
    )


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_apm_derivation_projects_pack_toml(tmp_path, pack_name):
    """AC11 (c): pack.toml is projected byte-for-byte under the APM tree."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    derived = tmp_path / "apm" / pack_name / "pack.toml"
    source = FIXTURES_PACKS / pack_name / "pack.toml"
    assert derived.exists(), f"[{pack_name}] APM pack.toml missing"
    assert derived.read_bytes() == source.read_bytes(), (
        f"[{pack_name}] APM pack.toml is not byte-identical to source"
    )


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_apm_derivation_synthesises_install_marker_json(tmp_path, pack_name):
    """AC7 + AC11 (a): install-marker.json carries the SessionStart block
    with the canonical APM command string and the timeout = 10 field."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    derived = (
        tmp_path / "apm" / pack_name / ".apm" / "hooks" / "install-marker.json"
    )
    assert derived.exists(), f"[{pack_name}] install-marker.json missing"
    obj = json.loads(derived.read_text(encoding="utf-8"))

    # Walk the path AC7 specifies literally.
    session_start = obj["hooks"]["SessionStart"]
    assert isinstance(session_start, list) and len(session_start) == 1
    inner = session_start[0]["hooks"]
    assert isinstance(inner, list) and len(inner) == 1
    entry = inner[0]
    assert entry["type"] == "command"
    assert entry["command"] == EXPECTED_APM_COMMAND, (
        f"[{pack_name}] expected APM command:\n  {EXPECTED_APM_COMMAND!r}\n"
        f"got:\n  {entry['command']!r}"
    )
    assert entry["timeout"] == 10


def test_apm_derivation_hook_command_shlex_quoting(tmp_path):
    """AC7 sub-assertion: substituting a synthetic PLUGIN_ROOT with a space
    and shlex-splitting the command yields exactly four tokens — the quoting
    survives the substitution."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    pack_name = FIXTURE_PACK_NAMES[0]
    derived = (
        tmp_path / "apm" / pack_name / ".apm" / "hooks" / "install-marker.json"
    )
    obj = json.loads(derived.read_text(encoding="utf-8"))
    command = obj["hooks"]["SessionStart"][0]["hooks"][0]["command"]

    synthetic_root = "/tmp/with space/root"
    expanded = command.replace("${PLUGIN_ROOT}", synthetic_root)
    tokens = shlex.split(expanded)
    expected = [
        "python3",
        f"{synthetic_root}/.apm/hooks/install-marker.py",
        "--install-route",
        "apm",
    ]
    assert tokens == expected, (
        f"shlex.split produced unexpected tokens:\n"
        f"  expected: {expected}\n"
        f"  got:      {tokens}\n"
        f"  command:  {command!r}\n"
        f"  expanded: {expanded!r}"
    )


def test_apm_derivation_idempotent(tmp_path):
    """Build twice; the APM projection is byte-identical (no phantom files,
    no time-of-day variation)."""
    result1 = _run_build(FIXTURES_PACKS, tmp_path)
    assert result1.returncode == 0, result1.stderr

    apm_root = tmp_path / "apm"

    def _snapshot(base: Path) -> dict[str, bytes]:
        return {
            str(p.relative_to(base)): p.read_bytes()
            for p in base.rglob("*")
            if p.is_file()
        }

    snap1 = _snapshot(apm_root)

    result2 = _run_build(FIXTURES_PACKS, tmp_path)
    assert result2.returncode == 0, result2.stderr

    snap2 = _snapshot(apm_root)
    assert snap1 == snap2, "APM projection is not byte-identical across two builds"
