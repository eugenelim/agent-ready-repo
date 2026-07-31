#!/usr/bin/env python3
"""loop-engine — work-loop phase FSM validator (Phase 1, Option A).

Validates legal phase ordering, runs read-only guards, and records the
current phase in engine-state.json. Does NOT invoke loop-cohort mutations.
The skill invokes all mutations explicitly.

Two modes in Phase 1:
  code       — full eight-state lifecycle with implementation waves
  spec-plan  — spec/plan drafting only (terminates at DONE via plan-approved)

Verb surface
------------
    loop-engine init <spec-dir> --mode {code|spec-plan} [--json]
    loop-engine transition <spec-dir> <event> [--wave-index <n>]
    loop-engine status <spec-dir> [--json]
    loop-engine reset <spec-dir>

Exit contract: 0 on success; non-zero with a one-line reason on stderr.

Schema reference: references/state-schema.md
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import uuid as _uuid_mod
from datetime import UTC, datetime
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_VERSION = 1

# ── FSM tables ─────────────────────────────────────────────────────────────
#
# Normative transition matrix per spec.md §Boundaries.
# Key: (mode, source_state, event) → target_state
# "both" modes share the SPEC-PLAN-* states.

_BOTH_TRANSITIONS = {
    ("SPEC-PLAN-DRAFTING", "spec-ready"): "SPEC-PLAN-REVIEW",
    ("SPEC-PLAN-REVIEW", "reviewers-clean"): "SPEC-PLAN-HUMAN-GATE",
    ("SPEC-PLAN-REVIEW", "findings-remain"): "SPEC-PLAN-DRAFTING",
    ("SPEC-PLAN-HUMAN-GATE", "plan-rejected"): "SPEC-PLAN-DRAFTING",
}

_CODE_TRANSITIONS = {
    **_BOTH_TRANSITIONS,
    ("SPEC-PLAN-HUMAN-GATE", "plan-approved"): "CODE-IMPLEMENTATION",
    ("CODE-IMPLEMENTATION", "wave-complete"): "CODE-VERIFICATION",
    ("CODE-VERIFICATION", "wave-passed"): "CODE-IMPLEMENTATION",
    ("CODE-VERIFICATION", "gates-clean"): "CODE-REVIEW",
    ("CODE-VERIFICATION", "gates-failed"): "CODE-IMPLEMENTATION",
    ("CODE-REVIEW", "reviewers-clean"): "CODE-HUMAN-GATE",
    ("CODE-REVIEW", "findings-remain"): "CODE-IMPLEMENTATION",
    ("CODE-HUMAN-GATE", "done"): "DONE",
    ("CODE-HUMAN-GATE", "blocker-applied"): "CODE-IMPLEMENTATION",
}

_SPEC_PLAN_TRANSITIONS = {
    **_BOTH_TRANSITIONS,
    ("SPEC-PLAN-HUMAN-GATE", "plan-approved"): "DONE",
}

_TRANSITIONS_BY_MODE = {
    "code": _CODE_TRANSITIONS,
    "spec-plan": _SPEC_PLAN_TRANSITIONS,
}

# States where pending_human_wait is True
_HUMAN_WAIT_STATES = frozenset({"SPEC-PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"})

# CODE-* states that require the mandatory schedule check-current pre-guard,
# EXCEPT "done" which is exempt.
_CODE_STATES = frozenset({
    "CODE-IMPLEMENTATION", "CODE-VERIFICATION", "CODE-REVIEW", "CODE-HUMAN-GATE"
})
_DONE_EXEMPT_FROM_SCHEDULE_GUARD = frozenset({"done"})

# ── guards ─────────────────────────────────────────────────────────────────
#
# Each entry: (mode, event) → guard_call_fn(spec_dir, engine_state, event_args)
# Guard functions return None on success, or a non-empty error string on failure.

LOOP_COHORT = str(SCRIPT_DIR / "loop-cohort.py")
CHECK_SPEC_STATUS = str(SCRIPT_DIR / "check-spec-status.py")


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a subprocess; return (returncode, combined stderr)."""
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    return proc.returncode, (proc.stderr.strip() or proc.stdout.strip())


