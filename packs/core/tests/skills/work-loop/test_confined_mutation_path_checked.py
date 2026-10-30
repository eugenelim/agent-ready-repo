"""Path-checked confined writes on a simulated host.

Each case patches only the module's host-capability point to ``path-checked``,
so ``os.lstat`` and the file-safety module stay real on a POSIX run.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


def _load() -> ModuleType:
    alias = "core_work_loop_cm_path_checked"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(alias, str(SCRIPTS / "_confined_mutation.py"))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


cm = _load()

OPS = ("create", "append", "replace")


def _call(op: str, root: Path, target: Path, data: bytes) -> None:
    {
        "create": cm.confined_create,
        "append": cm.confined_append,
        "replace": cm.confined_atomic_replace,
    }[op](root, target, data)


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    base = tmp_path / "root"
    base.mkdir()
    monkeypatch.setattr(cm, "_host_mode", lambda: "path-checked")
    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", None)
    return base.resolve()


def _denial(op: str, root: Path, target: Path, data: bytes = b"new") -> str:
    with pytest.raises(cm.MutationDenied) as caught:
        _call(op, root, target, data)
    return caught.value.denial_code


def _names(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


# ── success ──────────────────────────────────────────────────────────────────


def test_create_writes_exact_bytes(root: Path) -> None:
    cm.confined_create(root, root / "a.txt", b"hello")
    assert (root / "a.txt").read_bytes() == b"hello"
    assert _names(root) == ["a.txt"]


def test_create_in_nested_directory(root: Path) -> None:
    (root / "x" / "y").mkdir(parents=True)
    cm.confined_create(root, root / "x" / "y" / "a.txt", b"deep")
    assert (root / "x" / "y" / "a.txt").read_bytes() == b"deep"


def test_append_adds_after_prior_bytes(root: Path) -> None:
    (root / "a.txt").write_bytes(b"one;")
    cm.confined_append(root, root / "a.txt", b"two;")
    assert (root / "a.txt").read_bytes() == b"one;two;"


@pytest.mark.parametrize("existing", [True, False])
def test_replace_writes_exact_bytes(root: Path, existing: bool) -> None:
    if existing:
        (root / "a.txt").write_bytes(b"old old old")
    cm.confined_atomic_replace(root, root / "a.txt", b"fresh")
    assert (root / "a.txt").read_bytes() == b"fresh"
    assert _names(root) == ["a.txt"]


def test_mixed_case_target_name_succeeds(root: Path) -> None:
    cm.confined_create(root, root / "MiXeD.TXT", b"x")
    assert (root / "MiXeD.TXT").read_bytes() == b"x"


def test_containment_compares_case_normalised_resolved_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Letter case never decides containment; the Windows module covers a real volume."""
    monkeypatch.setattr(os.path, "realpath", lambda p, *a, **k: os.fspath(p))
    monkeypatch.setattr(os.path, "normcase", lambda p: os.fspath(p).lower())
    assert cm._inside(Path("/A/B"), Path("/a/b/C/d")) is True
    assert cm._inside(Path("/A/B"), Path("/a/bc")) is False
    assert cm._inside(Path("/A/B"), Path("/a")) is False


# ── links, special files, hard links ─────────────────────────────────────────


@pytest.mark.parametrize("op", OPS)
def test_symlinked_ancestor_refused(root: Path, op: str) -> None:
    (root / "real").mkdir()
    (root / "real" / "f.txt").write_bytes(b"prior")
    (root / "link").symlink_to(root / "real", target_is_directory=True)
    assert _denial(op, root, root / "link" / "f.txt") == "denied-path-violation"
    assert (root / "real" / "f.txt").read_bytes() == b"prior"
    assert _names(root / "real") == ["f.txt"]


@pytest.mark.parametrize("op", OPS)
def test_symlinked_target_refused(root: Path, op: str) -> None:
    (root / "real.txt").write_bytes(b"prior")
    (root / "t.txt").symlink_to(root / "real.txt")
    assert _denial(op, root, root / "t.txt") == "denied-path-violation"
    assert (root / "real.txt").read_bytes() == b"prior"
    assert (root / "t.txt").is_symlink()
    assert _names(root) == ["real.txt", "t.txt"]


