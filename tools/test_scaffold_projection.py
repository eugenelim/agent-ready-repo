"""Tests for catalogue/sync_authoring_scaffold.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_SCAFFOLD = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "catalogue-scaffold"
)


def _sync_pairs() -> list[tuple[Path, str]]:
    path = REPO_ROOT / "tools" / "catalogue" / "sync_authoring_scaffold.py"
    spec = importlib.util.spec_from_file_location("sync_authoring_scaffold", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._SYNC_PAIRS


def test_projection_byte_identical_to_repo_root() -> None:
    drifts = [
        scaffold_rel
        for source, scaffold_rel in _sync_pairs()
        if not (DATA_SCAFFOLD / scaffold_rel).exists()
        or source.read_bytes() != (DATA_SCAFFOLD / scaffold_rel).read_bytes()
    ]
    assert not drifts, f"scaffold projection is out of sync: {drifts}"
