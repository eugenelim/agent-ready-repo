"""The supervisor's git timeout: resolution of ``WORK_LOOP_GIT_TIMEOUT_S`` and its ceiling.

Not integration-gated: the resolver is a pure function, so these run in the default lane.
"""

from __future__ import annotations

import importlib.util
import itertools
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
_VARIABLE = "WORK_LOOP_GIT_TIMEOUT_S"
_counter = itertools.count()


def _load(name: str) -> ModuleType:
    """Load a fresh copy of a work-loop script under a unique, registered module name."""
    alias = f"core_work_loop_timeout_{name}_{next(_counter)}"
    spec = importlib.util.spec_from_file_location(alias, _SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module  # its dataclasses look the module up by name while it runs
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fresh_git() -> Iterator[ModuleType]:
    module = _load("_supervisor_git")
    yield module
    sys.modules.pop(module.__name__, None)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, 60.0),
        ("", 60.0),
        ("60", 60.0),
        ("90", 90.0),
        ("90.5", 90.5),
        (" 90 ", 90.0),
        ("1e2", 100.0),
        ("1_00", 100.0),
        ("240", 240.0),
        ("5", 60.0),
        ("0", 60.0),
        ("-3", 60.0),
        ("9000", 240.0),
        ("abc", 60.0),
        ("10m", 60.0),
        ("nan", 60.0),
        ("inf", 60.0),
        ("-inf", 60.0),
        ("1e309", 60.0),
    ],
)
def test_resolver_returns_the_specified_value(
    fresh_git: ModuleType, raw: str | None, expected: float
) -> None:
    """AC-0001 to AC-0004: unset and unusable values give 60, the rest clamp to 60-240."""
    assert fresh_git._resolve_git_timeout(raw) == expected


def test_the_module_binds_the_variable_at_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-0001, AC-0002 at the import boundary."""
    monkeypatch.setenv(_VARIABLE, "120")
    loaded = _load("_supervisor_git")
    try:
        assert loaded.GIT_TIMEOUT_S == 120.0
    finally:
        sys.modules.pop(loaded.__name__, None)
    monkeypatch.delenv(_VARIABLE)
    loaded = _load("_supervisor_git")
    try:
        assert loaded.GIT_TIMEOUT_S == 60.0
    finally:
        sys.modules.pop(loaded.__name__, None)


def test_the_ceiling_fits_the_run_lock_margin(fresh_git: ModuleType) -> None:
    """AC-0007: one call at the ceiling must fit the margin the lock invariant leaves for git."""
    admission = _load("_supervisor_admission")
    try:
        assert fresh_git._TIMEOUT_CEILING_S <= admission._LOCK_MARGIN_SECONDS
    finally:
        sys.modules.pop(admission.__name__, None)
