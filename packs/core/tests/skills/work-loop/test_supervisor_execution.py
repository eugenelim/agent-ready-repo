"""Approved gate declarations and closed supervisor execution records."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
SCRIPT_PATHS = {
    "projector": SCRIPTS / "_supervisor_projector.py",
    "execution": SCRIPTS / "_supervisor_execution.py",
    "policy": SCRIPTS / "_policy_import.py",
}


def _load(name: str) -> ModuleType:
    """Load each script under a pack- and skill-specific module name."""
    alias = "core_work_loop_execution_test_" + name
    spec = importlib.util.spec_from_file_location(alias, SCRIPT_PATHS[name])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


proj = _load("projector")
policy = _load("policy")


def _commands() -> list[dict]:
    """Commands retain argument boundaries, order, working directory and expected exit."""
    return [
        {"argv": ["python3", "-m", "pytest", "tests/a test.py"], "cwd": ".", "expected_exit": 0},
        {"argv": ["make", "check"], "cwd": "src", "expected_exit": 0},
    ]


def _spec(commands: object) -> str:
    """Place a declaration inside the approved Agent Rules section."""
    return "# Example\n\n## Agent Rules\n\n```gate-declaration\n" + json.dumps(commands) + "\n```\n"


def test_declaration_preserves_order_and_argument_boundaries() -> None:
    assert proj.gate_declaration(_spec(_commands())) == _commands()


def test_declaration_retains_empty_arguments_and_literal_shell_characters() -> None:
    commands = [{"argv": ["echo", "", "$(ignored); *"], "cwd": ".", "expected_exit": 0}]
    text = _spec(commands).replace("```", "~~~~").replace("\n", "\r\n")
    assert proj.gate_declaration(text) == commands


def test_declaration_edit_changes_existing_approval_digest(tmp_path: Path) -> None:
    path = tmp_path / "spec.md"
    text = _spec(_commands())
    path.write_text(text, encoding="utf-8")
    before = policy.compute_spec_digest(path)
    refs = proj.envelope_references(text, read_record=lambda p: "", list_dir=lambda p: []).refs
    changed = text.replace('"check"', '"lint"')
    path.write_text(changed, encoding="utf-8")
    assert policy.compute_spec_digest(path) != before
    assert proj.envelope_references(
        changed, read_record=lambda p: "", list_dir=lambda p: []
    ).refs["spec_policy"] != refs["spec_policy"]


@pytest.mark.parametrize("text", [
    "## Outcome\n```gate-declaration\n[]\n```\n",
    "## Agent Rules\nNo commands.\n",
    _spec(_commands()) + _spec(_commands()),
    _spec(_commands()) + "\n```gate-declaration\n[]\n```\n",
    "## Agent Rules\n```gate-declaration\n[\n",
    "## Agent Rules\n```gate-declaration\nnot json\n```\n",
    "## Agent Rules\n````markdown\n```gate-declaration\n[]\n```\n````\n",
    _spec([]),
    _spec([{"argv": "make check", "cwd": ".", "expected_exit": 0}]),
    _spec([{"argv": [], "cwd": ".", "expected_exit": 0}]),
    _spec([{"argv": ["make"], "cwd": "../outside", "expected_exit": 0}]),
    _spec([{"argv": ["make"], "cwd": "/outside", "expected_exit": 0}]),
    _spec([{"argv": ["make"], "cwd": ".", "expected_exit": True}]),
    _spec([{"argv": ["make"], "cwd": ".", "expected_exit": 0, "shell": True}]),
])
def test_invalid_or_ambiguous_declaration_refuses(text: str) -> None:
    with pytest.raises(proj.ProjectionRefused):
        proj.gate_declaration(text)


def _record() -> dict:
    """A completed execution binds all identities and records each observed command."""
    return {
        "schema_version": 1,
        "type": "gate-execution.v1",
        "execution_id": "exec-example",
        "run_id": "run-example",
        "request_id": "req-example",
        "issuance_id": "issue-example",
        "task_revision": "a" * 64,
        "candidate_tree_digest": "b" * 64,
        "gate_declaration_digest": "c" * 64,
        "commands": [{
            **_commands()[0], "exit_code": 0, "timed_out": False,
            "stdout_digest": "d" * 64, "stderr_digest": "e" * 64,
        }],
        "outcome": "passed",
    }


def test_execution_record_round_trips() -> None:
    execution = _load("execution")
    record = _record()
    assert execution.decode_execution(execution.encode_execution(record)) == record


@pytest.mark.parametrize("outcome", ["started", "failed"])
def test_nonpassing_and_run_wide_records_round_trip(outcome: str) -> None:
    execution = _load("execution")
    record = {**_record(), "outcome": outcome, "task_revision": None}
    if outcome == "started":
        record["commands"] = []
    else:
        record["commands"][0].update(exit_code=None, timed_out=True)
    assert execution.decode_execution(execution.encode_execution(record)) == record


@pytest.mark.parametrize("field", list(_record()))
def test_each_required_execution_field_refuses_when_missing(field: str) -> None:
    execution = _load("execution")
    record = _record()
    del record[field]
    with pytest.raises(execution.ExecutionRefused):
        execution.encode_execution(record)


@pytest.mark.parametrize("mutation", ["version", "missing", "extra", "nested-extra",
    "nested-missing", "boolean-version", "bad-argv", "bad-digest", "timeout-pass",
    "nonzero-pass", "empty-pass", "bad-outcome"])
def test_invalid_execution_record_refuses(mutation: str) -> None:
    execution = _load("execution")
    record = copy.deepcopy(_record())
    if mutation == "version":
        record["schema_version"] = 2
    elif mutation == "missing":
        del record["request_id"]
    elif mutation == "extra":
        record["proof"] = True
    elif mutation == "nested-extra":
        record["commands"][0]["shell"] = True
    elif mutation == "nested-missing":
        del record["commands"][0]["exit_code"]
    elif mutation == "boolean-version":
        record["schema_version"] = True
    elif mutation == "bad-argv":
        record["commands"][0]["argv"] = "python3"
    elif mutation == "bad-digest":
        record["candidate_tree_digest"] = "invalid"
    elif mutation == "timeout-pass":
        record["commands"][0]["timed_out"] = True
    elif mutation == "nonzero-pass":
        record["commands"][0]["exit_code"] = 1
    elif mutation == "empty-pass":
        record["commands"] = []
    else:
        record["outcome"] = "unknown"
    with pytest.raises(execution.ExecutionRefused):
        execution.decode_execution(json.dumps(record).encode())


@pytest.mark.parametrize("data", [b"{", b"[]", b"\xff", b'{"schema_version":1,"schema_version":1}'])
def test_unreadable_execution_refuses(data: bytes) -> None:
    execution = _load("execution")
    with pytest.raises(execution.ExecutionRefused):
        execution.decode_execution(data)
