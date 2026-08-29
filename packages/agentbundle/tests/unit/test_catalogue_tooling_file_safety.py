"""Confined regular-file read and race regressions."""

import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from agentbundle.catalogue_tooling import file_safety
from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
    sha256_confined_regular_file,
)


def test_regular_file_reads_and_hashes(tmp_path):
    target = tmp_path / "data.txt"
    target.write_bytes(b"data")
    assert read_confined_regular_file(tmp_path, target) == b"data"
    assert len(sha256_confined_regular_file(tmp_path, target)) == 64


def test_symlink_and_hardlink_are_refused(tmp_path):
    target = tmp_path / "data.txt"
    target.write_bytes(b"data")
    linked = tmp_path / "linked.txt"
    try:
        linked.symlink_to(target)
    except OSError:
        pytest.skip("links not available")
    with pytest.raises(UnsafeContentError):
        read_confined_regular_file(tmp_path, linked)
    linked.unlink()
    os.link(target, linked)
    with pytest.raises(UnsafeContentError):
        read_confined_regular_file(tmp_path, target)


@pytest.mark.parametrize(
    ("relative", "linked_parent"),
    (
        ("AGENT_RULES.md", "."),
        ("docs/AGENTS.md", "docs"),
        (".agents/rules/cognitive-load.md", ".agents"),
    ),
)
def test_lookup_reads_refuse_linked_parent_components(
    tmp_path: Path, relative: str, linked_parent: str
) -> None:
    actual_root = tmp_path / "actual"
    actual_root.mkdir()
    actual_target = actual_root / relative
    actual_target.parent.mkdir(parents=True, exist_ok=True)
    actual_target.write_text("rule\n", encoding="utf-8")

    if linked_parent == ".":
        declared_root = tmp_path / "repo"
        try:
            declared_root.symlink_to(actual_root, target_is_directory=True)
        except OSError:
            pytest.skip("links not available")
        target = declared_root / relative
    else:
        declared_root = tmp_path / "repo"
        declared_root.mkdir()
        linked = declared_root / linked_parent
        linked.parent.mkdir(parents=True, exist_ok=True)
        destination = actual_root / linked_parent
        try:
            linked.symlink_to(destination, target_is_directory=True)
        except OSError:
            pytest.skip("links not available")
        target = declared_root / relative

    with pytest.raises(UnsafeContentError, match="root|directory boundary"):
        read_confined_regular_file(declared_root, target)


@pytest.mark.parametrize(
    ("relative", "reparse_parent"),
    (
        ("AGENT_RULES.md", "."),
        ("docs/AGENTS.md", "docs"),
        (".agents/rules/cognitive-load.md", ".agents/rules"),
    ),
)
def test_lookup_reads_refuse_reparse_like_parent_components(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
    reparse_parent: str,
) -> None:
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("rule\n", encoding="utf-8")
    marked = tmp_path if reparse_parent == "." else tmp_path / reparse_parent
    original_lstat = Path.lstat
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def reparse_lstat(path: Path) -> os.stat_result | SimpleNamespace:
        inspected = original_lstat(path)
        if path == marked:
            return SimpleNamespace(
                st_mode=inspected.st_mode,
                st_file_attributes=reparse_flag,
            )
        return inspected

    monkeypatch.setattr(Path, "lstat", reparse_lstat)
    monkeypatch.setattr(file_safety, "_supports_descriptor_walk", lambda: False)

    with pytest.raises(UnsafeContentError, match="root|directory boundary"):
        read_confined_regular_file(tmp_path, target)


@pytest.mark.parametrize(
    "relative",
    (
        "AGENT_RULES.md",
        "docs/AGENTS.md",
        ".agents/rules/cognitive-load.md",
    ),
)
def test_lookup_reads_bind_each_component_to_parent_descriptors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    if not file_safety._supports_descriptor_walk():
        pytest.skip("directory descriptor walk is unavailable")
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("rule\n", encoding="utf-8")
    original_open = file_safety.os.open
    observed: list[tuple[str, int | None]] = []

    def observe_open(
        path: str | os.PathLike[str],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        observed.append((os.fspath(path), dir_fd))
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(file_safety.os, "open", observe_open)
    monkeypatch.setattr(file_safety, "_supports_descriptor_walk", lambda: True)

    assert read_confined_regular_file(tmp_path, target) == b"rule\n"
    bound_parts = [part for part, parent in observed if parent is not None]
    assert bound_parts == list(Path(relative).parts)


@pytest.mark.parametrize(
    "relative",
    (
        "AGENT_RULES.md",
        "docs/AGENTS.md",
        ".agents/rules/cognitive-load.md",
    ),
)
def test_lookup_reads_refuse_dot_segment_escape_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root / ".." / "outside" / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("outside\n", encoding="utf-8")

    def refuse_open(*args: object, **kwargs: object) -> int:
        raise AssertionError("dot-segment path reached os.open")

    monkeypatch.setattr(file_safety.os, "open", refuse_open)

    with pytest.raises(UnsafeContentError, match="dot segment"):
        read_confined_regular_file(root, target)


@pytest.mark.parametrize(
    ("mode", "link_count", "file_attributes", "message"),
    (
        (stat.S_IFLNK | 0o777, 1, 0, "not a regular file"),
        (stat.S_IFREG | 0o600, 2, 0, "hard link"),
        (
            stat.S_IFREG | 0o600,
            1,
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            "reparse point",
        ),
        (stat.S_IFIFO | 0o600, 1, 0, "not a regular file"),
    ),
)
def test_fallback_refuses_unsafe_leaf_before_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: int,
    link_count: int,
    file_attributes: int,
    message: str,
) -> None:
    target = tmp_path / "AGENT_RULES.md"
    target.write_text("rule\n", encoding="utf-8")
    original_lstat = Path.lstat

    def unsafe_lstat(path: Path) -> os.stat_result | SimpleNamespace:
        if path == target:
            return SimpleNamespace(
                st_mode=mode,
                st_nlink=link_count,
                st_file_attributes=file_attributes,
            )
        return original_lstat(path)

    def refuse_open(*args: object, **kwargs: object) -> int:
        raise AssertionError("unsafe fallback leaf reached os.open")

    monkeypatch.setattr(target.__class__, "lstat", unsafe_lstat)
    monkeypatch.setattr(file_safety, "_supports_descriptor_walk", lambda: False)
    monkeypatch.setattr(file_safety.os, "open", refuse_open)

    with pytest.raises(UnsafeContentError, match=message):
        read_confined_regular_file(tmp_path, target)


