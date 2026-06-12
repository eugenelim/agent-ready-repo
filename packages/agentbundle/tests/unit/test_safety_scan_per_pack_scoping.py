"""Per-pack scoping for ``safety.scan_for_pack_artifacts``.

The pre-2026-05-26 helper was adapter-prefix scoped — it walked every
file under each ``<root>/<prefix>/`` and returned them all. The
AC24(c) orphan-recovery trigger consumed this list, which produced a
**cross-pack false positive**: pack A's orphan files would surface
when installing pack B, with AC24(c)'s stderr line claiming "for pack
B" but citing pack A's paths.

This module covers the tightening: when callers pass ``pack_dir`` and
``pack_name``, the scan narrows to files whose path under an adapter
prefix either (a) shares a segment with a primitive name walked from
``<pack_dir>/.apm/<type>/``, or (b) has a file-stem equal to
``pack_name`` (a flat single-file-per-pack projection shape,
illustrated below as ``.github/instructions/<pack>.md``; note copilot
no longer emits instruction files post docs/specs/copilot-skills-and-web —
its skills are directory trees matched by branch (a) — so branch (b) is
a general flat-file heuristic, not copilot-specific). When the kwargs are
omitted the helper preserves the legacy behaviour for back-compat with any
external caller.
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def _make_pack_source(
    packs_dir: Path,
    *,
    name: str,
    skills: list[str] | None = None,
    agents: list[str] | None = None,
) -> Path:
    """Materialise a minimal pack source tree at ``packs_dir/<name>/.apm/``."""
    pack_dir = packs_dir / name
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        textwrap.dedent(
            f"""\
            [pack]
            name = "{name}"
            version = "0.1.0"

            [pack.adapter-contract]
            version = "0.7"
            """
        ),
        encoding="utf-8",
    )
    apm = pack_dir / ".apm"
    apm.mkdir()
    for skill_name in (skills or []):
        skill_dir = apm / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\ndescription: x\n---\nBody.",
            encoding="utf-8",
        )
    for agent_name in (agents or []):
        agents_dir = apm / "agents"
        agents_dir.mkdir(exist_ok=True)
        (agents_dir / f"{agent_name}.md").write_text(
            "agent body", encoding="utf-8"
        )
    return pack_dir


def _plant(root: Path, relpath: str, content: str = "x") -> Path:
    """Plant a file at ``root/<relpath>``; create parent dirs as needed."""
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


class PerPackScopingTests(unittest.TestCase):
    """``pack_dir`` + ``pack_name`` kwargs narrow the scan to
    pack-owned artifacts."""

    def test_legacy_mode_returns_every_file_under_prefix(self) -> None:
        """Without ``pack_dir``/``pack_name``, the helper preserves
        adapter-prefix-only scoping for back-compat."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            adopter = Path(raw)
            _plant(adopter, ".claude/skills/apack-skill/SKILL.md")
            _plant(adopter, ".claude/skills/bpack-skill/SKILL.md")

            result = safety.scan_for_pack_artifacts(adopter, [".claude/"])
            rels = sorted(p.relative_to(adopter).as_posix() for p in result)
            self.assertEqual(
                rels,
                [
                    ".claude/skills/apack-skill/SKILL.md",
                    ".claude/skills/bpack-skill/SKILL.md",
                ],
            )

    def test_per_pack_scoping_returns_only_own_primitives(self) -> None:
        """The load-bearing case: pack A's orphans must NOT surface
        when scanning for pack B."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Pack A's orphan under the same adapter prefix.
            _plant(adopter, ".claude/skills/apack-skill/SKILL.md")
            # Pack B's own orphan (if any).
            _plant(adopter, ".claude/skills/bpack-skill/SKILL.md")

            result = safety.scan_for_pack_artifacts(
                adopter, [".claude/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            rels = sorted(p.relative_to(adopter).as_posix() for p in result)
            self.assertEqual(
                rels, [".claude/skills/bpack-skill/SKILL.md"],
                f"pack-A's orphan leaked into pack-B's scan: {rels!r}",
            )

    def test_cross_pack_clean_install_returns_empty(self) -> None:
        """Pack B is greenfield. Pack A has orphans under the same
        adapter prefix. Per-pack scan for B returns empty — the AC24(c)
        cross-pack false positive is fixed."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Only pack A's orphan present.
            _plant(adopter, ".claude/skills/apack-skill/SKILL.md")
            _plant(adopter, ".claude/agents/some-other-agent.md")

            result = safety.scan_for_pack_artifacts(
                adopter, [".claude/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            self.assertEqual(
                result, [],
                f"cross-pack false positive: {[str(p) for p in result]!r}",
            )

    def test_copilot_stem_match(self) -> None:
        """Copilot projects every pack to a single file at
        ``.github/instructions/<pack>.md``. The per-pack scan picks
        this up via ``pack_name`` matching the file stem."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Copilot-shaped artifact for pack B.
            _plant(adopter, ".github/instructions/bpack.md")
            # And one belonging to pack A (different stem).
            _plant(adopter, ".github/instructions/apack.md")

            result = safety.scan_for_pack_artifacts(
                adopter, [".github/instructions/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            rels = sorted(p.relative_to(adopter).as_posix() for p in result)
            self.assertEqual(
                rels, [".github/instructions/bpack.md"],
                f"copilot stem match failed: {rels!r}",
            )

    def test_codex_projection_matches_primitive_segment(self) -> None:
        """Codex projects to ``.agents/skills/<skill>/...`` — no
        ``skills/`` segment under the prefix root. Per-pack scoping
        must match the primitive segment, not require ``skills/``."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Codex-shaped projection (prefix ends in skills/, so
            # the relpath under the prefix is just <skill>/SKILL.md).
            _plant(adopter, ".agents/skills/bpack-skill/SKILL.md")
            _plant(adopter, ".agents/skills/apack-skill/SKILL.md")

            result = safety.scan_for_pack_artifacts(
                adopter, [".agents/skills/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            rels = sorted(p.relative_to(adopter).as_posix() for p in result)
            self.assertEqual(
                rels, [".agents/skills/bpack-skill/SKILL.md"],
                f"codex primitive-segment match failed: {rels!r}",
            )

    def test_multiple_primitive_types(self) -> None:
        """A pack with skills AND agents has both surfaces' primitives
        in ``pack-owned-names``; both shapes get matched."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(
                packs, name="bpack",
                skills=["bpack-skill"],
                agents=["bpack-agent"],
            )
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant(adopter, ".claude/skills/bpack-skill/SKILL.md")
            _plant(adopter, ".claude/agents/bpack-agent.md")
            _plant(adopter, ".claude/skills/foreign-skill/SKILL.md")

            result = safety.scan_for_pack_artifacts(
                adopter, [".claude/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            rels = sorted(p.relative_to(adopter).as_posix() for p in result)
            self.assertEqual(
                rels,
                [".claude/agents/bpack-agent.md",
                 ".claude/skills/bpack-skill/SKILL.md"],
            )

    def test_pack_with_no_apm_directory_only_matches_pack_name(self) -> None:
        """A pack with no ``.apm/`` directory has only its pack name in
        the owned-names set — so only the Copilot single-file shape can
        match. Other adapters return empty."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            # No skills/agents → empty .apm/ → only pack_name in set.
            pack_dir = packs / "bpack"
            pack_dir.mkdir()
            (pack_dir / "pack.toml").write_text(
                '[pack]\nname = "bpack"\nversion = "0.1.0"\n',
                encoding="utf-8",
            )
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant(adopter, ".github/instructions/bpack.md")
            _plant(adopter, ".claude/skills/foreign-skill/SKILL.md")

            # Copilot shape: matches.
            copilot = safety.scan_for_pack_artifacts(
                adopter, [".github/instructions/"],
                pack_dir=pack_dir, pack_name="bpack",
            )
            self.assertEqual(
                [p.relative_to(adopter).as_posix() for p in copilot],
                [".github/instructions/bpack.md"],
            )
            # Claude-shape: no match (no primitive directories to match
            # against, and "bpack" doesn't appear in the foreign path).
            claude = safety.scan_for_pack_artifacts(
                adopter, [".claude/"],
                pack_dir=pack_dir, pack_name="bpack",
            )
            self.assertEqual(claude, [])


class CrossPackNameCollisionTests(unittest.TestCase):
    """Regression pin: a foreign pack's primitive named after pack B's
    pack-name must NOT match pack B's per-pack scan. The bare
    pack-name segment / stem rule (pre-refactor) admitted this false
    positive; the refactored matcher restricts pack-name matching to
    Copilot's depth-1 file shape only."""

    def test_foreign_primitive_named_after_pack_name_does_not_match(self) -> None:
        """Pack A ships a hook called ``bpack.py`` (same stem as pack
        B's pack-name). At claude-code projection that lands at
        ``.claude/hooks/bpack.py``. Pack B's per-pack scan must NOT
        return this file — it belongs to pack A."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            # Pack B with its own primitives (no name collision with
            # the foreign file).
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Foreign pack A's hook named after pack B's pack-name.
            _plant(adopter, ".claude/hooks/bpack.py", content="foreign-hook")

            result = safety.scan_for_pack_artifacts(
                adopter, [".claude/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            self.assertEqual(
                result, [],
                "cross-pack name collision matched pack B's scan; "
                "the depth-restricted stem rule isn't holding",
            )

    def test_foreign_primitive_segment_named_after_pack_name(self) -> None:
        """Same shape but with a directory segment: pack A ships a
        skill directory named ``bpack`` projecting to
        ``.claude/skills/bpack/SKILL.md``. Pack B's primitive_names
        set excludes the pack-name itself (by construction), so this
        does not match either."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Foreign skill directory named after pack B.
            _plant(adopter, ".claude/skills/bpack/SKILL.md", content="foreign")

            result = safety.scan_for_pack_artifacts(
                adopter, [".claude/"],
                pack_dir=packs / "bpack", pack_name="bpack",
            )
            self.assertEqual(
                result, [],
                "cross-pack segment-named-after-pack-name matched; "
                "primitive_names should not include pack_name itself",
            )


class CollectPackOwnedNamesTests(unittest.TestCase):
    """Direct coverage for the private helper. The public scan tests
    above exercise it indirectly via the full filter pipeline; this
    class pins the helper's own shape so a refactor that loosens the
    primitive-vs-pack-name split doesn't slip through."""

    def test_returns_primitive_names_and_pack_name_separately(self) -> None:
        from agentbundle.safety import _collect_pack_owned_names

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(
                packs, name="bpack",
                skills=["bpack-skill"],
                agents=["bpack-agent"],
            )
            primitives, stem = _collect_pack_owned_names(
                packs / "bpack", "bpack"
            )
            self.assertEqual(primitives, {"bpack-skill", "bpack-agent"})
            self.assertEqual(stem, "bpack")
            self.assertNotIn(
                "bpack", primitives,
                "primitive_names must not include pack_name — that's "
                "what enabled the cross-pack collision regression",
            )

    def test_skips_dunder_and_dotfile_children(self) -> None:
        """__pycache__ and .DS_Store under .apm/<type>/ must not pollute
        the owned-names set."""
        from agentbundle.safety import _collect_pack_owned_names

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs = tmp / "packs"
            packs.mkdir()
            _make_pack_source(packs, name="bpack", skills=["bpack-skill"])
            # Plant noise under .apm/skills/.
            (packs / "bpack" / ".apm" / "skills" / "__pycache__").mkdir()
            (packs / "bpack" / ".apm" / "skills" / ".DS_Store").write_text("")

            primitives, _ = _collect_pack_owned_names(
                packs / "bpack", "bpack"
            )
            self.assertEqual(primitives, {"bpack-skill"})

    def test_rfc_0013_primitive_types_are_collected(self) -> None:
        """RFC-0013 added ``shared-libs`` and ``adapter-root-bins`` to
        the contract's primitive set. The catalogue-broker pack
        projects load-bearing files under those types (e.g.
        ``adapter-root-bins/sso-broker.py`` → ``.agentbundle/bin/sso-broker.py``);
        if ``_PACK_PRIMITIVE_TYPES`` misses either type, the
        AC22/AC24(c) orphan scan silently returns empty on a real
        partial-write of that pack."""
        from agentbundle.safety import _collect_pack_owned_names

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack_dir = tmp / "broker"
            apm = pack_dir / ".apm"
            (apm / "shared-libs").mkdir(parents=True)
            (apm / "shared-libs" / "credentials_shim.py").write_text("x")
            (apm / "adapter-root-bins").mkdir(parents=True)
            (apm / "adapter-root-bins" / "sso-broker.py").write_text("x")

            primitives, _ = _collect_pack_owned_names(pack_dir, "broker")
            self.assertIn(
                "credentials_shim", primitives,
                "shared-libs primitive not collected; RFC-0013 type "
                "missing from _PACK_PRIMITIVE_TYPES",
            )
            self.assertIn(
                "sso-broker", primitives,
                "adapter-root-bins primitive not collected; RFC-0013 "
                "type missing from _PACK_PRIMITIVE_TYPES",
            )

    def test_no_apm_directory_returns_empty_primitives(self) -> None:
        from agentbundle.safety import _collect_pack_owned_names

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack_dir = tmp / "bpack"
            pack_dir.mkdir()
            # No .apm/ directory.
            primitives, stem = _collect_pack_owned_names(pack_dir, "bpack")
            self.assertEqual(primitives, set())
            self.assertEqual(stem, "bpack")


if __name__ == "__main__":
    unittest.main()
