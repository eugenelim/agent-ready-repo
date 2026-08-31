#!/usr/bin/env python3
"""Pytest tests for loop-engine.py — Phase-1 FSM transitions,
guards, lifecycle walks, and session-resumption state.

Run with pytest.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import signal
import stat
import subprocess
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
# The session-resumption transition table is disclosed progressively: SKILL.md
# links it rather than inlining it. The obligations are asserted where they
# live, plus a reachability check so the extraction cannot orphan them.
_RESUMPTION_REFERENCE = "references/session-resumption.md"
_RESUMPTION_PATH = _SKILL_DIR / "references" / "session-resumption.md"


def _skill_reaches_resumption_reference() -> bool:
    """Whether SKILL.md still points a reader at the resumption reference."""
    return _RESUMPTION_REFERENCE in (
        _SKILL_DIR / "SKILL.md"
    ).read_text(encoding="utf-8")


if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
ENGINE = SCRIPT_DIR / "loop-engine.py"
COHORT = SCRIPT_DIR / "loop-cohort.py"
EVALS_JSON = _SKILL_DIR / "evals" / "evals.json"


@pytest.fixture
def tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run each engine case inside its own throwaway Git repository."""
    subprocess.run(
        ["git", "init", "-q", str(tmp_path)],
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def ok(name: str) -> None:
    """Pytest reports the independently collected case."""


def fail(name: str, reason: str) -> None:
    pytest.fail(f"{name}: {reason}")


def symlink_or_skip(
    name: str,
    link: Path,
    target: Path | str,
    *,
    target_is_directory: bool = False,
) -> bool:
    """Create a required symlink, recording a real skip only outside CI."""
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        if os.environ.get("CI"):
            fail(name, f"CI must support this symlink regression: {exc}")
        pytest.skip(f"{name}: symlink creation unavailable ({exc})")
    return True


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


# Load the canonicalizer from the subject rather than restating it. The two
# copies that used to live here fed 28 state.json fixtures, so any drift in
# loop-cohort's hashing silently invalidated every CODE-* guard test.
_COHORT = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts" / "loop-cohort.py"
_cohort_spec = importlib.util.spec_from_file_location("_loop_cohort_for_tests", str(_COHORT))
_cohort = importlib.util.module_from_spec(_cohort_spec)
_cohort_spec.loader.exec_module(_cohort)

sha256_canonical_contract = _cohort.sha256_canonical_contract

_engine_spec = importlib.util.spec_from_file_location("_loop_engine_for_tests", str(ENGINE))
_engine = importlib.util.module_from_spec(_engine_spec)
_engine_spec.loader.exec_module(_engine)


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
        "approved_spec_hash": sha256_canonical_contract(spec_path) if spec_path.exists() else None,
        "approved_plan_hash": sha256_canonical_contract(plan_path) if plan_path.exists() else None,
        "plan_hash": sha256_canonical_contract(plan_path) if plan_path.exists() else None,
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


# STUB: AC3 — init must not create an event log through a dangling symlink.
def test_init_rejects_dangling_event_log_symlink(tmp: Path) -> None:
    name = "init-rejects-dangling-event-log-symlink"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    event_path = loop_dir / "events.jsonl"
    event_path.unlink(missing_ok=True)
    outside = tmp.parent / f"{tmp.name}-{name}-outside.jsonl"
    outside.unlink(missing_ok=True)
    if not symlink_or_skip(name, event_path, outside):
        return
    try:
        spec_dir = make_spec_dir(tmp, name)
        rc, _, err = run_engine("init", str(spec_dir), "--mode", "code")
        if rc != 0:
            fail(name, f"init's graceful event-log refusal changed exit status: {err!r}")
        elif outside.exists():
            fail(name, "init created the event log through a dangling symlink")
        elif not event_path.is_symlink():
            fail(name, "init mutated the unrecognized event-log symlink")
        elif "regular file" not in err:
            fail(name, f"event-log refusal was not explicit: {err!r}")
        else:
            ok(name)
    finally:
        event_path.unlink(missing_ok=True)
        outside.unlink(missing_ok=True)


# STUB: AC3 — append must not create an event log through a dangling symlink.
def test_append_rejects_dangling_event_log_symlink(tmp: Path) -> None:
    name = "append-rejects-dangling-event-log-symlink"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    event_path = loop_dir / "events.jsonl"
    event_path.unlink(missing_ok=True)
    outside = tmp.parent / f"{tmp.name}-{name}-outside.jsonl"
    outside.unlink(missing_ok=True)
    if not symlink_or_skip(name, event_path, outside):
        return
    try:
        try:
            _engine._append_events_jsonl(tmp, {"event": name})
        except OSError as exc:
            refusal = str(exc)
        else:
            fail(name, "append accepted a dangling event-log symlink")
            return
        if outside.exists():
            fail(name, "append created the event log through a dangling symlink")
        elif not event_path.is_symlink():
            fail(name, "append mutated the unrecognized event-log symlink")
        elif "regular file" not in refusal:
            fail(name, f"event-log refusal was not explicit: {refusal!r}")
        else:
            ok(name)
    finally:
        event_path.unlink(missing_ok=True)
        outside.unlink(missing_ok=True)


# STUB: AC3 — init must leave a non-regular event-log path untouched.
def test_init_rejects_non_regular_event_log(tmp: Path) -> None:
    name = "init-rejects-non-regular-event-log"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    event_path = loop_dir / "events.jsonl"
    event_path.unlink(missing_ok=True)
    event_path.mkdir()
    try:
        spec_dir = make_spec_dir(tmp, name)
        rc, _, err = run_engine("init", str(spec_dir), "--mode", "code")
        if rc != 0:
            fail(name, f"init's graceful event-log refusal changed exit status: {err!r}")
        elif not event_path.is_dir():
            fail(name, "init mutated the non-regular event-log path")
        elif "regular file" not in err:
            fail(name, f"non-regular event-log refusal was not explicit: {err!r}")
        else:
            ok(name)
    finally:
        event_path.rmdir()


# STUB: AC3 — append must leave a non-regular event-log path untouched.
def test_append_rejects_non_regular_event_log(tmp: Path) -> None:
    name = "append-rejects-non-regular-event-log"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    event_path = loop_dir / "events.jsonl"
    event_path.unlink(missing_ok=True)
    event_path.mkdir()
    try:
        try:
            _engine._append_events_jsonl(tmp, {"event": name})
        except OSError as exc:
            refusal = str(exc)
        else:
            fail(name, "append accepted a non-regular event-log path")
            return
        if not event_path.is_dir():
            fail(name, "append mutated the non-regular event-log path")
        elif "regular file" not in refusal:
            fail(name, f"non-regular event-log refusal was not explicit: {refusal!r}")
        else:
            ok(name)
    finally:
        event_path.rmdir()


# STUB: AC3 — event-log descriptor identity is checked before append writes.
def test_append_rejects_event_log_identity_change(tmp: Path) -> None:
    name = "append-rejects-event-log-identity-change"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    event_path = loop_dir / "events.jsonl"
    original = b'{"event": "existing"}\n'
    event_path.write_bytes(original)
    real_fstat = os.fstat
    calls = 0

    def changed_fstat(fd: int):
        nonlocal calls
        calls += 1
        observed = real_fstat(fd)
        fields = list(observed)
        fields[1] += 1  # st_ino
        return os.stat_result(fields)

    _engine.os.fstat = changed_fstat
    try:
        try:
            _engine._append_events_jsonl(tmp, {"event": name})
        except OSError as exc:
            refusal = str(exc)
        else:
            fail(name, "append accepted an identity-changing event log")
            return
    finally:
        _engine.os.fstat = real_fstat

    if calls < 1:
        fail(name, "append did not verify event-log descriptor identity")
    elif event_path.read_bytes() != original:
        fail(name, "append mutated the event log before verifying identity")
    elif "changed while being opened" not in refusal:
        fail(name, f"identity-change refusal was not explicit: {refusal!r}")
    else:
        ok(name)


# AC3 — a newly created event log is private even under a permissive umask.
def test_init_creates_owner_only_event_log(tmp: Path) -> None:
    name = "init-creates-owner-only-event-log"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    event_path = loop_dir / "events.jsonl"
    event_path.unlink(missing_ok=True)
    spec_dir = make_spec_dir(tmp, name)

    prior_umask = os.umask(0)
    try:
        rc, _, err = run_engine("init", str(spec_dir), "--mode", "code")
    finally:
        os.umask(prior_umask)

    if rc != 0:
        fail(name, f"init failed while creating the event log: {err!r}")
    elif not event_path.is_file():
        fail(name, "init did not create events.jsonl")
    elif stat.S_IMODE(event_path.stat().st_mode) & 0o077:
        fail(name, f"event log is group/world accessible: "
                   f"{stat.filemode(event_path.stat().st_mode)}")
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


# STUB: AC3 — status must not follow a managed engine-state symlink.
def test_status_rejects_symlinked_engine_state(tmp: Path) -> None:
    name = "status-rejects-symlinked-engine-state"
    spec_dir = make_spec_dir(tmp, name)
    sentinel = "outside-engine-state-sentinel"
    outside = tmp / f"{name}-outside.json"
    outside.write_text(
        json.dumps(minimal_engine_state(
            str(uuid.uuid4()), sentinel, "code", "SPEC-PLAN-DRAFTING"
        )),
        encoding="utf-8",
    )
    if not symlink_or_skip(name, spec_dir / "engine-state.json", outside):
        return

    rc, out, err = run_engine("status", str(spec_dir), "--json")

    if rc == 0:
        fail(name, "symlinked engine-state.json was accepted")
    elif sentinel in out + err:
        fail(name, "outside engine-state content reached command output")
    else:
        ok(name)


# STUB: AC3 — a descriptor whose identity changes during the read is rejected.
def test_engine_state_reader_rejects_identity_change(tmp: Path) -> None:
    name = "engine-state-reader-rejects-identity-change"
    sentinel = "identity-change-sentinel"
    spec_dir = make_spec_dir(tmp, name)
    path = spec_dir / "engine-state.json"
    path.write_text(
        json.dumps(minimal_engine_state(
            str(uuid.uuid4()), sentinel, "code", "SPEC-PLAN-DRAFTING"
        )),
        encoding="utf-8",
    )
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

    _engine.os.fstat = changed_fstat
    try:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = _engine.cmd_status(
                _engine.argparse.Namespace(spec_dir=str(spec_dir), json=True)
            )
    finally:
        _engine.os.fstat = real_fstat
    output = stdout.getvalue() + stderr.getvalue()
    if rc == 0:
        fail(name, "public status accepted an identity-changing state read")
    elif calls < 2:
        fail(name, "public status did not verify descriptor identity twice")
    elif sentinel in output:
        fail(name, f"identity-changing content reached output: {output!r}")
    else:
        ok(name)


def _pending_fixture(tmp: Path, name: str, sentinel: str) -> tuple[Path, Path, dict]:
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(exist_ok=True)
    pending_path = loop_dir / "events.pending"
    if pending_path.is_symlink() or pending_path.is_file():
        pending_path.unlink()
    elif pending_path.is_dir():
        pending_path.rmdir()
    (loop_dir / "events.jsonl").unlink(missing_ok=True)
    spec_dir = make_spec_dir(tmp, f"{name}-spec")
    run_id = str(uuid.uuid4())
    state = minimal_engine_state(run_id, name, "code", "SPEC-PLAN-DRAFTING")
    state["transition_sequence"] = 1
    write_engine_state(spec_dir, state)
    pending = {
        "spec": spec_dir.relative_to(tmp).as_posix(),
        "to": state["state"],
        "seq": 1,
        "run_id": run_id,
        "sentinel": sentinel,
    }
    return loop_dir, spec_dir, pending


# STUB: AC3 — pending-event recovery must not follow an outside symlink.
# (label, bytes for events.pending, must the audit record survive?)
#
# The discard decision is what commit b8c7d361's `_is_content_invalid` replaced: it
# used to substring-match `str(exc)` against a hand-listed set of message fragments,
# duplicated at two call sites, and the list had fallen behind the reader — the
# non-finite-number message was absent, so `NaN` and `1e400` were never recognised as
# invalid content and the file was retained forever, re-warning on every transition.
# Both directions matter: discarding too eagerly destroys a durable audit record, and
# retaining invalid content wedges every subsequent transition behind a warning.
_PENDING_RECOVERY_CASES = [
    # content-invalid: the bytes are unusable, so discarding is correct
    ("malformed-json", b'{ not json', False),
    ("nan-literal", b'{"seq": NaN, "to": "X"}', False),
    ("overflow-float", b'{"seq": 1e400, "to": "X"}', False),
    ("root-not-object", b'[1, 2]', False),
    ("invalid-utf8", b'{"a": "\xff\xfe"}', False),
    # structural: the read failed and says NOTHING about the content, so the audit
    # record must survive. A FIFO is the shape that used to hang the reader.
    ("fifo", None, True),
]


@pytest.mark.parametrize(
    "label,payload,must_survive",
    _PENDING_RECOVERY_CASES, ids=[c[0] for c in _PENDING_RECOVERY_CASES],
)
def test_recover_pending_discards_only_invalid_content(
    label: str, payload: bytes | None, must_survive: bool, tmp: Path,
) -> None:
    """`events.pending` is deleted for invalid CONTENT and kept for a failed READ."""
    name = f"recover-pending-content-vs-structural-{label}"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(parents=True, exist_ok=True)
    pending_path = loop_dir / "events.pending"
    if payload is None:
        os.mkfifo(pending_path)
    else:
        pending_path.write_bytes(payload)

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
        _engine._recover_pending(tmp)
    diagnostic = stderr.getvalue()

    survived = pending_path.exists() or pending_path.is_fifo()
    if survived != must_survive:
        fail(name,
             f"{label}: events.pending "
             f"{'survived' if survived else 'was discarded'}, expected the opposite. "
             f"diagnostic={diagnostic.strip()[:160]!r}")
        return
    # A silent decision is as bad as a wrong one — an operator has to be told which
    # happened, because the retained case needs manual cleanup.
    expected_phrase = "left in place" if must_survive else "discarded"
    if expected_phrase not in diagnostic:
        fail(name, f"{label}: diagnostic does not say {expected_phrase!r}: "
                   f"{diagnostic.strip()[:160]!r}")
        return
    ok(name)


def test_a_guard_module_load_failure_never_discards_the_audit_record(tmp: Path) -> None:
    """The data-loss case, stated as its own test.

    `_read_managed_json` delegates to the shared guard module, so it can now fail for
    a reason that says nothing about `events.pending` — most importantly a
    `GuardsUnavailable` when `_loop_guards.py` is missing or corrupt. Treating that as
    invalid content destroyed a byte-perfect audit record, which is what was observed
    before the fix. `_is_content_invalid` must answer False for it.
    """
    name = "load-failure-never-discards"
    loop_dir = tmp / ".loop-run"
    loop_dir.mkdir(parents=True, exist_ok=True)
    pending_path = loop_dir / "events.pending"
    payload = json.dumps({"seq": 1, "to": "CODE-VERIFICATION", "run_id": "r"})
    pending_path.write_text(payload, encoding="utf-8")

    exc = _engine.GuardsUnavailable("cannot load _loop_guards.py: truncated")
    if _engine._is_content_invalid(exc):
        fail(name, "a guard-module load failure was classified as invalid content, "
                   "which authorises deleting the audit record")
        return

    # And the same for an ordinary structural reader failure.
    if _engine._is_content_invalid(ValueError("events.pending must be a regular file")):
        fail(name, "a structural read failure was classified as invalid content")
        return

    if pending_path.read_text(encoding="utf-8") != payload:
        fail(name, "the audit record was modified")
        return
    ok(name)


_TMP_RECOVERY_CASES = [
    # (label, writer, expect the tmp file to survive)
    #
    # `deep-nesting` is the regression: `json.loads` raises RecursionError — NOT a
    # ValueError — so a narrowed `except (FileNotFoundError, ValueError)` let it
    # escape as a traceback from inside `sl.exclusive(...)`. And because the dotfile
    # was never removed, EVERY later transition on that spec failed identically.
    ("deep-nesting", lambda p: p.write_text(
        '{"state":"X","run_id":"y","z":' + "[" * 20000 + "]" * 20000 + "}",
        encoding="utf-8"), False),
    ("malformed", lambda p: p.write_text("{ not json", encoding="utf-8"), False),
    ("non-finite", lambda p: p.write_text(
        '{"state":"X","run_id":"y","n":NaN}', encoding="utf-8"), False),
    ("missing-fields", lambda p: p.write_text('{"foo":1}', encoding="utf-8"), False),
    # Structural: says nothing about the content, so the artifact must survive.
    ("fifo", lambda p: os.mkfifo(p), True),
]


@pytest.mark.parametrize(
    "label,writer,must_survive", _TMP_RECOVERY_CASES,
    ids=[c[0] for c in _TMP_RECOVERY_CASES],
)
def test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content(
    label: str, writer, must_survive: bool, tmp: Path,
) -> None:
    """Two independent properties, both of which this line has got wrong once.

    Nothing may ESCAPE — it runs inside `cmd_transition`'s critical section and
    `main()` handles only `GuardsUnavailable` and `KeyboardInterrupt`. And only invalid
    CONTENT may authorise the unlink, because a structural read failure says nothing
    about the file and deleting a byte-perfect crash-recovery artifact is irreversible.
    Catching broadly while deleting narrowly is what satisfies both.
    """
    name = f"recover-tmp-{label}"
    spec_dir = tmp / f"spec-{label}"
    spec_dir.mkdir(parents=True)
    tmp_path = spec_dir / ".engine-state-abc.json.tmp"
    writer(tmp_path)

    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            _engine._recover_engine_state_tmp(spec_dir)
    except BaseException as exc:  # noqa: BLE001 — that nothing escapes is the assertion
        fail(name, f"{label}: {type(exc).__name__} escaped a lock-holding section: {exc}")
        return

    survived = tmp_path.exists() or tmp_path.is_fifo()
    if survived != must_survive:
        fail(name, f"{label}: tmp file {'survived' if survived else 'was deleted'}, "
                   f"expected the opposite. stderr={stderr.getvalue().strip()[:160]!r}")
        return
    if "warning" not in stderr.getvalue():
        fail(name, f"{label}: the decision was silent: {stderr.getvalue()!r}")
        return
    ok(name)


def test_a_planted_filename_cannot_inject_control_characters(tmp: Path) -> None:
    """The engine's diagnostics are also an agent-captured stream.

    `_recover_engine_state_tmp` reads its filename from a `glob()`, under the same
    planted-file threat model it already accepts for the file's CONTENT — so a
    `.engine-state-<ESC>[2J<ESC>[31mFAKE-OK.json.tmp` emitted a real screen-clear and
    colour change into the transcript. The `GuardResult` chokepoint does not cover
    this: the engine formats these warnings itself.

    `_diag` is a deliberate second copy of the guard module's escape table, because
    these lines fire on paths where that module may be unloadable — which is when a
    diagnostic matters most.
    """
    name = "planted-filename-cannot-inject"
    spec_dir = tmp / "spec-inject"
    spec_dir.mkdir(parents=True)
    evil = ".engine-state-\x1b[2J\x1b[31mFAKE-OK.json.tmp"
    (spec_dir / evil).write_text("{ not json", encoding="utf-8")

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
        _engine._recover_engine_state_tmp(spec_dir)
    out = stderr.getvalue()

    if not out.strip():
        fail(name, "no diagnostic at all — nothing was measured")
        return
    offenders = sorted({c for c in out.rstrip("\n") if ord(c) < 32 or ord(c) == 127})
    if offenders:
        fail(name, f"raw control character(s) {[hex(ord(c)) for c in offenders]} reached "
                   f"the captured stream: {out!r}")
        return
    if len(out.strip().splitlines()) != 1:
        fail(name, f"the diagnostic is not one line: {out!r}")
        return
    ok(name)


def test_gitignore_courtesy_cannot_hang_the_locked_init(tmp: Path) -> None:
    """`_ensure_gitignore_entry` runs under `cmd_init`'s lock and must not block.

    It was a plain `read_text()`, and the caller's `is_symlink()` pre-check does not
    exclude a FIFO — so a repo-root `.gitignore` FIFO hung `init` indefinitely while
    holding `engine-state.json.lock`. Past `stale_after` the lock is reclaimed and a
    second writer admitted, which is the lost update the lock exists to prevent.

    The alarm is a LIVENESS guard, not a performance assertion: a blocking read has no
    exit code to assert on, so interrupting it is the only way to tell "refused" from
    "blocked forever".
    """
    name = "gitignore-cannot-hang-locked-init"
    gitignore = tmp / ".gitignore"
    os.mkfifo(gitignore)

    def _blocked(*_a):
        raise TimeoutError("the read blocked instead of refusing")

    previous = signal.signal(signal.SIGALRM, _blocked)
    signal.alarm(5)
    try:
        with pytest.raises(Exception) as caught:  # noqa: PT011 — the reader's vocabulary
            _engine._ensure_gitignore_entry(gitignore, ".loop-run/")
    except TimeoutError:
        fail(name, "the gitignore read blocked instead of refusing — a lock holder "
                   "that blocks is reclaimed as stale and a second writer admitted")
        return
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    if "regular file" not in str(caught.value):
        fail(name, f"refused, but not as a non-regular file: {caught.value!r}")
        return
    ok(name)


def test_recover_pending_rejects_symlink(tmp: Path) -> None:
    name = "recover-pending-rejects-symlink"
    sentinel = "outside-pending-sentinel"
    loop_dir, _, pending = _pending_fixture(tmp, name, sentinel)
    outside = tmp / f"{name}-outside.json"
    outside.write_text(json.dumps(pending), encoding="utf-8")
    pending_path = loop_dir / "events.pending"
    if not symlink_or_skip(name, pending_path, outside):
        return

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        _engine._recover_pending(tmp)

    events = loop_dir / "events.jsonl"
    event_text = events.read_text(encoding="utf-8") if events.exists() else ""
    if sentinel in event_text:
        fail(name, "outside pending content was replayed")
    elif not pending_path.is_symlink():
        fail(name, "recovery mutated the unrecognized pending symlink")
    elif "left in place; remove manually" not in stderr.getvalue():
        fail(name, f"recovery diagnostic hid retained symlink: {stderr.getvalue()!r}")
    else:
        ok(name)


# STUB: AC3 — recovery must validate .loop-run before any child-path access.
def test_recover_pending_rejects_symlinked_parent(tmp: Path) -> None:
    name = "recover-pending-rejects-symlinked-parent"
    repo = tmp / f"{name}-repo"
    repo.mkdir()
    outside = tmp / f"{name}-outside"
    outside.mkdir()
    sentinel = "symlinked-loop-run-parent-sentinel"
    pending_path = outside / "events.pending"
    pending_path.write_text(
        json.dumps({"spec": "outside", "sentinel": sentinel}),
        encoding="utf-8",
    )
    loop_run_link = repo / ".loop-run"
    if not symlink_or_skip(
        name, loop_run_link, outside, target_is_directory=True
    ):
        return

    before = pending_path.read_bytes()
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        _engine._recover_pending(repo)

    if pending_path.read_bytes() != before:
        fail(name, "recovery mutated events.pending through a symlinked parent")
    elif (outside / "events.jsonl").exists():
        fail(name, "recovery created an event log through a symlinked parent")
    elif sentinel in stderr.getvalue():
        fail(name, "recovery exposed external pending content through its diagnostic")
    elif ".loop-run must be a directory" not in stderr.getvalue():
        fail(name, f"parent refusal was not explicit: {stderr.getvalue()!r}")
    else:
        ok(name)


# STUB: AC3 — pending-event recovery rejects non-regular paths explicitly.
def test_recover_pending_rejects_non_regular_path(tmp: Path) -> None:
    name = "recover-pending-rejects-non-regular-path"
    loop_dir, _, _ = _pending_fixture(tmp, name, "unused-sentinel")
    (loop_dir / "events.pending").mkdir()
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        _engine._recover_pending(tmp)

    if "regular file" not in stderr.getvalue():
        fail(name, f"non-regular refusal was not explicit: {stderr.getvalue()!r}")
    elif "left in place; remove manually" not in stderr.getvalue():
        fail(name, f"recovery diagnostic hid retained directory: {stderr.getvalue()!r}")
    else:
        ok(name)


# STUB: AC3 — pending-event recovery enforces the 8 MiB managed JSON cap.
def test_recover_pending_rejects_over_limit_file(tmp: Path) -> None:
    name = "recover-pending-rejects-over-limit-file"
    loop_dir, _, _ = _pending_fixture(tmp, name, "unused-sentinel")
    (loop_dir / "events.pending").write_bytes(b"x" * (8 * 1024 * 1024 + 1))
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        _engine._recover_pending(tmp)

    if "8388608" not in stderr.getvalue() and "8 MiB" not in stderr.getvalue():
        fail(name, f"pending size cap was not identified: {stderr.getvalue()!r}")
    elif (loop_dir / "events.jsonl").exists():
        fail(name, "over-limit pending data reached the event log")
    else:
        ok(name)


# STUB: AC3 — identity verification is on the actual pending recovery path.
def test_recover_pending_rejects_identity_change(tmp: Path) -> None:
    name = "recover-pending-rejects-identity-change"
    sentinel = "pending-identity-change-sentinel"
    loop_dir, _, pending = _pending_fixture(tmp, name, sentinel)
    (loop_dir / "events.pending").write_text(json.dumps(pending), encoding="utf-8")
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

    _engine.os.fstat = changed_fstat
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            _engine._recover_pending(tmp)
    finally:
        _engine.os.fstat = real_fstat
    events = loop_dir / "events.jsonl"
    event_text = events.read_text(encoding="utf-8") if events.exists() else ""
    if calls < 2:
        fail(name, "pending recovery did not verify descriptor identity twice")
    elif sentinel in event_text:
        fail(name, "identity-changing pending content was replayed")
    elif not (loop_dir / "events.pending").is_file():
        fail(name, "identity-change cleanup deleted the pending path")
    elif "left in place; remove manually" not in stderr.getvalue():
        fail(name, f"identity-change cleanup diagnostic was unsafe: {stderr.getvalue()!r}")
    else:
        ok(name)


# STUB: AC3 — managed state has the same 8 MiB cap as shipped file readers.
def test_engine_state_reader_rejects_over_limit_file(tmp: Path) -> None:
    name = "engine-state-reader-rejects-over-limit-file"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "engine-state.json").write_bytes(b"x" * (8 * 1024 * 1024 + 1))

    rc, out, err = run_engine("status", str(spec_dir), "--json")

    if rc == 0:
        fail(name, "over-limit engine-state.json was accepted")
    elif "8388608" not in out + err and "8 MiB" not in out + err:
        fail(name, f"failure did not identify the managed-state size cap: {out} {err}")
    else:
        ok(name)


