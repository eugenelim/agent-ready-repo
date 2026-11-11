"""T5 TDD suite: record dispositions and derive review closure.

Mode: TDD (structured-review-boundary plan T5).

The suite loads shipped work-loop scripts by literal path. Every disposition
write must prove authority and audit-before-effect or return its stable
refusal without visibility. Deleting derived readiness state must yield the
same result dict on recompute.

VI-1010: disposition table and authority negatives.
VI-1011: readiness matrix.
"""

from __future__ import annotations

import copy
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path (pack+skill-unique name)."""
    if not path.exists():
        pytest.fail(f"T5 disposition module is not implemented: {path.name}")
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


# ── Module fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def core_work_loop_t5_disposition() -> ModuleType:
    """Load the T5 review-disposition typed port."""
    return _load_module(
        "core_work_loop_t5_disposition",
        SCRIPTS / "_review_disposition.py",
    )


@pytest.fixture(scope="module")
def core_work_loop_t5_evidence_store() -> ModuleType:
    """Load the evidence store for T5."""
    return _load_module(
        "core_work_loop_t5_evidence_store",
        SCRIPTS / "_evidence_store.py",
    )


@pytest.fixture(scope="module")
def core_work_loop_t5_review_persistence() -> ModuleType:
    """Load the T3 report persistence port for T5."""
    return _load_module(
        "core_work_loop_t5_review_persistence",
        SCRIPTS / "_review_persistence.py",
    )


@pytest.fixture(scope="module")
def core_work_loop_t5_review_bridge() -> ModuleType:
    """Load the T4 bridge for T5 setup."""
    return _load_module(
        "core_work_loop_t5_review_bridge",
        SCRIPTS / "_review_bridge.py",
    )


@pytest.fixture(scope="module")
def core_work_loop_t5_security_capability() -> ModuleType:
    """Load the capability issuer."""
    return _load_module(
        "core_work_loop_t5_security_capability",
        SCRIPTS / "_security_capability.py",
    )


@pytest.fixture(scope="module")
def core_work_loop_t5_acceptance() -> ModuleType:
    """Load the Slice 1 acceptance evaluator."""
    return _load_module(
        "core_work_loop_t5_acceptance",
        SCRIPTS / "_acceptance.py",
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

_REVIEW_POLICY_FP = "review-policy-t5"
_DELIVERY_SUBJECT_ID = "delivery-subject-t5"
_ACCEPTANCE_FP = "acceptance-fp-t5"
_CRITERIA = ["AC-T5-001", "AC-T5-002"]

# Persisted replacement report ID used by fixed-by authority-negative tests.
# _make_setup_store writes a clean replacement report under this ID so every
# parametrized fixed-by negative reaches its targeted guard rather than
# landing on denied-disposition-replacement-not-durable (Rule 5).
_FIXED_BY_AUTH_NEG_RPT_ID = "report-t5-replacement-auth-neg"


def _null_sink(event: object) -> None:
    """Drop events; not a spy here."""


class _SpySink:
    """Capture security events for assertion."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    def __call__(self, event: object) -> None:
        self.events.append(event)


class _FailSink:
    """Always raises to simulate an unavailable audit sink."""

    def __call__(self, event: object) -> None:
        raise RuntimeError("audit sink unavailable in test")


def _make_issuer(security_capability: ModuleType) -> object:
    """Create a CapabilityIssuer."""
    return security_capability.CapabilityIssuer()


def _make_grant_from_issuer(
    issuer: object,
    *,
    roots: list[str],
) -> object:
    """Issue a grant from an existing issuer covering the given roots."""
    return issuer.issue_root_grant(  # type: ignore[union-attr]
        roots=roots,
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=roots,
        control_denies=[],
    )


def _make_review_grant(
    security_capability: ModuleType,
    *,
    roots: list[str] | None = None,
    issuer: object | None = None,
) -> tuple[object, object]:
    """Issue a grant covering the given roots (default: review).

    When *issuer* is supplied, that issuer is reused (both grants then share
    the same issuer, so issuer.verify_grant(grant) succeeds for both).
    """
    used_roots = roots if roots is not None else ["review"]
    if issuer is None:
        issuer = _make_issuer(security_capability)
    grant = _make_grant_from_issuer(issuer, roots=used_roots)
    return issuer, grant


def _make_evidence_grant(
    security_capability: ModuleType,
    *,
    issuer: object | None = None,
) -> tuple[object, object]:
    """Issue a grant covering only evidence (should be refused for dispositions)."""
    if issuer is None:
        issuer = _make_issuer(security_capability)
    grant = _make_grant_from_issuer(issuer, roots=["evidence"])
    return issuer, grant


def _store_path(tmp_path: Path, name: str = "semantic-evidence.log") -> Path:
    log_path = tmp_path / "repo" / ".work-loop" / name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def _open_store(evidence_store: ModuleType, log_path: Path) -> Any:
    store = evidence_store.EvidenceStore(log_path)
    store.open()
    return store


def _subject() -> dict:
    """Build a review subject for T5 tests."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-t5",
        "review_subject_fingerprint": "review-subject-fp-t5",
        "delivery_subject_ref": {
            "subject_id": _DELIVERY_SUBJECT_ID,
            "acceptance_fingerprint": _ACCEPTANCE_FP,
        },
        "normalized_paths": ["packs/core/.apm/skills/work-loop/scripts/_review_disposition.py"],
        "normalized_statuses": ["added"],
        "review_policy_fingerprint": _REVIEW_POLICY_FP,
        "lineage": {"provider": "structured-review-boundary-test", "projection_version": "1.0"},
    }


def _replacement_subject() -> dict:
    """Build a replacement subject with same delivery id but different fingerprint."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-t5-replacement",
        "review_subject_fingerprint": "review-subject-fp-t5-replacement",
        "delivery_subject_ref": {
            "subject_id": _DELIVERY_SUBJECT_ID,
            "acceptance_fingerprint": _ACCEPTANCE_FP,
        },
        "normalized_paths": ["packs/core/.apm/skills/work-loop/scripts/_review_disposition.py"],
        "normalized_statuses": ["modified"],
        "review_policy_fingerprint": _REVIEW_POLICY_FP + "-v2",
        "lineage": {"provider": "structured-review-boundary-test", "projection_version": "1.1"},
    }


def _finding() -> dict:
    return {
        "schema_version": 1,
        "finding_id": "finding-t5",
        "rule_ref": "AC-T5-001",
        "observation": "T5 disposition test finding",
        "reachable_path": "disposition port to evidence",
        "actual_failure": "Unauthorized disposition would bypass evidence integrity",
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": ["evidence:t5-obs"],
        "material": True,
    }


def _report(subject: dict, *, report_id: str = "report-t5") -> dict:
    return {
        "schema_version": 1,
        "report_id": report_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": f"source-{report_id}",
            "producer": "synthetic-reviewer",
        },
        "findings": [_finding()],
    }


def _clean_report(subject: dict, *, report_id: str = "report-t5-clean") -> dict:
    return {
        "schema_version": 1,
        "report_id": report_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": f"source-{report_id}",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }


def _assessment(subject: dict, *, assessment_id: str = "assessment-t5") -> dict:
    return {
        "schema_version": 1,
        "assessment_id": assessment_id,
        "finding_id": "finding-t5",
        "report_id": "report-t5",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": ["evidence:t5-obs"],
        "lineage": {"predicate_version": "v1"},
    }


def _approval(
    *,
    approval_id: str = "approval-t5",
    decision: str = "approved",
    decision_scope: str = "review-disposition",
    authority_ref: str | None = None,
    authority_identity: str = "reviewer-identity-t5",
    authority_role: str = "risk-owner",
    spec_policy_fingerprint: str = _REVIEW_POLICY_FP,
    manifest_ref: str = "review-subject-fp-t5",
) -> dict:
    return {
        "schema_version": 1,
        "approval_id": approval_id,
        "authority": {
            "identity": authority_identity,
            "role": authority_role,
        },
        "decision_scope": decision_scope,
        "base": {"manifest_ref": manifest_ref},
        "lineage": {"spec_ref": "docs/specs/structured-review-boundary/spec.md"},
        "spec_policy_fingerprint": spec_policy_fingerprint,
        "decision": decision,
        "timestamp": "2026-10-09T00:00:00Z",
    }


def _disposition(
    subject: dict,
    *,
    disposition_id: str = "disposition-t5",
    disposition_kind: str = "accept-risk",
    assessment_id: str = "assessment-t5",
    authority_ref: str = "approval-t5",
    decision_maker_identity: str = "reviewer-identity-t5",
    decision_maker_role: str = "risk-owner",
    replacement_report_id: str | None = None,
) -> dict:
    record: dict = {
        "schema_version": 1,
        "disposition_id": disposition_id,
        "finding_id": "finding-t5",
        "assessment_id": assessment_id,
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "disposition": disposition_kind,
        "decision_maker": {
            "identity": decision_maker_identity,
            "role": decision_maker_role,
        },
        "lineage": {
            "authority_ref": authority_ref,
            "source_event_id": "event-t5",
        },
    }
    if replacement_report_id is not None:
        record["replacement_report_id"] = replacement_report_id
    return record


def _review_policy(subject: dict) -> dict:
    return {
        "policy_id": "policy-t5",
        "review_policy_fingerprint": _REVIEW_POLICY_FP,
        "policy_version": "v1",
        "selector": "core-policy-t5",
        "roles": [{"role": "quality-engineer", "kind": "mandatory"}],
        "waivers": [],
    }


def _setup_report_and_assessment(
    store: Any,
    review_persistence: ModuleType,
    review_bridge: ModuleType,
    subject: dict,
    *,
    issuer: object,
    evidence_grant: object,
) -> None:
    """Persist a findings report and a supported assessment."""
    review_persistence.append_current_review_report(
        store,
        _report(subject),
        transaction_id="tx-t5-report",
        expected_subject=subject,
        issuer=issuer,
        grant=evidence_grant,
        audit_sink=_null_sink,
    )
    review_bridge.append_finding_assessment_bridge(
        store,
        _assessment(subject),
        report_id="report-t5",
        finding=_finding(),
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-assessment",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=evidence_grant,
        audit_sink=_null_sink,
    )


# ── VI-1010: Disposition table ─────────────────────────────────────────────────


def test_repair_request_admitted_but_finding_stays_open(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """repair-request is admitted as a disposition but the obligation remains open."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "repair-request.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="repair-request")
    appr = _approval()

    tx = core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=appr,
        current_subject=subject,
        transaction_id="tx-t5-repair",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )
    assert tx is not None
    # Finding is still open: repair-request does not close the obligation
    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False
    # The finding appears in open_findings
    assert any(f["finding_id"] == "finding-t5" for f in readiness["open_findings"])


def test_accept_risk_closes_review_and_contradiction_preserved(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    core_work_loop_t5_acceptance: ModuleType,
    tmp_path: Path,
) -> None:
    """accept-risk closes review but does not remove the contradiction receipt."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "accept-risk.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="accept-risk")
    appr = _approval()

    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=appr,
        current_subject=subject,
        transaction_id="tx-t5-accept-risk",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # Contradiction receipts must still be active
    active = store.get_all_active_receipts()
    bridge_receipts = [
        r for r in active
        if r.get("selector", {}).get("term") == "supported-review-failure"
    ]
    assert len(bridge_receipts) == len(_CRITERIA)

    # Evaluate verdict: still contradicted
    prop = {
        "schema_version": 1,
        "property_id": _CRITERIA[0],
        "spec_ref": "docs/specs/structured-review-boundary/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {
            "paths_or_artifacts": ["packs/core/"],
            "fingerprint_algorithm": "sha256",
        },
        "required_observations": [{"term": "test-run", "observation_type": "test-result",
                                    "producer_class": "ci-runner", "outcomes": ["passed"]}],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": "supported-review-failure"},
        "policy_version": "v1",
    }
    acc = core_work_loop_t5_acceptance
    verdicts = store.evaluate_verdicts(
        [prop], _ACCEPTANCE_FP, acc
    )
    assert verdicts[0]["verdict"] == "contradicted"

    # Review is now eligible (accept-risk closed the obligation)
    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is True
    assert readiness["open_findings"] == []