def test_fifo_replacement_is_nonblocking_and_refused(tmp_path, monkeypatch):
    if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
        pytest.skip("FIFO nonblocking checks are unavailable")
    target = tmp_path / "data.txt"
    target.write_bytes(b"data")
    original_open = file_safety.os.open
    observed_flags: list[int] = []

    def replace_with_fifo(path, flags):
        observed_flags.append(flags)
        target.unlink()
        os.mkfifo(target)
        return original_open(path, flags)

    monkeypatch.setattr(file_safety.os, "open", replace_with_fifo)
    with pytest.raises(UnsafeContentError, match="not a regular file"):
        read_confined_regular_file(tmp_path, target)
    assert observed_flags[0] & os.O_NONBLOCK


# ── Traversal bounds ─────────────────────────────────────────────────────────
#
# All three bounds refuse *during* traversal, so a caller can apply a limit
# without first materialising an attacker-controlled tree. None had coverage.


def _tree(root, *, files=0, dirs=0, depth=0):
    root.mkdir(parents=True, exist_ok=True)
    for index in range(files):
        (root / f"f{index:03d}.txt").write_text("x\n", encoding="utf-8")
    for index in range(dirs):
        (root / f"d{index:03d}").mkdir()
    current = root
    for level in range(depth):
        current = current / f"deep{level}"
        current.mkdir()
    return root


def test_unbounded_call_collects_every_regular_file(tmp_path):
    root = _tree(tmp_path / "src", files=5, dirs=2)
    assert len(file_safety.list_confined_regular_files(tmp_path, root)) == 5


def test_max_files_refuses_before_exceeding_the_bound(tmp_path):
    root = _tree(tmp_path / "src", files=4)
    assert len(
        file_safety.list_confined_regular_files(tmp_path, root, max_files=4)
    ) == 4
    with pytest.raises(UnsafeContentError, match="file-count limit"):
        file_safety.list_confined_regular_files(tmp_path, root, max_files=3)


def test_max_depth_refuses_a_deeper_tree(tmp_path):
    root = _tree(tmp_path / "src", depth=3)
    file_safety.list_confined_regular_files(tmp_path, root, max_depth=3)
    with pytest.raises(UnsafeContentError, match="path-depth limit"):
        file_safety.list_confined_regular_files(tmp_path, root, max_depth=2)


def test_max_entries_bounds_a_directory_only_tree(tmp_path):
    """The gap `max_files` alone leaves open.

    A tree made entirely of directories collects no files, so `max_files` never
    fires and the traversal is unbounded. `max_entries` counts every directory
    entry visited, which is what a caller needs when a concurrent writer can
    grow the tree after a preflight measurement.
    """
    root = _tree(tmp_path / "src", dirs=30)

    # Unbounded by max_files, because no regular file is ever collected.
    assert file_safety.list_confined_regular_files(
        tmp_path, root, max_files=1
    ) == []

    file_safety.list_confined_regular_files(tmp_path, root, max_entries=30)
    with pytest.raises(UnsafeContentError, match="entry-count limit"):
        file_safety.list_confined_regular_files(tmp_path, root, max_entries=29)


@pytest.mark.parametrize("bound", ["max_files", "max_depth", "max_entries"])
@pytest.mark.parametrize("value", [-1, True, 1.5, "4"])
def test_bounds_reject_a_malformed_value(tmp_path, bound, value):
    root = _tree(tmp_path / "src", files=1)
    with pytest.raises(ValueError, match=bound):
        file_safety.list_confined_regular_files(tmp_path, root, **{bound: value})
