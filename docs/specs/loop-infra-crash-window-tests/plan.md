# Plan: loop-infra-crash-window-tests

- **Status:** Done
- **Spec:** [spec.md](spec.md)
- **Mode:** code (full mode)

## Context and Goals

Close the deferred AC6 of `loop-infrastructure-phase-1` by adding deterministic
crash-window and session-resumption tests using real CLI subprocess invocations.
Also adds one targeted SKILL.md prose enhancement (the `reviewers-clean` row in
the session-resumption table) to make double-increment and fingerprint audit
history consequences explicit. The `findings-remain` row already carries the
required phrases from the Phase 1 ship; AC8c pins those as a regression guard
without modification.

Phase 2 orchestration is out of scope.

## Constraints

- No production changes to `loop-engine.py` or `loop-cohort.py` unless a test
  discovers a bug blocking a required AC (surface first before any fix).
- All crash states are reached via real CLI transitions (`run_engine("transition",
  ...)`), never by writing synthetic engine-state.json files. Cohort crash states
  (wave advance already applied, or record-attempt already applied) are reached by
  calling the real cohort mutation command before the crash point.
- No sleeps, timing, network access, or process killing.
- Cross-platform (macOS and Linux).
- Every new `test_*` function must be added to the `tests` list in `main()`.

## Risks

- A test may reveal that the current `loop-cohort.py` does not fully implement
  the documented behavior for a crash window. If so: surface to human with the
  exact scenario + state diff before making any production fix.

## Design (LLD)

N/A — this spec adds tests and prose only. No new module boundary, no new
dependency, no production state changes. SKILL.md change is a single prose row.

## Rollout

N/A — test additions and prose changes ship in a single PR; no migration,
feature flag, or staged rollout required.

## Tasks

### T1: Crash-test harness and no-chat-history status recovery

**Depends on:** none
**Mode:** TDD
**ACs:** AC7, AC10

**Tests:**
```python
# Add to test-loop-engine.py, section:
# "## Crash-window tests (loop-infra-crash-window-tests AC6 closure)"
# All new tests take (tmp: Path) — matching the runner calling convention.

def test_no_chat_history_status_read_via_cli(tmp: Path) -> None:  # STUB: AC7
    """AC7: engine status --json is readable via subprocess; last_event parseable."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-status")
    rc, out, _ = run_engine("status", spec_dir, "--json")
    data = json.loads(out)
    if rc != 0 or "last_event" not in data or "run_id" not in data:
        fail("no-chat-history-status-read-via-cli",
             f"engine status returned rc={rc} or missing fields: {out!r}")
    else:
        ok("no-chat-history-status-read-via-cli")

def test_no_chat_history_identity_verify_via_cli(tmp: Path) -> None:  # STUB: AC7
    """AC7: identity --expect-run-id verifies cohort pairing via subprocess."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-identity")
    rc, out, _ = run_cohort("identity", spec_dir, "--expect-run-id", run_id, "--json")
    if rc != 0:
        fail("no-chat-history-identity-verify-via-cli",
             f"identity returned rc={rc}: {out!r}")
    else:
        ok("no-chat-history-identity-verify-via-cli")

def test_no_chat_history_route_wave_passed_via_cli(tmp: Path) -> None:  # STUB: AC7
    """AC7: reads last_event wave-passed from CLI and routes wave advance correctly."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-wave")
    # Simulate crash: fire real wave-passed transition, then stop before advance
    run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")
    # Fresh-process read sequence
    rc_s, out_s, _ = run_engine("status", spec_dir, "--json")
    eng = json.loads(out_s)
    rc_i, _, _ = run_cohort("identity", spec_dir, "--expect-run-id", eng["run_id"])
    rc_c, out_c, _ = run_cohort("status", spec_dir, "--json")
    coh = json.loads(out_c)
    n = eng["last_event_context"]["completed_wave_index"]
    rc_a, _, err_a = run_cohort(
        "wave", "advance", spec_dir,
        "--from-index", str(n), "--expect-run-id", eng["run_id"]
    )
    rc2, out2, _ = run_cohort("status", spec_dir, "--json")
    coh2 = json.loads(out2)
    if (eng["last_event"] != "wave-passed" or rc_i != 0 or rc_a != 0
            or coh2["current_wave_index"] != n + 1):
        fail("no-chat-history-route-wave-passed-via-cli",
             f"routing failed: last_event={eng['last_event']!r} rc_a={rc_a} "
             f"idx={coh2.get('current_wave_index')}")
    else:
        ok("no-chat-history-route-wave-passed-via-cli")

def test_no_chat_history_route_gates_failed_via_cli(tmp: Path) -> None:  # STUB: AC7
    """AC7: reads last_event gates-failed from CLI and routes record-attempt correctly."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "nch-gf")
    # Simulate crash: fire real gates-failed transition, stop before record-attempt
    run_engine("transition", spec_dir, "gates-failed")
    rc_s, out_s, _ = run_engine("status", spec_dir, "--json")
    eng = json.loads(out_s)
    rc_i, _, _ = run_cohort("identity", spec_dir, "--expect-run-id", eng["run_id"])
    rc_c, out_c, _ = run_cohort("status", spec_dir, "--json")
    coh_before = json.loads(out_c)
    cycle_id = f"{eng['run_id']}:{eng['transition_sequence']}"
    rc_r, _, _ = run_cohort(
        "record-attempt", spec_dir,
        "--phase", "implement",
        "--cycle-id", cycle_id,
        "--expect-run-id", eng["run_id"],
    )
    rc3, out3, _ = run_cohort("status", spec_dir, "--json")
    coh_after = json.loads(out3)
    if (eng["last_event"] != "gates-failed" or rc_i != 0 or rc_r != 0
            or coh_after["implementation_retry_count"]
               != coh_before["implementation_retry_count"] + 1):
        fail("no-chat-history-route-gates-failed-via-cli",
             f"routing failed: rc_r={rc_r} count {coh_before['implementation_retry_count']}"
             f"→{coh_after.get('implementation_retry_count')}")
    else:
        ok("no-chat-history-route-gates-failed-via-cli")
```

