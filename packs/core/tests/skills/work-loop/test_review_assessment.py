"""T4 construction tests for actual-failure assessment.

Mode: TDD (structured-review-boundary plan T4).

The suite loads shipped work-loop scripts by literal path. Runtime assessment
must stay standard-library-only and derive assessment records from current
structured reports before the bridge writes Slice 1 evidence receipts.
"""

from __future__ import annotations

import copy
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


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path for pack-boundary tests."""
    if not path.exists():
        pytest.fail(f"T4 review assessment module is not implemented: {path.name}")
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
def review_assessment() -> ModuleType:
    """Load the T4 actual-failure evaluator."""
    return _load_module(
        "review_assessment_under_test", SCRIPTS / "_review_assessment.py"
    )


@pytest.fixture(scope="module")
def review_contracts() -> ModuleType:
    """Load the T1 review contract validators."""
    return _load_module("review_contracts_t4", SCRIPTS / "_review_contracts.py")


def _review_subject() -> dict:
    """Build the current review subject used by the finding fixtures."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-t4-current",
        "review_subject_fingerprint": "review-subject-fp-t4-current",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-t4-current",
            "acceptance_fingerprint": "acceptance-fp-t4-current",
        },
        "normalized_paths": [
            "packs/core/.apm/skills/work-loop/scripts/_review_assessment.py"
        ],
        "normalized_statuses": ["added"],
        "review_policy_fingerprint": "review-policy-t4-current",
        "lineage": {
            "provider": "structured-review-boundary-test",
            "projection_version": "1.0",
        },
    }


def _finding(**overrides: object) -> dict:
    """Build a valid structured finding."""
    finding = {
        "schema_version": 1,
        "finding_id": "finding-t4-actual-failure",
        "rule_ref": "AC-0006",
        "observation": "A supported finding needs a controlled observation.",
        "reachable_path": "current report to affected criterion",
        "actual_failure": "The affected criterion can be contradicted by the review failure.",
        "affected_acceptance_criteria": ["AC-0006"],
        "evidence_refs": [
            "evidence:observation",
            "evidence:reachable-path",
            "evidence:actual-failure",
        ],
        "material": True,
    }
    finding.update(overrides)
    return finding


def _report(subject: dict, finding: dict) -> dict:
    """Build a current findings report containing one finding."""
    return {
        "schema_version": 1,
        "report_id": "report-t4-current",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": "source-report-t4-current",
            "producer": "synthetic-reviewer",
        },
        "findings": [copy.deepcopy(finding)],
    }


def _base_kwargs(subject: dict, finding: dict, *, assessment_id: str) -> dict:
    """Return the current controlled context for a supported assessment."""
    return {
        "assessment_id": assessment_id,
        "current_subject": subject,
        "current_report_id": "report-t4-current",
        "current_rule_refs": {finding["rule_ref"]},
        "current_evidence_refs": set(finding["evidence_refs"]) | {"evidence:authority"},
        "controlled_facts": {"falsifiable-delivery-failure": True},
        "controlled_edges": {
            "rule-to-observation": ["evidence:observation"],
            "observation-to-reachable-path": ["evidence:reachable-path"],
            "reachable-path-to-actual-failure": ["evidence:actual-failure"],
        },
        "predicate_version": "slice2-t4-v1",
    }


def _assert_valid_inputs(
    review_contracts: ModuleType,
    subject: dict,
    finding: dict,
    report: dict,
) -> None:
    """Assert fixture setup reaches the T4 evaluator as valid T1 records."""
    assert review_contracts.validate_review_subject_dict(subject) == (True, "ok")
    assert review_contracts.validate_finding_dict(finding) == (True, "ok")
    assert review_contracts.validate_review_report_dict(report) == (True, "ok")


def _assert_assessment(
    review_contracts: ModuleType,
    assessment: dict,
    *,
    assessment_id: str,
    finding_id: str,
    report_id: str = "report-t4-current",
    outcome: str,
    evidence_refs: list[str],
    judgment_authority: str | None = None,
) -> None:
    """Assert an assessment record's shape and validator conformance."""
    lineage = {"predicate_version": "slice2-t4-v1"}
    if judgment_authority is not None:
        lineage["judgment_authority"] = judgment_authority
    assert assessment == {
        "schema_version": 1,
        "assessment_id": assessment_id,
        "finding_id": finding_id,
        "report_id": report_id,
        "review_subject_fingerprint": "review-subject-fp-t4-current",
        "assessment": outcome,
        "evidence_refs": evidence_refs,
        "lineage": lineage,
    }
    assert review_contracts.validate_finding_assessment_dict(assessment) == (True, "ok")


