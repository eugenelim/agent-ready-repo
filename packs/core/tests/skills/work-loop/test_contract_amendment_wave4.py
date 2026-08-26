"""Wave 4 full-mode contract-amendment state contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "work-loop"
# Literal, pack-confined subject paths: the boundary lint resolves each script
# statically, which a name computed from a parameter would defeat.
ENGINE_PATH = SKILL_ROOT / "scripts" / "loop-engine.py"
COHORT_PATH = SKILL_ROOT / "scripts" / "loop-cohort.py"


def _load(name: str):
    path = ENGINE_PATH if name == "loop-engine.py" else COHORT_PATH
    assert path.name == name, f"unknown subject script {name!r}"
    module_name = f"wave4_{name.replace('-', '_').replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _state() -> dict:
    return {
        "schema_version": 1,
        "run_id": "run-current",
        "plan_review_status": "approved",
        "approved_spec_hash": "a" * 64,
        "approved_plan_hash": "b" * 64,
        "plan_hash": "b" * 64,
        "schedule_waves": [["T1"], ["T2"], ["T3"]],
        "current_wave_index": 2,
        "review_round_count": 1,
        "review_retry_count": 1,
        "finding_fingerprints": ["e" * 64],
    }


def _hashes() -> dict[str, str]:
    return {"T1": "c" * 64, "T2": "d" * 64}


def _evidence() -> dict[str, list[str]]:
    return {"T1": ["review:round-1"], "T2": ["gates:t2"]}


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _regular_file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _integration_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[object, object, Path, object, dict[str, list[str]]]:
    """Create a real two-file CODE-IMPLEMENTATION amendment baseline."""
    engine = _load("loop-engine.py")
    cohort = _load("loop-cohort.py")
    spec_dir = tmp_path / "contract-amendment-integration"
    spec_dir.mkdir()
    (tmp_path / ".loop-run").mkdir()
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Implementing\n\n"
        "## Acceptance criteria\n\n- [ ] AC1\n",
        encoding="utf-8",
    )
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n"
        "## T1: completed baseline\n\n**Depends on:** none\n\nproof one\n\n"
        "## T2: remaining work\n\n**Depends on:** T1\n\nbuild two\n",
        encoding="utf-8",
    )
    run_id = "integration-run"
    spec_hash = cohort.sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = cohort.sha256_canonical_contract(spec_dir / "plan.md")
    _write_json(
        spec_dir / "state.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "feature": spec_dir.name,
            "plan_review_status": "approved",
            "approved_spec_hash": spec_hash,
            "approved_plan_hash": plan_hash,
            "plan_hash": plan_hash,
            "schedule_waves": [["T1"], ["T2"]],
            "current_wave_index": 1,
            "completed_task_ids": [],
            "completed_task_section_hashes": {},
            "completed_task_evidence": {},
            "amendment_history": [],
            "amendment_pending": None,
            "implementation_retry_count": 1,
            "review_round_count": 2,
            "review_retry_count": 0,
            "finding_fingerprints": [],
            "previous_finding_fingerprints": [],
        },
    )
    _write_json(
        spec_dir / "engine-state.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "feature": spec_dir.name,
            "mode": "code",
            "state": "CODE-IMPLEMENTATION",
            "last_event": "plan-locked",
            "last_event_context": None,
            "gate_question": None,
            "transition_sequence": 8,
            "last_transition_at": "2026-08-25T00:00:00Z",
        },
    )
    monkeypatch.setattr(engine, "_get_repo_root", lambda: tmp_path)
    engine._cohort_mutator_module = cohort
    evidence = {"T1": ["gates:t1"]}
    args = engine.build_parser().parse_args(
        [
            "transition",
            str(spec_dir),
            "contract-amendment",
            "--owner-authority-ref",
            "approval:scope-owner",
            "--reason-ref",
            "follow-on:owned-record",
            "--completed-evidence-ref",
            "T1=gates:t1",
        ]
    )
    return engine, cohort, spec_dir, args, evidence


def test_contract_amendment_reopens_plan_without_erasing_completed_work() -> None:
    engine = _load("loop-engine.py")
    cohort = _load("loop-cohort.py")

    amended = cohort.begin_contract_amendment(
        _state(),
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-2",
    )

    assert engine._CODE_TRANSITIONS[
        ("CODE-IMPLEMENTATION", "contract-amendment")
    ] == "SPEC-PLAN-DRAFTING"
    assert amended["plan_review_status"] == "pending"
    assert amended["approved_spec_hash"] is None
    assert amended["approved_plan_hash"] is None
    assert amended["plan_hash"] is None
    assert amended["schedule_waves"] == []
    assert amended["completed_task_ids"] == ["T1", "T2"]
    assert amended["completed_task_section_hashes"] == _hashes()
    assert amended["completed_task_evidence"] == _evidence()
    assert amended["review_round_count"] == 1
    assert amended["review_retry_count"] == 1
    assert amended["finding_fingerprints"] == ["e" * 64]
    assert amended["amendment_history"][-1]["approved_spec_hash"] == "a" * 64
    assert amended["amendment_history"][-1]["approved_plan_hash"] == "b" * 64


def test_contract_amendment_event_is_legal_only_from_code_implementation() -> None:
    engine = _load("loop-engine.py")

    amendment_edges = {
        key: value
        for key, value in engine._CODE_TRANSITIONS.items()
        if key[1] == "contract-amendment"
    }
    assert amendment_edges == {
        ("CODE-IMPLEMENTATION", "contract-amendment"): "SPEC-PLAN-DRAFTING"
    }
    assert all(
        event != "contract-amendment"
        for _state, event in engine._SPEC_PLAN_TRANSITIONS
    )


@pytest.mark.parametrize(
    ("override", "kwargs", "match"),
    [
        ({}, {"expected_run_id": "stale-run"}, "run_id"),
        ({}, {"owner_authority_ref": ""}, "owner_authority_ref"),
        ({}, {"reason_ref": ""}, "reason_ref"),
        ({}, {"completed_task_evidence": {}}, "completed_task_evidence"),
        ({"plan_review_status": "pending"}, {}, "approved plan"),
        ({"current_wave_index": 0}, {}, "completed task"),
    ],
)
def test_contract_amendment_refuses_invalid_authority_or_state_without_mutation(
    override: dict, kwargs: dict, match: str
) -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    state.update(override)
    before = copy.deepcopy(state)
    call = {
        "expected_run_id": "run-current",
        "owner_authority_ref": "approval:scope-owner",
        "reason_ref": "follow-on:owned-record",
        "completed_task_section_hashes": _hashes(),
        "completed_task_evidence": _evidence(),
        "amendment_id": "amendment-2",
        **kwargs,
    }

    with pytest.raises(ValueError, match=match):
        cohort.begin_contract_amendment(state, **call)

    assert state == before


def test_engine_cli_requires_completed_evidence_before_any_state_read() -> None:
    engine = _load("loop-engine.py")
    args = engine.build_parser().parse_args(
        [
            "transition",
            "unused-spec",
            "contract-amendment",
            "--owner-authority-ref",
            "approval:scope-owner",
            "--reason-ref",
            "follow-on:owned-record",
        ]
    )

    assert engine.cmd_transition.__wrapped__(args) == 1


def test_engine_finishes_cohort_first_contract_amendment_crash_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, cohort, spec_dir, args, evidence = _integration_fixture(
        tmp_path, monkeypatch
    )
    amendment_id = engine._contract_amendment_id(
        "integration-run",
        9,
        "approval:scope-owner",
        "follow-on:owned-record",
        evidence,
    )
    cohort.apply_contract_amendment(
        spec_dir,
        expected_run_id="integration-run",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_evidence=evidence,
        amendment_id=amendment_id,
    )

    assert engine.cmd_transition(args) == 0

    engine_state = json.loads((spec_dir / "engine-state.json").read_text())
    cohort_state = json.loads((spec_dir / "state.json").read_text())
    assert engine_state["state"] == "SPEC-PLAN-DRAFTING"
    assert engine_state["transition_sequence"] == 9
    assert engine_state["last_event_context"]["completed_task_evidence"] == evidence
    assert cohort_state["completed_task_evidence"] == evidence
    assert len(cohort_state["amendment_history"]) == 1


def test_engine_finishes_engine_first_contract_amendment_crash_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, _cohort, spec_dir, args, evidence = _integration_fixture(
        tmp_path, monkeypatch
    )
    amendment_id = engine._contract_amendment_id(
        "integration-run",
        9,
        "approval:scope-owner",
        "follow-on:owned-record",
        evidence,
    )
    engine_first = json.loads((spec_dir / "engine-state.json").read_text())
    engine_first.update(
        {
            "state": "SPEC-PLAN-DRAFTING",
            "last_event": "contract-amendment",
            "last_event_context": {
                "amendment_id": amendment_id,
                "owner_authority_ref": "approval:scope-owner",
                "reason_ref": "follow-on:owned-record",
                "completed_task_evidence": evidence,
            },
            "transition_sequence": 9,
        }
    )
    _write_json(spec_dir / "engine-state.json", engine_first)

    assert engine.cmd_transition(args) == 0

    assert json.loads((spec_dir / "engine-state.json").read_text()) == engine_first
    cohort_state = json.loads((spec_dir / "state.json").read_text())
    assert cohort_state["completed_task_evidence"] == evidence
    assert cohort_state["amendment_pending"]["amendment_id"] == amendment_id
    assert len(cohort_state["amendment_history"]) == 1


def test_public_transition_refusal_leaves_both_states_and_outbox_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, _cohort, spec_dir, _args, _evidence_map = _integration_fixture(
        tmp_path, monkeypatch
    )
    args = engine.build_parser().parse_args(
        [
            "transition",
            str(spec_dir),
            "contract-amendment",
            "--owner-authority-ref",
            "approval:scope-owner",
            "--reason-ref",
            "follow-on:owned-record",
            "--completed-evidence-ref",
            "T2=gates:not-completed",
        ]
    )
    engine_before = (spec_dir / "engine-state.json").read_bytes()
    cohort_before = (spec_dir / "state.json").read_bytes()
    outbox_before = _regular_file_bytes(tmp_path / ".loop-run")

    assert engine.cmd_transition(args) == 1

    assert (spec_dir / "engine-state.json").read_bytes() == engine_before
    assert (spec_dir / "state.json").read_bytes() == cohort_before
    assert _regular_file_bytes(tmp_path / ".loop-run") == outbox_before


def test_evidence_map_rejects_non_string_references_without_coercion() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    before = copy.deepcopy(state)

    with pytest.raises(ValueError, match="reference must be a string"):
        cohort.begin_contract_amendment(
            state,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence={"T1": [123], "T2": ["gates:t2"]},
            amendment_id="amendment-2",
        )

    assert state == before


def test_contract_amendment_replay_is_idempotent() -> None:
    cohort = _load("loop-cohort.py")
    first = cohort.begin_contract_amendment(
        _state(),
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-2",
    )
    replay = cohort.begin_contract_amendment(
        first,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-2",
    )

    assert replay == first
    assert len(replay["amendment_history"]) == 1

    with pytest.raises(ValueError, match="replay facts"):
        cohort.begin_contract_amendment(
            first,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence={
                "T1": ["review:round-1"],
                "T2": ["different:evidence"],
            },
            amendment_id="amendment-2",
        )

    tampered = copy.deepcopy(first)
    tampered["completed_task_section_hashes"]["T2"] = "9" * 64
    with pytest.raises(ValueError, match="replay facts"):
        cohort.begin_contract_amendment(
            tampered,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=tampered["completed_task_section_hashes"],
            completed_task_evidence=_evidence(),
            amendment_id="amendment-2",
        )


def test_cohort_first_crash_window_is_classified_without_mutation() -> None:
    cohort = _load("loop-cohort.py")
    pending = {
        "amendment_id": "amendment-2",
        "owner_authority_ref": "approval:scope-owner",
        "reason_ref": "follow-on:owned-record",
        "completed_task_evidence": _evidence(),
    }
    snapshot = {
        "amendment_id": "amendment-2",
        "owner_authority_ref": "approval:scope-owner",
        "reason_ref": "follow-on:owned-record",
        "completed_task_ids": ["T1", "T2"],
        "completed_task_section_hashes": _hashes(),
        "completed_task_evidence": _evidence(),
    }
    applied = {
        "amendment_pending": pending,
        "amendment_history": [snapshot],
        "completed_task_ids": ["T1", "T2"],
        "completed_task_section_hashes": _hashes(),
        "completed_task_evidence": _evidence(),
    }
    states = iter(
        [
            applied,
            {**applied, "amendment_pending": {**pending, "reason_ref": "other"}},
            {
                **applied,
                "amendment_pending": {**pending, "amendment_id": "tampered"},
            },
            {
                **applied,
                "amendment_history": [
                    {**snapshot, "owner_authority_ref": "approval:tampered"}
                ],
            },
            {},
        ]
    )
    cohort.read_state = lambda _path: next(states)
    cohort.read_managed_text = lambda _path, _label: "unchanged plan"
    cohort.validate_completed_task_sections = lambda _text, _state: None
    args = {
        "amendment_id": "amendment-2",
        "owner_authority_ref": "approval:scope-owner",
        "reason_ref": "follow-on:owned-record",
        "completed_task_evidence": _evidence(),
    }

    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "applied"
    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "conflict"
    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "conflict"
    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "conflict"
    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "absent"


def test_fresh_reapproval_clears_only_replay_marker_and_allows_second_amendment() -> None:
    cohort = _load("loop-cohort.py")
    first = cohort.begin_contract_amendment(
        _state(),
        expected_run_id="run-current",
        owner_authority_ref="approval:first",
        reason_ref="follow-on:first",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-first",
    )
    first.update(
        {
            "plan_review_status": "approved",
            "approved_spec_hash": "f" * 64,
            "approved_plan_hash": "1" * 64,
            "plan_hash": "1" * 64,
            "schedule_waves": [["T3"], ["T4"]],
            "current_wave_index": 1,
        }
    )

    reapproved = cohort.complete_contract_amendment_reapproval(first)
    assert reapproved["amendment_pending"] is None
    assert len(reapproved["amendment_history"]) == 1

    second_hashes = {**_hashes(), "T3": "2" * 64}
    second = cohort.begin_contract_amendment(
        reapproved,
        expected_run_id="run-current",
        owner_authority_ref="approval:second",
        reason_ref="follow-on:second",
        completed_task_section_hashes=second_hashes,
        completed_task_evidence={"T3": ["gates:t3"]},
        amendment_id="amendment-second",
    )

    assert second["completed_task_ids"] == ["T1", "T2", "T3"]
    assert len(second["amendment_history"]) == 2
    assert second["completed_task_evidence"] == {
        **_evidence(),
        "T3": ["gates:t3"],
    }


def test_approve_plan_replay_clears_pending_amendment_after_baseline_was_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = tmp_path / "reapproval-replay"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n", encoding="utf-8"
    )
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n", encoding="utf-8"
    )
    spec_hash = cohort.sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = cohort.sha256_canonical_contract(spec_dir / "plan.md")
    state = {
        "schema_version": 1,
        "run_id": "run-current",
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "amendment_pending": {"amendment_id": "amendment-current"},
    }
    _write_json(spec_dir / "state.json", state)
    monkeypatch.setattr(cohort, "_resolve_spec_dir", lambda _value: spec_dir)
    args = cohort.build_parser().parse_args(
        [
            "approve-plan",
            str(spec_dir),
            "--expect-run-id",
            "run-current",
        ]
    )

    assert cohort.cmd_approve_plan(args) == 0
    reapproved = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    assert reapproved["amendment_pending"] is None
    assert reapproved["approved_spec_hash"] == spec_hash
    assert reapproved["approved_plan_hash"] == plan_hash


def test_completed_sections_are_pinned_and_only_unfinished_tasks_reschedule() -> None:
    cohort = _load("loop-cohort.py")
    plan = """\
