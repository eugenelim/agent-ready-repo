"""Repository-owned contract tests for `loop-cohort wave-decision` JSON.

The live schema sits under `contracts/`, so this assertion cannot live in the
core pack's test tree. `tests/AGENTS.md` owns the roster placement and CI wiring.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts/jsonschema/loop-cohort-wave-decision.schema.json"
SPEC = "docs/specs/loop-cohort-wave-decision/"

REFUSAL_DETAILS = {
    "unsupported-state-schema-version": "cohort state schema is unsupported",
    "state-unreadable": "cohort state could not be read",
    "no-schedule": "cohort has no scheduled wave",
    "state-malformed": "cohort state is malformed",
    "plan-missing": "scheduled plan could not be found",
    "plan-status-illegal": "scheduled plan status is illegal",
    "plan-hash-stale": "scheduled plan hash is stale",
    "wave-index-out-of-range": "requested wave index is out of range",
    "empty-wave": "selected wave has no unfinished work",
}


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _valid_verdict() -> dict:
    return {
        "schema_version": 2,
        "payload_version": 1,
        "run_id": "11111111-1111-4111-8111-111111111111",
        "plan_hash": "0" * 64,
        "wave_index": 0,
        "wave": ["T1", "T2", "T3", "T4"],
        "wave_disposition": "partially-parallel-capable",
        "cohort": ["T1", "T4"],
        "serialized": ["T2", "T3"],
        "admission_pending": True,
        "tasks": [
            {
                "task_id": "T1",
                "touches": ["src/a/*.py"],
                "disposition": "parallel-capable",
                "reasons": [],
            },
            {
                "task_id": "T2",
                "touches": ["src/a/x.py"],
                "disposition": "sequential",
                "reasons": [
                    {
                        "code": "touches-overlap",
                        "with": "T1",
                        "globs": ["src/a/x.py", "src/a/*.py"],
                    }
                ],
            },
            {
                "task_id": "T3",
                "touches": ["db/migrations/0001.sql"],
                "disposition": "sequential",
                "reasons": [
                    {
                        "code": "danger-path-declared",
                        "glob": "db/migrations/0001.sql",
                    },
                    {"code": "override-forced-sequential", "source": "cli"},
                ],
            },
            {
                "task_id": "T4",
                "touches": ["src/d/*.py"],
                "disposition": "parallel-capable",
                "reasons": [],
            },
        ],
        "pairs": [
            {"tasks": ["T1", "T2"], "touches_relation": "overlapping"},
            {"tasks": ["T1", "T3"], "touches_relation": "disjoint"},
            {"tasks": ["T1", "T4"], "touches_relation": "disjoint"},
            {"tasks": ["T2", "T3"], "touches_relation": "disjoint"},
            {"tasks": ["T2", "T4"], "touches_relation": "disjoint"},
            {"tasks": ["T3", "T4"], "touches_relation": "disjoint"},
        ],
    }


def _assert_rejects(document: dict) -> None:
    assert list(_validator().iter_errors(document)), document


def test_wave_decision_schema_is_valid_and_points_to_declaring_spec() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["x-spec"] == [SPEC]
    assert (ROOT / SPEC / "spec.md").is_file()


def test_wave_decision_verdict_and_refusals_validate() -> None:
    validator = _validator()
    validator.validate(_valid_verdict())
    for code, detail in REFUSAL_DETAILS.items():
        validator.validate({
            "payload_version": 1,
            "refusal": code,
            "detail": detail,
        })


def test_wave_decision_schema_rejects_forbidden_contract_mutants() -> None:
    payload = _valid_verdict()
    for mutate in [
        lambda p: p.update({"extra": True}),
        lambda p: p.pop("admission_pending"),
        lambda p: p["tasks"][0].update({"disposition": "parallel"}),
        lambda p: p["pairs"][0].update({"disposition": "parallel-capable"}),
        lambda p: p["tasks"][0]["reasons"].append({"code": "unknown-code"}),
        lambda p: p["tasks"][2]["reasons"][0].update({"extra": True}),
        lambda p: p.update({"cohort": ["T1"]}),
        lambda p: p.update({"wave": [f"T{i}" for i in range(1, 66)]}),
        lambda p: p.update({
            "pairs": [
                {"tasks": ["T1", "T2"], "touches_relation": "disjoint"}
            ] * 2017
        }),
        lambda p: p["tasks"][0].update({"task_id": "BAD"}),
        lambda p: p["tasks"][0].update({"task_id": "T" + ("1" * 64)}),
        lambda p: p["tasks"][0].update({"touches": [f"src/{i}.py" for i in range(65)]}),
        lambda p: p["tasks"][0].update({"touches": ["a" * 257]}),
        lambda p: p["tasks"][1]["reasons"][0].update({"globs": ["a" * 257, "b.py"]}),
    ]:
        clone = copy.deepcopy(payload)
        mutate(clone)
        _assert_rejects(clone)

    _assert_rejects({"payload_version": 1, "refusal": "not-a-code", "detail": "x"})
    _assert_rejects({
        "payload_version": 1,
        "refusal": "state-unreadable",
        "detail": "x" * 97,
    })
    _assert_rejects({
        "payload_version": 1,
        "refusal": "state-unreadable",
        "detail": "x",
        "admission_pending": True,
    })


def test_wave_decision_schema_carries_resource_bounds() -> None:
    schema = _schema()
    task = schema["$defs"]["task"]["properties"]
    assert task["touches"]["maxItems"] == 64
    assert schema["$defs"]["glob"]["maxLength"] == 256
    assert schema["x-max-total-touches"] == 256
