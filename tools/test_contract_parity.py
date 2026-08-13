"""Tests for catalogue/check_contract_parity.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARITY_TOOL = REPO_ROOT / "tools" / "catalogue" / "check_contract_parity.py"
GENERATOR_TOOL = REPO_ROOT / "tools" / "catalogue" / "sync_contract_inventory.py"


def test_check_contract_parity_tool_exits_0() -> None:
    result = subprocess.run(
        [sys.executable, str(PARITY_TOOL)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_check_contract_parity_rejects_stale_public_inventory(
    tmp_path: Path,
) -> None:
    staged = tmp_path / "staged"
    staged_tool = staged / "tools" / "catalogue" / PARITY_TOOL.name
    staged_tool.parent.mkdir(parents=True)
    shutil.copy2(PARITY_TOOL, staged_tool)
    # The gate loads the canonical contract scan from the generator so the two
    # cannot diverge, so the generator has to be staged alongside it.
    shutil.copy2(GENERATOR_TOOL, staged_tool.parent / GENERATOR_TOOL.name)
    shutil.copytree(REPO_ROOT / "contracts", staged / "contracts")
    staged_data = staged / "packages" / "agentbundle" / "agentbundle" / "_data"
    shutil.copytree(
        REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data",
        staged_data,
    )
    (staged_data / "public-contracts.txt").write_text(
        "pack.schema.json\n", encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, str(staged_tool)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "public-contracts.txt inventory is stale" in result.stderr


def test_sync_contract_inventory_check_matches_the_parity_gate() -> None:
    """The generator and the gate must agree on the canonical contract set.

    `check_contract_parity.py` imports `_render` from the generator so the
    two cannot drift; this pins that they stay wired together and that the
    generator's own `--check` mode agrees with the committed inventory.
    """
    result = subprocess.run(
        [sys.executable, "tools/catalogue/sync_contract_inventory.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_sync_contract_inventory_check_rejects_a_stale_inventory(
    tmp_path: Path,
) -> None:
    """`--check` must fail when the committed inventory is out of date."""
    inventory = (
        REPO_ROOT
        / "packages"
        / "agentbundle"
        / "agentbundle"
        / "_data"
        / "public-contracts.txt"
    )
    original = inventory.read_bytes()
    try:
        inventory.write_text("zzz-not-a-contract.json\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "tools/catalogue/sync_contract_inventory.py", "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
    finally:
        inventory.write_bytes(original)
