"""Tests for the gemini adapter (RFC-0027 / ADR-0016 / gemini-full-parity).

Gemini is a full-parity native adapter projecting all five catalogue primitives
to `.gemini/*` at both scopes. Unlike Cursor, agents KEEP their `tools:` allowlist
(name-mapped to Gemini tool ids) and a tier-preserving `model` map is applied.
Commands use the new `gemini-command-toml` mode (markdown → TOML `prompt`,
fail-closed on positional args). hook-wiring + the static `AGENTS.md`
`context.fileName` bridge land in one `.gemini/settings.json` managed-merge, with
the hook-event map applied fail-closed. hook bodies land at `.gemini/hooks/` (the
cursor model). Distribution-only (not in SELF_HOST_ADAPTERS).
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS, gemini, registry
from agentbundle.build.contract import load as load_contract
from agentbundle.build.projections.gemini_command_toml import (
    project_gemini_command_toml,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"

_COMMAND_RULE = {"target-path": ".gemini/commands/"}


def _write_command(pack: Path, rel: str, *, description: str | None, body: str) -> None:
    path = pack / ".apm" / "commands" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if description is not None:
        lines += ["---", f"description: {description}", "---"]
    lines.append(body)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


# ===========================================================================
# T2 — gemini-command-toml projection mode (fail-closed)
# ===========================================================================


class GeminiCommandTomlTests(unittest.TestCase):
    def _project(self, tmp: Path) -> Path:
        out = tmp / "out"
        project_gemini_command_toml(tmp / "pack" / ".apm" / "commands", out, _COMMAND_RULE)
        return out / ".gemini" / "commands"

    def test_single_injection_and_description(self) -> None:
        """AC7 — `$ARGUMENTS`→`{{args}}`, body→`prompt`, description→`description`."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _write_command(
                tmp / "pack", "do-thing.md",
                description="Do the thing",
                body="Run the thing with $ARGUMENTS now.",
            )
            commands = self._project(tmp)
            import tomllib

            data = tomllib.loads((commands / "do-thing.toml").read_text())
            self.assertEqual(data["description"], "Do the thing")
            self.assertEqual(data["prompt"], "Run the thing with {{args}} now.\n")
            self.assertNotIn("$ARGUMENTS", data["prompt"])

    def test_subdir_namespacing_preserved(self) -> None:
        """AC7 — `git/commit.md` → `.gemini/commands/git/commit.toml`."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _write_command(tmp / "pack", "git/commit.md", description=None, body="Commit.")
            commands = self._project(tmp)
            self.assertTrue((commands / "git" / "commit.toml").exists())

    def test_positional_arg_raises(self) -> None:
        """AC7 — a body using positional `$1` raises a build error (fail-closed)."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _write_command(
                tmp / "pack", "bad.md", description=None,
                body="Use $1 and $2 positionally.",
            )
            with self.assertRaises(ValueError):
                self._project(tmp)

    def test_no_description_omits_key(self) -> None:
        """AC7 — a command with no `description` frontmatter omits the key."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            _write_command(tmp / "pack", "plain.md", description=None, body="Just a prompt.")
            commands = self._project(tmp)
            import tomllib

            data = tomllib.loads((commands / "plain.toml").read_text())
            self.assertNotIn("description", data)
            self.assertEqual(data["prompt"], "Just a prompt.\n")

    def test_command_dir_symlink_not_traversed(self) -> None:
        """Security — a directory symlink under .apm/commands/ is NOT walked into
        (os.walk(followlinks=False)), so an untrusted catalogue cannot read an
        out-of-tree target's *.md bytes into an in-jail .toml. The version-conditional
        rglob-follows-dir-symlink read-through (3.11/3.12) is closed."""
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            pack = tmp / "pack"
            (pack / ".apm" / "commands").mkdir(parents=True)
            secret_dir = tmp / "outside"
            secret_dir.mkdir()
            (secret_dir / "leak.md").write_text("---\ndescription: x\n---\nSECRET", encoding="utf-8")
            os.symlink(secret_dir, pack / ".apm" / "commands" / "evil")
            _write_command(pack, "ok.md", description="d", body="ok")
            commands = self._project(tmp)
            self.assertTrue((commands / "ok.toml").exists())
            self.assertFalse((commands / "evil").exists(), "dir symlink must not be traversed")
            self.assertFalse((commands / "evil" / "leak.toml").exists())


# ===========================================================================
# T1/T3 — contract block
# ===========================================================================


class GeminiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_contract_version_is_0_14(self) -> None:
        """Contract version is 0.16 (docs/specs/consolidated-pack-layout
        bumped it from kiro-cli-agent-skill-resources' 0.15). Name preserved."""
        self.assertEqual(self.contract["contract"]["version"], "0.17")

    def test_gemini_block_projects_five_primitives(self) -> None:
        """AC2 — five standard primitives with their gemini targets."""
        block = self.contract["adapter"]["gemini"]
        prims = {e["primitive"]: e for e in block["projection"]}
        self.assertEqual(set(prims), {"skill", "agent", "hook-body", "hook-wiring", "command"})
        self.assertEqual(prims["skill"]["mode"], "direct-directory")
        self.assertEqual(prims["skill"]["target-path"], ".agents/skills/")
        self.assertEqual(prims["agent"]["mode"], "direct-file")
        self.assertEqual(prims["agent"]["target-path"], ".gemini/agents/")
        self.assertEqual(prims["agent"]["frontmatter-mapping"], "gemini-agent-frontmatter")
        self.assertEqual(prims["hook-body"]["mode"], "direct-file")
        self.assertEqual(prims["hook-body"]["target-path"], ".gemini/hooks/")
        self.assertEqual(prims["hook-wiring"]["mode"], "merge-json")
        self.assertEqual(prims["hook-wiring"]["target-path"], ".gemini/settings.json")
        self.assertEqual(prims["hook-wiring"]["managed-key"], "hooks")
        self.assertEqual(prims["command"]["mode"], "gemini-command-toml")
        self.assertEqual(prims["command"]["target-path"], ".gemini/commands/")

    def test_kiro_ide_hook_dropped_in_table_form(self) -> None:
        """AC2 — kiro-ide-hook dropped in the table form (not the array)."""
        block = self.contract["adapter"]["gemini"]
        self.assertNotIn("kiro-ide-hook", {e["primitive"] for e in block["projection"]})
        self.assertEqual(block["projections"]["kiro-ide-hook"]["mode"], "dropped")

    def test_hook_event_map_pascalcase_to_gemini(self) -> None:
        """AC9 — the hook-event-map keys on Claude PascalCase, values are Gemini events."""
        hw = next(
            e for e in self.contract["adapter"]["gemini"]["projection"]
            if e["primitive"] == "hook-wiring"
        )
        self.assertEqual(
            hw["hook-event-map"],
            {
                "SessionStart": "SessionStart",
                "SessionEnd": "SessionEnd",
                "UserPromptSubmit": "BeforeAgent",
                "PreToolUse": "BeforeTool",
                "PostToolUse": "AfterTool",
                "Stop": "AfterAgent",
            },
        )

    def test_context_filenames_on_hook_wiring_rule(self) -> None:
        """AC8 — the static context bridge data lives in the contract."""
        hw = next(
            e for e in self.contract["adapter"]["gemini"]["projection"]
            if e["primitive"] == "hook-wiring"
        )
        self.assertEqual(hw["context-filenames"], ["AGENTS.md", "GEMINI.md"])

    def test_scope_identical_prefixes_both_scopes(self) -> None:
        """AC3 — `.gemini/` prefix identical at both scopes (no rewrite)."""
        scope = self.contract["adapter"]["gemini"]["scope"]
        self.assertEqual(scope["repo"], ".")
        self.assertEqual(scope["user"], "~")
        self.assertEqual(scope["allowed-prefixes"]["repo"], [".agents/skills/", ".gemini/", ".agentbundle/"])
        self.assertEqual(scope["allowed-prefixes"]["repo"], scope["allowed-prefixes"]["user"])

    def test_frontmatter_mapping_keeps_tools_and_model(self) -> None:
        """AC5/AC6 — gemini-agent-frontmatter maps name/description/tools/model."""
        m = self.contract["frontmatter-mapping"]["gemini-agent-frontmatter"]
        self.assertEqual(m["name"]["rename"], "name")
        self.assertEqual(m["description"]["rename"], "description")
        self.assertEqual(m["tools"]["normalize"], "to-list")
        self.assertEqual(m["tools"]["values"]["Read"], "read_file")
        self.assertEqual(m["tools"]["values"]["Bash"], "run_shell_command")
        self.assertEqual(m["tools"]["values"]["Edit"], "replace")
        self.assertEqual(m["tools"]["values"]["MultiEdit"], "replace")
        self.assertEqual(m["model"]["values"]["opus"], "gemini-2.5-pro")
        self.assertEqual(m["model"]["values"]["haiku"], "gemini-2.5-flash-lite")

    def test_registered_in_both_registries(self) -> None:
        """AC1 — gemini in ADAPTERS and registry."""
        self.assertIn("gemini", ADAPTERS)
        self.assertIs(registry["gemini"], gemini)


# ===========================================================================
# T3 — primitive projection + agent frontmatter mapping
# ===========================================================================


class GeminiProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_skill_command_hook_body_project(self) -> None:
        """AC2 — skill (direct-directory), command (gemini-command-toml), hook-body."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "skills" / "my-skill").mkdir(parents=True)
            (pack / ".apm" / "skills" / "my-skill" / "SKILL.md").write_text("x", encoding="utf-8")
            _write_command(pack, "do-thing.md", description="d", body="cmd")
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "on-start.py").write_text("#!py", encoding="utf-8")
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            self.assertTrue((out / ".agents" / "skills" / "my-skill" / "SKILL.md").exists())
            self.assertTrue((out / ".gemini" / "commands" / "do-thing.toml").exists())
            self.assertTrue((out / ".gemini" / "hooks" / "on-start.py").exists())

    def test_agent_keeps_and_maps_tools_and_model(self) -> None:
        """AC5/AC6 — tools name-mapped + kept, model tier-mapped."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "foo", tools="Read, Grep, Glob, Bash", model="opus")
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            text = (out / ".gemini" / "agents" / "foo.md").read_text(encoding="utf-8")
            fm = text.split("---")[1]
            self.assertIn("name: foo", fm)
            self.assertIn("model: gemini-2.5-pro", fm)
            self.assertIn("read_file", fm)
            self.assertIn("grep_search", fm)
            self.assertIn("run_shell_command", fm)
            self.assertNotIn("Read", fm)  # claude name should not survive
            self.assertNotIn("opus", fm)
            self.assertIn("agent body", text)

    def test_agent_dedups_collided_tools(self) -> None:
        """AC5 — Edit + MultiEdit both map to `replace`; the list de-duplicates."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "writer", tools="Edit, MultiEdit, Write")
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            fm = (out / ".gemini" / "agents" / "writer.md").read_text().split("---")[1]
            tools_line = next(ln for ln in fm.splitlines() if ln.startswith("tools:"))
            tools = [t.strip() for t in tools_line.split(":", 1)[1].strip(" []").split(",")]
            self.assertEqual(sorted(tools), ["replace", "write_file"])  # Edit+MultiEdit→one replace

    def test_agent_all_tools_unmapped_omits_tools_key(self) -> None:
        """AC5 — an agent whose tools all drop emits NO `tools` key (not `tools: []`,
        which Gemini could read as 'no tools permitted'); matches model-absent omit."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "alldrop", tools="NotATool, AlsoNot")
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)  # must not raise
            fm = (out / ".gemini" / "agents" / "alldrop.md").read_text().split("---")[1]
            self.assertNotIn("tools:", fm)

    def test_agent_absent_model_omitted(self) -> None:
        """AC6 — an agent with no model produces no model field."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "nomodel", tools="Read")
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            fm = (out / ".gemini" / "agents" / "nomodel.md").read_text().split("---")[1]
            self.assertNotIn("model:", fm)

    def test_agent_unmapped_tool_dropped(self) -> None:
        """AC5 — an unmapped tool is dropped (not emitted), with no crash."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "weird", tools="Read, NotARealTool")
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)  # must not raise
            fm = (out / ".gemini" / "agents" / "weird.md").read_text().split("---")[1]
            self.assertIn("read_file", fm)
            self.assertNotIn("NotARealTool", fm)

    def test_agent_name_derived_from_filename(self) -> None:
        """AC2 — frontmatter omitting `name` derives it from the filename."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "from-file.md").write_text(
                "---\ndescription: no name\ntools: Read, Grep\n---\nBody.\n", encoding="utf-8"
            )
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            fm = (out / ".gemini" / "agents" / "from-file.md").read_text().split("---")[1]
            self.assertIn("name: from-file", fm)

    def test_real_core_pack_projects(self) -> None:
        """AC5 against the real core pack — reviewers + implementer map cleanly."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            gemini.project(REPO_ROOT / "packs" / "core", self.contract, out)
            impl_fm = (out / ".gemini" / "agents" / "implementer.md").read_text().split("---")[1]
            self.assertIn("read_file", impl_fm)
            self.assertIn("run_shell_command", impl_fm)

    def test_nested_symlink_not_reproduced(self) -> None:
        """Security — a nested symlink inside a skill dir is not reproduced."""
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
            gemini.project(pack, self.contract, out)
            leaked = out / ".agents" / "skills" / "s" / "leak.txt"
            self.assertFalse(leaked.exists())
            self.assertTrue((out / ".agents" / "skills" / "s" / "SKILL.md").exists())


