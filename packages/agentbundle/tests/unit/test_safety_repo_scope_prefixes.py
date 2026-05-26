"""Unit tests for the repo-scope path-jail widening + scan_for_pack_artifacts
helper (RFC-0012 / repo-scope-per-adapter-projection AC12-AC13, AC31).

Two surfaces:

  - ``safety.write_jailed`` accepts ``scope="repo"`` with
    ``allowed_prefixes`` populated and refuses out-of-prefix writes.
    Per-adapter coverage threads each shipped adapter's
    ``allowed-prefixes.repo`` from the v0.7 contract.
  - ``safety.scan_for_pack_artifacts`` returns every file under
    ``<root>/<prefix>/`` for each prefix; read-only.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class WriteJailedRepoScopeTests(unittest.TestCase):
    """The path-jail enforces ``allowed-prefixes.repo`` at repo scope."""

    def test_claude_code_in_prefix_write_succeeds(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            written = safety.write_jailed(
                root,
                ".claude/skills/demo/SKILL.md",
                "x",
                scope="repo",
                allowed_prefixes=[".claude/", ".agentbundle/"],
            )
            self.assertTrue(written.exists())

    def test_claude_code_out_of_prefix_write_refused(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            with self.assertRaises(safety.PathJailError):
                safety.write_jailed(
                    root,
                    ".kiro/skills/demo/SKILL.md",
                    "x",
                    scope="repo",
                    allowed_prefixes=[".claude/", ".agentbundle/"],
                )

    def test_kiro_in_prefix_write_succeeds(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            written = safety.write_jailed(
                root,
                ".kiro/agents/demo.json",
                "x",
                scope="repo",
                allowed_prefixes=[".kiro/", ".agentbundle/"],
            )
            self.assertTrue(written.exists())

    def test_codex_in_prefix_write_succeeds(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            written = safety.write_jailed(
                root,
                ".agents/skills/demo/SKILL.md",
                "x",
                scope="repo",
                allowed_prefixes=[".agents/skills/", ".agentbundle/"],
            )
            self.assertTrue(written.exists())

    def test_copilot_in_prefix_write_succeeds(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            written = safety.write_jailed(
                root,
                ".github/instructions/demo.md",
                "x",
                scope="repo",
                allowed_prefixes=[".github/instructions/"],
            )
            self.assertTrue(written.exists())

    def test_copilot_out_of_prefix_write_refused(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            with self.assertRaises(safety.PathJailError):
                safety.write_jailed(
                    root,
                    ".kiro/skills/demo/SKILL.md",
                    "x",
                    scope="repo",
                    allowed_prefixes=[".github/instructions/"],
                )

    def test_trailing_slash_required(self) -> None:
        """Defence-in-depth: the schema enforces trailing slashes; the
        runtime jail also refuses a prefix list missing one."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            with self.assertRaises(safety.PathJailError):
                safety.write_jailed(
                    root,
                    ".claude/skills/demo/SKILL.md",
                    "x",
                    scope="repo",
                    allowed_prefixes=[".claude"],  # no trailing slash
                )

    def test_repo_scope_with_none_prefixes_skips_check(self) -> None:
        """Backward-compat: ``scope="repo"`` with ``allowed_prefixes=None``
        is the pre-RFC-0012 shape — the per-prefix check is skipped and
        only the bare jail-under-root applies."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            # Write to an arbitrary path; no prefix-check refusal.
            written = safety.write_jailed(
                root,
                "any/legacy/path.txt",
                "x",
                scope="repo",
                allowed_prefixes=None,
            )
            self.assertTrue(written.exists())


class ScanForPackArtifactsTests(unittest.TestCase):
    """``safety.scan_for_pack_artifacts`` walks declared prefixes."""

    def test_empty_root_returns_empty_list(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            self.assertEqual(
                safety.scan_for_pack_artifacts(Path(raw), [".claude/"]),
                [],
            )

    def test_returns_every_file_under_prefix(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".claude" / "skills" / "demo").mkdir(parents=True)
            (root / ".claude" / "skills" / "demo" / "SKILL.md").write_text("x")
            (root / ".claude" / "agents").mkdir(parents=True)
            (root / ".claude" / "agents" / "a.md").write_text("y")
            found = safety.scan_for_pack_artifacts(root, [".claude/"])
            relpaths = sorted(p.relative_to(root).as_posix() for p in found)
            self.assertEqual(
                relpaths,
                [".claude/agents/a.md", ".claude/skills/demo/SKILL.md"],
            )

    def test_multiple_prefixes(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".claude" / "skills").mkdir(parents=True)
            (root / ".claude" / "skills" / "x.md").write_text("x")
            (root / ".agentbundle").mkdir(parents=True)
            (root / ".agentbundle" / "state.toml").write_text("y")
            found = safety.scan_for_pack_artifacts(
                root, [".claude/", ".agentbundle/"]
            )
            self.assertEqual(len(found), 2)

    def test_missing_prefix_dirs_silently_skipped(self) -> None:
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".claude" / "skills").mkdir(parents=True)
            (root / ".claude" / "skills" / "x.md").write_text("x")
            # .kiro/ doesn't exist — skipped, not an error.
            found = safety.scan_for_pack_artifacts(
                root, [".claude/", ".kiro/"]
            )
            self.assertEqual(len(found), 1)

    def test_read_only_no_state_mutation(self) -> None:
        """Walking the tree must not create or modify any files."""
        from agentbundle import safety

        with TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".claude" / "skills").mkdir(parents=True)
            (root / ".claude" / "skills" / "x.md").write_text("x")
            before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
            safety.scan_for_pack_artifacts(root, [".claude/"])
            after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
