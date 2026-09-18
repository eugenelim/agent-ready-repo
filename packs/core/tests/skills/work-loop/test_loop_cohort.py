#!/usr/bin/env python3
"""Pytest tests for loop-cohort.py — Phase-1 cohort state, identity, approval,
schedule guards, wave, retry, and review mutations.

Run with pytest.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import uuid
from pathlib import Path

import pytest

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"

if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
COHORT = SCRIPT_DIR / "loop-cohort.py"

# Load loop-cohort module for direct function tests
_spec = importlib.util.spec_from_file_location("_loop_cohort", str(COHORT))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_findings = _mod.parse_findings
canonical_contract = _mod.canonical_contract
sha256_canonical_contract = _mod.sha256_canonical_contract
CLEAN_SUBSTRING = _mod.CLEAN_SUBSTRING

# ── helpers ───────────────────────────────────────────────────────────────


def ok(name: str) -> None:
    """Pytest reports the independently collected case."""


def fail(name: str, reason: str) -> None:
    pytest.fail(f"{name}: {reason}")


def symlink_or_skip(name: str, link: Path, target: Path | str) -> bool:
    """Create a required symlink, recording a real skip only outside CI."""
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        if os.environ.get("CI"):
            fail(name, f"CI must support this symlink regression: {exc}")
        pytest.skip(f"{name}: symlink creation unavailable ({exc})")
    return True


def run_cohort(*args, spec_dir=None):
    """Run loop-cohort.py with args; return (exit_code, stdout, stderr)."""
    import subprocess
    cmd = [sys.executable, str(COHORT)]
    if spec_dir is not None:
        # insert spec_dir after the verb where the parser expects it
        pass
    cmd.extend(str(a) for a in args)
    spec_path = next((Path(a) for a in args if Path(a).is_dir()), None)
    proc = subprocess.run(
        cmd,
        cwd=str(spec_path.parent) if spec_path is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def make_spec_dir(tmp: Path, feature: str = "myfeature") -> Path:
    import subprocess
    subprocess.run(
        ["git", "init", "-q", str(tmp)], check=True, capture_output=True
    )
    d = tmp / feature
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_resolve_spec_dir_refuses_paths_outside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The resolver must reject absolute and symlinked paths that escape root."""
    repo_root = tmp_path / "repo"
    outside = tmp_path / "outside"
    repo_root.mkdir()
    outside.mkdir()
    escaped_link = repo_root / "escaped-link"
    symlink_or_skip("spec-dir confinement", escaped_link, outside)
    monkeypatch.setattr(_mod, "_get_repo_root", lambda: repo_root.resolve())

    with pytest.raises(ValueError, match="must be inside the repository"):
        _mod._resolve_spec_dir(str(outside))
    with pytest.raises(ValueError, match="must be inside the repository"):
        _mod._resolve_spec_dir(str(escaped_link))


def test_repo_root_ignores_git_relocation_environment(
    tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Caller-set Git relocation must not redirect the confinement root."""
    import subprocess

    make_spec_dir(tmp)
    foreign = tmp / "foreign"
    foreign.mkdir()
    subprocess.run(
        ["git", "init", "-q", str(foreign)], check=True, capture_output=True
    )
    monkeypatch.chdir(tmp)
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(foreign))

    assert _mod._get_repo_root() == tmp.resolve()


def write_state(spec_dir: Path, state: dict) -> None:
    path = spec_dir / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def write_spec(spec_dir: Path, status: str = "Draft") -> Path:
    p = spec_dir / "spec.md"
    content = f"# Spec\n\n- **Status:** {status}\n\n## Acceptance criteria\n\n- [ ] AC1\n"
    p.write_text(content, encoding="utf-8")
    return p


def write_plan(
    spec_dir: Path, content: str | None = None, status: str | None = "Approved"
) -> Path:
    p = spec_dir / "plan.md"
    if content is None:
        status_line = f"- **Status:** {status}\n\n" if status is not None else ""
        content = (
            f"# Plan\n\n{status_line}### T1\n\n**Depends on:** none\n\n"
            "### T2\n\n**Depends on:** T1\n"
        )
    p.write_text(content, encoding="utf-8")
    return p


def _fingerprint(key: str) -> str:
    """Independent recomputation of the documented fingerprint algorithm.

    Deliberately spelled out here rather than imported from loop-cohort, so a
    change to the algorithm has to be made in two places and cannot slip
    through as a tautology.
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


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
        cwd=str(tmp), capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"engine init failed: {proc.stderr.strip()}")
    run_id = json.loads(proc.stdout)["run_id"]
    # Cohort init
    proc2 = subprocess.run(
        [sys.executable, str(COHORT), "init", str(spec_dir), "--run-id", run_id],
        cwd=str(tmp), capture_output=True, text=True, check=False,
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


# STUB: AC3 — status must not follow a managed cohort-state symlink.
def test_status_rejects_symlinked_cohort_state(tmp: Path) -> None:
    name = "status-rejects-symlinked-cohort-state"
    spec_dir = make_spec_dir(tmp, name)
    sentinel = "outside-cohort-state-sentinel"
    outside = tmp / f"{name}-outside.json"
    outside.write_text(
        json.dumps({
            "schema_version": 1,
            "run_id": str(uuid.uuid4()),
            "feature": sentinel,
        }),
        encoding="utf-8",
    )
    if not symlink_or_skip(name, spec_dir / "state.json", outside):
        return

    rc, out, err = run_cohort("status", str(spec_dir), "--json")

    if rc == 0:
        fail(name, "symlinked state.json was accepted")
    elif sentinel in out + err:
        fail(name, "outside cohort-state content reached command output")
    else:
        ok(name)


# STUB: AC3 — a descriptor whose identity changes during the read is rejected.
def test_cohort_state_reader_rejects_identity_change(
    tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "cohort-state-reader-rejects-identity-change"
    sentinel = "identity-change-sentinel"
    spec_dir = make_spec_dir(tmp, name)
    monkeypatch.chdir(tmp)
    path = spec_dir / "state.json"
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "run_id": str(uuid.uuid4()),
            "feature": sentinel,
        }),
        encoding="utf-8",
    )
    import os
    real_fstat = os.fstat
    calls = 0

    def changed_fstat(fd: int):
        nonlocal calls
        calls += 1
        observed = real_fstat(fd)
        if calls < 2:
            return observed
        fields = list(observed)
        fields[1] += 1  # st_ino
        return os.stat_result(fields)

    _mod.os.fstat = changed_fstat
    try:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = _mod.cmd_status(
                _mod.argparse.Namespace(spec_dir=str(spec_dir), json=True)
            )
    finally:
        _mod.os.fstat = real_fstat
    output = stdout.getvalue() + stderr.getvalue()
    if rc == 0:
        fail(name, "public status accepted an identity-changing state read")
    elif calls < 2:
        fail(name, "public status did not verify descriptor identity twice")
    elif sentinel in output:
        fail(name, f"identity-changing content reached output: {output!r}")
    else:
        ok(name)


# STUB: AC3 — managed state has the same 8 MiB cap as shipped file readers.
def test_cohort_state_reader_rejects_over_limit_file(tmp: Path) -> None:
    name = "cohort-state-reader-rejects-over-limit-file"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "state.json").write_bytes(b"x" * (8 * 1024 * 1024 + 1))

    rc, out, err = run_cohort("status", str(spec_dir), "--json")

    if rc == 0:
        fail(name, "over-limit state.json was accepted")
    elif "8388608" not in out + err and "8 MiB" not in out + err:
        fail(name, f"failure did not identify the managed-state size cap: {out} {err}")
    else:
        ok(name)


# STUB: AC3 — managed cohort state must be a regular file.
def test_cohort_state_reader_rejects_non_regular_path(tmp: Path) -> None:
    name = "cohort-state-reader-rejects-non-regular-path"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "state.json").mkdir()

    rc, out, err = run_cohort("status", str(spec_dir), "--json")

    if rc == 0:
        fail(name, "directory state.json was accepted")
    elif "Traceback" in out + err:
        fail(name, f"non-regular state escaped the diagnostic boundary: {out} {err}")
    elif "regular file" not in out + err:
        fail(name, f"failure did not identify the required file type: {out} {err}")
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
    write_spec(spec_dir, status="Approved")
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
    write_spec(spec_dir, status="Approved")
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
    write_spec(spec_dir, status="Approved")
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
    """After approval, changing spec.md and re-running approve-plan refuses."""
    name = "approve-plan-overwrites-hashes"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # First approve-plan: pending → approved
    rc1, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc1 != 0:
        fail(name, f"first approve-plan failed: exit {rc1}")
        return
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # A status-only bump is bookkeeping: approve-plan replays as a no-op.
    write_spec(spec_dir, status="Implementing")
    rc_noop, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc_noop != 0:
        fail(name, f"status bump should replay as a no-op, got exit {rc_noop}")
        return
    # A substantive change must still refuse.
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance criteria\n\n"
        "- [ ] AC1\n- [ ] AC2 added after approval\n", encoding="utf-8")
    rc2, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc2 == 0:
        fail(name, "expected non-zero when spec changed after approval (refusal)")
    elif before != after:
        fail(name, "state.json was mutated despite spec change (should refuse without mutation)")
    else:
        ok(name)


# ── T1: plan check-current ────────────────────────────────────────────────


def test_plan_check_current_not_approved(tmp: Path) -> None:
    name = "plan-check-current-not-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when plan_review_status != approved")
    elif "plan_review_status: pending" not in err:
        fail(name, f"expected 'plan_review_status: pending' sentinel in stderr; got: {err!r}")
    else:
        ok(name)


def test_plan_check_current_changed_spec(tmp: Path) -> None:
    name = "plan-check-current-changed-spec"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    # Substantive change after approval — a *status* bump is bookkeeping and is
    # deliberately hash-neutral, so it would no longer prove anything here.
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance criteria\n\n"
        "- [ ] AC1\n- [ ] AC2 added after approval\n", encoding="utf-8")
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
    write_spec(spec_dir, status="Approved")
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
    write_spec(spec_dir, status="Approved")
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
    (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # No spec.md
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero when spec.md absent")
        return

    write_spec(spec_dir, status="Approved")
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
    write_spec(spec_dir, status="Approved")
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
    write_spec(spec_dir, status="Approved")
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
    write_spec(spec_dir, status="Approved")
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


def test_schedule_prints_implementer_dispatch_reminder(tmp: Path) -> None:
    name = "schedule-prints-implementer-dispatch-reminder"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    rc, out, _ = run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    collapsed_out = " ".join(out.split())
    last_wave_index = collapsed_out.find("wave 2: T2")
    persisted_index = collapsed_out.find("loop-cohort: schedule persisted")
    dispatch_index = collapsed_out.find("loop-cohort: dispatch")
    expected_reminder = (
        "loop-cohort: dispatch — send each task above to one implementer subagent, "
        "one at a time, when that agent is installed; otherwise run them yourself and "
        "note the degradation in the final summary. Scheduling, gates, review and state "
        "stay with you."
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
    elif last_wave_index == -1:
        fail(name, f"final wave missing from stdout: {out!r}")
    elif dispatch_index <= last_wave_index:
        fail(name, f"dispatch reminder did not follow the wave output: {out!r}")
    elif persisted_index == -1:
        fail(name, f"schedule persistence missing from stdout: {out!r}")
    elif dispatch_index <= persisted_index:
        fail(name, f"dispatch reminder did not follow schedule persistence: {out!r}")
    elif not collapsed_out[dispatch_index:].startswith(expected_reminder):
        fail(
            name,
            f"dispatch reminder mismatch: expected {expected_reminder!r}; "
            f"got {collapsed_out[dispatch_index:]!r}",
        )
    else:
        ok(name)


def test_schedule_run_id_mismatch(tmp: Path) -> None:
    name = "schedule-run-id-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
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


def test_schedule_rejects_alternate_plan_path(tmp: Path) -> None:
    """schedule --plan pointing to a different file than plan.md is rejected."""
    name = "schedule-rejects-alternate-plan-path"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # Create an alternate plan file somewhere else
    alt_plan = tmp / "other_plan.md"
    alt_plan.write_text("### T1: other\n\nApproach: other\nTests: no stub\n", encoding="utf-8")
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, _ = run_cohort("schedule", str(spec_dir), "--plan", str(alt_plan),
                          "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when --plan points to alternate file")
    elif before != after:
        fail(name, "state.json mutated despite alternate plan path")
    else:
        ok(name)


def test_schedule_help_states_canonical_plan_path() -> None:
    """The option help must not imply an alternate plan path is accepted."""
    rc, out, err = run_cohort("schedule", "--help")
    assert rc == 0, err
    assert "path to plan.md (must be <spec-dir>/plan.md)" in out


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


def test_record_attempt_invalid_sequence_suffix(tmp: Path) -> None:
    """cycle-id with non-decimal suffix is rejected without mutation."""
    name = "record-attempt-invalid-sequence-suffix"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "implementation_retry_count": 0, "max_implementation_retries": 5,
        "last_record_attempt_cycle_id": None,
    })
    path = spec_dir / "state.json"
    before = path.read_bytes()
    for bad_suffix in ("", "abc", "1.0"):
        rc, _, _ = run_cohort("record-attempt", str(spec_dir), "--phase", "implement",
                              "--cycle-id", f"{run_id}:{bad_suffix}", "--expect-run-id", run_id)
        after = path.read_bytes()
        if rc == 0:
            fail(name, f"expected non-zero for cycle-id suffix {bad_suffix!r}")
            return
        if before != after:
            fail(name, f"state.json mutated despite invalid suffix {bad_suffix!r}")
            return
    ok(name)


