"""The audit rule at every work-loop security boundary.

Every policy denial at a security boundary (writer authority, broker effect,
process launch, and untrusted launch) with an available sink stores exactly
one ``denied`` security event, and a correlation ID the content-safety check
refuses is stored redacted rather than dropped.  A sink that fails is called
once and never retried.

Additional invariants tested here:
- A credential-shaped ``operation_id`` is redacted on retry just like a
  credential-shaped ``correlation_id``, so no denial is ever lost when the
  sink is available.
- Every refusal that follows an allow event at the evidence-store and
  policy-import boundaries stores a matching ``denied`` event for the same
  operation ID, leaving the audit log internally consistent.
- Recovery refuses an evidence log that exceeds the declared size bound.
- A frame appended between recovery's read and its in-place truncation is
  preserved because the size re-check under the advisory lock refuses
  truncation when the file has grown.
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


class TestCredentialShapedOperationId:
    """A credential-shaped operation_id is redacted on retry so no denial is ever lost."""

    def test_credential_operation_id_stores_one_redacted_event(self, se: ModuleType) -> None:
        """emit_denial with a credential-shaped operation_id stores one redacted event."""
        stored: list = []
        event = se.SecurityEvent(
            schema_version=1,
            operation_id=CREDENTIAL_SHAPED,  # credential-shaped — triggers content safety refusal
            correlation_id="correlation-safe",
            event_type="capability-check",
            outcome="denied",
            reason_code="denied-invalid-grant",
            timestamp="2026-01-01T00:00:00Z",
        )
        se.emit_denial(stored.append, event)
        # Exactly one event is stored (the redacted retry).
        assert len(stored) == 1, stored
        # The stored event must not contain the credential-shaped value.
        assert CREDENTIAL_SHAPED not in repr(stored[0])
        # The retry uses a fresh operation_id (not the credential-shaped one).
        assert stored[0].operation_id != CREDENTIAL_SHAPED


# ── Helper fixtures shared by evidence-store and policy-import denial tests ───


def _null_sink_abi(event: object) -> None:
    """A no-op audit sink."""


def _make_grant_abi(sc: ModuleType) -> tuple:
    """Return a valid (issuer, grant) pair for evidence append tests."""
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


def _make_receipt_abi(receipt_id: str) -> dict:
    """Build a minimal valid evidence-receipt.v1 record."""
    return {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "acceptance_fingerprint": "fp-abi-test",
        "lineage": {"criterion_ref": "prop-001"},
        "selector": {"term": "test-run"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "test-result"},
        "outcome": "passed",
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _allows(events: list) -> list:
    return [e for e in events if getattr(e, "outcome", None) == "allowed"]


class TestPostAllowEvidenceStoreDenials:
    """Each post-allow refusal in the evidence store stores a matching denied event."""

    @pytest.mark.parametrize(
        "cause",
        ["invalid_receipt_missing_fields", "invalid_supersession_missing_fields"],
    )
    def test_post_allow_denial_stored_for_validation_failure(
        self,
        es: ModuleType,
        sc: ModuleType,
        tmp_path: Path,
        cause: str,
    ) -> None:
        """A validation refusal after the allow event stores a matched denied event."""
        log_path = tmp_path / f"ev-{cause}.log"
        store = es.EvidenceStore(log_path)
        store.open()
        issuer, grant = _make_grant_abi(sc)
        events: list = []

        if cause == "invalid_receipt_missing_fields":
            # Passes content safety but fails validate_receipt_dict (missing fields).
            bad = {"schema_version": 1, "receipt_id": "r-bad-abi"}
            with pytest.raises(es.EvidenceStoreRefused):
                store.append_receipt(
                    bad,
                    transaction_id="tx-bad-abi",
                    issuer=issuer,
                    grant=grant,
                    audit_sink=events.append,
                )
        else:
            # Passes content safety but fails validate_supersession_dict (missing fields).
            bad_sup = {"schema_version": 1, "supersession_id": "sup-bad-abi"}
            with pytest.raises(es.EvidenceStoreRefused):
                store.append_supersession(
                    bad_sup,
                    transaction_id="tx-sup-bad-abi",
                    acceptance_fingerprint="fp-abi-test",
                    issuer=issuer,
                    grant=grant,
                    audit_sink=events.append,
                )

        allows = _allows(events)
        denials = _denials(events)
        assert len(allows) == 1, f"expected 1 allow, got: {events}"
        assert len(denials) == 1, f"expected 1 denial, got: {events}"
        # The denial must share the operation_id with the allow event.
        assert allows[0].operation_id == denials[0].operation_id, (
            f"allow op_id={allows[0].operation_id!r} != "
            f"denial op_id={denials[0].operation_id!r}"
        )


# ── Policy-import post-allow denial tests ─────────────────────────────────────

_SPEC_TEXT_ABI = (
    "# Test spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n- [ ] AC-001.\n"
)
_PLAN_TEXT_ABI = (
    "# Test plan\n\n- **Status:** Approved\n\n## Tasks\n\n### T1\n\n- [ ] Done\n"
)
_VALID_REFS_ABI = {
    "spec_policy": "approval:spec-policy:v1",
    "scope_and_non_goals": "approval:scope:v1",
    "authority_and_security": "approval:authority:v1",
    "public_contracts": "approval:contracts:v1",
    "durable_outputs": "approval:outputs:v1",
    "accepted_risk": "approval:risk:v1",
}


def _make_pi_grant(sc: ModuleType) -> tuple:
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["delivery"],
        operations=["append", "write"],
        trust_class="trusted",
        writes_allowed_roots=["delivery"],
        control_denies=[],
    )
    return issuer, grant


class TestPostAllowPolicyImportDenials:
    """Each post-allow refusal in policy import stores a matching denied event."""

    @pytest.fixture(autouse=True)
    def _setup_files(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.md"
        plan = tmp_path / "plan.md"
        spec.write_text(_SPEC_TEXT_ABI, encoding="utf-8")
        plan.write_text(_PLAN_TEXT_ABI, encoding="utf-8")
        self._spec_path = spec
        self._plan_path = plan
        self._tmp = tmp_path

    @pytest.mark.parametrize(
        ("cause", "kwargs_override"),
        [
            ("empty_terminal_intent", {"terminal_intent": ""}),
            ("spec_digest_mismatch", {"approved_spec_digest": "a" * 64}),
            ("plan_digest_mismatch", {"approved_plan_digest": "b" * 64}),
            ("envelope_mismatch", {"approved_envelope_fingerprint": "fp-wrong"}),
        ],
    )
    def test_post_allow_denial_stored(
        self,
        pi: ModuleType,
        sc: ModuleType,
        cause: str,
        kwargs_override: dict,
    ) -> None:
        """A post-allow refusal in import_policy stores a denial with the same op_id."""
        issuer, grant = _make_pi_grant(sc)

        # Compute correct pins so we can override one.
        import importlib.util as _ilu

        acc_path = SCRIPTS / "_acceptance.py"
        assert stat.S_ISREG(os.lstat(acc_path).st_mode)
        acc_spec = _ilu.spec_from_file_location("_abi_acc", str(acc_path))
        assert acc_spec and acc_spec.loader
        acc_mod = _ilu.module_from_spec(acc_spec)
        acc_spec.loader.exec_module(acc_mod)  # type: ignore[union-attr]

        spec_d = pi.compute_spec_digest(self._spec_path)
        plan_d = pi.compute_plan_digest(self._plan_path)
        env_fp: str = acc_mod.derive_envelope(_VALID_REFS_ABI)["envelope_fingerprint"]

        base_kwargs: dict = {
            "spec_path": self._spec_path,
            "plan_path": self._plan_path,
            "refs": _VALID_REFS_ABI,
            "terminal_intent": "code",
            "writer_grant": grant,
            "issuer": issuer,
            "audit_sink": [].append,
            "store": pi.ImportStore(),
            "approval_identity": "authority-generic",
            "approval_role": "spec-policy-owner",
            "reviewer_identity": "reviewer-generic",
            "reviewer_role": "plan-review-authority",
            "approved_spec_digest": spec_d,
            "approved_plan_digest": plan_d,
            "approved_envelope_fingerprint": env_fp,
        }
        base_kwargs.update(kwargs_override)

        events: list = []
        base_kwargs["audit_sink"] = events.append

        with pytest.raises(pi.PolicyImportRefused):
            pi.import_policy(**base_kwargs)

        allows = _allows(events)
        denials = _denials(events)
        assert len(allows) == 1, f"[{cause}] expected 1 allow, got: {events}"
        assert len(denials) == 1, f"[{cause}] expected 1 denial, got: {events}"
        assert allows[0].operation_id == denials[0].operation_id, (
            f"[{cause}] allow op_id={allows[0].operation_id!r} "
            f"!= denial op_id={denials[0].operation_id!r}"
        )


class TestRecoveryBound:
    """Recovery refuses a log that exceeds the declared size bound."""

    def test_log_over_bound_raises_store_error(
        self, es: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_load_and_truncate raises EvidenceStoreError when the log exceeds _EVIDENCE_LOG_MAX_BYTES."""
        # Set a tiny bound so we can write a small file that exceeds it.
        monkeypatch.setattr(es, "_EVIDENCE_LOG_MAX_BYTES", 10)
        log_path = tmp_path / "huge.log"
        log_path.write_bytes(b"x" * 11)  # 11 bytes > 10-byte monkeypatched bound
        store = es.EvidenceStore(log_path)
        with pytest.raises(es.EvidenceStoreError):
            store.open()


