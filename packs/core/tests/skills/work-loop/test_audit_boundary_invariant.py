"""The audit rule at every work-loop security boundary.

Every policy denial at a security boundary (writer authority, broker effect,
process launch, and untrusted launch) with an available sink stores exactly
one ``denied`` security event, and a correlation ID the content-safety check
refuses is stored redacted rather than dropped.  A sink that fails is called
once and never retried.
"""

from __future__ import annotations

import dataclasses
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
CREDENTIAL_SHAPED = "AKIAIOSFODNN7EXAMPLE"


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
def se() -> ModuleType:
    return _load("core_work_loop_audit_inv_se", "_security_events.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    return _load("core_work_loop_audit_inv_sc", "_security_capability.py")


@pytest.fixture(scope="module")
def es() -> ModuleType:
    return _load("core_work_loop_audit_inv_es", "_evidence_store.py")


@pytest.fixture(scope="module")
def pi() -> ModuleType:
    return _load("core_work_loop_audit_inv_pi", "_policy_import.py")


@pytest.fixture(scope="module")
def cn() -> ModuleType:
    return _load("core_work_loop_audit_inv_cn", "_containment.py")


def _forged_grant(sc: ModuleType, grant_id: str) -> object:
    """A caller-built grant the issuer never issued, carrying *grant_id*."""
    issuer = sc.CapabilityIssuer()
    issued = issuer.issue_root_grant(
        roots=["/work"], operations=["append", "write"], trust_class="trusted-adapter",
        writes_allowed_roots=["/work"], control_denies=[],
    )
    return issuer, dataclasses.replace(issued, grant_id=grant_id)


def _denials(events: list) -> list:
    return [e for e in events if e.outcome == "denied"]


class TestWriterAuthorityDenials:
    """A forged grant is refused with its authority code and audited, redacted if needed."""

    @pytest.mark.parametrize("grant_id", ["grant-forged", CREDENTIAL_SHAPED])
    def test_evidence_store_denial_is_audited(
        self, sc: ModuleType, es: ModuleType, grant_id: str
    ) -> None:
        issuer, grant = _forged_grant(sc, grant_id)
        events: list = []
        with pytest.raises(es.EvidenceStoreRefused) as exc_info:
            es._check_producer_authority(
                issuer, grant, audit_sink=events.append,
                record_scope="evidence", required_operations=["append"],
            )
        assert exc_info.value.denial_code == "denied-producer-authority"
        assert len(_denials(events)) == 1, events
        assert all(CREDENTIAL_SHAPED not in repr(e) for e in events)

    @pytest.mark.parametrize("grant_id", ["grant-forged", CREDENTIAL_SHAPED])
    def test_policy_import_denial_is_audited(
        self, sc: ModuleType, pi: ModuleType, grant_id: str
    ) -> None:
        issuer, grant = _forged_grant(sc, grant_id)
        events: list = []
        with pytest.raises(pi.PolicyImportRefused) as exc_info:
            pi._check_writer_authority(
                issuer, grant, audit_sink=events.append,
                record_scope="delivery", required_operations=["append"],
            )
        assert exc_info.value.denial_code == "denied-writer-authority"
        assert len(_denials(events)) == 1, events
        assert all(CREDENTIAL_SHAPED not in repr(e) for e in events)


class _Host:
    """A containment host returning a fixed attestation dict (or none)."""

    def __init__(self, attestation: dict | None) -> None:
        self._attestation = attestation

    def get_attestation(self, spec_dict: dict, grant: object) -> dict | None:
        return self._attestation


class TestContainmentRefusals:
    """Every untrusted-launch refusal with an available sink stores one denial event."""

    @pytest.mark.parametrize(
        ("attestation", "code"),
        [
            (None, "denied-no-verified-containment"),
            ({"schema_version": 99}, None),
            (
                {"schema_version": 1, "host_mechanism": "os-sandbox",
                 "principal_or_sandbox": "sandbox-1", "roots": ("/etc",), "limits": {}},
                "denied-attestation-broader-than-grant",
            ),
        ],
    )
    def test_refusal_is_audited(
        self, sc: ModuleType, cn: ModuleType, attestation: dict | None, code: str | None
    ) -> None:
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/work/narrow"], operations=["read"], trust_class="untrusted",
            writes_allowed_roots=[], control_denies=[],
        )
        events: list = []
        with pytest.raises(cn.ContainmentRefused) as exc_info:
            cn.launch_untrusted({}, grant, host=_Host(attestation), audit_sink=events.append)
        if code is not None:
            assert exc_info.value.denial_code == code
        denials = _denials(events)
        assert len(denials) == 1, events
        assert denials[0].reason_code == exc_info.value.denial_code


class TestRedactionRetryOnlyOnRefusal:
    """A refused event is retried redacted; a failing sink is called once, never retried."""

    def _event(self, se: ModuleType, correlation_id: str) -> object:
        return se.SecurityEvent(
            schema_version=1, operation_id="op-1", correlation_id=correlation_id,
            event_type="policy-denial", outcome="denied", reason_code="denied-invalid-grant",
            timestamp="2026-01-01T00:00:00Z",
        )

    def test_failing_sink_is_called_once_and_keeps_its_correlation(self, se: ModuleType) -> None:
        calls: list = []

        def failing_sink(event: object) -> None:
            calls.append(event)
            raise OSError("sink down")

        with pytest.raises(se.AuditSinkUnavailable):
            se.emit_denial(failing_sink, self._event(se, "grant-safe"))
        se.emit_denial_best_effort(failing_sink, self._event(se, "grant-safe"))
        assert len(calls) == 2, "one call per emission, no retry"
        assert {e.correlation_id for e in calls} == {"grant-safe"}

    def test_refused_event_is_stored_redacted(self, se: ModuleType) -> None:
        stored: list = []
        se.emit_denial(stored.append, self._event(se, CREDENTIAL_SHAPED))
        assert [e.correlation_id for e in stored] == [se.REDACTED_CORRELATION_ID]