# STUB: AC3 — managed engine state must be a regular file.
def test_engine_state_reader_rejects_non_regular_path(tmp: Path) -> None:
    name = "engine-state-reader-rejects-non-regular-path"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "engine-state.json").mkdir()

    rc, out, err = run_engine("status", str(spec_dir), "--json")

    if rc == 0:
        fail(name, "directory engine-state.json was accepted")
    elif "Traceback" in out + err:
        fail(name, f"non-regular state escaped the diagnostic boundary: {out} {err}")
    elif "regular file" not in out + err:
        fail(name, f"failure did not identify the required file type: {out} {err}")
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
    """SPEC-HUMAN-GATE, PLAN-HUMAN-GATE, and CODE-HUMAN-GATE should show
    pending_human_wait=True."""
    name = "engine-status-human-wait"
    run_id = str(uuid.uuid4())
    for state_name in ("SPEC-HUMAN-GATE", "PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"):
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
        ("code", "SPEC-HUMAN-GATE", "wave-complete"),
        ("code", "SPEC-HUMAN-GATE", "gates-clean"),
        ("code", "SPEC-HUMAN-GATE", "done"),
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
        ("spec-plan", "SPEC-HUMAN-GATE", "wave-complete"),
        ("spec-plan", "SPEC-HUMAN-GATE", "reviewers-clean"),
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
    name = "legal-plan-rejected-compat"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    """spec-plan plan-approved → SPEC-PLAN-APPROVED; guard = plan.md Status: Approved."""
    name = "legal-plan-approved-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    plan_text = (
        "# Plan\n\n- **Status:** Approved\n\n"
        "### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n"
    )
    (spec_dir / "plan.md").write_text(plan_text)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "PLAN-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-APPROVED":
        fail(name, f"expected SPEC-PLAN-APPROVED; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_reviewers_clean_spec_plan(tmp: Path) -> None:
    """SPEC-PLAN-REVIEW → reviewers-clean → SPEC-HUMAN-GATE (no guard in spec-plan mode)."""
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
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-HUMAN-GATE":
        fail(name, f"expected SPEC-HUMAN-GATE; got {state.get('state')!r}")
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
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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


@pytest.mark.parametrize(
    ("status", "expected_rc"),
    [
        ("Implementing", 0),
        ("Draft", 1),
        ("Approved", 1),
        ("Archived", 1),
        ("Shipped", 1),
    ],
)
def test_reviewers_clean_intent_incomplete_requires_implementing(
    tmp: Path, status: str, expected_rc: int
) -> None:
    """The intermediate-unit declaration narrows, rather than bypasses, the guard.

    Mutation proof: changing the engine's opt-in expectation from ``Implementing``
    to ``Shipped`` makes the Implementing case refuse and the Shipped case admit,
    flipping both assertions below.
    """
    name = f"reviewers-clean-intent-incomplete-{status.lower()}"
    spec_dir, _ = make_code_review_run(tmp, name)
    write_spec(spec_dir, status=status)

    rc, _, err = run_engine(
        "transition", str(spec_dir), "reviewers-clean", "--intent-incomplete"
    )
    if rc != expected_rc:
        fail(name, f"expected exit {expected_rc}; got {rc}: {err.strip()}")
        return

    state = json.loads((spec_dir / "engine-state.json").read_text())
    expected_state = "CODE-HUMAN-GATE" if expected_rc == 0 else "CODE-REVIEW"
    if state.get("state") != expected_state:
        fail(name, f"expected {expected_state}; got {state.get('state')!r}")
    else:
        ok(name)


@pytest.mark.parametrize("status", ["Draft", "Approved", "Implementing", "Archived"])
def test_done_refuses_non_shipped_spec(tmp: Path, status: str) -> None:
    """done must not make an incomplete accepted intent terminal.

    Mutation proof: removing the ``("code", "done")`` guard entry admits this
    transition, so the assertion that engine state remains CODE-HUMAN-GATE flips.
    """
    name = f"done-refuses-{status.lower()}"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status=status)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "code", "CODE-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))

    rc, _, err = run_engine("transition", str(spec_dir), "done")
    if rc == 0:
        fail(name, "expected done to refuse a non-Shipped spec")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-HUMAN-GATE":
        fail(name, f"expected CODE-HUMAN-GATE; got {state.get('state')!r}: {err.strip()}")
    else:
        ok(name)


