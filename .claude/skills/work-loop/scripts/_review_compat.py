"""T6 compatibility adapter: reconcile legacy review events with the structured boundary.

Translates legacy review-record events (direct-clean, findings, adjudicated)
into structured review-report.v1 records held in the EvidenceStore.  The
adapter is read-only with respect to legacy state: it never calls any
loop-cohort mutator and never writes to state.json.

Legacy structural-clean records are outside the closed Slice 2 compatibility
corpus and are not reconciled.  A source event with form 'structural-clean' is
refused by the closed-form gate: result is 'unable', nothing is persisted, and
the event is never acknowledged.

Acknowledgement and divergence rules
-------------------------------------
``acknowledged`` is True only when:
  - legacy_present is True
  - the legacy event agrees with the structured result:
    ``reviewers-clean`` ↔ ``clean``, ``findings-remain`` ↔ ``findings``
  - the ``last_review_record_payload_digest`` in legacy_state equals the digest
    the legacy recorder would have computed for this source event (D3).

``divergent`` is True when legacy_present is True and the legacy event (clean or
findings) disagrees with the structured result.  An unknown event (operation_id
recorded but no history entry with the event) is not acknowledged and not divergent
unless the recorded payload digest mismatches (D3).

Shadow output is never acknowledgement.

Replay identity (D2)
--------------------
If structured facts already exist for ``source_event_id`` and differ in any
way from what this request would produce (report body or any assessment), the
adapter raises ``ReviewCompatRefused("denied-compat-source-event-conflict")``
and writes nothing.  ``structured_present`` is always read from the store.

Public API
----------
reconcile_review_source_event(store, source_event, *, legacy_state,
                               review_subject, review_policy,
                               issuer, grant, audit_sink) -> dict
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

# _SCRIPTS_DIR must be declared exactly this way so the sibling-module AST scan
# in test_loop_engine.py recognises the pattern and does not flag the module.
_SCRIPTS_DIR = Path(__file__).resolve().parent

# ── Closed corpus ─────────────────────────────────────────────────────────────

_CLOSED_FORMS: frozenset[str] = frozenset(
    {"direct-clean", "findings", "adjudicated"}
)

_CLOSED_AUDIT_DECISIONS: frozenset[str] = frozenset({"sustained", "refuted"})

# Legacy event names that carry an outcome we can verify.
_LEGACY_CLEAN_EVENT: str = "reviewers-clean"
_LEGACY_FINDINGS_EVENT: str = "findings-remain"

# Content-safety classification for legacy review text.
_REPORT_CLASSIFICATION: str = "repository-internal"

# Predicate version stamped on every assessment produced by this adapter.
_COMPAT_PREDICATE_VERSION: str = "compat-adapter-v1"


# ── Sibling module loaders ────────────────────────────────────────────────────


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling work-loop script by literal path, no global registration."""
    path = _SCRIPTS_DIR / filename
    if not path.exists():
        raise ImportError(f"sibling module not found: {path}")
    info = os.lstat(str(path))
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"not a regular file: {path}")
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot build spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = prev


_content_safety_module: ModuleType | None = None
_cohort_module: ModuleType | None = None
_review_persistence_module: ModuleType | None = None
_review_assessment_module: ModuleType | None = None
_review_bridge_module: ModuleType | None = None
_review_contracts_module: ModuleType | None = None


def _content_safety() -> ModuleType:
    global _content_safety_module
    if _content_safety_module is None:
        _content_safety_module = _load_sibling(
            "_work_loop_content_safety_compat", "_content_safety.py"
        )
    return _content_safety_module


def _cohort() -> ModuleType:
    global _cohort_module
    if _cohort_module is None:
        _cohort_module = _load_sibling("_work_loop_cohort_compat", "loop-cohort.py")
    return _cohort_module


def _review_persistence() -> ModuleType:
    global _review_persistence_module
    if _review_persistence_module is None:
        _review_persistence_module = _load_sibling(
            "_work_loop_review_persistence_compat", "_review_persistence.py"
        )
    return _review_persistence_module


def _review_assessment() -> ModuleType:
    global _review_assessment_module
    if _review_assessment_module is None:
        _review_assessment_module = _load_sibling(
            "_work_loop_review_assessment_compat", "_review_assessment.py"
        )
    return _review_assessment_module


