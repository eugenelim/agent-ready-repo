"""T4 construction tests for the assessment-to-evidence bridge.

Mode: TDD (structured-review-boundary plan T4).

The suite names the atomic bridge boundary before runtime bridge or
EvidenceStore repair work begins. The bridge must use T3 semantic batches, keep
Slice 1 receipt semantics, and rebuild views from the authoritative log.
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
        pytest.fail(f"T4 review bridge module is not implemented: {path.name}")
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
def review_bridge() -> ModuleType:
    """Load the T4 review-to-evidence bridge."""
    return _load_module("review_bridge_under_test", SCRIPTS / "_review_bridge.py")


@pytest.fixture(scope="module")
def evidence_store() -> ModuleType:
    """Load the Slice 1 evidence store."""
    return _load_module("evidence_store_t4_bridge", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    """Load the Slice 1 capability issuer."""
    return _load_module("security_capability_t4_bridge", SCRIPTS / "_security_capability.py")


@pytest.fixture(scope="module")
def review_persistence() -> ModuleType:
    """Load the T3 review report persistence boundary."""
    return _load_module("review_persistence_t4_bridge", SCRIPTS / "_review_persistence.py")


@pytest.fixture(scope="module")
def acceptance() -> ModuleType:
    """Load the Slice 1 acceptance evaluator."""
    return _load_module("acceptance_t4_bridge", SCRIPTS / "_acceptance.py")


def _null_sink(event: object) -> None:
    """Accept security events without persisting them in the test."""


def _make_grant(security_capability: ModuleType) -> tuple[object, object]:
    """Return a valid producer authority pair for semantic appends."""
    issuer = security_capability.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


def _store_path(tmp_path: Path) -> Path:
    """Return a semantic evidence log under a fake git root."""
    log_path = tmp_path / "repo" / ".work-loop" / "semantic-evidence.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def _open_store(evidence_store: ModuleType, log_path: Path) -> object:
    """Open a fresh EvidenceStore under a fake git root."""
    store = evidence_store.EvidenceStore(log_path)
    store.open()
    return store


def _subject() -> dict:
    """Build a review subject for bridge tests."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-t4-bridge",
        "review_subject_fingerprint": "review-subject-fp-t4-bridge",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-t4-bridge",
            "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        },
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_bridge.py"
        ],
        "normalized_statuses": ["added"],
        "review_policy_fingerprint": "review-policy-t4-current",
        "lineage": {"provider": "structured-review-boundary-test", "projection_version": "1.0"},
    }


def _finding() -> dict:
    """Build a supported finding."""
    return {
        "schema_version": 1,
        "finding_id": "finding-t4-bridge",
        "rule_ref": "AC-0014",
        "observation": "A supported assessment must reach acceptance evidence.",
        "reachable_path": "assessment bridge to criterion receipt",
        "actual_failure": "The affected criterion has a current supported review failure.",
        "affected_acceptance_criteria": ["AC-0014", "AC-0015"],
        "evidence_refs": ["evidence:observation", "evidence:reachable-path"],
        "material": True,
    }


def _report(subject: dict, finding: dict) -> dict:
    """Build a current findings report."""
    return {
        "schema_version": 1,
        "report_id": "report-t4-bridge",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": "review-policy-t4-current",
            "source_event_id": "source-report-t4-bridge",
            "producer": "synthetic-reviewer",
        },
        "findings": [copy.deepcopy(finding)],
    }


def _assessment(subject: dict) -> dict:
    """Build a supported finding assessment."""
    return {
        "schema_version": 1,
        "assessment_id": "assessment-t4-bridge-supported",
        "finding_id": "finding-t4-bridge",
        "report_id": "report-t4-bridge",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": ["evidence:observation", "evidence:reachable-path"],
        "lineage": {"predicate_version": "slice2-t4-v1"},
    }


def _new_subject() -> dict:
    """Build a replacement review subject with a different fingerprint but same delivery id."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-t4-new",
        "review_subject_fingerprint": "review-subject-fp-t4-new",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-t4-bridge",
            "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        },
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_bridge.py"
        ],
        "normalized_statuses": ["modified"],
        "review_policy_fingerprint": "review-policy-t4-new",
        "lineage": {"provider": "structured-review-boundary-test", "projection_version": "1.1"},
    }


def _property(criterion_ref: str) -> dict:
    """Build an approved property contradicted by supported review failures."""
    return {
        "schema_version": 1,
        "property_id": criterion_ref,
        "spec_ref": "docs/specs/structured-review-boundary/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {
            "paths_or_artifacts": ["packs/core/"],
            "fingerprint_algorithm": "sha256",
        },
        "required_observations": [
            {
                "term": "test-run",
                "observation_type": "test-result",
                "producer_class": "ci-runner",
                "outcomes": ["passed"],
            }
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": "supported-review-failure"},
        "policy_version": "v1",
    }


def test_supported_assessment_commits_complete_receipts_and_replays_projection(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    acceptance: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """One bridge frame contains the assessment and every criterion receipt."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    assessment = _assessment(subject)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-bridge-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    tx = review_bridge.append_finding_assessment_bridge(
        store,
        assessment,
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-bridge-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert tx["ordered_record_ids"][0] == "assessment-t4-bridge-supported"
    receipt_ids = tx["ordered_record_ids"][1:]
    assert len(receipt_ids) == 2
    assert len(set(receipt_ids)) == 2
    receipts = store.get_all_active_receipts()
    assert [receipt["receipt_id"] for receipt in receipts] == receipt_ids
    assert [receipt["lineage"]["criterion_ref"] for receipt in receipts] == [
        "AC-0014",
        "AC-0015",
    ]
    assert {receipt["acceptance_fingerprint"] for receipt in receipts} == {
        "acceptance-fp-t4-bridge"
    }
    assert {receipt["freshness_mode"] for receipt in receipts} == {"exact-subject"}
    assert {receipt["selector"]["term"] for receipt in receipts} == {
        "supported-review-failure"
    }
    assert {receipt["observation"]["type"] for receipt in receipts} == {
        "review-failure"
    }
    assert {receipt["outcome"] for receipt in receipts} == {"review-failure"}
    assert {receipt["producer"]["class"] for receipt in receipts} == {"review-bridge"}

    reopened = _open_store(evidence_store, log_path)
    assert [receipt["receipt_id"] for receipt in reopened.get_all_active_receipts()] == (
        receipt_ids
    )
    current = review_bridge.select_current_finding_assessments(
        reopened,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )
    assert current == {
        ("report-t4-bridge", "finding-t4-bridge"): {
            "assessment": assessment,
            "receipt_ids": receipt_ids,
        }
    }
    verdict = acceptance.evaluate_verdict(
        property_record=_property("AC-0014"),
        receipts=reopened.get_active_receipts("AC-0014"),
        current_acceptance_fingerprint="acceptance-fp-t4-bridge",
        adapter="sequential-reference",
    )
    assert verdict["verdict"] == "contradicted"


def test_bridge_receipt_identity_includes_acceptance_fingerprint(
    review_bridge: ModuleType,
) -> None:
    """Bridge-owned receipt IDs are stable and avoid cross-acceptance aliases."""
    first = review_bridge.derive_review_failure_receipt_id(
        report_id="report-t4-bridge",
        finding_id="finding-t4-bridge",
        assessment_id="assessment-t4-bridge-supported",
        criterion_ref="AC-0014",
        acceptance_fingerprint="acceptance-fp-a",
    )
    repeat = review_bridge.derive_review_failure_receipt_id(
        report_id="report-t4-bridge",
        finding_id="finding-t4-bridge",
        assessment_id="assessment-t4-bridge-supported",
        criterion_ref="AC-0014",
        acceptance_fingerprint="acceptance-fp-a",
    )
    other_acceptance = review_bridge.derive_review_failure_receipt_id(
        report_id="report-t4-bridge",
        finding_id="finding-t4-bridge",
        assessment_id="assessment-t4-bridge-supported",
        criterion_ref="AC-0014",
        acceptance_fingerprint="acceptance-fp-b",
    )

    assert first == repeat
    assert first != other_acceptance


