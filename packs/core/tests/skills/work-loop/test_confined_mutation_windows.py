"""Path-checked confined writes on a real Windows host.

Nothing is patched except the module's pre-commit test seam. Junctions are real,
hard links are real, and the short-name alias comes from the volume itself.
The module skips only off Windows, and the CI step fails on any skipped case.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

if sys.platform != "win32":
    pytest.skip("Windows-only module", allow_module_level=True)

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


def _load() -> ModuleType:
    alias = "core_work_loop_cm_windows"
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


def _junction(link: Path, target: Path) -> None:
    """Create a real directory junction; no privilege is needed."""
    try:
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    except (ImportError, AttributeError, OSError):
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
        )
    assert os.path.isjunction(link) if hasattr(os.path, "isjunction") else link.exists()


def _denial(op: str, root: Path, target: Path, data: bytes = b"new") -> str:
    with pytest.raises(cm.MutationDenied) as caught:
        _call(op, root, target, data)
    return caught.value.denial_code


def _names(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.iterdir())


@pytest.fixture
def root(tmp_path: Path) -> Path:
    base = tmp_path / "LongRootDirectoryName"
    base.mkdir()
    return Path(os.path.realpath(base))


@pytest.fixture(autouse=True)
def _hook_reset() -> object:
    cm._PRE_COMMIT_HOOK = None
    yield
    cm._PRE_COMMIT_HOOK = None


def test_host_is_path_checked_and_not_race_free() -> None:
    assert cm._host_mode() == "path-checked"
    assert cm.race_free_mutation() is False


# AC-0001


def test_create_writes_exact_bytes(root: Path) -> None:
    cm.confined_create(root, root / "a.txt", b"hello")
    assert (root / "a.txt").read_bytes() == b"hello"
    assert _names(root) == ["a.txt"]


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


# AC-0002: a real junction ancestor


@pytest.mark.parametrize("op", OPS)
def test_junction_ancestor_refused(root: Path, op: str) -> None:
    (root / "real").mkdir()
    (root / "real" / "f.txt").write_bytes(b"prior")
    _junction(root / "junc", root / "real")
    assert _denial(op, root, root / "junc" / "f.txt") == "denied-path-violation"
    assert (root / "real" / "f.txt").read_bytes() == b"prior"
    assert _names(root / "real") == ["f.txt"]


# AC-0003: a hard-linked target


@pytest.mark.parametrize("op", OPS)
def test_hard_linked_target_refused(root: Path, op: str) -> None:
    (root / "a.txt").write_bytes(b"prior")
    os.link(root / "a.txt", root / "b.txt")
    assert _denial(op, root, root / "a.txt") == "denied-path-violation"
    assert (root / "a.txt").read_bytes() == b"prior"
    assert (root / "b.txt").read_bytes() == b"prior"
    assert _names(root) == ["a.txt", "b.txt"]


# AC-0004: lexical forms on a real host

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


def _lexical_target(root: Path, form: str) -> Path:
    """The target the module is given for one lexical form, never a pathlib join.

    A join reinterprets drive-relative and rooted forms, and pathlib folds a
    doubled separator, so a form that starts with two backslashes (UNC, device,
    extended-length) is passed as the whole target; every other form is
    appended to the root as raw text on whatever drive the runner uses.

    Such a form cannot reach the module as a component below the root: joined as
    text, pathlib folds the doubled separator, so the extended-length form turns
    into a name with a question mark and the device and UNC forms turn into
    ordinary names. As the whole target it shares no prefix with the root, so the
    module judges its components after that prefix and refuses the form.
    """
    return Path(form) if form.startswith("\\\\") else Path(str(root) + "\\" + form)


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("form", LEXICAL)
def test_lexical_forms_refused(root: Path, op: str, form: str) -> None:
    assert _denial(op, root, _lexical_target(root, form)) == "denied-path-violation"
    assert _names(root) == []


# AC-0005: letter case and the short-name alias


@pytest.mark.parametrize("op", OPS)
def test_root_and_target_in_different_letter_case_succeed(root: Path, op: str) -> None:
    (root / "f.txt").write_bytes(b"prior;")
    swapped = Path(str(root).swapcase())
    assert str(swapped) != str(root)
    if op == "create":
        cm.confined_create(swapped, root / "g.txt", b"new")
        assert (root / "g.txt").read_bytes() == b"new"
    else:
        _call(op, swapped, root / "f.txt", b"new")
        expected = {"append": b"prior;new", "replace": b"new"}[op]
        assert (root / "f.txt").read_bytes() == expected


def _short_alias(path: Path) -> Path:
    out = subprocess.run(
        f'cmd /c for %I in ("{path}") do @echo %~sI',
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(out)


@pytest.mark.parametrize("op", OPS)
def test_root_given_as_short_alias_with_long_target_succeeds(root: Path, op: str) -> None:
    alias = _short_alias(root)
    if os.path.normcase(str(alias)) == os.path.normcase(str(root)):
        pytest.fail(f"the volume produced no short name for {root}; enable 8dot3 names")
    (root / "f.txt").write_bytes(b"prior;")
    if op == "create":
        cm.confined_create(alias, root / "g.txt", b"new")
        assert (root / "g.txt").read_bytes() == b"new"
    else:
        _call(op, alias, root / "f.txt", b"new")
        assert (root / "f.txt").read_bytes() == {"append": b"prior;new", "replace": b"new"}[op]


# AC-0007: an ancestor swapped for a real junction before the commit call


def _swap_for_junction(root: Path, log: list[str]) -> Callable[[Path], None]:
    def hook(target: Path) -> None:
        sub = target.parent
        try:
            sub.rename(root / "sub.orig")
        except OSError:
            log.append("rename-blocked")
            return
        _junction(sub, root / "sub.orig")
        log.append("swapped")

    return hook


@pytest.mark.parametrize("op", ["create", "replace"])
def test_ancestor_swapped_for_junction_is_late_detection(root: Path, op: str) -> None:
    (root / "sub").mkdir()
    if op == "replace":
        (root / "sub" / "f.txt").write_bytes(b"prior")
    log: list[str] = []
    cm._PRE_COMMIT_HOOK = _swap_for_junction(root, log)
    assert _denial(op, root, root / "sub" / "f.txt") == "denied-rollback-failed"
    assert log == ["swapped"]


def test_append_swap_is_late_detection_or_blocked_by_the_open_handle(root: Path) -> None:
    """The append holds the file open, so Windows may refuse to move its ancestor.

    Either the swap lands and the operation reports state unknown, or the swap
    is refused and the append succeeds with exactly the bytes supplied.
    """
    (root / "sub").mkdir()
    (root / "sub" / "f.txt").write_bytes(b"prior;")
    log: list[str] = []
    cm._PRE_COMMIT_HOOK = _swap_for_junction(root, log)
    try:
        cm.confined_append(root, root / "sub" / "f.txt", b"new")
    except cm.MutationDenied as exc:
        assert log == ["swapped"]
        assert exc.denial_code == "denied-rollback-failed"
    else:
        assert log == ["rename-blocked"]
        assert (root / "sub" / "f.txt").read_bytes() == b"prior;new"
