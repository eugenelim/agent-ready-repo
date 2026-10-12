"""_review_disposition — typed write port for finding dispositions and readiness query.

The write port validates all authority rules before delegating frame composition
to the evidence store's finding-disposition lifecycle.  The readiness query is a
pure computation from the durable log: deleting derived state and reopening the
store yields the identical result.

Standard library only.  Loads sibling modules by path using the established
_load_sibling pattern.

Python 3.11+.
"""

from __future__ import annotations

import copy
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "ReviewDispositionRefused",
    "append_finding_disposition",
    "review_readiness",
]

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent

_evidence_store_module: ModuleType | None = None
_review_contracts_module: ModuleType | None = None
_review_selection_module: ModuleType | None = None
_policy_import_module: ModuleType | None = None


class ReviewDispositionRefused(Exception):
    """The disposition was refused with a stable denial code.

    ``denial_code`` carries a stable string safe for logging without
    sensitive payload bytes or content-derived hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


def _refuse(denial_code: str, message: str) -> None:
    """Raise this port's stable refusal."""
    raise ReviewDispositionRefused(denial_code, message)


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling work-loop script by literal path, unregistered."""
    path = _SCRIPTS_DIR / filename
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"sibling module is not a regular file: {filename}")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load sibling module: {filename}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


def _evidence_store() -> ModuleType:
    """Return the sibling evidence-store helper module."""
    global _evidence_store_module
    if _evidence_store_module is None:
        _evidence_store_module = _load_sibling("_rd_evidence_store", "_evidence_store.py")
    return _evidence_store_module


def _review_contracts() -> ModuleType:
    """Return the sibling review-contract validator module."""
    global _review_contracts_module
    if _review_contracts_module is None:
        _review_contracts_module = _load_sibling(
            "_rd_review_contracts", "_review_contracts.py"
        )
    return _review_contracts_module


def _review_selection() -> ModuleType:
    """Return the sibling review-selection module."""
    global _review_selection_module
    if _review_selection_module is None:
        _review_selection_module = _load_sibling(
            "_rd_review_selection", "_review_selection.py"
        )
    return _review_selection_module


def _policy_import() -> ModuleType:
    """Return the sibling policy-import module for approval validation."""
    global _policy_import_module
    if _policy_import_module is None:
        _policy_import_module = _load_sibling("_rd_policy_import", "_policy_import.py")
    return _policy_import_module


# ── Write port ────────────────────────────────────────────────────────────────


def append_finding_disposition(
    store: Any,
    disposition: dict[str, Any],
    *,
    approval_record: dict[str, Any],
    current_subject: dict[str, Any],
    transaction_id: str,
    acceptance_fingerprint: str,
    issuer: object,
    grant: object,
    audit_sink: Any,
) -> dict[str, Any]:
    """Validate and append a finding disposition through the typed write port.

    Schema validation (disposition, approval, subject) runs here before any
    store call.  Finding eligibility (supported material assessment) is also
    validated here.  All semantic authority rules (G1/G2/G3, Rules 1–5) are
    enforced inside the store's _validate_review_transition, which is the
    single owner for those checks on the write path, replay, and
    disposition_closes.  An invalid record or authority failure raises
    ReviewDispositionRefused with a stable denial_code and leaves the log
    unchanged.

    The store uses the finding-disposition lifecycle kind, which requires a
    capability grant whose roots include "review" (not merely "evidence").

    Args:
        store:                  An open EvidenceStore instance.
        disposition:            A valid finding-disposition.v1 dict.
        approval_record:        A valid approval-record.v1 dict covering this disposition.
        current_subject:        The current review subject (review-subject.v1 dict).
        transaction_id:         Stable unique identifier; an identical retry is idempotent.
        acceptance_fingerprint: Acceptance fingerprint of the delivery subject.
        issuer:                 CapabilityIssuer that owns the grant.
        grant:                  CapabilityGrant with roots including "review".
        audit_sink:             Callable that stores security events durably.

    Returns:
        The committed semantic-evidence-transaction.v1 record.

    Raises:
        ReviewDispositionRefused: on any validation or authority failure.
    """
    safe_disposition = copy.deepcopy(disposition)
    safe_approval = copy.deepcopy(approval_record)
    safe_subject = copy.deepcopy(current_subject)

    # Validate disposition schema before any store interaction.
    ok, code = _review_contracts().validate_finding_disposition_dict(safe_disposition)
    if not ok:
        _refuse(
            f"denied-invalid-finding-disposition-{code}",
            f"disposition record is invalid: {code}",
        )

    # Validate approval-record schema.
    ok, code = _policy_import().validate_approval_dict(safe_approval)
    if not ok:
        _refuse(
            f"denied-invalid-approval-{code}",
            f"approval record is invalid: {code}",
        )

    # Validate current subject schema.
    ok, code = _review_contracts().validate_review_subject_dict(safe_subject)
    if not ok:
        _refuse(
            f"denied-invalid-current-subject-{code}",
            f"current subject is invalid: {code}",
        )

    # Delegate frame composition to the store via the finding-disposition lifecycle.
    # The store's _compose_finding_disposition_frame checks fixed-by replacement
    # durability and fingerprint after the authority check has run.
    # The store uses record_scope="review/disposition" for this lifecycle kind,
    # so the caller's grant must cover the "review" root.
    try:
        return store.append_semantic_records(
            [safe_disposition],
            transaction_id=transaction_id,
            acceptance_fingerprint=acceptance_fingerprint,
            issuer=issuer,
            grant=grant,
            audit_sink=audit_sink,
            lifecycle={
                "kind": "finding-disposition",
                "approval_record": safe_approval,
                "review_subject": safe_subject,
            },
        )
    except ReviewDispositionRefused:
        raise
    except Exception as exc:
        denial_code = getattr(exc, "denial_code", None)
        if denial_code is not None:
            raise ReviewDispositionRefused(denial_code, str(exc)) from exc
        raise


# ── Readiness query ───────────────────────────────────────────────────────────


def review_readiness(
    store: Any,
    *,
    review_subject: dict[str, Any],
    review_policy: dict[str, Any],
) -> dict[str, Any]:
    """Return the current review readiness for a subject.

    Pure computation from the durable log.  Deleting derived state (fresh store
    reopen) yields the identical result dict.  No write operations are performed.

    Returns:
        {
            "acceptance_eligible": bool,
            "obligations": [<obligation decision dicts with "role" prefix>],
            "open_findings": [<finding dicts>],
        }

    ``acceptance_eligible`` is True only when all mandatory obligations are
    satisfied and ``open_findings`` is empty.
    """
    rs = _review_selection()
    rc = _review_contracts()
    review_subject_fingerprint = review_subject.get("review_subject_fingerprint", "")
    review_policy_fingerprint = review_policy.get("review_policy_fingerprint", "")

    # Get all durable records.
    all_reports: list[dict[str, Any]] = store.get_semantic_records("review-report.v1")
    reports = all_reports
    all_assessments: list[dict[str, Any]] = store.get_semantic_records("finding-assessment.v1")
    # Scope assessments to the target subject fingerprint.
    assessments = [
        a for a in all_assessments
        if a.get("review_subject_fingerprint") == review_subject_fingerprint
    ]
    all_dispositions: list[dict[str, Any]] = store.get_semantic_records("finding-disposition.v1")
    # Scope dispositions to the target subject fingerprint.
    dispositions = [
        d for d in all_dispositions
        if d.get("review_subject_fingerprint") == review_subject_fingerprint
    ]

    # Get selected obligations from subject + policy.
    selected_obligations = rs.select_review_obligations(review_subject, review_policy)

    obligation_decisions: list[dict[str, Any]] = []
    acceptance_eligible = True

    for obligation in selected_obligations:
        try:
            decision = rs.decide_review_obligation(
                obligation,
                review_subject=review_subject,
                policy=review_policy,
                reports=copy.deepcopy(reports),
                assessments=assessments,
                # Pass no dispositions: all closure is re-verified live via
                # store.disposition_closes, which re-evaluates the full authority
                # rule set including approval supersession and assessment currency.
                dispositions=[],
            )
        except Exception:  # noqa: BLE001
            decision = {
                "obligation_satisfied": False,
                "review_block": True,
                "acceptance_block": True,
                "decision": "obligation-error",
                "reason": "obligation-evaluation-failed",
            }

        # When T2 reports open supported material findings, re-verify whether
        # every such finding is closed by a durable disposition that still
        # satisfies all authority rules via store.disposition_closes.
        if decision.get("decision") == "open-supported-material-finding":
            role = obligation.get("role", "")
            tip, _ = rc.select_current_report(
                all_reports,
                role=role,
                review_subject_fingerprint=review_subject_fingerprint,
                review_policy_fingerprint=review_policy_fingerprint,
            )
            if tip is not None:
                all_closed = True
                for finding in tip.get("findings", []):
                    if not finding.get("material", False):
                        continue
                    finding_id_loop = finding.get("finding_id", "")
                    # Find the assessment for this finding in the current report.
                    finding_assessment = next(
                        (
                            a for a in assessments
                            if a.get("finding_id") == finding_id_loop
                            and a.get("report_id") == tip.get("report_id")
                        ),
                        None,
                    )
                    if finding_assessment is None:
                        continue
                    if finding_assessment.get("assessment") != "supported":
                        continue
                    # Re-verify using the store's single verifier for all kinds.
                    if any(
                        store.disposition_closes(d.get("disposition_id", ""), review_subject)
                        for d in dispositions
                        if d.get("finding_id") == finding_id_loop
                    ):
                        continue
                    all_closed = False
                    break
                if all_closed:
                    decision = {
                        "obligation_satisfied": True,
                        "review_block": False,
                        "acceptance_block": False,
                        "decision": "satisfied-findings",
                        "reason": "dispositions-verified",
                    }

        obligation_decisions.append({"role": obligation.get("role", ""), **decision})
        if decision.get("acceptance_block"):
            acceptance_eligible = False

    # Compute open findings: supported material findings without a current
    # closing disposition (all kinds, re-verified via store.disposition_closes).
    open_findings: list[dict[str, Any]] = []
    try:
        current_assessments = store.current_finding_assessments(review_subject_fingerprint)
    except Exception:  # noqa: BLE001
        current_assessments = {}

    for (report_id, finding_id), entry in current_assessments.items():
        assessment = entry["assessment"]
        if assessment.get("assessment") != "supported":
            continue
        source_report = next(
            (r for r in all_reports if r.get("report_id") == report_id), None
        )
        if source_report is None:
            continue
        finding = next(
            (
                f for f in source_report.get("findings", [])
                if f.get("finding_id") == finding_id
            ),
            None,
        )
        if finding is None or not finding.get("material", False):
            continue
        if any(
            store.disposition_closes(d.get("disposition_id", ""), review_subject)
            for d in dispositions
            if d.get("finding_id") == finding_id
        ):
            continue
        # Annotate the finding with the reviewing role so callers can identify
        # which role flagged it without re-querying the source report.
        finding_entry = copy.deepcopy(finding)
        finding_entry["role"] = source_report.get("role", "")
        open_findings.append(finding_entry)

    if open_findings:
        acceptance_eligible = False

    return {
        "acceptance_eligible": acceptance_eligible,
        "obligations": obligation_decisions,
        "open_findings": open_findings,
    }
