"""Record validators and launch boundaries never raise on a malformed field.

Every field of a containment attestation and a process spec is replaced, one
at a time, with each value in a fixed set of wrong types and edge values.  The
validators must always return a ``(bool, str)`` decision, and the launch
boundaries must either succeed or refuse with their own refusal type after
storing a ``denied`` security event.  An exception of any other type, or a
refusal with no stored denial, fails the test.
"""

from __future__ import annotations

import contextlib
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


def _assert_schema_valid_events(events: list, context: object) -> None:
    """Every stored event is a valid ``security-event.v1`` record that encodes as JSON."""
    import json
    import math

    for event in events:
        record = {
            "schema_version": event.schema_version, "operation_id": event.operation_id,
            "correlation_id": event.correlation_id, "event_type": event.event_type,
            "outcome": event.outcome, "reason_code": event.reason_code,
            "timestamp": event.timestamp,
        }
        assert record["schema_version"] == 1 and record["schema_version"] is not True, context
        for key in ("operation_id", "correlation_id", "event_type", "reason_code", "timestamp"):
            assert isinstance(record[key], str) and record[key], (context, key, record[key])
        assert record["outcome"] in {"allowed", "denied"}, context
        assert not any(isinstance(v, float) and math.isnan(v) for v in record.values())
        json.dumps(record, allow_nan=False)


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
        _assert_schema_valid_events(events, (field, value))


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
        _assert_schema_valid_events(events, (field, value))


class _RaisingHost:
    def get_attestation(self, spec_dict: dict, grant: object) -> object:
        raise RuntimeError("host failure /private/detail")


class _RaisingIssuer:
    def verify_grant(self, grant: object) -> bool:
        raise RuntimeError("issuer failure")


class _GrantWithoutId:
    roots = ("/work",)


@pytest.mark.parametrize(
    ("host", "issuer", "grant_kind"),
    [
        (_RaisingHost(), None, "issued"),
        (None, _RaisingIssuer(), "issued"),
        (None, "real", "no-id"),
    ],
)
def test_untrusted_launch_audits_host_and_issuer_failures(
    cn: ModuleType, sc: ModuleType, host: object, issuer: object, grant_kind: str
) -> None:
    """A raising host, a raising issuer, or an unverifiable grant still ends audited."""
    real_issuer = sc.CapabilityIssuer()
    grant: object = (
        real_issuer.issue_root_grant(
            roots=["/work"], operations=["read"], trust_class="untrusted",
            writes_allowed_roots=[], control_denies=[],
        )
        if grant_kind == "issued" else _GrantWithoutId()
    )
    events: list = []
    with pytest.raises(cn.ContainmentRefused):
        cn.launch_untrusted(
            {}, grant,
            host=host if host is not None else _Host(_attestation()),
            issuer=real_issuer if issuer == "real" else issuer,
            audit_sink=events.append,
        )
    assert [e.outcome for e in events] == ["denied"], events
    _assert_schema_valid_events(events, (host, issuer, grant_kind))


@pytest.mark.parametrize("value", ODD_VALUES)
def test_safe_launch_never_stores_a_malformed_correlation(
    ps: ModuleType, tmp_path: Path, value: object
) -> None:
    """Odd caller correlation and operation IDs never reach a stored event."""
    record = _spec(str(tmp_path))
    record["grant_id"] = value
    events: list = []
    with contextlib.suppress(ps.ProcessDenied):
        ps.launch_safe_process(
            record, cwd_roots=(str(tmp_path),), audit_sink=events.append,
            correlation_id=value, operation_id=value,
        )
    assert events, value
    _assert_schema_valid_events(events, value)


@pytest.mark.parametrize("raiser", ["host", "issuer"])
def test_untrusted_launch_audits_a_refusal_raised_by_host_or_issuer(
    cn: ModuleType, sc: ModuleType, raiser: str
) -> None:
    """A ContainmentRefused from host or issuer code is re-audited under a stable code."""

    class RefusingHost:
        def get_attestation(self, spec_dict: dict, grant: object) -> object:
            raise cn.ContainmentRefused("host-made-up-code", "host refused")

    class RefusingIssuer:
        def verify_grant(self, grant: object) -> bool:
            raise cn.ContainmentRefused("issuer-made-up-code", "issuer refused")

    real_issuer = sc.CapabilityIssuer()
    grant = real_issuer.issue_root_grant(
        roots=["/work"], operations=["read"], trust_class="untrusted",
        writes_allowed_roots=[], control_denies=[],
    )
    events: list = []
    with pytest.raises(cn.ContainmentRefused) as exc_info:
        cn.launch_untrusted(
            {}, grant,
            host=RefusingHost() if raiser == "host" else _Host(_attestation()),
            issuer=RefusingIssuer() if raiser == "issuer" else None,
            audit_sink=events.append,
        )
    assert exc_info.value.denial_code in cn.ATTESTATION_DENIAL_CODES
    assert [e.outcome for e in events] == ["denied"], events
    _assert_schema_valid_events(events, raiser)


@pytest.mark.parametrize("value", ODD_VALUES)
def test_untrusted_launch_never_stores_a_malformed_operation_id(
    cn: ModuleType, sc: ModuleType, value: object
) -> None:
    """Odd caller operation IDs never reach a stored event at the untrusted boundary."""
    real_issuer = sc.CapabilityIssuer()
    grant = real_issuer.issue_root_grant(
        roots=["/work"], operations=["read"], trust_class="untrusted",
        writes_allowed_roots=[], control_denies=[],
    )
    events: list = []
    with pytest.raises(cn.ContainmentRefused):
        cn.launch_untrusted({}, grant, host=_Host(None), audit_sink=events.append,
                            operation_id=value)
    assert events, value
    _assert_schema_valid_events(events, value)


@pytest.mark.parametrize("field", ["read_enforcement", "trace_coverage"])
def test_present_but_null_optional_string_is_refused(cn: ModuleType, field: str) -> None:
    """A present-but-null optional string field fails validation, as the schema requires."""
    record = _attestation()
    record[field] = None
    ok, _ = cn.validate_attestation_dict(record)
    assert ok is False
