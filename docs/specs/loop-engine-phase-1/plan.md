# Plan: loop-engine-phase-1

- **Spec:** [`spec.md`](spec.md)
- **Verification modes:** TDD (loop-engine.py, check-spec-status.py), goal-based (SKILL.md, build-check), visual QA (SKILL.md diff, manual lifecycle trace)

## Declined temptations

**Daemon or watch mode for loop-engine.** A persistent process that fires
events automatically when build output changes sounds convenient for
long-running EXECUTE waves. Declined for phase 1 because INI-003's polling
model (`status --json` on a cron) already provides the supervisory observation
loop it needs, and a daemon introduces process-management complexity (PID files,
signal handling, restart semantics) that one-shot CLI avoids entirely.
*Disposition: deferred.* A watch variant is the natural INI-003 or
loop-engine phase 2 follow-on once the one-shot interface is battle-tested and
the polling cost becomes measurable.

**`--force` flag to bypass guards.** If a guard exits non-zero, a `--force`
flag could let the LLM override it and advance the state anyway. Declined
*permanently* — this would make the two human gates (`G-plan` and `G-pr`)
bypassable by the loop itself, violating `DESIGN.md §13 invariant #1`
("the loop cannot self-certify"). The guard contract must be unconditional; see
AC-E3. The right recovery for a stuck guard is to surface the reason to the
human and let the human direct the fix, not to silently bypass the gate.

**Pack-detection logic in loop-engine.** Loop-engine could inspect the working
directory (look for `pack.toml`, detect a SKILL.md) and auto-select `--mode`
rather than requiring the caller to pass it. Declined *permanently* — the skill
decides the mode from context; the engine is mode-agnostic by design. Embedding
heuristic detection logic would couple loop-engine to the current pack layout and
make it fragile against future structural changes. The SKILL.md's mode-selection
table is the single source of truth for this mapping; the engine must not
duplicate it.

**Merging `check-spec-status.py` into `lint-spec-status.py`.** Both scripts
inspect `**Status:**` in a spec file, so the logic is related. Declined for
phase 1 to preserve the clean boundary between the two call sites:
`check-spec-status.py` is an FSM guard called by loop-engine at a specific
transition point; `lint-spec-status.py` is a CI-level drift linter that runs
separately and also validates the status enum. Merging them would blur this
boundary and make the FSM guard dependent on a CI tool, complicating both
invocation paths. *Disposition: keep separate permanently.* If the overlap
becomes maintenance pain, the right resolution is a shared helper imported by
both — not a merge that conflates guard and linter semantics.

**Retry logic in side-effect failure path.** When a side effect (e.g.,
`loop-cohort review record`) fails, an automatic retry sounds like good
defensive programming. Declined *permanently* — `review record` is
non-idempotent (it increments `iteration_count` and rotates fingerprints);
a silent retry would corrupt the loop state. The correct recovery is to log
the failure to stderr, leave the FSM state written, and surface to the human.
The human can direct a manual `loop-cohort review record` call with full
context of what failed and why. Idempotent side effects like `schedule` are
safe to re-run, but the policy cannot vary per side effect without adding
fragile per-verb metadata — uniform "log and surface" is simpler and safer.

**Committed state or git operations in loop-engine.** Loop-engine could commit
`engine-state.json` after each transition, or push the branch before a
human-gate wait state, as a convenience for session resumption. Declined
*permanently* — `engine-state.json` is intentionally gitignored and
session-local; no branch changes are the engine's responsibility. The session
boundary is handled by the SKILL.md's human-wait state guidance (AC-E4), which
tells the LLM to ensure work product is on a named branch or open PR before
ending a session. Git operations belong to the LLM acting on the skill's
guidance, not to a mechanical engine that runs between transitions. A future
companion script could be git-aware, but loop-engine itself must not be.

## Assumptions (verified before EXECUTE)