**Approach:**

Add a `make_crash_window_run(tmp, feature)` helper that initialises a full run
(engine init → cohort init → spec-ready → reviewers-clean → write Status:
Approved → approve-plan → schedule → plan-approved → write Status: Implementing
→ wave-complete) and returns `(spec_dir, run_id, transition_sequence)`. This
helper drives the FSM to `CODE-VERIFICATION`, providing a consistent starting
point for all crash-window scenarios.

**Required:** `make_crash_window_run` must produce a plan.md with **at least two
tasks** (waves), so `schedule_waves` contains ≥2 entries (e.g. `[["T1"],["T2"]]`).
This is a hard precondition for T2's `wave advance --from-index 0` tests: without
it, the wave-advance guard refuses (`0 < len - 1` is false on a single-wave
schedule) before reaching the increment/no-op paths under test. Use the same
two-task pattern as existing lifecycle tests in `test-loop-engine.py`.

Crash states in T1 tests are reached by firing real engine transitions (not
synthetic state writes). `run_engine("transition", spec_dir, "wave-passed",
"--wave-index", "0")` from CODE-VERIFICATION sets the crash state for wave-passed
recovery tests. `run_engine("transition", spec_dir, "gates-failed")` from
CODE-VERIFICATION sets the crash state for gates-failed recovery tests.

The `tests` list in `main()` must include all four T1 test functions.

**Done when:** all four T1 tests pass; `python3
packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py` exits 0;
`make build-check` (SKIP_SAST=1) passes.

---

### T2: `wave-passed` and `wave advance` interruption tests

**Depends on:** T1
**Mode:** TDD
**ACs:** AC1, AC2, AC3