## T1: done

**Depends on:** none

proof one

## T2: done

**Depends on:** T1

proof two

## T3: remaining

**Depends on:** T2

build three

## T4: remaining

**Depends on:** T3

build four
"""
    pins = cohort.task_section_hashes(plan, {"T1", "T2"})
    state = {
        "completed_task_ids": ["T1", "T2"],
        "completed_task_section_hashes": pins,
    }

    assert cohort.validate_completed_task_sections(plan, state) is None
    assert cohort.schedule_unfinished_plan(plan, state) == [["T3"], ["T4"]]

    edited = plan.replace("proof two", "rewritten proof")
    assert "T2" in cohort.validate_completed_task_sections(edited, state)

    removed = plan.replace("## T1: done", "## T9: renamed")
    assert "T1" in cohort.validate_completed_task_sections(removed, state)


def test_amendment_history_is_bounded_and_cannot_drop_audit() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    state["amendment_history"] = [
        {"amendment_id": f"prior-{index}"}
        for index in range(cohort.MAX_AMENDMENT_HISTORY)
    ]
    before = copy.deepcopy(state)

    with pytest.raises(ValueError, match="history limit"):
        cohort.begin_contract_amendment(
            state,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence=_evidence(),
            amendment_id="amendment-overflow",
        )

    assert state == before


def test_amendment_evidence_count_and_aggregate_state_are_bounded() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    too_many = {
        "T1": [
            f"evidence:{index}"
            for index in range(cohort.MAX_AMENDMENT_EVIDENCE_REFS + 1)
        ]
    }
    before = copy.deepcopy(state)

    with pytest.raises(ValueError, match="count exceeds"):
        cohort.begin_contract_amendment(
            state,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence=too_many,
            amendment_id="amendment-too-many",
        )
    assert state == before

    oversized = _state()
    oversized["amendment_history"] = [
        {"amendment_id": f"prior-{index}", "padding": "x" * 60_000}
        for index in range(cohort.MAX_AMENDMENT_HISTORY - 1)
    ]
    oversized_before = copy.deepcopy(oversized)
    with pytest.raises(ValueError, match="aggregate limit"):
        cohort.begin_contract_amendment(
            oversized,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence=_evidence(),
            amendment_id="amendment-oversized",
        )
    assert oversized == oversized_before


def test_cohort_mutator_loader_refuses_links_and_incomplete_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = _load("loop-engine.py")
    engine._cohort_mutator_module = None
    monkeypatch.setattr(engine, "SCRIPT_DIR", tmp_path)

    real = tmp_path / "real-cohort.py"
    real.write_text("_MODULE_COMPLETE = True\n", encoding="utf-8")
    link = tmp_path / "loop-cohort.py"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ImportError, match="not a regular file"):
        engine._cohort_mutator()

    link.unlink()
    link.write_text("_MODULE_COMPLETE = True\n", encoding="utf-8")
    with pytest.raises(ImportError, match="missing required amendment symbols"):
        engine._cohort_mutator()

    link.write_text(
        "def apply_contract_amendment(): pass\n"
        "def contract_amendment_replay_status(): pass\n",
        encoding="utf-8",
    )
    with pytest.raises(ImportError, match="module is incomplete"):
        engine._cohort_mutator()


def test_workflow_and_eval_require_normal_reapproval_and_no_automatic_narrowing() -> None:
    lifecycle = SKILL_ROOT / "references/delivery-contract-lifecycle.md"
    skill = " ".join(
        (
            (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
            + lifecycle.read_text(encoding="utf-8")
        ).split()
    )
    for phrase in (
        "## Controlled full-mode contract amendment",
        "explicit scope-owner authority",
        "materialize the separated follow-on through `work-intake`",
        "From code mode `CODE-IMPLEMENTATION`, before editing",
        "preserves completed evidence bound to task IDs, review counters, and run identity",
        "Completed task sections cannot be edited, removed, or renamed",
        "Rescheduling emits only unfinished tasks",
        "session end, retry cap, stasis, or model judgment never invokes",
    ):
        assert phrase in skill

    evals = json.loads(
        (SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8")
    )["evals"]
    case = {item["id"]: item for item in evals}[
        "wave4-contract-amendment-preserves-completed-work"
    ]
    assert "stable owner-authority reference" in case["expected_output"]
    assert "ordinary plan-locked edge" in case["expected_output"]
    assert "cannot invoke it automatically" in case["expected_output"]
