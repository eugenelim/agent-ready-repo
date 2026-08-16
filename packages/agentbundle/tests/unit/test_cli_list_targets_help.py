"""`list-targets` help text must name exactly the registry's adapters.

The help string is hand-written rather than generated: importing
`agentbundle.render` to build it would put ~430 ms on every CLI invocation,
including `agentbundle --version`, against the explicit lazy-import design in
`cli.py`. This test is what makes the hand-written copy safe — it fails the
moment an adapter is added, removed, or renamed in the registry.

It caught the state this test was written for: the string named six targets
("claude-code, kiro-ide, kiro-cli, kiro (deprecated → kiro-ide), copilot,
codex") while the registry held eight, so `cursor` and `gemini` were invisible
to anyone reading `--help`.
"""

from __future__ import annotations

import re

from agentbundle.cli import _build_parser
from agentbundle.render import list_adapters


def _list_targets_help() -> str:
    """The help string argparse holds for the `list-targets` subcommand."""
    parser = _build_parser()
    for action in parser._actions:  # noqa: SLF001 — argparse exposes no public API
        if not hasattr(action, "choices") or not action.choices:
            continue
        if not isinstance(action.choices, dict):
            continue
        if "list-targets" in action.choices:
            for sub_action in action._get_subactions():  # noqa: SLF001
                if sub_action.dest == "list-targets":
                    return sub_action.help or ""
    raise AssertionError("list-targets subcommand not found on the parser")


def test_list_targets_help_matches_registry() -> None:
    help_text = _list_targets_help()
    named = set(re.findall(r"[a-z][a-z0-9_]*", help_text))
    registry = set(list_adapters())

    missing = registry - named
    assert not missing, (
        f"list-targets help omits registry adapters: {sorted(missing)}. "
        "Add them to the help string in cli.py."
    )

    # Guard the other direction: a name that looks like an adapter but is not
    # in the registry means the help advertises something the CLI cannot do.
    prose = {
        "list", "targets", "adapter", "adapters", "the", "cli", "supports",
        "deprecated",
    }
    invented = {n for n in named - registry - prose if "_" in n or n.startswith("kiro")}
    assert not invented, (
        f"list-targets help names non-registry adapters: {sorted(invented)}."
    )


def test_every_registry_adapter_is_named_verbatim() -> None:
    """Substring containment is not enough — `kiro` must not stand in for
    `kiro_cli`. Each adapter appears as a whole token."""
    help_text = _list_targets_help()
    tokens = set(re.findall(r"[a-z][a-z0-9_]*", help_text))
    for adapter in list_adapters():
        assert adapter in tokens, f"{adapter!r} is not named as a whole token"
