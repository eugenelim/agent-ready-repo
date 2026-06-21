"""Tests for the kiro-cli adapter (T3 — RFC-0022).

kiro-cli targets the `kiro` terminal binary. It projects agents as
`.json` with CLI short-name tool tokens (read, grep, glob, write,
shell, web_fetch, web_search) and retains hook-wiring via
merge-into-agent-json. kiro-ide-hook is dropped.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.kiro_cli import project
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_agent_pack(root: Path, tools: str = "Read, Grep, Glob, Bash") -> Path:
    pack = root / "pack"
    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "bar.md").write_text(
        f"---\nname: bar\ntools: {tools}\n---\nagent body\n",
        encoding="utf-8",
    )
    return pack


class KiroCliAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_cli_agent_is_json(self) -> None:
        """kiro-cli projects agents as .json, not .md."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue(
                (out / ".kiro" / "agents" / "bar.json").exists(),
                "kiro-cli must project agent as .json",
            )
            self.assertFalse(
                (out / ".kiro" / "agents" / "bar.md").exists(),
                "kiro-cli must not project agent as .md",
            )

    def test_cli_tool_short_names(self) -> None:
        """kiro-cli uses CLI short-name tool tokens per the
        kiro-cli-agent-frontmatter-v1.0 mapping table:
        Read→read, Grep→grep, Glob→glob, Bash→shell,
        WebFetch→web_fetch, WebSearch→web_search."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(
                tmp_path,
                tools="Read, Grep, Glob, Bash, WebFetch, WebSearch",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(encoding="utf-8")
            )
            tools = data.get("tools", [])
            self.assertIn("read", tools)
            self.assertIn("grep", tools)
            self.assertIn("glob", tools)
            self.assertIn("shell", tools)
            self.assertIn("web_fetch", tools)
            self.assertIn("web_search", tools)
            # Verify these are short-names, not the IDE ids
            self.assertNotIn("read_file", tools)
            self.assertNotIn("grep_search", tools)
            self.assertNotIn("execute_bash", tools)

    def test_cli_agent_gets_skill_resources(self) -> None:
        """kiro-cli custom agents must declare the skill-resources glob so
        they reach the bundle's skills — Kiro custom agents don't inherit the
        default agent's auto-discovery (RFC-0022 E4; kiro #6887/#6888)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                data.get("resources"),
                [
                    "skill://.kiro/skills/**/SKILL.md",
                    "skill://~/.kiro/skills/**/SKILL.md",
                ],
                "kiro-cli agent JSON must inject both repo- and user-scope skill globs",
            )

    def test_cli_agent_resources_author_override_wins(self) -> None:
        """An agent that declares its own `resources` keeps it — the default
        does not clobber an author-supplied value."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\nresources: [file://README.md]\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(encoding="utf-8")
            )
            self.assertEqual(data.get("resources"), ["file://README.md"])

    def test_cli_no_ide_hook_field(self) -> None:
        """kiro-cli projected agent JSON must not contain ide-event-vocabulary
        or kiro-ide-hook sections — those are IDE-only fields that cause the
        IDE loader to silently drop agents."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            raw = (out / ".kiro" / "agents" / "bar.json").read_text(encoding="utf-8")
            self.assertNotIn("ide-event-vocabulary", raw)
            self.assertNotIn("kiro-ide-hook", raw)
            data = json.loads(raw)
            self.assertNotIn("hooks", data, "kiro-cli agent JSON must not carry hooks key")
            self.assertNotIn("allowedTools", data)
            self.assertNotIn("toolsSettings", data)
            self.assertNotIn("mcpServers", data)


if __name__ == "__main__":
    unittest.main()
