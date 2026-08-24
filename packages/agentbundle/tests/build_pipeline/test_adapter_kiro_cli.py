"""Tests for the kiro-cli adapter (T3).

kiro-cli targets the `kiro` terminal binary. It projects agents as
`.json` with CLI short-name tool tokens (read, grep, glob, write,
shell, web_fetch, web_search) and retains hook-wiring via
merge-into-agent-json. kiro-ide-hook is dropped.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.kiro_cli import project
from agentbundle.build.contract import load as load_contract

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml"


def _seed_agent_pack(root: Path, tools: str = "Read, Grep, Glob, Bash") -> Path:
    pack = root / "pack"
    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "bar.md").write_text(
        f"---\nname: bar\ntools: {tools}\n---\nagent body\n",
        encoding="utf-8",
        newline="\n",
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
        default agent's auto-discovery (E4; kiro #6887/#6888)."""
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
                newline="\n",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(encoding="utf-8")
            )
            self.assertEqual(data.get("resources"), ["file://README.md"])

    def test_cli_agent_empty_resources_suppress_skill_injection(self) -> None:
        """An explicit empty list projects a no-resource CLI agent."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\nresources: []\n---\nbody\n",
                encoding="utf-8",
                newline="\n",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertNotIn("resources", data)

    def test_cli_empty_skills_suppress_skill_injection(self) -> None:
        """Claude Code's `skills: []` is the portable no-skill opt-out."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\nskills: []\n---\nbody\n",
                encoding="utf-8",
                newline="\n",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertNotIn("resources", data)
            # `skills` is Claude Code frontmatter Kiro cannot read.
            self.assertNotIn("skills", data)

    def test_cli_non_empty_skills_fails_loudly(self) -> None:
        """A non-empty `skills` list needs skill:// templating we don't have.

        Projecting it as a bare name would emit an unresolvable Kiro resource,
        so the build fails instead of shipping a silently broken agent.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\nskills: [work-loop]\n---\nbody\n",
                encoding="utf-8",
                newline="\n",
            )
            out = tmp_path / "out"
            with self.assertRaises(ValueError) as caught:
                project(pack, self.contract, out)
            self.assertIn("skill://", str(caught.exception))

    def test_cli_drops_unmapped_claude_agent_fields(self) -> None:
        """Kiro rewrites source frontmatter rather than allowlisting it, so an
        unmapped Claude Code field would otherwise reach the consumer verbatim.

        `hooks` is the sharp case: an IDE-only key in CLI agent JSON makes the
        loader silently drop the agent.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\ntools: Read\nmemory: project\n"
                "permissionMode: plan\nmaxTurns: 12\nbackground: true\n"
                "color: blue\nisolation: worktree\neffort: high\n"
                "disallowedTools: Bash\ninitialPrompt: go\nhooks: {}\n"
                "allowedTools: [read]\ntoolsSettings: {}\nmcpServers: {}\n"
                "---\nbody\n",
                encoding="utf-8",
                newline="\n",
            )
            out = tmp_path / "out"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                project(pack, self.contract, out)
            data = json.loads(
                (out / ".kiro" / "agents" / "bar.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                sorted(data),
                ["name", "prompt", "resources", "tools"],
            )
            # The stderr line is the pack author's only signal that a declared
            # field did not reach the consumer; silence would make an
            # over-eager field set indistinguishable from a correct one.
            log = stderr.getvalue()
            for dropped in (
                "memory",
                "permissionMode",
                "maxTurns",
                "background",
                "color",
                "isolation",
                "effort",
                "disallowedTools",
                "initialPrompt",
                "hooks",
                "allowedTools",
                "toolsSettings",
                "mcpServers",
            ):
                self.assertIn(
                    f"dropping kiro-cli agent field {dropped!r}", log, dropped
                )

    def test_cli_mapping_targets_are_all_emittable(self) -> None:
        """Every rename target must survive `_restrict_agent_fields`.

        The projector bounds its emitted field set in Python while the rename
        rules live in the contract. A target that is not a member of that set
        makes the contract rule a silent no-op whose only signal is a build-log
        line, so bind the two here.
        """
        from agentbundle.build.adapters.kiro import _CLI_AGENT_FIELDS

        mapping = self.contract["frontmatter-mapping"][
            "kiro-cli-agent-frontmatter-v1.0"
        ]
        for source_key, rule in mapping.items():
            target = rule.get("rename", source_key)
            self.assertIn(
                target,
                _CLI_AGENT_FIELDS,
                f"contract maps {source_key!r} -> {target!r}, which "
                f"_CLI_AGENT_FIELDS drops",
            )

    def test_cli_no_ide_hook_field(self) -> None:
        """kiro-cli projected agent JSON must not contain ide-event-vocabulary
        or kiro-ide-hook sections — those are IDE-only fields that cause the
        IDE loader to silently drop agents.

        Seeded with a fixture that actually declares the IDE-only keys: with
        the default fixture these assertions could not fail.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\ntools: Read, Grep\nhooks: {}\n"
                "allowedTools: [read]\ntoolsSettings: {}\nmcpServers: {}\n"
                "ide-event-vocabulary: [fileEdited]\n"
                "---\nagent body\n",
                encoding="utf-8",
                newline="\n",
            )
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
