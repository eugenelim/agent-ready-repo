"""Tests for write_jail.py (RFC-0059 write confinement via agentbundle.safety).
Confirms the reused engine jail rejects traversal + symlink escape and writes
in-bounds. Requires `agentbundle` importable (the repo engine)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import write_jail as wj


def test_in_bounds_write(tmp_path: Path) -> None:
    out = wj.jailed_write(tmp_path, "sub/file.txt", "hello")
    assert out.read_text() == "hello"
    assert out.resolve().is_relative_to(tmp_path.resolve())


def test_traversal_relpath_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(wj.PathJailError):
        wj.jailed_write(root, "../escape.txt", "x")


def test_confined_target_in_and_out(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "ok.txt").write_text("y")
    assert wj.confined_target(root, root / "ok.txt").is_relative_to(root.resolve())
    with pytest.raises(wj.PathJailError):
        wj.confined_target(root, tmp_path / "outside.txt")


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("s")
    link = root / "link"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    # A path that only stays in-bounds if symlinks are NOT resolved.
    with pytest.raises(wj.PathJailError):
        wj.confined_target(root, link / "secret.txt")