# ===========================================================================
# T4 — .gemini/settings.json single managed-merge (hooks + context)
# ===========================================================================


class GeminiSettingsMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def _settings(self, out: Path) -> dict:
        return json.loads((out / ".gemini" / "settings.json").read_text())

    def test_hooks_and_context_single_merge(self) -> None:
        """AC8 — hooks + context.fileName land in one settings.json; event remapped;
        command path-rewritten tools/hooks/→.gemini/hooks/."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_session_start_wiring(pack)
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            data = self._settings(out)
            self.assertEqual(data["context"]["fileName"], ["AGENTS.md", "GEMINI.md"])
            self.assertIn("SessionStart", data["hooks"])
            self.assertNotIn("UserPromptSubmit", data["hooks"])
            cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
            self.assertEqual(cmd, "python .gemini/hooks/session-start.py")

    def test_no_settings_json_without_wiring(self) -> None:
        """AC8 — a pack with no hook-wiring writes NO `.gemini/settings.json`
        (the cursor single-writer model: repo-scope install overwrites merge
        targets whole-file, so emitting a settings.json for every pack would
        clobber another pack's hooks). The `context` bridge rides in the
        hook-wiring write; in the catalogue `core` ships both."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_agent(pack, "foo", tools="Read")  # no wiring
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            self.assertFalse((out / ".gemini" / "settings.json").exists())

    def test_event_remap_all_arms(self) -> None:
        """AC9 — every shipped-vocabulary event maps to its Gemini event."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "w.toml").write_text(
                "".join(
                    f'[[hooks.{src}]]\nhooks = [ {{ type = "command", command = "echo x" }} ]\n'
                    for src in ("SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop")
                ),
                encoding="utf-8",
            )
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            hooks = self._settings(out)["hooks"]
            self.assertEqual(
                set(hooks),
                {"SessionStart", "SessionEnd", "BeforeAgent", "BeforeTool", "AfterTool", "AfterAgent"},
            )

    def test_foreign_key_survives_merge(self) -> None:
        """AC8 — a pre-existing foreign top-level key + foreign event survive."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            _seed_session_start_wiring(pack)
            out = tmp_path / "out"
            target = out / ".gemini" / "settings.json"
            target.parent.mkdir(parents=True)
            target.write_text(
                json.dumps({"theme": "keep-me", "hooks": {"AfterAgent": [{"hooks": []}]}}),
                encoding="utf-8",
            )
            gemini.project(pack, self.contract, out)
            data = self._settings(out)
            self.assertEqual(data["theme"], "keep-me")
            self.assertIn("AfterAgent", data["hooks"])  # foreign event preserved
            self.assertIn("SessionStart", data["hooks"])  # managed event added

    def test_unmapped_event_fails_build(self) -> None:
        """AC9 — an unrecognised source event fails the build (fail-closed)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "w.toml").write_text(
                '[[hooks.NoSuchEvent]]\nhooks = [ { type = "command", command = "echo x" } ]\n',
                encoding="utf-8",
            )
            out = tmp_path / "out"
            with self.assertRaises(ValueError):
                gemini.project(pack, self.contract, out)

    def test_matcher_passthrough(self) -> None:
        """AC9 — a source matcher passes through unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "w.toml").write_text(
                '[[hooks.PreToolUse]]\nmatcher = "Bash"\n'
                'hooks = [ { type = "command", command = "echo x" } ]\n',
                encoding="utf-8",
            )
            out = tmp_path / "out"
            gemini.project(pack, self.contract, out)
            entry = self._settings(out)["hooks"]["BeforeTool"][0]
            self.assertEqual(entry["matcher"], "Bash")


