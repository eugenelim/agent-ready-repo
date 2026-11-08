"""Emitted-record parity for the concurrent path.

Runs the permutation corpus's schedules (each once under each concurrent mode, in its first
completion order) into temporary stores, collects every record the runs write, and validates
each against its schema in `contracts/delivery/`. It fails when any of the eight kinds the
contract names is missing, so a producer that stops writing one cannot go unnoticed. The
corpus itself lives in the Core pack's tests; this suite is roster-owned because it reads
`contracts/`, which sits above any pack tree. The harness skips unless
`WORK_SUPERVISOR_INTEGRATION=1`, and the Gate A-supervisor lane sets it.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop"
_DELIVERY = REPO_ROOT / "contracts" / "delivery"

KINDS = (
    "containment-attestation.v1",
    "access-attestation.v1",
    "launcher-message.v1",
    "execution-result.v1",
    "result-integration.v1",
    "integration-conflict.v1",
    "execution-request.v1",
    "task-contract.v1",
)


def _helper(name: str) -> ModuleType:
    """Load a shared work-loop test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, HARNESS_DIR / f"{name}.py")
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


pc = _helper("permutation_corpus")
pytestmark = pc.sup.INTEGRATION


@functools.cache
def _validator(name: str) -> Draft202012Validator:
    resources = []
    for path in _DELIVERY.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema, DRAFT202012)
        resources += [(schema["$id"], resource), (path.name, resource)]
    schema = json.loads((_DELIVERY / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=Registry().with_resources(resources))


def _errors(kind: str, record: dict[str, Any]) -> list[str]:
    return [error.message for error in _validator(kind).iter_errors(record)]


def _lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _collect(run: Any, schedule: Any, mode: str) -> list[tuple[str, dict[str, Any]]]:
    """Every record one corpus run wrote, as ``(schema kind, record)``."""
    found: list[tuple[str, dict[str, Any]]] = []
    found += [("execution-request.v1", r) for r in run.controller.requests]
    found += [("execution-result.v1", r) for r in run.controller.reported]
    found += [("execution-result.v1", r) for r in run.records("results")]
    found += [("result-integration.v1", r) for r in run.records("integrations")]
    found += [("integration-conflict.v1", r) for r in run.records("conflicts")]
    found += [("mechanical-journal.v1", line) for line in run.journal()]
    for item in pc.plan_projection(schedule, mode):
        found.append(("task-contract.v1", item))
    # What the fixture launcher received and sent: every line is a launcher message, and the
    # containment and access envelopes carry the two attestations.
    for name in ("recv.log", "sent.log"):
        for message in _lines(run.env.log / name):
            found.append(("launcher-message.v1", message))
            if message.get("type") == "containment":
                found.append(("containment-attestation.v1", message["attestation"]))
            if message.get("type") == "access":
                found.append(("access-attestation.v1", message["attestation"]))
    return found


@pytest.fixture(scope="module")
def records(tmp_path_factory: pytest.TempPathFactory) -> list[tuple[str, dict[str, Any]]]:
    root = tmp_path_factory.mktemp("records")
    isolation = pc.Isolation(root)
    out: list[tuple[str, dict[str, Any]]] = []
    with pytest.MonkeyPatch.context() as monkeypatch:
        isolation.apply(monkeypatch)
        isolation.assert_clean()
        for schedule in pc.SCHEDULES:
            for mode in pc.MODES:
                order = pc.orders(schedule, mode)[0]
                run = pc.run_schedule(
                    schedule, mode, order, root / f"{schedule.name}-{mode}", monkeypatch, isolation
                )
                out += _collect(run, schedule, mode)
    return out


def test_every_corpus_record_validates(records: list[tuple[str, dict[str, Any]]]) -> None:
    assert records
    for kind, record in records:
        assert _errors(kind, record) == [], (kind, record)


def test_the_corpus_writes_at_least_one_of_each_kind(
    records: list[tuple[str, dict[str, Any]]],
) -> None:
    seen = {kind for kind, _record in records}
    assert [kind for kind in KINDS if kind not in seen] == []


def test_the_concurrent_journal_lines_carry_the_extended_fields(
    records: list[tuple[str, dict[str, Any]]],
) -> None:
    lines = [r for kind, r in records if kind == "mechanical-journal.v1"]
    assert any(line.get("outcome") == "landed" for line in lines)
    assert any(line.get("outcome") == "conflict" and line.get("reprojected") for line in lines)
    assert any(line.get("floor_reason") for line in lines)