def _review_bridge() -> ModuleType:
    global _review_bridge_module
    if _review_bridge_module is None:
        _review_bridge_module = _load_sibling(
            "_work_loop_review_bridge_compat", "_review_bridge.py"
        )
    return _review_bridge_module


def _review_contracts() -> ModuleType:
    global _review_contracts_module
    if _review_contracts_module is None:
        _review_contracts_module = _load_sibling(
            "_work_loop_review_contracts_compat", "_review_contracts.py"
        )
    return _review_contracts_module


# ── Legacy presence and outcome ───────────────────────────────────────────────


def _determine_legacy_outcome(
    legacy_state: dict[str, Any],
    source_event_id: str,
) -> tuple[bool, str | None]:
    """Return (legacy_present, legacy_event) for a source_event_id.

    legacy_event is one of "clean", "findings", or None (present but unknown).

    Checks:
    1. ``transition_history`` entries with shape ``{transition_id, event, ...}``.
       A matching ``transition_id`` with event ``reviewers-clean`` or
       ``findings-remain`` is the authoritative source of truth.
    2. ``last_review_record_operation_id``: the review was recorded but the
       transition event has not yet fired (or is not in history).  Legacy is
       present but the outcome is unknown.
    """
    for entry in legacy_state.get("transition_history", []):
        if isinstance(entry, dict) and entry.get("transition_id") == source_event_id:
            event = entry.get("event", "")
            if event == _LEGACY_CLEAN_EVENT:
                return True, "clean"
            if event == _LEGACY_FINDINGS_EVENT:
                return True, "findings"
    if legacy_state.get("last_review_record_operation_id") == source_event_id:
        return True, None
    return False, None


def _compute_acknowledged_divergent(
    legacy_present: bool,
    legacy_event: str | None,
    result: str,
    *,
    legacy_state: dict[str, Any],
    form: str,
    raw_report_text: str,
    source_event_id: str,
) -> tuple[bool, bool]:
    """Return (acknowledged, divergent) based on legacy/structured agreement.

    The legacy event must agree with the structured result.  When this source
    is the most recently recorded legacy review and the result is clean, the
    recorded payload digest must also equal the digest the legacy recorder
    computes for that form over these exact report bytes; cohort state keeps
    only the latest digest, so older clean events are checked by event alone.
    A findings digest covers adjudication fingerprints this adapter does not
    receive, so findings agreement is by event.
    """
    if not legacy_present:
        return False, False
    if legacy_event is None:
        # Legacy recorded but event unknown — cannot verify event agreement.
        return False, False
    # Event is known: check agreement by event.
    agrees = (legacy_event == "clean" and result == "clean") or (
        legacy_event == "findings" and result == "findings"
    )
    if not agrees:
        return False, True
    if (
        result == "clean"
        and legacy_state.get("last_review_record_operation_id") == source_event_id
    ):
        expected = _cohort()._review_payload_digest(
            form, hashlib.sha256(raw_report_text.encode("utf-8")).hexdigest()
        )
        if legacy_state.get("last_review_record_payload_digest") != expected:
            return False, True
    return True, False


# ── Idempotency check ─────────────────────────────────────────────────────────


def _find_existing_compat_report(
    store: object,
    source_event_id: str,
) -> dict[str, Any] | None:
    """Return the stored compat report for this source_event_id, or None."""
    for record in store.get_semantic_records("review-report.v1"):  # type: ignore[attr-defined]
        if record.get("lineage", {}).get("source_event_id") == source_event_id:
            return record
    return None


# ── Grammar classifiers ───────────────────────────────────────────────────────


def _run_classify_raw_report(
    source_event_id: str,
    raw_report_text: str,
    store_root: Path,
) -> dict[str, Any]:
    """Write raw_report_text to a private temp file and call _classify_raw_report.

    The temp directory is created inside the store's confinement root.
    Returns the result dict from _classify_raw_report, or {"classification": "error"}
    on any I/O failure.
    """
    tmpdir: Path | None = None
    try:
        tmpdir = Path(tempfile.mkdtemp(dir=str(store_root)))
        report_path = tmpdir / "compat-report.md"
        report_path.write_text(raw_report_text, encoding="utf-8")
        return _cohort()._classify_raw_report(report_path)  # type: ignore[no-any-return]
    except Exception:  # noqa: BLE001
        return {"classification": "error", "_reason": "io-failure", "not_checked_present": False}
    finally:
        if tmpdir is not None:
            shutil.rmtree(str(tmpdir), ignore_errors=True)