# ── T3: review inspect ────────────────────────────────────────────────────


SAMPLE_FINDINGS_REPORT = """\
## Blockers

**1. Missing null check.** `path/to/file.py:42`. The value is never validated. Fix: add guard.

## Nits

**2. Typo in comment.** `path/to/other.py:10`. Misspelling. Fix: fix it.
"""

CLEAN_REPORT = f"Review complete.\n\n{CLEAN_SUBSTRING}\n"
CLEAN_ADJUDICATION = (
    f"## Main-loop result\n{CLEAN_SUBSTRING}\n\n"
    "## Refuted audit\nNone.\n\n## Indeterminate audit\nNone.\n"
)

EMPTY_REPORT = "No findings reported here."


def test_review_inspect_clean(tmp: Path) -> None:
    name = "review-inspect-clean"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    report = tmp / "clean.md"
    report.write_text(CLEAN_REPORT, encoding="utf-8")
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
    report.write_text(SAMPLE_FINDINGS_REPORT, encoding="utf-8")
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
    report.write_text(EMPTY_REPORT, encoding="utf-8")
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
    report.write_text(SAMPLE_FINDINGS_REPORT, encoding="utf-8")
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
    report.write_text(CLEAN_REPORT, encoding="utf-8")
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
    report.write_text(mixed, encoding="utf-8")
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
    report.write_text(CLEAN_ADJUDICATION, encoding="utf-8")
    rc, _, _ = run_cohort("review", "record", str(spec_dir), "--report", str(report),
                          "--adjudication",
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
    report.write_text(SAMPLE_FINDINGS_REPORT, encoding="utf-8")
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


def test_review_record_fingerprint_invalid_format(tmp: Path) -> None:
    """Non-canonical fingerprints (wrong length, uppercase) are rejected without mutation."""
    name = "review-record-fp-invalid-format"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    path = spec_dir / "state.json"
    before = path.read_bytes()
    for bad_fp in ("abc", "A" * 40, "a" * 39):
        rc, _, _ = run_cohort("review", "record", str(spec_dir),
                              "--fingerprint", bad_fp, "--expect-run-id", run_id)
        after = path.read_bytes()
        if rc == 0:
            fail(name, f"expected non-zero for fingerprint {bad_fp!r}")
            return
        if before != after:
            fail(name, f"state.json mutated despite invalid fingerprint {bad_fp!r}")
            return
    ok(name)


def test_review_record_all_skipped(tmp: Path) -> None:
    """--all-skipped bumps review_round_count and clears fingerprints without a report."""
    name = "review-record-all-skipped"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "review_round_count": 2, "review_retry_count": 1, "max_review_retries": 5,
        "finding_fingerprints": ["a" * 40], "previous_finding_fingerprints": [],
    })
    rc, _, _ = run_cohort("review", "record", str(spec_dir),
                          "--all-skipped", "--expect-run-id", run_id)
    if rc != 0:
        fail(name, "expected exit 0 for --all-skipped")
        return
    state = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    if state.get("review_round_count") != 3:
        fail(name, f"expected review_round_count=3; got {state.get('review_round_count')}")
    elif state.get("review_retry_count") != 1:
        fail(name, "review_retry_count should be unchanged by --all-skipped")
    elif state.get("finding_fingerprints") != []:
        fail(name, "finding_fingerprints should be cleared by --all-skipped")
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
    report.write_text(CLEAN_ADJUDICATION, encoding="utf-8")
    run_cohort(
        "review", "record", str(spec_dir), "--report", str(report), "--adjudication",
        "--expect-run-id", run_id
    )
    # Now inspect the same findings report
    findings_report = tmp / "findings3.md"
    findings_report.write_text(SAMPLE_FINDINGS_REPORT, encoding="utf-8")
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


def test_skill_shows_every_clean_recording_form(tmp: Path) -> None:
    """The operator copies these commands; a missing form is a dead end.

    A clean security review always carries the mandatory `## Not checked`
    footer, so `--direct-clean-file` refuses it. If the skill shows only that
    form, the layer's headline case has no documented command.
    """
    name = "skill-clean-recording-forms"
    text = (_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    # Scope to the fenced block the operator copies from. A file-wide search
    # passes on any prose mention of a flag, which is how a guard stops being
    # able to fail. Anchor on `--all-skipped`, which appears only here, and take
    # the fence around it — "reviewers-clean" also appears in PLAN's block.
    anchor = text.index("--all-skipped")
    block = text[text.rindex("```", 0, anchor) : text.index("```", anchor)]
    missing = [
        form
        for form in (
            "--direct-clean-file",
            "--structural-clean-file",
            "--report <adjudication-report-path> --adjudication",
            "--all-skipped",
        )
        if form not in block
    ]
    if missing:
        fail(name, f"SKILL.md omits clean recording form(s): {missing}")
    else:
        ok(name)


def test_structural_clean_digest_comes_from_the_classified_read(tmp: Path) -> None:
    """The audit anchor must digest the bytes that were classified.

    Instrumented rather than source-inspecting: the reader is stubbed to return
    different content on a second call, so a re-read through *any* helper — not
    just a literal `read_bytes()` — produces a digest that provably describes
    bytes nobody classified.
    """
    name = "structural-clean-digest-provenance"
    module = _mod
    first = "Clean — ready to commit.\n"
    second = "Clean — ready to commit.\n## Not checked\n- Did not fuzz.\n"
    calls: list[str] = []

    def stub(path, label):
        calls.append(label)
        return first if len(calls) == 1 else second

    original = module.read_managed_text
    module.read_managed_text = stub
    try:
        result = module._classify_raw_report(tmp / "report.md")
        # A second read would digest `second`; the classified read saw `first`.
        expected = hashlib.sha256(first.encode("utf-8")).hexdigest()
        wrong = hashlib.sha256(second.encode("utf-8")).hexdigest()
        if result["_classified_digest"] == wrong:
            fail(name, "digest describes a later read, not the classified bytes")
        elif result["_classified_digest"] != expected:
            fail(name, f"digest {result['_classified_digest']} is neither read")
        elif len(calls) != 1:
            fail(name, f"classifier read the artifact {len(calls)} times, expected 1")
        else:
            ok(name)
    finally:
        module.read_managed_text = original


def test_record_path_never_rereads_for_its_digest(tmp: Path) -> None:
    """`cmd_review_record` must consume the classified digest, not reopen.

    Source-structural, and narrowly so: it rejects *any* re-read helper in that
    branch, not just a literal `read_bytes()`. The instrumented behavioural proof
    that one read happened lives in
    `test_structural_clean_digest_comes_from_the_classified_read`; this one pins
    that the recorder consumes it rather than taking its own.
    """
    name = "record-digest-no-reread"
    source = (_SKILL_DIR / "scripts" / "loop-cohort.py").read_text(encoding="utf-8")
    start = source.index("elif structural_clean_file :=")
    branch = source[start : source.index("    else:", start)]
    rereads = [c for c in ("read_bytes(", "read_text(", "read_managed_text(", "open(")
               if c in branch]
    if rereads:
        fail(name, f"structural-clean branch reopens the artifact via {rereads}")
    elif "_classified_digest" not in branch:
        fail(name, "structural-clean branch does not consume the classified digest")
    else:
        ok(name)


def test_raw_refusal_reasons_are_closed_and_reachable(tmp: Path) -> None:
    """Every declared refusal code must be produced by some real report."""
    name = "raw-refusal-reasons"
    bodies = {
        "sentinel-absent": "## Not checked\n- Did not fuzz.\n",
        "sentinel-repeated": "Clean — ready to commit.\nClean — ready to commit.\n",
        "content-before-sentinel": "Preamble.\nClean — ready to commit.\n",
        "footer-heading-repeated": (
            "Clean — ready to commit.\n## Not checked\n- a\n## Not checked\n- b\n"
        ),
        "footer-bullet-malformed": "Clean — ready to commit.\n## Not checked\nnot a bullet\n",
        "unpermitted-content": "Clean — ready to commit.\nLooks good.\n",
    }
    produced = set()
    for expected, body in bodies.items():
        report = tmp / f"{expected}.md"
        report.write_text(body, encoding="utf-8", newline="")
        result = _mod._classify_raw_report(report)
        if result["classification"] != "invalid":
            fail(name, f"{expected!r} body classified {result['classification']}")
            return
        if result["_reason"] != expected:
            fail(name, f"expected reason {expected!r}, got {result['_reason']!r}")
            return
        produced.add(result["_reason"])
    # `unreadable` needs a missing file rather than a body.
    missing = _mod._classify_raw_report(tmp / "absent.md")
    if missing["_reason"] != "unreadable":
        fail(name, f"missing file gave reason {missing['_reason']!r}")
        return
    produced.add("unreadable")
    unreachable = set(_mod.RAW_REFUSAL_REASONS) - produced
    if unreachable:
        fail(name, f"declared but unreachable refusal codes: {sorted(unreachable)}")
    else:
        ok(name)


def test_clean_source_replay_forms_are_exhaustive(tmp: Path) -> None:
    """Resumption must map each persisted clean source to its own command form.

    Scoped to the `reviewers-clean` table row. A file-wide search passes while
    that row is removed, reordered, or mis-mapped, as long as the strings survive
    anywhere in the document.
    """
    name = "clean-source-replay-forms"
    text = (_SKILL_DIR / "references" / "session-resumption.md").read_text(encoding="utf-8")
    # Two rows carry this event — the spec gate and the code gate. Replay of a
    # recorded clean round belongs to the CODE-HUMAN-GATE row.
    rows = [
        ln
        for ln in text.splitlines()
        if ln.lstrip().startswith("| `reviewers-clean`") and "`CODE-HUMAN-GATE`" in ln
    ]
    if len(rows) != 1:
        fail(name, f"expected one reviewers-clean CODE-HUMAN-GATE row, found {len(rows)}")
        return
    row = rows[0]
    required = (
        '`"direct-clean"` → `--direct-clean-file <raw-path>`',
        '`"structural-clean"` → `--structural-clean-file <raw-path>`',
        '`"report"` → `--report <adjudication-path> --adjudication`',
    )
    missing = [form for form in required if form not in row]
    if missing:
        fail(name, f"reviewers-clean row omits replay form(s): {missing}")
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
    """parse_findings must produce sha256('<file>|<line>|<title>') per finding."""
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
    expected_fp = hashlib.sha256(expected_key.encode("utf-8")).hexdigest()
    if fps[0] != expected_fp:
        fail(name, f"fingerprint mismatch: {fps[0]!r} != {expected_fp!r}")
    else:
        ok(name)


def test_parse_findings_specialist_formats(tmp: Path) -> None:
    """parse_findings handles frontend-reviewer and experience-reviewer formats."""
    name = "parse-findings-specialist-formats"
    # frontend-reviewer: unquoted file:line
    fe_report = "**1. Token drift.** src/styles.css:42. Lens: CSS. Fix: use token.\n"
    fps_fe = parse_findings(fe_report)
    fe_key = "src/styles.css|42|**1. Token drift.**"
    fe_fp = hashlib.sha256(fe_key.encode("utf-8")).hexdigest()
    if len(fps_fe) != 1:
        fail(name, f"frontend-reviewer: expected 1 fingerprint; got {len(fps_fe)}")
        return
    if fps_fe[0] != fe_fp:
        fail(name, f"frontend-reviewer fingerprint mismatch: {fps_fe[0]!r} != {fe_fp!r}")
        return
    # experience-reviewer: Where: <location>
    exp_report = (
        "**1. Incoherent contrast.** Where: Hero screen. "
        "What's wrong: grounded fit. Fix: raise contrast.\n"
    )
    fps_exp = parse_findings(exp_report)
    exp_key = "Hero screen|0|**1. Incoherent contrast.**"
    exp_fp = hashlib.sha256(exp_key.encode("utf-8")).hexdigest()
    if len(fps_exp) != 1:
        fail(name, f"experience-reviewer: expected 1 fingerprint; got {len(fps_exp)}")
        return
    if fps_exp[0] != exp_fp:
        fail(name, f"experience-reviewer fingerprint mismatch: {fps_exp[0]!r} != {exp_fp!r}")
        return
    ok(name)


def test_classify_report_ship_it_clean(tmp: Path) -> None:
    """review inspect classifies 'SHIP IT' reports as clean (specialist reviewer verdicts)."""
    name = "classify-report-ship-it-clean"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {"schema_version": 1, "run_id": run_id, "finding_fingerprints": []})
    report = tmp / "ship_it.md"
    report.write_text("## Verdict\nSHIP IT\n\n## What's working\nAll good.\n", encoding="utf-8")
    rc, out, _ = run_cohort("review", "inspect", str(spec_dir), "--report", str(report), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("classification") != "clean":
        fail(name, f"expected classification=clean; got {data.get('classification')!r}")
    else:
        ok(name)


def test_validate_run_id_rejects_wrong_schema(tmp: Path) -> None:
    """_validate_run_id rejects state with schema_version != 1 before checking run_id."""
    name = "validate-run-id-rejects-wrong-schema"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 99, "run_id": run_id,
        "review_round_count": 0, "review_retry_count": 0, "max_review_retries": 5,
        "finding_fingerprints": [], "previous_finding_fingerprints": [],
    })
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, _ = run_cohort("review", "record", str(spec_dir),
                          "--fingerprint", "a" * 40, "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when schema_version != 1")
    elif before != after:
        fail(name, "state.json mutated despite wrong schema_version")
    else:
        ok(name)


