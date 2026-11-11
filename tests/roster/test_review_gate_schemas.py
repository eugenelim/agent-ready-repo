"""VI-6012: the reviewer-selection exchange validates against the amended v1 schemas.

The amendment is additive: a selection request, a selection result, and the
`human-decision` results validate, a request or result that breaks the
exactly-one rules does not, and every shape valid before the amendment still
validates. Emitted-record parity for whole runs is in
`test_execution_supervisor_records.py`. Roster-owned because it reads `contracts/`.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

_DELIVERY = Path(__file__).resolve().parents[2] / "contracts" / "delivery"
_KEY = "a" * 64


def _validator(name: str) -> Draft202012Validator:
    resources = []
    for path in _DELIVERY.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema, DRAFT202012)
        resources += [(schema["$id"], resource), (path.name, resource)]
    schema = json.loads((_DELIVERY / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=Registry().with_resources(resources))


def _errors(name: str, record: dict[str, Any]) -> list[str]:
    return [e.message for e in _validator(name).iter_errors(record)]


REQUEST = "execution-request.v1.schema.json"
RESULT = "execution-result.v1.schema.json"
_SUBJECT = {"review_subject_id": "review-subject-sha256:x"}


def _request(**fields: Any) -> dict[str, Any]:
    base = {"schema_version": 1, "request_id": "r:1", "run_id": "run-1",
            "spec": "docs/specs/example", "kind": "review-role", "stage": "reviewing",
            "review_subject_fingerprint": "subject-1", "review_subject": _SUBJECT}
    return {**base, **fields}


def _selection_request() -> dict[str, Any]:
    return _request(request_id=f"select:{_KEY[:24]}:1", candidates=["security-reviewer"],
                    selection_key=_KEY)


def _result(kind: str, **fields: Any) -> dict[str, Any]:
    return {"schema_version": 1, "request_id": "r:1", "run_id": "run-1", "kind": kind, **fields}


def _selection() -> dict[str, Any]:
    return {"selected": ["security-reviewer"],
            "omitted": [{"role": "experience-reviewer", "reason": "no reader-facing change"}],
            "authority_ref": "controller:0123456789ab"}


def _reselect() -> dict[str, Any]:
    return {"decision": "reselect-review", "authority_ref": "owner:0123456789ab",
            "selection_key": _KEY}


def _accept_risk() -> dict[str, Any]:
    return {"decision": "accept-risk", "authority_ref": "risk-owner:0123456789ab",
            "finding_ids": ["finding-1"]}


VALID = {
    "selection request": (REQUEST, _selection_request),
    "role request": (REQUEST, lambda: _request(role="adversarial-reviewer")),
    "review-not-eligible request": (REQUEST, lambda: {
        "schema_version": 1, "request_id": "decide:review-not-eligible:1", "run_id": "run-1",
        "spec": "docs/specs/example", "kind": "human-decision", "stage": "awaiting-human",
        "reason": "review-not-eligible", "question": "Which?", "selection_key": _KEY}),
    "selection result": (RESULT, lambda: _result("review-role", selection=_selection())),
    "selection result with authorization": (RESULT, lambda: _result(
        "review-role", selection={**_selection(), "authorized_by": "decide:review-not-eligible:1"})),
    "report result": (RESULT, lambda: _result("review-role", report={"report_id": "x"})),
    "reselect-review result": (RESULT, lambda: _result("human-decision", decision=_reselect())),
    "accept-risk result": (RESULT, lambda: _result("human-decision", decision=_accept_risk())),
}


@pytest.mark.parametrize("name", sorted(VALID))
def test_vi6012_the_new_shapes_validate(name: str) -> None:
    """VI-6012: each selection and decision shape validates against its canonical schema."""
    schema, build = VALID[name]
    assert _errors(schema, build()) == []


def _drop(*path: str):  # noqa: ANN202 - mutator factory
    def mutate(record: dict[str, Any]) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return mutate


def _set(path: tuple[str, ...], value: Any):  # noqa: ANN202 - mutator factory
    def mutate(record: dict[str, Any]) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return mutate


INVALID = {
    "request with role and candidates": (REQUEST, _selection_request, _set(("role",), "x")),
    "request with neither": (REQUEST, lambda: _request(role="x"), _drop("role")),
    "candidates without selection_key": (REQUEST, _selection_request, _drop("selection_key")),
    "role request without subject": (REQUEST, lambda: _request(role="x"),
                                     _drop("review_subject")),
    "result with report and selection": (RESULT, lambda: _result("review-role",
                                         selection=_selection()),
                                         _set(("report",), {"report_id": "x"})),
    "review result with neither": (RESULT, lambda: _result("review-role", selection=_selection()),
                                   _drop("selection")),
    "selection without authority_ref": (RESULT, lambda: _result("review-role",
                                        selection=_selection()), _drop("selection", "authority_ref")),
    "omission without reason": (RESULT, lambda: _result("review-role", selection=_selection()),
                                _set(("selection", "omitted"), [{"role": "x"}])),
    "selection with extra field": (RESULT, lambda: _result("review-role", selection=_selection()),
                                   _set(("selection", "note"), "x")),
    "human-decision without decision": (RESULT, lambda: _result("human-decision",
                                        decision=_reselect()), _drop("decision")),
    "reselect without selection_key": (RESULT, lambda: _result("human-decision",
                                       decision=_reselect()), _drop("decision", "selection_key")),
    "accept-risk without finding_ids": (RESULT, lambda: _result("human-decision",
                                        decision=_accept_risk()), _drop("decision", "finding_ids")),
    "accept-risk with selection_key": (RESULT, lambda: _result("human-decision",
                                       decision=_accept_risk()),
                                       _set(("decision", "selection_key"), _KEY)),
    "unknown decision": (RESULT, lambda: _result("human-decision", decision=_reselect()),
                         _set(("decision", "decision"), "waive")),
}


@pytest.mark.parametrize("name", sorted(INVALID))
def test_vi6012_a_broken_shape_is_refused(name: str) -> None:
    """VI-6012: each exactly-one and pairing rule rejects its violation."""
    schema, build, mutate = INVALID[name]
    record = copy.deepcopy(build())
    mutate(record)
    assert _errors(schema, record), name
