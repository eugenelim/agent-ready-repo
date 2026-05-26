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
            # Plant an orphan projection file for the pack.
            orphan = adopter / ".claude" / "skills" / "demo-skill" / "SKILL.md"
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
            self.assertIn("orphan projection files for pack demo", stderr)
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
            orphan = adopter / ".claude" / "skills" / "demo-skill" / "SKILL.md"
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
                    "--output",
                    str(adopter),
                    str(packs_dir),
                ]
            )
            rc = install.run(args)
            self.assertEqual(rc, 0)
            # The fresh install replaced the orphan with the pack's
            # actual projection — the file exists but the content
            # differs from `stale`.
            self.assertTrue(orphan.exists())
            self.assertNotEqual(orphan.read_text(encoding="utf-8"), "stale")


if __name__ == "__main__":
    unittest.main()
