#!/usr/bin/env python3
"""Unit/integration tests for loop-engine.py — Phase-1 FSM transitions,
guards, lifecycle walks, and session-resumption state.

Run: python3 test-loop-engine.py
Exit 0 = all pass; exit non-zero = at least one failure.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE = SCRIPT_DIR / "loop-engine.py"
COHORT = SCRIPT_DIR / "loop-cohort.py"
EVALS_JSON = SCRIPT_DIR.parent / "evals" / "evals.json"

failures: list[str] = []
ran = 0


def ok(name: str) -> None:
    global ran
    ran += 1
    print(f"ok   [{name}]")


def fail(name: str, reason: str) -> None:
    global ran
    ran += 1
    failures.append(name)
    print(f"FAIL [{name}]: {reason}", file=sys.stderr)


def run_engine(*args) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(ENGINE)] + [str(a) for a in args],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_cohort(*args) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(COHORT)] + [str(a) for a in args],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ── state helpers ─────────────────────────────────────────────────────────


def make_spec_dir(tmp: Path, name: str) -> Path:
    d = tmp / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_engine_state(spec_dir: Path, state: dict) -> None:
    path = spec_dir / "engine-state.json"
    path.write_text(json.dumps(state, indent=2) + "\n")


def write_cohort_state(spec_dir: Path, state: dict) -> None:
    path = spec_dir / "state.json"
    path.write_text(json.dumps(state, indent=2) + "\n")


def write_spec(spec_dir: Path, status: str = "Draft") -> Path:
    p = spec_dir / "spec.md"
    p.write_text(f"# Spec\n\n- **Status:** {status}\n\n## Acceptance criteria\n\n- [ ] AC1\n")
    return p


def write_plan(spec_dir: Path, content: str | None = None) -> Path:
    p = spec_dir / "plan.md"
    if content is None:
        content = "# Plan\n\n### T1\n\n**Depends on:** none\n\n### T2\n\n**Depends on:** T1\n"
    p.write_text(content)
    return p


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_canonical_plan(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.rstrip() for ln in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    canonical = "\n".join(lines)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def minimal_cohort_state(run_id: str, feature: str, extra: dict | None = None) -> dict:
    base = {
        "schema_version": 1,
        "run_id": run_id,
        "feature": feature,
        "plan_review_status": "pending",
        "approved_spec_hash": None,
        "approved_plan_hash": None,
        "plan_hash": None,
        "schedule_waves": [],
        "current_wave_index": 0,
        "implementation_retry_count": 0,
        "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
        "review_round_count": 0,
        "review_retry_count": 0,
        "max_review_retries": 5,
        "finding_fingerprints": [],
        "previous_finding_fingerprints": [],
        "auto_parallel": False,
        "last_commit_sha": None,
        "worktrees": [],
    }
    if extra:
        base.update(extra)
    return base


def minimal_engine_state(run_id: str, feature: str, mode: str, current_state: str) -> dict:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "feature": feature,
        "mode": mode,
        "state": current_state,
        "last_event": None,
        "last_event_context": None,
        "transition_sequence": 0,
        "last_transition_at": "2026-01-01T00:00:00Z",
    }


def approved_cohort_state(spec_dir: Path, run_id: str, feature: str) -> dict:
    """Cohort state with approved plan/spec hashes, for use with plan-approved guard."""
    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    return minimal_cohort_state(run_id, feature, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": sha256_file(spec_path) if spec_path.exists() else None,
        "approved_plan_hash": sha256_canonical_plan(plan_path) if plan_path.exists() else None,
        "plan_hash": sha256_canonical_plan(plan_path) if plan_path.exists() else None,
    })


def approved_with_schedule_cohort_state(spec_dir: Path, run_id: str, feature: str,
                                         n_waves: int = 3) -> dict:
    """Cohort state with schedule + approved plan, for CODE-* transitions."""
    waves = [[f"T{i + 1}"] for i in range(n_waves)]
    state = approved_cohort_state(spec_dir, run_id, feature)
    state["schedule_waves"] = waves
    state["current_wave_index"] = 0
    return state


# ── T2: init verb ─────────────────────────────────────────────────────────


def test_init_creates_engine_state_code(tmp: Path) -> None:
    name = "init-creates-engine-state-code"
    spec_dir = make_spec_dir(tmp, name)
    rc, out, err = run_engine("init", str(spec_dir), "--mode", "code", "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    path = spec_dir / "engine-state.json"
    if not path.exists():
        fail(name, "engine-state.json not created")
        return
    state = json.loads(path.read_text())
    if state.get("state") != "SPEC-PLAN-DRAFTING":
        fail(name, f"expected SPEC-PLAN-DRAFTING; got {state.get('state')!r}")
    elif state.get("mode") != "code":
        fail(name, f"expected mode=code; got {state.get('mode')!r}")
    elif state.get("schema_version") != 1:
        fail(name, f"expected schema_version=1; got {state.get('schema_version')!r}")
    elif not isinstance(state.get("run_id"), str) or not state["run_id"]:
        fail(name, "run_id must be a non-empty string")
    else:
        ok(name)


def test_init_json_output(tmp: Path) -> None:
    name = "init-json-output"
    spec_dir = make_spec_dir(tmp, name)
    rc, out, err = run_engine("init", str(spec_dir), "--mode", "spec-plan", "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"expected JSON stdout; got {out!r}")
        return
    if "run_id" not in data:
        fail(name, "run_id missing from JSON output")
    elif "feature" not in data:
        fail(name, "feature missing from JSON output")
    elif data.get("mode") != "spec-plan":
        fail(name, f"mode wrong in output: {data.get('mode')!r}")
    else:
        ok(name)


def test_init_refuses_if_engine_state_exists(tmp: Path) -> None:
    name = "init-refuses-if-engine-state-exists"
    spec_dir = make_spec_dir(tmp, name)
    run_id = str(uuid.uuid4())
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING"))
    rc, _, err = run_engine("init", str(spec_dir), "--mode", "code")
    if rc == 0:
        fail(name, "expected non-zero exit when engine-state.json already exists")
    else:
        ok(name)


def test_init_rejects_dotdot_spec_dir(tmp: Path) -> None:
    name = "init-rejects-dotdot"
    spec_dir = tmp / "a" / ".." / "b"
    rc, _, err = run_engine("init", str(spec_dir), "--mode", "code")
    if rc == 0:
        fail(name, "expected non-zero exit for spec-dir with '..'")
    else:
        ok(name)


def test_init_field_set_complete(tmp: Path) -> None:
    name = "init-field-set-complete"
    spec_dir = make_spec_dir(tmp, name)
    run_engine("init", str(spec_dir), "--mode", "code", "--json")
    state = json.loads((spec_dir / "engine-state.json").read_text())
    required = {"schema_version", "run_id", "feature", "mode", "state",
                "last_event", "last_event_context", "transition_sequence",
                "last_transition_at"}
    missing = required - set(state.keys())
    if missing:
        fail(name, f"missing fields: {sorted(missing)}")
    elif state.get("transition_sequence") != 0:
        seq = state.get("transition_sequence")
        fail(name, f"transition_sequence should be 0 at init; got {seq}")
    elif state.get("last_event") is not None:
        fail(name, "last_event should be null at init")
    else:
        ok(name)


# ── T2: reset verb ────────────────────────────────────────────────────────


def test_reset_deletes_engine_state(tmp: Path) -> None:
    name = "reset-deletes-engine-state"
    spec_dir = make_spec_dir(tmp, name)
    run_engine("init", str(spec_dir), "--mode", "code")
    assert (spec_dir / "engine-state.json").exists()
    rc, _, _ = run_engine("reset", str(spec_dir))
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
    elif (spec_dir / "engine-state.json").exists():
        fail(name, "engine-state.json still exists after reset")
    else:
        ok(name)


def test_reset_idempotent(tmp: Path) -> None:
    name = "reset-idempotent"
    spec_dir = make_spec_dir(tmp, name)
    rc1, _, _ = run_engine("reset", str(spec_dir))
    rc2, _, _ = run_engine("reset", str(spec_dir))
    if rc1 != 0 or rc2 != 0:
        fail(name, f"expected both resets to exit 0; got {rc1}, {rc2}")
    else:
        ok(name)


def test_reset_leaves_state_json_intact(tmp: Path) -> None:
    """reset must NOT delete cohort state.json."""
    name = "reset-leaves-state-json"
    spec_dir = make_spec_dir(tmp, name)
    run_id = str(uuid.uuid4())
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    run_engine("init", str(spec_dir), "--mode", "code")
    run_engine("reset", str(spec_dir))
    if not (spec_dir / "state.json").exists():
        fail(name, "reset deleted state.json — must not touch cohort state")
    else:
        ok(name)


# ── T2: status verb ───────────────────────────────────────────────────────


def test_status_absent(tmp: Path) -> None:
    name = "engine-status-absent"
    spec_dir = make_spec_dir(tmp, name)
    rc, _, _ = run_engine("status", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when engine-state.json absent")
    else:
        ok(name)


def test_status_json_after_init(tmp: Path) -> None:
    name = "engine-status-json-after-init"
    spec_dir = make_spec_dir(tmp, name)
    run_engine("init", str(spec_dir), "--mode", "code")
    rc, out, _ = run_engine("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"expected JSON; got {out!r}")
        return
    if "pending_human_wait" not in data:
        fail(name, "pending_human_wait missing from status JSON")
    elif data.get("pending_human_wait") is not False:
        phw = data.get("pending_human_wait")
        fail(name, f"SPEC-PLAN-DRAFTING should not be pending_human_wait; got {phw!r}")
    else:
        ok(name)


def test_status_human_wait_states(tmp: Path) -> None:
    """SPEC-PLAN-HUMAN-GATE and CODE-HUMAN-GATE should show pending_human_wait=True."""
    name = "engine-status-human-wait"
    run_id = str(uuid.uuid4())
    for state_name in ("SPEC-PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"):
        spec_dir = make_spec_dir(tmp, f"{name}-{state_name}")
        write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", state_name))
        rc, out, _ = run_engine("status", str(spec_dir), "--json")
        if rc != 0:
            fail(name, f"status failed for {state_name}")
            return
        data = json.loads(out)
        if not data.get("pending_human_wait"):
            fail(name, f"expected pending_human_wait=True for {state_name}")
            return
    ok(name)


def test_status_is_read_only(tmp: Path) -> None:
    name = "engine-status-read-only"
    spec_dir = make_spec_dir(tmp, name)
    run_engine("init", str(spec_dir), "--mode", "code")
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    run_engine("status", str(spec_dir), "--json")
    after = path.read_bytes()
    if before != after:
        fail(name, "engine-state.json mutated by status")
    else:
        ok(name)


# ── T2: illegal FSM transitions ───────────────────────────────────────────


def _test_illegal_transition(tmp: Path, test_name: str, mode: str,
                              current_state: str, event: str) -> None:
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, test_name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, test_name, mode, current_state))
    # Cohort preflight: supply matching state.json so the failure is FSM-only, not preflight
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, test_name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, err = run_engine("transition", str(spec_dir), event)
    after = path.read_bytes()
    if rc == 0:
        fail(test_name, f"expected non-zero for illegal transition {current_state!r} + {event!r}")
    elif before != after:
        fail(test_name, "engine-state.json mutated on illegal transition")
    else:
        ok(test_name)


def test_illegal_transitions_code(tmp: Path) -> None:
    cases = [
        # wrong mode or wrong state for event
        ("code", "SPEC-PLAN-DRAFTING", "wave-complete"),
        ("code", "SPEC-PLAN-DRAFTING", "gates-clean"),
        ("code", "SPEC-PLAN-DRAFTING", "plan-approved"),   # must first reach HUMAN-GATE
        ("code", "SPEC-PLAN-DRAFTING", "done"),
        ("code", "SPEC-PLAN-REVIEW", "plan-approved"),
        ("code", "SPEC-PLAN-REVIEW", "plan-rejected"),
        ("code", "SPEC-PLAN-REVIEW", "wave-complete"),
        ("code", "SPEC-PLAN-REVIEW", "done"),
        ("code", "SPEC-PLAN-HUMAN-GATE", "wave-complete"),
        ("code", "SPEC-PLAN-HUMAN-GATE", "gates-clean"),
        ("code", "SPEC-PLAN-HUMAN-GATE", "done"),
        ("code", "CODE-IMPLEMENTATION", "plan-approved"),
        ("code", "CODE-IMPLEMENTATION", "gates-clean"),
        ("code", "CODE-IMPLEMENTATION", "done"),
        ("code", "CODE-IMPLEMENTATION", "wave-passed"),  # no wave-index
        ("code", "CODE-VERIFICATION", "plan-approved"),
        ("code", "CODE-VERIFICATION", "done"),
        ("code", "CODE-VERIFICATION", "wave-complete"),
        ("code", "CODE-REVIEW", "wave-complete"),
        ("code", "CODE-REVIEW", "gates-clean"),
        ("code", "CODE-REVIEW", "done"),
        ("code", "CODE-REVIEW", "plan-rejected"),
        ("code", "CODE-HUMAN-GATE", "wave-complete"),
        ("code", "CODE-HUMAN-GATE", "reviewers-clean"),
        ("code", "CODE-HUMAN-GATE", "plan-rejected"),
        ("code", "DONE", "spec-ready"),
        ("code", "DONE", "wave-complete"),
        ("code", "DONE", "done"),
    ]
    for mode, state, event in cases:
        name = f"illegal-{mode}-{state}-{event}"
        _test_illegal_transition(tmp, name, mode, state, event)


def test_illegal_transitions_spec_plan(tmp: Path) -> None:
    cases = [
        ("spec-plan", "SPEC-PLAN-DRAFTING", "plan-approved"),
        ("spec-plan", "SPEC-PLAN-DRAFTING", "wave-complete"),
        ("spec-plan", "SPEC-PLAN-DRAFTING", "done"),
        ("spec-plan", "SPEC-PLAN-REVIEW", "plan-rejected"),
        ("spec-plan", "SPEC-PLAN-REVIEW", "wave-complete"),
        ("spec-plan", "SPEC-PLAN-HUMAN-GATE", "wave-complete"),
        ("spec-plan", "SPEC-PLAN-HUMAN-GATE", "reviewers-clean"),
        ("spec-plan", "DONE", "spec-ready"),
        ("spec-plan", "DONE", "plan-approved"),
    ]
    for mode, state, event in cases:
        name = f"illegal-{mode}-{state}-{event}"
        _test_illegal_transition(tmp, name, mode, state, event)


def test_illegal_mode_in_engine_state(tmp: Path) -> None:
    name = "illegal-unknown-mode"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "unknown-mode", "SPEC-PLAN-DRAFTING")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-ready")
    if rc == 0:
        fail(name, "expected non-zero for unknown mode")
    else:
        ok(name)


# ── T2: wave-index validation ─────────────────────────────────────────────


def test_wave_passed_requires_wave_index(tmp: Path) -> None:
    name = "wave-passed-requires-wave-index"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-VERIFICATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "wave-passed")
    if rc == 0:
        fail(name, "expected non-zero when --wave-index absent for wave-passed")
    elif "wave-index" not in err:
        fail(name, f"expected 'wave-index' in stderr; got {err!r}")
    else:
        ok(name)


def test_non_wave_events_reject_wave_index(tmp: Path) -> None:
    name = "non-wave-events-reject-wave-index"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "spec-ready", "--wave-index", "0")
    if rc == 0:
        fail(name, "expected non-zero when --wave-index supplied for non-wave-passed event")
    elif "wave-index" not in err:
        fail(name, f"expected 'wave-index' in stderr; got {err!r}")
    else:
        ok(name)


# ── T2: run_id preflight ──────────────────────────────────────────────────


def test_run_id_preflight_mismatch_blocks_transition(tmp: Path) -> None:
    """Transition must fail (non-zero) when cohort run_id != engine run_id."""
    name = "run-id-preflight-mismatch"
    engine_run_id = str(uuid.uuid4())
    cohort_run_id = str(uuid.uuid4())
    assert engine_run_id != cohort_run_id
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(
        spec_dir, minimal_engine_state(engine_run_id, name, "code", "SPEC-PLAN-DRAFTING")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(cohort_run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-ready")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch")
    elif before != after:
        fail(name, "engine-state.json mutated despite preflight failure")
    else:
        ok(name)


def test_run_id_preflight_absent_cohort_blocks_transition(tmp: Path) -> None:
    name = "run-id-preflight-absent-cohort"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING"))
    # No state.json — cohort identity will fail
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-ready")
    if rc == 0:
        fail(name, "expected non-zero when cohort state.json absent")
    else:
        ok(name)


# ── T2: legal transitions without specific guards ─────────────────────────
#
# These transitions have no _GUARDS entry (or guards that always pass), so
# we can verify the FSM machinery: next_state, last_event, transition_sequence.


def test_legal_transition_spec_ready(tmp: Path) -> None:
    name = "legal-spec-ready"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-ready")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-REVIEW":
        fail(name, f"expected SPEC-PLAN-REVIEW; got {state.get('state')!r}")
    elif state.get("last_event") != "spec-ready":
        fail(name, f"last_event should be spec-ready; got {state.get('last_event')!r}")
    elif state.get("transition_sequence") != 1:
        fail(name, f"transition_sequence should be 1; got {state.get('transition_sequence')!r}")
    else:
        ok(name)


def test_legal_transition_plan_rejected(tmp: Path) -> None:
    name = "legal-plan-rejected"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-rejected")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-DRAFTING":
        fail(name, f"expected SPEC-PLAN-DRAFTING; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_transition_findings_remain_spec_plan_mode(tmp: Path) -> None:
    name = "legal-findings-remain-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-REVIEW")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, _ = run_engine("transition", str(spec_dir), "findings-remain")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-DRAFTING":
        fail(name, f"expected SPEC-PLAN-DRAFTING; got {state.get('state')!r}")
    else:
        ok(name)


def test_transition_increments_sequence(tmp: Path) -> None:
    name = "transition-sequence-increments"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    engine_s = minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING")
    engine_s["transition_sequence"] = 7
    write_engine_state(spec_dir, engine_s)
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-ready")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("transition_sequence") != 8:
        fail(name, f"expected transition_sequence=8; got {state.get('transition_sequence')}")
    else:
        ok(name)


def test_transition_preserves_run_id_feature_mode(tmp: Path) -> None:
    name = "transition-preserves-identity"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    run_engine("transition", str(spec_dir), "spec-ready")
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("run_id") != run_id:
        fail(name, f"run_id changed after transition; got {state.get('run_id')!r}")
    elif state.get("feature") != name:
        fail(name, f"feature changed after transition; got {state.get('feature')!r}")
    elif state.get("mode") != "code":
        fail(name, f"mode changed after transition; got {state.get('mode')!r}")
    else:
        ok(name)


def test_blocker_applied_code_human_gate(tmp: Path) -> None:
    name = "legal-blocker-applied"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # CODE-HUMAN-GATE → blocker-applied → CODE-IMPLEMENTATION
    # Pre-guard (schedule check-current) needs: plan_hash matches plan.md, schedule non-empty
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"], ["T2"]],
        "current_wave_index": 0,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "blocker-applied")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected CODE-IMPLEMENTATION; got {state.get('state')!r}")
    else:
        ok(name)


# ── T2: legal transitions with guards ────────────────────────────────────
#
# These tests exercise the full guard stack. They require correctly shaped
# cohort state so guards pass. A guard failure is captured as a test failure.


def test_legal_plan_approved_spec_plan_mode(tmp: Path) -> None:
    """spec-plan plan-approved → DONE; guard = plan check-current (no --require-schedule)."""
    name = "legal-plan-approved-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, approved_cohort_state(spec_dir, run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "DONE":
        fail(name, f"expected DONE; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_reviewers_clean_spec_plan(tmp: Path) -> None:
    """SPEC-PLAN-REVIEW → reviewers-clean → SPEC-PLAN-HUMAN-GATE (no guard in spec-plan mode)."""
    name = "legal-reviewers-clean-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-REVIEW")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc != 0:
        fail(name, f"expected exit 0 with Status: Shipped; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-HUMAN-GATE":
        fail(name, f"expected SPEC-PLAN-HUMAN-GATE; got {state.get('state')!r}")
    else:
        ok(name)


def test_guard_check_spec_status_fails_non_shipped(tmp: Path) -> None:
    """reviewers-clean guard fires on CODE-REVIEW → CODE-HUMAN-GATE when Status != 'Shipped'.

    The guard is scoped to CODE-REVIEW (not SPEC-PLAN-REVIEW) so it does not
    require Status: Shipped before G-plan sign-off.
    """
    name = "guard-check-spec-status-non-shipped"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-REVIEW"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc == 0:
        fail(name, "expected non-zero when spec.md Status != Shipped (CODE-REVIEW source)")
    else:
        ok(name)


def test_legal_wave_complete_to_code_verification(tmp: Path) -> None:
    """CODE-IMPLEMENTATION → wave-complete → CODE-VERIFICATION.

    Requires: schedule check-current (pre-guard) + check --phase implement (guard).
    """
    name = "legal-wave-complete"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-IMPLEMENTATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"], ["T2"]],
        "current_wave_index": 0,
        "implementation_retry_count": 0,
        "max_implementation_retries": 5,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "wave-complete")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-VERIFICATION":
        fail(name, f"expected CODE-VERIFICATION; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_gates_clean_to_code_review(tmp: Path) -> None:
    """CODE-VERIFICATION → gates-clean → CODE-REVIEW.

    Requires: schedule check-current (pre-guard) + wave check --expect last (guard).
    At the last wave (current_wave_index == len-1).
    """
    name = "legal-gates-clean"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    waves = [["T1"], ["T2"]]
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-VERIFICATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": waves,
        "current_wave_index": len(waves) - 1,  # at last wave
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "gates-clean")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-REVIEW":
        fail(name, f"expected CODE-REVIEW; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_wave_passed_to_code_implementation(tmp: Path) -> None:
    """CODE-VERIFICATION → wave-passed → CODE-IMPLEMENTATION.

    Requires: schedule check-current (pre-guard) + wave check --expect more (guard).
    last_event_context must carry completed_wave_index.
    """
    name = "legal-wave-passed"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    waves = [["T1"], ["T2"], ["T3"]]
    # At wave 0, more waves remain → wave-passed --wave-index 0 should succeed
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-VERIFICATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": waves,
        "current_wave_index": 0,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected CODE-IMPLEMENTATION; got {state.get('state')!r}")
    elif state.get("last_event_context") != {"completed_wave_index": 0}:
        lec = state.get("last_event_context")
        fail(name, f"expected last_event_context={{completed_wave_index: 0}}; got {lec!r}")
    else:
        ok(name)


def test_legal_gates_failed_to_code_implementation(tmp: Path) -> None:
    """CODE-VERIFICATION → gates-failed → CODE-IMPLEMENTATION.

    Requires: schedule check-current (pre-guard) + check --phase gates-failed (guard).
    """
    name = "legal-gates-failed"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-VERIFICATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
        "implementation_retry_count": 0,
        "max_implementation_retries": 5,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "gates-failed")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected CODE-IMPLEMENTATION; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_findings_remain_code_mode(tmp: Path) -> None:
    """CODE-REVIEW → findings-remain → CODE-IMPLEMENTATION.

    Requires: schedule check-current (pre-guard) + check --phase review (guard).
    """
    name = "legal-findings-remain-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-REVIEW"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
        "review_retry_count": 0,
        "max_review_retries": 5,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "findings-remain")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected CODE-IMPLEMENTATION; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_reviewers_clean_code_to_human_gate(tmp: Path) -> None:
    """CODE-REVIEW → reviewers-clean → CODE-HUMAN-GATE.

    Requires: schedule check-current (pre-guard) + check-spec-status (guard).
    """
    name = "legal-reviewers-clean-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Shipped")
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-REVIEW"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc != 0:
        fail(name, f"expected exit 0 with Status: Shipped; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-HUMAN-GATE":
        fail(name, f"expected CODE-HUMAN-GATE; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_done_from_code_human_gate(tmp: Path) -> None:
    """CODE-HUMAN-GATE → done → DONE. No pre-guard (done is exempt)."""
    name = "legal-done-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # done is exempt from schedule pre-guard, and no specific guard for "done"
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "done")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "DONE":
        fail(name, f"expected DONE; got {state.get('state')!r}")
    else:
        ok(name)


# ── T2: guard firing verification ────────────────────────────────────────


def test_guard_plan_check_current_fires_for_spec_plan_mode(tmp: Path) -> None:
    """plan-approved in spec-plan mode fires plan check-current (no --require-schedule).
    Verify by setting approved hashes then changing plan.md → guard must fail."""
    name = "guard-plan-check-current-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    cohort = approved_cohort_state(spec_dir, run_id, name)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-HUMAN-GATE")
    )
    # Change plan.md AFTER computing approved hash → guard detects mismatch
    (spec_dir / "plan.md").write_text("# Plan (modified)\n")
    write_cohort_state(spec_dir, cohort)
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected guard to fail when plan.md changes after approve")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_guard_plan_check_current_require_schedule_fires_for_code_mode(tmp: Path) -> None:
    """plan-approved in code mode fires plan check-current --require-schedule.
    Verify by omitting schedule → guard must fail."""
    name = "guard-plan-check-current-require-schedule"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    # Approved but no schedule_waves → --require-schedule fails
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, approved_cohort_state(spec_dir, run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected guard to fail with no schedule (--require-schedule)")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_guard_gates_failed_at_cap_blocks_transition(tmp: Path) -> None:
    """CODE-VERIFICATION gates-failed guard fails when at implementation retry cap."""
    name = "guard-gates-failed-at-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-VERIFICATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
        "implementation_retry_count": 5,  # at cap
        "max_implementation_retries": 5,
    }))
    rc, _, _ = run_engine("transition", str(spec_dir), "gates-failed")
    if rc == 0:
        fail(name, "expected non-zero when implementation_retry_count == max")
    else:
        ok(name)


def test_guard_review_at_cap_blocks_findings_remain(tmp: Path) -> None:
    """CODE-REVIEW findings-remain guard fails when at review retry cap."""
    name = "guard-review-at-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-REVIEW"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
        "review_retry_count": 5,  # at cap
        "max_review_retries": 5,
    }))
    rc, _, _ = run_engine("transition", str(spec_dir), "findings-remain")
    if rc == 0:
        fail(name, "expected non-zero when review_retry_count == max")
    else:
        ok(name)


def test_schedule_precheck_blocks_code_implementation_transition(tmp: Path) -> None:
    """All CODE-* transitions (except done) require schedule check-current.
    When plan.md is mutated after schedule, the pre-guard blocks the transition."""
    name = "schedule-precheck-blocks-code-impl"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    plan_path = spec_dir / "plan.md"
    plan_path.write_text("# Plan\n\n### T1\n\n**Depends on:** none\n")
    spec_hash = sha256_file(spec_dir / "spec.md")
    plan_hash = sha256_canonical_plan(plan_path)

    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-IMPLEMENTATION"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,          # matches current plan.md
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
        "implementation_retry_count": 0,
        "max_implementation_retries": 5,
    }))

    # Now mutate plan.md AFTER recording plan_hash in cohort state
    plan_path.write_text("# Plan (tampered)\n\n### TX\n\n**Depends on:** none\n")

    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "wave-complete")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when plan.md differs from scheduled plan_hash")
    elif before != after:
        fail(name, "engine-state.json mutated despite schedule check-current failure")
    else:
        ok(name)


def test_done_exempt_from_schedule_precheck(tmp: Path) -> None:
    """done event from CODE-HUMAN-GATE must NOT require schedule check-current."""
    name = "done-exempt-from-schedule-precheck"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # No plan.md, no schedule — done must still succeed
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "done")
    if rc != 0:
        fail(name, f"expected exit 0 for done (exempt from schedule); got {rc}: {err.strip()}")
    else:
        ok(name)


# ── T2: atomic write guarantee ────────────────────────────────────────────


def test_transition_no_tmp_file_left_on_success(tmp: Path) -> None:
    """After a successful transition, no .engine-state-*.json.tmp files remain."""
    name = "no-tmp-file-after-success"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    run_engine("transition", str(spec_dir), "spec-ready")
    tmp_files = list(spec_dir.glob(".engine-state-*.json.tmp"))
    if tmp_files:
        fail(name, f"temp files left after transition: {tmp_files}")
    else:
        ok(name)


# ── T2: schema version forward guard ─────────────────────────────────────


def test_schema_version_forward_guard(tmp: Path) -> None:
    """Transition must refuse engine-state.json with unknown schema_version."""
    name = "schema-version-forward-guard"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    engine_s = minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING")
    engine_s["schema_version"] = 99
    write_engine_state(spec_dir, engine_s)
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-ready")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for unknown schema_version")
    elif before != after:
        fail(name, "engine-state.json mutated despite schema_version guard")
    else:
        ok(name)


# ── T4: check-spec-status.py ─────────────────────────────────────────────


CHECK_SPEC_STATUS = SCRIPT_DIR / "check-spec-status.py"


def run_check_spec_status(*args) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(CHECK_SPEC_STATUS)] + [str(a) for a in args],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_check_spec_status_shipped(tmp: Path) -> None:
    name = "check-spec-status-shipped"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Shipped\n\n## Acceptance criteria\n\n- [x] AC1\n"
    )
    rc, out, _ = run_check_spec_status(str(spec_dir))
    if rc != 0:
        fail(name, f"expected exit 0 for Status: Shipped; got {rc}")
    elif "Shipped" not in out:
        fail(name, f"expected 'Shipped' in stdout; got {out!r}")
    else:
        ok(name)


def test_check_spec_status_draft_fails(tmp: Path) -> None:
    name = "check-spec-status-draft-fails"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Draft\n\n## Acceptance criteria\n\n- [ ] AC1\n"
    )
    rc, _, err = run_check_spec_status(str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero for Status: Draft")
    elif "Draft" not in err:
        fail(name, f"expected 'Draft' in stderr; got {err!r}")
    else:
        ok(name)


def test_check_spec_status_absent_spec(tmp: Path) -> None:
    name = "check-spec-status-absent-spec"
    spec_dir = make_spec_dir(tmp, name)
    rc, _, err = run_check_spec_status(str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when spec.md absent")
    else:
        ok(name)


def test_check_spec_status_no_status_line(tmp: Path) -> None:
    name = "check-spec-status-no-status-line"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text("# Spec\n\nNo status line here.\n")
    rc, _, err = run_check_spec_status(str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when no **Status:** line")
    else:
        ok(name)


def test_check_spec_status_no_args(tmp: Path) -> None:
    name = "check-spec-status-no-args"
    rc, _, err = run_check_spec_status()
    if rc == 0:
        fail(name, "expected non-zero when no spec-dir given")
    else:
        ok(name)


# ── full mode: spec-plan FSM walk ─────────────────────────────────────────
#
# Full transition chain for spec-plan mode without any guard bypasses.


def test_spec_plan_full_walk(tmp: Path) -> None:
    """Walk all five spec-plan transitions to DONE under realistic guard conditions."""
    name = "spec-plan-full-walk"
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)

    # 1. Init pair
    rc, out, err = run_engine("init", str(spec_dir), "--mode", "spec-plan", "--json")
    if rc != 0:
        fail(name, f"engine init failed: {err.strip()}")
        return
    eng_run_id = json.loads(out)["run_id"]
    run_cohort("init", str(spec_dir), "--run-id", eng_run_id)

    # 2. spec-ready (no guard)
    rc, _, err = run_engine("transition", str(spec_dir), "spec-ready")
    if rc != 0:
        fail(name, f"spec-ready failed: {err.strip()}")
        return

    # 3. findings-remain (no guard in spec-plan mode)
    rc, _, err = run_engine("transition", str(spec_dir), "findings-remain")
    if rc != 0:
        fail(name, f"findings-remain failed: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state["state"] != "SPEC-PLAN-DRAFTING":
        fail(name, f"expected back to DRAFTING; got {state['state']!r}")
        return

    # 4. spec-ready again, then reviewers-clean (no status guard at SPEC-PLAN-REVIEW)
    run_engine("transition", str(spec_dir), "spec-ready")
    rc, _, err = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc != 0:
        fail(name, f"reviewers-clean failed: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state["state"] != "SPEC-PLAN-HUMAN-GATE":
        fail(name, f"expected SPEC-PLAN-HUMAN-GATE; got {state['state']!r}")
        return

    # 5. plan-rejected → back to DRAFTING
    rc, _, err = run_engine("transition", str(spec_dir), "plan-rejected")
    if rc != 0:
        fail(name, f"plan-rejected failed: {err.strip()}")
        return

    # 6. spec-ready + reviewers-clean + plan-approved → DONE
    #    Human writes Status: Approved before approve-plan (spec-plan terminal is Approved)
    run_engine("transition", str(spec_dir), "spec-ready")
    run_engine("transition", str(spec_dir), "reviewers-clean")
    write_spec(spec_dir, status="Approved")

    # For plan-approved: need approved cohort state
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", eng_run_id)
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"plan-approved failed: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state["state"] != "DONE":
        fail(name, f"expected DONE; got {state['state']!r}")
        return
    spec_text = (spec_dir / "spec.md").read_text(encoding="utf-8")
    if "**Status:** Approved" not in spec_text:
        fail(name, "spec-plan terminal: expected Status: Approved at DONE")
    else:
        ok(name)


# ── evals.json shape assertion ────────────────────────────────────────────


def test_evals_json_shape(_tmp: Path) -> None:
    """evals.json exists, is valid JSON, has skill_name='work-loop' and 6 entries."""
    name = "evals-json-shape"
    if not EVALS_JSON.exists():
        fail(name, f"evals.json not found at {EVALS_JSON}")
        return
    try:
        data = json.loads(EVALS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(name, f"evals.json is not valid JSON: {exc}")
        return
    if data.get("skill_name") != "work-loop":
        fail(name, f"expected skill_name='work-loop'; got {data.get('skill_name')!r}")
        return
    evals = data.get("evals")
    if not isinstance(evals, list) or len(evals) != 6:
        count = len(evals) if isinstance(evals, list) else repr(evals)
        fail(name, f"expected 6 evals entries; got {count}")
        return
    required_fields = {"id", "prompt", "expected_output", "assertions"}
    for entry in evals:
        missing = required_fields - set(entry.keys())
        if missing:
            fail(name, f"entry {entry.get('id')!r} missing fields: {sorted(missing)}")
            return
    ok(name)


# ── Crash-window tests: session-resumption and idempotency coverage ─────────


def make_crash_window_run(tmp: Path, feature: str) -> tuple[Path, str, int]:
    """Drive a fresh ≥2-wave run to CODE-VERIFICATION via real CLI.

    Returns (spec_dir, run_id, transition_sequence).
    The ≥2-wave plan is required so wave advance --from-index 0 is legal
    (from-index must be < len - 1 on a single-wave schedule).
    """
    spec_dir = make_spec_dir(tmp, feature)
    write_spec(spec_dir, status="Draft")
    # Two-task plan → schedule_waves [["T1"], ["T2"]] (≥2 waves required)
    write_plan(spec_dir)

    rc, out, err = run_engine("init", str(spec_dir), "--mode", "code", "--json")
    if rc != 0:
        raise RuntimeError(f"make_crash_window_run: engine init failed: {err}")
    run_id = json.loads(out)["run_id"]

    run_cohort("init", str(spec_dir), "--run-id", run_id)
    run_engine("transition", str(spec_dir), "spec-ready")
    run_engine("transition", str(spec_dir), "reviewers-clean")
    write_spec(spec_dir, status="Approved")
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    run_engine("transition", str(spec_dir), "plan-approved")
    # wave-complete: CODE-IMPLEMENTATION → CODE-VERIFICATION (wave 0 done)
    rc_wc, _, err_wc = run_engine("transition", str(spec_dir), "wave-complete")
    if rc_wc != 0:
        raise RuntimeError(f"make_crash_window_run: wave-complete failed: {err_wc}")

    eng = json.loads((spec_dir / "engine-state.json").read_text())
    return spec_dir, run_id, eng["transition_sequence"]


def make_code_review_run(tmp: Path, feature: str) -> tuple[Path, str]:
    """Drive a fresh 1-wave run to CODE-REVIEW via real CLI.

    Returns (spec_dir, run_id).
    Single-wave plan means wave 0 is the last wave, allowing gates-clean
    (not wave-passed) to exit CODE-VERIFICATION → CODE-REVIEW.
    """
    spec_dir = make_spec_dir(tmp, feature)
    write_spec(spec_dir, status="Draft")
    # One-task plan → schedule_waves [["T1"]] (single last wave)
    write_plan(spec_dir, content="# Plan\n\n### T1\n\n**Depends on:** none\n")

    rc, out, err = run_engine("init", str(spec_dir), "--mode", "code", "--json")
    if rc != 0:
        raise RuntimeError(f"make_code_review_run: engine init failed: {err}")
    run_id = json.loads(out)["run_id"]

    run_cohort("init", str(spec_dir), "--run-id", run_id)
    run_engine("transition", str(spec_dir), "spec-ready")
    run_engine("transition", str(spec_dir), "reviewers-clean")
    write_spec(spec_dir, status="Approved")
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    run_engine("transition", str(spec_dir), "plan-approved")
    run_engine("transition", str(spec_dir), "wave-complete")
    # gates-clean: CODE-VERIFICATION → CODE-REVIEW (at last wave)
    rc_gc, _, err_gc = run_engine("transition", str(spec_dir), "gates-clean")
    if rc_gc != 0:
        raise RuntimeError(f"make_code_review_run: gates-clean failed: {err_gc}")

    return spec_dir, run_id


def _read_cohort_state(spec_dir: Path) -> dict:
    return json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))


_write_cohort_state = write_cohort_state  # same contract; named for crash-window tests


def _setup_retry_boundary_run(tmp: Path, feature: str) -> tuple[Path, str, int]:
    """Same as make_crash_window_run; alias clarifying CODE-VERIFICATION start state."""
    return make_crash_window_run(tmp, feature)


# ── T1: no-chat-history status recovery ───────────────────────────────────


def test_no_chat_history_status_read_via_cli(tmp: Path) -> None:
    """engine status --json is readable via subprocess; key fields present."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-status")
    rc, out, _ = run_engine("status", str(spec_dir), "--json")
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail("no-chat-history-status-read-via-cli",
             f"engine status --json not parseable: {out!r}")
        return
    if rc != 0 or "last_event" not in data or "run_id" not in data:
        fail("no-chat-history-status-read-via-cli",
             f"rc={rc} or missing fields; got keys {list(data.keys())}")
    else:
        ok("no-chat-history-status-read-via-cli")


