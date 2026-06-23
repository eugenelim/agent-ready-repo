"""Tests for the kiro-ide adapter (T1 — RFC-0022).

kiro-ide targets the Kiro VS Code-fork IDE. Agents project as .md with YAML
frontmatter (read by gray-matter), using IDE tool ids. kiro-ide-hook is
activated. No CLI-only keys in agent output.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters.kiro_ide import project
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_agent_pack(root: Path, tools: str = "Read, Grep", model: str | None = None) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "agents").mkdir(parents=True)
    model_line = f"\nmodel: {model}" if model else ""
    (pack / ".apm" / "agents" / "bar.md").write_text(
        f"---\nname: bar\ntools: {tools}{model_line}\n---\nagent body\n",
        encoding="utf-8",
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
        inherit the default agent's auto-discovery either (RFC-0022 E4)."""
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
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            raw = (out / ".kiro" / "agents" / "bar.md").read_text(encoding="utf-8")
            self.assertIn("file://README.md", raw)
            self.assertNotIn("skill://", raw)

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
        """Contract version is 0.16 (docs/specs/consolidated-pack-layout,
        atop kiro-cli-agent-skill-resources' 0.15 and enriched-pack-manifest's 0.14).
        Name preserved to keep the diff small."""
        self.assertEqual(
            self.contract["contract"]["version"],
            "0.16",
            "adapter.toml [contract] version must be '0.16' after consolidated-pack-layout",
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
                json.dumps(hook_body), encoding="utf-8"
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