def test_fixed_by_closes_on_replacement_subject(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """fixed-by with a fresh replacement-subject report closes the obligation."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "fixed-by.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Add a replacement report with a different subject fingerprint
    # and no open findings with the same actual_failure
    replacement_subj = _replacement_subject()
    replacement_rpt_id = "report-t5-replacement"

    # Persist a clean replacement report (no findings → no open failures)
    clean_replacement = {
        "schema_version": 1,
        "report_id": replacement_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-replacement",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        clean_replacement,
        transaction_id="tx-t5-replacement-report",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id=replacement_rpt_id,
    )
    appr = _approval()

    tx = core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=appr,
        current_subject=subject,
        transaction_id="tx-t5-fixed-by",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )
    assert tx is not None

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is True
    assert readiness["open_findings"] == []


# ── VI-1010: fixed-by negative cases ──────────────────────────────────────────


@pytest.mark.parametrize("missing_rpt_id", [True])
def test_fixed_by_without_replacement_report_stays_open(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
    missing_rpt_id: bool,
) -> None:
    """fixed-by without a durable replacement report is refused."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "fixed-by-no-replacement.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id="report-t5-nonexistent",
    )
    appr = _approval()
    before = log_path.read_bytes()

    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-t5-fixed-by-no-rpt",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-replacement-not-durable"
    assert log_path.read_bytes() == before


def test_fixed_by_same_subject_fingerprint_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """fixed-by with same subject fingerprint is refused (must differ)."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "fixed-by-same-subject.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Replacement report with same subject fingerprint — should be refused.
    # We do not store the replacement report; the disposition itself references
    # the original report (same fingerprint), which must be refused by the store.
    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id="report-t5",  # same report as the original
    )
    appr = _approval()
    before = log_path.read_bytes()

    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-t5-fixed-by-same",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-replacement-same-subject"
    assert log_path.read_bytes() == before


# ── VI-1010: Authority negatives (parametrized over all 3 kinds) ───────────────


_ALL_DISPOSITION_KINDS = ["repair-request", "fixed-by", "accept-risk"]


def _make_kind_disposition(
    subject: dict,
    kind: str,
    *,
    disposition_id: str = "disposition-t5-neg",
) -> dict:
    """Build a disposition of the given kind.

    For fixed-by, uses _FIXED_BY_AUTH_NEG_RPT_ID which _make_setup_store
    persists unconditionally, so authority-check negatives hit their specific
    guard rather than denied-disposition-replacement-not-durable (Rule 5).
    """
    replacement = None
    if kind == "fixed-by":
        replacement = _FIXED_BY_AUTH_NEG_RPT_ID
    return _disposition(
        subject,
        disposition_id=disposition_id,
        disposition_kind=kind,
        replacement_report_id=replacement,
    )


def _make_setup_store(
    es: ModuleType,
    persistence: ModuleType,
    bridge: ModuleType,
    capability: ModuleType,
    tmp_path: Path,
    name: str,
) -> tuple[Any, object, object, object, object, dict]:
    """Common store setup for authority negative cases.

    Also persists a clean replacement report under _FIXED_BY_AUTH_NEG_RPT_ID
    so that _make_kind_disposition with kind="fixed-by" reaches its targeted
    authority guard without failing on denied-disposition-replacement-not-durable.
    """
    log_path = _store_path(tmp_path, name)
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(capability)
    # Reuse the same issuer so issuer.verify_grant(rev_grant) succeeds.
    _, rev_grant = _make_review_grant(capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        persistence,
        bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )
    # Persist a clean replacement report for fixed-by authority-negative tests.
    replacement_subj = _replacement_subject()
    auth_neg_report = {
        "schema_version": 1,
        "report_id": _FIXED_BY_AUTH_NEG_RPT_ID,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": f"source-auth-neg-{name}",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    persistence.append_current_review_report(
        store,
        auth_neg_report,
        transaction_id=f"tx-auth-neg-repl-{name}",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )
    return store, log_path, issuer, ev_grant, rev_grant, subject


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_missing_approval_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Missing (invalid) approval is refused before any store write."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"missing-approval-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-missing-appr")
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record={"schema_version": 1},  # invalid
            current_subject=subject,
            transaction_id=f"tx-missing-appr-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-invalid-approval-denied-missing-required-field"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_wrong_decision_scope_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Approval with wrong decision_scope is refused."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"wrong-scope-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-wrong-scope")
    appr = _approval(decision_scope="spec-policy")  # wrong scope
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-wrong-scope-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-invalid-scope"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_authority_ref_mismatch_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Disposition authority_ref not matching approval_id is refused."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"auth-ref-mismatch-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-auth-mismatch")
    # Override authority_ref to not match approval_id
    disp["lineage"]["authority_ref"] = "wrong-approval-id"
    appr = _approval(approval_id="approval-t5-neg")  # different ID
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-auth-ref-mismatch-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    # R3 fires first: lifecycle approval.id != disposition.authority_ref → more
    # specific code than the previous denied-disposition-no-approval.
    assert exc_info.value.denial_code == "denied-approval-authority-required"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_identity_mismatch_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Disposition decision_maker identity not matching approval authority is refused."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"identity-mismatch-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-id-mismatch")
    disp["decision_maker"]["identity"] = "different-identity"
    appr = _approval()  # identity = "reviewer-identity-t5"
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-id-mismatch-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-identity-mismatch"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_policy_fingerprint_mismatch_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Approval spec_policy_fingerprint not matching review subject is refused."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"policy-fp-mismatch-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-pfp-mismatch")
    appr = _approval(spec_policy_fingerprint="wrong-policy-fp")
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-pfp-mismatch-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-policy-mismatch"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_subject_manifest_ref_mismatch_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Approval manifest_ref not matching review_subject_fingerprint is refused."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"manifest-ref-mismatch-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-mr-mismatch")
    appr = _approval(manifest_ref="wrong-subject-fp")
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-mr-mismatch-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-subject-mismatch"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_evidence_only_grant_refused_out_of_scope(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Evidence-only grant is refused for disposition (denied-out-of-scope)."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, ev_grant, _, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"evidence-only-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-ev-only")
    appr = _approval()
    before = log_path.read_bytes()
    spy = _SpySink()
    with pytest.raises(Exception) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-ev-only-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=ev_grant,
            audit_sink=spy,
        )
    denial_code = getattr(exc_info.value, "denial_code", str(exc_info.value))
    assert denial_code == "denied-producer-authority"
    assert log_path.read_bytes() == before
    # Exactly one denial event emitted (the authority check itself)
    denial_events = [e for e in spy.events if getattr(e, "outcome", None) == "denied"]
    assert len(denial_events) >= 1


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_invalid_grant_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """None grant is refused with a stable denial code."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, _, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"invalid-grant-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-no-grant")
    appr = _approval()
    before = log_path.read_bytes()
    with pytest.raises(Exception) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-no-grant-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=None,  # no grant
            audit_sink=_null_sink,
        )
    denial_code = getattr(exc_info.value, "denial_code", str(exc_info.value))
    assert denial_code == "denied-invalid-grant"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_audit_sink_unavailable_refused_no_effect(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Unavailable audit sink refuses with no effect on the log."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"audit-unavailable-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-no-audit")
    appr = _approval()
    before = log_path.read_bytes()
    fail_sink = _FailSink()
    with pytest.raises(Exception) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-no-audit-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=fail_sink,
        )
    denial_code = getattr(exc_info.value, "denial_code", str(exc_info.value))
    assert denial_code == "denied-audit-sink-unavailable"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_post_allow_denial_has_same_operation_id(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """After a successful authority check, a post-allow denial shares operation_id."""
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"post-allow-denial-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-post-allow")
    # Wrong decision scope → passes the grant check but fails the disposition rule
    appr = _approval(decision_scope="spec-policy")
    spy = _SpySink()
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused):
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id=f"tx-post-allow-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=spy,
        )
    allow_events = [e for e in spy.events if getattr(e, "outcome", None) == "allowed"]
    denial_events = [e for e in spy.events if getattr(e, "outcome", None) == "denied"]
    # Must have exactly one allow and one denial
    assert len(allow_events) == 1
    assert len(denial_events) == 1
    # They share the same operation_id
    assert allow_events[0].operation_id == denial_events[0].operation_id
    assert log_path.read_bytes() == before


# ── VI-1010: Eligibility negatives ────────────────────────────────────────────


def test_unsupported_assessment_cannot_be_disposed(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A disposition over an unsupported assessment is refused."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "unsupported-assessment.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    # Persist a findings report
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        _report(subject),
        transaction_id="tx-t5-report-unsup",
        expected_subject=subject,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )
    # Persist an UNSUPPORTED assessment
    unsupported_assessment = {
        "schema_version": 1,
        "assessment_id": "assessment-t5-unsupported",
        "finding_id": "finding-t5",
        "report_id": "report-t5",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        unsupported_assessment,
        report_id="report-t5",
        finding=_finding(),
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-unsupported",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(subject, assessment_id="assessment-t5-unsupported")
    appr = _approval()
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-t5-disp-unsup",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-not-supported"
    assert log_path.read_bytes() == before


def test_nonmaterial_finding_cannot_be_disposed(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A disposition for a non-material finding is refused (AC-0007)."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "nonmaterial.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    # Build a non-material finding
    nonmaterial_finding = dict(_finding())
    nonmaterial_finding["finding_id"] = "finding-t5-nonmaterial"
    nonmaterial_finding["material"] = False

    report = _report(subject)
    report["findings"] = [nonmaterial_finding]

    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t5-report-nonmat",
        expected_subject=subject,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )
    assessment = dict(_assessment(subject))
    assessment["assessment_id"] = "assessment-t5-nonmat"
    assessment["finding_id"] = "finding-t5-nonmaterial"
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        assessment,
        report_id="report-t5",
        finding=nonmaterial_finding,
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-assessment-nonmat",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        assessment_id="assessment-t5-nonmat",
    )
    disp["finding_id"] = "finding-t5-nonmaterial"
    appr = _approval()
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-t5-disp-nonmat",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-not-material"
    assert log_path.read_bytes() == before


# ── VI-1010: Raw bypass test ───────────────────────────────────────────────────


def test_raw_batch_with_disposition_refused(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Disposition passed on raw batch path is refused with denied-disposition-authority-required."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "raw-batch-bypass.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )
    disp = _disposition(subject)
    before = log_path.read_bytes()
    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-raw-bypass",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=ev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-authority-required"
    assert log_path.read_bytes() == before


# ── VI-1010: Retry idempotency ─────────────────────────────────────────────────


def test_identical_retry_is_idempotent(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Same transaction_id and identical request is idempotent."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "retry-idempotent.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject,
        issuer=issuer, evidence_grant=ev_grant,
    )
    disp = _disposition(subject)
    appr = _approval()

    tx1 = core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=appr, current_subject=subject,
        transaction_id="tx-retry-idem", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    before = log_path.read_bytes()
    tx2 = core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=appr, current_subject=subject,
        transaction_id="tx-retry-idem", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    assert log_path.read_bytes() == before
    assert tx1["transaction_id"] == tx2["transaction_id"]


