#!/usr/bin/env python3
"""Shim → tools/repo/build_gate_chain.py (ini-005 Wave 5 reorganisation).

This file is kept until the next minor AgentBundle release. Update direct
callers to: python tools/repo/build_gate_chain.py
"""
import subprocess
import sys
from pathlib import Path

print(
    "WARNING: tools/build_gate_chain.py moved to tools/repo/build_gate_chain.py",
    file=sys.stderr,
)
_delegate = Path(__file__).resolve().parent / "repo" / "build_gate_chain.py"
sys.exit(subprocess.run([sys.executable, str(_delegate)] + sys.argv[1:]).returncode)
