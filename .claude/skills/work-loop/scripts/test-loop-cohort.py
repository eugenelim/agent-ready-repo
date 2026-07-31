#!/usr/bin/env python3
"""Unit tests for loop-cohort.py — Phase-1 cohort state, identity, approval,
schedule guards, wave, retry, and review mutations.

Covers T1 and T3 test cases from plan.md.

Run: python3 test-loop-cohort.py
Exit 0 = all pass; exit non-zero = at least one failure.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COHORT = SCRIPT_DIR / "loop-cohort.py"

# Load loop-cohort module for direct function tests
_spec = importlib.util.spec_from_file_location("_loop_cohort", str(COHORT))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_findings = _mod.parse_findings
canonical_plan = _mod.canonical_plan
sha256_canonical_plan = _mod.sha256_canonical_plan
sha256_file = _mod.sha256_file
CLEAN_SUBSTRING = _mod.CLEAN_SUBSTRING

# ── helpers ───────────────────────────────────────────────────────────────

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


def run_cohort(*args, spec_dir=None):
    """Run loop-cohort.py with args; return (exit_code, stdout, stderr)."""
    import subprocess
    cmd = [sys.executable, str(COHORT)]
    if spec_dir is not None:
        # insert spec_dir after the verb where the parser expects it
        pass
    cmd.extend(str(a) for a in args)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def make_spec_dir(tmp: Path, feature: str = "myfeature") -> Path:
    d = tmp / feature
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_state(spec_dir: Path, state: dict) -> None:
    path = spec_dir / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


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


def _sha1(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8"), usedforsecurity=False).hexdigest()


def init_pair(tmp: Path, feature: str = "myfeature", mode: str = "code") -> tuple[Path, str]:
    """Run the full init pair: engine init then cohort init. Return (spec_dir, run_id)."""
    spec_dir = make_spec_dir(tmp, feature)
    # Engine init
    rc, out, err = run_cohort("__engine_skip__")  # placeholder — use direct calls
    # Use loop-engine.py for init
    engine = SCRIPT_DIR / "loop-engine.py"
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(engine), "init", str(spec_dir), "--mode", mode, "--json"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"engine init failed: {proc.stderr.strip()}")
    run_id = json.loads(proc.stdout)["run_id"]
    # Cohort init
    proc2 = subprocess.run(
        [sys.executable, str(COHORT), "init", str(spec_dir), "--run-id", run_id],
        capture_output=True, text=True, check=False,
    )
    if proc2.returncode != 0:
        raise RuntimeError(f"cohort init failed: {proc2.stderr.strip()}")
    return spec_dir, run_id


# ── T1: identity ──────────────────────────────────────────────────────────


def test_identity_absent_state(tmp: Path) -> None:
    name = "identity-absent-state"
    spec_dir = make_spec_dir(tmp, name)
    rc, _, _ = run_cohort("identity", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero exit when state.json absent")
    else:
        ok(name)


def test_identity_wrong_schema_version(tmp: Path) -> None:
    name = "identity-wrong-schema-version"
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 99, "run_id": "abc"})
    rc, _, err = run_cohort("identity", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when schema_version != 1")
    elif "schema_version" not in err:
        fail(name, f"expected 'schema_version' in stderr; got: {err!r}")
    else:
        ok(name)


def test_identity_run_id_mismatch(tmp: Path) -> None:
    name = "identity-run-id-mismatch"
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": "aaa"})
    rc, _, err = run_cohort("identity", str(spec_dir), "--expect-run-id", "bbb")
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch")
    elif "mismatch" not in err.lower() and "run_id" not in err.lower():
        fail(name, f"expected 'mismatch' or 'run_id' in stderr; got: {err!r}")
    else:
        ok(name)


def test_identity_success(tmp: Path) -> None:
    name = "identity-success"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id})
    rc, _, _ = run_cohort("identity", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, "expected exit 0 on matching run_id")
    else:
        ok(name)


def test_identity_json(tmp: Path) -> None:
    name = "identity-json"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id})
    rc, out, _ = run_cohort("identity", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"expected JSON output; got {out!r}")
        return
    if data.get("run_id") != run_id:
        fail(name, f"expected run_id {run_id!r}; got {data.get('run_id')!r}")
    else:
        ok(name)


# ── T1: init ──────────────────────────────────────────────────────────────


def test_init_creates_state(tmp: Path) -> None:
    name = "init-creates-state"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    rc, _, _ = run_cohort("init", str(spec_dir), "--run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state_path = spec_dir / "state.json"
    if not state_path.exists():
        fail(name, "state.json not created")
        return
    state = json.loads(state_path.read_text())
    if state.get("run_id") != run_id:
        fail(name, f"run_id mismatch: {state.get('run_id')!r} != {run_id!r}")
    elif state.get("feature") != name:
        fail(name, f"feature mismatch: {state.get('feature')!r} != {name!r}")
    elif state.get("schema_version") != 1:
        fail(name, f"schema_version expected 1, got {state.get('schema_version')!r}")
    else:
        ok(name)


def test_init_refuses_if_state_exists(tmp: Path) -> None:
    name = "init-refuses-if-state-exists"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id})
    rc, _, err = run_cohort("init", str(spec_dir), "--run-id", run_id)
    if rc == 0:
        fail(name, "expected non-zero exit when state.json already exists")
    else:
        ok(name)


def test_init_phase1_field_set(tmp: Path) -> None:
    """state.json written by init must carry Phase-1 field set exactly."""
    name = "init-phase1-field-set"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    rc, _, _ = run_cohort("init", str(spec_dir), "--run-id", run_id)
    if rc != 0:
        fail(name, f"init failed: exit {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    required = {
        "schema_version", "run_id", "feature", "plan_review_status",
        "approved_spec_hash", "approved_plan_hash", "plan_hash",
        "schedule_waves", "current_wave_index",
        "implementation_retry_count", "max_implementation_retries",
        "last_record_attempt_cycle_id",
        "review_round_count", "review_retry_count", "max_review_retries",
        "finding_fingerprints", "previous_finding_fingerprints",
        "auto_parallel", "last_commit_sha", "worktrees",
    }
    # Phase-2 fields must be absent
    phase2_absent = {
        "token_budget_used_pct", "token_budget_cap_pct",
        "consecutive_same_error_count", "consecutive_same_error_threshold",
        "last_error_fingerprint", "iteration_count", "max_iterations",
    }
    missing = required - set(state.keys())
    present_phase2 = phase2_absent & set(state.keys())
    if missing:
        fail(name, f"missing Phase-1 fields: {sorted(missing)}")
    elif present_phase2:
        fail(name, f"Phase-2 fields present in Phase-1 state: {sorted(present_phase2)}")
    elif state.get("approved_spec_hash") is not None:
        fail(name, "approved_spec_hash should be null at init")
    elif state.get("schedule_waves") != []:
        fail(name, "schedule_waves should be [] at init")
    else:
        ok(name)


# ── T1: pre-Phase-1 migration gate ────────────────────────────────────────


def test_pre_phase1_state_fails_identity(tmp: Path) -> None:
    """A state.json without run_id (pre-Phase-1) must fail identity."""
    name = "pre-phase1-fails-identity"
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "feature": "x",
        "iteration_count": 3,
        "max_iterations": 5,
        "plan_review_status": "approved",
    })
    rc, _, _ = run_cohort("identity", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero exit on pre-Phase-1 state.json (no run_id/schema_version)")
    else:
        ok(name)


# ── T1: status ────────────────────────────────────────────────────────────


def test_status_absent(tmp: Path) -> None:
    name = "status-absent"
    spec_dir = make_spec_dir(tmp, name)
    rc, _, _ = run_cohort("status", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when state.json absent")
    else:
        ok(name)


def test_status_json_after_init(tmp: Path) -> None:
    name = "status-json-after-init"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    rc, out, _ = run_cohort("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"expected JSON; got {out!r}")
        return
    if data.get("approved_spec_hash") is not None:
        fail(name, "approved_spec_hash should be null after init")
    elif data.get("schedule_waves") != []:
        fail(name, "schedule_waves should be [] after init")
    else:
        ok(name)


def test_status_is_read_only(tmp: Path) -> None:
    """status must not mutate state.json."""
    name = "status-read-only"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    run_cohort("status", str(spec_dir), "--json")
    after = path.read_bytes()
    if before != after:
        fail(name, "state.json was mutated by status")
    else:
        ok(name)


def test_status_null_to_value_transition(tmp: Path) -> None:
    """After approve-plan, hash fields transition from null to hex strings."""
    name = "status-null-to-value-transition"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)

    rc, out, _ = run_cohort("status", str(spec_dir), "--json")
    data = json.loads(out)
    if data.get("approved_spec_hash") is not None or data.get("approved_plan_hash") is not None:
        fail(name, "hash fields should be null before approve-plan")
        return

    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    rc2, out2, _ = run_cohort("status", str(spec_dir), "--json")
    data2 = json.loads(out2)
    spec_hash = data2.get("approved_spec_hash")
    plan_hash = data2.get("approved_plan_hash")
    if not isinstance(spec_hash, str) or len(spec_hash) != 64:
        fail(name, f"approved_spec_hash should be hex-64 after approve-plan; got {spec_hash!r}")
    elif not isinstance(plan_hash, str) or len(plan_hash) != 64:
        fail(name, f"approved_plan_hash should be hex-64 after approve-plan; got {plan_hash!r}")
    else:
        ok(name)


# ── T1: reset ─────────────────────────────────────────────────────────────


def test_reset_deletes_state(tmp: Path) -> None:
    name = "reset-deletes-state"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    assert (spec_dir / "state.json").exists()
    rc, _, _ = run_cohort("reset", str(spec_dir))
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
    elif (spec_dir / "state.json").exists():
        fail(name, "state.json still exists after reset")
    else:
        ok(name)


def test_reset_idempotent(tmp: Path) -> None:
    name = "reset-idempotent"
    spec_dir = make_spec_dir(tmp, name)
    rc1, _, _ = run_cohort("reset", str(spec_dir))
    rc2, _, _ = run_cohort("reset", str(spec_dir))
    if rc1 != 0 or rc2 != 0:
        fail(name, f"expected both resets to exit 0; got {rc1}, {rc2}")
    else:
        ok(name)


# ── T1: approve-plan ──────────────────────────────────────────────────────


def test_approve_plan_writes_hashes(tmp: Path) -> None:
    name = "approve-plan-writes-hashes"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    rc, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("plan_review_status") != "approved":
        fail(name, "plan_review_status not set to approved")
    elif not isinstance(state.get("approved_spec_hash"), str):
        fail(name, "approved_spec_hash not written")
    elif not isinstance(state.get("approved_plan_hash"), str):
        fail(name, "approved_plan_hash not written")
    else:
        ok(name)


def test_approve_plan_run_id_mismatch(tmp: Path) -> None:
    name = "approve-plan-run-id-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", "wrong-id")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch")
    elif before != after:
        fail(name, "state.json was mutated despite run_id mismatch")
    else:
        ok(name)


def test_approve_plan_overwrites_hashes(tmp: Path) -> None:
    """approve-plan unconditionally overwrites old hashes (no cleanup needed on retry)."""
    name = "approve-plan-overwrites-hashes"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    state1 = json.loads((spec_dir / "state.json").read_text())
    hash1 = state1.get("approved_spec_hash")
    # Simulate G-plan status-only edit and re-run
    write_spec(spec_dir, status="Approved")
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    state2 = json.loads((spec_dir / "state.json").read_text())
    hash2 = state2.get("approved_spec_hash")
    if hash1 == hash2:
        fail(name, "approved_spec_hash should differ after re-approve on changed spec")
    else:
        ok(name)


# ── T1: plan check-current ────────────────────────────────────────────────


def test_plan_check_current_not_approved(tmp: Path) -> None:
    name = "plan-check-current-not-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    rc, _, _ = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when plan_review_status != approved")
    else:
        ok(name)


def test_plan_check_current_changed_spec(tmp: Path) -> None:
    name = "plan-check-current-changed-spec"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    # Change spec.md after approval
    write_spec(spec_dir, status="Implementing")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when spec.md changed after approve-plan")
    else:
        ok(name)


def test_plan_check_current_changed_plan(tmp: Path) -> None:
    name = "plan-check-current-changed-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    # Change plan.md after approval
    write_plan(spec_dir, content="# Plan (modified)\n\n### T1\n\n**Depends on:** none\n")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when plan.md changed after approve-plan")
    else:
        ok(name)


def test_plan_check_current_require_schedule_no_schedule(tmp: Path) -> None:
    name = "plan-check-current-require-schedule-no-schedule"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    # No schedule run yet
    rc, _, _ = run_cohort("plan", "check-current", str(spec_dir), "--require-schedule")
    if rc == 0:
        fail(name, "expected non-zero when --require-schedule but no schedule run")
    else:
        ok(name)


def test_plan_check_current_absent_files_spec_plan_mode(tmp: Path) -> None:
    """spec-plan mode: plan check-current requires both spec.md and plan.md."""
    name = "plan-check-current-absent-files"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    # Manually set approved but no files
    state = json.loads((spec_dir / "state.json").read_text())
    state["plan_review_status"] = "approved"
    (spec_dir / "state.json").write_text(json.dumps(state))

    # No spec.md
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when spec.md absent")
        return

    write_spec(spec_dir)
    # No plan.md
    rc2, _, _ = run_cohort("plan", "check-current", str(spec_dir))
    if rc2 == 0:
        fail(name, "expected non-zero when plan.md absent")
    else:
        ok(name)


# ── T1: schedule check-current ────────────────────────────────────────────


def test_schedule_check_current_refuses_on_change(tmp: Path) -> None:
    name = "schedule-check-current-refuses-on-change"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    # Mutate plan.md
    write_plan(spec_dir, content="# Plan (modified)\n\n### T1\n\n**Depends on:** none\n")
    rc, _, err = run_cohort("schedule", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when plan.md changed after schedule")
    else:
        ok(name)


def test_schedule_check_current_passes_unchanged(tmp: Path) -> None:
    name = "schedule-check-current-passes-unchanged"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    rc, _, _ = run_cohort("schedule", "check-current", str(spec_dir))
    if rc != 0:
        fail(name, "expected exit 0 when plan.md unchanged")
    else:
        ok(name)


# ── T1: schedule run (persists state) ────────────────────────────────────


def test_schedule_persists_waves(tmp: Path) -> None:
    name = "schedule-persists-waves"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    rc, _, _ = run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if not state.get("schedule_waves"):
        fail(name, "schedule_waves not persisted")
    elif state.get("plan_hash") is None:
        fail(name, "plan_hash not persisted")
    elif state.get("current_wave_index") != 0:
        fail(name, f"current_wave_index should be 0; got {state.get('current_wave_index')}")
    else:
        ok(name)


def test_schedule_run_id_mismatch(tmp: Path) -> None:
    name = "schedule-run-id-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir)
    write_plan(spec_dir)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, _ = run_cohort("schedule", str(spec_dir), "--expect-run-id", "wrong")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch")
    elif before != after:
        fail(name, "state.json mutated despite run_id mismatch")
    else:
        ok(name)


# ── T1: disabled Phase-1 verbs ────────────────────────────────────────────


def test_disabled_worktree(tmp: Path) -> None:
    name = "disabled-worktree"
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": "x", "worktrees": []})
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, err = run_cohort("worktree", "add", str(spec_dir))
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for worktree add (disabled)")
    elif "disabled" not in err.lower():
        fail(name, f"expected 'disabled' in stderr; got {err!r}")
    elif before != after:
        fail(name, "state.json mutated by disabled worktree verb")
    else:
        ok(name)


def test_disabled_dispatch_decision(tmp: Path) -> None:
    name = "disabled-dispatch-decision"
    rc, _, err = run_cohort("dispatch-decision", "--branch", "main")
    if rc == 0:
        fail(name, "expected non-zero for dispatch-decision (disabled)")
    elif "disabled" not in err.lower():
        fail(name, f"expected 'disabled' in stderr; got {err!r}")
    else:
        ok(name)


def test_disabled_auto_parallel(tmp: Path) -> None:
    name = "disabled-auto-parallel"
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": "x"})
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, err = run_cohort("auto-parallel", str(spec_dir))
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for auto-parallel (disabled)")
    elif "disabled" not in err.lower():
        fail(name, f"expected 'disabled' in stderr; got {err!r}")
    elif before != after:
        fail(name, "state.json mutated by disabled auto-parallel verb")
    else:
        ok(name)


# ── T1: check --phase stubs ───────────────────────────────────────────────


def test_check_phase_implement_stub(tmp: Path) -> None:
    """check --phase implement must exit 0 for any valid Phase-1 state."""
    name = "check-phase-implement-stub"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # Write a minimal Phase-1 state — no token-budget or same-error fields
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "plan_review_status": "approved",
        "implementation_retry_count": 0, "max_implementation_retries": 5,
    })
    rc, _, _ = run_cohort("check", str(spec_dir), "--phase", "implement")
    if rc != 0:
        fail(name, f"check --phase implement should exit 0 (stub); got {rc}")
    else:
        ok(name)


def test_check_phase_implement_no_phase2_fields(tmp: Path) -> None:
    """check --phase implement must NOT read token-budget or same-error fields."""
    name = "check-phase-implement-no-phase2"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # State WITHOUT any Phase-2 fields — stub should still exit 0
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id})
    rc, _, _ = run_cohort("check", str(spec_dir), "--phase", "implement")
    if rc != 0:
        fail(name, "check --phase implement failed when Phase-2 fields are absent")
    else:
        ok(name)


def test_check_phase_gates_failed_cap(tmp: Path) -> None:
    name = "check-phase-gates-failed-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 5,
        "max_implementation_retries": 5,
    })
    rc, _, err = run_cohort("check", str(spec_dir), "--phase", "gates-failed")
    if rc == 0:
        fail(name, "expected non-zero at implementation retry cap")
    elif "cap" not in err.lower():
        fail(name, f"expected 'cap' in stderr; got {err!r}")
    else:
        ok(name)


def test_check_phase_gates_failed_under_cap(tmp: Path) -> None:
    name = "check-phase-gates-failed-under-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 4,
        "max_implementation_retries": 5,
    })
    rc, _, _ = run_cohort("check", str(spec_dir), "--phase", "gates-failed")
    if rc != 0:
        fail(name, "expected exit 0 when under implementation retry cap")
    else:
        ok(name)


def test_check_phase_review_cap(tmp: Path) -> None:
    name = "check-phase-review-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_retry_count": 5,
        "max_review_retries": 5,
    })
    rc, _, err = run_cohort("check", str(spec_dir), "--phase", "review")
    if rc == 0:
        fail(name, "expected non-zero at review retry cap")
    else:
        ok(name)


# ── T3: wave advance ──────────────────────────────────────────────────────


def _make_scheduled_state(spec_dir: Path, run_id: str, n_waves: int = 3) -> dict:
    waves = [[f"T{i + 1}"] for i in range(n_waves)]
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "plan_review_status": "approved",
        "schedule_waves": waves,
        "current_wave_index": 0,
        "implementation_retry_count": 0, "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    }
    write_state(spec_dir, state)
    return state


def test_wave_advance_normal(tmp: Path) -> None:
    name = "wave-advance-normal"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _make_scheduled_state(spec_dir, run_id, n_waves=3)
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("current_wave_index") != 1:
        fail(name, f"expected current_wave_index=1; got {state.get('current_wave_index')}")
    else:
        ok(name)


def test_wave_advance_idempotent(tmp: Path) -> None:
    """Advancing when current_wave_index == n+1 already is a no-op."""
    name = "wave-advance-idempotent"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _make_scheduled_state(spec_dir, run_id, n_waves=3)
    state["current_wave_index"] = 1
    write_state(spec_dir, state)
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
    )
    if rc != 0:
        fail(name, f"expected exit 0 on idempotent replay; got {rc}")
        return
    state2 = json.loads((spec_dir / "state.json").read_text())
    if state2.get("current_wave_index") != 1:
        cwi = state2.get("current_wave_index")
        fail(name, f"current_wave_index changed on idempotent replay; got {cwi}")
    else:
        ok(name)


def test_wave_advance_refuses_final_wave(tmp: Path) -> None:
    name = "wave-advance-refuses-final-wave"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _make_scheduled_state(spec_dir, run_id, n_waves=3)
    state["current_wave_index"] = 2
    write_state(spec_dir, state)
    rc, _, err = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "2", "--expect-run-id", run_id
    )
    if rc == 0:
        fail(name, "expected non-zero when advancing from final wave")
    else:
        ok(name)


def test_wave_advance_refuses_negative(tmp: Path) -> None:
    name = "wave-advance-refuses-negative"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _make_scheduled_state(spec_dir, run_id, n_waves=3)
    # argparse rejects non-integer, so pass a valid negative int
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "-1", "--expect-run-id", run_id
    )
    if rc == 0:
        fail(name, "expected non-zero for --from-index -1")
    else:
        ok(name)


def test_wave_advance_refuses_ge_len(tmp: Path) -> None:
    name = "wave-advance-refuses-ge-len"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _make_scheduled_state(spec_dir, run_id, n_waves=3)
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "3", "--expect-run-id", run_id
    )
    if rc == 0:
        fail(name, "expected non-zero for --from-index >= len(schedule_waves)")
    else:
        ok(name)


def test_wave_advance_refuses_empty_schedule(tmp: Path) -> None:
    name = "wave-advance-refuses-empty-schedule"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id, "schedule_waves": [], "current_wave_index": 0,
    })
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
    )
    if rc == 0:
        fail(name, "expected non-zero for empty schedule_waves")
    else:
        ok(name)


def test_wave_advance_expect_run_id_mismatch(tmp: Path) -> None:
    name = "wave-advance-expect-run-id-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _make_scheduled_state(spec_dir, run_id, n_waves=3)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", "wrong"
    )
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch")
    elif before != after:
        fail(name, "state.json mutated despite run_id mismatch")
    else:
        ok(name)


# ── T3: wave check ────────────────────────────────────────────────────────


def test_wave_check_more_succeeds(tmp: Path) -> None:
    name = "wave-check-more-succeeds"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _make_scheduled_state(spec_dir, run_id, n_waves=3)
    state["current_wave_index"] = 1
    write_state(spec_dir, state)
    rc, _, _ = run_cohort("wave", "check", str(spec_dir), "--expect", "more")
    if rc != 0:
        fail(name, f"expected exit 0 when more waves remain; got {rc}")
    else:
        ok(name)


def test_wave_check_more_fails_at_last(tmp: Path) -> None:
    name = "wave-check-more-fails-at-last"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _make_scheduled_state(spec_dir, run_id, n_waves=3)
    state["current_wave_index"] = 2
    write_state(spec_dir, state)
    rc, _, _ = run_cohort("wave", "check", str(spec_dir), "--expect", "more")
    if rc == 0:
        fail(name, "expected non-zero when at final wave")
    else:
        ok(name)


def test_wave_check_last_succeeds(tmp: Path) -> None:
    name = "wave-check-last-succeeds"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _make_scheduled_state(spec_dir, run_id, n_waves=3)
    state["current_wave_index"] = 2
    write_state(spec_dir, state)
    rc, _, _ = run_cohort("wave", "check", str(spec_dir), "--expect", "last")
    if rc != 0:
        fail(name, f"expected exit 0 at last wave; got {rc}")
    else:
        ok(name)


def test_wave_check_wave_index_mismatch(tmp: Path) -> None:
    name = "wave-check-wave-index-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _make_scheduled_state(spec_dir, run_id, n_waves=3)
    state["current_wave_index"] = 1
    write_state(spec_dir, state)
    rc, _, _ = run_cohort("wave", "check", str(spec_dir), "--expect", "more", "--wave-index", "0")
    if rc == 0:
        fail(name, "expected non-zero when --wave-index doesn't match current_wave_index")
    else:
        ok(name)


# ── T3: record-attempt ────────────────────────────────────────────────────


def test_record_attempt_increments(tmp: Path) -> None:
    name = "record-attempt-increments"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 0, "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
    })
    cycle = f"{run_id}:1"
    rc, _, _ = run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
                          "--cycle-id", cycle, "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("implementation_retry_count") != 1:
        irc = state.get("implementation_retry_count")
        fail(name, f"expected implementation_retry_count=1; got {irc}")
    elif state.get("last_record_attempt_cycle_id") != cycle:
        fail(name, "last_record_attempt_cycle_id not updated")
    else:
        ok(name)


def test_record_attempt_idempotent(tmp: Path) -> None:
    """Same cycle-id is a no-op."""
    name = "record-attempt-idempotent"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 0, "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
    })
    cycle = f"{run_id}:1"
    run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
               "--cycle-id", cycle, "--expect-run-id", run_id)
    # Second call with same cycle-id
    rc, _, _ = run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
                          "--cycle-id", cycle, "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0 on idempotent replay; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("implementation_retry_count") != 1:
        irc = state.get("implementation_retry_count")
        fail(name, f"expected count=1 after idempotent replay; got {irc}")
    else:
        ok(name)


def test_record_attempt_new_cycle_increments(tmp: Path) -> None:
    name = "record-attempt-new-cycle-increments"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 0, "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
    })
    run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
               "--cycle-id", f"{run_id}:1", "--expect-run-id", run_id)
    run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
               "--cycle-id", f"{run_id}:2", "--expect-run-id", run_id)
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("implementation_retry_count") != 2:
        irc = state.get("implementation_retry_count")
        fail(name, f"expected count=2 after two distinct cycle-ids; got {irc}")
    else:
        ok(name)


def test_record_attempt_run_id_prefix_mismatch(tmp: Path) -> None:
    """cycle-id's run_id prefix must match --expect-run-id."""
    name = "record-attempt-prefix-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 0, "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
    })
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # wrong run_id prefix in cycle-id
    rc, _, _ = run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
                          "--cycle-id", "wrong-run-id:1", "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on cycle-id prefix mismatch")
    elif before != after:
        fail(name, "state.json mutated despite prefix mismatch")
    else:
        ok(name)