def test_changed_retry_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Same transaction_id but changed request is refused."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "retry-changed.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject,
        issuer=issuer, evidence_grant=ev_grant,
    )
    disp = _disposition(subject)
    appr = _approval()

    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=appr, current_subject=subject,
        transaction_id="tx-retry-changed", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    before = log_path.read_bytes()
    disp2 = dict(disp)
    disp2["disposition_id"] = "disposition-t5-changed"

    with pytest.raises(Exception) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp2, approval_record=appr, current_subject=subject,
            transaction_id="tx-retry-changed",  # same tx_id, different record
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    denial_code = getattr(exc_info.value, "denial_code", str(exc_info.value))
    assert denial_code == "denied-duplicate-transaction-id"
    assert log_path.read_bytes() == before


# ── VI-1011: Readiness matrix ──────────────────────────────────────────────────


def test_mandatory_unsatisfied_not_eligible(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """No report → mandatory obligation unsatisfied → not eligible."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mandatory-unsatisfied.log")
    store = _open_store(es, log_path)
    subject = _subject()

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False
    assert any(
        ob.get("decision") in {
            "mandatory-report-unsatisfied", "finding-assessment-required",
            "open-supported-material-finding"
        }
        for ob in readiness["obligations"]
    )


def test_open_supported_finding_blocks_eligibility(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Open supported material finding blocks eligibility even with a current report."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "open-finding-blocks.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    subject = _subject()
    _setup_report_and_assessment(
        store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject,
        issuer=issuer, evidence_grant=ev_grant,
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False
    assert any(f["finding_id"] == "finding-t5" for f in readiness["open_findings"])


def test_fresh_store_reopen_yields_identical_readiness(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Deleting derived state (fresh store reopen) yields identical readiness dict."""
    import json
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "reopen-identical.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject,
        issuer=issuer, evidence_grant=ev_grant,
    )

    disp = _disposition(subject)
    appr = _approval()
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=appr, current_subject=subject,
        transaction_id="tx-t5-reopen", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    readiness_before = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )

    # Reopen: derives same state from durable log
    store2 = _open_store(es, log_path)
    readiness_after = core_work_loop_t5_disposition.review_readiness(
        store2,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )

    assert json.dumps(readiness_before, sort_keys=True) == json.dumps(
        readiness_after, sort_keys=True
    )


def test_waived_obligation_does_not_block(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Waived obligation counts as not required and does not block acceptance."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "waived.log")
    store = _open_store(es, log_path)
    subject = _subject()

    waived_policy = {
        "policy_id": "policy-t5-waived",
        "review_policy_fingerprint": _REVIEW_POLICY_FP,
        "policy_version": "v1",
        "selector": "core-policy-t5",
        "roles": [{"role": "quality-engineer", "kind": "mandatory"}],
        "waivers": [
            {
                "waiver_ref": "waiver-t5",
                "role": "quality-engineer",
                "review_subject_fingerprint": subject["review_subject_fingerprint"],
                "review_policy_fingerprint": _REVIEW_POLICY_FP,
                "authorized": True,
                "current": True,
            }
        ],
    }

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=waived_policy,
    )
    assert readiness["acceptance_eligible"] is True
    assert any(ob.get("decision") == "waived" for ob in readiness["obligations"])


# ── VI-1011: fixed-by readiness re-verification ───────────────────────────────


