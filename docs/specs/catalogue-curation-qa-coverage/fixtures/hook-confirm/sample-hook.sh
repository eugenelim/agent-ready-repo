#!/usr/bin/env bash
# pre-commit hook: delegate quality checks to the project's pre-commit script.
set -euo pipefail
python3 tools/pre-commit-checks.py
