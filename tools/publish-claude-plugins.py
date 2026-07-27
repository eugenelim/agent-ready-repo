"""Shim → tools/catalogue/publish_claude_plugins.py (ini-005 Wave 5 reorganisation).

This file is kept until the next minor AgentBundle release. Update direct
callers to: python3 tools/catalogue/publish_claude_plugins.py
"""
import subprocess
import sys
from pathlib import Path

print(
    "WARNING: tools/publish-claude-plugins.py moved to tools/catalogue/publish_claude_plugins.py",
    file=sys.stderr,
)
_delegate = Path(__file__).resolve().parent / "catalogue" / "publish_claude_plugins.py"
sys.exit(subprocess.run([sys.executable, str(_delegate)] + sys.argv[1:]).returncode)
