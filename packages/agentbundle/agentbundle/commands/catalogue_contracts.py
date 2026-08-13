"""``agentbundle catalogue contracts`` command handler."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from agentbundle.catalogue_tooling.contracts_inspector import (
    ContractResourceError,
    export_contracts,
    list_bundled_contracts,
    show_contract,
)
from agentbundle.safety import WriteError

if TYPE_CHECKING:
    import argparse

_REFERENCE_NOTICE = (
    "These are reference copies only. They do not override the contracts used "
    "for validation by this agentbundle version."
)


def _run_list(args: argparse.Namespace) -> int:
    try:
        contracts = list_bundled_contracts()
    except ContractResourceError:
        print("error: bundled contract resources are unavailable", file=sys.stderr)
        return 1
    if getattr(args, "format", "table") == "json":
        print(json.dumps([dataclasses.asdict(contract) for contract in contracts]))
        return 0

    rows = [("NAME", "KIND", "FILE")] + [
        (contract.name, contract.kind, contract.file) for contract in contracts
    ]
    # Pad to the widest cell so the header actually labels its column.
    widths = [max(len(row[column]) for row in rows) for column in range(3)]
    for row in rows:
        print(f"{row[0]:<{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]}")
    return 0


def _run_show(args: argparse.Namespace) -> int:
    name = str(args.name)
    try:
        content = show_contract(name)
    except (ContractResourceError, OSError, ValueError):
        print("error: bundled contract resources are unavailable", file=sys.stderr)
        return 1
    if content is None:
        print(f"error: unrecognized bundled contract {name!r}", file=sys.stderr)
        return 1
    sys.stdout.write(content)
    return 0


def _run_export(args: argparse.Namespace) -> int:
    try:
        written = export_contracts(Path(args.output))
    except ContractResourceError:
        print("error: bundled contract resources are unavailable", file=sys.stderr)
        return 2
    except ValueError as exc:
        message = str(exc).replace("\n", " ")
        print(f"error: cannot export bundled contracts: {message}", file=sys.stderr)
        return 2
    except WriteError as exc:
        # WriteError subclasses OSError, so it must be caught first. Its
        # messages name only the user-supplied output path and are the one
        # actionable signal here ("permission denied", "no space left").
        message = str(exc).replace("\n", " ")
        print(f"error: cannot export bundled contracts: {message}", file=sys.stderr)
        return 2
    except OSError:
        print(
            "error: cannot export bundled contracts: filesystem operation failed",
            file=sys.stderr,
        )
        return 2
    for filename in written:
        print(filename)
    print(_REFERENCE_NOTICE, file=sys.stderr)
    return 0


def run(args: argparse.Namespace) -> int:
    """Dispatch a bundled-contract operation."""
    subcommand = getattr(args, "contracts_sub", None)
    if subcommand == "list":
        return _run_list(args)
    if subcommand == "show":
        return _run_show(args)
    if subcommand == "export":
        return _run_export(args)
    print(
        "agentbundle catalogue contracts: specify a subcommand "
        "(list, show, export)",
        file=sys.stderr,
    )
    return 1
