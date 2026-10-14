"""Emitted-record parity for the work-loop execution supervisor.

Drives the supervisor's synthetic fixture runs and validates every record they
write against its canonical schema in `contracts/`: requests, results, journal
lines, task contracts, every effect-resolution entry kind, the approval pair,
and the `.loop-run/events.jsonl` envelope. Also checks that every plan in this
repository projects. Roster-owned because it reads `contracts/` and
`docs/specs/`, both above any pack tree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop"
sys.path.insert(0, str(HARNESS_DIR))
import supervisor_harness as h  # noqa: E402

_DELIVERY = REPO_ROOT / "contracts" / "delivery"
_EVENT_SCHEMA = REPO_ROOT / "contracts" / "jsonschema" / "loop-run-event.schema.json"


def _validator(name: str) -> Draft202012Validator:
    resources = []
    for path in _DELIVERY.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema, DRAFT202012)
        resources += [(schema["$id"], resource), (path.name, resource)]
    schema = json.loads((_DELIVERY / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=Registry().with_resources(resources))


def _errors(name: str, record: dict[str, Any]) -> list[str]:
    return [error.message for error in _validator(name).iter_errors(record)]


class Recording(h.Controller):
    """Keeps every result it reports."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.reported: list[dict[str, Any]] = []

    def report(self, result: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.reported.append(result)
        return super().report(result)


@pytest.fixture(scope="module")
def runs(tmp_path_factory: pytest.TempPathFactory) -> list[dict[str, Any]]:
    out = []
    # The uninterrupted fixture run.
    root = tmp_path_factory.mktemp("full")
    repo = h.make_repo(root)
    assert h.start(repo)[0] == 0
    controller = Recording(repo, root / "effects.log")
    assert controller.drive().get("terminal")
    out.append({"repo": repo, "controller": controller})
    # A run whose effect needs a decision, a claim, and a retried dispatch.
    root = tmp_path_factory.mktemp("decision")
    repo = h.make_repo(root)
    assert h.start(repo)[0] == 0
    controller = Recording(repo, root / "effects.log")
    for _ in range(40):
        _, payload = h.run_cli(repo, "next", h.SPEC_DIR)
        controller.log.append(payload)
        request = payload["request"]
        if request["kind"] in ("external-effect", "effect-query"):
            break
        controller.report(controller.work(request))
    key = request["effect"]["operation_key"]
    _, query = h.run_cli(repo, "next", h.SPEC_DIR)
    controller.log.append(query)
    controller.report({"schema_version": 1, "request_id": query["request"]["request_id"],
                       "run_id": query["request"]["run_id"], "kind": "effect-query",
                       "effect": {"outcome": "unknowable"}})
    _, decision = h.run_cli(repo, "next", h.SPEC_DIR)
    controller.log.append(decision)
    assert decision["request"]["kind"] == "human-decision"
    code, _ = h.run_cli(repo, "resolve-effect", h.SPEC_DIR, "--operation", key, "--decision",
                        "retry-authorized", "--authority-ref", "effect-authority")
    assert code == 0
    _, query = h.run_cli(repo, "next", h.SPEC_DIR)
    controller.log.append(query)
    code, admitted = controller.report(
        {"schema_version": 1, "request_id": query["request"]["request_id"],
         "run_id": query["request"]["run_id"], "kind": "effect-query",
         "effect": {"outcome": "absent"}})
    assert code == 0
    controller.log.append({"request": admitted["admitted"]["request"]})
    out.append({"repo": repo, "controller": controller})
    return out


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_every_issued_request_validates(runs: list[dict[str, Any]]) -> None:
    kinds = set()
    for run in runs:
        for payload in run["controller"].log:
            if "request" in payload:
                kinds.add(payload["request"]["kind"])
                assert _errors("execution-request.v1.schema.json", payload["request"]) == []
    assert {"write-stub", "implement-task", "external-effect", "effect-query", "run-gates",
            "review-role", "assess-finding", "human-decision"} <= kinds


def test_every_reported_result_validates(runs: list[dict[str, Any]]) -> None:
    for run in runs:
        for result in run["controller"].reported:
            assert _errors("execution-result.v1.schema.json", result) == [], result["kind"]


def test_every_journal_line_validates(runs: list[dict[str, Any]]) -> None:
    for run in runs:
        journal = run["repo"] / h.SPEC_DIR / ".supervisor" / "journal.jsonl"
        lines = _lines(journal)
        assert lines
        for line in lines:
            assert _errors("mechanical-journal.v1.schema.json", line) == []


def test_every_task_contract_validates(runs: list[dict[str, Any]]) -> None:
    plan = (runs[0]["repo"] / h.SPEC_DIR / "plan.md").read_text(encoding="utf-8")
    for task in h.projector.project_plan(plan).tasks:
        assert _errors("task-contract.v1.schema.json", h.projector.task_contract(task)) == []


def test_every_effect_resolution_entry_validates(runs: list[dict[str, Any]]) -> None:
    entries = set()
    for run in runs:
        path = run["repo"] / h.SPEC_DIR / "delivery" / "effect-resolutions.jsonl"
        for line in _lines(path):
            entries.add(line["entry"])
            assert _errors("effect-resolution.v1.schema.json", line) == [], line["entry"]
    assert entries == {"intent", "dispatch", "receipt", "decision", "claim"}


def test_the_approval_pair_validates(runs: list[dict[str, Any]]) -> None:
    for run in runs:
        for line in _lines(run["repo"] / h.SPEC_DIR / "delivery" / "approvals.jsonl"):
            assert _errors("approval-record.v1.schema.json", line["approval"]) == []
            assert _errors("initial-plan-review.v1.schema.json",
                           line["initial_plan_review"]) == []
            assert _errors("reviewed-execution-envelope.v1.schema.json", line["envelope"]) == []


def test_every_event_line_validates(runs: list[dict[str, Any]]) -> None:
    validator = Draft202012Validator(json.loads(_EVENT_SCHEMA.read_text(encoding="utf-8")))
    for run in runs:
        for line in _lines(run["repo"] / ".loop-run" / "events.jsonl"):
            assert [e.message for e in validator.iter_errors(line)] == []


def test_every_plan_under_docs_specs_projects() -> None:
    plans = sorted((REPO_ROOT / "docs" / "specs").glob("*/plan.md"))
    assert plans
    for plan_path in plans:
        h.projector.project_plan(plan_path.read_text(encoding="utf-8"))