def test_incomplete_raw_assessment_batch_refuses_before_visibility(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Central batch validation rejects assessment frames without receipts."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_assessment(subject)],
            transaction_id="tx-t4-incomplete-raw-assessment",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"
    assert store.get_semantic_records("finding-assessment.v1") == []


def test_supported_to_unsupported_replacement_supersedes_all_derived_receipts(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A non-supported replacement retires every bridge-owned receipt."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-replacement-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    review_bridge.append_finding_assessment_bridge(
        store,
        _assessment(subject),
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-replacement-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    unsupported = _assessment(subject)
    unsupported["assessment_id"] = "assessment-t4-bridge-unsupported"
    unsupported["assessment"] = "unsupported-opinion"

    review_bridge.append_finding_assessment_bridge(
        store,
        unsupported,
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-replacement-unsupported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert store.get_all_active_receipts() == []
    current = review_bridge.select_current_finding_assessments(
        store,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )
    assert current[("report-t4-bridge", "finding-t4-bridge")]["assessment"] == unsupported
    assert current[("report-t4-bridge", "finding-t4-bridge")]["receipt_ids"] == []


def test_explicit_old_source_invalidation_supersedes_receipts(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Explicit report or subject invalidation retires old-source receipts."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-invalidation-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    review_bridge.append_finding_assessment_bridge(
        store,
        _assessment(subject),
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-invalidation-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    review_bridge.append_finding_assessment_replacement(
        store,
        old_report_id=report["report_id"],
        old_finding_id=finding["finding_id"],
        new_assessment=None,
        current_subject=_new_subject(),
        transaction_id="tx-t4-invalidation-old-source",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert store.get_all_active_receipts() == []


def test_unpaired_bridge_owned_receipt_records_refuse_even_without_assessment(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Raw bridge-owned receipts cannot bypass the assessment lifecycle."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    receipt_id = review_bridge.derive_review_failure_receipt_id(
        report_id="report-t4-bridge",
        finding_id="finding-t4-bridge",
        assessment_id="assessment-t4-bridge-supported",
        criterion_ref="AC-0014",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
    )

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                {
                    "schema_version": 1,
                    "receipt_id": receipt_id,
                    "acceptance_fingerprint": "acceptance-fp-t4-bridge",
                    "lineage": {"criterion_ref": "AC-0014"},
                    "selector": {"term": "supported-review-failure"},
                    "freshness_mode": "exact-subject",
                    "observation": {"type": "review-failure"},
                    "outcome": "review-failure",
                    "producer": {
                        "class": "review-bridge",
                        "identity": "structured-review-boundary",
                    },
                }
            ],
            transaction_id="tx-t4-unpaired-bridge-receipt",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_malformed_assessment_inputs_refuse_with_bridge_exception(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Bridge prevalidation owns malformed inputs before store internals run."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    malformed = {"schema_version": 1, "assessment": "supported"}

    with pytest.raises(review_bridge.ReviewBridgeRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            malformed,
            report_id="report-t4-bridge",
            finding=_finding(),
            affected_criteria=["AC-0014"],
            transaction_id="tx-t4-malformed-assessment",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-invalid-finding-assessment"


def test_supported_assessment_for_stale_report_tip_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A supported assessment cannot bind an old same-group report tip."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    old_report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        old_report,
        transaction_id="tx-t4-stale-tip-old-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    new_report = _report(subject, finding)
    new_report["report_id"] = "report-t4-bridge-new-tip"
    review_persistence.append_current_review_report(
        store,
        new_report,
        transaction_id="tx-t4-stale-tip-new-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    with pytest.raises(review_bridge.ReviewBridgeRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            _assessment(subject),
            report_id=old_report["report_id"],
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id="tx-t4-stale-tip-assessment",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-stale-source-report"


def test_raw_report_replacement_must_supersede_source_receipts_same_frame(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A report replacement cannot leave old-source bridge receipts live."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-raw-replacement-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    review_bridge.append_finding_assessment_bridge(
        store,
        _assessment(subject),
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-raw-replacement-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    replacement = _report(subject, finding)
    replacement["report_id"] = "report-t4-bridge-replacement"

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [replacement],
            transaction_id="tx-t4-raw-report-replacement",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_single_record_supersession_cannot_clear_bridge_failure_without_lifecycle(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Bridge-owned failures retire only with source lifecycle context."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-single-sup-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    tx = review_bridge.append_finding_assessment_bridge(
        store,
        _assessment(subject),
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-single-sup-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-t4-single-record",
                    "superseded_receipt_ids": tx["ordered_record_ids"][1:],
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                }
            ],
            transaction_id="tx-t4-single-supersession",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_current_projection_keys_report_and_finding_to_avoid_role_collisions(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Two current reports with the same finding ID do not collide in projection."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    first = _report(subject, finding)
    second = _report(subject, finding)
    second["report_id"] = "report-t4-bridge-second-role"
    second["role"] = "adversarial-reviewer"
    for report in (first, second):
        review_persistence.append_current_review_report(
            store,
            report,
            transaction_id=f"tx-t4-projection-{report['report_id']}",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
        assessment = _assessment(subject)
        assessment["assessment_id"] = f"assessment-{report['report_id']}"
        assessment["report_id"] = report["report_id"]
        review_bridge.append_finding_assessment_bridge(
            store,
            assessment,
            report_id=report["report_id"],
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id=f"tx-t4-projection-assessment-{report['report_id']}",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

    current = review_bridge.select_current_finding_assessments(
        store,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )

    assert set(current) == {
        ("report-t4-bridge", "finding-t4-bridge"),
        ("report-t4-bridge-second-role", "finding-t4-bridge"),
    }


def test_replacement_retry_reuses_identical_supersession_body(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """An idempotent replacement retry does not recompute a different body."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-retry-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    review_bridge.append_finding_assessment_bridge(
        store,
        _assessment(subject),
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-retry-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    unsupported = _assessment(subject)
    unsupported["assessment_id"] = "assessment-t4-retry-unsupported"
    unsupported["assessment"] = "indeterminate"
    first = review_bridge.append_finding_assessment_bridge(
        store,
        unsupported,
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-retry-replacement",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    retry = review_bridge.append_finding_assessment_bridge(
        store,
        unsupported,
        report_id=report["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-retry-replacement",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert retry == first


def _append_supported_bridge_case(
    review_bridge: ModuleType,
    review_persistence: ModuleType,
    store: object,
    issuer: object,
    grant: object,
    subject: dict,
    finding: dict,
    *,
    report_id: str = "report-t4-bridge",
    tx_prefix: str = "case",
) -> dict:
    """Persist one current source report and supported bridge assessment."""
    report = _report(subject, finding)
    report["report_id"] = report_id
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id=f"tx-t4-{tx_prefix}-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assessment = _assessment(subject)
    assessment["report_id"] = report_id
    assessment["assessment_id"] = f"assessment-t4-{tx_prefix}-supported"
    return review_bridge.append_finding_assessment_bridge(
        store,
        assessment,
        report_id=report_id,
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id=f"tx-t4-{tx_prefix}-supported",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )


def test_explicit_invalidation_removes_current_projection_after_reopen(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Explicit invalidation removes old supported assessment eligibility."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="projection-invalidation",
    )
    review_bridge.append_finding_assessment_replacement(
        store,
        old_report_id="report-t4-bridge",
        old_finding_id="finding-t4-bridge",
        new_assessment=None,
        current_subject=_new_subject(),
        transaction_id="tx-t4-projection-invalidation",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    reopened = _open_store(evidence_store, log_path)
    current = review_bridge.select_current_finding_assessments(
        reopened,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )

    assert ("report-t4-bridge", "finding-t4-bridge") not in current
    assert all(
        item["assessment"]["report_id"] != "report-t4-bridge"
        for item in current.values()
    )
    assert reopened.get_all_active_receipts() == []


def test_current_projection_excludes_replaced_report_tip(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A replaced report tip is absent from current assessment projection."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        report_id="report-t4-old-tip", tx_prefix="old-tip",
    )
    replacement = _report(subject, finding)
    replacement["report_id"] = "report-t4-new-tip"
    # The typed report port now composes the supersession of old-tip receipts under lock.
    review_persistence.append_current_review_report(
        store,
        replacement,
        transaction_id="tx-t4-new-tip-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    current = review_bridge.select_current_finding_assessments(
        store,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )

    assert ("report-t4-old-tip", "finding-t4-bridge") not in current
    assert all(
        item["assessment"]["report_id"] != "report-t4-old-tip"
        for item in current.values()
    )
    reopened = _open_store(evidence_store, log_path)
    assert reopened.get_all_active_receipts() == []


def test_new_subject_invalidation_preserves_unrelated_role_receipts(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Invalidating one old source keeps unrelated role receipt sets active."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        report_id="report-t4-old-subject", tx_prefix="old-subject",
    )
    other = _report(subject, finding)
    other["report_id"] = "report-t4-other-role"
    other["role"] = "adversarial-reviewer"
    review_persistence.append_current_review_report(
        store,
        other,
        transaction_id="tx-t4-other-role-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    other_assessment = _assessment(subject)
    other_assessment["assessment_id"] = "assessment-t4-other-role"
    other_assessment["report_id"] = other["report_id"]
    review_bridge.append_finding_assessment_bridge(
        store,
        other_assessment,
        report_id=other["report_id"],
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-other-role-assessment",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    before = {receipt["receipt_id"] for receipt in store.get_all_active_receipts()}
    review_bridge.append_finding_assessment_replacement(
        store,
        old_report_id="report-t4-old-subject",
        old_finding_id="finding-t4-bridge",
        new_assessment=None,
        current_subject=_new_subject(),
        transaction_id="tx-t4-new-subject-invalidation",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    after = {receipt["receipt_id"] for receipt in store.get_all_active_receipts()}

    assert after
    assert after < before


def test_supported_to_indeterminate_replacement_supersedes_all_receipts(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Indeterminate replacement retires every derived review-failure receipt."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="indeterminate-replace",
    )
    replacement = _assessment(subject)
    replacement["assessment_id"] = "assessment-t4-indeterminate-replacement"
    replacement["assessment"] = "indeterminate"

    review_bridge.append_finding_assessment_bridge(
        store,
        replacement,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-indeterminate-replacement",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert store.get_all_active_receipts() == []


def test_partial_supersession_for_replacement_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A partial supersession delta cannot leave one derived receipt active."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    tx = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="partial-sup",
    )
    replacement = _assessment(subject)
    replacement["assessment_id"] = "assessment-t4-partial-sup"
    replacement["assessment"] = "unsupported-opinion"

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                replacement,
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-t4-partial",
                    "superseded_receipt_ids": [tx["ordered_record_ids"][1]],
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                },
            ],
            transaction_id="tx-t4-partial-sup",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_two_open_stores_refresh_before_bridge_append(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A stale open store refreshes before deriving lifecycle deltas."""
    log_path = _store_path(tmp_path)
    first = _open_store(evidence_store, log_path)
    second = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, first, issuer, grant, subject, finding,
        tx_prefix="concurrent-first",
    )
    replacement = _assessment(subject)
    replacement["assessment_id"] = "assessment-t4-concurrent-second"
    replacement["assessment"] = "indeterminate"

    review_bridge.append_finding_assessment_bridge(
        second,
        replacement,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-concurrent-second",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    reopened = _open_store(evidence_store, log_path)
    assert reopened.get_all_active_receipts() == []


def test_interleaved_two_store_lifecycle_append_completes_delta_under_lock(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Concurrent bridge lifecycle appends derive complete deltas after refresh."""
    log_path = _store_path(tmp_path)
    first = _open_store(evidence_store, log_path)
    second = _open_store(evidence_store, log_path)
    third = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, first, issuer, grant, subject, finding,
        tx_prefix="interleaved-first",
    )
    ready = threading.Barrier(3)
    errors: list[BaseException] = []
    results: dict[str, dict] = {}

    original_second_append = second.append_semantic_records
    original_third_append = third.append_semantic_records

    def interleaved_append(original: object, label: str) -> object:
        def wrapped(records: list[dict], **kwargs: object) -> dict:
            ready.wait(timeout=5)
            result = original(records, **kwargs)
            results[label] = result
            return result

        return wrapped

    second.append_semantic_records = interleaved_append(  # type: ignore[method-assign]
        original_second_append,
        "indeterminate",
    )
    third.append_semantic_records = interleaved_append(  # type: ignore[method-assign]
        original_third_append,
        "supported",
    )

    def append_indeterminate_replacement() -> None:
        try:
            replacement = _assessment(subject)
            replacement["assessment_id"] = "assessment-t4-interleaved-indeterminate"
            replacement["assessment"] = "indeterminate"
            review_bridge.append_finding_assessment_bridge(
                second,
                replacement,
                report_id="report-t4-bridge",
                finding=finding,
                affected_criteria=["AC-0014", "AC-0015"],
                transaction_id="tx-t4-interleaved-replacement",
                acceptance_fingerprint="acceptance-fp-t4-bridge",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        except BaseException as exc:  # noqa: BLE001 - surfaced after join
            errors.append(exc)

    def append_supported_replacement() -> None:
        try:
            replacement = _assessment(subject)
            replacement["assessment_id"] = "assessment-t4-interleaved-supported"
            review_bridge.append_finding_assessment_bridge(
                third,
                replacement,
                report_id="report-t4-bridge",
                finding=finding,
                affected_criteria=["AC-0014", "AC-0015"],
                transaction_id="tx-t4-interleaved-supported",
                acceptance_fingerprint="acceptance-fp-t4-bridge",
                issuer=issuer,
                grant=grant,
                audit_sink=_null_sink,
            )
        except BaseException as exc:  # noqa: BLE001 - surfaced after join
            errors.append(exc)

    indeterminate_worker = threading.Thread(target=append_indeterminate_replacement)
    supported_worker = threading.Thread(target=append_supported_replacement)
    indeterminate_worker.start()
    supported_worker.start()
    ready.wait(timeout=5)
    indeterminate_worker.join(timeout=5)
    supported_worker.join(timeout=5)

    assert not indeterminate_worker.is_alive()
    assert not supported_worker.is_alive()
    assert errors == []
    assert set(results) == {"indeterminate", "supported"}
    reopened = _open_store(evidence_store, log_path)
    assessments = reopened.get_semantic_records("finding-assessment.v1")
    winner = next(
        assessment
        for assessment in reversed(assessments)
        if assessment["assessment_id"]
        in {
            "assessment-t4-interleaved-indeterminate",
            "assessment-t4-interleaved-supported",
        }
    )
    current = review_bridge.select_current_finding_assessments(
        reopened,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )
    key = ("report-t4-bridge", "finding-t4-bridge")
    assert current[key]["assessment"]["assessment_id"] == winner["assessment_id"]
    if winner["assessment"] == "supported":
        receipt_ids = current[key]["receipt_ids"]
        assert len(receipt_ids) == 2
        assert {receipt["receipt_id"] for receipt in reopened.get_all_active_receipts()} == set(
            receipt_ids
        )
    else:
        assert current[key]["receipt_ids"] == []
        assert reopened.get_all_active_receipts() == []


def test_typed_report_replacement_composes_required_supersession_delta(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """The typed report port preserves usability by retiring old-source receipts."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="typed-report-replace",
    )
    replacement = _report(subject, finding)
    replacement["report_id"] = "report-t4-typed-replacement"

    review_persistence.append_current_review_report(
        store,
        replacement,
        transaction_id="tx-t4-typed-report-replacement",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    reopened = _open_store(evidence_store, log_path)
    assert reopened.get_all_active_receipts() == []
    current = review_bridge.select_current_finding_assessments(
        reopened,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )
    assert all(
        item["assessment"]["report_id"] != "report-t4-bridge"
        for item in current.values()
    )


def test_identical_retry_with_invalid_grant_has_no_effect_and_denial_event(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Retry still checks authority and leaves the committed frame unchanged."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="invalid-retry",
    )
    before = store.transaction_count
    events: list[object] = []

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            _assessment(subject),
            report_id="report-t4-bridge",
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id="tx-t4-invalid-retry-supported",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=object(),
            audit_sink=events.append,
        )

    assert exc_info.value.denial_code == "denied-invalid-grant"
    assert store.transaction_count == before
    assert len(events) == 1
    assert events[0].outcome == "denied"


def test_changed_transaction_body_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Same transaction ID with a changed assessment body is refused."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="changed-body",
    )
    committed = copy.deepcopy(store.get_transaction("tx-t4-changed-body-supported"))
    changed = _assessment(subject)
    changed["evidence_refs"] = ["evidence:changed"]

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            changed,
            report_id="report-t4-bridge",
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id="tx-t4-changed-body-supported",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"
    assert store.get_transaction("tx-t4-changed-body-supported") == committed
    assert store.get_semantic_records("finding-assessment.v1")[0]["evidence_refs"] == [
        "evidence:observation",
        "evidence:reachable-path",
    ]


def test_raw_checksum_valid_partial_assessment_frame_refuses_on_replay(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Replay wraps a checksum-valid partial assessment frame as store error."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="raw-partial-replay",
    )
    partial = _assessment(subject)
    partial["assessment_id"] = "assessment-t4-raw-partial"
    tx_body = {
        "schema_version": 1,
        "transaction_id": "tx-t4-raw-partial",
        "ordered_record_ids": [partial["assessment_id"]],
        "acceptance_fingerprint": "acceptance-fp-t4-bridge",
    }
    tx = {
        **tx_body,
        "checksum": evidence_store._compute_frame_checksum(tx_body, [partial]),
    }
    frame = evidence_store._canonical_json({"tx": tx, "records": [partial]})
    log_path.write_bytes(log_path.read_bytes() + f"{frame}\n".encode())

    with pytest.raises(evidence_store.EvidenceStoreError):
        _open_store(evidence_store, log_path)
    assert store.get_all_active_receipts()


def test_torn_suffix_keeps_completed_assessment_receipts_and_supersessions(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Recovery keeps the completed bridge replacement and drops torn suffix."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="torn-prefix",
    )
    replacement = _assessment(subject)
    replacement["assessment_id"] = "assessment-t4-torn-indeterminate"
    replacement["assessment"] = "indeterminate"
    review_bridge.append_finding_assessment_bridge(
        store,
        replacement,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-torn-replacement",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    log_path.write_bytes(log_path.read_bytes() + b'{"tx":{"partial":true}')

    reopened = _open_store(evidence_store, log_path)

    assert reopened.get_all_active_receipts() == []
    assert any(
        item["assessment_id"] == "assessment-t4-torn-indeterminate"
        for item in reopened.get_semantic_records("finding-assessment.v1")
    )


def test_post_allow_denial_uses_same_operation_id(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Central checker refusals store an allow and matching same-op denial."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    events: list[object] = []

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_assessment(_subject())],
            transaction_id="tx-t4-post-allow-denial",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=events.append,
        )

    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"
    assert [event.outcome for event in events] == ["allowed", "denied"]
    assert events[0].operation_id == events[1].operation_id


def test_bridge_receipt_body_mismatches_refuse(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A frame whose receipt ID does not match the derived expected ID is refused.

    Uses a bridge-shaped receipt with a wrong receipt_id (derived with a wrong
    acceptance_fingerprint) so that actual_ids does not cover expected_ids.  This
    isolates the completeness check (MUT-041) after the frame_receipts filter was
    widened to all evidence-receipt.v1 records: the body check is skipped for
    receipts whose IDs are not in expected_ids, so only the completeness check
    refuses the frame.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-body-mismatch-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assessment = _assessment(subject)
    # Receipt has a wrong receipt_id (derived with wrong acceptance_fingerprint) so
    # actual_ids = {wrong_id} and expected_ids = {correct_id}: completeness fails.
    receipt = {
        "schema_version": 1,
        "receipt_id": review_bridge.derive_review_failure_receipt_id(
            report_id=report["report_id"],
            finding_id=finding["finding_id"],
            assessment_id=assessment["assessment_id"],
            criterion_ref="AC-0014",
            acceptance_fingerprint="wrong-fp-for-completeness-test",
        ),
        "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        "lineage": {"criterion_ref": "AC-0014"},
        "selector": {"term": "supported-review-failure"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "review-failure"},
        "outcome": "review-failure",
        "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
    }

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [assessment, receipt],
            transaction_id="tx-t4-body-mismatch",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_multiple_new_assessments_same_finding_group_refuse(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """One frame cannot leave ambiguous assessments for the same source."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-ambiguous-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    first = _assessment(subject)
    second = _assessment(subject)
    second["assessment_id"] = "assessment-t4-ambiguous-second"
    records = [first]
    for assessment in (first, second):
        for criterion in ("AC-0014", "AC-0015"):
            records.append(
                {
                    "schema_version": 1,
                    "receipt_id": review_bridge.derive_review_failure_receipt_id(
                        report_id=report["report_id"],
                        finding_id=finding["finding_id"],
                        assessment_id=assessment["assessment_id"],
                        criterion_ref=criterion,
                        acceptance_fingerprint="acceptance-fp-t4-bridge",
                    ),
                    "acceptance_fingerprint": "acceptance-fp-t4-bridge",
                    "lineage": {"criterion_ref": criterion},
                    "selector": {"term": "supported-review-failure"},
                    "freshness_mode": "exact-subject",
                    "observation": {"type": "review-failure"},
                    "outcome": "review-failure",
                    "producer": {
                        "class": "review-bridge",
                        "identity": "structured-review-boundary",
                    },
                }
            )
        if assessment is first:
            records.append(second)

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            records,
            transaction_id="tx-t4-ambiguous-assessments",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-ambiguous-review-assessment-batch"


# ── New tests required by the lifecycle port ──────────────────────────────────


def test_lifecycle_invalid_kind_refuses_with_paired_denial_event(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """An unknown lifecycle kind refuses after the allow event with a paired denial."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    events: list[object] = []

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_assessment(_subject())],
            transaction_id="tx-t4-invalid-lifecycle-kind",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=events.append,
            lifecycle={"kind": "unknown-kind"},
        )

    assert exc_info.value.denial_code == "denied-invalid-review-lifecycle"
    assert [ev.outcome for ev in events] == ["allowed", "denied"]
    assert events[0].operation_id == events[1].operation_id


def test_lifecycle_extra_key_refuses(
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A lifecycle dict with an extra key refuses with the standard lifecycle code."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_assessment(_subject())],
            transaction_id="tx-t4-lifecycle-extra-key",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-assessment",
                "report_id": "report-t4-bridge",
                "finding_id": "finding-t4-bridge",
                "affected_criteria": ["AC-0014"],
                "extra_key": "not-allowed",
            },
        )

    assert exc_info.value.denial_code == "denied-invalid-review-lifecycle"


def test_lifecycle_affected_criteria_mismatch_refuses(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A lifecycle affected_criteria that does not match the finding criteria refuses."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-criteria-mismatch-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assessment = _assessment(subject)
    assessment["assessment_id"] = "assessment-t4-criteria-mismatch"

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [assessment],
            transaction_id="tx-t4-criteria-mismatch-assessment",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "finding-assessment",
                "report_id": report["report_id"],
                "finding_id": finding["finding_id"],
                "affected_criteria": ["AC-WRONG"],
            },
        )

    assert exc_info.value.denial_code == "denied-invalid-review-lifecycle"


def test_typed_report_replacement_retry_is_idempotent(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Retrying a typed report replacement with the same tx_id returns the same transaction."""
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="report-retry",
    )
    replacement = _report(subject, finding)
    replacement["report_id"] = "report-t4-retry-replacement"

    first = review_persistence.append_current_review_report(
        store,
        replacement,
        transaction_id="tx-t4-report-retry",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    retry = review_persistence.append_current_review_report(
        store,
        replacement,
        transaction_id="tx-t4-report-retry",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert retry == first
    assert store.transaction_count == 3  # report + assessment + replacement


def test_typed_report_replacement_changed_retry_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Retrying a typed report replacement with a different body refuses."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="report-changed-retry",
    )
    replacement = _report(subject, finding)
    replacement["report_id"] = "report-t4-changed-retry-replacement"

    review_persistence.append_current_review_report(
        store,
        replacement,
        transaction_id="tx-t4-changed-report-retry",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    changed = copy.deepcopy(replacement)
    changed["lineage"]["source_event_id"] = "source-event-changed"

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_persistence.append_current_review_report(
            store,
            changed,
            transaction_id="tx-t4-changed-report-retry",
            expected_subject=subject,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


def test_source_invalidation_with_same_subject_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Invalidation with the same fingerprint as the source subject refuses."""
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="same-subject-invalidation",
    )
    before = list(store.get_all_active_receipts())
    assert before  # there are active receipts before the attempted invalidation

    # Attempt to invalidate with the same review subject (same fingerprint).
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_replacement(
            store,
            old_report_id="report-t4-bridge",
            old_finding_id="finding-t4-bridge",
            new_assessment=None,
            current_subject=subject,  # same as source — must be refused
            transaction_id="tx-t4-same-subject-invalidation",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

    assert exc_info.value.denial_code == "denied-review-source-current"
    # Receipts must remain active after the refused invalidation.
    after = list(store.get_all_active_receipts())
    assert [r["receipt_id"] for r in after] == [r["receipt_id"] for r in before]


def test_raw_supersession_without_lifecycle_context_refuses_on_replay(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A schema-valid supersession-only frame without lifecycle context fails on replay.

    Uses _inject_raw_frame to produce a checksum-valid frame so that header
    validation passes and only the review-transition checker (bridge_superseded
    without any justification) causes the EvidenceStoreError.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="raw-sup-replay",
    )
    # Capture IDs of the active receipts that the bridge committed.
    active_receipt_ids = [r["receipt_id"] for r in store.get_all_active_receipts()]
    assert active_receipt_ids

    # Build a raw supersession record that references the bridge-owned receipts.
    sup = {
        "schema_version": 1,
        "supersession_id": "supersession-raw-replay-test",
        "superseded_receipt_ids": active_receipt_ids,
        "authority": {"identity": "structured-review-boundary", "role": "review-bridge"},
        "provenance": {"reason_code": "review-assessment-superseded"},
    }
    # Inject a checksum-valid frame so header validation passes; only the
    # transition checker (bridge_superseded without lifecycle context) refuses.
    _inject_raw_frame(log_path, [sup], "tx-raw-sup-replay")

    with pytest.raises(evidence_store.EvidenceStoreError):
        _open_store(evidence_store, log_path)


# ── D1: _write_frame_once must call _validate_review_transition ───────────────


def test_d1_append_supersession_of_bridge_receipt_refuses_at_live_write(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Single-record append_supersession of a bridge receipt is refused with denial code.

    Before the D1 fix, _write_frame_once bypassed _validate_review_transition so the
    supersession was admitted live; the store then failed to reopen (frame replay raised
    denied-incomplete-review-assessment-delta as EvidenceStoreError).  After the fix the
    live write itself is refused and no bytes are appended.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    tx = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d1-sup",
    )
    bridge_receipt_id = tx["ordered_record_ids"][1]
    before_size = log_path.stat().st_size

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_supersession(
            {
                "schema_version": 1,
                "supersession_id": "supersession-d1-single",
                "superseded_receipt_ids": [bridge_receipt_id],
                "authority": {"identity": "structured-review-boundary", "role": "review-bridge"},
                "provenance": {"reason_code": "review-assessment-superseded"},
            },
            transaction_id="tx-d1-single-sup",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"
    # No bytes appended: store reopens to the same state.
    assert log_path.stat().st_size == before_size
    reopened = _open_store(evidence_store, log_path)
    assert len(reopened.get_all_active_receipts()) == 2


def test_d1_forged_bridge_receipt_without_assessment_refuses_at_live_write(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Single-record append_receipt with a bridge-shaped receipt but no assessment is refused.

    Before the D1 fix the forged receipt was admitted because _write_frame_once skipped
    the assessment-pairing check.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_receipt(
            {
                "schema_version": 1,
                "receipt_id": "receipt-d1-forged-bridge",
                "acceptance_fingerprint": "acceptance-fp-t4-bridge",
                "lineage": {"criterion_ref": "AC-0014"},
                "selector": {"term": "supported-review-failure"},
                "freshness_mode": "exact-subject",
                "observation": {"type": "review-failure"},
                "outcome": "review-failure",
                "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
            },
            transaction_id="tx-d1-forged-receipt",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


# ── D2: invalidation-context check must be non-vacuous ───────────────────────


def test_d2_raw_batch_unrelated_subject_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Raw supersession batch with an unrelated delivery_subject_id is refused.

    Before the D2 fix any review-subject.v1 in the frame satisfied the check, even one
    for a completely different delivery entity.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    tx = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d2-unrelated",
    )
    bridge_receipt_ids = tx["ordered_record_ids"][1:]
    unrelated_subject = {
        "schema_version": 1,
        "review_subject_id": "review-subject-d2-unrelated",
        "review_subject_fingerprint": "review-subject-fp-d2-unrelated",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-UNRELATED",  # different delivery entity
            "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        },
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_bridge.py"
        ],
        "normalized_statuses": ["modified"],
        "review_policy_fingerprint": "review-policy-d2-unrelated",
        "lineage": {"provider": "test", "projection_version": "2.0"},
    }
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                unrelated_subject,
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-d2-unrelated",
                    "superseded_receipt_ids": bridge_receipt_ids,
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                },
            ],
            transaction_id="tx-d2-unrelated",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_d2_raw_batch_same_fingerprint_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Raw supersession batch with same fingerprint as the source subject is refused.

    Before the D2 fix any subject with the right delivery_subject_id would pass even if
    the fingerprint matched (no actual invalidation occurred).
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    tx = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d2-samefp",
    )
    bridge_receipt_ids = tx["ordered_record_ids"][1:]
    same_fp_subject = {
        "schema_version": 1,
        "review_subject_id": "review-subject-d2-samefp",
        "review_subject_fingerprint": subject["review_subject_fingerprint"],  # same fp
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-t4-bridge",  # same delivery id
            "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        },
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_bridge.py"
        ],
        "normalized_statuses": ["modified"],
        "review_policy_fingerprint": subject["review_policy_fingerprint"],  # same policy fp
        "lineage": {"provider": "test", "projection_version": "1.0"},
    }
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                same_fp_subject,
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-d2-samefp",
                    "superseded_receipt_ids": bridge_receipt_ids,
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                },
            ],
            transaction_id="tx-d2-samefp",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_d2_durable_subject_before_source_report_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Durable invalidating subject admitted before the source report is not sufficient.

    The "durable later" rule requires the invalidating subject to have been admitted in a
    transaction AFTER the source report.  A subject committed earlier does not satisfy it.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    # Commit the invalidating subject BEFORE the source report/assessment.
    store.append_semantic_records(
        [_new_subject()],
        transaction_id="tx-d2-earlier-subject",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    tx = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d2-earlier",
    )
    bridge_receipt_ids = tx["ordered_record_ids"][1:]
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-d2-earlier",
                    "superseded_receipt_ids": bridge_receipt_ids,
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                },
            ],
            transaction_id="tx-d2-earlier-sup",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_d2_durable_subject_after_source_report_admits(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Durable invalidating subject admitted after the source report satisfies the check.

    When the invalidating subject is already durable and was committed in a later
    transaction than the source report, a supersession-only frame is accepted and the
    bridge receipts are retired.  The store must reopen cleanly.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    tx = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d2-later",
    )
    bridge_receipt_ids = tx["ordered_record_ids"][1:]
    # Commit the invalidating subject AFTER the source report/assessment.
    store.append_semantic_records(
        [_new_subject()],
        transaction_id="tx-d2-later-subject",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    # Raw supersession-only frame is accepted: durable subject is later than source.
    store.append_semantic_records(
        [
            {
                "schema_version": 1,
                "supersession_id": "supersession-d2-later",
                "superseded_receipt_ids": bridge_receipt_ids,
                "authority": {
                    "identity": "structured-review-boundary",
                    "role": "review-bridge",
                },
                "provenance": {"reason_code": "review-assessment-superseded"},
            },
        ],
        transaction_id="tx-d2-later-sup",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert store.get_all_active_receipts() == []
    reopened = _open_store(evidence_store, log_path)
    assert reopened.get_all_active_receipts() == []


# ── D3: source-invalidation retry must be request-checked ────────────────────


def test_d3_source_invalidation_changed_source_retry_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Retry with same transaction_id but different finding_id is refused.

    Before the D3 fix, _check_lifecycle_idempotent compared only the committed subject
    body and returned True when it matched, regardless of the lifecycle source coordinates.
    A retry with a different finding_id was therefore silently treated as idempotent.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d3-inv",
    )
    # First invalidation: succeeds.
    review_bridge.append_finding_assessment_replacement(
        store,
        old_report_id="report-t4-bridge",
        old_finding_id="finding-t4-bridge",
        new_assessment=None,
        current_subject=_new_subject(),
        transaction_id="tx-d3-inv",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    # Retry with same transaction_id but a different finding_id in the lifecycle.
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [_new_subject()],
            transaction_id="tx-d3-inv",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
            lifecycle={
                "kind": "source-invalidation",
                "report_id": "report-t4-bridge",
                "finding_id": "finding-CHANGED",  # differs from the committed lifecycle
            },
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


# ── D4: finding-assessment retry must check lifecycle criteria ────────────────


def test_d4_unsupported_assessment_lifecycle_mismatch_retry_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Retry with same transaction_id but mismatched affected_criteria is refused.

    Before the D4 fix, _check_lifecycle_idempotent did not verify that the retry's
    lifecycle criteria matched the durable finding's criteria for unsupported outcomes.
    A retry with a subset of criteria was silently treated as idempotent.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="d4-unsup",
    )
    unsupported = _assessment(subject)
    unsupported["assessment_id"] = "assessment-t4-d4-unsupported"
    unsupported["assessment"] = "indeterminate"
    # First unsupported assessment with full criteria: succeeds.
    review_bridge.append_finding_assessment_bridge(
        store,
        unsupported,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-d4-unsup",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    # Retry with same transaction_id but a strict subset of criteria.
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            unsupported,
            report_id="report-t4-bridge",
            finding=finding,
            affected_criteria=["AC-0014"],  # subset: differs from the committed lifecycle
            transaction_id="tx-d4-unsup",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


# ── D5: projection uses select_current_report for exact tip check ─────────────


def test_d5_forked_report_group_yields_no_projection_entry(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A forked report group (tied sequence numbers) produces no projection entry.

    Before the D5 fix, current_finding_assessments used _is_current_report which returns
    True for both members of a tied group because neither has a strictly higher sequence.
    select_current_report correctly returns None for a duplicate-sequence group, so the
    entry is omitted.
    """
    import hashlib
    import json as _json

    def _canonical(obj: object) -> str:
        return _json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def _inject_report_frame(log_path: Path, report: dict, tx_id: str) -> None:
        """Append a checksum-valid single-report frame directly to the log."""
        tx_body = {
            "schema_version": 1,
            "transaction_id": tx_id,
            "ordered_record_ids": [report["report_id"]],
            "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        }
        payload = _canonical({"tx": tx_body, "records": [report]})
        checksum = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        tx_full = {**tx_body, "checksum": checksum}
        frame = _canonical({"tx": tx_full, "records": [report]}) + "\n"
        log_path.write_bytes(log_path.read_bytes() + frame.encode("utf-8"))

    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()

    # Step 1: commit source report (gets sequence = 1) with no receipts yet.
    review_persistence.append_current_review_report(
        store,
        _report(subject, finding),
        transaction_id="tx-d5-report1",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 2: inject a forked twin with the SAME sequence = 1 into the log.
    # No bridge receipts exist yet so the report-replacement validation passes on replay.
    forked_report = {
        "schema_version": 1,
        "report_id": "report-t4-bridge-fork",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,  # tied with report1 — creates a forked group
            "review_policy_fingerprint": "review-policy-t4-current",
            "source_event_id": "source-event-fork",
            "producer": "synthetic-reviewer-fork",
        },
        "findings": [copy.deepcopy(finding)],
    }
    _inject_report_frame(log_path, forked_report, "tx-d5-fork")

    # Step 3: commit the bridge assessment for report1.  Under the advisory lock the
    # store re-reads the log (_refresh_from_durable_log) so the forked report is now
    # indexed.  _is_current_report(report1) returns True (no seq > 1) so the assessment
    # is accepted.
    assessment = _assessment(subject)
    review_bridge.append_finding_assessment_bridge(
        store,
        assessment,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-d5-assessment",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 4: reopen and query.  select_current_report returns None for the tied group
    # (both reports at sequence = 1) so the assessment entry must be omitted.
    reopened = _open_store(evidence_store, log_path)
    current = review_bridge.select_current_finding_assessments(
        reopened,
        review_subject_fingerprint=subject["review_subject_fingerprint"],
    )
    assert current == {}


# ── D6 helpers ───────────────────────────────────────────────────────────────


def _subject_b() -> dict:
    """Build an independent review subject for D6 source B (different delivery entity)."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-d6-B",
        "review_subject_fingerprint": "review-subject-fp-d6-B",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-d6-B",
            "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        },
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_bridge.py"
        ],
        "normalized_statuses": ["modified"],
        "review_policy_fingerprint": "review-policy-d6-B",
        "lineage": {"provider": "structured-review-boundary-test", "projection_version": "1.0"},
    }


def _finding_b() -> dict:
    """Build a supported finding for D6 source B (single criterion)."""
    return {
        "schema_version": 1,
        "finding_id": "finding-d6-B",
        "rule_ref": "AC-0014",
        "observation": "D6 source B: the criterion has a review failure.",
        "reachable_path": "assessment bridge to criterion receipt",
        "actual_failure": "The affected criterion has a current supported review failure.",
        "affected_acceptance_criteria": ["AC-0014"],
        "evidence_refs": [],
        "material": True,
    }


def _report_b(subject_b: dict, finding_b: dict) -> dict:
    """Build a findings report for D6 source B."""
    return {
        "schema_version": 1,
        "report_id": "report-d6-B",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject_b),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": "review-policy-d6-B",
            "source_event_id": "source-d6-B",
            "producer": "synthetic-reviewer",
        },
        "findings": [copy.deepcopy(finding_b)],
    }


def _append_bridge_case_b(
    review_bridge: ModuleType,
    review_persistence: ModuleType,
    store: object,
    issuer: object,
    grant: object,
    *,
    tx_prefix: str = "d6-B",
) -> dict:
    """Commit a second independent bridge assessment for D6 source B."""
    subj_b = _subject_b()
    find_b = _finding_b()
    review_persistence.append_current_review_report(
        store,
        _report_b(subj_b, find_b),
        transaction_id=f"tx-{tx_prefix}-report",
        expected_subject=subj_b,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assessment_b = {
        "schema_version": 1,
        "assessment_id": f"assessment-{tx_prefix}",
        "finding_id": "finding-d6-B",
        "report_id": "report-d6-B",
        "review_subject_fingerprint": subj_b["review_subject_fingerprint"],
        "assessment": "supported",
        "evidence_refs": [],
        "lineage": {"predicate_version": "slice2-t4-v1"},
    }
    return review_bridge.append_finding_assessment_bridge(
        store,
        assessment_b,
        report_id="report-d6-B",
        finding=find_b,
        affected_criteria=["AC-0014"],
        transaction_id=f"tx-{tx_prefix}-assessment",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )


def _inject_raw_frame(log_path: Path, records: list[dict], tx_id: str) -> None:
    """Append a checksum-valid multi-record frame directly to the evidence log."""
    import hashlib
    import json as _json

    def _canonical(obj: object) -> str:
        return _json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    record_ids = []
    for r in records:
        for key in ("receipt_id", "supersession_id", "assessment_id", "report_id", "review_subject_id"):
            v = r.get(key)
            if v:
                record_ids.append(v)
                break

    tx_body = {
        "schema_version": 1,
        "transaction_id": tx_id,
        "ordered_record_ids": record_ids,
        "acceptance_fingerprint": "acceptance-fp-t4-bridge",
    }
    payload = _canonical({"tx": tx_body, "records": records})
    checksum = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    tx_full = {**tx_body, "checksum": checksum}
    frame = _canonical({"tx": tx_full, "records": records}) + "\n"
    log_path.write_bytes(log_path.read_bytes() + frame.encode("utf-8"))


# ── D6: universal per-receipt justification check ────────────────────────────


def test_d6_assessment_piggyback_refuses_live(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Raw assessment frame that piggbacks an unrelated source's receipts is refused live.

    A frame [indeterminate assessment for source A, supersession of A's receipts AND B's
    receipt] must be refused even though the assessment legitimately justifies A's
    receipts — B's receipt has no in-frame justification.  Before the D6 fix, the
    per-receipt check only ran when the frame had no assessment and no report, so the
    piggybacked B receipt was silently admitted.

    After refusal no bytes are appended and the store reopens with the original 3
    active receipts (2 from A, 1 from B).
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject_a = _subject()
    finding_a = _finding()
    tx_a = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject_a, finding_a,
        report_id="report-d6-piggyback-A",
        tx_prefix="d6-piggyback-A",
    )
    tx_b = _append_bridge_case_b(
        review_bridge, review_persistence, store, issuer, grant, tx_prefix="d6-piggyback-B",
    )
    receipt_a_ids = list(tx_a["ordered_record_ids"][1:])  # skip assessment_a_id
    receipt_b_id = tx_b["ordered_record_ids"][1]           # single receipt for B
    before_size = log_path.stat().st_size

    new_assessment_a = {
        "schema_version": 1,
        "assessment_id": "assessment-d6-piggyback-A-indeterminate",
        "finding_id": "finding-t4-bridge",
        "report_id": "report-d6-piggyback-A",
        "review_subject_fingerprint": subject_a["review_subject_fingerprint"],
        "assessment": "indeterminate",
        "evidence_refs": [],
        "lineage": {"predicate_version": "slice2-t4-v1"},
    }
    piggybacked_ids = receipt_a_ids + [receipt_b_id]

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                new_assessment_a,
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-d6-assess-piggyback",
                    "superseded_receipt_ids": piggybacked_ids,
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                },
            ],
            transaction_id="tx-d6-assess-piggyback",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"
    assert log_path.stat().st_size == before_size
    reopened = _open_store(evidence_store, log_path)
    assert len(reopened.get_all_active_receipts()) == 3  # 2 from A + 1 from B


