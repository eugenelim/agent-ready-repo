"""Architect README install-command checks."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
ARCHITECT_README = PACK_ROOT / "README.md"


def _agentbundle_commands(markdown: str) -> list[list[str]]:
    commands: list[list[str]] = []
    in_fence = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence or not stripped.startswith("agentbundle "):
            continue
        commands.append(shlex.split(stripped, comments=True)[1:])
    return commands


def test_readme_documents_at_least_one_install_command() -> None:
    commands = _agentbundle_commands(ARCHITECT_README.read_text(encoding="utf-8"))
    assert any(command and command[0] == "install" for command in commands)


def test_every_documented_agentbundle_command_parses() -> None:
    from agentbundle.cli import _build_parser

    parser = _build_parser()
    for argv in _agentbundle_commands(ARCHITECT_README.read_text(encoding="utf-8")):
        parser.parse_args(argv)


def test_readme_uses_pack_flag_form() -> None:
    body = ARCHITECT_README.read_text(encoding="utf-8")
    assert re.search(r"agentbundle install --pack architect", body, re.MULTILINE)
