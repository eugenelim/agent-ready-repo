"""Confined regular-file read and race regressions."""

import hashlib
import os
import stat
import threading
from collections.abc import Callable
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
        (".agents/rules/example.md", ".agents"),
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
        (".agents/rules/example.md", ".agents/rules"),
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
        ".agents/rules/example.md",
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
        ".agents/rules/example.md",
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


# --- write_confined_regular_file -------------------------------------------

write_confined = file_safety.write_confined_regular_file


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(params=["descriptor", "fallback"])
def walk_mode(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> str:
    """Run each write test with and without descriptor-relative opening."""
    if request.param == "fallback":
        monkeypatch.setattr(file_safety, "_supports_descriptor_walk", lambda: False)
    return str(request.param)


def _fail_once(real: Callable[..., object], counter: dict[str, int]):
    def wrapper(*args: object, **kwargs: object) -> object:
        counter["n"] += 1
        if counter["n"] == 1:
            raise OSError("injected failure")
        return real(*args, **kwargs)

    return wrapper


def test_create_writes_exact_bytes(tmp_path, walk_mode):
    """AC-0032."""
    target = tmp_path / "new.md"
    write_confined(tmp_path, target, b"hello\n", expect_sha256=None)
    assert target.read_bytes() == b"hello\n"


def test_create_refuses_anything_present(tmp_path, walk_mode):
    """AC-0033."""
    present = tmp_path / "present.md"
    present.write_bytes(b"keep")
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, present, b"new", expect_sha256=None)
    assert present.read_bytes() == b"keep"

    dangling = tmp_path / "dangling.md"
    try:
        dangling.symlink_to(tmp_path / "nowhere.md")
    except OSError:
        pytest.skip("links not available")
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, dangling, b"new", expect_sha256=None)
    assert dangling.is_symlink()
    assert not (tmp_path / "nowhere.md").exists()


def test_update_keeps_the_inode(tmp_path, walk_mode):
    """AC-0034."""
    target = tmp_path / "t.md"
    target.write_bytes(b"old content that is long")
    before = target.stat()
    write_confined(tmp_path, target, b"new", expect_sha256=_digest(b"old content that is long"))
    after = target.stat()
    assert target.read_bytes() == b"new"
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)


def test_update_refuses_digest_mismatch_or_absent(tmp_path, walk_mode):
    """AC-0035."""
    target = tmp_path / "t.md"
    target.write_bytes(b"old")
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"new", expect_sha256=_digest(b"other"))
    assert target.read_bytes() == b"old"
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, tmp_path / "gone.md", b"new", expect_sha256=_digest(b"old"))
    assert not (tmp_path / "gone.md").exists()


_SHAPES = (
    "symlink",
    "hardlink",
    "directory",
    "fifo",
    "symlink-component",
    "outside-root",
    "dot-segment",
    "missing-parent",
)


@pytest.mark.parametrize("shape", _SHAPES)
@pytest.mark.parametrize("update", [False, True])
def test_refused_target_shapes(tmp_path, walk_mode, shape, update):
    """AC-0036."""
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_bytes(b"secret")
    expected: bytes | None = None
    try:
        if shape == "symlink":
            (root / "real.md").write_bytes(b"real")
            target = root / "link.md"
            target.symlink_to(root / "real.md")
            expected = b"real"
        elif shape == "hardlink":
            (root / "real.md").write_bytes(b"real")
            target = root / "hard.md"
            os.link(root / "real.md", target)
            expected = b"real"
        elif shape == "directory":
            target = root / "dir"
            target.mkdir()
        elif shape == "fifo":
            if not hasattr(os, "mkfifo"):
                pytest.skip("FIFOs not available")
            target = root / "pipe"
            os.mkfifo(target)
        elif shape == "symlink-component":
            (root / "linked").symlink_to(outside, target_is_directory=True)
            target = root / "linked" / "secret.md"
            expected = b"secret"
        elif shape == "outside-root":
            target = outside / "secret.md"
            expected = b"secret"
        elif shape == "dot-segment":
            (root / "sub").mkdir()
            target = root / "sub" / ".." / "x.md"
        else:
            target = root / "absent" / "x.md"
    except OSError:
        pytest.skip("links not available")
    digest = _digest(expected) if (update and expected is not None) else (
        _digest(b"x") if update else None
    )
    with pytest.raises(UnsafeContentError):
        write_confined(root, target, b"new", expect_sha256=digest)
    if expected is not None:
        assert target.read_bytes() == expected
    if shape in ("symlink-component", "outside-root"):
        assert (outside / "secret.md").read_bytes() == b"secret"
    assert not (outside / "x.md").exists()
    assert not (root / "x.md").exists()