def test_canonical_contract_normalization(tmp: Path) -> None:
    name = "canonical-contract-normalization"
    crlf_text = "line1  \r\nline2\r\n"
    result = canonical_contract(crlf_text)
    if "\r" in result:
        fail(name, "CRLF not normalized")
    elif any(line != line.rstrip() for line in result.split("\n")):
        fail(name, "trailing whitespace not stripped")
    else:
        ok(name)


def test_schedule_accepts_level2_task_headings(tmp: Path) -> None:
    """schedule parses '## T<n>' (level-2) headings for backward-compatible plans."""
    name = "schedule-accepts-level2-headings"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    level2_plan = (
        "# Plan\n\n- **Status:** Approved\n\n"
        "## T1\n\n**Depends on:** none\n\n## T2\n\n**Depends on:** T1\n"
    )
    write_plan(spec_dir, content=level2_plan)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    rc, _, err = run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"schedule rejected level-2 headings: exit {rc} — {err.strip()}")
    else:
        ok(name)


# ── T3: approve-plan idempotency and status visibility ───────────────────


def test_approve_plan_first_write(tmp: Path) -> None:
    """pending → approved: records hashes, exits 0 (first-write path)."""
    name = "approve-plan-first-write"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    rc, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0 on first write; got {rc}")
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


def test_approve_plan_idempotent_no_op(tmp: Path) -> None:
    """Same run_id + unchanged files → exit 0; state bytes not rewritten (no-op)."""
    name = "approve-plan-idempotent-no-op"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, out, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc != 0:
        fail(name, f"expected exit 0 on idempotent replay; got {rc}")
    elif before != after:
        fail(name, "state.json was rewritten on idempotent replay (bytes must be unchanged)")
    elif "no-op" not in out:
        fail(name, f"expected 'no-op' in stdout; got {out!r}")
    else:
        ok(name)


def test_approve_plan_refuses_changed_spec(tmp: Path) -> None:
    """spec.md modified after approval → non-zero, no mutation."""
    name = "approve-plan-refuses-changed-spec"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # Substantive modification — a status bump is now hash-neutral by design.
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance criteria\n\n"
        "- [ ] AC1\n- [ ] AC2 added after approval\n", encoding="utf-8")
    rc, _, err = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when spec changed after approval")
    elif before != after:
        fail(name, "state.json was mutated despite spec change")
    elif "spec_changed=True" not in err:
        fail(name, f"expected 'spec_changed=True' in stderr; got {err!r}")
    else:
        ok(name)


def test_approve_plan_refuses_changed_plan(tmp: Path) -> None:
    """plan.md modified after approval → non-zero, no mutation."""
    name = "approve-plan-refuses-changed-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # Modify plan.md after approval
    write_plan(spec_dir, content="# Plan (modified)\n\n### T1\n\n**Depends on:** none\n")
    rc, _, err = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when plan changed after approval")
    elif before != after:
        fail(name, "state.json was mutated despite plan change")
    elif "plan_changed=True" not in err:
        fail(name, f"expected 'plan_changed=True' in stderr; got {err!r}")
    else:
        ok(name)


def test_approve_plan_refuses_unapproved_spec(tmp: Path) -> None:
    """approve-plan on first call must refuse if spec.md does not have Status: Approved."""
    name = "approve-plan-refuses-unapproved-spec"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, err = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when spec.md has Status: Draft")
    elif before != after:
        fail(name, "state.json was mutated despite unapproved spec (crash-window guard)")
    elif "expected Approved" not in err:
        fail(name, f"expected 'expected Approved' in stderr; got {err!r}")
    else:
        ok(name)


def test_approve_plan_refuses_unapproved_plan(tmp: Path) -> None:
    """approve-plan on first call must refuse if plan.md does not have Status: Approved."""
    name = "approve-plan-refuses-unapproved-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir, status=None)  # no Status field — simulates plan reverted in crash window
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, _, err = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when plan.md has no Status: Approved")
    elif before != after:
        fail(name, "state.json was mutated despite unapproved plan (crash-window guard)")
    elif "expected Approved" not in err:
        fail(name, f"expected 'expected Approved' in stderr; got {err!r}")
    else:
        ok(name)


def test_approve_plan_refuses_run_id_mismatch(tmp: Path) -> None:
    """run_id mismatch when already approved → non-zero, no mutation."""
    name = "approve-plan-refuses-run-id-mismatch"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # First call: transitions to approved
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # Second call with wrong run_id (plan_review_status is now "approved")
    rc, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", "wrong-run-id")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero on run_id mismatch when already approved")
    elif before != after:
        fail(name, "state.json was mutated despite run_id mismatch")
    else:
        ok(name)


def test_approve_plan_state_preserved_on_refusal(tmp: Path) -> None:
    """Raw state bytes are identical before and after any refused approve-plan call."""
    name = "approve-plan-state-preserved-on-refusal"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    path = spec_dir / "state.json"
    # Scenario A: substantively changed spec after approval. A status bump is
    # hash-neutral by design, so it would leave this case green while no longer
    # exercising the refusal the test name claims.
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance criteria\n\n"
        "- [ ] AC1\n- [ ] AC2 added after approval\n", encoding="utf-8")
    before_a = path.read_bytes()
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after_a = path.read_bytes()
    if before_a != after_a:
        fail(name, "state.json mutated after changed-spec refusal")
        return
    # Scenario B: changed plan after approval (reset first)
    run_cohort("reset", str(spec_dir))
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    write_plan(spec_dir, content="# Plan changed\n\n### T1\n\n**Depends on:** none\n")
    before_b = path.read_bytes()
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after_b = path.read_bytes()
    if before_b != after_b:
        fail(name, "state.json mutated after changed-plan refusal")
    else:
        ok(name)


def test_cohort_status_json_includes_plan_review_status_pending(tmp: Path) -> None:
    """status --json output includes plan_review_status=pending after init."""
    name = "cohort-status-json-plan-review-status-pending"
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
        fail(name, f"expected JSON output; got {out!r}")
        return
    if "plan_review_status" not in data:
        fail(name, "plan_review_status absent from status --json output")
    elif data["plan_review_status"] != "pending":
        fail(name, f"expected plan_review_status=pending; got {data['plan_review_status']!r}")
    else:
        ok(name)


def test_cohort_status_json_includes_plan_review_status_approved(tmp: Path) -> None:
    """status --json output includes plan_review_status=approved after approve-plan."""
    name = "cohort-status-json-plan-review-status-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    rc, out, _ = run_cohort("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"expected JSON output; got {out!r}")
        return
    if "plan_review_status" not in data:
        fail(name, "plan_review_status absent from status --json output")
    elif data["plan_review_status"] != "approved":
        fail(name, f"expected plan_review_status=approved; got {data['plan_review_status']!r}")
    else:
        ok(name)


def test_crash_after_plan_approved_before_approve_plan(tmp: Path) -> None:
    """Crash window: engine moved to SPEC-PLAN-APPROVED but cohort approve-plan not yet run.
    Recovery: approve-plan runs as a normal first write (plan_review_status was pending)."""
    name = "crash-after-plan-approved-before-approve-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # Cohort state: plan_review_status="pending" (initial after init) — approve-plan not run yet
    rc, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"recovery approve-plan failed: exit {rc}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if state.get("plan_review_status") != "approved":
        fail(name, "plan_review_status not approved after recovery approve-plan")
    else:
        ok(name)


def test_crash_after_approve_plan_before_schedule(tmp: Path) -> None:
    """Crash window: approve-plan done, schedule not yet run.
    Recovery: approve-plan is an idempotent no-op; schedule then runs normally."""
    name = "crash-after-approve-plan-before-schedule"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # First approve-plan: records hashes
    run_cohort("approve-plan", str(spec_dir), "--run-id", run_id)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # Recovery step 1: approve-plan again (should be no-op)
    rc1, out1, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc1 != 0:
        fail(name, f"idempotent approve-plan failed: exit {rc1}")
        return
    if before != after:
        fail(name, "state.json was rewritten on idempotent approve-plan replay")
        return
    # Recovery step 2: schedule runs normally
    rc2, _, _ = run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    if rc2 != 0:
        fail(name, f"schedule failed after idempotent approve-plan: exit {rc2}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    if not state.get("schedule_waves"):
        fail(name, "schedule_waves not populated after schedule")
    else:
        ok(name)


def test_crash_after_schedule_before_plan_locked(tmp: Path) -> None:
    """Crash window: schedule done, plan-locked not yet fired.
    Recovery: approve-plan is no-op; plan check-current --require-schedule passes."""
    name = "crash-after-schedule-before-plan-locked"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    # State: approve-plan done, schedule done — plan-locked not yet fired (crash point)
    path = spec_dir / "state.json"
    before = path.read_bytes()
    # Recovery step 1: approve-plan is a no-op
    rc1, _, _ = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    after = path.read_bytes()
    if rc1 != 0:
        fail(name, f"idempotent approve-plan failed: exit {rc1}")
        return
    if before != after:
        fail(name, "state.json was rewritten on idempotent approve-plan replay")
        return
    # Recovery step 2: plan check-current --require-schedule should pass
    rc2, _, err2 = run_cohort("plan", "check-current", str(spec_dir), "--require-schedule")
    if rc2 != 0:
        fail(name, f"plan check-current --require-schedule failed: exit {rc2} — {err2.strip()}")
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


# ── STUBS: docs/specs/loop-tooling-mandated-writes, task T1 ─────────────────
#
# They encode the invariant the pin is *supposed* to hold: the loop's own
# mandated bookkeeping writes must not move the hash, while anything that
# changes approved scope still must.
#
# Only the first is red today. The second is a must-still-pass guard — the
# current raw-byte hash already catches it, and the point is that the
# canonicalization of T1 must not stop catching it.


# STUB: AC4
def test_stub_lifecycle_status_bump_keeps_pin(tmp: Path) -> None:
    """STUB: AC4. SKILL.md's EXECUTE step mandates spec `Status: Implementing` before
    any code, and its finish checklist mandates spec `Shipped` / plan `Done`. None of
    those writes may move the approved baseline."""
    name = "stub-lifecycle-status-bump-keeps-pin"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    for spec_status, plan_status in (("Implementing", "Approved"),
                                     ("Shipped", "Done")):
        write_spec(spec_dir, status=spec_status)
        write_plan(spec_dir, status=plan_status)
        rc_plan, _, err_plan = run_cohort(
            "plan", "check-current", str(spec_dir), "--require-schedule")
        if rc_plan != 0:
            fail(name, f"plan check-current went red on spec={spec_status} "
                       f"plan={plan_status}: {err_plan!r}")
            return
        rc_sched, _, err_sched = run_cohort(
            "schedule", "check-current", str(spec_dir))
        if rc_sched != 0:
            fail(name, f"schedule check-current went red on spec={spec_status} "
                       f"plan={plan_status}: {err_sched!r}")
            return
    ok(name)


# STUB: AC4
def test_stub_lifecycle_bump_with_vocabulary_comment(tmp: Path) -> None:
    """STUB: AC4, on the shape real specs actually have.

    Every spec and plan the template emits carries the status token a second time
    inside the trailing vocabulary comment. `write_spec` / `write_plan` emit no
    comment, so a `str.replace(token, ...)` implementation normalizes both
    occurrences, produces a different digest per status, and fails every real
    spec while the other fixtures stay green. Only a span-bounded splice of the
    token itself passes this.
    """
    name = "stub-lifecycle-bump-with-vocabulary-comment"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    spec_vocab = "<!-- Draft | Approved | Implementing | Shipped | Archived -->"
    plan_vocab = "<!-- Drafting | Approved | Executing | Done -->"

    def write_real(spec_status: str, plan_status: str) -> None:
        (spec_dir / "spec.md").write_text(
            f"# Spec\n\n- **Status:** {spec_status} {spec_vocab}\n\n"
            "## Acceptance criteria\n\n- [ ] AC1\n", encoding="utf-8")
        (spec_dir / "plan.md").write_text(
            f"# Plan\n\n- **Status:** {plan_status} {plan_vocab}\n\n"
            "### T1\n\n**Depends on:** none\n", encoding="utf-8")

    write_real("Approved", "Approved")
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    for spec_status, plan_status in (("Implementing", "Approved"),
                                     ("Shipped", "Done")):
        write_real(spec_status, plan_status)
        rc, _, err = run_cohort("plan", "check-current", str(spec_dir),
                                "--require-schedule")
        if rc != 0:
            fail(name, f"went red on spec={spec_status} plan={plan_status} "
                       f"with the vocabulary comment present: {err!r}")
            return
    ok(name)


# STUB: AC6
def test_stub_status_line_smuggling_still_caught(tmp: Path) -> None:
    """STUB: AC6. Only the status *token* is bookkeeping. Free text appended
    after it sits inside the approved contract and must still trip the pin."""
    name = "stub-status-line-smuggling-still-caught"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Implementing — scope now also covers "
        "deleting packages/credbroker\n\n## Acceptance criteria\n\n- [ ] AC1\n",
        encoding="utf-8",
    )
    rc, _, _ = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "free text appended after the status token passed the pin")
    else:
        ok(name)