# ── T3: review inspect ────────────────────────────────────────────────────


SAMPLE_FINDINGS_REPORT = """\
## Blockers

**1. Missing null check.** `path/to/file.py:42`. The value is never validated. Fix: add guard.

## Nits

**2. Typo in comment.** `path/to/other.py:10`. Misspelling. Fix: fix it.
"""

CLEAN_REPORT = f"Review complete.\n\n{CLEAN_SUBSTRING}\n"

EMPTY_REPORT = "No findings reported here."


def test_review_inspect_clean(tmp: Path) -> None:
    name = "review-inspect-clean"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    report = tmp / "clean.md"
    report.write_text(CLEAN_REPORT)
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("classification") != "clean":
        fail(name, f"expected classification=clean; got {data.get('classification')!r}")
    elif data.get("fingerprints") != []:
        fail(name, "expected empty fingerprints for clean report")
    else:
        ok(name)


def test_review_inspect_findings(tmp: Path) -> None:
    name = "review-inspect-findings"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    report = tmp / "findings.md"
    report.write_text(SAMPLE_FINDINGS_REPORT)
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0 for findings; got {rc}")
        return
    data = json.loads(out)
    if data.get("classification") != "findings":
        fail(name, f"expected classification=findings; got {data.get('classification')!r}")
    elif len(data.get("fingerprints", [])) != 2:
        fail(name, f"expected 2 fingerprints; got {len(data.get('fingerprints', []))}")
    else:
        ok(name)