def test_fifo_target_returns_promptly(tmp_path, walk_mode):
    """AC-0037."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs not available")
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    outcomes: list[type[BaseException]] = []

    def attempt() -> None:
        for digest in (None, _digest(b"x")):
            try:
                write_confined(tmp_path, pipe, b"new", expect_sha256=digest)
            except UnsafeContentError:
                outcomes.append(UnsafeContentError)

    thread = threading.Thread(target=attempt, daemon=True)
    thread.start()
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert outcomes == [UnsafeContentError, UnsafeContentError]


def test_identity_change_after_open_is_refused(tmp_path, monkeypatch, walk_mode):
    """AC-0038."""
    target = tmp_path / "t.md"
    target.write_bytes(b"old")
    real_fstat = os.fstat

    def shifted(descriptor: int):
        inspected = real_fstat(descriptor)
        if stat.S_ISREG(inspected.st_mode):
            return SimpleNamespace(
                st_mode=inspected.st_mode,
                st_nlink=inspected.st_nlink,
                st_dev=inspected.st_dev,
                st_ino=inspected.st_ino + 1,
                st_size=inspected.st_size,
            )
        return inspected

    monkeypatch.setattr(os, "fstat", shifted)
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"new", expect_sha256=_digest(b"old"))
    monkeypatch.undo()
    assert target.read_bytes() == b"old"


def test_digest_is_read_from_the_descriptor_that_is_written(tmp_path, monkeypatch, walk_mode):
    """AC-0039."""
    target = tmp_path / "t.md"
    target.write_bytes(b"old")
    reads: list[int] = []
    writes: list[int] = []
    real_read, real_write = os.read, os.write

    def read(descriptor: int, size: int) -> bytes:
        reads.append(descriptor)
        return real_read(descriptor, size)

    def write(descriptor: int, data) -> int:
        writes.append(descriptor)
        return real_write(descriptor, data)

    monkeypatch.setattr(os, "read", read)
    monkeypatch.setattr(os, "write", write)
    write_confined(tmp_path, target, b"new", expect_sha256=_digest(b"old"))
    assert reads and writes
    assert set(reads) == set(writes) and len(set(writes)) == 1


@pytest.mark.parametrize("failing", ["write", "ftruncate", "fsync"])
def test_failed_update_restores_original(tmp_path, monkeypatch, walk_mode, failing):
    """AC-0040."""
    target = tmp_path / "t.md"
    original = b"original bytes that are long"
    target.write_bytes(original)
    counter = {"n": 0}
    if failing == "write":
        real_write = os.write

        def partial_then_fail(descriptor: int, data) -> int:
            # Part of the data reaches the file first, so only the restore can undo it.
            counter["n"] += 1
            if counter["n"] == 1:
                real_write(descriptor, bytes(data)[:2])
                raise OSError("injected failure")
            return real_write(descriptor, data)

        monkeypatch.setattr(os, "write", partial_then_fail)
    else:
        monkeypatch.setattr(os, failing, _fail_once(getattr(os, failing), counter))
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"short", expect_sha256=_digest(original))
    monkeypatch.undo()
    assert target.read_bytes() == original


def test_failed_restore_still_raises(tmp_path, monkeypatch, walk_mode):
    """AC-0111."""
    target = tmp_path / "t.md"
    target.write_bytes(b"old")

    def broken(*args: object, **kwargs: object) -> int:
        raise OSError("injected failure")

    monkeypatch.setattr(os, "write", broken)
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"new", expect_sha256=_digest(b"old"))


def test_failed_create_removes_only_what_it_created(tmp_path, monkeypatch, walk_mode):
    """AC-0041."""
    target = tmp_path / "t.md"

    def broken(*args: object, **kwargs: object) -> int:
        raise OSError("injected failure")

    monkeypatch.setattr(os, "write", broken)
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"new", expect_sha256=None)
    monkeypatch.undo()
    assert not target.exists()


def test_failed_create_keeps_a_swapped_in_file(tmp_path, monkeypatch, walk_mode):
    """AC-0041: the cleanup unlinks only a file with the descriptor's identity."""
    target = tmp_path / "t.md"
    other = tmp_path / "other.md"
    other.write_bytes(b"other")

    def swap_then_fail(descriptor: int) -> None:
        target.unlink()
        other.rename(target)
        raise OSError("injected failure")

    monkeypatch.setattr(os, "fsync", swap_then_fail)
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"new", expect_sha256=None)
    monkeypatch.undo()
    assert target.read_bytes() == b"other"


