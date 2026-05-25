"""Tests for the Claude Code adapter (T2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.claude_code import project, project_packs
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


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


def _seed_minimal_pack(root: Path, name: str, skill_name: str, body: str) -> Path:
    """Pack with a single skill at .apm/skills/<skill_name>/SKILL.md."""
    pack = root / name
    skill_dir = pack / ".apm" / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return pack


class ProjectPacksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_project_packs_iterates_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_minimal_pack(tmp_path, "pack-a", "skill-a", "# a\n")
            pack_b = _seed_minimal_pack(tmp_path, "pack-b", "skill-b", "# b\n")
            out = tmp_path / "out"

            project_packs([pack_a, pack_b], self.contract, out)

            self.assertTrue((out / ".claude" / "skills" / "skill-a" / "SKILL.md").is_file())
            self.assertTrue((out / ".claude" / "skills" / "skill-b" / "SKILL.md").is_file())

    def test_single_pack_project_delegates_to_project_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_minimal_pack(tmp_path, "pack", "skill-x", "# x\n")
            out_a = tmp_path / "out-a"
            out_b = tmp_path / "out-b"

            project(pack, self.contract, out_a)
            project_packs([pack], self.contract, out_b)

            self.assertEqual(
                (out_a / ".claude" / "skills" / "skill-x" / "SKILL.md").read_bytes(),
                (out_b / ".claude" / "skills" / "skill-x" / "SKILL.md").read_bytes(),
            )

    def test_same_name_last_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_minimal_pack(
                tmp_path, "pack-a", "same-name", "# pack-a\nPACK_A_SENTINEL\n",
            )
            pack_b = _seed_minimal_pack(
                tmp_path, "pack-b", "same-name", "# pack-b\nPACK_B_SENTINEL\n",
            )
            out = tmp_path / "out"

            project_packs([pack_a, pack_b], self.contract, out)
            body = (out / ".claude" / "skills" / "same-name" / "SKILL.md").read_text(
                encoding="utf-8",
            )
            self.assertIn("PACK_B_SENTINEL", body)
            self.assertNotIn("PACK_A_SENTINEL", body)

    def test_same_name_last_wins_reversed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_minimal_pack(
                tmp_path, "pack-a", "same-name", "# pack-a\nPACK_A_SENTINEL\n",
            )
            pack_b = _seed_minimal_pack(
                tmp_path, "pack-b", "same-name", "# pack-b\nPACK_B_SENTINEL\n",
            )
            out = tmp_path / "out"

            project_packs([pack_b, pack_a], self.contract, out)
            body = (out / ".claude" / "skills" / "same-name" / "SKILL.md").read_text(
                encoding="utf-8",
            )
            self.assertIn("PACK_A_SENTINEL", body)
            self.assertNotIn("PACK_B_SENTINEL", body)


def _seed_named_skills_pack(root: Path, pack_name: str, skill_names: list[str]) -> Path:
    pack = root / pack_name
    for skill_name in skill_names:
        skill_dir = pack / ".apm" / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"# {skill_name}\nfrom {pack_name}\n",
            encoding="utf-8",
        )
    return pack


class TestClaudeCodeOrphanSweep(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_two_stage_shrink(self) -> None:
        # AC18: project {a, b, c} then {a, c} into the same output.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            three = _seed_named_skills_pack(tmp_path, "three-skill", ["a", "b", "c"])
            shrink = _seed_named_skills_pack(tmp_path, "two-skill-shrink", ["a", "c"])
            out = tmp_path / "out"

            project_packs([three], self.contract, out)
            self.assertTrue((out / ".claude" / "skills" / "b").is_dir())

            project_packs([shrink], self.contract, out)
            children = {p.name for p in (out / ".claude" / "skills").iterdir()}
            self.assertEqual(children, {"a", "c"})

    def test_two_pack_union(self) -> None:
        # AC20 — claude-code case.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_named_skills_pack(tmp_path, "pack-a", ["a", "b"])
            pack_b = _seed_named_skills_pack(tmp_path, "pack-b", ["b", "c"])
            out = tmp_path / "out"

            project_packs([pack_a, pack_b], self.contract, out)
            children = {p.name for p in (out / ".claude" / "skills").iterdir()}
            self.assertEqual(children, {"a", "b", "c"})

            project_packs([pack_a], self.contract, out)
            children = {p.name for p in (out / ".claude" / "skills").iterdir()}
            self.assertEqual(children, {"a", "b"})


if __name__ == "__main__":
    unittest.main()
