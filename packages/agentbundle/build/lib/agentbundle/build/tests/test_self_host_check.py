"""Tests for `make build --self`, `--self --dry-run`, and `--check` (T7).

The dirty-tree fixture is a `tempfile.TemporaryDirectory()` initialised
as a git repo (`git init`), with a tracked file committed and then
modified — exercising the real refusal path against `git status
--porcelain`.

Test-only symlink creation: several cases below call `os.symlink` /
`Path.symlink_to` to fabricate CLAUDE.md symlink fixtures and exercise
the symlink branch of `_recreate_claude_symlink`. These are runtime
test fixtures, not release content; the Windows-portability lint
(`lint_packs.py`) catches symlinks shipped *inside packs*, which is
a different surface. On native Windows these tests would need a
`skipIf(sys.platform == 'win32')` decorator, but Windows CI is Phase 5
of the portability plan and out of scope for this PR.
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
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


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


def _seed_pack_with_skill(root: Path, name: str, skill: str, description: str) -> Path:
    pack = root / name
    (pack / ".apm" / "skills" / skill).mkdir(parents=True)
    (pack / ".apm" / "skills" / skill / "SKILL.md").write_text(
        f"---\ndescription: {description}\n---\n# {skill}\n",
        encoding="utf-8",
    )
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    return pack


def _seed_discovery(tree: Path) -> Path:
    """Drop a minimal `.adapt-discovery.toml` into a test working tree so
    `run_self_host`'s fail-fast (spec AC14) doesn't reject the call.
    Canonical v0.1 shape per adapt-to-project AC9 — no `[markers]`
    table needed for the no-marker case.
    """
    path = tree / ".adapt-discovery.toml"
    path.write_text('discovery-schema-version = "0.1"\n', encoding="utf-8")
    return path


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
            _seed_discovery(working_tree)

            # Pre-seed via real-write self-host so the working tree
            # exactly matches what a subsequent dry-run will produce
            # (including the new seed/marketplace/symlink outputs).
            run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
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
            _seed_discovery(working_tree)

            run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            _git_commit_all(working_tree, "seed")

            target = working_tree / ".claude" / "skills" / "foo" / "SKILL.md"
            target.write_text("drift!\n", encoding="utf-8")

            buf = io.StringIO()
            with redirect_stderr(buf):
                exit_code = run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=True,
                    force=False,
                    contract=self.contract,
                )
            self.assertNotEqual(exit_code, 0)
            # AC #10: stderr names the drifted file (per-file drift listing).
            stderr_text = buf.getvalue()
            self.assertIn(".claude/skills/foo/SKILL.md", stderr_text)
            self.assertIn("drift", stderr_text)


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
            _seed_discovery(working_tree)
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
            _seed_discovery(working_tree)
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
            _seed_discovery(working_tree)
            (working_tree / ".adapt-discovery.toml").write_text(
                'discovery-schema-version = "0.1"\n[markers]\nproject-name = "demo"\n',
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
            # resolve_markers restricts its scope to adapter-target paths
            # (TARGET_PATHS) — write the fixture under AGENTS.md so the
            # walk actually visits it.
            (tmp_path / "AGENTS.md").write_text(
                "Hello <adapt:name>, also <adapt:unknown>!\n",
                encoding="utf-8",
            )
            count = resolve_markers(tmp_path, {"name": "World"})
            self.assertEqual(count, 1)
            text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
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
            _seed_discovery(working_tree)
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
            core = _seed_pack(packs_dir, "core")
            (core / "seeds").mkdir()
            (core / "seeds" / "AGENTS.md").write_text(
                "# Custom AGENTS.md\n\nDo not lose me.\n",
                encoding="utf-8",
            )

            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            _seed_discovery(working_tree)

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)
            text = (working_tree / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# Custom AGENTS.md", text)
            self.assertIn("Do not lose me.", text)
            self.assertIn("<!-- agent-skills:start -->", text)


class SelfHostAdapterAllowListTests(unittest.TestCase):
    """Self-host allow-list (spec § Phased rollout / § Always do).

    The allow-list is load-bearing: a future contributor adding the
    `kiro` or `copilot` adapter to `ADAPTERS` (the global registry) but
    not to `SELF_HOST_ADAPTERS` would otherwise produce a silent
    no-op surprise. These tests pin the contract.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_non_allow_listed_adapter_is_skipped(self) -> None:
        """An adapter registered in ADAPTERS and the contract but excluded
        from SELF_HOST_ADAPTERS does not run under run_self_host."""
        from unittest.mock import MagicMock, patch

        from agentbundle.build import self_host as self_host_module

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            _seed_discovery(working_tree)
            (working_tree / ".keep").write_text("", encoding="utf-8")
            _git_commit_all(working_tree, "init")

            # Register a sentinel adapter into both ADAPTERS and the
            # contract; if SELF_HOST_ADAPTERS is honoured, it must not
            # be invoked.
            sentinel = MagicMock()
            patched_adapters = dict(self_host_module.ADAPTERS)
            patched_adapters["sentinel"] = sentinel
            patched_contract = dict(self.contract)
            patched_contract["adapter"] = {
                **self.contract["adapter"],
                "sentinel": {"projection": []},
            }
            with patch.object(self_host_module, "ADAPTERS", patched_adapters):
                exit_code = self_host_module.run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=False,
                    force=True,
                    contract=patched_contract,
                )
            self.assertEqual(exit_code, 0)
            sentinel.assert_not_called()

    def test_allow_listed_adapter_runs(self) -> None:
        """An adapter in SELF_HOST_ADAPTERS, registered in ADAPTERS and the
        contract, IS invoked under run_self_host."""
        from unittest.mock import MagicMock, patch

        from agentbundle.build import self_host as self_host_module

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            _seed_discovery(working_tree)
            (working_tree / ".keep").write_text("", encoding="utf-8")
            _git_commit_all(working_tree, "init")

            sentinel = MagicMock()
            patched_adapters = dict(self_host_module.ADAPTERS)
            patched_adapters["sentinel"] = sentinel
            patched_contract = dict(self.contract)
            patched_contract["adapter"] = {
                **self.contract["adapter"],
                "sentinel": {"projection": []},
            }
            with patch.object(self_host_module, "ADAPTERS", patched_adapters), \
                 patch.object(
                     self_host_module,
                     "SELF_HOST_ADAPTERS",
                     ("claude-code", "sentinel"),
                 ):
                exit_code = self_host_module.run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=False,
                    force=True,
                    contract=patched_contract,
                )
            self.assertEqual(exit_code, 0)
            # Sentinel called once per discovered pack (one here).
            self.assertEqual(sentinel.call_count, 1)


class AgentsMdCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_self_host_composes_agents_body_codex_block_and_footer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            core = _seed_pack_with_skill(
                packs_dir, "core", "core-skill", "core skill description"
            )
            _seed_pack_with_skill(
                packs_dir,
                "governance",
                "governance-skill",
                "governance skill description",
            )
            (core / "seeds").mkdir()
            (core / "seeds" / "AGENTS.md").write_text(
                "# Body\n\nBody source.\n", encoding="utf-8"
            )
            (core / "seeds" / "_agents-footer.md").write_text(
                "> Footer source.\n", encoding="utf-8"
            )

            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            _seed_discovery(working_tree)

            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )

            self.assertEqual(exit_code, 0)
            text = (working_tree / "AGENTS.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# Body\n\nBody source.\n"))
            self.assertIn("core skill description", text)
            self.assertIn("governance skill description", text)
            self.assertTrue(text.endswith("> Footer source.\n"))


class ExcludedGlobTests(unittest.TestCase):
    """Pin the glob corner cases that the second adversarial sweep caught:
    `**` must match arbitrary depth (not literal-prefix-startswith), and
    bare root-only patterns must anchor to the repo root."""

    def test_double_star_matches_arbitrary_depth(self) -> None:
        from agentbundle.build.self_host import _is_excluded

        # docs/specs/*/notes/** should match a nested notes file
        self.assertTrue(
            _is_excluded(Path("docs/specs/self-hosting/notes/foo.md"))
        )
        self.assertTrue(
            _is_excluded(Path("docs/specs/feature/notes/sub/dir/bar.md"))
        )

    def test_root_only_patterns_do_not_match_nested(self) -> None:
        from agentbundle.build.self_host import _is_excluded

        # README.md is root-only; nested README.md must NOT be excluded
        self.assertTrue(_is_excluded(Path("README.md")))
        self.assertFalse(_is_excluded(Path(".claude/skills/README.md")))
        self.assertFalse(_is_excluded(Path("docs/random/README.md")))

        # AGENTS.md root-only; nested AGENTS.md must NOT be excluded
        self.assertTrue(_is_excluded(Path("AGENTS.md")))
        self.assertFalse(_is_excluded(Path("packages/foo/AGENTS.md")))

        # Makefile, .gitignore, .adapt-discovery.toml — same pattern
        self.assertTrue(_is_excluded(Path("Makefile")))
        self.assertFalse(_is_excluded(Path("subdir/Makefile")))
        self.assertTrue(_is_excluded(Path(".adapt-discovery.toml")))

    def test_directory_double_star_matches_anything_under(self) -> None:
        from agentbundle.build.self_host import _is_excluded

        # packs/** matches everything under packs/
        self.assertTrue(_is_excluded(Path("packs/core/pack.toml")))
        self.assertTrue(
            _is_excluded(Path("packs/core/.apm/skills/work-loop/SKILL.md"))
        )
        # but packs.md at root is NOT under packs/
        self.assertFalse(_is_excluded(Path("packs.md")))

    def test_projected_overrides_take_precedence(self) -> None:
        from agentbundle.build.self_host import _is_excluded

        # docs/architecture/*.md would exclude README.md, but
        # PROJECTED_README_OVERRIDES restores it
        self.assertFalse(_is_excluded(Path("docs/architecture/README.md")))
        self.assertFalse(_is_excluded(Path("docs/architecture/overview.md")))
        # but a contributor-added subsystem doc IS excluded
        self.assertTrue(_is_excluded(Path("docs/architecture/data-pipeline.md")))


