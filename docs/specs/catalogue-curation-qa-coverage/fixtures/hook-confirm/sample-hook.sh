#!/usr/bin/env bash
# pre-commit hook: delegate quality checks to the companion script.
# The companion is projected to .agentbundle/bin/ via adapter-root-bins.
set -euo pipefail
python3 .agentbundle/bin/pre-commit-checks.py