def test_supported_finding_requires_controlled_evidence_for_every_reachability_edge(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A supported assessment records the current actual-failure chain."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-supported-1"),
    )

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-supported-1",
        finding_id="finding-t4-actual-failure",
        outcome="supported",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )


def test_opinion_without_falsifiable_delivery_failure_is_unsupported(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A preference claim stays out of disposition as unsupported opinion."""
    subject = _review_subject()
    finding = _finding(
        finding_id="finding-t4-opinion",
        rule_ref="AC-0007",
        observation="The implementation style feels too indirect.",
        reachable_path="style preference only; no path to an acceptance failure",
        actual_failure=(
            "The reviewer preference names no falsifiable delivery failure."
        ),
        affected_acceptance_criteria=["AC-0007"],
        evidence_refs=["evidence:opinion"],
    )
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-opinion-1")
    kwargs["controlled_facts"] = {"falsifiable-delivery-failure": False}
    kwargs["controlled_edges"] = {}
    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **kwargs,
    )

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-opinion-1",
        finding_id="finding-t4-opinion",
        outcome="unsupported-opinion",
        evidence_refs=["evidence:opinion"],
    )


def test_duplicate_requires_same_failure_current_finding_on_same_subject(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Only the same failure on the same current subject is a duplicate."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)

    # Build a schema-valid source_report containing the existing duplicate finding.
    # The duplicate finding has a different finding_id but the same actual_failure.
    existing_source_finding = _finding(
        finding_id="finding-t4-existing",
        actual_failure=finding["actual_failure"],
    )
    existing_source_report = {
        "schema_version": 1,
        "report_id": "report-t4-current",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": "source-report-t4-duplicate",
            "producer": "synthetic-reviewer",
        },
        "findings": [copy.deepcopy(existing_source_finding)],
    }
    ok, _ = review_contracts.validate_review_report_dict(existing_source_report)
    assert ok, "existing_source_report fixture must be schema-valid"

    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-duplicate-1"),
        current_duplicate_finding={
            "finding_id": "finding-t4-existing",
            "report_id": "report-t4-current",
            "actual_failure": finding["actual_failure"],
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
            "current": True,
            "source_report": copy.deepcopy(existing_source_report),
            "source_finding": copy.deepcopy(existing_source_finding),
        },
    )
    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-duplicate-1",
        finding_id="finding-t4-actual-failure",
        outcome="unsupported-duplicate",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )

    not_same_subject = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-not-duplicate-1"),
        current_duplicate_finding={
            "finding_id": "finding-t4-existing",
            "report_id": "report-t4-current",
            "actual_failure": finding["actual_failure"],
            "review_subject_fingerprint": "other-subject",
            "current": True,
            "source_report": copy.deepcopy(existing_source_report),
            "source_finding": copy.deepcopy(existing_source_finding),
        },
    )
    assert not_same_subject["assessment"] == "supported"


@pytest.mark.parametrize(
    "case,changes",
    [
        ("report", {"current_report_id": "report-replaced"}),
        ("rule", {"current_rule_refs": {"AC-9999"}}),
        ("evidence", {"current_evidence_refs": {"evidence:observation"}}),
        ("subject", {"subject_fingerprint": "review-subject-fp-replaced"}),
    ],
)
def test_stale_report_rule_evidence_or_subject_is_unsupported(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
    case: str,
    changes: dict,
) -> None:
    """Any noncurrent input yields unsupported-stale before disposition."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    current_subject = copy.deepcopy(subject)
    if "subject_fingerprint" in changes:
        current_subject["review_subject_fingerprint"] = changes["subject_fingerprint"]
    kwargs = _base_kwargs(subject, finding, assessment_id=f"assessment-t4-stale-{case}")
    kwargs["current_subject"] = current_subject
    for key, value in changes.items():
        if key != "subject_fingerprint":
            kwargs[key] = value

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id=f"assessment-t4-stale-{case}",
        finding_id="finding-t4-actual-failure",
        outcome="unsupported-stale",
        evidence_refs=(
            ["evidence:observation"]
            if case == "evidence"
            else [
                "evidence:actual-failure",
                "evidence:observation",
                "evidence:reachable-path",
            ]
        ),
    )