# ── AC1/AC5-AC10: the criteria mutation testing proved unverified ───────────
#
# Every case below was written against a mutation: remove the behaviour it
# names from loop-cohort.py and this case must go red. A case that survives its
# own mutation is not coverage.

def _approved_run(tmp: Path, name: str) -> tuple[Path, str]:
    """A spec dir past approve-plan + schedule, with a realistic spec shape."""
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved "
        "<!-- Draft | Approved | Implementing | Shipped | Archived -->\n\n"
        "## Acceptance Criteria\n\n- [ ] AC1 first\n- [ ] AC2 second\n",
        encoding="utf-8")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    return spec_dir, run_id


def _check(spec_dir: Path) -> int:
    rc, _, _ = run_cohort("plan", "check-current", str(spec_dir), "--require-schedule")
    return rc


def test_ac5_ticking_a_criterion_is_bookkeeping(tmp: Path) -> None:
    """AC5. SKILL.md's finish checklist mandates ticking every AC."""
    name = "ac5-ticking-a-criterion-is-bookkeeping"
    spec_dir, _ = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- [ ] AC1 first", "- [x] AC1 first")
        .replace("- [ ] AC2 second", "- [x] AC2 second"), encoding="utf-8")
    ok(name) if _check(spec_dir) == 0 else fail(name, "ticking an AC broke the pin")


def test_ac1_reindenting_a_criterion_is_scope(tmp: Path) -> None:
    """AC1. Only the bracket contents are normalized. A whole-match
    substitution would also eat the indentation, so nesting AC2 under AC1 —
    which changes what the list contains — would hash identically."""
    name = "ac1-reindenting-a-criterion-is-scope"
    spec_dir, _ = _approved_run(tmp, name)
    # The box must be TICKED: the splice only fires on `[x]`, so re-indenting an
    # unticked line would move the digest through the raw bytes and prove
    # nothing about the splice.
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- [ ] AC2 second", "- [x] AC2 second"), encoding="utf-8")
    if _check(spec_dir) != 0:
        fail(name, "ticking alone broke the pin — precondition failed")
        return
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- [x] AC2 second", "  - [x] AC2 second"), encoding="utf-8")
    fail(name, "re-indenting a ticked criterion passed the pin") if _check(spec_dir) == 0 else ok(name)


def test_ac5_checkbox_outside_the_ac_section_is_scope(tmp: Path) -> None:
    """AC5's boundary. A checkbox under `## Boundaries` is not progress
    bookkeeping — `Never do` items are exactly the scope the pin protects."""
    name = "ac5-checkbox-outside-ac-section-is-scope"
    spec_dir2, _ = _approved_run(tmp, name + "-2")
    (spec_dir2 / "spec.md").write_text(
        (spec_dir2 / "spec.md").read_text(encoding="utf-8")
        + "\n## Boundaries\n\n- [ ] Never delete the database\n", encoding="utf-8")
    run_id2 = json.loads((spec_dir2 / "state.json").read_text())["run_id"]
    run_cohort("reset", str(spec_dir2))
    run_cohort("init", str(spec_dir2), "--run-id", run_id2)
    run_cohort("approve-plan", str(spec_dir2), "--expect-run-id", run_id2)
    run_cohort("schedule", str(spec_dir2), "--expect-run-id", run_id2)
    (spec_dir2 / "spec.md").write_text(
        (spec_dir2 / "spec.md").read_text(encoding="utf-8")
        .replace("- [ ] Never delete the database", "- [x] Never delete the database"),
        encoding="utf-8")
    fail(name, "ticking a Boundaries checkbox passed the pin") if _check(spec_dir2) == 0 else ok(name)


def test_ac7_body_status_line_is_pinned(tmp: Path) -> None:
    """AC7. Unit-level on purpose.

    The preamble scan `break`s at the first `**Status:**`, so when a preamble
    status exists a body occurrence is unreachable and the section guard is
    unobservable. The shape where the guard *is* load-bearing — status only in
    the body — cannot reach `approve-plan` at all, because its crash-window
    guard requires a parseable `Approved` in the preamble. So the guard is
    defense-in-depth for any caller of the pure function, and that is the level
    it has to be tested at; a CLI round trip here passes on the pending
    sentinel and proves nothing.
    """
    name = "ac7-body-status-line-is-pinned"
    body = ("# Spec\n\n## Notes\n\nQuoting the template:\n\n"
            "    - **Status:** {token}\n")
    draft = canonical_contract(body.format(token="Draft"))
    shipped = canonical_contract(body.format(token="Shipped"))
    if draft == shipped:
        fail(name, "a body-section Status token was normalized away")
        return
    # And the preamble one still is, in the same document shape.
    pre = "# Spec\n\n- **Status:** {t}\n\n## Notes\n\n- **Status:** Draft\n"
    if canonical_contract(pre.format(t="Approved")) != canonical_contract(pre.format(t="Shipped")):
        fail(name, "the preamble token was not normalized")
        return
    ok(name)


def test_ac1_splice_preserves_indentation(tmp: Path) -> None:
    """AC1, unit-level. A whole-match substitution would collapse the leading
    whitespace and the bullet run, making a re-indent invisible."""
    name = "ac1-splice-preserves-indentation"
    head = "# S\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n"
    flat = canonical_contract(head + "- [x] AC1\n")
    nested = canonical_contract(head + "  - [x] AC1\n")
    ticked = canonical_contract(head + "- [x] AC1\n")
    unticked = canonical_contract(head + "- [ ] AC1\n")
    if flat == nested:
        fail(name, "re-indenting a ticked criterion did not move the digest")
    elif ticked != unticked:
        fail(name, "ticking a criterion moved the digest")
    else:
        ok(name)


def test_ac8_deferral_annotation_is_scope(tmp: Path) -> None:
    """AC8. Deferring a criterion is a scope change, not progress."""
    name = "ac8-deferral-annotation-is-scope"
    spec_dir, _ = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- [ ] AC2 second", "- [ ] AC2 second (deferred: some-slug)"),
        encoding="utf-8")
    fail(name, "a deferral annotation passed the pin") if _check(spec_dir) == 0 else ok(name)


def test_ac8_status_annotation_is_scope(tmp: Path) -> None:
    """AC8. extract_status_token truncates at ' (', so a dated annotation is
    outside the token and stays hashed."""
    name = "ac8-status-annotation-is-scope"
    spec_dir, _ = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- **Status:** Approved <!--", "- **Status:** Shipped (2026-01-01) <!--"),
        encoding="utf-8")
    fail(name, "a dated status annotation passed the pin") if _check(spec_dir) == 0 else ok(name)


def test_ac6_changed_task_text_is_scope(tmp: Path) -> None:
    """AC6. Task text and dependency edges are the build strategy."""
    name = "ac6-changed-task-text-is-scope"
    spec_dir, _ = _approved_run(tmp, name)
    write_plan(spec_dir, content="# Plan\n\n- **Status:** Approved\n\n"
               "### T1 do something else\n\n**Depends on:** none\n\n"
               "### T2\n\n**Depends on:** T1\n")
    fail(name, "changed task text passed the pin") if _check(spec_dir) == 0 else ok(name)


def test_ac6_changed_depends_on_is_scope(tmp: Path) -> None:
    """AC6. Re-wiring the DAG changes what may run in parallel."""
    name = "ac6-changed-depends-on-is-scope"
    spec_dir, _ = _approved_run(tmp, name)
    write_plan(spec_dir, content="# Plan\n\n- **Status:** Approved\n\n"
               "### T1\n\n**Depends on:** none\n\n"
               "### T2\n\n**Depends on:** none\n")
    fail(name, "a changed Depends on passed the pin") if _check(spec_dir) == 0 else ok(name)


def test_ac9_regressed_spec_status_stops(tmp: Path) -> None:
    """AC9. The byte hash used to catch a status regression incidentally;
    normalizing the token out means it must be asserted directly."""
    name = "ac9-regressed-spec-status-stops"
    spec_dir, _ = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- **Status:** Approved <!--", "- **Status:** Draft <!--"),
        encoding="utf-8")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir), "--require-schedule")
    if rc == 0:
        fail(name, "a spec regressed to Draft passed")
    elif "Status is 'Draft'" not in err:
        fail(name, f"stopped, but not for the status reason: {err!r}")
    else:
        ok(name)


def test_ac9_absent_plan_status_is_skipped(tmp: Path) -> None:
    """AC9. Plan fixtures carry no status line; the assertion must not turn a
    CODE-* pre-guard red for them."""
    name = "ac9-absent-plan-status-is-skipped"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir, status=None)  # no status line at all
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    rc, _, err = run_cohort("schedule", "check-current", str(spec_dir))
    ok(name) if rc == 0 else fail(name, f"a status-less plan went red: {err!r}")


def test_ac9_pending_sentinel_survives(tmp: Path) -> None:
    """AC9's ordering. The `plan_review_status: pending` sentinel is the
    documented PLAN-time cue; a status assertion placed before the early return
    would replace it with a Draft complaint on every PLAN invocation."""
    name = "ac9-pending-sentinel-survives"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "expected non-zero before approval")
    elif "plan_review_status: pending" not in err:
        fail(name, f"sentinel replaced by another message: {err!r}")
    else:
        ok(name)