def test_no_chat_history_identity_verify_via_cli(tmp: Path) -> None:
    """cohort identity --expect-run-id verifies pairing via subprocess."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-identity")
    rc, out, err = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail("no-chat-history-identity-verify-via-cli",
             f"identity returned rc={rc}: {err.strip()!r}")
    else:
        ok("no-chat-history-identity-verify-via-cli")


def test_no_chat_history_route_wave_passed_via_cli(tmp: Path) -> None:
    """reads last_event=wave-passed via CLI and routes wave advance correctly."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-wave")
    # Crash: fire real wave-passed; stop before advance
    run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    # Fresh-process read sequence
    rc_s, out_s, _ = run_engine("status", str(spec_dir), "--json")
    if rc_s != 0:
        fail("no-chat-history-route-wave-passed-via-cli",
             f"engine status failed rc={rc_s}")
        return
    eng = json.loads(out_s)
    rc_i, _, err_i = run_cohort("identity", str(spec_dir), "--expect-run-id", eng["run_id"])
    if rc_i != 0:
        fail("no-chat-history-route-wave-passed-via-cli",
             f"identity failed rc={rc_i}: {err_i.strip()!r}")
        return
    rc_c, out_c, _ = run_cohort("status", str(spec_dir), "--json")
    if rc_c != 0:
        fail("no-chat-history-route-wave-passed-via-cli",
             f"cohort status failed rc={rc_c}")
        return
    n = eng["last_event_context"]["completed_wave_index"]
    rc_a, _, err_a = run_cohort(
        "wave", "advance", str(spec_dir),
        "--from-index", str(n), "--expect-run-id", eng["run_id"],
    )
    if rc_a != 0:
        fail("no-chat-history-route-wave-passed-via-cli",
             f"wave advance failed rc={rc_a}: {err_a.strip()!r}")
        return
    rc_c2, out_c2, _ = run_cohort("status", str(spec_dir), "--json")
    if rc_c2 != 0:
        fail("no-chat-history-route-wave-passed-via-cli",
             f"post-advance cohort status failed rc={rc_c2}")
        return
    coh2 = json.loads(out_c2)
    if eng["last_event"] != "wave-passed" or coh2["current_wave_index"] != n + 1:
        fail("no-chat-history-route-wave-passed-via-cli",
             f"last_event={eng['last_event']!r} idx={coh2.get('current_wave_index')}")
    else:
        ok("no-chat-history-route-wave-passed-via-cli")