1. `loop-cohort.py` exit-code contract is stable: exit 0 on success, non-zero with one-line stderr on failure.
2. `check --phase {plan,implement,review}` are the only loop-cohort guard verbs needed; no new verbs required.
3. `make build-self` regenerates the projected SKILL.md and plugin.json after source edits.
4. `SKIP_SAST=1 make build-check` passes on the current branch before EXECUTE begins.
5. `dispatch-decision` verb signature is `--branch <b> [--branch <b>...] [--category <c>...] [--base <ref>]` — verified from source before documenting in arch doc.

## Tasks

### Task 1 — `check-spec-status.py`

**Depends on:** none

**Tests:**
```python
# tests/test_check_spec_status.py
def test_exits_0_when_status_shipped(tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("**Status:** Shipped\n")
    result = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True)
    assert result.returncode == 0

def test_exits_nonzero_when_status_implementing(tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("**Status:** Implementing\n")
    result = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True)
    assert result.returncode != 0
    assert result.stderr  # one-line message

def test_exits_nonzero_when_spec_absent(tmp_path):
    result = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True)
    assert result.returncode != 0

def test_exits_nonzero_when_status_line_absent(tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\nNo status line here.\n")
    result = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True)
    assert result.returncode != 0
```

**Approach:** Parse `spec.md` line by line; match `r'^\*\*Status:\*\*\s*(\S+)'`; exit 0 iff match group is `Shipped`. Pure stdlib. Single positional `work_dir` argument (file or directory; resolves per AC-A3) with `--help`.

**Done when:** `python3 tests/test_check_spec_status.py` passes; `python3 packs/core/.apm/skills/work-loop/scripts/check-spec-status.py --help` prints usage.

---

### Task 2 — `loop-engine.py` core FSM

**Depends on:** none (can build in parallel with Task 1)

**Tests:**
```python
# tests/test_loop_engine_integration.py — stubs for Task 2

def test_init_creates_engine_state_json(tmp_spec):
    run_engine("init", str(tmp_spec), "--mode", "spec-plan")
    state = json.loads((tmp_spec / "engine-state.json").read_text())
    assert state["state"] == "SPEC-PLAN-DRAFTING"
    assert state["mode"] == "spec-plan"

def test_init_refuses_if_already_exists(tmp_spec):
    run_engine("init", str(tmp_spec), "--mode", "spec-plan")
    result = run_engine("init", str(tmp_spec), "--mode", "spec-plan", check=False)
    assert result.returncode != 0

def test_invalid_transition_exits_nonzero(tmp_spec):
    run_engine("init", str(tmp_spec), "--mode", "spec-plan")
    result = run_engine("transition", str(tmp_spec), "plan-approved", check=False)
    assert result.returncode != 0
    assert result.stderr

def test_spec_plan_full_lifecycle(tmp_spec, mock_loop_cohort_ok):
    run_engine("init", str(tmp_spec), "--mode", "spec-plan")
    run_engine("transition", str(tmp_spec), "spec-ready")
    run_engine("transition", str(tmp_spec), "reviewers-clean")
    run_engine("transition", str(tmp_spec), "plan-approved")
    state = json.loads((tmp_spec / "engine-state.json").read_text())
    assert state["state"] == "DONE"

def test_doc_full_lifecycle(tmp_spec):
    run_engine("init", str(tmp_spec), "--mode", "doc")
    run_engine("transition", str(tmp_spec), "doc-ready")
    run_engine("transition", str(tmp_spec), "reviewers-clean")
    run_engine("transition", str(tmp_spec), "doc-approved")
    state = json.loads((tmp_spec / "engine-state.json").read_text())
    assert state["state"] == "DONE"

def test_status_json(tmp_spec, mock_loop_cohort_ok):
    run_engine("init", str(tmp_spec), "--mode", "doc")
    result = run_engine("status", str(tmp_spec), "--json")
    data = json.loads(result.stdout)
    assert {"feature", "mode", "state", "last_transition_at"} == set(data)

def test_reset_idempotent(tmp_spec):
    run_engine("init", str(tmp_spec), "--mode", "doc")
    run_engine("reset", str(tmp_spec))
    assert not (tmp_spec / "engine-state.json").exists()
    run_engine("reset", str(tmp_spec))  # second reset exits 0
```