def test_ac10_mismatch_names_both_causes(tmp: Path) -> None:
    """AC10. The verb cannot tell an unapproved scope change from a
    pre-canonical baseline, so it must not assert either one."""
    name = "ac10-mismatch-names-both-causes"
    spec_dir, run_id = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- [ ] AC2 second", "- [ ] AC2 rewritten"), encoding="utf-8")
    seen = []
    _, _, e1 = run_cohort("plan", "check-current", str(spec_dir), "--require-schedule")
    seen.append(("plan check-current spec", e1))
    _, _, e2 = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    seen.append(("approve-plan idempotency", e2))
    write_plan(spec_dir, content="# Plan\n\n- **Status:** Approved\n\n### T9\n\n**Depends on:** none\n")
    _, _, e3 = run_cohort("schedule", "check-current", str(spec_dir))
    seen.append(("schedule check-current", e3))
    missing = [label for label, msg in seen if "predates canonical hashing" not in msg
               and "before canonical hashing" not in msg]
    fail(name, f"sites missing the both-causes wording: {missing}") if missing else ok(name)


def test_ac10_plan_compare_names_both_causes(tmp: Path) -> None:
    """AC10, plan side. The spec compare runs first and returns, so a
    spec-and-plan mismatch never reaches this branch — it needs a plan-only
    change."""
    name = "ac10-plan-compare-names-both-causes"
    spec_dir, _ = _approved_run(tmp, name)
    write_plan(spec_dir, content="# Plan\n\n- **Status:** Approved\n\n"
               "### T1 different\n\n**Depends on:** none\n")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "a plan-only change passed")
    elif "canonical hashing" not in err:
        fail(name, f"plan compare omits the both-causes wording: {err!r}")
    else:
        ok(name)


def test_ac10_plan_hash_desync_names_both_causes(tmp: Path) -> None:
    """AC10, the state-vs-state site. Re-running `schedule` against a legacy
    approved_plan_hash reaches a compare that touches no file."""
    name = "ac10-plan-hash-desync-names-both-causes"
    spec_dir, run_id = _approved_run(tmp, name)
    state = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    state["plan_hash"] = "0" * 64
    (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir), "--require-schedule")
    if rc == 0:
        fail(name, "a desynced plan_hash passed")
    elif "canonical hashing" not in err:
        fail(name, f"the plan_hash compare omits the both-causes wording: {err!r}")
    else:
        ok(name)


def test_ac9_regressed_plan_status_stops(tmp: Path) -> None:
    """AC9, plan side. Deleting plan.md's entry from the legal-status table
    leaves every other case green."""
    name = "ac9-regressed-plan-status-stops"
    spec_dir, _ = _approved_run(tmp, name)
    write_plan(spec_dir, status="Drafting")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "a plan regressed to Drafting passed")
    elif "Status is 'Drafting'" not in err:
        fail(name, f"stopped, but not on the plan status: {err!r}")
    else:
        ok(name)


def test_ac9_approve_plan_replay_checks_status(tmp: Path) -> None:
    """AC9's third site. The already-approved branch returns a clean no-op
    before the crash-window guard, so without its own assertion it reports
    success against a spec that no longer claims to be approved."""
    name = "ac9-approve-plan-replay-checks-status"
    spec_dir, run_id = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_text(
        (spec_dir / "spec.md").read_text(encoding="utf-8")
        .replace("- **Status:** Approved <!--", "- **Status:** Draft <!--"),
        encoding="utf-8")
    rc, out, err = run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    if rc == 0:
        fail(name, f"replay reported success against a Draft spec: {out!r}")
    elif "Status is 'Draft'" not in err:
        fail(name, f"stopped, but not on the status: {err!r}")
    else:
        ok(name)


def test_ac5_plan_task_checkbox_is_bookkeeping(tmp: Path) -> None:
    """AC5, plan side. A plan has no Acceptance Criteria section, so its
    checkboxes are task progress and are normalized file-wide — four plans in
    this repo carry them."""
    name = "ac5-plan-task-checkbox-is-bookkeeping"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    write_spec(spec_dir, status="Approved")
    plan = ("# Plan\n\n- **Status:** Approved\n\n### T1\n\n"
            "**Depends on:** none\n\n- [{m}] wire the thing\n")
    write_plan(spec_dir, content=plan.format(m=" "))
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    write_plan(spec_dir, content=plan.format(m="x"))
    rc, _, err = run_cohort("schedule", "check-current", str(spec_dir))
    ok(name) if rc == 0 else fail(name, f"ticking a plan task broke the pin: {err!r}")


def test_ac5_lowercase_ac_heading_still_normalizes(tmp: Path) -> None:
    """AC5. The AC-section scan is case-insensitive on purpose: the shared
    linter matches `Acceptance Criteria` exactly, so specs spelling it with a
    lowercase `c` would otherwise get no normalization at all."""
    name = "ac5-lowercase-ac-heading-still-normalizes"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    run_cohort("init", str(spec_dir), "--run-id", run_id)
    body = ("# Spec\n\n- **Status:** Approved\n\n"
            "## Acceptance criteria\n\n- [{m}] AC1 first\n")
    (spec_dir / "spec.md").write_text(body.format(m=" "), encoding="utf-8")
    write_plan(spec_dir)
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    (spec_dir / "spec.md").write_text(body.format(m="x"), encoding="utf-8")
    rc, _, err = run_cohort("plan", "check-current", str(spec_dir))
    ok(name) if rc == 0 else fail(name, f"lowercase heading was not recognized: {err!r}")


def test_ac7_fenced_ac_heading_does_not_open_the_region(tmp: Path) -> None:
    """AC7. A `## Acceptance Criteria` inside a fenced example is documentation,
    not a section boundary — without fence tracking it would open the region
    and un-pin a Boundaries checkbox below it."""
    name = "ac7-fenced-ac-heading-does-not-open-the-region"
    head = "# S\n\n- **Status:** Approved\n\n## Boundaries\n\n"
    fence = "```markdown\n## Acceptance Criteria\n```\n\n"
    never = "- [{m}] Never force-push to main\n"
    unticked = canonical_contract(head + fence + never.format(m=" "))
    ticked = canonical_contract(head + fence + never.format(m="x"))
    ok(name) if unticked != ticked else fail(
        name, "a Boundaries checkbox was un-pinned by a fenced AC heading")


def test_ac5_prose_ac_lead_in_opens_the_region(tmp: Path) -> None:
    """AC5. Two specs here head their criteria with a bold prose lead-in rather
    than a heading. Missing it leaves them with no normalization at all — AC5
    failing by construction for exactly the specs this change is meant to serve."""
    name = "ac5-prose-ac-lead-in-opens-the-region"
    body = ("# S\n\n- **Status:** Approved\n\n"
            "**Acceptance Criteria**\n\n- [{m}] AC1 first\n")
    ok(name) if canonical_contract(body.format(m=" ")) == canonical_contract(body.format(m="x")) \
        else fail(name, "a prose AC lead-in did not open the region")


def test_ac1_h1_closes_the_ac_region(tmp: Path) -> None:
    """AC1. An H1 ends the criteria section as surely as an H2; closing only on
    `##` leaves a later checkbox inside the region and un-pinned."""
    name = "ac1-h1-closes-the-ac-region"
    body = ("# S\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n"
            "- [ ] AC1\n\n# Appendix\n\n- [{m}] Never force-push\n")
    ok(name) if canonical_contract(body.format(m=" ")) != canonical_contract(body.format(m="x")) \
        else fail(name, "a checkbox after an H1 was still treated as a criterion")


def test_unreadable_artifact_reports_from_every_verb(tmp: Path) -> None:
    """A gate that stack-traces on its own input is not a gate. Both branches of
    `approve-plan` reach the artifacts — the pending branch through the
    crash-window guard, the already-approved branch through the hash — and each
    was fixed one round apart, so both need pinning."""
    name = "unreadable-artifact-reports-from-every-verb"
    BAD = b"# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n- [ ] AC1 \xff\xfe\n"
    # The *pending* branch: a fresh cohort, so approve-plan reaches the
    # crash-window guard rather than the already-approved hash compare. The two
    # were fixed a round apart, so each needs driving.
    pend_id = str(uuid.uuid4())
    pend = make_spec_dir(tmp, name + "-pending")
    run_cohort("init", str(pend), "--run-id", pend_id)
    (pend / "spec.md").write_bytes(BAD)
    write_plan(pend)
    rc, out, err = run_cohort("approve-plan", str(pend), "--expect-run-id", pend_id)
    if rc == 0:
        fail(name, "approve-plan (pending) accepted an undecodable spec.md")
        return
    if "Traceback" in err or "Traceback" in out:
        fail(name, f"approve-plan (pending) tracebacked:\n{err[:200]}")
        return

    spec_dir, run_id = _approved_run(tmp, name)
    (spec_dir / "spec.md").write_bytes(BAD)
    for verb in (("approve-plan", str(spec_dir), "--expect-run-id", run_id),
                 ("plan", "check-current", str(spec_dir), "--require-schedule")):
        rc, out, err = run_cohort(*verb)
        if rc == 0:
            fail(name, f"{verb[0]} accepted an undecodable spec.md")
            return
        if "Traceback" in err or "Traceback" in out:
            fail(name, f"{verb[0]} tracebacked instead of reporting:\n{err[:200]}")
            return
    ok(name)


def test_ac9_schedule_check_current_stops_on_regressed_plan(tmp: Path) -> None:
    """AC9's third site, and the one it argues hardest for. Normalizing the
    status token out means a `Drafting` plan no longer moves the hash, so if
    this verb does not assert the token nothing catches it — and this is the
    verb wired into every `CODE-*` pre-guard."""
    name = "ac9-schedule-check-current-stops-on-regressed-plan"
    spec_dir, _ = _approved_run(tmp, name)
    write_plan(spec_dir, status="Drafting")
    rc, _, err = run_cohort("schedule", "check-current", str(spec_dir))
    if rc == 0:
        fail(name, "schedule check-current passed a plan regressed to Drafting")
    elif "Status is 'Drafting'" not in err:
        fail(name, f"stopped, but not on the plan status: {err!r}")
    else:
        ok(name)


def test_ac2_multiline_preamble_comment_keeps_line_indices(tmp: Path) -> None:
    """AC2's comment-stripping bridge. `parse_status` strips HTML comments with
    a plain `sub("", text)` under re.DOTALL, which collapses a multiline comment
    to nothing and shifts every later line index. The canonicalizer needs the
    index to map back to the raw line it rewrites, so it substitutes a
    newline-preserving replacement instead.

    18 spec/plan files in this tree carry a multiline preamble comment — the
    exact population this fix serves — and no fixture emitted that shape, so
    the plain-sub mutation survived every other case.
    """
    name = "ac2-multiline-preamble-comment-keeps-line-indices"
    body = ("# Spec\n\n"
            "<!--\n  a preamble note\n  spanning three lines\n-->\n\n"
            "- **Status:** {t}\n\n## Acceptance Criteria\n\n- [ ] AC1\n")
    if canonical_contract(body.format(t="Approved")) == canonical_contract(body.format(t="Shipped")):
        ok(name)
    else:
        fail(name, "a status bump moved the digest when a multiline comment "
                   "preceded the status line — the line index did not map back")


def test_ac9_comment_only_status_is_skipped(tmp: Path) -> None:
    """AC9. `extract_status_token` returns "" — not None — when the status value
    is only an HTML comment, so an `is not None` guard stops on it. AC9 promises
    absent *or unparseable* is skipped, and that promise is the whole safety
    argument for wiring the assertion into a `CODE-*` pre-guard, so the empty
    case has to behave like the absent one.
    """
    name = "ac9-comment-only-status-is-skipped"
    spec_dir, _ = _approved_run(tmp, name)
    write_plan(spec_dir, content="# Plan\n\n"
               "- **Status:** <!-- Drafting | Approved | Executing | Done -->\n\n"
               "### T1\n\n**Depends on:** none\n\n### T2\n\n**Depends on:** T1\n")
    rc, _, err = run_cohort("schedule", "check-current", str(spec_dir))
    if rc != 0 and "Status is" in err:
        fail(name, f"an unparseable token stopped the pre-guard: {err!r}")
        return
    rc2, _, err2 = run_cohort("plan", "check-current", str(spec_dir))
    if rc2 != 0 and "Status is" in err2:
        fail(name, f"an unparseable token stopped plan check-current: {err2!r}")
    else:
        ok(name)