def test_no_chat_history_route_gates_failed_via_cli(tmp: Path) -> None:
    """reads last_event=gates-failed via CLI and routes record-attempt correctly."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-gf")
    # Crash: fire real gates-failed; stop before record-attempt
    run_engine("transition", str(spec_dir), "gates-failed")
    rc_s, out_s, _ = run_engine("status", str(spec_dir), "--json")
    if rc_s != 0:
        fail("no-chat-history-route-gates-failed-via-cli",
             f"engine status failed rc={rc_s}")
        return
    eng = json.loads(out_s)
    rc_i, _, err_i = run_cohort("identity", str(spec_dir), "--expect-run-id", eng["run_id"])
    if rc_i != 0:
        fail("no-chat-history-route-gates-failed-via-cli",
             f"identity failed rc={rc_i}: {err_i.strip()!r}")
        return
    rc_c, out_c, _ = run_cohort("status", str(spec_dir), "--json")
    if rc_c != 0:
        fail("no-chat-history-route-gates-failed-via-cli",
             f"cohort status failed rc={rc_c}")
        return
    coh_before = json.loads(out_c)
    cycle_id = f"{eng['run_id']}:{eng['transition_sequence']}"
    rc_r, _, err_r = run_cohort(
        "record-attempt", str(spec_dir),
        "--phase", "implement",
        "--cycle-id", cycle_id,
        "--expect-run-id", eng["run_id"],
    )
    if rc_r != 0:
        fail("no-chat-history-route-gates-failed-via-cli",
             f"record-attempt failed rc={rc_r}: {err_r.strip()!r}")
        return
    rc_c2, out_c2, _ = run_cohort("status", str(spec_dir), "--json")
    if rc_c2 != 0:
        fail("no-chat-history-route-gates-failed-via-cli",
             f"post-record cohort status failed rc={rc_c2}")
        return
    coh_after = json.loads(out_c2)
    if (eng["last_event"] != "gates-failed"
            or coh_after["implementation_retry_count"]
               != coh_before["implementation_retry_count"] + 1):
        fail("no-chat-history-route-gates-failed-via-cli",
             f"last_event={eng['last_event']!r} count "
             f"{coh_before['implementation_retry_count']}"
             f"→{coh_after.get('implementation_retry_count')}")
    else:
        ok("no-chat-history-route-gates-failed-via-cli")


# ── T2: wave-passed crash windows and refusals ────────────────────────────


def test_wave_passed_window_a_advance_before_crash(tmp: Path) -> None:
    """window A — crash before advance; advance succeeds and increments once."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-a")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    if rc_t != 0:
        fail("wave-passed-window-a",
             f"wave-passed transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    before = _read_cohort_state(spec_dir)
    if before["current_wave_index"] != 0:
        fail("wave-passed-window-a",
             f"pre-condition: current_wave_index={before['current_wave_index']} != 0")
        return
    rc, _, err = run_cohort(
        "wave", "advance", str(spec_dir),
        "--from-index", "0", "--expect-run-id", run_id,
    )
    after = _read_cohort_state(spec_dir)
    if rc != 0 or after["current_wave_index"] != 1:
        fail("wave-passed-window-a",
             f"rc={rc} idx={after.get('current_wave_index')} err={err.strip()!r}")
    else:
        ok("wave-passed-window-a")


def test_wave_passed_window_b_advance_after_crash(tmp: Path) -> None:
    """window B — crash after advance; replay is idempotent no-op."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-b")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    if rc_t != 0:
        fail("wave-passed-window-b",
             f"wave-passed transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    # Advance already applied (crash happens after this)
    run_cohort("wave", "advance", str(spec_dir),
               "--from-index", "0", "--expect-run-id", run_id)
    before_json = (spec_dir / "state.json").read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir),
        "--from-index", "0", "--expect-run-id", run_id,
    )
    after_json = (spec_dir / "state.json").read_bytes()
    if rc != 0 or before_json != after_json:
        fail("wave-passed-window-b",
             f"rc={rc} state_mutated={before_json != after_json}")
    else:
        ok("wave-passed-window-b")


def test_wave_passed_wrong_from_index_refused(tmp: Path) -> None:
    """wrong --from-index exits non-zero; both state files unchanged; run IDs paired."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-wfi")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    if rc_t != 0:
        fail("wave-passed-wrong-from-index-refused",
             f"wave-passed transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    before_coh = (spec_dir / "state.json").read_bytes()
    before_eng = (spec_dir / "engine-state.json").read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir),
        "--from-index", "99", "--expect-run-id", run_id,
    )
    after_coh = (spec_dir / "state.json").read_bytes()
    after_eng = (spec_dir / "engine-state.json").read_bytes()
    rc_pair, _, _ = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    if rc == 0 or before_coh != after_coh or before_eng != after_eng or rc_pair != 0:
        fail("wave-passed-wrong-from-index-refused",
             f"rc={rc} coh_mutated={before_coh != after_coh} "
             f"eng_mutated={before_eng != after_eng} pair_rc={rc_pair}")
    else:
        ok("wave-passed-wrong-from-index-refused")


