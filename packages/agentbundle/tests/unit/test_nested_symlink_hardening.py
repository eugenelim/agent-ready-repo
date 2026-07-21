"""Nested-symlink-install-hardening regression guard.

A malicious pack shipping `.apm/skills/x/link -> /etc/passwd` must not
reproduce that symlink in any adapter's projection. cursor.py was hardened
first; this file pins the same protection for the four remaining adapters:
kiro, claude_code, codex, and copilot.

Each test: create a skill dir with a nested symlink → call the adapter's
`_project_direct_directory` (or `project_packs` for codex) → assert the
symlink is absent from the output.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


def _make_skill_source(tmp: Path) -> tuple[Path, Path]:
    """Return (source_dir, target_dir) with a nested symlink fixture.

    source_dir/
        my-skill/
            SKILL.md     ← regular file (must be copied)
            secret-link  → /etc/passwd (symlink — must be dropped)
    """
    source_dir = tmp / "source"
    source_skill = source_dir / "my-skill"
    source_skill.mkdir(parents=True)
    (source_skill / "SKILL.md").write_text("# My Skill\n", encoding="utf-8")
    (source_skill / "secret-link").symlink_to("/etc/passwd")

    target_dir = tmp / "target"
    target_dir.mkdir()
    return source_dir, target_dir


class TestKiroNestedSymlinkDropped(unittest.TestCase):
    def test_nested_symlink_not_reproduced(self) -> None:
        from agentbundle.build.adapters.kiro import _project_direct_directory

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            source_dir, target_dir = _make_skill_source(tmp)
            _project_direct_directory(source_dir, target_dir)

            skill_out = target_dir / "my-skill"
            self.assertTrue(skill_out.exists(), "skill dir must be projected")
            self.assertTrue((skill_out / "SKILL.md").exists(), "SKILL.md must be copied")
            self.assertFalse(
                (skill_out / "secret-link").exists(),
                "nested symlink must NOT be reproduced",
            )
            self.assertFalse(
                (skill_out / "secret-link").is_symlink(),
                "nested symlink must NOT appear as symlink in output",
            )


class TestClaudeCodeNestedSymlinkDropped(unittest.TestCase):
    def test_nested_symlink_not_reproduced(self) -> None:
        from agentbundle.build.adapters.claude_code import _project_direct_directory

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            source_dir, target_dir = _make_skill_source(tmp)
            _project_direct_directory(source_dir, target_dir)

            skill_out = target_dir / "my-skill"
            self.assertTrue(skill_out.exists())
            self.assertTrue((skill_out / "SKILL.md").exists())
            self.assertFalse((skill_out / "secret-link").exists())
            self.assertFalse((skill_out / "secret-link").is_symlink())


class TestCopilotNestedSymlinkDropped(unittest.TestCase):
    def test_nested_symlink_not_reproduced(self) -> None:
        from agentbundle.build.adapters.copilot import _project_direct_directory

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            source_dir, _ = _make_skill_source(tmp)

            output_root = tmp / "output"
            output_root.mkdir()
            rule = {"target-path": ".github/skills/"}
            _project_direct_directory(source_dir, output_root, rule, "skill")

            skill_out = output_root / ".github" / "skills" / "my-skill"
            self.assertTrue(skill_out.exists())
            self.assertTrue((skill_out / "SKILL.md").exists())
            self.assertFalse((skill_out / "secret-link").exists())
            self.assertFalse((skill_out / "secret-link").is_symlink())


class TestCodexNestedSymlinkDropped(unittest.TestCase):
    def test_nested_symlink_not_reproduced(self) -> None:
        from agentbundle.build.adapters.codex import project_packs

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)

            # Minimal pack with a nested symlink in a skill subdir.
            pack = tmp / "pack"
            skill_dir = pack / ".apm" / "skills" / "my-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# My Skill\n", encoding="utf-8")
            (skill_dir / "secret-link").symlink_to("/etc/passwd")

            output = tmp / "output"
            output.mkdir()

            contract: dict = {
                "adapter": {
                    "codex": {
                        "projection": [
                            {
                                "primitive": "skill",
                                "mode": "direct-directory",
                                "target-path": ".agents/skills/",
                            }
                        ]
                    }
                },
                "primitive": {
                    "skill": {"source-path": ".apm/skills/"}
                },
            }
            project_packs([pack], contract, output)

            skill_out = output / ".agents" / "skills" / "my-skill"
            self.assertTrue(skill_out.exists(), "skill dir must be projected")
            self.assertTrue((skill_out / "SKILL.md").exists(), "SKILL.md must be copied")
            self.assertFalse(
                (skill_out / "secret-link").exists(),
                "nested symlink must NOT be reproduced",
            )
            self.assertFalse(
                (skill_out / "secret-link").is_symlink(),
                "nested symlink must NOT appear as symlink in output",
            )


if __name__ == "__main__":
    unittest.main()