class SeedProjectionTests(unittest.TestCase):
    """Unit tests for `_project_seeds` (spec § Always do, AC7, AC9)."""

    def test_basic_seed_projection_copies_to_root(self) -> None:
        from agentbundle.build.self_host import _project_seeds

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = packs_dir / "core"
            (pack / "seeds" / "docs").mkdir(parents=True)
            (pack / "seeds" / "docs" / "CHARTER.md").write_text(
                "# Charter\n", encoding="utf-8"
            )
            (pack / "pack.toml").write_text(
                '[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8"
            )
            output = tmp_path / "out"
            output.mkdir()

            _project_seeds(packs_dir, output)

            self.assertTrue((output / "docs" / "CHARTER.md").exists())
            self.assertEqual(
                (output / "docs" / "CHARTER.md").read_text(encoding="utf-8"),
                "# Charter\n",
            )

    def test_two_packs_contribute_to_same_dir_without_collision(self) -> None:
        from agentbundle.build.self_host import _project_seeds

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            for name, fname in [("core", "spec.md"), ("governance", "rfc.md")]:
                pack = packs_dir / name
                (pack / "seeds" / "docs" / "_templates").mkdir(parents=True)
                (pack / "seeds" / "docs" / "_templates" / fname).write_text(
                    f"# {fname}\n", encoding="utf-8"
                )
                (pack / "pack.toml").write_text(
                    f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
                    encoding="utf-8",
                )
            output = tmp_path / "out"
            output.mkdir()

            _project_seeds(packs_dir, output)

            self.assertTrue((output / "docs" / "_templates" / "spec.md").exists())
            self.assertTrue((output / "docs" / "_templates" / "rfc.md").exists())

    def test_collision_with_different_content_raises(self) -> None:
        from agentbundle.build.self_host import _project_seeds

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            for name, content in [("core", "v1\n"), ("other", "v2\n")]:
                pack = packs_dir / name
                (pack / "seeds").mkdir(parents=True)
                (pack / "seeds" / "AGENTS.md").write_text(content, encoding="utf-8")
                (pack / "pack.toml").write_text(
                    f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
                    encoding="utf-8",
                )
            output = tmp_path / "out"
            output.mkdir()

            with self.assertRaises(ValueError) as ctx:
                _project_seeds(packs_dir, output)
            self.assertIn("seed collision", str(ctx.exception))
            self.assertIn("AGENTS.md", str(ctx.exception))

    def test_underscore_prefixed_files_are_composition_fragments_not_projected(
        self,
    ) -> None:
        """Files like `_agents-footer.md` live in seeds for composition;
        they aren't standalone projection targets."""
        from agentbundle.build.self_host import _project_seeds

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = packs_dir / "core"
            (pack / "seeds").mkdir(parents=True)
            (pack / "seeds" / "_agents-footer.md").write_text(
                "> footer\n", encoding="utf-8"
            )
            (pack / "seeds" / "AGENTS.md").write_text(
                "# AGENTS\n", encoding="utf-8"
            )
            (pack / "pack.toml").write_text(
                '[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8"
            )
            output = tmp_path / "out"
            output.mkdir()

            _project_seeds(packs_dir, output)

            self.assertTrue((output / "AGENTS.md").exists())
            self.assertFalse((output / "_agents-footer.md").exists())


