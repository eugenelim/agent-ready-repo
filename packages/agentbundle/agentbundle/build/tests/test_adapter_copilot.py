"""Tests for the Copilot adapter (T4)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.copilot import project
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_pack(root: Path) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "skills" / "foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
        "---\ndescription: foo skill\n---\nfoo body\n",
        encoding="utf-8",
    )

    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "bar.md").write_text("agent body\n", encoding="utf-8")

    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "baz.sh").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    (pack / ".apm" / "hooks" / "baz.py").write_text("print('hi')\n", encoding="utf-8")

    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring" / "baz.toml").write_text("[hooks]\n", encoding="utf-8")

    (pack / ".apm" / "commands").mkdir(parents=True)
    (pack / ".apm" / "commands" / "qux.md").write_text("# qux\n", encoding="utf-8")
    return pack


class CopilotAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_skill_projects_as_first_class_skill_md(self) -> None:
        # RFC-0052 / ADR-0040: copilot `skill` routes to the shared cohort home
        # `.agents/skills/<name>/SKILL.md` (joining codex, cursor, gemini).
        # Agents/hooks/hook-wiring remain under `.github/`.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            source_body = (pack / ".apm" / "skills" / "foo" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            output_path = out / ".agents" / "skills" / "foo" / "SKILL.md"
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), source_body)
            # No legacy instruction-file output.
            self.assertFalse((out / ".github" / "instructions").exists())

    def test_skill_orphan_sweep_bounded_to_skills_dir(self) -> None:
        # AC4: re-projection sweeps a stale skill dir, and the sweep is bounded
        # to the skill target — it never touches sibling `.github/agents/` or
        # `.github/hooks/` content.
        # RFC-0052: skill target is now `.agents/skills/` (shared cohort home).
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".agents" / "skills" / "foo").exists())
            agents_before = sorted((out / ".github" / "agents").iterdir())
            hooks_before = sorted((out / ".github" / "hooks").iterdir())
            # Rename the source skill; re-project. The old name is now orphaned.
            (pack / ".apm" / "skills" / "foo").rename(pack / ".apm" / "skills" / "renamed")
            project(pack, self.contract, out)
            self.assertFalse((out / ".agents" / "skills" / "foo").exists())
            self.assertTrue((out / ".agents" / "skills" / "renamed").exists())
            # Sibling agent/hook trees are untouched by the skill sweep.
            self.assertEqual(sorted((out / ".github" / "agents").iterdir()), agents_before)
            self.assertEqual(sorted((out / ".github" / "hooks").iterdir()), hooks_before)

    def test_agent_projects_agent_md(self) -> None:
        # v0.10 (copilot-full-parity): agent flips dropped → copilot-agent-md.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".github" / "agents" / "bar.agent.md").exists())

    def test_hook_body_lands_in_github_hooks(self) -> None:
        # v0.10: hook-body retargets tools/hooks/ → .github/hooks/ (repo-relpaths).
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".github" / "hooks" / "baz.sh").exists())
            self.assertTrue((out / ".github" / "hooks" / "baz.py").exists())
            # No legacy tools/hooks/ output remains for copilot.
            self.assertFalse((out / "tools" / "hooks").exists())

    def test_hook_wiring_projects_per_file_json_command_dropped(self) -> None:
        # v0.10: hook-wiring flips dropped → copilot-hooks-json (one <name>.json
        # per source file); command stays dropped.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".github" / "hooks" / "baz.json").exists())
            self.assertFalse(any(out.rglob("settings.local.json")))
            self.assertFalse(any(out.rglob("qux.md")))


if __name__ == "__main__":
    unittest.main()
