"""Stub handler for agentbundle catalogue <sub> and agentbundle lint packs.

This handler prints "agentbundle catalogue <sub> not yet implemented" to stderr
and returns 1.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace) -> int:
    sub = getattr(args, "catalogue_sub", None) or getattr(args, "lint_sub", None) or ""
    print(
        f"agentbundle catalogue {sub} not yet implemented".rstrip(),
        file=sys.stderr,
    )
    return 1
