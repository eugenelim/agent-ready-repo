#!/usr/bin/env python3
"""loop-engine — phase FSM validator and loop-cohort coordinator.

Tracks work-loop phase state in engine-state.json (session-local, gitignored).
Calls loop-cohort as guards and side effects on transitions.

Three modes:
  code       Full delivery (spec/plan + implementation + review + merge).
  spec-plan  Spec/plan authoring only (terminates at human plan approval).
  doc        RFC, ADR, arch doc, or any review-and-approve document.

WORK_DIR accepts either a directory path or a file path. When a file is
passed, the parent directory is the work-dir and the file's stem is the
feature name. engine-state.json always lives inside the resolved work-dir.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Transition tables ─────────────────────────────────────────────────────────

INITIAL_STATE: dict[str, str] = {
    "code": "SPEC-PLAN-DRAFTING",
    "spec-plan": "SPEC-PLAN-DRAFTING",
    "doc": "DOC-DRAFTING",
}

TRANSITIONS: dict[str, dict[tuple[str, str], str]] = {
    "code": {
        ("SPEC-PLAN-DRAFTING",   "spec-ready"):      "SPEC-PLAN-REVIEW",
        ("SPEC-PLAN-REVIEW",     "reviewers-clean"): "SPEC-PLAN-HUMAN-GATE",
        ("SPEC-PLAN-REVIEW",     "findings-remain"): "SPEC-PLAN-DRAFTING",
        ("SPEC-PLAN-HUMAN-GATE", "plan-approved"):   "CODE-IMPLEMENTATION",
        ("SPEC-PLAN-HUMAN-GATE", "plan-rejected"):   "SPEC-PLAN-DRAFTING",
        ("CODE-IMPLEMENTATION",  "wave-complete"):   "CODE-VERIFICATION",
        ("CODE-VERIFICATION",    "gates-clean"):     "CODE-REVIEW",
        ("CODE-VERIFICATION",    "gates-failed"):    "CODE-IMPLEMENTATION",
        ("CODE-REVIEW",          "reviewers-clean"): "CODE-HUMAN-GATE",
        ("CODE-REVIEW",          "findings-remain"): "CODE-IMPLEMENTATION",
        ("CODE-HUMAN-GATE",      "done"):            "DONE",
        ("CODE-HUMAN-GATE",      "blocker-applied"): "CODE-IMPLEMENTATION",
    },
    "spec-plan": {
        ("SPEC-PLAN-DRAFTING",   "spec-ready"):      "SPEC-PLAN-REVIEW",
        ("SPEC-PLAN-REVIEW",     "reviewers-clean"): "SPEC-PLAN-HUMAN-GATE",
        ("SPEC-PLAN-REVIEW",     "findings-remain"): "SPEC-PLAN-DRAFTING",
        ("SPEC-PLAN-HUMAN-GATE", "plan-approved"):   "DONE",
        ("SPEC-PLAN-HUMAN-GATE", "plan-rejected"):   "SPEC-PLAN-DRAFTING",
    },
    "doc": {
        ("DOC-DRAFTING",   "doc-ready"):       "DOC-REVIEW",
        ("DOC-REVIEW",     "reviewers-clean"): "DOC-HUMAN-GATE",
        ("DOC-REVIEW",     "findings-remain"): "DOC-DRAFTING",
        ("DOC-HUMAN-GATE", "doc-approved"):    "DONE",
        ("DOC-HUMAN-GATE", "doc-returned"):    "DOC-DRAFTING",
    },
}

# ── Script paths ──────────────────────────────────────────────────────────────

_SCRIPTS = Path(__file__).resolve().parent


def _lc(*args: str) -> list[str]:
    return [sys.executable, str(_SCRIPTS / "loop-cohort.py"), *args]


def _css(work_dir: Path) -> list[str]:
    return [sys.executable, str(_SCRIPTS / "check-spec-status.py"), str(work_dir)]


# ── Guards ────────────────────────────────────────────────────────────────────
# Called before the state write. Non-zero exit refuses the transition.
# Key: (mode, current_state, event) → list[callable(work_dir, **kw) → list[str]]

def _guard_lc_check_plan(wd: Path, **_kw: object) -> list[str]:
    return _lc("check", str(wd), "--phase", "plan")


def _guard_lc_check_implement(wd: Path, **kw: object) -> list[str]:
    return _lc("check", str(wd), "--phase", "implement")


def _guard_lc_check_review(wd: Path, **kw: object) -> list[str]:
    return _lc("check", str(wd), "--phase", "review")


def _guard_css(wd: Path, **_kw: object) -> list[str]:
    return _css(wd)


GUARDS: dict[tuple[str, str, str], list] = {
    ("code",      "SPEC-PLAN-HUMAN-GATE", "plan-approved"): [_guard_lc_check_plan],
    ("spec-plan", "SPEC-PLAN-HUMAN-GATE", "plan-approved"): [_guard_lc_check_plan],
    ("code",      "CODE-IMPLEMENTATION",  "wave-complete"):  [_guard_lc_check_implement],
    ("code",      "CODE-REVIEW",          "findings-remain"): [_guard_lc_check_review],
    ("code",      "CODE-REVIEW",          "reviewers-clean"): [_guard_css],
}

# ── Side effects ──────────────────────────────────────────────────────────────
# Called after the state write. Failure is logged but does not reverse the
# transition. Builders return [] to skip silently.

def _se_lc_schedule(wd: Path, **_kw: object) -> list[str]:
    return _lc("schedule", str(wd))


def _se_lc_review_record_clean(wd: Path, **kw: object) -> list[str]:
    report = kw.get("report")
    if not report:
        print(
            "warning: reviewers-clean from CODE-REVIEW without --report; "
            "loop-cohort review record skipped (iteration_count not incremented)",
            file=sys.stderr,
        )
        return []
    return _lc("review", "record", str(wd), f"--report={report}")


def _se_lc_review_record_findings(wd: Path, **kw: object) -> list[str]:
    fps: list[str] = kw.get("fingerprints", [])
    cmd = _lc("review", "record", str(wd))
    for h in fps:
        cmd.append(f"--fingerprint={h}")
    return cmd


SIDE_EFFECTS: dict[tuple[str, str, str], list] = {
    ("code", "SPEC-PLAN-HUMAN-GATE", "plan-approved"): [_se_lc_schedule],
    ("code", "CODE-REVIEW", "reviewers-clean"):        [_se_lc_review_record_clean],
    ("code", "CODE-REVIEW", "findings-remain"):        [_se_lc_review_record_findings],
}

# ── State I/O ─────────────────────────────────────────────────────────────────

def resolve_work_dir(arg: str) -> tuple[Path, str]:
    """Return (work_dir, feature_name). Accepts file or directory path."""
    p = Path(arg).resolve()
    if p.is_file():
        return p.parent, p.stem
    return p, p.name


def _state_path(work_dir: Path) -> Path:
    return work_dir / "engine-state.json"


def _read_state(work_dir: Path) -> dict:
    path = _state_path(work_dir)
    if not path.exists():
        print(
            f"error: engine-state.json not found in {work_dir}\n"
            "  Run 'loop-engine init <work-dir> --mode <mode>' first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(work_dir: Path, state: dict) -> None:
    state["last_transition_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = _state_path(work_dir)
    fd, tmp = tempfile.mkstemp(dir=work_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ── Guard / side-effect runners ───────────────────────────────────────────────

def _run_guard(cmd: list[str], label: str) -> bool:
    if not cmd:
        return True
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = (result.stderr.strip() or result.stdout.strip() or "(no output)")
        print(f"guard refused [{label}]: {msg}", file=sys.stderr)
        return False
    return True


def _run_side_effect(cmd: list[str], label: str) -> None:
    if not cmd:
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = (result.stderr.strip() or result.stdout.strip() or "(no output)")
        print(
            f"side-effect failed [{label}] (transition is NOT reversed): {msg}",
            file=sys.stderr,
        )


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> int:
    work_dir, feature = resolve_work_dir(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    path = _state_path(work_dir)
    if path.exists():
        print(
            f"error: engine-state.json already exists at {path}\n"
            "  Run 'loop-engine reset <work-dir>' before re-initialising.",
            file=sys.stderr,
        )
        return 1

    state: dict = {
        "feature": feature,
        "mode": args.mode,
        "state": INITIAL_STATE[args.mode],
        "last_transition_at": "",
    }
    _write_state(work_dir, state)

    # Side effect: initialise loop-cohort for code/spec-plan modes
    if args.mode in ("code", "spec-plan"):
        lc = _SCRIPTS / "loop-cohort.py"
        if lc.exists():
            _run_side_effect(_lc("init", str(work_dir)), "loop-cohort init")

    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    work_dir, _ = resolve_work_dir(args.work_dir)
    state = _read_state(work_dir)
    mode = state["mode"]
    current = state["state"]
    event = args.event
    fingerprints: list[str] = args.fingerprints or []
    report: str | None = args.report

    table = TRANSITIONS.get(mode, {})
    if (current, event) not in table:
        valid = sorted(e for (s, e) in table if s == current)
        print(
            f"error: invalid transition in {mode!r} mode: {current!r} + {event!r}\n"
            f"  valid events from {current!r}: {valid or '(none — terminal state)'}",
            file=sys.stderr,
        )
        return 1

    next_state = table[(current, event)]
    ctx = dict(fingerprints=fingerprints, report=report)

    # Guards — must all pass before state is written
    guard_key = (mode, current, event)
    for builder in GUARDS.get(guard_key, []):
        cmd = builder(work_dir, **ctx)
        if not _run_guard(cmd, f"{mode}:{current}+{event}"):
            return 1

    # Write new state atomically
    state["state"] = next_state
    _write_state(work_dir, state)
    print(f"{current} + {event} → {next_state}")

    # Side effects — failure is logged, transition is not reversed
    for builder in SIDE_EFFECTS.get(guard_key, []):
        cmd = builder(work_dir, **ctx)
        _run_side_effect(cmd, f"{mode}:{current}+{event}")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    work_dir, _ = resolve_work_dir(args.work_dir)
    state = _read_state(work_dir)
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        ts = state.get("last_transition_at", "unknown")
        print(f"{state['feature']} | {state['mode']} | {state['state']} | last transition: {ts}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    work_dir, _ = resolve_work_dir(args.work_dir)
    _state_path(work_dir).unlink(missing_ok=True)
    return 0


# ── Argument parser ───────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loop-engine",
        description="Phase FSM validator and loop-cohort coordinator for the work-loop skill.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "WORK_DIR accepts a directory path or a file path.\n"
            "  directory → work-dir; basename → feature name\n"
            "  file      → parent is work-dir; file stem → feature name\n\n"
            "engine-state.json is always written inside the resolved work-dir.\n"
            "It is session-local and gitignored — not committed to git.\n\n"
            "Modes:  code (full delivery)  |  spec-plan (spec/plan authoring)\n"
            "        doc (RFC / ADR / arch doc / any review-and-approve document)"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p = sub.add_parser(
        "init",
        help="Initialise phase tracking for a work item.",
        description="Creates engine-state.json in the work-dir. Fails if it already exists.",
    )
    p.add_argument(
        "work_dir", metavar="WORK_DIR",
        help="Directory containing spec.md, or path to a doc file.",
    )
    p.add_argument(
        "--mode", required=True, choices=["code", "spec-plan", "doc"],
        help=(
            "Work mode: 'code' (full spec→implement→review→merge), "
            "'spec-plan' (spec/plan authoring only), "
            "'doc' (RFC/ADR/arch doc or any review-and-approve document)."
        ),
    )

    # transition
    p = sub.add_parser(
        "transition",
        help="Fire an event and advance the FSM.",
        description=(
            "Validates the event, runs applicable guards, writes the new state, "
            "then runs side effects. Guards run before the write; a non-zero guard "
            "refuses the transition. Side-effect failures are logged but do not "
            "reverse the transition."
        ),
    )
    p.add_argument("work_dir", metavar="WORK_DIR", help="Directory or doc file.")
    p.add_argument(
        "event", metavar="EVENT",
        help=(
            "Event name. Examples: spec-ready, wave-complete, reviewers-clean, "
            "findings-remain, plan-approved, done, doc-approved."
        ),
    )
    p.add_argument(
        "--fingerprints", nargs="+", metavar="HASH",
        help=(
            "Diff fingerprints (hex strings) for stasis detection. "
            "Passed to 'loop-cohort review record --fingerprint' when recording findings."
        ),
    )
    p.add_argument(
        "--report", metavar="PATH",
        help=(
            "Path to the reviewer's markdown report. "
            "Used for the 'loop-cohort review record --report' side effect "
            "when firing reviewers-clean from CODE-REVIEW."
        ),
    )

    # status
    p = sub.add_parser(
        "status",
        help="Show current phase state.",
        description="Reads engine-state.json and prints the current state.",
    )
    p.add_argument("work_dir", metavar="WORK_DIR", help="Directory or doc file.")
    p.add_argument(
        "--json", action="store_true",
        help="Emit the engine-state.json object to stdout (for machine consumers).",
    )

    # reset
    p = sub.add_parser(
        "reset",
        help="Remove engine-state.json (idempotent).",
        description=(
            "Deletes engine-state.json from the work-dir. "
            "Exits 0 even if the file is already absent."
        ),
    )
    p.add_argument("work_dir", metavar="WORK_DIR", help="Directory or doc file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "init": cmd_init,
        "transition": cmd_transition,
        "status": cmd_status,
        "reset": cmd_reset,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