def _classify_direct_clean(
    source_event_id: str,
    raw_report_text: str,
    store_root: Path,
) -> tuple[str, list[dict[str, Any]]]:
    """Classify a direct-clean report using the legacy byte-equality rule.

    D1: The legacy ``--direct-clean-file`` rule requires exact byte equality
    with the clean sentinel ``CLEAN_SUBSTRING.encode("utf-8")``.  Any deviation
    — trailing newline, footer, findings — returns "unable".  This calls
    loop-cohort's own ``CLEAN_SUBSTRING`` constant; nothing is copied.
    """
    cohort = _cohort()
    sentinel: bytes = cohort.CLEAN_SUBSTRING.encode("utf-8")
    if raw_report_text.encode("utf-8") != sentinel:
        return "unable", []
    return "clean", []


def _classify_findings_form(
    source_event_id: str,
    raw_report_text: str,
    store_root: Path,
) -> tuple[str, list[dict[str, Any]]]:
    """Classify a findings-form report using the legacy raw classifier.

    grammar-valid findings (classification == "findings") → indeterminate
    grammar-invalid or schema-invalid → unable
    """
    result = _run_classify_raw_report(source_event_id, raw_report_text, store_root)
    if result.get("classification") == "findings":
        # Grammar-valid findings without adjudication is unmappable → indeterminate
        return "indeterminate", []
    # Grammar-invalid or any other outcome → unable
    return "unable", []


# Audit decision entry produced by _classify_adjudicated.
_AuditEntry = dict[str, Any]  # {finding, decision, authority_ref}


def _classify_adjudicated(
    raw_report_text: str,
    adjudication_text: str | None,
) -> tuple[str, list[dict[str, Any]], list[_AuditEntry]]:
    """Parse the adjudicated form.

    raw_report_text carries the finding.v1 list as JSON.
    adjudication_text carries per-finding audit decisions as JSON:
      {finding_id: {decision: "sustained"|"refuted", authority_ref: "..."}}

    A finding that fails the finding contract (unknown major, missing or
    mistyped field, unsafe content) or repeats a finding_id makes the report
    schema-invalid, so the result is "unable" and nothing may be persisted.
    A schema-valid report whose audit cannot be mapped one-to-one is
    "indeterminate".

    Returns:
      ("findings", findings, audit_entries) on success
      ("indeterminate", [], [])             on an unmappable audit
      ("unable", [], [])                    on a schema-invalid report
    """
    if adjudication_text is None:
        return "indeterminate", [], []

    # Parse raw_report_text as JSON list of finding.v1 dicts.
    try:
        raw_findings = json.loads(raw_report_text)
    except (json.JSONDecodeError, ValueError):
        return "indeterminate", [], []

    if not isinstance(raw_findings, list) or not raw_findings:
        return "indeterminate", [], []

    contracts = _review_contracts()
    validated_findings: list[dict[str, Any]] = []
    for item in raw_findings:
        ok, _code = contracts.validate_finding_dict(item)
        if not ok:
            return "unable", [], []
        validated_findings.append(copy.deepcopy(item))
    if len({f["finding_id"] for f in validated_findings}) != len(validated_findings):
        return "unable", [], []

    # Parse adjudication_text as {finding_id: {decision, authority_ref}}.
    try:
        audit = json.loads(adjudication_text)
    except (json.JSONDecodeError, ValueError):
        return "indeterminate", [], []

    if not isinstance(audit, dict):
        return "indeterminate", [], []

    # One-to-one mapping required.
    raw_ids = {f["finding_id"] for f in validated_findings}
    audit_ids = set(audit.keys())
    if raw_ids != audit_ids:
        return "indeterminate", [], []

    # Validate each audit decision.
    audit_entries: list[_AuditEntry] = []
    for finding in validated_findings:
        fid = finding["finding_id"]
        decision_entry = audit[fid]
        if not isinstance(decision_entry, dict):
            return "indeterminate", [], []
        decision = decision_entry.get("decision")
        authority_ref = decision_entry.get("authority_ref")
        if decision not in _CLOSED_AUDIT_DECISIONS:
            return "indeterminate", [], []
        if not isinstance(authority_ref, str) or not authority_ref:
            return "indeterminate", [], []
        audit_entries.append(
            {"finding": finding, "decision": decision, "authority_ref": authority_ref}
        )

    return "findings", validated_findings, audit_entries


