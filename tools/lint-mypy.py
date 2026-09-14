#!/usr/bin/env python3
"""mypy type-check wrapper — runs mypy against the project's typed packages
(packages/agentbundle/agentbundle and packages/credbroker/credbroker) with
the config in the root pyproject.toml.

Returns mypy's exit code verbatim (0=clean, 1=errors found).

Scoped to typed packages only. Untyped scripts (tools/, skill scripts) are
not checked — typing them is a separate initiative.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Positional arguments OVERRIDE the `files` setting in pyproject.toml, so this
# list -- not the config -- decides what the gate checks. A package absent from
# here is not checked and nothing says so; `test_lint_mypy_covers_every_package.py`
# is what turns that silence into a failure.
TYPED_PACKAGES = [
    "packages/agentbundle/agentbundle",
    "packages/credbroker/credbroker",
    "packages/jsonl-otlp-exporter/jsonl_otlp_exporter",
]


def main() -> int:
    cmd = [
        sys.executable, "-m", "mypy",
        "--config-file", str(REPO_ROOT / "pyproject.toml"),
        *TYPED_PACKAGES,
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