# ===========================================================================
# T4 — install dispatch (both scopes), T7 — distribution-only
# ===========================================================================


class GeminiInstallDispatchTests(unittest.TestCase):
    def _seed_pack(self, root: Path) -> Path:
        pack = root / "pack"
        (pack / ".apm" / "agents").mkdir(parents=True)
        (pack / ".apm" / "agents" / "foo.md").write_text(
            "---\nname: foo\ndescription: a foo agent\ntools: Read, Grep\n---\nBody.\n",
            encoding="utf-8",
        )
        return pack

    def test_gemini_dispatch_not_refused_user_scope(self) -> None:
        from agentbundle.commands.install import _render_for_user_scope

        with tempfile.TemporaryDirectory() as tmp:
            pack = self._seed_pack(Path(tmp))
            projection = _render_for_user_scope(
                pack, adapter="gemini", allowed_adapters=["gemini"],
                contract_version="0.13", command_name="install",
            )
        self.assertIn(".gemini/agents/foo.md", projection)

    def test_gemini_dispatch_not_refused_repo_scope(self) -> None:
        from agentbundle.commands.install import _render_for_repo_scope

        with tempfile.TemporaryDirectory() as tmp:
            pack = self._seed_pack(Path(tmp))
            target_adapter, projection = _render_for_repo_scope(
                pack, adapter="gemini", allowed_adapters=["gemini"],
                contract_version="0.13", command_name="install",
            )
        self.assertEqual(target_adapter, "gemini")
        self.assertIn(".gemini/agents/foo.md", projection)

    def test_gemini_user_scope_hook_body_and_settings(self) -> None:
        """AC10 — a hook-shipping pack lands its hook body at `.gemini/hooks/` AND
        `.gemini/settings.json` in the user-scope projection (every target under
        `.gemini/`, rooted at `~` by the generic user-rooting)."""
        from agentbundle.commands.install import _render_for_user_scope

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hooks").mkdir(parents=True)
            (pack / ".apm" / "hooks" / "session-start.py").write_text("#!py", encoding="utf-8")
            _seed_session_start_wiring(pack)
            projection = _render_for_user_scope(
                pack, adapter="gemini", allowed_adapters=["gemini"],
                contract_version="0.13", command_name="install",
            )
        self.assertIn(".gemini/hooks/session-start.py", projection)
        self.assertIn(".gemini/settings.json", projection)
        # every projected target is under `.gemini/` (no stray tools/hooks/ at user scope)
        self.assertTrue(all(k.startswith(".gemini/") for k in projection), sorted(projection))


