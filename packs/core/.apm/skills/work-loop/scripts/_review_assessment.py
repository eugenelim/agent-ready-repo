"""_review_assessment — actual-failure assessment for structured reviews."""

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
    "ReviewAssessmentRefused",
    "assess_finding_actual_failure",
]

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent
_review_contracts_module: ModuleType | None = None

_REQUIRED_EDGE_KEYS: Final[tuple[str, ...]] = (
    "rule-to-observation",
    "observation-to-reachable-path",
    "reachable-path-to-actual-failure",
)

_FACT_KEYS: Final[frozenset[str]] = frozenset({
    "falsifiable-delivery-failure",
    "all-cited-paths-blocked",
})


class ReviewAssessmentRefused(Exception):
    """An actual-failure assessment refused malformed boundary input."""

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
            "_review_assessment_contracts", "_review_contracts.py"
        )
    return _review_contracts_module


def _canonical_json(value: Any) -> str:
    """Return deterministic JSON for boundary identity comparisons."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _refuse(denial_code: str, message: str) -> None:
    """Raise this port's stable refusal."""
    raise ReviewAssessmentRefused(denial_code, message)


def _string_set(value: object, *, name: str, nonempty: bool = False) -> set[str]:
    """Return a validated string set."""
    if not isinstance(value, set) or not all(isinstance(item, str) and item for item in value):
        _refuse("denied-invalid-assessment-context", f"{name} must be a set of strings")
    if nonempty and not value:
        _refuse("denied-invalid-assessment-context", f"{name} must not be empty")
    return set(value)


def _controlled_facts(value: object) -> dict[str, bool]:
    """Return validated closed controlled facts."""
    if not isinstance(value, dict):
        _refuse("denied-invalid-controlled-facts", "controlled facts must be a dict")
    facts: dict[str, bool] = {}
    for key, fact in value.items():
        if key not in _FACT_KEYS:
            _refuse("denied-unknown-controlled-fact", f"unknown controlled fact: {key!r}")
        if not isinstance(fact, bool):
            _refuse("denied-invalid-controlled-fact", f"controlled fact must be bool: {key!r}")
        facts[key] = fact
    return facts


def _controlled_edges(
    value: object,
    current_evidence_refs: set[str],
) -> tuple[dict[str, list[str] | None], bool]:
    """Return validated edge evidence, allowing ``None`` only for undecidable edges."""
    if not isinstance(value, dict):
        _refuse("denied-invalid-controlled-edges", "controlled edges must be a dict")
    edges: dict[str, list[str] | None] = {}
    stale = False
    for key, refs in value.items():
        if key not in _REQUIRED_EDGE_KEYS:
            _refuse("denied-unknown-reachability-edge", f"unknown edge: {key!r}")
        if refs is None:
            edges[key] = None
            continue
        if (
            not isinstance(refs, list)
            or not refs
            or not all(isinstance(ref, str) and ref for ref in refs)
        ):
            _refuse("denied-invalid-reachability-edge", f"invalid edge evidence: {key!r}")
        missing = [ref for ref in refs if ref not in current_evidence_refs]
        if missing:
            stale = True
        edges[key] = list(refs)
    return edges, stale


def _requested_authority_judgment(
    authority: object,
    evidence_refs: list[str],
    current_evidence_refs: set[str],
) -> tuple[str, str] | None:
    """Return a current authority's requested judgment and identity."""
    if not isinstance(authority, dict):
        return None
    allowed = {
        "authority_ref",
        "requested_judgment",
        "edge_evidence_refs",
        "predicate_judgments",
        "rationale",
        "current",
    }
    if set(authority) - allowed:
        return None
    if not isinstance(authority.get("authority_ref"), str) or not authority["authority_ref"]:
        return None
    judgment = authority.get("requested_judgment")
    if judgment not in {
        "supported",
        "unsupported-opinion",
        "unsupported-duplicate",
        "unsupported-stale",
        "unsupported-controlled-elsewhere",
        "indeterminate",
    }:
        return None
    refs = authority.get("edge_evidence_refs")
    if not isinstance(refs, list) or not refs:
        return None
    if not all(isinstance(ref, str) and ref in current_evidence_refs for ref in refs):
        return None
    if not isinstance(authority.get("rationale"), str) or not authority["rationale"]:
        return None
    if authority.get("current") is not True:
        return None
    evidence_refs.extend(refs)
    return judgment, authority["authority_ref"]


def _authority_decides_falsifiability(authority: object) -> bool:
    """Return whether authority explicitly decides the falsifiability predicate."""
    if not isinstance(authority, dict):
        return False
    predicates = authority.get("predicate_judgments")
    return (
        isinstance(predicates, dict)
        and predicates.get("falsifiable-delivery-failure") is True
    )


