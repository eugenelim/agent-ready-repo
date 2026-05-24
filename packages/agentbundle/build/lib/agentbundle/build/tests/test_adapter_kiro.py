"""Tests for the Kiro adapter (T3)."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from agentbundle.build.adapters.kiro import project
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_pack(root: Path) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "skills" / "foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "foo" / "SKILL.md").write_text(
        "# foo skill\n",
        encoding="utf-8",
    )

    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "bar.md").write_text(
        "---\nname: bar\ntools: Read\n---\nagent body\n",
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


class KiroAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_skill_projects_to_kiro_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / ".kiro" / "skills" / "foo" / "SKILL.md").exists())

    def test_agent_projects_as_json_per_kiro_schema(self) -> None:
        """RFC-0005 / T7: Kiro agents are JSON files per the documented
        Kiro schema (https://kiro.dev/docs/cli/custom-agents/configuration-reference/),
        not markdown-with-frontmatter as v0.2 used to project. The
        `kiro-agent-frontmatter-v0.9` mapping table is reinterpreted as
        *markdown-frontmatter → JSON-field* — the rename / to-list
        normalize semantics carry over to JSON emission."""
        import json

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            # File is .json, not .md.
            agent_json_path = out / ".kiro" / "agents" / "bar.json"
            self.assertTrue(agent_json_path.exists(), "agent projected as .md instead of .json")
            self.assertFalse(
                (out / ".kiro" / "agents" / "bar.md").exists(),
                "stale .md projection left behind",
            )
            data = json.loads(agent_json_path.read_text(encoding="utf-8"))
            # `tools: Read` source normalises to a list per the mapping
            # table's `normalize: to-list` rule.
            self.assertEqual(data["tools"], ["Read"])
            # `name` from filename (or frontmatter); body becomes prompt.
            self.assertEqual(data["name"], "bar")
            self.assertEqual(data.get("prompt", "").strip(), "agent body")

    def test_hook_wiring_array_entry_removed(self) -> None:
        """AC2: the legacy `degraded-info-log` kiro hook-wiring entry is gone."""
        kiro_array_primitives = {
            entry["primitive"]
            for entry in self.contract["adapter"]["kiro"].get("projection", [])
        }
        self.assertNotIn(
            "hook-wiring",
            kiro_array_primitives,
            "legacy kiro hook-wiring projection array entry still present",
        )

    def test_hook_wiring_no_info_log_emitted(self) -> None:
        """No info-log fires for kiro hook-wiring under v0.3 (the legacy
        `degraded-info-log` array entry that produced it has been removed).
        The v0.3 `merge-into-agent-json` projection is wired up in T5/T6 —
        this test pins the regression of the prior runtime behaviour."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            buf = io.StringIO()
            with redirect_stderr(buf):
                project(pack, self.contract, out)
            self.assertNotIn(
                "hook-wiring",
                buf.getvalue(),
                "kiro adapter emitted a hook-wiring info-log after AC2 removal",
            )

    def test_hook_body_extensions_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / "tools" / "hooks" / "baz.sh").exists())
            self.assertTrue((out / "tools" / "hooks" / "baz.py").exists())

    def test_command_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            # No command output.
            self.assertFalse(any(out.rglob("commands")))


if __name__ == "__main__":
    unittest.main()