def test_controlled_elsewhere_requires_every_cited_path_blocked(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A current control over every cited path makes the finding non-blocking."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-controlled-1")
    kwargs["controlled_facts"] = {
        "falsifiable-delivery-failure": True,
        "all-cited-paths-blocked": True,
    }
    kwargs["controlled_path_facts"] = [
        {
            "path_ref": "evidence:observation",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:observation",
        },
        {
            "path_ref": "evidence:reachable-path",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:reachable-path",
        },
        {
            "path_ref": "evidence:actual-failure",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:actual-failure",
        },
    ]

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-controlled-1",
        finding_id="finding-t4-actual-failure",
        outcome="unsupported-controlled-elsewhere",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )


@pytest.mark.parametrize(
    "controlled_edges",
    [
        {},
        {
            "rule-to-observation": ["evidence:observation"],
            "observation-to-reachable-path": None,
            "reachable-path-to-actual-failure": ["evidence:actual-failure"],
        },
    ],
)
def test_undecidable_edge_without_current_authority_is_indeterminate(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
    controlled_edges: dict,
) -> None:
    """Evidence that cannot decide an edge leaves the assessment indeterminate."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-indeterminate-1")
    kwargs["controlled_edges"] = controlled_edges

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-indeterminate-1",
        finding_id="finding-t4-actual-failure",
        outcome="indeterminate",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )


def test_named_independent_authority_only_resolves_mechanical_indeterminate(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Independent authority cannot override a decidable unsupported class."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-authority-1")
    kwargs["controlled_edges"] = {}
    kwargs["independent_authority"] = {
        "authority_ref": "authority:review-assessment",
        "requested_judgment": "supported",
        "edge_evidence_refs": ["evidence:authority"],
        "predicate_judgments": {"falsifiable-delivery-failure": True},
        "rationale": "The named authority decides the missing reachability edge.",
        "current": True,
    }

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-authority-1",
        finding_id="finding-t4-actual-failure",
        outcome="supported",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:authority",
            "evidence:observation",
            "evidence:reachable-path",
        ],
        judgment_authority="authority:review-assessment",
    )

    opinion = _finding(
        finding_id="finding-t4-authority-opinion",
        rule_ref="AC-0007",
        observation="The implementation style feels too indirect.",
        reachable_path="style preference only; no path to an acceptance failure",
        actual_failure="The reviewer preference names no falsifiable delivery failure.",
        affected_acceptance_criteria=["AC-0007"],
        evidence_refs=["evidence:opinion"],
    )
    opinion_report = _report(subject, opinion)
    _assert_valid_inputs(review_contracts, subject, opinion, opinion_report)
    opinion_kwargs = _base_kwargs(
        subject, opinion, assessment_id="assessment-t4-authority-opinion-1"
    )
    opinion_kwargs["controlled_facts"] = {"falsifiable-delivery-failure": False}
    opinion_kwargs["controlled_edges"] = {}
    opinion_kwargs["independent_authority"] = kwargs["independent_authority"]
    opinion_assessment = review_assessment.assess_finding_actual_failure(
        opinion_report,
        opinion,
        **opinion_kwargs,
    )
    assert opinion_assessment["assessment"] == "unsupported-opinion"
    assert "judgment_authority" not in opinion_assessment["lineage"]


@pytest.mark.parametrize(
    "bad_kwargs,denial_code",
    [
        ({"controlled_facts": {"falsifiable-delivery-failure": "yes"}}, "denied-invalid-controlled-fact"),
        ({"controlled_facts": {"preference": True}}, "denied-unknown-controlled-fact"),
        ({"controlled_edges": {"unknown-edge": ["evidence:observation"]}}, "denied-unknown-reachability-edge"),
    ],
)
def test_assessment_context_refuses_non_closed_control_inputs(
    review_assessment: ModuleType,
    bad_kwargs: dict,
    denial_code: str,
) -> None:
    """Context controls are explicit booleans and closed edge names."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-refused-1")
    kwargs.update(bad_kwargs)

    with pytest.raises(review_assessment.ReviewAssessmentRefused) as exc_info:
        review_assessment.assess_finding_actual_failure(report, finding, **kwargs)
    assert exc_info.value.denial_code == denial_code


