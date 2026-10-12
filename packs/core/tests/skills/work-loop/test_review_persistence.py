"""T3 TDD suite: validated review reports persist through EvidenceStore.

Mode: TDD (structured-review-boundary plan T3).

The suite loads shipped work-loop scripts by literal path. Runtime review
persistence must stay standard-library-only, reuse EvidenceStore's semantic
transaction log, and derive current reports only from validated semantic
frames.
"""

from __future__ import annotations

import copy
import importlib.util
import os
import stat
import sys
import threading
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path for pack-boundary tests."""
    if not path.exists():
        pytest.fail(f"T3 review persistence module is not implemented: {path.name}")
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


@pytest.fixture(scope="module")
def evidence_store() -> ModuleType:
    """Load the Slice 1 evidence store."""
    return _load_module("evidence_store_t3", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def review_persistence() -> ModuleType:
    """Load the T3 review persistence boundary."""
    return _load_module(
        "review_persistence_under_test",
        SCRIPTS / "_review_persistence.py",
    )


@pytest.fixture(scope="module")
def review_selection() -> ModuleType:
    """Load the T2 review subject projector."""
    return _load_module("review_selection_t3", SCRIPTS / "_review_selection.py")


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    """Load the Slice 1 capability issuer."""
    return _load_module("security_capability_t3", SCRIPTS / "_security_capability.py")


def _null_sink(event: object) -> None:
    """Accept security events without persisting them in the test."""


def _make_grant(
    security_capability: ModuleType,
    *,
    operations: list[str] | None = None,
) -> tuple[object, object]:
    """Return a valid producer authority pair for semantic evidence appends."""
    issuer = security_capability.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=operations or ["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


def _delivery_subject() -> dict:
    """Build the delivery subject consumed by the review projector."""
    return {
        "schema_version": 1,
        "subject_id": "delivery-subject-current",
        "acceptance_fingerprint": "acceptance-current",
        "product": {
            "base_ref": "base-tree",
            "result_ref": "result-tree",
        },
        "spec": {
            "path": "docs/specs/structured-review-boundary/spec.md",
            "fingerprint": "spec-fingerprint",
        },
        "evidence_policy_ref": "evidence-policy-v1",
        "exclusions": [],
        "lineage": {
            "provider": "legacy-worktree-snapshot",
            "projection_version": "1.0",
        },
        "task_projection_revision": "task-revision-a",
        "task_projection_hash": "task-hash-a",
    }


def _delivery_subject_with_task_revision(revision: str) -> dict:
    """Build a delivery subject with only task-projection provenance changed."""
    subject = _delivery_subject()
    subject["task_projection_revision"] = revision
    subject["task_projection_hash"] = f"task-hash-{revision}"
    return subject


def _changed_paths() -> list[dict[str, str]]:
    """Return a deterministic fake change manifest."""
    return [
        {
            "path": "packs/core/.apm/skills/work-loop/scripts/_evidence_store.py",
            "status": "modified",
        },
        {
            "path": "packs/core/tests/skills/work-loop/test_review_persistence.py",
            "status": "added",
        },
    ]


def _review_subject(review_selection: ModuleType) -> dict:
    """Project the current review subject."""
    return review_selection.project_review_subject(
        _delivery_subject(),
        changed_paths=_changed_paths(),
        review_policy_fingerprint="review-policy-v1",
        plan_digest="plan-digest-a",
        task_projection_revision="task-revision-b",
        adapter_event_id="adapter-event-a",
    )


def _finding() -> dict:
    """Build a minimal valid finding embedded in a report."""
    return {
        "schema_version": 1,
        "finding_id": "finding-review-persistence-1",
        "rule_ref": "AC-0012",
        "observation": "Review report persistence must validate complete report content.",
        "reachable_path": "review adapter to semantic evidence store",
        "actual_failure": "Unsafe report content could become durable review authority.",
        "affected_acceptance_criteria": ["AC-0012"],
        "evidence_refs": ["packs/core/.apm/skills/work-loop/scripts/_content_safety.py"],
        "material": True,
    }


def _report(subject: dict, *, report_id: str = "report-current-1") -> dict:
    """Build a current structured review report."""
    return {
        "schema_version": 1,
        "report_id": report_id,
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": "review-policy-v1",
            "source_event_id": f"source-{report_id}",
            "producer": "synthetic-reviewer",
        },
        "findings": [_finding()],
    }


def _clean_report(
    subject: dict,
    *,
    report_id: str = "report-clean-1",
    sequence: int = 1,
    previous_report_id: str | None = None,
) -> dict:
    """Build a valid clean report with caller-controlled lineage."""
    report = _report(subject, report_id=report_id)
    report["terminal_status"] = "clean"
    report["findings"] = []
    report["lineage"]["sequence"] = sequence
    report["lineage"]["source_event_id"] = f"source-{report_id}"
    if previous_report_id is not None:
        report["lineage"]["previous_report_id"] = previous_report_id
    return report


def _obligation(subject: dict) -> dict:
    """Build a valid review obligation."""
    return {
        "schema_version": 1,
        "obligation_id": "obligation-quality-1",
        "role": "quality-engineer",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "review_policy_fingerprint": "review-policy-v1",
        "kind": "mandatory",
        "lineage": {"selector": "core-policy", "policy_version": "v1"},
    }


def _assessment(subject: dict, report_id: str = "report-clean-1") -> dict:
    """Build a valid finding assessment record."""
    return {
        "schema_version": 1,
        "assessment_id": "assessment-quality-1",
        "finding_id": "finding-review-persistence-1",
        "report_id": report_id,
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": ["evidence-ref-1"],
        "lineage": {"predicate_version": "v1"},
    }


def _disposition(subject: dict) -> dict:
    """Build a valid finding disposition record."""
    return {
        "schema_version": 1,
        "disposition_id": "disposition-quality-1",
        "finding_id": "finding-review-persistence-1",
        "assessment_id": "assessment-quality-1",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "disposition": "accept-risk",
        "decision_maker": {"identity": "review-owner", "role": "risk-owner"},
        "lineage": {"authority_ref": "authority-1", "source_event_id": "event-1"},
    }


def _receipt(receipt_id: str = "receipt-batch-1") -> dict:
    """Build a valid legacy evidence receipt."""
    return {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "acceptance_fingerprint": "acceptance-current",
        "lineage": {"criterion_ref": "AC-0004"},
        "selector": {"term": "test-run"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "test-result"},
        "outcome": "passed",
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _supersession(
    supersession_id: str = "supersession-batch-1",
    superseded_receipt_ids: list[str] | None = None,
) -> dict:
    """Build a valid legacy evidence supersession."""
    return {
        "schema_version": 1,
        "supersession_id": supersession_id,
        "superseded_receipt_ids": superseded_receipt_ids or ["receipt-batch-1"],
        "authority": {"identity": "authority-generic", "role": "evidence-authority"},
        "provenance": {"reason_code": "review-assessment-superseded"},
    }


def _open_store(evidence_store: ModuleType, log_path: Path) -> object:
    """Open a fresh EvidenceStore at a fake git root under tmp_path."""
    store = evidence_store.EvidenceStore(log_path)
    store.open()
    return store


def _store_path(tmp_path: Path, name: str) -> Path:
    """Return an evidence log under a fake git root."""
    log_path = tmp_path / "repo" / ".work-loop" / name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def _append_review_frame(
    evidence_store: ModuleType,
    log_path: Path,
    report: dict,
    *,
    tx_id: str,
    acceptance_fingerprint: str,
) -> None:
    """Append a raw review-report frame with a valid checksum."""
    body = {
        "schema_version": 1,
        "transaction_id": tx_id,
        "ordered_record_ids": [report["report_id"]],
        "acceptance_fingerprint": acceptance_fingerprint,
    }
    tx = {**body, "checksum": evidence_store._compute_frame_checksum(body, [report])}
    frame = (
        evidence_store._canonical_json({"tx": tx, "records": [report]}) + "\n"
    ).encode("utf-8")
    log_path.write_bytes(log_path.read_bytes() + frame)


def _append_frame(
    evidence_store: ModuleType,
    log_path: Path,
    records: list[dict],
    *,
    tx_id: str,
    ordered_record_ids: list[str],
    acceptance_fingerprint: str,
) -> None:
    """Append a raw semantic frame with a valid checksum."""
    body = {
        "schema_version": 1,
        "transaction_id": tx_id,
        "ordered_record_ids": ordered_record_ids,
        "acceptance_fingerprint": acceptance_fingerprint,
    }
    tx = {**body, "checksum": evidence_store._compute_frame_checksum(body, records)}
    frame = (
        evidence_store._canonical_json({"tx": tx, "records": records}) + "\n"
    ).encode("utf-8")
    log_path.write_bytes(log_path.read_bytes() + frame)


def test_current_report_persists_replays_and_binds_whole_subject_identity(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A report transaction is durable only when its whole subject matches."""
    log_path = _store_path(tmp_path, "semantic-evidence.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    report = _report(subject)

    tx = review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-review-report-current-1",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert tx["ordered_record_ids"] == ["report-current-1"]

    report["subject"]["normalized_paths"] = ["packs/core/forged-after-append.py"]
    current, code = review_persistence.select_current_review_report(
        store,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert current["report_id"] == "report-current-1"
    assert current["subject"] == subject

    current["subject"]["normalized_paths"] = ["packs/core/forged-after-read.py"]
    current_again, code = review_persistence.select_current_review_report(
        store,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert current_again["subject"] == subject

    reopened = _open_store(evidence_store, log_path)
    replayed, code = review_persistence.select_current_review_report(
        reopened,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert replayed["subject"] == subject

    forged_subject = {
        **subject,
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_evidence_store.py",
            "packs/core/forged-before-append.py",
        ],
    }
    forged = _report(forged_subject, report_id="report-forged-1")
    with pytest.raises(review_persistence.ReviewPersistenceRefused) as exc_info:
        review_persistence.append_current_review_report(
            store,
            forged,
            transaction_id="tx-review-report-forged-1",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-review-subject-mismatch"

    still_current, code = review_persistence.select_current_review_report(
        _open_store(evidence_store, log_path),
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert still_current["report_id"] == "report-current-1"


def test_plan_task_provenance_revision_keeps_same_current_report_tip(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Subject binding follows T2 identity, so provenance-only changes do not stale reports."""
    log_path = _store_path(tmp_path, "provenance-stays-current.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    review_persistence.append_current_review_report(
        store,
        _clean_report(subject, report_id="report-provenance-tip"),
        transaction_id="tx-report-provenance-tip",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    same_identity = review_selection.project_review_subject(
        _delivery_subject_with_task_revision("task-revision-plan-only"),
        changed_paths=_changed_paths(),
        review_policy_fingerprint="review-policy-v1",
        plan_digest="plan-digest-plan-only",
        task_projection_revision="task-revision-plan-only",
        adapter_event_id="adapter-event-plan-only",
    )
    assert same_identity == subject

    current, code = review_persistence.select_current_review_report(
        _open_store(evidence_store, log_path),
        role="quality-engineer",
        expected_subject=same_identity,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert current["report_id"] == "report-provenance-tip"


def test_refused_reports_write_no_semantic_record(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Malformed and unsafe reports refuse before a semantic record is stored."""
    log_path = _store_path(tmp_path, "refused.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    cases = [
        ("malformed", {**_clean_report(subject), "terminal_status": "blocked"}),
        ("unknown-major", {**_clean_report(subject), "schema_version": 2}),
        ("content-safety", _clean_report(subject)),
    ]
    cases[2][1]["lineage"]["producer"] = '{"_grant": "admin"}'

    for index, (_case, report) in enumerate(cases):
        before = log_path.read_bytes()
        with pytest.raises(review_persistence.ReviewPersistenceRefused):
            review_persistence.append_current_review_report(
                store,
                report,
                transaction_id=f"tx-refused-{index}",
                expected_subject=subject,
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        assert log_path.read_bytes() == before
        current, code = review_persistence.select_current_review_report(
            store,
            role="quality-engineer",
            expected_subject=subject,
            review_policy_fingerprint="review-policy-v1",
        )
        assert current is None
        assert code == "denied-no-current-report"


def test_prevalidation_refusal_uses_owned_exception_without_store_introspection(
    review_persistence: ModuleType,
) -> None:
    """Invalid prevalidation input refuses before depending on an EvidenceStore class."""
    with pytest.raises(review_persistence.ReviewPersistenceRefused) as exc_info:
        review_persistence.append_current_review_report(
            object(),
            {"schema_version": 2},
            transaction_id="tx-prevalidation-owned",
            expected_subject={"schema_version": 1},
            issuer=object(),
            grant=object(),
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-missing-required-field"


def test_stale_report_does_not_select_a_current_tip(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Current selection ignores reports bound to a stale subject."""
    log_path = _store_path(tmp_path, "lineage.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    stale_subject = {
        **subject,
        "review_subject_fingerprint": "review-subject-sha256:stale",
    }
    store.append_semantic_records(
        [_clean_report(stale_subject, report_id="report-stale-1")],
        transaction_id="tx-stale-1",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    current, code = review_persistence.select_current_review_report(
        store,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert current is None
    assert code == "denied-no-current-report"


def test_raw_replayed_forked_reports_do_not_select_a_current_tip(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    tmp_path: Path,
) -> None:
    """Reader selection rejects schema-valid forked reports found on replay."""
    log_path = _store_path(tmp_path, "lineage-fork-replay.log")
    _open_store(evidence_store, log_path)
    subject = _review_subject(review_selection)
    _append_review_frame(
        evidence_store,
        log_path,
        _clean_report(subject, report_id="report-fork-a", sequence=1),
        tx_id="tx-fork-a",
        acceptance_fingerprint="acceptance-current",
    )
    _append_review_frame(
        evidence_store,
        log_path,
        _clean_report(subject, report_id="report-fork-b", sequence=1),
        tx_id="tx-fork-b",
        acceptance_fingerprint="acceptance-current",
    )
    store = _open_store(evidence_store, log_path)
    current, code = review_persistence.select_current_review_report(
        store,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert current is None
    assert code == "denied-duplicate-report-sequence"


def test_duplicate_report_identity_is_refused_and_paired_after_allow(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A conflicting report id refuses without replacing the first record."""
    log_path = _store_path(tmp_path, "duplicate.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    review_persistence.append_current_review_report(
        store,
        _clean_report(subject, report_id="report-duplicate"),
        transaction_id="tx-duplicate-first",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    events: list = []
    changed = _clean_report(subject, report_id="report-duplicate")
    changed["lineage"]["source_event_id"] = "source-changed"
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_persistence.append_current_review_report(
            store,
            changed,
            transaction_id="tx-duplicate-second",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=events.append,
        )
    assert exc_info.value.denial_code == "denied-duplicate-review-record-id"
    allow, denial = events
    assert (allow.outcome, denial.outcome) == ("allowed", "denied")
    assert denial.operation_id == allow.operation_id
    assert denial.reason_code == "denied-duplicate-review-record-id"


def test_crash_recovery_replays_only_complete_validated_review_frames(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    tmp_path: Path,
) -> None:
    """A torn review frame is truncated and does not create a report."""
    log_path = _store_path(tmp_path, "crash.log")
    _open_store(evidence_store, log_path)
    subject = _review_subject(review_selection)
    log_path.write_bytes(log_path.read_bytes() + b'{"tx": {"partial": true}')
    reopened = _open_store(evidence_store, log_path)
    current, code = review_persistence.select_current_review_report(
        reopened,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert current is None
    assert code == "denied-no-current-report"
    assert log_path.read_bytes() == b""


def test_replay_refuses_malformed_review_record_without_raw_exception(
    evidence_store: ModuleType,
    review_selection: ModuleType,
    tmp_path: Path,
) -> None:
    """Replay validates review records instead of trusting a recomputed checksum."""
    log_path = _store_path(tmp_path, "malformed-replay.log")
    _open_store(evidence_store, log_path)
    subject = _review_subject(review_selection)
    malformed = {**_clean_report(subject), "lineage": {"sequence": True}}
    _append_review_frame(
        evidence_store,
        log_path,
        malformed,
        tx_id="tx-malformed-replay",
        acceptance_fingerprint="acceptance-current",
    )
    with pytest.raises(evidence_store.EvidenceStoreError, match="record is invalid"):
        evidence_store.EvidenceStore(log_path).open()


def test_unknown_semantic_kind_refuses_and_legacy_batch_records_replay(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """The batch port is closed while receipt and supersession records stay compatible."""
    log_path = _store_path(tmp_path, "batch-compat.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["append"])
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [{"schema_version": 1, "unknown_id": "unknown-1"}],
            transaction_id="tx-unknown-kind",
            acceptance_fingerprint="acceptance-current",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == (
        "denied-invalid-semantic-record-denied-unknown-record-kind"
    )

    receipt = _receipt()
    supersession = _supersession()
    tx = store.append_semantic_records(
        [receipt, supersession],
        transaction_id="tx-batch-compat",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert tx["ordered_record_ids"] == ["receipt-batch-1", "supersession-batch-1"]
    reopened = _open_store(evidence_store, log_path)
    assert reopened.get_all_active_receipts() == []


def test_all_six_review_record_families_round_trip_through_batch_port(
    evidence_store: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """The closed registry admits every T1 review family without collisions.

    Dispositions are now routed through the typed write port; raw batches containing
    finding-disposition records are refused by design (denied-disposition-authority-required).
    """
    # Load the T5 disposition port inline for this fixture.
    review_bridge = _load_module(
        "review_bridge_t3_allfamily", SCRIPTS / "_review_bridge.py"
    )
    review_disposition = _load_module(
        "review_disposition_t3_allfamily", SCRIPTS / "_review_disposition.py"
    )

    log_path = _store_path(tmp_path, "all-review-families.log")
    store = _open_store(evidence_store, log_path)
    issuer, evidence_grant = _make_grant(security_capability)
    # Disposition lifecycle requires a "review"-scoped grant.
    review_grant = issuer.issue_root_grant(
        roots=["review"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["review"],
        control_denies=[],
    )

    subject = _review_subject(review_selection)
    report = _report(subject)
    source_records = [
        subject,
        _obligation(subject),
        report,
        report["findings"][0],
    ]

    tx = store.append_semantic_records(
        source_records,
        transaction_id="tx-all-review-families-source",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=evidence_grant,
        audit_sink=_null_sink,
    )
    assert tx["ordered_record_ids"] == [
        subject["review_subject_id"],
        "obligation-quality-1",
        report["report_id"],
        "finding-review-persistence-1",
    ]

    # Append the assessment via the bridge lifecycle (routes receipts correctly).
    assessment = _assessment(subject, report["report_id"])
    review_bridge.append_finding_assessment_bridge(
        store,
        assessment,
        report_id=report["report_id"],
        finding=report["findings"][0],
        affected_criteria=report["findings"][0]["affected_acceptance_criteria"],
        transaction_id="tx-all-review-families-assessment",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=evidence_grant,
        audit_sink=_null_sink,
    )

    # Dispositions are refused by design on the raw batch path.
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_disposition(subject)],
            transaction_id="tx-raw-disposition-attempt",
            acceptance_fingerprint="acceptance-current",
            issuer=issuer,
            grant=evidence_grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-disposition-authority-required"

    # Route dispositions through the typed write port with a review grant.
    approval = {
        "schema_version": 1,
        "approval_id": "authority-1",
        "authority": {"identity": "review-owner", "role": "risk-owner"},
        "decision_scope": "review-disposition",
        "base": {"manifest_ref": subject["review_subject_fingerprint"]},
        "lineage": {"spec_ref": "docs/specs/structured-review-boundary/spec.md"},
        "spec_policy_fingerprint": subject["review_policy_fingerprint"],
        "decision": "approved",
        "timestamp": "2026-10-09T00:00:00Z",
    }
    review_disposition.append_finding_disposition(
        store,
        _disposition(subject),
        approval_record=approval,
        current_subject=subject,
        transaction_id="tx-all-review-families-disposition",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=review_grant,
        audit_sink=_null_sink,
    )

    reopened = _open_store(evidence_store, log_path)
    assert [
        item["assessment_id"]
        for item in reopened.get_semantic_records("finding-assessment.v1")
    ] == ["assessment-quality-1"]
    assert [
        item["disposition_id"]
        for item in reopened.get_semantic_records("finding-disposition.v1")
    ] == ["disposition-quality-1"]


def test_batch_supersession_matches_append_only_legacy_authority(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A batch containing a supersession keeps S1's append-only authority contract."""
    log_path = _store_path(tmp_path, "batch-append-authority.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["append"])
    tx = store.append_semantic_records(
        [_receipt(), _supersession()],
        transaction_id="tx-batch-append-only",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert tx["ordered_record_ids"] == ["receipt-batch-1", "supersession-batch-1"]
    assert _open_store(evidence_store, log_path).get_all_active_receipts() == []


def test_batch_preserves_typed_namespaces_for_same_opaque_id(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Batch records may share an opaque id when their semantic kinds differ."""
    log_path = _store_path(tmp_path, "batch-same-opaque-id.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["append"])
    tx = store.append_semantic_records(
        [_receipt("same-opaque-id"), _supersession("same-opaque-id", ["same-opaque-id"])],
        transaction_id="tx-batch-same-opaque-id",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert tx["ordered_record_ids"] == ["same-opaque-id", "same-opaque-id"]
    reopened = _open_store(evidence_store, log_path)
    assert reopened.receipt_count == 1
    assert reopened.supersession_count == 1
    assert reopened.get_all_active_receipts() == []


def test_same_opaque_id_different_typed_body_is_not_false_retry(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Idempotency compares the typed record body, not just the ordered opaque id."""
    log_path = _store_path(tmp_path, "same-opaque-id-false-retry.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["append"])
    store.append_receipt(
        _receipt("same-opaque-id"),
        transaction_id="tx-same-opaque-receipt",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    store.append_supersession(
        _supersession("same-opaque-id", ["same-opaque-id"]),
        transaction_id="tx-same-opaque-supersession",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_supersession("same-opaque-id", ["same-opaque-id"])],
            transaction_id="tx-same-opaque-receipt",
            acceptance_fingerprint="acceptance-current",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


def test_batch_supersession_without_append_authority_denies_with_zero_effect(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A batch containing a supersession denies when the S1 append grant is missing."""
    log_path = _store_path(tmp_path, "batch-missing-append-authority.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["read"])
    events: list = []
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_receipt(), _supersession()],
            transaction_id="tx-batch-missing-append",
            acceptance_fingerprint="acceptance-current",
            issuer=issuer,
            grant=grant,
            audit_sink=events.append,
        )
    assert exc_info.value.denial_code == "denied-producer-authority"
    assert log_path.read_bytes() == b""
    assert len(events) == 1
    assert events[0].outcome == "denied"
    assert events[0].reason_code == "denied-missing-operation"


def test_old_single_record_ports_keep_typed_identity_namespaces(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Receipt and supersession IDs are separate typed namespaces in S1 APIs."""
    log_path = _store_path(tmp_path, "typed-id-namespaces.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["append", "supersede"])
    store.append_receipt(
        _receipt("same-opaque-id"),
        transaction_id="tx-same-id-receipt",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    store.append_supersession(
        _supersession("same-opaque-id", ["same-opaque-id"]),
        transaction_id="tx-same-id-supersession",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    reopened = _open_store(evidence_store, log_path)
    assert reopened.get_all_active_receipts() == []
    again = store.append_receipt(
        _receipt("same-opaque-id"),
        transaction_id="tx-same-id-receipt",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert again["transaction_id"] == "tx-same-id-receipt"


@pytest.mark.parametrize("bad_marker", ["supersession_id", "report_id", "assessment_id"])
def test_old_receipt_with_extra_identity_marker_keeps_stable_denial(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    bad_marker: str,
) -> None:
    """Malformed old receipts keep S1-style validation codes."""
    log_path = _store_path(tmp_path, f"receipt-extra-{bad_marker}.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    bad = {**_receipt("receipt-extra-marker"), bad_marker: "extra-id"}
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_receipt(
            bad,
            transaction_id=f"tx-receipt-extra-{bad_marker}",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == (
        "denied-invalid-receipt-denied-unknown-authority-field"
    )


def test_review_port_issues_sequence_and_rejects_wrong_policy_lineage(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """The report port owns current sequence and policy binding."""
    log_path = _store_path(tmp_path, "port-sequence.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    first = _clean_report(subject, report_id="report-seq-1")
    first["lineage"]["sequence"] = 99
    first.pop("previous_report_id", None)
    tx1 = review_persistence.append_current_review_report(
        store,
        first,
        transaction_id="tx-report-seq-1",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert tx1["ordered_record_ids"] == ["report-seq-1"]
    second = _clean_report(subject, report_id="report-seq-2", sequence=99)
    review_persistence.append_current_review_report(
        store,
        second,
        transaction_id="tx-report-seq-2",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    current, code = review_persistence.select_current_review_report(
        store,
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert current["report_id"] == "report-seq-2"
    assert current["lineage"]["sequence"] == 2
    assert current["lineage"]["previous_report_id"] == "report-seq-1"

    wrong_policy = _clean_report(subject, report_id="report-wrong-policy")
    wrong_policy["lineage"]["review_policy_fingerprint"] = "review-policy-other"
    with pytest.raises(review_persistence.ReviewPersistenceRefused) as exc_info:
        review_persistence.append_current_review_report(
            store,
            wrong_policy,
            transaction_id="tx-report-wrong-policy",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-review-policy-mismatch"


def test_two_open_stores_cannot_create_report_sequence_fork(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A stale open store must re-read before assigning the next report sequence."""
    log_path = _store_path(tmp_path, "two-open-sequence.log")
    first_store = _open_store(evidence_store, log_path)
    second_store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    review_persistence.append_current_review_report(
        first_store,
        _clean_report(subject, report_id="report-race-1"),
        transaction_id="tx-report-race-1",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    review_persistence.append_current_review_report(
        second_store,
        _clean_report(subject, report_id="report-race-2"),
        transaction_id="tx-report-race-2",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    current, code = review_persistence.select_current_review_report(
        _open_store(evidence_store, log_path),
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert current["report_id"] == "report-race-2"
    assert current["lineage"]["sequence"] == 2


def test_concurrent_open_stores_assign_distinct_report_sequences(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Actual concurrent appends serialize under the EvidenceStore append lock."""
    if not getattr(evidence_store, "_HAS_FCNTL", False):
        pytest.skip("fcntl not available; lock serialization is platform-specific")
    log_path = _store_path(tmp_path, "threaded-report-sequence.log")
    _open_store(evidence_store, log_path)
    subject = _review_subject(review_selection)
    barrier = threading.Barrier(2)
    results: list[tuple[str, str]] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def append_report(report_id: str) -> None:
        """Persist a report from a separate store after both workers are ready."""
        try:
            store = _open_store(evidence_store, log_path)
            issuer, grant = _make_grant(security_capability)
            barrier.wait(timeout=5)
            tx = review_persistence.append_current_review_report(
                store,
                _clean_report(subject, report_id=report_id),
                transaction_id=f"tx-{report_id}",
                expected_subject=subject,
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
            with lock:
                results.append((report_id, tx["transaction_id"]))
        except BaseException as exc:  # noqa: BLE001 - thread reports any failure to the test
            with lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=append_report, args=("report-thread-a",)),
        threading.Thread(target=append_report, args=("report-thread-b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in threads)
    assert not errors
    assert sorted(results) == [
        ("report-thread-a", "tx-report-thread-a"),
        ("report-thread-b", "tx-report-thread-b"),
    ]
    reopened = _open_store(evidence_store, log_path)
    reports = sorted(
        reopened.get_semantic_records("review-report.v1"),
        key=lambda item: item["lineage"]["sequence"],
    )
    assert [report["lineage"]["sequence"] for report in reports] == [1, 2]
    assert reports[1]["lineage"]["previous_report_id"] == reports[0]["report_id"]


def test_report_retry_matches_normalized_stored_sequence(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Retrying the same original report returns the normalized committed transaction."""
    log_path = _store_path(tmp_path, "report-retry-normalized.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    original = _clean_report(subject, report_id="report-retry-normalized")
    original["lineage"]["sequence"] = 99
    first = review_persistence.append_current_review_report(
        store,
        original,
        transaction_id="tx-report-retry-normalized",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    events: list = []
    again = review_persistence.append_current_review_report(
        store,
        original,
        transaction_id="tx-report-retry-normalized",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=events.append,
    )
    assert again == first
    assert [event.outcome for event in events] == ["allowed"]
    current, code = review_persistence.select_current_review_report(
        _open_store(evidence_store, log_path),
        role="quality-engineer",
        expected_subject=subject,
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert current["lineage"]["sequence"] == 1


def test_reused_transaction_id_with_different_record_body_is_not_idempotent(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Transaction retry identity is bound to the exact associated record body."""
    log_path = _store_path(tmp_path, "retry-associated-body.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    review_persistence.append_current_review_report(
        store,
        _clean_report(subject, report_id="report-associated-a"),
        transaction_id="tx-associated-body",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    changed = _clean_report(subject, report_id="report-associated-b")
    review_persistence.append_current_review_report(
        store,
        changed,
        transaction_id="tx-associated-body-b",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_persistence.append_current_review_report(
            store,
            changed,
            transaction_id="tx-associated-body",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


def test_batch_with_two_new_reports_for_same_group_refuses_ambiguous_sequence(
    evidence_store: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A single batch cannot introduce two reports that need the same next sequence."""
    log_path = _store_path(tmp_path, "batch-ambiguous-report-sequence.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                _clean_report(subject, report_id="report-batch-a"),
                _clean_report(subject, report_id="report-batch-b"),
            ],
            transaction_id="tx-batch-ambiguous-report-sequence",
            acceptance_fingerprint="acceptance-current",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-ambiguous-review-report-batch"


@pytest.mark.parametrize(
    ("case", "mutate", "expected_code"),
    [
        (
            "free-text",
            lambda report: report["lineage"].__setitem__("producer", "x" * (64 * 1024 + 1)),
            "denied-free-text-field-too-large",
        ),
        (
            "whole-report",
            lambda report: (
                report.__setitem__("terminal_status", "findings"),
                report.__setitem__(
                    "findings",
                    [
                        {
                            **_finding(),
                            "finding_id": f"finding-oversized-{index}",
                            "observation": "bounded inert observation",
                        }
                        for index in range(18000)
                    ],
                ),
            ),
            "denied-content-safety-rejected-size",
        ),
        (
            "privacy",
            lambda report: report["lineage"].__setitem__(
                "producer", "contact generic@example.com"
            ),
            "denied-content-safety-rejected-personal-data",
        ),
        (
            "control",
            lambda report: report["lineage"].__setitem__("producer", "bad\x01text"),
            "denied-content-safety-rejected-encoding",
        ),
    ],
    ids=["free-text", "whole-report", "privacy", "control"],
)
def test_review_report_content_safety_boundaries_are_enforced_before_persist(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    case: str,
    mutate: object,
    expected_code: str,
) -> None:
    """Review reports hit the T1 content-safety profile before bytes persist."""
    log_path = _store_path(tmp_path, f"content-{case}.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    report = _clean_report(subject)
    mutate(report)
    if case == "whole-report":
        encoded_fields = [
            str(finding["observation"]).encode("utf-8") for finding in report["findings"]
        ]
        assert encoded_fields
        assert all(len(item) < 64 * 1024 for item in encoded_fields)
        canonical = review_persistence._canonical_json(report).encode("utf-8")
        assert len(canonical) > 1024 * 1024
    before = log_path.read_bytes()
    with pytest.raises(review_persistence.ReviewPersistenceRefused) as exc_info:
        review_persistence.append_current_review_report(
            store,
            report,
            transaction_id=f"tx-content-{case}",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == expected_code
    assert log_path.read_bytes() == before


@pytest.mark.parametrize("record_type", [[], {}], ids=["list", "dict"])
def test_get_semantic_records_refuses_malformed_record_type(
    evidence_store: ModuleType,
    tmp_path: Path,
    record_type: object,
) -> None:
    """The reader refuses malformed type selectors with a stable code."""
    store = _open_store(evidence_store, _store_path(tmp_path, "bad-record-type.log"))
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.get_semantic_records(record_type)
    assert exc_info.value.denial_code == "denied-unknown-record-kind"


def test_transaction_return_and_batch_inputs_are_isolated_from_callers(
    evidence_store: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Batch append snapshots inputs and returned transactions."""
    log_path = _store_path(tmp_path, "alias-isolation.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _review_subject(review_selection)
    report = _clean_report(subject, report_id="report-alias")
    original = copy.deepcopy(report)
    tx = store.append_semantic_records(
        [report],
        transaction_id="tx-alias",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    report["lineage"]["producer"] = "mutated-after-append"
    tx["ordered_record_ids"] = ["mutated-after-return"]
    assert store.get_semantic_records("review-report.v1")[0]["lineage"]["producer"] == (
        "synthetic-reviewer"
    )
    retry = store.append_semantic_records(
        [original],
        transaction_id="tx-alias",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert retry["ordered_record_ids"] == ["report-alias"]
    reopened = _open_store(evidence_store, log_path)
    records = reopened.get_semantic_records("review-report.v1")
    assert records[0]["lineage"]["producer"] == "synthetic-reviewer"
    assert reopened._transactions[0]["ordered_record_ids"] == ["report-alias"]


def test_incomplete_multi_record_frame_preserves_complete_prefix(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Recovery keeps a complete batch prefix and truncates only the torn suffix."""
    log_path = _store_path(tmp_path, "multi-record-crash.log")
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability, operations=["append", "supersede"])
    store.append_semantic_records(
        [_receipt(), _supersession()],
        transaction_id="tx-complete-batch-prefix",
        acceptance_fingerprint="acceptance-current",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    log_path.write_bytes(log_path.read_bytes() + b'{"tx": {"partial": true}')
    reopened = _open_store(evidence_store, log_path)
    assert reopened.transaction_count == 1
    assert reopened.receipt_count == 1
    assert reopened.supersession_count == 1
    assert reopened.get_all_active_receipts() == []
    assert [item["receipt_id"] for item in reopened.get_semantic_records("evidence-receipt.v1")] == [
        "receipt-batch-1"
    ]
    assert [
        item["supersession_id"]
        for item in reopened.get_semantic_records("evidence-supersession.v1")
    ] == ["supersession-batch-1"]
    assert log_path.read_bytes().endswith(b"\n")