def test_review_inspect_invalid_absent(tmp: Path) -> None:
    name = "review-inspect-invalid-absent"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir),
                            "--report", str(tmp / "nonexistent.md"), "--json")
    if rc != 0:
        fail(name, f"review inspect should exit 0 for absent report; got {rc}")
        return
    data = json.loads(out)
    if data.get("classification") != "invalid":
        cls = data.get("classification")
        fail(name, f"expected classification=invalid for absent report; got {cls!r}")
    else:
        ok(name)


def test_review_inspect_invalid_no_clean_no_findings(tmp: Path) -> None:
    name = "review-inspect-invalid-empty"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    report = tmp / "empty.md"
    report.write_text(EMPTY_REPORT)
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("classification") != "invalid":
        fail(name, f"expected classification=invalid; got {data.get('classification')!r}")
    else:
        ok(name)


def test_review_inspect_stasis(tmp: Path) -> None:
    """matches_previous_round should be True when fingerprints match stored set."""
    name = "review-inspect-stasis"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # Prime the state with known fingerprints
    fps = sorted(set(parse_findings(SAMPLE_FINDINGS_REPORT)))
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "finding_fingerprints": fps,
    })
    report = tmp / "stasis.md"
    report.write_text(SAMPLE_FINDINGS_REPORT)
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if not data.get("matches_previous_round"):
        fail(name, "expected matches_previous_round=True for identical findings")
    else:
        ok(name)


