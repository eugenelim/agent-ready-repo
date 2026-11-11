"""Regression checks for the `local gate` make-target lint rule.

These assert stderr because scratch repositories intentionally fail unrelated
structure checks; the local-gate diagnostic is the signal under test.
"""

from __future__ import annotations

import importlib.util
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


def fixture(root: Path, makefile: str, agents: str = AGENTS) -> None:
    (root / "AGENTS.md").write_text(agents, encoding="utf-8")
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

    def undefined(self, line: str, makefile: str = "") -> set[str]:
        """Targets reported undefined for a `local gate` fenced line over `makefile`."""
        agents = f"# AGENTS.md\n\n```bash\n{line}  # the local gate\n```\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, makefile, agents)
            return {
                part.split(f"{MARKER}: ")[1].strip()
                for part in run(root).splitlines()
                if MARKER in part
            }

    def test_every_make_invocation_on_a_line_is_checked(self) -> None:
        self.assertEqual(self.undefined("make aa; make bb"), {"aa", "bb"})
        self.assertEqual(self.undefined("make aa && make bb"), {"aa", "bb"})

    def test_prose_starting_with_make_is_not_a_target(self) -> None:
        agents = "# AGENTS.md\n\nThis is the local gate: `make aa`.\nmake any push.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, "", agents)
            stderr = run(root)
        self.assertIn(f"{MARKER}: aa", stderr)
        self.assertNotIn(f"{MARKER}: any", stderr)
        self.assertNotIn(f"{MARKER}: push", stderr)

    def test_option_arguments_are_not_targets(self) -> None:
        self.assertEqual(self.undefined("make -C web build"), {"build"})
        self.assertEqual(self.undefined("make -f other.mk -j 4 build"), {"build"})
        self.assertEqual(self.undefined("make -j4 build"), {"build"})

    def test_real_repository_is_silent(self) -> None:
        self.assertNotIn(MARKER, run(REPO_ROOT))

    def test_real_repository_targets_include_precheck(self) -> None:
        spec = importlib.util.spec_from_file_location("lint_agents_md", LINTER)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("precheck", module._local_gate_targets(text))


if __name__ == "__main__":
    unittest.main()
