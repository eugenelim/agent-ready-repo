#!/usr/bin/env bash
# pre-commit hook: delegate quality checks to .agentbundle/bin/pre-commit-checks.py.
# The companion script is distributed via adapter-root-bins and lands at
# .agentbundle/bin/ in the adopter's repo root.
set -euo pipefail
python .agentbundle/bin/pre-commit-checks.py
