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
