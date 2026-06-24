"""Unit tests for the RFC-0012 install-time message rail at repo scope
(spec AC20-AC23, AC32) and the route-list formatting helper.

Covers:

  - ``_format_route_list`` — serial-comma + final "and" semantics:
    N=1 → "X", N=2 → "X and Y", N>=3 → "X, Y, and Z".
  - ``emitted install routes for <pack> at <route-list>`` shape under
    ``--emit-install-routes`` at repo scope.
  - ``installed: <pack> @ repo via <adapter>`` shape under the default
    per-IDE projection.
  - Orphan-projection refusal (AC22): pre-existing on-disk per-IDE
    artifacts with no state row trigger the pinned refusal.
  - ``--force`` clears orphans and proceeds (AC23).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class FormatRouteListTests(unittest.TestCase):
    """The route-list join rule pinned in AC20."""

    def test_single_route_returns_bare_string(self) -> None:
        from agentbundle.commands.install import _format_route_list

        self.assertEqual(_format_route_list(["X"]), "X")

    def test_two_routes_uses_and(self) -> None:
        """N=2 → ``X and Y`` (with surrounding spaces — load-bearing
        for the integration assertion that pins the join rule)."""
        from agentbundle.commands.install import _format_route_list

        result = _format_route_list(["X", "Y"])
        self.assertEqual(result, "X and Y")
        self.assertIn(" and ", result)

    def test_three_routes_uses_serial_comma_plus_and(self) -> None:
        """N>=3 → ``X, Y, and Z`` (serial comma + final "and"). Pins
        the rule before a third install route lands."""
        from agentbundle.commands.install import _format_route_list

        self.assertEqual(_format_route_list(["X", "Y", "Z"]), "X, Y, and Z")

    def test_four_routes(self) -> None:
        from agentbundle.commands.install import _format_route_list

        self.assertEqual(
            _format_route_list(["A", "B", "C", "D"]),
            "A, B, C, and D",
        )


class OrphanRefusalTests(unittest.TestCase):
    """AC22: refuse install when on-disk per-IDE artifacts exist with
    no state row for the pack."""

    def _make_pack(self, packs_dir: Path) -> Path:
        import textwrap

        pack_dir = packs_dir / "demo"
        pack_dir.mkdir(parents=True)
        (pack_dir / "pack.toml").write_text(
            textwrap.dedent(
                """\
                [pack]
                name = "demo"
                version = "0.1.0"
                spec-version = "0.6"

                [pack.adapter-contract]
                version = "0.7"

                [pack.install]
                default-scope = "repo"
                allowed-scopes = ["repo"]
                allowed-adapters = ["claude-code", "kiro"]
                """
            ),
            encoding="utf-8",
        )
        # Minimal skill so the projection lands something.
        skill_dir = pack_dir / ".apm" / "skills" / "demo-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: demo\n---\nBody.",
            encoding="utf-8",
        )
        return pack_dir

    def test_orphan_files_refused_without_force(self) -> None:
        import io
        from contextlib import redirect_stderr

        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            self._make_pack(packs_dir)

            adopter = tmp / "adopter"
            adopter.mkdir()
            # Plant a GENUINE orphan: a file under the skill's directory that
            # the current projection does NOT ship. Issue #190 — a file that
            # *is* a projection path (e.g. SKILL.md itself) is now companion-
            # protected, not refused. `STALE.md` matches the `demo-skill`
            # primitive-name segment so the scanner flags it, but it is not a
            # projected relpath, so the issue-#190 filter keeps it an orphan.
            orphan = adopter / ".claude" / "skills" / "demo-skill" / "STALE.md"
            orphan.parent.mkdir(parents=True)
            orphan.write_text("stale", encoding="utf-8")
            # No state row recorded.

            parser = _build_parser()
            args = parser.parse_args(
                [
                    "install",
                    "--pack",
                    "demo",
                    "--scope",
                    "repo",
                    "--output",
                    str(adopter),
                    str(packs_dir),
                ]
            )
            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = install.run(args)
            stderr = buf.getvalue()
            self.assertNotEqual(rc, 0)
            self.assertIn(
                "unrecognized files at projection paths not shipped by pack demo",
                stderr,
            )
            self.assertNotIn("prior install interrupted", stderr)
            self.assertIn("rerun with --force", stderr)

    def test_orphan_files_cleared_by_force(self) -> None:
        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            self._make_pack(packs_dir)

            adopter = tmp / "adopter"
            adopter.mkdir()
            # Genuine non-projection orphan (see the without-force test).
            orphan = adopter / ".claude" / "skills" / "demo-skill" / "STALE.md"
            orphan.parent.mkdir(parents=True)
            orphan.write_text("stale", encoding="utf-8")

            parser = _build_parser()
            args = parser.parse_args(
                [
                    "install",
                    "--pack",
                    "demo",
                    "--scope",
                    "repo",
                    "--force",
                    # `--yes` so the orphan-cleanup confirm (CLI-hygiene AC7)
                    # does not refuse on the non-TTY test stdin.
                    "--yes",
                    "--output",
                    str(adopter),
                    str(packs_dir),
                ]
            )
            rc = install.run(args)
            self.assertEqual(rc, 0)
            # `--force` removed the genuine non-projection orphan and reinstalled.
            # The crumb is gone (it is not a projected relpath, so nothing
            # re-creates it), while the pack's real projection landed.
            self.assertFalse(orphan.exists(), "--force must remove the orphan crumb")
            self.assertTrue(
                (adopter / ".claude" / "skills" / "demo-skill" / "SKILL.md").exists(),
                "the pack's real projection must land after --force reinstall",
            )

    def _setup_orphan(self, tmp: Path):
        """Plant the (c) orphan shape and return ``(packs_dir, adopter, orphan)``."""
        packs_dir = tmp / "packs"
        packs_dir.mkdir()
        self._make_pack(packs_dir)
        adopter = tmp / "adopter"
        adopter.mkdir()
        orphan = adopter / ".claude" / "skills" / "demo-skill" / "STALE.md"
        orphan.parent.mkdir(parents=True)
        orphan.write_text("stale", encoding="utf-8")
        return packs_dir, adopter, orphan

    def _argv(self, adopter: Path, packs_dir: Path, *, yes: bool = False) -> list[str]:
        argv = ["install", "--pack", "demo", "--scope", "repo", "--force"]
        if yes:
            argv.append("--yes")
        return argv + ["--output", str(adopter), str(packs_dir)]

    def test_orphan_force_confirm_lists_files_and_proceeds_on_yes(self) -> None:
        """CLI-hygiene AC6: the orphan (c) --force confirm lists the exact files
        and proceeds on a TTY 'y'."""
        import io
        from contextlib import redirect_stderr
        from unittest.mock import patch

        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir, adopter, orphan = self._setup_orphan(tmp)
            args = _build_parser().parse_args(self._argv(adopter, packs_dir))
            buf = io.StringIO()
            with patch("sys.stdin.isatty", return_value=True), \
                 patch("builtins.input", return_value="y"), \
                 redirect_stderr(buf):
                rc = install.run(args)
            stderr = buf.getvalue()
            self.assertEqual(rc, 0, stderr)
            self.assertIn("will REMOVE orphan file:", stderr)
            self.assertIn("STALE.md", stderr)
            self.assertFalse(orphan.exists(), "confirmed --force must remove the orphan")

    def test_orphan_force_confirm_decline_deletes_nothing(self) -> None:
        """CLI-hygiene AC6: declining the orphan --force confirm deletes nothing."""
        import io
        from contextlib import redirect_stderr
        from unittest.mock import patch

        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir, adopter, orphan = self._setup_orphan(tmp)
            args = _build_parser().parse_args(self._argv(adopter, packs_dir))
            buf = io.StringIO()
            with patch("sys.stdin.isatty", return_value=True), \
                 patch("builtins.input", return_value="n"), \
                 redirect_stderr(buf):
                rc = install.run(args)
            self.assertNotEqual(rc, 0)
            self.assertIn("aborted", buf.getvalue())
            self.assertTrue(orphan.exists(), "a declined --force must delete nothing")

    def test_orphan_force_non_tty_without_yes_refuses_zero_deletions(self) -> None:
        """CLI-hygiene AC7: a non-TTY orphan --force without --yes refuses and
        leaves the orphan on disk."""
        import io
        from contextlib import redirect_stderr
        from unittest.mock import patch

        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir, adopter, orphan = self._setup_orphan(tmp)
            args = _build_parser().parse_args(self._argv(adopter, packs_dir))

            def _boom(prompt=""):
                raise AssertionError("input() must not be called on a non-TTY")

            buf = io.StringIO()
            with patch("sys.stdin.isatty", return_value=False), \
                 patch("builtins.input", _boom), \
                 redirect_stderr(buf):
                rc = install.run(args)
            self.assertNotEqual(rc, 0)
            self.assertIn("--yes", buf.getvalue())
            self.assertTrue(
                orphan.exists(),
                "a non-TTY --force without --yes must delete nothing (AC7)",
            )


if __name__ == "__main__":
    unittest.main()
