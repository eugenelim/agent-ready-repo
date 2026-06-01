"""Tests for the Kiro adapter (T3)."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from agentbundle.build.adapters.kiro import project, project_packs
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
            # `tools: Read` source normalises to a list (`to-list`) then
            # maps onto the Kiro `read_file` tool id (`values`).
            self.assertEqual(data["tools"], ["read_file"])
            # `name` from filename (or frontmatter); body becomes prompt.
            self.assertEqual(data["name"], "bar")
            self.assertEqual(data.get("prompt", "").strip(), "agent body")

    def test_model_alias_translates_to_kiro_id(self) -> None:
        """Source `model: opus` (Claude Code's friendly alias) translates
        to Kiro's documented model ID per the contract's values map.
        Kiro CLI rejects an unknown identifier — emitting the alias
        verbatim would break the agent at load time."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "opus-agent.md").write_text(
                "---\nname: opus-agent\nmodel: opus\n---\nbody\n",
                encoding="utf-8",
            )
            (pack / ".apm" / "agents" / "sonnet-agent.md").write_text(
                "---\nname: sonnet-agent\nmodel: sonnet\n---\nbody\n",
                encoding="utf-8",
            )
            (pack / ".apm" / "agents" / "haiku-agent.md").write_text(
                "---\nname: haiku-agent\nmodel: haiku\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            opus = json.loads((out / ".kiro" / "agents" / "opus-agent.json").read_text(encoding="utf-8"))
            sonnet = json.loads((out / ".kiro" / "agents" / "sonnet-agent.json").read_text(encoding="utf-8"))
            haiku = json.loads((out / ".kiro" / "agents" / "haiku-agent.json").read_text(encoding="utf-8"))
            self.assertEqual(opus["model"], "claude-opus-4.6")
            self.assertEqual(sonnet["model"], "claude-sonnet-4.5")
            self.assertEqual(haiku["model"], "claude-haiku-4.5")

    def test_model_unknown_alias_drops_field_and_warns(self) -> None:
        """A source `model` value not in the contract's values map is
        dropped from the JSON output. Kiro then falls back to its CLI
        default with a warning rather than refusing the agent. The
        adapter also emits a stderr warning at build time so a
        pack-author typo (`opsus` for `opus`) surfaces before the
        agent ships."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "mystery.md").write_text(
                "---\nname: mystery\nmodel: gpt-5-turbo\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            buf = io.StringIO()
            with redirect_stderr(buf):
                project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "mystery.json").read_text(encoding="utf-8"))
            self.assertNotIn("model", data)
            stderr = buf.getvalue()
            self.assertIn("dropping model=", stderr)
            self.assertIn("gpt-5-turbo", stderr)

    def test_model_absent_in_source_absent_in_output(self) -> None:
        """An agent with no `model` frontmatter produces no `model`
        field in the JSON — regression check that the values rule
        doesn't inject anything for an absent source key."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "no-model.md").write_text(
                "---\nname: no-model\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "no-model.json").read_text(encoding="utf-8"))
            self.assertNotIn("model", data)

    def test_model_non_scalar_value_drops_field(self) -> None:
        """A non-string `model` value (e.g. a YAML flow-sequence
        `model: [opus]`) takes the values-miss branch and drops the
        field — `values` is defined to translate scalar source values
        only, so non-scalar input is intentionally rejected rather
        than smuggled through as a literal list."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "list-model.md").write_text(
                "---\nname: list-model\nmodel: [opus]\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            buf = io.StringIO()
            with redirect_stderr(buf):
                project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "list-model.json").read_text(encoding="utf-8"))
            self.assertNotIn("model", data)

    def test_tools_comma_string_splits_to_list(self) -> None:
        """Pack authors write `tools: Read, Grep, Glob, Bash` —
        Claude Code's frontmatter convention, not YAML flow syntax —
        and the kiro projection must split on commas, then map each
        Claude Code name onto its Kiro tool id: Read→read_file,
        Grep→grep_search, Glob→file_search, Bash→execute_bash."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "multi.md").write_text(
                "---\nname: multi\ntools: Read, Grep, Glob, Bash\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "multi.json").read_text(encoding="utf-8"))
            self.assertEqual(
                data["tools"], ["read_file", "grep_search", "file_search", "execute_bash"]
            )

    def test_tools_single_token_one_element_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "one.md").write_text(
                "---\nname: one\ntools: Read\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "one.json").read_text(encoding="utf-8"))
            self.assertEqual(data["tools"], ["read_file"])

    def test_tools_bracketed_list_preserved(self) -> None:
        """A YAML flow-sequence `tools: [Read, Grep]` is parsed as a
        list by `_parse_frontmatter`; the to-list normalize must not
        re-wrap or re-split it, and each element still maps to its
        Kiro tool id."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bracketed.md").write_text(
                "---\nname: bracketed\ntools: [Read, Grep]\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "bracketed.json").read_text(encoding="utf-8"))
            self.assertEqual(data["tools"], ["read_file", "grep_search"])

    def test_tools_web_search_maps_to_web_tag(self) -> None:
        """`WebSearch` has no granular Kiro tool id, so it maps to the
        `web` tag; `WebFetch` maps to the granular `web_fetch` id. Order
        is preserved."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "web.md").write_text(
                "---\nname: web\ntools: Read, WebFetch, WebSearch\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "web.json").read_text(encoding="utf-8"))
            self.assertEqual(data["tools"], ["read_file", "web_fetch", "web"])

    def test_tools_unmapped_token_drops_with_warning(self) -> None:
        """A Claude Code tool name absent from the values map (e.g.
        `NotebookEdit`) drops from the output with a stderr warning,
        rather than emitting a token Kiro can't resolve."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "nb.md").write_text(
                "---\nname: nb\ntools: Read, NotebookEdit\n---\nbody\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                project(pack, self.contract, out)
            data = json.loads((out / ".kiro" / "agents" / "nb.json").read_text(encoding="utf-8"))
            self.assertEqual(data["tools"], ["read_file"])
            self.assertIn("NotebookEdit", stderr.getvalue())

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


def _seed_minimal_pack(root: Path, name: str, skill_name: str, body: str) -> Path:
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

            self.assertTrue((out / ".kiro" / "skills" / "skill-a" / "SKILL.md").is_file())
            self.assertTrue((out / ".kiro" / "skills" / "skill-b" / "SKILL.md").is_file())

    def test_single_pack_project_delegates_to_project_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_minimal_pack(tmp_path, "pack", "skill-x", "# x\n")
            out_a = tmp_path / "out-a"
            out_b = tmp_path / "out-b"

            project(pack, self.contract, out_a)
            project_packs([pack], self.contract, out_b)

            self.assertEqual(
                (out_a / ".kiro" / "skills" / "skill-x" / "SKILL.md").read_bytes(),
                (out_b / ".kiro" / "skills" / "skill-x" / "SKILL.md").read_bytes(),
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
            body = (out / ".kiro" / "skills" / "same-name" / "SKILL.md").read_text(
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
            body = (out / ".kiro" / "skills" / "same-name" / "SKILL.md").read_text(
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


class TestKiroOrphanSweep(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_two_stage_shrink(self) -> None:
        # AC19: project {a, b, c} then {a, c} into the same output.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            three = _seed_named_skills_pack(tmp_path, "three-skill", ["a", "b", "c"])
            shrink = _seed_named_skills_pack(tmp_path, "two-skill-shrink", ["a", "c"])
            out = tmp_path / "out"

            project_packs([three], self.contract, out)
            self.assertTrue((out / ".kiro" / "skills" / "b").is_dir())

            project_packs([shrink], self.contract, out)
            children = {p.name for p in (out / ".kiro" / "skills").iterdir()}
            self.assertEqual(children, {"a", "c"})

    def test_two_pack_union(self) -> None:
        # AC20 — kiro case.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_named_skills_pack(tmp_path, "pack-a", ["a", "b"])
            pack_b = _seed_named_skills_pack(tmp_path, "pack-b", ["b", "c"])
            out = tmp_path / "out"

            project_packs([pack_a, pack_b], self.contract, out)
            children = {p.name for p in (out / ".kiro" / "skills").iterdir()}
            self.assertEqual(children, {"a", "b", "c"})

            project_packs([pack_a], self.contract, out)
            children = {p.name for p in (out / ".kiro" / "skills").iterdir()}
            self.assertEqual(children, {"a", "b"})


if __name__ == "__main__":
    unittest.main()
