#!/usr/bin/env python3
"""Quality-gate checks invoked by the pre-commit hook.

This is a fixture stub. Replace with real checks (ruff format, ruff check,
mypy, pytest -x, etc.) before using this in production.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# Stub: exits 0 (allows commit) unconditionally.
# Real implementation would run:
#   subprocess.run(["ruff", "format", "--check", "."], check=True)
#   subprocess.run(["ruff", "check", "."], check=True)
sys.exit(0)
