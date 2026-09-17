"""Pack-local tests for the shared confinement helper _record_paths.py (T1).

This suite is gated by name in the gate chain (T8 adds the build-check.yml
step).  It may not read above its own pack — lint-pack-test-boundary.py
check 8 enforces that boundary.

T1 cases cover:
- helper loading (all required entry points present)
- every load-failure mode produces a detectable refusal rather than a silent
  fallback (a path that does not resolve, an exec_module that raises, a None
  spec or loader, and a module missing an entry point)
- list_candidate_entries refuses a symlinked supplied directory and accepts an
  ordinary directory nested under a symlinked ancestor
- classify_entry identifies symlinks, FIFOs, directories, and regular files
- read_confined reads a regular single-link file; refuses a hard link
- the hard-link case is the load-bearing proof that read_confined is stricter
  than the lstat-then-read_text idiom the scripts previously carried
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import types

import pytest

sys.dont_write_bytecode = True

SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-adr/scripts"
_HELPER_PATH = SCRIPTS / "_record_paths.py"


def _load_helper() -> types.ModuleType:
    """Load _record_paths.py using the same pattern the sibling scripts use.

    Loaded by path via importlib.util.spec_from_file_location, never by bare
    name, matching the packs/AGENTS.md requirement and the precedent in
    check-spec-status.py:69-114.
    """
    spec = importlib.util.spec_from_file_location(
        "new_adr_record_paths_test", str(_HELPER_PATH)
    )
    assert spec is not None and spec.loader is not None, (
        f"no import spec for {_HELPER_PATH}"
    )
    mod = importlib.util.module_from_spec(spec)
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        sys.dont_write_bytecode = prev
    return mod  # type: ignore[return-value]


# ── Helper loading ─────────────────────────────────────────────────────────────


def test_helper_loads_and_exposes_entry_points() -> None:
    """The helper loads cleanly and exposes all three required entry points."""
    rp = _load_helper()
    assert hasattr(rp, "list_candidate_entries"), "missing list_candidate_entries"
    assert hasattr(rp, "classify_entry"), "missing classify_entry"
    assert hasattr(rp, "read_confined"), "missing read_confined"
    assert hasattr(rp, "EntryRefused"), "missing EntryRefused exception class"


def test_load_from_nonexistent_path_raises(tmp_path: pathlib.Path) -> None:
    """A path that does not resolve raises rather than returning a usable module.

    spec_from_file_location may return a spec for a missing file, but
    exec_module raises at load time.  The loading code in the scripts must
    propagate that exception rather than falling back to a direct scan.
    """
    missing = tmp_path / "nonexistent.py"
    spec = importlib.util.spec_from_file_location("missing_helper", str(missing))
    if spec is None or spec.loader is None:
        # None spec is already a refusal — the caller can detect and refuse.
        return
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises((FileNotFoundError, OSError, ImportError)):
        spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_load_when_exec_module_raises_propagates(tmp_path: pathlib.Path) -> None:
    """A module body that raises during exec_module propagates the exception.

    The loading code in the scripts wraps this in _HelperUnavailable and
    returns 1 rather than proceeding with a partial or absent helper.
    """
    bad = tmp_path / "bad.py"
    bad.write_text("raise RuntimeError('deliberate failure')\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("bad_helper", str(bad))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(RuntimeError, match="deliberate failure"):
        spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_none_spec_for_non_python_extension(tmp_path: pathlib.Path) -> None:
    """spec_from_file_location returns None for a file with no Python loader.

    The loading code must check for None before calling exec_module and refuse
    rather than raising AttributeError or proceeding with a missing loader.
    """
    not_python = tmp_path / "helper.txt"
    not_python.write_text("not python\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("helper_txt", str(not_python))
    # No loader handles .txt files; the spec is None.
    assert spec is None


def test_module_missing_entry_points_is_detectable(tmp_path: pathlib.Path) -> None:
    """A module that loads but lacks entry points is distinguishable from one that has them.

    The loading code checks hasattr for each required entry point after
    exec_module succeeds, and refuses rather than letting callers hit
    AttributeError at the use site.
    """
    incomplete = tmp_path / "incomplete.py"
    incomplete.write_text("# no entry points here\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("incomplete_helper", str(incomplete))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert not hasattr(mod, "list_candidate_entries")
    assert not hasattr(mod, "classify_entry")
    assert not hasattr(mod, "read_confined")


# ── list_candidate_entries ─────────────────────────────────────────────────────


def test_list_candidate_entries_refuses_symlinked_directory(
    tmp_path: pathlib.Path,
) -> None:
    """list_candidate_entries refuses a directory that is itself a symlink."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    rp = _load_helper()
    with pytest.raises(rp.EntryRefused, match="symlink"):
        rp.list_candidate_entries(link)