def test_short_and_zero_writes(tmp_path, monkeypatch, walk_mode):
    """AC-0042."""
    real_write = os.write

    def one_byte(descriptor: int, data) -> int:
        return real_write(descriptor, bytes(data)[:1])

    monkeypatch.setattr(os, "write", one_byte)
    target = tmp_path / "t.md"
    write_confined(tmp_path, target, b"abcdef", expect_sha256=None)
    assert target.read_bytes() == b"abcdef"
    write_confined(tmp_path, target, b"xyz", expect_sha256=_digest(b"abcdef"))
    assert target.read_bytes() == b"xyz"

    monkeypatch.setattr(os, "write", lambda descriptor, data: 0)
    zero = tmp_path / "zero.md"
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, zero, b"abc", expect_sha256=None)
    assert not zero.exists()


def test_malformed_arguments_raise_value_error(tmp_path):
    target = tmp_path / "t.md"
    with pytest.raises(ValueError):
        write_confined(tmp_path, target, "text", expect_sha256=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        write_confined(tmp_path, target, b"x", expect_sha256="ABC")
    with pytest.raises(ValueError):
        write_confined(tmp_path, target, b"x", expect_sha256=_digest(b"x").upper())
    assert not target.exists()


def test_fallback_create_writes_nothing_when_path_resolves_outside_root(
    tmp_path, monkeypatch
):
    """AC-0109."""
    monkeypatch.setattr(file_safety, "_supports_descriptor_walk", lambda: False)
    target = tmp_path / "t.md"
    real_resolve = Path.resolve

    def resolve(self: Path, strict: bool = False) -> Path:
        if self.name == "t.md":
            return Path("/elsewhere/t.md")
        return real_resolve(self, strict=strict)

    writes: list[int] = []
    real_write = os.write

    def recording_write(descriptor: int, data) -> int:
        writes.append(descriptor)
        return real_write(descriptor, data)

    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(os, "write", recording_write)
    with pytest.raises(UnsafeContentError):
        write_confined(tmp_path, target, b"new", expect_sha256=None)
    monkeypatch.undo()
    assert writes == []
    assert not target.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits")
def test_create_makes_an_owner_only_file(tmp_path: Path) -> None:
    target = tmp_path / "GOVERNANCE.md"
    file_safety.write_confined_regular_file(tmp_path, target, b"x", expect_sha256=None)
    assert stat.S_IMODE(target.stat().st_mode) & 0o077 == 0