def test_wave_passed_wrong_run_id_refused(tmp: Path) -> None:
    """wrong --expect-run-id exits non-zero; both state files unchanged; run IDs paired."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-wri")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    if rc_t != 0:
        fail("wave-passed-wrong-run-id-refused",
             f"wave-passed transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    before_coh = (spec_dir / "state.json").read_bytes()
    before_eng = (spec_dir / "engine-state.json").read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir),
        "--from-index", "0",
        "--expect-run-id", "00000000-0000-0000-0000-000000000000",
    )
    after_coh = (spec_dir / "state.json").read_bytes()
    after_eng = (spec_dir / "engine-state.json").read_bytes()
    rc_pair, _, _ = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    if rc == 0 or before_coh != after_coh or before_eng != after_eng or rc_pair != 0:
        fail("wave-passed-wrong-run-id-refused",
             f"rc={rc} coh_mutated={before_coh != after_coh} "
             f"eng_mutated={before_eng != after_eng} pair_rc={rc_pair}")
    else:
        ok("wave-passed-wrong-run-id-refused")


def test_wave_passed_run_ids_remain_paired_after_advance(tmp: Path) -> None:
    """engine and cohort run_ids remain paired after crash recovery."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-pair")
    run_engine("transition", str(spec_dir), "wave-passed", "--wave-index", "0")
    run_cohort("wave", "advance", str(spec_dir),
               "--from-index", "0", "--expect-run-id", run_id)
    rc, out, err = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail("wave-passed-run-ids-paired",
             f"identity failed after advance: rc={rc} {err.strip()!r}")
    else:
        ok("wave-passed-run-ids-paired")


