"""Wave 4 full-mode contract-amendment state contracts."""
# ruff: noqa: E402,F811 -- approved AC stubs are appended byte-for-byte.

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
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
        "schema_version": 2,
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
            "schema_version": 2,
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
            "transition_history": [],
            "pending_transition": None,
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
        pre_transition_sequence=2,
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
    assert amended["transition_history"][-1]["approved_spec_hash"] == "a" * 64
    assert amended["transition_history"][-1]["approved_plan_hash"] == "b" * 64


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
        ({"plan_review_status": "pending"}, {}, "approved plan"),
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
        "pre_transition_sequence": 2,
        **kwargs,
    }

    with pytest.raises(ValueError, match=match):
        cohort.begin_contract_amendment(state, **call)

    assert state == before


def test_contract_amendment_succeeds_before_wave_one_without_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, _cohort, spec_dir, _args, _evidence_map = _integration_fixture(
        tmp_path, monkeypatch
    )
    state = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    state["current_wave_index"] = 0
    _write_json(spec_dir / "state.json", state)
    args = engine.build_parser().parse_args(
        [
            "transition",
            str(spec_dir),
            "contract-amendment",
            "--owner-authority-ref",
            "approval:scope-owner",
            "--reason-ref",
            "follow-on:owned-record",
        ]
    )

    assert engine.cmd_transition(args) == 0

    amended = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    snapshot = amended["transition_history"][-1]
    assert snapshot["completed_task_ids"] == []
    assert snapshot["completed_task_section_hashes"] == {}
    assert snapshot["completed_task_evidence"] == {}


def test_contract_amendment_requires_evidence_for_completed_tasks_without_mutation() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    before = copy.deepcopy(state)

    with pytest.raises(ValueError, match="completed task has no evidence binding"):
        cohort.begin_contract_amendment(
            state,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence={},
            amendment_id="amendment-missing-evidence",
            pre_transition_sequence=2,
        )

    assert state == before


def test_contract_amendment_pre_wave_replay_is_idempotent_without_evidence() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    state["current_wave_index"] = 0
    first = cohort.begin_contract_amendment(
        state,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes={},
        completed_task_evidence={},
        amendment_id="amendment-pre-wave",
        pre_transition_sequence=2,
    )

    replay = cohort.begin_contract_amendment(
        first,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes={},
        completed_task_evidence={},
        amendment_id="amendment-pre-wave",
        pre_transition_sequence=2,
    )

    assert replay == first
    assert len(replay["transition_history"]) == 1


def test_engine_finishes_cohort_first_contract_amendment_crash_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, cohort, spec_dir, args, evidence = _integration_fixture(
        tmp_path, monkeypatch
    )
    effect_args = engine._canonical_transition_args(
        {
            "owner_authority_ref": "approval:scope-owner",
            "reason_ref": "follow-on:owned-record",
            "completed_task_evidence": evidence,
        }
    )
    transition_id = engine._registered_transition_id(
        "integration-run", 8, "contract-amendment", effect_args
    )
    cohort.prepare_transition(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=8,
        event="contract-amendment",
        args=effect_args,
        opened_at="2026-09-25T00:00:00Z",
    )
    cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=8,
        event="contract-amendment",
        args=effect_args,
    )

    assert engine.cmd_transition(args) == 0

    engine_state = json.loads((spec_dir / "engine-state.json").read_text())
    cohort_state = json.loads((spec_dir / "state.json").read_text())
    assert engine_state["state"] == "SPEC-PLAN-DRAFTING"
    assert engine_state["transition_sequence"] == 9
    assert engine_state["last_event_context"]["completed_task_evidence"] == evidence
    assert cohort_state["completed_task_evidence"] == evidence
    assert len(cohort_state["transition_history"]) == 1


