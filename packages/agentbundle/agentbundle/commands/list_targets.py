"""`agentbundle list-targets` subcommand.

Prints one adapter name per line, in stable sort order, then exits 0.

The list is derived from `agentbundle.render.list_adapters()`, which queries
the runtime registry at `agentbundle.build.adapters.registry` — not a
hardcoded constant.  Adding an adapter to the registry makes it appear here
automatically.
"""

from __future__ import annotations

import argparse
import sys

from agentbundle.render import list_adapters


def run(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Print one adapter name per line; exit 0."""
    for name in list_adapters():
        print(name)
    return 0
