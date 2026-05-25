"""Integration tests for the build-pipeline claude-plugins derivation (T4 / AC9).

Goal-based check: run ``agentbundle build`` against the fixture packs and verify:

  (a) pack.toml is copied verbatim (AC9 c)
  (b) install-marker.py is copied byte-identical from the canonical template (AC9 b)
  (c) the derived plugin.json carries the synthesised SessionStart hook (AC9 a)
  (d) source-tree fields name/version/description are preserved (AC9 a)
  (e) the build is idempotent — warm-overwrite AND cold-rebuild (Concern-6)
  (f) agentbundle build check exits zero after the T4 migration lands
      (Concerns 7+8: uses Python entry point, copies packs to tmp_path — no
      real-repo mutation)
  (g) the SessionStart command string survives a space-in-CLAUDE_PLUGIN_ROOT
      path (AC9 sub-assertion)
  (h) transactional cleanup: phantom files from a prior build do not survive
      a fresh build (Blocker-4)
  (i) schema-rejection integration: source plugin.json carrying a hooks block
      causes the build to exit non-zero (AC10 gate 1 at the pipeline layer,
      Concern-11)

Tests (a)-(d) and (g) are parametrised over all fixture packs (Concern-5
multi-pack coverage).

Spec: docs/specs/claude-plugins-install-route/spec.md
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
# packages/agentbundle/tests/integration/ → parents[2] = packages/agentbundle/
FIXTURES_PACKS = (
    Path(__file__).resolve().parents[2]
    / "agentbundle"
    / "build"
    / "tests"
    / "fixtures"
    / "packs"
)
TEMPLATE_PATH = REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py"

# Expected canonical command in the derived plugin.json.
EXPECTED_COMMAND = 'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"'

# All fixture packs — parametrisation covers multi-pack derivation (Concern-5).
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
# Parametrised per-pack artifact tests (Concern-5: multi-pack coverage)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_derivation_projects_pack_toml(tmp_path, pack_name):
    """AC9 (c): pack.toml is projected byte-for-byte for every fixture pack."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    derived_toml = tmp_path / "claude-plugins" / pack_name / "pack.toml"
    source_toml = FIXTURES_PACKS / pack_name / "pack.toml"

    assert derived_toml.exists(), f"derived pack.toml missing at {derived_toml}"
    assert derived_toml.read_bytes() == source_toml.read_bytes(), (
        f"[{pack_name}] derived pack.toml is not byte-identical to source pack.toml"
    )


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_derivation_projects_install_marker(tmp_path, pack_name):
    """AC9 (b): install-marker.py is projected byte-identical to the template for every pack."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    derived_marker = (
        tmp_path
        / "claude-plugins"
        / pack_name
        / ".claude-plugin"
        / "scripts"
        / "install-marker.py"
    )
    assert derived_marker.exists(), f"[{pack_name}] derived install-marker.py missing"
    assert derived_marker.read_bytes() == TEMPLATE_PATH.read_bytes(), (
        f"[{pack_name}] derived install-marker.py is not byte-identical to "
        "packages/agentbundle/templates/install-marker.py"
    )


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_derivation_synthesises_hooks_block(tmp_path, pack_name):
    """AC9 (a): derived plugin.json carries the synthesised SessionStart hook for every pack."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    derived_json = (
        tmp_path / "claude-plugins" / pack_name / ".claude-plugin" / "plugin.json"
    )
    assert derived_json.exists(), f"[{pack_name}] derived plugin.json missing"

    manifest = json.loads(derived_json.read_text(encoding="utf-8"))
    assert "hooks" in manifest, f"[{pack_name}] derived plugin.json missing 'hooks' key"
    hooks = manifest["hooks"]
    assert "SessionStart" in hooks, f"[{pack_name}] derived hooks missing 'SessionStart'"
    session_start = hooks["SessionStart"]
    assert isinstance(session_start, list), "SessionStart must be a list"
    assert len(session_start) == 1, f"[{pack_name}] Expected 1 SessionStart entry"
    assert session_start[0]["command"] == EXPECTED_COMMAND, (
        f"[{pack_name}] SessionStart command mismatch:\n"
        f"  expected: {EXPECTED_COMMAND!r}\n"
        f"  got:      {session_start[0]['command']!r}"
    )


