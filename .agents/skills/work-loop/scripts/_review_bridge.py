"""_review_bridge — bridge supported findings to Slice 1 evidence receipts."""

from __future__ import annotations

import copy
import importlib.util
import json
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
    "ReviewBridgeRefused",
    "append_finding_assessment_bridge",
    "append_finding_assessment_replacement",
    "derive_review_failure_receipt_id",
    "select_current_finding_assessments",
]

_BRIDGE_PRODUCER: Final[dict[str, str]] = {
    "class": "review-bridge",
    "identity": "structured-review-boundary",
}
_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent
_evidence_store_module: ModuleType | None = None
_review_contracts_module: ModuleType | None = None


class ReviewBridgeRefused(Exception):
    """The review-to-evidence bridge refused a malformed transition."""

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code = denial_code


def _canonical_json(value: Any) -> str:
    """Return deterministic JSON for bridge identities."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _refuse(denial_code: str, message: str) -> None:
    """Raise this port's stable refusal."""
    raise ReviewBridgeRefused(denial_code, message)


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling work-loop module without registering it globally."""
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
        _evidence_store_module = _load_sibling(
            "_review_bridge_evidence_store", "_evidence_store.py"
        )
    return _evidence_store_module


def _review_contracts() -> ModuleType:
    """Return the sibling review-contract validator module."""
    global _review_contracts_module
    if _review_contracts_module is None:
        _review_contracts_module = _load_sibling(
            "_review_bridge_contracts", "_review_contracts.py"
        )
    return _review_contracts_module


def derive_review_failure_receipt_id(
    *,
    report_id: str,
    finding_id: str,
    assessment_id: str,
    criterion_ref: str,
    acceptance_fingerprint: str,
) -> str:
    """Return the stable bridge-owned receipt identity for one criterion."""
    return _evidence_store().derive_review_failure_receipt_id(
        report_id=report_id,
        finding_id=finding_id,
        assessment_id=assessment_id,
        criterion_ref=criterion_ref,
        acceptance_fingerprint=acceptance_fingerprint,
    )


def append_finding_assessment_bridge(
    store: object,
    assessment: dict[str, Any],
    *,
    report_id: str,
    finding: dict[str, Any],
    affected_criteria: list[str],
    transaction_id: str,
    acceptance_fingerprint: str,
    issuer: object,
    grant: object,
    audit_sink: object,
) -> dict[str, Any]:
    """Validate an assessment and delegate frame composition to the store.

    The store composes receipts and supersessions inside the advisory lock,
    so the delta is always consistent with the committed state regardless of
    which in-memory view the caller holds.
    """
    safe_assessment = copy.deepcopy(assessment)
    ok, code = _review_contracts().validate_finding_assessment_dict(safe_assessment)
    if not ok:
        _refuse("denied-invalid-finding-assessment", f"assessment is invalid: {code}")

    # Verify the durable finding matches what the caller declared (when present).
    # Also refuse a stale (non-current-tip) source report early so the caller sees
    # a bridge denial code rather than a store denial code.
    reports = store.get_semantic_records("review-report.v1")  # type: ignore[union-attr]
    source_report = next(
        (r for r in reports if r.get("report_id") == report_id), None
    )
    if source_report is not None:
        subject = source_report.get("subject", {})
        policy_fp = source_report.get("lineage", {}).get("review_policy_fingerprint")
        sequence = source_report.get("lineage", {}).get("sequence", 0)
        if any(
            candidate.get("role") == source_report.get("role")
            and _canonical_json(candidate.get("subject")) == _canonical_json(subject)
            and candidate.get("lineage", {}).get("review_policy_fingerprint") == policy_fp
            and candidate.get("lineage", {}).get("sequence", 0) > sequence
            for candidate in reports
        ):
            _refuse("denied-stale-source-report", "source report is not current")
        source_finding = next(
            (
                f for f in source_report.get("findings", [])
                if isinstance(f, dict) and f.get("finding_id") == safe_assessment["finding_id"]
            ),
            None,
        )
        if source_finding is None or _canonical_json(source_finding) != _canonical_json(finding):
            _refuse("denied-source-finding-mismatch", "finding must match durable report")

    return store.append_semantic_records(  # type: ignore[union-attr]
        [safe_assessment],
        transaction_id=transaction_id,
        acceptance_fingerprint=acceptance_fingerprint,
        issuer=issuer,
        grant=grant,
        audit_sink=audit_sink,
        lifecycle={
            "kind": "finding-assessment",
            "report_id": report_id,
            "finding_id": safe_assessment["finding_id"],
            "affected_criteria": affected_criteria,
        },
    )


def append_finding_assessment_replacement(
    store: object,
    *,
    old_report_id: str,
    old_finding_id: str,
    new_assessment: dict[str, Any] | None,
    transaction_id: str,
    acceptance_fingerprint: str,
    issuer: object,
    grant: object,
    audit_sink: object,
    current_subject: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append an explicit source-invalidation or replacement receipt delta.

    When ``new_assessment`` is given the call delegates to the finding-assessment
    lifecycle port.  When ``new_assessment`` is ``None`` a ``current_subject``
    (a schema-valid review-subject.v1) is required; the store composes the
    supersession under lock using the source-invalidation lifecycle.
    """
    if new_assessment is not None:
        safe_assessment = copy.deepcopy(new_assessment)
        ok, code = _review_contracts().validate_finding_assessment_dict(safe_assessment)
        if not ok:
            _refuse("denied-invalid-finding-assessment", f"assessment is invalid: {code}")
        reports = store.get_semantic_records("review-report.v1")  # type: ignore[union-attr]
        source_report = next(
            (r for r in reports if r.get("report_id") == old_report_id), None
        )
        if source_report is not None:
            source_finding = next(
                (
                    f for f in source_report.get("findings", [])
                    if isinstance(f, dict) and f.get("finding_id") == old_finding_id
                ),
                None,
            )
            affected = []
            if source_finding is not None:
                affected = source_finding.get("affected_acceptance_criteria", [])
        else:
            affected = []
        return store.append_semantic_records(  # type: ignore[union-attr]
            [safe_assessment],
            transaction_id=transaction_id,
            acceptance_fingerprint=acceptance_fingerprint,
            issuer=issuer,
            grant=grant,
            audit_sink=audit_sink,
            lifecycle={
                "kind": "finding-assessment",
                "report_id": old_report_id,
                "finding_id": old_finding_id,
                "affected_criteria": affected,
            },
        )

    # Source-invalidation path: current_subject required.
    if current_subject is None:
        _refuse(
            "denied-missing-current-subject",
            "source invalidation requires current_subject",
        )
    safe_subject = copy.deepcopy(current_subject)
    ok, code = _review_contracts().validate_review_subject_dict(safe_subject)
    if not ok:
        _refuse("denied-invalid-current-subject", f"current_subject is invalid: {code}")
    return store.append_semantic_records(  # type: ignore[union-attr]
        [safe_subject],
        transaction_id=transaction_id,
        acceptance_fingerprint=acceptance_fingerprint,
        issuer=issuer,
        grant=grant,
        audit_sink=audit_sink,
        lifecycle={
            "kind": "source-invalidation",
            "report_id": old_report_id,
            "finding_id": old_finding_id,
        },
    )


def select_current_finding_assessments(
    store: object,
    *,
    review_subject_fingerprint: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Return the current finding assessment view from the store's projection."""
    return store.current_finding_assessments(review_subject_fingerprint)  # type: ignore[union-attr]