**Tests:**
```python
def test_wave_passed_window_a_advance_before_crash(tmp: Path) -> None:  # STUB: AC1
    """AC1: window A — current_wave_index == N; advance succeeds and increments."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-a")
    # Set crash state: real wave-passed transition (crash before advance)
    run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")
    before = _read_cohort_state(spec_dir)
    assert before["current_wave_index"] == 0, "pre-condition: index not at 0"
    rc, _, _ = run_cohort(
        "wave", "advance", spec_dir,
        "--from-index", "0", "--expect-run-id", run_id
    )
    after = _read_cohort_state(spec_dir)
    if rc != 0 or after["current_wave_index"] != 1:
        fail("wave-passed-window-a",
             f"rc={rc} idx={after.get('current_wave_index')}")
    else:
        ok("wave-passed-window-a")

def test_wave_passed_window_b_advance_after_crash(tmp: Path) -> None:  # STUB: AC2
    """AC2: window B — current_wave_index == N+1; replay is idempotent no-op."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-b")
    # Set crash state: engine wave-passed, then advance (crash after advance)
    run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")
    run_cohort("wave", "advance", spec_dir, "--from-index", "0", "--expect-run-id", run_id)
    # Advance already applied (current_wave_index == 1); snapshot before replay
    before_json = (spec_dir / "state.json").read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", spec_dir,
        "--from-index", "0", "--expect-run-id", run_id
    )
    after_json = (spec_dir / "state.json").read_bytes()
    if rc != 0 or before_json != after_json:
        fail("wave-passed-window-b",
             f"rc={rc} state_mutated={before_json != after_json}")
    else:
        ok("wave-passed-window-b")

def test_wave_passed_wrong_from_index_refused(tmp: Path) -> None:  # STUB: AC3
    """AC3: wrong --from-index exits non-zero; state.json unchanged."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-wfi")
    run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")
    before = (spec_dir / "state.json").read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", spec_dir,
        "--from-index", "99", "--expect-run-id", run_id
    )
    after = (spec_dir / "state.json").read_bytes()
    if rc == 0 or before != after:
        fail("wave-passed-wrong-from-index-refused",
             f"rc={rc} state_mutated={before != after}")
    else:
        ok("wave-passed-wrong-from-index-refused")

def test_wave_passed_wrong_run_id_refused(tmp: Path) -> None:  # STUB: AC3
    """AC3: wrong --expect-run-id exits non-zero; state.json unchanged."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-wri")
    run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")
    before = (spec_dir / "state.json").read_bytes()
    rc, _, _ = run_cohort(
        "wave", "advance", spec_dir,
        "--from-index", "0",
        "--expect-run-id", "00000000-0000-0000-0000-000000000000"
    )
    after = (spec_dir / "state.json").read_bytes()
    if rc == 0 or before != after:
        fail("wave-passed-wrong-run-id-refused",
             f"rc={rc} state_mutated={before != after}")
    else:
        ok("wave-passed-wrong-run-id-refused")

def test_wave_passed_run_ids_remain_paired_after_advance(tmp: Path) -> None:  # STUB: AC1
    """AC1: engine and cohort run_ids remain paired after recovery."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "wp-pair")
    run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")
    run_cohort("wave", "advance", spec_dir, "--from-index", "0",
               "--expect-run-id", run_id)
    rc, out, _ = run_cohort("identity", spec_dir, "--expect-run-id", run_id)
    if rc != 0:
        fail("wave-passed-run-ids-paired",
             f"identity check failed after advance: rc={rc} {out!r}")
    else:
        ok("wave-passed-run-ids-paired")
```

**T2 helpers (new — to author alongside the stubs):**
- `_read_cohort_state(spec_dir)` — reads and returns parsed `state.json` dict.

No synthetic `_set_engine_wave_passed` helper. Crash states are reached by
calling `run_engine("transition", spec_dir, "wave-passed", "--wave-index", "0")`
from the CODE-VERIFICATION starting point provided by `make_crash_window_run`.

The `tests` list must include all five T2 functions.

**Done when:** all T2 tests pass; no regression in existing tests.

---

### T3: `gates-failed`, idempotent attempt replay, and retry-boundary tests

**Depends on:** T1
**Mode:** TDD
**ACs:** AC4, AC5, AC6

