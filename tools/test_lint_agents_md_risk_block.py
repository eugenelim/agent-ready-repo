"""Regression checks for the risk-trigger single-home lint rule.

These assert stderr because scratch repositories intentionally fail unrelated
structure checks; the risk-trigger diagnostic is the signal under test.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "tools" / "lint-agents-md.py"
MARKER = "risk-trigger-block drift"
BLOCK = "<!-- risk-triggers:start -->\ntext\n<!-- risk-triggers:end -->\n"


def run(root: Path) -> str:
    result = subprocess.run([sys.executable, str(LINTER)], cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, encoding="utf-8")
    return result.stderr


class RiskBlockHomeTests(unittest.TestCase):
    def test_canonical_source_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "packs/core/.apm/skills/work-loop/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(BLOCK, encoding="utf-8")
            (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
            (root / "CLAUDE.md").symlink_to("AGENTS.md")
            self.assertNotIn(MARKER, run(root))

    def test_canonical_deletion_and_truncation_fail(self) -> None:
        for text in ("", "<!-- risk-triggers:start -->\n"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "packs/core/.apm/skills/work-loop/SKILL.md"
                source.parent.mkdir(parents=True)
                source.write_text(text, encoding="utf-8")
                (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
                (root / "CLAUDE.md").symlink_to("AGENTS.md")
                self.assertIn(MARKER, run(root))

    def test_two_canonical_blocks_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "packs/core/.apm/skills/work-loop/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(BLOCK + BLOCK, encoding="utf-8")
            (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
            (root / "CLAUDE.md").symlink_to("AGENTS.md")
            self.assertIn("must carry exactly one", run(root))

    def test_noncanonical_homes_fail(self) -> None:
        # The canonical source must exist in the fixture. Without it the
        # "source must carry one complete block" branch emits the same marker,
        # so the assertion below passes whether or not the non-canonical-home
        # guard exists — the test cannot then detect that guard's removal.
        for path in ("AGENTS.md", "packs/core/seeds/AGENTS.md", "docs/CONVENTIONS.md"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "packs/core/.apm/skills/work-loop/SKILL.md"
                source.parent.mkdir(parents=True)
                source.write_text(BLOCK, encoding="utf-8")
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(BLOCK, encoding="utf-8")
                (root / "AGENTS.md").write_text(BLOCK if path == "AGENTS.md" else "# AGENTS.md\n", encoding="utf-8")
                (root / "CLAUDE.md").symlink_to("AGENTS.md")
                self.assertIn(MARKER, run(root))
