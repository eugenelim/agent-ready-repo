"""_review_persistence — validated structured-review report persistence.

The module is the Slice 2 review-report store boundary. It composes the
EvidenceStore semantic transaction log and the review-contract validators; it
does not own reviewer invocation, finding assessment, disposition authority, or
the review-to-evidence bridge.
"""

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
    "REVIEW_REPORT_RECORD_TYPE",
    "ReviewPersistenceRefused",
    "append_current_review_report",
    "select_current_review_report",
]

REVIEW_REPORT_RECORD_TYPE: Final[str] = "review-report.v1"

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent
_review_contracts_module: ModuleType | None = None


class ReviewPersistenceRefused(Exception):
    """A review persistence prevalidation step was refused with a stable code."""

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code = denial_code


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


def _review_contracts() -> ModuleType:
    """Return the sibling review-contract validation module."""
    global _review_contracts_module
    if _review_contracts_module is None:
        _review_contracts_module = _load_sibling(
            "_review_persistence_contracts", "_review_contracts.py"
        )
    return _review_contracts_module


def _canonical_json(value: Any) -> str:
    """Return deterministic JSON for identity comparisons."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _refuse(denial_code: str, message: str) -> None:
    """Raise this port's prevalidation refusal."""
    raise ReviewPersistenceRefused(denial_code, message)


def append_current_review_report(
    store: object,
    report: dict[str, Any],
    *,
    transaction_id: str,
    expected_subject: dict[str, Any],
    issuer: object,
    grant: object,
    audit_sink: object,
) -> dict[str, Any]:
    """Validate and persist one current review-report transaction."""
    safe_report = copy.deepcopy(report)
    safe_subject = copy.deepcopy(expected_subject)
    ok, code = _review_contracts().validate_review_subject_dict(safe_subject)
    if not ok:
        _refuse(code, f"expected review subject is invalid: {code}")
    ok, code = _review_contracts().validate_review_report_dict(safe_report)
    if not ok:
        _refuse(code, f"review report is invalid: {code}")
    if _canonical_json(safe_report.get("subject")) != _canonical_json(safe_subject):
        _refuse(
            "denied-review-subject-mismatch",
            "review report subject does not match the expected subject",
        )
    lineage = safe_report["lineage"]
    if lineage["review_policy_fingerprint"] != safe_subject["review_policy_fingerprint"]:
        _refuse("denied-review-policy-mismatch", "report policy does not match subject policy")
    return store.append_semantic_records(
        [safe_report],
        transaction_id=transaction_id,
        acceptance_fingerprint=safe_subject["delivery_subject_ref"]["acceptance_fingerprint"],
        issuer=issuer,
        grant=grant,
        audit_sink=audit_sink,
        lifecycle={"kind": "review-report"},
    )


def select_current_review_report(
    store: object,
    *,
    role: str,
    expected_subject: dict[str, Any],
    review_policy_fingerprint: str,
) -> tuple[dict[str, Any] | None, str]:
    """Return the current report bound to the expected whole subject."""
    safe_subject = copy.deepcopy(expected_subject)
    ok, code = _review_contracts().validate_review_subject_dict(safe_subject)
    if not ok:
        return None, code
    records = store.get_semantic_records(REVIEW_REPORT_RECORD_TYPE)
    reports = [
        record for record in records
        if _canonical_json(record.get("subject")) == _canonical_json(safe_subject)
    ]
    report, code = _review_contracts().select_current_report(
        reports,
        role=role,
        review_subject_fingerprint=safe_subject["review_subject_fingerprint"],
        review_policy_fingerprint=review_policy_fingerprint,
    )
    return copy.deepcopy(report) if report is not None else None, code
