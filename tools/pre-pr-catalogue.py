#!/usr/bin/env python3
"""Shim → tools/catalogue/pre_pr_catalogue.py (ini-005 Wave 5 reorganisation).

This file is kept until the next minor AgentBundle release. Update direct
callers to: python tools/catalogue/pre_pr_catalogue.py
"""
import subprocess
import sys
from pathlib import Path

print(
    "WARNING: tools/pre-pr-catalogue.py moved to tools/catalogue/pre_pr_catalogue.py",
    file=sys.stderr,
)
_delegate = Path(__file__).resolve().parent / "catalogue" / "pre_pr_catalogue.py"
sys.exit(subprocess.run([sys.executable, str(_delegate)] + sys.argv[1:]).returncode)
