"""Console-script entry point.

Argument parsing, the exit-code contract and the run itself are built out by
later tasks. This module currently carries only what T1 owns: a command that
exists, is reachable from the installed console script, and reports its version.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jsonl-otlp-export",
        description="Send JSONL records to an OpenTelemetry Collector as OTLP logs.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover - console script is the surface
    sys.exit(main())