# ── Structured record builders ────────────────────────────────────────────────


def _build_compat_report(
    source_event_id: str,
    role: str,
    result: str,
    findings: list[dict[str, Any]],
    review_subject: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic review-report.v1 from compat inputs."""
    return {
        "schema_version": 1,
        "report_id": f"compat-report:{source_event_id}",
        "role": role,
        "subject": copy.deepcopy(review_subject),
        "terminal_status": result,
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
            "source_event_id": source_event_id,
            "producer": "compat-adapter",
        },
        "findings": copy.deepcopy(findings),
    }


def _write_compat_report(
    store: object,
    report: dict[str, Any],
    *,
    source_event_id: str,
    review_subject: dict[str, Any],
    issuer: object,
    grant: object,
    audit_sink: object,
) -> None:
    """Persist the compat report via the review-persistence port."""
    _review_persistence().append_current_review_report(
        store,
        report,
        transaction_id=f"compat-tx:{source_event_id}:report",
        expected_subject=review_subject,
        issuer=issuer,
        grant=grant,
        audit_sink=audit_sink,
    )


def _build_assessment_for_finding(
    report: dict[str, Any],
    finding: dict[str, Any],
    audit_entry: _AuditEntry,
    *,
    source_event_id: str,
    review_subject: dict[str, Any],
    all_rule_refs: set[str],
) -> dict[str, Any]:
    """Assess one finding: sustained → supported via authority; refuted → unsupported-opinion."""
    ra = _review_assessment()
    report_id: str = report["report_id"]
    finding_id: str = finding["finding_id"]
    assessment_id = f"compat-assessment:{source_event_id}:{finding_id}"

    decision = audit_entry["decision"]
    authority_ref = audit_entry["authority_ref"]

    if decision == "refuted":
        # Refuted findings are assessed as unsupported-opinion.
        return ra.assess_finding_actual_failure(
            report,
            finding,
            assessment_id=assessment_id,
            current_subject=review_subject,
            current_report_id=report_id,
            current_rule_refs=all_rule_refs,
            current_evidence_refs=set(finding.get("evidence_refs", [])),
            controlled_facts={"falsifiable-delivery-failure": False},
            controlled_edges={
                "rule-to-observation": None,
                "observation-to-reachable-path": None,
                "reachable-path-to-actual-failure": None,
            },
            predicate_version=_COMPAT_PREDICATE_VERSION,
        )
    # Sustained findings are assessed through the named independent-authority
    # judgment shape.  The authority_ref from the audit is the authority
    # identity; it is added to current_evidence_refs so edge_evidence_refs
    # validation passes.
    evidence_refs_with_authority = set(finding.get("evidence_refs", [])) | {authority_ref}
    independent_authority = {
        "authority_ref": authority_ref,
        "requested_judgment": "supported",
        "edge_evidence_refs": [authority_ref],
        "predicate_judgments": {"falsifiable-delivery-failure": True},
        "rationale": "Adjudicated as sustained by the review authority.",
        "current": True,
    }
    return ra.assess_finding_actual_failure(
        report,
        finding,
        assessment_id=assessment_id,
        current_subject=review_subject,
        current_report_id=report_id,
        current_rule_refs=all_rule_refs,
        current_evidence_refs=evidence_refs_with_authority,
        controlled_facts={},
        controlled_edges={
            "rule-to-observation": None,
            "observation-to-reachable-path": None,
            "reachable-path-to-actual-failure": None,
        },
        predicate_version=_COMPAT_PREDICATE_VERSION,
        independent_authority=independent_authority,
    )


class ReviewCompatRefused(Exception):
    """The compatibility adapter refused a request that conflicts with stored facts."""

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code = denial_code


def _canonical(value: Any) -> str:
    """Return deterministic JSON for record comparison."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _string_values(value: Any) -> list[str]:
    """Return every string key and value inside a decoded JSON structure."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [
            text
            for key, item in value.items()
            for text in (*_string_values(key), *_string_values(item))
        ]
    if isinstance(value, (list, tuple)):
        return [text for item in value for text in _string_values(item)]
    return []


def _comparable_report(report: dict[str, Any]) -> dict[str, Any]:
    """Drop the lineage fields the persistence port assigns at commit time."""
    comparable = copy.deepcopy(report)
    comparable["lineage"].pop("sequence", None)
    comparable["lineage"].pop("previous_report_id", None)
    return comparable


def _build_all_assessments(
    report: dict[str, Any],
    findings: list[dict[str, Any]],
    audit_entries: list[_AuditEntry],
    *,
    source_event_id: str,
    review_subject: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build and validate every assessment before anything is written."""
    contracts = _review_contracts()
    all_rule_refs: set[str] = {f["rule_ref"] for f in findings}
    audit_by_id = {entry["finding"]["finding_id"]: entry for entry in audit_entries}
    assessments: list[dict[str, Any]] = []
    for finding in findings:
        assessment = _build_assessment_for_finding(
            report,
            finding,
            audit_by_id[finding["finding_id"]],
            source_event_id=source_event_id,
            review_subject=review_subject,
            all_rule_refs=all_rule_refs,
        )
        ok, _code = contracts.validate_review_record_dict("finding-assessment.v1", assessment)
        if not ok:
            raise ValueError("compat assessment failed its contract")
        assessments.append(assessment)
    return assessments


# ── Public entry point ────────────────────────────────────────────────────────


def reconcile_review_source_event(
    store: object,
    source_event: dict[str, Any],
    *,
    legacy_state: dict[str, Any],
    review_subject: dict[str, Any],
    review_policy: dict[str, Any],
    issuer: object,
    grant: object,
    audit_sink: object,
) -> dict[str, Any]:
    """Reconcile one legacy review source event with the structured boundary.

    Every input is validated and every record (report and assessments) is
    built in memory before the first write, so a refusal persists nothing.
    A replay must describe exactly the stored facts; any difference raises
    ``ReviewCompatRefused("denied-compat-source-event-conflict")`` with no
    write.  A crash between writes is repaired by writing only the missing
    assessments, each with a deterministic identity.

    Returns exactly: source_event_id, result ("clean" | "findings" |
    "indeterminate" | "unable"), legacy_present, structured_present (read
    from the store), acknowledged, and divergent.  ``review_policy`` is part
    of the published caller signature and is not consulted here.
    """
    legacy = copy.deepcopy(legacy_state)
    source_event_id: str = source_event["source_event_id"]
    role: str = source_event["role"]
    form: str = source_event["form"]
    raw_report_text: str = source_event["raw_report_text"]
    adjudication_text: str | None = source_event.get("adjudication_text")
    legacy_present, legacy_event = _determine_legacy_outcome(legacy, source_event_id)

    def _structured_present() -> bool:
        return _find_existing_compat_report(store, source_event_id) is not None

    def _unable() -> dict[str, Any]:
        return {
            "source_event_id": source_event_id,
            "result": "unable",
            "legacy_present": legacy_present,
            "structured_present": _structured_present(),
            "acknowledged": False,
            "divergent": False,
        }

    if form not in _CLOSED_FORMS:
        return _unable()

    cs = _content_safety()
    for text in (raw_report_text, adjudication_text):
        if text is None:
            continue
        # Guard lone Unicode surrogates: encode with strict errors so that a
        # surrogate (e.g. "\ud800") raises UnicodeEncodeError here rather than
        # propagating to the content-safety layer.  Pattern mirrors
        # _review_contracts.py near the _check_report_content_safety guard.
        try:
            encoded_text = text.encode("utf-8")
        except UnicodeEncodeError:
            return _unable()
        decision = cs.check_content_safety(
            "review-report",
            encoded_text,
            source_record_id=source_event_id,
            classification=_REPORT_CLASSIFICATION,
        )
        if not decision.accepted:
            return _unable()

    store_root = getattr(store, "_root", None)
    if not isinstance(store_root, Path) or not store_root.is_dir():
        return _unable()

    audit_entries: list[_AuditEntry] = []
    findings: list[dict[str, Any]] = []
    if form == "direct-clean":
        result, findings = _classify_direct_clean(source_event_id, raw_report_text, store_root)
    elif form == "findings":
        result, findings = _classify_findings_form(source_event_id, raw_report_text, store_root)
    else:
        result, findings, audit_entries = _classify_adjudicated(
            raw_report_text, adjudication_text
        )
    if result == "unable":
        return _unable()

    report = _build_compat_report(source_event_id, role, result, findings, review_subject)
    ok, _code = _review_contracts().validate_review_record_dict("review-report.v1", report)
    if not ok:
        return _unable()
    # JSON escapes can hide characters the raw-text check never saw, and
    # re-serializing escapes them again, so every decoded string value of the
    # report and audit passes the same content-safety boundary.
    decoded = "\n".join(
        _string_values([report, [(e["decision"], e["authority_ref"]) for e in audit_entries]])
    )
    # Guard surrogates on the decoded composite string for the same reason as above.
    try:
        encoded_decoded = decoded.encode("utf-8")
    except UnicodeEncodeError:
        return _unable()
    if not cs.check_content_safety(
        "review-report",
        encoded_decoded,
        source_record_id=source_event_id,
        classification=_REPORT_CLASSIFICATION,
    ).accepted:
        return _unable()
    assessments: list[dict[str, Any]] = []
    if result == "findings":
        try:
            assessments = _build_all_assessments(
                report,
                findings,
                audit_entries,
                source_event_id=source_event_id,
                review_subject=review_subject,
            )
        except Exception:  # noqa: BLE001 - any refusal of a built record is unable
            return _unable()

    existing_report = _find_existing_compat_report(store, source_event_id)
    stored_assessments = {
        record["assessment_id"]: record
        for record in store.get_semantic_records("finding-assessment.v1")  # type: ignore[attr-defined]
        if record.get("report_id") == report["report_id"]
    }
    if existing_report is not None:
        conflict = _canonical(_comparable_report(existing_report)) != _canonical(
            _comparable_report(report)
        ) or any(
            assessment["assessment_id"] in stored_assessments
            and _canonical(stored_assessments[assessment["assessment_id"]])
            != _canonical(assessment)
            for assessment in assessments
        ) or not set(stored_assessments) <= {a["assessment_id"] for a in assessments}
        if conflict:
            raise ReviewCompatRefused(
                "denied-compat-source-event-conflict",
                "a different request already produced facts for this source event",
            )
    else:
        _write_compat_report(
            store,
            report,
            source_event_id=source_event_id,
            review_subject=review_subject,
            issuer=issuer,
            grant=grant,
            audit_sink=audit_sink,
        )

    acceptance_fingerprint: str = review_subject["delivery_subject_ref"]["acceptance_fingerprint"]
    findings_by_id = {finding["finding_id"]: finding for finding in findings}
    for assessment in assessments:
        if assessment["assessment_id"] in stored_assessments:
            continue
        finding = findings_by_id[assessment["finding_id"]]
        _review_bridge().append_finding_assessment_bridge(
            store,
            assessment,
            report_id=report["report_id"],
            finding=finding,
            affected_criteria=finding["affected_acceptance_criteria"],
            transaction_id=f"compat-tx:{source_event_id}:assess:{finding['finding_id']}",
            acceptance_fingerprint=acceptance_fingerprint,
            issuer=issuer,
            grant=grant,
            audit_sink=audit_sink,
        )

    acknowledged, divergent = _compute_acknowledged_divergent(
        legacy_present,
        legacy_event,
        result,
        legacy_state=legacy,
        form=form,
        raw_report_text=raw_report_text,
        source_event_id=source_event_id,
    )
    return {
        "source_event_id": source_event_id,
        "result": result,
        "legacy_present": legacy_present,
        "structured_present": _structured_present(),
        "acknowledged": acknowledged,
        "divergent": divergent,
    }
