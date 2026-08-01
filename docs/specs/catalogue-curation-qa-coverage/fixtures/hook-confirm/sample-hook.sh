#!/usr/bin/env bash
# pre-commit hook: block commits that stage .env files.
set -euo pipefail
if git diff --cached --name-only | grep -q '\.env$'; then
  echo "Error: .env file staged — refusing commit." >&2
  exit 1
fi
