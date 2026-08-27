"""Confined regular-file read and race regressions."""

import os

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
