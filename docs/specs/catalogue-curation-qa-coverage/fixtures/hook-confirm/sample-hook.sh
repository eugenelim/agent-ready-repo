#!/usr/bin/env bash
# pre-commit hook: delegate quality checks to scripts/pre-commit-checks.py.
# Keep hook logic minimal — all check logic lives in the script.
set -euo pipefail
python scripts/pre-commit-checks.py