@pytest.mark.parametrize("pack_name", FIXTURE_PACK_NAMES)
def test_derivation_preserves_source_fields(tmp_path, pack_name):
    """AC9 (a): derived plugin.json name/version/description match source for every pack."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    source_json = FIXTURES_PACKS / pack_name / ".claude-plugin" / "plugin.json"
    derived_json = (
        tmp_path / "claude-plugins" / pack_name / ".claude-plugin" / "plugin.json"
    )

    source = json.loads(source_json.read_text(encoding="utf-8"))
    derived = json.loads(derived_json.read_text(encoding="utf-8"))

    for field in ("name", "version", "description"):
        assert derived.get(field) == source.get(field), (
            f"[{pack_name}] Field {field!r} mismatch: source={source.get(field)!r}, "
            f"derived={derived.get(field)!r}"
        )


# ---------------------------------------------------------------------------
# Idempotence tests (Concern-6: warm-overwrite AND cold-rebuild)
# ---------------------------------------------------------------------------


def test_derivation_idempotent(tmp_path):
    """Warm-overwrite idempotence: running build twice without clearing yields
    byte-identical output for all fixture packs."""
    result1 = _run_build(FIXTURES_PACKS, tmp_path)
    assert result1.returncode == 0, result1.stderr

    derived_root = tmp_path / "claude-plugins"

    def _snapshot(base: Path) -> dict[str, bytes]:
        return {
            str(p.relative_to(base)): p.read_bytes()
            for p in base.rglob("*")
            if p.is_file()
        }

    snap1 = _snapshot(derived_root)

    result2 = _run_build(FIXTURES_PACKS, tmp_path)
    assert result2.returncode == 0, result2.stderr

    snap2 = _snapshot(derived_root)

    assert snap1.keys() == snap2.keys(), (
        f"Second build produced different file set:\n"
        f"  added:   {snap2.keys() - snap1.keys()}\n"
        f"  removed: {snap1.keys() - snap2.keys()}"
    )
    for path, bytes1 in snap1.items():
        bytes2 = snap2[path]
        assert bytes1 == bytes2, f"File {path} differs between warm build runs"


def test_derivation_cold_rebuild_byte_identical(tmp_path):
    """Cold-rebuild idempotence (Concern-6): first run → rmtree → second run
    must produce byte-identical output for all fixture packs."""
    result1 = _run_build(FIXTURES_PACKS, tmp_path)
    assert result1.returncode == 0, result1.stderr

    derived_root = tmp_path / "claude-plugins"

    def _snapshot(base: Path) -> dict[str, bytes]:
        return {
            str(p.relative_to(base)): p.read_bytes()
            for p in base.rglob("*")
            if p.is_file()
        }

    snap1 = _snapshot(derived_root)

    # Clear the derived output between runs to exercise cold-rebuild path.
    shutil.rmtree(derived_root)

    result2 = _run_build(FIXTURES_PACKS, tmp_path)
    assert result2.returncode == 0, result2.stderr

    snap2 = _snapshot(derived_root)

    assert snap1.keys() == snap2.keys(), (
        f"Cold-rebuild produced different file set:\n"
        f"  added:   {snap2.keys() - snap1.keys()}\n"
        f"  removed: {snap1.keys() - snap2.keys()}"
    )
    for path, bytes1 in snap1.items():
        bytes2 = snap2[path]
        assert bytes1 == bytes2, f"File {path} differs between cold-rebuild runs"


# ---------------------------------------------------------------------------
# Transactional cleanup (Blocker-4: phantom files do not survive a fresh build)
# ---------------------------------------------------------------------------


def test_derivation_recovers_from_phantom_files(tmp_path):
    """Blocker-4: a stale file left by a prior crashed build must not survive.

    Seeds a phantom file into one pack's derived directory BEFORE the build,
    then asserts the phantom is gone after a successful build.
    """
    pack_name = FIXTURE_PACK_NAMES[0]  # use first fixture pack
    phantom_dir = tmp_path / "claude-plugins" / pack_name / ".claude-plugin"
    phantom_dir.mkdir(parents=True, exist_ok=True)
    phantom_file = phantom_dir / "stale.json"
    phantom_file.write_text('{"phantom": true}', encoding="utf-8")

    assert phantom_file.exists(), "pre-condition: phantom file must exist before build"

    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    assert not phantom_file.exists(), (
        f"Phantom file {phantom_file} survived the build — "
        "transactional per_pack_output cleanup is not working"
    )


# ---------------------------------------------------------------------------
# build check (Concerns 7+8: Python entry point, shadow copy of packs/)
# ---------------------------------------------------------------------------


def test_make_build_check_passes_post_migration(tmp_path):
    """AC9: agentbundle build check exits zero against the migrated working tree.

    Concerns 7+8: uses the Python entry point (not 'make build-check') and
    copies packs/ into tmp_path so the real repo tree is never mutated.
    __pycache__ directories inside the copy are removed before the check so
    the self-host gate does not flag them as unexpected projection artifacts.
    """
    # Shadow-copy packs/ into tmp_path so the real repo is never mutated.
    packs_shadow = tmp_path / "packs_shadow"
    shutil.copytree(REPO_ROOT / "packs", packs_shadow, symlinks=True)

    # Remove any __pycache__ from the shadow copy — they would be flagged as
    # unexpected projection artifacts by the self-host gate.
    for pycache in packs_shadow.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle.build",
            "check",
            "--packs-dir",
            str(packs_shadow),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"agentbundle build check failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# AC9 sub-assertion: space in CLAUDE_PLUGIN_ROOT
# ---------------------------------------------------------------------------


def test_shell_exec_quoting_survives_space_in_root(tmp_path):
    """AC9 sub-assertion: the SessionStart command survives a space in CLAUDE_PLUGIN_ROOT."""
    result = _run_build(FIXTURES_PACKS, tmp_path)
    assert result.returncode == 0, result.stderr

    pack_name = FIXTURE_PACK_NAMES[0]
    derived_json = (
        tmp_path / "claude-plugins" / pack_name / ".claude-plugin" / "plugin.json"
    )
    manifest = json.loads(derived_json.read_text(encoding="utf-8"))
    command = manifest["hooks"]["SessionStart"][0]["command"]

    # Substitute a CLAUDE_PLUGIN_ROOT value containing a space.
    synthetic_root = "/tmp/with space/root"
    expanded = command.replace("${CLAUDE_PLUGIN_ROOT}", synthetic_root)
    tokens = shlex.split(expanded)

    expected_tokens = [
        "python3",
        f"{synthetic_root}/.claude-plugin/scripts/install-marker.py",
    ]
    assert tokens == expected_tokens, (
        f"shlex.split produced unexpected tokens:\n"
        f"  expected: {expected_tokens}\n"
        f"  got:      {tokens}\n"
        f"  command:  {command!r}\n"
        f"  expanded: {expanded!r}"
    )


# ---------------------------------------------------------------------------
# Schema-rejection integration (Concern-11 / AC10 gate 1 at pipeline layer)
# ---------------------------------------------------------------------------


def test_build_rejects_source_plugin_json_with_hooks_block(tmp_path):
    """Concern-11 / AC10 gate 1: a source plugin.json carrying a hooks block
    must cause the build pipeline to exit non-zero and name 'hooks' or the
    offending file in the error output.

    This pins AC10 gate 1 at the build-pipeline integration layer (the
    existing schema unit tests pin it at the schema unit layer).
    """
    # Copy a fixture pack into tmp_path and mutate its source plugin.json
    # to include a hooks block — simulating hand-authored drift.
    pack_name = FIXTURE_PACK_NAMES[0]
    src_pack = FIXTURES_PACKS / pack_name
    mutated_packs = tmp_path / "mutated_packs"
    shutil.copytree(src_pack, mutated_packs / pack_name, symlinks=True)

    mutated_manifest = mutated_packs / pack_name / ".claude-plugin" / "plugin.json"
    original = json.loads(mutated_manifest.read_text(encoding="utf-8"))
    original["hooks"] = {"SessionStart": [{"command": "echo evil"}]}
    mutated_manifest.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")

    result = _run_build(mutated_packs, tmp_path / "out")

    assert result.returncode != 0, (
        "Build should have failed for a source plugin.json with a hooks block "
        f"but exited {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "hooks" in combined or "plugin.json" in combined, (
        "Error output must name 'hooks' or the offending file; got:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
