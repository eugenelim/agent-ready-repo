"""Stub handler for agentbundle catalogue <sub> and agentbundle lint packs.

All catalogue_tooling subcommands exit 1 with "not yet implemented" until
Wave 2-4 specs fill them in.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    sub = getattr(args, "catalogue_sub", None) or getattr(args, "lint_sub", None) or ""
    print(
        f"agentbundle catalogue {sub} not yet implemented — see ini-005 Wave 2-4 specs".rstrip(),
        file=sys.stderr,
    )
    return 1
