"""Tests for the build pipeline (T6) — recipe loading, dispatch,
pack-internal collision detection, aggregate marketplace, RFC-0002
recipe expansion shapes, and the empty-pack edge case.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.contract import load as load_contract
from agentbundle.build.main import (
    Pack,
    discover_packs,
    load_recipe,
    load_recipe_from_path,
    run_recipe,
    validate_pack_uniqueness,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "specs" / "adapter-contract" / "contract.toml"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _seed_pack(root: Path, name: str = "demo") -> Path:
    pack = root / name
    (pack / ".apm" / "skills" / "foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
        "---\ndescription: foo\n---\n# foo\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "bar.md").write_text("---\nname: bar\n---\n", encoding="utf-8")
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "baz.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (pack / ".apm" / "commands").mkdir(parents=True)
    (pack / ".apm" / "commands" / "qux.md").write_text("# qux\n", encoding="utf-8")

    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\ndescription = "demo pack"\n',
        encoding="utf-8",
    )
    (pack / ".claude-plugin").mkdir(parents=True)
    (pack / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {"name": name, "version": "0.1.0", "description": "demo plugin"}, indent=2
        ),
        encoding="utf-8",
    )
    return pack


class PerPackClaudePluginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_runs_against_single_pack_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            output_dir = tmp_path / "dist"
            recipe = load_recipe("per-pack-claude-plugin")
            result = run_recipe(recipe, discover_packs(packs_dir), output_dir, self.contract)
            self.assertIn("core", result["produced"])
            self.assertTrue(
                (output_dir / "claude-plugins" / "core" / ".claude-plugin" / "plugin.json").exists()
            )
            self.assertTrue(
                (output_dir / "claude-plugins" / "core" / ".claude" / "skills" / "foo").exists()
            )


class PerPackApmPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_produces_apm_yml_and_apm_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            output_dir = tmp_path / "dist"
            recipe = load_recipe("per-pack-apm-package")
            run_recipe(recipe, discover_packs(packs_dir), output_dir, self.contract)
            apm_yml = output_dir / "apm" / "core" / "apm.yml"
            self.assertTrue(apm_yml.exists())
            self.assertIn("name: core", apm_yml.read_text(encoding="utf-8"))
            self.assertTrue((output_dir / "apm" / "core" / ".apm" / "skills" / "foo").exists())


class MarketplaceAggregateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_aggregates_all_plugin_jsons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            _seed_pack(packs_dir, "extras")
            output_dir = tmp_path / "dist"

            run_recipe(
                load_recipe("per-pack-claude-plugin"),
                discover_packs(packs_dir),
                output_dir,
                self.contract,
            )
            result = run_recipe(
                load_recipe("marketplace"),
                discover_packs(packs_dir),
                output_dir,
                self.contract,
            )

            marketplace = output_dir / "claude-plugins" / "marketplace.json"
            self.assertTrue(marketplace.exists())
            payload = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["plugins"]), 2)
            self.assertEqual(result["entries"], 2)


class PackInternalCollisionTests(unittest.TestCase):
    def test_duplicate_skill_name_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_path = _seed_pack(tmp_path / "packs", "core")
            (pack_path / ".apm" / "skills" / "foo").mkdir(exist_ok=True)
            (pack_path / ".apm" / "skills" / "foo.md").write_text("dup\n", encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                validate_pack_uniqueness(Pack(name="core", path=pack_path))
            self.assertIn("duplicate primitive", str(caught.exception))


class UnknownRecipeTests(unittest.TestCase):
    def test_unknown_recipe_name_exits_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentbundle.build",
                    "build",
                    "--recipe",
                    "bogus-recipe",
                    "--packs-dir",
                    tmp,
                    "--output-dir",
                    tmp,
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("bogus-recipe", result.stderr)


class UnknownAdapterTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_unknown_target_in_recipe_raises(self) -> None:
        recipe = load_recipe_from_path(FIXTURES / "recipes" / "bogus-target.toml")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            with self.assertRaises(ValueError) as caught:
                run_recipe(recipe, discover_packs(packs_dir), tmp_path / "dist", self.contract)
            self.assertIn("bogus", str(caught.exception))


class Rfc0002RecipeLoadTests(unittest.TestCase):
    """The three RFC-0002 recipe files load and expand to the shapes T7 needs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_per_pack_overlay_expansion_shape(self) -> None:
        recipe = load_recipe("per-pack-overlay")
        self.assertEqual(recipe.type, "overlay")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            result = run_recipe(
                recipe, discover_packs(packs_dir), tmp_path / "dist", self.contract
            )
            self.assertEqual(result["type"], "overlay")
            self.assertIn("core", result["expansion"])
            paths = result["expansion"]["core"]
            self.assertTrue(any(p.endswith(".apm") for p in paths))
            self.assertTrue(any(p.endswith("seeds") for p in paths))

    def test_composite_agents_md_expansion(self) -> None:
        recipe = load_recipe("composite-agents-md")
        self.assertEqual(recipe.type, "composite")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack_one = _seed_pack(packs_dir, "core")
            pack_two = _seed_pack(packs_dir, "extras")
            (pack_one / "seeds").mkdir()
            (pack_one / "seeds" / "AGENTS.fragment.md").write_text("core fragment\n", encoding="utf-8")
            (pack_two / "seeds").mkdir()
            (pack_two / "seeds" / "AGENTS.fragment.md").write_text("extras fragment\n", encoding="utf-8")
            result = run_recipe(
                recipe, discover_packs(packs_dir), tmp_path / "dist", self.contract
            )
            self.assertEqual(len(result["composed"]), 2)

    def test_composite_marketplace_expansion(self) -> None:
        recipe = load_recipe("composite-marketplace")
        self.assertEqual(recipe.type, "composite")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            _seed_pack(packs_dir, "core")
            _seed_pack(packs_dir, "extras")
            _seed_pack(packs_dir, "monorepo-extras")
            result = run_recipe(
                recipe, discover_packs(packs_dir), tmp_path / "dist", self.contract
            )
            self.assertEqual(len(result["composed"]), 3)


class EmptyPackEdgeCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_pack_missing_commands_dir_runs_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            packs_dir = tmp_path / "packs"
            packs_dir.mkdir()
            pack = _seed_pack(packs_dir, "minimal")
            (pack / ".apm" / "commands" / "qux.md").unlink()
            (pack / ".apm" / "commands").rmdir()
            output_dir = tmp_path / "dist"
            run_recipe(
                load_recipe("per-pack-claude-plugin"),
                discover_packs(packs_dir),
                output_dir,
                self.contract,
            )
            self.assertFalse(
                (output_dir / "claude-plugins" / "minimal" / ".claude" / "commands").exists()
            )


if __name__ == "__main__":
    unittest.main()
