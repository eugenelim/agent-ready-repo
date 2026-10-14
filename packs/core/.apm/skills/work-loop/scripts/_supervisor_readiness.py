"""_supervisor_readiness — readiness derived from durable facts.

A run is ready when the current approval pair matches the working envelope and
terminal intent, every acceptance criterion is supported by fresh admissible
evidence, and the shared review readiness says the subject is acceptance
eligible. Nothing here reads a stored verdict or readiness answer: criteria
verdicts are evaluated from receipts on every call, and review readiness is
computed from the durable review records.

Freshness is exact-subject over the product: every file at HEAD outside the
spec directory, so a supervisor step that appends only ``delivery/`` records
never stales evidence.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module.

    Registered under a name unique to this scripts directory, so two installed
    copies of the skill never share an instance.
    """
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_loop = _supervisor("_supervisor_loop.py")
_projector = _supervisor("_supervisor_projector.py")
sibling = _loop.sibling
Refusal = _loop.Refusal

__all__ = [
    "criteria",
    "delivery_subject",
    "readiness",
    "readiness_action",
    "report_readiness",
    "review_subject",
]

EVIDENCE_POLICY = "work-supervisor:criteria:v1"
GATES_RUN = "run:gates"
_CRITERION_RE = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*\*\*(AC-\d{4})\b", re.MULTILINE)


def criteria(ws: Any) -> list[str]:
    """Acceptance criterion ids in the working spec's Acceptance Criteria section."""
    sections = _projector._find_sections(ws.spec_text(), "Acceptance Criteria")
    found = _CRITERION_RE.findall(sections[0]) if sections else []
    return list(dict.fromkeys(found))


def delivery_subject(ws: Any, state: Any) -> dict[str, Any]:
    """The ``delivery-subject.v1`` for the product at HEAD."""
    prefix = ws.spec_rel + "/"
    manifest = tuple(
        sorted((p, oid) for p, oid in ws.git.tree_entries() if not p.startswith(prefix))
    )
    return sibling("_subject_projection.py").project_delivery_subject(
        subject_id=state.run_id,
        base_ref=state.base,
        result_ref=state.head,
        spec_path=f"{ws.spec_rel}/spec.md",
        spec_fingerprint=state.latest["envelope"]["envelope_fingerprint"],
        evidence_policy_ref=EVIDENCE_POLICY,
        exclusions=(prefix,),
        provider="work-supervisor",
        projection_version="1",
        manifest_pairs=manifest,
    )


def review_subject(ws: Any, state: Any, subject: dict[str, Any]) -> dict[str, Any]:
    """The ``review-subject.v1`` over the product paths the run's own commits changed.

    Read from the run's ``stub`` and ``implement`` commits, so a rebase onto new
    upstream work never makes that work part of the run's review.
    """
    prefix = ws.spec_rel + "/"
    first_touch: dict[str, str] = {}
    for commit in state.commits:
        if commit.operation in ("stub", "implement"):
            for path in ws.git.touched_paths(commit.sha):
                if not path.startswith(prefix):
                    first_touch.setdefault(path, commit.sha)
    changes = []
    for path, sha in sorted(first_touch.items()):
        if ws.git.show(path) is None:
            status = "deleted"
        elif ws.git.show(path, f"{sha}^") is None:
            status = "added"
        else:
            status = "modified"
        changes.append({"path": path, "status": status})
    policy = ws.policy["review_policy"]
    return sibling("_review_selection.py").project_review_subject(
        subject,
        changed_paths=changes,
        review_policy_fingerprint=policy["review_policy_fingerprint"],
    )


def _properties(state: Any, ids: list[str]) -> list[dict[str, Any]]:
    authority = state.latest["approval"]["approval_id"]
    return [
        {
            "schema_version": 1,
            "property_id": ac,
            "spec_ref": "spec.md",
            "authority_ref": authority,
            "subject_selector": {"paths_or_artifacts": ["."], "fingerprint_algorithm": "sha256"},
            "required_observations": [
                {
                    "term": f"criterion:{ac}",
                    "observation_type": "gate",
                    "producer_class": _loop.PRODUCER_CLASS,
                    "outcomes": ["pass"],
                }
            ],
            "freshness_scope": "exact-subject",
            "satisfaction_rule": {"expression": "any"},
            "contradiction_rule": {"expression": f"criterion-fail:{ac}"},
            "policy_version": EVIDENCE_POLICY,
        }
        for ac in ids
    ]


