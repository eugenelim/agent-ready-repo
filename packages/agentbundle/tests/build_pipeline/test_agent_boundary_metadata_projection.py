"""Construction checks for source-only agent boundary metadata."""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import tomllib
import unittest
from pathlib import Path

from agentbundle.build import self_host
from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.build.main import CONTRACT_PATH

_AGENT = """---
name: read-only
description: Read-only projection fixture.
tools: Read, Grep, Glob
skills: []
metadata:
  type: agent
  boundaries: [filesystem_read_untrusted]
---

# Read-only
"""
_CORE_PACK = Path(__file__).resolve().parents[4] / "packs" / "core"


def _seed_pack(root: Path) -> Path:
    """Create a minimal pack with an agent plus Claude direct-file neighbors."""
    pack = root / "pack"
    agents = pack / ".apm" / "agents"
    commands = pack / ".apm" / "commands"
    hooks = pack / ".apm" / "hooks"
    agents.mkdir(parents=True)
    commands.mkdir(parents=True)
    hooks.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "pack"\nversion = "0.1.0"\n',
        encoding="utf-8",
        newline="\n",
    )
    (agents / "read-only.md").write_text(_AGENT, encoding="utf-8", newline="\n")
    (commands / "command.md").write_text(
        "---\nmetadata:\n  retained: true\n---\n# Command\n",
        encoding="utf-8",
        newline="\n",
    )
    (hooks / "hook.sh").write_text(
        "#!/bin/sh\n# metadata: retained\n",
        encoding="utf-8",
        newline="\n",
    )
    return pack


class AgentBoundaryMetadataProjectionTests(unittest.TestCase):
    """Each adapter realizes the read-only source contract natively."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_claude_code_strips_agent_metadata_only(self) -> None:
        """Claude's direct-file agent projection excludes source-only metadata."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            output = temporary / "output"
            ADAPTERS["claude-code"](_seed_pack(temporary), self.contract, output)
            agent = (output / ".claude" / "agents" / "read-only.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("metadata:", agent)
            self.assertIn("tools: Read, Grep, Glob", agent)
            self.assertIn(
                "metadata:",
                (output / ".claude" / "commands" / "command.md").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertIn(
                "metadata: retained",
                (output / "tools" / "hooks" / "hook.sh").read_text(encoding="utf-8"),
            )

    def test_claude_code_strip_preserves_agent_file_mode(self) -> None:
        """The content transform retains the source agent's file mode."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            pack = _seed_pack(temporary)
            source = pack / ".apm" / "agents" / "read-only.md"
            source.chmod(0o744)
            output = temporary / "output"
            ADAPTERS["claude-code"](pack, self.contract, output)
            rendered = output / ".claude" / "agents" / "read-only.md"
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(rendered.stat().st_mode), 0o744)
                rendered.chmod(0o600)
                ADAPTERS["claude-code"](
                    pack,
                    self.contract,
                    output,
                    preserve_existing_metadata=True,
                )
                self.assertEqual(stat.S_IMODE(rendered.stat().st_mode), 0o600)

    def test_self_host_routes_agents_through_the_metadata_strip(self) -> None:
        """Self-host delegates agent projection to the Claude adapter seam."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            _seed_pack(temporary)
            output = temporary / "output"
            original_packs = self_host.SELF_HOST_PACKS
            self_host.SELF_HOST_PACKS = ("pack",)
            try:
                self_host._project_all_adapters(output, temporary, self.contract)
            finally:
                self_host.SELF_HOST_PACKS = original_packs
            rendered = (output / ".claude" / "agents" / "read-only.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("metadata:", rendered)

    def test_core_shaping_reviewer_projection_strips_source_metadata(self) -> None:
        """The real Core reviewer excludes source-only metadata when projected."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "output"
            ADAPTERS["claude-code"](_CORE_PACK, self.contract, output)
            rendered = (output / ".claude" / "agents" / "shaping-reviewer.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("metadata:", rendered)

    def test_all_adapters_preserve_the_native_read_only_restriction(self) -> None:
        """Every supported adapter projects the synthetic read-only agent safely."""
        for adapter_name in (
            "claude-code",
            "codex",
            "copilot",
            "cursor",
            "gemini",
            "kiro-ide",
            "kiro-cli",
        ):
            with self.subTest(adapter=adapter_name), tempfile.TemporaryDirectory() as temporary_directory:
                temporary = Path(temporary_directory)
                output = temporary / "output"
                ADAPTERS[adapter_name](_seed_pack(temporary), self.contract, output)
                if adapter_name == "claude-code":
                    rendered = (output / ".claude" / "agents" / "read-only.md").read_text(
                        encoding="utf-8"
                    )
                    tools_match = re.search(r"^tools:\s*(.+)$", rendered, re.MULTILINE)
                    self.assertIsNotNone(tools_match)
                    assert tools_match is not None
                    self.assertEqual(tools_match.group(1), "Read, Grep, Glob")
                elif adapter_name == "codex":
                    rendered = tomllib.loads(
                        (output / ".codex" / "agents" / "read-only.toml").read_text(
                            encoding="utf-8"
                        )
                    )
                    self.assertEqual(rendered["sandbox_mode"], "read-only")
                    self.assertEqual(rendered["web_search"], "disabled")
                    self.assertTrue(rendered["features"]["shell_tool"])
                    self.assertNotIn("mcp_servers", rendered)
                    self.assertNotIn("skills", rendered)
                    self.assertFalse(
                        any("dispatch" in key for key in rendered),
                        "Codex projection must not emit a dispatch key",
                    )
                elif adapter_name == "copilot":
                    rendered = (output / ".github" / "agents" / "read-only.agent.md").read_text(
                        encoding="utf-8"
                    )
                    tools_match = re.search(r"^tools:\s*(.+)$", rendered, re.MULTILINE)
                    self.assertIsNotNone(tools_match)
                    assert tools_match is not None
                    self.assertEqual(tools_match.group(1), "Read, Grep, Glob")
                elif adapter_name == "cursor":
                    rendered = (output / ".cursor" / "agents" / "read-only.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("readonly: true", rendered)
                elif adapter_name == "gemini":
                    rendered = (output / ".gemini" / "agents" / "read-only.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("tools: [read_file, grep_search, glob]", rendered)
                elif adapter_name == "kiro-ide":
                    rendered = (output / ".kiro" / "agents" / "read-only.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("tools: [read_file, grep_search, file_search]", rendered)
                    self.assertNotIn("skill://", rendered)
                else:
                    rendered = json.loads(
                        (output / ".kiro" / "agents" / "read-only.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    self.assertEqual(rendered["tools"], ["read", "grep", "glob"])
                    self.assertNotIn("resources", rendered)
