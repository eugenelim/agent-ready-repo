"""Cases for the shared parser-backed namespace fixture builder.

`cli_namespace` exists so command tests stop hand-rolling partial namespaces.
A builder that silently produced a thinner namespace than the CLI would be
worse than the hand-rolled fixtures it replaces — it would look principled and
still hide the same class of defect — so these cases pin what it supplies.
"""

from __future__ import annotations

import argparse

import pytest

from tests._support import cli_namespace


def test_namespace_carries_defaults_the_caller_never_mentioned() -> None:
    """Parsing supplies every default the subcommand declares."""
    namespace = cli_namespace("validate", "some/pack")

    assert namespace.pack_path == "some/pack"
    # Neither appears in the call; both are read unconditionally by
    # `commands.validate.run`.
    assert namespace.strict is False
    assert namespace.format == "text"


def test_namespace_is_strictly_richer_than_a_hand_rolled_one() -> None:
    """The gap this builder closes, stated as a comparison.

    Asserted differentially rather than as a bare attribute count: a count
    would still pass if the builder and the hand-rolled fixture drifted apart
    in different directions.
    """
    built = set(vars(cli_namespace("validate", "some/pack")))
    hand_rolled = set(vars(argparse.Namespace(pack_path="some/pack")))

    assert hand_rolled < built
    assert {"strict", "format"} <= built - hand_rolled


def test_overrides_apply_after_parsing() -> None:
    """Private attributes no flag can express are still settable."""
    namespace = cli_namespace("validate", "some/pack", _user_config="sentinel")

    assert namespace._user_config == "sentinel"
    assert namespace.format == "text"


def test_overrides_can_replace_a_parsed_value() -> None:
    """An override wins over the parsed value, so callers keep full control."""
    namespace = cli_namespace("validate", "some/pack", "--format", "json", format="text")

    assert namespace.format == "text"


def test_a_flag_the_parser_does_not_declare_is_refused() -> None:
    """A renamed or deleted flag surfaces here instead of passing quietly."""
    with pytest.raises(SystemExit):
        cli_namespace("validate", "some/pack", "--no-such-flag")


def test_a_subcommand_the_parser_does_not_declare_is_refused() -> None:
    """The same protection for the command words themselves."""
    with pytest.raises(SystemExit):
        cli_namespace("no-such-command")


def test_multi_word_subcommands_resolve_to_their_own_leaf() -> None:
    """Nested subcommands get the leaf's defaults, not the parent's."""
    namespace = cli_namespace("catalogue verify", "--root", ".")

    assert namespace.root == "."
    assert namespace.func is not None