def test_finding_must_be_the_claim_embedded_in_the_current_report(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """The evaluator refuses a valid but unrelated finding."""
    subject = _review_subject()
    embedded = _finding()
    unrelated = _finding(
        finding_id="finding-t4-unrelated",
        actual_failure="A different failure is not in the report.",
    )
    report = _report(subject, embedded)
    _assert_valid_inputs(review_contracts, subject, unrelated, report)

    with pytest.raises(review_assessment.ReviewAssessmentRefused) as exc_info:
        review_assessment.assess_finding_actual_failure(
            report,
            unrelated,
            **_base_kwargs(subject, unrelated, assessment_id="assessment-t4-unrelated-1"),
        )
    assert exc_info.value.denial_code == "denied-finding-not-in-current-report"


def test_duplicate_candidate_needs_current_report_and_finding_identity(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A same-text failure is not a duplicate without a valid current binding."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)

    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-malformed-duplicate-1"),
        current_duplicate_finding={
            "actual_failure": finding["actual_failure"],
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
        },
    )

    assert assessment["assessment"] == "supported"


def test_duplicate_can_be_current_same_subject_across_report_or_role(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A duplicate is proved by a current source fact, not by same report ID."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    duplicate_finding = _finding(finding_id="finding-t4-existing-cross-role")
    duplicate_report = _report(subject, duplicate_finding)
    duplicate_report["report_id"] = "report-t4-cross-role"
    duplicate_report["role"] = "adversarial-reviewer"
    _assert_valid_inputs(review_contracts, subject, finding, report)
    _assert_valid_inputs(review_contracts, subject, duplicate_finding, duplicate_report)

    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-cross-report-duplicate"),
        current_duplicate_finding={
            "finding_id": duplicate_finding["finding_id"],
            "report_id": duplicate_report["report_id"],
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
            "actual_failure": duplicate_finding["actual_failure"],
            "source_report": duplicate_report,
            "source_finding": duplicate_finding,
            "current": True,
        },
    )

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-cross-report-duplicate",
        finding_id="finding-t4-actual-failure",
        outcome="unsupported-duplicate",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )


@pytest.mark.parametrize(
    "candidate",
    [
        {
            "finding_id": "",
            "report_id": "report-t4-cross-role",
            "actual_failure": "The affected criterion can be contradicted by the review failure.",
            "review_subject_fingerprint": "review-subject-fp-t4-current",
            "current": True,
        },
        {
            "finding_id": "finding-t4-existing-cross-role",
            "report_id": "report-t4-cross-role",
            "actual_failure": "The affected criterion can be contradicted by the review failure.",
            "review_subject_fingerprint": "review-subject-fp-t4-current",
            "current": False,
        },
        {
            "finding_id": "finding-t4-existing-cross-role",
            "report_id": "report-t4-cross-role",
            "actual_failure": "The affected criterion can be contradicted by the review failure.",
            "review_subject_fingerprint": "review-subject-fp-t4-current",
            "source_report": {"report_id": "report-t4-cross-role"},
            "current": True,
        },
    ],
)
def test_duplicate_candidate_requires_valid_current_source_binding(
    review_assessment: ModuleType,
    candidate: dict,
) -> None:
    """Malformed or stale duplicate facts cannot close a finding."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)

    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-bad-duplicate-source"),
        current_duplicate_finding=candidate,
    )

    assert assessment["assessment"] == "supported"


def test_controlled_elsewhere_requires_verified_current_control_for_every_path(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Partial or stale controls do not make a finding controlled elsewhere."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-partial-control-1")
    kwargs["controlled_facts"] = {"falsifiable-delivery-failure": True}
    kwargs["controlled_path_facts"] = [
        {
            "path_ref": "evidence:observation",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:observation",
        },
        {
            "path_ref": "evidence:reachable-path",
            "blocked": False,
            "current": True,
            "evidence_ref": "evidence:reachable-path",
        },
        {
            "path_ref": "evidence:actual-failure",
            "blocked": True,
            "current": False,
            "evidence_ref": "evidence:actual-failure",
        },
    ]

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    assert assessment["assessment"] == "supported"


def test_aggregate_control_boolean_without_verified_paths_is_not_sufficient(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """An aggregate control fact cannot stand in for per-path proof."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-aggregate-control-1")
    kwargs["controlled_facts"] = {
        "falsifiable-delivery-failure": True,
        "all-cited-paths-blocked": True,
    }

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    assert assessment["assessment"] == "supported"


