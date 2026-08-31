"""Regression: the architect pack's published install commands parse.

The architect README once documented `agentbundle install architect`, which
binds `architect` to the `catalogue` positional and names no pack. That form is
still rejected, but the layer that rejects it moved: `--pack`/`--profile` is no
longer an argparse-required group, because a direct source arrives as the
positional with neither flag. The handler now enforces "exactly one of --pack,
--profile, or a direct source" and still exits 2, so the observable contract is
unchanged and this test asserts it at the command rather than at the parser.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr


class ArchitectReadmeInstallCommandTests(unittest.TestCase):
    def test_bare_install_pack_name_is_rejected(self) -> None:
        """The old defect: `agentbundle install architect` (no --pack)."""
        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        parser = _build_parser()
        # The parser accepts it now; `architect` is a candidate direct source.
        args = parser.parse_args(["install", "architect"])
        self.assertIsNone(args.pack)
        self.assertEqual(args.catalogue, "architect")

        # It is not one — no such directory, so no direct marker — and the
        # handler refuses with the usage exit code.
        captured = io.StringIO()
        with redirect_stderr(captured):
            exit_code = install.run(args)
        self.assertEqual(exit_code, 2)
        message = captured.getvalue()
        self.assertIn("--pack", message)
        self.assertIn("--profile", message)

    def test_a_directory_with_no_direct_marker_is_also_rejected(self) -> None:
        """A real directory that is neither a pack nor a direct source."""
        import tempfile

        from agentbundle.cli import _build_parser
        from agentbundle.commands import install

        with tempfile.TemporaryDirectory() as empty:
            args = _build_parser().parse_args(["install", empty])
            captured = io.StringIO()
            with redirect_stderr(captured):
                exit_code = install.run(args)
        self.assertEqual(exit_code, 2)
        self.assertIn("--pack", captured.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
