#!/usr/bin/env python3
"""Shim — forwards to tools/catalogue/pre_pr_catalogue.py.

The real implementation lives at tools/catalogue/pre_pr_catalogue.py. This shim
keeps legacy direct invocations (`python tools/pre-pr-catalogue.py`) stable while
current repository orchestration calls the real implementation.
"""
import subprocess
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parent / "catalogue" / "pre_pr_catalogue.py"
sys.exit(subprocess.run([sys.executable, str(_REAL)] + sys.argv[1:], check=False).returncode)
