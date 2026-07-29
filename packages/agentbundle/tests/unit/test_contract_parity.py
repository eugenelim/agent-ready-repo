"""Contract parity tests — Wave 1 schema sync (AC14–AC17, AC19).

Verifies that:
  (1) The four schemas newly synced in Wave 1 are byte-identical between
      contracts/ and agentbundle/_data/.
  (2) check_contract_parity.py exits 0 on a clean repo.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]  # packages/agentbundle/tests/unit -> repo root
_CONTRACTS = _REPO_ROOT / "contracts"
_DATA = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"
_PARITY_TOOL = _REPO_ROOT / "tools" / "catalogue" / "check_contract_parity.py"


def _parity(name: str) -> None:
    """Assert contracts/<name> is byte-identical to agentbundle/_data/<name>."""
    src = _CONTRACTS / name
    dst = _DATA / name
    assert src.exists(), f"contracts/{name} not found"
    assert dst.exists(), f"agentbundle/_data/{name} not found"
    assert src.read_bytes() == dst.read_bytes(), (
        f"Parity violation: contracts/{name} differs from agentbundle/_data/{name}"
    )


def test_guide_schema_synced() -> None:
    """AC14: guide.schema.json byte-identical between contracts/ and _data/."""
    _parity("guide.schema.json")


def test_skill_schema_synced() -> None:
    """AC15: skill.schema.json byte-identical between contracts/ and _data/."""
    _parity("skill.schema.json")


def test_skill_manifest_schema_synced() -> None:
    """AC16: skill-manifest.schema.json byte-identical between contracts/ and _data/."""
    _parity("skill-manifest.schema.json")


def test_target_vocab_toml_synced() -> None:
    """AC17: target-vocab.toml byte-identical between contracts/ and _data/."""
    _parity("target-vocab.toml")


def test_check_contract_parity_tool_exits_0() -> None:
    """AC19: check_contract_parity.py bare invocation exits 0 on clean repo."""
    result = subprocess.run(
        [sys.executable, str(_PARITY_TOOL)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"check_contract_parity.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "ok" in result.stdout
