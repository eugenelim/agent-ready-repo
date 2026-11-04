"""Roster test: proof-by-run assessments fit finding-assessment.v1.

Builds a ``supported`` and an ``unsupported-opinion`` record with the shipped
predicate and validates each against the canonical schema, which a pack test
cannot read.

Spec: docs/specs/proof-by-run-evidence/spec.md
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "packs/core/.apm/skills/work-loop/scripts"
CONTRACTS = ROOT / "contracts/delivery"
COMMIT = "a" * 40


def _load_assessment() -> ModuleType:
    """Load the shipped assessment module under a name unique to this test."""
    name = "roster_proof_by_run_contract_fit_review_assessment"
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / "_review_assessment.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _validator() -> Draft202012Validator:
    """Return a validator for finding-assessment.v1 that resolves its sibling schemas."""
    resources = []
    for path in CONTRACTS.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema)
        resources += [(schema["$id"], resource), (path.name, resource)]
    registry = Registry().with_resources(resources)
    schema = json.loads((CONTRACTS / "finding-assessment.v1.schema.json").read_text("utf-8"))
    return Draft202012Validator(schema, registry=registry)


def _envelope() -> dict[str, Any]:
    """Return a run envelope bound to the test commit."""
    digest = hashlib.sha256(b"x").hexdigest()
    return {
        "command_sha256": digest,
        "exit_status": 1,
        "stderr_sha256": digest,
        "stdout_sha256": digest,
        "subject_commit": COMMIT,
    }


@pytest.mark.parametrize(
    ("observed", "expected"), [("fail", "supported"), ("pass", "unsupported-opinion")]
)
def test_proof_by_run_records_fit_finding_assessment_schema(observed: str, expected: str) -> None:
    """Each predicate outcome is a schema-valid finding-assessment.v1 record."""
    record = _load_assessment().proof_by_run_assessment(
        assessment_id="assessment-1",
        report_id="report-1",
        finding_id="finding-1",
        review_subject_fingerprint="review-subject-fp",
        observed=observed,
        envelope=_envelope(),
        current_subject_commit=COMMIT,
        judgment_authority="controller",
    )
    assert record["assessment"] == expected
    errors = sorted(_validator().iter_errors(record), key=str)
    assert errors == []
