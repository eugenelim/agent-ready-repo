#!/usr/bin/env python3
"""pre-commit hook: block commits that stage .env files."""
import subprocess
import sys

result = subprocess.run(
    ["git", "diff", "--cached", "--name-only"],
    capture_output=True,
    text=True,
    check=True,
)
staged = result.stdout.splitlines()
if any(f == ".env" or f.endswith("/.env") for f in staged):
    print("Error: .env file staged — refusing commit.", file=sys.stderr)
    sys.exit(1)
