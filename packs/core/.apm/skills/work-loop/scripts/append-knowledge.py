#!/usr/bin/env python3
"""Refuse the retired flat-JSONL knowledge write path.

Project knowledge has one writer authority. Workflows hand a typed captured
observation to ``project-knowledge --capture``; migration alone reads the
legacy ``patterns.jsonl`` corpus. Keeping this command as a refusal shim gives
older workflow installations a deterministic failure without creating a
second lock or writer generation.
"""

from __future__ import annotations

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="append-knowledge.py",
        description="Retired compatibility shim; no knowledge is written.",
    )
    parser.add_argument("--kind")
    parser.add_argument("--scope")
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--source")
    parser.add_argument("--tier")
    parser.add_argument("--file")
    parser.parse_args(argv)
    print(
        "append-knowledge: retired writer; use project-knowledge --capture",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