def test_legal_done_from_code_human_gate(tmp: Path) -> None:
    """CODE-HUMAN-GATE → done → DONE when spec.md Status is Shipped."""
    name = "legal-done-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    # done skips the schedule pre-guard but fires its Shipped-status guard.
    write_spec(spec_dir, status="Shipped")
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
    """plan-locked in spec-plan mode fires plan check-current (no --require-schedule).
    Verify by setting approved hashes then changing plan.md → guard must fail."""
    name = "guard-plan-check-current-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    cohort = approved_cohort_state(spec_dir, run_id, name)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-APPROVED")
    )
    # Change plan.md AFTER computing approved hash → guard detects mismatch
    (spec_dir / "plan.md").write_text("# Plan (modified)\n")
    write_cohort_state(spec_dir, cohort)
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-locked")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected guard to fail when plan.md changes after approve")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_guard_plan_check_current_require_schedule_fires_for_code_mode(tmp: Path) -> None:
    """plan-locked in code mode fires plan check-current --require-schedule.
    Verify by omitting schedule → guard must fail."""
    name = "guard-plan-check-current-require-schedule"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # Approved but no schedule_waves → --require-schedule fails
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-APPROVED")
    )
    write_cohort_state(spec_dir, approved_cohort_state(spec_dir, run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-locked")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
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


# STUB: adjudicator-evidence-and-remedy-predicate AC5
def test_guard_spec_plan_review_at_cap_blocks_findings_remain(tmp: Path) -> None:
    """SPEC-PLAN-REVIEW shares the review retry-cap guard."""
    name = "guard-spec-plan-review-at-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    write_engine_state(
        spec_dir,
        minimal_engine_state(run_id, name, "code", "SPEC-PLAN-REVIEW"),
    )
    write_cohort_state(
        spec_dir,
        minimal_cohort_state(
            run_id,
            name,
            extra={
                "review_retry_count": 5,
                "max_review_retries": 5,
            },
        ),
    )

    rc, _, _ = run_engine("transition", str(spec_dir), "findings-remain")
    if rc == 0:
        fail(name, "expected non-zero when review_retry_count == max")
    else:
        ok(name)


def test_guard_spec_plan_only_review_at_cap_blocks_findings_remain(tmp: Path) -> None:
    """SPEC-PLAN-REVIEW is capped in spec-plan-only mode too."""
    name = "guard-spec-plan-only-review-at-cap"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    write_plan(spec_dir)
    write_engine_state(
        spec_dir,
        minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-REVIEW"),
    )
    write_cohort_state(
        spec_dir,
        minimal_cohort_state(
            run_id,
            name,
            extra={
                "review_retry_count": 5,
                "max_review_retries": 5,
            },
        ),
    )

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
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(plan_path)

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
    # No plan.md, no schedule — done must still succeed. spec.md is present and
    # Shipped only to satisfy done's status guard; this case is about the
    # schedule exemption, which the missing plan.md still exercises.
    write_spec(spec_dir, status="Shipped")
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
    """Walk all spec-plan transitions to DONE under realistic guard conditions."""
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

    # 4. spec-ready again, then reviewers-clean → SPEC-HUMAN-GATE
    run_engine("transition", str(spec_dir), "spec-ready")
    rc, _, err = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc != 0:
        fail(name, f"reviewers-clean failed: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state["state"] != "SPEC-HUMAN-GATE":
        fail(name, f"expected SPEC-HUMAN-GATE; got {state['state']!r}")
        return

    # 5. spec-rejected → back to DRAFTING (tests that spec-rejected works from SPEC-HUMAN-GATE)
    rc, _, err = run_engine("transition", str(spec_dir), "spec-rejected")
    if rc != 0:
        fail(name, f"spec-rejected failed: {err.strip()}")
        return

    # 6. Full two-gate approval path → DONE
    #    spec-ready → reviewers-clean → SPEC-HUMAN-GATE
    run_engine("transition", str(spec_dir), "spec-ready")
    run_engine("transition", str(spec_dir), "reviewers-clean")
    #    Human writes spec.md Status: Approved → spec-approved → PLAN-HUMAN-GATE
    write_spec(spec_dir, status="Approved")
    rc, _, err = run_engine("transition", str(spec_dir), "spec-approved")
    if rc != 0:
        fail(name, f"spec-approved failed: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state["state"] != "PLAN-HUMAN-GATE":
        fail(name, f"expected PLAN-HUMAN-GATE after spec-approved; got {state['state']!r}")
        return
    #    Human writes plan.md Status: Approved → plan-approved → SPEC-PLAN-APPROVED
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n"
        "### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n"
    )
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"plan-approved failed: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state["state"] != "SPEC-PLAN-APPROVED":
        fail(name, f"expected SPEC-PLAN-APPROVED after plan-approved; got {state['state']!r}")
        return
    #    Cohort records approved baseline
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", eng_run_id)
    #    plan-locked → DONE (spec-plan mode; guard: spec Approved + plan check-current)
    rc, _, err = run_engine("transition", str(spec_dir), "plan-locked")
    if rc != 0:
        fail(name, f"plan-locked failed: {err.strip()}")
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


def test_evals_json_shape() -> None:
    """evals.json exists, is valid JSON, has skill_name='work-loop' and at least 14 entries."""
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
    if not isinstance(evals, list) or len(evals) < 14:
        count = len(evals) if isinstance(evals, list) else repr(evals)
        fail(name, f"expected at least 14 evals entries; got {count}")
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
    # Spec approver writes Status: Approved → spec-approved → PLAN-HUMAN-GATE
    write_spec(spec_dir, status="Approved")
    rc_sa, _, err_sa = run_engine("transition", str(spec_dir), "spec-approved")
    if rc_sa != 0:
        raise RuntimeError(f"make_crash_window_run: spec-approved failed: {err_sa}")
    # Plan approver writes Status: Approved in plan.md → plan-approved → SPEC-PLAN-APPROVED
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n"
        "### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n"
    )
    rc_pa, _, err_pa = run_engine("transition", str(spec_dir), "plan-approved")
    if rc_pa != 0:
        raise RuntimeError(f"make_crash_window_run: plan-approved failed: {err_pa}")
    # Cohort records approved baseline; code mode also needs schedule
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    # plan-locked seals the baseline → CODE-IMPLEMENTATION
    rc_pl, _, err_pl = run_engine("transition", str(spec_dir), "plan-locked")
    if rc_pl != 0:
        raise RuntimeError(f"make_crash_window_run: plan-locked failed: {err_pl}")
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
    # Spec approver writes Status: Approved → spec-approved → PLAN-HUMAN-GATE
    write_spec(spec_dir, status="Approved")
    rc_sa, _, err_sa = run_engine("transition", str(spec_dir), "spec-approved")
    if rc_sa != 0:
        raise RuntimeError(f"make_code_review_run: spec-approved failed: {err_sa}")
    # Plan approver writes Status: Approved in plan.md → plan-approved → SPEC-PLAN-APPROVED
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n"
    )
    rc_pa, _, err_pa = run_engine("transition", str(spec_dir), "plan-approved")
    if rc_pa != 0:
        raise RuntimeError(f"make_code_review_run: plan-approved failed: {err_pa}")
    # Cohort records approved baseline; schedule; plan-locked → CODE-IMPLEMENTATION
    run_cohort("approve-plan", str(spec_dir), "--expect-run-id", run_id)
    run_cohort("schedule", str(spec_dir), "--expect-run-id", run_id)
    rc_pl, _, err_pl = run_engine("transition", str(spec_dir), "plan-locked")
    if rc_pl != 0:
        raise RuntimeError(f"make_code_review_run: plan-locked failed: {err_pl}")
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
    """findings-remain resumption row contains required phrases."""
    if not _RESUMPTION_PATH.is_file():
        fail("findings-remain-skill-prose-present",
             f"resumption reference missing at {_RESUMPTION_PATH.name}")
        return
    if not _skill_reaches_resumption_reference():
        fail("findings-remain-skill-prose-present",
             "SKILL.md no longer links references/session-resumption.md")
        return
    lines = _RESUMPTION_PATH.read_text(encoding="utf-8").splitlines()
    row_line = next(
        (ln for ln in lines
         if ("| `findings-remain`" in ln or "findings-remain" in ln)
         and "| `CODE-IMPLEMENTATION`" in ln),
        None,
    )
    if row_line is None:
        fail("findings-remain-skill-prose-present",
             "could not find findings-remain row in the resumption reference")
        return
    required = ["stale fingerprint baseline", "under-count", "do NOT auto-reissue"]
    missing = [p for p in required if p not in row_line]
    if missing:
        fail("findings-remain-skill-prose-present",
             f"findings-remain row missing: {missing}")
    else:
        ok("findings-remain-skill-prose-present")


