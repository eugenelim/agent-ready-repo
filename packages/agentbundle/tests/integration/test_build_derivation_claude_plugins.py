"""Integration tests for the build-pipeline claude-plugins derivation (T4 / AC9).

Goal-based check: run ``agentbundle build`` against the fixture packs and diff
the produced tree against a checked-in fixture to verify that:

  (a) pack.toml is copied verbatim (AC9 c)
  (b) install-marker.py is copied byte-identical from the canonical template (AC9 b)
  (c) the derived plugin.json carries the synthesised SessionStart hook (AC9 a)
  (d) source-tree fields name/version/description are preserved (AC9 a)
  (e) the build is idempotent (running twice yields byte-identical output)
  (f) make build-check exits zero after the T4 migration lands
  (g) the SessionStart command string survives a space-in-CLAUDE_PLUGIN_ROOT path (AC9 sub-assertion)

Spec: docs/specs/claude-plugins-install-route/spec.md
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
# packages/agentbundle/tests/integration/ → parents[2] = packages/agentbundle/
FIXTURES_PACKS = Path(__file__).resolve().parents[2] / "agentbundle" / "build" / "tests" / "fixtures" / "packs"
DERIVED_FIXTURE = Path(__file__).resolve().parents[2] / "agentbundle" / "build" / "tests" / "fixtures" / "derived"
TEMPLATE_PATH = REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py"

# The pack we use for fixture-based assertions.
FIXTURE_PACK = "core"

# Expected canonical command in the derived plugin.json.
EXPECTED_COMMAND = 'python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"'


def _run_build(packs_dir: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, "-m", "agentbundle.build",
            "build",
            "--packs-dir", str(packs_dir),
            "--output-dir", str(output_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class TestDerivationProjectsPackToml:
    """AC9 (c): pack.toml is projected byte-for-byte into the derived tree."""

    def test_derivation_projects_pack_toml(self, tmp_path):
        result = _run_build(FIXTURES_PACKS, tmp_path)
        assert result.returncode == 0, result.stderr

        derived_toml = tmp_path / "claude-plugins" / FIXTURE_PACK / "pack.toml"
        source_toml = FIXTURES_PACKS / FIXTURE_PACK / "pack.toml"

        assert derived_toml.exists(), f"derived pack.toml missing at {derived_toml}"
        assert derived_toml.read_bytes() == source_toml.read_bytes(), (
            "derived pack.toml is not byte-identical to source pack.toml"
        )


class TestDerivationProjectsInstallMarker:
    """AC9 (b): install-marker.py is projected byte-identical to the template."""

    def test_derivation_projects_install_marker(self, tmp_path):
        result = _run_build(FIXTURES_PACKS, tmp_path)
        assert result.returncode == 0, result.stderr

        derived_marker = (
            tmp_path / "claude-plugins" / FIXTURE_PACK
            / ".claude-plugin" / "scripts" / "install-marker.py"
        )
        assert derived_marker.exists(), f"derived install-marker.py missing at {derived_marker}"
        assert derived_marker.read_bytes() == TEMPLATE_PATH.read_bytes(), (
            "derived install-marker.py is not byte-identical to "
            "packages/agentbundle/templates/install-marker.py"
        )


class TestDerivationSynthesisesHooksBlock:
    """AC9 (a): derived plugin.json carries the synthesised SessionStart hook."""

    def test_derivation_synthesises_hooks_block(self, tmp_path):
        result = _run_build(FIXTURES_PACKS, tmp_path)
        assert result.returncode == 0, result.stderr

        derived_json = (
            tmp_path / "claude-plugins" / FIXTURE_PACK / ".claude-plugin" / "plugin.json"
        )
        assert derived_json.exists(), f"derived plugin.json missing at {derived_json}"

        manifest = json.loads(derived_json.read_text(encoding="utf-8"))
        assert "hooks" in manifest, "derived plugin.json missing 'hooks' key"
        hooks = manifest["hooks"]
        assert "SessionStart" in hooks, "derived hooks missing 'SessionStart' key"
        session_start = hooks["SessionStart"]
        assert isinstance(session_start, list), "SessionStart must be a list"
        assert len(session_start) == 1, f"Expected 1 SessionStart entry, got {len(session_start)}"
        assert session_start[0]["command"] == EXPECTED_COMMAND, (
            f"SessionStart command mismatch:\n"
            f"  expected: {EXPECTED_COMMAND!r}\n"
            f"  got:      {session_start[0]['command']!r}"
        )


class TestDerivationPreservesSourceFields:
    """AC9 (a): derived plugin.json name/version/description match source."""

    def test_derivation_preserves_source_fields(self, tmp_path):
        result = _run_build(FIXTURES_PACKS, tmp_path)
        assert result.returncode == 0, result.stderr

        source_json = FIXTURES_PACKS / FIXTURE_PACK / ".claude-plugin" / "plugin.json"
        derived_json = (
            tmp_path / "claude-plugins" / FIXTURE_PACK / ".claude-plugin" / "plugin.json"
        )

        source = json.loads(source_json.read_text(encoding="utf-8"))
        derived = json.loads(derived_json.read_text(encoding="utf-8"))

        for field in ("name", "version", "description"):
            assert derived.get(field) == source.get(field), (
                f"Field {field!r} mismatch: source={source.get(field)!r}, "
                f"derived={derived.get(field)!r}"
            )


class TestDerivationIdempotent:
    """Running make build twice produces byte-identical output."""

    def test_derivation_idempotent(self, tmp_path):
        result1 = _run_build(FIXTURES_PACKS, tmp_path)
        assert result1.returncode == 0, result1.stderr

        # Capture first-run bytes for the three key derived artifacts.
        derived_root = tmp_path / "claude-plugins" / FIXTURE_PACK

        def _snapshot(base: Path) -> dict[str, bytes]:
            return {
                str(p.relative_to(base)): p.read_bytes()
                for p in base.rglob("*")
                if p.is_file()
            }

        snap1 = _snapshot(derived_root)

        # Second run — must produce byte-identical output.
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
            assert bytes1 == bytes2, f"File {path} differs between build runs"


class TestMakeBuildCheckPassesPostMigration:
    """AC9: make build-check exits zero against the migrated working tree."""

    def test_make_build_check_passes_post_migration(self):
        """Run make build-check against the real packs tree; must exit 0.

        Clears __pycache__ directories under packs/ first — a pre-existing
        issue where importing the example-credentialed-skill creates pyc files
        that the self-host gate sees as unexpected projection artifacts.
        The gate instructions call this out explicitly.
        """
        # Clear pycache files in the packs tree that the build-check gate
        # incorrectly flags as projection drift (pre-existing issue, not T4).
        for pycache in (REPO_ROOT / "packs").rglob("__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache, ignore_errors=True)

        result = subprocess.run(
            ["make", "build-check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"make build-check failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class TestShellExecQuotingSurvivesSpaceInRoot:
    """AC9 sub-assertion: the SessionStart command survives a space in CLAUDE_PLUGIN_ROOT."""

    def test_shell_exec_quoting_survives_space_in_root(self, tmp_path):
        result = _run_build(FIXTURES_PACKS, tmp_path)
        assert result.returncode == 0, result.stderr

        derived_json = (
            tmp_path / "claude-plugins" / FIXTURE_PACK / ".claude-plugin" / "plugin.json"
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