def test_ac5_bold_ac_region_terminates(tmp: Path) -> None:
    """AC5/AC1. A bold-lead-in AC region has no heading to close it, so without
    an explicit terminator it runs to EOF and un-pins every later checkbox —
    including a `Never do` item, which is the scope the pin protects. H3 is not
    a terminator: 293 H3 headings sit inside AC sections across this repo, so
    closing on them would end the region early for most specs.
    """
    name = "ac5-bold-ac-region-terminates"
    head = "# S\n\n- **Status:** Approved\n\n"
    checks = [
        ("bold AC then bold Never-do",
         head + "**Acceptance criteria:**\n\n- [ ] AC1\n\n**Never do**\n\n"
                "- [{m}] never add a top-level dir\n", False),
        ("bold AC then H2 Boundaries",
         head + "**Acceptance criteria:**\n\n- [ ] AC1\n\n## Boundaries\n\n"
                "- [{m}] never force-push\n", False),
        # H3 closes a bold-opened region but not an H2-opened one: H3
        # subheadings sit inside H2-opened AC sections all over this repo, and
        # inside no bold-opened one.
        ("bold AC then H3 Never-do",
         head + "**Acceptance criteria:**\n\n- [ ] AC1\n\n### Never do\n\n"
                "- [{m}] never add a top-level dep\n", False),
        # A bold lead-in inside a *heading-opened* region is a group header, not
        # a terminator — this spec's own `**Defect 1 — ...**` rows sit under
        # `## Acceptance Criteria`, so closing on them would un-pin every
        # criterion it has.
        ("bold group header inside a heading-opened AC section",
         head + "## Acceptance Criteria\n\n**Defect 1 — hashing**\n\n"
                "- [{m}] AC1\n", True),
        ("H3 subgroup inside the AC section",
         head + "## Acceptance Criteria\n\n### Group A\n\n- [{m}] AC1\n", True),
        # An H3-opened AC section is closed by its own siblings. `_AC_HEADING_RE`
        # accepts `#{2,3}`, but the terminator was a fixed `#{1,2}`, so an
        # `### Acceptance Criteria` ran through every later H3 to the next H2 and
        # un-pinned the `Never do` items underneath — the exact scope the pin
        # protects. No spec in this tree heads its criteria with H3 today (283
        # are H2, 16 are a bold lead-in), so this is a latent defect rather than
        # a live one: the recognizer admits a shape the terminator mishandles,
        # and the first spec to use it would silently lose its pin.
        ("H3 AC then sibling H3 Never-do",
         head + "### Acceptance Criteria\n\n- [ ] AC1\n\n### Never do\n\n"
                "- [{m}] never drop a table\n", False),
        ("H3 AC then H2",
         head + "### Acceptance Criteria\n\n- [ ] AC1\n\n## Boundaries\n\n"
                "- [{m}] never force-push\n", False),
        # ...but not by a deeper one: H4 nests inside H3 exactly as H3 nests
        # inside H2, so the rule is depth, not a hard-coded level.
        ("H4 subgroup inside an H3-opened AC section",
         head + "### Acceptance Criteria\n\n#### Group A\n\n- [{m}] AC1\n", True),
    ]
    for label, body, should_be_bookkeeping in checks:
        same = canonical_contract(body.format(m=" ")) == canonical_contract(body.format(m="x"))
        if same != should_be_bookkeeping:
            fail(name, f"{label}: un-pinned={same}, expected {should_be_bookkeeping}")
            return
    ok(name)


def test_ac1_fence_tracking_follows_commonmark(tmp: Path) -> None:
    """AC1. A fence *toggle* desyncs on a nested fence — a ```toml inside a
    ```markdown example flips the state back — and one plan already in this tree
    has an odd fence count, which left the tracker stuck open and disabled
    checkbox normalization for the rest of the file. Only a bare run of the
    opening character, at least as long, closes.
    """
    name = "ac1-fence-tracking-follows-commonmark"
    head = "# S\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n"
    checks = [
        ("well-formed nested, 4-tick outer",
         head + "````markdown\n```toml\nx = 1\n```\n````\n\n- [{m}] AC1\n", True),
        ("a fence carrying an info string never closes",
         head + "```markdown\n## Acceptance Criteria\n```\n\n- [{m}] AC1\n", True),
        ("tilde fences",
         head + "~~~markdown\nstuff\n~~~\n\n- [{m}] AC1\n", True),
        ("an unclosed fence swallows what follows",
         head + "```python\nx\n\n- [{m}] AC1\n", False),
    ]
    for label, body, should_be_bookkeeping in checks:
        same = canonical_contract(body.format(m=" ")) == canonical_contract(body.format(m="x"))
        if same != should_be_bookkeeping:
            fail(name, f"{label}: un-pinned={same}, expected {should_be_bookkeeping}")
            return
    ok(name)


def test_ac5_nested_fence_plan_stays_normalizable() -> None:
    """AC5 regression fixture for a valid plan with an odd raw fence count."""
    name = "ac5-nested-fence-plan-stays-normalizable"
    base = """# Plan\n\n### T1: Example\n\n```markdown\n```toml\nvalue = 1\n```\n```\n```\n"""
    assert base.count("```") == 5
    same = (canonical_contract(base + "\n### T9\n\n- [ ] T9 done\n", ac_section_only=False)
            == canonical_contract(base + "\n### T9\n\n- [x] T9 done\n", ac_section_only=False))
    ok(name) if same else fail(name, "ticking a task after nested fences moved the digest")


# ── dispatch-receipt (wave-complete dispatch receipts) ────────────────────
#
# Spec: docs/specs/wave-complete-dispatch-receipts/spec.md § The
# `dispatch-receipt` verb. The verb writes one per-task assertion of who the
# controller says implemented a plan task; every refusal must leave state.json
# byte-identical, because nothing here has durable side-effect semantics.

_RECEIPTS_KEY = _mod.RECEIPTS_KEY
_KEY_PATH = _mod.RECEIPT_KEY_PATH


def _receipts_state(
    spec_dir: Path,
    run_id: str,
    *,
    waves=None,
    current: object = 0,
    container: object = None,
) -> dict:
    """A scheduled state carrying the receipts container `init` now writes."""
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "plan_review_status": "approved",
        "schedule_waves": [["T1", "T2"], ["T3"]] if waves is None else waves,
        "current_wave_index": current,
        _RECEIPTS_KEY: {} if container is None else container,
    }
    write_state(spec_dir, state)
    return state


def _record_at(state: dict, wave_index: int, task_id: str):
    """The record for one task, read by walking the DECLARED key path.

    The depth comes from the module's own `RECEIPT_KEY_PATH`, never from a
    literal here: a reader hand-built at a literal depth ratifies the shape its
    author assumed rather than the shape the declaration states, which is how a
    two-key check coexisted with a three-key data model.
    """
    keys = [
        _mod.partition_digest(state.get("schedule_waves", [])),
        str(wave_index),
        task_id,
    ]
    assert len(keys) == len(_KEY_PATH), "key path declaration changed shape"
    node = state.get(_RECEIPTS_KEY)
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _refuses_without_writing(name: str, spec_dir: Path, argv, *, expect) -> None:
    """Drive one refusal: non-zero, expected text, no exception type, no write."""
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, out, err = run_cohort(*argv)
    blob = out + err
    if rc == 0:
        fail(name, f"expected non-zero; got 0 with {blob.strip()!r}")
        return
    for needle in expect:
        if needle not in blob:
            fail(name, f"expected {needle!r} in output; got {blob.strip()!r}")
            return
    for leak in ("Traceback", "TypeError", "KeyError", "AttributeError"):
        if leak in blob:
            fail(name, f"refusal surfaced an exception type ({leak}): {blob.strip()!r}")
            return
    if path.read_bytes() != before:
        fail(name, "state.json changed on a refusing invocation")
        return
    ok(name)


def test_dispatch_receipt_records_a_receipt(tmp: Path) -> None:
    name = "dispatch-receipt-records-a-receipt"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id)
    rc, out, err = run_cohort(
        "dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
        "--receipt", "--expect-run-id", run_id,
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()!r}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    record = _record_at(state, 0, "T1")
    if record != {"kind": "receipt"}:
        fail(name, f"expected a receipt at the declared key path; got {record!r}")
        return
    if not _mod.is_dispatch_record(record):
        fail(name, "the written value is not a record by the module's own definition")
        return
    ok(name)


@pytest.mark.parametrize("reason", ["no-implementer-installed", "human-directed"])
def test_dispatch_receipt_records_each_closed_decline_reason(
    tmp: Path, reason: str
) -> None:
    name = f"dispatch-receipt-decline-{reason}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id)
    rc, _, err = run_cohort(
        "dispatch-receipt", str(spec_dir), "--task", "T2", "--wave-index", "0",
        "--decline", reason, "--expect-run-id", run_id,
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()!r}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    record = _record_at(state, 0, "T2")
    if record != {"kind": "decline", "reason": reason}:
        fail(name, f"expected a {reason} decline; got {record!r}")
        return
    if not _mod.is_dispatch_record(record):
        fail(name, "the written decline is not a record by the module's definition")
        return
    ok(name)


def test_dispatch_receipt_accepts_the_current_and_a_lower_wave_index(tmp: Path) -> None:
    """A repair round re-enters a wave the pointer has already passed in part."""
    name = "dispatch-receipt-current-and-lower-index"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id, current=1)
    for task, index in (("T3", "1"), ("T1", "0")):
        rc, _, err = run_cohort(
            "dispatch-receipt", str(spec_dir), "--task", task, "--wave-index", index,
            "--receipt", "--expect-run-id", run_id,
        )
        if rc != 0:
            fail(name, f"index {index} expected exit 0; got {rc}: {err.strip()!r}")
            return
    state = json.loads((spec_dir / "state.json").read_text())
    if _record_at(state, 1, "T3") is None or _record_at(state, 0, "T1") is None:
        fail(name, f"both records must be held; got {state[_RECEIPTS_KEY]!r}")
        return
    ok(name)


def test_dispatch_receipt_refuses_an_index_above_the_pointer(tmp: Path) -> None:
    """Accepting a future wave lets one pre-run batch discharge every later exit."""
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-index-above-pointer")
    _receipts_state(spec_dir, run_id, current=0)
    _refuses_without_writing(
        "dispatch-receipt-index-above-pointer",
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T3", "--wave-index", "1",
         "--receipt", "--expect-run-id", run_id),
        expect=("current_wave_index",),
    )


@pytest.mark.parametrize("raw", ["-1", "1.9", "abc", "true", ""])
def test_dispatch_receipt_refuses_a_non_non_negative_integer_index(
    tmp: Path, raw: str
) -> None:
    """Every spelling refuses through the guard layer's one integer validation."""
    name = f"dispatch-receipt-index-{raw or 'empty'}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-bad-index")
    _receipts_state(spec_dir, run_id)
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", raw,
         "--receipt", "--expect-run-id", run_id),
        expect=("--wave-index must be a non-negative integer",),
    )


def test_dispatch_receipt_index_validation_rejects_a_boolean() -> None:
    """`isinstance(True, int)` is True, so a bool is the discriminating case.

    Asserted at the verb's validation entry point because argv cannot carry a
    Python bool: the CLI cases above cover the spellings a caller can type.
    """
    name = "dispatch-receipt-index-boolean"
    state = {
        "schema_version": 1, "run_id": "r", "schedule_waves": [["T1"]],
        "current_wave_index": 0, _RECEIPTS_KEY: {},
    }
    updated, reason = _mod.plan_dispatch_receipt(
        state, task_id="T1", wave_index=True, receipt=True, decline=None
    )
    if updated is not None or not reason:
        fail(name, f"a boolean index must refuse; got {updated!r} / {reason!r}")
        return
    if "non-negative integer" not in reason or "bool" not in reason:
        fail(name, f"refusal must name the bool it rejected; got {reason!r}")
        return
    ok(name)


def test_dispatch_receipt_refuses_an_empty_partition(tmp: Path) -> None:
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-empty-partition")
    _receipts_state(spec_dir, run_id, waves=[])
    _refuses_without_writing(
        "dispatch-receipt-empty-partition",
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        # `unusable` is the usable-partition row's own word. `schedule_waves`
        # alone appears in three rows' messages, so with the clause removed an
        # empty partition falls to the pointer row and this case still passes.
        expect=("schedule_waves", "unusable"),
    )


def test_dispatch_receipt_refuses_a_pointer_outside_the_partition(tmp: Path) -> None:
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-pointer-out-of-range")
    _receipts_state(spec_dir, run_id, current=7)
    _refuses_without_writing(
        "dispatch-receipt-pointer-out-of-range",
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        expect=("current_wave_index",),
    )


def test_dispatch_receipt_refuses_a_receipt_and_a_decline_together(tmp: Path) -> None:
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-both-forms")
    _receipts_state(spec_dir, run_id)
    _refuses_without_writing(
        "dispatch-receipt-both-forms",
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--decline", "human-directed", "--expect-run-id", run_id),
        expect=("--receipt", "--decline"),
    )