def test_reviewers_clean_record_forms_present(tmp: Path) -> None:
    """All clean record forms exist in cohort review record --help."""
    rc, out, err = run_cohort("review", "record", "--help")
    combined = out + err
    if any(flag not in combined for flag in ("--direct-clean", "--report", "--all-skipped")):
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
    """reviewers-clean resumption row contains required consequence phrases."""
    if not _RESUMPTION_PATH.is_file():
        fail("reviewers-clean-skill-prose-obligations",
             f"resumption reference missing at {_RESUMPTION_PATH.name}")
        return
    if not _skill_reaches_resumption_reference():
        fail("reviewers-clean-skill-prose-obligations",
             "SKILL.md no longer links references/session-resumption.md")
        return
    lines = _RESUMPTION_PATH.read_text(encoding="utf-8").splitlines()
    row_line = next(
        (ln for ln in lines
         if ("| `reviewers-clean`" in ln or "reviewers-clean" in ln)
         and "| `CODE-HUMAN-GATE`" in ln),
        None,
    )
    if row_line is None:
        fail("reviewers-clean-skill-prose-obligations",
             "could not find reviewers-clean row in the resumption reference")
        return
    required = ["non-idempotent", "double-increment",
                "fingerprint audit history", "authorized"]
    missing = [p for p in required if p not in row_line]
    if missing:
        fail("reviewers-clean-skill-prose-obligations",
             f"reviewers-clean row missing: {missing}")
    else:
        ok("reviewers-clean-skill-prose-obligations")


