#!/usr/bin/env python3
"""Guard: verifies **Status:** Shipped in spec.md for a given work-dir.

Called by loop-engine at CODE-REVIEW + reviewers-clean → CODE-HUMAN-GATE
(code mode only). Exits 0 only when Status is exactly "Shipped".
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(\S+)", re.MULTILINE)


def resolve_spec(arg: str) -> Path:
    """Return path to spec.md. If arg is a file, use its parent dir."""
    p = Path(arg)
    if p.is_file():
        return p.parent / "spec.md"
    return p / "spec.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-spec-status",
        description="Verify **Status:** Shipped in spec.md before the G-pr human gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "WORK_DIR may be a directory (containing spec.md) or a file path\n"
            "(the parent directory is used as the work-dir).\n\n"
            "Exits 0 only when **Status:** is exactly 'Shipped'.\n"
            "Valid status values: Draft | Approved | Implementing | Shipped | Archived"
        ),
    )
    parser.add_argument(
        "work_dir",
        metavar="WORK_DIR",
        help="directory with spec.md, or path to a doc file (resolves to parent dir)",
    )
    args = parser.parse_args(argv)

    spec_path = resolve_spec(args.work_dir)
    if not spec_path.exists():
        print(f"error: spec.md not found: {spec_path}", file=sys.stderr)
        return 1

    text = spec_path.read_text(encoding="utf-8")
    m = _STATUS_RE.search(text)
    if not m:
        print(
            f"error: no bare **Status:** line found in {spec_path}\n"
            "  Required format: **Status:** Shipped  (no leading dash or other prefix)",
            file=sys.stderr,
        )
        return 1

    status = m.group(1)
    if status != "Shipped":
        print(
            f"error: spec status is '{status}', expected 'Shipped'\n"
            "  Update spec.md to '**Status:** Shipped' before firing reviewers-clean from CODE-REVIEW.\n"
            "  Valid values: Draft | Approved | Implementing | Shipped | Archived",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
