#!/usr/bin/env python3
"""check-spec-status — guard: spec.md Status must be 'Shipped'.

Used as the reviewers-clean guard in CODE-REVIEW → CODE-HUMAN-GATE.

Usage: check-spec-status.py <spec-dir>

Exit 0 iff the canonical status parser resolves spec.md Status to 'Shipped'.
Exit non-zero with a one-line reason on stderr otherwise.

Imports parse_status / extract_status_token from lint-spec-status.py via
importlib so both tools share one canonical parser implementation.
"""

from __future__ import annotations

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
    if len(sys.argv) < 2:
        print("check-spec-status: <spec-dir> required", file=sys.stderr)
        return 1

    spec_dir = Path(sys.argv[1]).resolve()
    spec_path = spec_dir / "spec.md"

    if not spec_path.exists():
        print(
            f"check-spec-status: spec.md not found at {spec_path}",
            file=sys.stderr,
        )
        return 1

    parse_status, _ = _load_status_parser()

    try:
        spec_text = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"check-spec-status: cannot read {spec_path}: {exc}", file=sys.stderr)
        return 1

    token = parse_status(spec_text)
    if token is None:
        print(
            f"check-spec-status: no **Status:** line found in {spec_path}",
            file=sys.stderr,
        )
        return 1

    if token != "Shipped":
        print(
            f"check-spec-status: spec.md Status is {token!r}, expected 'Shipped'",
            file=sys.stderr,
        )
        return 1

    print(f"check-spec-status: OK — Status: Shipped at {spec_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
