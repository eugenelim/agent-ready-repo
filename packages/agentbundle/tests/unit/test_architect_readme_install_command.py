"""Regression: the architect pack's published install commands parse.

The architect README once documented `agentbundle install architect`, which
the current parser rejects — `architect` binds to the `catalogue` positional
and the required `--pack`/`--profile` group is unsatisfied. This test locks
every `agentbundle …` command in the README to the live parser so the invalid
form cannot silently return, and pins the bare form as rejected.
"""

from __future__ import annotations

import re
import shlex
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ARCHITECT_README = REPO_ROOT / "packs" / "architect" / "README.md"


def _agentbundle_commands(markdown: str) -> list[list[str]]:
    """Extract `agentbundle …` invocations from fenced code blocks.

    Returns each as an argv list (with the leading `agentbundle` dropped).
    Comment lines (`# …`) are skipped; the `<catalogue>` placeholder is a
    plain token that parses like any positional.
    """
    commands: list[list[str]] = []
    in_fence = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence or not stripped.startswith("agentbundle "):
            continue
        # Drop a trailing inline comment if present.
        argv = shlex.split(stripped, comments=True)
        commands.append(argv[1:])  # drop "agentbundle"
    return commands


class ArchitectReadmeInstallCommandTests(unittest.TestCase):
    def test_readme_documents_at_least_one_install_command(self) -> None:
        commands = _agentbundle_commands(ARCHITECT_README.read_text())
        install = [c for c in commands if c and c[0] == "install"]
        self.assertTrue(
            install,
            "architect README should document at least one `agentbundle install` command",
        )

    def test_every_documented_agentbundle_command_parses(self) -> None:
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        for argv in _agentbundle_commands(ARCHITECT_README.read_text()):
            with self.subTest(argv=argv):
                # A parse error raises SystemExit via argparse; a clean parse
                # returns a namespace. We only assert it parses.
                try:
                    parser.parse_args(argv)
                except SystemExit:  # pragma: no cover - failure path
                    self.fail(
                        f"architect README documents an unparseable command: "
                        f"agentbundle {' '.join(argv)}"
                    )

    def test_bare_install_pack_name_is_rejected(self) -> None:
        """The old defect: `agentbundle install architect` (no --pack)."""
        from agentbundle.cli import _build_parser

        parser = _build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["install", "architect"])

    def test_readme_uses_pack_flag_form(self) -> None:
        body = ARCHITECT_README.read_text()
        self.assertRegex(
            body,
            re.compile(r"agentbundle install --pack architect", re.MULTILINE),
            "architect README should use the `--pack architect` install form",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
