"""_review_contracts — structured review record validation helpers.

The module owns Slice 2 review-record validation and current report selection.
It is standard-library-only and does not load JSON Schema files at runtime;
canonical schemas under contracts/delivery are test-time contracts.
"""

from __future__ import annotations

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
    "SUPPORTED_REVIEW_SCHEMA_VERSION",
    "REVIEW_WRITER_BOUNDARIES",
    "SLICE_1_WRITER_BOUNDARIES",
    "validate_review_subject_dict",
    "validate_review_obligation_dict",
    "validate_finding_dict",
    "validate_review_report_dict",
    "validate_finding_assessment_dict",
    "validate_finding_disposition_dict",
    "validate_review_record_dict",
    "select_current_report",
]

SUPPORTED_REVIEW_SCHEMA_VERSION: Final[int] = 1
MAX_REPORT_BYTES: Final[int] = 1024 * 1024
MAX_FREE_TEXT_BYTES: Final[int] = 64 * 1024

REVIEW_WRITER_BOUNDARIES: Final[dict[str, str]] = {
    "review-subject.v1": "structured-control",
    "review-obligation.v1": "structured-control",
    "review-report.v1": "review-report",
    "finding.v1": "review-report",
    "finding-assessment.v1": "structured-control",
    "finding-disposition.v1": "structured-control",
}

_REVIEW_STATUS_VALUES: Final[frozenset[str]] = frozenset({
    "added",
    "modified",
    "deleted",
    "renamed",
    "unchanged",
})

_REPORT_STATUS_VALUES: Final[frozenset[str]] = frozenset({
    "clean",
    "findings",
    "unable",
    "indeterminate",
})

_OBLIGATION_KIND_VALUES: Final[frozenset[str]] = frozenset({
    "mandatory",
    "optional",
    "waived",
})

_ASSESSMENT_VALUES: Final[frozenset[str]] = frozenset({
    "supported",
    "unsupported-opinion",
    "unsupported-duplicate",
    "unsupported-stale",
    "unsupported-controlled-elsewhere",
    "indeterminate",
})

_DISPOSITION_VALUES: Final[frozenset[str]] = frozenset({
    "repair-request",
    "fixed-by",
    "accept-risk",
})

_content_safety_module: ModuleType | None = None


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling script by literal filename."""
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
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previous


def _content_safety() -> ModuleType:
    """Return the Slice 1 content-safety sibling module."""
    global _content_safety_module
    if _content_safety_module is None:
        _content_safety_module = _load_sibling(
            "_review_contracts_content_safety", "_content_safety.py"
        )
    return _content_safety_module


SLICE_1_WRITER_BOUNDARIES: Final[dict[str, str]] = dict(
    _content_safety().SLICE_1_WRITER_BOUNDARIES
)


def _is_exact_schema_version(value: object) -> bool:
    """Return true only for integer 1, excluding bool."""
    return type(value) is int and value == SUPPORTED_REVIEW_SCHEMA_VERSION


def _nonempty_string(value: object) -> bool:
    """Return true when value is a non-empty string."""
    if not isinstance(value, str) or value == "":
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return True


def _enum_value(value: object, allowed: frozenset[str]) -> bool:
    """Return true when value is a string in the closed enum set."""
    return isinstance(value, str) and value in allowed


def _positive_int(value: object) -> bool:
    """Return true for positive integers, excluding bool."""
    return type(value) is int and value > 0


def _string_list(value: object, *, nonempty: bool = False) -> bool:
    """Return true when value is a list of non-empty strings."""
    if not isinstance(value, list):
        return False
    if nonempty and not value:
        return False
    return all(_nonempty_string(item) for item in value)


def _sorted_unique_string_list(value: object) -> bool:
    """Return true for sorted unique non-empty string lists."""
    if not isinstance(value, list):
        return False
    if not _string_list(value):
        return False
    strings = list(value)
    return strings == sorted(set(strings))


def _unknown_fields(record: dict[str, Any], allowed: set[str]) -> bool:
    """Return true when record carries fields outside allowed."""
    return bool(set(record) - allowed)


def _canonical_bytes(record: dict[str, Any]) -> bytes:
    """Return deterministic JSON bytes for content-safety scanning."""
    text = json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return text.encode("utf-8")


def _iter_strings(value: object) -> list[str]:
    """Collect string fields from a nested record for per-field bounds."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            found.extend(_iter_strings(item))
        return found
    if isinstance(value, dict):
        found = []
        for item in value.values():
            found.extend(_iter_strings(item))
        return found
    return []