# ── T4: legacy compat tests ───────────────────────────────────────────────


def test_legacy_code_impl_plan_approved_readable(tmp: Path) -> None:
    """engine-state.json with state=CODE-IMPLEMENTATION, last_event=plan-approved
    → loop-engine status exits 0 (legacy pre-split run recognized as readable)."""
    name = "legacy-code-impl-plan-approved-readable"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, {
        **minimal_engine_state(run_id, name, "code", "CODE-IMPLEMENTATION"),
        "last_event": "plan-approved",
        "transition_sequence": 4,
    })
    rc, out, err = run_engine("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"status --json not valid JSON: {out!r}")
        return
    if data.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected state=CODE-IMPLEMENTATION; got {data.get('state')!r}")
    elif data.get("last_event") != "plan-approved":
        fail(name, f"expected last_event=plan-approved; got {data.get('last_event')!r}")
    else:
        ok(name)


def test_legacy_done_plan_approved_readable(tmp: Path) -> None:
    """engine-state.json with state=DONE, last_event=plan-approved
    → loop-engine status exits 0 (legacy pre-split spec-plan terminal recognized)."""
    name = "legacy-done-plan-approved-readable"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, {
        **minimal_engine_state(run_id, name, "spec-plan", "DONE"),
        "last_event": "plan-approved",
        "transition_sequence": 3,
    })
    rc, out, err = run_engine("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        fail(name, f"status --json not valid JSON: {out!r}")
        return
    if data.get("state") != "DONE":
        fail(name, f"expected state=DONE; got {data.get('state')!r}")
    elif data.get("last_event") != "plan-approved":
        fail(name, f"expected last_event=plan-approved; got {data.get('last_event')!r}")
    else:
        ok(name)


# ── T2 new-gate tests ─────────────────────────────────────────────────────


def test_legal_reviewers_clean_to_spec_human_gate(tmp: Path) -> None:
    """SPEC-PLAN-REVIEW + reviewers-clean → SPEC-HUMAN-GATE in both modes."""
    name = "legal-reviewers-clean-to-spec-human-gate"
    for mode in ("code", "spec-plan"):
        run_id = str(uuid.uuid4())
        spec_dir = make_spec_dir(tmp, f"{name}-{mode}")
        write_spec(spec_dir, status="Draft")
        write_plan(spec_dir)
        write_engine_state(spec_dir, minimal_engine_state(run_id, name, mode, "SPEC-PLAN-REVIEW"))
        write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
        rc, _, err = run_engine("transition", str(spec_dir), "reviewers-clean")
        if rc != 0:
            fail(name, f"mode={mode}: expected exit 0; got {rc}: {err.strip()}")
            return
        state = json.loads((spec_dir / "engine-state.json").read_text())
        if state.get("state") != "SPEC-HUMAN-GATE":
            fail(name, f"mode={mode}: expected SPEC-HUMAN-GATE; got {state.get('state')!r}")
            return
    ok(name)


def test_legal_spec_approved_to_plan_human_gate_code(tmp: Path) -> None:
    """code mode: SPEC-HUMAN-GATE + spec-approved → PLAN-HUMAN-GATE (spec.md Status=Approved)."""
    name = "legal-spec-approved-to-plan-human-gate-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "spec-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "PLAN-HUMAN-GATE":
        fail(name, f"expected PLAN-HUMAN-GATE; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_spec_approved_to_plan_human_gate_spec_plan(tmp: Path) -> None:
    """spec-plan mode: SPEC-HUMAN-GATE + spec-approved → PLAN-HUMAN-GATE
    (spec.md Status=Approved)."""
    name = "legal-spec-approved-to-plan-human-gate-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "spec-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "PLAN-HUMAN-GATE":
        fail(name, f"expected PLAN-HUMAN-GATE; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_plan_approved_to_spec_plan_approved_code(tmp: Path) -> None:
    """code mode: PLAN-HUMAN-GATE + plan-approved → SPEC-PLAN-APPROVED
    (plan.md Status=Approved)."""
    name = "legal-plan-approved-to-spec-plan-approved-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n"
    )
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-APPROVED":
        fail(name, f"expected SPEC-PLAN-APPROVED; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_plan_approved_to_spec_plan_approved_spec_plan(tmp: Path) -> None:
    """spec-plan: PLAN-HUMAN-GATE + plan-approved → SPEC-PLAN-APPROVED
    (plan.md Status=Approved)."""
    name = "legal-plan-approved-to-spec-plan-approved-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n"
    )
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "PLAN-HUMAN-GATE")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-APPROVED":
        fail(name, f"expected SPEC-PLAN-APPROVED; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_plan_locked_code(tmp: Path) -> None:
    """code: SPEC-PLAN-APPROVED + plan-locked → CODE-IMPLEMENTATION."""
    name = "legal-plan-locked-code"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-APPROVED"))
    write_cohort_state(spec_dir, approved_with_schedule_cohort_state(spec_dir, run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-locked")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected CODE-IMPLEMENTATION; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_plan_locked_spec_plan(tmp: Path) -> None:
    """spec-plan: SPEC-PLAN-APPROVED + plan-locked → DONE."""
    name = "legal-plan-locked-spec-plan"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-APPROVED")
    )
    write_cohort_state(spec_dir, approved_cohort_state(spec_dir, run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-locked")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "DONE":
        fail(name, f"expected DONE; got {state.get('state')!r}")
    else:
        ok(name)


def test_legal_spec_rejected(tmp: Path) -> None:
    """Both modes: SPEC-HUMAN-GATE + spec-rejected → SPEC-PLAN-DRAFTING (no guard)."""
    name = "legal-spec-rejected"
    for mode in ("code", "spec-plan"):
        run_id = str(uuid.uuid4())
        spec_dir = make_spec_dir(tmp, f"{name}-{mode}")
        write_spec(spec_dir, status="Draft")
        write_plan(spec_dir)
        write_engine_state(spec_dir, minimal_engine_state(run_id, name, mode, "SPEC-HUMAN-GATE"))
        write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
        rc, _, err = run_engine("transition", str(spec_dir), "spec-rejected")
        if rc != 0:
            fail(name, f"mode={mode}: expected exit 0; got {rc}: {err.strip()}")
            return
        state = json.loads((spec_dir / "engine-state.json").read_text())
        if state.get("state") != "SPEC-PLAN-DRAFTING":
            fail(name, f"mode={mode}: expected SPEC-PLAN-DRAFTING; got {state.get('state')!r}")
            return
    ok(name)


def test_legal_plan_rejected(tmp: Path) -> None:
    """Both modes: PLAN-HUMAN-GATE + plan-rejected → SPEC-PLAN-DRAFTING (no guard)."""
    name = "legal-plan-rejected"
    for mode in ("code", "spec-plan"):
        run_id = str(uuid.uuid4())
        spec_dir = make_spec_dir(tmp, f"{name}-{mode}")
        write_spec(spec_dir, status="Draft")
        write_plan(spec_dir)
        write_engine_state(spec_dir, minimal_engine_state(run_id, name, mode, "PLAN-HUMAN-GATE"))
        write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
        rc, _, err = run_engine("transition", str(spec_dir), "plan-rejected")
        if rc != 0:
            fail(name, f"mode={mode}: expected exit 0; got {rc}: {err.strip()}")
            return
        state = json.loads((spec_dir / "engine-state.json").read_text())
        if state.get("state") != "SPEC-PLAN-DRAFTING":
            fail(name, f"mode={mode}: expected SPEC-PLAN-DRAFTING; got {state.get('state')!r}")
            return
    ok(name)


def test_illegal_plan_approved_from_spec_human_gate(tmp: Path) -> None:
    """SPEC-HUMAN-GATE + plan-approved is illegal in both modes (non-zero, no mutation)."""
    name = "illegal-plan-approved-from-spec-human-gate"
    for mode in ("code", "spec-plan"):
        _test_illegal_transition(tmp, f"{name}-{mode}", mode, "SPEC-HUMAN-GATE", "plan-approved")


def test_illegal_plan_rejected_from_spec_human_gate(tmp: Path) -> None:
    """SPEC-HUMAN-GATE + plan-rejected is an illegal cross-rejection (non-zero, no mutation)."""
    name = "illegal-plan-rejected-from-spec-human-gate"
    for mode in ("code", "spec-plan"):
        _test_illegal_transition(tmp, f"{name}-{mode}", mode, "SPEC-HUMAN-GATE", "plan-rejected")


def test_illegal_spec_approved_from_plan_human_gate(tmp: Path) -> None:
    """PLAN-HUMAN-GATE + spec-approved is illegal in both modes (non-zero, no mutation)."""
    name = "illegal-spec-approved-from-plan-human-gate"
    for mode in ("code", "spec-plan"):
        _test_illegal_transition(tmp, f"{name}-{mode}", mode, "PLAN-HUMAN-GATE", "spec-approved")


def test_illegal_spec_rejected_from_plan_human_gate(tmp: Path) -> None:
    """PLAN-HUMAN-GATE + spec-rejected is an illegal cross-rejection (non-zero, no mutation)."""
    name = "illegal-spec-rejected-from-plan-human-gate"
    for mode in ("code", "spec-plan"):
        _test_illegal_transition(tmp, f"{name}-{mode}", mode, "PLAN-HUMAN-GATE", "spec-rejected")


def test_illegal_spec_approved_from_spec_plan_approved(tmp: Path) -> None:
    """SPEC-PLAN-APPROVED + spec-approved is illegal in both modes."""
    name = "illegal-spec-approved-from-spec-plan-approved"
    for mode in ("code", "spec-plan"):
        _test_illegal_transition(
            tmp, f"{name}-{mode}", mode, "SPEC-PLAN-APPROVED", "spec-approved"
        )


def test_illegal_plan_locked_from_human_gates(tmp: Path) -> None:
    """plan-locked from SPEC-HUMAN-GATE or PLAN-HUMAN-GATE is illegal."""
    name = "illegal-plan-locked-from-human-gates"
    cases = [
        ("code", "SPEC-HUMAN-GATE"),
        ("code", "PLAN-HUMAN-GATE"),
        ("spec-plan", "SPEC-HUMAN-GATE"),
        ("spec-plan", "PLAN-HUMAN-GATE"),
    ]
    for mode, state in cases:
        _test_illegal_transition(tmp, f"{name}-{mode}-{state}", mode, state, "plan-locked")


def test_illegal_plan_locked_from_code_states(tmp: Path) -> None:
    """plan-locked from any CODE-* state is illegal."""
    name = "illegal-plan-locked-from-code-states"
    code_states = ["CODE-IMPLEMENTATION", "CODE-VERIFICATION", "CODE-REVIEW", "CODE-HUMAN-GATE"]
    for state in code_states:
        _test_illegal_transition(tmp, f"{name}-{state}", "code", state, "plan-locked")


def test_illegal_wave_events_from_spec_plan_approved(tmp: Path) -> None:
    """Wave and review events from SPEC-PLAN-APPROVED are all illegal."""
    name = "illegal-wave-events-from-spec-plan-approved"
    illegal_events = [
        "wave-complete", "gates-clean", "gates-failed",
        "findings-remain", "reviewers-clean",
        "spec-rejected", "plan-rejected",
    ]
    for event in illegal_events:
        _test_illegal_transition(
            tmp, f"{name}-{event}", "code", "SPEC-PLAN-APPROVED", event
        )


def test_spec_human_gate_pending_human_wait_true(tmp: Path) -> None:
    """SPEC-HUMAN-GATE reports pending_human_wait=True."""
    name = "spec-human-gate-pending-human-wait-true"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    rc, out, _ = run_engine("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if not data.get("pending_human_wait"):
        fail(name, f"expected pending_human_wait=True; got {data.get('pending_human_wait')!r}")
    else:
        ok(name)


def test_plan_human_gate_pending_human_wait_true(tmp: Path) -> None:
    """PLAN-HUMAN-GATE reports pending_human_wait=True."""
    name = "plan-human-gate-pending-human-wait-true"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    rc, out, _ = run_engine("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if not data.get("pending_human_wait"):
        fail(name, f"expected pending_human_wait=True; got {data.get('pending_human_wait')!r}")
    else:
        ok(name)


def test_spec_plan_approved_pending_human_wait_false(tmp: Path) -> None:
    """SPEC-PLAN-APPROVED reports pending_human_wait=False."""
    name = "spec-plan-approved-pending-human-wait-false"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-APPROVED"))
    rc, out, _ = run_engine("status", str(spec_dir), "--json")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}")
        return
    data = json.loads(out)
    if data.get("pending_human_wait") is not False:
        fail(name, f"expected pending_human_wait=False; got {data.get('pending_human_wait')!r}")
    else:
        ok(name)


def test_spec_approved_fields(tmp: Path) -> None:
    """After spec-approved: state=PLAN-HUMAN-GATE, last_event=spec-approved."""
    name = "spec-approved-fields"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "spec-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "PLAN-HUMAN-GATE":
        fail(name, f"expected state=PLAN-HUMAN-GATE; got {state.get('state')!r}")
    elif state.get("last_event") != "spec-approved":
        fail(name, f"expected last_event=spec-approved; got {state.get('last_event')!r}")
    else:
        ok(name)


def test_plan_approved_fields(tmp: Path) -> None:
    """After plan-approved: state=SPEC-PLAN-APPROVED, last_event=plan-approved."""
    name = "plan-approved-fields"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n"
    )
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "SPEC-PLAN-APPROVED":
        fail(name, f"expected state=SPEC-PLAN-APPROVED; got {state.get('state')!r}")
    elif state.get("last_event") != "plan-approved":
        fail(name, f"expected last_event=plan-approved; got {state.get('last_event')!r}")
    else:
        ok(name)


def test_spec_approved_guard_accepts_approved(tmp: Path) -> None:
    """spec-approved guard: accepts spec.md Status: Approved."""
    name = "spec-approved-guard-accepts-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "spec-approved")
    if rc != 0:
        fail(name, f"expected exit 0 for Status: Approved; got {rc}: {err.strip()}")
    else:
        ok(name)


def test_spec_approved_guard_refuses_draft(tmp: Path) -> None:
    """spec-approved guard: refuses spec.md Status: Draft (non-zero, no mutation)."""
    name = "spec-approved-guard-refuses-draft"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Draft")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for Status: Draft")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_spec_approved_guard_refuses_implementing(tmp: Path) -> None:
    """spec-approved guard: refuses spec.md Status: Implementing (non-zero, no mutation)."""
    name = "spec-approved-guard-refuses-implementing"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Implementing")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for Status: Implementing")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_spec_approved_guard_refuses_malformed(tmp: Path) -> None:
    """spec-approved guard: refuses spec.md with no **Status:** line (non-zero, no mutation)."""
    name = "spec-approved-guard-refuses-malformed"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text("# Spec\n\nNo status line here.\n")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "spec-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for malformed spec.md")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_plan_approved_guard_accepts_approved(tmp: Path) -> None:
    """plan-approved guard: accepts plan.md Status: Approved (reads plan.md, not spec.md)."""
    name = "plan-approved-guard-accepts-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)  # spec.md Status: Draft — guard reads plan.md
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n"
    )
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-approved")
    if rc != 0:
        fail(name, f"expected exit 0 for plan.md Status: Approved; got {rc}: {err.strip()}")
    else:
        ok(name)


def test_plan_approved_guard_refuses_drafting(tmp: Path) -> None:
    """plan-approved guard: refuses plan.md Status: Drafting (non-zero, no mutation)."""
    name = "plan-approved-guard-refuses-drafting"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Drafting\n\n### T1\n\n**Depends on:** none\n"
    )
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for plan.md Status: Drafting")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_plan_approved_guard_refuses_done(tmp: Path) -> None:
    """plan-approved guard: refuses plan.md Status: Done (non-zero, no mutation)."""
    name = "plan-approved-guard-refuses-done"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Done\n\n### T1\n\n**Depends on:** none\n"
    )
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for plan.md Status: Done")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_plan_approved_guard_refuses_malformed(tmp: Path) -> None:
    """plan-approved guard: refuses plan.md with no **Status:** line (non-zero, no mutation)."""
    name = "plan-approved-guard-refuses-malformed"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir)
    (spec_dir / "plan.md").write_text("# Plan\n\nNo status line here.\n")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "PLAN-HUMAN-GATE"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-approved")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero for malformed plan.md")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_plan_locked_guard_code_approved(tmp: Path) -> None:
    """plan-locked (code mode): spec Status=Approved + schedule → CODE-IMPLEMENTATION."""
    name = "plan-locked-guard-code-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-APPROVED"))
    write_cohort_state(spec_dir, approved_with_schedule_cohort_state(spec_dir, run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-locked")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "CODE-IMPLEMENTATION":
        fail(name, f"expected CODE-IMPLEMENTATION; got {state.get('state')!r}")
    else:
        ok(name)


def test_plan_locked_guard_spec_plan_approved(tmp: Path) -> None:
    """plan-locked (spec-plan): spec Status=Approved + plan check-current → succeeds → DONE."""
    name = "plan-locked-guard-spec-plan-approved"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "spec-plan", "SPEC-PLAN-APPROVED")
    )
    write_cohort_state(spec_dir, approved_cohort_state(spec_dir, run_id, name))
    rc, _, err = run_engine("transition", str(spec_dir), "plan-locked")
    if rc != 0:
        fail(name, f"expected exit 0; got {rc}: {err.strip()}")
        return
    state = json.loads((spec_dir / "engine-state.json").read_text())
    if state.get("state") != "DONE":
        fail(name, f"expected DONE; got {state.get('state')!r}")
    else:
        ok(name)


