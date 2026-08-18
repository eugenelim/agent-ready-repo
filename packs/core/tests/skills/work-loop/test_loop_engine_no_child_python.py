#!/usr/bin/env python3
"""The normative regression test: a transition launches no child Python process (T5).

The acceptance property, stated as the spec states it:

    one loop-engine transition CLI invocation
      = one Python interpreter process
      + zero child Python guard processes

Deliberately NOT a timing assertion. Wall-clock thresholds are forbidden by the
spec because CI and endpoint-security variance make them flaky, and a slow machine
would fail a correct implementation. This measures the thing that actually matters —
whether a process was spawned — which is binary and machine-independent.

Two independent signals, because they fail differently:

  1. A RUNTIME recorder wrapped around every spawn primitive, driven over every
     `(mode, source_state, event)` entry the FSM admits. Proves no spawn happened on
     the paths it drove.
  2. A SOURCE-absence assertion (in `test_loop_engine.py`). Proves the engine cannot
     name a Python script to spawn on any path, including ones no fixture reaches.

Neither subsumes the other: a recorder cannot cover a path it does not drive, and
source absence cannot prove a dynamically-constructed argv is never assembled.

Run with pytest.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import spawn_support as ss

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
ENGINE = SCRIPTS / "loop-engine.py"
GUARDS = SCRIPTS / "_loop_guards.py"


if not ENGINE.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {ENGINE} — check the parents[] depth")


# ── the spawn primitives the recorder covers ───────────────────────────────
#
# Every way a Python process can be started, patched on the module object that OWNS
# it rather than on an engine-local alias — otherwise a spawn originating inside
# `_loop_guards.py` would be invisible, which is exactly the module whose purity
# this test is asserting.
#
# Both sets come from `spawn_support`, shared with `test_loop_concurrency.py`'s
# static scan. They were previously two independent literals in the two files, under
# a comment in the other file asserting they were shared "so the two cannot drift" —
# and they had: this tuple was the broader of the two, and the static scan covered
# only `subprocess`. One definition now genuinely feeds both.
_SUBPROCESS_ATTRS = tuple(sorted(ss.SUBPROCESS_ATTRS))
_OS_ATTRS = tuple(sorted(ss.OS_SPAWN_ATTRS))

# Windows ships `py.exe` / `pyw.exe` as launchers, so a basename check that only
# looked for `python*` would miss them.
_PYTHON_BASENAMES = ("python", "py", "pyw")


class SpawnRecorder:
    """Records every spawn and fails the test on any Python-shaped argv."""

    def __init__(self):
        self.calls: list[list[str]] = []
        self.violations: list[str] = []
        self.git_calls: list[dict] = []
        # Re-entrancy depth. `subprocess.run` is implemented ON TOP of `Popen`, so
        # patching both makes one logical spawn arrive twice — and the inner `Popen`
        # legitimately carries no `timeout=`, because `run` consumes it and applies it
        # to `communicate()`. Without this, every bounded `git rev-parse` was flagged
        # as unbounded. One logical spawn, one record.
        self._depth = 0

    # ── inspection ─────────────────────────────────────────────────────────
    def _inspect(self, argv, kwargs) -> None:
        if isinstance(argv, (str, bytes, os.PathLike)):
            parts = [os.fspath(argv) if not isinstance(argv, bytes) else argv.decode()]
        else:
            try:
                parts = [os.fspath(a) if isinstance(a, os.PathLike) else str(a) for a in argv]
            except TypeError:
                parts = [str(argv)]
        self.calls.append(parts)
        if not parts:
            self.violations.append("empty argv")
            return

        program = parts[0]
        base = Path(program).name.lower()
        if base.endswith(".exe"):
            base = base[:-4]

        if program == sys.executable:
            self.violations.append(f"sys.executable spawned: {parts}")
        elif base in _PYTHON_BASENAMES or base.startswith("python"):
            self.violations.append(f"a Python interpreter spawned: {parts}")

        for element in parts:
            if element.endswith(".py"):
                self.violations.append(f"a .py script appears in argv: {parts}")
                break

        if base == "git":
            # git is permitted, but must stay bounded — the lock-hold budget's
            # arithmetic depends on it.
            self.git_calls.append({"argv": parts, "timeout": kwargs.get("timeout")})
            if kwargs.get("timeout") is None:
                self.violations.append(f"git spawned with no timeout=: {parts}")

    # ── patching ───────────────────────────────────────────────────────────
    def install(self, monkeypatch) -> None:
        for attr in _SUBPROCESS_ATTRS:
            real = getattr(subprocess, attr, None)
            if real is None:
                continue

            def wrapper(argv, *a, _real=real, **kw):
                if self._depth == 0:
                    self._inspect(argv, kw)
                self._depth += 1
                try:
                    return _real(argv, *a, **kw)
                finally:
                    self._depth -= 1

            monkeypatch.setattr(subprocess, attr, wrapper)

        for attr in _OS_ATTRS:
            real = getattr(os, attr, None)
            if real is None:
                continue

            def os_wrapper(*a, _real=real, _attr=attr, **kw):
                # No depth guard: `subprocess` does not route through these, so any
                # call is a direct use and always a violation.
                self._inspect(a[0] if a else [], kw)
                self.violations.append(f"os.{_attr} called — no spawn primitive is permitted")
                return _real(*a, **kw)

            monkeypatch.setattr(os, attr, os_wrapper)


@pytest.fixture
def engine(monkeypatch, tmp_path):
    """The engine module, loaded in-process, inside a throwaway git repo.

    `git init` + `chdir` is not incidental. `_get_repo_root()` runs `git rev-parse`
    in the process cwd and `_resolve_spec_dir` confines against that root — so
    without a repo here every transition would refuse at confinement having already
    fired one git call, which satisfies a naive "the recorder fired" check while no
    guard ever executed. That is the vacuity trap this fixture exists to close.
    """
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location("_engine_no_child", str(ENGINE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def guards():
    spec = importlib.util.spec_from_file_location("_guards_no_child", str(GUARDS))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SPEC_MD = "# Spec\n\n- **Status:** {s}\n\n## Acceptance Criteria\n\n- [ ] AC1\n"
PLAN_MD = "# Plan\n\n- **Status:** {s}\n\n## T1 a\n\n**Depends on:** none\n\n## T2 b\n\n**Depends on:** T1\n"


def make_fixture(guards, root: Path, name: str, *, mode: str, state: str,
                 spec_status="Approved", plan_status="Approved",
                 approved=True, wave_index=0, waves=None, **over) -> tuple[Path, str]:
    """A spec dir that satisfies the REAL guards for `state`, not one that bypasses them.

    Hashes are computed with the shared implementation, so a fixture cannot pass by
    sidestepping the baseline checks — which would make the whole test vacuous in a
    way no assertion here could detect.
    """
    d = root / "docs" / "specs" / name
    d.mkdir(parents=True)
    (d / "spec.md").write_text(SPEC_MD.format(s=spec_status), encoding="utf-8")
    (d / "plan.md").write_text(PLAN_MD.format(s=plan_status), encoding="utf-8")
    run_id = str(uuid.uuid4())
    (d / "engine-state.json").write_text(json.dumps({
        "schema_version": 1, "run_id": run_id, "feature": name, "mode": mode,
        "state": state, "last_event": None, "last_event_context": None,
        "gate_question": None, "transition_sequence": 0,
        "last_transition_at": "2026-01-01T00:00:00Z",
    }), encoding="utf-8")
    st = {
        "schema_version": 1, "run_id": run_id, "feature": name,
        "plan_review_status": "pending",
        "approved_spec_hash": None, "approved_plan_hash": None, "plan_hash": None,
        "schedule_waves": [], "current_wave_index": 0,
        "implementation_retry_count": 0, "review_round_count": 0,
        "review_retry_count": 0, "finding_fingerprints": [],
        "previous_finding_fingerprints": [],
        "max_implementation_retries": 5, "max_review_retries": 5,
    }
    if approved:
        st.update({
            "plan_review_status": "approved",
            "approved_spec_hash": guards.sha256_canonical_contract(d / "spec.md"),
            "approved_plan_hash": guards.sha256_canonical_contract(d / "plan.md"),
            "plan_hash": guards.sha256_canonical_contract(d / "plan.md"),
            "schedule_waves": waves if waves is not None else [["T1"], ["T2"]],
            "current_wave_index": wave_index,
        })
    st.update(over)
    (d / "state.json").write_text(json.dumps(st), encoding="utf-8")
    return d, run_id


def drive(engine, argv: list) -> int:
    """Run one transition through `main()`, in-process.

    In-process because the recorder has to be installed on the module under test; a
    subprocess would hide every spawn behind its own interpreter, which is the thing
    being measured. `@_locked` still runs, so the real lock is genuinely exercised.
    """
    try:
        return engine.main([str(a) for a in argv])
    except SystemExit as exc:  # argparse or an explicit exit
        return exc.code if isinstance(exc.code, int) else 1


# ── the six path shapes the spec names ─────────────────────────────────────

def _shape_cases() -> list[tuple]:
    """(label, mode, from_state, event, extra kwargs, expected rc, expected to_state)."""
    return [
        # identity only — SPEC-PLAN-* states run no schedule pre-check
        ("identity-only", "code", "SPEC-PLAN-DRAFTING", "spec-ready",
         {"approved": False}, 0, "SPEC-PLAN-REVIEW"),
        # identity + event guard, no schedule pre-check
        ("identity+guard", "code", "SPEC-HUMAN-GATE", "spec-approved",
         {"approved": False}, 0, "PLAN-HUMAN-GATE"),
        # identity + schedule pre-check, no event guard
        ("identity+schedule", "code", "CODE-HUMAN-GATE", "blocker-applied",
         {"spec_status": "Shipped", "plan_status": "Executing", "wave_index": 1},
         0, "CODE-IMPLEMENTATION"),
        # identity + schedule + event guard
        ("identity+schedule+guard", "code", "CODE-IMPLEMENTATION", "wave-complete",
         {"spec_status": "Implementing", "plan_status": "Executing"},
         0, "CODE-VERIFICATION"),
        # a composed plan/status guard: two checks in one guard
        ("composed-plan-locked", "code", "SPEC-PLAN-APPROVED", "plan-locked",
         {}, 0, "CODE-IMPLEMENTATION"),
        # a FAILING guard — the refusal path must be spawn-free too
        ("failing-guard", "code", "CODE-VERIFICATION", "gates-clean",
         {"spec_status": "Implementing", "plan_status": "Executing", "wave_index": 0},
         1, "CODE-VERIFICATION"),
    ]


@pytest.mark.parametrize(
    "label,mode,from_state,event,extra,expected_rc,expected_to",
    _shape_cases(), ids=[c[0] for c in _shape_cases()],
)
def test_no_child_python_on_each_path_shape(
    label, mode, from_state, event, extra, expected_rc, expected_to,
    engine, guards, monkeypatch, tmp_path,
) -> None:
    """Each shape the spec names, with three-way non-vacuity.

    The recorder firing is not enough on its own: a fixture that refused at spec-dir
    confinement would have fired one git call and executed no guard. So each case
    also asserts the exit code AND the resulting engine state — which together mean
    the transition really was evaluated.
    """
    spec_dir, _ = make_fixture(guards, tmp_path, f"nc-{label}",
                               mode=mode, state=from_state, **extra)
    recorder = SpawnRecorder()
    recorder.install(monkeypatch)

    argv = ["transition", spec_dir, event]
    rc = drive(engine, argv)

    assert not recorder.violations, (
        f"{label}: a transition spawned a Python process.\n  "
        + "\n  ".join(recorder.violations)
    )
    # Non-vacuity 1: the recorder was actually wired in.
    assert recorder.calls, f"{label}: the recorder never fired — it is not installed"
    # Non-vacuity 2: git ran, so the engine really did resolve its repo root.
    assert recorder.git_calls, f"{label}: no git call — the engine did not get started"
    # Non-vacuity 3: the transition reached its decision.
    assert rc == expected_rc, f"{label}: rc={rc}, expected {expected_rc}"
    state = json.loads((spec_dir / "engine-state.json").read_text(encoding="utf-8"))
    assert state["state"] == expected_to, (
        f"{label}: engine state is {state['state']!r}, expected {expected_to!r} — the "
        "transition did not actually evaluate"
    )


def test_the_guard_module_is_loaded_once_per_transition(
    engine, guards, monkeypatch, tmp_path,
) -> None:
    """AC20: the engine loads `_loop_guards.py` once, not once per guard.

    The whole point of the change is that a transition costs one interpreter. If the
    loader re-executed the module per guard call, the process count would be 1 but
    the *parse* count would scale with the number of guards — the same cost moved
    rather than removed, and invisible to a spawn recorder.

    Driven over `plan-locked`, which is the composed multi-guard path: the engine's
    identity pre-check, the schedule pre-check, and the `plan-locked` event guard
    (itself two checks) all run in one transition. The assertion is that memoisation
    holds ACROSS those, so it needs a path with more than one guard to be meaningful
    — hence the `> 1` guard-call floor below.
    """
    spec_dir, _ = make_fixture(guards, tmp_path, "nc-load-once",
                               mode="code", state="SPEC-PLAN-APPROVED")

    loads, guard_calls = [], []
    real_loader = engine._guards

    def counting_loader():
        module = real_loader()
        # `_guards()` is called per guard; a LOAD is a fresh module object.
        if not any(m is module for m in loads):
            loads.append(module)
        guard_calls.append(1)
        return module

    monkeypatch.setattr(engine, "_guards", counting_loader)

    rc = drive(engine, ["transition", spec_dir, "plan-locked"])

    assert rc == 0, f"transition failed (rc={rc}) — nothing was measured"
    state = json.loads((spec_dir / "engine-state.json").read_text(encoding="utf-8"))
    assert state["state"] == "CODE-IMPLEMENTATION", "the transition did not evaluate"

    # Non-vacuity: this must be a genuinely multi-guard path, or "loaded once" is
    # trivially true and the test proves nothing.
    assert len(guard_calls) > 1, (
        f"only {len(guard_calls)} guard-module lookup(s) on plan-locked — this is no "
        "longer a multi-guard path, so the memoisation claim is untested here"
    )
    assert len(loads) == 1, (
        f"the guard module was loaded {len(loads)} times across one transition; "
        "memoisation is broken, so each guard re-parses the module"
    )


def test_no_child_python_over_every_fsm_entry(engine, guards, monkeypatch, tmp_path) -> None:
    """Every `(mode, source_state, event)` entry, not a sampled subset.

    Note `_TRANSITIONS_BY_MODE`'s own keys are the two MODE names, so iterating those
    would satisfy a loose reading of "every key" with a two-case test. The assertion
    is over the flattened entry set, and the count is checked exactly.

    Most entries refuse — a generic fixture cannot satisfy every guard — and that is
    fine here: the property under test is "no Python was spawned", which must hold on
    refusal paths too. Whether each guard refuses *correctly* is
    `test_loop_engine.py`'s job.
    """
    table = engine._TRANSITIONS_BY_MODE
    entries = [(mode, state, event)
               for mode, inner in table.items() for (state, event) in inner]
    expected = sum(len(inner) for inner in table.values())
    assert len(entries) == expected
    assert len(entries) > len(table), (
        "the entry set collapsed to the mode keys — this would pass with two cases"
    )

    recorder = SpawnRecorder()
    recorder.install(monkeypatch)
    driven = 0
    for i, (mode, from_state, event) in enumerate(entries):
        spec_dir, _ = make_fixture(
            guards, tmp_path, f"all-{i}", mode=mode, state=from_state,
            spec_status="Shipped", plan_status="Executing", wave_index=1,
        )
        argv = ["transition", spec_dir, event]
        if event == "wave-passed":
            argv += ["--wave-index", "1"]
        drive(engine, argv)
        driven += 1

    assert driven == expected, f"drove {driven} of {expected} FSM entries"
    assert not recorder.violations, (
        f"a Python process was spawned across {driven} FSM entries:\n  "
        + "\n  ".join(recorder.violations[:10])
    )
    assert recorder.calls, "the recorder never fired across the whole table"


def test_the_recorder_would_actually_catch_a_child_python(engine, monkeypatch, tmp_path) -> None:
    """Prove the detector detects. Otherwise every assertion above is unfalsifiable.

    A recorder that silently failed to patch would make this whole file green forever
    — the failure mode the spec calls out for AC17's ordering assertion, in a
    different place. So: install it, deliberately spawn a child Python, and assert it
    was flagged.
    """
    recorder = SpawnRecorder()
    recorder.install(monkeypatch)
    subprocess.run([sys.executable, "-c", "pass"], capture_output=True, check=False)
    assert recorder.violations, "the recorder did NOT flag a real child Python process"
    assert any("sys.executable" in v for v in recorder.violations)


def test_the_recorder_permits_bounded_git(engine, monkeypatch, tmp_path) -> None:
    """And prove it does not over-flag: git with a timeout is legal."""
    recorder = SpawnRecorder()
    recorder.install(monkeypatch)
    subprocess.run(["git", "--version"], capture_output=True, check=False, timeout=20)
    assert not recorder.violations
    assert recorder.git_calls and recorder.git_calls[0]["timeout"] == 20


def test_unbounded_git_is_flagged(engine, monkeypatch, tmp_path) -> None:
    """git is permitted, but only bounded — the budget arithmetic depends on it."""
    recorder = SpawnRecorder()
    recorder.install(monkeypatch)
    subprocess.run(["git", "--version"], capture_output=True, check=False)
    assert any("no timeout" in v for v in recorder.violations)