**Approach:**
- `argparse` with subcommands `init`, `transition`, `status`, `reset`.
- FSM defined as a dict: `TRANSITIONS[mode][(current_state, event)] = next_state`.
- `init`: writes `engine-state.json` atomically via `tempfile.NamedTemporaryFile` + `os.replace`. Runs `loop-cohort init` for code/spec-plan modes.
- `transition`: read state → validate → run guards (subprocess) → write new state → run side effects (subprocess).
- `status`: read and emit; `--json` emits raw JSON.
- `reset`: `Path.unlink(missing_ok=True)`.

**Done when:** Task 2 stubs pass (red); Task 3 wires guards/side-effects (green).

---

### Task 3 — Guards and side effects wiring

**Depends on:** Task 2

**Tests:**
```python
def test_guard_refusal_blocks_transition(tmp_spec, mock_loop_cohort_fail):
    run_engine("init", str(tmp_spec), "--mode", "spec-plan")
    run_engine("transition", str(tmp_spec), "spec-ready")
    run_engine("transition", str(tmp_spec), "reviewers-clean")
    # plan-approved guard calls loop-cohort check --phase plan → fails
    result = run_engine("transition", str(tmp_spec), "plan-approved", check=False)
    assert result.returncode != 0
    state = json.loads((tmp_spec / "engine-state.json").read_text())
    assert state["state"] == "SPEC-PLAN-HUMAN-GATE"  # not advanced

def test_check_spec_status_guard_blocks_code_review_clean(tmp_spec, mock_loop_cohort_ok, mock_check_spec_status_fail):
    # drive to CODE-REVIEW state then try reviewers-clean
    ...
    result = run_engine("transition", str(tmp_spec), "reviewers-clean", check=False)
    assert result.returncode != 0

def test_plan_approved_triggers_schedule_side_effect(tmp_spec, mock_loop_cohort_ok, captured_calls):
    # drive code mode to SPEC-PLAN-HUMAN-GATE, fire plan-approved
    ...
    assert any("schedule" in c for c in captured_calls)

def test_reviewers_clean_from_spec_plan_review_does_not_trigger_review_record(tmp_spec, mock_loop_cohort_ok, captured_calls):
    run_engine("init", str(tmp_spec), "--mode", "spec-plan")
    run_engine("transition", str(tmp_spec), "spec-ready")
    run_engine("transition", str(tmp_spec), "reviewers-clean")
    assert not any("review record" in c for c in captured_calls)

def test_reviewers_clean_from_code_review_triggers_review_record(tmp_spec, ...):
    # drive code mode to CODE-REVIEW, fire reviewers-clean
    ...
    assert any("review record" in c for c in captured_calls)
```

**Approach:**
- Guard table: `GUARDS[(mode, current_state, event)] = [guard_cmd_fn, ...]`.
- Side-effect table: `SIDE_EFFECTS[(mode, current_state, event)] = [effect_cmd_fn, ...]`.
- Subprocess invocations pass `check=False`; non-zero from guard → engine exits non-zero (transition rolled back — state not written); non-zero from side effect → logged to stderr, transition not reversed.
- `--fingerprints` nargs='+' on `transition`; expands to repeated `--fingerprint` for loop-cohort.

**Done when:** All Task 3 stubs green; `SKIP_SAST=1 make build-check` passes.

---

### Task 4 — SKILL.md reduction

**Depends on:** Tasks 1–3 (loop-engine.py must exist before removing choreography prose)

**Tests:** (goal-based)
- `make build-self` exits 0.
- `python tools/lint-agent-artifacts.py` exits 0.
- Risk-triggers grep-equality: `diff <(grep -A100 'risk-triggers:start' AGENTS.md | grep -B100 'risk-triggers:end') <(grep -A100 'risk-triggers:start' packs/core/.apm/skills/work-loop/SKILL.md | grep -B100 'risk-triggers:end')` exits 0.
- SKILL.md line count decreases vs origin/main (mode/checkpoint tables moved to `references/loop-infrastructure.md`; net ~16 lines; choreography prose removed per AC-H2).