class MarketplaceAggregationTests(unittest.TestCase):
    """Unit tests for `_aggregate_marketplace`."""

    def test_aggregates_all_plugin_jsons(self) -> None:
        from agentbundle.build.self_host import _aggregate_marketplace

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            for name in ("core", "governance-extras"):
                pack = packs_dir / name
                (pack / ".claude-plugin").mkdir(parents=True)
                (pack / ".claude-plugin" / "plugin.json").write_text(
                    json.dumps({"name": name, "version": "0.1.0"}),
                    encoding="utf-8",
                )
                (pack / "pack.toml").write_text(
                    f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
                    encoding="utf-8",
                )
            output = tmp_path / "out"
            output.mkdir()

            _aggregate_marketplace(packs_dir, output)

            mp = output / ".claude-plugin" / "marketplace.json"
            self.assertTrue(mp.exists())
            payload = json.loads(mp.read_text(encoding="utf-8"))
            names = {entry["name"] for entry in payload["plugins"]}
            self.assertEqual(names, {"core", "governance-extras"})
            self.assertEqual(payload["owner"], {"name": "eugenelim"})

    def test_aggregation_is_deterministic(self) -> None:
        from agentbundle.build.self_host import _aggregate_marketplace

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            for name in ("zeta", "alpha"):
                pack = packs_dir / name
                (pack / ".claude-plugin").mkdir(parents=True)
                (pack / ".claude-plugin" / "plugin.json").write_text(
                    json.dumps({"name": name, "version": "0.1.0"}),
                    encoding="utf-8",
                )
                (pack / "pack.toml").write_text(
                    f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
                    encoding="utf-8",
                )
            output_a = tmp_path / "out_a"
            output_a.mkdir()
            output_b = tmp_path / "out_b"
            output_b.mkdir()
            _aggregate_marketplace(packs_dir, output_a)
            _aggregate_marketplace(packs_dir, output_b)
            self.assertEqual(
                (output_a / ".claude-plugin" / "marketplace.json").read_bytes(),
                (output_b / ".claude-plugin" / "marketplace.json").read_bytes(),
            )