**Tests:**
```python
def test_gates_failed_window_a_record_before_crash(tmp: Path) -> None:  # STUB: AC4
    """AC4: window A — no prior record-attempt; count increments exactly once."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "gf-a")
    # Set crash state: real gates-failed transition (crash before record-attempt)
    run_engine("transition", spec_dir, "gates-failed")
    before = _read_cohort_state(spec_dir)
    eng = json.loads(run_engine("status", spec_dir, "--json")[1])
    cycle_id = f"{run_id}:{eng['transition_sequence']}"
    rc, _, _ = run_cohort(
        "record-attempt", spec_dir,
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id
    )
    after = _read_cohort_state(spec_dir)
    if rc != 0 or after["implementation_retry_count"] != before["implementation_retry_count"] + 1:
        fail("gates-failed-window-a",
             f"rc={rc} count {before['implementation_retry_count']}->"
             f"{after.get('implementation_retry_count')}")
    else:
        ok("gates-failed-window-a")

def test_gates_failed_window_b_record_after_crash(tmp: Path) -> None:  # STUB: AC5
    """AC5: window B — cycle_id already recorded; replay is no-op."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "gf-b")
    run_engine("transition", spec_dir, "gates-failed")
    eng = json.loads(run_engine("status", spec_dir, "--json")[1])
    cycle_id = f"{run_id}:{eng['transition_sequence']}"
    # First call (crash happened after this)
    run_cohort(
        "record-attempt", spec_dir,
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id
    )
    before_2 = _read_cohort_state(spec_dir)
    rc2, _, _ = run_cohort(
        "record-attempt", spec_dir,
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id
    )
    after_2 = _read_cohort_state(spec_dir)
    if rc2 != 0 or before_2["implementation_retry_count"] != after_2["implementation_retry_count"]:
        fail("gates-failed-window-b",
             f"rc2={rc2} count changed {before_2['implementation_retry_count']}"
             f"->{after_2.get('implementation_retry_count')}")
    else:
        ok("gates-failed-window-b")

def test_gates_failed_wrong_run_id_prefix_refused(tmp: Path) -> None:  # STUB: AC4/AC5
    """AC4/AC5: cycle_id with mismatched run_id prefix exits non-zero; state unchanged."""
    spec_dir, run_id, _ = make_crash_window_run(tmp, "gf-wri")
    run_engine("transition", spec_dir, "gates-failed")
    eng = json.loads(run_engine("status", spec_dir, "--json")[1])
    bad_cycle = f"00000000-0000-0000-0000-000000000000:{eng['transition_sequence']}"
    before = (spec_dir / "state.json").read_bytes()
    rc, _, _ = run_cohort(
        "record-attempt", spec_dir,
        "--phase", "implement", "--cycle-id", bad_cycle, "--expect-run-id", run_id
    )
    after = (spec_dir / "state.json").read_bytes()
    if rc == 0 or before != after:
        fail("gates-failed-wrong-run-id-prefix",
             f"rc={rc} state_mutated={before != after}")
    else:
        ok("gates-failed-wrong-run-id-prefix")

def test_gates_failed_fifth_retry_permitted(tmp: Path) -> None:  # STUB: AC6
    """AC6: fifth repair cycle is permitted; implementation_retry_count reaches 5."""
    spec_dir, run_id, _ = _setup_retry_boundary_run(tmp, "gf-5th")
    # Drive count to 4 via direct state write (pre-condition)
    st = _read_cohort_state(spec_dir)
    st["implementation_retry_count"] = 4
    _write_cohort_state(spec_dir, st)
    # Fire the fifth gates-failed transition
    rc_t, _, err_t = run_engine("transition", spec_dir, "gates-failed")
    eng = json.loads(run_engine("status", spec_dir, "--json")[1])
    cycle_id = f"{run_id}:{eng['transition_sequence']}"
    rc_r, _, _ = run_cohort(
        "record-attempt", spec_dir,
        "--phase", "implement", "--cycle-id", cycle_id, "--expect-run-id", run_id
    )
    after = _read_cohort_state(spec_dir)
    if rc_t != 0 or rc_r != 0 or after["implementation_retry_count"] != 5:
        fail("gates-failed-fifth-permitted",
             f"rc_t={rc_t} rc_r={rc_r} count={after.get('implementation_retry_count')}")
    else:
        ok("gates-failed-fifth-permitted")

def test_gates_failed_sixth_retry_refused(tmp: Path) -> None:  # STUB: AC6
    """AC6: sixth gates-failed transition is refused; both state files unchanged."""
    spec_dir, run_id, _ = _setup_retry_boundary_run(tmp, "gf-6th")
    # Set count to 5 (cap exhausted)
    st = _read_cohort_state(spec_dir)
    st["implementation_retry_count"] = 5
    _write_cohort_state(spec_dir, st)
    before_eng = (spec_dir / "engine-state.json").read_bytes()
    before_coh = (spec_dir / "state.json").read_bytes()
    rc_t, _, err_t = run_engine("transition", spec_dir, "gates-failed")
    after_eng = (spec_dir / "engine-state.json").read_bytes()
    after_coh = (spec_dir / "state.json").read_bytes()
    after_st = _read_cohort_state(spec_dir)
    if (rc_t == 0 or before_eng != after_eng or before_coh != after_coh
            or after_st["implementation_retry_count"] != 5):
        fail("gates-failed-sixth-refused",
             f"rc_t={rc_t} eng_mutated={before_eng != after_eng} "
             f"coh_mutated={before_coh != after_coh} "
             f"count={after_st.get('implementation_retry_count')}")
    else:
        ok("gates-failed-sixth-refused")
```