def _check_report_content_safety(report: dict[str, Any]) -> tuple[bool, str]:
    """Validate whole-report and per-field review-report content bounds."""
    for text in _iter_strings(report):
        try:
            payload = text.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            return False, "denied-content-safety-rejected-encoding"
        if len(payload) > MAX_FREE_TEXT_BYTES:
            return False, "denied-free-text-field-too-large"
        decision = _content_safety().check_content_safety(
            "review-report",
            payload,
            source_record_id=str(report.get("report_id", "review-report")),
            classification="repository-internal",
        )
        if not decision.accepted:
            suffix = decision.decision_code.removeprefix("rejected-")
            return False, f"denied-content-safety-rejected-{suffix}"
    payload = _canonical_bytes(report)
    if len(payload) > MAX_REPORT_BYTES:
        return False, "denied-content-safety-rejected-size"
    profile = REVIEW_WRITER_BOUNDARIES["review-report.v1"]
    decision = _content_safety().check_content_safety(
        profile,
        payload,
        source_record_id=str(report.get("report_id", "review-report")),
        classification="repository-internal",
    )
    if not decision.accepted:
        suffix = decision.decision_code.removeprefix("rejected-")
        return False, f"denied-content-safety-rejected-{suffix}"
    return True, "ok"


def _check_structured_record_content_safety(
    record_type: str, record: dict[str, Any]
) -> tuple[bool, str]:
    """Validate a structured review record through its registered profile."""
    profile = REVIEW_WRITER_BOUNDARIES[record_type]
    for text in _iter_strings(record):
        try:
            payload = text.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            return False, "denied-content-safety-rejected-encoding"
        decision = _content_safety().check_content_safety(
            profile,
            payload,
            source_record_id=str(record.get("record_id", record_type)),
            classification="repository-internal",
        )
        if not decision.accepted:
            suffix = decision.decision_code.removeprefix("rejected-")
            return False, f"denied-content-safety-rejected-{suffix}"
    payload = _canonical_bytes(record)
    decision = _content_safety().check_content_safety(
        profile,
        payload,
        source_record_id=str(record.get("record_id", record_type)),
        classification="repository-internal",
    )
    if not decision.accepted:
        suffix = decision.decision_code.removeprefix("rejected-")
        return False, f"denied-content-safety-rejected-{suffix}"
    return True, "ok"


