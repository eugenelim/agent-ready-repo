"""Concurrency policy keys: shipped values, ranges, and refusal of anything outside them."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

_HARNESS = Path(__file__).resolve().parent / "supervisor_harness.py"


def _harness() -> ModuleType:
    """Load the shared supervisor test harness under a pack- and skill-qualified name."""
    alias = "core_work_loop_supervisor_harness"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HARNESS)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


admission = _harness().admission

SHIPPED = {
    "concurrency": "sequential",
    "max_concurrent_attempts": 4,
    "reprojection_bound": 2,
    "attempt_timeout_seconds": 3600,
}


def _with(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **changes: object) -> None:
    policy = json.loads(admission._POLICY_PATH.read_text("utf-8"))
    for key, value in changes.items():
        if value is _ABSENT:
            policy.pop(key, None)
        else:
            policy[key] = value
    path = tmp_path / "supervisor-policy.json"
    path.write_text(json.dumps(policy), "utf-8")
    monkeypatch.setattr(admission, "_POLICY_PATH", path)


_ABSENT = object()


def test_the_shipped_policy_is_the_sequential_floor() -> None:
    policy = admission.load_policy()
    assert {key: policy[key] for key in SHIPPED} == SHIPPED


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("concurrency", "sequential"),
        ("concurrency", "enforced-allowlist"),
        ("concurrency", "complete-trace"),
        ("max_concurrent_attempts", 2),
        ("max_concurrent_attempts", 8),
        ("reprojection_bound", 0),
        ("reprojection_bound", 8),
        ("attempt_timeout_seconds", 60),
        ("attempt_timeout_seconds", 86400),
    ],
)
def test_each_range_bound_is_accepted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, key: str, value: object
) -> None:
    _with(monkeypatch, tmp_path, **{key: value})
    assert admission.load_policy()[key] == value


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("concurrency", "parallel"),
        ("concurrency", ""),
        ("concurrency", 1),
        ("concurrency", _ABSENT),
        ("max_concurrent_attempts", 1),
        ("max_concurrent_attempts", 9),
        ("max_concurrent_attempts", "4"),
        ("max_concurrent_attempts", 4.0),
        ("max_concurrent_attempts", True),
        ("max_concurrent_attempts", _ABSENT),
        ("reprojection_bound", -1),
        ("reprojection_bound", 9),
        ("reprojection_bound", 1.5),
        ("reprojection_bound", False),
        ("reprojection_bound", _ABSENT),
        ("attempt_timeout_seconds", 59),
        ("attempt_timeout_seconds", 86401),
        ("attempt_timeout_seconds", "60"),
        ("attempt_timeout_seconds", _ABSENT),
    ],
)
def test_a_value_outside_its_range_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, key: str, value: object
) -> None:
    _with(monkeypatch, tmp_path, **{key: value})
    with pytest.raises(admission.Refusal) as info:
        admission.load_policy()
    assert info.value.code == "invalid-policy"
    assert info.value.owner == "skill maintainer"
    assert key in info.value.detail
