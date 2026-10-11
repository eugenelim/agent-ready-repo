"""_review_selection — review subject projection and obligation decisions.

Pure Slice 2 review-policy service. It composes the T1 review contracts and the
Slice 1 delivery-subject shape without loading delivery schemas at runtime.
Plan digests, task-projection revisions, adapter event IDs, and reviewer
workflow state are provenance only and never enter review identity.
"""

from __future__ import annotations

import hashlib
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
    "SUPPORTED_REVIEW_SELECTION_VERSION",
    "ReviewSelectionRefused",
    "project_review_subject",
    "select_review_obligations",
    "decide_review_obligation",
    "current_engine_review_obligations",
    "synthetic_review_obligations",
]

SUPPORTED_REVIEW_SELECTION_VERSION: Final[int] = 1
SUBJECT_PROVIDER: Final[str] = "core-review-subject-projector"
SUBJECT_PROJECTION_VERSION: Final[str] = "1.0"
_REVIEW_STATUSES: Final[frozenset[str]] = frozenset({
    "added",
    "modified",
    "deleted",
    "renamed",
    "unchanged",
})
_ROLE_KINDS: Final[frozenset[str]] = frozenset({"mandatory", "optional"})
_review_contracts_module: ModuleType | None = None
_subject_projection_module: ModuleType | None = None


