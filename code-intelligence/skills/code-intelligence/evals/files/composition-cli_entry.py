"""Command-line entry point."""
from __future__ import annotations

import sys

from composition_config_loader import parse_config


def run(argv: list[str]) -> int:
    """Parse arguments, load configuration, and return an exit code."""
    if len(argv) < 2:
        print("usage: cli_entry <config-path>", file=sys.stderr)
        return 1
    config = parse_config(argv[1])
    print(config)
    return 0
