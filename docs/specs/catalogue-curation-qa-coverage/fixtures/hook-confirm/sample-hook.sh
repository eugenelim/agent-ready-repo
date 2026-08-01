#!/usr/bin/env bash
# pre-commit hook: run basic quality gates before each commit.
set -euo pipefail
python3 -m ruff check . --quiet
python3 -m mypy packages/agentbundle/ --quiet