def test_plan_locked_guard_refuses_wrong_spec_status(tmp: Path) -> None:
    """plan-locked guard: refuses when spec.md Status != Approved (non-zero, no mutation)."""
    name = "plan-locked-guard-refuses-wrong-spec-status"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Draft")  # not Approved
    write_plan(spec_dir)
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-APPROVED"))
    write_cohort_state(spec_dir, approved_with_schedule_cohort_state(spec_dir, run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-locked")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when spec.md Status != Approved")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_plan_locked_guard_code_requires_schedule(tmp: Path) -> None:
    """plan-locked guard (code mode): fails when no schedule (--require-schedule check)."""
    name = "plan-locked-guard-code-requires-schedule"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")
    write_plan(spec_dir)
    # approved but no schedule_waves
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "SPEC-PLAN-APPROVED"))
    write_cohort_state(spec_dir, approved_cohort_state(spec_dir, run_id, name))
    path = spec_dir / "engine-state.json"
    before = path.read_bytes()
    rc, _, _ = run_engine("transition", str(spec_dir), "plan-locked")
    after = path.read_bytes()
    if rc == 0:
        fail(name, "expected non-zero when no schedule (code mode --require-schedule)")
    elif before != after:
        fail(name, "engine-state.json mutated despite guard failure")
    else:
        ok(name)


