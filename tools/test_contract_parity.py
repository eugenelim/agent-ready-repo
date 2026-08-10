"""Tests for catalogue/check_contract_parity.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARITY_TOOL = REPO_ROOT / "tools" / "catalogue" / "check_contract_parity.py"


def test_check_contract_parity_tool_exits_0() -> None:
    result = subprocess.run(
        [sys.executable, str(PARITY_TOOL)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