def _guard_plan_check_current_require_schedule(
    spec_dir: Path, engine_state: dict, _
) -> str | None:
    rc, msg = _run(
        [sys.executable, LOOP_COHORT, "plan", "check-current", str(spec_dir), "--require-schedule"]
    )
    if rc != 0:
        return f"plan check-current --require-schedule failed: {msg}"
    return None


def _guard_plan_check_current(spec_dir: Path, engine_state: dict, _) -> str | None:
    rc, msg = _run(
        [sys.executable, LOOP_COHORT, "plan", "check-current", str(spec_dir)]
    )
    if rc != 0:
        return f"plan check-current failed: {msg}"
    return None


def _guard_check_phase_implement(spec_dir: Path, engine_state: dict, _) -> str | None:
    # Phase-1 stub: exits 0 unconditionally.
    rc, msg = _run(
        [sys.executable, LOOP_COHORT, "check", str(spec_dir), "--phase", "implement"]
    )
    if rc != 0:
        return f"check --phase implement failed: {msg}"
    return None


def _guard_check_phase_gates_failed(spec_dir: Path, engine_state: dict, _) -> str | None:
    rc, msg = _run(
        [sys.executable, LOOP_COHORT, "check", str(spec_dir), "--phase", "gates-failed"]
    )
    if rc != 0:
        return f"check --phase gates-failed failed: {msg}"
    return None


def _guard_wave_check_more(spec_dir: Path, engine_state: dict, event_args: dict) -> str | None:
    wave_index = event_args.get("wave_index")
    if wave_index is None:
        return "wave-passed requires --wave-index"
    cmd = [
        sys.executable, LOOP_COHORT, "wave", "check", str(spec_dir),
        "--expect", "more", "--wave-index", str(wave_index),
    ]
    rc, msg = _run(cmd)
    if rc != 0:
        return f"wave check --expect more --wave-index {wave_index} failed: {msg}"
    return None


def _guard_wave_check_last(spec_dir: Path, engine_state: dict, _) -> str | None:
    rc, msg = _run(
        [sys.executable, LOOP_COHORT, "wave", "check", str(spec_dir), "--expect", "last"]
    )
    if rc != 0:
        return f"wave check --expect last failed: {msg}"
    return None


def _guard_check_phase_review(spec_dir: Path, engine_state: dict, _) -> str | None:
    rc, msg = _run(
        [sys.executable, LOOP_COHORT, "check", str(spec_dir), "--phase", "review"]
    )
    if rc != 0:
        return f"check --phase review failed: {msg}"
    return None


def _guard_check_spec_status(spec_dir: Path, engine_state: dict, _) -> str | None:
    rc, msg = _run([sys.executable, CHECK_SPEC_STATUS, str(spec_dir)])
    if rc != 0:
        return f"check-spec-status failed: {msg}"
    return None


def _guard_check_spec_status_on_code_review(
    spec_dir: Path, engine_state: dict, event_args: dict
) -> str | None:
    # reviewers-clean fires in both SPEC-PLAN-REVIEW and CODE-REVIEW; the
    # shipped-status guard applies only on the CODE-REVIEW → CODE-HUMAN-GATE edge.
    if engine_state.get("state") != "CODE-REVIEW":
        return None
    return _guard_check_spec_status(spec_dir, engine_state, event_args)


def _guard_check_phase_review_on_code_review(
    spec_dir: Path, engine_state: dict, event_args: dict
) -> str | None:
    # findings-remain is legal from both SPEC-PLAN-REVIEW and CODE-REVIEW; the
    # review retry-cap guard applies only on the CODE-REVIEW edge.
    if engine_state.get("state") != "CODE-REVIEW":
        return None
    return _guard_check_phase_review(spec_dir, engine_state, event_args)


