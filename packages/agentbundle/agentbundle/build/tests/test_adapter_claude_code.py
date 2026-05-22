"""Tests for the Claude Code adapter (T2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.claude_code import project
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "specs" / "adapter-contract" / "contract.toml"


def _seed_pack(root: Path) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "skills" / "foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
        "---\ndescription: foo skill\n---\n# foo\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "skills" / "foo" / "extra.txt").write_text("nested\n", encoding="utf-8")

    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "bar.md").write_text(
        "---\nname: bar\n---\nagent body\n",
        encoding="utf-8",
    )

    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "baz.sh").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    (pack / ".apm" / "hooks" / "baz.py").write_text("print('hi')\n", encoding="utf-8")

    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring" / "baz.toml").write_text(
        '[hooks]\nbaz = "tools/hooks/baz.sh"\n',
        encoding="utf-8",
    )

    (pack / ".apm" / "commands").mkdir(parents=True)
    (pack / ".apm" / "commands" / "qux.md").write_text("# qux\n", encoding="utf-8")
    return pack


class ClaudeCodeAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_skill_projects_to_claude_skills_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".claude" / "skills" / "foo" / "SKILL.md").exists())
            self.assertTrue((out / ".claude" / "skills" / "foo" / "extra.txt").exists())

    def test_agent_projects_to_claude_agents_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            agent_path = out / ".claude" / "agents" / "bar.md"
            self.assertTrue(agent_path.exists())
            self.assertIn("name: bar", agent_path.read_text(encoding="utf-8"))

    def test_hook_body_sh_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / "tools" / "hooks" / "baz.sh").exists())

    def test_hook_body_py_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / "tools" / "hooks" / "baz.py").exists())

    def test_hook_wiring_merges_under_hooks_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            settings_path = out / ".claude" / "settings.local.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text(
                json.dumps({"otherKey": {"preserved": True}}),
                encoding="utf-8",
            )
            project(pack, self.contract, out)
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(data["hooks"], {"baz": "tools/hooks/baz.sh"})
            self.assertEqual(data["otherKey"], {"preserved": True})

    def test_command_projects_to_claude_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".claude" / "commands" / "qux.md").exists())

    def test_idempotent_direct_file_and_merge_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            first_agent = (out / ".claude" / "agents" / "bar.md").read_bytes()
            first_settings = (out / ".claude" / "settings.local.json").read_bytes()
            project(pack, self.contract, out)
            second_agent = (out / ".claude" / "agents" / "bar.md").read_bytes()
            second_settings = (out / ".claude" / "settings.local.json").read_bytes()
            self.assertEqual(first_agent, second_agent)
            self.assertEqual(first_settings, second_settings)


if __name__ == "__main__":
    unittest.main()
