"""Construction tests for the unregistered captured item's closed state.

Spec: docs/specs/captured-item-registration-stop/spec.md (AC-0001 to AC-0007).
Verification mode: TDD.

A captured-item file that no registry entry names settles a dependency by its
own ``Status:`` and ``Resolution:``. Each case plants one file and a waiting
spec, and asserts the outcome of the canonical reconciliation.

The AC-0005 outcomes are literals recorded once against the engine at commit
``dd4f7038c``; ``_AC0005_BUILDERS`` is the list of cases that were recorded.
"""
from __future__ import annotations

import builtins
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

_TESTS = Path(__file__).parent
_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm/skills/workspace-status/scripts"
_ENGINE_MODULE = "workspace_status_engine_captured_item_registration_stop"
_HELPERS_MODULE = "workspace_status_test_helpers_registration_stop"


def _load(name: str, path: Path) -> ModuleType:
    """Load a module by file path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


ENGINE = _load(_ENGINE_MODULE, _SCRIPTS / "workspace_status_engine.py")
_H = _load(_HELPERS_MODULE, _TESTS / "test_captured_item_files_equivalence.py")
Case, WAITER, observe = _H.Case, _H.WAITER, _H.observe
_note, _record, _write_repo = _H._note, _H._record, _H._write_repo

DIR = "docs/product/captured"
LOOSE = f"{DIR}/loose.md"
KINDS = ("defect", "design", "research", "intent")
RESOLUTIONS = ("fixed", "declined", "superseded")
RECEIPT = "completion d-1 completed merge pr:812"


def _plant(root: Path, case: Case, receipt: bool = False) -> None:
    """Write the case; a receipt line is added to the waiter when asked."""
    _write_repo(root, case)
    if receipt:
        waiter = root / WAITER
        waiter.write_text(
            waiter.read_text(encoding="utf-8")
            + f"- **Dependency receipts:** {case.depends_on} {RECEIPT}\n",
            encoding="utf-8",
        )


def _waiting(files: dict[str, str], depends_on: str = LOOSE, cooled: tuple[str, ...] = ()) -> Case:
    return Case("p", files, (), depends_on=depends_on, cooled=cooled)


def _unregistered(kind: str, status: str, resolution: str | None) -> Case:
    return _waiting({LOOSE: _note(kind, status, resolution)})


SATISFIED = {"findings": [], "dispatchable": {WAITER: True}}


def _unsatisfied(path: str = LOOSE, code: str = "unsatisfied_dependency") -> dict[str, Any]:
    return {"findings": [[code, path]], "dispatchable": {WAITER: False}}


# stub: true
def test_unregistered_closed_fixed_design_satisfies(tmp_path):
    path = "docs/product/captured/loose.md"
    case = Case("p", {path: _note("design", "Closed", "fixed")}, (), depends_on=path)
    _write_repo(tmp_path, case)
    assert observe(tmp_path) == {"findings": [], "dispatchable": {WAITER: True}}


# AC-0001 ------------------------------------------------------------------


def _failing(*fields: str) -> str | None:
    text = "# Item\n\n" + "\n".join(fields) + "\n"
    return ENGINE.parse_captured_item(text)[1]


@pytest.mark.parametrize("kind", KINDS)
def test_closed_without_resolution_is_invalid_for_every_kind(kind: str) -> None:
    """AC-0001: `Closed` needs a `Resolution:` whatever the kind."""
    assert _failing("- **Status:** Closed", f"- **Kind:** {kind}") == "Resolution"


@pytest.mark.parametrize("kind", KINDS)
def test_open_with_resolution_is_invalid_for_every_kind(kind: str) -> None:
    """AC-0001, regression pin: `Open` with a `Resolution:` is invalid at `dd4f7038c` too."""
    assert (
        _failing("- **Status:** Open", f"- **Kind:** {kind}", "- **Resolution:** fixed")
        == "Resolution"
    )


@pytest.mark.parametrize("kind", KINDS)
def test_closed_with_resolution_is_valid_for_every_kind(kind: str) -> None:
    assert _failing("- **Status:** Closed", f"- **Kind:** {kind}", "- **Resolution:** fixed") is None


# AC-0002, AC-0003 ---------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_closed_fixed_satisfies(tmp_path: Path, kind: str) -> None:
    """AC-0002: an unregistered `Closed`, `fixed` file satisfies, whatever its kind."""
    _plant(tmp_path, _unregistered(kind, "Closed", "fixed"))
    assert observe(tmp_path) == SATISFIED


@pytest.mark.parametrize("resolution", ["declined", "superseded"])
@pytest.mark.parametrize("kind", KINDS)
def test_closed_declined_or_superseded_is_unsatisfied(
    tmp_path: Path, kind: str, resolution: str
) -> None:
    """AC-0003: `Closed` with another resolution gives `unsatisfied_dependency`."""
    _plant(tmp_path, _unregistered(kind, "Closed", resolution))
    assert observe(tmp_path) == _unsatisfied()


@pytest.mark.parametrize("kind", KINDS)
def test_open_is_unsatisfied(tmp_path: Path, kind: str) -> None:
    """AC-0003: an `Open` file gives `unsatisfied_dependency`."""
    _plant(tmp_path, _unregistered(kind, "Open", None))
    assert observe(tmp_path) == _unsatisfied()


# AC-0004 ------------------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_otherwise_invalid_file_gives_its_invalid_finding(tmp_path: Path, kind: str) -> None:
    """AC-0004: a captured `Kind:` and a bad `Type:` give `invalid_captured_item`."""
    text = _note(kind, "Closed", "fixed") + "- **Type:** nonsense\n"
    _plant(tmp_path, _waiting({LOOSE: text}))
    assert observe(tmp_path) == _unsatisfied(code="invalid_captured_item")


def test_closed_without_resolution_gives_its_invalid_finding(tmp_path: Path) -> None:
    """AC-0004: the new `Resolution:` rule reaches a waiter's dependency."""
    _plant(tmp_path, _unregistered("design", "Closed", None))
    assert observe(tmp_path) == _unsatisfied(code="invalid_captured_item")