# ── T3: gates-failed crash windows and retry boundary ────────────────────


def test_gates_failed_window_a_record_before_crash(tmp: Path) -> None:
    """window A — crash before record-attempt; count increments exactly once."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "gf-a")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "gates-failed")
    if rc_t != 0:
        fail("gates-failed-window-a",
             f"gates-failed transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    before = _read_cohort_state(spec_dir)
    eng = json.loads(run_engine("status", str(spec_dir), "--json")[1])
    cycle_id = f"{run_id}:{eng['transition_sequence']}"
    rc, _, err = run_cohort(
        "record-attempt", str(spec_dir),
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id,
    )
    after = _read_cohort_state(spec_dir)
    if rc != 0 or after["implementation_retry_count"] != before["implementation_retry_count"] + 1:
        fail("gates-failed-window-a",
             f"rc={rc} count {before['implementation_retry_count']}"
             f"→{after.get('implementation_retry_count')} {err.strip()!r}")
    else:
        ok("gates-failed-window-a")


def test_gates_failed_window_b_record_after_crash(tmp: Path) -> None:
    """window B — cycle_id already recorded; replay is no-op."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "gf-b")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "gates-failed")
    if rc_t != 0:
        fail("gates-failed-window-b",
             f"gates-failed transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    eng = json.loads(run_engine("status", str(spec_dir), "--json")[1])
    cycle_id = f"{run_id}:{eng['transition_sequence']}"
    # First call (crash happens after this)
    run_cohort(
        "record-attempt", str(spec_dir),
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id,
    )
    before_2 = (spec_dir / "state.json").read_bytes()
    rc2, _, err2 = run_cohort(
        "record-attempt", str(spec_dir),
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id,
    )
    after_2 = (spec_dir / "state.json").read_bytes()
    if rc2 != 0 or before_2 != after_2:
        fail("gates-failed-window-b",
             f"rc2={rc2} state_mutated={before_2 != after_2} {err2.strip()!r}")
    else:
        ok("gates-failed-window-b")


def test_gates_failed_wrong_run_id_prefix_refused(tmp: Path) -> None:
    """cycle_id with wrong run_id prefix exits non-zero; state unchanged."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "gf-wri")
    run_engine("transition", str(spec_dir), "gates-failed")
    eng = json.loads(run_engine("status", str(spec_dir), "--json")[1])
    bad_cycle = f"00000000-0000-0000-0000-000000000000:{eng['transition_sequence']}"
    before = (spec_dir / "state.json").read_bytes()
    rc, _, _ = run_cohort(
        "record-attempt", str(spec_dir),
        "--phase", "implement", "--cycle-id", bad_cycle, "--expect-run-id", run_id,
    )
    after = (spec_dir / "state.json").read_bytes()
    if rc == 0 or before != after:
        fail("gates-failed-wrong-run-id-prefix",
             f"rc={rc} state_mutated={before != after}")
    else:
        ok("gates-failed-wrong-run-id-prefix")


def test_gates_failed_fifth_retry_permitted(tmp: Path) -> None:
    """fifth repair cycle permitted; implementation_retry_count reaches 5."""
    spec_dir, run_id, _ = _setup_retry_boundary_run(tmp, "gf-5th")
    st = _read_cohort_state(spec_dir)
    st["implementation_retry_count"] = 4
    _write_cohort_state(spec_dir, st)
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "gates-failed")
    eng = json.loads(run_engine("status", str(spec_dir), "--json")[1])
    cycle_id = f"{run_id}:{eng['transition_sequence']}"
    rc_r, _, err_r = run_cohort(
        "record-attempt", str(spec_dir),
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id,
    )
    after = _read_cohort_state(spec_dir)
    if rc_t != 0 or rc_r != 0 or after["implementation_retry_count"] != 5:
        fail("gates-failed-fifth-permitted",
             f"rc_t={rc_t} rc_r={rc_r} count={after.get('implementation_retry_count')} "
             f"t_err={err_t.strip()!r} r_err={err_r.strip()!r}")
    else:
        ok("gates-failed-fifth-permitted")


def test_gates_failed_sixth_retry_refused(tmp: Path) -> None:
    """sixth gates-failed transition refused; both state files unchanged."""
    spec_dir, run_id, _ = _setup_retry_boundary_run(tmp, "gf-6th")
    st = _read_cohort_state(spec_dir)
    st["implementation_retry_count"] = 5
    _write_cohort_state(spec_dir, st)
    before_eng = (spec_dir / "engine-state.json").read_bytes()
    before_coh = (spec_dir / "state.json").read_bytes()
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "gates-failed")
    after_eng = (spec_dir / "engine-state.json").read_bytes()
    after_coh = (spec_dir / "state.json").read_bytes()
    after_st = _read_cohort_state(spec_dir)
    if (rc_t == 0 or before_eng != after_eng or before_coh != after_coh
            or after_st["implementation_retry_count"] != 5):
        fail("gates-failed-sixth-refused",
             f"rc_t={rc_t} eng_mutated={before_eng != after_eng} "
             f"coh_mutated={before_coh != after_coh} "
             f"count={after_st.get('implementation_retry_count')} "
             f"err={err_t.strip()!r}")
    else:
        ok("gates-failed-sixth-refused")


# ── T4: review-window limitation tests and SKILL.md prose ─────────────────


def test_findings_remain_phase_recoverable_from_engine(tmp: Path) -> None:
    """last_event=findings-remain readable from engine status --json."""
    spec_dir, run_id = make_code_review_run(tmp, "fr-phase")
    run_engine("transition", str(spec_dir), "findings-remain")
    rc, out, _ = run_engine("status", str(spec_dir), "--json")
    try:
        eng = json.loads(out)
    except json.JSONDecodeError:
        fail("findings-remain-phase-recoverable", f"status not JSON: {out!r}")
        return
    if rc != 0 or eng.get("last_event") != "findings-remain":
        fail("findings-remain-phase-recoverable",
             f"rc={rc} last_event={eng.get('last_event')!r}")
    else:
        ok("findings-remain-phase-recoverable")


def test_findings_remain_no_auto_replay(tmp: Path) -> None:
    """cohort state unchanged after recovery reads; reads must succeed."""
    spec_dir, run_id = make_code_review_run(tmp, "fr-noreplay")
    run_engine("transition", str(spec_dir), "findings-remain")
    before = (spec_dir / "state.json").read_bytes()
    # Full documented read sequence
    rc_s, _, _ = run_engine("status", str(spec_dir), "--json")
    rc_i, _, _ = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    rc_c, _, _ = run_cohort("status", str(spec_dir), "--json")
    # Deliberately do NOT call review record --fingerprint
    after = (spec_dir / "state.json").read_bytes()
    if rc_s != 0 or rc_i != 0 or rc_c != 0:
        fail("findings-remain-no-auto-replay",
             f"recovery reads failed: rc_s={rc_s} rc_i={rc_i} rc_c={rc_c}")
    elif before != after:
        fail("findings-remain-no-auto-replay",
             "state.json mutated by read-only recovery sequence")
    else:
        ok("findings-remain-no-auto-replay")


def test_findings_remain_skill_prose_present(tmp: Path) -> None:
    """findings-remain SKILL.md row contains required phrases."""
    skill_path = SCRIPT_DIR.parent / "SKILL.md"
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    row_line = next(
        (ln for ln in lines
         if ("| `findings-remain`" in ln or "findings-remain" in ln)
         and "| `CODE-IMPLEMENTATION`" in ln),
        None,
    )
    if row_line is None:
        fail("findings-remain-skill-prose-present",
             "could not find findings-remain row in SKILL.md")
        return
    required = ["stale fingerprint baseline", "under-count", "do NOT auto-reissue"]
    missing = [p for p in required if p not in row_line]
    if missing:
        fail("findings-remain-skill-prose-present",
             f"findings-remain row missing: {missing}")
    else:
        ok("findings-remain-skill-prose-present")


def test_reviewers_clean_record_forms_present(tmp: Path) -> None:
    """--report and --all-skipped exist in cohort review record --help."""
    rc, out, err = run_cohort("review", "record", "--help")
    combined = out + err
    if "--report" not in combined or "--all-skipped" not in combined:
        fail("reviewers-clean-record-forms-present",
             f"missing flags in help: {combined!r}")
    else:
        ok("reviewers-clean-record-forms-present")


def test_reviewers_clean_no_silent_replay(tmp: Path) -> None:
    """cohort state unchanged after recovery reads; reads must succeed."""
    spec_dir, run_id = make_code_review_run(tmp, "rc-noreplay")
    write_spec(spec_dir, status="Shipped")
    rc_t, _, err_t = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc_t != 0:
        fail("reviewers-clean-no-silent-replay",
             f"reviewers-clean transition failed: rc={rc_t} {err_t.strip()!r}")
        return
    eng = json.loads(run_engine("status", str(spec_dir), "--json")[1])
    if eng.get("last_event") != "reviewers-clean":
        fail("reviewers-clean-no-silent-replay",
             f"engine last_event != reviewers-clean: {eng.get('last_event')!r}")
        return
    before = (spec_dir / "state.json").read_bytes()
    # Full documented read sequence (deliberate read-only; no review record call)
    rc_s, _, _ = run_engine("status", str(spec_dir), "--json")
    rc_i, _, _ = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    rc_c, _, _ = run_cohort("status", str(spec_dir), "--json")
    after = (spec_dir / "state.json").read_bytes()
    if rc_s != 0 or rc_i != 0 or rc_c != 0:
        fail("reviewers-clean-no-silent-replay",
             f"recovery reads failed: rc_s={rc_s} rc_i={rc_i} rc_c={rc_c}")
    elif before != after:
        fail("reviewers-clean-no-silent-replay",
             "state.json mutated by read-only recovery sequence")
    else:
        ok("reviewers-clean-no-silent-replay")


def test_reviewers_clean_skill_prose_obligations(tmp: Path) -> None:
    """reviewers-clean SKILL.md row contains required consequence phrases."""
    skill_path = SCRIPT_DIR.parent / "SKILL.md"
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    row_line = next(
        (ln for ln in lines
         if ("| `reviewers-clean`" in ln or "reviewers-clean" in ln)
         and "| `CODE-HUMAN-GATE`" in ln),
        None,
    )
    if row_line is None:
        fail("reviewers-clean-skill-prose-obligations",
             "could not find reviewers-clean row in SKILL.md")
        return
    required = ["non-idempotent", "double-increment",
                "fingerprint audit history", "authorized"]
    missing = [p for p in required if p not in row_line]
    if missing:
        fail("reviewers-clean-skill-prose-obligations",
             f"reviewers-clean row missing: {missing}")
    else:
        ok("reviewers-clean-skill-prose-obligations")


# ── runner ────────────────────────────────────────────────────────────────


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tests = [
            test_init_creates_engine_state_code,
            test_init_json_output,
            test_init_refuses_if_engine_state_exists,
            test_init_rejects_dotdot_spec_dir,
            test_init_field_set_complete,
            test_reset_deletes_engine_state,
            test_reset_idempotent,
            test_reset_leaves_state_json_intact,
            test_status_absent,
            test_status_json_after_init,
            test_status_human_wait_states,
            test_status_is_read_only,
            test_illegal_transitions_code,
            test_illegal_transitions_spec_plan,
            test_illegal_mode_in_engine_state,
            test_wave_passed_requires_wave_index,
            test_non_wave_events_reject_wave_index,
            test_run_id_preflight_mismatch_blocks_transition,
            test_run_id_preflight_absent_cohort_blocks_transition,
            test_legal_transition_spec_ready,
            test_legal_transition_plan_rejected,
            test_legal_transition_findings_remain_spec_plan_mode,
            test_transition_increments_sequence,
            test_transition_preserves_run_id_feature_mode,
            test_blocker_applied_code_human_gate,
            test_legal_plan_approved_spec_plan_mode,
            test_legal_reviewers_clean_spec_plan,
            test_guard_check_spec_status_fails_non_shipped,
            test_legal_wave_complete_to_code_verification,
            test_legal_gates_clean_to_code_review,
            test_legal_wave_passed_to_code_implementation,
            test_legal_gates_failed_to_code_implementation,
            test_legal_findings_remain_code_mode,
            test_legal_reviewers_clean_code_to_human_gate,
            test_legal_done_from_code_human_gate,
            test_guard_plan_check_current_fires_for_spec_plan_mode,
            test_guard_plan_check_current_require_schedule_fires_for_code_mode,
            test_guard_gates_failed_at_cap_blocks_transition,
            test_guard_review_at_cap_blocks_findings_remain,
            test_schedule_precheck_blocks_code_implementation_transition,
            test_done_exempt_from_schedule_precheck,
            test_transition_no_tmp_file_left_on_success,
            test_schema_version_forward_guard,
            test_check_spec_status_shipped,
            test_check_spec_status_draft_fails,
            test_check_spec_status_absent_spec,
            test_check_spec_status_no_status_line,
            test_check_spec_status_no_args,
            test_spec_plan_full_walk,
            test_evals_json_shape,
            # Crash-window tests: session-resumption and idempotency coverage
            test_no_chat_history_status_read_via_cli,
            test_no_chat_history_identity_verify_via_cli,
            test_no_chat_history_route_wave_passed_via_cli,
            test_no_chat_history_route_gates_failed_via_cli,
            test_wave_passed_window_a_advance_before_crash,
            test_wave_passed_window_b_advance_after_crash,
            test_wave_passed_wrong_from_index_refused,
            test_wave_passed_wrong_run_id_refused,
            test_wave_passed_run_ids_remain_paired_after_advance,
            test_gates_failed_window_a_record_before_crash,
            test_gates_failed_window_b_record_after_crash,
            test_gates_failed_wrong_run_id_prefix_refused,
            test_gates_failed_fifth_retry_permitted,
            test_gates_failed_sixth_retry_refused,
            test_findings_remain_phase_recoverable_from_engine,
            test_findings_remain_no_auto_replay,
            test_findings_remain_skill_prose_present,
            test_reviewers_clean_record_forms_present,
            test_reviewers_clean_no_silent_replay,
            test_reviewers_clean_skill_prose_obligations,
        ]
        for t in tests:
            try:
                t(tmp)
            except Exception as exc:
                fail(t.__name__, f"uncaught exception: {exc}")

    print(f"\n{ran - len(failures)}/{ran} passed", end="")
    if failures:
        print(f"  FAILED: {', '.join(failures)}", file=sys.stderr)
        return 1
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