def test_review_inspect_empty_vs_empty_not_stasis(tmp: Path) -> None:
    """Empty fingerprints vs empty stored set is NOT stasis (always False)."""
    name = "review-inspect-empty-not-stasis"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    report = tmp / "clean2.md"
    report.write_text(CLEAN_REPORT)
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("matches_previous_round"):
        fail(name, "empty-vs-empty should NOT be stasis (matches_previous_round=False)")
    else:
        ok(name)


def test_review_inspect_findings_precedence(tmp: Path) -> None:
    """A report with both clean substring and findings classifies as 'findings'."""
    name = "review-inspect-findings-precedence"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    mixed = SAMPLE_FINDINGS_REPORT + f"\n{CLEAN_SUBSTRING}\n"
    report = tmp / "mixed.md"
    report.write_text(mixed)
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("classification") != "findings":
        cls = data.get("classification")
        fail(name, f"expected classification=findings when both present; got {cls!r}")
    else:
        ok(name)


# ── T3: review record ──────────────────────────────────────────────────────


def test_review_record_fingerprint_increments_both_counters(tmp: Path) -> None:
    name = "review-record-fingerprint-counters"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    fp = "aabbccdd" * 5
    rc, _, _ = run_cohort(
        "review", "record", str(spec_dir), "--fingerprint", fp, "--expect-run-id", run_id
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("review_round_count") != 1:
        fail(name, f"expected review_round_count=1; got {state.get('review_round_count')}")
    elif state.get("review_retry_count") != 1:
        fail(name, f"expected review_retry_count=1; got {state.get('review_retry_count')}")
    else:
        ok(name)


def test_review_record_report_increments_only_round(tmp: Path) -> None:
    """--report branch increments review_round_count only (not review_retry_count)."""
    name = "review-record-report-counter-separation"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 2, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    report = tmp / "clean3.md"
    report.write_text(CLEAN_REPORT)
    rc, _, _ = run_cohort("review", "record", str(spec_dir), "--report", str(report),
                          "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("review_round_count") != 1:
        fail(name, f"expected review_round_count=1; got {state.get('review_round_count')}")
    elif state.get("review_retry_count") != 2:
        rrc = state.get("review_retry_count")
        fail(name, f"review_retry_count should be unchanged (2); got {rrc}")
    else:
        ok(name)


def test_review_record_report_rejects_non_clean(tmp: Path) -> None:
    name = "review-record-report-rejects-non-clean"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    report = tmp / "findings2.md"
    report.write_text(SAMPLE_FINDINGS_REPORT)
    rc, _, _ = run_cohort("review", "record", str(spec_dir), "--report", str(report),
                          "--expect-run-id", run_id)
    if rc == 0:
        fail(name, "expected non-zero when --report used with non-clean report")
    else:
        ok(name)


def test_review_record_fingerprint_canonicalization(tmp: Path) -> None:
    """Duplicate/reordered fingerprints produce identical sorted-set state."""
    name = "review-record-fp-canonicalization"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)

    h1 = "a" * 40
    h2 = "b" * 40

    # Call 1: duplicated h1
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    run_cohort("review", "record", str(spec_dir), "--fingerprint", h1, "--fingerprint", h2,
               "--fingerprint", h1, "--expect-run-id", run_id)
    state1 = json.loads((spec_dir / "state.json").read_text())
    fps1 = state1.get("finding_fingerprints", [])

    # Call 2: reordered — reset and re-init
    run_cohort("reset", str(spec_dir))
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    run_cohort("review", "record", str(spec_dir), "--fingerprint", h2, "--fingerprint", h1,
               "--expect-run-id", run_id)
    state2 = json.loads((spec_dir / "state.json").read_text())
    fps2 = state2.get("finding_fingerprints", [])

    expected = sorted({h1, h2})
    if fps1 != expected:
        fail(name, f"first call: expected {expected}; got {fps1}")
    elif fps2 != expected:
        fail(name, f"second call (reordered): expected {expected}; got {fps2}")
    else:
        ok(name)


def test_review_record_run_id_mismatch(tmp: Path) -> None:
    name = "review-record-run-id-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, _ = run_cohort("review", "record", str(spec_dir), "--fingerprint", "aa" * 20,
                          "--expect-run-id", "wrong")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch")
    elif before != after:
        fail(name, "state.json mutated despite run_id mismatch")
    else:
        ok(name)


