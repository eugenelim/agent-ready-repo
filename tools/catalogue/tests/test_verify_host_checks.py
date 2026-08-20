"""Tests for the repository-local catalogue leak checker."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[2]
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS / "catalogue"))
sys.path.insert(0, str(TOOLS / "repo"))

import build_gate_chain  # noqa: E402
import verify_host_checks  # noqa: E402


class HostCheckFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        (self.root / "packs").mkdir()

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def write_seed(
        self,
        content: str | bytes,
        relative_path: str = "AGENTS.md",
    ) -> Path:
        pack = self.root / "packs" / "seed-test-pack"
        (pack / "seeds").mkdir(parents=True, exist_ok=True)
        (pack / "pack.toml").write_text(
            '[pack]\nname = "seed-test-pack"\nversion = "0.1.0"\nlint-seeds = true\n',
            encoding="utf-8",
        )
        target = pack / "seeds" / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    def write_apm(self, content: str) -> Path:
        target = self.root / "packs" / "core" / ".apm" / "skills" / "test" / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def run_check(self) -> tuple[int, str]:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = verify_host_checks.main(["--root", str(self.root)])
        return result, stderr.getvalue()


class TestHostCheckDetectsPattern(HostCheckFixture):
    def test_seed_patterns_are_detected(self) -> None:
        for trigger in (
            "agent-ready-repo",
            "RFC-0042",
            "K-0003",
            "distribution-adapters",
        ):
            with self.subTest(trigger=trigger):
                self.write_seed(
                    f"# AGENTS.md\nA monorepo for `<project-name>` — contains {trigger}\n"
                )
                result, stderr = self.run_check()
                self.assertEqual(result, 1)
                self.assertIn("leaked", stderr)

    def test_non_markdown_seed_patterns_are_detected(self) -> None:
        self.write_seed(
            'description = "copied from agent-ready-repo"\n',
            "workspace.toml",
        )

        result, stderr = self.run_check()

        self.assertEqual(result, 1)
        self.assertIn("packs/seed-test-pack/seeds/workspace.toml:1", stderr)
        self.assertIn("leaked catalogue name", stderr)

    def test_core_apm_patterns_are_detected(self) -> None:
        for trigger in ("agent-ready-repo", "RFC-0042", "K-0003"):
            with self.subTest(trigger=trigger):
                self.write_apm(trigger)
                result, stderr = self.run_check()
                self.assertEqual(result, 1)
                self.assertIn("packs/core/.apm/skills", stderr)

    def test_other_pack_apm_is_outside_the_host_scope(self) -> None:
        target = self.root / "packs" / "other" / ".apm" / "skills" / "test" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("agent-ready-repo", encoding="utf-8")
        result, _ = self.run_check()
        self.assertEqual(result, 0)


class TestSeedExemptions(HostCheckFixture):
    def test_fenced_content_is_exempt(self) -> None:
        self.write_seed("# AGENTS.md\n<project-name>\n```\nagent-ready-repo\n```\n")
        result, stderr = self.run_check()
        self.assertEqual(result, 0, stderr)

    def test_sentinel_exempts_next_content_line(self) -> None:
        self.write_seed(
            "# AGENTS.md\n<project-name>\n"
            "<!-- seed-content-lint-ignore: example -->\n"
            "[RFC-0013](rfc/0013-example.md)\n"
        )
        result, stderr = self.run_check()
        self.assertEqual(result, 0, stderr)


class TestHostCheckFilesystemSafety(HostCheckFixture):
    def test_dangling_packs_root_is_refused(self) -> None:
        packs = self.root / "packs"
        packs.rmdir()
        try:
            packs.symlink_to("missing-packs", target_is_directory=True)
        except OSError:
            self.skipTest("symlinks not available")

        result, stderr = self.run_check()

        self.assertEqual(result, 1)
        self.assertIn("not a real directory", stderr)

    def test_linked_pack_is_refused(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.root / "packs" / "linked").symlink_to(outside)
        except OSError:
            self.skipTest("symlinks not available")
        result, stderr = self.run_check()
        self.assertEqual(result, 1)
        self.assertIn("linked pack", stderr)

    def test_linked_skill_root_is_refused(self) -> None:
        core = self.root / "packs" / "core"
        core.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (core / ".apm").symlink_to(outside)
        except OSError:
            self.skipTest("symlinks not available")
        result, stderr = self.run_check()
        self.assertEqual(result, 1)
        self.assertIn("not a real directory", stderr)

    def test_dangling_manifest_is_refused(self) -> None:
        pack = self.root / "packs" / "seed-test-pack"
        pack.mkdir()
        try:
            (pack / "pack.toml").symlink_to("missing.toml")
        except OSError:
            self.skipTest("symlinks not available")

        result, stderr = self.run_check()

        self.assertEqual(result, 1)
        self.assertIn("not a regular file", stderr)

    def test_dangling_seed_root_is_refused(self) -> None:
        pack = self.root / "packs" / "seed-test-pack"
        pack.mkdir()
        (pack / "pack.toml").write_text(
            '[pack]\nname = "seed-test-pack"\nversion = "0.1.0"\nlint-seeds = true\n',
            encoding="utf-8",
        )
        try:
            (pack / "seeds").symlink_to("missing-seeds", target_is_directory=True)
        except OSError:
            self.skipTest("symlinks not available")

        result, stderr = self.run_check()

        self.assertEqual(result, 1)
        self.assertIn("not a real directory", stderr)

    def test_hardlinked_seed_is_refused(self) -> None:
        target = self.write_seed("# AGENTS.md\n<project-name>\n")
        alias = target.with_name("ALIAS.md")
        try:
            os.link(target, alias)
        except OSError:
            self.skipTest("hard links not available")
        result, stderr = self.run_check()
        self.assertEqual(result, 1)
        self.assertIn("hard link", stderr)

    def test_invalid_utf8_is_refused(self) -> None:
        self.write_seed(b"\xff\xfe")
        result, stderr = self.run_check()
        self.assertEqual(result, 1)
        self.assertIn("invalid UTF-8", stderr)

    def test_junction_like_directory_is_refused_before_traversal(self) -> None:
        seed_root = self.root / "packs" / "seed-test-pack" / "seeds"
        seed_root.mkdir(parents=True)
        (self.root / "packs" / "seed-test-pack" / "pack.toml").write_text(
            '[pack]\nname = "seed-test-pack"\nversion = "0.1.0"\nlint-seeds = true\n',
            encoding="utf-8",
        )
        junction = seed_root / "junction"
        junction.mkdir()
        with mock.patch.object(
            verify_host_checks,
            "_path_is_junction",
            side_effect=lambda path: path.name == "junction",
        ):
            result, stderr = self.run_check()
        self.assertEqual(result, 1)
        self.assertIn("linked entry", stderr)


class TestGateChainWiring(unittest.TestCase):
    def test_checker_and_its_tests_are_runtime_steps(self) -> None:
        seen: list[list[str]] = []

        def fake_run(argv, check=False, env=None, cwd=None, **kwargs):
            seen.append(list(argv))
            return mock.Mock(returncode=0, stdout="t::a\n" * 200, stderr="")

        with mock.patch.object(build_gate_chain.subprocess, "run", fake_run):
            result = build_gate_chain.build_check(
                argparse.Namespace(packs_dir="packs", output_dir="dist")
            )
        self.assertEqual(result, 0)
        rendered = [" ".join(argv) for argv in seen]
        self.assertTrue(any("test_verify_host_checks.py" in argv for argv in rendered))
        self.assertTrue(any("verify_host_checks.py" in argv for argv in rendered))


if __name__ == "__main__":
    unittest.main()
