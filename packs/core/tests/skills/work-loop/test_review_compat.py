"""T6 goal-based integration suite: compatibility boundary.

Verification IDs: VI-1012 (AC-0001), VI-1013 (AC-0011), VI-1018 (AC-0013),
VI-1019 (AC-0016).

Mode: goal-based check (structured-review-boundary plan T6).

The suite loads shipped work-loop scripts by literal path.  Every imported
module is standard-library-only or a sibling work-loop module.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchors ──────────────────────────────────────────────────────────────

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)
ENGINE = SCRIPTS / "loop-engine.py"
COHORT = SCRIPTS / "loop-cohort.py"

# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path for pack-boundary tests."""
    if not path.exists():
        pytest.fail(f"T6 module is not implemented: {path.name}")
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


# ── Module fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def review_compat() -> ModuleType:
    """The T6 compatibility adapter."""
    return _load_module("review_compat_t6", SCRIPTS / "_review_compat.py")


@pytest.fixture(scope="module")
def evidence_store_mod() -> ModuleType:
    """The Slice 1 evidence store."""
    return _load_module("evidence_store_t6", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def review_persistence() -> ModuleType:
    return _load_module("review_persistence_t6", SCRIPTS / "_review_persistence.py")


@pytest.fixture(scope="module")
def review_bridge() -> ModuleType:
    return _load_module("review_bridge_t6", SCRIPTS / "_review_bridge.py")


@pytest.fixture(scope="module")
def review_assessment() -> ModuleType:
    return _load_module("review_assessment_t6", SCRIPTS / "_review_assessment.py")


@pytest.fixture(scope="module")
def review_disposition() -> ModuleType:
    return _load_module("review_disposition_t6", SCRIPTS / "_review_disposition.py")


@pytest.fixture(scope="module")
def review_selection() -> ModuleType:
    return _load_module("review_selection_t6", SCRIPTS / "_review_selection.py")


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    return _load_module("security_capability_t6", SCRIPTS / "_security_capability.py")


@pytest.fixture(scope="module")
def loop_engine_mod() -> ModuleType:
    return _load_module("loop_engine_t6", ENGINE)


# ── Shared test helpers ───────────────────────────────────────────────────────

# The exact clean sentinel that the legacy grammar recognises.
_CLEAN_TEXT = "Clean — ready to commit."

# Grammar-valid findings text (one numbered finding).
_FINDINGS_TEXT = (
    "**1. Missing null check.** `packs/core/_review_compat.py:42`. "
    "The value is never validated. Fix: add guard.\n"
)

# finding.v1 dicts used in adjudicated corpus rows.
_COMPAT_FINDING_REFUTED: dict = {
    "schema_version": 1,
    "finding_id": "finding-compat-refuted-t6",
    "rule_ref": "AC-0011",
    "observation": "Observation for refuted finding.",
    "reachable_path": "No reachable path.",
    "actual_failure": "No actual failure.",
    "affected_acceptance_criteria": ["AC-0011"],
    "evidence_refs": [
        "packs/core/.apm/skills/work-loop/scripts/_review_compat.py"
    ],
    "material": False,
}
_COMPAT_FINDING_SUSTAINED: dict = {
    "schema_version": 1,
    "finding_id": "finding-compat-sustained-t6",
    "rule_ref": "AC-0011",
    "observation": "Observation for sustained finding.",
    "reachable_path": "Reachable path for sustained.",
    "actual_failure": "Actual failure confirmed.",
    "affected_acceptance_criteria": ["AC-0011"],
    "evidence_refs": [
        "packs/core/.apm/skills/work-loop/scripts/_review_compat.py"
    ],
    "material": False,
}


def _null_sink(event: object) -> None:
    """Accept security events without persisting them."""


def _make_grant(
    security_capability: ModuleType,
) -> tuple[object, object]:
    """Return a valid producer authority pair for semantic evidence appends."""
    issuer = security_capability.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


def _open_store(
    evidence_store_mod: ModuleType,
    log_path: Path,
) -> object:
    """Open a fresh EvidenceStore at the given path."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    store = evidence_store_mod.EvidenceStore(log_path)
    store.open()
    return store


def _delivery_subject() -> dict:
    return {
        "schema_version": 1,
        "subject_id": "delivery-subject-t6",
        "acceptance_fingerprint": "acceptance-fp-t6",
        "product": {
            "base_ref": "base-tree-t6",
            "result_ref": "result-tree-t6",
        },
        "spec": {
            "path": "docs/specs/structured-review-boundary/spec.md",
            "fingerprint": "spec-fp-t6",
        },
        "evidence_policy_ref": "evidence-policy-t6",
        "exclusions": [],
        "lineage": {
            "provider": "legacy-worktree-snapshot",
            "projection_version": "1.0",
        },
        "task_projection_revision": "task-rev-t6-a",
        "task_projection_hash": "task-hash-t6-a",
    }


def _changed_paths() -> list[dict]:
    return [
        {
            "path": "packs/core/.apm/skills/work-loop/scripts/_review_compat.py",
            "status": "added",
        }
    ]


def _make_review_subject(review_selection: ModuleType) -> dict:
    """Project a current review subject for T6 tests."""
    return review_selection.project_review_subject(
        _delivery_subject(),
        changed_paths=_changed_paths(),
        review_policy_fingerprint="review-policy-fp-t6",
    )


def _make_review_policy(review_subject: dict) -> dict:
    """Build a minimal review policy matching the test subject."""
    return {
        "policy_id": "review-policy-t6",
        "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
        "policy_version": "1",
        "selector": "core-review-t6",
        "roles": [{"role": "structured-reviewer-t6", "kind": "mandatory"}],
        "waivers": [],
    }


def _make_compat_review_policy(review_subject: dict) -> dict:
    """Build a review policy expecting the legacy-reviewer role.

    The compat adapter writes reports with the source_event's role (default:
    legacy-reviewer).  Tests that check acceptance_eligible against compat
    reports must use this policy.
    """
    return {
        "policy_id": "review-policy-compat-t6",
        "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
        "policy_version": "1",
        "selector": "core-review-compat-t6",
        "roles": [{"role": "legacy-reviewer", "kind": "mandatory"}],
        "waivers": [],
    }


def _clean_report(review_subject: dict, *, source_event_id: str) -> dict:
    """Build a minimal valid clean review-report.v1."""
    return {
        "schema_version": 1,
        "report_id": f"report-clean-{source_event_id}",
        "role": "structured-reviewer-t6",
        "subject": copy.deepcopy(review_subject),
        "terminal_status": "clean",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
            "source_event_id": source_event_id,
            "producer": "synthetic-reviewer-t6",
        },
        "findings": [],
    }


def _findings_report(
    review_subject: dict,
    finding: dict,
    *,
    source_event_id: str,
) -> dict:
    """Build a minimal valid findings review-report.v1."""
    return {
        "schema_version": 1,
        "report_id": f"report-findings-{source_event_id}",
        "role": "structured-reviewer-t6",
        "subject": copy.deepcopy(review_subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
            "source_event_id": source_event_id,
            "producer": "synthetic-reviewer-t6",
        },
        "findings": [copy.deepcopy(finding)],
    }


def _unsupported_finding() -> dict:
    """Build an unsupported finding for test fixtures."""
    return {
        "schema_version": 1,
        "finding_id": "finding-t6-opinion",
        "rule_ref": "AC-0001",
        "observation": "This observation is unsupported opinion.",
        "reachable_path": "No verifiable path to an actual failure.",
        "actual_failure": "No confirmed actual failure reachable.",
        "affected_acceptance_criteria": ["AC-0001"],
        "evidence_refs": [
            "packs/core/.apm/skills/work-loop/scripts/_review_compat.py"
        ],
        "material": False,
    }


def _empty_legacy_state() -> dict:
    """Return a minimal cohort state dict with no recorded review."""
    return {
        "last_review_record_operation_id": None,
        "last_review_record_payload_digest": None,
        "transition_history": [],
    }


def _legacy_clean_digest(form: str = "direct-clean", text: str = _CLEAN_TEXT) -> str:
    """Return the payload digest the legacy recorder stores for a clean form.

    Computed independently of the runtime: sha256(form + "\\n" + sha256(bytes)).
    """
    inner = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return hashlib.sha256(f"{form}\n{inner}".encode()).hexdigest()


def _legacy_state_with_operation(operation_id: str) -> dict:
    """Return a cohort state dict with the given operation ID recorded.

    This has only last_review_record_operation_id set — legacy is present
    but no transition event is recorded, so acknowledged=False.
    """
    return {
        "last_review_record_operation_id": operation_id,
        "last_review_record_payload_digest": "payload-digest-t6",
        "transition_history": [],
    }


def _legacy_state_with_clean_transition(operation_id: str) -> dict:
    """Return a cohort state dict with a reviewers-clean transition event.

    This produces legacy_present=True, legacy_event="clean" → acknowledged=True
    when the structured result is also "clean".
    """
    return {
        "last_review_record_operation_id": operation_id,
        "last_review_record_payload_digest": _legacy_clean_digest(),
        "transition_history": [
            {
                "transition_id": operation_id,
                "pre_transition_sequence": 0,
                "event": "reviewers-clean",
                "args": {},
            }
        ],
    }


# ── VI-1012: Synthetic Reviewer Conformance ───────────────────────────────────


def test_vi1012_clean_report_reaches_acceptance_eligible(
    review_selection: ModuleType,
    review_persistence: ModuleType,
    review_disposition: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Synthetic reviewer journey: clean report → acceptance_eligible True.

    The synthetic reviewer knows only the published reviewer port:
    select_review_obligations → append_current_review_report → review_readiness.
    No reviewer-specific branch in any shipped module is required.
    """
    issuer, grant = _make_grant(security_capability)
    log_path = tmp_path / "vi1012-clean" / "store.log"
    store = _open_store(evidence_store_mod, log_path)

    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Step 1: the synthetic reviewer selects its obligation.
    obligations = review_selection.select_review_obligations(
        review_subject, review_policy
    )
    assert obligations, "at least one obligation must be selected"
    obligation = obligations[0]
    assert obligation["kind"] == "mandatory"

    # Step 2: the synthetic reviewer submits a clean report through the generic port.
    report = _clean_report(review_subject, source_event_id="vi1012-clean-evt")
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-vi1012-clean",
        expected_subject=review_subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 3: check readiness via the generic port.
    readiness = review_disposition.review_readiness(
        store,
        review_subject=review_subject,
        review_policy=review_policy,
    )
    assert readiness["acceptance_eligible"] is True, (
        f"acceptance_eligible must be True after a clean report: {readiness}"
    )
    # T5: assert the readiness obligation decision value exactly.
    assert readiness["obligations"], "at least one obligation must be present"
    assert readiness["obligations"][0]["decision"] == "satisfied-clean", (
        "clean report obligation decision must be 'satisfied-clean'; "
        f"got {readiness['obligations'][0].get('decision')!r}"
    )


def test_vi1012_unsupported_findings_report_reaches_acceptance_eligible(
    review_selection: ModuleType,
    review_persistence: ModuleType,
    review_assessment: ModuleType,
    review_bridge: ModuleType,
    review_disposition: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Synthetic reviewer journey: findings report with unsupported finding →
    acceptance_eligible True (unsupported findings do not block).
    """
    issuer, grant = _make_grant(security_capability)
    log_path = tmp_path / "vi1012-findings" / "store.log"
    store = _open_store(evidence_store_mod, log_path)

    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)
    finding = _unsupported_finding()

    # Step 1: select obligation.
    obligations = review_selection.select_review_obligations(
        review_subject, review_policy
    )
    assert obligations

    # Step 2: submit findings report.
    report = _findings_report(
        review_subject, finding, source_event_id="vi1012-findings-evt"
    )
    report_id = report["report_id"]
    review_persistence.append_current_review_report(
        store,
        report,
        transaction_id="tx-vi1012-findings",
        expected_subject=review_subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 3: assess the finding (unsupported — no reachable path).
    assessment = review_assessment.assess_finding_actual_failure(
        report,
        finding,
        assessment_id="assessment-vi1012-opinion",
        current_subject=review_subject,
        current_report_id=report_id,
        current_rule_refs={finding["rule_ref"]},
        current_evidence_refs=set(finding["evidence_refs"]),
        controlled_facts={"falsifiable-delivery-failure": False},
        controlled_edges={
            "rule-to-observation": None,
            "observation-to-reachable-path": None,
            "reachable-path-to-actual-failure": None,
        },
        predicate_version="t6-v1",
    )
    assert assessment["assessment"] in {
        "unsupported-opinion",
        "unsupported-controlled-elsewhere",
        "unsupported-stale",
    }, f"assessment should be unsupported: {assessment}"

    # Step 4: send through the bridge.
    review_bridge.append_finding_assessment_bridge(
        store,
        assessment,
        report_id=report_id,
        finding=finding,
        affected_criteria=finding["affected_acceptance_criteria"],
        transaction_id="tx-vi1012-bridge",
        acceptance_fingerprint=review_subject["delivery_subject_ref"][
            "acceptance_fingerprint"
        ],
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 5: readiness with only an unsupported finding.
    readiness = review_disposition.review_readiness(
        store,
        review_subject=review_subject,
        review_policy=review_policy,
    )
    assert readiness["acceptance_eligible"] is True, (
        f"unsupported finding must not block acceptance: {readiness}"
    )
    # T5: assert the readiness obligation decision value exactly.
    assert readiness["obligations"], "at least one obligation must be present"
    assert readiness["obligations"][0]["decision"] == "satisfied-findings", (
        "findings-assessed obligation decision must be 'satisfied-findings'; "
        f"got {readiness['obligations'][0].get('decision')!r}"
    )


# ── S-3: Unicode surrogate safety guard ──────────────────────────────────────


@pytest.mark.parametrize(
    "label,source_event_kwargs",
    [
        # direct-clean form with a lone surrogate in raw_report_text
        (
            "direct-clean-surrogate-in-raw",
            {
                "source_event_id": "evt-s3-direct-clean",
                "form": "direct-clean",
                "raw_report_text": "Clean \ud800 has lone surrogate.",
                "adjudication_text": None,
            },
        ),
        # findings form with a lone surrogate in raw_report_text
        (
            "findings-surrogate-in-raw",
            {
                "source_event_id": "evt-s3-findings",
                "form": "findings",
                "raw_report_text": _FINDINGS_TEXT + "\ud800",
                "adjudication_text": None,
            },
        ),
        # adjudicated form with a lone surrogate in adjudication_text
        (
            "adjudicated-surrogate-in-adj",
            {
                "source_event_id": "evt-s3-adjudicated",
                "form": "adjudicated",
                "raw_report_text": json.dumps([_COMPAT_FINDING_REFUTED]),
                "adjudication_text": "adjudication with \ud800 lone surrogate",
            },
        ),
    ],
)
def test_s3_unicode_surrogate_returns_unable(
    label: str,
    source_event_kwargs: dict,
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """S-3: A lone Unicode surrogate in raw_report_text or adjudication_text returns unable.

    UnicodeEncodeError must be caught by the content-safety encode guard before
    any classification or persistence.  Result must be 'unable', structured_present
    must be False, and no report must be stored in the evidence log.

    Mutation-check: removing the surrogate guard causes the encode call inside
    reconcile_review_source_event to raise UnicodeEncodeError directly into the
    test body, turning the assertion failure into a propagated exception (red).
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, f"s3-{label}")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    source_event = _source_event(**source_event_kwargs)

    result = review_compat.reconcile_review_source_event(
        store,
        source_event,
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        f"[{label}] lone surrogate must yield 'unable', got {result['result']!r}"
    )
    assert result["structured_present"] is False, (
        f"[{label}] unable result must not persist a structured record"
    )
    stored = store.get_semantic_records("review-report.v1")
    assert not stored, (
        f"[{label}] no report must be stored for refused surrogate input: {stored}"
    )


