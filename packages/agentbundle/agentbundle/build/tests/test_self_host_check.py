"""Tests for `make build --self`, `--self --dry-run`, and `--check` (T7).

The dirty-tree fixture is a `tempfile.TemporaryDirectory()` initialised
as a git repo (`git init`), with a tracked file committed and then
modified — exercising the real refusal path against `git status
--porcelain`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.contract import load as load_contract
from agentbundle.build.self_host import (
    diff_against_working_tree,
    is_dirty_tree,
    project_to_temp,
    resolve_markers,
    run_self_host,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "specs" / "adapter-contract" / "contract.toml"


def _seed_pack(root: Path, name: str = "core") -> Path:
    pack = root / name
    (pack / ".apm" / "skills" / "foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
        "---\ndescription: foo\n---\n# foo\n",
        encoding="utf-8",
    )
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    return pack


def _git_init(path: Path) -> None:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=env)
    subprocess.run(["git", "-C", str(path), "checkout", "-q", "-b", "main"], check=False, env=env)


def _git_commit_all(path: Path, message: str) -> None:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", message], check=True, env=env)


class DryRunCleanTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_dry_run_against_already_projected_tree_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)

            # First project so the working tree matches the rendered output.
            from agentbundle.build.adapters import ADAPTERS
            for adapter_name, project in ADAPTERS.items():
                if adapter_name not in self.contract["adapter"]:
                    continue
                project(packs_dir / "core", self.contract, working_tree)
            _git_commit_all(working_tree, "seed")

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=True,
                force=False,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)

    def test_dry_run_with_drift_returns_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)

            from agentbundle.build.adapters import ADAPTERS
            for adapter_name, project in ADAPTERS.items():
                if adapter_name not in self.contract["adapter"]:
                    continue
                project(packs_dir / "core", self.contract, working_tree)
            _git_commit_all(working_tree, "seed")

            target = working_tree / ".claude" / "skills" / "foo" / "SKILL.md"
            target.write_text("drift!\n", encoding="utf-8")

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=True,
                force=False,
                contract=self.contract,
            )
            self.assertNotEqual(exit_code, 0)


class DirtyTreeRefusalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_refuses_dirty_tree_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            (working_tree / "tracked.txt").write_text("a\n", encoding="utf-8")
            _git_commit_all(working_tree, "seed")
            (working_tree / "tracked.txt").write_text("b\n", encoding="utf-8")
            self.assertTrue(is_dirty_tree(working_tree))

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=False,
                contract=self.contract,
            )
            self.assertNotEqual(exit_code, 0)

    def test_force_proceeds_through_dirty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            (working_tree / "tracked.txt").write_text("a\n", encoding="utf-8")
            _git_commit_all(working_tree, "seed")
            (working_tree / "tracked.txt").write_text("b\n", encoding="utf-8")

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)


class MarkerResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_self_resolves_markers_against_discovery_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = _seed_pack(packs_dir, "core")
            # Use a marker in a skill file the adapter projects through.
            (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
                "---\ndescription: <adapt:project-name>\n---\nHello <adapt:project-name>.\n",
                encoding="utf-8",
            )
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            (working_tree / ".adapt-discovery.toml").write_text(
                '[adapt]\nproject-name = "demo"\n',
                encoding="utf-8",
            )

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,  # tree is dirty (just added discovery file)
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)
            skill = working_tree / ".claude" / "skills" / "foo" / "SKILL.md"
            self.assertTrue(skill.exists())
            text = skill.read_text(encoding="utf-8")
            self.assertIn("demo", text)
            self.assertNotIn("<adapt:", text)

    def test_resolve_markers_helper_leaves_unmatched_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "file.md").write_text(
                "Hello <adapt:name>, also <adapt:unknown>!\n",
                encoding="utf-8",
            )
            count = resolve_markers(tmp_path, {"name": "World"})
            self.assertEqual(count, 1)
            text = (tmp_path / "file.md").read_text(encoding="utf-8")
            self.assertIn("Hello World", text)
            self.assertIn("<adapt:unknown>", text)


class WorkingTreeOnConflictTests(unittest.TestCase):
    """`--self` must honour each adapter's on-conflict policy against
    the working tree. The previous render-to-temp pattern broke this
    because the temp dir started empty."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_merge_json_preserves_unrelated_keys_under_self(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = _seed_pack(packs_dir, "core")
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "baz.toml").write_text(
                '[hooks]\nbaz = "tools/hooks/baz.sh"\n',
                encoding="utf-8",
            )

            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            settings_path = working_tree / ".claude" / "settings.local.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text(
                json.dumps({"otherKey": {"preserved": True}}),
                encoding="utf-8",
            )

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            # Existing key survives — merge-managed-key-only honoured.
            self.assertEqual(data["otherKey"], {"preserved": True})
            # New hooks-key content landed.
            self.assertIn("baz", data["hooks"])

    def test_managed_block_preserves_outside_content_under_self(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")

            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            agents_md = working_tree / "AGENTS.md"
            preamble = "# Custom AGENTS.md\n\nDo not lose me.\n"
            agents_md.write_text(preamble, encoding="utf-8")

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)
            text = agents_md.read_text(encoding="utf-8")
            self.assertIn("# Custom AGENTS.md", text)
            self.assertIn("Do not lose me.", text)
            self.assertIn("<!-- agent-skills:start -->", text)


class DirtyTreeStderrMessageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_refusal_message_names_dirty_tree(self) -> None:
        import io
        from contextlib import redirect_stderr

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            (working_tree / "tracked.txt").write_text("a\n", encoding="utf-8")
            _git_commit_all(working_tree, "seed")
            (working_tree / "tracked.txt").write_text("b\n", encoding="utf-8")

            buf = io.StringIO()
            with redirect_stderr(buf):
                exit_code = run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=False,
                    force=False,
                    contract=self.contract,
                )
            self.assertNotEqual(exit_code, 0)
            self.assertIn("dirty", buf.getvalue())
            self.assertIn("refusing", buf.getvalue())


class PlainBuildCopiesMarkerThroughTests(unittest.TestCase):
    """Spec § Boundaries: only --self resolves markers. Plain `make build`
    must copy `<adapt:NAME>` markers through unchanged."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_plain_build_preserves_marker(self) -> None:
        from agentbundle.build.main import discover_packs, load_recipe, run_recipe

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = _seed_pack(packs_dir, "core")
            (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
                "---\ndescription: foo\n---\nHello <adapt:project-name>.\n",
                encoding="utf-8",
            )
            (pack / ".claude-plugin").mkdir()
            (pack / ".claude-plugin" / "plugin.json").write_text(
                json.dumps({"name": "core", "version": "0.1.0", "description": "x"}),
                encoding="utf-8",
            )
            output_dir = tmp_path / "dist"
            run_recipe(
                load_recipe("per-pack-claude-plugin"),
                discover_packs(packs_dir),
                output_dir,
                self.contract,
            )
            text = (
                output_dir
                / "claude-plugins"
                / "core"
                / ".claude"
                / "skills"
                / "foo"
                / "SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("<adapt:project-name>", text)


if __name__ == "__main__":
    unittest.main()