class ClaudeSymlinkTests(unittest.TestCase):
    """Unit tests for `_recreate_claude_symlink`."""

    def test_creates_symlink_when_missing(self) -> None:
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            _recreate_claude_symlink(tree)
            link = tree / "CLAUDE.md"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), "AGENTS.md")

    def test_idempotent_on_correct_symlink(self) -> None:
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            (tree / "CLAUDE.md").symlink_to("AGENTS.md")
            _recreate_claude_symlink(tree)  # should not raise
            self.assertEqual(os.readlink(tree / "CLAUDE.md"), "AGENTS.md")

    def test_replaces_wrong_symlink(self) -> None:
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            (tree / "CLAUDE.md").symlink_to("other.md")
            _recreate_claude_symlink(tree)
            self.assertEqual(os.readlink(tree / "CLAUDE.md"), "AGENTS.md")

    def test_creates_dangling_symlink_when_agents_md_missing_on_posix(self) -> None:
        """Historic POSIX semantic preserved: when AGENTS.md is absent
        the symlink branch creates a dangling link rather than raising.
        Test fixtures throughout this suite rely on it. The copy
        branch, exercised on Windows, takes the documented skip-with-
        warning path instead — see `ClaudeSymlinkFallbackTests`."""
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            link = _recreate_claude_symlink(tree)
            self.assertTrue(link.is_symlink())
            self.assertFalse((tree / "AGENTS.md").exists())


class ClaudeSymlinkFallbackTests(unittest.TestCase):
    """Windows-portability: copy fallback on Windows / under --no-symlink.

    The host OS is faked via monkeypatching `sys.platform` so these
    tests run identically on macOS, Linux, and Windows CI."""

    def test_force_copy_skips_with_warning_when_source_missing(self) -> None:
        """No AGENTS.md to copy → emit a one-line warning, return
        without writing CLAUDE.md. Mirror of the POSIX dangling-symlink
        semantic, adapted to the copy mode."""
        import io
        from contextlib import redirect_stderr

        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _recreate_claude_symlink(tree, force_copy=True)
            self.assertFalse((tree / "CLAUDE.md").exists())
            self.assertIn("missing", buf.getvalue())

    def test_force_copy_writes_regular_file_with_agents_md_contents(self) -> None:
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("# agents canonical\n", encoding="utf-8")
            claude = _recreate_claude_symlink(tree, force_copy=True)
            self.assertFalse(claude.is_symlink())
            self.assertTrue(claude.is_file())
            self.assertEqual(
                claude.read_text(encoding="utf-8"), "# agents canonical\n"
            )

    def test_force_copy_replaces_existing_symlink(self) -> None:
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("content\n", encoding="utf-8")
            (tree / "CLAUDE.md").symlink_to("AGENTS.md")
            _recreate_claude_symlink(tree, force_copy=True)
            claude = tree / "CLAUDE.md"
            self.assertFalse(claude.is_symlink())
            self.assertEqual(claude.read_text(encoding="utf-8"), "content\n")

    def test_force_copy_idempotent_when_contents_match(self) -> None:
        """Idempotency: the on-disk file isn't rewritten when CLAUDE.md
        already matches AGENTS.md, and the warning only fires on the
        actual write (one occurrence across two calls). Pin both
        contracts here so a future refactor cannot silently flip
        either behaviour."""
        import io
        from contextlib import redirect_stderr

        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("hello\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stderr(buf):
                _recreate_claude_symlink(tree, force_copy=True)
                mtime_first = (tree / "CLAUDE.md").stat().st_mtime_ns
                _recreate_claude_symlink(tree, force_copy=True)
                mtime_second = (tree / "CLAUDE.md").stat().st_mtime_ns
            self.assertEqual(mtime_first, mtime_second)
            # Warning fires only on the actual write — the idempotent
            # short-circuit returns early before emitting it.
            self.assertEqual(buf.getvalue().count("--no-symlink"), 1)

    def test_windows_platform_takes_copy_path(self) -> None:
        import io
        from contextlib import redirect_stderr
        from unittest.mock import patch

        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            buf = io.StringIO()
            with patch("agentbundle.build.self_host.sys.platform", "win32"):
                with redirect_stderr(buf):
                    _recreate_claude_symlink(tree)
            claude = tree / "CLAUDE.md"
            self.assertFalse(claude.is_symlink())
            self.assertTrue(claude.is_file())
            self.assertEqual(claude.read_text(encoding="utf-8"), "agents\n")
            self.assertIn("CLAUDE.md", buf.getvalue())
            self.assertIn("copy", buf.getvalue().lower())

    def test_default_path_unchanged_on_posix(self) -> None:
        """Sanity: with no force_copy and sys.platform unmonkeypatched,
        the existing symlink behaviour is unchanged."""
        from agentbundle.build.self_host import _recreate_claude_symlink

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / "AGENTS.md").write_text("agents\n", encoding="utf-8")
            _recreate_claude_symlink(tree)
            link = tree / "CLAUDE.md"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), "AGENTS.md")


