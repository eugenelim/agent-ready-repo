"""Tests for `sweep_orphans` — the shared post-pass for
`direct-directory` skill projections."""

from __future__ import annotations

from pathlib import Path

from agentbundle.build.projections.direct_directory import sweep_orphans


def test_removes_orphan_directory(tmp_path: Path) -> None:
    for name in ("a", "b", "c"):
        (tmp_path / name).mkdir()

    sweep_orphans(tmp_path, {"a", "c"})

    assert (tmp_path / "a").is_dir()
    assert (tmp_path / "c").is_dir()
    assert not (tmp_path / "b").exists()


def test_noop_on_full_match(tmp_path: Path) -> None:
    for name in ("a", "b"):
        (tmp_path / name).mkdir()

    sweep_orphans(tmp_path, {"a", "b"})

    assert (tmp_path / "a").is_dir()
    assert (tmp_path / "b").is_dir()


def test_noop_on_missing_target(tmp_path: Path) -> None:
    sweep_orphans(tmp_path / "does-not-exist", {"a"})


def test_ignores_root_files(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    readme = tmp_path / "README.md"
    readme.write_text("hello\n", encoding="utf-8")

    sweep_orphans(tmp_path, set())

    assert not (tmp_path / "a").exists()
    assert readme.is_file()
    assert readme.read_text(encoding="utf-8") == "hello\n"


def test_symlink_safe_sweep(tmp_path: Path) -> None:
    external = tmp_path / "outside"
    external.mkdir()
    (external / "anchor").write_text("keep me\n", encoding="utf-8")

    target = tmp_path / "skills"
    target.mkdir()
    (target / "a").mkdir()
    link = target / "b"
    link.symlink_to(external, target_is_directory=True)

    sweep_orphans(target, {"a"})

    assert (target / "a").is_dir()
    assert not link.exists()
    assert not link.is_symlink()
    assert external.is_dir()
    assert (external / "anchor").read_text(encoding="utf-8") == "keep me\n"