# AC-0005 ------------------------------------------------------------------
# Each builder plants a case whose outcome the engine at `dd4f7038c` decided.


def _variant(root: Path) -> bool:
    path = "docs/product/Captured/loose.md"
    _plant(root, _waiting({path: _note("design", "Closed", "fixed")}, depends_on=path))
    return False


def _symlink(root: Path) -> bool:
    _plant(root, _waiting({LOOSE: _note("design", "Closed", "fixed")}))
    (root / LOOSE).unlink()
    (root / LOOSE).symlink_to(root / "workspace.toml")
    return False


def _unreadable(root: Path) -> bool:
    _plant(root, _waiting({LOOSE: _note("design", "Closed", "fixed")}))
    (root / LOOSE).unlink()
    (root / LOOSE).mkdir()
    return False


def _no_kind(root: Path) -> bool:
    _plant(root, _waiting({LOOSE: "# Item\n\n- **Status:** Closed\n- **Resolution:** fixed\n"}))
    return False


def _non_captured_kind(root: Path) -> bool:
    text = "# Item\n\n- **Status:** Closed\n- **Resolution:** fixed\n- **Kind:** spec\n"
    _plant(root, _waiting({LOOSE: text}))
    return False


def _cooled(root: Path) -> bool:
    files = {LOOSE: _note("design", "Closed", "fixed"), "docs/lifecycle/loose.json": _record("loose", LOOSE)}
    _plant(root, _waiting(files, cooled=(LOOSE,)))
    (root / LOOSE).unlink()
    (root / LOOSE).mkdir()
    return True


def _missing(root: Path) -> bool:
    _plant(root, _waiting({}))
    return False


def _missing_with_receipt(root: Path) -> bool:
    _plant(root, _waiting({}), receipt=True)
    return False


_AC0005_BUILDERS: dict[str, Callable[[Path], bool]] = {
    "variant-spelling": _variant,
    "symlink": _symlink,
    "unreadable": _unreadable,
    "no-kind": _no_kind,
    "non-captured-kind": _non_captured_kind,
    "cooled": _cooled,
    "missing": _missing,
    "missing-with-receipt": _missing_with_receipt,
}


# The outcomes of the engine at commit dd4f7038c, recorded once.
_AC0005_AT_DD4F: dict[str, dict[str, Any]] = {
    "variant-spelling": {"findings": [["unreadable_artifact", WAITER]], "dispatchable": {WAITER: False}},
    "symlink": {"findings": [["unreadable_artifact", WAITER]], "dispatchable": {WAITER: False}},
    "unreadable": {"findings": [["unreadable_artifact", WAITER]], "dispatchable": {WAITER: False}},
    "no-kind": {"findings": [["invalid_dependency", WAITER]], "dispatchable": {WAITER: False}},
    "non-captured-kind": {
        "findings": [["invalid_captured_item", LOOSE]], "dispatchable": {WAITER: False},
    },
    "cooled": {"findings": [["invalid_dependency", WAITER]], "dispatchable": {WAITER: False}},
    "missing": {"findings": [["missing_dependency", LOOSE]], "dispatchable": {WAITER: False}},
    # A completion receipt cannot apply to a captured item, so the receipt line adds a finding.
    "missing-with-receipt": {
        "findings": [["invalid_dependency", WAITER], ["missing_dependency", LOOSE]],
        "dispatchable": {WAITER: False},
    },
}