def _validate_review_subject_shape(record: object) -> tuple[bool, str]:
    """Validate review-subject.v1 owned fields."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    allowed = {
        "schema_version",
        "review_subject_id",
        "review_subject_fingerprint",
        "delivery_subject_ref",
        "review_policy_fingerprint",
        "normalized_paths",
        "normalized_statuses",
        "lineage",
    }
    required = allowed
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-unknown-schema-version"
    for field in required:
        if field not in record:
            return False, "denied-missing-required-field"
    if _unknown_fields(record, allowed):
        return False, "denied-unknown-authority-field"
    for field in (
        "review_subject_id",
        "review_subject_fingerprint",
        "review_policy_fingerprint",
    ):
        if not _nonempty_string(record.get(field)):
            return False, "denied-invalid-field"
    delivery_ref = record.get("delivery_subject_ref")
    if not isinstance(delivery_ref, dict):
        return False, "denied-invalid-field"
    if set(delivery_ref) != {"subject_id", "acceptance_fingerprint"}:
        return False, "denied-invalid-field"
    if not _nonempty_string(delivery_ref.get("subject_id")):
        return False, "denied-invalid-field"
    if not _nonempty_string(delivery_ref.get("acceptance_fingerprint")):
        return False, "denied-invalid-field"
    paths = record.get("normalized_paths")
    statuses = record.get("normalized_statuses")
    if not _sorted_unique_string_list(paths):
        return False, "denied-invalid-field"
    if not isinstance(statuses, list) or any(
        not _enum_value(status, _REVIEW_STATUS_VALUES) for status in statuses
    ):
        return False, "denied-invalid-field"
    if len(paths) != len(statuses):
        return False, "denied-invalid-field"
    lineage = record.get("lineage")
    if not isinstance(lineage, dict):
        return False, "denied-invalid-field"
    if set(lineage) != {"provider", "projection_version"}:
        return False, "denied-invalid-field"
    if not _nonempty_string(lineage.get("provider")):
        return False, "denied-invalid-field"
    if not _nonempty_string(lineage.get("projection_version")):
        return False, "denied-invalid-field"
    return _check_structured_record_content_safety("review-subject.v1", record)


def validate_review_subject_dict(record: object) -> tuple[bool, str]:
    """Validate a review-subject.v1 dictionary."""
    return _validate_review_subject_shape(record)


def validate_review_obligation_dict(record: object) -> tuple[bool, str]:
    """Validate a review-obligation.v1 dictionary."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    allowed = {
        "schema_version",
        "obligation_id",
        "role",
        "review_subject_fingerprint",
        "review_policy_fingerprint",
        "kind",
        "lineage",
    }
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-unknown-schema-version"
    for field in allowed:
        if field not in record:
            return False, "denied-missing-required-field"
    if _unknown_fields(record, allowed):
        return False, "denied-unknown-authority-field"
    for field in (
        "obligation_id",
        "role",
        "review_subject_fingerprint",
        "review_policy_fingerprint",
    ):
        if not _nonempty_string(record.get(field)):
            return False, "denied-invalid-field"
    if not _enum_value(record.get("kind"), _OBLIGATION_KIND_VALUES):
        return False, "denied-invalid-enum"
    lineage = record.get("lineage")
    if not isinstance(lineage, dict):
        return False, "denied-invalid-field"
    allowed_lineage = {"selector", "policy_version", "waiver_ref"}
    if {"selector", "policy_version"} - set(lineage):
        return False, "denied-missing-required-field"
    if _unknown_fields(lineage, allowed_lineage):
        return False, "denied-unknown-authority-field"
    if not _nonempty_string(lineage.get("selector")):
        return False, "denied-invalid-field"
    if not _nonempty_string(lineage.get("policy_version")):
        return False, "denied-invalid-field"
    if "waiver_ref" in lineage and not _nonempty_string(lineage.get("waiver_ref")):
        return False, "denied-invalid-field"
    return _check_structured_record_content_safety("review-obligation.v1", record)