def _all_paths_verified_current_controlled(
    path_facts: object,
    finding: dict[str, Any],
    current_evidence_refs: set[str],
) -> bool:
    """Return true when every cited path has a current verified blocking control."""
    if not isinstance(path_facts, list) or not path_facts:
        return False
    by_path: dict[str, dict[str, Any]] = {}
    for fact in path_facts:
        if not isinstance(fact, dict):
            return False
        if set(fact) != {"path_ref", "blocked", "current", "evidence_ref"}:
            return False
        path_ref = fact.get("path_ref")
        evidence_ref = fact.get("evidence_ref")
        if not isinstance(path_ref, str) or not path_ref:
            return False
        if not isinstance(evidence_ref, str) or evidence_ref not in current_evidence_refs:
            return False
        if fact.get("blocked") is not True or fact.get("current") is not True:
            return False
        by_path[path_ref] = fact
    return all(ref in by_path for ref in finding["evidence_refs"])


def _same_failure_duplicate(
    duplicate_finding: object,
    *,
    finding: dict[str, Any],
    report_id: str,
    current_subject: dict[str, Any],
) -> bool:
    """Return whether a current same-subject finding already represents the failure."""
    if not isinstance(duplicate_finding, dict):
        return False
    finding_id_val = duplicate_finding.get("finding_id")
    if not isinstance(finding_id_val, str) or not finding_id_val:
        return False
    if duplicate_finding.get("current") is not True:
        return False
    source_report = duplicate_finding.get("source_report")
    source_finding = duplicate_finding.get("source_finding")
    if not isinstance(source_report, dict) or not isinstance(source_finding, dict):
        return False
    ok, _code = _review_contracts().validate_review_report_dict(source_report)
    if not ok:
        return False
    ok, _code = _review_contracts().validate_finding_dict(source_finding)
    if not ok:
        return False
    if source_report.get("report_id") != duplicate_finding.get("report_id"):
        return False
    if not any(
        _canonical_json(candidate) == _canonical_json(source_finding)
        for candidate in source_report.get("findings", [])
    ):
        return False
    if duplicate_finding.get("review_subject_fingerprint") != current_subject.get(
        "review_subject_fingerprint"
    ):
        return False
    return (
        duplicate_finding.get("finding_id") != finding.get("finding_id")
        and duplicate_finding.get("actual_failure") == finding.get("actual_failure")
    )


def _assessment_record(
    *,
    assessment_id: str,
    finding: dict[str, Any],
    report_id: str,
    subject: dict[str, Any],
    assessment: str,
    evidence_refs: list[str],
    predicate_version: str,
    judgment_authority: str | None = None,
) -> dict[str, Any]:
    """Build and validate a finding-assessment.v1 record."""
    lineage = {"predicate_version": predicate_version}
    if judgment_authority is not None:
        lineage["judgment_authority"] = judgment_authority
    record = {
        "schema_version": 1,
        "assessment_id": assessment_id,
        "finding_id": finding["finding_id"],
        "report_id": report_id,
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "assessment": assessment,
        "evidence_refs": sorted(set(evidence_refs)),
        "lineage": lineage,
    }
    ok, code = _review_contracts().validate_finding_assessment_dict(record)
    if not ok:
        _refuse(code, f"generated finding assessment is invalid: {code}")
    return record