**T3 helpers (new — to author alongside the stubs):**
- `_setup_retry_boundary_run(tmp, feature)` — same as `make_crash_window_run`,
  leaving the engine in `CODE-VERIFICATION` ready to fire `gates-failed`. Returns
  `(spec_dir, run_id, seq)`.
- `_write_cohort_state(spec_dir, state_dict)` — writes state.json atomically;
  used to preset `implementation_retry_count` for boundary tests.
- `_read_cohort_state(spec_dir)` — same as T2; reused here.

No synthetic `_set_engine_gates_failed` helper. Crash states are reached by
calling `run_engine("transition", spec_dir, "gates-failed")` from CODE-VERIFICATION.

The `tests` list must include all five T3 functions.

**Done when:** all T3 tests pass; no regression in existing tests.

---

### T4: Non-idempotent review-window limitation tests, SKILL.md prose, and pack bump

**Depends on:** T1
**Mode:** TDD (state comparison) + goal-based content (SKILL.md prose, --help)
**ACs:** AC8, AC9

**Tests:**
```python
def test_findings_remain_phase_recoverable_from_engine(tmp: Path) -> None:  # STUB: AC8a
    """AC8a: committed phase is readable from engine state via loop-engine status."""
    spec_dir, run_id = make_code_review_run(tmp, "fr-phase")
    # Set crash state: fire real findings-remain from CODE-REVIEW
    run_engine("transition", spec_dir, "findings-remain")
    rc, out, _ = run_engine("status", spec_dir, "--json")
    eng = json.loads(out)
    if rc != 0 or eng.get("last_event") != "findings-remain":
        fail("findings-remain-phase-recoverable",
             f"rc={rc} last_event={eng.get('last_event')!r}")
    else:
        ok("findings-remain-phase-recoverable")

def test_findings_remain_no_auto_replay(tmp: Path) -> None:  # STUB: AC8b
    """AC8b: cohort state.json unchanged after running the recovery read sequence
    (engine status + cohort status) without calling review record --fingerprint."""
    spec_dir, run_id = make_code_review_run(tmp, "fr-noreplay")
    run_engine("transition", spec_dir, "findings-remain")
    before = (spec_dir / "state.json").read_bytes()
    # Run the full documented read sequence; require all reads to succeed.
    rc_s, out_s, _ = run_engine("status", spec_dir, "--json")
    rc_i, _, _ = run_cohort("identity", spec_dir, "--expect-run-id", run_id)
    rc_c, out_c, _ = run_cohort("status", spec_dir, "--json")
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

def test_findings_remain_skill_prose_present(tmp: Path) -> None:  # STUB: AC8c
    """AC8c: the findings-remain session-resumption table row contains required phrases."""
    skill_path = SCRIPT_DIR.parent / "SKILL.md"
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    # Extract the single table row for findings-remain in CODE-IMPLEMENTATION
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
    required = [
        "stale fingerprint baseline",
        "under-count",
        "do NOT auto-reissue",
    ]
    missing = [p for p in required if p not in row_line]
    if missing:
        fail("findings-remain-skill-prose-present",
             f"findings-remain row missing phrases: {missing}")
    else:
        ok("findings-remain-skill-prose-present")

def test_reviewers_clean_record_forms_present(tmp: Path) -> None:  # STUB: AC9
    """AC9: --report and --all-skipped forms exist in loop-cohort review record help."""
    rc, out, err = run_cohort("review", "record", "--help")
    combined = out + err
    if "--report" not in combined or "--all-skipped" not in combined:
        fail("reviewers-clean-record-forms-present",
             f"missing forms in help: {combined!r}")
    else:
        ok("reviewers-clean-record-forms-present")

def test_reviewers_clean_no_silent_replay(tmp: Path) -> None:  # STUB: AC9
    """AC9: cohort state.json unchanged after running the recovery read sequence
    (engine status + cohort status) without calling review record --report."""
    spec_dir, run_id = make_code_review_run(tmp, "rc-noreplay")
    # Set crash state: write Status: Shipped and fire real reviewers-clean
    write_spec(spec_dir, status="Shipped")
    run_engine("transition", spec_dir, "reviewers-clean")
    before = (spec_dir / "state.json").read_bytes()
    # Run the full documented read sequence; require all reads to succeed.
    rc_s, out_s, _ = run_engine("status", spec_dir, "--json")
    rc_i, _, _ = run_cohort("identity", spec_dir, "--expect-run-id", run_id)
    rc_c, out_c, _ = run_cohort("status", spec_dir, "--json")
    # Deliberately do NOT call review record --report
    after = (spec_dir / "state.json").read_bytes()
    if rc_s != 0 or rc_i != 0 or rc_c != 0:
        fail("reviewers-clean-no-silent-replay",
             f"recovery reads failed: rc_s={rc_s} rc_i={rc_i} rc_c={rc_c}")
    elif before != after:
        fail("reviewers-clean-no-silent-replay",
             "state.json mutated by read-only recovery sequence")
    else:
        ok("reviewers-clean-no-silent-replay")

def test_reviewers_clean_skill_prose_obligations(tmp: Path) -> None:  # STUB: AC9
    """AC9: the reviewers-clean session-resumption table row contains required phrases."""
    skill_path = SCRIPT_DIR.parent / "SKILL.md"
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    # Extract the single table row for reviewers-clean in CODE-HUMAN-GATE
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
    required = [
        "non-idempotent",
        "double-increment",
        "fingerprint audit history",
        "authorized",
    ]
    missing = [p for p in required if p not in row_line]
    if missing:
        fail("reviewers-clean-skill-prose-obligations",
             f"reviewers-clean row missing phrases: {missing}")
    else:
        ok("reviewers-clean-skill-prose-obligations")
```

