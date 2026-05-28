"""Tests for `agentbundle config` argparse surface.

Asserts structurally — walking `parser._actions` for
`argparse._SubParsersAction` — so a CPython internal-attr shuffle
doesn't quietly break the test.
"""

from __future__ import annotations

import argparse

from agentbundle.cli import _build_parser


def _find_subparsers_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    raise AssertionError("no _SubParsersAction found on parser")


def test_top_level_lists_config() -> None:
    parser = _build_parser()
    sub = _find_subparsers_action(parser)
    assert "config" in sub.choices


def test_config_subparser_has_four_actions() -> None:
    parser = _build_parser()
    sub = _find_subparsers_action(parser)
    config = sub.choices["config"]
    sub_actions = _find_subparsers_action(config) if any(
        isinstance(a, argparse._SubParsersAction) for a in config._actions
    ) else None
    # `config` uses a positional `choices=` argument, NOT sub-subparsers.
    # Find the positional action whose dest is `config_action`.
    positional = None
    for action in config._actions:
        if getattr(action, "dest", None) == "config_action":
            positional = action
            break
    assert positional is not None, "config_action positional not found"
    assert tuple(positional.choices) == ("get", "set", "unset", "path")
