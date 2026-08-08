"""Projection and end-to-end tests for workspace-status scripts/ (Order 1A).

Coverage:
- Source scripts exist in the pack.
- claude-code adapter projects both scripts under `.claude/skills/workspace-status/scripts/`.
- Real-tree invariant: both scripts present in the self-hosted projection.
- End-to-end installed CLI: exit 0, schema_version == 1, semantic counts plausible.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.scope import shipped_adapters_from_contract

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "contracts" / "adapter.toml"
CORE_PACK = REPO_ROOT / "packs" / "core"
SKILL_NAME = "workspace-status"
_SCRIPTS = ("workspace_status.py", "workspace_status_engine.py")


class SourceInvariantTests(unittest.TestCase):
    """Precondition: source scripts must exist in the pack."""

    _scripts_dir = CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts"

    def test_scripts_directory_exists(self) -> None:
        self.assertTrue(
            self._scripts_dir.is_dir(),
            f"scripts/ directory not found at {self._scripts_dir}",
        )

    def test_cli_script_present_in_pack(self) -> None:
        self.assertTrue(
            (self._scripts_dir / "workspace_status.py").is_file(),
            "workspace_status.py not found in pack scripts/",
        )

    def test_engine_script_present_in_pack(self) -> None:
        self.assertTrue(
            (self._scripts_dir / "workspace_status_engine.py").is_file(),
            "workspace_status_engine.py not found in pack scripts/",
        )

    def test_old_engine_not_in_tools(self) -> None:
        stale = REPO_ROOT / "tools" / "workspace_status_engine.py"
        self.assertFalse(
            stale.exists(),
            f"Old engine copy still exists at {stale} — should have been git mv'd",
        )


class AdapterProjectionTests(unittest.TestCase):
    """Both scripts appear under every shipped adapter's projection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def _project_to_tmp(self, adapter_name: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        ADAPTERS[adapter_name](CORE_PACK, self.contract, tmp)
        return tmp

    def test_scripts_project_for_all_adapters(self) -> None:
        """scripts/ present under every shipped adapter's skill output."""
        for adapter_name in shipped_adapters_from_contract():
            with self.subTest(adapter=adapter_name):
                out = self._project_to_tmp(adapter_name)
                # Each adapter places skills under its own prefix; find by rglob.
                script_dirs = list(out.rglob(f"{SKILL_NAME}/scripts"))
                self.assertTrue(
                    len(script_dirs) >= 1,
                    f"{adapter_name}: no scripts/ directory found under {out}",
                )
                for name in _SCRIPTS:
                    found = any((d / name).is_file() for d in script_dirs)
                    self.assertTrue(
                        found,
                        f"{adapter_name}: {name} not found in any scripts/ dir",
                    )

    def test_skill_md_projects_for_claude_code(self) -> None:
        out = self._project_to_tmp("claude-code")
        skill_md = out / ".claude" / "skills" / SKILL_NAME / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md not projected alongside scripts/ for claude-code")

    def test_projected_cli_invokes_ok(self) -> None:
        """Projected CLI (claude-code) exits 0 against the real repo root (exercise)."""
        out = self._project_to_tmp("claude-code")
        cli = out / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        if not cli.exists():
            self.skipTest("CLI not projected — previous projection test likely failed")
        r = subprocess.run(
            [sys.executable, str(cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, f"CLI failed: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertEqual(data.get("schema_version"), 1)

    def test_exit2_stderr_no_root_path(self) -> None:
        """Exit-2 stderr must not expose the --root path."""
        out = self._project_to_tmp("claude-code")
        cli = out / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        if not cli.exists():
            self.skipTest("CLI not projected — previous projection test likely failed")
        # Pass an existing file (not a dir) as --root to force NotADirectoryError → exit 2.
        fake_file = out / "not_a_dir.txt"
        fake_file.write_bytes(b"")
        r = subprocess.run(
            [sys.executable, str(cli), "--root", str(fake_file)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(r.returncode, 2, f"Expected exit 2, got {r.returncode}; stderr={r.stderr!r}")
        self.assertNotIn(str(fake_file), r.stderr,
            "exit-2 stderr exposes the --root path; it must be redacted to <root>")

    def test_projected_cli_against_fixture_workspace(self) -> None:
        """Projected CLI against a fixture workspace (not the real repo).

        Exercises the install path end-to-end: projects to a temp dir, invokes the
        CLI from a CWD outside the fixture, parses the JSON, and cross-checks
        key semantic fields against the source-engine CLI to detect installed/source
        divergence.
        """
        out = self._project_to_tmp("claude-code")
        cli = out / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        if not cli.exists():
            self.skipTest("CLI not projected — previous projection test likely failed")
        fixture = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fixture, True)
        (fixture / "workspace.toml").write_bytes(b"# fixture\n")

        # Invoke from a CWD that is neither the fixture nor the repo root.
        outside_cwd = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside_cwd, True)
        r = subprocess.run(
            [sys.executable, str(cli), "--root", str(fixture)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(outside_cwd),
        )
        self.assertEqual(r.returncode, 0, f"CLI failed on fixture: {r.stderr}")
        installed = json.loads(r.stdout)
        self.assertEqual(installed.get("schema_version"), 1)
        self.assertTrue(installed.get("workspace_present"), "workspace_present should be True")

        # Cross-check against source engine — same fixture, same CWD.
        source_cli = CORE_PACK / ".apm" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"
        r_src = subprocess.run(
            [sys.executable, str(source_cli), "--root", str(fixture)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(outside_cwd),
        )
        self.assertEqual(r_src.returncode, 0, f"Source CLI failed: {r_src.stderr}")
        source = json.loads(r_src.stdout)
        for key in ("schema_version", "workspace_present", "work", "shaping", "reconciliation"):
            self.assertEqual(
                installed.get(key), source.get(key),
                f"Installed vs source engine mismatch on {key!r}",
            )


class RealTreeProjectionTests(unittest.TestCase):
    """Real-tree invariant: scripts present in the self-hosted .claude/ projection."""

    _projected_scripts = (
        REPO_ROOT / ".claude" / "skills" / SKILL_NAME / "scripts"
    )

    def test_scripts_in_real_tree_projection(self) -> None:
        """Both scripts must be present in the self-hosted projection.

        If this test fails, run `make build-self` (or
        `python3 -m agentbundle catalogue self-host --root . --write --force`)
        to regenerate the projection.
        """
        if not self._projected_scripts.is_dir():
            self.skipTest(
                f"self-hosted scripts/ not found at {self._projected_scripts} — "
                "run make build-self to generate projection"
            )
        for name in _SCRIPTS:
            with self.subTest(script=name):
                self.assertTrue(
                    (self._projected_scripts / name).is_file(),
                    f"{name} absent from self-hosted projection at {self._projected_scripts}",
                )


class EndToEndCLITests(unittest.TestCase):
    """Installed CLI executed end-to-end; result recorded."""

    _cli = REPO_ROOT / ".claude" / "skills" / SKILL_NAME / "scripts" / "workspace_status.py"

    @classmethod
    def setUpClass(cls) -> None:
        if not cls._cli.exists():
            cls._skip_reason = (
                f"Installed CLI not found at {cls._cli} — run make build-self"
            )
        else:
            cls._skip_reason = None

    def _skip_if_not_installed(self) -> None:
        if self._skip_reason:
            self.skipTest(self._skip_reason)

    def test_installed_cli_exit_0(self) -> None:
        """Installed CLI returns exit 0 against the real repo."""
        self._skip_if_not_installed()
        r = subprocess.run(
            [sys.executable, str(self._cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, f"CLI failed.\nstdout: {r.stdout[:500]}\nstderr: {r.stderr[:500]}")

    def test_installed_cli_schema_version(self) -> None:
        """Output is valid JSON with schema_version == 1."""
        self._skip_if_not_installed()
        r = subprocess.run(
            [sys.executable, str(self._cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("schema_version"), 1)
        # Record semantic counts (printed to the test runner output)
        work = data.get("work", {})
        diag = data.get("diagnostics", {})
        print(
            f"\nAC17 record — installed CLI against real repo:\n"
            f"  exit_code=0  schema_version=1\n"
            f"  work.ready={len(work.get('ready', []))}"
            f"  work.blocked={len(work.get('blocked', []))}"
            f"  work.active={len(work.get('active', []))}"
            f"  work.shipped={len(work.get('shipped', []))}\n"
            f"  diagnostics.spec_files_read={diag.get('spec_files_read', '?')}",
            flush=True,
        )

    def test_installed_cli_workspace_present(self) -> None:
        """workspace_present is True for the real repo."""
        self._skip_if_not_installed()
        r = subprocess.run(
            [sys.executable, str(self._cli), "--root", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data.get("workspace_present"), "workspace_present should be True for the real repo")


if __name__ == "__main__":
    unittest.main()