**Approach:**
- Remove: "Initialize the loop's state file" block (PLAN section), `loop-cohort schedule`/`dispatch-decision` supervisor blocks (EXECUTE section), "record findings via the tool" block (REVIEW section), condition #2 `loop-cohort.py check` block (Termination section).
- Add: mode-selection table (work type → `loop-engine init --mode`; light mode row = "skip"), checkpoint table (state | event | human gate? | guards | modes), pointer to `docs/architecture/loop-infrastructure.md`.
- Extend light-mode note to include "and no `loop-engine`".
- Preserve byte-identical risk-triggers sentinel block.

**Done when:** Goal-based checks pass; visual diff confirms judgment content intact.

---

### Task 5 — `packs/core/pack.toml` version bump + `make build-self`

**Depends on:** Task 4

**Tests:** (goal-based)
- `grep version packs/core/pack.toml` shows `0.15.8`.
- `make build-self` exits 0.
- `git diff .claude/skills/work-loop/scripts/loop-engine.py` shows projected copy.

**Approach:** Bump `version` in `packs/core/pack.toml` from `0.15.7` to `0.15.8`. Run `make build-self`. Verify projected copies of `loop-engine.py` and `check-spec-status.py` appear under `.claude/skills/work-loop/scripts/`.

**Done when:** `make build-self` passes; both new scripts appear in projection.

---

### Task 6 — Architecture doc pointer + gitignore + ecosystem

**Depends on:** none (parallel with Tasks 1–2)

**Tests:** (goal-based)
- `grep loop-infrastructure docs/architecture/overview.md` finds the new bullet.
- `git check-ignore -v docs/specs/dummy/engine-state.json` exits 0.
- `grep 'loop-engine status' docs/product/shaping/ecosystem-overview.md` finds the sentence.

**Approach:**
- Add bullet to `docs/architecture/overview.md` Subsystems section.
- Add `docs/specs/**/engine-state.json` to `.gitignore` if not already covered.
- Add one sentence to INI-003 section of `docs/product/shaping/ecosystem-overview.md`.
- Add `"spec/loop-engine-phase-1"` to `["ini-002".work].queue` in `workspace.toml` (after G-plan approval).

**Done when:** All three goal-based checks pass.

---

### Task 7 — Manual QA trace (verify step)

**Depends on:** Tasks 1–5

**Tests:** (visual / manual QA)
- `loop-engine --help` and all subcommand `--help` print usage without error.
- Run complete `spec-plan` lifecycle on a scratch spec directory:
  1. `mkdir /tmp/scratch-spec && echo "**Status:** Draft" > /tmp/scratch-spec/spec.md`
  2. `loop-engine init /tmp/scratch-spec --mode spec-plan`
  3. `cat /tmp/scratch-spec/engine-state.json` → state: SPEC-PLAN-DRAFTING
  4. `loop-engine transition /tmp/scratch-spec spec-ready`
  5. `loop-engine transition /tmp/scratch-spec reviewers-clean`
  6. `loop-cohort approve-plan /tmp/scratch-spec`
  7. `loop-engine transition /tmp/scratch-spec plan-approved`
  8. `loop-engine status /tmp/scratch-spec --json` → emits valid JSON, state: DONE
- `check-spec-status.py /tmp/scratch-spec` → exits non-zero (Status is Draft, not Shipped).
- `sed -i '' 's/Status: Draft/Status: Shipped/' /tmp/scratch-spec/spec.md && check-spec-status.py /tmp/scratch-spec` → exits 0.

**Done when:** All trace steps produce the documented output.

## Verification summary

| Deliverable | Mode | Gate |
|---|---|---|
| `loop-engine.py` | TDD | `pytest tests/test_loop_engine_integration.py` |
| `check-spec-status.py` | TDD | `pytest tests/test_check_spec_status.py` |
| Guards + side effects | TDD | included in loop-engine integration tests |
| `SKILL.md` reduction | goal-based | `make build-self`, lint-agent-artifacts, risk-triggers grep |
| `pack.toml` bump | goal-based | `make build-self`, version grep |
| arch doc pointer, gitignore, ecosystem | goal-based | targeted greps |
| End-to-end | manual QA | Task 7 trace |
