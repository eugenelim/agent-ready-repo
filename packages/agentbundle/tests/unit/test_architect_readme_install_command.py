"""Regression: the architect pack's published install commands parse.

The architect README once documented `agentbundle install architect`, which
the current parser rejects — `architect` binds to the `catalogue` positional
and the required `--pack`/`--profile` group is unsatisfied. This test locks
every `agentbundle …` command in the README to the live parser so the invalid
form cannot silently return, and pins the bare form as rejected.
"""

from __future__ import annotations

import unittest


class ArchitectReadmeInstallCommandTests(unittest.TestCase):
    def test_bare_install_pack_name_is_rejected(self) -> None:
        """The old defect: `agentbundle install architect` (no --pack)."""
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["install", "architect"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