def test_dispatch_receipt_refuses_neither_form(tmp: Path) -> None:
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-no-form")
    _receipts_state(spec_dir, run_id)
    _refuses_without_writing(
        "dispatch-receipt-no-form",
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--expect-run-id", run_id),
        expect=("--receipt",),
    )


def test_dispatch_receipt_refuses_a_reason_outside_the_closed_set(tmp: Path) -> None:
    """The refusal names both accepted codes, so the caller needs no reference."""
    name = "dispatch-receipt-reason-outside-closed-set"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id)
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--decline", "because-i-said-so", "--expect-run-id", run_id),
        expect=("no-implementer-installed", "human-directed"),
    )


def test_dispatch_receipt_refuses_an_unknown_task_and_names_the_wave(tmp: Path) -> None:
    name = "dispatch-receipt-unknown-task"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id)
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T9", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        expect=("T9", "T1", "T2"),
    )


def test_dispatch_receipt_bounds_and_discloses_a_long_identifier_list(tmp: Path) -> None:
    """The verb's largest state-derived refusal: bounded, partial, whole ids only.

    `loop-cohort`'s own diagnostic helper applies no length bound, so a raw join
    would put the whole wave on stderr; the guard layer's per-value bound is the
    tighter of the two and therefore the one that truncates.
    """
    name = "dispatch-receipt-bounded-identifier-list"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    wave = [f"T{i}-long-identifier-name" for i in range(1, 201)]
    _receipts_state(spec_dir, run_id, waves=[wave, ["TZ"]])
    rc, out, err = run_cohort(
        "dispatch-receipt", str(spec_dir), "--task", "T-absent", "--wave-index", "0",
        "--receipt", "--expect-run-id", run_id,
    )
    if rc == 0:
        fail(name, "expected non-zero for a task outside the wave")
        return
    if len(err.strip().splitlines()) != 1:
        fail(name, f"refusal must stay one line; got {err!r}")
        return
    if "partial list" not in err:
        fail(name, f"truncation must be disclosed; got {err.strip()!r}")
        return
    if len(err) > 1000:
        fail(name, f"refusal is unbounded at {len(err)} chars")
        return
    # Every identifier the refusal prints must be whole: no fragment of a task
    # name may be presented as a task name.
    printed = err.split("holds ")[1].split(" (partial list")[0].strip().strip("'")
    for token in printed.split(", "):
        if token not in wave:
            fail(name, f"refusal printed a fragment rather than an identifier: {token!r}")
            return
    if out:
        fail(name, f"a refusal must print nothing on stdout; got {out!r}")
        return
    ok(name)


def test_dispatch_receipt_refuses_a_run_id_mismatch(tmp: Path) -> None:
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-run-id-mismatch")
    _receipts_state(spec_dir, run_id)
    _refuses_without_writing(
        "dispatch-receipt-run-id-mismatch",
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", "not-the-run"),
        expect=("run-id",),
    )


def test_dispatch_receipt_refuses_an_unsupported_schema(tmp: Path) -> None:
    """Separate from the run-id case: the schema branch emits its own message.

    The wave exit deliberately tolerates this state class; the verb refuses it,
    as every other run-scoped mutation does.
    """
    name = "dispatch-receipt-unsupported-schema"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    state = _receipts_state(spec_dir, run_id)
    state["schema_version"] = 99
    write_state(spec_dir, state)
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        expect=("schema_version",),
    )


def test_dispatch_receipt_refusal_from_the_state_read_writes_nothing(tmp: Path) -> None:
    """The byte-identical property covers the refusals raised by the read itself."""
    name = "dispatch-receipt-unreadable-state"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "state.json").write_text("{not json", encoding="utf-8")
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        expect=("state.json",),
    )


def _malformed_container_cases() -> list[tuple[str, object]]:
    """One hostile container per DECLARED depth, generated from the key path.

    Depth 0 is the container itself; depth `len(KEY_PATH)` is the leaf a record
    must occupy. Hand-building these at a literal depth is what let a predicate
    that rejected every valid container pass a green walk.
    """
    cases = []
    for depth in range(len(_KEY_PATH) + 1):
        value: object = 5
        for _ in range(depth):
            value = {"k": value}
        cases.append((f"depth-{depth}", value))
    return cases


@pytest.mark.parametrize("label,container", _malformed_container_cases())
def test_dispatch_receipt_refuses_a_malformed_container(
    tmp: Path, label: str, container: object
) -> None:
    name = f"dispatch-receipt-malformed-container-{label}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-malformed-container")
    _receipts_state(spec_dir, run_id, container=container)
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        expect=(_RECEIPTS_KEY, "malformed"),
    )


@pytest.mark.parametrize(
    "label,waves,owned",
    [
        # Derived from the well-formedness declaration's conjuncts, not sampled:
        # `schedule_waves` a non-list, and the wave at the named index a
        # non-list, an empty list, and a list carrying a non-string. Three wave
        # shapes because a single non-list case leaves the other two unexercised.
        #
        # Third element: the word this parameter's own refusal row owns, carried
        # per parameter rather than once for the test. A non-list partition is
        # refused by the usable-partition row (`unusable`); the wave shapes are
        # refused by the wave row (`malformed`). One shared expectation cannot
        # be both — asserting `unusable` for every row reddens the three wave
        # shapes on an unmutated tree, and asserting only `schedule_waves`
        # cannot fail at all, because three rows' messages carry it.
        ("schedule-waves-not-a-list", "nope", "unusable"),
        ("wave-not-a-list", ["nope", ["T3"]], "malformed"),
        ("wave-empty", [[], ["T3"]], "malformed"),
        ("wave-holds-a-non-string", [["T1", 5], ["T3"]], "malformed"),
    ],
)
def test_dispatch_receipt_refuses_a_malformed_partition(
    tmp: Path, label: str, waves: object, owned: str
) -> None:
    name = f"dispatch-receipt-malformed-partition-{label}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, "dispatch-receipt-malformed-partition")
    _receipts_state(spec_dir, run_id, waves=waves)
    _refuses_without_writing(
        name,
        spec_dir,
        ("dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
         "--receipt", "--expect-run-id", run_id),
        expect=("schedule_waves", owned),
    )


def test_dispatch_receipt_is_idempotent_for_one_triple(tmp: Path) -> None:
    """The same triple twice exits zero twice and leaves exactly one record."""
    name = "dispatch-receipt-idempotent"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id)
    for attempt in (1, 2):
        rc, _, err = run_cohort(
            "dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
            "--receipt", "--expect-run-id", run_id,
        )
        if rc != 0:
            fail(name, f"attempt {attempt} expected exit 0; got {rc}: {err.strip()!r}")
            return
    state = json.loads((spec_dir / "state.json").read_text())
    digest = _mod.partition_digest(state["schedule_waves"])
    holding = state[_RECEIPTS_KEY][digest]["0"]
    if list(holding) != ["T1"]:
        fail(name, f"expected exactly one record for the triple; got {holding!r}")
        return
    ok(name)


def test_partition_digest_is_a_function_of_the_partition_alone() -> None:
    """Equal partitions agree, different partitions differ, and it never raises."""
    name = "partition-digest-function-of-the-partition"
    waves = [["T1", "T2"], ["T3"]]
    if _mod.partition_digest(waves) != _mod.partition_digest([["T1", "T2"], ["T3"]]):
        fail(name, "an equal partition produced a different digest")
        return
    if _mod.partition_digest(waves) == _mod.partition_digest([["T1"], ["T2"], ["T3"]]):
        fail(name, "a different partition produced the same digest")
        return
    if _mod.partition_digest([]) != _mod.partition_digest([]):
        fail(name, "the empty partition is not stable")
        return
    # Total over hostile values: a refusal that names the malformed field must
    # not be pre-empted by a serialization error inside the digest.
    _mod.partition_digest({"not": "a list"})
    _mod.partition_digest("nope")
    ok(name)


def test_a_single_recorded_receipt_reads_as_accounted_for(tmp: Path) -> None:
    name = "single-receipt-reads-as-accounted-for"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _receipts_state(spec_dir, run_id, waves=[["T1"], ["T2"]])
    rc, _, err = run_cohort(
        "dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
        "--receipt", "--expect-run-id", run_id,
    )
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()!r}")
        return
    state = json.loads((spec_dir / "state.json").read_text())
    # Through the SHARED accounting predicate, which `check --phase wave-exit`
    # and `wave advance`'s advancing branch also apply — not a reading local to
    # this test, which could agree with neither consumer.
    unaccounted = _mod.unaccounted_wave_tasks(state, 0)
    if unaccounted:
        fail(name, f"wave 0 must read as accounted for; unaccounted: {unaccounted}")
        return
    ok(name)


# ── check --phase wave-exit, and the wave advance coupling ────────────────
#
# Spec: docs/specs/wave-complete-dispatch-receipts/spec.md § The
# `check --phase wave-exit` verdict and § Leaving a wave. The verdict table's
# partition and per-row verdicts are asserted against the guard API in
# `test_loop_guards.py`; what these cases add is the real CLI — the exit code and
# both streams a controller actually sees, and the verb whose advancing branch
# consults the same accounting predicate.


def _receipts_container(waves, index, tasks, *, record=None) -> dict:
    """A container keyed by the module's DECLARED key path, never a literal depth."""
    record = record or {"kind": _mod.RECEIPT_KIND}
    keys = [_mod.partition_digest(waves), str(index)]
    assert len(keys) + 1 == len(_KEY_PATH), "key path declaration changed shape"
    return {keys[0]: {keys[1]: {task: dict(record) for task in tasks}}}


_WAVES = [["T1", "T2"], ["T3"]]

# One row per verdict, with the exit code and what each stream must carry.
# `None` means "this stream must be empty".
_WAVE_EXIT_CLI_ROWS = {
    "read-refuses": (None, 1, None, "state.json"),
    "schema-unsupported": ({"schema_version": 99}, 0, None, None),
    "malformed-partition": ({"schedule_waves": []}, 1, None, "schedule_waves"),
    "malformed-container": ({_RECEIPTS_KEY: {"d": 5}}, 1, None, _RECEIPTS_KEY),
    "container-absent": ({_RECEIPTS_KEY: None}, 0, "not enforced", None),
    "pointer-invalid": ({"current_wave_index": 9}, 1, None, "current_wave_index"),
    "wave-malformed": ({"schedule_waves": [[], ["T3"]]}, 1, None, "malformed"),
    "accounted": (
        {_RECEIPTS_KEY: _receipts_container(_WAVES, 0, ["T1", "T2"])}, 0, None, None,
    ),
    "unaccounted": (
        {_RECEIPTS_KEY: _receipts_container(_WAVES, 0, ["T1"])}, 1, None, "T2",
    ),
}


@pytest.mark.parametrize("row", sorted(_WAVE_EXIT_CLI_ROWS))
def test_wave_exit_cli_verdict_per_row(tmp: Path, row: str) -> None:
    """Exit code and BOTH streams, per row, through the verb a controller runs."""
    name = f"wave-exit-cli-{row}"
    over, expect_rc, on_stdout, on_stderr = _WAVE_EXIT_CLI_ROWS[row]
    spec_dir = make_spec_dir(tmp, name)
    if over is not None:
        state = {
            "schema_version": 1, "run_id": str(uuid.uuid4()),
            "schedule_waves": _WAVES, "current_wave_index": 0, _RECEIPTS_KEY: {},
        }
        for key, value in over.items():
            if value is None:
                state.pop(key, None)
            else:
                state[key] = value
        write_state(spec_dir, state)
    rc, out, err = run_cohort("check", str(spec_dir), "--phase", "wave-exit")
    if rc != expect_rc:
        fail(name, f"expected exit {expect_rc}; got {rc}: {(out + err).strip()!r}")
        return
    for stream, label, needle in ((out, "stdout", on_stdout), (err, "stderr", on_stderr)):
        if needle is None:
            if stream.strip():
                fail(name, f"{label} must be empty; got {stream.strip()!r}")
                return
        elif needle not in stream:
            fail(name, f"{label} must name {needle!r}; got {stream.strip()!r}")
            return
    if "Traceback" in out + err:
        fail(name, "the verdict surfaced a traceback")
        return
    ok(name)


