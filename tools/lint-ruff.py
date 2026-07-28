#!/usr/bin/env python3
"""Ruff lint wrapper — runs `ruff check .` with the project's pyproject.toml
config and returns ruff's exit code verbatim (0=clean, 1=violations).

Called by CI via: python3 tools/lint-ruff.py
Called locally:   python tools/lint-ruff.py [--fix]

Passes any extra arguments through to ruff, so `--fix` works as expected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    cmd = [sys.executable, "-m", "ruff", "check", str(REPO_ROOT), *sys.argv[1:]]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