def test_review_record_clean_resets_fingerprint_baseline(tmp: Path) -> None:
    """After clean review, a subsequent inspect of the same findings is not stasis."""
    name = "review-record-clean-resets-baseline"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    fps = sorted(set(parse_findings(SAMPLE_FINDINGS_REPORT)))
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 1, "review_retry_count": 1, "max_review_retries": 5,
        "finding_fingerprints": fps, "previous_finding_fingerprints": [],
    })
    # Clean review resets baseline to []
    report = tmp / "clean4.md"
    report.write_text(CLEAN_REPORT)
    run_cohort(
        "review", "record", str(spec_dir), "--report", str(report), "--expect-run-id", run_id
    )
    # Now inspect the same findings report
    findings_report = tmp / "findings3.md"
    findings_report.write_text(SAMPLE_FINDINGS_REPORT)
    rc, out, _ = run_cohort(
        "review", "inspect", str(spec_dir), "--report", str(findings_report), "--json"
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("matches_previous_round"):
        fail(name, "after clean review, same findings should NOT trigger stasis"
                   " (baseline reset to [])")
    else:
        ok(name)


# ── T3: module-scope constant characterization ────────────────────────────


def test_clean_substring_constant(tmp: Path) -> None:
    """CLEAN_SUBSTRING must have the exact value the adversarial-reviewer emits."""
    name = "clean-substring-constant"
    expected = "Clean — ready to commit."  # em-dash
    if expected != CLEAN_SUBSTRING:
        fail(name, f"CLEAN_SUBSTRING={CLEAN_SUBSTRING!r} != {expected!r}")
    else:
        ok(name)


def test_parse_findings_canonical_algorithm(tmp: Path) -> None:
    """parse_findings must produce sha1('<file>|<line>|<title>') per finding."""
    name = "parse-findings-algorithm"
    report = """\
## Blockers

**1. Bad thing.** `src/foo.py:99`. Something wrong. Fix: fix it.
"""
    fps = parse_findings(report)
    if len(fps) != 1:
        fail(name, f"expected 1 fingerprint; got {len(fps)}")
        return
    expected_key = "src/foo.py|99|**1. Bad thing.**"
    expected_fp = hashlib.sha1(expected_key.encode("utf-8"), usedforsecurity=False).hexdigest()
    if fps[0] != expected_fp:
        fail(name, f"fingerprint mismatch: {fps[0]!r} != {expected_fp!r}")
    else:
        ok(name)


def test_canonical_plan_normalization(tmp: Path) -> None:
    name = "canonical-plan-normalization"
    crlf_text = "line1  \r\nline2\r\n"
    result = canonical_plan(crlf_text)
    if "\r" in result:
        fail(name, "CRLF not normalized")
    elif any(line != line.rstrip() for line in result.split("\n")):
        fail(name, "trailing whitespace not stripped")
    else:
        ok(name)


# ── G-plan ordering test ──────────────────────────────────────────────────


def test_gplan_ordering_status_approved_before_approve_plan(tmp: Path) -> None:
    """Writing Status: Approved then approve-plan hashes the correct spec bytes."""
    name = "gplan-ordering-status-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    rc, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"approve-plan failed: exit {rc}")
        return
    # plan check-current should pass (status-only edit is the permitted post-sign-off edit)
    rc2, _, _ = run_cohort("plan", "check-current", str(spec_dir))
    if rc2 != 0:
        fail(name, "plan check-current failed after status-only edit (Approved)")
    else:
        ok(name)


# ── runner ────────────────────────────────────────────────────────────────


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tests = [
            test_identity_absent_state,
            test_identity_wrong_schema_version,
            test_identity_run_id_mismatch,
            test_identity_success,
            test_identity_json,
            test_init_creates_state,
            test_init_refuses_if_state_exists,
            test_init_phase1_field_set,
            test_pre_phase1_state_fails_identity,
            test_status_absent,
            test_status_json_after_init,
            test_status_is_read_only,
            test_status_null_to_value_transition,
            test_reset_deletes_state,
            test_reset_idempotent,
            test_approve_plan_writes_hashes,
            test_approve_plan_run_id_mismatch,
            test_approve_plan_overwrites_hashes,
            test_plan_check_current_not_approved,
            test_plan_check_current_changed_spec,
            test_plan_check_current_changed_plan,
            test_plan_check_current_require_schedule_no_schedule,
            test_plan_check_current_absent_files_spec_plan_mode,
            test_schedule_check_current_refuses_on_change,
            test_schedule_check_current_passes_unchanged,
            test_schedule_persists_waves,
            test_schedule_run_id_mismatch,
            test_disabled_worktree,
            test_disabled_dispatch_decision,
            test_disabled_auto_parallel,
            test_check_phase_implement_stub,
            test_check_phase_implement_no_phase2_fields,
            test_check_phase_gates_failed_cap,
            test_check_phase_gates_failed_under_cap,
            test_check_phase_review_cap,
            test_wave_advance_normal,
            test_wave_advance_idempotent,
            test_wave_advance_refuses_final_wave,
            test_wave_advance_refuses_negative,
            test_wave_advance_refuses_ge_len,
            test_wave_advance_refuses_empty_schedule,
            test_wave_advance_expect_run_id_mismatch,
            test_wave_check_more_succeeds,
            test_wave_check_more_fails_at_last,
            test_wave_check_last_succeeds,
            test_wave_check_wave_index_mismatch,
            test_record_attempt_increments,
            test_record_attempt_idempotent,
            test_record_attempt_new_cycle_increments,
            test_record_attempt_run_id_prefix_mismatch,
            test_review_inspect_clean,
            test_review_inspect_findings,
            test_review_inspect_invalid_absent,
            test_review_inspect_invalid_no_clean_no_findings,
            test_review_inspect_stasis,
            test_review_inspect_empty_vs_empty_not_stasis,
            test_review_inspect_findings_precedence,
            test_review_record_fingerprint_increments_both_counters,
            test_review_record_report_increments_only_round,
            test_review_record_report_rejects_non_clean,
            test_review_record_fingerprint_canonicalization,
            test_review_record_run_id_mismatch,
            test_review_record_clean_resets_fingerprint_baseline,
            test_clean_substring_constant,
            test_parse_findings_canonical_algorithm,
            test_canonical_plan_normalization,
            test_gplan_ordering_status_approved_before_approve_plan,
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
