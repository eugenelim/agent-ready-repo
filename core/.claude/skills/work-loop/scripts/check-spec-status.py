#!/usr/bin/env python3
"""check-spec-status — guard: a spec or plan file must have a specific Status value.

Used as the reviewers-clean guard in CODE-REVIEW → CODE-HUMAN-GATE (default: Status Shipped)
and as the spec-approved / plan-approved / plan-locked guards (--expect Approved).

Usage:
    check-spec-status.py <spec-dir> [--expect <status>] [--file <filename>]

    <spec-dir>          directory containing the target file
    --expect <status>   expected Status value (default: Shipped)
    --file <filename>   file to read within <spec-dir> (default: spec.md)

Exit 0 iff the canonical status parser resolves the file's Status to the expected value.
Exit non-zero with a one-line reason on stderr otherwise.

Imports parse_status / extract_status_token from lint-spec-status.py via
importlib so both tools share one canonical parser implementation.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
LINT_SPEC_STATUS = SCRIPT_DIR / "lint-spec-status.py"


def _load_status_parser():
    """Import parse_status and extract_status_token from lint-spec-status.py."""
    spec = importlib.util.spec_from_file_location(
        "_lint_spec_status", str(LINT_SPEC_STATUS)
    )
    if spec is None or spec.loader is None:
        print(
            f"check-spec-status: cannot load {LINT_SPEC_STATUS}",
            file=sys.stderr,
        )
        sys.exit(1)
    module = importlib.util.module_from_spec(spec)
    # Suppress lint-spec-status's own stdout/stderr side-effects during import
    # by only loading the module object without executing it as __main__.
    spec.loader.exec_module(module)
    return module.parse_status, module.extract_status_token


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="check-spec-status",
        description="Guard: verify that a spec or plan file has the expected Status value.",
    )
    parser.add_argument("spec_dir", help="directory containing the target file")
    parser.add_argument(
        "--expect",
        default="Shipped",
        help="expected Status value (default: Shipped)",
    )
    parser.add_argument(
        "--file",
        default="spec.md",
        help="file to read within spec-dir (default: spec.md)",
    )
    args = parser.parse_args()

    spec_dir = Path(args.spec_dir).resolve()
    target_path = (spec_dir / args.file).resolve()

    if not target_path.is_relative_to(spec_dir):
        print(
            "check-spec-status: --file must be within spec-dir",
            file=sys.stderr,
        )
        return 1

    if not target_path.exists():
        print(
            f"check-spec-status: {args.file} not found at {target_path}",
            file=sys.stderr,
        )
        return 1

    parse_status, _ = _load_status_parser()

    try:
        text = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"check-spec-status: cannot read {target_path}: {exc}", file=sys.stderr)
        return 1

    token = parse_status(text)
    if token is None:
        print(
            f"check-spec-status: no **Status:** line found in {target_path}",
            file=sys.stderr,
        )
        return 1

    if token != args.expect:
        print(
            f"check-spec-status: {args.file} Status is {token!r}, expected {args.expect!r}",
            file=sys.stderr,
        )
        return 1

    print(f"check-spec-status: OK — Status: {args.expect} at {target_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