class GeminiShippedAgentToolCoverageTests(unittest.TestCase):
    """AC5 — every tool any shipped agent declares is in the gemini tools map, so
    an unmapped tool would surface here rather than silently dropping at install."""

    def test_every_shipped_agent_tool_is_mapped(self) -> None:
        contract = load_contract(CONTRACT_PATH)
        values = contract["frontmatter-mapping"]["gemini-agent-frontmatter"]["tools"]["values"]
        declared: set[str] = set()
        for agent_md in (REPO_ROOT / "packs").glob("*/.apm/agents/*.md"):
            for line in agent_md.read_text(encoding="utf-8").splitlines():
                if line.startswith("tools:"):
                    declared.update(
                        t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()
                    )
        self.assertTrue(declared, "no shipped agent tools found — glob likely wrong")
        unmapped = declared - set(values)
        self.assertEqual(
            unmapped, set(),
            f"shipped agent tools not in gemini-agent-frontmatter values map: {unmapped}",
        )


class GeminiSelfHostTests(unittest.TestCase):
    def test_gemini_not_in_self_host_adapters(self) -> None:
        """AC12 — gemini is distribution-only, not self-hosted."""
        from agentbundle.build.self_host import SELF_HOST_ADAPTERS

        self.assertNotIn("gemini", SELF_HOST_ADAPTERS)