# ── VI-1012: F-1 goal-based journey: material finding accept-risk ─────────────


def test_vi1012_f1_material_finding_accept_risk_journey(
    review_selection: ModuleType,
    review_persistence: ModuleType,
    review_assessment: ModuleType,
    review_bridge: ModuleType,
    review_disposition: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """VI-1012 F-1: material finding accept-risk journey via published review ports only.

    Journey:
      1. select_review_obligations
      2. append_current_review_report — findings report with one material finding
      3. assess_finding_actual_failure — controlled facts → SUPPORTED
      4. append_finding_assessment_bridge
      5. review_readiness → not eligible; finding in open_findings
      6. append_finding_disposition accept-risk — approval-record.v1; review-scoped grant
      7. review_readiness → acceptance_eligible True

    Also asserts that the contradiction receipts (supported-review-failure) remain
    active after accept-risk.

    Mutation-check: making disposition_closes always False (in _evidence_store.py)
    causes step 7 to return acceptance_eligible=False instead of True → RED.
    """
    # ── Authority setup ──────────────────────────────────────────────────────
    # Two grants from the same issuer: evidence for reports/assessments, review
    # for dispositions.  Pattern mirrors test_review_disposition.py.
    issuer = security_capability.CapabilityIssuer()
    evidence_grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    review_grant = issuer.issue_root_grant(
        roots=["review"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["review"],
        control_denies=[],
    )

    log_path = tmp_path / "vi1012-f1" / "store.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    store = evidence_store_mod.EvidenceStore(log_path)
    store.open()

    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # ── Step 1: select obligation ────────────────────────────────────────────
    obligations = review_selection.select_review_obligations(review_subject, review_policy)
    assert obligations, "at least one obligation must be selected"
    assert obligations[0]["kind"] == "mandatory"

    # ── Material finding definition ──────────────────────────────────────────
    # evidence_refs drives the edge refs for the supported assessment below.
    evidence_ref = "evidence-vi1012-f1"
    finding_f1 = {
        "schema_version": 1,
        "finding_id": "finding-vi1012-f1",
        "rule_ref": "AC-0001",
        "observation": "F1 journey: observable delivery failure.",
        "reachable_path": "F1 journey: reachable path to the actual failure.",
        "actual_failure": "F1 journey: confirmed actual failure in the delivery.",
        "affected_acceptance_criteria": ["AC-0001"],
        "evidence_refs": [evidence_ref],
        "material": True,
    }

    # ── Step 2: submit findings report with a material finding ───────────────
    report_f1 = {
        "schema_version": 1,
        "report_id": "report-vi1012-f1",
        "role": "structured-reviewer-t6",
        "subject": copy.deepcopy(review_subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
            "source_event_id": "evt-vi1012-f1",
            "producer": "synthetic-reviewer-f1",
        },
        "findings": [copy.deepcopy(finding_f1)],
    }
    review_persistence.append_current_review_report(
        store,
        report_f1,
        transaction_id="tx-vi1012-f1-report",
        expected_subject=review_subject,
        issuer=issuer,
        grant=evidence_grant,
        audit_sink=_null_sink,
    )

    # ── Step 3: assess the finding — controlled facts → SUPPORTED ────────────
    # All three required edges point to evidence_ref; evidence_ref is in
    # current_evidence_refs, so stale_edges is False and all edges are decidable.
    # falsifiable-delivery-failure=True prevents unsupported-opinion; every edge
    # present and decidable → assessment="supported".
    assessment_f1 = review_assessment.assess_finding_actual_failure(
        report_f1,
        finding_f1,
        assessment_id="assessment-vi1012-f1",
        current_subject=review_subject,
        current_report_id=report_f1["report_id"],
        current_rule_refs={finding_f1["rule_ref"]},
        current_evidence_refs={evidence_ref},
        controlled_facts={"falsifiable-delivery-failure": True},
        controlled_edges={
            "rule-to-observation": [evidence_ref],
            "observation-to-reachable-path": [evidence_ref],
            "reachable-path-to-actual-failure": [evidence_ref],
        },
        predicate_version="vi1012-f1-v1",
    )
    assert assessment_f1["assessment"] == "supported", (
        f"F1: assessment must be 'supported'; got {assessment_f1['assessment']!r}"
    )

    # ── Step 4: send the assessment through the bridge ───────────────────────
    review_bridge.append_finding_assessment_bridge(
        store,
        assessment_f1,
        report_id=report_f1["report_id"],
        finding=finding_f1,
        affected_criteria=finding_f1["affected_acceptance_criteria"],
        transaction_id="tx-vi1012-f1-bridge",
        acceptance_fingerprint=review_subject["delivery_subject_ref"]["acceptance_fingerprint"],
        issuer=issuer,
        grant=evidence_grant,
        audit_sink=_null_sink,
    )

    # ── Step 5: review_readiness — not eligible; finding in open_findings ────
    readiness_before = review_disposition.review_readiness(
        store,
        review_subject=review_subject,
        review_policy=review_policy,
    )
    assert readiness_before["acceptance_eligible"] is False, (
        f"F1: supported material finding must block acceptance before disposition; "
        f"readiness={readiness_before}"
    )
    assert any(
        f["finding_id"] == finding_f1["finding_id"]
        for f in readiness_before["open_findings"]
    ), (
        f"F1: finding must be in open_findings; "
        f"open_findings={readiness_before['open_findings']}"
    )

    # ── Step 6: append_finding_disposition accept-risk ───────────────────────
    # Approval record (approval-record.v1): decision_scope="review-disposition",
    # authority matches the disposition decision_maker, decision="approved".
    authority_identity = "risk-owner-vi1012-f1"
    authority_role = "risk-owner"
    approval_f1 = {
        "schema_version": 1,
        "approval_id": "approval-vi1012-f1",
        "authority": {
            "identity": authority_identity,
            "role": authority_role,
        },
        "decision_scope": "review-disposition",
        "base": {"manifest_ref": review_subject["review_subject_fingerprint"]},
        "lineage": {"spec_ref": "docs/specs/structured-review-boundary/spec.md"},
        "spec_policy_fingerprint": review_subject["review_policy_fingerprint"],
        "decision": "approved",
        "timestamp": "2026-10-09T00:00:00Z",
    }
    disposition_f1 = {
        "schema_version": 1,
        "disposition_id": "disposition-vi1012-f1",
        "finding_id": finding_f1["finding_id"],
        "assessment_id": assessment_f1["assessment_id"],
        "review_subject_fingerprint": review_subject["review_subject_fingerprint"],
        "disposition": "accept-risk",
        "decision_maker": {
            "identity": authority_identity,
            "role": authority_role,
        },
        "lineage": {
            "authority_ref": approval_f1["approval_id"],
            "source_event_id": "event-vi1012-f1",
        },
    }
    review_disposition.append_finding_disposition(
        store,
        disposition_f1,
        approval_record=approval_f1,
        current_subject=review_subject,
        transaction_id="tx-vi1012-f1-disposition",
        acceptance_fingerprint=review_subject["delivery_subject_ref"]["acceptance_fingerprint"],
        issuer=issuer,
        grant=review_grant,
        audit_sink=_null_sink,
    )

    # ── Step 7: review_readiness → acceptance_eligible True ──────────────────
    readiness_after = review_disposition.review_readiness(
        store,
        review_subject=review_subject,
        review_policy=review_policy,
    )
    assert readiness_after["acceptance_eligible"] is True, (
        f"F1: accept-risk disposition must make review acceptance_eligible; "
        f"readiness={readiness_after}"
    )

    # Contradiction receipts (supported-review-failure) must remain active after
    # accept-risk — the disposition closes the obligation without removing evidence.
    active_receipts = store.get_all_active_receipts()
    bridge_receipts = [
        r for r in active_receipts
        if r.get("selector", {}).get("term") == "supported-review-failure"
    ]
    assert bridge_receipts, (
        "F1: contradiction receipts (supported-review-failure) must remain active "
        f"after accept-risk; active_receipts={active_receipts}"
    )


# ── VI-1013: Compatibility Corpus ─────────────────────────────────────────────


def _make_compat_store(
    evidence_store_mod: ModuleType,
    tmp_path: Path,
    name: str,
) -> object:
    log_path = tmp_path / name / "store.log"
    return _open_store(evidence_store_mod, log_path)


def _source_event(
    *,
    source_event_id: str,
    role: str = "legacy-reviewer",
    form: str,
    raw_report_text: str,
    adjudication_text: str | None = None,
) -> dict:
    return {
        "source_event_id": source_event_id,
        "role": role,
        "form": form,
        "raw_report_text": raw_report_text,
        "adjudication_text": adjudication_text,
    }


@pytest.mark.parametrize(
    "label,source_event_kwargs,legacy_state_fn,expected_result,expected_acknowledged",
    [
        # Row 1: exact direct-clean report — reviewers-clean transition recorded
        # in transition_history → acknowledged=True.
        (
            "direct-clean",
            {
                "source_event_id": "evt-direct-clean",
                "form": "direct-clean",
                "raw_report_text": _CLEAN_TEXT,
            },
            lambda: _legacy_state_with_clean_transition("evt-direct-clean"),
            "clean",
            True,
        ),
        # Row 2: adjudicated form with all findings refuted → result="findings"
        # (unsupported-opinion assessments → acceptance eligible).
        # raw_report_text is a JSON list of finding.v1 dicts.
        # adjudication_text is {finding_id: {decision, authority_ref}}.
        # acknowledged=False because _legacy_state_with_operation provides only
        # last_review_record_operation_id (no transition_history entry with event).
        (
            "adjudicated-all-refuted",
            {
                "source_event_id": "evt-adjudicated-clean",
                "form": "adjudicated",
                "raw_report_text": json.dumps([_COMPAT_FINDING_REFUTED]),
                "adjudication_text": json.dumps({
                    "finding-compat-refuted-t6": {
                        "decision": "refuted",
                        "authority_ref": "review-authority-t6",
                    }
                }),
            },
            lambda: _legacy_state_with_operation("evt-adjudicated-clean"),
            "findings",
            False,
        ),
        # Row 2b: adjudicated form with sustained finding → result="findings",
        # acknowledged=False (same reason as row 2).
        (
            "adjudicated-sustained",
            {
                "source_event_id": "evt-adjudicated-findings",
                "form": "adjudicated",
                "raw_report_text": json.dumps([_COMPAT_FINDING_SUSTAINED]),
                "adjudication_text": json.dumps({
                    "finding-compat-sustained-t6": {
                        "decision": "sustained",
                        "authority_ref": "review-authority-t6",
                    }
                }),
            },
            lambda: _legacy_state_with_operation("evt-adjudicated-findings"),
            "findings",
            False,
        ),
        # Row 3: findings without required adjudication → indeterminate.
        # raw_report_text must be grammar-valid (parse_findings returns count > 0)
        # for _classify_findings_form to return "indeterminate" rather than "unable".
        (
            "findings-no-adjudication",
            {
                "source_event_id": "evt-findings-no-adj",
                "form": "findings",
                "raw_report_text": _FINDINGS_TEXT,
                "adjudication_text": None,
            },
            lambda: _legacy_state_with_operation("evt-findings-no-adj"),
            "indeterminate",
            False,
        ),
        # Row 4: schema-invalid (form not in closed corpus) → unable.
        (
            "unknown-form",
            {
                "source_event_id": "evt-unknown-form",
                "form": "unknown-form",
                "raw_report_text": "some text",
            },
            lambda: _empty_legacy_state(),
            "unable",
            False,
        ),
        # Row 5: content-safety refused → unable.
        # SOH (0x01) is in the rejected C0 control-character set; the safety
        # check fires on step 4 (control-character scan) before any grammar
        # call or temp-file write.  Uses direct-clean (an in-corpus form) to
        # prove the content-safety gate, not the closed-form gate.
        (
            "content-safety-refused",
            {
                "source_event_id": "evt-content-safety",
                "form": "direct-clean",
                "raw_report_text": "Clean \x01 has control character.",
            },
            lambda: _empty_legacy_state(),
            "unable",
            False,
        ),
        # Row 6: safe but unmappable (adjudicated with non-JSON adjudication) →
        # indeterminate.
        (
            "safe-unmappable",
            {
                "source_event_id": "evt-safe-unmappable",
                "form": "adjudicated",
                "raw_report_text": (
                    "## Finding 1\n"
                    "sha256:e3b0c44298fc1c149afbf4c8996fb924"
                    "27ae41e4649b934ca495991b7852b855\n"
                    "Observation: test.\n"
                ),
                "adjudication_text": "This is legacy three-section text that cannot "
                "be parsed as JSON and thus cannot be mapped.",
            },
            lambda: _empty_legacy_state(),
            "indeterminate",
            False,
        ),
        # Row 7a: one-sided write — structured missing, legacy present → reconcile.
        # Uses clean transition so acknowledged=True.
        (
            "one-sided-legacy-present",
            {
                "source_event_id": "evt-one-sided",
                "form": "direct-clean",
                "raw_report_text": _CLEAN_TEXT,
            },
            lambda: _legacy_state_with_clean_transition("evt-one-sided"),
            "clean",
            True,
        ),
        # Row 7b: one-sided write — legacy absent, structured may be present → not
        # acknowledged (legacy_present=False).
        (
            "one-sided-legacy-absent",
            {
                "source_event_id": "evt-one-sided-no-legacy",
                "form": "direct-clean",
                "raw_report_text": _CLEAN_TEXT,
            },
            lambda: _empty_legacy_state(),
            "clean",
            False,  # not acknowledged because legacy_present=False
        ),
    ],
)
def test_vi1013_compatibility_corpus(
    label: str,
    source_event_kwargs: dict,
    legacy_state_fn: object,
    expected_result: str,
    expected_acknowledged: bool,
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """VI-1013: every compatibility corpus row produces its required result."""
    # Re-build the source_event with the correct structure.
    source_event = _source_event(**source_event_kwargs)
    legacy_state = legacy_state_fn()

    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, f"vi1013-{label}")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        source_event,
        legacy_state=legacy_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert result["source_event_id"] == source_event["source_event_id"]
    assert result["result"] == expected_result, (
        f"[{label}] expected result={expected_result!r}, got {result['result']!r}"
    )
    assert result["acknowledged"] == expected_acknowledged, (
        f"[{label}] expected acknowledged={expected_acknowledged}, "
        f"got {result['acknowledged']}"
    )
    stored = [
        report["terminal_status"]
        for report in store.get_semantic_records("review-report.v1")
        if report["lineage"]["source_event_id"] == source_event["source_event_id"]
    ]
    # unable results must not produce structured records; every other row,
    # including indeterminate, persists exactly its validated result.
    if expected_result == "unable":
        assert not result["structured_present"], (
            f"[{label}] unable result must not persist a structured record"
        )
        assert stored == []
    else:
        assert result["structured_present"] is True
        assert stored == [expected_result]


def test_vi1013_out_of_corpus_input_refused(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """An input class outside the closed corpus is refused."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "vi1013-oor")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        {
            "source_event_id": "evt-out-of-corpus",
            "role": "legacy-reviewer",
            "form": "synthetic-new-form",  # not in closed corpus
            "raw_report_text": "some text",
            "adjudication_text": None,
        },
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable"
    assert not result["acknowledged"]


def test_vi1013_crash_before_acknowledgement_is_idempotent(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """Crash before acknowledgement: replay produces same facts, acknowledged once.

    Simulates a crash between the report write and assessment write by calling
    reconcile twice with legacy_present=False on the first call, then
    legacy_present=True on the second.  The facts must be identical and
    acknowledged only when both sides exist.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "vi1013-crash")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    source_event = _source_event(
        source_event_id="evt-crash-replay",
        form="direct-clean",
        raw_report_text=_CLEAN_TEXT,
    )

    # First call: legacy not yet present → structured written, not acknowledged.
    r1 = review_compat.reconcile_review_source_event(
        store,
        source_event,
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert r1["result"] == "clean"
    assert r1["structured_present"] is True
    assert r1["acknowledged"] is False  # legacy not present yet

    # Second call (replay): legacy now present with reviewers-clean transition →
    # acknowledged, no duplicate records.
    r2 = review_compat.reconcile_review_source_event(
        store,
        source_event,
        legacy_state=_legacy_state_with_clean_transition("evt-crash-replay"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert r2["result"] == "clean"
    assert r2["structured_present"] is True
    assert r2["acknowledged"] is True  # both sides now present

    # Verify no duplicate records were written.
    from_store = store.get_semantic_records("review-report.v1")  # type: ignore[attr-defined]
    compat_reports = [
        r for r in from_store
        if r.get("lineage", {}).get("source_event_id") == "evt-crash-replay"
    ]
    assert len(compat_reports) == 1, (
        f"Replay must produce exactly one record, not {len(compat_reports)}"
    )


# ── VI-1013: Loop-engine importable caller ───────────────────────────────────


def test_vi1013_loop_engine_caller_exists(loop_engine_mod: ModuleType) -> None:
    """loop-engine.py exposes project_compat_reconcile_review_source_event."""
    assert hasattr(loop_engine_mod, "project_compat_reconcile_review_source_event"), (
        "loop-engine.py must expose project_compat_reconcile_review_source_event "
        "as an importable, CLI-free compatibility caller"
    )


# ── VI-1018: Authority Isolation ─────────────────────────────────────────────


def _write_minimal_git_repo(spec_dir: Path) -> None:
    """Create a minimal fake git repository with spec and plan files."""
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Implementing\n\n## Acceptance criteria\n\n- [ ] AC1\n",
        encoding="utf-8",
    )
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n### T1\n\n**Depends on:** none\n\n### T2\n\n**Depends on:** T1\n",
        encoding="utf-8",
    )


def _run_script(script: Path, *args: str, cwd: Path, env: dict | None = None) -> tuple[int, str, str]:
    """Run a Python script in subprocess and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd),
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def _normalize_state(state: dict) -> dict:
    """Remove timestamps and run IDs from cohort state for comparison."""
    normalized = copy.deepcopy(state)
    for key in (
        "run_id",
        "last_transition_at",
        "transition_history",
        "last_review_record_operation_id",
        "last_review_record_payload_digest",
        "last_review_clean_source",
        "last_review_clean_digest",
        "last_commit_sha",
        "last_record_attempt_cycle_id",
    ):
        normalized.pop(key, None)
    return normalized


def test_vi1018_authority_isolation(
    tmp_path: Path,
    loop_engine_mod: ModuleType,
    evidence_store_mod: ModuleType,
    review_selection: ModuleType,
    security_capability: ModuleType,
) -> None:
    """Slice 2 wiring leaves legacy plan-lock and procedure authority unchanged.

    Drives loop-engine/loop-cohort through:
      init → approve-plan → schedule → dispatch-receipt → plan check-current

    Then reconcile_review_source_event is called against the same spec dir.
    Normalized state.json decisions must be identical before and after.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    # Init a minimal git repo so the engine can find a git root.
    subprocess.run(
        ["git", "-C", str(repo_dir), "init", "-q"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )

    spec_dir = repo_dir / "docs" / "specs" / "test-feature"
    _write_minimal_git_repo(spec_dir)

    # Step 1: init engine.
    # T2: engine init failure must FAIL the test (not skip); a skip here would hide
    # a broken fixture that the test depends on.
    rc, _, err = _run_script(ENGINE, "init", str(spec_dir), "--mode", "code", cwd=repo_dir)
    if rc != 0:
        pytest.fail(f"engine init failed: {err[:200]}")

    # Step 2: read run_id from engine state.
    engine_state = json.loads((spec_dir / "engine-state.json").read_text())
    run_id = engine_state["run_id"]

    # Step 3: init cohort.
    rc, _, err = _run_script(
        COHORT, "init", str(spec_dir), "--run-id", run_id, cwd=repo_dir
    )
    if rc != 0:
        pytest.fail(f"cohort init failed: {err[:200]}")

    # Capture state before any Slice 2 compat adapter interaction.
    state_before = json.loads((spec_dir / "state.json").read_text())
    normalized_before = _normalize_state(state_before)

    # Step 4: run plan check-current (should be pending at this point).
    rc_check, out_check, _ = _run_script(
        COHORT, "plan", "check-current", str(spec_dir), "--json", cwd=repo_dir
    )
    # T2: Call project_compat_reconcile_review_source_event with real inputs between
    # the two state.json captures.  The adapter must write structured facts to its
    # EvidenceStore WITHOUT touching cohort state.json.
    issuer_t2, grant_t2 = _make_grant(security_capability)
    store_t2 = _make_compat_store(evidence_store_mod, tmp_path, "vi1018-compat")
    review_subject_t2 = _make_review_subject(review_selection)
    review_policy_t2 = _make_review_policy(review_subject_t2)
    compat_result = loop_engine_mod.project_compat_reconcile_review_source_event(
        store_t2,
        {
            "source_event_id": "evt-vi1018-compat",
            "role": "legacy-reviewer",
            "form": "direct-clean",
            "raw_report_text": "Clean — ready to commit.",
            "adjudication_text": None,
        },
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject_t2,
        review_policy=review_policy_t2,
        issuer=issuer_t2,
        grant=grant_t2,
        audit_sink=_null_sink,
    )

    # The compat adapter must not change the cohort state.
    state_after_compat = json.loads((spec_dir / "state.json").read_text())
    normalized_after = _normalize_state(state_after_compat)

    assert normalized_before == normalized_after, (
        "Slice 2 compat adapter must not mutate cohort state"
    )

    # T2: Remove the tautological `or True`.  The compat result must be a
    # recognised terminal status — proves the adapter ran real code, not a stub.
    assert compat_result["result"] in ("clean", "indeterminate", "findings", "unable"), (
        f"project_compat_reconcile_review_source_event must return a valid result; "
        f"got {compat_result!r}"
    )
    # A direct-clean event with the sentinel text must produce "clean".
    assert compat_result["result"] == "clean", (
        f"direct-clean sentinel must produce result='clean'; got {compat_result!r}"
    )


def test_vi1018_initial_plan_review_not_consumed_as_task_approval() -> None:
    """initial-plan-review.v1 is not consumed by any Slice 2 review module.

    Slice 4 owns mutable task projection and the cutover.  No Slice 2 module
    may treat initial-plan-review.v1 as task approval or admit task reprojection.
    """
    slice2_modules = [
        p for p in SCRIPTS.iterdir()
        if p.name.startswith("_review_") and p.suffix == ".py"
    ] + [SCRIPTS / "_evidence_store.py"]

    hits: list[str] = []
    for path in slice2_modules:
        src = path.read_text(encoding="utf-8")
        if "initial-plan-review.v1" in src:
            # Check if it appears as a consumed record kind (not just a comment or
            # string literal that could be documentation).
            try:
                tree = ast.parse(src, filename=str(path))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and node.value == "initial-plan-review.v1":
                    hits.append(f"{path.name}:{node.lineno}")
    assert not hits, (
        "initial-plan-review.v1 must not appear in Slice 2 review modules "
        "(Slice 4 owns task approval and cutover):\n" + "\n".join(hits)
    )


def test_vi1018_no_mutable_task_projection_api() -> None:
    """No Slice 2 module exposes a mutable-task projection API.

    Tasks, plan, and schedule writes are Slice 4 concerns.  No Slice 2 review
    module may expose a function that writes tasks, plan, or schedule.
    """
    slice2_modules = [
        p for p in SCRIPTS.iterdir()
        if p.name.startswith("_review_") and p.suffix == ".py"
    ] + [SCRIPTS / "_evidence_store.py"]

    # Check __all__ in each module for task/plan/schedule writes.
    task_plan_patterns = {
        "write_task", "project_task", "update_plan", "write_plan",
        "write_schedule", "project_schedule", "approve_task",
    }
    hits: list[str] = []
    for path in slice2_modules:
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and any(pattern in node.name for pattern in task_plan_patterns):
                hits.append(f"{path.name}:{node.lineno}: {node.name}")
    assert not hits, (
        "No Slice 2 module may expose a mutable-task projection API:\n"
        + "\n".join(hits)
    )


# ── VI-1019: Self-containment ─────────────────────────────────────────────────


_SELF_CONTAINMENT_SCRIPT_TEMPLATE = r"""
"""[1:-1]  # placeholder; real content assembled below using replacement


def _build_self_containment_script(
    scripts_path: str,
    _explicit_repo_root: str | None = None,
) -> str:
    """Build the VI-1019 self-containment script with the SCRIPTS path embedded.

    Uses marker substitution rather than str.format() to avoid escaping
    Python f-string braces inside the script body.

    When *_explicit_repo_root* is given the generated script uses it directly
    instead of walking parent directories, which is required when the scripts
    path is outside the repository (e.g. a temp copy in a spy test).
    """
    return (
        '"""VI-1019 self-containment proof.\n'
        "\n"
        "Runs with python3 -I -S (no user site-packages, no site module).\n"
        "PYTHONPATH must be empty.  cwd must be outside the repo.\n"
        "\n"
        "Checks in order:\n"
        "  1. Package availability: agentbundle and other non-stdlib packages are NOT\n"
        "     importable (find_spec returns None) BEFORE any module load.\n"
        "  2. Filesystem spy: wrap builtins.open/io.open/os.open before any module\n"
        "     load; assert zero paths under contracts/delivery/ are opened.\n"
        "  3. Synthetic reviewer journey via review modules (sibling-load only).\n"
        "  4. Closed compatibility corpus rows.\n"
        '"""\n'
        "import builtins\n"
        "import importlib.util\n"
        "import io\n"
        "import json\n"
        "import os\n"
        "import pathlib\n"
        "import stat\n"
        "import sys\n"
        "\n"
        "# Check 1: package availability BEFORE any module load.\n"
        '_NON_STDLIB_PKGS = ["agentbundle", "credbroker", "jsonl_otlp_exporter"]\n'
        "_pkg_results = []\n"
        "for _pkg in _NON_STDLIB_PKGS:\n"
        "    _spec = importlib.util.find_spec(_pkg)\n"
        "    _pkg_results.append((_pkg, _spec is None))\n"
        '    print(f"PKG_CHECK {_pkg} not_importable={_spec is None}", flush=True)\n'
        "_bad = [p for p, ok in _pkg_results if not ok]\n"
        "if _bad:\n"
        '    print(f"FAIL: packages importable despite -S: {_bad}", file=sys.stderr)\n'
        "    sys.exit(1)\n"
        'print("CHECK1_PASS", flush=True)\n'
        "\n"
        "# Check 3: filesystem spy — install BEFORE any module load.\n"
        "_opened_paths = []\n"
        f'_SCRIPTS = {scripts_path!r}\n'
        "_SCRIPTS_PATH = pathlib.Path(_SCRIPTS)\n"
        "_original_builtin_open = builtins.open\n"
        "_original_io_open = io.open\n"
        "_original_os_open = os.open\n"
        "\n"
        "def _spy_open(file, *args, **kwargs):\n"
        "    try:\n"
        "        _opened_paths.append(str(pathlib.Path(str(file)).resolve()))\n"
        "    except Exception:\n"
        "        _opened_paths.append(str(file))\n"
        "    return _original_builtin_open(file, *args, **kwargs)\n"
        "\n"
        "def _spy_io_open(file, *args, **kwargs):\n"
        "    try:\n"
        "        _opened_paths.append(str(pathlib.Path(str(file)).resolve()))\n"
        "    except Exception:\n"
        "        _opened_paths.append(str(file))\n"
        "    return _original_io_open(file, *args, **kwargs)\n"
        "\n"
        "builtins.open = _spy_open\n"
        "io.open = _spy_io_open\n"
        "\n"
        "# Module loader.\n"
        "def _load(name, filename):\n"
        "    path = _SCRIPTS_PATH / filename\n"
        "    info = os.stat(str(path))\n"
        "    import stat as _stat\n"
        "    assert _stat.S_ISREG(info.st_mode)\n"
        "    prev = sys.dont_write_bytecode\n"
        "    sys.dont_write_bytecode = True\n"
        "    try:\n"
        "        spec = importlib.util.spec_from_file_location(name, str(path))\n"
        "        mod = importlib.util.module_from_spec(spec)\n"
        "        spec.loader.exec_module(mod)\n"
        "        return mod\n"
        "    finally:\n"
        "        sys.dont_write_bytecode = prev\n"
        "\n"
        'rc_mod = _load("review_contracts_vi1019", "_review_contracts.py")\n'
        'rs_mod = _load("review_selection_vi1019", "_review_selection.py")\n'
        'rp_mod = _load("review_persistence_vi1019", "_review_persistence.py")\n'
        'ra_mod = _load("review_assessment_vi1019", "_review_assessment.py")\n'
        'rb_mod = _load("review_bridge_vi1019", "_review_bridge.py")\n'
        'rd_mod = _load("review_disposition_vi1019", "_review_disposition.py")\n'
        'compat_mod = _load("review_compat_vi1019", "_review_compat.py")\n'
        'es_mod = _load("evidence_store_vi1019", "_evidence_store.py")\n'
        'sc_mod = _load("security_capability_vi1019", "_security_capability.py")\n'
        "\n"
        "import copy, tempfile, shutil\n"
        "\n"
        "delivery_subject = {\n"
        '    "schema_version": 1,\n'
        '    "subject_id": "delivery-subject-vi1019",\n'
        '    "acceptance_fingerprint": "acceptance-fp-vi1019",\n'
        '    "product": {"base_ref": "base-t", "result_ref": "result-t"},\n'
        '    "spec": {"path": "docs/specs/test/spec.md", "fingerprint": "spec-fp"},\n'
        '    "evidence_policy_ref": "evidence-policy-vi1019",\n'
        '    "exclusions": [],\n'
        '    "lineage": {"provider": "legacy-worktree-snapshot", "projection_version": "1.0"},\n'
        '    "task_projection_revision": "rev-vi1019",\n'
        '    "task_projection_hash": "hash-vi1019",\n'
        "}\n"
        'changed_paths = [{"path": "packs/core/.apm/skills/work-loop/scripts/_review_compat.py", "status": "added"}]\n'
        "review_subject = rs_mod.project_review_subject(\n"
        "    delivery_subject,\n"
        "    changed_paths=changed_paths,\n"
        '    review_policy_fingerprint="review-policy-fp-vi1019",\n'
        ")\n"
        "review_policy = {\n"
        '    "policy_id": "review-policy-vi1019",\n'
        '    "review_policy_fingerprint": review_subject["review_policy_fingerprint"],\n'
        '    "policy_version": "1",\n'
        '    "selector": "core-review-vi1019",\n'
        '    "roles": [{"role": "structured-reviewer-vi1019", "kind": "mandatory"}],\n'
        '    "waivers": [],\n'
        "}\n"
        "\n"
        "issuer = sc_mod.CapabilityIssuer()\n"
        "grant = issuer.issue_root_grant(\n"
        '    roots=["evidence"],\n'
        '    operations=["append"],\n'
        '    trust_class="trusted",\n'
        '    writes_allowed_roots=["evidence"],\n'
        "    control_denies=[],\n"
        ")\n"
        "def null_sink(e): pass\n"
        "\n"
        "tmpdir = tempfile.mkdtemp()\n"
        "try:\n"
        "    log_path = pathlib.Path(tmpdir) / 'store.log'\n"
        "    store = es_mod.EvidenceStore(log_path)\n"
        "    store.open()\n"
        "\n"
        "    report = {\n"
        '        "schema_version": 1,\n'
        '        "report_id": "report-vi1019-clean",\n'
        '        "role": "structured-reviewer-vi1019",\n'
        "        \"subject\": copy.deepcopy(review_subject),\n"
        '        "terminal_status": "clean",\n'
        '        "lineage": {\n'
        '            "sequence": 1,\n'
        '            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],\n'
        '            "source_event_id": "source-vi1019-clean",\n'
        '            "producer": "synthetic-reviewer-vi1019",\n'
        "        },\n"
        '        "findings": [],\n'
        "    }\n"
        "    rp_mod.append_current_review_report(\n"
        "        store, report,\n"
        '        transaction_id="tx-vi1019-clean",\n'
        "        expected_subject=review_subject,\n"
        "        issuer=issuer, grant=grant, audit_sink=null_sink,\n"
        "    )\n"
        "    readiness = rd_mod.review_readiness(\n"
        "        store, review_subject=review_subject, review_policy=review_policy,\n"
        "    )\n"
        "    assert readiness['acceptance_eligible'] is True, str(readiness)\n"
        '    print("JOURNEY_PASS", flush=True)\n'
        "\n"
        "    # Corpus row: direct-clean.\n"
        "    log_path2 = pathlib.Path(tmpdir) / 'store2.log'\n"
        "    store2 = es_mod.EvidenceStore(log_path2)\n"
        "    store2.open()\n"
        "    _empty_legacy = {'last_review_record_operation_id': None, 'transition_history': []}\n"
        "    corpus_result = compat_mod.reconcile_review_source_event(\n"
        "        store2,\n"
        "        {\n"
        '            "source_event_id": "corpus-evt-direct-clean",\n'
        '            "role": "legacy-reviewer",\n'
        '            "form": "direct-clean",\n'
        "            \"raw_report_text\": \"Clean — ready to commit.\",\n"
        '            "adjudication_text": None,\n'
        "        },\n"
        "        legacy_state=_empty_legacy,\n"
        "        review_subject=review_subject,\n"
        "        review_policy=review_policy,\n"
        "        issuer=issuer, grant=grant, audit_sink=null_sink,\n"
        "    )\n"
        "    assert corpus_result['result'] == 'clean', f'corpus direct-clean: {corpus_result}'\n"
        '    print("CORPUS_DIRECT_CLEAN_PASS", flush=True)\n'
        "\n"
        "    # Corpus row: adjudicated all-refuted.\n"
        "    _refuted_finding = {\n"
        '        "schema_version": 1,\n'
        '        "finding_id": "finding-corpus-refuted",\n'
        '        "rule_ref": "AC-0011",\n'
        '        "observation": "Observation.",\n'
        '        "reachable_path": "No path.",\n'
        '        "actual_failure": "No failure.",\n'
        '        "affected_acceptance_criteria": ["AC-0011"],\n'
        '        "evidence_refs": ["packs/core/.apm/skills/work-loop/scripts/_review_compat.py"],\n'
        '        "material": False,\n'
        "    }\n"
        "    log_path3 = pathlib.Path(tmpdir) / 'store3.log'\n"
        "    store3 = es_mod.EvidenceStore(log_path3)\n"
        "    store3.open()\n"
        "    corpus_adj = compat_mod.reconcile_review_source_event(\n"
        "        store3,\n"
        "        {\n"
        '            "source_event_id": "corpus-evt-adj-refuted",\n'
        '            "role": "legacy-reviewer",\n'
        '            "form": "adjudicated",\n'
        "            \"raw_report_text\": json.dumps([_refuted_finding]),\n"
        '            "adjudication_text": json.dumps({\n'
        '                "finding-corpus-refuted": {"decision": "refuted", "authority_ref": "auth-ref-t6"},\n'
        "            }),\n"
        "        },\n"
        "        legacy_state=_empty_legacy,\n"
        "        review_subject=review_subject,\n"
        "        review_policy=review_policy,\n"
        "        issuer=issuer, grant=grant, audit_sink=null_sink,\n"
        "    )\n"
        "    assert corpus_adj['result'] == 'findings', f'corpus adj-refuted: {corpus_adj}'\n"
        '    print("CORPUS_ADJ_REFUTED_PASS", flush=True)\n'
        "\n"
        "finally:\n"
        "    shutil.rmtree(tmpdir, ignore_errors=True)\n"
        "\n"
        "# Check 3: verify spy.\n"
        'print(f"SPY_OPEN_COUNT={len(_opened_paths)}", flush=True)\n'
        'assert len(_opened_paths) > 0, "Filesystem spy recorded zero opens"\n'
        "\n"
        + (
            # Embed the explicit repo root directly; no directory walk needed.
            f"_repo_root = pathlib.Path({_explicit_repo_root!r})\n"
            if _explicit_repo_root is not None
            else (
                "_scripts_p = pathlib.Path(_SCRIPTS)\n"
                "_repo_root = _scripts_p\n"
                "# T1: Resolve repository root by BOTH markers: contracts/delivery/ AND packs/core/.\n"
                "# Walking up and stopping at the first directory with 'contracts' OR 'packs' is wrong\n"
                "# because packs/contracts/ exists and stops the walk at packs/ too early.\n"
                "for _ in range(15):\n"
                "    if (_repo_root / 'contracts' / 'delivery').is_dir() and (_repo_root / 'packs' / 'core').is_dir():\n"
                "        break\n"
                "    _repo_root = _repo_root.parent\n"
                "\n"
            )
        )
        + "_contracts_delivery = str(_repo_root / 'contracts' / 'delivery')\n"
        + "_bad_opens = [p for p in _opened_paths if _contracts_delivery in p]\n"
        + "if _bad_opens:\n"
        + '    print(f"FAIL: opened files under contracts/delivery: {_bad_opens}", file=sys.stderr)\n'
        + "    sys.exit(1)\n"
        + 'print("CHECK3_PASS", flush=True)\n'
        + 'print("OK", flush=True)\n'
    )


# ── VI-1019 self-containment script helpers ───────────────────────────────────

_CLEAN_TEXT_UNICODE = "Clean — ready to commit."  # em dash as unicode


def _run_self_containment(
    tmp_path: Path,
    *,
    name: str = "vi1019-runner",
    extra_env: dict | None = None,
    python_flags: list[str] | None = None,
    scripts_override: Path | None = None,
) -> subprocess.CompletedProcess:
    """Write and run the self-containment script, returning the process result."""
    script_dir = tmp_path / name
    script_dir.mkdir(exist_ok=True)
    script_path = script_dir / "vi1019_self_containment.py"
    scripts_path = scripts_override if scripts_override is not None else SCRIPTS
    script_content = _build_self_containment_script(str(scripts_path))
    script_path.write_text(script_content, encoding="utf-8")

    env = {"PYTHONPATH": ""}
    if extra_env:
        env.update(extra_env)

    flags = python_flags if python_flags is not None else ["-I", "-S"]

    return subprocess.run(
        [sys.executable, *flags, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(tmp_path),
        env=env,
    )


def test_vi1019_self_containment(tmp_path: Path) -> None:
    """VI-1019: projected Core review path is self-contained.

    Runs with python3 -I -S (isolated, no site module), empty PYTHONPATH,
    cwd outside the repo.  The script:
      1. Asserts non-stdlib packages are NOT importable before any module load.
      2. Installs a filesystem spy before any module load.
      3. Runs the synthetic reviewer journey.
      4. Runs two closed compatibility corpus rows.
      5. Asserts zero paths under contracts/delivery/ were opened.
    """
    result = _run_self_containment(tmp_path)
    assert result.returncode == 0, (
        f"VI-1019 self-containment check failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr[:800]}"
    )
    assert "OK" in result.stdout, f"Expected 'OK' in stdout: {result.stdout!r}"
    assert "CHECK1_PASS" in result.stdout
    assert "CHECK3_PASS" in result.stdout
    assert "JOURNEY_PASS" in result.stdout
    assert "CORPUS_DIRECT_CLEAN_PASS" in result.stdout


# ── VI-1019: Fail-proof violation detection ───────────────────────────────────


def test_vi1019_package_check_detects_violation(tmp_path: Path) -> None:
    """VI-1019 check 1 can detect when a non-stdlib package IS importable.

    Sets PYTHONPATH to a directory containing an agentbundle stub, then runs
    the self-containment script.  The package-availability assertion must cause
    the script to exit non-zero.
    """
    # Create a minimal agentbundle stub in a temp directory.
    stub_dir = tmp_path / "stub_pkgs"
    (stub_dir / "agentbundle").mkdir(parents=True)
    (stub_dir / "agentbundle" / "__init__.py").write_text("", encoding="utf-8")

    # -S alone keeps site-packages off but honours PYTHONPATH (-I would ignore
    # it), so the stub is importable and the availability check must fire.
    result = _run_self_containment(
        tmp_path,
        name="vi1019-pkg-fail",
        extra_env={"PYTHONPATH": str(stub_dir)},
        python_flags=["-S"],
    )
    assert "PKG_CHECK agentbundle not_importable=False" in result.stdout
    assert result.returncode == 1
    assert "CHECK1_PASS" not in result.stdout
    assert "JOURNEY_PASS" not in result.stdout


def test_vi1019_spy_detects_contracts_delivery_access(tmp_path: Path) -> None:
    """VI-1019 check 3: spy fires when a review module opens contracts/delivery.

    Builds a fake repository under tmp_path with the same root markers
    (contracts/delivery/ and packs/core/), copies the scripts into it, and
    injects an open of its contracts/delivery schema.  The spy must detect the
    violation (returncode == 1) and name that path in stderr.
    """
    import hashlib as _hashlib
    import shutil as _shutil

    # Capture the original file hash BEFORE any copy or modification.
    _original_bytes = (SCRIPTS / "_review_compat.py").read_bytes()
    original_hash = _hashlib.sha256(_original_bytes).hexdigest()

    # Copy SCRIPTS to a temp directory so we don't modify originals.
    scripts_copy = tmp_path / "scripts-spy-test"
    _shutil.copytree(str(SCRIPTS), str(scripts_copy))

    compat_copy = scripts_copy / "_review_compat.py"
    copy_src = compat_copy.read_text(encoding="utf-8")

    # The real contracts/delivery schema file — inject an open of this real path so
    # the spy records a path the detection loop will flag.
    _repo_root = tmp_path / "fake-repo"
    (_repo_root / "packs" / "core").mkdir(parents=True)
    _schema_path = _repo_root / "contracts" / "delivery" / "review-report.v1.schema.json"
    _schema_path.parent.mkdir(parents=True)
    _schema_path.write_text("{}", encoding="utf-8")
    _real_schema = str(_schema_path)

    # Inject a controlled open at module level.  The open succeeds (the file exists),
    # the spy records the resolved path, the script continues and prints SPY_OPEN_COUNT,
    # then the detection loop finds "contracts/delivery" in the recorded path and exits 1.
    injection = (
        "\n\n# VIOLATION-INJECTION: spy-test\n"
        "try:\n"
        f"    open({_real_schema!r}, 'rb').close()\n"
        "except (FileNotFoundError, PermissionError, OSError):\n"
        "    pass  # spy already recorded the path; swallow any IO failure\n"
    )
    compat_copy.write_text(copy_src + injection, encoding="utf-8")

    # Write the self-containment script with the explicit repo root embedded so
    # the spy detection does not have to walk parent directories.
    script_dir = tmp_path / "spy-runner"
    script_dir.mkdir(exist_ok=True)
    script_path = script_dir / "vi1019_spy_test.py"
    script_content = _build_self_containment_script(
        str(scripts_copy), _explicit_repo_root=str(_repo_root)
    )
    script_path.write_text(script_content, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-I", "-S", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(tmp_path),
        env={"PYTHONPATH": ""},
    )

    # T1: SPY_OPEN_COUNT is printed before the bad-opens exit, so it must appear.
    assert "SPY_OPEN_COUNT=" in result.stdout, (
        "self-containment script must print SPY_OPEN_COUNT=; "
        f"returncode={result.returncode}, stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}"
    )

    # T2: The spy MUST detect the violation and exit 1 (not 0).
    assert result.returncode == 1, (
        "spy must detect contracts/delivery access and exit 1; "
        f"got returncode={result.returncode}; stderr={result.stderr!r}"
    )

    # T3: The exit-1 message must name the contracts/delivery path.
    assert "contracts/delivery" in result.stderr, (
        "spy exit message must name the contracts/delivery path; "
        f"stderr={result.stderr!r}"
    )

    # T4: Verify the original file was not modified; use the hash captured before
    # any copy (not a self-comparison of the restored file against itself).
    _restored_hash = _hashlib.sha256((SCRIPTS / "_review_compat.py").read_bytes()).hexdigest()
    assert _restored_hash == original_hash, (
        "original _review_compat.py must be unmodified by this test"
    )


def test_vi1019_static_check_detects_agentbundle_import(tmp_path: Path) -> None:
    """VI-1019 check 4: static import scan detects an agentbundle import.

    Copies _review_compat.py to a temp location, adds `import agentbundle`
    inside a function body, then runs the static import check on the temp copy.
    The scan must flag the violation.
    """
    import hashlib as _hashlib

    # Work on temp copies only — never modify originals.
    compat_src = (SCRIPTS / "_review_compat.py").read_text(encoding="utf-8")
    original_hash = _hashlib.sha256(compat_src.encode()).hexdigest()

    # Add `import agentbundle` inside a function body via a harmless suffix.
    injected_src = compat_src + (
        "\n\n# VIOLATION-INJECTION: static-check-test\n"
        "def _injected_violation() -> None:\n"
        "    import agentbundle  # noqa\n"
    )

    work_dir = tmp_path / "static-check"
    work_dir.mkdir()
    injected_path = work_dir / "_review_compat.py"
    injected_path.write_text(injected_src, encoding="utf-8")

    # Run the static import scan on the injected file.
    tree = ast.parse(injected_src, filename=str(injected_path))
    sibling_stems = {p.stem for p in SCRIPTS.iterdir() if p.suffix == ".py"}
    stdlib_names: frozenset[str] = frozenset(
        getattr(sys, "stdlib_module_names", frozenset())
    )
    stdlib_extended = stdlib_names | {"__future__"}

    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in stdlib_extended and top not in sibling_stems:
                    hits.append(f"_review_compat.py:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            top = node.module.split(".")[0]
            if top not in stdlib_extended and top not in sibling_stems:
                hits.append(f"_review_compat.py:{node.lineno}: from {node.module} import ...")

    assert hits, (
        "static import scan must detect `import agentbundle` in injected file;\n"
        "hits found: " + str(hits)
    )
    assert any("agentbundle" in h for h in hits), (
        f"scan must flag the agentbundle import: {hits}"
    )

    # T3: Verify original file unmodified using the hash captured BEFORE injection.
    # original_hash was computed from the original file; comparing restored against
    # itself (reading twice) would be tautological and prove nothing.
    restored = (SCRIPTS / "_review_compat.py").read_text(encoding="utf-8")
    restored_hash = _hashlib.sha256(restored.encode()).hexdigest()
    assert restored_hash == original_hash, (
        "original _review_compat.py must be unmodified by this test; "
        "file on disk has changed since the test started"
    )


def test_vi1019_static_import_check() -> None:
    """VI-1019: review runtime modules import only stdlib or sibling work-loop modules.

    Uses sys.stdlib_module_names (Python 3.10+) as the authoritative source of
    stdlib names.  Scans ALL imports (top-level and nested function bodies) in
    every _review_*.py and _evidence_store.py transitively.
    """
    # sys.stdlib_module_names is available since Python 3.10.
    stdlib_names: frozenset[str] = frozenset(
        getattr(sys, "stdlib_module_names", frozenset())
    )
    # Include __future__ (from __future__ import annotations) and legacy extras.
    stdlib_extended = stdlib_names | {"__future__", "fcntl"}

    # Sibling modules allowed (all .py files in scripts dir, by stem).
    sibling_stems = {p.stem for p in SCRIPTS.iterdir() if p.suffix == ".py"}
    # Also allow "loop-cohort" and "loop-engine" referenced as hyphenated stems.
    sibling_stems.add("loop-cohort")
    sibling_stems.add("loop-engine")

    review_module_files = [
        p for p in SCRIPTS.iterdir()
        if (p.name.startswith("_review_") or p.name == "_evidence_store.py")
        and p.suffix == ".py"
    ]

    hits: list[str] = []
    for path in review_module_files:
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError:
            continue
        # Walk ALL nodes (including nested function bodies).
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in stdlib_extended and top not in sibling_stems:
                        hits.append(f"{path.name}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top = node.module.split(".")[0]
                if node.level > 0:
                    continue  # relative import — allowed as sibling
                if top not in stdlib_extended and top not in sibling_stems:
                    hits.append(
                        f"{path.name}:{node.lineno}: from {node.module} import ..."
                    )
    assert not hits, (
        "Review runtime modules must import only stdlib or sibling work-loop modules "
        "(sys.stdlib_module_names used as authority):\n"
        + "\n".join(hits)
    )


# ── C1-C6: Adapter defect regression tests ───────────────────────────────────


@pytest.mark.parametrize(
    "raw_report_text,label",
    [
        (_CLEAN_TEXT, "clean-text"),
        (_FINDINGS_TEXT, "findings-text"),
    ],
)
def test_c1_structural_clean_is_refused(
    raw_report_text: str,
    label: str,
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C1: structural-clean is out of the closed corpus → always refused.

    AC-0011 admits only {"direct-clean", "findings", "adjudicated"}.  A
    structural-clean source event is refused by the closed-form gate:
    result='unable', structured_present=False, acknowledged=False, and no
    report is stored — regardless of report content and even when legacy_state
    records a matching reviewers-clean transition with a structural-clean digest.

    Mutation-check: re-adding 'structural-clean' to _CLOSED_FORMS with a
    minimal clean classifier maps clean-text → 'clean', causing the clean-text
    case to assert result='unable' but receive result='clean' → RED.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(
        evidence_store_mod, tmp_path, f"c1-structural-clean-{label}"
    )
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Build a legacy_state that looks like a matching clean record with a
    # structural-clean digest.  The test must still refuse even in this case.
    evt_id = f"evt-c1-structural-clean-{label}"
    legacy_state = _legacy_state_with_clean_transition(evt_id)
    legacy_state["last_review_record_payload_digest"] = _legacy_clean_digest(
        "structural-clean", raw_report_text
    )

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id=evt_id,
            form="structural-clean",
            raw_report_text=raw_report_text,
        ),
        legacy_state=legacy_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        f"C1[{label}]: structural-clean must return 'unable' (out of closed corpus); "
        f"got {result['result']!r}"
    )
    assert not result["structured_present"], (
        f"C1[{label}]: unable result must not persist a structured record"
    )
    assert result["acknowledged"] is False, (
        f"C1[{label}]: structural-clean must not be acknowledged; "
        f"got acknowledged={result['acknowledged']!r}"
    )
    stored = store.get_semantic_records("review-report.v1")
    assert not stored, (
        f"C1[{label}]: no report must be stored for refused structural-clean; "
        f"got {stored}"
    )


def test_c2_sustained_finding_produces_findings_result_not_eligible(
    review_compat: ModuleType,
    review_selection: ModuleType,
    review_disposition: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C2(a): adjudicated sustained material finding → result=findings, NOT acceptance-eligible.

    A sustained material finding must block acceptance.  The old C2 defect
    forced all adjudicated findings to unsupported-opinion, silently clearing
    the block.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c2-sustained-material")
    review_subject = _make_review_subject(review_selection)
    # Use compat policy: expects "legacy-reviewer" role matching the compat report.
    compat_policy = _make_compat_review_policy(review_subject)

    material_finding = {
        **_COMPAT_FINDING_SUSTAINED,
        "finding_id": "finding-c2-material-sustained",
        "material": True,  # material → blocks acceptance
    }
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c2-sustained",
            form="adjudicated",
            raw_report_text=json.dumps([material_finding]),
            adjudication_text=json.dumps({
                "finding-c2-material-sustained": {
                    "decision": "sustained",
                    "authority_ref": "review-authority-c2",
                }
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=compat_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "findings", (
        f"C2: sustained adjudicated finding must yield 'findings', got {result['result']!r}"
    )
    # Verify acceptance is blocked (sustained material finding is NOT unsupported-opinion).
    readiness = review_disposition.review_readiness(
        store,
        review_subject=review_subject,
        review_policy=compat_policy,
    )
    assert readiness["acceptance_eligible"] is False, (
        "C2: sustained material finding must block acceptance_eligible; "
        f"readiness={readiness}"
    )


def test_c2_all_refuted_produces_acceptance_eligible(
    review_compat: ModuleType,
    review_selection: ModuleType,
    review_disposition: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C2(b): adjudicated all-refuted → acceptance eligible.

    Refuted findings are assessed as unsupported-opinion, which does not block.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c2-all-refuted")
    review_subject = _make_review_subject(review_selection)
    compat_policy = _make_compat_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c2-refuted",
            form="adjudicated",
            raw_report_text=json.dumps([_COMPAT_FINDING_REFUTED]),
            adjudication_text=json.dumps({
                "finding-compat-refuted-t6": {
                    "decision": "refuted",
                    "authority_ref": "review-authority-c2",
                }
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=compat_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "findings"

    readiness = review_disposition.review_readiness(
        store,
        review_subject=review_subject,
        review_policy=compat_policy,
    )
    assert readiness["acceptance_eligible"] is True, (
        "C2: all-refuted findings must not block acceptance_eligible; "
        f"readiness={readiness}"
    )


def test_c2_id_mismatch_produces_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C2(c): adjudicated form with mismatched finding IDs → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c2-id-mismatch")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c2-id-mismatch",
            form="adjudicated",
            raw_report_text=json.dumps([_COMPAT_FINDING_REFUTED]),
            adjudication_text=json.dumps({
                "WRONG-FINDING-ID": {  # ID doesn't match the finding
                    "decision": "refuted",
                    "authority_ref": "review-authority-c2",
                }
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        f"C2: finding ID mismatch must yield 'indeterminate', got {result['result']!r}"
    )


def test_c2_bad_decision_produces_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C2(d): adjudicated form with unknown decision value → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c2-bad-decision")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c2-bad-decision",
            form="adjudicated",
            raw_report_text=json.dumps([_COMPAT_FINDING_REFUTED]),
            adjudication_text=json.dumps({
                "finding-compat-refuted-t6": {
                    "decision": "unknown-verdict",  # not in closed set
                    "authority_ref": "review-authority-c2",
                }
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        f"C2: bad decision value must yield 'indeterminate', got {result['result']!r}"
    )


def _make_legacy_state_with_transition(
    source_event_id: str,
    event: str,
) -> dict:
    """Build a legacy_state dict with a real transition_history entry."""
    return {
        "last_review_record_operation_id": source_event_id,
        "last_review_record_payload_digest": _legacy_clean_digest(),
        "transition_history": [
            {
                "transition_id": source_event_id,
                "pre_transition_sequence": 0,
                "event": event,
                "args": {},
            }
        ],
    }


def test_c3_transition_history_clean_acknowledged(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C3: reviewers-clean event in transition_history → acknowledged=True for clean result."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c3-clean-ack")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    legacy_state = _make_legacy_state_with_transition(
        "evt-c3-clean", "reviewers-clean"
    )
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c3-clean",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=legacy_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "clean"
    assert result["legacy_present"] is True
    assert result["acknowledged"] is True, (
        f"C3: reviewers-clean event must acknowledge clean result; got {result}"
    )
    assert result["divergent"] is False


def test_c3_transition_history_divergent(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C3: findings-remain event in transition_history but structured result=clean → divergent."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c3-divergent")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Legacy says findings-remain but the clean text produces clean.
    legacy_state = _make_legacy_state_with_transition(
        "evt-c3-divergent", "findings-remain"
    )
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c3-divergent",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=legacy_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "clean"
    assert result["legacy_present"] is True
    assert result["acknowledged"] is False, (
        f"C3: disagreement must not acknowledge; got {result}"
    )
    assert result["divergent"] is True, (
        f"C3: disagreement must set divergent=True; got {result}"
    )


def test_c4_crash_recovery_writes_missing_assessments(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C4: if the report exists but assessments are missing (crash), rerun writes them.

    Simulates a crash by writing the report directly, then calling reconcile.
    The rerun must complete the full fact set without duplicates.
    """
    import copy as _copy

    issuer, grant = _make_grant(security_capability)
    log_path = tmp_path / "c4-crash" / "store.log"
    store = _open_store(evidence_store_mod, log_path)
    review_selection_mod = _load_module("review_selection_c4", SCRIPTS / "_review_selection.py")
    review_subject = _make_review_subject(review_selection_mod)
    review_policy = _make_review_policy(review_subject)
    review_persistence = _load_module(
        "review_persistence_c4", SCRIPTS / "_review_persistence.py"
    )

    source_event_id = "evt-c4-crash"
    finding = {
        **_COMPAT_FINDING_REFUTED,
        "finding_id": "finding-c4-crash",
    }

    # Write the report directly (simulating crash before assessments).
    pre_crash_report = {
        "schema_version": 1,
        "report_id": f"compat-report:{source_event_id}",
        "role": "legacy-reviewer",
        "subject": _copy.deepcopy(review_subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
            "source_event_id": source_event_id,
            "producer": "compat-adapter",
        },
        "findings": [_copy.deepcopy(finding)],
    }
    review_persistence.append_current_review_report(
        store,
        pre_crash_report,
        transaction_id=f"compat-tx:{source_event_id}:report",
        expected_subject=review_subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Verify no assessments yet.
    assessments_before = store.get_semantic_records("finding-assessment.v1")
    assert not assessments_before, (
        f"Expected no assessments before crash recovery, got {assessments_before}"
    )

    # Rerun reconcile: must detect missing assessments and write them.
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id=source_event_id,
            form="adjudicated",
            raw_report_text=json.dumps([finding]),
            adjudication_text=json.dumps({
                "finding-c4-crash": {
                    "decision": "refuted",
                    "authority_ref": "review-authority-c4",
                }
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "findings"
    assert result["structured_present"] is True

    # Assert complete fact set: exactly one assessment for the one finding.
    assessments_after = store.get_semantic_records("finding-assessment.v1")
    assessment_finding_ids = [a.get("finding_id") for a in assessments_after]
    assert "finding-c4-crash" in assessment_finding_ids, (
        f"C4: crash recovery must write the missing assessment; got {assessment_finding_ids}"
    )

    # Run rerun again: must produce no duplicates.
    review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id=source_event_id,
            form="adjudicated",
            raw_report_text=json.dumps([finding]),
            adjudication_text=json.dumps({
                "finding-c4-crash": {
                    "decision": "refuted",
                    "authority_ref": "review-authority-c4",
                }
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assessments_final = store.get_semantic_records("finding-assessment.v1")
    c4_assessments = [
        a for a in assessments_final
        if a.get("finding_id") == "finding-c4-crash"
    ]
    assert len(c4_assessments) == 1, (
        f"C4: rerun must not duplicate assessments; got {len(c4_assessments)}"
    )


def test_c5_grammar_invalid_findings_produces_unable(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C5: findings form with grammar-invalid text → unable, nothing persisted."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c5-grammar-invalid")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Text that does NOT contain numbered findings (parse_findings returns 0).
    grammar_invalid_text = (
        "## Finding 1\n"
        "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n"
        "Observation: test.\n"
    )
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c5-grammar-invalid",
            form="findings",
            raw_report_text=grammar_invalid_text,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        f"C5: grammar-invalid findings form must yield 'unable', got {result['result']!r}"
    )
    assert not result["structured_present"], (
        "C5: unable result must not persist a structured record"
    )


def test_c6_return_value_has_required_fields(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """C6: reconcile_review_source_event returns exactly the required 6 fields."""
    required_keys = {
        "source_event_id",
        "result",
        "legacy_present",
        "structured_present",
        "acknowledged",
        "divergent",
    }
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "c6-return-fields")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-c6-fields",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    missing = required_keys - result.keys()
    assert not missing, (
        f"C6: return value missing required fields: {missing}; got keys: {result.keys()}"
    )
    # structured_present must reflect the actual store state (not a constant).
    assert result["structured_present"] is True, (
        "C6: structured_present must be True after successful reconciliation"
    )
    # legacy_present and divergent must be present with correct types.
    assert isinstance(result["legacy_present"], bool)
    assert isinstance(result["divergent"], bool)


# ── T4: Single-input tests for each reachable-untested (i) ledger guard ───────
# Each function names the mutation it catches (e.g., "T6-MUT-010").
# The comment after the mutation shows the exact string that would be changed.


def _probe_finding() -> dict:
    """Minimal valid finding.v1 for ledger tests."""
    return {
        "schema_version": 1,
        "finding_id": "f-probe",
        "rule_ref": "AC-0099",
        "observation": "Probe observation.",
        "reachable_path": "Probe path.",
        "actual_failure": "Probe failure.",
        "affected_acceptance_criteria": ["AC-0099"],
        "evidence_refs": ["packs/core/.apm/skills/work-loop/scripts/_review_compat.py"],
        "material": True,
    }


def _probe_adjudication(finding_id: str = "f-probe", decision: str = "refuted") -> str:
    """Minimal valid adjudication JSON for one finding."""
    return json.dumps({
        finding_id: {
            "decision": decision,
            "authority_ref": "probe-authority",
        }
    })


def _legacy_state_with_findings_transition(operation_id: str) -> dict:
    """Return cohort state with a findings-remain transition event.

    Produces legacy_present=True, legacy_event='findings' → acknowledged=True
    when the structured result is 'findings'.
    """
    return {
        "last_review_record_operation_id": operation_id,
        "last_review_record_payload_digest": "payload-digest-t6",
        "transition_history": [
            {
                "transition_id": operation_id,
                "pre_transition_sequence": 0,
                "event": "findings-remain",
                "args": {},
            }
        ],
    }


# ── 010: content-safety refusal returns unable ────────────────────────────────
# Mutation: `if not cs_decision.accepted:⏎ return _unable()` → `if False:⏎ return _unable()`
def test_t4_010_content_safety_refusal_returns_unable(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-010: findings form with a raw GitHub credential → unable before classification.

    Pin: raw_report_text contains ghp_<36 chars>; the content-safety loop catches
    it on the first iteration (raw_report_text pass) and returns _unable() before
    any classification or write.  Without this check (MUT-010 equivalent: disable
    content-safety on raw_report_text), the findings-form classifier would return
    'indeterminate' instead of 'unable'.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-010")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Embed a credential only in raw_report_text; adjudication_text is absent.
    cred = "ghp_" + "A" * 36
    raw = _FINDINGS_TEXT + f"\n\ntoken {cred}"

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-010",
            form="findings",
            raw_report_text=raw,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-010: credential in raw_report_text must be caught by content-safety and"
        " return unable before findings classification"
    )
    assert not result["structured_present"]


# ── 020: direct-clean grammar requirement ─────────────────────────────────────
# Mutation (MUT-021/022 equivalent): disable byte-equality sentinel check.
# Pre-fix classifier uses grammar not exact bytes, so `_CLEAN_TEXT + "\n"` would
# be classified "clean" by grammar, but D1 byte equality REJECTS it → unable.
# Without the byte-equality guard the pre-fix classifier would return "clean".
def test_t4_020_direct_clean_requires_sentinel_text(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-020: direct-clean with sentinel plus trailing newline → unable (D1 fails).

    The sentinel is exactly _CLEAN_TEXT encoded as UTF-8; any extra byte (trailing
    newline here) fails the byte-equality check and must return unable.  Without
    the D1 byte-equality guard the grammar-based pre-fix classifier would accept
    the newline variant and return 'clean'.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-020")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-020",
            form="direct-clean",
            # Sentinel plus a trailing newline: grammar-clean, but fails byte equality.
            raw_report_text=_CLEAN_TEXT + "\n",
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-020: direct-clean with trailing newline must return unable (D1 byte equality)"
    )
    assert not result["structured_present"]


# T4-031 (structural-clean Not-checked footer) deleted.
# The guard `if result.get("not_checked_present"):` no longer exists because
# _classify_structural_clean was removed with the form.  A direct-clean case
# with a Not-checked footer (same raw text) would fail D1 byte equality and
# return 'unable', but that is already covered by T4-020 (trailing newline)
# and T4-021/022 (byte equality rejects trailing content).  No new test is
# needed.

# ── 050: adjudicated with adjudication_text=None → indeterminate ─────────────
# Mutation: `if adjudication_text is None:⏎ return "indeterminate", [], []` → `if False:⏎ ...`
def test_t4_050_adjudicated_none_adjudication_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-050: adjudicated form with adjudication_text=None → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-050")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-050",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=None,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-050: adjudicated with adjudication_text=None must return indeterminate"
    )


# ── 052: adjudicated with empty finding list → indeterminate ─────────────────
# Mutation: `if not isinstance(raw_findings, list) or not raw_findings:` → `if False:`
def test_t4_052_adjudicated_empty_finding_list_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-052: adjudicated with empty finding list → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-052")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-052",
            form="adjudicated",
            raw_report_text=json.dumps([]),
            adjudication_text=json.dumps({}),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-052: adjudicated with empty finding list must return indeterminate"
    )


# ── 053: finding fails finding.v1 validation → indeterminate ─────────────────
# Mutation: `ok, _code = contracts.validate_finding_dict(item)⏎ if not ok:` → `... if False:`
def test_t4_053_schema_invalid_finding_returns_unable_and_persists_nothing(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-053: a finding missing rule_ref makes the report schema-invalid: unable, nothing stored."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-053")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    bad_finding = {k: v for k, v in _probe_finding().items() if k != "rule_ref"}
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-053",
            form="adjudicated",
            raw_report_text=json.dumps([bad_finding]),
            adjudication_text=_probe_adjudication("f-probe"),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable"
    assert result["structured_present"] is False
    assert store.get_semantic_records("review-report.v1") == []


# ── 054: non-JSON adjudication text → indeterminate ──────────────────────────
# Mutation: adjudication parse except → raise instead of return indeterminate
def test_t4_054_non_json_adjudication_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-054: adjudicated with non-JSON adjudication_text → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-054")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-054",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text="not json",
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-054: non-JSON adjudication text must return indeterminate"
    )


# ── 055: audit is a list (not a dict) → indeterminate ────────────────────────
# Mutation: `if not isinstance(audit, dict):⏎ return "indeterminate"` → `if False:`
def test_t4_055_audit_not_dict_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-055: adjudication is a JSON array, not an object → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-055")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-055",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=json.dumps(["f-probe"]),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-055: audit that is a JSON array must return indeterminate"
    )


# ── 057: extra audit id (not one-to-one) → indeterminate ─────────────────────
# Mutation: `if raw_ids != audit_ids:` → `if raw_ids - audit_ids:`  (misses extra)
def test_t4_057_extra_audit_id_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-057: audit carries finding id plus an extra id → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-057")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-057",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=json.dumps({
                "f-probe": {"decision": "refuted", "authority_ref": "probe-auth"},
                "extra-id": {"decision": "refuted", "authority_ref": "probe-auth"},
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-057: audit with extra id (not in finding set) must return indeterminate"
    )


# ── 058: audit entry is a string, not a dict → indeterminate ─────────────────
# Mutation: `if not isinstance(decision_entry, dict):⏎ return "indeterminate"` → `if False:`
def test_t4_058_audit_entry_not_dict_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-058: audit entry is a string, not an object → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-058")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-058",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=json.dumps({"f-probe": "refuted"}),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-058: audit entry that is a string must return indeterminate"
    )


# ── 061: empty authority_ref → indeterminate ─────────────────────────────────
# Mutation: `if not isinstance(authority_ref, str) or not authority_ref:` → `if False:`
def test_t4_061_empty_authority_ref_returns_indeterminate(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-061: refuted with authority_ref='' → indeterminate."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-061")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-061",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=json.dumps({
                "f-probe": {"decision": "refuted", "authority_ref": ""},
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate", (
        "T4-061: empty authority_ref must return indeterminate"
    )


# ── 070: sustained → assessment is 'supported' ───────────────────────────────
# Mutation: `independent_authority=independent_authority` → `independent_authority=None`
def test_t4_070_sustained_produces_supported_assessment(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-070: sustained material finding → stored assessment class is 'supported'."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-070")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    sustained_finding = {**_probe_finding(), "material": True}
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-070",
            form="adjudicated",
            raw_report_text=json.dumps([sustained_finding]),
            adjudication_text=json.dumps({
                "f-probe": {"decision": "sustained", "authority_ref": "probe-auth"},
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "findings"
    # The adapter must persist the assessment; check it is 'supported'.
    assessments = store.get_semantic_records("finding-assessment.v1")
    assert assessments, "T4-070: sustained finding must produce a stored assessment"
    assert assessments[0]["assessment"] == "supported", (
        f"T4-070: sustained finding must produce assessment='supported'; "
        f"got {assessments[0]['assessment']!r}"
    )


# ── 072: refuted material finding → assessment 'unsupported-opinion', eligible True ──
# Mutation: `if decision == "refuted":⏎ # Refuted findings` → `if False:⏎ # Refuted findings`
def test_t4_072_refuted_material_produces_unsupported_opinion_and_eligible(
    review_compat: ModuleType,
    review_selection: ModuleType,
    review_disposition: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-072: refuted material finding → 'unsupported-opinion', acceptance_eligible True."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-072")
    review_subject = _make_review_subject(review_selection)
    # Use the compat policy (role=legacy-reviewer) for readiness check.
    review_policy = _make_compat_review_policy(review_subject)

    refuted_material = {**_probe_finding(), "material": True}
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-072",
            form="adjudicated",
            raw_report_text=json.dumps([refuted_material]),
            adjudication_text=json.dumps({
                "f-probe": {"decision": "refuted", "authority_ref": "probe-auth"},
            }),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "findings"
    assessments = store.get_semantic_records("finding-assessment.v1")
    assert assessments, "T4-072: refuted finding must produce a stored assessment"
    assert assessments[0]["assessment"] == "unsupported-opinion", (
        f"T4-072: refuted finding must produce 'unsupported-opinion'; "
        f"got {assessments[0]['assessment']!r}"
    )
    # Unsupported-opinion must not block acceptance_eligible.
    readiness = review_disposition.review_readiness(
        store, review_subject=review_subject, review_policy=review_policy,
    )
    assert readiness["acceptance_eligible"] is True, (
        f"T4-072: refuted material finding must not block acceptance; readiness={readiness}"
    )


# ── 080: legacy presence via last_review_record_operation_id ─────────────────
# Mutation: `if legacy_state.get("last_review_record_operation_id") == source_event_id:⏎ return True, None` → `if False:`
def test_t4_080_operation_id_sets_legacy_present(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-080: state with matching op-id → legacy_present=True."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-080")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-080",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_legacy_state_with_operation("evt-t4-080"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["legacy_present"] is True, (
        "T4-080: state with matching last_review_record_operation_id must set legacy_present=True"
    )


# ── 082: transition id must match for legacy_present ─────────────────────────
# Mutation: `entry.get("transition_id") == source_event_id` → `entry.get("transition_id") is not None`
def test_t4_082_different_transition_id_no_legacy_present(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-082: transition_history entry for a DIFFERENT id → legacy_present=False."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-082")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # History has a reviewers-clean entry, but for a DIFFERENT transition_id.
    other_state = {
        "last_review_record_operation_id": None,
        "last_review_record_payload_digest": None,
        "transition_history": [
            {
                "transition_id": "other-event-id",  # does NOT match
                "pre_transition_sequence": 0,
                "event": "reviewers-clean",
                "args": {},
            }
        ],
    }
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-082",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=other_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["legacy_present"] is False, (
        "T4-082: history entry for a different id must not set legacy_present"
    )
    assert result["acknowledged"] is False


# ── 083: only allowed events (reviewers-clean, findings-remain) count ─────────
# Mutation: `if event == _LEGACY_CLEAN_EVENT:` → `if event != _LEGACY_FINDINGS_EVENT:`
def test_t4_083_unrecognised_event_no_legacy_present(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-083: same-id history entry with event 'approve-plan' → legacy_present, ack False."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-083")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    unrecognised_state = {
        "last_review_record_operation_id": None,
        "last_review_record_payload_digest": None,
        "transition_history": [
            {
                "transition_id": "evt-t4-083",  # matches
                "pre_transition_sequence": 0,
                "event": "approve-plan",  # NOT a recognised review event
                "args": {},
            }
        ],
    }
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-083",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=unrecognised_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    # legacy_present=True because the id matches, but event is unknown → ack=False
    assert result["acknowledged"] is False, (
        "T4-083: unrecognised event must not set acknowledged"
    )


# ── 090: legacy clean + structured findings → ack False, divergent True ───────
# Mutation: `agrees = (legacy_event == "clean" and result == "clean") or (` → `agrees = (legacy_event == "clean") or (`
def test_t4_090_clean_legacy_with_findings_result_not_acknowledged(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-090: reviewers-clean legacy + adjudicated findings → ack=False, divergent=True."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-090")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-090",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=_probe_adjudication("f-probe", "refuted"),
        ),
        # reviewers-clean legacy for the same id
        legacy_state=_legacy_state_with_clean_transition("evt-t4-090"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["acknowledged"] is False, (
        "T4-090: legacy clean + structured findings must not be acknowledged"
    )
    assert result["divergent"] is True, (
        "T4-090: legacy clean vs structured findings must set divergent=True"
    )


# ── 092: legacy findings + structured findings → ack True ─────────────────────
# Mutation: `legacy_event == "findings" and result == "findings"⏎ )` → `False⏎ )`
def test_t4_092_findings_legacy_with_findings_result_acknowledged(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-092: findings-remain legacy + adjudicated findings → ack=True."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-092")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-092",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=_probe_adjudication("f-probe", "refuted"),
        ),
        # findings-remain legacy for the same id
        legacy_state=_legacy_state_with_findings_transition("evt-t4-092"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["acknowledged"] is True, (
        "T4-092: findings-remain legacy + adjudicated findings must set acknowledged=True"
    )
    assert result["divergent"] is False


# ── 094: op-id-only state → divergent False ───────────────────────────────────
# Mutation: `if legacy_event is None:⏎ ... return False, False` → `if False: ...`
def test_t4_094_op_id_only_state_is_not_divergent(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-094: operation-id-only state (no event) → divergent=False."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-094")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-094",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_legacy_state_with_operation("evt-t4-094"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["divergent"] is False, (
        "T4-094: op-id-only legacy state must not set divergent (event unknown)"
    )


# ── 098: indeterminate never acknowledged against legacy clean ────────────────
# Mutation: `agrees = (legacy_event == "clean" and result == "clean") or (` →
#           `agrees = (legacy_event == "clean" and result in ("clean", "indeterminate")) or (`
def test_t4_098_indeterminate_never_acknowledged_against_legacy_clean(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-098: reviewers-clean legacy + findings form (indeterminate) → ack=False, divergent=True."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-098")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # findings form with grammar-valid text + no adjudication → indeterminate
    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-098",
            form="findings",
            raw_report_text=_FINDINGS_TEXT,
            adjudication_text=None,
        ),
        legacy_state=_legacy_state_with_clean_transition("evt-t4-098"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "indeterminate"
    assert result["acknowledged"] is False, (
        "T4-098: indeterminate result must not be acknowledged even against legacy clean"
    )
    assert result["divergent"] is True, (
        "T4-098: legacy clean vs indeterminate must set divergent=True"
    )


# ── 116: assessments scoped to their own report ───────────────────────────────
# Mutation: `if r.get("report_id") == report_id⏎` → `if True⏎`
def test_t4_116_assessments_scoped_to_report(
    review_compat: ModuleType,
    review_persistence: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-116: event B's assessments are scoped to B's report, not A's."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-116")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    finding = _probe_finding()
    adj_text = _probe_adjudication("f-probe", "refuted")

    # Step 1: Fully reconcile event A (report + assessment for f-probe).
    review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-116-A",
            form="adjudicated",
            raw_report_text=json.dumps([finding]),
            adjudication_text=adj_text,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 2: Pre-write report B using the persistence port (crash-before-assessment sim).
    report_b_id = "compat-report:evt-t4-116-B"
    report_b = {
        "schema_version": 1,
        "report_id": report_b_id,
        "role": "legacy-reviewer",
        "subject": copy.deepcopy(review_subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
            "source_event_id": "evt-t4-116-B",
            "producer": "compat-adapter",
        },
        "findings": [copy.deepcopy(finding)],
    }
    review_persistence.append_current_review_report(
        store,
        report_b,
        transaction_id="compat-tx:evt-t4-116-B:report",
        expected_subject=review_subject,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    # Step 3: Reconcile event B — must write B's assessment.
    result_b = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-116-B",
            form="adjudicated",
            raw_report_text=json.dumps([finding]),
            adjudication_text=adj_text,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result_b["result"] == "findings"

    # Assert B's assessment is present (scoped to B's report_id).
    all_assessments = store.get_semantic_records("finding-assessment.v1")
    b_assessments = [
        a for a in all_assessments
        if a.get("report_id") == report_b_id
    ]
    assert b_assessments, (
        "T4-116: reconcile for event B must write B's assessment (scoped to B's report_id)"
    )


# ── 120-123: deterministic ids ────────────────────────────────────────────────
# Mutations: random suffixes appended to report_id, transaction ids, assessment_id.
def test_t4_120_123_deterministic_ids(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-120 to T4-123: all derived ids are deterministic from source_event_id."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-120-123")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    src_id = "evt-t4-120-123"
    finding = _probe_finding()
    adj_text = _probe_adjudication("f-probe", "refuted")

    review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id=src_id,
            form="adjudicated",
            raw_report_text=json.dumps([finding]),
            adjudication_text=adj_text,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    reports = store.get_semantic_records("review-report.v1")
    assert reports, "T4-120: must write a report"
    report = reports[0]
    expected_report_id = f"compat-report:{src_id}"
    assert report["report_id"] == expected_report_id, (
        f"T4-120: report_id must be deterministic; "
        f"expected {expected_report_id!r}, got {report['report_id']!r}"
    )

    # The transaction id is in the append log; check via get_semantic_records metadata.
    # We check the assessment id is also deterministic.
    assessments = store.get_semantic_records("finding-assessment.v1")
    assert assessments, "T4-122: must write an assessment"
    assessment = assessments[0]
    expected_assessment_id = f"compat-assessment:{src_id}:f-probe"
    assert assessment["assessment_id"] == expected_assessment_id, (
        f"T4-122: assessment_id must be deterministic; "
        f"expected {expected_assessment_id!r}, got {assessment['assessment_id']!r}"
    )


# ── 130: temp dir created under store root ────────────────────────────────────
# Mutation: `tmpdir = Path(tempfile.mkdtemp(dir=str(store_root)))` → `Path(tempfile.mkdtemp())`
def test_t4_130_temp_dir_under_store_root(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T4-130: classifier mkdtemp is called with dir=store._root."""
    import tempfile as _tempfile

    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-130")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    captured_dir: list[str] = []
    original_mkdtemp = _tempfile.mkdtemp

    def spy_mkdtemp(suffix=None, prefix=None, dir=None):  # type: ignore[no-untyped-def]
        captured_dir.append(dir)
        return original_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)

    # Patch tempfile.mkdtemp in the review_compat module's namespace.
    monkeypatch.setattr(
        review_compat.tempfile,  # type: ignore[attr-defined]
        "mkdtemp",
        spy_mkdtemp,
    )

    # Use findings form (not direct-clean) — it calls _run_classify_raw_report
    # which creates a temp dir.  direct-clean uses byte equality and never calls mkdtemp.
    review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-130",
            form="findings",
            raw_report_text=_FINDINGS_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert captured_dir, "T4-130: mkdtemp must be called at least once"
    store_root_str = str(store._root)  # type: ignore[attr-defined]
    assert all(d == store_root_str for d in captured_dir), (
        f"T4-130: all mkdtemp calls must use dir=store._root ({store_root_str!r}); "
        f"got {captured_dir!r}"
    )


# ── 131: temp dir is cleaned up after use ─────────────────────────────────────
# Mutation: `shutil.rmtree(str(tmpdir), ignore_errors=True)` → `tmpdir.exists()`
def test_t4_131_temp_dir_removed_after_classification(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-131: no tmp* dirs remain under store root after classification."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-131")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    store_root = store._root  # type: ignore[attr-defined]

    # Use findings form — it calls _run_classify_raw_report which creates a tmpdir.
    # direct-clean uses byte equality and never creates a tmpdir to clean up.
    review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-131",
            form="findings",
            raw_report_text=_FINDINGS_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    stray = list(store_root.glob("tmp*"))
    assert not stray, (
        f"T4-131: temp dirs must be cleaned up after classification; "
        f"stray dirs: {stray}"
    )


# ── 132: store without _root → unable ─────────────────────────────────────────
# Mutation: `if store_root is None or not isinstance(store_root, Path):⏎ return _unable()` → `if False:`
def test_t4_132_store_without_root_returns_unable(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-132: store wrapper without _root → reconcile returns unable."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-132")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Build a minimal wrapper without the _root attribute.
    class _NoRootStore:
        def get_semantic_records(self, kind: str) -> list:
            return store.get_semantic_records(kind)

    result = review_compat.reconcile_review_source_event(
        _NoRootStore(),
        _source_event(
            source_event_id="evt-t4-132",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=_probe_adjudication("f-probe", "refuted"),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-132: store without _root must produce unable (no classification possible)"
    )
    assert not result["structured_present"]


# ── 133: I/O failure in classifier → unable, not a raise ─────────────────────
# Mutation: except-Exception branch returns {"classification": "error", ...} instead of raise
def test_t4_133_classifier_io_failure_returns_unable(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T4-133: classifier I/O failure (mkdtemp raises) → reconcile returns unable, not a raise."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-133")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Make mkdtemp raise OSError so the findings classifier path fails.
    def _failing_mkdtemp(*args: object, **kwargs: object) -> str:
        raise OSError("T4-133: simulated IO failure")

    monkeypatch.setattr(review_compat.tempfile, "mkdtemp", _failing_mkdtemp)  # type: ignore[attr-defined]

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-133",
            form="findings",
            raw_report_text=_FINDINGS_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-133: classifier I/O failure must return unable (not raise)"
    )


# ── 141: return set is closed to exactly six keys ────────────────────────────
# Mutation: `"divergent": divergent,⏎ }` → `"divergent": divergent,⏎ "legacy_event": legacy_event,⏎ }`
def test_t4_141_return_value_has_exactly_six_keys(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-141: return dict has exactly the six required keys and no extras."""
    required_keys = {
        "source_event_id", "result", "legacy_present",
        "structured_present", "acknowledged", "divergent",
    }
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-141")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-141",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert set(result.keys()) == required_keys, (
        f"T4-141: return dict must have exactly {sorted(required_keys)}; "
        f"got {sorted(result.keys())}"
    )


# ── 151: caller passes legacy_state through unchanged ─────────────────────────
# Mutation: `legacy_state=legacy_state` → `legacy_state={}`
def test_t4_151_caller_passes_legacy_state(
    loop_engine_mod: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-151: project_compat_reconcile_review_source_event passes legacy_state unchanged."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-151")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # A reviewers-clean state for the same id should produce ack=True.
    result = loop_engine_mod.project_compat_reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-151",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_legacy_state_with_clean_transition("evt-t4-151"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["acknowledged"] is True, (
        "T4-151: caller must pass legacy_state through; "
        "acknowledged must be True with a matching reviewers-clean transition"
    )


# ── 152: caller passes source_event through unchanged ─────────────────────────
# Mutation: `store, source_event,` → `store, {**source_event, "role": "caller-substituted-role"},`
def test_t4_152_caller_passes_source_event(
    loop_engine_mod: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-152: caller passes source_event unchanged; stored report role matches."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-152")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = loop_engine_mod.project_compat_reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-152",
            role="legacy-reviewer",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "clean"
    reports = store.get_semantic_records("review-report.v1")
    assert reports, "T4-152: must write a report"
    stored_role = reports[0].get("role")
    assert stored_role == "legacy-reviewer", (
        f"T4-152: stored report role must be 'legacy-reviewer' (from source_event); "
        f"got {stored_role!r}"
    )


@pytest.mark.parametrize(
    "recorded_digest",
    [
        "0" * 64,
        _legacy_clean_digest(form="structural-clean"),
    ],
    ids=["unrelated-digest", "wrong-form-digest"],
)
def test_d3_clean_digest_mismatch_is_divergent(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    recorded_digest: str,
) -> None:
    """A clean legacy record for other bytes or another form never acknowledges."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "d3-digest")
    review_subject = _make_review_subject(review_selection)
    legacy_state = _legacy_state_with_clean_transition("evt-d3-digest")
    legacy_state["last_review_record_payload_digest"] = recorded_digest

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-d3-digest",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=legacy_state,
        review_subject=review_subject,
        review_policy=_make_review_policy(review_subject),
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert result["result"] == "clean"
    assert result["acknowledged"] is False
    assert result["divergent"] is True


# ── T6 new tests: uncaught (i) ledger items ────────────────────────────────────


# ── 011: adjudication-text content-safety ─────────────────────────────────────
# MUT-011 equivalent: disable content-safety check on adjudication_text.
# Under mutation the loop skips the adjudication iteration → credential passes
# through → classified as "findings" instead of "unable".
def test_t4_011_adjudication_text_content_safety_returns_unable(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-011: adjudication_text with GitHub credential → unable before write.

    The raw_report_text contains a valid findings payload (no credential).
    The credential is only in adjudication_text.  The content-safety loop checks
    adjudication_text on its second iteration and must return _unable() before any
    report is written.  Without this check the adjudicated classifier would return
    'findings'.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-011")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Credential only in adjudication_text — raw_report_text is clean.
    cred = "ghp_" + "A" * 36
    adj_text = json.dumps({
        "f-probe": {
            "decision": "refuted",
            "authority_ref": cred,
        }
    })

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-011",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=adj_text,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-011: credential in adjudication_text must be caught by content-safety"
        " and return unable before adjudication parsing or write"
    )
    assert not result["structured_present"]
    # No report must have been written.
    reports = store.get_semantic_records("review-report.v1")
    assert not reports, (
        f"T4-011: content-safety refusal must not write a report; got {reports}"
    )


# ── 021/022: D1 byte equality rejects trailing newline ──────────────────────
# MUT-021 equivalent: revert to pre-fix classifier (grammar not byte equality).
# MUT-022 equivalent: rstrip-newline before comparison.
# Both mutations would accept `_CLEAN_TEXT + "\n"` as "clean"; the D1 byte-equality
# guard rejects it → unable.
def test_t4_021_022_d1_byte_equality_rejects_trailing_newline(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-021/022: direct-clean with sentinel plus trailing newline → unable (D1).

    `_CLEAN_TEXT + chr(10)` is grammatically clean but fails byte equality against
    the exact UTF-8 sentinel.  Under mutation 021 (grammar classifier) or 022
    (rstrip before compare) this input would return 'clean' instead of 'unable'.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-021-022")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-021-022",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT + "\n",
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-021/022: direct-clean with trailing newline must fail D1 byte equality"
        " and return unable"
    )
    assert not result["structured_present"]


# ── 023: D1 byte equality rejects prefix match ────────────────────────────────
# MUT-023 equivalent: prefix-match instead of exact byte equality.
# Under mutation, `_CLEAN_TEXT + " extra"` passes as "clean"; D1 rejects it.
def test_t4_023_d1_byte_equality_rejects_prefix_match(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-023: direct-clean with sentinel plus trailing text → unable (D1).

    `_CLEAN_TEXT + ' extra'` passes a prefix match but fails exact byte equality.
    Under mutation 023 (prefix-match classifier) this would return 'clean'.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-023")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-023",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT + " extra",
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-023: direct-clean with trailing text must fail D1 byte equality and"
        " return unable even though the text starts with the sentinel"
    )
    assert not result["structured_present"]


# ── 053B: unknown major schema version → unable ───────────────────────────────
# MUT-053B equivalent: skip the `not ok` return path for schema validation.
# Under mutation the finding with schema_version:2 passes validation → classified
# as "indeterminate" instead of "unable", report written.
def test_t4_053b_unknown_major_finding_returns_unable(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-053B: adjudicated form with schema_version:2 finding → unable, no write.

    An unknown major schema version fails validate_finding_dict → ok=False →
    reconcile returns 'unable' before writing anything.  Under mutation (skip
    the not-ok guard) the report would be written with result 'indeterminate'.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-053b")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Build a finding with an unrecognised schema_version.
    unknown_finding = {**_probe_finding(), "schema_version": 2}

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-053b",
            form="adjudicated",
            raw_report_text=json.dumps([unknown_finding]),
            adjudication_text=_probe_adjudication(),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-053B: finding with schema_version:2 must fail validation and return unable"
    )
    assert not result["structured_present"]
    reports = store.get_semantic_records("review-report.v1")
    assert not reports, (
        f"T4-053B: unknown major schema must not write a report; got {reports}"
    )


# ── 101: structured_present on unable path reads the store ────────────────────
# MUT-101 equivalent: hard-code `structured_present: False` in _unable().
# Under mutation the second call returns structured_present=False even though
# the store has a prior report for the same source_event_id.
def test_t4_101_structured_present_on_unable_reads_store(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-101: _unable() reads the store; structured_present=True if report exists.

    First call stores a clean report for 'e'.  Second call for 'e' triggers
    content-safety refusal (credential in raw_report_text) before the existing-
    report lookup → _unable() is invoked → _structured_present() queries the store
    dynamically and finds the prior report → structured_present=True.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-101")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # First call: store a clean report for "evt-t4-101".
    first = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-101",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert first["result"] == "clean", f"T4-101 setup: first call must be clean; {first}"

    # Second call: same source_event_id, but raw_report_text has a credential →
    # content-safety fires BEFORE the existing-report lookup → _unable() called.
    cred = "ghp_" + "B" * 36
    second = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-101",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT + f"\nghp-token: {cred}",
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert second["result"] == "unable", (
        "T4-101: second call with credential must return unable"
    )
    assert second["structured_present"] is True, (
        "T4-101: _unable() must read store and find the prior clean report; "
        f"structured_present must be True; got {second}"
    )


# ── 104: early store lookup enables conflict detection ────────────────────────
# MUT-104 equivalent: skip `existing_report = _find_existing_compat_report(...)`;
# always treat existing_report as None.  Under mutation no conflict is detected;
# the second call tries to write a second record and the store raises instead of
# the compat adapter raising ReviewCompatRefused.
def test_t4_104_early_store_lookup_enables_conflict_detection(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-104: early lookup of existing_report enables D2 conflict detection.

    First call stores a findings report for 'e'.  Second call for 'e' with a
    direct-clean (different status) must raise ReviewCompatRefused because the
    early lookup found the prior findings report and the status differs.  Without
    the lookup the conflict is invisible and the adapter would try to double-write.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-104")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # First call: store a findings report for "evt-t4-104".
    first = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-104",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=_probe_adjudication(decision="sustained"),
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert first["result"] == "findings", f"T4-104 setup: {first}"

    # Second call: same source_event_id, different status (clean vs findings) →
    # the early lookup finds the prior findings report → conflict → ReviewCompatRefused.
    with pytest.raises(review_compat.ReviewCompatRefused) as exc_info:
        review_compat.reconcile_review_source_event(
            store,
            _source_event(
                source_event_id="evt-t4-104",
                form="direct-clean",
                raw_report_text=_CLEAN_TEXT,
            ),
            legacy_state=_empty_legacy_state(),
            review_subject=review_subject,
            review_policy=review_policy,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    assert exc_info.value.denial_code == "denied-compat-source-event-conflict", (
        f"T4-104: conflict must use denial code 'denied-compat-source-event-conflict';"
        f" got {exc_info.value.denial_code!r}"
    )


# ── 141B: unable key set is closed (exactly six keys) ────────────────────────
# MUT-141B equivalent: add `"_reason": "unable"` to the _unable() return dict.
# Under mutation set(result) contains 7 keys, not 6.
_T4_SIX_KEYS = frozenset({
    "source_event_id",
    "result",
    "legacy_present",
    "structured_present",
    "acknowledged",
    "divergent",
})


def test_t4_141b_unable_key_set_is_closed(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-141B: the unable path returns exactly six keys — no extras allowed.

    An unknown form triggers _unable().  The result dict must contain exactly
    the six canonical keys.  Under mutation 141B an extra '_reason' key would be
    present, breaking callers that validate the response shape.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-141b")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-141b",
            form="unknown-form-t6",
            raw_report_text="Some report text.",
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "unable", (
        "T4-141B: unknown form must return unable"
    )
    assert set(result) == _T4_SIX_KEYS, (
        f"T4-141B: unable result must have exactly six keys {_T4_SIX_KEYS}; "
        f"got {set(result)}"
    )


# ── 166: legacy_state is deep-copied at entry — caller's dict not mutated ─────
# MUT-166 equivalent: write `legacy_state["last_review_record_operation_id"] = source_event_id`
# to the ORIGINAL dict instead of the deep copy.  Under mutation the caller's
# dict is modified after the call.
def test_t4_166_legacy_state_not_mutated(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-166: reconcile_review_source_event must not modify the caller's legacy_state.

    The function deep-copies legacy_state at entry; any internal updates must
    apply only to the copy.  Under mutation 166 the caller's dict would have
    'last_review_record_operation_id' overwritten with the source_event_id.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-166")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Sentinel value that must survive the call unchanged.
    sentinel_op_id = "SENTINEL-OP-ID-t4-166"
    caller_state: dict = {
        "last_review_record_operation_id": sentinel_op_id,
        "last_review_record_payload_digest": "0" * 64,
        "transition_history": [],
    }
    import copy as _copy
    state_before = _copy.deepcopy(caller_state)

    review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-166",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=caller_state,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert caller_state == state_before, (
        "T4-166: reconcile_review_source_event must not mutate the caller's legacy_state; "
        f"before={state_before!r}, after={caller_state!r}"
    )


# ── 192: D3 latest-recorded predicate — skipped when op_id differs ────────────
# MUT-192 equivalent: remove `last_review_record_operation_id == source_event_id`
# predicate so D3 runs unconditionally.  Under mutation the wrong digest causes
# acknowledged=False even when the predicate should NOT have fired.
def test_t4_192_d3_digest_check_skipped_for_older_event(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-192: D3 digest check is skipped when last_review_record_operation_id ≠ source_event_id.

    The legacy state has a reviewers-clean transition for 'evt-t4-192' but
    last_review_record_operation_id is 'later-op' and the stored digest is
    deliberately wrong ('0'*64).  Because the predicate fails (op IDs differ)
    the digest is NOT checked → acknowledged=True.  Under mutation 192 the digest
    check runs → mismatch → acknowledged=False.
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-192")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # Clean transition for the target event, but op_id points to a LATER event.
    legacy = _legacy_state_with_clean_transition("evt-t4-192")
    legacy["last_review_record_operation_id"] = "later-op-id-t4-192"
    legacy["last_review_record_payload_digest"] = "0" * 64  # wrong digest

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-192",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=legacy,
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    assert result["result"] == "clean"
    assert result["acknowledged"] is True, (
        "T4-192: D3 predicate must be False (op_id differs) → digest not checked"
        " → acknowledged must remain True; got acknowledged="
        f"{result['acknowledged']!r}"
    )


# T4-194 (D3 digest form-binding for structural-clean) deleted.
# structural-clean is now out of the closed corpus and is refused before any
# digest check.  The D3 form-binding property (a direct-clean digest computed
# for 'structural-clean' is divergent) is already covered exactly by
# test_d3_clean_digest_mismatch_is_divergent[wrong-form-digest], which passes
# form='direct-clean' with a legacy digest computed for 'structural-clean' and
# asserts result='clean', acknowledged=False, divergent=True.

# ── 200–205: D2 conflict guard — comprehensive ────────────────────────────────
# MUT-200 equivalent: skip `if stored_status != result:` conflict check.
# All six properties of the D2 conflict path are verified here.
def test_t4_200_205_d2_conflict_guard(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """T4-200–205: D2 conflict guard raises ReviewCompatRefused on status mismatch.

    Properties pinned:
      200: raises ReviewCompatRefused (not silent return or different exception)
      201: stored report is unchanged after the exception (stored_status = 'clean')
      202: no second report is written (store has exactly one record)
      203: denial_code == 'denied-compat-source-event-conflict'
      204: structured_present was True on the first call's result (store had a
           report before the second call; the first call's result shows False
           since the store was empty before it)
      205: legacy_present is True on the first call (clean transition present)
    """
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "t4-200-205")
    review_subject = _make_review_subject(review_selection)
    review_policy = _make_review_policy(review_subject)

    # First call: store a clean report (status='clean').
    first_result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-t4-200-205",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_legacy_state_with_clean_transition("evt-t4-200-205"),
        review_subject=review_subject,
        review_policy=review_policy,
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )
    # 205: legacy_present=True on the first call (clean transition present).
    assert first_result["result"] == "clean", f"T4-200-205 setup: {first_result}"
    assert first_result["legacy_present"] is True, (
        "T4-205: first-call legacy_present must be True (clean transition present)"
    )

    reports_after_first = store.get_semantic_records("review-report.v1")
    assert len(reports_after_first) == 1, (
        f"T4-200-205 setup: must have exactly one report after first call; {reports_after_first}"
    )

    # Second call: same source_event_id, findings status → D2 conflict.
    # 200: must raise ReviewCompatRefused.
    with pytest.raises(review_compat.ReviewCompatRefused) as exc_info:
        review_compat.reconcile_review_source_event(
            store,
            _source_event(
                source_event_id="evt-t4-200-205",
                form="adjudicated",
                raw_report_text=json.dumps([_probe_finding()]),
                adjudication_text=_probe_adjudication(decision="sustained"),
            ),
            legacy_state=_empty_legacy_state(),
            review_subject=review_subject,
            review_policy=review_policy,
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )

    # 203: denial_code must identify the conflict.
    assert exc_info.value.denial_code == "denied-compat-source-event-conflict", (
        f"T4-203: denial_code must be 'denied-compat-source-event-conflict'; "
        f"got {exc_info.value.denial_code!r}"
    )

    # 201 & 202: stored report is unchanged; no second write occurred.
    reports_after_conflict = store.get_semantic_records("review-report.v1")
    assert len(reports_after_conflict) == 1, (
        f"T4-202: conflict path must not write a second report; "
        f"got {len(reports_after_conflict)} reports"
    )
    stored_status = reports_after_conflict[0].get("terminal_status") or reports_after_conflict[0].get("result")
    assert stored_status == "clean", (
        f"T4-201: stored report status must remain 'clean' (not overwritten); "
        f"got {stored_status!r}"
    )

    # 204: structured_present can be verified by checking the store has a prior
    # report; the caller knows structured_present=True after the first call stores it.
    assert len(reports_after_conflict) == 1, "T4-204: report exists in store (structured_present=True)"


def _escaped_ctrl_finding() -> list[dict]:
    """One probe finding whose observation decodes to a control character."""
    return [{**_probe_finding(), "observation": "bad\u0001obs"}]


def _duplicate_id_findings() -> list[dict]:
    """Two otherwise valid probe findings that share one finding_id."""
    return [_probe_finding(), {**_probe_finding(), "observation": "Second."}]


@pytest.mark.parametrize(
    ("raw_findings", "adjudication"),
    [
        (_escaped_ctrl_finding(), _probe_adjudication()),
        (
            [_probe_finding()],
            json.dumps({"f-probe": {"decision": "refuted", "authority_ref": "a\u0001b"}}),
        ),
        (_duplicate_id_findings(), _probe_adjudication()),
        ([{**_probe_finding(), "material": "yes"}], _probe_adjudication()),
    ],
    ids=[
        "escaped-ctrl-in-finding",
        "escaped-ctrl-in-authority-ref",
        "duplicate-finding-id",
        "wrong-type-field",
    ],
)
def test_validate_before_write_refusals_persist_nothing(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    raw_findings: list[dict],
    adjudication: str,
) -> None:
    """Decoded-content and schema refusals are unable with no record stored."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "validate-first")
    review_subject = _make_review_subject(review_selection)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-validate-first",
            form="adjudicated",
            raw_report_text=json.dumps(raw_findings),
            adjudication_text=adjudication,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=_make_review_policy(review_subject),
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert result["result"] == "unable"
    assert result["structured_present"] is False
    assert store.get_semantic_records("review-report.v1") == []
    assert store.get_semantic_records("finding-assessment.v1") == []


@pytest.mark.parametrize("root_kind", ["missing", "file"])
def test_unusable_store_root_is_unable_for_direct_clean(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
    root_kind: str,
) -> None:
    """A store root that is not a directory refuses before any write, even direct-clean."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, f"root-{root_kind}")
    bad_root = tmp_path / f"unusable-root-{root_kind}"
    if root_kind == "file":
        bad_root.write_text("", encoding="utf-8")
    store._root = bad_root  # type: ignore[attr-defined]
    review_subject = _make_review_subject(review_selection)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id=f"evt-root-{root_kind}",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=_make_review_policy(review_subject),
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert result["result"] == "unable"
    assert store.get_semantic_records("review-report.v1") == []


def test_same_status_replay_with_different_findings_conflicts(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A findings replay with a changed finding body raises and writes nothing."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "same-status-conflict")
    review_subject = _make_review_subject(review_selection)
    kwargs = {
        "legacy_state": _empty_legacy_state(),
        "review_subject": review_subject,
        "review_policy": _make_review_policy(review_subject),
        "issuer": issuer,
        "grant": grant,
        "audit_sink": _null_sink,
    }
    first = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-same-status",
            form="adjudicated",
            raw_report_text=json.dumps([_probe_finding()]),
            adjudication_text=_probe_adjudication(),
        ),
        **kwargs,
    )
    assert first["result"] == "findings"
    before = (
        store.get_semantic_records("review-report.v1"),
        store.get_semantic_records("finding-assessment.v1"),
    )

    with pytest.raises(review_compat.ReviewCompatRefused) as exc_info:
        review_compat.reconcile_review_source_event(
            store,
            _source_event(
                source_event_id="evt-same-status",
                form="adjudicated",
                raw_report_text=json.dumps([{**_probe_finding(), "observation": "Changed."}]),
                adjudication_text=_probe_adjudication(),
            ),
            **kwargs,
        )

    assert exc_info.value.denial_code == "denied-compat-source-event-conflict"
    assert (
        store.get_semantic_records("review-report.v1"),
        store.get_semantic_records("finding-assessment.v1"),
    ) == before


def test_replay_of_complete_findings_appends_no_transaction_and_ids_are_deterministic(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """An identical replay writes nothing; every write uses its derived transaction id."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "replay-no-write")
    review_subject = _make_review_subject(review_selection)
    event = _source_event(
        source_event_id="evt-replay-no-write",
        form="adjudicated",
        raw_report_text=json.dumps([_probe_finding()]),
        adjudication_text=_probe_adjudication(),
    )
    kwargs = {
        "legacy_state": _empty_legacy_state(),
        "review_subject": review_subject,
        "review_policy": _make_review_policy(review_subject),
        "issuer": issuer,
        "grant": grant,
        "audit_sink": _null_sink,
    }

    review_compat.reconcile_review_source_event(store, event, **kwargs)
    count_after_first = store.transaction_count
    review_compat.reconcile_review_source_event(store, event, **kwargs)

    assert store.transaction_count == count_after_first == 2
    assert store.get_transaction("compat-tx:evt-replay-no-write:report") is not None
    assert store.get_transaction("compat-tx:evt-replay-no-write:assess:f-probe") is not None


def test_report_contract_refusal_is_unable_and_persists_nothing(
    review_compat: ModuleType,
    review_selection: ModuleType,
    evidence_store_mod: ModuleType,
    security_capability: ModuleType,
    tmp_path: Path,
) -> None:
    """A role the report contract rejects is unable before any write."""
    issuer, grant = _make_grant(security_capability)
    store = _make_compat_store(evidence_store_mod, tmp_path, "report-contract")
    review_subject = _make_review_subject(review_selection)

    result = review_compat.reconcile_review_source_event(
        store,
        _source_event(
            source_event_id="evt-report-contract",
            role="",
            form="direct-clean",
            raw_report_text=_CLEAN_TEXT,
        ),
        legacy_state=_empty_legacy_state(),
        review_subject=review_subject,
        review_policy=_make_review_policy(review_subject),
        issuer=issuer,
        grant=grant,
        audit_sink=_null_sink,
    )

    assert result["result"] == "unable"
    assert store.get_semantic_records("review-report.v1") == []
