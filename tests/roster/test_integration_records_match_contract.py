"""Roster test: the records ordered integration writes validate against their contracts.

Roster-owned: it reads ``contracts/`` above any pack tree. It drives the record builders in
the supervisor's integration module directly, with a stand-in for the Git helper.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
CONTRACTS = ROOT / "contracts" / "delivery"


def _load() -> object:
    alias = "roster_work_loop_supervisor_integration"
    if alias not in sys.modules:
        sys.path.insert(0, str(SCRIPTS))
        try:
            spec = importlib.util.spec_from_file_location(alias, SCRIPTS / "_supervisor_integration.py")
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            sys.modules[alias] = module
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(str(SCRIPTS))
    return sys.modules[alias]


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((CONTRACTS / name).read_text("utf-8")))


HELD = {
    "attempt_id": "att-0123456789abcdef", "run_id": "run-0123456789abcdef", "task_id": "t1",
    "source": "a" * 40, "result_tree": "b" * 40, "access_attestation_sha256": "c" * 64,
}


def test_a_result_integration_record_validates() -> None:
    integ = _load()
    ws = SimpleNamespace(git=SimpleNamespace(hardened=SimpleNamespace(git_version=(2, 56))))
    record = integ._integration_record(ws, HELD, "d" * 40, "e" * 40)  # type: ignore[attr-defined]
    _validator("result-integration.v1.schema.json").validate(record)
    assert record["algorithm"] == {"name": "git-merge-tree-write-tree", "git_version": "2.56"}


def test_a_conflict_record_validates_whole_and_truncated() -> None:
    integ = _load()
    validator = _validator("integration-conflict.v1.schema.json")
    few = json.loads(
        integ._diagnostic(None, HELD, "d" * 40, "content", ["b.txt", "a.txt"])  # type: ignore[attr-defined]
    )
    validator.validate(few)
    assert few["paths"] == ["a.txt", "b.txt"] and few["truncated"] is False
    many = [f"dir/f{n:04d}.txt" for n in range(1001)]
    cut = json.loads(integ._diagnostic(None, HELD, "d" * 40, "content", many))  # type: ignore[attr-defined]
    validator.validate(cut)
    assert cut["path_count"] == 1001 and cut["truncated"] is True and len(cut["paths"]) == 1000