class MissingDiscoveryFailFastTests(unittest.TestCase):
    """AC14: missing `.adapt-discovery.toml` causes fail-fast with named message."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_missing_discovery_returns_non_zero_with_named_message(self) -> None:
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
            # Deliberately do NOT seed .adapt-discovery.toml.
            buf = io.StringIO()
            with redirect_stderr(buf):
                exit_code = run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=False,
                    force=True,
                    contract=self.contract,
                )
            self.assertNotEqual(exit_code, 0)
            self.assertIn(
                "missing .adapt-discovery.toml required by --self",
                buf.getvalue(),
            )


class DriftSourceNamingTests(unittest.TestCase):
    """AC: drift messages name source path + regeneration command."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_drift_message_includes_source_and_regen_command(self) -> None:
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
            _seed_discovery(working_tree)

            run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            _git_commit_all(working_tree, "seed")

            # Introduce drift on a projected path.
            target = working_tree / ".claude" / "skills" / "foo" / "SKILL.md"
            target.write_text("drift!\n", encoding="utf-8")

            buf = io.StringIO()
            with redirect_stderr(buf):
                exit_code = run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=True,
                    force=False,
                    contract=self.contract,
                )
            self.assertEqual(exit_code, 1)
            stderr_text = buf.getvalue()
            self.assertIn("[drift]", stderr_text)
            self.assertIn(".claude/skills/foo/SKILL.md", stderr_text)
            # Source path named
            self.assertIn("packs/core/.apm/skills/foo/SKILL.md", stderr_text)
            # Regen command named
            self.assertIn("run: make build-self", stderr_text)


class InfoLineUnclassifiedTests(unittest.TestCase):
    """AC6: paths not in Projected and not in Excluded surface as `[info]`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_unclassified_path_surfaces_as_info_without_failing(self) -> None:
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
            _seed_discovery(working_tree)

            run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )

            # Introduce an unclassified path: not under any Excluded pattern,
            # not in Projected set.
            (working_tree / "stray-note.md").write_text("note\n", encoding="utf-8")
            _git_commit_all(working_tree, "seed + stray")

            buf = io.StringIO()
            with redirect_stderr(buf):
                exit_code = run_self_host(
                    working_tree=working_tree,
                    packs_dir=packs_dir,
                    dry_run=True,
                    force=False,
                    contract=self.contract,
                )
            self.assertEqual(exit_code, 0)  # info lines don't fail the build
            self.assertIn("[info] unclassified: stray-note.md", buf.getvalue())


class ForwardFlowIntegrationTests(unittest.TestCase):
    """End-to-end forward-flow (plan T7): mutate a pack-side source,
    re-project, and assert the projection updated AND the gate is clean
    against the new content."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_forward_flow_pack_edit_re_projects_and_gate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = _seed_pack(packs_dir, "core")
            (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
                "---\ndescription: foo\n---\n# foo v1\n",
                encoding="utf-8",
            )
            working_tree = tmp_path / "tree"
            working_tree.mkdir()
            _git_init(working_tree)
            _seed_discovery(working_tree)

            # Initial real-write seeds the projection.
            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)
            projected = working_tree / ".claude" / "skills" / "foo" / "SKILL.md"
            self.assertIn("foo v1", projected.read_text(encoding="utf-8"))
            _git_commit_all(working_tree, "initial projection")

            # Mutate the pack-side source.
            (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
                "---\ndescription: foo\n---\n# foo v2\n",
                encoding="utf-8",
            )

            # Re-projection picks up the new content.
            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=False,
                force=True,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)
            self.assertIn("foo v2", projected.read_text(encoding="utf-8"))

            # Gate is now clean against the freshly-projected content.
            _git_commit_all(working_tree, "re-projection")
            exit_code = run_self_host(
                working_tree=working_tree,
                packs_dir=packs_dir,
                dry_run=True,
                force=False,
                contract=self.contract,
            )
            self.assertEqual(exit_code, 0)


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
            _seed_discovery(working_tree)
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