class ReviewSelectionRefused(Exception):
    """Review subject projection or obligation selection refused with a code."""

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code = denial_code


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling work-loop script by regular file path."""
    path = Path(__file__).with_name(filename)
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
    """Return the T1 review-contract sibling module."""
    global _review_contracts_module
    if _review_contracts_module is None:
        _review_contracts_module = _load_sibling(
            "_review_selection_contracts", "_review_contracts.py"
        )
    return _review_contracts_module


def _subject_projection() -> ModuleType:
    """Return the Slice 1 delivery-subject validator sibling module."""
    global _subject_projection_module
    if _subject_projection_module is None:
        _subject_projection_module = _load_sibling(
            "_review_selection_subject_projection", "_subject_projection.py"
        )
    return _subject_projection_module


def _is_exact_schema_version(value: object) -> bool:
    """Return true only for integer 1, excluding bool."""
    return type(value) is int and value == SUPPORTED_REVIEW_SELECTION_VERSION


def _nonempty_string(value: object) -> bool:
    """Return true for strict non-empty UTF-8 strings."""
    if not isinstance(value, str) or value == "":
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return True


def _canonical_digest(data: dict[str, Any]) -> str:
    """Return the stable SHA-256 digest for canonical JSON data."""
    text = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def _validate_delivery_subject(record: object) -> tuple[bool, str]:
    """Validate the delivery-subject identity T2 consumes."""
    ok, code = _subject_projection().validate_subject_dict(record)
    if not ok:
        return False, code
    if not isinstance(record, dict):
        return False, "denied-delivery-subject-not-a-dict"
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-delivery-subject-schema-version"
    for field in ("subject_id", "acceptance_fingerprint"):
        if not _nonempty_string(record.get(field)):
            return False, "denied-delivery-subject-invalid-field"
    return True, "ok"


def _normalize_changed_paths(changed_paths: object) -> tuple[list[str], list[str]]:
    """Return sorted path/status pairs or refuse ambiguous path input."""
    if not isinstance(changed_paths, list):
        raise ReviewSelectionRefused("denied-review-subject-invalid-changes")
    by_path: dict[str, str] = {}
    for item in changed_paths:
        if not isinstance(item, dict) or set(item) != {"path", "status"}:
            raise ReviewSelectionRefused("denied-review-subject-invalid-changes")
        path = item.get("path")
        status = item.get("status")
        if not _canonical_relative_path(path):
            raise ReviewSelectionRefused("denied-review-subject-invalid-changes")
        if not isinstance(status, str) or status not in _REVIEW_STATUSES:
            raise ReviewSelectionRefused("denied-review-subject-invalid-changes")
        previous = by_path.setdefault(path, status)
        if previous != status:
            raise ReviewSelectionRefused("denied-review-subject-ambiguous-path")
    ordered = sorted(by_path)
    return ordered, [by_path[path] for path in ordered]


def _canonical_relative_path(path: object) -> bool:
    """Return true for lexical relative canonical paths only."""
    if not _nonempty_string(path):
        return False
    if ":" in path:
        return False
    if "\\" in path:
        return False
    parts = path.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def project_review_subject(
    delivery_subject: dict[str, Any],
    *,
    changed_paths: list[dict[str, str]],
    review_policy_fingerprint: str,
    plan_digest: str | None = None,
    task_projection_revision: str | None = None,
    adapter_event_id: str | None = None,
) -> dict[str, Any]:
    """Project a current review-subject.v1 record from delivery and policy facts."""
    del plan_digest, task_projection_revision, adapter_event_id
    ok, code = _validate_delivery_subject(delivery_subject)
    if not ok:
        raise ReviewSelectionRefused(code)
    if not _nonempty_string(review_policy_fingerprint):
        raise ReviewSelectionRefused("denied-review-policy-invalid-fingerprint")
    normalized_paths, normalized_statuses = _normalize_changed_paths(changed_paths)
    identity = {
        "delivery_subject_ref": {
            "subject_id": delivery_subject["subject_id"],
            "acceptance_fingerprint": delivery_subject["acceptance_fingerprint"],
        },
        "lineage": {
            "provider": SUBJECT_PROVIDER,
            "projection_version": SUBJECT_PROJECTION_VERSION,
        },
        "normalized_paths": normalized_paths,
        "normalized_statuses": normalized_statuses,
        "review_policy_fingerprint": review_policy_fingerprint,
    }
    fingerprint = "review-subject-sha256:" + _canonical_digest(identity)
    record = {
        "schema_version": SUPPORTED_REVIEW_SELECTION_VERSION,
        "review_subject_id": fingerprint,
        "review_subject_fingerprint": fingerprint,
        **identity,
    }
    ok, code = _review_contracts().validate_review_subject_dict(record)
    if not ok:
        raise ReviewSelectionRefused(code)
    return record


def _validate_policy(policy: object) -> tuple[bool, str]:
    """Validate the closed policy shape consumed by the selector."""
    if not isinstance(policy, dict):
        return False, "denied-review-policy-not-a-dict"
    allowed = {
        "policy_id",
        "review_policy_fingerprint",
        "policy_version",
        "selector",
        "roles",
        "waivers",
    }
    if allowed - set(policy):
        return False, "denied-review-policy-missing-field"
    if set(policy) - allowed:
        return False, "denied-review-policy-unknown-field"
    for field in ("policy_id", "review_policy_fingerprint", "policy_version", "selector"):
        if not _nonempty_string(policy.get(field)):
            return False, "denied-review-policy-invalid-field"
    roles = policy.get("roles")
    if not isinstance(roles, list) or not roles:
        return False, "denied-review-policy-invalid-role"
    seen: set[str] = set()
    for role in roles:
        if not isinstance(role, dict) or set(role) != {"role", "kind"}:
            return False, "denied-review-policy-invalid-role"
        if not _nonempty_string(role.get("role")):
            return False, "denied-review-policy-invalid-role"
        if not isinstance(role.get("kind"), str) or role.get("kind") not in _ROLE_KINDS:
            return False, "denied-review-policy-invalid-role"
        if role["role"] in seen:
            return False, "denied-review-policy-duplicate-role"
        seen.add(role["role"])
    if not isinstance(policy.get("waivers"), list):
        return False, "denied-review-policy-invalid-waiver"
    return True, "ok"


def _current_authorized_waiver(
    *,
    role: str,
    subject: dict[str, Any],
    policy: dict[str, Any],
) -> str | None:
    """Return a current authorized waiver reference for role, if one exists."""
    for waiver in policy.get("waivers", []):
        if not isinstance(waiver, dict):
            continue
        if set(waiver) != {
            "waiver_ref",
            "role",
            "review_subject_fingerprint",
            "review_policy_fingerprint",
            "authorized",
            "current",
        }:
            continue
        if not _nonempty_string(waiver.get("waiver_ref")):
            continue
        if waiver.get("role") != role:
            continue
        if waiver.get("review_subject_fingerprint") != subject["review_subject_fingerprint"]:
            continue
        if waiver.get("review_policy_fingerprint") != policy["review_policy_fingerprint"]:
            continue
        if waiver.get("authorized") is True and waiver.get("current") is True:
            return waiver["waiver_ref"]
    return None


def select_review_obligations(
    review_subject: dict[str, Any],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Select ordered review-obligation.v1 records from subject and policy."""
    ok, code = _review_contracts().validate_review_subject_dict(review_subject)
    if not ok:
        raise ReviewSelectionRefused(code)
    ok, code = _validate_policy(policy)
    if not ok:
        raise ReviewSelectionRefused(code)
    if policy["review_policy_fingerprint"] != review_subject["review_policy_fingerprint"]:
        raise ReviewSelectionRefused("denied-review-policy-subject-mismatch")
    obligations: list[dict[str, Any]] = []
    for role_policy in policy["roles"]:
        role = role_policy["role"]
        kind = role_policy["kind"]
        lineage = {
            "selector": policy["selector"],
            "policy_version": policy["policy_version"],
        }
        waiver_ref = _current_authorized_waiver(
            role=role, subject=review_subject, policy=policy
        )
        if waiver_ref is not None:
            kind = "waived"
            lineage["waiver_ref"] = waiver_ref
        obligation = {
            "schema_version": SUPPORTED_REVIEW_SELECTION_VERSION,
            "obligation_id": "review-obligation-sha256:"
            + _canonical_digest(
                {
                    "role": role,
                    "review_subject_fingerprint": review_subject[
                        "review_subject_fingerprint"
                    ],
                    "review_policy_fingerprint": policy["review_policy_fingerprint"],
                }
            ),
            "role": role,
            "review_subject_fingerprint": review_subject["review_subject_fingerprint"],
            "review_policy_fingerprint": policy["review_policy_fingerprint"],
            "kind": kind,
            "lineage": lineage,
        }
        ok, code = _review_contracts().validate_review_obligation_dict(obligation)
        if not ok:
            raise ReviewSelectionRefused(code)
        obligations.append(obligation)
    return obligations


