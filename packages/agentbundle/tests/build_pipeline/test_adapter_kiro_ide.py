"""Tests for the kiro-ide adapter (T1).

kiro-ide targets the Kiro VS Code-fork IDE. Agents project as .md with YAML
frontmatter (read by gray-matter), using IDE tool ids. kiro-ide-hook is
activated. No CLI-only keys in agent output.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.kiro_ide import project
from agentbundle.build.contract import load as load_contract

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml"


def _seed_agent_pack(root: Path, tools: str = "Read, Grep", model: str | None = None) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "agents").mkdir(parents=True)
    model_line = f"\nmodel: {model}" if model else ""
    (pack / ".apm" / "agents" / "bar.md").write_text(
        f"---\nname: bar\ntools: {tools}{model_line}\n---\nagent body\n",
        encoding="utf-8",
        newline="\n",
    )
    return pack


class KiroIdeAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_kiro_ide_agent_is_md(self) -> None:
        """kiro-ide projects agents as .md, not .json."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue(
                (out / ".kiro" / "agents" / "bar.md").exists(),
                "kiro-ide must project agent as .md",
            )
            self.assertFalse(
                (out / ".kiro" / "agents" / "bar.json").exists(),
                "kiro-ide must not project agent as .json",
            )

    def test_kiro_ide_no_cli_only_keys(self) -> None:
        """kiro-ide .md frontmatter must not carry CLI-only keys that would
        cause the IDE loader to silently drop the agent."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            for cli_only in ("hooks", "allowedTools", "toolsSettings", "mcpServers"):
                self.assertNotIn(cli_only, raw, f"kiro-ide agent .md must not contain {cli_only!r}")

    def test_kiro_ide_gets_skill_resources(self) -> None:
        """kiro-ide custom agents (and IDE subagents) must declare the
        skill-resources glob so they reach skills — IDE custom agents don't
        inherit the default agent's auto-discovery either."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            # Assert the exact emitted line: a flow sequence of DOUBLE-QUOTED
            # scalars. Quoting makes the `skill://` URIs / `**` globs
            # unambiguous YAML, guarding the IDE's fail-silent frontmatter
            # parser (kiro #8329). The bytes were confirmed to round-trip
            # through PyYAML to the two-element list during verification; this
            # gate is exact-string (the build tree is stdlib-only — no yaml).
            self.assertIn(
                'resources: ["skill://.kiro/skills/**/SKILL.md", '
                '"skill://~/.kiro/skills/**/SKILL.md"]',
                raw,
            )

    def test_kiro_ide_resources_author_override_wins(self) -> None:
        """An IDE agent that declares its own `resources` keeps it."""
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
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            self.assertIn("file://README.md", raw)
            self.assertNotIn("skill://", raw)

    def test_kiro_ide_empty_resources_suppress_skill_injection(self) -> None:
        """An explicit empty list projects a no-resource IDE agent."""
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
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("resources:", raw)
            self.assertNotIn("skill://", raw)

    def test_kiro_ide_empty_skills_suppress_skill_injection(self) -> None:
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
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("resources:", raw)
            self.assertNotIn("skill://", raw)
            self.assertNotIn("skills", raw)

    def test_kiro_ide_drops_unmapped_claude_agent_fields(self) -> None:
        """An unmapped Claude Code field must not reach the IDE agent.

        Asserts the exact emitted key set rather than absent substrings, so an
        over-eager `_IDE_AGENT_FIELDS` that dropped a required field fails here
        too. The fixture includes the CLI-only keys this module's docstring
        warns silently break the IDE loader.
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
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(
                encoding="utf-8"
            )
            lines = raw.splitlines()
            end = lines.index("---", 1)
            emitted = sorted(
                line.split(":")[0]
                for line in lines[1:end]
                if line and not line[0].isspace()
            )
            self.assertEqual(emitted, ["name", "resources", "tools"])
            # The stderr line is the pack author's only signal that a declared
            # field did not reach the consumer.
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
                    f"dropping kiro-ide agent field {dropped!r}", log, dropped
                )

    def test_kiro_ide_mapping_targets_are_all_emittable(self) -> None:
        """Every rename target must survive `_restrict_agent_fields`.

        The projector bounds its emitted field set in Python while the rename
        rules live in the contract; a target outside that set makes the contract
        rule a silent no-op. Bind the two so the contract cannot drift.
        """
        from agentbundle.build.adapters.kiro import _IDE_AGENT_FIELDS

        mapping = self.contract["frontmatter-mapping"][
            "kiro-ide-agent-frontmatter-v0.9"
        ]
        for source_key, rule in mapping.items():
            target = rule.get("rename", source_key)
            self.assertIn(
                target,
                _IDE_AGENT_FIELDS,
                f"contract maps {source_key!r} -> {target!r}, which "
                f"_IDE_AGENT_FIELDS drops",
            )

    def test_kiro_ide_tools_use_ide_ids(self) -> None:
        """kiro-ide uses IDE tool ids (read_file, grep_search) not CLI short-names."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path, tools="Read, Grep, Glob, Bash")
            out = tmp_path / "out"
            project(pack, self.contract, out)
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            self.assertIn("read_file", raw)
            self.assertIn("grep_search", raw)
            self.assertIn("file_search", raw)
            self.assertIn("execute_bash", raw)
            # Not CLI short-names
            self.assertNotIn("shell", raw.split("---")[1])  # only check frontmatter

    def test_kiro_ide_md_has_frontmatter_and_body(self) -> None:
        """Output .md file has --- fenced frontmatter and the original body."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            text = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), "must start with --- frontmatter fence")
            self.assertIn("\n---\n", text, "must have closing --- fence")
            self.assertIn("agent body", text, "original body must be preserved")

    def test_kiro_ide_model_translates_to_kiro_id(self) -> None:
        """model: opus translates to claude-opus-4.6 (same mapping as kiro-cli)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_agent_pack(tmp_path, model="opus")
            out = tmp_path / "out"
            project(pack, self.contract, out)
            text = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            self.assertIn("claude-opus-4.6", text)
            self.assertNotIn(": opus", text)

    def test_frontmatter_table_renamed(self) -> None:
        """The mapping table is kiro-ide-agent-frontmatter-v0.9 (renamed from
        kiro-agent-frontmatter-v0.9 in T1). Old name must not exist."""
        mapping = self.contract.get("frontmatter-mapping", {})
        self.assertIn(
            "kiro-ide-agent-frontmatter-v0.9",
            mapping,
            "kiro-ide-agent-frontmatter-v0.9 must be in contract",
        )
        self.assertNotIn(
            "kiro-agent-frontmatter-v0.9",
            mapping,
            "old name kiro-agent-frontmatter-v0.9 must not exist after T1 rename",
        )

    def test_kiro_ide_hook_declared_in_contract(self) -> None:
        """[adapter.kiro-ide.projections.kiro-ide-hook] is declared in contract."""
        kiro_ide_block = self.contract["adapter"]["kiro-ide"]
        projections = kiro_ide_block.get("projections", {})
        self.assertIn(
            "kiro-ide-hook",
            projections,
            "kiro-ide adapter must declare kiro-ide-hook in projections",
        )
        rule = projections["kiro-ide-hook"]
        self.assertEqual(rule.get("mode"), "direct-file")
        target = rule.get("target", {})
        target_repo = target.get("repo") if isinstance(target, dict) else target
        self.assertIsNotNone(target_repo)
        self.assertIn("<pack>--<name>", target_repo, "flat-with-prefix path must use -- separator")
        self.assertIn(".kiro.hook", target_repo)

    def test_contract_version_is_0_9(self) -> None:
        """Contract version is 0.18 (Claude-plugin hook parity,
        atop kiro-cli-agent-skill-resources' 0.15 and enriched-pack-manifest's 0.14).
        Name preserved to keep the diff small."""
        self.assertEqual(
            self.contract["contract"]["version"],
            "0.18",
            "adapter.toml [contract] version must be '0.18' after Claude-plugin hook parity",
        )

    def test_kiro_ide_hook_projects_with_flat_prefix_path(self) -> None:
        """kiro-ide-hook files project to .kiro/hooks/<pack>--<name>.kiro.hook
        (flat-with-prefix, confirmed by Q6 probe no×yes 2026-06-01)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "my-pack"
            hooks_dir = pack / ".apm" / "kiro-ide-hooks"
            hooks_dir.mkdir(parents=True)
            hook_body = {
                "name": "on-save",
                "version": "1",
                "when": {"type": "fileEdited", "patterns": ["**/*.py"]},
                "then": {"type": "askAgent", "prompt": "Run lint."},
            }
            (hooks_dir / "on-save.kiro.hook").write_text(
                json.dumps(hook_body), encoding="utf-8", newline="\n"
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            # Flat path: .kiro/hooks/my-pack--on-save.kiro.hook
            expected = out / ".kiro" / "hooks" / "my-pack--on-save.kiro.hook"
            self.assertTrue(expected.exists(), f"expected hook at flat path {expected}")
            # No subdirectory
            subdir = out / ".kiro" / "hooks" / "my-pack"
            self.assertFalse(subdir.exists(), "must NOT create a subdirectory for the pack")


if __name__ == "__main__":
    unittest.main()
