"""Eval inventory for architect-design's new modes and offers."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = PACK_ROOT / ".apm/skills/architect-design/evals"
MODE_IDS = (
    "solution-reference-mode",
    "solution-reference-app-repo-routes-to-core",
    "physical-bom-offer-and-grounding",
    "physical-bom-delta-for-change",
)


def test_solution_reference_eval_cases_have_three_assertions() -> None:
    cases = {
        str(case["id"]): case
        for case in json.loads((EVAL_DIR / "evals.json").read_text("utf-8"))["evals"]
    }
    for case_id in MODE_IDS:
        assert case_id in cases, case_id
        assert len(cases[case_id]["assertions"]) >= 3, case_id


def test_a_should_trigger_query_names_a_reference_architecture() -> None:
    queries = json.loads((EVAL_DIR / "eval_queries.json").read_text("utf-8"))
    assert any(
        item["should_trigger"] is True
        and "reference architecture" in item["query"].lower()
        for item in queries
    )


def test_a_should_trigger_query_names_a_bill_of_materials() -> None:
    queries = json.loads((EVAL_DIR / "eval_queries.json").read_text("utf-8"))
    assert any(
        item["should_trigger"] is True and "bill of materials" in item["query"].lower()
        for item in queries
    )