def test_controlled_elsewhere_is_not_vacuously_true_without_cited_evidence(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Empty cited evidence cannot satisfy the every-path control row."""
    subject = _review_subject()
    finding = _finding(evidence_refs=[])
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-empty-path-control")
    # Include all edge evidence refs so stale_edges is False and the controlled-elsewhere
    # row is actually evaluated (previously {"evidence:authority"} caused stale_edges=True).
    kwargs["current_evidence_refs"] = {
        "evidence:observation",
        "evidence:reachable-path",
        "evidence:actual-failure",
        "evidence:authority",
    }
    kwargs["controlled_facts"] = {
        "falsifiable-delivery-failure": True,
        "all-cited-paths-blocked": True,
    }
    kwargs["controlled_path_facts"] = []

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    assert assessment["assessment"] != "unsupported-controlled-elsewhere"


def test_independent_authority_records_requested_judgment_and_rationale(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Authority over a mechanical gap records its requested judgment."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-authority-requested-1")
    kwargs["controlled_edges"] = {}
    kwargs["independent_authority"] = {
        "authority_ref": "authority:review-assessment",
        "requested_judgment": "indeterminate",
        "edge_evidence_refs": ["evidence:authority"],
        "rationale": "The reachability edge remains mechanically undecidable.",
        "current": True,
    }

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-authority-requested-1",
        finding_id="finding-t4-actual-failure",
        outcome="indeterminate",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:authority",
            "evidence:observation",
            "evidence:reachable-path",
        ],
        judgment_authority="authority:review-assessment",
    )


def test_authority_cannot_support_without_deciding_missing_falsifiability_fact(
    review_assessment: ModuleType,
) -> None:
    """A missing falsifiability fact remains indeterminate without that judgment."""
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-authority-fact-1")
    kwargs["controlled_facts"] = {}
    kwargs["controlled_edges"] = {}
    kwargs["independent_authority"] = {
        "authority_ref": "authority:review-assessment",
        "requested_judgment": "supported",
        "edge_evidence_refs": ["evidence:authority"],
        "rationale": "Only the edge was reviewed.",
        "current": True,
    }

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    assert assessment["assessment"] == "indeterminate"


# ── Mutation-repair: single-guard isolation tests ─────────────────────────────


def test_stale_finding_evidence_only_is_unsupported_stale(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Finding evidence not in current_evidence_refs yields unsupported-stale.

    Isolates MUT-004: the finding-evidence staleness line
    ``or any(ref not in current_evidence for ref in safe_finding["evidence_refs"])``.
    All edge evidence is current; only the extra finding evidence ref is stale.
    """
    subject = _review_subject()
    # Add one extra evidence_ref that will be absent from current_evidence_refs.
    finding = _finding(
        finding_id="finding-t4-stale-finding-ev",
        evidence_refs=[
            "evidence:observation",
            "evidence:reachable-path",
            "evidence:actual-failure",
            "evidence:stale-finding-ref",
        ],
    )
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-stale-finding-ev")
    # Edge refs are all current; only the extra finding ref is absent.
    kwargs["current_evidence_refs"] = {
        "evidence:observation",
        "evidence:reachable-path",
        "evidence:actual-failure",
        "evidence:authority",
    }

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-stale-finding-ev",
        finding_id="finding-t4-stale-finding-ev",
        outcome="unsupported-stale",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )


def test_stale_edge_evidence_only_is_unsupported_stale(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Edge evidence not in current_evidence_refs yields unsupported-stale.

    Isolates MUT-005: the edge-staleness line ``or stale_edges``.
    All finding evidence_refs are current; one edge carries a stale ref.
    """
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-stale-edge-ev")
    # All finding refs are in current_evidence_refs; add a stale ref to one edge.
    kwargs["current_evidence_refs"] = set(finding["evidence_refs"]) | {"evidence:authority"}
    kwargs["controlled_edges"] = {
        "rule-to-observation": ["evidence:observation", "evidence:stale-edge-ref"],
        "observation-to-reachable-path": ["evidence:reachable-path"],
        "reachable-path-to-actual-failure": ["evidence:actual-failure"],
    }

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    _assert_assessment(
        review_contracts,
        assessment,
        assessment_id="assessment-t4-stale-edge-ev",
        finding_id="finding-t4-actual-failure",
        outcome="unsupported-stale",
        evidence_refs=[
            "evidence:actual-failure",
            "evidence:observation",
            "evidence:reachable-path",
        ],
    )


def test_duplicate_candidate_empty_finding_id_with_valid_source_is_not_duplicate(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """An empty finding_id cannot constitute a same-failure duplicate.

    Isolates MUT-012: the finding-id non-empty guard
    ``if not isinstance(finding_id_val, str) or not finding_id_val: return False``.
    The candidate has a valid source binding and current=True; only the finding_id
    is empty.
    """
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)

    dup_finding = _finding(finding_id="finding-t4-dup-mut012")
    dup_report = _report(subject, dup_finding)
    dup_report["report_id"] = "report-t4-dup-mut012"
    dup_report["role"] = "adversarial-reviewer"
    ok, _ = review_contracts.validate_review_report_dict(dup_report)
    assert ok, "dup_report must be schema-valid for MUT-012 isolation"

    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-mut012"),
        current_duplicate_finding={
            "finding_id": "",
            "report_id": dup_report["report_id"],
            "actual_failure": finding["actual_failure"],
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
            "current": True,
            "source_report": copy.deepcopy(dup_report),
            "source_finding": copy.deepcopy(dup_finding),
        },
    )

    assert assessment["assessment"] == "supported"


def test_duplicate_candidate_not_current_with_valid_source_is_not_duplicate(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A non-current candidate cannot constitute a same-failure duplicate.

    Isolates MUT-013: the current flag guard
    ``if duplicate_finding.get("current") is not True: return False``.
    The candidate has a valid source binding and non-empty finding_id; only
    current is False.
    """
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)

    dup_finding = _finding(finding_id="finding-t4-dup-mut013")
    dup_report = _report(subject, dup_finding)
    dup_report["report_id"] = "report-t4-dup-mut013"
    dup_report["role"] = "adversarial-reviewer"
    ok, _ = review_contracts.validate_review_report_dict(dup_report)
    assert ok, "dup_report must be schema-valid for MUT-013 isolation"

    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        **_base_kwargs(subject, finding, assessment_id="assessment-t4-mut013"),
        current_duplicate_finding={
            "finding_id": dup_finding["finding_id"],
            "report_id": dup_report["report_id"],
            "actual_failure": finding["actual_failure"],
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
            "current": False,
            "source_report": copy.deepcopy(dup_report),
            "source_finding": copy.deepcopy(dup_finding),
        },
    )

    assert assessment["assessment"] == "supported"


def test_controlled_elsewhere_path_must_be_blocked_and_current(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """A path fact with blocked=False prevents the controlled-elsewhere outcome.

    Isolates MUT-018: the per-path blocked/current guard
    ``if fact.get("blocked") is not True or fact.get("current") is not True: return False``.
    The aggregate fact is True, all evidence is current, but one path has blocked=False.
    """
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-mut018")
    kwargs["controlled_facts"] = {
        "falsifiable-delivery-failure": True,
        "all-cited-paths-blocked": True,
    }
    kwargs["controlled_path_facts"] = [
        {
            "path_ref": "evidence:observation",
            "blocked": False,
            "current": True,
            "evidence_ref": "evidence:observation",
        },
        {
            "path_ref": "evidence:reachable-path",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:reachable-path",
        },
        {
            "path_ref": "evidence:actual-failure",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:actual-failure",
        },
    ]

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    assert assessment["assessment"] == "supported"


def test_controlled_elsewhere_requires_aggregate_all_paths_blocked_fact(
    review_assessment: ModuleType,
    review_contracts: ModuleType,
) -> None:
    """Valid per-path facts without the aggregate are insufficient for controlled-elsewhere.

    Isolates MUT-019: the aggregate check
    ``facts.get("all-cited-paths-blocked") is True``.
    All path facts are valid but all-cited-paths-blocked is absent from controlled_facts.
    """
    subject = _review_subject()
    finding = _finding()
    report = _report(subject, finding)
    _assert_valid_inputs(review_contracts, subject, finding, report)
    kwargs = _base_kwargs(subject, finding, assessment_id="assessment-t4-mut019")
    kwargs["controlled_facts"] = {"falsifiable-delivery-failure": True}  # no aggregate
    kwargs["controlled_path_facts"] = [
        {
            "path_ref": "evidence:observation",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:observation",
        },
        {
            "path_ref": "evidence:reachable-path",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:reachable-path",
        },
        {
            "path_ref": "evidence:actual-failure",
            "blocked": True,
            "current": True,
            "evidence_ref": "evidence:actual-failure",
        },
    ]

    assessment = review_assessment.assess_finding_actual_failure(report, finding, **kwargs)

    assert assessment["assessment"] == "supported"
