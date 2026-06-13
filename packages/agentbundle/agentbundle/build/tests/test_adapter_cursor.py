"""Tests for the cursor adapter (RFC-0026 / ADR-0015 / cursor-full-parity).

Cursor is a full-parity native adapter projecting all five catalogue
primitives to `.cursor/*`. Agents project as `.md` with the source `tools`
allowlist dropped and a `readonly` flag derived for non-mutating agents.
hook-wiring aggregates into one `.cursor/hooks.json` with an event remap and a
`version` key. Commands are first-class. No new projection mode; no schema
change. Distribution-only (not in SELF_HOST_ADAPTERS).
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters import cursor, ADAPTERS, registry
from agentbundle.build.contract import load as load_contract
from agentbundle.scope import contract_version_at_least

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_agent(pack: Path, name: str, *, tools: str | None, model: str | None = None) -> None:
    (pack / ".apm" / "agents").mkdir(parents=True, exist_ok=True)
    lines = ["---", f"name: {name}"]
    if tools is not None:
        lines.append(f"tools: {tools}")
    if model is not None:
        lines.append(f"model: {model}")
    lines.append("---")
    lines.append("agent body")
    (pack / ".apm" / "agents" / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _seed_session_start_wiring(pack: Path) -> None:
    (pack / ".apm" / "hook-wiring").mkdir(parents=True, exist_ok=True)
    (pack / ".apm" / "hook-wiring" / "session-start.toml").write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [\n  { type = "command", command = "python tools/hooks/session-start.py" },\n]\n',
        encoding="utf-8",
    )


class CursorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_contract_version_is_0_11(self) -> None:
        """AC1 — contract bumped to 0.11 by cursor-full-parity; subsequently
        0.12 (copilot-skills-and-web), 0.13 (docs/specs/gemini-full-parity),
        then 0.14 (docs/specs/enriched-pack-manifest).
        Name preserved to keep the diff small."""
        self.assertEqual(self.contract["contract"]["version"], "0.14")

    def test_cursor_block_projects_five_primitives(self) -> None:
        """AC2 — the five standard primitives are in the projection array."""
        block = self.contract["adapter"]["cursor"]
        prims = {e["primitive"]: e for e in block["projection"]}
        self.assertEqual(
            set(prims),
            {"skill", "agent", "hook-body", "hook-wiring", "command"},
        )
        self.assertEqual(prims["skill"]["mode"], "direct-directory")
        self.assertEqual(prims["skill"]["target-path"], ".cursor/skills/")
        self.assertEqual(prims["agent"]["mode"], "direct-file")
        self.assertEqual(prims["agent"]["target-path"], ".cursor/agents/")
        self.assertEqual(
            prims["agent"]["frontmatter-mapping"], "cursor-agent-frontmatter-v0.11"
        )
        self.assertEqual(prims["hook-body"]["mode"], "direct-file")
        self.assertEqual(prims["hook-body"]["target-path"], ".cursor/hooks/")
        self.assertEqual(prims["hook-wiring"]["mode"], "merge-json")
        self.assertEqual(prims["hook-wiring"]["target-path"], ".cursor/hooks.json")
        self.assertEqual(prims["hook-wiring"]["managed-key"], "hooks")
        self.assertEqual(prims["command"]["mode"], "direct-file")
        self.assertEqual(prims["command"]["target-path"], ".cursor/commands/")

    def test_kiro_ide_hook_dropped_in_table_form(self) -> None:
        """AC2 — kiro-ide-hook is dropped, in the table form (not the array)."""
        block = self.contract["adapter"]["cursor"]
        array_prims = {e["primitive"] for e in block["projection"]}
        self.assertNotIn("kiro-ide-hook", array_prims)
        self.assertEqual(block["projections"]["kiro-ide-hook"]["mode"], "dropped")

    def test_hook_event_map_keys_on_pascalcase(self) -> None:
        """AC10 — the contract hook-event-map keys on Claude PascalCase."""
        block = self.contract["adapter"]["cursor"]
        hw = next(e for e in block["projection"] if e["primitive"] == "hook-wiring")
        self.assertEqual(
            hw["hook-event-map"],
            {
                "SessionStart": "sessionStart",
                "UserPromptSubmit": "beforeSubmitPrompt",
                "PreToolUse": "preToolUse",
                "PostToolUse": "postToolUse",
                "Stop": "stop",
            },
        )

    def test_scope_same_prefix_both_scopes(self) -> None:
        """AC3 — `.cursor/` prefix is identical at both scopes (no rewrite)."""
        scope = self.contract["adapter"]["cursor"]["scope"]
        self.assertEqual(scope["repo"], ".")
        self.assertEqual(scope["user"], "~")
        self.assertEqual(scope["allowed-prefixes"]["repo"], [".cursor/", ".agentbundle/"])
        self.assertEqual(
            scope["allowed-prefixes"]["repo"], scope["allowed-prefixes"]["user"]
        )

    def test_frontmatter_mapping_present_no_tools(self) -> None:
        """AC4 — cursor-agent-frontmatter-v0.11 renames name/description/model,
        no `tools` rule (tools is dropped by the adapter)."""
        mapping = self.contract["frontmatter-mapping"]["cursor-agent-frontmatter-v0.11"]
        self.assertEqual(mapping["name"]["rename"], "name")
        self.assertEqual(mapping["description"]["rename"], "description")
        self.assertEqual(mapping["model"]["rename"], "model")
        self.assertNotIn("tools", mapping)

    def test_registered_in_both_registries(self) -> None:
        """AC12 — cursor is in ADAPTERS and registry."""
        self.assertIn("cursor", ADAPTERS)
        self.assertIs(registry["cursor"], cursor)


class CursorProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_skill_command_hook_body_project(self) -> None:
        """AC7 — skill (direct-directory), command + hook-body (direct-file)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "skills" / "my-skill").mkdir(parents=True)
            (pack / ".apm" / "skills" / "my-skill" / "SKILL.md").write_text("x", encoding="utf-8")
            (pack / ".apm" / "commands").mkdir(parents=True)
            (pack / ".apm" / "commands" / "do-thing.md").write_text("cmd", encoding="utf-8")
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "on-start.py").write_text("#!py", encoding="utf-8")
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            self.assertTrue((out / ".cursor" / "skills" / "my-skill" / "SKILL.md").exists())
            self.assertTrue((out / ".cursor" / "commands" / "do-thing.md").exists())
            self.assertTrue((out / ".cursor" / "hooks" / "on-start.py").exists())

    def test_agent_md_shape_readonly_reviewer(self) -> None:
        """AC8 — agent .md: name/description/model/readonly, no tools."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "foo", tools="Read, Grep, Glob, Bash", model="opus")
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            text = (out / ".cursor" / "agents" / "foo.md").read_text(encoding="utf-8")
            frontmatter = text.split("---")[1]
            self.assertIn("name: foo", frontmatter)
            self.assertIn("model: opus", frontmatter)
            self.assertIn("readonly: true", frontmatter)
            self.assertNotIn("tools", frontmatter)
            self.assertNotIn("readonly: True", frontmatter)  # lower-cased bool
            self.assertIn("agent body", text)

    def test_readonly_predicate_all_arms(self) -> None:
        """AC9 — readonly: true for non-mutating declared tools; omitted for
        mutating tools and for absent tools."""
        cases = {
            # name: (tools, expects_readonly_line)
            "reviewer": ("Read, Grep, Glob, Bash", True),
            "retriever": ("Read, Grep, Glob, WebFetch, WebSearch", True),
            "writer": ("Read, Edit, Write, Grep, Glob, Bash", False),
            "notebook": ("Read, NotebookEdit", False),
            "multiedit": ("Read, MultiEdit", False),
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            for name, (tools, _) in cases.items():
                _seed_agent(pack, name, tools=tools)
            _seed_agent(pack, "notools", tools=None)
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            for name, (_, expects) in cases.items():
                fm = (out / ".cursor" / "agents" / f"{name}.md").read_text().split("---")[1]
                if expects:
                    self.assertIn("readonly: true", fm, f"{name} should be readonly")
                else:
                    self.assertNotIn("readonly", fm, f"{name} should omit readonly")
            notools_fm = (out / ".cursor" / "agents" / "notools.md").read_text().split("---")[1]
            self.assertNotIn("readonly", notools_fm, "no-tools agent should omit readonly")

    def test_empty_tools_list_is_readonly(self) -> None:
        """AC9 edge — a declared-but-empty tools list has zero mutating tools,
        so it is read-only (documents the chosen behavior of the predicate)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "empty", tools="")
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            fm = (out / ".cursor" / "agents" / "empty.md").read_text().split("---")[1]
            self.assertIn("readonly: true", fm)

    def test_agent_name_derived_from_filename(self) -> None:
        """AC8 — when frontmatter omits `name`, it is derived from the filename."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "from-file.md").write_text(
                "---\ndescription: no name field\ntools: Read, Grep\n---\nBody.\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            fm = (out / ".cursor" / "agents" / "from-file.md").read_text().split("---")[1]
            self.assertIn("name: from-file", fm)

    def test_hook_wiring_aggregated_with_version_and_remap(self) -> None:
        """AC10 — one hooks.json, version 1, event remap, path-rewritten cmd."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_session_start_wiring(pack)
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            data = json.loads((out / ".cursor" / "hooks.json").read_text())
            self.assertEqual(data["version"], 1)
            self.assertIn("sessionStart", data["hooks"])
            self.assertNotIn("SessionStart", data["hooks"])
            self.assertEqual(
                data["hooks"]["sessionStart"][0]["command"],
                "python .cursor/hooks/session-start.py",
            )

    def test_hook_wiring_merge_is_non_destructive(self) -> None:
        """AC11 — merge preserves foreign top-level keys + foreign events."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_session_start_wiring(pack)
            out = tmp_path / "out"
            target = out / ".cursor" / "hooks.json"
            target.parent.mkdir(parents=True)
            target.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "customTopLevel": "keep-me",
                        "hooks": {"stop": [{"command": "echo bye"}]},
                    }
                ),
                encoding="utf-8",
            )
            cursor.project(pack, self.contract, out)
            data = json.loads(target.read_text())
            self.assertEqual(data["customTopLevel"], "keep-me")
            self.assertIn("stop", data["hooks"])  # foreign event preserved
            self.assertIn("sessionStart", data["hooks"])  # managed event added

    def test_unmapped_event_dropped_not_crash(self) -> None:
        """AC10 — an unmapped source event is dropped (no exception)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "w.toml").write_text(
                "[[hooks.NoSuchEvent]]\n"
                'hooks = [ { type = "command", command = "echo x" } ]\n'
                "[[hooks.SessionStart]]\n"
                'hooks = [ { type = "command", command = "echo y" } ]\n',
                encoding="utf-8",
            )
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)  # must not raise
            data = json.loads((out / ".cursor" / "hooks.json").read_text())
            self.assertIn("sessionStart", data["hooks"])
            self.assertNotIn("NoSuchEvent", data["hooks"])
            self.assertEqual(len(data["hooks"]), 1)

    def test_malformed_handler_dropped_not_crash(self) -> None:
        """A handler missing a string `command` (or wrong `type`) is dropped,
        not crashed on — and a well-formed sibling still wires."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "w.toml").write_text(
                "[[hooks.SessionStart]]\n"
                'hooks = [ { type = "command" }, '
                '{ type = "command", command = "python tools/hooks/ok.py" } ]\n',
                encoding="utf-8",
            )
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)  # must not raise
            data = json.loads((out / ".cursor" / "hooks.json").read_text())
            handlers = data["hooks"]["sessionStart"]
            self.assertEqual(len(handlers), 1)
            self.assertEqual(handlers[0]["command"], "python .cursor/hooks/ok.py")

    def test_real_core_pack_projects(self) -> None:
        """AC8/AC9 against the real shipped core pack: reviewers readonly,
        implementer writable (omitted)."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            cursor.project(REPO_ROOT / "packs" / "core", self.contract, out)
            for reviewer in ("security-reviewer", "adversarial-reviewer", "quality-engineer"):
                fm = (out / ".cursor" / "agents" / f"{reviewer}.md").read_text().split("---")[1]
                self.assertIn("readonly: true", fm, f"{reviewer} must be readonly")
            impl_fm = (out / ".cursor" / "agents" / "implementer.md").read_text().split("---")[1]
            self.assertNotIn("readonly", impl_fm, "implementer must omit readonly")

    def test_nested_symlink_not_reproduced(self) -> None:
        """Ride-along (security): a nested symlink inside a skill dir is not
        reproduced in the output, so the install walker can't read through it
        to embed out-of-tree content. Regular files still copy."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            skill = pack / ".apm" / "skills" / "s"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("ok", encoding="utf-8")
            secret = tmp_path / "secret.txt"
            secret.write_text("SECRET", encoding="utf-8")
            os.symlink(secret, skill / "leak.txt")
            out = tmp_path / "out"
            cursor.project(pack, self.contract, out)
            leaked = out / ".cursor" / "skills" / "s" / "leak.txt"
            self.assertFalse(leaked.is_symlink(), "nested symlink must not be reproduced")
            self.assertFalse(leaked.exists(), "nested symlink target must not be copied")
            self.assertTrue((out / ".cursor" / "skills" / "s" / "SKILL.md").exists())


class CursorInstallDispatchTests(unittest.TestCase):
    """AC14 — cursor is wired into both install render dispatchers; neither
    raises `no … projection wired for adapter 'cursor'` for a cursor pack."""

    def _seed_pack(self, root: Path) -> Path:
        pack = root / "pack"
        (pack / ".apm" / "agents").mkdir(parents=True)
        (pack / ".apm" / "agents" / "foo.md").write_text(
            "---\nname: foo\ndescription: a foo agent\ntools: Read, Grep\n---\nBody.\n",
            encoding="utf-8",
        )
        return pack

    def test_cursor_dispatch_not_refused_user_scope(self) -> None:
        from agentbundle.commands.install import _render_for_user_scope

        with tempfile.TemporaryDirectory() as tmp:
            pack = self._seed_pack(Path(tmp))
            projection = _render_for_user_scope(
                pack,
                adapter="cursor",
                allowed_adapters=["cursor"],
                contract_version="0.11",
                command_name="install",
            )
        # Scope-agnostic repo-relpaths (no rewrite); user-rooting at `~` is the
        # caller's job.
        self.assertIn(".cursor/agents/foo.md", projection)

    def test_cursor_dispatch_not_refused_repo_scope(self) -> None:
        from agentbundle.commands.install import _render_for_repo_scope

        with tempfile.TemporaryDirectory() as tmp:
            pack = self._seed_pack(Path(tmp))
            target_adapter, projection = _render_for_repo_scope(
                pack,
                adapter="cursor",
                allowed_adapters=["cursor"],
                contract_version="0.11",
                command_name="install",
            )
        self.assertEqual(target_adapter, "cursor")
        self.assertIn(".cursor/agents/foo.md", projection)


class ContractVersionAtLeastTests(unittest.TestCase):
    """Ride-along: the numeric `contract_version_at_least` replaces the lexical
    `>= "0.7"` compare the cursor v0.11 bump pushed into two-digit territory
    (lexically `"0.11" < "0.7"`)."""

    def test_numeric_compare_not_lexical(self) -> None:
        self.assertTrue(contract_version_at_least("0.11", "0.7"))  # the bug case
        self.assertTrue(contract_version_at_least("0.10", "0.7"))
        self.assertTrue(contract_version_at_least("0.8", "0.7"))
        self.assertTrue(contract_version_at_least("0.7", "0.7"))
        self.assertTrue(contract_version_at_least("1.0", "0.7"))
        self.assertFalse(contract_version_at_least("0.6", "0.7"))

    def test_none_or_unparseable_is_false(self) -> None:
        self.assertFalse(contract_version_at_least(None, "0.7"))
        self.assertFalse(contract_version_at_least("garbage", "0.7"))


class CursorSelfHostTests(unittest.TestCase):
    def test_cursor_not_in_self_host_adapters(self) -> None:
        """AC15 — cursor is distribution-only, not self-hosted."""
        from agentbundle.build.self_host import SELF_HOST_ADAPTERS

        self.assertNotIn("cursor", SELF_HOST_ADAPTERS)


if __name__ == "__main__":
    unittest.main()
