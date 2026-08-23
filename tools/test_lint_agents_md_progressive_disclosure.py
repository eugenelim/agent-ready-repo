"""Mutation-oriented regression checks for progressive-disclosure lint guards."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINTER = ROOT / "tools" / "lint-agents-md.py"


def lint(root: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(LINTER)],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stderr


def seed(root: Path, root_text: str = "# AGENTS.md\n") -> None:
    (root / "AGENTS.md").write_text(root_text, encoding="utf-8")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")


class ProgressiveDisclosureLintTests(unittest.TestCase):
    def test_caps_and_nested_vendor_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root)
            vendor = root / "docs-site/node_modules/x/AGENTS.md"
            vendor.parent.mkdir(parents=True)
            vendor.write_text("x\n" * 100, encoding="utf-8")
            self.assertNotIn("node_modules/x/AGENTS.md is", lint(root))

    def test_root_local_cap_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root)
            local = root / "AGENTS.local.md"
            local.write_text("x\n" * 60, encoding="utf-8")
            self.assertNotIn("AGENTS.local.md is 60 lines", lint(root))
            local.write_text("x\n" * 61, encoding="utf-8")
            self.assertIn("AGENTS.local.md is 61 lines (max 60)", lint(root))

    def test_root_placeholder_but_not_feature_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root, "docs/specs/<feature>/\n")
            self.assertNotIn("unresolved adaptation placeholder", lint(root))
            (root / "AGENTS.md").write_text("<project-name>\n", encoding="utf-8")
            self.assertIn("unresolved adaptation placeholder", lint(root))

    def test_scope_and_fragment_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root, "# Root\n")
            child = root / "x/AGENTS.md"
            child.parent.mkdir()
            child.write_text("# Child\n", encoding="utf-8")
            self.assertIn("missing Applies to", lint(root))
            child.write_text(
                "Applies to `x/`. Inherits the root `AGENTS.md`. "
                "Scope-specific deltas only.\n[s](../AGENTS.md#missing)\n",
                encoding="utf-8",
            )
            self.assertIn("broken heading fragment", lint(root))

    def test_declaration_must_be_first_content_after_indented_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root)
            child = root / "x/AGENTS.md"
            child.parent.mkdir()
            child.write_text(
                "ordinary paragraph\nApplies to `x/`. Inherits the root AGENTS.md.\n",
                encoding="utf-8",
            )
            self.assertIn("missing Applies to", lint(root))
            child.write_text(
                "   # Heading\n\nApplies to `x/`. Inherits the root AGENTS.md.\n",
                encoding="utf-8",
            )
            self.assertNotIn("missing Applies to", lint(root))

    def test_duplication_fires_for_exact_consecutive_parent_block(self) -> None:
        block = (
            "First substantial instruction line belongs in the parent guidance.\n"
            "Second substantial instruction line belongs in the parent guidance.\n"
            "Third substantial instruction line belongs in the parent guidance.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root, "# Root\n\n" + block)
            child = root / "x/AGENTS.md"
            child.parent.mkdir()
            child.write_text(
                "Applies to `x/`. Inherits the root `AGENTS.md`. "
                "Scope-specific deltas only.\n\n" + block,
                encoding="utf-8",
            )
            self.assertIn("delete the child copy", lint(root))

    def test_duplication_silent_for_non_consecutive_and_short_runs(self) -> None:
        block = (
            "First substantial instruction line belongs in the parent guidance.\n"
            "Second substantial instruction line belongs in the parent guidance.\n"
            "Third substantial instruction line belongs in the parent guidance.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent = "# Root\n\n" + block.replace(
                "Second substantial instruction line belongs in the parent guidance.\n",
                "intervening parent line\n",
            )
            seed(root, parent)
            child = root / "x/AGENTS.md"
            child.parent.mkdir()
            child.write_text(
                "Applies to `x/`. Inherits the root `AGENTS.md`. "
                "Scope-specific deltas only.\n\n" + block,
                encoding="utf-8",
            )
            self.assertNotIn("delete the child copy", lint(root))
            (root / "AGENTS.md").write_text(
                "# Root\n\nalpha\nbeta\ngamma\n", encoding="utf-8"
            )
            child.write_text(
                "Applies to `x/`. Inherits the root `AGENTS.md`. "
                "Scope-specific deltas only.\n\nalpha\nbeta\ngamma\n",
                encoding="utf-8",
            )
            self.assertNotIn("delete the child copy", lint(root))
            (root / "AGENTS.md").write_text(
                "# Root\n\nfirst long enough line\nsecond long enough line\n",
                encoding="utf-8",
            )
            child.write_text(
                "Applies to `x/`. Inherits the root `AGENTS.md`. "
                "Scope-specific deltas only.\n\nfirst long enough line\n"
                "second long enough line\n",
                encoding="utf-8",
            )
            self.assertNotIn("delete the child copy", lint(root))

    def test_scaffold_and_claude_alias_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root)
            pairs = (
                ("packs/AGENTS.md", "packages/agentbundle/agentbundle/_data/"
                 "catalogue-scaffold/packs/AGENTS.md"),
                ("profiles/AGENTS.md", "packages/agentbundle/agentbundle/_data/"
                 "catalogue-scaffold/profiles/AGENTS.md"),
            )
            for source, projection in pairs:
                for name, text in ((source, "same\n"), (projection, "different\n")):
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")
            for directory in ("web", "docs-site"):
                path = root / directory
                path.mkdir()
                (path / "AGENTS.md").write_text(
                    "Applies to x. Inherits the root AGENTS.md.\n", encoding="utf-8"
                )
                (path / "CLAUDE.md").write_text("wrong\n", encoding="utf-8")
            result = lint(root)
            self.assertIn("scaffold drift", result)
            self.assertIn("alias must point", result)

    def test_inactive_surfaces_are_exempt_but_active_surfaces_fire(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root)
            inactive = root / "packages/x/build/lib/y/AGENTS.md"
            inactive.parent.mkdir(parents=True)
            inactive.write_text("x\n" * 100, encoding="utf-8")
            (root / "AGENTS.local.md").write_text("root overlay\n", encoding="utf-8")
            spec = root / "docs/specs/foo/spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("<!-- risk-triggers:start -->\n", encoding="utf-8")
            scaffold = root / "packages/x/agentbundle/_data/catalogue-scaffold/profiles/AGENTS.md"
            scaffold.parent.mkdir(parents=True)
            scaffold.write_text("[bad](../missing.md)\n", encoding="utf-8")
            result = lint(root)
            self.assertNotIn("build/lib/y/AGENTS.md is", result)
            self.assertNotIn("root AGENTS.local.md", result)
            self.assertNotIn("docs/specs/foo/spec.md", result)
            active = root / "x/AGENTS.md"
            active.parent.mkdir()
            active.write_text("x\n" * 100, encoding="utf-8")
            self.assertIn("x/AGENTS.md is", lint(root))

    def test_seed_vendor_paths_respect_backlog_and_gitignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed(root)
            contract = root / "contracts/adapter.toml"
            contract.parent.mkdir()
            contract.write_text(
                "[adapter.example]\nprojection = [{target-path = '.claude/skills'}]\n",
                encoding="utf-8",
            )
            active = root / "packs/example/seeds/README.md"
            active.parent.mkdir(parents=True)
            active.write_text(".claude/skills/example/\n", encoding="utf-8")
            self.assertIn("seed vendor path", lint(root))
            active.unlink()
            ignored = root / "packs/example/seeds/.gitignore"
            ignored.write_text(".claude/cache\n", encoding="utf-8")
            backlog = root / "packs/core/seeds/docs/specs/README.md"
            backlog.parent.mkdir(parents=True)
            backlog.write_text(".claude/skills/example/\n", encoding="utf-8")
            self.assertNotIn("seed vendor path", lint(root))