**T4 helpers (new — to author alongside the stubs):**
- `make_code_review_run(tmp, feature)` — drives a fresh 1-wave run to `CODE-REVIEW`
  via real CLI: engine init → cohort init → spec-ready → reviewers-clean → write
  Status: Approved → approve-plan → schedule → plan-approved → wave-complete →
  gates-clean → CODE-REVIEW. Returns `(spec_dir, run_id)`. Uses a 1-wave plan
  (`write_plan(spec_dir, content="# Plan\n\n### T1\n\n**Depends on:** none\n")`)
  so that the single wave is the last wave and `gates-clean` (not `wave-passed`)
  exits CODE-VERIFICATION.

**SKILL.md prose enhancements (in-scope):**

Edit the `reviewers-clean` row in the Session Resumption table of
`packs/core/.apm/skills/work-loop/SKILL.md` to make the consequence language
explicit. Extend the Changes-requested cell to say: "— specifically that a replay
may double-increment `review_round_count` and overwrite one level of fingerprint
audit history; explicit human authorization required before any replay".

After editing `packs/core/.apm/skills/work-loop/SKILL.md`, the pack requires a
**patch version bump** (prose-body change = patch increment):
- `packs/core/pack.toml`: bump `[pack] version` from `1.0.0` to `1.0.1`
- `packs/core/.claude-plugin/plugin.json`: bump `"version"` to `"1.0.1"`
- `docs/product/changelog.md`: add `## [core][1.0.1] — 2026-07-31` section
- Run `FORCE=1 make build-self` to regenerate projections

The T4 tests must include all six functions.

