"""Record validators and launch boundaries never raise on a malformed field.

Every field of a containment attestation and a process spec is replaced, one
at a time, with each value in a fixed set of wrong types and edge values.  The
validators must always return a ``(bool, str)`` decision, and the launch
boundaries must either succeed or refuse with their own refusal type after
storing a ``denied`` security event.  An exception of any other type, or a
refusal with no stored denial, fails the test.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
)
PYTHON = str(Path(sys.executable).resolve())

ODD_VALUES: tuple[object, ...] = (
    None, True, 0, -1, 1.5, float("nan"), 2**70,
    "", "x", "\x00", [], ["x"], [1], {}, {"a": 1},
)


def _load(name: str, filename: str) -> ModuleType:
    """Load a work-loop script by path under a unique name."""
    path = SCRIPTS / filename
    assert stat.S_ISREG(os.lstat(path).st_mode), path
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


@pytest.fixture(scope="module")
def cn() -> ModuleType:
    return _load("core_work_loop_totality_cn", "_containment.py")


@pytest.fixture(scope="module")
def ps() -> ModuleType:
    return _load("core_work_loop_totality_ps", "_process_safety.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    return _load("core_work_loop_totality_sc", "_security_capability.py")


def _attestation() -> dict:
    return {
        "schema_version": 1, "host_mechanism": "os-sandbox",
        "principal_or_sandbox": "sandbox-1", "roots": ["/work"], "limits": {},
    }


def _spec(cwd: str) -> dict:
    return {
        "schema_version": 1,
        "executable": PYTHON,
        "executable_identity": hashlib.sha256(Path(PYTHON).read_bytes()).hexdigest(),
        "argv": ["-c", "pass"],
        "grant_id": "grant-totality",
        "cwd": cwd,
        "environment_allowlist": [],
        "stdin_mode": "closed",
        "process_tree_timeout_s": 10,
        "output_bound_bytes": 1024,
    }


class _Host:
    def __init__(self, attestation: object) -> None:
        self._attestation = attestation

    def get_attestation(self, spec_dict: dict, grant: object) -> object:
        return self._attestation


def _attestation_cases(cn: ModuleType) -> list[tuple[str, object]]:
    fields = sorted(cn._ALLOWED_ATTESTATION_KEYS)
    return [(field, value) for field in fields for value in ODD_VALUES]


def _spec_cases(ps: ModuleType) -> list[tuple[str, object]]:
    fields = sorted(ps._ALLOWED_SPEC_KEYS)
    return [(field, value) for field in fields for value in ODD_VALUES]


def test_attestation_validator_never_raises(cn: ModuleType) -> None:
    for field, value in _attestation_cases(cn):
        record = _attestation()
        record[field] = value
        ok, code = cn.validate_attestation_dict(record)
        assert isinstance(ok, bool) and isinstance(code, str), (field, value)
    for record in ODD_VALUES:
        ok, _ = cn.validate_attestation_dict(record)
        assert ok is False, record


def test_spec_validator_never_raises(ps: ModuleType, tmp_path: Path) -> None:
    for field, value in _spec_cases(ps):
        record = _spec(str(tmp_path))
        record[field] = value
        ok, code = ps.validate_process_spec_dict(record)
        assert isinstance(ok, bool) and isinstance(code, str), (field, value)
    for record in ODD_VALUES:
        ok, _ = ps.validate_process_spec_dict(record)
        assert ok is False, record


def test_untrusted_launch_refuses_every_malformed_attestation_with_an_audit(
    cn: ModuleType, sc: ModuleType
) -> None:
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["/work"], operations=["read"], trust_class="untrusted",
        writes_allowed_roots=[], control_denies=[],
    )
    for field, value in _attestation_cases(cn):
        record = _attestation()
        record[field] = value
        events: list = []
        with pytest.raises(Exception) as exc_info:
            cn.launch_untrusted({}, grant, host=_Host(record), audit_sink=events.append)
        kind = type(exc_info.value).__name__
        assert kind in {"ContainmentRefused", "ProcessDenied"}, (field, value, kind)
        assert any(e.outcome == "denied" for e in events), (field, value)


def test_safe_launch_refuses_every_malformed_spec_with_an_audit(
    ps: ModuleType, tmp_path: Path
) -> None:
    for field, value in _spec_cases(ps):
        record = _spec(str(tmp_path))
        record[field] = value
        events: list = []
        try:
            ps.launch_safe_process(record, cwd_roots=(str(tmp_path),), audit_sink=events.append)
        except ps.ProcessDenied:
            assert any(e.outcome == "denied" for e in events), (field, value)