class TestRecoveryPreservesConcurrentFrame:
    """A frame appended between recovery's read and its truncation is preserved."""

    def test_truncate_log_safe_skips_when_file_grew(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """_truncate_log_safe does not truncate when the file has grown beyond bytes_read.

        Simulates a concurrent append by passing bytes_read smaller than the
        actual file size, verifying that the existing committed content is left
        intact.
        """
        log_path = tmp_path / "concurrent.log"
        store = es.EvidenceStore(log_path)
        store.open()

        issuer, grant = _make_grant_abi(sc)
        receipt = _make_receipt_abi("r-concurrent-001")
        store.append_receipt(
            receipt,
            transaction_id="tx-concurrent-001",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink_abi,
        )

        full_bytes = log_path.read_bytes()
        assert full_bytes.endswith(b"\n"), "appended frame must end with newline"

        # Pass bytes_read smaller than the actual file size to simulate the
        # case where the file grew (a concurrent append committed) between
        # recovery's read and its size check under the advisory lock.
        fake_bytes_read = len(full_bytes) // 2  # half the real size
        store._truncate_log_safe(b"", bytes_read=fake_bytes_read)

        # The file must be unchanged: the concurrent-append simulation caused
        # _truncate_log_safe to refuse truncation.
        assert log_path.read_bytes() == full_bytes, (
            "file was truncated even though bytes_read < actual file size; "
            "a concurrent committed frame would have been lost"
        )


class TestAttestationFieldTypes:
    """Malformed attestation values refuse with one audited denial, never pass or crash."""

    @pytest.mark.parametrize(
        "patch",
        [
            {"limits": {"max_bytes": float("nan"), "timeout_s": float("nan")}},
            {"limits": {"max_bytes": True, "timeout_s": True}},
            {"limits": {"max_bytes": "5", "timeout_s": 10}},
            {"limits": {"max_bytes": 100, "timeout_s": 0}},
            {"limits": {"max_bytes": 100, "timeout_s": 10, "extra": 1}},
            {"limits": ["x"]},
            {"network": "yes"},
            {"network": {"allowed": "true"}},
            {"children": {"allowed": False, "extra": 1}},
        ],
    )
    def test_malformed_attestation_refused_and_audited(
        self, sc: ModuleType, cn: ModuleType, patch: dict
    ) -> None:
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/work"], operations=["read"], trust_class="untrusted",
            writes_allowed_roots=[], control_denies=[],
            limits=sc._Limits(max_bytes=100, timeout_s=10),
        )
        attestation = {
            "schema_version": 1, "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-1", "roots": ("/work",),
            "limits": {"max_bytes": 100, "timeout_s": 10},
        }
        attestation.update(patch)
        events: list = []
        with pytest.raises(cn.ContainmentRefused):
            cn.launch_untrusted({}, grant, host=_Host(attestation), audit_sink=events.append)
        assert len(_denials(events)) == 1, events


class TestRecoveryIdentityBinding:
    """Recovery refuses to truncate unless the bytes read are bound to one file identity."""

    def test_identity_change_during_read_refuses_truncation(
        self, es: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        log_path = tmp_path / "ev.log"
        log_path.write_bytes(b'{"partial')  # a torn final frame
        identities = iter([(1, 1), (1, 2)])
        monkeypatch.setattr(es, "_regular_file_identity", lambda path: next(identities))
        store = es.EvidenceStore(log_path)
        with pytest.raises(es.EvidenceStoreError):
            store.open()
        assert log_path.read_bytes() == b'{"partial', "the log must be left intact"
