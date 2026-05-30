"""T3 (issue #190 Finding 3): `--force` help text documents orphan/file removal.

The runtime orphan message tells users to rerun with `--force` to remove on-disk
files, so the `--force` help string must disclose that file-removing behaviour —
not document only the cross-scope-conflict bypass. Walk `parser._actions`
structurally so a CPython internal shuffle doesn't silently break the test.
"""

from __future__ import annotations

import argparse

from agentbundle.cli import _build_parser


def _install_force_help() -> str:
    parser = _build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            install = action.choices["install"]
            for a in install._actions:
                if a.dest == "force":
                    return a.help or ""
    raise AssertionError("install --force action not found")


def test_force_help_mentions_file_removal() -> None:
    help_text = _install_force_help().lower()
    assert "remove" in help_text, (
        "--force help must disclose that it removes on-disk orphan files"
    )
    # Not solely the cross-scope-conflict bypass — the removal behaviour is named.
    assert "projection paths" in help_text or "leftover" in help_text
