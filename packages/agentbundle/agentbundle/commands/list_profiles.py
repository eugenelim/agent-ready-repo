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
    from agentbundle.commands._common import resolve_catalogue_uri
    from agentbundle.commands.profile import list_profiles

    # RFC-0047: default the source through the same four-layer chain as
    # install/upgrade when the `catalogue` positional is omitted.
    try:
        catalogue_uri: str = resolve_catalogue_uri(args)
        catalogue_dir = resolve_catalogue(catalogue_uri)
    except CatalogueError as exc:
        print(f"list-profiles: {exc}", file=sys.stderr)
        return 1

    profiles = list_profiles(catalogue_dir)
    _print_table(profiles)
    return 0


def _print_table(profiles) -> None:
    """Print the profile table to stdout: ID, SCOPE, DESCRIPTION.

    Deterministic: ``list_profiles`` returns id-sorted rows; column widths are
    content-derived so the table is alignment-stable. The long DESCRIPTION
    column word-wraps to fit an interactive terminal — see
    ``_common.render_table`` for the TTY / non-TTY contract.
    """
    from agentbundle.commands._common import render_table

    headers = ["ID", "SCOPE", "DESCRIPTION"]
    rows = [[p.id, p.scope, p.description] for p in profiles]
    render_table(headers, rows, wrap_col=2)