def test_reviewers_clean_still_requires_shipped(tmp: Path) -> None:
    """reviewers-clean guard on CODE-REVIEW → CODE-HUMAN-GATE still requires Status: Shipped."""
    name = "reviewers-clean-still-requires-shipped"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Approved")  # not Shipped
    write_plan(spec_dir)
    spec_hash = sha256_canonical_contract(spec_dir / "spec.md")
    plan_hash = sha256_canonical_contract(spec_dir / "plan.md")
    write_engine_state(spec_dir, minimal_engine_state(run_id, name, "code", "CODE-REVIEW"))
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "approved_spec_hash": spec_hash,
        "approved_plan_hash": plan_hash,
        "plan_hash": plan_hash,
        "schedule_waves": [["T1"]],
        "current_wave_index": 0,
    }))
    rc, _, _ = run_engine("transition", str(spec_dir), "reviewers-clean")
    if rc == 0:
        fail(name, "expected non-zero when spec.md Status != Shipped (CODE-REVIEW source)")
    else:
        ok(name)


def test_check_spec_status_expect_approved_spec_md(tmp: Path) -> None:
    """check-spec-status --expect Approved exits 0 when spec.md Status: Approved."""
    name = "check-spec-status-expect-approved-spec-md"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance criteria\n\n- [ ] AC1\n"
    )
    rc, out, _ = run_check_spec_status(str(spec_dir), "--expect", "Approved")
    if rc != 0:
        fail(name, f"expected exit 0 for --expect Approved with Status: Approved; got {rc}")
    elif "Approved" not in out:
        fail(name, f"expected 'Approved' in stdout; got {out!r}")
    else:
        ok(name)