def readiness(ws: Any, state: Any) -> dict[str, Any]:
    """Readiness from the approval pair, criteria verdicts, and review readiness."""
    subject = delivery_subject(ws, state)
    fingerprint = subject["acceptance_fingerprint"]
    ids = criteria(ws)
    store = ws.open_evidence()
    verdicts = store.evaluate_verdicts(
        _properties(state, ids), fingerprint, sibling("_acceptance.py")
    )
    by_criterion = {ac: v["verdict"] for ac, v in zip(ids, verdicts, strict=True)}
    gated = any(
        r["acceptance_fingerprint"] == fingerprint and r["observation"]["type"] == "gate"
        for r in state.receipts
    )
    gates_failed = any(
        r["acceptance_fingerprint"] == fingerprint and r["lineage"]["criterion_ref"] == GATES_RUN
        for r in state.receipts
    )
    review = review_subject(ws, state, subject)
    review_state = sibling("_review_disposition.py").review_readiness(
        store, review_subject=review, review_policy=ws.policy["review_policy"]
    )
    supported = all(v == "supported" for v in by_criterion.values())
    return {
        "ready": supported and not gates_failed and bool(review_state["acceptance_eligible"]),
        "gates_failed": gates_failed,
        "acceptance_fingerprint": fingerprint,
        "criteria": by_criterion,
        "gates_ran_for_subject": gated,
        "review_subject": review,
        "review": review_state,
    }


def readiness_action(ws: Any, state: Any) -> Any:
    """Evidence, review, or repair work while the run is not ready; None when ready."""
    view = readiness(ws, state)
    if view["ready"]:
        return None
    fingerprint = view["acceptance_fingerprint"]
    if view["gates_failed"]:
        return _loop.Action(
            "request",
            _loop.human_decision(
                ws,
                state,
                "gates-failed",
                "Gates failed on this product without naming a criterion. Replan repair work.",
                key=fingerprint,
            ),
        )
    unsupported = sorted(ac for ac, v in view["criteria"].items() if v != "supported")
    if unsupported:
        if not view["gates_ran_for_subject"]:
            return _loop.Action(
                "request",
                _loop.make_request(
                    ws,
                    state,
                    "run-gates",
                    f"gates:{fingerprint[:24]}",
                    acceptance_fingerprint=fingerprint,
                    criteria=list(view["criteria"]),
                ),
            )
        return _loop.Action(
            "request",
            _loop.human_decision(
                ws,
                state,
                "criteria-unsupported",
                "Gates ran on this product and these criteria are not supported: "
                + ", ".join(unsupported)
                + ". Replan repair work or amend the spec.",
                key=fingerprint,
            ),
        )
    review = view["review_subject"]
    subject_fp = review["review_subject_fingerprint"]
    reports = ws.open_evidence().get_semantic_records("review-report.v1")
    for decision in view["review"]["obligations"]:
        role = decision["role"]
        if decision["decision"] == "mandatory-report-unsatisfied":
            sequence = 1 + sum(
                1
                for r in reports
                if r["role"] == role and r["subject"]["review_subject_fingerprint"] == subject_fp
            )
            return _loop.Action(
                "request",
                _loop.make_request(
                    ws,
                    state,
                    "review-role",
                    f"review:{role}:{subject_fp[-24:]}:{sequence}",
                    role=role,
                    review_subject_fingerprint=subject_fp,
                    review_subject=review,
                ),
            )
        if decision["decision"] == "finding-assessment-required":
            assessed = {
                (a["report_id"], a["finding_id"])
                for a in ws.open_evidence().get_semantic_records("finding-assessment.v1")
                if a["assessment"] != "indeterminate"
            }
            current = _current_report(reports, role, subject_fp)
            for finding in current["findings"] if current else []:
                if (current["report_id"], finding["finding_id"]) not in assessed:
                    return _loop.Action(
                        "request",
                        _loop.make_request(
                            ws,
                            state,
                            "assess-finding",
                            f"assess:{current['report_id']}:{finding['finding_id']}",
                            role=role,
                            review_subject_fingerprint=subject_fp,
                            report_id=current["report_id"],
                            finding_id=finding["finding_id"],
                        ),
                    )
    return _loop.Action(
        "request",
        _loop.human_decision(
            ws,
            state,
            "review-not-eligible",
            "Review readiness is not acceptance eligible: a supported finding is open or an "
            "obligation cannot be decided. Replan repair work or record a disposition.",
            key=subject_fp,
        ),
    )


