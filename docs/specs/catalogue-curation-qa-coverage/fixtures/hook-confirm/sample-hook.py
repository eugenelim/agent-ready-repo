#!/usr/bin/env python3
"""pre-commit hook: block commits that stage .env files."""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

result = subprocess.run(
    ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACMR"],
    capture_output=True,
    check=True,
)
staged = result.stdout.decode("utf-8", errors="replace").split("\0")
if any(f == ".env" or f.endswith("/.env") for f in staged):
    print("Error: .env file staged — refusing commit.", file=sys.stderr)
    sys.exit(1)