def _policy_fingerprint(policy: object) -> str:
    """Return the review policy fingerprint after typed policy validation."""
    ok, code = _validate_policy(policy)
    if not ok:
        raise ReviewSelectionRefused(code)
    assert isinstance(policy, dict)
    return policy["review_policy_fingerprint"]


def _current_assessment(
    assessments: list[dict[str, Any]], finding: dict[str, Any], report: dict[str, Any]
) -> dict[str, Any] | None:
    """Return the current assessment for a finding on the report tip."""
    matches = []
    for assessment in assessments:
        ok, _code = _review_contracts().validate_finding_assessment_dict(assessment)
        if not ok:
            continue
        if assessment["finding_id"] != finding["finding_id"]:
            continue
        if assessment["report_id"] != report["report_id"]:
            continue
        if (
            assessment["review_subject_fingerprint"]
            != report["subject"]["review_subject_fingerprint"]
        ):
            continue
        matches.append(assessment)
    if len(matches) != 1:
        return None
    return matches[0]


def _has_closing_disposition(
    dispositions: list[dict[str, Any]],
    finding: dict[str, Any],
    assessment: dict[str, Any],
    *,
    review_subject: dict[str, Any],
) -> bool:
    """Return true when accept-risk closes the current supported finding."""
    for disposition in dispositions:
        ok, _code = _review_contracts().validate_finding_disposition_dict(disposition)
        if not ok:
            continue
        if disposition["review_subject_fingerprint"] != review_subject[
            "review_subject_fingerprint"
        ]:
            continue
        if disposition["finding_id"] != finding["finding_id"]:
            continue
        if disposition["assessment_id"] != assessment["assessment_id"]:
            continue
        if disposition["disposition"] == "accept-risk":
            return True
    return False