class CrlfNormalisationTests(unittest.TestCase):
    """Phase-2 comparison rule (a): text-like files compare equal after
    CRLF→LF normalisation. Pins the spec's CRLF + `core.autocrlf` case."""

    def test_crlf_on_disk_lf_in_shadow_is_not_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            (shadow / "doc.md").write_bytes(b"hello\nworld\n")
            (tree / "doc.md").write_bytes(b"hello\r\nworld\r\n")

            self.assertEqual(diff_against_working_tree(shadow, tree), [])

    def test_trailing_space_after_lf_normalisation_drifts(self) -> None:
        """LF norm doesn't whitewash genuine content differences."""
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            (shadow / "doc.md").write_bytes(b"hello\nworld\n")
            (tree / "doc.md").write_bytes(b"hello \nworld\n")  # extra space

            drifts = diff_against_working_tree(shadow, tree)
            self.assertEqual(len(drifts), 1)
            self.assertIn("doc.md", drifts[0])
            self.assertIn("content differs", drifts[0])

    def test_binary_files_not_normalised(self) -> None:
        """A non-UTF-8 binary that happens to contain 0x0D 0x0A must not
        be normalised — the bytes carry value beyond line termination."""
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            # Two binary blobs that would be equal under LF normalisation
            # but differ byte-for-byte. The leading 0xFF makes them
            # un-decodable as UTF-8.
            (shadow / "icon.bin").write_bytes(b"\xff\x00\r\n\x01")
            (tree / "icon.bin").write_bytes(b"\xff\x00\n\x01")

            drifts = diff_against_working_tree(shadow, tree)
            self.assertEqual(len(drifts), 1)
            self.assertIn("icon.bin", drifts[0])
            self.assertIn("content differs", drifts[0])


