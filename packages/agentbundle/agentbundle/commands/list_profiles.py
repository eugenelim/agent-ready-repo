"""``agentbundle list-profiles`` subcommand (RFC-0034 / spec pack-profiles).

Resolves a catalogue URI, enumerates every valid ``profiles/*.toml``, and
prints a stable table of id, scope, description to stdout. Modeled on
``list_packs``.

Exit codes:
  0  — success (an empty listing is not an error).
  1  — catalogue resolution error (one-line stderr from CatalogueError).
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle list-profiles``.

    Args:
        args.catalogue — catalogue URI (local path or git+https://...).

    Returns 0 on success, 1 on catalogue resolution failure.
    """
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands.profile import list_profiles

    catalogue_uri: str = args.catalogue

    try:
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"list-profiles: {exc}", file=sys.stderr)
        return 1

    profiles = list_profiles(catalogue_dir)
    _print_table(profiles)
    return 0


def _print_table(profiles) -> None:
    """Print a fixed-column table to stdout: ID, SCOPE, DESCRIPTION.

    Deterministic: ``list_profiles`` returns id-sorted rows; column widths are
    derived from content so the table is alignment-stable.
    """
    headers = ["ID", "SCOPE", "DESCRIPTION"]
    rows = [(p.id, p.scope, p.description) for p in profiles]

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))
