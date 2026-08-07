#!/usr/bin/env python3
"""Negative fixture: the post-fix shape. The rule MUST be silent here.

Two distinct silent shapes are covered:
  1. `_validated_root(...)` — the validator this spec introduces.
  2. resolve()-then-is_relative_to() in one function — the pre-existing
     exemplar at check-spec-status.py:72-80, which was already taint-legible
     and must not be flagged.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def _repo_root() -> Path:
    return Path.cwd()


def _validated_root(candidate: Path | None) -> Path:
    root = (candidate if candidate is not None else _repo_root()).resolve()
    if not root.is_dir():
        raise SystemExit(f"--root is not a directory: {root}")
    return root


def main_with_validator() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = _validated_root(args.root)   # silent
    print(root)
    return 0


def main_with_containment_check() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec_dir")
    parser.add_argument("--file", default="spec.md")
    args = parser.parse_args()
    spec_dir = Path(args.spec_dir).resolve()          # silent — guarded below
    target_path = (spec_dir / args.file).resolve()
    if not target_path.is_relative_to(spec_dir):
        return 1
    print(target_path)
    return 0
