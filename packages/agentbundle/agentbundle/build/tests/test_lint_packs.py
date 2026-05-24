"""Windows-portability lint: catches symlinks and Windows-poisonous
names in pack content before they reach a release artefact."""

from __future__ import annotations

import argparse
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from agentbundle.build.lint_packs import (
    cmd_lint_packs,
    lint_all_packs,
    lint_pack,
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


if __name__ == "__main__":  # pragma: no cover
    sys.exit(unittest.main())
