#!/usr/bin/env python3
"""Shim — forwards to tools/repo/build_gate_chain.py.

The real implementation lives at tools/repo/build_gate_chain.py. This shim
keeps the Makefile / CI call-site (`python tools/build_gate_chain.py`) stable
while the logic lives in the subdirectory layout introduced in v0.13.0.
"""
import subprocess
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parent / "repo" / "build_gate_chain.py"
sys.exit(subprocess.run([sys.executable, str(_REAL)] + sys.argv[1:], check=False).returncode)