def _current_report(
    reports: list[dict[str, Any]], role: str, subject_fp: str
) -> dict[str, Any] | None:
    matching = [
        r
        for r in reports
        if r["role"] == role and r["subject"]["review_subject_fingerprint"] == subject_fp
    ]
    return max(matching, key=lambda r: r["lineage"]["sequence"]) if matching else None


def report_readiness(ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any]) -> str:
    """Admit a run-gates, review-role, or assess-finding result as one supervisor step."""
    step = request["request_id"]
    view = readiness(ws, state)
    fingerprint = view["acceptance_fingerprint"]
    if request["kind"] == "run-gates":
        gate = result.get("gate")
        rows = result.get("criteria")
        if (
            not isinstance(gate, dict)
            or not isinstance(gate.get("passed"), bool)
            or not isinstance(rows, list)
        ):
            raise Refusal(
                "invalid-result", "controller", "a run-gates result needs gate and criteria"
            )
        unattributed = not gate["passed"] and all(
            isinstance(row, dict) and row.get("outcome") == "pass" for row in rows
        )
        wanted = set(request["criteria"])
        receipts = []
        for row in rows:
            if (
                not isinstance(row, dict)
                or row.get("criterion_ref") not in wanted
                or row.get("outcome") not in ("pass", "fail")
            ):
                raise Refusal("invalid-result", "controller", "a criterion row is malformed")
            ac, outcome = row["criterion_ref"], row["outcome"]
            term = f"criterion:{ac}" if outcome == "pass" else f"criterion-fail:{ac}"
            receipts.append(
                _loop.receipt(
                    state,
                    step,
                    criterion=ac,
                    term=term,
                    observation="gate",
                    outcome=outcome,
                    fingerprint=fingerprint,
                )
            )
        if unattributed:
            # Gates failed without naming a criterion (a lint or typecheck, say):
            # recorded for the run so readiness asks for repair work.
            receipts.append(
                _loop.receipt(
                    state,
                    step,
                    criterion=GATES_RUN,
                    term="gates-failed",
                    observation="gate",
                    outcome="fail",
                    fingerprint=fingerprint,
                )
            )
        if not receipts:
            raise Refusal("invalid-result", "controller", "a run-gates result names no criterion")
        evidence = ws.evidence_append(receipts)
        ws.git.build_commit(
            run_id=state.run_id,
            step=step,
            operation="evidence",
            appends={"evidence.jsonl": evidence},
            summary="record gate evidence",
            known_steps=state.steps,
        )
        return "evidence"
    persistence = sibling("_review_persistence.py")
    bridge = sibling("_review_bridge.py")
    if request["kind"] == "review-role":
        report = result.get("report")
        if not isinstance(report, dict) or report.get("role") != request["role"]:
            raise Refusal(
                "invalid-result", "controller", "the report is not for the requested role"
            )

        def write_report(store: Any, issuer: Any, grant: Any, sink: Any) -> None:
            persistence.append_current_review_report(
                store,
                report,
                transaction_id=f"tx:{step}",
                expected_subject=view["review_subject"],
                issuer=issuer,
                grant=grant,
                audit_sink=sink,
            )

        writer = write_report
    else:
        assessment = result.get("assessment")
        if (
            not isinstance(assessment, dict)
            or assessment.get("report_id") != request["report_id"]
            or assessment.get("finding_id") != request["finding_id"]
        ):
            raise Refusal("invalid-result", "controller", "the assessment is not for the request")
        reports = ws.open_evidence().get_semantic_records("review-report.v1")
        source = next(r for r in reports if r["report_id"] == request["report_id"])
        finding = next(f for f in source["findings"] if f["finding_id"] == request["finding_id"])

        def write_assessment(store: Any, issuer: Any, grant: Any, sink: Any) -> None:
            bridge.append_finding_assessment_bridge(
                store,
                assessment,
                report_id=request["report_id"],
                finding=finding,
                affected_criteria=list(finding.get("affected_acceptance_criteria", [])),
                transaction_id=f"tx:{step}",
                acceptance_fingerprint=fingerprint,
                issuer=issuer,
                grant=grant,
                audit_sink=sink,
            )

        writer = write_assessment
    try:
        evidence = ws.evidence_append(writer=writer)
    except Exception as exc:  # noqa: BLE001 - every review-record refusal names its own code
        code = getattr(exc, "denial_code", None) or type(exc).__name__
        raise Refusal("review-record-refused", "controller", str(code)) from exc
    ws.git.build_commit(
        run_id=state.run_id,
        step=step,
        operation="review",
        appends={"evidence.jsonl": evidence},
        summary=f"record {request['kind']}",
        known_steps=state.steps,
    )
    return "review"
