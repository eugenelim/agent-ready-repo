"""Tests for tools/catalogue/check_spec_version.py (check 2)."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

_CAT = Path(__file__).resolve().parent / "catalogue"
_REAL = Path(__file__).resolve().parents[1] / "contracts"


def _load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, _CAT / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


check = _load("check_spec_version")
rewrite = _load("rewrite_member_ids")
inventory = _load("sync_contract_inventory")


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    dest = tmp_path / "contracts"
    shutil.copytree(_REAL, dest)
    return dest


def _set_ids(root: Path, version: str, only: str | None = None) -> None:
    for row in inventory.json_schema_members(root):
        name = Path(row.path).name
        if only is None or name == only:
            path = root / name
            path.write_bytes(rewrite.rewrite_bytes(path.read_bytes(), rewrite.member_id(version, name)))


def test_real_tree_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert check.main(contracts_dir=_REAL) == 0
    assert "ok" in capsys.readouterr().out


def test_one_id_moved_fails(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _set_ids(tree, "0.2", only="pack.schema.json")
    assert check.main(contracts_dir=tree) == 1
    assert "rewrite_member_ids.py" in capsys.readouterr().err


def test_bytes_differ_with_latest_id_fails(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tree / "pack.schema.json"
    path.write_bytes(path.read_bytes().replace(b'"title"', b'"title" ', 1))
    assert path.read_bytes() != (tree / "releases/catalogue/0.1/pack.schema.json").read_bytes()
    assert check.main(contracts_dir=tree) == 1
    assert "rewrite_member_ids.py" in capsys.readouterr().err


def test_bytes_differ_with_unreleased_id_passes(tree: Path) -> None:
    path = tree / "pack.schema.json"
    path.write_bytes(path.read_bytes().replace(b'"title"', b'"title" ', 1))
    _set_ids(tree, "0.2")
    assert check.main(contracts_dir=tree) == 0


def test_three_consumers_share_one_member_set() -> None:
    expected = {Path(r.path).name for r in inventory.json_schema_members(_REAL)}
    assert expected
    assert {Path(r.path).name for r in rewrite._load_inventory().json_schema_members(_REAL)} == expected
    assert {Path(r.path).name for r in check._generator.json_schema_members(_REAL)} == expected