def test_d6_report_replacement_piggyback_refuses_live(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Report-replacement frame that piggbacks an unrelated source's receipts is refused live.

    A frame [replacement report for source A's group, supersession of A's receipts AND
    B's receipt] must be refused — B's receipt has no in-frame justification from the
    replacement report (different role/subject/policy group).  Before the D6 fix, the
    per-receipt check only ran when the frame had no assessment and no report.

    After refusal no bytes are appended and the store reopens with the original 3
    active receipts.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject_a = _subject()
    finding_a = _finding()
    tx_a = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject_a, finding_a,
        report_id="report-d6-replace-A",
        tx_prefix="d6-replace-A",
    )
    tx_b = _append_bridge_case_b(
        review_bridge, review_persistence, store, issuer, grant, tx_prefix="d6-replace-B",
    )
    receipt_a_ids = list(tx_a["ordered_record_ids"][1:])
    receipt_b_id = tx_b["ordered_record_ids"][1]
    before_size = log_path.stat().st_size

    # Replacement report for A's group (sequence 2, same role/subject/policy)
    replacement_report_a = {
        "schema_version": 1,
        "report_id": "report-d6-replace-A-v2",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject_a),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 2,
            "review_policy_fingerprint": "review-policy-t4-current",
            "source_event_id": "source-d6-replace-A-v2",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    piggybacked_ids = receipt_a_ids + [receipt_b_id]

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [
                replacement_report_a,
                {
                    "schema_version": 1,
                    "supersession_id": "supersession-d6-replace-piggyback",
                    "superseded_receipt_ids": piggybacked_ids,
                    "authority": {
                        "identity": "structured-review-boundary",
                        "role": "review-bridge",
                    },
                    "provenance": {"reason_code": "review-assessment-superseded"},
                },
            ],
            transaction_id="tx-d6-replace-piggyback",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"
    assert log_path.stat().st_size == before_size
    reopened = _open_store(evidence_store, log_path)
    assert len(reopened.get_all_active_receipts()) == 3


def test_d6_assessment_piggyback_refuses_on_replay(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Injected checksum-valid assessment-piggyback frame causes EvidenceStoreError on reopen.

    A raw frame with a valid checksum but a piggybacked unrelated receipt is admitted
    by first-wins replay only if the transition checker does not run universally.
    After the D6 fix, replay enforces the same per-receipt justification rule and
    raises EvidenceStoreError when it finds an unjustified bridge receipt supersession.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject_a = _subject()
    finding_a = _finding()
    tx_a = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject_a, finding_a,
        report_id="report-d6-replay-A",
        tx_prefix="d6-replay-A",
    )
    tx_b = _append_bridge_case_b(
        review_bridge, review_persistence, store, issuer, grant, tx_prefix="d6-replay-B",
    )
    receipt_a_ids = list(tx_a["ordered_record_ids"][1:])
    receipt_b_id = tx_b["ordered_record_ids"][1]
    piggybacked_ids = receipt_a_ids + [receipt_b_id]

    new_assessment_a = {
        "schema_version": 1,
        "assessment_id": "assessment-d6-replay-A-indeterminate",
        "finding_id": "finding-t4-bridge",
        "report_id": "report-d6-replay-A",
        "review_subject_fingerprint": subject_a["review_subject_fingerprint"],
        "assessment": "indeterminate",
        "evidence_refs": [],
        "lineage": {"predicate_version": "slice2-t4-v1"},
    }
    sup_record = {
        "schema_version": 1,
        "supersession_id": "supersession-d6-replay-piggyback",
        "superseded_receipt_ids": piggybacked_ids,
        "authority": {
            "identity": "structured-review-boundary",
            "role": "review-bridge",
        },
        "provenance": {"reason_code": "review-assessment-superseded"},
    }
    _inject_raw_frame(
        log_path,
        [new_assessment_a, sup_record],
        "tx-d6-replay-assess-piggyback",
    )

    with pytest.raises(evidence_store.EvidenceStoreError):
        _open_store(evidence_store, log_path)


def test_d6_report_replacement_piggyback_refuses_on_replay(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Injected checksum-valid report-replacement piggyback frame refuses on replay.

    A raw report-replacement frame that piggbacks a receipt from an unrelated source
    must refuse on replay, not just during live writes.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject_a = _subject()
    finding_a = _finding()
    tx_a = _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject_a, finding_a,
        report_id="report-d6-replay-rpt-A",
        tx_prefix="d6-replay-rpt-A",
    )
    tx_b = _append_bridge_case_b(
        review_bridge, review_persistence, store, issuer, grant, tx_prefix="d6-replay-rpt-B",
    )
    receipt_a_ids = list(tx_a["ordered_record_ids"][1:])
    receipt_b_id = tx_b["ordered_record_ids"][1]
    piggybacked_ids = receipt_a_ids + [receipt_b_id]

    replacement_report_a = {
        "schema_version": 1,
        "report_id": "report-d6-replay-rpt-A-v2",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject_a),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 2,
            "review_policy_fingerprint": "review-policy-t4-current",
            "source_event_id": "source-d6-replay-rpt-A-v2",
            "producer": "synthetic-reviewer",
        },
        "findings": [],
    }
    sup_record = {
        "schema_version": 1,
        "supersession_id": "supersession-d6-replay-rpt-piggyback",
        "superseded_receipt_ids": piggybacked_ids,
        "authority": {
            "identity": "structured-review-boundary",
            "role": "review-bridge",
        },
        "provenance": {"reason_code": "review-assessment-superseded"},
    }
    _inject_raw_frame(
        log_path,
        [replacement_report_a, sup_record],
        "tx-d6-replay-rpt-piggyback",
    )

    with pytest.raises(evidence_store.EvidenceStoreError):
        _open_store(evidence_store, log_path)


