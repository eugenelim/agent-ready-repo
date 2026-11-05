"""Regression checks for the `local gate` make-target lint rule.

These assert stderr because scratch repositories intentionally fail unrelated
structure checks; the local-gate diagnostic is the signal under test.
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
MARKER = "local-gate target not defined"
AGENTS = (
    "# AGENTS.md\n\n```bash\n"
    "make alpha beta  # ~8s. This IS the local gate\n"
    "```\n"
)


def run(root: Path) -> str:
    result = subprocess.run([sys.executable, str(LINTER)], cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, encoding="utf-8")
    return result.stderr


def fixture(root: Path, makefile: str) -> None:
    (root / "AGENTS.md").write_text(AGENTS, encoding="utf-8")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")
    (root / "Makefile").write_text(makefile, encoding="utf-8")


class LocalGateTargetTests(unittest.TestCase):
    def test_missing_second_target_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, "alpha:\n\t@true\n")
            stderr = run(root)
            self.assertIn(f"{MARKER}: beta", stderr)
            self.assertNotIn(f"{MARKER}: alpha", stderr)

    def test_defined_targets_are_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, "alpha:\n\t@true\nbeta:\n\t@true\n")
            self.assertNotIn(MARKER, run(root))

    def test_real_repository_is_silent(self) -> None:
        self.assertNotIn(MARKER, run(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