**Done when:** all T4 tests pass; SKILL.md prose enhancement in place;
pack bumped to `1.0.1`; changelog entry added; `FORCE=1 make build-self` exits
clean; no regression in existing tests.

---

### T5: Full gates, documentation closure, and end-to-end verification

**Depends on:** T2, T3, T4
**Mode:** goal-based + visual/manual QA
**ACs:** AC10, AC11

**Tests:**
```bash
# Goal-based:
python3 packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py
make build-check SKIP_SAST=1
python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .
```

**Approach:**

1. Check AC6 in `docs/specs/loop-infrastructure-phase-1/spec.md`:
   change `- [ ]` to `- [x]` and remove `(deferred: loop-infra-crash-window-tests)`.
2. Mark this spec `Status: Shipped`; mark plan.md `Status: Done`.
3. Remove the `{slug = "loop-infra-crash-window-tests", ...}` entry from
   `[backlog].open` in `workspace.toml`.
4. Add this spec to `docs/specs/README.md` active list (required by new-spec step 7).
5. Run `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
   and verify clean.
6. Run `FORCE=1 make build-self` to verify no projection drift.
7. Run `make build-check SKIP_SAST=1` for full build gates.

**Manual QA — happy-path recovery (wave-passed scenario):**
- Init a fresh run in a temp dir; drive to `CODE-VERIFICATION`.
- Fire `loop-engine transition ... wave-passed --wave-index 0`; verify engine
  state has `last_event: wave-passed` and `last_event_context.completed_wave_index: 0`.
- In a fresh shell: run `loop-engine status --json`; verify `last_event: wave-passed`.
- Run `loop-cohort identity --expect-run-id <run_id>`; verify exit 0.
- Run `loop-cohort status --json`; read `current_wave_index`.
- Run `loop-cohort wave advance --from-index 0 --expect-run-id <run_id>`.
- Verify exit 0 and `current_wave_index == 1`.
- Record observed output in PR description.

**Done when:** all crash-window tests pass; `lint-spec-status.py` clean;
`make build-check` (SKIP_SAST=1) green; Phase 1 AC6 checked off; backlog entry
removed; `docs/specs/README.md` updated; manual QA result recorded in PR.

---

## Changelog

- Initial draft — full mode.
- Rev 1 — addressed adversarial-reviewer findings: added `tests` list registration
  requirement; added SKILL.md prose enhancements to scope; replaced bare stubs with
  compiling contract-surface assertions; added `(tmp: Path)` parameter to all test
  stubs; fixed T3 retry mechanism to call `record-attempt`; scoped SKILL.md grep
  assertions to actual phrases; fixed lint path; clarified conflicting-cycle-id
  behavior to run_id-prefix mismatch only.
- Rev 2 — addressed second adversarial-reviewer findings: fixed vacuous no-replay
  tests (now run read-only recovery sequence between snapshots); reconciled spec
  Objective to state only one SKILL.md row is edited; documented T2/T3 new helpers
  (_read_cohort_state, _set_cohort_wave_index, _write_cohort_state,
  _setup_retry_boundary_run).
- Rev 3 — addressed third adversarial-reviewer findings: fixed stale "two
  enhancements" phrasing in Context (now matches spec: one row, reviewers-clean
  only); scoped SKILL.md grep assertions to the specific table row (extract the
  matching line, not whole-file text) for AC8c and AC9.
- Rev 4 — addressed fourth adversarial-reviewer findings: fixed operator-precedence
  bug in row-extraction filters (parenthesized `(A or B) and C`); documented the
  ≥2-wave precondition for `make_crash_window_run` in T1 Approach.
- Rev 5 — addressed Codex CLI review findings: (1) changed spec Shape from `code`
  to `mixed`; (2) added spec Assumptions section; (3) removed all synthetic
  `_set_engine_*` helpers — crash states now reached via real CLI transitions;
  (4) added `make_code_review_run` helper (drives to CODE-REVIEW for T4 tests);
  (5) added engine-state.json snapshot to sixth-retry refusal test (AC6); (6) added
  rc assertions to no-replay recovery reads (AC8b, AC9); (7) added T4 pack version
  bump (1.0.0→1.0.1), changelog entry, and eval check; (8) added
  `docs/specs/README.md` update to T5.
