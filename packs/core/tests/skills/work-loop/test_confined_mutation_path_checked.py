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


def test_mixed_case_target_name_succeeds_and_containment_normalises(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []
    real = os.path.normcase

    def spy(value: Any) -> Any:
        seen.append(os.fspath(value))
        return real(value)

    monkeypatch.setattr(os.path, "normcase", spy)
    cm.confined_create(root, root / "MiXeD.TXT", b"x")
    assert (root / "MiXeD.TXT").read_bytes() == b"x"
    assert any(s.startswith(str(root)) for s in seen)


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


# ── staging file checks ──────────────────────────────────────────────────────


@pytest.mark.parametrize("op", ["create", "replace"])
def test_staging_identity_mismatch_refused_before_any_byte(
    root: Path, op: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    (root / "a.txt").write_bytes(b"prior")
    if op == "create":
        (root / "a.txt").unlink()
    real_lstat = os.lstat

    def lstat(path: Any, *a: Any, **k: Any) -> Any:
        info = real_lstat(path, *a, **k)
        if Path(os.fspath(path)).name.startswith(".wl-tmp-"):
            fields = {n: getattr(info, n) for n in dir(info) if n.startswith("st_")}
            fields["st_ino"] = info.st_ino + 1
            return types.SimpleNamespace(**fields)
        return info

    writes: list[int] = []
    real_write = os.write

    def write(fd: int, data: Any) -> int:
        writes.append(fd)
        return real_write(fd, data)

    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(os, "write", write)
    assert _denial(op, root, root / "a.txt") == "denied-path-violation"
    monkeypatch.undo()
    assert writes == []
    assert _names(root) == (["a.txt"] if op == "replace" else [])
    if op == "replace":
        assert (root / "a.txt").read_bytes() == b"prior"


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


def test_hook_defaults_to_none_and_is_not_read_from_environment() -> None:
    assert _load()._PRE_COMMIT_HOOK is None
    source = (SCRIPTS / "_confined_mutation.py").read_text(encoding="utf-8")
    assert "environ" not in source and "getenv" not in source


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