# Guard dispatch: (mode, event) → guard_fn | None
_GUARDS: dict[tuple[str, str], object] = {
    ("code", "plan-approved"): _guard_plan_check_current_require_schedule,
    ("spec-plan", "plan-approved"): _guard_plan_check_current,
    ("code", "wave-complete"): _guard_check_phase_implement,
    ("code", "gates-failed"): _guard_check_phase_gates_failed,
    ("code", "wave-passed"): _guard_wave_check_more,
    ("code", "gates-clean"): _guard_wave_check_last,
    ("code", "findings-remain"): _guard_check_phase_review_on_code_review,
    ("code", "reviewers-clean"): _guard_check_spec_status_on_code_review,
}

# ── engine-state.json helpers ──────────────────────────────────────────────


def _engine_state_path(spec_dir: Path) -> Path:
    return spec_dir / "engine-state.json"


def _read_engine_state(spec_dir: Path) -> dict:
    path = _engine_state_path(spec_dir)
    if not path.exists():
        raise FileNotFoundError(f"engine-state.json missing at {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"engine-state.json malformed: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(data, dict):
        raise ValueError("engine-state.json root must be an object")
    return data


def _write_engine_state_atomic(spec_dir: Path, state: dict) -> None:
    path = _engine_state_path(spec_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".engine-state-", suffix=".json.tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh, indent=2)
            fh.write("\n")
        Path(tmp).replace(path)
    except Exception:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


def _resolve_spec_dir(raw: str) -> Path:
    parts = Path(raw).parts
    if ".." in parts:
        raise ValueError(f"spec-dir must not contain '..': {raw!r}")
    return Path(raw).resolve()


def stop(reason: str, code: int = 1) -> int:
    print(f"loop-engine: stop — {reason}", file=sys.stderr)
    return code


# ── init ───────────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))

    engine_path = _engine_state_path(spec_dir)
    if engine_path.exists():
        return stop(
            f"engine-state.json already exists at {engine_path}; "
            "run 'loop-engine reset' first (engine-orphan: prior init incomplete)"
        )

    run_id = str(_uuid_mod.uuid4())
    feature = spec_dir.name
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "feature": feature,
        "mode": args.mode,
        "state": "SPEC-PLAN-DRAFTING",
        "last_event": None,
        "last_event_context": None,
        "transition_sequence": 0,
        "last_transition_at": now,
    }
    _write_engine_state_atomic(spec_dir, state)
    if args.json:
        print(json.dumps({"run_id": run_id, "feature": feature, "mode": args.mode}))
    else:
        print(
            f"loop-engine: initialised {engine_path} "
            f"(feature={feature} mode={args.mode} run_id={run_id})"
        )
    return 0


# ── reset ──────────────────────────────────────────────────────────────────


def cmd_reset(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    path = _engine_state_path(spec_dir)
    if path.exists():
        path.unlink()
        print(f"loop-engine: deleted {path}")
    else:
        print(f"loop-engine: reset — engine-state.json already absent at {path}")
    return 0


# ── status ─────────────────────────────────────────────────────────────────


def cmd_status(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = _read_engine_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    if state.get("schema_version") != SCHEMA_VERSION:
        sv = state.get("schema_version")
        return stop(f"status: unsupported schema_version={sv!r} (expected {SCHEMA_VERSION})")

    result = dict(state)
    result["pending_human_wait"] = state.get("state") in _HUMAN_WAIT_STATES
    if args.json:
        print(json.dumps(result))
    else:
        print(f"loop-engine status for {spec_dir.name}:")
        for k, v in result.items():
            print(f"  {k}: {v!r}")
    return 0


# ── transition ─────────────────────────────────────────────────────────────


def _run_id_preflight(spec_dir: Path, engine_run_id: str) -> str | None:
    """Call loop-cohort identity --expect-run-id; return error string on failure."""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "loop-cohort.py"),
        "identity", str(spec_dir),
        "--expect-run-id", engine_run_id,
    ]
    rc, msg = _run(cmd)
    if rc != 0:
        return f"run_id preflight failed: {msg}"
    return None


def _schedule_check_current(spec_dir: Path) -> str | None:
    """Call loop-cohort schedule check-current; return error string on failure."""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "loop-cohort.py"),
        "schedule", "check-current", str(spec_dir),
    ]
    rc, msg = _run(cmd)
    if rc != 0:
        return f"schedule check-current failed: {msg}"
    return None