def assess_finding_actual_failure(
    report: dict[str, Any],
    finding: dict[str, Any],
    *,
    assessment_id: str,
    current_subject: dict[str, Any],
    current_report_id: str,
    current_rule_refs: set[str],
    current_evidence_refs: set[str],
    controlled_facts: dict[str, bool],
    controlled_edges: dict[str, list[str] | None],
    predicate_version: str,
    controlled_path_facts: list[dict[str, Any]] | None = None,
    current_duplicate_finding: dict[str, Any] | None = None,
    independent_authority: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assess whether a structured finding names a reachable actual failure."""
    safe_report = copy.deepcopy(report)
    safe_finding = copy.deepcopy(finding)
    safe_subject = copy.deepcopy(current_subject)
    if not isinstance(assessment_id, str) or not assessment_id:
        _refuse("denied-invalid-assessment-id", "assessment_id must be a non-empty string")
    if not isinstance(current_report_id, str) or not current_report_id:
        _refuse("denied-invalid-current-report", "current report id is required")
    if not isinstance(predicate_version, str) or not predicate_version:
        _refuse("denied-invalid-predicate-version", "predicate version is required")

    contracts = _review_contracts()
    for value, validator, label in (
        (safe_subject, contracts.validate_review_subject_dict, "subject"),
        (safe_report, contracts.validate_review_report_dict, "report"),
        (safe_finding, contracts.validate_finding_dict, "finding"),
    ):
        ok, code = validator(value)
        if not ok:
            _refuse(code, f"{label} is invalid: {code}")

    current_rules = _string_set(current_rule_refs, name="current_rule_refs")
    current_evidence = _string_set(current_evidence_refs, name="current_evidence_refs")
    facts = _controlled_facts(controlled_facts)
    edges, stale_edges = _controlled_edges(controlled_edges, current_evidence)
    evidence_refs = [ref for ref in safe_finding["evidence_refs"] if ref in current_evidence]
    report_subject = safe_report["subject"]

    stale = (
        safe_report.get("report_id") != current_report_id
        or _canonical_json(safe_report.get("subject")) != _canonical_json(safe_subject)
        or safe_finding.get("rule_ref") not in current_rules
        or any(ref not in current_evidence for ref in safe_finding["evidence_refs"])
        or stale_edges
    )
    if stale:
        return _assessment_record(
            assessment_id=assessment_id,
            finding=safe_finding,
            report_id=safe_report["report_id"],
            subject=report_subject,
            assessment="unsupported-stale",
            evidence_refs=evidence_refs,
            predicate_version=predicate_version,
        )

    embedded = [
        candidate for candidate in safe_report.get("findings", [])
        if _canonical_json(candidate) == _canonical_json(safe_finding)
    ]
    if len(embedded) != 1:
        _refuse(
            "denied-finding-not-in-current-report",
            "finding must be embedded in the current report",
        )

    if _same_failure_duplicate(
        current_duplicate_finding,
        finding=safe_finding,
        report_id=safe_report["report_id"],
        current_subject=safe_subject,
    ):
        return _assessment_record(
            assessment_id=assessment_id,
            finding=safe_finding,
            report_id=safe_report["report_id"],
            subject=safe_subject,
            assessment="unsupported-duplicate",
            evidence_refs=evidence_refs,
            predicate_version=predicate_version,
        )

    if facts.get("falsifiable-delivery-failure") is False:
        return _assessment_record(
            assessment_id=assessment_id,
            finding=safe_finding,
            report_id=safe_report["report_id"],
            subject=safe_subject,
            assessment="unsupported-opinion",
            evidence_refs=evidence_refs,
            predicate_version=predicate_version,
        )

    if (
        facts.get("all-cited-paths-blocked") is True
        and _all_paths_verified_current_controlled(
            controlled_path_facts, safe_finding, current_evidence
        )
    ):
        return _assessment_record(
            assessment_id=assessment_id,
            finding=safe_finding,
            report_id=safe_report["report_id"],
            subject=safe_subject,
            assessment="unsupported-controlled-elsewhere",
            evidence_refs=evidence_refs,
            predicate_version=predicate_version,
        )

    # A missing edge always appears in undecidable_edges (edges.get(key) is None for absent
    # keys), so checking undecidable_edges alone is sufficient; missing_edges is redundant.
    undecidable_edges = [edge for edge in _REQUIRED_EDGE_KEYS if edges.get(edge) is None]
    if undecidable_edges:
        authority_refs: list[str] = []
        authority_judgment = _requested_authority_judgment(
            independent_authority, authority_refs, current_evidence
        )
        can_use_authority = authority_judgment is not None and (
            facts.get("falsifiable-delivery-failure") is True
            or _authority_decides_falsifiability(independent_authority)
        )
        if can_use_authority and authority_judgment is not None:
            judgment, authority_ref = authority_judgment
            return _assessment_record(
                assessment_id=assessment_id,
                finding=safe_finding,
                report_id=safe_report["report_id"],
                subject=safe_subject,
                assessment=judgment,
                evidence_refs=evidence_refs + authority_refs,
                predicate_version=predicate_version,
                judgment_authority=authority_ref,
            )
        return _assessment_record(
            assessment_id=assessment_id,
            finding=safe_finding,
            report_id=safe_report["report_id"],
            subject=safe_subject,
            assessment="indeterminate",
            evidence_refs=evidence_refs,
            predicate_version=predicate_version,
        )

    if facts.get("falsifiable-delivery-failure") is not True:
        return _assessment_record(
            assessment_id=assessment_id,
            finding=safe_finding,
            report_id=safe_report["report_id"],
            subject=safe_subject,
            assessment="indeterminate",
            evidence_refs=evidence_refs,
            predicate_version=predicate_version,
        )

    edge_refs: list[str] = []
    for key in _REQUIRED_EDGE_KEYS:
        refs = edges[key]
        if refs is not None:
            edge_refs.extend(refs)
    return _assessment_record(
        assessment_id=assessment_id,
        finding=safe_finding,
        report_id=safe_report["report_id"],
        subject=safe_subject,
        assessment="supported",
        evidence_refs=edge_refs,
        predicate_version=predicate_version,
    )
