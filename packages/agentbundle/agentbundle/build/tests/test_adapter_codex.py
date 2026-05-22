"""Tests for the Codex adapter (T5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.codex import project
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "specs" / "adapter-contract" / "contract.toml"


def _seed_pack(root: Path) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "skills" / "foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
        "---\ndescription: foo skill description\n---\n# foo\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "skills" / "alpha").mkdir(parents=True)
    (pack / ".apm" / "skills" / "alpha" / "SKILL.md").write_text(
        "---\ndescription: alpha skill description\n---\n# alpha\n",
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


class CodexAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_skill_description_appears_in_managed_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            text = (out / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- agent-skills:start -->", text)
            self.assertIn("<!-- agent-skills:end -->", text)
            self.assertIn("foo skill description", text)
            self.assertIn("alpha skill description", text)

    def test_outside_block_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            out.mkdir()
            preamble = "# Existing AGENTS.md\n\nKeep me.\n"
            (out / "AGENTS.md").write_text(preamble, encoding="utf-8")
            project(pack, self.contract, out)
            text = (out / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# Existing AGENTS.md", text)
            self.assertIn("Keep me.", text)

    def test_agent_hook_wiring_command_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertFalse(any(out.rglob("bar.md")))
            self.assertFalse(any(out.rglob("qux.md")))

    def test_hook_body_extensions_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / "tools" / "hooks" / "baz.sh").exists())
            self.assertTrue((out / "tools" / "hooks" / "baz.py").exists())

    def test_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            first = (out / "AGENTS.md").read_bytes()
            project(pack, self.contract, out)
            second = (out / "AGENTS.md").read_bytes()
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
