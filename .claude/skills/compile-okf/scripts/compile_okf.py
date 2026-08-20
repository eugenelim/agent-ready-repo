#!/usr/bin/env python3
"""CLI wrapper for the OKF authoring compiler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from okf_compiler import compile_pack

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--pack", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    result = compile_pack(Path(args.root), args.pack, check=args.check)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