def validate_finding_dict(record: object) -> tuple[bool, str]:
    """Validate a finding.v1 dictionary."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    allowed = {
        "schema_version",
        "finding_id",
        "rule_ref",
        "observation",
        "reachable_path",
        "actual_failure",
        "affected_acceptance_criteria",
        "evidence_refs",
        "material",
    }
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-unknown-schema-version"
    for field in allowed:
        if field not in record:
            return False, "denied-missing-required-field"
    if _unknown_fields(record, allowed):
        return False, "denied-unknown-authority-field"
    for field in ("finding_id", "rule_ref", "observation", "reachable_path", "actual_failure"):
        if not _nonempty_string(record.get(field)):
            return False, "denied-invalid-field"
    if not _string_list(record.get("affected_acceptance_criteria"), nonempty=True):
        return False, "denied-invalid-field"
    if not _string_list(record.get("evidence_refs")):
        return False, "denied-invalid-field"
    if not isinstance(record.get("material"), bool):
        return False, "denied-invalid-field"
    return _check_structured_record_content_safety("finding.v1", record)


def validate_review_report_dict(record: object) -> tuple[bool, str]:
    """Validate a review-report.v1 dictionary and its content-safety boundary."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    allowed = {
        "schema_version",
        "report_id",
        "role",
        "subject",
        "terminal_status",
        "lineage",
        "findings",
    }
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-unknown-schema-version"
    for field in allowed:
        if field not in record:
            return False, "denied-missing-required-field"
    if _unknown_fields(record, allowed):
        return False, "denied-unknown-authority-field"
    if not _nonempty_string(record.get("report_id")):
        return False, "denied-invalid-field"
    if not _nonempty_string(record.get("role")):
        return False, "denied-invalid-field"
    ok, code = validate_review_subject_dict(record.get("subject"))
    if not ok:
        return False, code
    if not _enum_value(record.get("terminal_status"), _REPORT_STATUS_VALUES):
        return False, "denied-invalid-enum"
    lineage = record.get("lineage")
    if not isinstance(lineage, dict):
        return False, "denied-invalid-field"
    lineage_allowed = {
        "sequence",
        "review_policy_fingerprint",
        "source_event_id",
        "producer",
        "previous_report_id",
    }
    if {"sequence", "review_policy_fingerprint", "source_event_id", "producer"} - set(lineage):
        return False, "denied-missing-required-field"
    if _unknown_fields(lineage, lineage_allowed):
        return False, "denied-unknown-authority-field"
    if not _positive_int(lineage.get("sequence")):
        return False, "denied-invalid-field"
    for field in ("review_policy_fingerprint", "source_event_id", "producer"):
        if not _nonempty_string(lineage.get(field)):
            return False, "denied-invalid-field"
    if "previous_report_id" in lineage and not _nonempty_string(
        lineage.get("previous_report_id")
    ):
        return False, "denied-invalid-field"
    findings = record.get("findings")
    if not isinstance(findings, list):
        return False, "denied-invalid-field"
    if record.get("terminal_status") == "findings" and not findings:
        return False, "denied-missing-required-field"
    if record.get("terminal_status") != "findings" and findings:
        return False, "denied-invalid-field"
    for finding in findings:
        ok, code = validate_finding_dict(finding)
        if not ok:
            return False, code
    return _check_report_content_safety(record)