def test_engine_finishes_engine_first_contract_amendment_crash_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, _cohort, spec_dir, args, evidence = _integration_fixture(
        tmp_path, monkeypatch
    )
    effect_args = engine._canonical_transition_args(
        {
            "owner_authority_ref": "approval:scope-owner",
            "reason_ref": "follow-on:owned-record",
            "completed_task_evidence": evidence,
        }
    )
    transition_id = engine._registered_transition_id(
        "integration-run", 8, "contract-amendment", effect_args
    )
    engine_first = json.loads((spec_dir / "engine-state.json").read_text())
    engine_first.update(
        {
            "state": "SPEC-PLAN-DRAFTING",
            "last_event": "contract-amendment",
            "last_event_context": {
                "amendment_id": transition_id,
                "pre_transition_sequence": 8,
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
    assert cohort_state["pending_transition"] is None
    assert cohort_state["transition_history"][-1]["transition_id"] == transition_id
    assert len(cohort_state["transition_history"]) == 1


def test_engine_first_recovery_refuses_when_the_plan_no_longer_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The recovery branch may complete a pinned baseline, never derive a new one.

    Reaching this branch means the two untracked scratch files diverged, so the
    plan cannot be assumed to still be what was approved. The branch returns
    before the main critical section, so nothing downstream re-checks the plan;
    without its own check, `apply_contract_amendment` lands on the derive path
    and recomputes `task_section_hashes` from whatever `plan.md` now holds —
    laundering an edit to an already-completed task section into the baseline
    that `validate_completed_task_sections` later ratifies.

    The refusal must also be total: a rejected recovery leaves the cohort state
    byte-identical, so no partial pin is left behind for a second attempt.
    """
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

    # Substantive drift, not a checkbox or status change: canonical form
    # normalises those two, so they are hash-neutral by design and would not
    # exercise the check.
    plan_path = spec_dir / "plan.md"
    plan_path.write_text(
        plan_path.read_text(encoding="utf-8") + "\nSmuggled plan content.\n",
        encoding="utf-8",
    )

    cohort_before = (spec_dir / "state.json").read_bytes()
    engine_before = (spec_dir / "engine-state.json").read_bytes()

    assert engine.cmd_transition(args) == 1

    assert (spec_dir / "state.json").read_bytes() == cohort_before
    assert (spec_dir / "engine-state.json").read_bytes() == engine_before


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
            pre_transition_sequence=2,
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
        pre_transition_sequence=2,
    )
    replay = cohort.begin_contract_amendment(
        first,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-2",
        pre_transition_sequence=2,
    )

    assert replay == first
    assert len(replay["transition_history"]) == 1

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
            pre_transition_sequence=2,
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
            pre_transition_sequence=2,
        )


def test_cohort_first_crash_window_is_classified_without_mutation() -> None:
    cohort = _load("loop-cohort.py")
    pending = {
        "transition_id": "amendment-2",
        "pre_transition_sequence": 2,
        "event": "contract-amendment",
        "args": {
            "owner_authority_ref": "approval:scope-owner",
            "reason_ref": "follow-on:owned-record",
            "completed_task_evidence": _evidence(),
        },
        "opened_at": None,
    }
    snapshot = {
        "transition_id": "amendment-2",
        "pre_transition_sequence": 2,
        "event": "contract-amendment",
        "args": {
            "owner_authority_ref": "approval:scope-owner",
            "reason_ref": "follow-on:owned-record",
            "completed_task_evidence": _evidence(),
        },
        "amendment_id": "amendment-2",
        "owner_authority_ref": "approval:scope-owner",
        "reason_ref": "follow-on:owned-record",
        "completed_task_ids": ["T1", "T2"],
        "completed_task_section_hashes": _hashes(),
        "completed_task_evidence": _evidence(),
    }
    applied = {
        "schema_version": 2,
        "pending_transition": pending,
        "transition_history": [snapshot],
        "completed_task_ids": ["T1", "T2"],
        "completed_task_section_hashes": _hashes(),
        "completed_task_evidence": _evidence(),
    }
    states = iter(
        [
            applied,
            {**applied, "pending_transition": {**pending, "opened_at": "later"}},
            {
                **applied,
                "pending_transition": {**pending, "transition_id": "tampered"},
            },
            {
                **applied,
                "transition_history": [
                    {**snapshot, "owner_authority_ref": "approval:tampered"}
                ],
            },
            {"schema_version": 2, "transition_history": []},
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
        "pre_transition_sequence": 2,
    }

    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "applied"
    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "applied"
    assert cohort.contract_amendment_replay_status(Path("unused"), **args) == "applied"
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
        pre_transition_sequence=1,
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
    assert reapproved["pending_transition"] is None
    assert len(reapproved["transition_history"]) == 1

    second_hashes = {**_hashes(), "T3": "2" * 64}
    second = cohort.begin_contract_amendment(
        reapproved,
        expected_run_id="run-current",
        owner_authority_ref="approval:second",
        reason_ref="follow-on:second",
        completed_task_section_hashes=second_hashes,
        completed_task_evidence={"T3": ["gates:t3"]},
        amendment_id="amendment-second",
        pre_transition_sequence=2,
    )

    assert second["completed_task_ids"] == ["T1", "T2", "T3"]
    assert len(second["transition_history"]) == 2
    assert second["completed_task_evidence"] == {
        **_evidence(),
        "T3": ["gates:t3"],
    }


def test_second_amendment_replay_status_uses_transition_args_not_accumulated_evidence(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    first = cohort.begin_contract_amendment(
        _state(),
        expected_run_id="run-current",
        owner_authority_ref="approval:first",
        reason_ref="follow-on:first",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="run-current:1",
        pre_transition_sequence=1,
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
    second_hashes = {**_hashes(), "T3": "2" * 64}
    second = cohort.begin_contract_amendment(
        reapproved,
        expected_run_id="run-current",
        owner_authority_ref="approval:second",
        reason_ref="follow-on:second",
        completed_task_section_hashes=second_hashes,
        completed_task_evidence={"T3": ["gates:t3"]},
        amendment_id="run-current:2",
        pre_transition_sequence=2,
    )
    applied = cohort.complete_contract_amendment_reapproval(
        {
            **second,
            "plan_review_status": "approved",
            "approved_spec_hash": "3" * 64,
            "approved_plan_hash": "4" * 64,
        }
    )
    spec_dir = tmp_path / "second-amendment"
    spec_dir.mkdir()
    (spec_dir / "plan.md").write_text(
        "## T1: done\n\n**Depends on:** none\n\nproof one\n\n"
        "## T2: done\n\n**Depends on:** T1\n\nproof two\n\n"
        "## T3: done\n\n**Depends on:** T2\n\nproof three\n",
        encoding="utf-8",
    )
    applied["completed_task_section_hashes"] = cohort.task_section_hashes(
        (spec_dir / "plan.md").read_text(encoding="utf-8"),
        set(applied["completed_task_ids"]),
    )
    applied["transition_history"][-1]["completed_task_section_hashes"] = dict(
        applied["completed_task_section_hashes"]
    )
    _write_json(spec_dir / "state.json", applied)

    assert applied["pending_transition"] is None
    assert applied["transition_history"][-1]["args"]["completed_task_evidence"] == {
        "T3": ["gates:t3"]
    }
    assert applied["transition_history"][-1]["completed_task_evidence"] == {
        **_evidence(),
        "T3": ["gates:t3"],
    }
    assert cohort.transition_replay_status(
        spec_dir,
        transition_id="run-current:2",
        pre_transition_sequence=2,
        event="contract-amendment",
        args={
            "owner_authority_ref": "approval:second",
            "reason_ref": "follow-on:second",
            "completed_task_evidence": {"T3": ["gates:t3"]},
        },
    ) == "applied"


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
        "schema_version": 2,
        "run_id": "run-current",
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "pending_transition": {"transition_id": "amendment-current"},
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
    assert reapproved["pending_transition"] is None
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


def test_transition_history_can_exceed_twenty_entries_and_keeps_newest() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    state["transition_history"] = [
        {"transition_id": f"prior-{index}", "pre_transition_sequence": index}
        for index in range(25)
    ]

    amended = cohort.begin_contract_amendment(
        state,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-overflow",
        pre_transition_sequence=26,
    )

    assert len(amended["transition_history"]) == 26
    assert amended["transition_history"][-1]["transition_id"] == "amendment-overflow"


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
            pre_transition_sequence=2,
        )
    assert state == before

    oversized = _state()
    oversized["transition_history"] = [
        {"transition_id": f"prior-{index}", "padding": "x" * 60_000}
        for index in range(25)
    ]
    oversized_before = copy.deepcopy(oversized)
    amended = cohort.begin_contract_amendment(
        oversized,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_section_hashes=_hashes(),
        completed_task_evidence=_evidence(),
        amendment_id="amendment-oversized",
        pre_transition_sequence=26,
    )
    assert oversized == oversized_before
    assert amended["transition_history"][0]["transition_id"] != "prior-0"
    assert amended["transition_history"][-1]["transition_id"] == "amendment-oversized"
    assert len(json.dumps(amended, ensure_ascii=False, separators=(",", ":")).encode()) <= (
        cohort.MAX_TRANSITION_STATE_BYTES
    )


def test_transition_history_refuses_when_newest_entry_cannot_fit() -> None:
    cohort = _load("loop-cohort.py")
    state = {"schema_version": 2, "transition_history": [{"transition_id": "old"}]}
    before = copy.deepcopy(state)
    newest = {
        "transition_id": "newest",
        "pre_transition_sequence": 99,
        "event": "gates-failed",
        "args": {},
        "padding": "x" * cohort.MAX_TRANSITION_STATE_BYTES,
    }

    with pytest.raises(ValueError, match="newest entry exceeds"):
        cohort._retained_transition_state(state, newest)

    assert state == before


def _compact_state_size(state: dict) -> int:
    return len(json.dumps(state, ensure_ascii=False, separators=(",", ":")).encode())


def _with_padding_to_fit(
    cohort,
    state: dict,
    history_index: int,
    *,
    margin: int,
) -> dict:
    """Return a copy whose selected history padding leaves `margin` bytes free."""
    candidate = copy.deepcopy(state)
    low = 0
    high = cohort.MAX_TRANSITION_STATE_BYTES
    while low <= high:
        mid = (low + high) // 2
        candidate["transition_history"][history_index]["padding"] = "x" * mid
        size = _compact_state_size(candidate)
        if size <= cohort.MAX_TRANSITION_STATE_BYTES - margin:
            low = mid + 1
        else:
            high = mid - 1
    candidate["transition_history"][history_index]["padding"] = "x" * high
    return candidate


def _large_contract_amendment_args() -> dict:
    return {
        "owner_authority_ref": "o" * 1000,
        "reason_ref": "r" * 1000,
        "completed_task_evidence": {
            "T1": [f"evidence-{index}-" + "x" * 980 for index in range(64)]
        },
    }


def _contract_amendment_retention_state(
    cohort,
    spec_dir: Path,
    transition_id: str,
    args: dict,
) -> dict:
    state = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    state["current_wave_index"] = 1
    state["pending_transition"] = {
        **cohort._transition_identity(
            transition_id=transition_id,
            pre_transition_sequence=21,
            event="contract-amendment",
            args=args,
        ),
        "opened_at": "2026-09-25T00:00:00Z",
    }
    return state


def _apply_contract_amendment_effect(
    cohort,
    spec_dir: Path,
    transition_id: str,
    args: dict,
) -> str:
    return cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=21,
        event="contract-amendment",
        args=args,
    )


def test_registered_contract_amendment_retention_measures_final_state_after_marker_clear(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "run-current:contract-marker-does-not-trim"
    args = _large_contract_amendment_args()
    state = _contract_amendment_retention_state(cohort, spec_dir, transition_id, args)
    state["transition_history"] = [
        {
            "transition_id": "oldest",
            "pre_transition_sequence": 20,
            "event": "gates-failed",
            "args": {},
        }
    ]
    expected_final = cohort.begin_contract_amendment(
        state,
        expected_run_id="run-current",
        owner_authority_ref=args["owner_authority_ref"],
        reason_ref=args["reason_ref"],
        completed_task_section_hashes=cohort.task_section_hashes(
            (spec_dir / "plan.md").read_text(encoding="utf-8"), {"T1"}
        ),
        completed_task_evidence=args["completed_task_evidence"],
        amendment_id=transition_id,
        pre_transition_sequence=21,
        retain_transition_history=False,
    )
    expected_final["pending_transition"] = None
    expected_final = _with_padding_to_fit(
        cohort, expected_final, 0, margin=1_024
    )
    state["transition_history"][0]["padding"] = expected_final["transition_history"][0][
        "padding"
    ]
    markerful = copy.deepcopy(expected_final)
    markerful["pending_transition"] = state["pending_transition"]
    assert _compact_state_size(expected_final) <= cohort.MAX_TRANSITION_STATE_BYTES
    assert _compact_state_size(markerful) > cohort.MAX_TRANSITION_STATE_BYTES
    _write_json(state_path, state)

    assert _apply_contract_amendment_effect(
        cohort, spec_dir, transition_id, args
    ) == "applied"

    applied = json.loads(state_path.read_text(encoding="utf-8"))
    assert applied["pending_transition"] is None
    assert [entry["transition_id"] for entry in applied["transition_history"]] == [
        "oldest",
        transition_id,
    ]
    assert _compact_state_size(applied) <= cohort.MAX_TRANSITION_STATE_BYTES


def test_registered_contract_amendment_marker_bytes_do_not_false_refuse(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "run-current:contract-marker-does-not-refuse"
    args = _large_contract_amendment_args()
    state = _contract_amendment_retention_state(cohort, spec_dir, transition_id, args)
    expected_final = cohort.begin_contract_amendment(
        state,
        expected_run_id="run-current",
        owner_authority_ref=args["owner_authority_ref"],
        reason_ref=args["reason_ref"],
        completed_task_section_hashes=cohort.task_section_hashes(
            (spec_dir / "plan.md").read_text(encoding="utf-8"), {"T1"}
        ),
        completed_task_evidence=args["completed_task_evidence"],
        amendment_id=transition_id,
        pre_transition_sequence=21,
        retain_transition_history=False,
    )
    expected_final["pending_transition"] = None
    low = 0
    high = cohort.MAX_TRANSITION_STATE_BYTES
    while low <= high:
        mid = (low + high) // 2
        state["schedule_waves"] = [["T1"], ["x" * mid]]
        expected_final = cohort.begin_contract_amendment(
            state,
            expected_run_id="run-current",
            owner_authority_ref=args["owner_authority_ref"],
            reason_ref=args["reason_ref"],
            completed_task_section_hashes=cohort.task_section_hashes(
                (spec_dir / "plan.md").read_text(encoding="utf-8"), {"T1"}
            ),
            completed_task_evidence=args["completed_task_evidence"],
            amendment_id=transition_id,
            pre_transition_sequence=21,
            retain_transition_history=False,
        )
        expected_final["pending_transition"] = None
        if _compact_state_size(expected_final) <= cohort.MAX_TRANSITION_STATE_BYTES - 1_024:
            low = mid + 1
        else:
            high = mid - 1
    state["schedule_waves"] = [["T1"], ["x" * high]]
    final_check = cohort.begin_contract_amendment(
        state,
        expected_run_id="run-current",
        owner_authority_ref=args["owner_authority_ref"],
        reason_ref=args["reason_ref"],
        completed_task_section_hashes=cohort.task_section_hashes(
            (spec_dir / "plan.md").read_text(encoding="utf-8"), {"T1"}
        ),
        completed_task_evidence=args["completed_task_evidence"],
        amendment_id=transition_id,
        pre_transition_sequence=21,
        retain_transition_history=False,
    )
    final_check["pending_transition"] = None
    markerful = copy.deepcopy(final_check)
    markerful["pending_transition"] = state["pending_transition"]
    assert _compact_state_size(final_check) <= cohort.MAX_TRANSITION_STATE_BYTES
    assert _compact_state_size(markerful) > cohort.MAX_TRANSITION_STATE_BYTES
    _write_json(state_path, state)

    assert _apply_contract_amendment_effect(
        cohort, spec_dir, transition_id, args
    ) == "applied"

    applied = json.loads(state_path.read_text(encoding="utf-8"))
    assert applied["pending_transition"] is None
    assert applied["transition_history"][-1]["transition_id"] == transition_id
    assert _compact_state_size(applied) <= cohort.MAX_TRANSITION_STATE_BYTES


def test_registered_contract_amendment_true_post_clear_oversize_refuses_unchanged(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "run-current:contract-newest-too-large"
    args = _large_contract_amendment_args()
    state = _contract_amendment_retention_state(cohort, spec_dir, transition_id, args)
    state["schedule_waves"] = [["T1"], ["x" * cohort.MAX_TRANSITION_STATE_BYTES]]
    _write_json(state_path, state)
    before = state_path.read_bytes()

    with pytest.raises(ValueError, match="newest entry exceeds"):
        _apply_contract_amendment_effect(cohort, spec_dir, transition_id, args)

    assert state_path.read_bytes() == before


def test_apply_transition_retention_measures_final_state_after_marker_clear(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "run-current:marker-does-not-trim"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pending_transition"] = {
        "transition_id": transition_id,
        "pre_transition_sequence": 11,
        "event": "gates-failed",
        "args": {},
        "opened_at": "m" * 4_096,
    }
    state["transition_history"] = [
        {
            "transition_id": "oldest",
            "pre_transition_sequence": 10,
            "event": "gates-failed",
            "args": {},
        }
    ]
    expected_final = copy.deepcopy(state)
    expected_final["pending_transition"] = None
    expected_final["implementation_retry_count"] = 1
    expected_final["last_record_attempt_cycle_id"] = "run-current:11"
    expected_final["transition_history"].append(
        {
            "transition_id": transition_id,
            "pre_transition_sequence": 11,
            "event": "gates-failed",
            "args": {},
            "implementation_retry_count": 1,
            "last_record_attempt_cycle_id": "run-current:11",
        }
    )
    expected_final = _with_padding_to_fit(
        cohort, expected_final, 0, margin=1_024
    )
    state["transition_history"][0]["padding"] = expected_final["transition_history"][0][
        "padding"
    ]
    assert _compact_state_size(expected_final) <= cohort.MAX_TRANSITION_STATE_BYTES
    assert _compact_state_size({**expected_final, "pending_transition": state["pending_transition"]}) > (
        cohort.MAX_TRANSITION_STATE_BYTES
    )
    _write_json(state_path, state)

    assert cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=11,
        event="gates-failed",
        args={},
    ) == "applied"

    applied = json.loads(state_path.read_text(encoding="utf-8"))
    assert applied["pending_transition"] is None
    assert [entry["transition_id"] for entry in applied["transition_history"]] == [
        "oldest",
        transition_id,
    ]
    assert _compact_state_size(applied) <= cohort.MAX_TRANSITION_STATE_BYTES


def test_apply_transition_retention_false_refusal_ignores_marker_bytes(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "run-current:marker-does-not-refuse"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pending_transition"] = {
        "transition_id": transition_id,
        "pre_transition_sequence": 12,
        "event": "gates-failed",
        "args": {},
        "opened_at": "m" * cohort.MAX_TRANSITION_STATE_BYTES,
    }
    _write_json(state_path, state)
    before = state_path.read_bytes()

    assert cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=12,
        event="gates-failed",
        args={},
    ) == "applied"

    applied = json.loads(state_path.read_text(encoding="utf-8"))
    assert state_path.read_bytes() != before
    assert applied["pending_transition"] is None
    assert applied["transition_history"][-1]["transition_id"] == transition_id
    assert _compact_state_size(applied) <= cohort.MAX_TRANSITION_STATE_BYTES


def test_apply_transition_retention_refuses_true_newest_only_oversize_unchanged(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "run-current:newest-too-large"
    args = {"padding": "x" * cohort.MAX_TRANSITION_STATE_BYTES}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pending_transition"] = {
        "transition_id": transition_id,
        "pre_transition_sequence": 13,
        "event": "gates-failed",
        "args": args,
        "opened_at": "2026-09-25T00:00:00Z",
    }
    _write_json(state_path, state)
    before = state_path.read_bytes()

    with pytest.raises(ValueError, match="newest entry exceeds"):
        cohort.apply_transition_effect(
            spec_dir,
            transition_id=transition_id,
            pre_transition_sequence=13,
            event="gates-failed",
            args=args,
        )

    assert state_path.read_bytes() == before


def test_schema_one_cohort_state_refuses_without_mutation() -> None:
    cohort = _load("loop-cohort.py")
    state = _state()
    state["schema_version"] = 1
    before = copy.deepcopy(state)

    with pytest.raises(ValueError, match="schema_version=2"):
        cohort.begin_contract_amendment(
            state,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_section_hashes=_hashes(),
            completed_task_evidence=_evidence(),
            amendment_id="amendment-old-schema",
            pre_transition_sequence=2,
        )

    assert state == before


def test_transition_schema_refusals_name_reset_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["schema_version"] = 1
    _write_json(state_path, state)
    reset_order = "run `loop-cohort reset` then `loop-engine reset`"

    with pytest.raises(ValueError, match=reset_order):
        cohort.prepare_transition(
            spec_dir,
            transition_id="run-current:3",
            pre_transition_sequence=3,
            event="gates-failed",
            args={},
            opened_at="2026-09-25T00:00:00Z",
        )
    with pytest.raises(ValueError, match=reset_order):
        cohort.transition_replay_status(
            spec_dir,
            transition_id="run-current:3",
            pre_transition_sequence=3,
            event="gates-failed",
            args={},
        )
    with pytest.raises(ValueError, match=reset_order):
        cohort.apply_transition_effect(
            spec_dir,
            transition_id="run-current:3",
            pre_transition_sequence=3,
            event="gates-failed",
            args={},
        )
    stderr = io.StringIO()
    monkeypatch.setattr(cohort, "_resolve_spec_dir", lambda _value: spec_dir)
    with contextlib.redirect_stderr(stderr):
        rc = cohort.cmd_status(
            cohort.argparse.Namespace(spec_dir=str(spec_dir), json=False)
        )
    assert rc == 1
    assert reset_order in stderr.getvalue()


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


# ── Unknown-dependency refusal (T2) ────────────────────────────────────────


def test_schedule_unfinished_plan_raises_for_unknown_dep() -> None:
    """schedule_unfinished_plan raises ValueError naming the (task, dep) pair
    when an unfinished task declares a dependency that names no task in the plan."""
    cohort = _load("loop-cohort.py")
    plan = (
        "## T1: task one\n\n**Depends on:** none\n\nsome content\n\n"
        "## T2: task two\n\n**Depends on:** T7\n\nsome content\n"
    )
    state: dict = {"completed_task_ids": [], "completed_task_section_hashes": {}}
    with pytest.raises(ValueError, match="T2->T7"):
        cohort.schedule_unfinished_plan(plan, state)


def test_schedule_unfinished_plan_ac7_completed_dep_is_met() -> None:
    """AC7: an unfinished task that depends on a completed task schedules normally.

    The resolution set is every task in the plan, not just unfinished ones, so
    a completed dependency is resolved rather than refused."""
    cohort = _load("loop-cohort.py")
    plan = (
        "## T1: completed\n\n**Depends on:** none\n\nproof one\n\n"
        "## T2: remaining\n\n**Depends on:** T1\n\nbuild two\n"
    )
    pins = cohort.task_section_hashes(plan, {"T1"})
    state: dict = {
        "completed_task_ids": ["T1"],
        "completed_task_section_hashes": pins,
    }
    # T2 depends on completed T1 — must succeed, not refuse.
    assert cohort.schedule_unfinished_plan(plan, state) == [["T2"]]


def test_schedule_unfinished_plan_ac7a_completed_task_stale_dep_is_ignored() -> None:
    """AC7a: a completed task whose Depends on names an absent ID does not refuse
    the run, because completed tasks are outside the scan set."""
    cohort = _load("loop-cohort.py")
    # T1 (completed) declares a dependency on T99, which does not exist in the plan.
    # T2 (remaining) has a valid dependency on none.
    plan = (
        "## T1: completed\n\n**Depends on:** T99\n\nproof one\n\n"
        "## T2: remaining\n\n**Depends on:** none\n\nbuild two\n"
    )
    pins = cohort.task_section_hashes(plan, {"T1"})
    state: dict = {
        "completed_task_ids": ["T1"],
        "completed_task_section_hashes": pins,
    }
    # T1's stale declaration is out of scope (not in remaining_set); must not raise.
    assert cohort.schedule_unfinished_plan(plan, state) == [["T2"]]


def test_schedule_unfinished_plan_ac4_unknown_dep_beats_cycle() -> None:
    """AC4 (amendment path): when a plan has both an unknown dependency and a cycle,
    the unknown-dependency refusal takes precedence over the cycle refusal."""
    cohort = _load("loop-cohort.py")
    # T1 and T2 form a cycle; T3 has an unknown dependency on T99.
    plan = (
        "## T1: task one\n\n**Depends on:** T2\n\ncontent\n\n"
        "## T2: task two\n\n**Depends on:** T1\n\ncontent\n\n"
        "## T3: task three\n\n**Depends on:** T99\n\ncontent\n"
    )
    state: dict = {"completed_task_ids": [], "completed_task_section_hashes": {}}
    with pytest.raises(ValueError, match="T3->T99") as exc_info:
        cohort.schedule_unfinished_plan(plan, state)
    assert "cycle" not in str(exc_info.value)


# ── dispatch receipts across an amendment ─────────────────────────────────
#
# Contract: § The record
# lifecycle. An amendment reopens the contract, so no record written before it
# may account for a task after it.


def _receipts_amendment_fixture(tmp_path: Path) -> tuple[object, Path, dict]:
    """A wave-index-zero cohort holding one receipt, ready to be amended.

    Index zero is the discriminating case: no task is completed, so the
    re-scheduled partition is identical and its digest therefore unchanged. An
    implementation that emptied the container only by re-keying on a new digest
    passes every other lifecycle case and fails this one.
    """
    cohort = _load("loop-cohort.py")
    spec_dir = tmp_path / "receipts-amendment"
    spec_dir.mkdir()
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n## T1: first\n\n**Depends on:** none\n\nbuild one\n\n"
        "## T2: second\n\n**Depends on:** T1\n\nbuild two\n",
        encoding="utf-8",
    )
    plan_hash = cohort.sha256_canonical_contract(spec_dir / "plan.md")
    waves = [["T1"], ["T2"]]
    digest = cohort.partition_digest(waves)
    state = {
        "schema_version": 2,
        "run_id": "run-current",
        "plan_review_status": "approved",
        "approved_spec_hash": "a" * 64,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": waves,
        "current_wave_index": 0,
        "completed_task_ids": [],
        "completed_task_section_hashes": {},
        "completed_task_evidence": {},
        "transition_history": [],
        "pending_transition": None,
        cohort.RECEIPTS_KEY: {digest: {"0": {"T1": {"kind": "receipt"}}}},
    }
    _write_json(spec_dir / "state.json", state)
    return cohort, spec_dir, state


def test_amendment_leaves_the_receipts_container_empty(tmp_path: Path) -> None:
    cohort, spec_dir, before = _receipts_amendment_fixture(tmp_path)
    amended = cohort.apply_contract_amendment(
        spec_dir,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_evidence={},
        amendment_id="amendment-receipts-zero",
        pre_transition_sequence=0,
    )

    # The digest has not moved, so emptying the container is the only thing that
    # can have removed the record.
    unchanged_digest = cohort.partition_digest(before["schedule_waves"])
    assert unchanged_digest in before[cohort.RECEIPTS_KEY]
    assert amended[cohort.RECEIPTS_KEY] == {}, (
        "an amendment must leave the receipts container empty"
    )
    persisted = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    assert persisted[cohort.RECEIPTS_KEY] == {}
    assert cohort.RECEIPTS_KEY in persisted, "the container stays present, just empty"

    # A re-schedule reproduces the same partition, and the pre-amendment record
    # must not come back with it.
    replayed = dict(persisted, schedule_waves=before["schedule_waves"])
    assert cohort.partition_digest(replayed["schedule_waves"]) == unchanged_digest
    assert replayed[cohort.RECEIPTS_KEY] == {}


def test_contract_amendment_commits_without_an_engine_side_cohort_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC14: the exempt event completes, and the engine takes no cohort lock for it.

    Spec: docs/specs/wave-exit-verdict-serialisation/spec.md AC14.

    The exemption is mechanically forced — `apply_contract_amendment` writes
    cohort state, so this event's fingerprint always differs and including it
    would refuse every amendment. It is also what keeps the commit hold from
    enclosing that call, which takes the cohort lock itself on a lock that is
    not reentrant. Asserting only that the amendment still succeeds would pass
    against a hold that acquired and released around it, so this counts the
    acquisitions the engine's own hold makes.
    """
    engine, _cohort, spec_dir, _args, _evidence_map = _integration_fixture(
        tmp_path, monkeypatch
    )
    state = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    state["current_wave_index"] = 0
    _write_json(spec_dir / "state.json", state)

    held: list[str] = []
    real_hold = engine._cohort_commit_hold

    def counting_hold(sd: Path, event: str):
        held.append(event)
        return real_hold(sd, event)

    monkeypatch.setattr(engine, "_cohort_commit_hold", counting_hold)

    args = engine.build_parser().parse_args(
        [
            "transition",
            str(spec_dir),
            "contract-amendment",
            "--owner-authority-ref",
            "approval:scope-owner",
            "--reason-ref",
            "follow-on:owned-record",
        ]
    )
    assert engine.cmd_transition(args) == 0
    assert held == ["contract-amendment"], held

    # The hold for this event yields without acquiring; a checked event does not.
    acquired: list[str] = []
    sl = engine._statelock()
    real_exclusive = sl.exclusive

    def recording(path, **kwargs):
        acquired.append(Path(path).name)
        return real_exclusive(path, **kwargs)

    monkeypatch.setattr(sl, "exclusive", recording)
    with engine._cohort_commit_hold(spec_dir, "contract-amendment"):
        pass
    assert acquired == [], f"the exempt event must acquire nothing, got {acquired}"
    with engine._cohort_commit_hold(spec_dir, "spec-ready"):
        pass
    assert acquired == ["state.json"], acquired


def _transition_effect_fixture(tmp_path: Path) -> Path:
    spec_dir = tmp_path / "transition-effects"
    spec_dir.mkdir()
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n"
        "## T1: completed baseline\n\n**Depends on:** none\n\nproof one\n\n"
        "## T2: remaining work\n\n**Depends on:** T1\n\nbuild two\n",
        encoding="utf-8",
    )
    state = {
        "schema_version": 2,
        "run_id": "run-current",
        "feature": spec_dir.name,
        "plan_review_status": "approved",
        "approved_spec_hash": "a" * 64,
        "approved_plan_hash": "b" * 64,
        "plan_hash": "b" * 64,
        "schedule_waves": [["T1"], ["T2"]],
        "current_wave_index": 0,
        "completed_task_ids": [],
        "completed_task_section_hashes": {},
        "completed_task_evidence": {},
        "transition_history": [],
        "pending_transition": None,
        "implementation_retry_count": 0,
        "review_round_count": 0,
        "review_retry_count": 0,
        "max_review_retries": 5,
        "finding_fingerprints": [],
        "previous_finding_fingerprints": [],
        "last_review_record_operation_id": None,
        "last_review_record_payload_digest": None,
        "dispatch_receipts": {},
    }
    _write_json(spec_dir / "state.json", state)
    return spec_dir


@pytest.mark.parametrize(
    ("event", "args", "expect"),
    [
        ("contract-amendment", {
            "owner_authority_ref": "approval:scope-owner",
            "reason_ref": "follow-on:owned-record",
            "completed_task_evidence": {"T1": ["gates:t1"]},
        }, {"plan_review_status": "pending", "completed_task_ids": ["T1"]}),
        ("wave-passed", {"wave_index": 0}, {"current_wave_index": 1}),
        ("gates-failed", {}, {
            "implementation_retry_count": 1,
            "last_record_attempt_cycle_id": "run-current:7",
        }),
        ("findings-remain", {"fingerprints": ["f" * 64]}, {
            "review_round_count": 1,
            "review_retry_count": 1,
            "last_review_record_operation_id": "7" * 64,
        }),
        ("reviewers-clean", {"all_skipped": True}, {
            "review_round_count": 1,
            "last_review_record_operation_id": "7" * 64,
        }),
    ],
)
def test_apply_transition_effect_registry_rows_apply_once_and_clear_marker(
    tmp_path: Path, event: str, args: dict, expect: dict
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    transition_id = "7" * 64
    state_path = spec_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if event == "contract-amendment":
        state["current_wave_index"] = 1
    if event == "wave-passed":
        waves = state["schedule_waves"]
        state[cohort.RECEIPTS_KEY] = {
            cohort.partition_digest(waves): {
                "0": {"T1": {"kind": cohort.RECEIPT_KIND}}
            }
        }
    _write_json(state_path, state)

    cohort.prepare_transition(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=7,
        event=event,
        args=args,
        opened_at="2026-09-25T00:00:00Z",
    )
    assert cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=7,
        event=event,
        args=args,
    ) == "applied"
    first = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    assert first["pending_transition"] is None
    assert first["transition_history"][-1]["transition_id"] == transition_id
    assert first["transition_history"][-1]["pre_transition_sequence"] == 7
    assert first["transition_history"][-1]["event"] == event
    for key, value in expect.items():
        assert first[key] == value

    assert cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=7,
        event=event,
        args=args,
    ) == "applied"
    replay = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    assert replay == first


def test_unregistered_transition_effect_leaves_cohort_bytes_unchanged(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    engine = _load("loop-engine.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    before = (spec_dir / "state.json").read_bytes()
    fsm_events = {
        event
        for table in engine._TRANSITIONS_BY_MODE.values()
        for (_state, event) in table
    }
    non_members = sorted(fsm_events - set(cohort._TRANSITION_EFFECTS))
    assert non_members
    assert fsm_events & set(cohort._TRANSITION_EFFECTS) == set(
        cohort._TRANSITION_EFFECTS
    )

    for index, event in enumerate(non_members, start=1):
        assert cohort.apply_transition_effect(
            spec_dir,
            transition_id=f"run-current:{index}",
            pre_transition_sequence=index,
            event=event,
            args={},
        ) == "skipped"
        assert (spec_dir / "state.json").read_bytes() == before

    assert (spec_dir / "state.json").read_bytes() == before


@pytest.mark.parametrize(
    ("event", "args", "seed"),
    [
        ("wave-passed", {"wave_index": 0}, "wave"),
        ("gates-failed", {}, "attempt"),
        ("findings-remain", {"fingerprints": ["f" * 64]}, "findings"),
        ("reviewers-clean", {"all_skipped": True}, "clean"),
    ],
)
def test_registered_effect_already_branches_still_append_unified_history(
    tmp_path: Path, event: str, args: dict, seed: str
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    transition_id = "8" * 64
    sequence = 31

    assert cohort.prepare_transition(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=sequence,
        event=event,
        args=args,
        opened_at="2026-09-25T00:00:00Z",
    ) == "prepared"

    seeded = json.loads(state_path.read_text(encoding="utf-8"))
    if seed == "wave":
        seeded["current_wave_index"] = 1
    elif seed == "attempt":
        seeded["implementation_retry_count"] = 1
        seeded["last_record_attempt_cycle_id"] = "run-current:31"
    elif seed == "findings":
        seeded["review_round_count"] = 1
        seeded["review_retry_count"] = 1
        seeded["finding_fingerprints"] = ["f" * 64]
        seeded["last_review_record_operation_id"] = transition_id
        seeded["last_review_record_payload_digest"] = cohort._review_payload_digest(
            "fingerprint", "f" * 64
        )
    elif seed == "clean":
        seeded["review_round_count"] = 1
        seeded["finding_fingerprints"] = []
        seeded["last_review_record_operation_id"] = transition_id
        seeded["last_review_record_payload_digest"] = cohort._review_payload_digest(
            "all-skipped", ""
        )
    else:  # pragma: no cover - parameter table is closed above
        raise AssertionError(seed)
    _write_json(state_path, seeded)

    assert cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=sequence,
        event=event,
        args=args,
    ) == "applied"

    applied = json.loads(state_path.read_text(encoding="utf-8"))
    assert applied["pending_transition"] is None
    assert len(applied["transition_history"]) == 1
    assert applied["transition_history"][0]["transition_id"] == transition_id
    assert applied["transition_history"][0]["pre_transition_sequence"] == sequence
    assert applied["transition_history"][0]["event"] == event
    assert cohort.transition_replay_status(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=sequence,
        event=event,
        args=args,
    ) == "applied"
    assert cohort.apply_transition_effect(
        spec_dir,
        transition_id=transition_id,
        pre_transition_sequence=sequence,
        event=event,
        args=args,
    ) == "applied"
    replay = json.loads(state_path.read_text(encoding="utf-8"))
    assert replay == applied

    if seed == "wave":
        assert applied["current_wave_index"] == 1
    elif seed == "attempt":
        assert applied["implementation_retry_count"] == 1
    elif seed == "findings":
        assert applied["review_round_count"] == 1
        assert applied["review_retry_count"] == 1
    elif seed == "clean":
        assert applied["review_round_count"] == 1


def test_absent_registered_effect_without_marker_refuses_unchanged(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    before = (spec_dir / "state.json").read_bytes()

    with pytest.raises(ValueError, match="pending transition is required"):
        cohort.apply_transition_effect(
            spec_dir,
            transition_id="run-current:absent-without-marker",
            pre_transition_sequence=41,
            event="gates-failed",
            args={},
        )

    assert (spec_dir / "state.json").read_bytes() == before


def test_prepare_transition_skips_every_fsm_non_member_before_lock_or_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cohort = _load("loop-cohort.py")
    engine = _load("loop-engine.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    before = (spec_dir / "state.json").read_bytes()
    fsm_events = {
        event
        for table in engine._TRANSITIONS_BY_MODE.values()
        for (_state, event) in table
    }
    non_members = sorted(fsm_events - set(cohort._TRANSITION_EFFECTS))
    assert non_members

    class ExplodingStateLock:
        def exclusive(self, path):  # pragma: no cover - must not be reached
            raise AssertionError(f"unexpected cohort lock for {path}")

    monkeypatch.setattr(cohort, "_statelock", lambda: ExplodingStateLock())

    for index, event in enumerate(non_members, start=1):
        assert cohort.prepare_transition(
            spec_dir,
            transition_id=f"run-current:{index}",
            pre_transition_sequence=index,
            event=event,
            args={},
            opened_at="2026-09-25T00:00:00Z",
        ) == "skipped"
        assert (spec_dir / "state.json").read_bytes() == before

    assert (spec_dir / "state.json").read_bytes() == before


@pytest.mark.parametrize("bad_sequence", [None, True, -1])
def test_prepare_transition_refuses_invalid_pre_transition_sequence_unchanged(
    tmp_path: Path, bad_sequence: object
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    before = (spec_dir / "state.json").read_bytes()

    with pytest.raises(ValueError, match="pre_transition_sequence"):
        cohort.prepare_transition(
            spec_dir,
            transition_id="run-current:bad-sequence",
            pre_transition_sequence=bad_sequence,
            event="gates-failed",
            args={},
            opened_at="2026-09-25T00:00:00Z",
        )

    assert (spec_dir / "state.json").read_bytes() == before


def test_legacy_contract_amendment_derives_sequence_for_apply_and_replay(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    state_path = spec_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["current_wave_index"] = 1
    _write_json(state_path, state)
    evidence = {"T1": ["gates:t1"]}
    amendment_id = cohort._legacy_contract_amendment_id(
        "run-current",
        9,
        "approval:scope-owner",
        "follow-on:owned-record",
        evidence,
    )

    amended = cohort.apply_contract_amendment(
        spec_dir,
        expected_run_id="run-current",
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_evidence=evidence,
        amendment_id=amendment_id,
    )

    assert amended["transition_history"][-1]["transition_id"] == amendment_id
    assert amended["transition_history"][-1]["pre_transition_sequence"] == 9
    assert cohort.contract_amendment_replay_status(
        spec_dir,
        amendment_id=amendment_id,
        owner_authority_ref="approval:scope-owner",
        reason_ref="follow-on:owned-record",
        completed_task_evidence=evidence,
    ) == "applied"


@pytest.mark.parametrize(
    ("amendment_id", "message"),
    [
        ("amendment-not-a-hash", "malformed"),
        ("amendment-" + "0" * 64, "could not be derived"),
    ],
)
def test_legacy_contract_amendment_refuses_bad_or_nonderivable_id_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    amendment_id: str,
    message: str,
) -> None:
    cohort = _load("loop-cohort.py")
    monkeypatch.setattr(cohort, "MAX_LEGACY_AMENDMENT_SEQUENCE_DERIVATION", 3)
    spec_dir = _transition_effect_fixture(tmp_path)
    before = (spec_dir / "state.json").read_bytes()

    with pytest.raises(ValueError, match=message):
        cohort.apply_contract_amendment(
            spec_dir,
            expected_run_id="run-current",
            owner_authority_ref="approval:scope-owner",
            reason_ref="follow-on:owned-record",
            completed_task_evidence={},
            amendment_id=amendment_id,
        )

    assert (spec_dir / "state.json").read_bytes() == before


def test_registered_review_effect_requires_hash_transition_id(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    cohort.prepare_transition(
        spec_dir,
        transition_id="run-current:7",
        pre_transition_sequence=7,
        event="findings-remain",
        args={"fingerprints": ["f" * 64]},
        opened_at="2026-09-25T00:00:00Z",
    )
    prepared = (spec_dir / "state.json").read_bytes()

    with pytest.raises(ValueError, match="SHA-256 transition id"):
        cohort.apply_transition_effect(
            spec_dir,
            transition_id="run-current:7",
            pre_transition_sequence=7,
            event="findings-remain",
            args={"fingerprints": ["f" * 64]},
        )

    assert (spec_dir / "state.json").read_bytes() == prepared


def test_prepare_and_apply_transition_effect_hold_the_cohort_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)
    acquired: list[str] = []

    class FakeStateLock:
        def exclusive(self, path):
            acquired.append(Path(path).name)
            return contextlib.nullcontext()

    monkeypatch.setattr(cohort, "_statelock", lambda: FakeStateLock())

    cohort.prepare_transition(
        spec_dir,
        transition_id="run-current:3",
        pre_transition_sequence=3,
        event="gates-failed",
        args={},
        opened_at="2026-09-25T00:00:00Z",
    )
    cohort.apply_transition_effect(
        spec_dir,
        transition_id="run-current:3",
        pre_transition_sequence=3,
        event="gates-failed",
        args={},
    )

    assert acquired == ["state.json", "state.json"]


def test_prepare_transition_replay_matches_identity_not_opened_at(
    tmp_path: Path,
) -> None:
    cohort = _load("loop-cohort.py")
    spec_dir = _transition_effect_fixture(tmp_path)

    assert cohort.prepare_transition(
        spec_dir,
        transition_id="run-current:3",
        pre_transition_sequence=3,
        event="gates-failed",
        args={"stable": ["fact"]},
        opened_at="2026-09-25T00:00:00Z",
    ) == "prepared"
    before = (spec_dir / "state.json").read_bytes()

    assert cohort.prepare_transition(
        spec_dir,
        transition_id="run-current:3",
        pre_transition_sequence=3,
        event="gates-failed",
        args={"stable": ["fact"]},
        opened_at="2026-09-25T00:00:01Z",
    ) == "prepared"
    assert (spec_dir / "state.json").read_bytes() == before

    with pytest.raises(ValueError, match="pending transition conflicts"):
        cohort.prepare_transition(
            spec_dir,
            transition_id="run-current:3",
            pre_transition_sequence=3,
            event="gates-failed",
            args={"stable": ["different"]},
            opened_at="2026-09-25T00:00:02Z",
        )
    assert (spec_dir / "state.json").read_bytes() == before


def test_transition_effect_source_shape_is_closed_and_shared() -> None:
    source = COHORT_PATH.read_text(encoding="utf-8")

    assert "_TRANSITION_EFFECTS = {" in source
    assert 'event not in _TRANSITION_EFFECTS' in source
    assert "_advance_wave_state(state" in source
    assert "_record_attempt_state(" in source
    assert "_record_review_state(" in source


# STUB: AC-0002 — applied status survives marker clearance
import importlib.util
import json
import sys
from pathlib import Path

COHORT_PATH = (
    Path.cwd()
    / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"
)


def _load_cohort():
    spec = importlib.util.spec_from_file_location("durable_t1_cohort", COHORT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_applied_status_survives_marker_clear(tmp_path: Path) -> None:
    cohort = _load_cohort()
    transition = {
        "transition_id": "transition-7",
        "pre_transition_sequence": 7,
        "event": "gates-failed",
        "args": {},
    }
    state = {
        "schema_version": 2,
        "run_id": "run-current",
        "pending_transition": None,
        "transition_history": [transition],
    }
    (tmp_path / "state.json").write_text(
        json.dumps(state) + "\n", encoding="utf-8"
    )

    assert cohort.transition_replay_status(
        tmp_path,
        transition_id=transition["transition_id"],
        pre_transition_sequence=7,
        event="gates-failed",
        args=transition["args"],
) == "applied"
