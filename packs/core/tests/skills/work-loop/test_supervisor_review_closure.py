"""The supervisor review stage closes from Slice 2 readiness (T3).

VI-6020 (AC-0001, AC-0003): a supported finding gets a repair-request, `fixed-by`
follows only a fresh report that no longer carries it, and the run passes on the
step where readiness turns eligible. VI-6021 (AC-0002): a `risk-owner` decision
records `accept-risk` and any other result records nothing. VI-6022 (AC-0004): a
synthetic role added only to the rules closes its obligation. VI-6023 (AC-0017):
every Slice 2 compatibility row maps to its required result through the
supervisor's ingest. The function-level cases use a real evidence store; the runs
that drive `work-supervisor.py` sit behind the supervisor integration marker.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_HELPER_PATHS = {
    "supervisor_harness": _HERE / "supervisor_harness.py",
    "supervisor_support": _HERE / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")
review = h.cli._supervisor("_supervisor_review.py")
Refusal = review.Refusal
security = h.cli._supervisor("_security_capability.py")
evidence_store = h.cli._supervisor("_evidence_store.py")
persistence = h.cli._supervisor("_review_persistence.py")
bridge = h.cli._supervisor("_review_bridge.py")
selection = h.cli._supervisor("_review_selection.py")
disposition = h.cli._supervisor("_review_disposition.py")

SPEC = h.SPEC_DIR
OWNER = "owner:0123456789ab"
RISK_OWNER = "risk-owner:0123456789ab"
SKILL = sup.SCRIPTS.parent
_ROSTER_HEADER = "| The change reaches | Adds |"

integration = sup.INTEGRATION


# ── a real evidence store, without a git run ────────────────────────────────


def _sink(event: object) -> None:
    """Accept security events."""


class Lab:
    """An evidence store, an issuer, and the writes the review boundary takes."""

    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.store = evidence_store.EvidenceStore(root / "evidence.log")
        self.store.open()
        self.issuer = security.CapabilityIssuer()
        self.grant = self.issuer.issue_root_grant(
            roots=["evidence"],
            operations=["append"],
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
        )
        self.ws = SimpleNamespace(spec_rel=SPEC, clock=lambda: h.FIXED_TIME)
        self.state = SimpleNamespace(run_id="run-0123456789abcdef")

    def subject(self, tag: str, policy: str = "review-policy-t3") -> dict[str, Any]:
        """A review subject; each *tag* is another delivery fingerprint and path."""
        delivery = {
            "schema_version": 1,
            "subject_id": "delivery-subject-t3",
            "acceptance_fingerprint": f"acceptance-fp-{tag}",
            "product": {"base_ref": "base-tree", "result_ref": f"result-tree-{tag}"},
            "spec": {"path": f"{SPEC}/spec.md", "fingerprint": "spec-fp"},
            "evidence_policy_ref": "evidence-policy",
            "exclusions": [],
            "lineage": {"provider": "synthetic", "projection_version": "1.0"},
            "task_projection_revision": "task-rev",
            "task_projection_hash": "task-hash",
        }
        return selection.project_review_subject(
            delivery,
            changed_paths=[{"path": f"calc-{tag}.py", "status": "added"}],
            review_policy_fingerprint=policy,
        )

    def report(
        self,
        subject: dict[str, Any],
        report_id: str,
        findings: list[dict[str, Any]],
        role: str = "adversarial-reviewer",
    ) -> dict[str, Any]:
        record = {
            "schema_version": 1,
            "report_id": report_id,
            "role": role,
            "subject": copy.deepcopy(subject),
            "terminal_status": "findings" if findings else "clean",
            "lineage": {
                "sequence": 1,
                "review_policy_fingerprint": subject["review_policy_fingerprint"],
                "source_event_id": f"event-{report_id}",
                "producer": "synthetic-reviewer",
            },
            "findings": copy.deepcopy(findings),
        }
        persistence.append_current_review_report(
            self.store,
            record,
            transaction_id=f"tx:{report_id}",
            expected_subject=subject,
            issuer=self.issuer,
            grant=self.grant,
            audit_sink=_sink,
        )
        return record

    def assess(
        self, report: dict[str, Any], finding_id: str, outcome: str, assessment_id: str
    ) -> dict[str, Any]:
        """Append one assessment of *finding_id* in *report*."""
        finding = next(f for f in report["findings"] if f["finding_id"] == finding_id)
        record = {
            "schema_version": 1,
            "assessment_id": assessment_id,
            "finding_id": finding_id,
            "report_id": report["report_id"],
            "review_subject_fingerprint": report["subject"]["review_subject_fingerprint"],
            "assessment": outcome,
            "evidence_refs": ["calc.py"],
            "lineage": {"predicate_version": "v1"},
        }
        bridge.append_finding_assessment_bridge(
            self.store,
            record,
            report_id=report["report_id"],
            finding=finding,
            affected_criteria=finding["affected_acceptance_criteria"],
            transaction_id=f"tx:{assessment_id}",
            acceptance_fingerprint=report["subject"]["delivery_subject_ref"][
                "acceptance_fingerprint"
            ],
            issuer=self.issuer,
            grant=self.grant,
            audit_sink=_sink,
        )
        return record

    def record(self, subject: dict[str, Any], step: str) -> None:
        review.record_dispositions(
            self.ws, self.state, self.store, self.issuer, _sink, subject=subject, step=step
        )

    def dispositions(self, kind: str | None = None) -> list[dict[str, Any]]:
        found = self.store.get_semantic_records("finding-disposition.v1")
        return [d for d in found if kind is None or d["disposition"] == kind]

    def readiness(self, subject: dict[str, Any]) -> dict[str, Any]:
        policy = {
            "policy_id": "policy-t3",
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "policy_version": "1",
            "selector": "synthetic",
            "roles": [{"role": "adversarial-reviewer", "kind": "mandatory"}],
            "waivers": [],
        }
        return disposition.review_readiness(  # type: ignore[no-any-return]
            self.store, review_subject=subject, review_policy=policy
        )


def _finding(
    finding_id: str, *, material: bool = True, failure: str = "calc.answer returns a wrong value"
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "finding_id": finding_id,
        "rule_ref": "AC-0001",
        "observation": "The calculator answers 41.",
        "reachable_path": "calc.answer",
        "actual_failure": failure,
        "affected_acceptance_criteria": ["AC-0001"],
        "evidence_refs": ["calc.py"],
        "material": material,
    }


# ── VI-6020: repair work, fixed-by, and the closing step ────────────────────


def test_vi6020_fixed_by_follows_only_a_fresh_report_that_no_longer_carries_the_finding(
    tmp_path: Path,
) -> None:
    """VI-6020: AC-0003: repair-request first, fixed-by only after a clean replacement report."""
    lab = Lab(tmp_path)
    first = lab.subject("a")
    carried = lab.report(first, "report-1", [_finding("finding-1")])
    lab.assess(carried, "finding-1", "supported", "assessment-1")
    lab.record(first, "step-1")

    (repair,) = lab.dispositions()
    assert repair["disposition"] == "repair-request"
    assert repair["decision_maker"] == {"identity": lab.state.run_id, "role": "work-supervisor"}
    ready = lab.readiness(first)
    assert ready["acceptance_eligible"] is False
    assert [f["finding_id"] for f in ready["open_findings"]] == ["finding-1"]
    lab.record(first, "step-1")  # a second look at the same facts writes nothing
    assert len(lab.dispositions()) == 1

    # A fresh report for a replacement subject that still carries the finding.
    second = lab.subject("b")
    still = lab.report(second, "report-2", [_finding("finding-1")])
    lab.record(second, "step-2")
    assert lab.dispositions("fixed-by") == []
    lab.assess(still, "finding-1", "supported", "assessment-2")
    lab.record(second, "step-3")
    assert lab.dispositions("fixed-by") == []
    assert [d["review_subject_fingerprint"] for d in lab.dispositions("repair-request")] == [
        first["review_subject_fingerprint"],
        second["review_subject_fingerprint"],
    ]

    # A fresh clean report for a third subject closes both earlier findings.
    third = lab.subject("c")
    lab.report(third, "report-3", [])
    lab.record(third, "step-4")
    fixed = lab.dispositions("fixed-by")
    assert sorted(d["replacement_report_id"] for d in fixed) == ["report-3", "report-3"]
    for done, old in zip(fixed, (first, second), strict=True):
        assert done["review_subject_fingerprint"] == old["review_subject_fingerprint"]
        assert lab.store.disposition_closes(done["disposition_id"], old)
    assert lab.readiness(third)["acceptance_eligible"] is True


def test_vi6020_a_replacement_with_an_unassessed_finding_waits(tmp_path: Path) -> None:
    """VI-6020: fixed-by waits for every replacement finding to carry its assessment."""
    lab = Lab(tmp_path)
    first = lab.subject("a")
    lab.assess(
        lab.report(first, "report-1", [_finding("finding-1")]), "finding-1", "supported", "a-1"
    )
    lab.record(first, "step-1")
    second = lab.subject("b")
    other = lab.report(
        second, "report-2", [_finding("finding-2", failure="calc.answer has no docstring")]
    )
    lab.record(second, "step-2")
    assert lab.dispositions("fixed-by") == []
    lab.assess(other, "finding-2", "unsupported-opinion", "a-2")
    lab.record(second, "step-3")
    assert len(lab.dispositions("fixed-by")) == 1


@integration
def test_vi6020_a_synthetic_run_repairs_and_passes_when_readiness_turns_eligible(
    tmp_path: Path,
) -> None:
    """VI-6020: AC-0001, AC-0003: repair work, fixed-by, and the pass step, through a run."""
    repo, controller, decision = _run_to_open_finding(tmp_path)
    store = h.workspace(repo).open_evidence()
    (repair,) = store.get_semantic_records("finding-disposition.v1")
    assert repair["disposition"] == "repair-request" and repair["finding_id"] == "finding-1"
    assert _last_operation(repo) == "review"
    assert "evidence.jsonl" in h.git(repo, "show", "HEAD", "--stat", "--format=")
    view = _status(repo)["readiness"]
    assert view["ready"] is False and view["review"]["acceptance_eligible"] is False
    # Repair work reaches the controller through the existing human-decision request.
    assert decision["kind"] == "human-decision" and "Replan repair work" in decision["question"]
    old_key = decision["selection_key"]

    # The controller replans with a repair task; the supervisor dispatches it.
    repair_task = sup.task(
        "T4",
        "Repair note is written",
        touches="`repair.txt`",
        mode="goal-based",
        tests="no stub (goal-based)",
        done="repair.txt says fixed",
    )
    plan = sup.plan(sup.TASKS["calc"](), sup.TASKS["push"](), sup.TASKS["plain"](), repair_task)
    (repo / SPEC / "plan.md").write_text(plan, "utf-8")
    request = _next(repo)
    assert request["kind"] == "implement-task" and request["task"]["title"].startswith("Repair")
    (repo / "repair.txt").write_text("fixed\n", "utf-8")
    result = {**_result(request), "gate": {"passed": True}}
    assert controller.report(result)[0] == 0

    # The repaired product asks for fresh gates, a fresh selection, and a fresh report.
    request = _next(repo)
    assert request["kind"] == "run-gates"
    assert controller.report(controller.work(request))[0] == 0
    request = _next(repo)
    assert request["kind"] == "review-role" and request["selection_key"] != old_key
    assert controller.report(_result(request, selection=h.select_none(request)))[0] == 0
    request = _next(repo)
    assert request["kind"] == "review-role" and request["role"] == "adversarial-reviewer"
    assert request["review_subject_fingerprint"] != repair["review_subject_fingerprint"]

    # Until the clean report lands, the stage is open and no fixed-by exists.
    before = _status(repo)["readiness"]
    assert before["ready"] is False and before["review"]["acceptance_eligible"] is False
    assert _status(repo)["terminal"] is False
    assert [d["disposition"] for d in store.get_semantic_records("finding-disposition.v1")] == [
        "repair-request"
    ]
    clean = h.report_review("adversarial-reviewer", request["review_subject"], 1)
    clean["report_id"] = "report-clean-after-repair"
    clean["terminal_status"], clean["findings"] = "clean", []
    code, admitted = controller.report(_result(request, report=clean))
    assert code == 0, admitted
    assert admitted["admitted"] == "review"

    # The same step recorded fixed-by, and readiness is eligible exactly now.
    store = h.workspace(repo).open_evidence()
    kinds = {d["disposition"]: d for d in store.get_semantic_records("finding-disposition.v1")}
    assert set(kinds) == {"repair-request", "fixed-by"}
    assert kinds["fixed-by"]["replacement_report_id"] == clean["report_id"]
    assert store.disposition_closes(kinds["fixed-by"]["disposition_id"], _old_subject(store))
    after = _status(repo)["readiness"]
    assert after["review"]["acceptance_eligible"] is True and after["ready"] is True
    assert after["review"]["open_findings"] == []
    assert _status(repo)["terminal"] is True
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload.get("terminal") is True


# ── VI-6021: accept-risk ────────────────────────────────────────────────────


def _lab_with_findings(root: Path) -> tuple[Lab, dict[str, Any]]:
    """One report with a supported material, a supported non-material, and an opinion finding."""
    lab = Lab(root)
    subject = lab.subject("a")
    report = lab.report(
        subject,
        "report-1",
        [
            _finding("f-material", failure="the answer is wrong"),
            _finding("f-minor", material=False, failure="the name is odd"),
            _finding("f-opinion", failure="the style is not liked"),
        ],
    )
    lab.assess(report, "f-material", "supported", "a-material")
    lab.assess(report, "f-minor", "supported", "a-minor")
    lab.assess(report, "f-opinion", "unsupported-opinion", "a-opinion")
    return lab, subject


def _accept(lab: Lab, subject: dict[str, Any], ids: list[str], ref: str = RISK_OWNER) -> None:
    open_findings = lab.readiness(subject)["open_findings"]
    write = review.accept_risk_writer(
        lab.ws,
        subject=subject,
        open_findings=open_findings,
        record={"request_id": "decide:review-not-eligible:abc", "finding_ids": ids,
                "authority_ref": ref},
        role="risk-owner",
    )
    write(lab.store, lab.issuer, lab.grant, _sink)


def test_vi6021_accept_risk_closes_exactly_the_named_open_finding(tmp_path: Path) -> None:
    """VI-6021: AC-0002: the risk-owner reference is the decision maker; readiness counts it."""
    lab, subject = _lab_with_findings(tmp_path)
    assert lab.readiness(subject)["acceptance_eligible"] is False
    _accept(lab, subject, ["f-material"])
    (accepted,) = lab.dispositions("accept-risk")
    assert accepted["finding_id"] == "f-material"
    assert accepted["decision_maker"] == {"identity": RISK_OWNER, "role": "risk-owner"}
    ready = lab.readiness(subject)
    assert ready["acceptance_eligible"] is True and ready["open_findings"] == []
    # Slice 2 keeps the contradiction: accept-risk adds no support, only review closure.
    active = lab.store.get_all_active_receipts()
    assert any(r["selector"]["term"] == "supported-review-failure" for r in active)


@pytest.mark.parametrize(
    "ids",
    [["f-minor"], ["f-opinion"], ["f-unknown"]],
    ids=["not-material", "not-supported", "not-current"],
)
def test_vi6021_a_finding_that_is_not_open_supported_and_material_is_refused(
    tmp_path: Path, ids: list[str]
) -> None:
    """VI-6021: a non-material, unsupported, or unknown finding records nothing."""
    lab, subject = _lab_with_findings(tmp_path)
    with pytest.raises(Refusal) as refused:
        _accept(lab, subject, ids)
    assert refused.value.code == "invalid-result"
    assert lab.dispositions("accept-risk") == []


def test_vi6021_an_already_closed_finding_is_not_current(tmp_path: Path) -> None:
    """VI-6021: accepting the same finding twice refuses the second."""
    lab, subject = _lab_with_findings(tmp_path)
    _accept(lab, subject, ["f-material"])
    with pytest.raises(Refusal) as refused:
        _accept(lab, subject, ["f-material"])
    assert refused.value.code == "invalid-result"
    assert len(lab.dispositions("accept-risk")) == 1


def test_vi6021_only_risk_owner_decisions_on_a_review_not_eligible_request_pass() -> None:
    """VI-6021: a wrong role, another reason, an unknown decision, and a bad shape refuse."""
    ws = SimpleNamespace(policy=h.admission.load_policy())
    state = SimpleNamespace(run_id="run-0123456789abcdef")
    request = {"request_id": "decide:review-not-eligible:abc", "reason": "review-not-eligible",
               "selection_key": "a" * 64}
    good = {"decision": "accept-risk", "authority_ref": RISK_OWNER, "finding_ids": ["f-1"]}
    record = review.admit_decision(ws, state, request, {"decision": good})
    assert record["decision"] == "accept-risk" and record["finding_ids"] == ["f-1"]
    assert record["authority_ref"] == RISK_OWNER

    refused: list[tuple[dict[str, Any], dict[str, Any]]] = [
        (request, {"decision": {**good, "authority_ref": OWNER}}),
        (request, {"decision": {**good, "authority_ref": "risk-owner-x:0123456789ab"}}),
        (request, {"decision": {**good, "decision": "waive-everything"}}),
        (request, {"decision": {**good, "finding_ids": []}}),
        (request, {"decision": {**good, "finding_ids": ["f-1", "f-1"]}}),
        (request, {"decision": {**good, "selection_key": "a" * 64}}),
        (request, {"decision": {"decision": "accept-risk", "authority_ref": RISK_OWNER}}),
        ({**request, "reason": "criteria-unsupported"}, {"decision": good}),
        ({**request, "reason": "gates-failed"}, {"decision": good}),
        ({**request, "reason": "retry-cap"}, {"decision": good}),
    ]
    for asked, answer in refused:
        with pytest.raises(Refusal) as error:
            review.admit_decision(ws, state, asked, answer)
        assert error.value.code in {"authority-refused", "invalid-result"}, answer


@integration
def test_vi6021_a_risk_owner_decision_through_a_run_closes_the_finding(tmp_path: Path) -> None:
    """VI-6021: AC-0002: refusals write nothing; the risk-owner decision records and passes."""
    repo, controller, decision = _run_to_open_finding(tmp_path)
    head = h.git(repo, "rev-parse", "HEAD")
    for answer in (
        {"decision": "accept-risk", "authority_ref": OWNER, "finding_ids": ["finding-1"]},
        {"decision": "accept-risk", "authority_ref": RISK_OWNER, "finding_ids": ["finding-9"]},
        {"decision": "accept-risk", "authority_ref": RISK_OWNER,
         "finding_ids": ["finding-1", "finding-9"]},
        {"decision": "waive-everything", "authority_ref": RISK_OWNER},
        {"decision": "accept-risk", "authority_ref": RISK_OWNER, "finding_ids": ["finding-1"],
         "selection_key": decision["selection_key"]},
    ):
        code, refused = controller.report(_result(decision, decision=answer))
        assert code == 1, answer
        assert refused["refusal"]["code"] in {"authority-refused", "invalid-result"}, refused
        assert h.git(repo, "rev-parse", "HEAD") == head
    store = h.workspace(repo).open_evidence()
    assert [d["disposition"] for d in store.get_semantic_records("finding-disposition.v1")] == [
        "repair-request"
    ]

    answer = {"decision": "accept-risk", "authority_ref": RISK_OWNER, "finding_ids": ["finding-1"]}
    code, admitted = controller.report(_result(decision, decision=answer))
    assert code == 0 and admitted["admitted"] == "review"
    stat = h.git(repo, "show", "HEAD", "--stat", "--format=")
    assert _last_operation(repo) == "review"
    assert "review-decisions.jsonl" in stat and "evidence.jsonl" in stat
    lines = h.git(repo, "show", f"HEAD:{SPEC}/delivery/review-decisions.jsonl").splitlines()
    assert json.loads(lines[-1])["finding_ids"] == ["finding-1"]

    store = h.workspace(repo).open_evidence()
    accepted = [d for d in store.get_semantic_records("finding-disposition.v1")
                if d["disposition"] == "accept-risk"]
    assert [d["decision_maker"] for d in accepted] == [
        {"identity": RISK_OWNER, "role": "risk-owner"}
    ]
    view = _status(repo)["readiness"]
    assert view["review"]["open_findings"] == [] and view["review"]["acceptance_eligible"]
    assert view["ready"] is True
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0 and payload.get("terminal") is True


# ── VI-6022: a role added only to the rules ─────────────────────────────────


def _roster_module() -> ModuleType:
    """The roster parity check, loaded from its test module by path."""
    alias = "core_work_loop_roster_parity"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HERE / "test_review_rules_roster.py")
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


def test_vi6022_a_role_added_only_to_the_rules_closes_its_obligation(tmp_path: Path) -> None:
    """VI-6022: AC-0004: no roster table, one new rules entry, no code edit, closes on a report."""
    skill = tmp_path / "work-loop"
    skill.mkdir()
    lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("\n")
    start = lines.index(_ROSTER_HEADER)
    end = start + 2
    while lines[end].startswith("|"):
        end += 1
    (skill / "SKILL.md").write_text("\n".join(lines[:start] + lines[end:]), encoding="utf-8")
    rules = json.loads((SKILL / "review-rules.json").read_text(encoding="utf-8"))
    rules["roles"].append({
        "role": "synthetic-reviewer",
        "kind": "conditional",
        "condition": "the change reaches a synthetic lens",
        "mode_limit": ["light", "full"],
        "boundary": "Reviews only the synthetic lens.",
        "fallback": "",
        "mandatory_when": "selected",
    })
    (skill / "review-rules.json").write_text(json.dumps(rules), encoding="utf-8")
    assert _ROSTER_HEADER not in (skill / "SKILL.md").read_text(encoding="utf-8")
    # With no table to compare, the roster parity check has nothing to object to.
    assert _roster_module().roster_problems(skill) == []

    loaded = review.load_rules(skill / "review-rules.json")
    assert "synthetic-reviewer" in review.candidates(loaded)
    omitted = [
        {"role": r, "reason": "not reached"}
        for r in review.candidates(loaded)
        if r != "synthetic-reviewer"
    ]
    policy = review.resolve_policy(
        loaded, {"selected": ["synthetic-reviewer"], "omitted": omitted}
    )
    assert {"role": "synthetic-reviewer", "kind": "mandatory"} in policy["roles"]

    lab = Lab(tmp_path / "store")
    subject = lab.subject("a", policy=policy["review_policy_fingerprint"])
    verdict = disposition.review_readiness(
        lab.store, review_subject=subject, review_policy=policy
    )
    waiting = {o["role"]: o["decision"] for o in verdict["obligations"]}
    assert waiting["synthetic-reviewer"] == "mandatory-report-unsatisfied"
    lab.report(subject, "report-adversarial", [], role="adversarial-reviewer")
    partial = disposition.review_readiness(
        lab.store, review_subject=subject, review_policy=policy
    )
    assert partial["acceptance_eligible"] is False
    lab.report(subject, "report-synthetic", [], role="synthetic-reviewer")
    closed = disposition.review_readiness(
        lab.store, review_subject=subject, review_policy=policy
    )
    assert closed["acceptance_eligible"] is True
    assert {o["role"]: o["obligation_satisfied"] for o in closed["obligations"]} == {
        "adversarial-reviewer": True,
        "synthetic-reviewer": True,
    }
    # The shipped code was not edited for the role: it knows no name from the rules.
    for name in ("_supervisor_review.py", "_supervisor_readiness.py"):
        assert "synthetic-reviewer" not in (sup.SCRIPTS / name).read_text(encoding="utf-8")


# ── VI-6023: the ingest maps the compatibility corpus ───────────────────────


def _corpus_rows() -> list[tuple[Any, ...]]:
    """The parametrized rows Slice 2's compatibility test runs, read from that test."""
    path = _HERE / "test_review_compat.py"
    spec = importlib.util.spec_from_file_location("core_work_loop_review_compat_corpus", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    marks = [m for m in module.test_vi1013_compatibility_corpus.pytestmark if m.name == "parametrize"]
    (mark,) = marks
    return [tuple(getattr(row, "values", row)) for row in mark.args[1]]


def test_vi6023_every_compatibility_row_maps_to_its_required_result(tmp_path: Path) -> None:
    """VI-6023: AC-0017: each row of Slice 2's compatibility corpus, through the ingest."""
    rows = _corpus_rows()
    assert {r[0] for r in rows} >= {
        "direct-clean",
        "adjudicated-all-refuted",
        "findings-no-adjudication",
        "unknown-form",
        "content-safety-refused",
        "safe-unmappable",
        "one-sided-legacy-present",
        "one-sided-legacy-absent",
    }
    assert {r[3] for r in rows} == {"clean", "findings", "indeterminate", "unable"}
    for number, (label, kwargs, legacy_state, expected, acknowledged) in enumerate(rows):
        lab = Lab(tmp_path / f"row-{number}")
        subject = lab.subject("a")
        event = {"role": "legacy-reviewer", "adjudication_text": None, **kwargs}
        result = review.ingest_legacy_event(
            lab.store,
            event,
            legacy_state=legacy_state(),
            review_subject=subject,
            review_policy={},
            issuer=lab.issuer,
            grant=lab.grant,
            audit_sink=_sink,
        )
        assert result["result"] == expected, label
        assert result["acknowledged"] is acknowledged, label
        stored = [
            r["terminal_status"]
            for r in lab.store.get_semantic_records("review-report.v1")
            if r["lineage"]["source_event_id"] == event["source_event_id"]
        ]
        assert stored == ([] if expected == "unable" else [expected]), label


def test_vi6023_a_crash_before_acknowledgement_replays_to_the_same_facts(tmp_path: Path) -> None:
    """VI-6023: the replay row: the same paired facts, acknowledged once, with no duplicate."""
    rows = {r[0]: r for r in _corpus_rows()}
    _label, kwargs, legacy_state, _expected, _ack = rows["direct-clean"]
    lab = Lab(tmp_path)
    subject = lab.subject("a")
    event = {"role": "legacy-reviewer", "adjudication_text": None, **kwargs}

    def ingest(state: dict[str, Any]) -> dict[str, Any]:
        return review.ingest_legacy_event(  # type: ignore[no-any-return]
            lab.store, event, legacy_state=state, review_subject=subject, review_policy={},
            issuer=lab.issuer, grant=lab.grant, audit_sink=_sink,
        )

    first = ingest({"last_review_record_operation_id": None,
                    "last_review_record_payload_digest": None, "transition_history": []})
    assert first["result"] == "clean" and first["acknowledged"] is False
    second = ingest(legacy_state())
    assert second["result"] == "clean" and second["acknowledged"] is True
    assert len(lab.store.get_semantic_records("review-report.v1")) == 1


def test_vi6023_the_ingest_calls_the_shipped_mapping_and_does_not_copy_it() -> None:
    """VI-6023: the ingest holds none of the four result values; it calls the shipped mapping."""
    source = inspect.getsource(review.ingest_legacy_event)
    for value in ("clean", "findings", "indeterminate", "unable"):
        assert f'"{value}"' not in source
    assert "reconcile_review_source_event" in source


# ── a git-backed run to an open supported finding ───────────────────────────


def _result(request: dict[str, Any], **fields: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": request["kind"],
        **fields,
    }


def _next(repo: Path) -> dict[str, Any]:
    code, payload = h.run_cli(repo, "next", SPEC)
    assert code == 0, payload
    request: dict[str, Any] = payload["request"]
    return request


def _status(repo: Path) -> dict[str, Any]:
    code, view = h.run_cli(repo, "status", SPEC, "--json")
    assert code == 0, view
    return view


def _last_operation(repo: Path) -> str:
    message = h.git(repo, "log", "-1", "--format=%B")
    return next(
        line.split(": ", 1)[1]
        for line in message.splitlines()
        if line.startswith("Supervisor-Operation: ")
    )


def _old_subject(store: Any) -> dict[str, Any]:
    """The review subject the first report carried."""
    reports = store.get_semantic_records("review-report.v1")
    first = next(r for r in reports if r["findings"])
    subject: dict[str, Any] = first["subject"]
    return subject


def _run_to_open_finding(
    tmp_path: Path,
) -> tuple[Path, Any, dict[str, Any]]:
    """Drive a fixture run until a supported material finding is open.

    Returns the repo, the controller, and the unanswered ``review-not-eligible``
    request.
    """
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    for _ in range(60):
        request = _next(repo)
        if request["kind"] == "review-role":
            break
        if request["kind"] == "external-effect":
            controller.handle_effect(request)
            continue
        assert controller.report(controller.work(request))[0] == 0
    assert "candidates" in request
    assert controller.report(_result(request, selection=h.select_none(request)))[0] == 0
    request = _next(repo)
    assert request["kind"] == "review-role" and request["role"] == "adversarial-reviewer"
    report = h.report_review("adversarial-reviewer", request["review_subject"], 1)
    report["findings"][0]["material"] = True
    assert controller.report(_result(request, report=report))[0] == 0
    request = _next(repo)
    assert request["kind"] == "assess-finding"
    supported = {**h.assessment(request), "assessment": "supported"}
    assert controller.report(_result(request, assessment=supported))[0] == 0
    decision = _next(repo)
    assert decision["kind"] == "human-decision" and decision["reason"] == "review-not-eligible"
    assert "finding-1" in decision["question"] and "accept-risk" in decision["question"]
    return repo, controller, decision