# ===========================================================================
# T5 — every pack admits gemini at BOTH repo and user scope (user directive)
# ===========================================================================


class GeminiAllPacksAdmissibleTests(unittest.TestCase):
    """AC11 — `--adapter gemini` resolves (is not refused) for every shipped pack
    at both repo and user scope: the 7 list-declaring packs list gemini, and the
    4 list-less packs admit any shipped (repo) / user-scope-capable (user) adapter."""

    PACKS_DIR = REPO_ROOT / "packs"

    def _allowed_adapters(self, pack_dir: Path) -> list[str] | None:
        import tomllib

        data = tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))
        return data.get("install", {}).get("allowed-adapters")

    def test_every_pack_admits_gemini_both_scopes(self) -> None:
        from agentbundle.commands.install import _resolve_target_adapter

        pack_dirs = sorted(p for p in self.PACKS_DIR.iterdir() if (p / "pack.toml").exists())
        self.assertTrue(pack_dirs, "no packs discovered under packs/ — pack lookup is broken")
        # Count-independent by design: don't pin the number of packs (every new
        # pack would break an unrelated adapter test). Assert gemini resolution
        # for the packs that *support* gemini — a pack with no allowed-adapters
        # list admits any shipped adapter; a pack with a list must name gemini.
        # Packs that constrain to a list without gemini are skipped, not failed.
        # `checked` is the non-vacuity guard the old hard count used to be.
        checked = 0
        for pack_dir in pack_dirs:
            allowed = self._allowed_adapters(pack_dir)
            if allowed is not None and "gemini" not in allowed:
                continue
            for scope in ("repo", "user"):
                resolved = _resolve_target_adapter(
                    pack_dir,
                    scope=scope,
                    adapter="gemini",
                    allowed_adapters=allowed,
                    contract_version="0.13",
                    command_name="install",
                )
                self.assertEqual(
                    resolved, "gemini",
                    f"{pack_dir.name} @ {scope}: --adapter gemini was not admitted",
                )
            checked += 1
        self.assertTrue(
            checked, "no pack exercised gemini admission — the check ran vacuously"
        )


if __name__ == "__main__":
    unittest.main()
