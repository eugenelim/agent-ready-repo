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
                        "--review-authority-ref", "plan-reviewer:0123456789ab",
                        *h.digest_args(repo))
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
                        "--review-authority-ref", "plan-reviewer:0123456789ab",
                        *h.digest_args(repo))
    assert code == 0
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"


def _start_args(repo: Path, trust: str) -> list[str]:
    return ["start", h.SPEC_DIR, "--intent", "code", "--code-trust", trust,
            "--authority-ref", "owner:0123456789ab",
            "--review-authority-ref", "plan-reviewer:0123456789ab", *h.digest_args(repo)]


@sup.INTEGRATION
def test_a_red_task_re_approved_as_untrusted_gets_no_implement_task_and_no_report(
    tmp_path: Path,
) -> None:
    repo = h.make_repo(tmp_path)
    assert h.run_cli(repo, *_start_args(repo, "trusted"))[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    stub = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    assert stub["kind"] == "write-stub"
    assert controller.report(controller.work(stub))[0] == 0
    issued = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    assert issued["kind"] == "implement-task"
    result = controller.work(issued)
    code, out = h.run_cli(repo, *_start_args(repo, "untrusted"))
    assert code == 0, out
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    request = out["request"]
    assert code == 0 and request["kind"] == "human-decision", out
    assert request["reason"] == "untrusted-code"
    before = h.git(repo, "rev-parse", "HEAD")
    code, out = controller.report(result)
    assert code != 0 and "refusal" in out, out
    assert h.git(repo, "rev-parse", "HEAD") == before


def test_legacy_pinned_run_still_accepts_boolean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pre-proof pin retains boolean admission without minting an execution."""
    attempt = h.cli._supervisor("_supervisor_attempt.py")
    artifact = h.cli._supervisor("review-artifact.py")
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    original_line = h.admission.canonical_line

    def legacy_pin(self: Any, run_id: str, digests: dict[str, str]) -> bytes:
        """Serialize the prior release's pin schema without the proof protocol."""
        return json.dumps({"schema_version": 1, "run_id": run_id,
                           "spec": self.ws.spec_rel, "digests": digests}).encode()

    def legacy_line(record: dict[str, Any]) -> bytes:
        """Write approval records using only the previous release's fields."""
        return original_line({k: v for k, v in record.items()
                              if k not in {"review_budget", "allow_primary_checkout"}})

    # Exercise old serializers from creation; no new budget or protocol is written.
    with monkeypatch.context() as old:
        old.setattr(attempt.Attempts, "_pin_body", legacy_pin)
        old.setattr(h.admission, "canonical_line", legacy_line)
        old.setattr(h.loop, "save_review_budget", lambda *args: None)
        old.setattr(h.loop, "load_review_budget",
                    lambda ws, run_id: artifact.new_review_budget(run_id))
        assert h.start(repo)[0] == 0
    ws = h.workspace(repo)
    run_id = ws.approvals()[0]["run_id"]
    store = ws.git._store_dir(run_id)
    assert (store / "pins.json").exists()
    assert "gate_execution_protocol" not in json.loads((store / "pins.json").read_text())
    assert not (store / "review-budget.json").exists()
    assert "review_budget" not in ws.approvals()[0]
    import uuid
    review_id = str(uuid.uuid5(uuid.NAMESPACE_URL, run_id))
    records = repo / ".context" / "reviews" / review_id
    records.mkdir(parents=True)
    (records / "1-record.md").write_text(json.dumps({
        "record_version": artifact.RECORD_VERSION, "run_id": review_id, "round": 1,
        "form": "findings", "fingerprints": ["a" * 64], "review_round_count": 1,
        "review_retry_count": 1, "max_review_retries": 5, "override": False, "stdout": "",
    }))
    expected = artifact.load_review_budget(repo, review_id)
    assert expected["rounds"]["spec-stage"] == 1
    code, payload = h.run_cli(repo, "status", h.SPEC_DIR)
    assert code == 0, payload
    assert payload["run"]["review_budget"] == expected
    assert json.loads((store / "review-budget.json").read_text()) == expected
    request = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    controller = h.Controller(repo, tmp_path / "effects.log")
    result = controller.work(request)
    result["gate"].update(commands=["legacy"], exit_code=0, record={})
    path = tmp_path / "legacy-result.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    code, out = h.run_cli(repo, "report", h.SPEC_DIR, str(path))
    assert code == 0 and out["admitted"] == "implement", out
    store = h.workspace(repo).git.ensure_store(request["run_id"])
    assert not list(store.glob("exec-*.json"))


@pytest.mark.parametrize("kind", ["implement-task", "run-gates"])
def test_boolean_only_new_run_refuses_before_ref_moves(tmp_path: Path, kind: str) -> None:
    """Both report boundaries demand supervisor proof on a new run."""
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    assert h.start(repo)[0] == 0
    request = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    controller = h.Controller(repo, tmp_path / "effects.log")
    if kind == "run-gates":
        code, out = controller.report(controller.work(request))
        assert code == 0, out
        request = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    assert request["kind"] == kind
    result = controller.work(request)
    before = h.git(repo, "show-ref")
    path = tmp_path / "boolean.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    code, out = h.run_cli(repo, "report", h.SPEC_DIR, str(path))
    assert code == 1 and out["refusal"]["code"] == "gate-execution-missing", out
    assert h.git(repo, "show-ref") == before


def _proof_case(tmp_path: Path, kind: str) -> tuple[Path, dict[str, Any], dict[str, Any], Path]:
    """Prepare real observed proof at either report boundary."""
    repo = h.make_repo(tmp_path, plan=RELEASE_PLAN)
    assert h.start(repo)[0] == 0
    request = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    controller = h.Controller(repo, tmp_path / "effects.log")
    if kind == "run-gates":
        code, out = controller.report(controller.work(request))
        assert code == 0, out
        request = h.run_cli(repo, "next", h.SPEC_DIR)[1]["request"]
    assert request["kind"] == kind
    result = controller.work(request)
    code, out = h.run_cli(repo, "execute-gates", h.SPEC_DIR, "--request", request["request_id"])
    assert code == 0 and out["execution"]["outcome"] == "passed", out
    store = h.workspace(repo).git.ensure_store(request["run_id"])
    return repo, request, result, store / (out["execution"]["execution_id"] + ".completed.json")


def _raw_report(repo: Path, result: dict[str, Any], tmp_path: Path) -> tuple[int, dict[str, Any]]:
    """Submit the worker's boolean without generating proof on its behalf."""
    path = tmp_path / "raw-result.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    return h.run_cli(repo, "report", h.SPEC_DIR, str(path))


@pytest.mark.parametrize("kind", ["implement-task", "run-gates"])
@pytest.mark.parametrize("field,value", [
    ("run_id", "another-run"), ("request_id", "another-request"),
    ("issuance_id", "another-issuance"), ("task_revision", "a" * 64),
    ("candidate_tree_digest", "b" * 64), ("gate_declaration_digest", "c" * 64),
    ("schema_version", 2), ("commands", []),
])
def test_each_proof_mismatch_moves_no_refs(
    tmp_path: Path, kind: str, field: str, value: Any,
) -> None:
    """Stored proof cannot be rebound to another identity or product."""
    repo, _request, result, path = _proof_case(tmp_path, kind)
    record = json.loads(path.read_bytes())
    record[field] = value
    path.write_text(json.dumps(record), encoding="utf-8")
    before = h.git(repo, "show-ref")
    code, out = _raw_report(repo, result, tmp_path)
    assert code == 1 and out["refusal"]["code"] == "gate-execution-mismatch", out
    assert h.git(repo, "show-ref") == before


@pytest.mark.parametrize("kind", ["implement-task", "run-gates"])
@pytest.mark.parametrize("outcome", ["failed", "started", "unreadable"])
def test_nonpassing_or_unreadable_proof_is_not_admitted(
    tmp_path: Path, kind: str, outcome: str,
) -> None:
    """Failed and interrupted executions cannot make a passing receipt."""
    repo, _request, result, path = _proof_case(tmp_path, kind)
    record = json.loads(path.read_bytes())
    record["outcome"] = outcome
    if outcome == "failed":
        record["commands"][0]["exit_code"] = 1
    if outcome == "started":
        path.unlink()
    else:
        path.write_bytes(b"{" if outcome == "unreadable" else json.dumps(record).encode())
    before = h.git(repo, "show-ref")
    code, out = _raw_report(repo, result, tmp_path)
    expected = "gate-execution-mismatch" if outcome == "unreadable" else "gate-execution-missing"
    assert code == 1 and out["refusal"]["code"] == expected, out
    assert h.git(repo, "show-ref") == before


@pytest.mark.parametrize("kind", ["implement-task", "run-gates"])
def test_proof_consumption_is_atomic_and_retry_creates_no_commit(
    tmp_path: Path, kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pre-ref crash leaves proof usable; admission consumes it exactly once."""
    repo, request, result, path = _proof_case(tmp_path, kind)
    record = json.loads(path.read_bytes())
    before = h.git(repo, "show-ref")

    def crash(point: str) -> None:
        """Stop after construction, before the atomic ref transaction."""
        if point == "commit-built":
            raise h.Crash(point)

    with monkeypatch.context() as patch:
        patch.setattr(h.commit_module, "kill_point", crash)
        with pytest.raises(h.Crash):
            _raw_report(repo, result, tmp_path)
    assert h.git(repo, "show-ref") == before
    code, out = _raw_report(repo, result, tmp_path)
    assert code == 0, out
    admitted = h.git(repo, "show-ref")
    assert "Supervisor-Gate-Execution: " + record["execution_id"] in h.git(repo, "log", "-1")
    code, out = _raw_report(repo, result, tmp_path)
    assert code == 1 and "refusal" in out
    assert h.git(repo, "show-ref") == admitted
    # At the admission boundary, even rebinding the same request cannot reuse proof.
    ws = h.workspace(repo)
    state = h.loop.derive(ws)
    from types import SimpleNamespace
    ws.attempts.open = SimpleNamespace(run_id=request["run_id"], seq=int(
        record["issuance_id"].rsplit(":", 1)[1]))
    tdd = h.cli._supervisor("_supervisor_tdd.py")
    with pytest.raises(h.loop.Refusal) as caught:
        tdd.gate_proof(ws, state, request)
    assert caught.value.code in ("gate-execution-missing", "gate-execution-mismatch")


@pytest.mark.parametrize("kind", ["implement-task", "run-gates"])
@pytest.mark.parametrize("changed_source", [False, True])
def test_refused_admission_reuses_only_identical_issuance(
    tmp_path: Path, kind: str, changed_source: bool,
) -> None:
    """A failed ref compare and restored attempt preserve unused proof."""
    repo, request, result, path = _proof_case(tmp_path, kind)
    record = json.loads(path.read_bytes())
    ws = h.workspace(repo)
    product = ws.git.product_record(request["run_id"])
    assert product is not None
    source = h.git(repo, "rev-parse", "HEAD").strip()
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    child = h.git(repo, "commit-tree", tree, "-p", source, "-m", "racing writer").strip()

    def race() -> None:
        """Invalidate the builder's compare without admitting its commit."""
        h.git(repo, "update-ref", product.name, child)

    h.commit_module.set_update_hook(race)
    try:
        code, out = _raw_report(repo, result, tmp_path)
    finally:
        h.commit_module.set_update_hook(None)
    assert code == 1 and out["refusal"]["code"] == "integration-conflict", out
    assert h.git(repo, "rev-parse", "HEAD").strip() == source
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 1 and out["refusal"]["code"] == "attempt-residue", out
    h.git(repo, "update-ref", product.name, source)
    code, out = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0 and out["request"]["request_id"] == request["request_id"], out
    assert h.workspace(repo).attempts._load(request["run_id"], path.parent).seq > int(
        record["issuance_id"].rsplit(":", 1)[1])
    if changed_source:
        original = path.parent / "attempts" / (record["issuance_id"].rsplit(":", 1)[1] + ".json")
        saved = json.loads(original.read_bytes())
        saved["head"] = child
        original.write_text(json.dumps(saved), encoding="utf-8")
        before = h.git(repo, "show-ref")
        code, out = _raw_report(repo, result, tmp_path)
        assert code == 1 and out["refusal"]["code"] == "gate-execution-mismatch", out
        assert h.git(repo, "show-ref") == before
        return
    code, out = _raw_report(repo, result, tmp_path)
    assert code == 0, out
    assert "Supervisor-Gate-Execution: " + record["execution_id"] in h.git(repo, "log", "-1")
    admitted = h.git(repo, "show-ref")
    assert _raw_report(repo, result, tmp_path)[0] == 1
    assert h.git(repo, "show-ref") == admitted


@pytest.mark.parametrize("kind", ["implement-task", "run-gates"])
@pytest.mark.parametrize("nested", [False, True], ids=["top-level", "gate"])
@pytest.mark.parametrize("claim,value", [
    ("commands", ["unapproved"]), ("exit_code", 0),
    ("record", {"outcome": "passed"}), ("other", {"passed": True}),
])
def test_new_protocol_refuses_worker_gate_claims(
    tmp_path: Path, kind: str, nested: bool, claim: str, value: Any,
) -> None:
    """Even matching supervisor proof cannot authorize worker-supplied gate facts."""
    repo, _request, result, _path = _proof_case(tmp_path, kind)
    target = result["gate"] if nested else result
    target[claim] = value
    before = h.git(repo, "show-ref")
    code, out = _raw_report(repo, result, tmp_path)
    assert code == 1 and out["refusal"]["code"] == "result-fact-refused", out
    assert h.git(repo, "show-ref") == before


@pytest.mark.parametrize("tamper", ["binding", "manifest"])
def test_execution_refuses_manifest_mode_substitution(tmp_path: Path, tamper: str) -> None:
    """An unchanged product digest cannot hide a substituted executable bit."""
    repo, request, result, path = _proof_case(tmp_path, "implement-task")
    record = json.loads(path.read_bytes())
    store = path.parent
    binding = store / ("candidate-" + record["execution_id"] + ".json")
    manifest = json.loads(binding.read_bytes())
    ws = h.workspace(repo)
    entries = ws.git.tree_modes(manifest["tree"])
    mode, oid = entries["release.txt"]
    with ws.git._private_index(manifest["tree"]) as env:
        ws.git.run("update-index", "--cacheinfo", "100755," + oid + ",release.txt", env=env)
        tree = ws.git.text("write-tree", env=env).strip()
    assert mode == "100644" and ws.git.product_tree(tree) == record["candidate_tree_digest"]
    manifest["tree"] = tree
    target = binding if tamper == "binding" else store / (
        "candidate-" + manifest["mode_tree_digest"] + ".json")
    target.write_text(json.dumps(manifest))
    before = h.git(repo, "show-ref")
    code, out = _raw_report(repo, result, tmp_path)
    assert code == 1 and out["refusal"]["code"] == "gate-execution-mismatch", out
    assert h.git(repo, "show-ref") == before
