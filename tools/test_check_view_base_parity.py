"""Tests for tools/check_view_base_parity.py over temporary repositories."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_view_base_parity", Path(__file__).with_name("check_view_base_parity.py")
)
assert _SPEC and _SPEC.loader
parity = importlib.util.module_from_spec(_SPEC)
sys.modules["check_view_base_parity"] = parity
_SPEC.loader.exec_module(parity)

COPY = Path("packs/other/.apm/skills/x/view-base.css")


def _write(root: Path, rel: Path, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run(root: Path) -> int:
    return parity.main(["--root", str(root)])


def test_identical_copy_passes(tmp_path: Path) -> None:
    _write(tmp_path, parity.CANONICAL, "a{}\n")
    _write(tmp_path, COPY, "a{}\n")
    assert _run(tmp_path) == 0


def test_differing_copy_fails_and_is_named(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, parity.CANONICAL, "a{}\n")
    _write(tmp_path, COPY, "b{}\n")
    assert _run(tmp_path) == 1
    assert COPY.as_posix() in capsys.readouterr().err


def test_missing_canonical_fails(tmp_path: Path) -> None:
    _write(tmp_path, COPY, "a{}\n")
    assert _run(tmp_path) == 1


def test_symlink_copy_fails_and_is_named(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    canonical = _write(tmp_path, parity.CANONICAL, "a{}\n")
    link = tmp_path / COPY
    link.parent.mkdir(parents=True)
    link.symlink_to(canonical)
    assert _run(tmp_path) == 1
    assert COPY.as_posix() in capsys.readouterr().err