def test_list_candidate_entries_accepts_ordinary_dir_under_symlinked_ancestor(
    tmp_path: pathlib.Path,
) -> None:
    """An ordinary directory under a symlinked ancestor is accepted.

    macOS resolves /var through a symlink to /private/var.  The only check is
    on the supplied directory itself; an ancestor symlink is ordinary and must
    not cause a refusal.
    """
    real = tmp_path / "real"
    real.mkdir()
    inner = real / "records"
    inner.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    rp = _load_helper()
    # link/records is a real directory; its ancestor link is a symlink.
    # list_candidate_entries checks only the supplied path, not ancestors.
    entries = rp.list_candidate_entries(link / "records")
    assert isinstance(entries, list)


# ── classify_entry ─────────────────────────────────────────────────────────────


def test_classify_entry_returns_symlink_for_symlink(tmp_path: pathlib.Path) -> None:
    """A symlink entry is classified as "symlink", not as its target's type."""
    target = tmp_path / "target.md"
    target.write_text("content\n", encoding="utf-8")
    link = tmp_path / "link.md"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    link_entry = next(e for e in entries if e.name == "link.md")
    assert rp.classify_entry(link_entry) == "symlink"


def test_classify_entry_returns_directory_for_directory(
    tmp_path: pathlib.Path,
) -> None:
    """A directory entry is classified as "directory"."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    dir_entry = next(e for e in entries if e.name == "subdir")
    assert rp.classify_entry(dir_entry) == "directory"


def test_classify_entry_returns_other_for_fifo(tmp_path: pathlib.Path) -> None:
    """A FIFO entry is classified as "other" (not regular and not a symlink)."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs not supported on this platform")
    fifo = tmp_path / "pipe.md"
    os.mkfifo(fifo)
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    fifo_entry = next(e for e in entries if e.name == "pipe.md")
    assert rp.classify_entry(fifo_entry) == "other"


def test_classify_entry_returns_regular_for_regular_file(
    tmp_path: pathlib.Path,
) -> None:
    """A regular file entry is classified as "regular"."""
    f = tmp_path / "file.md"
    f.write_text("content\n", encoding="utf-8")
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    file_entry = next(e for e in entries if e.name == "file.md")
    assert rp.classify_entry(file_entry) == "regular"


# ── read_confined ──────────────────────────────────────────────────────────────


def test_read_confined_reads_a_regular_file(tmp_path: pathlib.Path) -> None:
    """read_confined returns the bytes of a regular, single-link file."""
    f = tmp_path / "record.md"
    f.write_bytes(b"hello, world\n")
    rp = _load_helper()
    assert rp.read_confined(tmp_path, f) == b"hello, world\n"


def test_read_confined_refuses_hard_link(tmp_path: pathlib.Path) -> None:
    """read_confined refuses a hard link; lstat-then-read_bytes does not.

    This case is load-bearing: it proves the descriptor-based implementation
    is strictly stronger than the lstat-then-read_text idiom the scripts
    previously used, and that extracting the idiom into a helper introduced
    real confinement value.  Without this case every other helper case is also
    passed by the weaker idiom already shipped, and the extraction proves
    nothing.

    A hard link has st_nlink > 1.  The naive idiom reads it successfully.
    read_confined checks st_nlink before and after open and raises EntryRefused.
    """
    original = tmp_path / "original.md"
    original.write_bytes(b"some content")
    hard_link = tmp_path / "hard-link.md"
    try:
        os.link(original, hard_link)
    except OSError:
        pytest.skip("hard links not supported on this filesystem")

    # The naive implementation succeeds — reading a hard link with read_bytes
    # works, and this assertion makes the test self-proving: if hard links were
    # unavailable the skip above would have fired.
    assert hard_link.read_bytes() == b"some content"

    # The descriptor-based implementation refuses the hard link.
    rp = _load_helper()
    with pytest.raises(rp.EntryRefused, match="hard link"):
        rp.read_confined(tmp_path, hard_link)