def test_check_spec_status_expect_approved_plan_md(tmp: Path) -> None:
    """check-spec-status --file plan.md --expect Approved exits 0 when plan.md Status: Approved."""
    name = "check-spec-status-expect-approved-plan-md"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n"
    )
    rc, out, _ = run_check_spec_status(
        str(spec_dir), "--expect", "Approved", "--file", "plan.md"
    )
    if rc != 0:
        fail(name, f"expected exit 0 for --file plan.md --expect Approved; got {rc}")
    elif "Approved" not in out:
        fail(name, f"expected 'Approved' in stdout; got {out!r}")
    else:
        ok(name)


def test_check_spec_status_expect_shipped_spec_md(tmp: Path) -> None:
    """check-spec-status --expect Shipped exits 0 when spec.md Status: Shipped."""
    name = "check-spec-status-expect-shipped-spec-md"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Shipped\n\n## Acceptance criteria\n\n- [x] AC1\n"
    )
    rc, out, _ = run_check_spec_status(str(spec_dir), "--expect", "Shipped")
    if rc != 0:
        fail(name, f"expected exit 0 for --expect Shipped with Status: Shipped; got {rc}")
    elif "Shipped" not in out:
        fail(name, f"expected 'Shipped' in stdout; got {out!r}")
    else:
        ok(name)


def test_check_spec_status_no_flags_defaults_shipped_spec_md(tmp: Path) -> None:
    """check-spec-status bare invocation defaults to --expect Shipped --file spec.md."""
    name = "check-spec-status-no-flags-defaults"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Shipped\n\n## Acceptance criteria\n\n- [x] AC1\n"
    )
    rc, out, _ = run_check_spec_status(str(spec_dir))  # no --expect or --file
    if rc != 0:
        fail(name, f"expected exit 0 for bare invocation with Status: Shipped; got {rc}")
    elif "Shipped" not in out:
        fail(name, f"expected 'Shipped' in stdout; got {out!r}")
    else:
        ok(name)


# ── runner ────────────────────────────────────────────────────────────────


# ══ in-process guards: transition ordering and the guard boundary (T3) ══════
#
# AC17 is the rail the `Never do` reordering prohibition is measured against, so it
# needs an artifact rather than prose. Two shapes, because neither alone is enough:
# double-violation cases prove which refusal *wins* at runtime, and a source-order
# assertion covers the steps that have no callee to observe.

# The eleven steps cmd_transition holds the lock across, in order. Each entry is
# (label, source anchor) — a substring that must appear in cmd_transition's body.
_TRANSITION_STEPS = [
    ("spec-dir re-resolution", "_resolve_spec_dir(args.spec_dir)"),
    ("--wave-index validation", "does not accept --wave-index"),
    ("crash recovery: engine-state tmp", "_recover_engine_state_tmp(spec_dir)"),
    ("crash recovery: pending outbox", "_recover_pending("),
    ("engine-state read", "_read_engine_state(spec_dir)"),
    ("schema_version check", "unsupported schema_version"),
    ("run-ID preflight", "_run_id_preflight(spec_dir, run_id)"),
    ("transition-table validation", "illegal transition"),
    # Anchored on Step 1b's own condition, not on the `_schedule_check_current`
    # call, because that call now has two sites: this one and the pre-Step-1
    # contract-amendment recovery branch, which verifies the plan against the
    # scheduled baseline before it may derive new completed-section pins. A
    # `find` on the shared callee would report the recovery branch's position
    # and make this ordering assertion fail for a step that had not moved.
    ("CODE schedule pre-check", "and not cohort_amendment_already_applied"),
    ("event-specific guard", "guard_fn(spec_dir, state, event_args)"),
    # The DECISION and the FINALIZATION are two steps, and they were previously one
    # anchor: the label said "state decision" while the anchor was the atomic write,
    # so AC17's decision step had no anchor at all and the count only looked right
    # because crash recovery had been split into two. This list is now one-for-one
    # with AC17's twelve.
    ("state decision", '"gate_question": _GATE_QUESTIONS.get(next_state)'),
    ("outbox plus state finalization", "_write_engine_state_atomic(spec_dir, new_state)"),
]


def _cmd_transition_source() -> str:
    import ast

    tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "cmd_transition")
    lines = ENGINE.read_text(encoding="utf-8").split("\n")
    return "\n".join(lines[fn.lineno - 1:fn.end_lineno])


def test_transition_steps_appear_in_the_documented_order() -> None:
    """All twelve anchors resolve, and in AC17's order.

    The vacuity guard is the point. Four of these steps — wave-index validation, the
    schema check, transition-table validation, the state decision — have no callee to
    observe at runtime, so the assertion keys on literals. An anchor that silently
    stopped matching would drop out of a sorted list that then always passes, which is
    the antipattern `e6d4c14a` records: "a gate whose scanned file set can collapse to
    zero while still exiting 0 is silent when it works and silent when it is broken."
    So a missing anchor is a failure, not a skipped comparison.
    """
    src = _cmd_transition_source()
    positions = []
    missing = []
    for label, anchor in _TRANSITION_STEPS:
        idx = src.find(anchor)
        if idx < 0:
            missing.append(f"{label} ({anchor!r})")
        else:
            positions.append((idx, label))
    assert not missing, (
        "these transition steps no longer resolve in cmd_transition, so the ordering "
        f"assertion would silently stop covering them: {missing}"
    )
    assert len(positions) == len(_TRANSITION_STEPS)
    ordered = [label for _, label in sorted(positions)]
    expected = [label for label, _ in _TRANSITION_STEPS]
    assert ordered == expected, (
        "cmd_transition's critical section has been reordered.\n"
        f"  expected: {expected}\n  found:    {ordered}"
    )


def test_wave_index_validation_wins_over_an_unreadable_engine_state(tmp: Path) -> None:
    """Double violation, steps 2 vs 5: the earlier step's refusal is the one reported.

    `wave-passed` without `--wave-index` AND an unreadable engine-state.json. The
    wave-index check is step 2 and the engine-state read is step 5, so the wave-index
    message wins. Step numbers are AC17's twelve, which `_TRANSITION_STEPS` mirrors
    one-for-one — an earlier revision cited two different numberings in these two
    docstrings.
    """
    name = "double-violation-wave-index-vs-read"
    spec_dir = make_spec_dir(tmp, name)
    (spec_dir / "engine-state.json").write_text("{ not json", encoding="utf-8")
    rc, _, err = run_engine("transition", str(spec_dir), "wave-passed")
    if rc == 0:
        fail(name, "expected a refusal")
    elif "requires --wave-index" not in err:
        fail(name, f"the later step's refusal won: {err.strip()[:160]!r}")
    else:
        ok(name)


def test_schedule_precheck_wins_over_a_failing_event_guard(tmp: Path) -> None:
    """Double violation, steps 9 vs 10: the CODE schedule pre-check precedes the guard.

    Step numbers are AC17's twelve, mirrored by `_TRANSITION_STEPS`.

    A drifted plan hash AND a not-last wave. `gates-clean`'s own guard would refuse on
    the wave, but the schedule pre-check runs first.
    """
    name = "double-violation-schedule-vs-guard"
    run_id = str(uuid.uuid4())
    spec_dir = make_spec_dir(tmp, name)
    write_spec(spec_dir, status="Implementing")
    write_plan(spec_dir)
    write_engine_state(
        spec_dir, minimal_engine_state(run_id, name, "code", "CODE-VERIFICATION")
    )
    write_cohort_state(spec_dir, minimal_cohort_state(run_id, name, extra={
        "plan_review_status": "approved",
        "plan_hash": "0" * 64,               # drifted -> step 9 refuses
        "schedule_waves": [["T1"], ["T2"]],
        "current_wave_index": 0,             # not last -> step 10 would refuse
    }))
    rc, _, err = run_engine("transition", str(spec_dir), "gates-clean")
    if rc == 0:
        fail(name, "expected a refusal")
    elif "schedule check-current" not in err:
        fail(name, f"the event guard won over the schedule pre-check: {err.strip()[:160]!r}")
    else:
        ok(name)


def test_engine_names_only_in_process_python_siblings_and_never_spawns_python() -> None:
    """Source-absence signal, independent of the runtime recorder in T5.

    Two signals rather than one because they fail differently: a recorder proves no
    spawn happened on the paths it drove, and this proves the engine cannot name a
    Python script to spawn on any path at all.
    """
    import ast
    import re as _re

    src = ENGINE.read_text(encoding="utf-8")
    tree = ast.parse(src)

    executable_refs = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "executable"
        and isinstance(node.value, ast.Name) and node.value.id == "sys"
    ]
    assert not executable_refs, f"sys.executable is referenced at lines {executable_refs}"

    literals = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and _re.search(r"\.py$", node.value)
    }
    allowed = {"_statelock.py", "_loop_guards.py", "loop-cohort.py"}
    assert literals <= allowed, (
        f"the engine names other Python scripts: {sorted(literals - allowed)}"
    )
