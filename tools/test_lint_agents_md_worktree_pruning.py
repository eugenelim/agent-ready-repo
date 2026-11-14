"""Keep nested worktrees out of instruction and risk-marker lint scans."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import AbstractContextManager
from pathlib import Path
from unittest.mock import patch

LINTER = Path(__file__).resolve().with_name("lint-agents-md.py")
WORKTREES = (".worktrees", ".claude/worktrees", ".vlx-worktrees")
BLOCK = "<!-- risk-triggers:start -->\ntext\n<!-- risk-triggers:end -->\n"


class WorktreePruningTests(unittest.TestCase):
    """Worktree copies are skipped while ordinary Markdown stays covered."""

    def test_worktree_violations_are_ignored_and_ordinary_ones_reported(self) -> None:
        """Both recursive lint checks preserve their non-worktree coverage."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
            source = root / "packs/core/.apm/skills/work-loop/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(BLOCK, encoding="utf-8")
            for directory in (*WORKTREES, "ordinary", ".claude/skills/ordinary", "worktrees"):
                child = root / directory / "canary"
                child.mkdir(parents=True)
                (child / "AGENTS.md").write_text("bad\n" * 90, encoding="utf-8")
                (child / "notes.md").write_text(BLOCK, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LINTER)], cwd=root, capture_output=True,
                text=True, encoding="utf-8", timeout=30, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            for directory in WORKTREES:
                self.assertNotIn(f"{directory}/canary/", result.stderr)
            for directory in ("ordinary", ".claude/skills/ordinary", "worktrees"):
                self.assertIn(f"{directory}/canary/AGENTS.md is 90 lines", result.stderr)
                self.assertIn(f"{directory}/canary/notes.md carries risk triggers", result.stderr)

    def test_worktree_directories_are_never_opened(self) -> None:
        """Prune before descent rather than filtering an already walked tree."""
        spec = importlib.util.spec_from_file_location("lint_agents_md_pruning", LINTER)
        assert spec is not None and spec.loader is not None
        with patch.dict(sys.modules), patch.object(sys, "path", [str(LINTER.parent), *sys.path]):
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            excluded = [root / directory for directory in WORKTREES]
            for directory in excluded:
                directory.mkdir(parents=True)
                (directory / "unvisited.md").write_text(BLOCK, encoding="utf-8")
            (root / "visible.md").write_text("visible\n", encoding="utf-8")
            scandir = os.scandir

            def guarded_scandir(path: str | os.PathLike[str]) -> AbstractContextManager[Iterator[os.DirEntry[str]]]:
                """Fail if discovery tries to enumerate an excluded subtree."""
                self.assertFalse(any(Path(path).is_relative_to(p) for p in excluded), path)
                return scandir(path)

            with patch.object(os, "scandir", guarded_scandir):
                self.assertEqual(list(module._markdown_files(root)), [root / "visible.md"])