def cmd_transition(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))

    event = args.event
    wave_index = args.wave_index

    # Validate --wave-index usage
    if event == "wave-passed":
        if wave_index is None:
            return stop("transition wave-passed requires --wave-index")
    else:
        if wave_index is not None:
            return stop(f"transition {event!r} does not accept --wave-index")

    # Read engine-state.json
    try:
        state = _read_engine_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    if state.get("schema_version") != SCHEMA_VERSION:
        sv = state.get("schema_version")
        return stop(f"transition: unsupported schema_version={sv!r} (expected {SCHEMA_VERSION})")

    mode = state["mode"]
    current_state = state["state"]
    run_id = state["run_id"]

    # Step 0: run_id preflight (all transitions)
    err = _run_id_preflight(spec_dir, run_id)
    if err:
        return stop(err)

    # Step 1: validate event against FSM for current mode × state
    table = _TRANSITIONS_BY_MODE.get(mode, {})
    key = (current_state, event)
    if key not in table:
        return stop(
            f"illegal transition: mode={mode!r} state={current_state!r} event={event!r}"
        )
    next_state = table[key]

    # Step 1b: mandatory plan-hash check for CODE-* states (except `done`)
    if current_state in _CODE_STATES and event not in _DONE_EXEMPT_FROM_SCHEDULE_GUARD:
        err = _schedule_check_current(spec_dir)
        if err:
            return stop(err)

    # Step 2: fire event-specific guard (if one exists)
    guard_fn = _GUARDS.get((mode, event))
    if guard_fn is not None:
        event_args = {}
        if wave_index is not None:
            event_args["wave_index"] = wave_index
        err = guard_fn(spec_dir, state, event_args)
        if err:
            return stop(err)

    # Step 3: write new state atomically
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_seq = int(state.get("transition_sequence", 0)) + 1
    last_event_context = None
    if event == "wave-passed" and wave_index is not None:
        last_event_context = {"completed_wave_index": wave_index}

    new_state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "feature": state["feature"],
        "mode": mode,
        "state": next_state,
        "last_event": event,
        "last_event_context": last_event_context,
        "transition_sequence": new_seq,
        "last_transition_at": now,
    }
    _write_engine_state_atomic(spec_dir, new_state)
    print(
        f"loop-engine: transition {current_state!r} → {event!r} → {next_state!r} "
        f"(seq={new_seq}) for {spec_dir.name}"
    )
    return 0


# ── dispatcher ─────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loop-engine", description=__doc__)
    sub = p.add_subparsers(dest="verb", required=True)

    sp = sub.add_parser("init", help="initialise engine-state.json; output run_id")
    sp.add_argument("spec_dir")
    sp.add_argument("--mode", required=True, choices=["code", "spec-plan"])
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("transition", help="fire an FSM event; enforce guards")
    sp.add_argument("spec_dir")
    sp.add_argument("event")
    sp.add_argument("--wave-index", type=int, dest="wave_index", default=None)
    sp.set_defaults(func=cmd_transition)

    sp = sub.add_parser("status", help="read engine-state.json + pending_human_wait")
    sp.add_argument("spec_dir")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("reset", help="delete engine-state.json; idempotent")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_reset)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return stop("interrupted")


if __name__ == "__main__":
    sys.exit(main())
