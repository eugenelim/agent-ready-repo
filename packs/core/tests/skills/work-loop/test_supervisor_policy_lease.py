"""The supervisor policy carries the brief-level runner's lease table (AC-0018).

The loader refuses a lease table that is missing, has a missing or extra key, a
value that is not a positive integer, or a retry budget other than 2.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


def _admission() -> ModuleType:
    """Load the supervisor admission module by path under a pack- and skill-unique name."""
    alias = "core_work_loop_policy_lease_supervisor_admission"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _SCRIPTS / "_supervisor_admission.py")
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


adm = _admission()
SHIPPED = json.loads(adm._POLICY_PATH.read_text("utf-8"))


def _load_with(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, policy: dict[str, Any]) -> Any:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), "utf-8")
    monkeypatch.setattr(adm, "_POLICY_PATH", path)
    return adm.load_policy()


def test_the_shipped_policy_carries_the_lease_table() -> None:
    lease = adm.load_policy()["lease"]
    assert lease["retry_budget"] == 2
    assert set(lease["stuck_after_seconds"]) == {"implementer", "reviewer", "slice-session"}
    assert lease["max_slices_in_flight"] >= 1 and lease["heartbeat_seconds"] >= 1


def _without(key: str) -> dict[str, Any]:
    policy = copy.deepcopy(SHIPPED)
    del policy["lease"][key]
    return policy


def _with(path: tuple[str, ...], value: object) -> dict[str, Any]:
    policy = copy.deepcopy(SHIPPED)
    target = policy["lease"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    return policy


def _no_lease() -> dict[str, Any]:
    policy = copy.deepcopy(SHIPPED)
    del policy["lease"]
    return policy


@pytest.mark.parametrize("policy", [
    pytest.param(_no_lease(), id="no-lease-table"),
    pytest.param(_without("heartbeat_seconds"), id="missing-heartbeat"),
    pytest.param(_without("max_slices_in_flight"), id="missing-in-flight-cap"),
    pytest.param(_without("stuck_after_seconds"), id="missing-stuck-after"),
    pytest.param(_with(("extra",), 1), id="extra-key"),
    pytest.param(_with(("stuck_after_seconds", "assessor"), 60), id="extra-agent-kind"),
    pytest.param(_with(("heartbeat_seconds",), "1800"), id="string-value"),
    pytest.param(_with(("heartbeat_seconds",), True), id="bool-value"),
    pytest.param(_with(("max_slices_in_flight",), 0), id="zero-value"),
    pytest.param(_with(("stuck_after_seconds", "reviewer"), -5), id="negative-stuck-after"),
    pytest.param(_with(("retry_budget",), 3), id="budget-not-two"),
    pytest.param(_with(("stuck_after_seconds",), 60), id="stuck-after-not-a-table"),
])
def test_a_bad_lease_table_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, policy: dict[str, Any]) -> None:
    with pytest.raises(adm.Refusal) as caught:
        _load_with(tmp_path, monkeypatch, policy)
    assert caught.value.code == "invalid-policy"