@pytest.fixture
def opens(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every path the process opens through the stdlib's open calls."""
    seen: list[str] = []
    real_builtin, real_os, real_path = builtins.open, os.open, pathlib.Path.open

    def note(target: object) -> None:
        if isinstance(target, (str, bytes, os.PathLike)):
            seen.append(os.fsdecode(target))

    def spy_builtin(file, *args, **kwargs):  # type: ignore[no-untyped-def]
        note(file)
        return real_builtin(file, *args, **kwargs)

    def spy_os(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        note(path)
        return real_os(path, *args, **kwargs)

    def spy_path(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        note(self)
        return real_path(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy_builtin)
    monkeypatch.setattr(os, "open", spy_os)
    monkeypatch.setattr(pathlib.Path, "open", spy_path)
    return seen


@pytest.mark.parametrize("name", sorted(_AC0005_BUILDERS))
def test_unchanged_routes_give_the_outcome_at_dd4f7038c(
    tmp_path: Path, name: str, opens: list[str]
) -> None:
    """AC-0005: variant, link, unreadable, kindless, cooled, and missing paths."""
    _AC0005_BUILDERS[name](tmp_path)
    opens.clear()  # planting the repository opens files; only the run is watched
    assert observe(tmp_path) == _AC0005_AT_DD4F[name]
    if name == "cooled":
        assert not any(path.endswith("/" + LOOSE) for path in opens)


# AC-0006 ------------------------------------------------------------------


def _run_status(root: Path) -> dict[str, Any]:
    done = subprocess.run(
        [sys.executable, "-I", str(_SCRIPTS / "workspace_status.py"), "status", "--root", str(root)],
        capture_output=True, text=True, check=False,
    )
    return json.loads(done.stdout)


def _named(output: dict[str, Any], path: str) -> list[Any]:
    findings = output["captured"]["findings"] + output["canonical"]["findings"]
    return [f for f in findings if path in json.dumps(f)]


def test_valid_unregistered_items_give_no_finding(tmp_path: Path) -> None:
    """AC-0006: one valid file per kind, with and without `Type:`, in each status."""
    paths: list[str] = []
    files: dict[str, str] = {}
    for kind in KINDS:
        for typed in (False, True):
            for status, resolution in (("Open", None), *(("Closed", r) for r in RESOLUTIONS)):
                text = _note(kind, status, resolution) + ("- **Type:** shape\n" if typed else "")
                path = f"{DIR}/{kind}-{'typed' if typed else 'plain'}-{status.lower()}-{resolution or 'none'}.md"
                files[path] = text
                paths.append(path)
    _write_repo(tmp_path, Case("p", files, ()))
    output = _run_status(tmp_path)
    assert len(output["captured"]["items"]) == len(paths)
    assert output["captured"]["findings"] == []
    assert output["canonical"]["findings"] == []


def test_own_missing_target_gives_no_finding(tmp_path: Path) -> None:
    """AC-0006, regression pin of the accepted removal: passes at `dd4f7038c` too."""
    text = _note("design", "Open") + f"- **Depends on:** {DIR}/gone.md\n"
    _write_repo(tmp_path, Case("p", {LOOSE: text}, ()))
    assert _named(_run_status(tmp_path), LOOSE) == []


def test_own_cycle_gives_no_finding(tmp_path: Path) -> None:
    """AC-0006, regression pin of the accepted removal: passes at `dd4f7038c` too."""
    other = f"{DIR}/other.md"
    files = {
        LOOSE: _note("design", "Open") + f"- **Depends on:** {other}\n",
        other: _note("design", "Open") + f"- **Depends on:** {LOOSE}\n",
    }
    _write_repo(tmp_path, Case("p", files, ()))
    output = _run_status(tmp_path)
    assert _named(output, LOOSE) == [] and _named(output, other) == []


def test_waiter_finding_names_only_the_dependency(tmp_path: Path) -> None:
    """AC-0006: the AC-0003 finding for a waiter is the one finding naming the file."""
    _plant(tmp_path, _unregistered("design", "Open", None))
    output = _run_status(tmp_path)
    assert [f["code"] for f in _named(output, LOOSE)] == ["unsatisfied_dependency"]
