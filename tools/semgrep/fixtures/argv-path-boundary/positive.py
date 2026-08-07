#!/usr/bin/env python3
"""Positive fixture: the pre-fix shape. The rule MUST fire exactly once here.

Mirrors lint-traceability.py:1251 as it stood before
spec/pack-script-root-boundary-validation. Not executable production code —
this file exists only so the gate's own rule is proven to fire.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def _repo_root() -> Path:
    return Path.cwd()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve() if args.root else _repo_root()   # rule fires here
    print(root)
    return 0
