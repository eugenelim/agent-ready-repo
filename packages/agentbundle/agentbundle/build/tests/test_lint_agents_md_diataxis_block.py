"""`tools/lint-agents-md.py` check #8 — the Diátaxis-structure block.

After the per-pack guide migration (ADR-0020) the four Diátaxis quadrant
directories may live either at the top level (`docs/guides/<quadrant>/`, the
by-quadrant scaffold an adopter installs) or under `docs/guides/_shared/`
(the per-pack layout this catalogue uses). The check passes in *either*
layout and fails only when a quadrant name resolves to neither.

This guards the two-branch condition (`top-level OR _shared/`) so a future
refactor that flips the OR to an AND — requiring both layouts — ships red
instead of silently passing.

Test shape mirrors the sibling block tests: CLI subprocess in a `tmp_path`
scratch tree run with `cwd=tmp_path` (the linter falls back to cwd when the
tree isn't a git repo); assert on the block's stdout/stderr message.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
LINTER = REPO_ROOT / "tools" / "lint-agents-md.py"

QUADRANTS = ("tutorials", "how-to", "reference", "explanation")

_OK_SUBSTR = "exposes the four Diátaxis quadrants"
_MISSING_SUBSTR = "is missing Diátaxis subdirectories"


def _seed_common(root: Path) -> None:
    (root / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guides").mkdir(parents=True, exist_ok=True)


def _make_quadrants(base: Path) -> None:
    for q in QUADRANTS:
        d = base / q
        d.mkdir(parents=True, exist_ok=True)
        (d / "README.md").write_text("# quadrant\n", encoding="utf-8")


def _run_linter(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINTER)],
        cwd=cwd,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        check=False,
    )


class DiataxisBlockTests(unittest.TestCase):
    def test_top_level_quadrants_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_common(root)
            _make_quadrants(root / "docs" / "guides")
            result = _run_linter(root)
            self.assertIn(_OK_SUBSTR, result.stdout)
            self.assertNotIn(_MISSING_SUBSTR, result.stderr)

    def test_per_pack_shared_quadrants_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_common(root)
            _make_quadrants(root / "docs" / "guides" / "_shared")
            # A representative pack home, no top-level quadrant dirs.
            (root / "docs" / "guides" / "core" / "how-to").mkdir(parents=True)
            result = _run_linter(root)
            self.assertIn(_OK_SUBSTR, result.stdout)
            self.assertNotIn(_MISSING_SUBSTR, result.stderr)

    def test_neither_layout_flags_all_four(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_common(root)
            # docs/guides/ exists but carries no quadrant dirs in either spot.
            result = _run_linter(root)
            self.assertIn(_MISSING_SUBSTR, result.stderr)
            for q in QUADRANTS:
                self.assertIn(q, result.stderr)


if __name__ == "__main__":
    unittest.main()