def validate_finding_assessment_dict(record: object) -> tuple[bool, str]:
    """Validate a finding-assessment.v1 dictionary."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    allowed = {
        "schema_version",
        "assessment_id",
        "finding_id",
        "report_id",
        "review_subject_fingerprint",
        "assessment",
        "evidence_refs",
        "lineage",
    }
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-unknown-schema-version"
    for field in allowed:
        if field not in record:
            return False, "denied-missing-required-field"
    if _unknown_fields(record, allowed):
        return False, "denied-unknown-authority-field"
    for field in (
        "assessment_id",
        "finding_id",
        "report_id",
        "review_subject_fingerprint",
    ):
        if not _nonempty_string(record.get(field)):
            return False, "denied-invalid-field"
    if not _enum_value(record.get("assessment"), _ASSESSMENT_VALUES):
        return False, "denied-invalid-enum"
    if not _string_list(record.get("evidence_refs")):
        return False, "denied-invalid-field"
    lineage = record.get("lineage")
    if not isinstance(lineage, dict):
        return False, "denied-invalid-field"
    allowed_lineage = {"predicate_version", "judgment_authority"}
    if "predicate_version" not in lineage:
        return False, "denied-missing-required-field"
    if _unknown_fields(lineage, allowed_lineage):
        return False, "denied-unknown-authority-field"
    if not _nonempty_string(lineage.get("predicate_version")):
        return False, "denied-invalid-field"
    if "judgment_authority" in lineage and not _nonempty_string(
        lineage.get("judgment_authority")
    ):
        return False, "denied-invalid-field"
    return _check_structured_record_content_safety(
        "finding-assessment.v1", record
    )


def validate_finding_disposition_dict(record: object) -> tuple[bool, str]:
    """Validate a finding-disposition.v1 dictionary."""
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    allowed = {
        "schema_version",
        "disposition_id",
        "finding_id",
        "assessment_id",
        "review_subject_fingerprint",
        "disposition",
        "replacement_report_id",
        "decision_maker",
        "lineage",
    }
    required = allowed - {"replacement_report_id"}
    if not _is_exact_schema_version(record.get("schema_version")):
        return False, "denied-unknown-schema-version"
    for field in required:
        if field not in record:
            return False, "denied-missing-required-field"
    if _unknown_fields(record, allowed):
        return False, "denied-unknown-authority-field"
    for field in (
        "disposition_id",
        "finding_id",
        "assessment_id",
        "review_subject_fingerprint",
    ):
        if not _nonempty_string(record.get(field)):
            return False, "denied-invalid-field"
    if not _enum_value(record.get("disposition"), _DISPOSITION_VALUES):
        return False, "denied-invalid-enum"
    if "replacement_report_id" in record and not _nonempty_string(
        record.get("replacement_report_id")
    ):
        return False, "denied-invalid-field"
    decision_maker = record.get("decision_maker")
    if not isinstance(decision_maker, dict):
        return False, "denied-invalid-field"
    if set(decision_maker) != {"identity", "role"}:
        return False, "denied-invalid-field"
    if not _nonempty_string(decision_maker.get("identity")):
        return False, "denied-invalid-field"
    if not _nonempty_string(decision_maker.get("role")):
        return False, "denied-invalid-field"
    lineage = record.get("lineage")
    if not isinstance(lineage, dict):
        return False, "denied-invalid-field"
    if set(lineage) != {"authority_ref", "source_event_id"}:
        return False, "denied-invalid-field"
    if not _nonempty_string(lineage.get("authority_ref")):
        return False, "denied-invalid-field"
    if not _nonempty_string(lineage.get("source_event_id")):
        return False, "denied-invalid-field"
    return _check_structured_record_content_safety(
        "finding-disposition.v1", record
    )


_REVIEW_RECORD_VALIDATORS: Final[dict[str, Any]] = {
    "review-subject.v1": validate_review_subject_dict,
    "review-obligation.v1": validate_review_obligation_dict,
    "review-report.v1": validate_review_report_dict,
    "finding.v1": validate_finding_dict,
    "finding-assessment.v1": validate_finding_assessment_dict,
    "finding-disposition.v1": validate_finding_disposition_dict,
}


def validate_review_record_dict(record_type: object, record: object) -> tuple[bool, str]:
    """Validate a registered review-owned record type."""
    if not isinstance(record_type, str):
        return False, "denied-unknown-review-record-type"
    validator = _REVIEW_RECORD_VALIDATORS.get(record_type)
    if validator is None:
        return False, "denied-unknown-review-record-type"
    if record_type not in REVIEW_WRITER_BOUNDARIES:
        return False, "denied-unregistered-review-boundary"
    return validator(record)


def select_current_report(
    reports: list[dict[str, Any]],
    *,
    role: str,
    review_subject_fingerprint: str,
    review_policy_fingerprint: str,
) -> tuple[dict[str, Any] | None, str]:
    """Return the unique safe lineage tip for role, subject, and policy."""
    current: list[dict[str, Any]] = []
    for report in reports:
        ok, code = validate_review_report_dict(report)
        if not ok:
            return None, code
        subject = report["subject"]
        lineage = report["lineage"]
        if report["role"] != role:
            continue
        if subject["review_subject_fingerprint"] != review_subject_fingerprint:
            continue
        if subject["review_policy_fingerprint"] != review_policy_fingerprint:
            continue
        if lineage["review_policy_fingerprint"] != review_policy_fingerprint:
            continue
        current.append(report)
    if not current:
        return None, "denied-no-current-report"
    sequences: dict[int, str] = {}
    for report in current:
        sequence = report["lineage"]["sequence"]
        if sequence in sequences:
            return None, "denied-duplicate-report-sequence"
        sequences[sequence] = report["report_id"]
    ordered = sorted(current, key=lambda item: item["lineage"]["sequence"])
    seen: set[str] = set()
    previous_id: str | None = None
    for index, report in enumerate(ordered):
        lineage = report["lineage"]
        if index == 0:
            if lineage["sequence"] != 1:
                return None, "denied-forked-report-lineage"
            if "previous_report_id" in lineage:
                return None, "denied-forked-report-lineage"
        else:
            if lineage.get("previous_report_id") != previous_id:
                return None, "denied-forked-report-lineage"
        if report["report_id"] in seen:
            return None, "denied-duplicate-report-id"
        seen.add(report["report_id"])
        previous_id = report["report_id"]
    return ordered[-1], "ok"