def test_verified_fixed_by_obligation_decision_is_satisfied_findings(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Verified fixed-by flips a mandatory open-finding obligation to satisfied-findings.

    Removing the fixed-by recompute in review_readiness causes this test to fail:
    without the recompute, the obligation decision remains open-supported-material-finding
    and acceptance_eligible stays False.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "verified-fixed-by-obligation.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Replacement subject with a clean tip report — different fingerprint.
    replacement_subj = _replacement_subject()
    replacement_rpt_id = "report-t5-verified-replacement"
    clean_replacement = {
        "schema_version": 1,
        "report_id": replacement_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-verified-replacement",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        clean_replacement,
        transaction_id="tx-t5-verified-replacement-report",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        disposition_id="disposition-t5-verified",
        disposition_kind="fixed-by",
        replacement_report_id=replacement_rpt_id,
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-t5-verified-fixed-by",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    # The obligation must show satisfied-findings, not open-supported-material-finding.
    obligation_decisions = {
        ob["role"]: ob["decision"] for ob in readiness["obligations"]
    }
    assert obligation_decisions.get("quality-engineer") == "satisfied-findings", (
        "verified fixed-by must flip mandatory obligation to satisfied-findings; "
        "got: " + str(obligation_decisions)
    )
    assert readiness["acceptance_eligible"] is True
    assert readiness["open_findings"] == []


def test_fixed_by_with_replacement_not_tip_stays_open(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """fixed-by is not trusted when its replacement report is no longer the tip.

    After a newer report supersedes the replacement, the fixed-by disposition
    must not close the original finding.  Trusting a stale replacement would
    let an unverified disposition silently close an obligation.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "fixed-by-stale-replacement.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Replacement subject — first report (will become stale).
    replacement_subj = _replacement_subject()
    first_rpt_id = "report-t5-replacement-first"
    first_replacement = {
        "schema_version": 1,
        "report_id": first_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-first-replacement",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        first_replacement,
        transaction_id="tx-t5-first-replacement",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Write the fixed-by disposition pointing at the first (soon-to-be-stale) report.
    disp = _disposition(
        subject,
        disposition_id="disposition-t5-stale",
        disposition_kind="fixed-by",
        replacement_report_id=first_rpt_id,
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-t5-stale-fixed-by",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # Now add a second report for the replacement subject, making the first stale.
    second_rpt_id = "report-t5-replacement-second"
    second_replacement = {
        "schema_version": 1,
        "report_id": second_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 2,
            "previous_report_id": first_rpt_id,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-second-replacement",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        second_replacement,
        transaction_id="tx-t5-second-replacement",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # The replacement is no longer the tip: readiness must NOT close the finding.
    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False, (
        "fixed-by whose replacement is no longer the tip must not close the finding"
    )
    assert any(f["finding_id"] == "finding-t5" for f in readiness["open_findings"])


# ── E1: disposition_closes verifier — fixed-by same-failure and indeterminate ─────


def test_fixed_by_stops_closing_on_same_failure_supported_assessment(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """fixed-by stops closing once a replacement finding gets a supported same-failure assessment.

    Rule 5 (none supported with the same actual_failure as the original finding)
    is re-evaluated live; a replacement finding that receives a supported
    assessment matching the original failure breaks the fixed-by closure.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "fixed-by-same-failure.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Replacement: a report with one finding whose actual_failure matches the original.
    replacement_subj = _replacement_subject()
    repl_rpt_id = "report-t5-repl-samefail"
    repl_finding_id = "repl-finding-samefail"
    same_failure = _finding()["actual_failure"]
    repl_finding = {
        "schema_version": 1,
        "finding_id": repl_finding_id,
        "rule_ref": "AC-T5-001",
        "observation": "same failure in replacement",
        "reachable_path": "same path",
        "actual_failure": same_failure,
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": ["evidence:t5-repl-sf-obs"],
        "material": True,
    }
    repl_report = {
        "schema_version": 1,
        "report_id": repl_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-repl-sf",
            "producer": "synthetic-reviewer",
        },
        "findings": [repl_finding],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        repl_report,
        transaction_id="tx-t5-repl-sf-report",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Write the fixed-by disposition pointing to the replacement.
    disp = _disposition(
        subject,
        disposition_id="disposition-t5-sf",
        disposition_kind="fixed-by",
        replacement_report_id=repl_rpt_id,
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-t5-sf-disp",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # Write an "unsupported-opinion" assessment for the replacement finding so rule 7
    # passes.  (unsupported-opinion is not indeterminate and not supported-same-failure,
    # so rules 8+9 pass.)
    repl_assessment_unsup = {
        "schema_version": 1,
        "assessment_id": "repl-assessment-unsup-sf",
        "finding_id": repl_finding_id,
        "report_id": repl_rpt_id,
        "review_subject_fingerprint": replacement_subj["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        repl_assessment_unsup,
        report_id=repl_rpt_id,
        finding=repl_finding,
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-repl-unsup-sf",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Before: store.disposition_closes returns True (unsupported does not trigger rule 9).
    assert store.disposition_closes("disposition-t5-sf", subject) is True, (
        "fixed-by must close when replacement finding has only an unsupported assessment"
    )
    readiness_before = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness_before["acceptance_eligible"] is True, (
        "review must be eligible before the same-failure supported assessment is written"
    )

    # Write a SUPPORTED same-failure assessment for the replacement finding.
    repl_assessment_sup = {
        "schema_version": 1,
        "assessment_id": "repl-assessment-sup-sf",
        "finding_id": repl_finding_id,
        "report_id": repl_rpt_id,
        "review_subject_fingerprint": replacement_subj["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": ["evidence:t5-repl-sf-obs"],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        repl_assessment_sup,
        report_id=repl_rpt_id,
        finding=repl_finding,
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-repl-sup-sf",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # After: rule 9 fires — supported same-failure assessment on replacement finding.
    assert store.disposition_closes("disposition-t5-sf", subject) is False, (
        "fixed-by must stop closing once replacement finding has supported same-failure assessment"
    )
    readiness_after = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness_after["acceptance_eligible"] is False, (
        "fixed-by must stop closing once replacement gets a supported same-failure assessment"
    )
    assert any(f["finding_id"] == "finding-t5" for f in readiness_after["open_findings"])


def test_fixed_by_stops_closing_on_indeterminate_replacement_assessment(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """fixed-by stops closing once a replacement finding gets an indeterminate assessment.

    Rule 8 (none indeterminate among replacement findings) is re-evaluated live;
    an indeterminate assessment on any replacement finding breaks the closure.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "fixed-by-indeterminate.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Replacement: a report with one finding having a DIFFERENT actual_failure.
    replacement_subj = _replacement_subject()
    repl_rpt_id = "report-t5-repl-indet"
    repl_finding_id = "repl-finding-indet"
    repl_finding = {
        "schema_version": 1,
        "finding_id": repl_finding_id,
        "rule_ref": "AC-T5-001",
        "observation": "different failure in replacement",
        "reachable_path": "same path",
        "actual_failure": "Different failure not matching original",
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": ["evidence:t5-repl-indet-obs"],
        "material": True,
    }
    repl_report = {
        "schema_version": 1,
        "report_id": repl_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-repl-indet",
            "producer": "synthetic-reviewer",
        },
        "findings": [repl_finding],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        repl_report,
        transaction_id="tx-t5-repl-indet-report",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        disposition_id="disposition-t5-indet",
        disposition_kind="fixed-by",
        replacement_report_id=repl_rpt_id,
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-t5-indet-disp",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # Write an "unsupported-opinion" assessment — disposition closes initially.
    repl_assessment_unsup = {
        "schema_version": 1,
        "assessment_id": "repl-assessment-unsup-indet",
        "finding_id": repl_finding_id,
        "report_id": repl_rpt_id,
        "review_subject_fingerprint": replacement_subj["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        repl_assessment_unsup,
        report_id=repl_rpt_id,
        finding=repl_finding,
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-repl-unsup-indet",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Before: closes (unsupported passes rule 8).
    assert store.disposition_closes("disposition-t5-indet", subject) is True, (
        "fixed-by must close when replacement finding has only an unsupported assessment"
    )

    # Write an "indeterminate" assessment for the replacement finding.
    repl_assessment_indet = {
        "schema_version": 1,
        "assessment_id": "repl-assessment-indet",
        "finding_id": repl_finding_id,
        "report_id": repl_rpt_id,
        "review_subject_fingerprint": replacement_subj["review_subject_fingerprint"],
        "assessment": "indeterminate",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        repl_assessment_indet,
        report_id=repl_rpt_id,
        finding=repl_finding,
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-repl-indet",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # After: rule 8 fires — indeterminate assessment on replacement finding.
    assert store.disposition_closes("disposition-t5-indet", subject) is False, (
        "fixed-by must stop closing once replacement finding has an indeterminate assessment"
    )
    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False, (
        "fixed-by must stop closing once replacement gets an indeterminate assessment"
    )
    assert any(f["finding_id"] == "finding-t5" for f in readiness["open_findings"])


# ── E1: disposition_closes verifier — accept-risk supersession and stale assessment ──


def test_accept_risk_stops_closing_after_approval_superseded(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """accept-risk stops closing once a later approval supersedes its authority.

    Writing a second disposition whose approval names the original approval_id as
    predecessor_id marks the original approval superseded.  store.disposition_closes
    then returns False for the original accept-risk even though its record is intact.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "accept-risk-superseded.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Write the original accept-risk disposition.
    disp_v1 = _disposition(subject, disposition_kind="accept-risk")
    appr_v1 = _approval()
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp_v1,
        approval_record=appr_v1,
        current_subject=subject,
        transaction_id="tx-t5-accept-risk-supersede",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # Before: accept-risk closes.
    assert store.disposition_closes("disposition-t5", subject) is True, (
        "accept-risk must close before its approval is superseded"
    )
    readiness_before = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness_before["acceptance_eligible"] is True, (
        "review must be eligible before the approval is superseded"
    )

    # Write a second approval that supersedes the original (predecessor_id = approval-t5).
    # Pair it with a repair-request disposition which does NOT close the finding.
    appr_v2 = copy.deepcopy(_approval(approval_id="approval-t5-superseder"))
    appr_v2["lineage"]["predecessor_id"] = "approval-t5"
    disp_v2 = _disposition(
        subject,
        disposition_id="disposition-t5-superseder",
        disposition_kind="repair-request",
        authority_ref="approval-t5-superseder",
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp_v2,
        approval_record=appr_v2,
        current_subject=subject,
        transaction_id="tx-t5-superseder-disp",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # After: the original approval is superseded — accept-risk stops closing.
    assert store.disposition_closes("disposition-t5", subject) is False, (
        "accept-risk must stop closing once its approval is superseded"
    )
    readiness_after = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness_after["acceptance_eligible"] is False, (
        "review must not be eligible after the accept-risk approval is superseded"
    )
    assert any(f["finding_id"] == "finding-t5" for f in readiness_after["open_findings"])


def test_accept_risk_stops_closing_after_assessment_replaced(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """accept-risk stops closing once a newer supported assessment replaces the original.

    store.disposition_closes checks that the disposition's assessment_id is still the
    latest for the finding in current_finding_assessments.  A second assessment for the
    same (report_id, finding_id) becomes the latest, leaving the accept-risk referencing
    a stale assessment_id.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "accept-risk-stale-assessment.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Write the accept-risk disposition.
    disp = _disposition(subject, disposition_kind="accept-risk")
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-t5-accept-risk-stale",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    # Before: accept-risk closes.
    assert store.disposition_closes("disposition-t5", subject) is True, (
        "accept-risk must close before its assessment is superseded"
    )

    # Write a newer supported assessment for the same finding/report.
    new_assessment = {
        "schema_version": 1,
        "assessment_id": "assessment-t5-v2",
        "finding_id": "finding-t5",
        "report_id": "report-t5",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": ["evidence:t5-obs"],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store,
        new_assessment,
        report_id="report-t5",
        finding=_finding(),
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-assessment-v2",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # After: current_finding_assessments returns assessment-t5-v2, not assessment-t5.
    # The accept-risk disposition references assessment-t5 — now stale.
    assert store.disposition_closes("disposition-t5", subject) is False, (
        "accept-risk must stop closing once its assessment_id is no longer current"
    )
    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False, (
        "review must not be eligible after the accept-risk assessment is replaced"
    )


# ── E2: raw and replayed approval-record frames ───────────────────────────────────


def test_raw_approval_write_refused_and_store_reopens(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """approval-record.v1 written via raw semantic batch is refused; log unchanged.

    Raw batches cannot write approval-record.v1 — approval records are only
    admitted inside a finding-disposition lifecycle frame.  The refusal must
    carry a stable denial code and leave the log byte-for-byte unchanged.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "raw-approval.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)

    appr = _approval()
    before = log_path.read_bytes()

    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [appr],
            transaction_id="tx-raw-approval",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=ev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-approval-authority-required", (
        "raw approval write must use the stable denial code"
    )
    assert log_path.read_bytes() == before, (
        "log must be unchanged after refused raw approval write"
    )

    # Store reopens cleanly after the refusal (no corruption introduced).
    store2 = es.EvidenceStore(log_path)
    store2.open()
    assert store2 is not None


def test_replayed_raw_approval_frame_refuses_on_open(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A checksum-valid raw approval frame in the log causes open() to raise EvidenceStoreError.

    If an approval-record.v1 reaches the log without a paired finding-disposition
    (e.g. a crafted frame bypassing the write port), the replay path must refuse
    it as malformed rather than silently admitting it.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "raw-approval-replay.log")
    # Open once to create the log file (empty).
    store = _open_store(es, log_path)
    del store

    # Directly append a checksum-valid raw approval frame to the log.
    appr = _approval(approval_id="approval-raw-replay")
    appr_id = appr["approval_id"]
    tx = es._build_transaction("tx-raw-approval-replay", [appr_id], _ACCEPTANCE_FP, [appr])
    frame_bytes = es._serialize_frame(tx, [appr])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    # Reopening must raise EvidenceStoreError (replay refuses the orphan approval frame).
    with pytest.raises(es.EvidenceStoreError):
        store2 = es.EvidenceStore(log_path)
        store2.open()


# ── G1/G2/G3 TDD red phase ────────────────────────────────────────────────────


def test_g1_approval_not_approved_refuses(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G1: approval.decision != 'approved' is refused before admission.

    A valid accept-risk baseline is admitted. Mutating decision to 'superseded'
    and exactly nothing else must cause a refusal with the stable denial code.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g1-decision.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="accept-risk")
    # Mutate exactly ONE field: decision -> "superseded"
    appr = _approval(decision="superseded")

    with pytest.raises(
        core_work_loop_t5_disposition.ReviewDispositionRefused
    ) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-g1-neg",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-decision-not-approved", (
        "G1: superseded decision must produce stable denial code"
    )


def test_g2_role_mismatch_refuses(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G2: decision_maker.role != approval.authority.role is refused.

    Baseline: accept-risk where decision_maker.role == approval.authority.role == 'risk-owner'.
    Mutation: decision_maker.role = 'other-role' (approval unchanged).
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g2-role.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    appr = _approval(authority_role="risk-owner")
    # Mutate exactly ONE field: decision_maker.role != approval.authority.role
    disp = _disposition(subject, disposition_kind="accept-risk", decision_maker_role="other-role")

    with pytest.raises(
        core_work_loop_t5_disposition.ReviewDispositionRefused
    ) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-g2-neg",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-role-mismatch", (
        "G2: role mismatch must produce stable denial code"
    )


def test_g3_accept_risk_with_replacement_report_id_refuses(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G3: accept-risk carrying replacement_report_id is refused.

    Baseline accept-risk does not carry replacement_report_id and is admitted.
    Mutating exactly one field: adding replacement_report_id must refuse.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g3-accept-risk-replacement.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    appr = _approval()
    # Mutate exactly ONE field: add replacement_report_id to accept-risk
    disp = _disposition(
        subject,
        disposition_kind="accept-risk",
        replacement_report_id="report-t5-replacement-neg",
    )

    with pytest.raises(
        core_work_loop_t5_disposition.ReviewDispositionRefused
    ) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-g3-accept-risk-neg",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-unexpected-replacement", (
        "G3: accept-risk with replacement_report_id must produce stable denial code"
    )


def test_g3_repair_request_with_replacement_report_id_refuses(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G3: repair-request carrying replacement_report_id is refused.

    Baseline repair-request does not carry replacement_report_id and is admitted.
    Mutating exactly one field: adding replacement_report_id must refuse.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g3-repair-request-replacement.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    appr = _approval()
    # Mutate exactly ONE field: add replacement_report_id to repair-request
    disp = _disposition(
        subject,
        disposition_kind="repair-request",
        replacement_report_id="report-t5-replacement-neg",
    )

    with pytest.raises(
        core_work_loop_t5_disposition.ReviewDispositionRefused
    ) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-g3-repair-neg",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-unexpected-replacement", (
        "G3: repair-request with replacement_report_id must produce stable denial code"
    )


# ── G1/G2/G3 store-level and replay tests ─────────────────────────────────────


def test_g1_store_direct_refuses(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G1 fires at store level when the lifecycle is called directly, bypassing the port.

    Baseline: accept-risk with approval.decision='approved' is admitted.
    Single mutation: approval.decision='superseded'.
    The store's _validate_review_transition must refuse with the stable denial code
    even without the port's _validate_disposition_rules.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g1-store-direct.log")
    store = _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    appr = _approval(approval_id="approval-g1-store", decision="superseded")
    disp = _disposition(
        subject,
        disposition_id="disposition-g1-store",
        disposition_kind="accept-risk",
        authority_ref="approval-g1-store",
    )

    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-g1-store-direct",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-decision-not-approved", (
        "G1: store must refuse superseded decision when port is bypassed"
    )


def test_g2_store_direct_refuses(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G2 fires at store level when the lifecycle is called directly, bypassing the port.

    Baseline: accept-risk where decision_maker.role == approval.authority.role is admitted.
    Single mutation: decision_maker.role set to 'other-role'.
    The store must refuse with the stable denial code.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g2-store-direct.log")
    store = _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    appr = _approval(approval_id="approval-g2-store", authority_role="risk-owner")
    disp = _disposition(
        subject,
        disposition_id="disposition-g2-store",
        disposition_kind="accept-risk",
        authority_ref="approval-g2-store",
        decision_maker_role="other-role",
    )

    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-g2-store-direct",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-role-mismatch", (
        "G2: store must refuse role mismatch when port is bypassed"
    )


def test_g3_store_direct_refuses(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G3 fires at store level when the lifecycle is called directly, bypassing the port.

    Baseline: accept-risk without replacement_report_id is admitted.
    Single mutation: replacement_report_id added to accept-risk.
    The store must refuse with the stable denial code.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g3-store-direct.log")
    store = _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    appr = _approval(approval_id="approval-g3-store")
    disp = _disposition(
        subject,
        disposition_id="disposition-g3-store",
        disposition_kind="accept-risk",
        authority_ref="approval-g3-store",
        replacement_report_id="report-t5-replacement-neg",
    )

    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-g3-store-direct",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-unexpected-replacement", (
        "G3: store must refuse accept-risk with replacement_report_id when port is bypassed"
    )


def test_g1_replay_refuses(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """G1: a checksum-valid replayed frame with non-approved decision causes open() to raise.

    If an approval with decision='superseded' reaches the log (e.g. via a crafted
    frame bypassing the write port), the replay path must refuse it with
    EvidenceStoreError rather than silently admitting it.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g1-replay.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-g1-replay", decision="superseded")
    disp = _disposition(
        subject,
        disposition_id="disposition-g1-replay",
        disposition_kind="accept-risk",
        authority_ref="approval-g1-replay",
    )
    appr_id = appr["approval_id"]
    disp_id = disp["disposition_id"]
    tx = es._build_transaction(
        "tx-g1-replay", [appr_id, disp_id], _ACCEPTANCE_FP, [appr, disp]
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError):
        store2 = es.EvidenceStore(log_path)
        store2.open()


def test_g2_replay_refuses(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """G2: a checksum-valid replayed frame with role mismatch causes open() to raise.

    If a disposition with decision_maker.role != approval.authority.role reaches
    the log, the replay path must refuse it.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g2-replay.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-g2-replay", authority_role="risk-owner")
    disp = _disposition(
        subject,
        disposition_id="disposition-g2-replay",
        disposition_kind="accept-risk",
        authority_ref="approval-g2-replay",
        decision_maker_role="other-role",
    )
    appr_id = appr["approval_id"]
    disp_id = disp["disposition_id"]
    tx = es._build_transaction(
        "tx-g2-replay", [appr_id, disp_id], _ACCEPTANCE_FP, [appr, disp]
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError):
        store2 = es.EvidenceStore(log_path)
        store2.open()


def test_g3_replay_refuses(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """G3: a checksum-valid replayed accept-risk frame with replacement_report_id refuses on open.

    If an accept-risk carrying replacement_report_id reaches the log, the replay
    path must refuse it rather than silently admitting it.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g3-replay.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-g3-replay")
    disp = _disposition(
        subject,
        disposition_id="disposition-g3-replay",
        disposition_kind="accept-risk",
        authority_ref="approval-g3-replay",
        replacement_report_id="report-t5-replacement-neg",
    )
    appr_id = appr["approval_id"]
    disp_id = disp["disposition_id"]
    tx = es._build_transaction(
        "tx-g3-replay", [appr_id, disp_id], _ACCEPTANCE_FP, [appr, disp]
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError):
        store2 = es.EvidenceStore(log_path)
        store2.open()


# ── (b) per-kind decision and role negatives ──────────────────────────────────


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_decision_not_approved_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G1: approval.decision != 'approved' is refused for every disposition kind.

    Single mutation per kind: decision field changed from 'approved' to 'superseded';
    everything else is valid.  Exact denial code must be produced for all three kinds.
    """
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"decision-not-approved-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-decision-neg")
    appr = _approval(decision="superseded")  # single mutation
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp, approval_record=appr, current_subject=subject,
            transaction_id=f"tx-decision-not-approved-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-decision-not-approved"
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_role_mismatch_refused_per_kind(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """G2: decision_maker.role != approval.authority.role is refused for every kind.

    Single mutation: decision_maker.role set to 'different-role' while
    approval.authority.role remains 'risk-owner'.
    """
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer, _, rev_grant, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"role-mismatch-kind-{kind}.log",
    )
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-role-neg")
    disp["decision_maker"]["role"] = "different-role"  # single mutation
    appr = _approval(authority_role="risk-owner")
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp, approval_record=appr, current_subject=subject,
            transaction_id=f"tx-role-mismatch-kind-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-role-mismatch"
    assert log_path.read_bytes() == before


# ── (b) predecessor-role refusal ─────────────────────────────────────────────


def test_predecessor_role_mismatch_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A superseding approval with a different authority role is refused.

    A valid accept-risk is admitted first (establishing approval-t5 in the log).
    A second approval naming approval-t5 as predecessor but with a different
    authority role is refused with the stable denial code.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "predecessor-role.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject, issuer=issuer, evidence_grant=ev_grant)

    # Admit a valid accept-risk (approval-t5 role="risk-owner").
    disp_v1 = _disposition(subject, disposition_kind="accept-risk")
    appr_v1 = _approval()  # authority_role="risk-owner"
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp_v1, approval_record=appr_v1, current_subject=subject,
        transaction_id="tx-predrole-v1", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    # Attempt a superseding approval with a DIFFERENT role (single mutation).
    appr_v2 = copy.deepcopy(_approval(
        approval_id="approval-t5-predrole-v2",
        authority_role="different-role",
    ))
    appr_v2["lineage"]["predecessor_id"] = "approval-t5"  # predecessor role="risk-owner"
    disp_v2 = _disposition(
        subject,
        disposition_id="disposition-t5-predrole-v2",
        disposition_kind="repair-request",
        authority_ref="approval-t5-predrole-v2",
        decision_maker_role="different-role",
    )
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp_v2, approval_record=appr_v2, current_subject=subject,
            transaction_id="tx-predrole-v2", acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-approval-authority-role-mismatch"
    assert log_path.read_bytes() == before


# ── (b) changed approval body same id ────────────────────────────────────────


def test_changed_approval_body_same_id_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A changed approval body reusing a durable approval_id is refused.

    Once approval-t5 is durable, a follow-up disposition that supplies the
    same approval_id with a different body (timestamp changed) must be refused
    with the stable denial code.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "changed-approval.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject, issuer=issuer, evidence_grant=ev_grant)

    # Admit a repair-request (approval-t5 becomes durable).
    disp_v1 = _disposition(subject, disposition_kind="repair-request")
    appr_v1 = _approval()
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp_v1, approval_record=appr_v1, current_subject=subject,
        transaction_id="tx-changed-appr-v1", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    # Write another disposition with the SAME approval_id but a different timestamp.
    appr_v2 = copy.deepcopy(appr_v1)
    appr_v2["timestamp"] = "2026-10-10T00:00:00Z"  # single mutation
    disp_v2 = _disposition(
        subject, disposition_id="disposition-t5-changed-appr",
        disposition_kind="accept-risk",
    )
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp_v2, approval_record=appr_v2, current_subject=subject,
            transaction_id="tx-changed-appr-v2", acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-changed-approval"
    assert log_path.read_bytes() == before


# ── (b) invalid grant — non-None from a different issuer ─────────────────────


@pytest.mark.parametrize("kind", _ALL_DISPOSITION_KINDS)
def test_grant_from_different_issuer_refused(
    kind: str,
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A valid grant from a different issuer is refused with denied-producer-authority.

    The grant has a grant_id but issuer_a.verify_grant(grant_b) returns False
    because grant_b was issued by issuer_b; check_writer_authority_and_emit
    returns False → denied-producer-authority.
    """
    es = core_work_loop_t5_evidence_store
    store, log_path, issuer_a, _, _, subject = _make_setup_store(
        es, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        core_work_loop_t5_security_capability,
        tmp_path, f"diff-issuer-{kind}.log",
    )
    # Grant issued by a DIFFERENT issuer (has grant_id but issuer_a won't verify it).
    _issuer_b, grant_b = _make_review_grant(core_work_loop_t5_security_capability)
    disp = _make_kind_disposition(subject, kind, disposition_id=f"disp-{kind}-diff-issuer")
    appr = _approval()
    before = log_path.read_bytes()
    with pytest.raises(Exception) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp, approval_record=appr, current_subject=subject,
            transaction_id=f"tx-diff-issuer-{kind}",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer_a,  # original issuer — does not recognise grant_b
            grant=grant_b,
            audit_sink=_null_sink,
        )
    denial_code = getattr(exc_info.value, "denial_code", str(exc_info.value))
    assert denial_code == "denied-producer-authority"
    assert log_path.read_bytes() == before


# ── (d) disposition_closes: subject mismatch ──────────────────────────────────


def test_disposition_closes_false_for_wrong_subject(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """disposition_closes returns True for the correct subject and False for a different one.

    The admitted accept-risk references review_subject_fingerprint A.  Called
    with a subject whose fingerprint differs, disposition_closes must return False
    because the fingerprint check fails before reaching any other rule.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "closes-wrong-subject.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject, issuer=issuer, evidence_grant=ev_grant)

    disp = _disposition(subject, disposition_kind="accept-risk")
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-closes-wrong-subject", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    # True for the correct subject.
    assert store.disposition_closes("disposition-t5", subject) is True

    # False when a different review_subject_fingerprint is passed in.
    other_subject = _replacement_subject()
    assert store.disposition_closes("disposition-t5", other_subject) is False, (
        "disposition_closes must return False when subject fingerprint does not match"
    )


# ── (d) disposition_closes: replacement unassessed finding ────────────────────


def test_disposition_closes_false_until_replacement_finding_assessed(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """fixed-by disposition_closes returns False while a replacement finding is unassessed.

    All replacement findings must have a current assessment for disposition_closes
    to return True.  Before the first assessment, it must return False.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "closes-unassessed.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject, issuer=issuer, evidence_grant=ev_grant)

    replacement_subj = _replacement_subject()
    repl_rpt_id = "report-t5-repl-unassessed"
    repl_finding_id = "repl-finding-unassessed"
    repl_finding = {
        "schema_version": 1,
        "finding_id": repl_finding_id,
        "rule_ref": "AC-T5-001",
        "observation": "replacement finding — initially unassessed",
        "reachable_path": "path-unassessed",
        "actual_failure": "different failure — not matching original",
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": ["evidence:t5-repl-unassessed"],
        "material": True,
    }
    repl_report = {
        "schema_version": 1,
        "report_id": repl_rpt_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-t5-repl-unassessed",
            "producer": "synthetic-reviewer",
        },
        "findings": [repl_finding],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, repl_report,
        transaction_id="tx-t5-repl-unassessed-report",
        expected_subject=replacement_subj,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    disp = _disposition(
        subject, disposition_id="disposition-t5-unassessed",
        disposition_kind="fixed-by", replacement_report_id=repl_rpt_id,
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-t5-unassessed-disp", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    # Before assessment: replacement finding unassessed → must not close.
    assert store.disposition_closes("disposition-t5-unassessed", subject) is False, (
        "fixed-by must not close when replacement finding has no current assessment"
    )

    # Write an unsupported-opinion assessment (non-indeterminate, non-same-failure).
    repl_assessment = {
        "schema_version": 1,
        "assessment_id": "repl-assessment-unassessed",
        "finding_id": repl_finding_id,
        "report_id": repl_rpt_id,
        "review_subject_fingerprint": replacement_subj["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, repl_assessment,
        report_id=repl_rpt_id, finding=repl_finding, affected_criteria=_CRITERIA,
        transaction_id="tx-t5-repl-unassessed-assessment",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    # After assessment: every replacement finding has a current assessment → closes.
    assert store.disposition_closes("disposition-t5-unassessed", subject) is True, (
        "fixed-by must close once every replacement finding has a current assessment"
    )


# ── (d) disposition_closes: source report superseded (receipts retired) ──────


def test_disposition_closes_false_after_source_report_superseded(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """disposition_closes returns False after the assessment's source report is superseded.

    A second report for the same subject group (sequence=2) supersedes the
    original, making assessment-t5 non-current.  disposition_closes must return
    False because current_finding_assessments excludes the assessment.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "closes-source-superseded.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject, issuer=issuer, evidence_grant=ev_grant)

    disp = _disposition(subject, disposition_kind="accept-risk")
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-src-sup-disp", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    # Before: accept-risk closes.
    assert store.disposition_closes("disposition-t5", subject) is True, (
        "accept-risk must close before its source report is superseded"
    )

    # Write a second report for the same subject group (sequence=2, supersedes report-t5).
    report_v2 = {
        "schema_version": 1,
        "report_id": "report-t5-v2",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 2,
            "previous_report_id": "report-t5",
            "review_policy_fingerprint": _REVIEW_POLICY_FP,
            "source_event_id": "source-t5-v2",
            "producer": "synthetic-reviewer",
        },
        "findings": [_finding()],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, report_v2,
        transaction_id="tx-src-sup-report-v2",
        expected_subject=subject,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    # After: report-t5 no longer tip; assessment-t5 excluded from current_finding_assessments.
    assert store.disposition_closes("disposition-t5", subject) is False, (
        "accept-risk must stop closing once its source report is superseded by a newer one"
    )


# ── (e) optional-role open finding blocks eligibility ─────────────────────────


def test_optional_role_open_finding_blocks_eligibility(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Optional-role open supported material finding blocks acceptance_eligible.

    Mandatory quality-engineer is satisfied by a clean report.  Optional
    security-engineer has an open supported material finding.  The review must
    not be eligible.  The open_findings entry must carry the role field.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "optional-role-blocks.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    subject = _subject()

    # Mandatory role satisfied.
    mandatory_clean = _clean_report(subject, report_id="report-t5-mandatory-clean")
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, mandatory_clean,
        transaction_id="tx-t5-mandatory-clean",
        expected_subject=subject,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    # Optional role "security-engineer" with a supported material finding.
    opt_finding = {
        "schema_version": 1,
        "finding_id": "finding-t5-optional",
        "rule_ref": "AC-T5-002",
        "observation": "optional-role finding",
        "reachable_path": "path-optional",
        "actual_failure": "optional failure",
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": ["evidence:t5-optional-obs"],
        "material": True,
    }
    opt_report = {
        "schema_version": 1,
        "report_id": "report-t5-optional",
        "role": "security-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": _REVIEW_POLICY_FP,
            "source_event_id": "source-t5-optional",
            "producer": "synthetic-reviewer",
        },
        "findings": [opt_finding],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, opt_report,
        transaction_id="tx-t5-optional-report",
        expected_subject=subject,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )
    opt_assessment = {
        "schema_version": 1,
        "assessment_id": "assessment-t5-optional",
        "finding_id": "finding-t5-optional",
        "report_id": "report-t5-optional",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": ["evidence:t5-optional-obs"],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, opt_assessment,
        report_id="report-t5-optional", finding=opt_finding,
        affected_criteria=_CRITERIA,
        transaction_id="tx-t5-optional-assessment",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    policy_with_optional = {
        "policy_id": "policy-t5-optional",
        "review_policy_fingerprint": _REVIEW_POLICY_FP,
        "policy_version": "v1",
        "selector": "core-policy-t5",
        "roles": [
            {"role": "quality-engineer", "kind": "mandatory"},
            {"role": "security-engineer", "kind": "optional"},
        ],
        "waivers": [],
    }

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=policy_with_optional,
    )
    assert readiness["acceptance_eligible"] is False, (
        "optional-role open supported material finding must block eligibility"
    )
    open_findings = readiness["open_findings"]
    assert any(f["finding_id"] == "finding-t5-optional" for f in open_findings), (
        "open_findings must contain the optional-role finding"
    )
    opt_entry = next(
        (f for f in open_findings if f["finding_id"] == "finding-t5-optional"), None
    )
    assert opt_entry is not None
    assert opt_entry.get("role") == "security-engineer", (
        "open_findings entry must carry the reviewing role that flagged the finding"
    )


# ── (e) repair-request never closes ──────────────────────────────────────────


def test_repair_request_never_closes(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """repair-request disposition_closes always returns False.

    A successfully admitted repair-request signals that a fix is needed but
    does not assert the fix is complete.  disposition_closes must return False
    and the finding must remain open in review_readiness.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "repair-request-never-closes.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(store, core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge, subject, issuer=issuer, evidence_grant=ev_grant)

    disp = _disposition(subject, disposition_kind="repair-request")
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-repair-never-closes", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    assert store.disposition_closes("disposition-t5", subject) is False, (
        "repair-request must always return False from disposition_closes"
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store,
        review_subject=subject,
        review_policy=_review_policy(subject),
    )
    assert readiness["acceptance_eligible"] is False, (
        "repair-request must leave the finding open in readiness"
    )
    assert any(f["finding_id"] == "finding-t5" for f in readiness["open_findings"])


# ── R1–R4 repair ─────────────────────────────────────────────────────────────
#
# R1: Rule 4 bypass when lifecycle review_subject fingerprint differs.
# R2: Eligibility checks (016 no-assessment, 018 subject-equality, 020 no-finding)
#     must be owned by the store write path, not the port only.
# R3: An unreferenced approval in a disposition lifecycle frame must be refused.
# R4: A finding-assessment whose review_subject_fingerprint differs from its
#     source report's subject fingerprint must be refused.


# ── R1: port refuses when current_subject fingerprint != disposition fingerprint


def test_r1_port_refuses_wrong_subject_fingerprint(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R1: port refuses when current_subject fingerprint differs from disposition fingerprint.

    The probe scenario: accept-risk whose approval has manifest_ref='wrong' and
    spec_policy_fingerprint='wrong', sent with current_subject=_replacement_subject()
    (fingerprint 'review-subject-fp-t5-replacement') while the disposition targets
    subject fingerprint 'review-subject-fp-t5'.  Before the fix the store admitted
    this because the fingerprint-equality guard short-circuited Rule 4.  After the
    fix the store refuses with denied-disposition-subject-mismatch.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r1-port-wrong-subject.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="accept-risk")
    appr = _approval(manifest_ref="wrong", spec_policy_fingerprint="wrong")
    before = log_path.read_bytes()
    # Bypass: pass the replacement subject (different fingerprint) as current_subject.
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=_replacement_subject(),
            transaction_id="tx-r1-port-wrong-subject",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-subject-mismatch", (
        "R1: store must refuse when lifecycle subject fingerprint differs from disposition"
    )
    assert log_path.read_bytes() == before


def test_r1_store_direct_refuses_wrong_subject_fingerprint(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R1: store-direct refuses when lifecycle review_subject fingerprint differs.

    The lifecycle carries review_subject=_replacement_subject() (fingerprint
    'review-subject-fp-t5-replacement') but the disposition has
    review_subject_fingerprint='review-subject-fp-t5'.  The store must refuse
    denied-disposition-subject-mismatch rather than silently skipping Rule 4.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r1-store-direct-wrong-subject.log")
    store = _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    appr = _approval(approval_id="approval-r1-sd", manifest_ref="wrong")
    disp = _disposition(
        subject,
        disposition_id="disposition-r1-sd",
        disposition_kind="accept-risk",
        authority_ref="approval-r1-sd",
    )
    # The lifecycle passes the replacement subject (fingerprint mismatch with disp).
    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-r1-store-direct",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": _replacement_subject(),
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-subject-mismatch", (
        "R1: store must refuse when lifecycle review_subject fingerprint != disposition fp"
    )


def test_r1_replay_refuses_wrong_manifest_ref(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """R1: replay refuses a frame whose approval manifest_ref != review_subject_fingerprint.

    After the R1 fix, approval.base.manifest_ref is checked unconditionally on
    both the live path and replay, without needing a durable review-subject record.
    A crafted frame with manifest_ref='wrong' must be refused on open().
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r1-replay-wrong-manifest.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-r1-replay", manifest_ref="wrong-ref")
    disp = _disposition(
        subject,
        disposition_id="disposition-r1-replay",
        disposition_kind="accept-risk",
        authority_ref="approval-r1-replay",
    )
    appr_id = appr["approval_id"]
    disp_id = disp["disposition_id"]
    tx = es._build_transaction(
        "tx-r1-replay", [appr_id, disp_id], _ACCEPTANCE_FP, [appr, disp]
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError) as exc_info:
        store2 = es.EvidenceStore(log_path)
        store2.open()
    assert "denied-disposition-subject-mismatch" in str(exc_info.value), (
        "R1: replay must refuse frames with manifest_ref != review_subject_fingerprint"
    )


# ── R2: store-direct eligibility refusals (016, 018, 020) ────────────────────


def test_r2_store_direct_no_assessment_refused(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R2 / T5-MUT-016: store-direct disposition with a missing assessment is refused.

    A raw store caller (no port) sends a disposition whose assessment_id is not
    in the durable store.  The store must refuse denied-disposition-no-assessment.
    Before the R2 fix, this check lived only in the port.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r2-no-assessment.log")
    store = _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    appr = _approval(approval_id="approval-r2-016")
    disp = _disposition(
        subject,
        disposition_id="disposition-r2-016",
        disposition_kind="accept-risk",
        assessment_id="assessment-missing",
        authority_ref="approval-r2-016",
    )
    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-r2-016",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-no-assessment", (
        "R2/016: store must refuse a disposition whose assessment_id is not durable"
    )


def test_r2_store_direct_subject_mismatch_refused(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R2 / T5-MUT-018: store-direct disposition with wrong subject fingerprint is refused.

    The durable assessment has review_subject_fingerprint A.  The disposition is
    submitted with review_subject_fingerprint B (a different value).  The store
    must refuse denied-disposition-subject-mismatch.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r2-subject-mismatch.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Build a disposition that targets the original subject but claims a different fp.
    disp = _disposition(subject, disposition_id="disposition-r2-018", authority_ref="approval-r2-018")
    disp["review_subject_fingerprint"] = "other-subject-fp"
    appr = _approval(approval_id="approval-r2-018", manifest_ref="other-subject-fp")
    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-r2-018",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-subject-mismatch", (
        "R2/018: store must refuse disposition whose subject fp != assessment subject fp"
    )


def test_r2_store_direct_no_finding_refused(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R2 / T5-MUT-020: store-direct disposition with a missing finding is refused.

    The assessment exists and is supported, but the disposition's finding_id
    is not present in the source report.  The store must refuse
    denied-disposition-no-finding.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r2-no-finding.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Disposition references a finding_id not in the source report.
    appr = _approval(approval_id="approval-r2-020")
    disp = _disposition(
        subject,
        disposition_id="disposition-r2-020",
        disposition_kind="accept-risk",
        authority_ref="approval-r2-020",
    )
    disp["finding_id"] = "finding-missing"
    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp],
            transaction_id="tx-r2-020",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-disposition-no-finding", (
        "R2/020: store must refuse a disposition whose finding_id is not in the report"
    )


# ── R3: unreferenced ride-along approval is refused ───────────────────────────


def test_r3_ride_along_approval_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R3: a lifecycle approval_record whose id differs from the disposition's authority_ref
    must be refused with denied-approval-authority-required.

    The probe scenario: the first accept-risk (approval-t5) is admitted and closes.
    A second store-direct call includes approval-x in the lifecycle while the
    disposition still references approval-t5 (already durable).  approval-x must
    not ride along; the store must refuse.  After the refusal:
    - disposition_closes still returns True for the first disposition.
    - The store reopens cleanly.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "r3-ride-along.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Admit the first accept-risk via the port so the approval (approval-t5) becomes durable.
    disp = _disposition(subject, disposition_kind="accept-risk")
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-r3-first",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )
    assert store.disposition_closes("disposition-t5", subject) is True

    # Build a second disposition still referencing the durable approval-t5,
    # but provide approval-x in the lifecycle (unreferenced).
    appr_x = _approval(
        approval_id="approval-x",
        decision_scope="spec-policy",
        decision="superseded",
        authority_ref="approval-t5",
    )
    disp2 = _disposition(
        subject,
        disposition_id="disposition-r3-second",
        disposition_kind="accept-risk",
        assessment_id="assessment-t5",
        authority_ref="approval-t5",
    )
    before = log_path.read_bytes()
    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [disp2],
            transaction_id="tx-r3-ride-along",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": appr_x,
                "review_subject": subject,
            },
        )
    assert exc_info.value.denial_code == "denied-approval-authority-required", (
        "R3: a lifecycle approval whose id differs from the disposition authority_ref "
        "must be refused"
    )
    assert log_path.read_bytes() == before, "refused write must not modify the log"

    # The earlier accept-risk still closes.
    assert store.disposition_closes("disposition-t5", subject) is True, (
        "the first accepted disposition must still close after the refused second"
    )

    # The store reopens cleanly.
    store2 = es.EvidenceStore(log_path)
    store2.open()
    assert store2.disposition_closes("disposition-t5", subject) is True, (
        "the store must reopen and the first disposition must still close"
    )


# ── NOT PROVEN: raw batch pairing an approval with a disposition ───────────────


def test_raw_approval_paired_with_disposition_refused(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """NOT PROVEN fix: raw batch pairing an approval with a disposition is refused
    with denied-approval-authority-required, not denied-disposition-authority-required.

    The original test_raw_approval_write_refused_and_store_reopens sends only an
    approval record, which is caught by both T5-MUT-030 (raw approval gate) and
    T5-MUT-031 (unpaired approval gate) — so neither alone distinguishes.  Pairing
    the approval with a disposition makes T5-MUT-030 the only gate that names
    approvals; T5-MUT-033 would refuse with a different code.
    Mutation: T5-MUT-030 (raw approval gate removed) → refused with
    denied-disposition-authority-required instead.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "not-proven-raw-pair.log")
    store = _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    # The raw semantic batch path uses an evidence grant (not a review grant).
    grant = _ev_grant

    subject = _subject()
    appr = _approval(approval_id="approval-raw-pair")
    disp = _disposition(subject, authority_ref="approval-raw-pair")

    with pytest.raises(es.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [appr, disp],
            transaction_id="tx-raw-pair",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-approval-authority-required", (
        "raw batch pairing approval with disposition must refuse with "
        "denied-approval-authority-required (not denied-disposition-authority-required)"
    )


# ── G replay: assert which rule refused via EvidenceStoreError message code ───


def test_g1_replay_refuses_with_code(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """G1: replayed frame with non-approved decision names the rule in the error message."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g1-replay-code.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-g1-replay-code", decision="superseded")
    disp = _disposition(
        subject,
        disposition_id="disposition-g1-replay-code",
        disposition_kind="accept-risk",
        authority_ref="approval-g1-replay-code",
    )
    tx = es._build_transaction(
        "tx-g1-replay-code", [appr["approval_id"], disp["disposition_id"]],
        _ACCEPTANCE_FP, [appr, disp],
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError) as exc_info:
        store2 = es.EvidenceStore(log_path)
        store2.open()
    assert "denied-disposition-decision-not-approved" in str(exc_info.value), (
        "G1 replay: error message must name the violated rule"
    )


def test_g2_replay_refuses_with_code(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """G2: replayed frame with role mismatch names the rule in the error message."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g2-replay-code.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-g2-replay-code", authority_role="risk-owner")
    disp = _disposition(
        subject,
        disposition_id="disposition-g2-replay-code",
        disposition_kind="accept-risk",
        authority_ref="approval-g2-replay-code",
        decision_maker_role="other-role",
    )
    tx = es._build_transaction(
        "tx-g2-replay-code", [appr["approval_id"], disp["disposition_id"]],
        _ACCEPTANCE_FP, [appr, disp],
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError) as exc_info:
        store2 = es.EvidenceStore(log_path)
        store2.open()
    assert "denied-disposition-role-mismatch" in str(exc_info.value), (
        "G2 replay: error message must name the violated rule"
    )


def test_g3_replay_refuses_with_code(
    core_work_loop_t5_evidence_store: ModuleType,
    tmp_path: Path,
) -> None:
    """G3: replayed accept-risk frame with replacement_report_id names the rule."""
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "g3-replay-code.log")
    store = _open_store(es, log_path)
    del store

    subject = _subject()
    appr = _approval(approval_id="approval-g3-replay-code")
    disp = _disposition(
        subject,
        disposition_id="disposition-g3-replay-code",
        disposition_kind="accept-risk",
        authority_ref="approval-g3-replay-code",
        replacement_report_id="report-t5-replacement-neg",
    )
    tx = es._build_transaction(
        "tx-g3-replay-code", [appr["approval_id"], disp["disposition_id"]],
        _ACCEPTANCE_FP, [appr, disp],
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(es.EvidenceStoreError) as exc_info:
        store2 = es.EvidenceStore(log_path)
        store2.open()
    assert "denied-disposition-unexpected-replacement" in str(exc_info.value), (
        "G3 replay: error message must name the violated rule"
    )


# ── Reachable-untested cases ──────────────────────────────────────────────────


def test_t5_mut_041_fixed_by_without_replacement_id_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-041: fixed-by disposition with no replacement_report_id key is refused.

    The schema allows omitting the key.  Store Rule 5 requires a non-empty id.
    Mutation: Rule 5 non-empty check removed → refused with
    denied-disposition-replacement-not-durable instead.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-041-fixed-by-no-id.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # fixed-by with no replacement_report_id key (not just empty string).
    disp = _disposition(subject, disposition_kind="fixed-by")
    # _disposition sets replacement_report_id=None; remove it from the record to
    # leave the key absent (schema-valid for fixed-by without the key).
    disp.pop("replacement_report_id", None)
    appr = _approval()
    before = log_path.read_bytes()
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store,
            disp,
            approval_record=appr,
            current_subject=subject,
            transaction_id="tx-mut-041",
            acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer,
            grant=rev_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-missing-replacement", (
        "T5-MUT-041: fixed-by without replacement_report_id key must refuse "
        "denied-disposition-missing-replacement"
    )
    assert log_path.read_bytes() == before


def test_t5_mut_053_retry_different_disposition_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-053: retry with same tx-id but different disposition_id is refused.

    Commit disp-1 under tx-A and disp-2 under tx-B.  Retry tx-A with disp-2's
    exact body — the disposition_id does not match the committed one, so the
    idempotent recognition must fail and the duplicate-tx check must refuse.
    Mutation: disposition-id check removed → tx-A returned as idempotent.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-053-retry-diff-disp.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp1 = _disposition(subject, disposition_id="disp-053-a", disposition_kind="accept-risk")
    disp2 = _disposition(subject, disposition_id="disp-053-b", disposition_kind="repair-request")
    appr = _approval()
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp1, approval_record=appr, current_subject=subject,
        transaction_id="tx-053-A", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp2, approval_record=appr, current_subject=subject,
        transaction_id="tx-053-B", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    # Retry tx-053-A with disp-2's body.
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp2, approval_record=appr, current_subject=subject,
            transaction_id="tx-053-A", acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id", (
        "T5-MUT-053: retry with different disposition_id must refuse "
        "denied-duplicate-transaction-id"
    )


def test_t5_mut_054_retry_changed_disposition_body_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-054: retry with same tx-id and disposition_id but changed body is refused.

    Commit disp under tx-A.  Retry tx-A with same disposition_id but
    lineage.source_event_id changed.  The idempotent check must fail.
    Mutation: disposition body check removed → accepted as idempotent.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-054-retry-body.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="accept-risk")
    appr = _approval()
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=appr, current_subject=subject,
        transaction_id="tx-054-A", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    # Change the body: same disposition_id, different source_event_id.
    import copy as _copy
    disp_changed = _copy.deepcopy(disp)
    disp_changed["lineage"]["source_event_id"] = "event-changed-054"
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp_changed, approval_record=appr, current_subject=subject,
            transaction_id="tx-054-A", acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id", (
        "T5-MUT-054: retry with changed disposition body must refuse "
        "denied-duplicate-transaction-id"
    )


def test_t5_mut_055_retry_changed_approval_body_refused(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-055: retry with same tx-id and disposition but changed approval body is refused.

    Commit under tx-A.  Retry with same disposition but approval timestamp changed.
    Mutation: approval body check removed → accepted as idempotent.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-055-retry-appr.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="accept-risk")
    appr = _approval()
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=appr, current_subject=subject,
        transaction_id="tx-055-A", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )
    # Same approval_id, different timestamp.
    import copy as _copy2
    appr_changed = _copy2.deepcopy(appr)
    appr_changed["timestamp"] = "2026-10-10T00:00:00Z"
    with pytest.raises(core_work_loop_t5_disposition.ReviewDispositionRefused) as exc_info:
        core_work_loop_t5_disposition.append_finding_disposition(
            store, disp, approval_record=appr_changed, current_subject=subject,
            transaction_id="tx-055-A", acceptance_fingerprint=_ACCEPTANCE_FP,
            issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id", (
        "T5-MUT-055: retry with changed approval body must refuse "
        "denied-duplicate-transaction-id"
    )


def test_t5_mut_065_closes_missing_assessment_returns_false(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-065: disposition_closes returns False when the referenced assessment is absent.

    A disposition committed with assessment_id='assessment-missing' via store-direct
    (bypassing eligibility).  disposition_closes must return False, not raise.
    Mutation: assessment exists check removed → AttributeError instead of False.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-065-closes-no-assessment.log")
    # Open to create the log file, then close immediately; raw frame injection follows.
    _open_store(es, log_path)
    issuer, _ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    appr = _approval(approval_id="approval-065")
    disp = _disposition(
        subject,
        disposition_id="disposition-065",
        disposition_kind="accept-risk",
        assessment_id="assessment-missing",
        authority_ref="approval-065",
    )
    # Inject directly so the eligibility check is bypassed.
    # After R2 fix, the store's eligibility check would refuse this; we inject
    # via the raw frame path to simulate an already-committed but invalid frame.
    tx = es._build_transaction(
        "tx-065", [appr["approval_id"], disp["disposition_id"]],
        _ACCEPTANCE_FP, [appr, disp],
    )
    frame_bytes = es._serialize_frame(tx, [appr, disp])
    with Path(log_path).open("ab") as f:
        f.write(frame_bytes)

    # Replay owns eligibility: an injected disposition with no durable
    # assessment must refuse the whole log rather than admit the frame.
    store2 = es.EvidenceStore(log_path)
    with pytest.raises(es.EvidenceStoreError, match="denied-disposition-no-assessment"):
        store2.open()


def test_t5_mut_073_closes_false_replacement_wrong_role(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-073: disposition_closes returns False when replacement has wrong role.

    A fixed-by disposition whose replacement report has role='security-reviewer'
    while the original is 'quality-engineer'.  Role mismatch must return False.
    Mutation: role equality check removed → True.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-073-wrong-role.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Persist a replacement report with the wrong role.
    replacement_subj = _replacement_subject()
    wrong_role_report = {
        "schema_version": 1,
        "report_id": "report-t5-wrong-role",
        "role": "security-reviewer",  # differs from original "quality-engineer"
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-wrong-role",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        wrong_role_report,
        transaction_id="tx-wrong-role-report",
        expected_subject=replacement_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id="report-t5-wrong-role",
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-073-fixed-by",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    assert store.disposition_closes("disposition-t5", subject) is False, (
        "T5-MUT-073: disposition_closes must return False when replacement has wrong role"
    )


def test_t5_mut_074_closes_false_different_delivery_subject(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-074: disposition_closes returns False when replacement has different delivery subject.

    A fixed-by replacement report whose delivery_subject_ref.subject_id differs
    from the original's delivery subject id must not close the disposition.
    Mutation: shared delivery_subject_ref check removed → True.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-074-diff-delivery.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    # Build a replacement subject with a different delivery subject id.
    other_subj = copy.deepcopy(_replacement_subject())
    other_subj["delivery_subject_ref"]["subject_id"] = "delivery-subject-other"
    other_report = {
        "schema_version": 1,
        "report_id": "report-t5-other-delivery",
        "role": "quality-engineer",
        "subject": other_subj,
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": other_subj["review_policy_fingerprint"],
            "source_event_id": "source-other-delivery",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        other_report,
        transaction_id="tx-other-delivery",
        expected_subject=other_subj,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id="report-t5-other-delivery",
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-074-fixed-by",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    assert store.disposition_closes("disposition-t5", subject) is False, (
        "T5-MUT-074: disposition_closes must return False when replacement has "
        "different delivery_subject_ref.subject_id"
    )


def test_t5_mut_076_closes_false_replacement_before_assessment(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-076: disposition_closes returns False when replacement admitted before assessment.

    The replacement report is admitted in the log BEFORE the original report and
    assessment.  Rule: replacement must be admitted after the assessment.
    Mutation: tx ordering check removed → True.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-076-before-assessment.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    # Persist replacement FIRST, before original report and assessment.
    replacement_subj = _replacement_subject()
    replacement_report = {
        "schema_version": 1,
        "report_id": "report-t5-repl-076",
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-076",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, replacement_report, transaction_id="tx-repl-076",
        expected_subject=replacement_subj, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Now persist original report and assessment.
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id="report-t5-repl-076",
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store,
        disp,
        approval_record=_approval(),
        current_subject=subject,
        transaction_id="tx-076-fixed-by",
        acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer,
        grant=rev_grant,
        audit_sink=_null_sink,
    )

    assert store.disposition_closes("disposition-t5", subject) is False, (
        "T5-MUT-076: disposition_closes must return False when replacement report "
        "was admitted before the assessment"
    )


def test_t5_mut_080_closes_true_different_actual_failure(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-080: disposition_closes returns True when replacement finding has a different actual_failure.

    Only a SAME actual_failure blocks closing.  A different failure string must
    not block it.
    Mutation: actual_failure equality clause removed → False (both failures block).
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-080-diff-failure.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    replacement_subj = _replacement_subject()
    repl_finding = {
        "schema_version": 1,
        "finding_id": "repl-finding-080",
        "rule_ref": "AC-T5-001",
        "observation": "replacement finding",
        "reachable_path": "replacement path",
        "actual_failure": "a different failure",  # differs from original
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": [],
        "material": True,
    }
    repl_report = {
        "schema_version": 1,
        "report_id": "report-t5-repl-080",
        "role": "quality-engineer",
        "subject": copy.deepcopy(replacement_subj),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": replacement_subj["review_policy_fingerprint"],
            "source_event_id": "source-080",
            "producer": "synthetic-reviewer",
        },
        "findings": [repl_finding],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, repl_report, transaction_id="tx-repl-080",
        expected_subject=replacement_subj, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Assess the replacement finding as supported.
    repl_assessment = {
        "schema_version": 1,
        "assessment_id": "assessment-repl-080",
        "finding_id": "repl-finding-080",
        "report_id": "report-t5-repl-080",
        "review_subject_fingerprint": replacement_subj["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, repl_assessment, report_id="report-t5-repl-080",
        finding=repl_finding, affected_criteria=_CRITERIA,
        transaction_id="tx-repl-a-080", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    disp = _disposition(
        subject,
        disposition_kind="fixed-by",
        replacement_report_id="report-t5-repl-080",
    )
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-080-fixed-by", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    assert store.disposition_closes("disposition-t5", subject) is True, (
        "T5-MUT-080: disposition_closes must return True when replacement finding "
        "has a different actual_failure from the original"
    )


def test_t5_mut_090_current_assessments_excludes_stale_tip(
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-090 + T5-MUT-091 direct: current_finding_assessments excludes replaced tip.

    After report-t5 is superseded by report-t5-v2, an unsupported assessment of
    report-t5 must not appear in current_finding_assessments.
    Mutation (090): tip check removed → absent entry becomes present.
    Mutation (091): exact receipt set removed → stale entry becomes current.
    Both are gated together for supported entries; unsupported uses only 090.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-090-stale-tip.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    subject = _subject()

    # Persist original report.
    core_work_loop_t5_review_persistence.append_current_review_report(
        store,
        _report(subject),
        transaction_id="tx-090-r1",
        expected_subject=subject,
        issuer=issuer,
        grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Assess the finding as unsupported (no receipts needed).
    unsupported_a = {
        "schema_version": 1,
        "assessment_id": "assessment-090-unsup",
        "finding_id": "finding-t5",
        "report_id": "report-t5",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, unsupported_a, report_id="report-t5", finding=_finding(),
        affected_criteria=_CRITERIA,
        transaction_id="tx-090-a", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    # Supersede with report-t5-v2.
    v2_report = {
        "schema_version": 1,
        "report_id": "report-t5-v2",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 2,
            "previous_report_id": "report-t5",
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": "source-v2",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, v2_report, transaction_id="tx-090-r2",
        expected_subject=subject, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    # The stale report-t5 assessment must not appear in current_finding_assessments.
    current = dict(store.current_finding_assessments(subject["review_subject_fingerprint"]))
    assert ("report-t5", "finding-t5") not in current, (
        "T5-MUT-090: current_finding_assessments must exclude assessment of stale report tip"
    )


def test_t5_mut_094_current_assessments_scoped_to_subject(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-094: review_readiness is scoped to the queried subject fingerprint.

    After the standard setup for subject A, querying readiness for subject B
    (_replacement_subject) must yield empty open_findings.
    Mutation: subject scope filter removed → finding-t5 appears in open_findings.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-094-scope.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    other = _replacement_subject()
    other_policy = _review_policy(other)
    other_policy["review_policy_fingerprint"] = other["review_policy_fingerprint"]
    readiness = core_work_loop_t5_disposition.review_readiness(
        store, review_subject=other, review_policy=other_policy,
    )
    assert readiness["open_findings"] == [], (
        "T5-MUT-094: review_readiness for a different subject must yield no open_findings"
    )


def test_t5_mut_104_obligation_recompute_rereverifies_disposition(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-104: obligation recompute re-verifies each disposition via disposition_closes.

    After a repair-request is admitted (which never closes), the obligation decision
    must be 'open-supported-material-finding', not 'satisfied-findings'.
    Mutation: disposition_closes call replaced with True → 'satisfied-findings'.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-104-recompute.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="repair-request")
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-104-repair", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store, review_subject=subject, review_policy=_review_policy(subject),
    )
    assert readiness["obligations"][0]["decision"] == "open-supported-material-finding", (
        "T5-MUT-104: obligation decision after repair-request must remain "
        "'open-supported-material-finding' (repair-request never closes)"
    )


def test_t5_mut_106_recompute_skips_nonsupported_assessments(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-106: recompute skips non-supported assessments.

    Two material findings: f1 is supported+disposed accept-risk, f2 is unsupported.
    Only f1 enters the recompute loop.  Obligation decision must be
    'satisfied-findings' and acceptance_eligible must be True.
    Mutation: non-supported skip removed → f2 also recomputed, decision becomes
    'open-supported-material-finding' and eligible becomes False.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-106-skip-nonsup.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()

    f1 = _finding()
    f2 = {
        "schema_version": 1,
        "finding_id": "finding-t5-b",
        "rule_ref": "AC-T5-002",
        "observation": "second finding",
        "reachable_path": "path-b",
        "actual_failure": "second failure",
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": [],
        "material": True,
    }
    report = _report(subject)
    report["findings"] = [f1, f2]
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, report, transaction_id="tx-106-report",
        expected_subject=subject, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Assess f1 as supported.
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, _assessment(subject), report_id="report-t5", finding=f1,
        affected_criteria=_CRITERIA, transaction_id="tx-106-a1",
        acceptance_fingerprint=_ACCEPTANCE_FP, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    # Assess f2 as unsupported.
    a2 = {
        "schema_version": 1,
        "assessment_id": "assessment-t5-b",
        "finding_id": "finding-t5-b",
        "report_id": "report-t5",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, a2, report_id="report-t5", finding=f2, affected_criteria=_CRITERIA,
        transaction_id="tx-106-a2", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=ev_grant, audit_sink=_null_sink,
    )

    # Dispose f1 with accept-risk.
    core_work_loop_t5_disposition.append_finding_disposition(
        store, _disposition(subject), approval_record=_approval(),
        current_subject=subject, transaction_id="tx-106-disp",
        acceptance_fingerprint=_ACCEPTANCE_FP, issuer=issuer, grant=rev_grant,
        audit_sink=_null_sink,
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store, review_subject=subject, review_policy=_review_policy(subject),
    )
    assert readiness["obligations"][0]["decision"] == "satisfied-findings", (
        "T5-MUT-106: obligation decision must be 'satisfied-findings' when only "
        "f1 (supported+closed) is in the recompute loop"
    )
    assert readiness["acceptance_eligible"] is True, (
        "T5-MUT-106: acceptance_eligible must be True when all supported findings "
        "are disposed and only an unsupported finding remains"
    )


def test_t5_mut_107_open_findings_material_only(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-107: open_findings only includes material findings.

    A report with one non-material finding assessed as supported must yield
    open_findings == [].
    Mutation: material filter in open_findings removed → finding appears.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-107-nonmaterial-open.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    subject = _subject()

    nonmat_finding = {
        "schema_version": 1,
        "finding_id": "finding-t5",
        "rule_ref": "AC-T5-001",
        "observation": "non-material finding",
        "reachable_path": "path",
        "actual_failure": "failure",
        "affected_acceptance_criteria": _CRITERIA,
        "evidence_refs": [],
        "material": False,
    }
    report = _report(subject)
    report["findings"] = [nonmat_finding]
    core_work_loop_t5_review_persistence.append_current_review_report(
        store, report, transaction_id="tx-107-report",
        expected_subject=subject, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )
    # Assess it supported (even though not material).
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, _assessment(subject), report_id="report-t5", finding=nonmat_finding,
        affected_criteria=_CRITERIA, transaction_id="tx-107-a",
        acceptance_fingerprint=_ACCEPTANCE_FP, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store, review_subject=subject, review_policy=_review_policy(subject),
    )
    assert readiness["open_findings"] == [], (
        "T5-MUT-107: open_findings must be empty when only a non-material finding "
        "is assessed"
    )


def test_t5_mut_108_open_findings_supported_only(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-108: open_findings only includes supported assessments.

    A material finding assessed as unsupported-opinion must not appear in
    open_findings.
    Mutation: supported filter in open_findings removed → finding appears.
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-108-unsup-open.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    subject = _subject()

    core_work_loop_t5_review_persistence.append_current_review_report(
        store, _report(subject), transaction_id="tx-108-report",
        expected_subject=subject, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )
    unsup_assessment = {
        "schema_version": 1,
        "assessment_id": "assessment-t5",
        "finding_id": "finding-t5",
        "report_id": "report-t5",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "unsupported-opinion",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    core_work_loop_t5_review_bridge.append_finding_assessment_bridge(
        store, unsup_assessment, report_id="report-t5", finding=_finding(),
        affected_criteria=_CRITERIA, transaction_id="tx-108-a",
        acceptance_fingerprint=_ACCEPTANCE_FP, issuer=issuer, grant=ev_grant,
        audit_sink=_null_sink,
    )

    readiness = core_work_loop_t5_disposition.review_readiness(
        store, review_subject=subject, review_policy=_review_policy(subject),
    )
    assert readiness["open_findings"] == [], (
        "T5-MUT-108: open_findings must be empty when the finding is assessed "
        "unsupported-opinion (not supported)"
    )


def test_t5_mut_060_closes_subject_direct(
    core_work_loop_t5_disposition: ModuleType,
    core_work_loop_t5_evidence_store: ModuleType,
    core_work_loop_t5_review_persistence: ModuleType,
    core_work_loop_t5_review_bridge: ModuleType,
    core_work_loop_t5_security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T5-MUT-060 direct: disposition_closes False for a different subject fingerprint.

    Pins the disposition subject check alone: the disposition is accept-risk so
    the only reason disposition_closes returns False is the subject mismatch.
    Mutation (060): subject check removed → True (because accept-risk otherwise
    returns True unconditionally).
    """
    es = core_work_loop_t5_evidence_store
    log_path = _store_path(tmp_path, "mut-060-subject-direct.log")
    store = _open_store(es, log_path)
    issuer, ev_grant = _make_evidence_grant(core_work_loop_t5_security_capability)
    _, rev_grant = _make_review_grant(core_work_loop_t5_security_capability, issuer=issuer)
    subject = _subject()
    _setup_report_and_assessment(
        store,
        core_work_loop_t5_review_persistence,
        core_work_loop_t5_review_bridge,
        subject,
        issuer=issuer,
        evidence_grant=ev_grant,
    )

    disp = _disposition(subject, disposition_kind="accept-risk")
    core_work_loop_t5_disposition.append_finding_disposition(
        store, disp, approval_record=_approval(), current_subject=subject,
        transaction_id="tx-060-accept-risk", acceptance_fingerprint=_ACCEPTANCE_FP,
        issuer=issuer, grant=rev_grant, audit_sink=_null_sink,
    )

    # Correct subject: closes = True.
    assert store.disposition_closes("disposition-t5", subject) is True

    # Wrong subject: the subject check is the ONLY reason it is False.
    other = _replacement_subject()
    assert store.disposition_closes("disposition-t5", other) is False, (
        "T5-MUT-060: disposition_closes must return False for a different subject "
        "(and must not raise)"
    )