def test_wave_exit_cli_refusal_names_no_accounted_task(tmp: Path) -> None:
    """Three tasks, two accounted: stderr names the third and neither of the two."""
    name = "wave-exit-cli-names-only-the-unaccounted"
    spec_dir = make_spec_dir(tmp, name)
    waves = [["T1", "T2", "T3"], ["T4"]]
    write_state(spec_dir, {
        "schema_version": 1, "run_id": str(uuid.uuid4()),
        "schedule_waves": waves, "current_wave_index": 0,
        _RECEIPTS_KEY: _receipts_container(waves, 0, ["T1", "T2"]),
    })
    rc, _, err = run_cohort("check", str(spec_dir), "--phase", "wave-exit")
    if rc == 0:
        fail(name, "expected non-zero with one unaccounted task")
    elif "T3" not in err:
        fail(name, f"stderr must name T3; got {err.strip()!r}")
    elif "T1" in err or "T2" in err:
        fail(name, f"stderr names an accounted task; got {err.strip()!r}")
    else:
        ok(name)


def test_a_record_written_by_the_verb_is_counted_by_the_guard(tmp: Path) -> None:
    """The round trip, with no intervening re-schedule.

    The verb and the guard cannot be tested for naming the same container key —
    the key has one home, so no divergence is expressible — so agreement is
    proved here instead. This reddens under either half being removed.
    """
    name = "dispatch-receipt-round-trips-to-the-wave-exit"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_state(spec_dir, {
        "schema_version": 1, "run_id": run_id,
        "schedule_waves": [["T1"], ["T2"]], "current_wave_index": 0,
        _RECEIPTS_KEY: {},
    })
    rc, _, err = run_cohort("check", str(spec_dir), "--phase", "wave-exit")
    if rc == 0:
        fail(name, "the exit must refuse before the record is written")
        return
    rc, _, err = run_cohort(
        "dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
        "--receipt", "--expect-run-id", run_id,
    )
    if rc != 0:
        fail(name, f"the verb refused: {err.strip()!r}")
        return
    rc, out, err = run_cohort("check", str(spec_dir), "--phase", "wave-exit")
    if rc != 0:
        fail(name, f"the exit did not count the record: {err.strip()!r}")
    elif (out + err).strip():
        fail(name, f"a passing exit must be silent; got {(out + err).strip()!r}")
    else:
        ok(name)


@pytest.mark.parametrize("present", [True, False])
def test_status_reports_whether_receipts_are_enforced(tmp: Path, present: bool) -> None:
    """Both output forms, since a controller may read either."""
    name = f"status-receipts-enforced-{present}"
    spec_dir = make_spec_dir(tmp, name)
    state = {
        "schema_version": 1, "run_id": str(uuid.uuid4()),
        "schedule_waves": _WAVES, "current_wave_index": 0,
    }
    if present:
        state[_RECEIPTS_KEY] = {}
    write_state(spec_dir, state)

    rc, out, err = run_cohort("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"status refused: {err.strip()!r}")
        return
    payload = json.loads(out)
    if payload.get("dispatch_receipts_enforced") is not present:
        fail(name, f"--json reported {payload.get('dispatch_receipts_enforced')!r}")
        return
    rc, out, err = run_cohort("status", str(spec_dir))
    if rc != 0:
        fail(name, f"default status refused: {err.strip()!r}")
    elif f"dispatch_receipts_enforced: {present}" not in out:
        fail(name, f"default output missing the key; got {out.strip()!r}")
    else:
        ok(name)


def _advance_state(spec_dir: Path, run_id: str, **over) -> None:
    state = {
        "schema_version": 1, "run_id": run_id, "plan_review_status": "approved",
        "schedule_waves": _WAVES, "current_wave_index": 0,
        _RECEIPTS_KEY: _receipts_container(_WAVES, 0, ["T1", "T2"]),
    }
    for key, value in over.items():
        if value is _ADVANCE_ABSENT:
            state.pop(key, None)
        else:
            state[key] = value
    write_state(spec_dir, state)


_ADVANCE_ABSENT = object()


def test_wave_advance_refuses_an_unaccounted_wave_without_moving(tmp: Path) -> None:
    name = "wave-advance-refuses-an-unaccounted-wave"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _advance_state(spec_dir, run_id,
                   **{_RECEIPTS_KEY: _receipts_container(_WAVES, 0, ["T1"])})
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", "0",
         "--expect-run-id", run_id),
        expect=("T2", "dispatch-receipt"),
    )


def test_wave_advance_accepts_a_fully_accounted_wave(tmp: Path) -> None:
    name = "wave-advance-accepts-an-accounted-wave"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _advance_state(spec_dir, run_id)
    rc, _, err = run_cohort("wave", "advance", str(spec_dir), "--from-index", "0",
                            "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()!r}")
    elif json.loads((spec_dir / "state.json").read_text())["current_wave_index"] != 1:
        fail(name, "the pointer did not move")
    else:
        ok(name)


def test_wave_advance_advances_when_the_container_is_absent(tmp: Path) -> None:
    """The absent-container exemption, reached through the verb rather than the guard.

    Without it the coupling would refuse every in-flight run at its next wave
    boundary, and no migration step exists to repair that.
    """
    name = "wave-advance-absent-container-advances"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _advance_state(spec_dir, run_id, **{_RECEIPTS_KEY: _ADVANCE_ABSENT})
    rc, _, err = run_cohort("wave", "advance", str(spec_dir), "--from-index", "0",
                            "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"expected exit 0 with no container; got {rc}: {err.strip()!r}")
    elif json.loads((spec_dir / "state.json").read_text())["current_wave_index"] != 1:
        fail(name, "the pointer did not move")
    else:
        ok(name)


@pytest.mark.parametrize("label,stored", [
    # Four cases rather than one because the `int(...)` reading this replaces
    # ACCEPTED the first three and RAISED on the fourth, so no single case can
    # show the change.
    ("string", "1"), ("float", 1.9), ("bool", True), ("null", None),
])
def test_wave_advance_refuses_an_unusable_pointer(
    tmp: Path, label: str, stored: object
) -> None:
    name = f"wave-advance-unusable-pointer-{label}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, f"wave-advance-unusable-pointer-{label}")
    _advance_state(spec_dir, run_id, current_wave_index=stored)
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", "0",
         "--expect-run-id", run_id),
        expect=("current_wave_index",),
    )


@pytest.mark.parametrize("label,container", _malformed_container_cases())
def test_wave_advance_refuses_a_malformed_container(
    tmp: Path, label: str, container: object
) -> None:
    """The advancing branch now reads the container, so it is a position it can raise on."""
    name = f"wave-advance-malformed-container-{label}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, f"wave-advance-malformed-container-{label}")
    _advance_state(spec_dir, run_id, **{_RECEIPTS_KEY: container})
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", "0",
         "--expect-run-id", run_id),
        expect=(_RECEIPTS_KEY, "malformed", "reset"),
    )


@pytest.mark.parametrize("label,waves,owned", [
    # Derived from the well-formedness declaration's conjuncts, not sampled.
    # Third element as above: the word this parameter's own row owns. The verb
    # refuses a non-list partition as `unusable` and a malformed wave as
    # `malformed`, and `schedule_waves` is common to both.
    ("schedule-waves-not-a-list", "nope", "unusable"),
    ("wave-not-a-list", ["nope", ["T3"]], "malformed"),
    ("wave-empty", [[], ["T3"]], "malformed"),
    ("wave-holds-a-non-string", [["T1", 5], ["T3"]], "malformed"),
])
def test_wave_advance_refuses_a_malformed_partition(
    tmp: Path, label: str, waves: object, owned: str
) -> None:
    name = f"wave-advance-malformed-partition-{label}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, f"wave-advance-malformed-partition-{label}")
    _advance_state(spec_dir, run_id, schedule_waves=waves)
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", "0",
         "--expect-run-id", run_id),
        expect=("schedule_waves", "reset", owned),
    )


def test_wave_advance_keeps_its_pointer_mismatch_refusal(tmp: Path) -> None:
    """The third branch: neither `n` nor `n + 1`, and the accounting check is not it."""
    name = "wave-advance-pointer-mismatch-unchanged"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _advance_state(spec_dir, run_id, current_wave_index=2,
                   schedule_waves=[["T1"], ["T2"], ["T3"]],
                   **{_RECEIPTS_KEY: {}})
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", "0",
         "--expect-run-id", run_id),
        expect=("does not match",),
    )


def test_wave_advance_replays_on_the_already_applied_branch(tmp: Path) -> None:
    """`current_wave_index == n + 1` with wave `n` unaccounted still exits zero.

    The discriminating case for the branch asymmetry: a coupling applied to both
    branches passes the unaccounted-refusal case above and fails this one, which
    would turn the documented crash-resume replay into a dead end.
    """
    name = "wave-advance-already-applied-ignores-accounting"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _advance_state(spec_dir, run_id, current_wave_index=1,
                   **{_RECEIPTS_KEY: {}})
    path = spec_dir / "state.json"
    before = path.read_bytes()
    rc, out, err = run_cohort("wave", "advance", str(spec_dir), "--from-index", "0",
                              "--expect-run-id", run_id)
    if rc != 0:
        fail(name, f"the replay must exit 0; got {rc}: {err.strip()!r}")
    elif "already applied" not in out:
        fail(name, f"expected the already-applied notice; got {out.strip()!r}")
    elif path.read_bytes() != before:
        fail(name, "the replay wrote state")
    else:
        ok(name)


@pytest.mark.parametrize("label,index,over,expect", [
    # Each existing refusal asserted against a state where the accounting check
    # would ALSO have refused, so precedence is pinned rather than incidental.
    ("empty-partition", "0", {"schedule_waves": []}, "empty"),
    ("negative-index", "-1", {}, ">= 0"),
    ("index-past-the-end", "9", {}, "len(schedule_waves)"),
    ("final-wave", "1", {"current_wave_index": 1}, "final wave"),
])
def test_wave_advance_existing_refusals_are_decided_first(
    tmp: Path, label: str, index: str, over: dict, expect: str
) -> None:
    name = f"wave-advance-precedence-{label}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, f"wave-advance-precedence-{label}")
    _advance_state(spec_dir, run_id, **{_RECEIPTS_KEY: {}}, **over)
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", index,
         "--expect-run-id", run_id),
        expect=(expect,),
    )


def test_wave_advance_run_id_mismatch_is_decided_first(tmp: Path) -> None:
    name = "wave-advance-precedence-run-id"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    _advance_state(spec_dir, run_id, **{_RECEIPTS_KEY: {}})
    _refuses_without_writing(
        name, spec_dir,
        ("wave", "advance", str(spec_dir), "--from-index", "0",
         "--expect-run-id", "wrong"),
        expect=("expect-run-id mismatch",),
    )


def test_wave_advance_bounds_the_unaccounted_list_at_an_identifier_boundary(
    tmp: Path,
) -> None:
    """Driven through the verb, which emits via `_diag` — a channel with NO bound.

    The guard-side pair proves nothing about this stream, which is why the spec
    names the verb explicitly.
    """
    name = "wave-advance-bounds-the-unaccounted-list"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    tasks = [f"T{i:03d}" for i in range(200)]
    _advance_state(spec_dir, run_id, schedule_waves=[tasks, ["Z1"]],
                   **{_RECEIPTS_KEY: {}})
    rc, _, err = run_cohort("wave", "advance", str(spec_dir), "--from-index", "0",
                            "--expect-run-id", run_id)
    if rc == 0:
        fail(name, "expected non-zero")
        return
    if "partial list" not in err:
        fail(name, f"the refusal must disclose truncation; got {err.strip()!r}")
        return
    printed = err.split("dispatch receipt: ")[1].split("'")[1]
    for fragment in printed.split(", "):
        if fragment not in tasks:
            fail(name, f"{fragment!r} is not a whole identifier — the bound cut inside one")
            return
    if len(err) > 1000:
        fail(name, f"stderr is {len(err)} chars — no bound applied")
        return
    ok(name)


def test_wave_advance_does_not_carry_a_long_state_value_whole(tmp: Path) -> None:
    name = "wave-advance-bounds-a-state-derived-value"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    huge = "W" * 5000
    _advance_state(spec_dir, run_id, schedule_waves=[[huge], ["T3"]],
                   **{_RECEIPTS_KEY: {}})
    rc, _, err = run_cohort("wave", "advance", str(spec_dir), "--from-index", "0",
                            "--expect-run-id", run_id)
    if rc == 0:
        fail(name, "expected non-zero")
    elif huge in err:
        fail(name, "an unbounded state-derived value reached stderr")
    elif len(err) > 1000:
        fail(name, f"stderr is {len(err)} chars — no bound applied")
    else:
        ok(name)
