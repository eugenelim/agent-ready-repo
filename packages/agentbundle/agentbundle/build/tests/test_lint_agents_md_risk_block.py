"""Local regression check for `tools/lint-agents-md.py` check 10g, which
fails when the `risk-triggers:start`..`:end` block diverges between the
four docs that carry it (work-loop-light-mode spec AC2).

The standing CI guard is the lint itself (run in `.github/workflows/docs.yml`);
this test — like its sibling `test_lint_agents_md_legacy_block.py` — runs
only under a local `pytest` invocation, not in CI, and exists to pin the
check's behaviour against regressions.

Test shape mirrors test_lint_agents_md_legacy_block.py: CLI subprocess
invocation in a `tmp_path` scratch tree, asserting on stderr (the linter
fails on other missing-repo-structure checks regardless, so the exit code
is not a clean signal — the `risk-trigger-block drift` substring is).
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

_DRIFT_MARKER = "risk-trigger-block drift"


def _block(third_bullet: str) -> str:
    return (
        "<!-- risk-triggers:start — canonical wording lives here. -->\n"
        "**Risk triggers — any one routes the work to full mode:**\n\n"
        "- **Unfamiliar** — territory you don't know well.\n"
        "- **Multi-person** — more than one person builds or reviews it.\n"
        f"- {third_bullet}\n"
        "<!-- risk-triggers:end -->\n"
    )


def _seed(root: Path, canonical_block: str, agents_block: str) -> None:
    skill = root / ".claude" / "skills" / "work-loop"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "# Skill: work-loop\n\n" + canonical_block, encoding="utf-8"
    )
    (root / "AGENTS.md").write_text(
        "# AGENTS.md\n\n" + agents_block, encoding="utf-8"
    )
    (root / "CLAUDE.md").symlink_to("AGENTS.md")


def _run_linter(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINTER)],
        cwd=cwd,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        check=False,
    )


class RiskBlockEqualityTests(unittest.TestCase):
    def test_fires_when_blocks_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _seed(
                tmp_path,
                canonical_block=_block("**New dependency** — it adds a dependency."),
                agents_block=_block("**New dependency** — it adds a DIFFERENT thing."),
            )
            result = _run_linter(tmp_path)
            self.assertIn(_DRIFT_MARKER, result.stderr)
            self.assertIn("AGENTS.md", result.stderr)

    def test_silent_when_blocks_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            same = _block("**New dependency** — it adds a dependency.")
            _seed(tmp_path, canonical_block=same, agents_block=same)
            result = _run_linter(tmp_path)
            self.assertNotIn(_DRIFT_MARKER, result.stderr)

    def test_fires_on_truncated_block(self) -> None:
        # A `:start` with no matching `:end` is itself drift — fail closed.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            same = _block("**New dependency** — it adds a dependency.")
            _seed(tmp_path, canonical_block=same, agents_block=same)
            # Truncate the AGENTS.md copy: drop its closing marker.
            agents = tmp_path / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8").replace(
                    "<!-- risk-triggers:end -->\n", ""
                ),
                encoding="utf-8",
            )
            result = _run_linter(tmp_path)
            self.assertIn(_DRIFT_MARKER, result.stderr)
            self.assertIn("truncated", result.stderr)

    def test_silent_when_no_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "AGENTS.md").write_text(
                "# AGENTS.md\n\nNo risk-trigger block here.\n", encoding="utf-8"
            )
            (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
            result = _run_linter(tmp_path)
            self.assertNotIn(_DRIFT_MARKER, result.stderr)


if __name__ == "__main__":
    unittest.main()
