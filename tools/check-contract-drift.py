#!/usr/bin/env python3
"""Shim → tools/repo/check_contract_drift.py (ini-005 Wave 5 reorganisation).

This file is kept until the next minor AgentBundle release. Update direct
callers to: python tools/repo/check_contract_drift.py
"""
import subprocess
import sys
from pathlib import Path

print(
    "WARNING: tools/check-contract-drift.py moved to tools/repo/check_contract_drift.py",
    file=sys.stderr,
)
_delegate = Path(__file__).resolve().parent / "repo" / "check_contract_drift.py"
sys.exit(subprocess.run([sys.executable, str(_delegate)] + sys.argv[1:]).returncode)
