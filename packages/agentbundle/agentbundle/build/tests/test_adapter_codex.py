"""Tests for the Codex adapter (T5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agentbundle.build.adapters import codex
from agentbundle.build.adapters.codex import (
    _LEGACY_SKILL_BLOCK_END,
    _LEGACY_SKILL_BLOCK_START,
    _splice_managed_block,
    _strip_legacy_skill_block,
    project,
    project_packs,
)
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_pack(root: Path, name: str = "pack", skill_prefix: str = "") -> Path:
    pack = root / name
    (pack / ".apm" / "skills" / f"{skill_prefix}foo").mkdir(parents=True)
    (pack / ".apm" / "skills" / f"{skill_prefix}foo" / "SKILL.md").write_text(
        f"---\ndescription: {skill_prefix}foo skill description\n---\n# foo\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "skills" / f"{skill_prefix}alpha").mkdir(parents=True)
    (pack / ".apm" / "skills" / f"{skill_prefix}alpha" / "SKILL.md").write_text(
        f"---\ndescription: {skill_prefix}alpha skill description\n---\n# alpha\n",
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

    def test_only_command_dropped_post_v08(self) -> None:
        """v0.8 inverts the pre-bump assertion: codex now projects `agent`
        (via codex-agent-toml) and `hook-wiring` (via merge-json) natively.
        Only `command` stays dropped — codex custom-prompts are deprecated
        upstream in favour of skills (RFC pointer in spec § Assumptions).

        Renamed from ``test_agent_hook_wiring_command_dropped`` — the
        v0.7 assertion was the inverse of what the v0.8 contract claims
        (AC2). Deliberate spec-driven inversion, not a regression hiding
        behind a test deletion.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            # Agent .md no longer appears anywhere (projected as .toml).
            self.assertFalse(any(out.rglob("bar.md")))
            # Command .md still nowhere (codex command stays dropped).
            self.assertFalse(any(out.rglob("qux.md")))
            # Agent IS projected as TOML.
            self.assertTrue((out / ".codex" / "agents" / "bar.toml").exists())

    def test_codex_agent_projects_via_codex_agent_toml_mode(self) -> None:
        """The pack ships ``.apm/agents/<name>.md``; codex projects each
        as ``.codex/agents/<name>.toml`` with the three expected keys."""
        import tomllib

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "bar.md").write_text(
                "---\nname: bar\ndescription: a bar agent\n---\nAgent body.\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            target = out / ".codex" / "agents" / "bar.toml"
            self.assertTrue(target.exists(), f"expected {target}")
            data = tomllib.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "bar")
            self.assertEqual(data["description"], "a bar agent")
            self.assertIn("developer_instructions", data)

    def test_codex_agent_projects_model_and_tool_config(self) -> None:
        """Codex projection preserves model/tool intent as documented
        Codex config, collapsing multiple Claude tool names to one Codex
        capability knob and never emitting a generic top-level tools list."""
        import tomllib

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "agents").mkdir(parents=True)
            (pack / ".apm" / "agents" / "reviewer.md").write_text(
                "---\n"
                "name: reviewer\n"
                "description: review\n"
                "tools: Read, Grep, Glob, Bash, WebFetch, WebSearch\n"
                "model: sonnet\n"
                "---\n"
                "Body.\n",
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            data = tomllib.loads(
                (out / ".codex" / "agents" / "reviewer.toml").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(data["model"], "gpt-5.5")
            self.assertEqual(data["model_reasoning_effort"], "medium")
            self.assertEqual(data["sandbox_mode"], "read-only")
            self.assertEqual(data["features"]["shell_tool"], True)
            self.assertEqual(data["web_search"], "live")
            self.assertEqual(data["tools"]["web_search"], True)

    def test_codex_hook_wiring_projects_via_merge_json(self) -> None:
        """Pack ships ``.apm/hook-wiring/<name>.toml``; codex projects the
        merged result at ``.codex/hooks.json`` with the ``hooks`` key."""
        import json

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack / ".apm" / "hook-wiring" / "wire.toml").write_text(
                '[hooks]\n'
                '"SessionStart" = [{matcher = "*", hooks = [{type = "command", command = "echo hi"}]}]\n',
                encoding="utf-8",
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            target = out / ".codex" / "hooks.json"
            self.assertTrue(target.exists(), f"expected {target}")
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("hooks", data)
            self.assertIn("SessionStart", data["hooks"])

    def test_codex_command_still_dropped_at_build_time(self) -> None:
        """Fixture pack with one command; assert NO command-shaped output
        anywhere under ``<output>/.codex/`` (mode is `dropped`,
        ``_iter_primitives`` skips it)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = tmp_path / "pack"
            (pack / ".apm" / "commands").mkdir(parents=True)
            (pack / ".apm" / "commands" / "qux.md").write_text(
                "# qux command\n", encoding="utf-8"
            )
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertFalse(
                any(out.rglob("qux.md")),
                "command projection should be skipped (dropped)",
            )

    def test_hook_body_extensions_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            project(pack, self.contract, out)
            self.assertTrue((out / "tools" / "hooks" / "baz.sh").exists())
            self.assertTrue((out / "tools" / "hooks" / "baz.py").exists())


def _seed_two_skill_pack(root: Path, name: str = "two-skill") -> Path:
    """Two skills: one flat, one with nested subdirectories."""
    pack = root / name
    flat = pack / ".apm" / "skills" / "flat"
    flat.mkdir(parents=True)
    (flat / "SKILL.md").write_text(
        "---\ndescription: flat skill\n---\n# flat\nbody\n",
        encoding="utf-8",
    )

    nested = pack / ".apm" / "skills" / "nested"
    (nested / "scripts").mkdir(parents=True)
    (nested / "references").mkdir(parents=True)
    (nested / "SKILL.md").write_text(
        "---\ndescription: nested skill\n---\n# nested\nbody\n",
        encoding="utf-8",
    )
    (nested / "scripts" / "run.sh").write_text(
        "#!/bin/sh\necho run\n",
        encoding="utf-8",
    )
    (nested / "references" / "notes.md").write_text(
        "# Notes\nReference content.\n",
        encoding="utf-8",
    )
    return pack


def _seed_symlinked_pack(root: Path, name: str = "symlinked") -> Path:
    """Skill body with a relative symlink under references/."""
    pack = root / name
    (pack / ".apm" / "assets").mkdir(parents=True)
    (pack / ".apm" / "assets" / "shared.md").write_text(
        "# Shared\nContent.\n",
        encoding="utf-8",
    )

    linker = pack / ".apm" / "skills" / "linker"
    (linker / "references").mkdir(parents=True)
    (linker / "SKILL.md").write_text(
        "---\ndescription: linker skill\n---\n# linker\n",
        encoding="utf-8",
    )
    (linker / "references" / "shared.md").symlink_to(Path("../../../assets/shared.md"))
    return pack


def _seed_same_name_pack(root: Path, name: str, body: str) -> Path:
    pack = root / name
    skill_dir = pack / ".apm" / "skills" / "same-name"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return pack


class TestDirectDirectoryProjection(unittest.TestCase):
    """Post-RFC-0009 Codex `skill` projection — `direct-directory` mode."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_byte_equal_projection_two_skill(self) -> None:
        # AC3, AC4.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_two_skill_pack(tmp_path)
            out = tmp_path / "out"

            project_packs([pack], self.contract, out)

            for rel in (
                "flat/SKILL.md",
                "nested/SKILL.md",
                "nested/scripts/run.sh",
                "nested/references/notes.md",
            ):
                source_bytes = (pack / ".apm" / "skills" / rel).read_bytes()
                projected_bytes = (out / ".agents" / "skills" / rel).read_bytes()
                self.assertEqual(
                    projected_bytes,
                    source_bytes,
                    f"byte mismatch at {rel}",
                )

    def test_symlink_pass_through(self) -> None:
        # AC5.
        import os

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_symlinked_pack(tmp_path)
            out = tmp_path / "out"

            project_packs([pack], self.contract, out)

            projected_link = out / ".agents" / "skills" / "linker" / "references" / "shared.md"
            self.assertTrue(os.path.islink(projected_link))
            self.assertEqual(
                os.readlink(projected_link),
                str(Path("../../../assets/shared.md")),
            )

    def test_same_name_last_wins(self) -> None:
        # AC6 — Codex case.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_same_name_pack(
                tmp_path, "pack-a", "# pack-a\nPACK_A_SENTINEL\n",
            )
            pack_b = _seed_same_name_pack(
                tmp_path, "pack-b", "# pack-b\nPACK_B_SENTINEL\n",
            )
            out = tmp_path / "out"

            project_packs([pack_a, pack_b], self.contract, out)
            body = (out / ".agents" / "skills" / "same-name" / "SKILL.md").read_text(
                encoding="utf-8",
            )
            self.assertIn("PACK_B_SENTINEL", body)
            self.assertNotIn("PACK_A_SENTINEL", body)

    def test_top_level_symlink_skill_is_skipped(self) -> None:
        # Defense-in-depth: a malicious pack with `.apm/skills/<name>`
        # as a symlink to a sensitive directory would exfiltrate its
        # contents via `copytree` (the `symlinks=True` flag only
        # governs symlinks *inside* the tree). The adapter must skip
        # symlink entries at the iteration level so the contents do
        # not land in the projection. `lint-packs` already refuses
        # such packs; this is the adapter-layer safety net.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            external = tmp_path / "external-secrets"
            external.mkdir()
            (external / "secret.txt").write_text("DO NOT LEAK\n", encoding="utf-8")

            pack = tmp_path / "pack"
            skills_dir = pack / ".apm" / "skills"
            skills_dir.mkdir(parents=True)
            # Top-level skill entry is a symlink-to-directory.
            (skills_dir / "malicious").symlink_to(external, target_is_directory=True)
            # And a legitimate skill — that one must still project.
            legit = skills_dir / "legit"
            legit.mkdir()
            (legit / "SKILL.md").write_text("# legit\n", encoding="utf-8")

            out = tmp_path / "out"

            project_packs([pack], self.contract, out)

            self.assertFalse((out / ".agents" / "skills" / "malicious").exists())
            self.assertFalse((out / ".agents" / "skills" / "secret.txt").exists())
            self.assertTrue((out / ".agents" / "skills" / "legit" / "SKILL.md").is_file())
            # External directory untouched.
            self.assertEqual(
                (external / "secret.txt").read_text(encoding="utf-8"),
                "DO NOT LEAK\n",
            )

    def test_destination_symlink_safe_overwrite(self) -> None:
        # Spec § Never do: `shutil.rmtree` is barred against entries
        # whose `is_symlink()` is true. If a previous run left a
        # symlink at `<target>/skills/<name>`, the next projection
        # must unlink it (removing the link, not the target).
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_two_skill_pack(tmp_path)
            out = tmp_path / "out"
            target = out / ".agents" / "skills"
            target.mkdir(parents=True)

            external = tmp_path / "external"
            external.mkdir()
            (external / "anchor").write_text("keep me\n", encoding="utf-8")
            (target / "flat").symlink_to(external, target_is_directory=True)

            project_packs([pack], self.contract, out)

            self.assertFalse((target / "flat").is_symlink())
            self.assertTrue((target / "flat" / "SKILL.md").is_file())
            self.assertTrue(external.is_dir())
            self.assertEqual(
                (external / "anchor").read_text(encoding="utf-8"),
                "keep me\n",
            )

    def test_same_name_last_wins_reversed(self) -> None:
        # AC6 — Codex case, reversed.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_same_name_pack(
                tmp_path, "pack-a", "# pack-a\nPACK_A_SENTINEL\n",
            )
            pack_b = _seed_same_name_pack(
                tmp_path, "pack-b", "# pack-b\nPACK_B_SENTINEL\n",
            )
            out = tmp_path / "out"

            project_packs([pack_b, pack_a], self.contract, out)
            body = (out / ".agents" / "skills" / "same-name" / "SKILL.md").read_text(
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


class TestCodexOrphanSweep(unittest.TestCase):
    """T7 — `direct-directory` skill projection runs `sweep_orphans`
    against the union of source skill names across the call's pack list.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_codex_two_stage_shrink(self) -> None:
        # AC17: project {a, b, c} then {a, c} into the same output.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            three = _seed_named_skills_pack(tmp_path, "three-skill", ["a", "b", "c"])
            shrink = _seed_named_skills_pack(tmp_path, "two-skill-shrink", ["a", "c"])
            out = tmp_path / "out"

            project_packs([three], self.contract, out)
            self.assertTrue((out / ".agents" / "skills" / "b").is_dir())

            project_packs([shrink], self.contract, out)
            children = {p.name for p in (out / ".agents" / "skills").iterdir()}
            self.assertEqual(children, {"a", "c"})

    def test_codex_two_pack_union(self) -> None:
        # AC20: pack_a={a,b} + pack_b={b,c} → {a,b,c};
        #        then pack_a alone → {a,b}, c removed.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack_a = _seed_named_skills_pack(tmp_path, "pack-a", ["a", "b"])
            pack_b = _seed_named_skills_pack(tmp_path, "pack-b", ["b", "c"])
            out = tmp_path / "out"

            project_packs([pack_a, pack_b], self.contract, out)
            children = {p.name for p in (out / ".agents" / "skills").iterdir()}
            self.assertEqual(children, {"a", "b", "c"})

            project_packs([pack_a], self.contract, out)
            children = {p.name for p in (out / ".agents" / "skills").iterdir()}
            self.assertEqual(children, {"a", "b"})

    def test_codex_symlink_safe_sweep(self) -> None:
        # AC21: pre-seed a symlink-to-external in the target dir; the
        # sweep removes the symlink but leaves the external dir intact.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_named_skills_pack(tmp_path, "pack", ["a"])
            external = tmp_path / "external"
            external.mkdir()
            (external / "anchor").write_text("keep me\n", encoding="utf-8")
            out = tmp_path / "out"
            target = out / ".agents" / "skills"
            target.mkdir(parents=True)
            link = target / "b"
            link.symlink_to(external, target_is_directory=True)

            project_packs([pack], self.contract, out)

            self.assertTrue((target / "a").is_dir())
            self.assertFalse(link.exists())
            self.assertFalse(link.is_symlink())
            self.assertTrue(external.is_dir())
            self.assertEqual(
                (external / "anchor").read_text(encoding="utf-8"),
                "keep me\n",
            )


class TestMigrationStripIntegrated(unittest.TestCase):
    """Codex `project_packs` strips the legacy block from `<output_root>/AGENTS.md`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def _populated(self) -> str:
        return (
            "# Top\n\nIntroductory prose.\n\n"
            f"{_LEGACY_SKILL_BLOCK_START}\n"
            "- **a** — desc-a\n"
            "- **b** — desc-b\n"
            f"{_LEGACY_SKILL_BLOCK_END}\n"
            "\nClosing prose.\n"
        )

    def test_happy_path_strips_delimiters_and_preserves_prose(self) -> None:
        # AC10, AC11. The strip's only allowed mutation is removing
        # the legacy delimiter region; outside-delimiter bytes must
        # survive byte-for-byte. Substring `assertIn` would pass on
        # munged surrounding bytes; the concatenation assertion
        # below pins the byte-equality contract AC11(c) names.
        outside_before = "# Top\n\nIntroductory prose.\n\n"
        outside_after = "\nClosing prose.\n"
        populated = (
            f"{outside_before}"
            f"{_LEGACY_SKILL_BLOCK_START}\n"
            f"- **a** — desc-a\n"
            f"- **b** — desc-b\n"
            f"{_LEGACY_SKILL_BLOCK_END}\n"
            f"{outside_after}"
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_two_skill_pack(tmp_path)
            out = tmp_path / "out"
            out.mkdir()
            (out / "AGENTS.md").write_text(populated, encoding="utf-8")

            project_packs([pack], self.contract, out)

            text = (out / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn(_LEGACY_SKILL_BLOCK_START, text)
            self.assertNotIn(_LEGACY_SKILL_BLOCK_END, text)
            # Byte-for-byte preservation: the outside-delimiter prose
            # appears unchanged, in order, with no munging.
            self.assertIn(outside_before + outside_after, text)

    def test_already_clean_is_byte_identical(self) -> None:
        # AC12.
        clean = "# Top\n\nNo managed block.\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_two_skill_pack(tmp_path)
            out = tmp_path / "out"
            out.mkdir()
            (out / "AGENTS.md").write_text(clean, encoding="utf-8")

            project_packs([pack], self.contract, out)

            self.assertEqual(
                (out / "AGENTS.md").read_text(encoding="utf-8"),
                clean,
            )

    def test_idempotent_across_two_calls(self) -> None:
        # AC13.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_two_skill_pack(tmp_path)
            out = tmp_path / "out"
            out.mkdir()
            (out / "AGENTS.md").write_text(self._populated(), encoding="utf-8")

            project_packs([pack], self.contract, out)
            first = (out / "AGENTS.md").read_bytes()
            project_packs([pack], self.contract, out)
            second = (out / "AGENTS.md").read_bytes()
            self.assertEqual(first, second)

    def test_hand_edited_content_between_delimiters_is_lost(self) -> None:
        # AC14.
        sentinel = "<<HAND-EDITED-PRESERVE-ME>>"
        body = (
            "prefix\n"
            f"{_LEGACY_SKILL_BLOCK_START}\n"
            f"{sentinel}\n"
            f"{_LEGACY_SKILL_BLOCK_END}\n"
            "suffix\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_two_skill_pack(tmp_path)
            out = tmp_path / "out"
            out.mkdir()
            (out / "AGENTS.md").write_text(body, encoding="utf-8")

            project_packs([pack], self.contract, out)

            text = (out / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn(sentinel, text)


class TestMigrationStripPureFunction(unittest.TestCase):
    """Pure-function tests for `_strip_legacy_skill_block`.

    No filesystem; the strip is a text transform. Integration with
    `project_packs` is covered by T4's tests.
    """

    OUTSIDE_BEFORE = "# Top\n\nIntroductory prose.\n\n"
    OUTSIDE_AFTER = "\nClosing prose.\n"

    def _populated(self) -> str:
        return (
            f"{self.OUTSIDE_BEFORE}"
            f"{_LEGACY_SKILL_BLOCK_START}\n"
            f"- **a** — desc-a\n"
            f"- **b** — desc-b\n"
            f"{_LEGACY_SKILL_BLOCK_END}\n"
            f"{self.OUTSIDE_AFTER}"
        )

    def test_happy_path_strips_delimiters_and_preserves_outside_prose(self) -> None:
        stripped = _strip_legacy_skill_block(self._populated())
        self.assertNotIn(_LEGACY_SKILL_BLOCK_START, stripped)
        self.assertNotIn(_LEGACY_SKILL_BLOCK_END, stripped)
        self.assertIn("# Top\n", stripped)
        self.assertIn("Introductory prose.", stripped)
        self.assertIn("Closing prose.", stripped)

    def test_already_clean_input_is_byte_identical(self) -> None:
        clean = "# Top\n\nNo managed block here.\n"
        self.assertEqual(_strip_legacy_skill_block(clean), clean)

    def test_idempotent(self) -> None:
        once = _strip_legacy_skill_block(self._populated())
        twice = _strip_legacy_skill_block(once)
        self.assertEqual(once, twice)

    def test_non_list_content_between_delimiters_is_lost(self) -> None:
        sentinel = "<<HAND-EDITED-PRESERVE-ME>>"
        text = (
            f"prefix\n"
            f"{_LEGACY_SKILL_BLOCK_START}\n"
            f"{sentinel}\n"
            f"{_LEGACY_SKILL_BLOCK_END}\n"
            f"suffix\n"
        )
        stripped = _strip_legacy_skill_block(text)
        self.assertNotIn(sentinel, stripped)
        self.assertIn("prefix", stripped)
        self.assertIn("suffix", stripped)

    def test_out_of_order_delimiters_refused(self) -> None:
        # If the adopter pasted the delimiters in reverse order, the
        # splice would otherwise corrupt the file silently. Refuse
        # the input with a named error so the adopter can fix.
        reversed_input = (
            "prefix\n"
            f"{_LEGACY_SKILL_BLOCK_END}\n"
            f"{_LEGACY_SKILL_BLOCK_START}\n"
            "suffix\n"
        )
        with self.assertRaises(ValueError) as caught:
            _strip_legacy_skill_block(reversed_input)
        self.assertIn("appears before", str(caught.exception))

    def test_splice_managed_block_symbol_still_exists(self) -> None:
        # AC23(i): a future refactor that inlines the splice and deletes
        # the helper symbol breaks this import-and-call assertion.
        self.assertTrue(callable(_splice_managed_block))

    def test_strip_invokes_splice_managed_block_once(self) -> None:
        # AC23(ii) — deliberate retention test. A refactor that
        # inlines the splice and deletes `_splice_managed_block`
        # breaks the import. A refactor that keeps the symbol but
        # stops calling it from `_strip_legacy_skill_block` makes
        # `call_count == 0`. Either signals the retention contract
        # has been broken before the migration window closes. Do
        # not "simplify" by removing the mock — the mock IS the
        # contract. Patch with `wraps=` so the real function still
        # runs and the strip behaviour is unchanged.
        with mock.patch.object(
            codex,
            "_splice_managed_block",
            wraps=codex._splice_managed_block,
        ) as spy:
            _strip_legacy_skill_block(self._populated())
        self.assertEqual(spy.call_count, 1)


class TestCodexProjectsEveryShippedSkill(unittest.TestCase):
    """AC29 — every skill any in-tree pack ships projects through Codex
    into `.agents/skills/<name>/SKILL.md` (byte-equal to source).

    The spec text references `dist/codex/` as a notional adopter path;
    in this self-hosting repo, Codex projects to the repo root, so the
    test runs the projection against a `tmp_path` and enumerates
    `packs/*/.apm/skills/`. The sentinel set (`work-loop`, `new-spec`,
    `new-rfc`, `new-adr`) spans multiple packs (core +
    governance-extras), so the test must walk all packs — a core-only
    walk would silently skip `new-rfc` / `new-adr` against the spec's
    explicit sentinel list.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_every_shipped_skill_projects_with_equal_bytes(self) -> None:
        packs_root = REPO_ROOT / "packs"
        self.assertTrue(packs_root.is_dir())
        pack_paths = sorted(p for p in packs_root.iterdir() if p.is_dir())

        # Collect every source skill across every pack. Tracks the
        # "winning" source path for same-name collisions so byte-equal
        # comparisons use the last-supplied pack's body (matching
        # AC6).
        winning_source: dict[str, Path] = {}
        for pack_path in pack_paths:
            skills_dir = pack_path / ".apm" / "skills"
            if not skills_dir.is_dir():
                continue
            for entry in skills_dir.iterdir():
                if entry.is_dir():
                    winning_source[entry.name] = entry

        self.assertGreater(len(winning_source), 0)
        for sentinel in ("work-loop", "new-spec", "new-rfc", "new-adr"):
            self.assertIn(
                sentinel,
                winning_source,
                f"sentinel skill {sentinel!r} missing from any in-tree pack",
            )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_packs(pack_paths, self.contract, tmp_path)

            for skill_name, source_skill_dir in winning_source.items():
                projected_skill_md = (
                    tmp_path / ".agents" / "skills" / skill_name / "SKILL.md"
                )
                source_skill_md = source_skill_dir / "SKILL.md"
                if not source_skill_md.exists():
                    continue
                self.assertTrue(
                    projected_skill_md.is_file(),
                    f"skill {skill_name!r}: SKILL.md missing in projection",
                )
                self.assertEqual(
                    projected_skill_md.read_bytes(),
                    source_skill_md.read_bytes(),
                    f"skill {skill_name!r}: SKILL.md bytes differ",
                )


if __name__ == "__main__":
    unittest.main()
