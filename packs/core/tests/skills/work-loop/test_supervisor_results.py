"""Results assert only their kind's facts, and untrusted code runs no task (T5).

VI-5040 (AC-0018): one fixture per Result acceptance row. VI-5042 (AC-0017):
untrusted trust issues no ``implement-task`` request.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
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

loop = h.loop


def _result(kind: str, **facts: Any) -> dict[str, Any]:
    return {"schema_version": 1, "request_id": "r-1", "run_id": "run-0123456789abcdef",
            "kind": kind, **facts}


# ── VI-5040: the Result acceptance table ────────────────────────────────────

ADMITTED = [
    ("implement-task", {"gate": {"passed": True}}),
    ("write-stub", {}),
    ("review-role", {"report": {}}),
    ("review-role", {"selection": {}}),
    ("assess-finding", {"assessment": {}}),
    ("run-gates", {"gate": {"passed": True}, "criteria": []}),
    ("external-effect", {"effect": {"outcome": "completed"}}),
    ("effect-query", {"effect": {"outcome": "absent"}}),
    ("regenerate", {}),
    ("human-decision", {"decision": {"decision": "accept-risk", "authority_ref": "x"}}),
]

REFUSED = [
    ("implement-task", {"gate": {"passed": True}, "criteria": []}),
    ("implement-task", {"gate": {"passed": False}, "report": {}}),
    ("implement-task", {"gate": {"passed": True}, "effect": {"outcome": "completed"}}),
    ("write-stub", {"gate": {"passed": True}}),
    ("write-stub", {"assessment": {}}),
    ("review-role", {"gate": {"passed": True}}),
    ("review-role", {"report": {}, "effect": {"outcome": "present"}}),
    ("review-role", {"report": {}, "selection": {}}),
    ("assess-finding", {"report": {}}),
    ("assess-finding", {"assessment": {}, "criteria": []}),
    ("run-gates", {"gate": {"passed": True}, "criteria": [], "report": {}}),
    ("run-gates", {"decision": {}}),
    ("external-effect", {"effect": {"outcome": "completed"}, "gate": {"passed": True}}),
    ("effect-query", {"selection": {}}),
    ("regenerate", {"digests": {"scripts/x.py": "0" * 64}}),
    ("regenerate", {"gate": {"passed": True}}),
    ("human-decision", {"decision": {}, "report": {}}),
    ("human-decision", {"assessment": {}}),
]


@pytest.mark.parametrize(("kind", "facts"), ADMITTED, ids=lambda v: v if isinstance(v, str) else "")
def test_a_row_admits_the_facts_it_lists(kind: str, facts: dict[str, Any]) -> None:
    loop.accept_facts(_result(kind, **facts))


@pytest.mark.parametrize(("kind", "facts"), REFUSED, ids=lambda v: v if isinstance(v, str) else "")
def test_a_row_refuses_everything_else(kind: str, facts: dict[str, Any]) -> None:
    with pytest.raises(loop.Refusal) as caught:
        loop.accept_facts(_result(kind, **facts))
    assert caught.value.code == "result-fact-refused"
    assert kind in caught.value.detail


def test_an_unknown_kind_asserts_nothing() -> None:
    with pytest.raises(loop.Refusal) as caught:
        loop.accept_facts(_result("deploy"))
    assert caught.value.code == "result-kind-refused"


@sup.INTEGRATION
def test_report_refuses_before_any_write(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    code, _ = h.run_cli(repo, "start", h.SPEC_DIR, "--intent", "code", "--code-trust", "trusted",
                        "--authority-ref", "owner:0123456789ab",
                        "--review-authority-ref", "plan-reviewer:0123456789ab")
    assert code == 0
    _, issued = h.run_cli(repo, "next", h.SPEC_DIR)
    request = issued["request"]
    before = h.git(repo, "rev-parse", "HEAD")
    path = tmp_path / "result.json"
    path.write_text(json.dumps({
        "schema_version": 1, "request_id": request["request_id"], "run_id": request["run_id"],
        "kind": "deploy",
    }), encoding="utf-8")
    code, payload = h.run_cli(repo, "report", h.SPEC_DIR, str(path))
    assert code != 0
    assert json.dumps(payload).count("result-kind-refused") >= 1
    assert h.git(repo, "rev-parse", "HEAD") == before


# ── VI-5042: untrusted code is not run for a task either ────────────────────

RELEASE_PLAN = sup.plan(
    sup.task(
        "T1",
        "Release note is written",
        touches="`release.txt`",
        mode="goal-based",
        tests="no stub (goal-based)",
        done="release.txt says ready",
    )
)


@sup.INTEGRATION
def test_untrusted_trust_issues_no_implement_task_for_a_task_without_stubs(
    tmp_path: Path,
) -> None:
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    code, _ = h.run_cli(repo, "start", h.SPEC_DIR, "--intent", "code", "--code-trust",
                        "untrusted", "--authority-ref", "owner:0123456789ab",
                        "--review-authority-ref", "plan-reviewer:0123456789ab")
    assert code == 0
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"


def _start_args(trust: str) -> list[str]:
    return ["start", h.SPEC_DIR, "--intent", "code", "--code-trust", trust,
            "--authority-ref", "owner:0123456789ab",
            "--review-authority-ref", "plan-reviewer:0123456789ab"]


@sup.INTEGRATION
def test_a_red_task_re_approved_as_untrusted_gets_no_implement_task_and_no_report(
    tmp_path: Path,
) -> None:
    repo = h.make_repo(tmp_path)
    assert h.run_cli(repo, *_start_args("trusted"))[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    stub = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    assert stub["kind"] == "write-stub"
    assert controller.report(controller.work(stub))[0] == 0
    issued = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    assert issued["kind"] == "implement-task"
    result = controller.work(issued)
    code, out = h.run_cli(repo, *_start_args("untrusted"))
    assert code == 0, out
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"
    before = h.git(repo, "rev-parse", "HEAD")
    code, out = controller.report(result)
    assert code != 0 and "refusal" in out, out
    assert h.git(repo, "rev-parse", "HEAD") == before