class FileModeBitsTests(unittest.TestCase):
    """Phase-2 comparison rule (b): mode bits drift for regular files."""

    def test_mode_bits_drift_for_regular_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            (shadow / "hook.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (tree / "hook.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(shadow / "hook.sh", 0o755)
            os.chmod(tree / "hook.sh", 0o644)

            drifts = diff_against_working_tree(shadow, tree)
            self.assertEqual(len(drifts), 1)
            self.assertIn("hook.sh", drifts[0])
            self.assertIn("mode 0o644 vs 0o755", drifts[0])

    def test_matching_mode_no_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            (shadow / "hook.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (tree / "hook.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(shadow / "hook.sh", 0o755)
            os.chmod(tree / "hook.sh", 0o755)

            self.assertEqual(diff_against_working_tree(shadow, tree), [])


class SymlinkTargetTests(unittest.TestCase):
    """Phase-2 comparison rule (c): symlink targets compared via lstat,
    never followed. Pins the CLAUDE.md → AGENTS.md gate."""

    def test_symlink_target_mismatch_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            os.symlink("AGENTS.md", shadow / "CLAUDE.md")
            os.symlink("README.md", tree / "CLAUDE.md")

            drifts = diff_against_working_tree(shadow, tree)
            self.assertEqual(len(drifts), 1)
            self.assertIn("CLAUDE.md", drifts[0])
            self.assertIn("symlink target differs", drifts[0])
            self.assertIn("AGENTS.md", drifts[0])
            self.assertIn("README.md", drifts[0])

    def test_matching_symlinks_no_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            os.symlink("AGENTS.md", shadow / "CLAUDE.md")
            os.symlink("AGENTS.md", tree / "CLAUDE.md")

            self.assertEqual(diff_against_working_tree(shadow, tree), [])

    def test_symlink_in_shadow_regular_on_disk_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            # Create a target so shadow's symlink "looks" valid in isolation.
            (shadow / "AGENTS.md").write_text("body", encoding="utf-8")
            os.symlink("AGENTS.md", shadow / "CLAUDE.md")
            # On-disk: a regular file with identical content.
            (tree / "AGENTS.md").write_text("body", encoding="utf-8")
            (tree / "CLAUDE.md").write_text("body", encoding="utf-8")

            drifts = diff_against_working_tree(shadow, tree)
            type_mismatch = [d for d in drifts if "CLAUDE.md" in d and "expected symlink" in d]
            self.assertEqual(len(type_mismatch), 1)

    def test_symlink_target_never_followed(self) -> None:
        """A dangling symlink does not crash the gate — the target is
        compared as a string, no read-through happens."""
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()
            os.symlink("/nonexistent/target", shadow / "ptr")
            os.symlink("/nonexistent/target", tree / "ptr")

            # Equal targets → no drift, even though neither target exists.
            self.assertEqual(diff_against_working_tree(shadow, tree), [])


class StrengthenedDiffRegressionIntegrationTests(unittest.TestCase):
    """Integration: one fixture exercising all three Phase-2 rules.

    Each rule is paired with the regression it was added to catch:
    CRLF accidentally drifting against LF source; an executable bit
    silently dropped during projection; a CLAUDE.md → AGENTS.md
    symlink replaced by a regular file or pointed at the wrong target.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_each_rule_catches_its_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "shadow"
            tree = Path(tmp) / "tree"
            shadow.mkdir()
            tree.mkdir()

            # Rule (a) regression: same content, LF in shadow, CRLF on
            # disk. The pre-Phase-2 gate would have drifted; the
            # strengthened gate must NOT.
            (shadow / "doc.md").write_bytes(b"hello\nworld\n")
            (tree / "doc.md").write_bytes(b"hello\r\nworld\r\n")

            # Rule (b) regression: an executable hook script whose
            # +x bit gets dropped on disk.
            (shadow / "hook.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (tree / "hook.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(shadow / "hook.sh", 0o755)
            os.chmod(tree / "hook.sh", 0o644)

            # Rule (c) regression: CLAUDE.md → AGENTS.md projected as a
            # symlink, but on disk it points at the wrong target. The
            # gate must not follow the symlinks — read_bytes would
            # accidentally compare AGENTS.md vs README.md content and
            # might have hidden the regression.
            (shadow / "AGENTS.md").write_text("agents-body", encoding="utf-8")
            (shadow / "README.md").write_text("readme-body", encoding="utf-8")
            (tree / "AGENTS.md").write_text("agents-body", encoding="utf-8")
            (tree / "README.md").write_text("readme-body", encoding="utf-8")
            os.symlink("AGENTS.md", shadow / "CLAUDE.md")
            os.symlink("README.md", tree / "CLAUDE.md")

            drifts = diff_against_working_tree(shadow, tree)

            # Rule (a): no drift on the CRLF-vs-LF file.
            self.assertFalse(
                any("doc.md" in d for d in drifts),
                f"doc.md drifted despite CRLF→LF normalisation: {drifts}",
            )
            # Rule (b): mode drift surfaced.
            mode_drifts = [d for d in drifts if "hook.sh" in d]
            self.assertEqual(len(mode_drifts), 1)
            self.assertIn("mode 0o644 vs 0o755", mode_drifts[0])
            # Rule (c): symlink-target drift surfaced; the gate did
            # NOT follow through to compare AGENTS.md content.
            symlink_drifts = [d for d in drifts if "CLAUDE.md" in d]
            self.assertEqual(len(symlink_drifts), 1)
            self.assertIn("symlink target differs", symlink_drifts[0])


if __name__ == "__main__":
    unittest.main()
