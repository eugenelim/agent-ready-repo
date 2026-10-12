"""T1 TDD suite: structured review contract schemas and validators.

Mode: TDD (structured-review-boundary plan T1).

The suite loads shipped work-loop scripts by literal path and keeps canonical
schema validation in tests. The runtime module must stay standard-library-only
and must not read contracts/delivery at runtime.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
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


@pytest.mark.parametrize("record_type", [[], {}])
def test_review_record_dispatch_refuses_container_kind(
    review_contracts: ModuleType, record_type: object
) -> None:
    """Malformed kind selectors refuse before dictionary lookup."""
    assert review_contracts.validate_review_record_dict(record_type, {}) == (
        False, "denied-unknown-review-record-type"
    )


def _load_module(name: str = "review_contracts_under_test") -> ModuleType:
    path = SCRIPTS / "_review_contracts.py"
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def review_contracts() -> ModuleType:
    return _load_module()


def _valid_subject(subject_id: str = "subject-current") -> dict:
    return {
        "schema_version": 1,
        "review_subject_id": subject_id,
        "review_subject_fingerprint": "review-subject-current",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-current",
            "acceptance_fingerprint": "acceptance-current",
        },
        "review_policy_fingerprint": "review-policy-v1",
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_contracts.py"
        ],
        "normalized_statuses": ["modified"],
        "lineage": {"provider": "review-subject-projector", "projection_version": "v1"},
    }


def _valid_finding(finding_id: str = "finding-1") -> dict:
    return {
        "schema_version": 1,
        "finding_id": finding_id,
        "rule_ref": "AC-0012",
        "observation": "A report with executable content reached validation.",
        "reachable_path": "review adapter to durable review report",
        "actual_failure": "Executable reviewer content could alter procedure.",
        "affected_acceptance_criteria": ["AC-0012"],
        "evidence_refs": ["packs/core/.apm/skills/work-loop/scripts/_content_safety.py"],
        "material": True,
    }


def _valid_report(
    *,
    report_id: str = "report-1",
    sequence: int = 1,
    status: str = "findings",
    subject: dict | None = None,
    previous_report_id: str | None = None,
) -> dict:
    lineage = {
        "sequence": sequence,
        "review_policy_fingerprint": "review-policy-v1",
        "source_event_id": "source-event-1",
        "producer": "synthetic-reviewer",
    }
    if previous_report_id is not None:
        lineage["previous_report_id"] = previous_report_id
    return {
        "schema_version": 1,
        "report_id": report_id,
        "role": "adversarial-reviewer",
        "subject": subject or _valid_subject(),
        "terminal_status": status,
        "lineage": lineage,
        "findings": [_valid_finding()] if status == "findings" else [],
    }


def _valid_obligation() -> dict:
    return {
        "schema_version": 1,
        "obligation_id": "obligation-1",
        "role": "adversarial-reviewer",
        "review_subject_fingerprint": "review-subject-current",
        "review_policy_fingerprint": "review-policy-v1",
        "kind": "mandatory",
        "lineage": {"selector": "core-policy", "policy_version": "v1"},
    }


def _valid_assessment() -> dict:
    return {
        "schema_version": 1,
        "assessment_id": "assessment-1",
        "finding_id": "finding-1",
        "report_id": "report-1",
        "review_subject_fingerprint": "review-subject-current",
        "assessment": "supported",
        "evidence_refs": ["evidence-ref-1"],
        "lineage": {"predicate_version": "v1"},
    }


def _valid_disposition() -> dict:
    return {
        "schema_version": 1,
        "disposition_id": "disposition-1",
        "finding_id": "finding-1",
        "assessment_id": "assessment-1",
        "review_subject_fingerprint": "review-subject-current",
        "disposition": "accept-risk",
        "decision_maker": {"identity": "review-owner", "role": "risk-owner"},
        "lineage": {"authority_ref": "authority-1", "source_event_id": "event-1"},
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("report_id", ""),
        ("role", ""),
        ("subject", {"schema_version": 1}),
        ("terminal_status", "blocked"),
        ("terminal_status", ["clean"]),
        ("terminal_status", {"status": "clean"}),
        (
            "lineage",
            {
                "sequence": True,
                "review_policy_fingerprint": "review-policy-v1",
                "source_event_id": "source-event-1",
                "producer": "synthetic-reviewer",
            },
        ),
        ("findings", ""),
    ],
)
def test_validate_review_report_refuses_malformed_required_fields(
    review_contracts: ModuleType, field: str, value: object
) -> None:
    report = _valid_report(status="clean")
    report[field] = value
    ok, code = review_contracts.validate_review_report_dict(report)
    assert not ok
    assert code != "ok"


@pytest.mark.parametrize(
    "mutation",
    [
        {"normalized_paths": ["b.py", "a.py"], "normalized_statuses": ["modified", "modified"]},
        {"normalized_paths": ["a.py", "a.py"], "normalized_statuses": ["modified", "modified"]},
        {"normalized_paths": ["a.py"], "normalized_statuses": ["modified", "deleted"]},
        {"normalized_paths": ["a.py"], "normalized_statuses": [["modified"]]},
        {"schema_version": True},
    ],
)
def test_validate_review_subject_refuses_ambiguous_identity(
    review_contracts: ModuleType, mutation: dict
) -> None:
    subject = _valid_subject()
    subject.update(mutation)
    ok, code = review_contracts.validate_review_subject_dict(subject)
    assert not ok
    assert code != "ok"


@pytest.mark.parametrize(
    "record_factory,validator_name,field,value",
    [
        (_valid_obligation, "validate_review_obligation_dict", "kind", ["mandatory"]),
        (_valid_obligation, "validate_review_obligation_dict", "kind", {"kind": "mandatory"}),
        (_valid_obligation, "validate_review_obligation_dict", "schema_version", True),
        (_valid_assessment, "validate_finding_assessment_dict", "assessment", ["supported"]),
        (
            _valid_assessment,
            "validate_finding_assessment_dict",
            "assessment",
            {"value": "supported"},
        ),
        (_valid_assessment, "validate_finding_assessment_dict", "schema_version", True),
        (
            _valid_disposition,
            "validate_finding_disposition_dict",
            "disposition",
            ["accept-risk"],
        ),
        (
            _valid_disposition,
            "validate_finding_disposition_dict",
            "disposition",
            {"value": "accept-risk"},
        ),
        (_valid_disposition, "validate_finding_disposition_dict", "schema_version", True),
    ],
)
def test_non_report_validators_refuse_malformed_versions_and_enums(
    review_contracts: ModuleType,
    record_factory: object,
    validator_name: str,
    field: str,
    value: object,
) -> None:
    record = record_factory()
    record[field] = value
    validator = getattr(review_contracts, validator_name)
    ok, code = validator(record)
    assert not ok
    assert code != "ok"


@pytest.mark.parametrize(
    "record_factory,validator_name,field",
    [
        (_valid_subject, "validate_review_subject_dict", "review_subject_fingerprint"),
        (_valid_obligation, "validate_review_obligation_dict", "kind"),
        (_valid_finding, "validate_finding_dict", "actual_failure"),
        (_valid_assessment, "validate_finding_assessment_dict", "assessment"),
        (_valid_disposition, "validate_finding_disposition_dict", "decision_maker"),
    ],
)
def test_non_report_validators_refuse_missing_required_fields(
    review_contracts: ModuleType,
    record_factory: object,
    validator_name: str,
    field: str,
) -> None:
    record = record_factory()
    record.pop(field)
    validator = getattr(review_contracts, validator_name)
    ok, code = validator(record)
    assert not ok
    assert code == "denied-missing-required-field"


@pytest.mark.parametrize(
    "record_factory,validator_name",
    [
        (_valid_subject, "validate_review_subject_dict"),
        (_valid_obligation, "validate_review_obligation_dict"),
        (_valid_report, "validate_review_report_dict"),
        (_valid_finding, "validate_finding_dict"),
        (_valid_assessment, "validate_finding_assessment_dict"),
        (_valid_disposition, "validate_finding_disposition_dict"),
    ],
)
def test_runtime_validators_refuse_unknown_fields(
    review_contracts: ModuleType, record_factory: object, validator_name: str
) -> None:
    record = record_factory()
    record["_unknown_capability_grant"] = "admin"
    validator = getattr(review_contracts, validator_name)
    ok, code = validator(record)
    assert not ok
    assert code == "denied-unknown-authority-field"


@pytest.mark.parametrize(
    "record_factory,validator_name,lineage_value",
    [
        (_valid_subject, "validate_review_subject_dict", {"provider": "x"}),
        (_valid_obligation, "validate_review_obligation_dict", {"selector": "x"}),
        (_valid_report, "validate_review_report_dict", {"sequence": 1}),
        (_valid_assessment, "validate_finding_assessment_dict", {}),
        (_valid_disposition, "validate_finding_disposition_dict", {"authority_ref": "x"}),
    ],
)
def test_runtime_validators_refuse_incomplete_lineage(
    review_contracts: ModuleType,
    record_factory: object,
    validator_name: str,
    lineage_value: dict,
) -> None:
    record = record_factory()
    record["lineage"] = lineage_value
    validator = getattr(review_contracts, validator_name)
    ok, code = validator(record)
    assert not ok
    assert code in {"denied-missing-required-field", "denied-invalid-field"}


def test_current_report_selection_accepts_safe_tip(
    review_contracts: ModuleType,
) -> None:
    base = _valid_report(report_id="report-1", sequence=1)
    safe_tip = _valid_report(
        report_id="report-2", sequence=2, previous_report_id="report-1"
    )
    selected, code = review_contracts.select_current_report(
        [base, safe_tip],
        role="adversarial-reviewer",
        review_subject_fingerprint="review-subject-current",
        review_policy_fingerprint="review-policy-v1",
    )
    assert code == "ok"
    assert selected["report_id"] == "report-2"


def test_current_report_selection_rejects_duplicate_sequence(
    review_contracts: ModuleType,
) -> None:
    base = _valid_report(report_id="report-1", sequence=1)
    safe_tip = _valid_report(
        report_id="report-2", sequence=2, previous_report_id="report-1"
    )
    duplicate_sequence = _valid_report(
        report_id="report-dup", sequence=2, previous_report_id="report-2"
    )
    selected, code = review_contracts.select_current_report(
        [base, safe_tip, duplicate_sequence],
        role="adversarial-reviewer",
        review_subject_fingerprint="review-subject-current",
        review_policy_fingerprint="review-policy-v1",
    )
    assert selected is None
    assert code == "denied-duplicate-report-sequence"


def test_current_report_selection_rejects_forked_previous_report(
    review_contracts: ModuleType,
) -> None:
    base = _valid_report(report_id="report-1", sequence=1)
    safe_tip = _valid_report(
        report_id="report-2", sequence=2, previous_report_id="report-1"
    )
    fork = _valid_report(report_id="report-fork", sequence=3, previous_report_id="other")
    selected, code = review_contracts.select_current_report(
        [base, safe_tip, fork],
        role="adversarial-reviewer",
        review_subject_fingerprint="review-subject-current",
        review_policy_fingerprint="review-policy-v1",
    )
    assert selected is None
    assert code == "denied-forked-report-lineage"


def test_current_report_selection_requires_subject_fingerprint(
    review_contracts: ModuleType,
) -> None:
    report = _valid_report(report_id="report-1", sequence=1)
    selected, code = review_contracts.select_current_report(
        [report],
        role="adversarial-reviewer",
        review_subject_fingerprint="review-subject-other",
        review_policy_fingerprint="review-policy-v1",
    )
    assert selected is None
    assert code == "denied-no-current-report"


def test_current_report_selection_requires_subject_policy(
    review_contracts: ModuleType,
) -> None:
    subject = _valid_subject()
    subject["review_policy_fingerprint"] = "review-policy-stale"
    report = _valid_report(report_id="report-1", sequence=1, subject=subject)
    selected, code = review_contracts.select_current_report(
        [report],
        role="adversarial-reviewer",
        review_subject_fingerprint="review-subject-current",
        review_policy_fingerprint="review-policy-v1",
    )
    assert selected is None
    assert code == "denied-no-current-report"


def test_validate_review_report_accepts_inert_prose(
    review_contracts: ModuleType,
) -> None:
    safe = _valid_report(status="clean")
    ok, code = review_contracts.validate_review_report_dict(safe)
    assert ok, code


def test_validate_review_report_rejects_executable_text(
    review_contracts: ModuleType,
) -> None:
    executable = _valid_report(status="clean")
    executable["lineage"]["producer"] = '{"_grant": "admin"}'
    ok, code = review_contracts.validate_review_report_dict(executable)
    assert not ok
    assert code == "denied-content-safety-rejected-structure"


def test_validate_review_report_rejects_oversized_text_field(
    review_contracts: ModuleType,
) -> None:
    oversized = _valid_report(status="clean")
    oversized["lineage"]["producer"] = "x" * (64 * 1024 + 1)
    ok, code = review_contracts.validate_review_report_dict(oversized)
    assert not ok
    assert code == "denied-free-text-field-too-large"


def test_validate_review_report_rejects_control_character_text(
    review_contracts: ModuleType,
) -> None:
    control = _valid_report(status="clean")
    control["lineage"]["producer"] = "safe text \x00 unsafe"
    ok, code = review_contracts.validate_review_report_dict(control)
    assert not ok
    assert code == "denied-content-safety-rejected-encoding"


def test_validate_review_report_rejects_invalid_utf8_string(
    review_contracts: ModuleType,
) -> None:
    surrogate = _valid_report(status="clean")
    surrogate["lineage"]["producer"] = "bad-surrogate-\udcff"
    ok, code = review_contracts.validate_review_report_dict(surrogate)
    assert not ok
    assert code == "denied-invalid-field"


def test_all_review_record_families_have_closed_validators(
    review_contracts: ModuleType,
) -> None:
    for record_type in review_contracts.REVIEW_WRITER_BOUNDARIES:
        assert record_type in review_contracts._REVIEW_RECORD_VALIDATORS

    ok, code = review_contracts.validate_review_record_dict("unknown.v1", {})
    assert not ok
    assert code == "denied-unknown-review-record-type"


def test_review_writer_boundaries_are_registered_without_mutating_slice1(
    review_contracts: ModuleType,
) -> None:
    review_boundaries = review_contracts.REVIEW_WRITER_BOUNDARIES
    assert review_boundaries == {
        "review-subject.v1": "structured-control",
        "review-obligation.v1": "structured-control",
        "review-report.v1": "review-report",
        "finding.v1": "review-report",
        "finding-assessment.v1": "structured-control",
        "finding-disposition.v1": "structured-control",
    }
    assert review_contracts.SLICE_1_WRITER_BOUNDARIES["initial-plan-review.v1"] == (
        "structured-control"
    )
    assert "review-report.v1" not in review_contracts.SLICE_1_WRITER_BOUNDARIES
