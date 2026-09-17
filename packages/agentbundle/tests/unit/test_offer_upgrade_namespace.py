"""`install._offer_upgrade` must hand `upgrade.run` a complete namespace.

`_offer_upgrade` is the one place in the package where one command calls
another's `run()` with a namespace it assembles by hand, so it is the one place
the CLI parser cannot guarantee the attribute set. Its docstring has always
claimed it "builds the FULL attribute set `upgrade.run` reads"; nothing checked
that, and it was short by three dests that `getattr` defaults happened to cover.

Derived from the live parser rather than pinned to a list: a list would need
editing in lockstep with `cli.py`, which is the failure this case exists to
catch.
"""

from __future__ import annotations

import argparse
from unittest import mock


def _upgrade_dests() -> set[str]:
    """Every dest the `upgrade` subparser puts on a real namespace."""
    from agentbundle.cli import _build_parser

    parsed = _build_parser().parse_args(["upgrade", "--pack", "demo"])
    return {name for name in vars(parsed) if not name.startswith("_")}


def _captured_offer_namespace() -> argparse.Namespace:
    """Run `_offer_upgrade` with `upgrade.run` stubbed, return the namespace."""
    from agentbundle.commands import install

    captured: list[argparse.Namespace] = []

    def _fake_run(ns: argparse.Namespace) -> int:
        captured.append(ns)
        return 0

    caller = argparse.Namespace(output="/tmp/repo", adapter=None, _user_config=None)
    with mock.patch("agentbundle.commands.upgrade.run", _fake_run):
        rc = install._offer_upgrade(
            caller,
            pack_name="demo",
            scope="repo",
            catalogue_uri="/tmp/catalogue",
            resolved_adapter="claude-code",
        )

    assert rc == 0
    assert len(captured) == 1
    return captured[0]


def test_offer_upgrade_namespace_is_complete() -> None:
    """Every public dest the upgrade parser declares is set by the hand-off.

    `func` and `command` are argparse dispatch bookkeeping that `upgrade.run`
    never reads, so they are excluded rather than stubbed.
    """
    expected = _upgrade_dests() - {"func", "command"}
    actual = set(vars(_captured_offer_namespace()))

    missing = expected - actual
    assert not missing, (
        f"_offer_upgrade omits {sorted(missing)}; upgrade.run reads the "
        "parser's dests, so every one must be set here"
    )


def test_offer_upgrade_namespace_matches_parser_defaults_where_unforced() -> None:
    """The dests the offer does not deliberately pin carry parser defaults.

    Stated as values, not just presence: setting `format` to something the
    parser would never produce would satisfy the completeness case above and
    still print a plan shape no `agentbundle upgrade` run can produce.
    """
    namespace = _captured_offer_namespace()

    assert namespace.all is False
    assert namespace.source is None
    assert namespace.format == "table"


def test_offer_upgrade_pins_the_values_the_hand_off_owns() -> None:
    """The offer is itself the confirmation, and it targets one resolved row."""
    namespace = _captured_offer_namespace()

    assert namespace.yes is True
    assert namespace.dry_run is False
    assert namespace.pack == "demo"
    assert namespace.scope == "repo"
    assert namespace.root == "/tmp/repo"
    assert namespace.catalogue == "/tmp/catalogue"
    # `--adapter` was omitted on the install side, so the auto-detected adapter
    # is what keeps the upgrade on the row the install would have written.
    assert namespace.adapter == "claude-code"
    assert namespace.skill is None
    assert namespace.agent is None
    assert namespace.hook is None
    assert namespace.seed is None
    assert namespace.command is None
