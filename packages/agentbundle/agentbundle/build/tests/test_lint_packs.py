"""Windows-portability lint: catches symlinks and Windows-poisonous
names in pack content before they reach a release artefact.

Also covers the per-target metadata gate landed under
docs/specs/lint-packs-target-vocab/: skill/agent name pattern, name
length, and description length per docs/contracts/target-vocab.toml.
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from agentbundle.build.lint_packs import (
    Constraints,
    cmd_lint_packs,
    lint_all_packs,
    lint_pack,
)


def _make_constraints(
    *,
    description_max: int = 1024,
    name_max: int = 64,
    name_pattern: str = r"^[a-z][a-z0-9-]*$",
    binding_targets: dict[str, list[str]] | None = None,
) -> Constraints:
    """Build a Constraints tuple inline for tests that need one but
    don't want to materialise a vocab file on disk. Defaults match
    the in-tree target-vocab.toml's strictest cap.
    """
    if binding_targets is None:
        binding_targets = {
            "description_max": ["codex", "kiro"],
            "name_max": ["kiro"],
            "name_pattern": ["claude-code", "codex", "copilot", "kiro"],
        }
    return Constraints(
        description_max=description_max,
        name_pattern=re.compile(name_pattern),
        name_max=name_max,
        binding_targets=binding_targets,
    )


def _write_minimal_pack(pack_dir: Path, name: str = "fixture-pack") -> None:
    """Drop a minimal pack.toml so lint_all_packs treats the dir as
    a pack. Tests that materialise packs build on this."""
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.0.1"\n',
        encoding="utf-8",
    )

# The repo-checked-in fixture lives under tests/fixtures/lint_packs/.
# Reserved-name violations are constructed at runtime under tmp_path
# (POSIX-only) because NTFS forbids `git checkout` from materialising
# a path like `seeds/CON.md` — keeping the fixture purely runtime-
# constructed lets the Windows CI runner clone the repo without
# `error: invalid path`. The symlink fixture is also runtime-only for
# the same portability reason.
FIXTURES = Path(__file__).resolve().parent.parent.parent.parent / "tests" / "fixtures" / "lint_packs"


def _materialise_with_reserved_fixture(root: Path) -> Path:
    """Build the equivalent of the legacy `with_reserved/` fixture under
    ``root``. POSIX-only — Windows refuses the `CON.md` create itself,
    so callers MUST gate on ``sys.platform != "win32"``.
    """
    pack = root / "with_reserved"
    (pack / "seeds").mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\n'
        'name = "with-reserved"\n'
        'version = "0.0.1"\n'
        'description = "Windows-portability lint fixture: ships seeds/CON.md to '
        'prove the lint rejects Windows-reserved names. Not for installation."\n'
        '\n'
        '[pack.adapter-contract]\n'
        'version = "0.2"\n'
        '\n'
        '[pack.install]\n'
        'default-scope = "repo"\n'
        'allowed-scopes = ["repo"]\n',
        encoding="utf-8",
    )
    (pack / "seeds" / "CON.md").write_text("reserved\n", encoding="utf-8")
    return pack


class LintPackTests(unittest.TestCase):
    def test_clean_fixture_returns_no_findings(self) -> None:
        findings = lint_pack(FIXTURES / "clean")
        self.assertEqual(findings, [])

    @unittest.skipIf(
        sys.platform == "win32",
        "NTFS refuses to materialise seeds/CON.md; lint logic is OS-agnostic "
        "so POSIX coverage is sufficient",
    )
    def test_with_reserved_fixture_catches_con_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = _materialise_with_reserved_fixture(Path(tmp))
            findings = lint_pack(pack)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("CON.md", findings[0])
        self.assertIn("reserved", findings[0].lower())

    def test_runtime_symlink_violation_detected(self) -> None:
        """Build a pack with a symlink under seeds/ in a tmp dir;
        assert the lint surfaces it. The symlink is created at test
        time so the on-disk fixture stays portable."""
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "linky"
            (pack / "seeds").mkdir(parents=True)
            (pack / "pack.toml").write_text(
                '[pack]\nname = "linky"\nversion = "0.0.1"\n',
                encoding="utf-8",
            )
            (pack / "seeds" / "target.md").write_text("target\n", encoding="utf-8")
            (pack / "seeds" / "alias.md").symlink_to("target.md")
            findings = lint_pack(pack)
            self.assertEqual(len(findings), 1, findings)
            self.assertIn("symlink", findings[0])
            self.assertIn("alias.md", findings[0])

    def test_runtime_symlink_under_apm_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "linky-apm"
            (pack / ".apm" / "skills").mkdir(parents=True)
            (pack / "pack.toml").write_text(
                '[pack]\nname = "linky-apm"\nversion = "0.0.1"\n',
                encoding="utf-8",
            )
            (pack / ".apm" / "skills" / "real.md").write_text("x\n", encoding="utf-8")
            (pack / ".apm" / "skills" / "link.md").symlink_to("real.md")
            findings = lint_pack(pack)
            self.assertTrue(any("symlink" in f for f in findings))

    @unittest.skipIf(
        sys.platform == "win32",
        "NTFS refuses to materialise seeds/CON.md; lint logic is OS-agnostic "
        "so POSIX coverage is sufficient",
    )
    def test_lint_all_packs_returns_per_pack_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packs_dir = Path(tmp)
            # Mirror the legacy on-disk fixture tree at runtime: a
            # `clean` pack alongside a `with_reserved` pack.
            clean = packs_dir / "clean"
            (clean / "seeds").mkdir(parents=True)
            (clean / "pack.toml").write_text(
                '[pack]\nname = "clean"\nversion = "0.0.1"\n',
                encoding="utf-8",
            )
            (clean / "seeds" / "ok.md").write_text("ok\n", encoding="utf-8")
            _materialise_with_reserved_fixture(packs_dir)
            results = lint_all_packs(packs_dir)
        self.assertIn("clean", results)
        self.assertIn("with_reserved", results)
        self.assertEqual(results["clean"], [])
        self.assertEqual(len(results["with_reserved"]), 1)

    def test_lint_skips_directories_without_pack_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packs = Path(tmp)
            (packs / "real-pack").mkdir()
            (packs / "real-pack" / "pack.toml").write_text(
                '[pack]\nname = "real-pack"\nversion = "0.0.1"\n',
                encoding="utf-8",
            )
            (packs / "not-a-pack").mkdir()  # no pack.toml
            results = lint_all_packs(packs)
            self.assertIn("real-pack", results)
            self.assertNotIn("not-a-pack", results)

    @unittest.skipIf(
        sys.platform == "win32",
        "NTFS refuses to materialise seeds/CON.md; lint logic is OS-agnostic "
        "so POSIX coverage is sufficient",
    )
    def test_cmd_lint_packs_exits_one_on_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packs_dir = Path(tmp)
            _materialise_with_reserved_fixture(packs_dir)
            args = argparse.Namespace(packs_dir=str(packs_dir))
            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = cmd_lint_packs(args)
        self.assertEqual(rc, 1)
        self.assertIn("CON.md", buf.getvalue())
        self.assertIn("violation", buf.getvalue())

    def test_findings_are_sorted_by_relpath(self) -> None:
        """Findings come back in deterministic alphabetical order so
        operators see the same first-fix-target on every run; the
        underlying `rglob("*")` is sorted before each entry is
        examined."""
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "multi-violation"
            (pack / "seeds").mkdir(parents=True)
            (pack / "pack.toml").write_text(
                '[pack]\nname = "multi-violation"\nversion = "0.0.1"\n',
                encoding="utf-8",
            )
            # Three deliberate violations across two segments. The
            # sorted relpaths are: NUL.md, alpha/CON.md, beta/PRN.md.
            (pack / "seeds" / "NUL.md").write_text("x\n", encoding="utf-8")
            (pack / "seeds" / "alpha").mkdir()
            (pack / "seeds" / "alpha" / "CON.md").write_text("x\n", encoding="utf-8")
            (pack / "seeds" / "beta").mkdir()
            (pack / "seeds" / "beta" / "PRN.md").write_text("x\n", encoding="utf-8")
            findings = lint_pack(pack)
            self.assertEqual(len(findings), 3)
            relpaths = [f.rsplit(": ", 1)[-1] for f in findings]
            self.assertEqual(relpaths, sorted(relpaths))

    def test_cmd_lint_packs_exits_zero_on_clean_packs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packs = Path(tmp)
            shutil.copytree(FIXTURES / "clean", packs / "only-clean")
            args = argparse.Namespace(packs_dir=str(packs))
            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = cmd_lint_packs(args)
            self.assertEqual(rc, 0)


class LintPackVocabTests(unittest.TestCase):
    """Per-target metadata gate (spec: lint-packs-target-vocab)."""

    def _build_skill(
        self,
        pack: Path,
        dir_name: str,
        description: str | None = "A short, single-line description.",
        frontmatter_name: str | None = None,
    ) -> Path:
        skill_dir = pack / ".apm" / "skills" / dir_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        lines = ["---"]
        if frontmatter_name is not None:
            lines.append(f"name: {frontmatter_name}")
        if description is not None:
            lines.append(f"description: {description}")
        lines.append("---")
        lines.append("Body.")
        (skill_dir / "SKILL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return skill_dir / "SKILL.md"

    def _build_agent(
        self,
        pack: Path,
        stem: str,
        description: str | None = "A short, single-line description.",
        frontmatter_name: str | None = None,
    ) -> Path:
        agents_dir = pack / ".apm" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        lines = ["---"]
        if frontmatter_name is not None:
            lines.append(f"name: {frontmatter_name}")
        if description is not None:
            lines.append(f"description: {description}")
        lines.append("model: opus")
        lines.append("---")
        lines.append("Body.")
        path = agents_dir / f"{stem}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Skill checks (AC2 — name pattern, AC3 — name length, AC4 — desc)
    # ------------------------------------------------------------------

    def test_skill_dir_name_pattern_violation_detected(self) -> None:
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            self._build_skill(pack, "Bad_Name")
            findings = lint_pack(pack, constraints=constraints)
            vocab_findings = [f for f in findings if "name does not match" in f]
        self.assertEqual(len(vocab_findings), 1, findings)
        self.assertIn("skill/Bad_Name", vocab_findings[0])
        self.assertIn("name does not match", vocab_findings[0])
        self.assertIn("binding target:", vocab_findings[0])

    def test_skill_frontmatter_name_mismatch_pattern_detected(self) -> None:
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fm-name"
            _write_minimal_pack(pack, name="vocab-fm-name")
            self._build_skill(pack, "valid-name", frontmatter_name="Bad_Name")
            findings = lint_pack(pack, constraints=constraints)
            fm_findings = [
                f for f in findings if "Bad_Name" in f and "name does not match" in f
            ]
        self.assertEqual(len(fm_findings), 1, findings)
        self.assertIn("skill/valid-name", fm_findings[0])

    def test_skill_name_length_violation_detected(self) -> None:
        constraints = _make_constraints()
        long_name = "a" + "b" * 69  # 70 chars, kebab-valid
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            self._build_skill(pack, long_name)
            findings = lint_pack(pack, constraints=constraints)
            length_findings = [f for f in findings if "name length exceeds" in f]
        self.assertEqual(len(length_findings), 1, findings)
        self.assertIn(f"name length exceeds 64 (got 70", length_findings[0])
        self.assertIn("binding target: kiro", length_findings[0])

    def test_skill_description_length_violation_detected(self) -> None:
        constraints = _make_constraints()
        long_desc = "x" * 1100
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            self._build_skill(pack, "valid-name", description=long_desc)
            findings = lint_pack(pack, constraints=constraints)
            desc_findings = [
                f for f in findings if "description length exceeds" in f
            ]
        self.assertEqual(len(desc_findings), 1, findings)
        self.assertIn("description length exceeds 1024 (got 1100", desc_findings[0])
        self.assertIn("binding target: codex, kiro", desc_findings[0])

    def test_skill_description_singleline_required(self) -> None:
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            skill_dir = pack / ".apm" / "skills" / "valid-name"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(
                "---\ndescription: >\n  folded\n  multi-line\nmodel: opus\n---\nBody.\n",
                encoding="utf-8",
            )
            findings = lint_pack(pack, constraints=constraints)
            ml_findings = [
                f for f in findings if "description must be a single-line value" in f
            ]
        self.assertEqual(len(ml_findings), 1, findings)
        self.assertIn("skill/valid-name", ml_findings[0])

    # ------------------------------------------------------------------
    # Agent checks (AC5 — name pattern + length, AC6 — desc length)
    # ------------------------------------------------------------------

    def test_agent_name_length_violation_detected(self) -> None:
        constraints = _make_constraints()
        long_stem = "a" + "b" * 69  # 70 chars
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            self._build_agent(pack, long_stem)
            findings = lint_pack(pack, constraints=constraints)
            length_findings = [
                f for f in findings if "agent/" in f and "name length exceeds" in f
            ]
        self.assertEqual(len(length_findings), 1, findings)
        self.assertIn(f"agent/{long_stem}", length_findings[0])
        self.assertIn("name length exceeds 64 (got 70", length_findings[0])

    def test_agent_description_length_violation_detected(self) -> None:
        constraints = _make_constraints()
        long_desc = "x" * 1100
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            self._build_agent(pack, "valid-agent", description=long_desc)
            findings = lint_pack(pack, constraints=constraints)
            desc_findings = [
                f for f in findings
                if "agent/" in f and "description length exceeds" in f
            ]
        self.assertEqual(len(desc_findings), 1, findings)
        self.assertIn("description length exceeds 1024 (got 1100", desc_findings[0])

    def test_agent_description_singleline_required(self) -> None:
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "vocab-fixture"
            _write_minimal_pack(pack, name="vocab-fixture")
            agents_dir = pack / ".apm" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "valid-agent.md").write_text(
                "---\ndescription: |\n  folded\nmodel: opus\n---\nBody.\n",
                encoding="utf-8",
            )
            findings = lint_pack(pack, constraints=constraints)
            ml_findings = [
                f for f in findings if "description must be a single-line value" in f
            ]
        self.assertEqual(len(ml_findings), 1, findings)
        self.assertIn("agent/valid-agent", ml_findings[0])

    # ------------------------------------------------------------------
    # Clean pack — no vocab findings
    # ------------------------------------------------------------------

    def test_clean_pack_with_skills_and_agents_has_no_vocab_findings(self) -> None:
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "clean-vocab"
            _write_minimal_pack(pack, name="clean-vocab")
            self._build_skill(pack, "good-skill", description="x" * 100)
            self._build_agent(pack, "good-agent", description="x" * 100)
            findings = lint_pack(pack, constraints=constraints)
        self.assertEqual(findings, [], findings)

    # ------------------------------------------------------------------
    # Sort invariant (AC10) — vocab + portability findings interleave
    # ------------------------------------------------------------------

    def test_findings_remain_sorted_when_vocab_and_portability_mix(self) -> None:
        constraints = _make_constraints()
        if sys.platform == "win32":
            self.skipTest(
                "NTFS refuses to materialise seeds/NUL.md; the sort invariant "
                "is OS-agnostic so POSIX coverage is sufficient"
            )
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "mix-pack"
            _write_minimal_pack(pack, name="mix-pack")
            (pack / "seeds").mkdir(parents=True, exist_ok=True)
            (pack / "seeds" / "NUL.md").write_text("x\n", encoding="utf-8")
            self._build_skill(pack, "Bad_Name")
            findings = lint_pack(pack, constraints=constraints)
            relpaths = [f.rsplit(": ", 1)[-1] for f in findings]
        self.assertEqual(relpaths, sorted(relpaths))

    @unittest.skipIf(
        sys.platform == "win32",
        "NTFS refuses to materialise seeds/NUL.md / .apm/agents/CON.md; sort "
        "invariant is OS-agnostic so POSIX coverage is sufficient",
    )
    def test_portability_findings_sort_across_subtrees_when_constraints_supplied(
        self,
    ) -> None:
        """The constraints-supplied path adds a cross-subtree sort step;
        without it, portability findings come back subtree-by-subtree
        (`seeds/` first, then `.apm/`). With it, the combined list is
        sorted by trailing relpath."""
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "cross-subtree"
            _write_minimal_pack(pack, name="cross-subtree")
            (pack / "seeds").mkdir(parents=True, exist_ok=True)
            (pack / "seeds" / "NUL.md").write_text("x\n", encoding="utf-8")
            agents_dir = pack / ".apm" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "CON.md").write_text("x\n", encoding="utf-8")
            findings = lint_pack(pack, constraints=constraints)
            relpaths = [f.rsplit(": ", 1)[-1] for f in findings]
        # `.apm/agents/CON.md` sorts before `seeds/NUL.md` alphabetically.
        # The constraints-supplied path must produce them in that order.
        self.assertEqual(relpaths, sorted(relpaths))
        self.assertGreater(len(relpaths), 1)

    def test_multi_target_tie_renders_comma_joined_binding(self) -> None:
        """When multiple targets share the binding cap (codex + kiro at
        1024), the finding renders `binding target: codex, kiro`."""
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "tie-pack"
            _write_minimal_pack(pack, name="tie-pack")
            self._build_skill(pack, "good-name", description="x" * 1100)
            findings = lint_pack(pack, constraints=constraints)
            desc_findings = [
                f for f in findings if "description length exceeds" in f
            ]
        self.assertEqual(len(desc_findings), 1, findings)
        self.assertIn("binding target: codex, kiro", desc_findings[0])

    # ------------------------------------------------------------------
    # AC11 — vocab file missing / inconsistent fails loud
    # ------------------------------------------------------------------

    def test_missing_vocab_file_fails_loud(self) -> None:
        """When neither the --packs-dir walk nor the module-ancestor
        fallback finds the vocab file, cmd_lint_packs exits non-zero
        with a stderr line naming the config file. We patch
        `_VOCAB_RELPATH` to a sentinel filename that exists nowhere so
        both walks fail deterministically."""
        from unittest.mock import patch
        from agentbundle.build import lint_packs as lp_module
        sentinel = Path("docs/contracts/__nonexistent_target_vocab__.toml")
        with tempfile.TemporaryDirectory() as tmp:
            packs_dir = Path(tmp) / "isolated" / "packs"
            packs_dir.mkdir(parents=True)
            _write_minimal_pack(packs_dir / "p", name="p")
            args = argparse.Namespace(packs_dir=str(packs_dir))
            buf = io.StringIO()
            with patch.object(lp_module, "_VOCAB_RELPATH", sentinel), \
                    redirect_stderr(buf):
                rc = cmd_lint_packs(args)
        self.assertEqual(rc, 1)
        self.assertIn("target-vocab.toml", buf.getvalue())

    def test_skill_name_multiline_refused(self) -> None:
        """A folded `name:` in frontmatter must be refused — same
        rationale as AC12 for `description:`, applied to `name:`."""
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "ml-name-pack"
            _write_minimal_pack(pack, name="ml-name-pack")
            skill_dir = pack / ".apm" / "skills" / "valid-name"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: >\n  Bad_Name\ndescription: short.\n---\nBody.\n",
                encoding="utf-8",
            )
            findings = lint_pack(pack, constraints=constraints)
            ml_findings = [
                f for f in findings
                if "name must be a single-line value" in f
            ]
        self.assertEqual(len(ml_findings), 1, findings)
        self.assertIn("skill/valid-name", ml_findings[0])

    def test_agent_name_multiline_refused(self) -> None:
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "ml-agent"
            _write_minimal_pack(pack, name="ml-agent")
            agents_dir = pack / ".apm" / "agents"
            agents_dir.mkdir(parents=True)
            (agents_dir / "valid-agent.md").write_text(
                "---\nname: |\n  Bad_Name\ndescription: short.\nmodel: opus\n---\nBody.\n",
                encoding="utf-8",
            )
            findings = lint_pack(pack, constraints=constraints)
            ml_findings = [
                f for f in findings
                if "name must be a single-line value" in f
            ]
        self.assertEqual(len(ml_findings), 1, findings)
        self.assertIn("agent/valid-agent", ml_findings[0])

    def test_loader_module_ancestor_fallback_succeeds(self) -> None:
        """The loader walks up from the supplied start; when that
        finds nothing, it falls back to walking from the module's
        own ancestor chain. Production-side this is what makes
        `cmd_lint_packs` work for an out-of-tree --packs-dir while
        still reading the in-tree vocab. Direct test of the
        fallback hit-path."""
        from agentbundle.build.lint_packs import _load_target_vocab
        with tempfile.TemporaryDirectory() as tmp:
            vocab, err = _load_target_vocab(Path(tmp))
        self.assertIsNone(err, err)
        self.assertIsNotNone(vocab)
        self.assertEqual(vocab["target"]["kiro"]["name-max-length"], 64)

    def test_skill_frontmatter_with_bom_still_checked(self) -> None:
        """A SKILL.md saved with a UTF-8 BOM must still have its
        frontmatter parsed — otherwise an over-cap description would
        slip through silently. Regression for the BOM under-counting
        risk surfaced by quality-engineer review."""
        constraints = _make_constraints()
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "bom-pack"
            _write_minimal_pack(pack, name="bom-pack")
            skill_dir = pack / ".apm" / "skills" / "good-name"
            skill_dir.mkdir(parents=True)
            long_desc = "x" * 1100
            (skill_dir / "SKILL.md").write_text(
                "﻿---\ndescription: " + long_desc + "\n---\nBody.\n",
                encoding="utf-8",
            )
            findings = lint_pack(pack, constraints=constraints)
            desc_findings = [
                f for f in findings if "description length exceeds" in f
            ]
        self.assertEqual(len(desc_findings), 1, findings)

    def _run_with_bad_vocab(self, body: str) -> tuple[int, str]:
        """Helper for AC11 refusal-branch coverage. Materialises an
        isolated tree with a controlled `target-vocab.toml`, invokes
        `cmd_lint_packs` against a minimal pack inside that tree, and
        returns `(rc, stderr_text)`. The explicit `--packs-dir` walk
        finds the tmp vocab first, so the module-ancestor fallback
        doesn't shadow the bad config under test."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "isolated"
            packs_dir = root / "packs"
            packs_dir.mkdir(parents=True)
            _write_minimal_pack(packs_dir / "p", name="p")
            vocab_dir = root / "docs" / "contracts"
            vocab_dir.mkdir(parents=True)
            (vocab_dir / "target-vocab.toml").write_text(body, encoding="utf-8")
            args = argparse.Namespace(packs_dir=str(packs_dir))
            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = cmd_lint_packs(args)
            return rc, buf.getvalue()

    def test_malformed_toml_fails_loud(self) -> None:
        rc, stderr = self._run_with_bad_vocab("not valid toml [[[\n")
        self.assertEqual(rc, 1)
        self.assertIn("failed to parse", stderr)
        self.assertIn("configuration error", stderr)

    def test_no_target_tables_fails_loud(self) -> None:
        rc, stderr = self._run_with_bad_vocab(
            '[contract]\nversion = "0.1"\n'
        )
        self.assertEqual(rc, 1)
        self.assertIn("no [target.<name>] tables", stderr)
        self.assertIn("configuration error", stderr)

    def test_missing_name_pattern_on_target_fails_loud(self) -> None:
        rc, stderr = self._run_with_bad_vocab(
            '[target.alpha]\n'
            'description-max-length = 1024\n'
            'name-max-length = 64\n'
        )
        self.assertEqual(rc, 1)
        self.assertIn("name-pattern", stderr)
        self.assertIn("configuration error", stderr)

    def test_no_description_cap_anywhere_fails_loud(self) -> None:
        rc, stderr = self._run_with_bad_vocab(
            '[target.alpha]\n'
            'name-pattern = "^[a-z][a-z0-9-]*$"\n'
            'name-max-length = 64\n'
        )
        self.assertEqual(rc, 1)
        self.assertIn("description-max-length", stderr)
        self.assertIn("configuration error", stderr)

    def test_no_name_max_length_anywhere_fails_loud(self) -> None:
        rc, stderr = self._run_with_bad_vocab(
            '[target.alpha]\n'
            'name-pattern = "^[a-z][a-z0-9-]*$"\n'
            'description-max-length = 1024\n'
        )
        self.assertEqual(rc, 1)
        self.assertIn("name-max-length", stderr)
        self.assertIn("configuration error", stderr)

    def test_portability_sort_no_constraints_also_sorts_across_subtrees(
        self,
    ) -> None:
        """The unconditional sort step at the end of `lint_pack` keeps
        the trailing-relpath ordering invariant in the no-constraints
        path too. Regression-pin: a future change that re-gates the
        sort behind `constraints is not None` would let this test
        fail loudly."""
        if sys.platform == "win32":
            self.skipTest(
                "NTFS refuses to materialise seeds/NUL.md / .apm/agents/CON.md"
            )
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "no-constraints-mix"
            _write_minimal_pack(pack, name="no-constraints-mix")
            (pack / "seeds").mkdir(parents=True, exist_ok=True)
            (pack / "seeds" / "NUL.md").write_text("x\n", encoding="utf-8")
            agents_dir = pack / ".apm" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            (agents_dir / "CON.md").write_text("x\n", encoding="utf-8")
            findings = lint_pack(pack)
            relpaths = [f.rsplit(": ", 1)[-1] for f in findings]
        self.assertEqual(relpaths, sorted(relpaths))
        self.assertGreater(len(relpaths), 1)

    def test_inconsistent_name_pattern_fails_loud(self) -> None:
        """A target-vocab.toml whose targets carry different name-pattern
        values must be refused by the loader (AC11)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "isolated"
            packs_dir = root / "packs"
            packs_dir.mkdir(parents=True)
            _write_minimal_pack(packs_dir / "p", name="p")
            vocab_dir = root / "docs" / "contracts"
            vocab_dir.mkdir(parents=True)
            (vocab_dir / "target-vocab.toml").write_text(
                '[target.alpha]\nname-pattern = "^[a-z][a-z0-9-]*$"\n'
                'description-max-length = 1024\n'
                '[target.beta]\nname-pattern = "^[A-Z][A-Z0-9-]*$"\n'
                'description-max-length = 1024\n',
                encoding="utf-8",
            )
            args = argparse.Namespace(packs_dir=str(packs_dir))
            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = cmd_lint_packs(args)
        self.assertEqual(rc, 1)
        self.assertIn("name-pattern", buf.getvalue())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(unittest.main())