@pytest.mark.parametrize("op", OPS)
def test_non_regular_target_refused(root: Path, op: str) -> None:
    (root / "d").mkdir()
    assert _denial(op, root, root / "d") == "denied-path-violation"
    assert _names(root) == ["d"]


@pytest.mark.parametrize("op", OPS)
def test_hard_linked_target_refused(root: Path, op: str) -> None:
    (root / "a.txt").write_bytes(b"prior")
    os.link(root / "a.txt", root / "b.txt")
    assert _denial(op, root, root / "a.txt") == "denied-path-violation"
    assert (root / "a.txt").read_bytes() == b"prior"
    assert (root / "b.txt").read_bytes() == b"prior"
    assert _names(root) == ["a.txt", "b.txt"]


@pytest.mark.parametrize("op", OPS)
def test_reparse_attribute_refused(root: Path, op: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A reparse attribute on a directory ancestor refuses, as a Windows junction would."""
    (root / "j").mkdir()
    (root / "j" / "f.txt").write_bytes(b"prior")
    real = os.lstat

    def lstat(path: Any, *a: Any, **k: Any) -> Any:
        info = real(path, *a, **k)
        if Path(os.fspath(path)).name == "j":
            fields = {n: getattr(info, n) for n in dir(info) if n.startswith("st_")}
            fields["st_file_attributes"] = 0x400
            return types.SimpleNamespace(**fields)
        return info

    monkeypatch.setattr(os, "lstat", lstat)
    assert _denial(op, root, root / "j" / "f.txt") == "denied-path-violation"
    monkeypatch.undo()
    assert (root / "j" / "f.txt").read_bytes() == b"prior"


# ── lexical forms: refused before any filesystem call ────────────────────────

LEXICAL = [
    "a:b",
    "a.txt:stream",
    "C:drive-relative",
    "CON",
    "con",
    "CON.txt",
    "prn.log",
    "AUX",
    "NUL.x.y",
    "COM1",
    "com9.txt",
    "LPT1",
    "lpt9.log",
    "CONIN$",
    "CONOUT$",
    "CONIN$.txt",
    "name.",
    "name ",
    "dir./f.txt",
    "CON/f.txt",
    "d:x/f.txt",
    "\\\\?\\x",
    "\\\\.\\x",
    "\\\\server\\share",
]


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("relative", LEXICAL)
def test_lexical_forms_refused_before_any_filesystem_call(
    root: Path, op: str, relative: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = root / relative
    calls: list[str] = []

    def trap(name: str) -> Callable[..., Any]:
        def inner(*a: Any, **k: Any) -> Any:
            calls.append(name)
            raise AssertionError(name)

        return inner

    with monkeypatch.context() as m:
        for name in ("lstat", "stat", "open", "link", "replace", "unlink", "fstat", "mkdir"):
            m.setattr(os, name, trap(name))
        m.setattr(os.path, "realpath", trap("realpath"))
        code = _denial(op, root, target)
    assert code == "denied-path-violation"
    assert calls == []
    assert _names(root) == []


# ── late detection through the pre-commit hook ───────────────────────────────


def _swap_ancestor_for_symlink(root: Path) -> Callable[[Path], None]:
    def hook(target: Path) -> None:
        sub = target.parent
        sub.rename(root / "sub.orig")
        sub.symlink_to(root / "sub.orig", target_is_directory=True)

    return hook


@pytest.mark.parametrize("op", OPS)
def test_ancestor_swapped_before_commit_is_late_detection(
    root: Path, op: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    (root / "sub").mkdir()
    if op != "create":
        (root / "sub" / "f.txt").write_bytes(b"prior")
    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", _swap_ancestor_for_symlink(root))
    assert _denial(op, root, root / "sub" / "f.txt") == "denied-rollback-failed"


@pytest.mark.parametrize("op", ["create", "replace"])
def test_hard_link_added_to_committed_target_is_late_detection(
    root: Path, op: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if op == "replace":
        (root / "f.txt").write_bytes(b"prior")

    def hook(target: Path) -> None:
        (stage,) = [p for p in target.parent.iterdir() if p.name.startswith(".wl-tmp-")]
        os.link(stage, target.parent / "alias.txt")

    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", hook)
    assert _denial(op, root, root / "f.txt") == "denied-rollback-failed"


def test_append_whose_path_is_renamed_away_is_late_detection(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (root / "f.txt").write_bytes(b"prior")

    def hook(target: Path) -> None:
        target.rename(target.parent / "moved.txt")

    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", hook)
    assert _denial("append", root, root / "f.txt") == "denied-rollback-failed"


@pytest.mark.parametrize("op", OPS)
def test_hook_receives_the_target_path(root: Path, op: str, monkeypatch: pytest.MonkeyPatch) -> None:
    if op != "create":
        (root / "f.txt").write_bytes(b"prior")
    seen: list[Path] = []
    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", lambda target: seen.append(Path(target)))
    _call(op, root, root / "f.txt", b"x")
    assert seen == [root / "f.txt"]


def test_hook_is_none_on_a_fresh_load_under_a_populated_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("_PRE_COMMIT_HOOK", "PRE_COMMIT_HOOK", "CONFINED_MUTATION_PRE_COMMIT_HOOK"):
        monkeypatch.setenv(name, "os:system")
    assert _load()._PRE_COMMIT_HOOK is None


# ── unsafe host and the capability query ─────────────────────────────────────


@pytest.mark.parametrize("op", OPS)
def test_unsafe_host_refuses_each_operation(root: Path, op: str, monkeypatch: pytest.MonkeyPatch) -> None:
    (root / "a.txt").write_bytes(b"prior")
    monkeypatch.setattr(cm, "_host_mode", lambda: "unsafe")
    assert _denial(op, root, root / "a.txt") == "denied-unsafe-host"
    assert (root / "a.txt").read_bytes() == b"prior"
    assert _names(root) == ["a.txt"]


@pytest.mark.parametrize(
    ("mode", "expected"), [("descriptor", True), ("path-checked", False), ("unsafe", False)]
)
def test_race_free_mutation_follows_host_mode(
    mode: str, expected: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cm, "_host_mode", lambda: mode)
    assert cm.race_free_mutation() is expected
    assert "race_free_mutation" in cm.__all__


def test_host_mode_reads_capabilities_without_a_filesystem_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def trap(*a: Any, **k: Any) -> Any:
        raise AssertionError("filesystem call")

    with monkeypatch.context() as m:
        for name in ("lstat", "stat", "open"):
            m.setattr(os, name, trap)
        m.setattr(cm._fs, "_supports_descriptor_walk", lambda: True)
        assert cm._host_mode() == "descriptor"
        m.setattr(cm._fs, "_supports_descriptor_walk", lambda: False)
        m.setattr(os, "stat_result", type("R", (), {"st_file_attributes": 0}))
        assert cm._host_mode() == "path-checked"
        m.setattr(os, "stat_result", type("R", (), {}))
        assert cm._host_mode() == "unsafe"


# ── a root given by an alias of its long name ────────────────────────────────


def _alias_host(root: Path, alias: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make *alias* stand for *root* in ``lstat`` and ``realpath`` only."""
    real_lstat, real_realpath = os.lstat, os.path.realpath

    def swap(value: Any) -> Any:
        text = os.fspath(value)
        return str(root) + text[len(str(alias)) :] if text.startswith(str(alias)) else value

    monkeypatch.setattr(os, "lstat", lambda p, *a, **k: real_lstat(swap(p), *a, **k))
    monkeypatch.setattr(os.path, "realpath", lambda p, *a, **k: real_realpath(swap(p), *a, **k))


@pytest.mark.parametrize("op", OPS)
def test_root_given_as_alias_with_target_in_long_form_succeeds(
    root: Path, op: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    alias = root.parent / "ROOT~1"
    if op != "create":
        (root / "f.txt").write_bytes(b"prior;")
    _alias_host(root, alias, monkeypatch)
    _call(op, alias, root / "f.txt", b"new")
    monkeypatch.undo()
    expected = {"create": b"new", "append": b"prior;new", "replace": b"new"}[op]
    assert (root / "f.txt").read_bytes() == expected


def test_target_outside_an_unrelated_root_is_still_refused(root: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    assert _denial("create", other, root / "f.txt") == "denied-path-violation"
    assert _names(root) == []


# ── one host-mode decision per call ──────────────────────────────────────────


@pytest.mark.parametrize("mode", ["descriptor", "path-checked"])
@pytest.mark.parametrize("op", OPS)
def test_each_operation_chooses_the_host_mode_once(
    root: Path, op: str, mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if op != "create":
        (root / "f.txt").write_bytes(b"prior")
    calls: list[str] = []

    def counted() -> str:
        calls.append(mode)
        return mode

    monkeypatch.setattr(cm, "_host_mode", counted)
    _call(op, root, root / "f.txt", b"x")
    assert calls == [mode]


# ── lexical refusal comes before the root is resolved ────────────────────────


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("name", ["CON", "a:b", "name.", "NUL.txt", "bad?name"])
def test_lexical_refusal_precedes_resolving_a_mismatched_root(
    root: Path, op: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A root that is not a textual prefix of the target (an alias) is resolved only
    after the target's own components pass the lexical checks."""
    alias = root.parent / "ROOT~1"
    calls: list[str] = []

    def trap(label: str) -> Callable[..., Any]:
        def inner(*a: Any, **k: Any) -> Any:
            calls.append(label)
            raise AssertionError(label)

        return inner

    with monkeypatch.context() as m:
        for label in ("lstat", "stat", "open", "fstat"):
            m.setattr(os, label, trap(label))
        m.setattr(os.path, "realpath", trap("realpath"))
        code = _denial(op, alias, root / name)
    assert code == "denied-path-violation"
    assert calls == []


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("form", ["\\\\?\\x", "\\\\.\\x", "\\\\server\\share"])
def test_prefix_forms_as_the_whole_target_refused_before_any_call(
    root: Path, op: str, form: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    with monkeypatch.context() as m:
        for label in ("lstat", "stat", "open", "fstat"):
            m.setattr(os, label, lambda *a, **k: (_ for _ in ()).throw(AssertionError("fs")))
        m.setattr(os.path, "realpath", lambda *a, **k: (_ for _ in ()).throw(AssertionError("fs")))
        assert _denial(op, root, Path(form)) == "denied-path-violation"


# ── staging file: each failed check refuses, writes no byte, removes only its file ──


def _stage_files(directory: Path) -> list[str]:
    return [p.name for p in directory.iterdir() if p.name.startswith(".wl-tmp-")]


def _fake(info: Any, **changes: Any) -> Any:
    fields = {n: getattr(info, n) for n in dir(info) if n.startswith("st_")}
    fields.update(changes)
    return types.SimpleNamespace(**fields)


@pytest.fixture
def writes(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    seen: list[int] = []
    real = os.write

    def write(fd: int, data: Any) -> int:
        seen.append(fd)
        return real(fd, data)

    monkeypatch.setattr(os, "write", write)
    return seen


def _arrange_staging_failure(
    kind: str, root: Path, monkeypatch: pytest.MonkeyPatch
) -> Path | None:
    """Make the freshly created staging file fail one named check; return a file to keep."""
    real_open, real_lstat, real_fstat, real_realpath = os.open, os.lstat, os.fstat, os.path.realpath
    keep = root / "keep.txt"
    stage_fds: set[int] = set()

    def opening(path: Any, flags: int, *a: Any, **k: Any) -> int:
        fd = real_open(path, flags, *a, **k)
        if Path(os.fspath(path)).name.startswith(".wl-tmp-"):
            stage_fds.add(fd)
            if kind == "link-count":
                os.link(path, keep)
        return fd

    seen_lstat: set[str] = set()

    def lstat(path: Any, *a: Any, **k: Any) -> Any:
        info = real_lstat(path, *a, **k)
        name = Path(os.fspath(path)).name
        if kind == "identity" and name.startswith(".wl-tmp-") and name not in seen_lstat:
            seen_lstat.add(name)
            return _fake(info, st_ino=info.st_ino + 1)
        return info

    def fstat(fd: int) -> Any:
        info = real_fstat(fd)
        if kind == "reparse" and fd in stage_fds:
            return _fake(info, st_file_attributes=0x400)
        return info

    def realpath(path: Any, *a: Any, **k: Any) -> Any:
        if kind == "containment" and Path(os.fspath(path)).name.startswith(".wl-tmp-"):
            return str(root.parent / "elsewhere" / "stage")
        return real_realpath(path, *a, **k)

    monkeypatch.setattr(os, "open", opening)
    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(os, "fstat", fstat)
    monkeypatch.setattr(os.path, "realpath", realpath)
    return keep if kind == "link-count" else None


@pytest.mark.parametrize("kind", ["identity", "link-count", "reparse", "containment"])
@pytest.mark.parametrize("op", ["create", "replace"])
def test_staging_check_failure_refuses_without_a_byte_and_removes_only_its_file(
    root: Path, op: str, kind: str, writes: list[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    bystander = root / "bystander.txt"
    bystander.write_bytes(b"mine")
    if op == "replace":
        (root / "a.txt").write_bytes(b"prior")
    keep = _arrange_staging_failure(kind, root, monkeypatch)
    assert _denial(op, root, root / "a.txt") == "denied-path-violation"
    monkeypatch.undo()
    assert writes == []
    assert _stage_files(root) == []
    assert bystander.read_bytes() == b"mine"
    if op == "replace":
        assert (root / "a.txt").read_bytes() == b"prior"
    else:
        assert not (root / "a.txt").exists()
    if keep is not None:
        assert keep.read_bytes() == b""


def test_staging_cleanup_leaves_a_file_that_is_not_the_one_created(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_open = os.open

    def opening(path: Any, flags: int, *a: Any, **k: Any) -> int:
        fd = real_open(path, flags, *a, **k)
        name = Path(os.fspath(path))
        if name.name.startswith(".wl-tmp-"):
            name.rename(name.parent / "ours.moved")
            name.write_bytes(b"someone else's file")
        return fd

    monkeypatch.setattr(os, "open", opening)
    assert _denial("create", root, root / "a.txt") == "denied-path-violation"
    monkeypatch.undo()
    (other,) = [p for p in root.iterdir() if p.name.startswith(".wl-tmp-")]
    assert other.read_bytes() == b"someone else's file"
    assert not (root / "a.txt").exists()


# ── late detection: the target path names a different, clean regular file ────


def _swap_stage_for_other_file(target: Path) -> None:
    (stage,) = [p for p in target.parent.iterdir() if p.name.startswith(".wl-tmp-")]
    # Keep the original inode alive under another name, so the replacement can
    # never be handed the same (st_dev, st_ino) by a filesystem that reuses them.
    stage.rename(target.parent / "stage.kept")
    stage.write_bytes(b"a different file")


@pytest.mark.parametrize("op", ["create", "replace"])
def test_committed_target_that_is_a_different_clean_file_is_late_detection(
    root: Path, op: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if op == "replace":
        (root / "f.txt").write_bytes(b"prior")
    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", _swap_stage_for_other_file)
    assert _denial(op, root, root / "f.txt") == "denied-rollback-failed"
    info = os.lstat(root / "f.txt")
    assert info.st_nlink == 1 and (root / "f.txt").read_bytes() == b"a different file"


def test_append_whose_path_now_names_another_clean_file_is_late_detection(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (root / "f.txt").write_bytes(b"prior")

    def hook(target: Path) -> None:
        target.rename(target.parent / "moved.txt")
        target.write_bytes(b"another file")

    monkeypatch.setattr(cm, "_PRE_COMMIT_HOOK", hook)
    assert _denial("append", root, root / "f.txt") == "denied-rollback-failed"
    assert (root / "f.txt").read_bytes() == b"another file"


# ── exclusive-create cleanup removes the target only while it is ours ────────


def test_failed_stage_unlink_after_link_leaves_a_target_that_is_not_ours(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_link, real_unlink = os.link, Path.unlink

    def link(src: Any, dst: Any, *a: Any, **k: Any) -> None:
        real_link(src, dst, *a, **k)
        target = Path(os.fspath(dst))
        target.rename(target.parent / "t.txt.ours")
        target.write_bytes(b"someone else's file")

    def unlink(self: Path, *a: Any, **k: Any) -> None:
        if self.name.startswith(".wl-tmp-"):
            raise PermissionError("simulated: staging name cannot be removed")
        real_unlink(self, *a, **k)

    monkeypatch.setattr(os, "link", link)
    monkeypatch.setattr(Path, "unlink", unlink)
    assert _denial("create", root, root / "t.txt") == "denied-rollback-failed"
    monkeypatch.undo()
    assert (root / "t.txt").read_bytes() == b"someone else's file"


def test_failed_stage_unlink_after_link_still_removes_our_own_target(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_unlink = Path.unlink

    def unlink(self: Path, *a: Any, **k: Any) -> None:
        if self.name.startswith(".wl-tmp-"):
            raise PermissionError("simulated: staging name cannot be removed")
        real_unlink(self, *a, **k)

    monkeypatch.setattr(Path, "unlink", unlink)
    assert _denial("create", root, root / "t.txt") == "denied-rollback-failed"
    monkeypatch.undo()
    assert not (root / "t.txt").exists()


# ── lexical refusals cover only the path below the root ──────────────────────


@pytest.fixture(params=["aux", "release 1.0.", "con.d"])
def odd_root(request: pytest.FixtureRequest, root: Path) -> Path:
    base = root / request.param / "work"
    base.mkdir(parents=True)
    return base


@pytest.mark.parametrize("op", OPS)
def test_a_root_under_an_odd_name_accepts_an_ordinary_target(odd_root: Path, op: str) -> None:
    if op != "create":
        (odd_root / "f.txt").write_bytes(b"prior;")
    _call(op, odd_root, odd_root / "f.txt", b"new")
    expected = {"create": b"new", "append": b"prior;new", "replace": b"new"}[op]
    assert (odd_root / "f.txt").read_bytes() == expected


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("name", ["CON", "a:b", "name.", "bad?name"])
def test_the_same_forms_below_an_odd_root_refuse_without_a_filesystem_call(
    odd_root: Path, op: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def trap(*a: Any, **k: Any) -> Any:
        raise AssertionError("filesystem call")

    with monkeypatch.context() as m:
        for label in ("lstat", "stat", "open", "fstat"):
            m.setattr(os, label, trap)
        m.setattr(os.path, "realpath", trap)
        assert _denial(op, odd_root, odd_root / name) == "denied-path-violation"


@pytest.mark.parametrize("op", OPS)
def test_a_unc_like_root_accepts_an_ordinary_target(
    tmp_path: Path, op: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A root whose own text begins with two backslashes is not refused for that."""
    monkeypatch.chdir(tmp_path)
    unc = Path("\\\\srv\\share")
    unc.mkdir()
    monkeypatch.setattr(cm, "_host_mode", lambda: "path-checked")
    if op != "create":
        (unc / "f.txt").write_bytes(b"prior;")
    _call(op, unc, unc / "f.txt", b"new")
    expected = {"create": b"new", "append": b"prior;new", "replace": b"new"}[op]
    assert (unc / "f.txt").read_bytes() == expected
