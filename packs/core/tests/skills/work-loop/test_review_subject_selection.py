"""T2 TDD suite: review subject projection and obligation selection.

Mode: TDD (structured-review-boundary plan T2).

The suite loads shipped work-loop scripts by literal path. Runtime selection
must stay standard-library-only, reuse the T1 review contracts, and leave plan
and task-projection provenance outside review-subject identity.
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


def _load_review_selection_module() -> ModuleType:
    """Load the T2 review-selection script by literal path."""
    path = SCRIPTS / "_review_selection.py"
    if not path.exists():
        pytest.fail(f"T2 selection module is not implemented: {path.name}")
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(
            "review_selection_under_test", str(path)
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def review_selection() -> ModuleType:
    return _load_review_selection_module()


def _delivery_subject(
    *,
    task_revision: str,
    task_hash: str,
    acceptance_fingerprint: str = "acceptance-current",
) -> dict:
    return {
        "schema_version": 1,
        "subject_id": "delivery-subject-current",
        "acceptance_fingerprint": acceptance_fingerprint,
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
        "task_projection_revision": task_revision,
        "task_projection_hash": task_hash,
    }


def _policy() -> dict:
    return {
        "policy_id": "core-review-policy",
        "review_policy_fingerprint": "review-policy-v1",
        "policy_version": "2026-10-07",
        "selector": "core-review-obligation-selector",
        "roles": [
            {"role": "adversarial-reviewer", "kind": "mandatory"},
            {"role": "security-reviewer", "kind": "optional"},
            {"role": "quality-engineer", "kind": "mandatory"},
        ],
        "waivers": [],
    }


def _policy_with_waiver(subject: dict, *, authorized: bool = True) -> dict:
    policy = _policy()
    policy["waivers"] = [
        {
            "waiver_ref": "waiver-1",
            "role": "adversarial-reviewer",
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
            "review_policy_fingerprint": policy["review_policy_fingerprint"],
            "authorized": authorized,
            "current": True,
        }
    ]
    return policy


def _manifest() -> list[dict]:
    return [
        {
            "path": "packs/core/.apm/skills/work-loop/scripts/_review_contracts.py",
            "status": "modified",
        },
        {
            "path": "packs/core/tests/skills/work-loop/test_review_contracts.py",
            "status": "modified",
        },
    ]


def _ordered_obligation_summary(obligations: list[dict]) -> list[tuple[str, str]]:
    return [(item["role"], item["kind"]) for item in obligations]


def _subject(review_selection: ModuleType) -> dict:
    return review_selection.project_review_subject(
        _delivery_subject(task_revision="task-a", task_hash="task-hash-a"),
        changed_paths=_manifest(),
        review_policy_fingerprint="review-policy-v1",
    )


def _subject_for_acceptance(
    review_selection: ModuleType, acceptance_fingerprint: str
) -> dict:
    return review_selection.project_review_subject(
        _delivery_subject(
            task_revision=f"task-{acceptance_fingerprint}",
            task_hash=f"task-hash-{acceptance_fingerprint}",
            acceptance_fingerprint=acceptance_fingerprint,
        ),
        changed_paths=_manifest(),
        review_policy_fingerprint="review-policy-v1",
    )


def _finding(*, finding_id: str = "finding-1", material: bool = True) -> dict:
    return {
        "schema_version": 1,
        "finding_id": finding_id,
        "rule_ref": "AC-0003",
        "observation": "A supported review failure is observable.",
        "reachable_path": "review report to acceptance gate",
        "actual_failure": "A material failure can reach acceptance.",
        "affected_acceptance_criteria": ["AC-0003"],
        "evidence_refs": ["evidence-ref-1"],
        "material": material,
    }


def _report(
    subject: dict,
    *,
    status: str = "clean",
    role: str = "adversarial-reviewer",
    report_id: str = "report-1",
    sequence: int = 1,
    finding: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "report_id": report_id,
        "role": role,
        "subject": subject,
        "terminal_status": status,
        "lineage": {
            "sequence": sequence,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": "source-event-1",
            "producer": "synthetic-reviewer",
        },
        "findings": [finding or _finding()] if status == "findings" else [],
    }


def _assessment(
    subject: dict,
    *,
    assessment: str = "supported",
    finding_id: str = "finding-1",
    report_id: str = "report-1",
) -> dict:
    return {
        "schema_version": 1,
        "assessment_id": f"assessment-{assessment}",
        "finding_id": finding_id,
        "report_id": report_id,
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": assessment,
        "evidence_refs": ["evidence-ref-1"],
        "lineage": {"predicate_version": "v1"},
    }


def _disposition(
    subject: dict,
    *,
    disposition: str = "accept-risk",
    finding_id: str = "finding-1",
    assessment_id: str = "assessment-supported",
) -> dict:
    return {
        "schema_version": 1,
        "disposition_id": f"disposition-{disposition}",
        "finding_id": finding_id,
        "assessment_id": assessment_id,
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "disposition": disposition,
        "decision_maker": {"identity": "review-owner", "role": "risk-owner"},
        "lineage": {"authority_ref": "authority-1", "source_event_id": "event-1"},
    }


def _fixed_by_disposition(
    subject: dict, *, replacement_report_id: str = "replacement-report"
) -> dict:
    disposition = _disposition(subject, disposition="fixed-by")
    disposition["replacement_report_id"] = replacement_report_id
    return disposition


def _mandatory_obligation(review_selection: ModuleType, subject: dict, policy: dict) -> dict:
    obligations = review_selection.select_review_obligations(subject, policy)
    return next(item for item in obligations if item["role"] == "adversarial-reviewer")


def _decision(
    review_selection: ModuleType,
    *,
    subject: dict,
    policy: dict,
    reports: list[dict],
    assessments: list[dict] | None = None,
    dispositions: list[dict] | None = None,
) -> dict:
    obligation = _mandatory_obligation(review_selection, subject, policy)
    return review_selection.decide_review_obligation(
        obligation,
        review_subject=subject,
        policy=policy,
        reports=reports,
        assessments=assessments or [],
        dispositions=dispositions or [],
    )


@pytest.mark.parametrize(
    "case_name,expected",
    [
        (
            "mandatory-clean-report",
            {
                "obligation_satisfied": True,
                "review_block": False,
                "acceptance_block": False,
                "decision": "satisfied-clean",
            },
        ),
        (
            "mandatory-findings-closed",
            {
                "obligation_satisfied": True,
                "review_block": False,
                "acceptance_block": False,
                "decision": "satisfied-findings",
            },
        ),
        (
            "mandatory-findings-missing-assessment",
            {
                "obligation_satisfied": False,
                "review_block": True,
                "acceptance_block": True,
                "decision": "finding-assessment-required",
            },
        ),
        (
            "mandatory-findings-indeterminate-assessment",
            {
                "obligation_satisfied": False,
                "review_block": True,
                "acceptance_block": True,
                "decision": "finding-assessment-required",
            },
        ),
        (
            "mandatory-supported-open",
            {
                "obligation_satisfied": True,
                "review_block": False,
                "acceptance_block": True,
                "decision": "open-supported-material-finding",
            },
        ),
        (
            "mandatory-findings-unsupported",
            {
                "obligation_satisfied": True,
                "review_block": False,
                "acceptance_block": False,
                "decision": "satisfied-findings",
            },
        ),
        (
            "mandatory-supported-nonmaterial",
            {
                "obligation_satisfied": True,
                "review_block": False,
                "acceptance_block": False,
                "decision": "satisfied-findings",
            },
        ),
        (
            "mandatory-missing-report",
            {
                "obligation_satisfied": False,
                "review_block": True,
                "acceptance_block": True,
                "decision": "mandatory-report-unsatisfied",
            },
        ),
        (
            "mandatory-unable-report",
            {
                "obligation_satisfied": False,
                "review_block": True,
                "acceptance_block": True,
                "decision": "mandatory-report-unsatisfied",
            },
        ),
    ],
)
def test_obligation_truth_table_mandatory_rows(
    review_selection: ModuleType, case_name: str, expected: dict
) -> None:
    """Mandatory obligation rows follow the approved truth table."""
    subject = _subject(review_selection)
    policy = _policy()
    finding = _finding()
    reports: list[dict]
    assessments: list[dict] = []
    dispositions: list[dict] = []
    if case_name == "mandatory-clean-report":
        reports = [_report(subject, status="clean")]
    elif case_name == "mandatory-findings-closed":
        reports = [_report(subject, status="findings", finding=finding)]
        assessments = [_assessment(subject, assessment="supported")]
        dispositions = [_disposition(subject, disposition="accept-risk")]
    elif case_name == "mandatory-findings-missing-assessment":
        reports = [_report(subject, status="findings", finding=finding)]
    elif case_name == "mandatory-findings-indeterminate-assessment":
        reports = [_report(subject, status="findings", finding=finding)]
        assessments = [_assessment(subject, assessment="indeterminate")]
    elif case_name == "mandatory-supported-open":
        reports = [_report(subject, status="findings", finding=finding)]
        assessments = [_assessment(subject, assessment="supported")]
        dispositions = [_disposition(subject, disposition="repair-request")]
    elif case_name == "mandatory-findings-unsupported":
        reports = [_report(subject, status="findings", finding=finding)]
        assessments = [_assessment(subject, assessment="unsupported-opinion")]
    elif case_name == "mandatory-supported-nonmaterial":
        nonmaterial = _finding(material=False)
        reports = [_report(subject, status="findings", finding=nonmaterial)]
        assessments = [_assessment(subject, assessment="supported")]
    elif case_name == "mandatory-missing-report":
        reports = []
    elif case_name == "mandatory-unable-report":
        reports = [_report(subject, status="unable")]
    else:
        raise AssertionError(case_name)

    decision = _decision(
        review_selection,
        subject=subject,
        policy=policy,
        reports=reports,
        assessments=assessments,
        dispositions=dispositions,
    )

    assert {key: decision[key] for key in expected} == expected


def test_obligation_truth_table_optional_missing_report_does_not_block(
    review_selection: ModuleType,
) -> None:
    """Optional missing reports remain unsatisfied without blocking acceptance."""
    subject = _subject(review_selection)
    policy = _policy()
    obligation = next(
        item
        for item in review_selection.select_review_obligations(subject, policy)
        if item["role"] == "security-reviewer"
    )

    decision = review_selection.decide_review_obligation(
        obligation,
        review_subject=subject,
        policy=policy,
        reports=[],
        assessments=[],
        dispositions=[],
    )

    assert decision["obligation_satisfied"] is False
    assert decision["review_block"] is False
    assert decision["acceptance_block"] is False
    assert decision["decision"] == "optional-unsatisfied"


@pytest.mark.parametrize("kind", ["mandatory", "optional"])
def test_indeterminate_report_with_no_findings_is_unusable(
    review_selection: ModuleType, kind: str
) -> None:
    """A terminal indeterminate report never satisfies an obligation."""
    subject = _subject(review_selection)
    policy = _policy()
    obligation = next(
        item
        for item in review_selection.select_review_obligations(subject, policy)
        if item["kind"] == kind
    )
    report = _report(subject, status="indeterminate", role=obligation["role"])

    decision = review_selection.decide_review_obligation(
        obligation,
        review_subject=subject,
        policy=policy,
        reports=[report],
        assessments=[],
        dispositions=[],
    )

    assert decision["obligation_satisfied"] is False
    assert decision["acceptance_block"] is (kind == "mandatory")


def test_obligation_truth_table_current_authorized_waiver_removes_requirement(
    review_selection: ModuleType,
) -> None:
    """A current authorized waiver bound to subject and policy removes the requirement."""
    subject = _subject(review_selection)
    policy = _policy_with_waiver(subject)
    obligation = _mandatory_obligation(review_selection, subject, policy)

    decision = review_selection.decide_review_obligation(
        obligation,
        review_subject=subject,
        policy=policy,
        reports=[],
        assessments=[],
        dispositions=[],
    )

    assert obligation["kind"] == "waived"
    assert decision["obligation_satisfied"] is True
    assert decision["acceptance_block"] is False
    assert decision["decision"] == "waived"


def test_obligation_truth_table_invalid_waiver_falls_back_to_mandatory(
    review_selection: ModuleType,
) -> None:
    """A stale or unauthorized waiver does not suppress the mandatory row."""
    subject = _subject(review_selection)
    policy = _policy_with_waiver(subject, authorized=False)
    obligation = _mandatory_obligation(review_selection, subject, policy)

    decision = review_selection.decide_review_obligation(
        obligation,
        review_subject=subject,
        policy=policy,
        reports=[],
        assessments=[],
        dispositions=[],
    )

    assert obligation["kind"] == "mandatory"
    assert decision["decision"] == "mandatory-report-unsatisfied"
    assert decision["acceptance_block"] is True


@pytest.mark.parametrize(
    "mutation",
    [
        {"review_subject_fingerprint": "review-subject-stale"},
        {"review_policy_fingerprint": "review-policy-stale"},
        {"current": False},
    ],
)
def test_invalid_waiver_subject_policy_or_currentness_falls_back_to_mandatory(
    review_selection: ModuleType, mutation: dict
) -> None:
    """Only current waivers bound to the same subject and policy suppress mandatory."""
    subject = _subject(review_selection)
    policy = _policy_with_waiver(subject)
    policy["waivers"][0].update(mutation)
    obligation = _mandatory_obligation(review_selection, subject, policy)

    decision = review_selection.decide_review_obligation(
        obligation,
        review_subject=subject,
        policy=policy,
        reports=[],
        assessments=[],
        dispositions=[],
    )

    assert obligation["kind"] == "mandatory"
    assert decision["decision"] == "mandatory-report-unsatisfied"


@pytest.mark.parametrize(
    "report_mutation",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"subject": "not-a-subject"},
    ],
)
def test_malformed_or_unknown_major_mandatory_report_is_unsatisfied(
    review_selection: ModuleType, report_mutation: dict
) -> None:
    """Malformed and unknown-major reports follow the unusable report row."""
    subject = _subject(review_selection)
    report = _report(subject, status="clean")
    report.update(report_mutation)

    decision = _decision(
        review_selection,
        subject=subject,
        policy=_policy(),
        reports=[report],
    )

    assert decision["decision"] == "mandatory-report-unsatisfied"
    assert decision["acceptance_block"] is True


def test_forked_mandatory_report_lineage_is_unsatisfied(
    review_selection: ModuleType,
) -> None:
    """Forked report lineage follows the unusable report row."""
    subject = _subject(review_selection)
    base = _report(subject, report_id="report-1", sequence=1)
    fork = _report(subject, report_id="report-2", sequence=1)

    decision = _decision(
        review_selection,
        subject=subject,
        policy=_policy(),
        reports=[base, fork],
    )

    assert decision["decision"] == "mandatory-report-unsatisfied"
    assert decision["acceptance_block"] is True


def test_stale_mandatory_report_subject_is_unsatisfied(
    review_selection: ModuleType,
) -> None:
    """A stale report subject cannot satisfy the current mandatory obligation."""
    subject = _subject(review_selection)
    stale_subject = dict(subject)
    stale_subject["review_subject_fingerprint"] = "review-subject-stale"

    decision = _decision(
        review_selection,
        subject=subject,
        policy=_policy(),
        reports=[_report(stale_subject, status="clean")],
    )

    assert decision["decision"] == "mandatory-report-unsatisfied"
    assert decision["acceptance_block"] is True


@pytest.mark.parametrize(
    "column,expected_decision",
    [
        ("report", "mandatory-report-unsatisfied"),
        ("finding", "open-supported-material-finding"),
        ("waiver", "mandatory-report-unsatisfied"),
        ("subject", "mandatory-report-unsatisfied"),
        ("policy", "mandatory-report-unsatisfied"),
    ],
)
def test_obligation_deciding_input_mutations_select_mutated_row(
    review_selection: ModuleType, column: str, expected_decision: str
) -> None:
    """Each deciding input column can move the result to its own row."""
    subject = _subject(review_selection)
    policy = _policy()
    finding = _finding()
    reports = [_report(subject, status="findings", finding=finding)]
    assessments = [_assessment(subject, assessment="supported")]
    dispositions = [_disposition(subject, disposition="accept-risk")]
    if column == "report":
        reports = [_report(subject, status="unable")]
        assessments = []
        dispositions = []
    elif column == "finding":
        dispositions = []
    elif column == "waiver":
        policy = _policy_with_waiver(subject, authorized=False)
        reports = []
        assessments = []
        dispositions = []
    elif column == "subject":
        stale_subject = dict(subject)
        stale_subject["review_subject_fingerprint"] = "review-subject-stale"
        reports = [_report(stale_subject, status="clean")]
        assessments = []
        dispositions = []
    elif column == "policy":
        policy = _policy()
        policy["review_policy_fingerprint"] = "review-policy-v2"
        subject = review_selection.project_review_subject(
            _delivery_subject(task_revision="task-a", task_hash="task-hash-a"),
            changed_paths=_manifest(),
            review_policy_fingerprint=policy["review_policy_fingerprint"],
        )
        reports = [_report(subject, status="clean")]
        reports[0]["lineage"]["review_policy_fingerprint"] = "review-policy-v1"
        assessments = []
        dispositions = []
    else:
        raise AssertionError(column)

    decision = _decision(
        review_selection,
        subject=subject,
        policy=policy,
        reports=reports,
        assessments=assessments,
        dispositions=dispositions,
    )

    assert decision["decision"] == expected_decision


def test_stale_bound_obligation_identity_refuses(
    review_selection: ModuleType,
) -> None:
    """A caller cannot pass an old obligation with the same kind."""
    subject = _subject(review_selection)
    policy = _policy()
    obligation = _mandatory_obligation(review_selection, subject, policy)
    stale_obligation = dict(obligation)
    stale_obligation["review_subject_fingerprint"] = "review-subject-stale"

    with pytest.raises(review_selection.ReviewSelectionRefused):
        review_selection.decide_review_obligation(
            stale_obligation,
            review_subject=subject,
            policy=policy,
            reports=[_report(subject, status="clean")],
            assessments=[],
            dispositions=[],
        )


def test_conflicting_current_assessments_fail_closed(
    review_selection: ModuleType,
) -> None:
    """Ambiguous assessment currentness stays unsatisfied until T4 supplies one tip."""
    subject = _subject(review_selection)
    report = _report(subject, status="findings")
    supported = _assessment(subject, assessment="supported")
    unsupported = _assessment(subject, assessment="unsupported-opinion")

    decision = _decision(
        review_selection,
        subject=subject,
        policy=_policy(),
        reports=[report],
        assessments=[supported, unsupported],
    )

    assert decision["obligation_satisfied"] is False
    assert decision["decision"] == "finding-assessment-required"


@pytest.mark.parametrize(
    "disposition",
    [
        "stale-subject",
        "fixed-by-missing-replacement",
        "fixed-by-same-subject-current-finding",
        "fixed-by-other-role-replacement",
        "fixed-by-replacement-still-open",
    ],
)
def test_disposition_currentness_or_replacement_gaps_keep_finding_open(
    review_selection: ModuleType, disposition: str
) -> None:
    """T2 consumes only current verified disposition facts."""
    subject = _subject(review_selection)
    report = _report(subject, status="findings")
    assessment = _assessment(subject, assessment="supported")
    dispositions: list[dict]
    reports = [report]
    assessments = [assessment]
    if disposition == "stale-subject":
        stale = _disposition(subject, disposition="accept-risk")
        stale["review_subject_fingerprint"] = "review-subject-stale"
        dispositions = [stale]
    elif disposition == "fixed-by-missing-replacement":
        dispositions = [_disposition(subject, disposition="fixed-by")]
    elif disposition == "fixed-by-same-subject-current-finding":
        current_report = _report(
            subject,
            status="findings",
            report_id="replacement-report",
            sequence=2,
        )
        current_report["lineage"]["previous_report_id"] = "report-1"
        reports.append(current_report)
        assessments = [
            _assessment(
                subject,
                assessment="supported",
                report_id="replacement-report",
            )
        ]
        dispositions = [_fixed_by_disposition(subject)]
    elif disposition == "fixed-by-other-role-replacement":
        reports.append(
            _report(
                subject,
                status="clean",
                role="security-reviewer",
                report_id="replacement-report",
            )
        )
        dispositions = [_fixed_by_disposition(subject)]
    elif disposition == "fixed-by-replacement-still-open":
        replacement_subject = _subject_for_acceptance(review_selection, "acceptance-repair")
        replacement_finding = _finding(finding_id="replacement-finding")
        reports.append(
            _report(
                replacement_subject,
                status="findings",
                report_id="replacement-report",
                finding=replacement_finding,
            )
        )
        assessments.append(
            _assessment(
                replacement_subject,
                assessment="supported",
                finding_id="replacement-finding",
                report_id="replacement-report",
            )
        )
        dispositions = [_fixed_by_disposition(subject)]
    else:
        raise AssertionError(disposition)

    decision = _decision(
        review_selection,
        subject=subject,
        policy=_policy(),
        reports=reports,
        assessments=assessments,
        dispositions=dispositions,
    )

    assert decision["decision"] == "open-supported-material-finding"
    assert decision["acceptance_block"] is True


def test_fixed_by_with_fresh_replacement_subject_current_report_closes_finding(
    review_selection: ModuleType,
) -> None:
    """Replacement subjects close by their own current clean report."""
    subject = _subject(review_selection)
    replacement_subject = _subject_for_acceptance(review_selection, "acceptance-repair")
    finding = _finding()
    report = _report(subject, status="findings", finding=finding)
    replacement = _report(
        replacement_subject,
        status="clean",
        report_id="replacement-report",
    )

    decision = _decision(
        review_selection,
        subject=replacement_subject,
        policy=_policy(),
        reports=[report, replacement],
        assessments=[_assessment(subject, assessment="supported")],
        dispositions=[_fixed_by_disposition(subject)],
    )

    assert decision["decision"] == "satisfied-clean"
    assert decision["acceptance_block"] is False


@pytest.mark.parametrize(
    "path",
    [
        "/absolute/path.py",
        "../outside.py",
        "packs\\core\\path.py",
        "./relative.py",
        "packs/core//path.py",
        "packs/core/./path.py",
        "packs/core/../path.py",
        "C:/path.py",
        "C:path.py",
        "file://path.py",
    ],
)
def test_review_subject_projection_rejects_noncanonical_changed_paths(
    review_selection: ModuleType, path: str
) -> None:
    """Changed paths are lexical relative canonical paths, not filesystem probes."""
    with pytest.raises(review_selection.ReviewSelectionRefused):
        review_selection.project_review_subject(
            _delivery_subject(task_revision="task-a", task_hash="task-hash-a"),
            changed_paths=[{"path": path, "status": "modified"}],
            review_policy_fingerprint="review-policy-v1",
        )


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": True},
        {"subject_id": ""},
        {"lineage": {"provider": "legacy-worktree-snapshot"}},
    ],
)
def test_review_subject_projection_rejects_invalid_delivery_subject_shape(
    review_selection: ModuleType, mutation: dict
) -> None:
    """The T2 port rejects invalid Slice 1 subject identities it consumes."""
    delivery_subject = _delivery_subject(task_revision="task-a", task_hash="task-hash-a")
    delivery_subject.update(mutation)

    with pytest.raises(review_selection.ReviewSelectionRefused) as excinfo:
        review_selection.project_review_subject(
            delivery_subject,
            changed_paths=_manifest(),
            review_policy_fingerprint="review-policy-v1",
        )
    expected = {
        "schema_version": "denied-delivery-subject-schema-version",
        "subject_id": "denied-delivery-subject-invalid-field",
        "lineage": "denied-missing-required-field",
    }
    mutated_field = next(iter(mutation))
    assert excinfo.value.denial_code == expected[mutated_field]


@pytest.mark.parametrize(
    "policy,expected_code",
    [
        (None, "denied-review-policy-not-a-dict"),
        ([], "denied-review-policy-not-a-dict"),
        ({"review_policy_fingerprint": "review-policy-v1"}, "denied-review-policy-missing-field"),
        (
            {
                "policy_id": "core-review-policy",
                "review_policy_fingerprint": "review-policy-v1",
                "policy_version": "2026-10-07",
                "selector": "core-review-obligation-selector",
                "roles": [{"role": "adversarial-reviewer", "kind": ["mandatory"]}],
                "waivers": [],
            },
            "denied-review-policy-invalid-role",
        ),
        (
            {
                "policy_id": "core-review-policy",
                "review_policy_fingerprint": "review-policy-v1",
                "policy_version": "2026-10-07",
                "selector": "core-review-obligation-selector",
                "roles": [["adversarial-reviewer", "mandatory"]],
                "waivers": [],
            },
            "denied-review-policy-invalid-role",
        ),
    ],
)
def test_policy_parse_refuses_malformed_containers_stably(
    review_selection: ModuleType, policy: object, expected_code: str
) -> None:
    """Malformed policy containers refuse without TypeError or KeyError."""
    subject = _subject(review_selection)

    with pytest.raises(review_selection.ReviewSelectionRefused) as excinfo:
        review_selection.select_review_obligations(subject, policy)
    assert excinfo.value.denial_code == expected_code