# ── Mutation-repair: single-guard isolation tests ─────────────────────────────


def test_bridge_receipt_correct_id_wrong_body_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A bridge receipt with the correct expected ID but wrong body is refused.

    Isolates MUT-061: the body check
    ``if (receipt.get("acceptance_fingerprint") != acceptance_fingerprint or ...)``.
    The receipt is bridge-shaped (selector.term and producer.class are correct) and
    has the correct expected receipt_id, so the completeness check passes.  Only
    the body check catches the wrong outcome field.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-mut061-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assessment = _assessment(subject)
    # The finding has two criteria: AC-0014 and AC-0015.  Provide both receipts so
    # the completeness check passes and the body check is the sole refusal path.
    # AC-0014 receipt: correct ID, bridge shape, but wrong outcome — caught by body check.
    receipt_wrong = {
        "schema_version": 1,
        "receipt_id": review_bridge.derive_review_failure_receipt_id(
            report_id=report["report_id"],
            finding_id=finding["finding_id"],
            assessment_id=assessment["assessment_id"],
            criterion_ref="AC-0014",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
        ),
        "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        "lineage": {"criterion_ref": "AC-0014"},
        "selector": {"term": "supported-review-failure"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "review-failure"},
        "outcome": "no-violation",  # wrong: should be "review-failure"
        "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
    }
    # AC-0015 receipt: correct ID and correct body — keeps completeness check passing.
    receipt_ok = {
        "schema_version": 1,
        "receipt_id": review_bridge.derive_review_failure_receipt_id(
            report_id=report["report_id"],
            finding_id=finding["finding_id"],
            assessment_id=assessment["assessment_id"],
            criterion_ref="AC-0015",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
        ),
        "acceptance_fingerprint": "acceptance-fp-t4-bridge",
        "lineage": {"criterion_ref": "AC-0015"},
        "selector": {"term": "supported-review-failure"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "review-failure"},
        "outcome": "review-failure",
        "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
    }

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        store.append_semantic_records(
            [assessment, receipt_wrong, receipt_ok],
            transaction_id="tx-t4-mut061",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta"


def test_finding_assessment_retry_same_id_changed_body_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A lifecycle retry with the same assessment_id but changed body is refused.

    Isolates MUT-071: the body-comparison guard
    ``if _canonical_json(committed_assessment) != _canonical_json(assessment): return False``.
    The assessment_id matches committed_ids[0], so the assessment_id check passes,
    but the body has changed (different evidence_refs).
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()
    _append_supported_bridge_case(
        review_bridge, review_persistence, store, issuer, grant, subject, finding,
        tx_prefix="mut071",
    )
    # The committed assessment_id is "assessment-t4-mut071-supported" (from tx_prefix).
    # Build a retry with the same assessment_id but different evidence_refs.
    retry_assessment = _assessment(subject)
    retry_assessment["assessment_id"] = "assessment-t4-mut071-supported"
    retry_assessment["report_id"] = "report-t4-bridge"
    retry_assessment["evidence_refs"] = ["evidence:changed-mut071"]

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            retry_assessment,
            report_id="report-t4-bridge",
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id="tx-t4-mut071-supported",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


def test_finding_assessment_retry_different_id_same_tx_refuses(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A lifecycle retry with a different assessment_id under the same tx is refused.

    Isolates MUT-072: the assessment_id first-record guard
    ``if committed_ids[0] != assessment_id: return False``.
    A second assessment (same body) was committed under a bootstrap transaction,
    so its assessment body exists in semantic_records.  The retry reuses the
    target transaction_id but provides the bootstrap assessment_id.  Without
    MUT-072's guard, _check_lifecycle_idempotent would find the matching body in
    semantic_records and incorrectly treat the retry as idempotent.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()

    # Step 1: persist the source report.
    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-t4-mut072-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 2: commit assessment_id="assessment-mut072-initial" as indeterminate under
    # the target transaction_id.
    initial_assessment = _assessment(subject)
    initial_assessment["assessment_id"] = "assessment-mut072-initial"
    initial_assessment["assessment"] = "indeterminate"
    review_bridge.append_finding_assessment_bridge(
        store,
        initial_assessment,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-mut072-target",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 3: commit assessment_id="assessment-mut072-bootstrap" under a separate tx
    # so it exists in semantic_records (needed for MUT-072 to incorrectly match body).
    bootstrap_assessment = _assessment(subject)
    bootstrap_assessment["assessment_id"] = "assessment-mut072-bootstrap"
    bootstrap_assessment["assessment"] = "indeterminate"
    review_bridge.append_finding_assessment_bridge(
        store,
        bootstrap_assessment,
        report_id="report-t4-bridge",
        finding=finding,
        affected_criteria=["AC-0014", "AC-0015"],
        transaction_id="tx-t4-mut072-bootstrap",
        acceptance_fingerprint="acceptance-fp-t4-bridge",
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 4: retry the target tx with the bootstrap assessment_id.
    # committed_ids[0]="assessment-mut072-initial" != "assessment-mut072-bootstrap".
    retry_assessment = copy.deepcopy(bootstrap_assessment)
    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            retry_assessment,
            report_id="report-t4-bridge",
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id="tx-t4-mut072-target",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-duplicate-transaction-id"


# ── R4: assessment subject fingerprint binding ────────────────────────────────


def test_r4_assessment_wrong_subject_fingerprint_refused(
    review_bridge: ModuleType,
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R4: an assessment whose review_subject_fingerprint differs from the source
    report's subject fingerprint must be refused with
    denied-incomplete-review-assessment-delta.

    The store's assessment loop checks:
        assessment.review_subject_fingerprint == report.subject.review_subject_fingerprint.
    A mismatch means the assessment claims a finding for a subject that the report
    did not review.
    Mutation: this check removed → assessment admitted with wrong fingerprint.
    """
    store = _open_store(evidence_store, _store_path(tmp_path))
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()

    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-r4-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Build an assessment that claims a different review_subject_fingerprint.
    bad_assessment = _assessment(subject)
    bad_assessment["assessment_id"] = "assessment-r4-wrong-fp"
    bad_assessment["review_subject_fingerprint"] = "wrong-subject-fingerprint"

    with pytest.raises(evidence_store.EvidenceStoreRefused) as exc_info:
        review_bridge.append_finding_assessment_bridge(
            store,
            bad_assessment,
            report_id="report-t4-bridge",
            finding=finding,
            affected_criteria=["AC-0014", "AC-0015"],
            transaction_id="tx-r4-wrong-fp",
            acceptance_fingerprint="acceptance-fp-t4-bridge",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-incomplete-review-assessment-delta", (
        "R4: assessment with wrong review_subject_fingerprint must be refused"
    )


def test_r4_replay_refuses_wrong_subject_fingerprint(
    evidence_store: ModuleType,
    review_persistence: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """R4 replay: a committed assessment frame with wrong review_subject_fingerprint
    must be refused on store re-open with an EvidenceStoreError naming
    denied-incomplete-review-assessment-delta.

    This verifies that the R4 check is also enforced on the replay path so that
    a crafted frame cannot bypass the live-write guard.
    """
    log_path = _store_path(tmp_path)
    store = _open_store(evidence_store, log_path)
    issuer, grant = _make_grant(security_capability)
    subject = _subject()
    finding = _finding()

    report = _report(subject, finding)
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-r4-replay-report",
        expected_subject=subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    del store  # close before replay injection

    # Inject a raw assessment frame with wrong fingerprint directly into the log.
    bad_assessment = {
        "schema_version": 1,
        "assessment_id": "assessment-r4-replay",
        "finding_id": "finding-t4-bridge",
        "report_id": "report-t4-bridge",
        "review_subject_fingerprint": "wrong-fp-replay",
        "assessment": "indeterminate",
        "evidence_refs": [],
        "lineage": {"predicate_version": "v1"},
    }
    tx = evidence_store._build_transaction(
        "tx-r4-replay", [bad_assessment["assessment_id"]], "acceptance-fp-t4-bridge",
        [bad_assessment],
    )
    frame_bytes = evidence_store._serialize_frame(tx, [bad_assessment])
    with log_path.open("ab") as f:
        f.write(frame_bytes)

    with pytest.raises(evidence_store.EvidenceStoreError) as exc_info:
        store2 = evidence_store.EvidenceStore(log_path)
        store2.open()
    assert "denied-incomplete-review-assessment-delta" in str(exc_info.value), (
        "R4 replay: EvidenceStoreError must name denied-incomplete-review-assessment-delta"
    )