def decide_review_obligation(
    obligation: dict[str, Any],
    *,
    review_subject: dict[str, Any],
    policy: dict[str, Any],
    reports: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    dispositions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return the review decision for one selected obligation."""
    ok, code = _review_contracts().validate_review_obligation_dict(obligation)
    if not ok:
        raise ReviewSelectionRefused(code)
    ok, code = _review_contracts().validate_review_subject_dict(review_subject)
    if not ok:
        raise ReviewSelectionRefused(code)
    ok, code = _validate_policy(policy)
    if not ok:
        raise ReviewSelectionRefused(code)
    expected = select_review_obligations(review_subject, policy)
    expected_by_role = {item["role"]: item for item in expected}
    selected = expected_by_role.get(obligation["role"])
    if selected is None:
        raise ReviewSelectionRefused("denied-obligation-not-selected")
    identity_fields = (
        "obligation_id",
        "review_subject_fingerprint",
        "review_policy_fingerprint",
    )
    if any(obligation[field] != selected[field] for field in identity_fields):
        raise ReviewSelectionRefused("denied-obligation-not-current")
    if selected["kind"] != obligation["kind"]:
        obligation = selected
    if obligation["kind"] == "waived":
        return {
            "obligation_satisfied": True,
            "review_block": False,
            "acceptance_block": False,
            "decision": "waived",
            "reason": "current-authorized-waiver",
        }
    report, report_code = _review_contracts().select_current_report(
        reports,
        role=obligation["role"],
        review_subject_fingerprint=review_subject["review_subject_fingerprint"],
        review_policy_fingerprint=policy["review_policy_fingerprint"],
    )
    if report is None or report.get("terminal_status") in {"unable", "indeterminate"}:
        return {
            "obligation_satisfied": False,
            "review_block": obligation["kind"] == "mandatory",
            "acceptance_block": obligation["kind"] == "mandatory",
            "decision": "optional-unsatisfied"
            if obligation["kind"] == "optional"
            else "mandatory-report-unsatisfied",
            "reason": report_code if report is None else "report-unable",
        }
    if obligation["kind"] == "optional":
        return {
            "obligation_satisfied": True,
            "review_block": False,
            "acceptance_block": False,
            "decision": "optional-current-report",
            "reason": "optional-current-report",
        }
    if report["terminal_status"] == "clean":
        return {
            "obligation_satisfied": True,
            "review_block": False,
            "acceptance_block": False,
            "decision": "satisfied-clean",
            "reason": "terminal-clean",
        }
    unsupported_or_closed = True
    for finding in report["findings"]:
        assessment = _current_assessment(assessments, finding, report)
        if assessment is None or assessment["assessment"] == "indeterminate":
            return {
                "obligation_satisfied": False,
                "review_block": True,
                "acceptance_block": True,
                "decision": "finding-assessment-required",
                "reason": "missing-or-indeterminate-assessment",
            }
        if assessment["assessment"] != "supported":
            continue
        if finding["material"] and not _has_closing_disposition(
            dispositions,
            finding,
            assessment,
            review_subject=review_subject,
        ):
            unsupported_or_closed = False
    if not unsupported_or_closed:
        return {
            "obligation_satisfied": True,
            "review_block": False,
            "acceptance_block": True,
            "decision": "open-supported-material-finding",
            "reason": "supported-material-finding-open",
        }
    return {
        "obligation_satisfied": True,
        "review_block": False,
        "acceptance_block": False,
        "decision": "satisfied-findings",
        "reason": "findings-assessed-and-closed",
    }


def current_engine_review_obligations(
    delivery_subject: dict[str, Any],
    *,
    changed_paths: list[dict[str, str]],
    review_policy: dict[str, Any],
    plan_digest: str | None = None,
    task_projection_revision: str | None = None,
    adapter_event_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Project and select obligations for the current engine compatibility path."""
    subject = project_review_subject(
        delivery_subject,
        changed_paths=changed_paths,
        review_policy_fingerprint=_policy_fingerprint(review_policy),
        plan_digest=plan_digest,
        task_projection_revision=task_projection_revision,
        adapter_event_id=adapter_event_id,
    )
    return subject, select_review_obligations(subject, review_policy)


def synthetic_review_obligations(
    delivery_subject: dict[str, Any],
    *,
    changed_paths: list[dict[str, str]],
    review_policy: dict[str, Any],
    plan_digest: str | None = None,
    task_projection_revision: str | None = None,
    adapter_event_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Project and select obligations for the runtime-neutral synthetic adapter."""
    subject = project_review_subject(
        delivery_subject,
        changed_paths=changed_paths,
        review_policy_fingerprint=_policy_fingerprint(review_policy),
        plan_digest=plan_digest,
        task_projection_revision=task_projection_revision,
        adapter_event_id=adapter_event_id,
    )
    return subject, select_review_obligations(subject, review_policy)
