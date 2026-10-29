"""Typed reports drive the shipped review path to the right acceptance verdicts.

Three fixture properties each hold a passing receipt and name
``supported-review-failure`` as their contradiction. A typed report is sent
through the shipped path: report contract, current-report persistence, finding
assessment, assessment bridge, and ``EvidenceStore.evaluate_verdicts``. A
supported material finding contradicts exactly the property it names; clean,
indeterminate, refused, and unsupported inputs leave every property supported.

Spec: docs/specs/grounding-preservation-review/spec.md
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"

ORDINARY = "ordinary-calls"
SEARCH = "default-search"
LIFECYCLE = "lifecycle"
PROPERTY_IDS = (ORDINARY, SEARCH, LIFECYCLE)
POLICY_FP = "review-policy-preservation-v1"
ADVERSARIAL = "adversarial-reviewer"
QUALITY = "quality-engineer"
UNSHIPPED_ROLE = "unshipped-review-role"
EVIDENCE = ["evidence:observation", "evidence:reachable-path", "evidence:failure"]
SPEC_TEXT = (
    "# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n"
    "- [ ] AC-0001. Ordinary calls resolve to no value node.\n"
)
PLAN_TAIL = "\n## Tasks\n\n### T1: Preserve call resolution\n\n- [ ] Done.\n"
PLAN_HEAD = "# Plan\n\n- **Status:** Approved\n\n## Design (LLD)\n\n"
MAP_HEADER = "| Class | Consumer evidence | Criterion or gap |\n| --- | --- | --- |\n"
MAP_ROWS = (
    "| selection and resolution | src/model/graph.py:4 | AC-0001 |",
    "| default search | src/model/graph.py:9 | AC-0002 |",
    "| lifecycle and cleanup | src/model/graph.py:12 | AC-0003 |",
)
PLAN_WITH_MAP = PLAN_HEAD + MAP_HEADER + "\n".join(MAP_ROWS) + "\n" + PLAN_TAIL
PLAN_REORDERED_MAP = PLAN_HEAD + MAP_HEADER + "\n".join(reversed(MAP_ROWS)) + "\n" + PLAN_TAIL
PLAN_NO_MAP = PLAN_HEAD + PLAN_TAIL
PLAN_NEW_TASKS = PLAN_HEAD + MAP_HEADER + "\n".join(MAP_ROWS) + (
    "\n\n## Tasks\n\n### T9: Different work entirely\n\n- [ ] Other.\n### T10: More\n\n- [ ] Too.\n"
)


def _load_module(name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path under a unique *name*."""
    assert stat.S_ISREG(os.lstat(path).st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(name, None)
        return module
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def m() -> SimpleNamespace:
    """The shipped review, evidence, and subject modules, loaded once by path."""
    return SimpleNamespace(
        review_contracts=_load_module("core_work_loop_review_contracts_preservation_review", SCRIPTS / "_review_contracts.py"),
        review_selection=_load_module("core_work_loop_review_selection_preservation_review", SCRIPTS / "_review_selection.py"),
        review_persistence=_load_module("core_work_loop_review_persistence_preservation_review", SCRIPTS / "_review_persistence.py"),
        review_assessment=_load_module("core_work_loop_review_assessment_preservation_review", SCRIPTS / "_review_assessment.py"),
        review_bridge=_load_module("core_work_loop_review_bridge_preservation_review", SCRIPTS / "_review_bridge.py"),
        evidence_store=_load_module("core_work_loop_evidence_store_preservation_review", SCRIPTS / "_evidence_store.py"),
        acceptance=_load_module("core_work_loop_acceptance_preservation_review", SCRIPTS / "_acceptance.py"),
        subject_source=_load_module("core_work_loop_subject_source_preservation_review", SCRIPTS / "_subject_source.py"),
        loop_guards=_load_module("core_work_loop_loop_guards_preservation_review", SCRIPTS / "_loop_guards.py"),
        security_capability=_load_module("core_work_loop_security_capability_preservation_review", SCRIPTS / "_security_capability.py"),
    )


def _null_sink(event: object) -> None:
    """Accept security events without persisting them."""


def _git(root: Path, *args: str) -> None:
    """Run one git command in *root*, failing the test on a non-zero exit."""
    subprocess.run(["git", *args], cwd=str(root), capture_output=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repository with one product file under ``src/model/``."""
    root = tmp_path / "repo"
    (root / "src" / "model").mkdir(parents=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    (root / "src" / "model" / "graph.py").write_text("def resolve():\n    pass\n", "utf-8")
    return root


def _property(property_id: str) -> dict[str, Any]:
    """An acceptance-property.v1 record with one test-result term."""
    return {
        "schema_version": 1,
        "property_id": property_id,
        "spec_ref": "docs/specs/shared-substrate-change/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {"paths_or_artifacts": ["src/model/"], "fingerprint_algorithm": "sha256"},
        "required_observations": [
            {
                "term": f"{property_id}-test",
                "observation_type": "test-result",
                "producer_class": "ci-runner",
                "outcomes": ["pass"],
            }
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": "supported-review-failure"},
        "policy_version": "v1",
    }


def _passing_receipt(property_id: str, fingerprint: str) -> dict[str, Any]:
    """A current passing evidence-receipt.v1 for *property_id*'s term."""
    return {
        "schema_version": 1,
        "receipt_id": f"{property_id}:pass",
        "acceptance_fingerprint": fingerprint,
        "lineage": {"criterion_ref": property_id},
        "selector": {"term": f"{property_id}-test"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "test-result"},
        "outcome": "pass",
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _finding(property_id: str) -> dict[str, Any]:
    """A material finding.v1 whose affected criteria name *property_id*."""
    return {
        "schema_version": 1,
        "finding_id": "finding-1",
        "rule_ref": "rule-preservation",
        "observation": "A consumer of the changed substrate was not updated.",
        "reachable_path": "consumer reads every node without a filter",
        "actual_failure": "The consumer returns the new node kind to callers.",
        "affected_acceptance_criteria": [property_id],
        "evidence_refs": list(EVIDENCE),
        "material": True,
    }


@dataclass
class World:
    """One delivery subject, review subject, policy, and evidence store."""

    m: SimpleNamespace
    store: Any
    issuer: Any
    grant: Any
    delivery: dict[str, Any]
    subject: dict[str, Any]
    policy: dict[str, Any]
    properties: list[dict[str, Any]]

    @property
    def fingerprint(self) -> str:
        """The acceptance fingerprint every receipt binds to."""
        return str(self.delivery["acceptance_fingerprint"])

    def obligations(self) -> list[dict[str, Any]]:
        """The ordered review obligations selected for the subject."""
        return list(self.m.review_selection.select_review_obligations(self.subject, self.policy))

    def report(
        self, role: str, status: str, findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """A review-report.v1 for *role* on this world's review subject."""
        return {
            "schema_version": 1,
            "report_id": "report-1",
            "role": role,
            "subject": copy.deepcopy(self.subject),
            "terminal_status": status,
            "lineage": {
                "sequence": 1,
                "review_policy_fingerprint": POLICY_FP,
                "source_event_id": "source-report-1",
                "producer": "synthetic-reviewer",
            },
            "findings": findings,
        }

    def persist(self, report: dict[str, Any]) -> None:
        """Persist *report* as the current report."""
        self.m.review_persistence.append_current_review_report(
            self.store,
            report,
            transaction_id=f"tx-{report['report_id']}",
            expected_subject=self.subject,
            issuer=self.issuer,
            grant=self.grant,
            audit_sink=_null_sink,
        )

    def assess(self, report: dict[str, Any], finding: dict[str, Any], *, supported: bool) -> dict[str, Any]:
        """Assess *finding* and record the assessment through the bridge."""
        assessment = self.m.review_assessment.assess_finding_actual_failure(
            report,
            finding,
            assessment_id=f"assessment-{finding['finding_id']}",
            current_subject=self.subject,
            current_report_id=report["report_id"],
            current_rule_refs={finding["rule_ref"]},
            current_evidence_refs=set(EVIDENCE),
            controlled_facts={"falsifiable-delivery-failure": supported},
            controlled_edges={
                "rule-to-observation": [EVIDENCE[0]],
                "observation-to-reachable-path": [EVIDENCE[1]],
                "reachable-path-to-actual-failure": [EVIDENCE[2]],
            },
            predicate_version="preservation-v1",
        )
        self.m.review_bridge.append_finding_assessment_bridge(
            self.store,
            assessment,
            report_id=report["report_id"],
            finding=finding,
            affected_criteria=finding["affected_acceptance_criteria"],
            transaction_id=f"tx-{assessment['assessment_id']}",
            acceptance_fingerprint=self.fingerprint,
            issuer=self.issuer,
            grant=self.grant,
            audit_sink=_null_sink,
        )
        return assessment

    def send(self, role: str, property_id: str, *, supported: bool = True) -> dict[str, Any]:
        """Send a one-finding typed report through the whole generic path."""
        finding = _finding(property_id)
        report = self.report(role, "findings", [finding])
        self.persist(report)
        return {
            "report": report,
            "assessment": self.assess(report, finding, supported=supported),
        }

    def decide(self, role: str, reports: list[dict[str, Any]], assessments: list[dict[str, Any]]) -> dict[str, Any]:
        """The obligation decision for *role*."""
        obligation = next(o for o in self.obligations() if o["role"] == role)
        return dict(
            self.m.review_selection.decide_review_obligation(
                obligation,
                review_subject=self.subject,
                policy=self.policy,
                reports=reports,
                assessments=assessments,
                dispositions=[],
            )
        )

    def review_failures(self) -> list[dict[str, Any]]:
        """Active review-failure receipts, in log order."""
        return [r for r in self.store.get_all_active_receipts() if r["observation"]["type"] == "review-failure"]

    def verdicts(self) -> dict[str, str]:
        """Verdict string for each fixture property."""
        result = self.store.evaluate_verdicts(
            self.properties, self.fingerprint, self.m.acceptance, adapter="sequential-reference"
        )
        return {p["property_id"]: v["verdict"] for p, v in zip(self.properties, result, strict=True)}


def _world(m: SimpleNamespace, repo: Path, store_dir: Path, plan: str = PLAN_WITH_MAP, roles: tuple[str, ...] = (ADVERSARIAL, QUALITY)) -> World:
    """Commit spec and plan, project the subjects, and seed three passing receipts."""
    spec_dir = repo / "docs" / "specs" / "shared-substrate-change"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(SPEC_TEXT, "utf-8")
    (spec_dir / "plan.md").write_text(plan, "utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "variant")
    delivery = m.subject_source.project_legacy_subject(
        repo_root=repo,
        spec_dir=spec_dir,
        approved_spec_hash=m.loop_guards.sha256_canonical_contract(spec_dir / "spec.md"),
        approved_plan_hash=m.loop_guards.sha256_canonical_contract(spec_dir / "plan.md"),
        audit_sink=_null_sink,
        subject_id="subject:shared-substrate-change",
        evidence_policy_ref="evidence-policy:v1",
    )
    subject = m.review_selection.project_review_subject(
        delivery,
        changed_paths=[{"path": "src/model/graph.py", "status": "added"}],
        review_policy_fingerprint=POLICY_FP,
    )
    policy = {
        "policy_id": "policy-preservation",
        "review_policy_fingerprint": POLICY_FP,
        "policy_version": "v1",
        "selector": "shared-substrate",
        "roles": [{"role": role, "kind": "mandatory"} for role in roles],
        "waivers": [],
    }
    store_dir.mkdir(parents=True, exist_ok=True)
    store = m.evidence_store.EvidenceStore(store_dir / "semantic-evidence.log")
    store.open()
    issuer = m.security_capability.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    for property_id in PROPERTY_IDS:
        store.append_receipt(
            _passing_receipt(property_id, delivery["acceptance_fingerprint"]),
            transaction_id=f"tx-seed-{property_id}",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    return World(m, store, issuer, grant, delivery, subject, policy, [_property(p) for p in PROPERTY_IDS])


@pytest.fixture
def world(m: SimpleNamespace, repo: Path, tmp_path: Path) -> World:
    """A fresh world with the shipped two-role mandatory policy."""
    return _world(m, repo, tmp_path / "store")


def _all_supported(world: World) -> None:
    """Assert every fixture property is supported."""
    assert world.verdicts() == dict.fromkeys(PROPERTY_IDS, "supported")


def _contradicted_only(world: World, property_id: str) -> None:
    """Assert *property_id* is contradicted and the other two are supported."""
    expected = dict.fromkeys(PROPERTY_IDS, "supported")
    expected[property_id] = "contradicted"
    assert world.verdicts() == expected


def test_fixture_properties_are_supported_before_any_report(world: World) -> None:
    """The baseline: three passing receipts give three supported verdicts."""
    _all_supported(world)
    assert world.review_failures() == []


def test_adversarial_missed_consumer_contradicts_only_default_search(world: World) -> None:
    """One material adversarial finding records one receipt and blocks acceptance."""
    sent = world.send(ADVERSARIAL, SEARCH)

    assert sent["assessment"]["assessment"] == "supported"
    [receipt] = world.review_failures()
    assert receipt["lineage"]["criterion_ref"] == SEARCH
    _contradicted_only(world, SEARCH)
    decision = world.decide(ADVERSARIAL, [sent["report"]], [sent["assessment"]])
    assert decision["obligation_satisfied"] is True
    assert decision["acceptance_block"] is True
    assert decision["decision"] == "open-supported-material-finding"


def test_quality_weak_evidence_contradicts_only_ordinary_calls(world: World) -> None:
    """One material quality finding contradicts the ordinary-calls property alone."""
    world.send(QUALITY, ORDINARY)

    [receipt] = world.review_failures()
    assert receipt["lineage"]["criterion_ref"] == ORDINARY
    _contradicted_only(world, ORDINARY)


def test_clean_report_records_nothing_and_satisfies_without_blocking(world: World) -> None:
    """A clean report leaves every property supported and blocks nothing."""
    report = world.report(ADVERSARIAL, "clean", [])
    world.persist(report)

    assert world.review_failures() == []
    _all_supported(world)
    decision = world.decide(ADVERSARIAL, [report], [])
    assert decision["obligation_satisfied"] is True
    assert decision["review_block"] is False
    assert decision["acceptance_block"] is False


def _without_affected(finding: dict[str, Any]) -> None:
    """Empty the affected-criteria list."""
    finding["affected_acceptance_criteria"] = []


def _without_observation(finding: dict[str, Any]) -> None:
    """Drop one required finding field."""
    del finding["observation"]


@pytest.mark.parametrize("break_finding", [_without_affected, _without_observation])
def test_malformed_finding_is_refused_and_nothing_is_persisted(world: World, break_finding: Any) -> None:
    """The shipped report contract refuses the report before any append."""
    finding = _finding(SEARCH)
    break_finding(finding)
    report = world.report(ADVERSARIAL, "findings", [finding])

    ok, _code = world.m.review_contracts.validate_review_report_dict(report)
    assert ok is False
    with pytest.raises(world.m.review_persistence.ReviewPersistenceRefused):
        world.persist(report)
    assert world.store.get_semantic_records("review-report.v1") == []
    assert world.review_failures() == []
    _all_supported(world)


def _outcome(world: World, role: str, property_id: str) -> dict[str, Any]:
    """Send one report and return its assessment, full active receipts, and verdicts."""
    sent = world.send(role, property_id)
    return {
        "assessment": sent["assessment"],
        "receipts": world.review_failures(),
        "verdicts": world.verdicts(),
    }


@pytest.mark.parametrize(("shipped_role", "property_id"), [(ADVERSARIAL, SEARCH), (QUALITY, ORDINARY)])
def test_role_name_does_not_change_assessments_receipts_or_verdicts(
    m: SimpleNamespace, repo: Path, tmp_path: Path, shipped_role: str, property_id: str
) -> None:
    """A role no shipped reviewer uses gives the same outcome as the shipped role."""
    shipped = _outcome(_world(m, repo, tmp_path / "a", roles=(shipped_role,)), shipped_role, property_id)
    other = _outcome(_world(m, repo, tmp_path / "b", roles=(UNSHIPPED_ROLE,)), UNSHIPPED_ROLE, property_id)

    assert other == shipped
    assert shipped["verdicts"][property_id] == "contradicted"


def test_unsupported_assessment_records_no_receipt(world: World) -> None:
    """An unsupported finding leaves its named property supported."""
    sent = world.send(ADVERSARIAL, SEARCH, supported=False)

    assert sent["assessment"]["assessment"] != "supported"
    assert world.review_failures() == []
    _all_supported(world)


def test_indeterminate_report_is_current_and_unsatisfied_for_a_distinct_reason(world: World) -> None:
    """An indeterminate report is the role's tip and differs from having no report."""
    no_report = world.decide(ADVERSARIAL, [], [])
    report = world.report(ADVERSARIAL, "indeterminate", [])
    world.persist(report)

    current, _code = world.m.review_persistence.select_current_review_report(
        world.store,
        role=ADVERSARIAL,
        expected_subject=world.subject,
        review_policy_fingerprint=POLICY_FP,
    )
    assert current == report
    decision = world.decide(ADVERSARIAL, [report], [])
    assert decision["obligation_satisfied"] is False
    assert decision["reason"] == "report-unable"
    assert no_report["reason"] == "denied-no-current-report"
    assert world.review_failures() == []
    _all_supported(world)


def _observed(world: World) -> dict[str, Any]:
    """Send AC-0009's report and capture what a plan edit must not move."""
    sent = world.send(ADVERSARIAL, SEARCH)
    current, _code = world.m.review_persistence.select_current_review_report(
        world.store,
        role=ADVERSARIAL,
        expected_subject=world.subject,
        review_policy_fingerprint=POLICY_FP,
    )
    return {
        "fingerprint": world.fingerprint,
        "obligations": world.obligations(),
        "report": current,
        "verdicts": world.verdicts(),
        "sent_report": sent["report"],
    }


def test_plan_map_and_task_edits_leave_fingerprint_obligations_report_and_verdicts(
    m: SimpleNamespace, repo: Path, tmp_path: Path
) -> None:
    """Deleting or reordering the map and replacing the task list move nothing."""
    variants = {
        "with map": PLAN_WITH_MAP,
        "map deleted": PLAN_NO_MAP,
        "map reordered": PLAN_REORDERED_MAP,
        "tasks replaced": PLAN_NEW_TASKS,
    }
    observed = {
        name: _observed(_world(m, repo, tmp_path / name.replace(" ", "-"), plan))
        for name, plan in variants.items()
    }

    baseline = observed["with map"]
    assert baseline["verdicts"][SEARCH] == "contradicted"
    for name, result in observed.items():
        assert result == baseline, name


def _imported_roots(path: Path) -> set[str]:
    """Top-level module names a file imports (absolute imports only)."""
    tree = ast.parse(path.read_text("utf-8"))
    names = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    names |= {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0
    }
    return names


def test_new_modules_import_only_stdlib_and_pytest() -> None:
    """All three new test modules import only the standard library, pytest, or __future__."""
    tests_root = Path(__file__).resolve().parents[2]
    modules = (
        tests_root / "skills" / "work-loop" / "test_preservation_review.py",
        tests_root / "skills" / "work-loop" / "test_preservation_review_eval.py",
        tests_root / "pack" / "test_preservation_review_guidance.py",
    )
    allowed = set(sys.stdlib_module_names) | {"pytest", "__future__"}
    for module in modules:
        names = _imported_roots(module)
        assert names, module.name
        assert names <= allowed, (module.name, names - allowed)
