# Plan: loop-approved-spec-state

- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Decision:** [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md)
- **Spec:** [`spec.md`](spec.md)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This change splits the single `SPEC-PLAN-HUMAN-GATE` state into two — `SPEC-HUMAN-GATE` (scope decision) and `PLAN-HUMAN-GATE` (build decision) — each with its own human signal and guard. The spec approver writes `Status: Approved` to `spec.md`; the plan approver writes `Status: Approved` to `plan.md`. Both rejections return to `SPEC-PLAN-DRAFTING`.

After both approvals, a durable `SPEC-PLAN-APPROVED` state holds while the cohort records the approved baseline (`approve-plan`, `schedule`). The `plan-locked` event (analogous to the original `approval-committed` concept) seals the baseline and hands off to implementation.

The work is sequenced so conventions (T1) land first, engine + check-spec-status (T2) and cohort idempotency (T3) are independent, guidance + architecture (T4) depends on T2+T3, and integration/release (T5) closes out.

The riskiest part is the rename of `SPEC-PLAN-HUMAN-GATE` → `SPEC-HUMAN-GATE` throughout the codebase — it touches test helpers, existing tests, and SKILL.md content assertions. The anchor-test sweep in T2 must enumerate all affected locations before production code changes.

## Constraints

- ADR-0061: `loop-engine` owns phase state and read-only guards; `loop-cohort` owns execution-state mutations. The engine never writes `state.json`.
- No in-place replanning after `SPEC-PLAN-APPROVED`; post-approval plan changes require the reset-pair + new run.
- Approved baseline is immutable once recorded by `approve-plan` — idempotent no-op or refuse, never silent rebaseline.
- `SPEC-PLAN-APPROVED` must not be in `_HUMAN_WAIT_STATES`.
- `SPEC-HUMAN-GATE` and `PLAN-HUMAN-GATE` must both be in `_HUMAN_WAIT_STATES`.
- `schedule` is only called in code mode; spec-plan `plan-locked` guard has no schedule requirement.

## Construction tests

**Integration tests (cross-task):**

- Full code-mode approval path (T2+T3+T5): `init pair → spec-ready → reviewers-clean → SPEC-HUMAN-GATE → spec-approved → PLAN-HUMAN-GATE → plan-approved → SPEC-PLAN-APPROVED → approve-plan → schedule → plan-locked → CODE-IMPLEMENTATION` — all CLIs exit 0; states verified at each step.
- Full spec-plan-mode approval path: same through `plan-locked → DONE`; spec Status `Approved` and plan Status `Approved` remain.
- Crash-window tests (T3+T2): processes halted at each step between `PLAN-HUMAN-GATE` and `CODE-IMPLEMENTATION`; verify idempotent resume succeeds.

**Manual verification (recorded in `notes/manual-qa.md`):**
- Code-mode end-to-end via real CLI (AC9).
- Spec-plan-mode end-to-end via real CLI (AC9).

## Design (LLD)

### Design decisions

- **Split SPEC-HUMAN-GATE / PLAN-HUMAN-GATE** separates two genuinely distinct stakeholder decisions: scope acceptance (a product/design call) and build-strategy acceptance (a technical call). Traces to: AC1, AC3.
- **`plan.md Status: Approved`** as the plan-gate signal gives each approver a dedicated artifact to review and sign; no new field or file needed. Traces to: AC1, AC4.
- **`check-spec-status.py --file` flag** lets the same parser check either artifact; no duplicate status-reading logic. Traces to: AC4.
- **Idempotency on `approve-plan`** uses existing `approved_spec_hash` / `approved_plan_hash` — no new fields. Traces to: AC5.
- **Both rejections → `SPEC-PLAN-DRAFTING`** because a plan rejection sometimes requires re-scoping; merging both paths keeps the FSM simple. Traces to: AC1, Constraints.
- **Legacy compatibility** is documentation-only; engine-state files with `CODE-IMPLEMENTATION + last_event: plan-approved` or `DONE + last_event: plan-approved` carry states that don't accept those events, so the existing illegal-transition guard already blocks any accidental re-fire. Traces to: AC6.

### State & control flow

**Updated code-mode FSM (10 states):**

```
SPEC-PLAN-DRAFTING
  --spec-ready-->
SPEC-PLAN-REVIEW
  --reviewers-clean-->
SPEC-HUMAN-GATE            [pending_human_wait: true]
  --spec-approved-->          guard: spec.md Status == Approved
PLAN-HUMAN-GATE            [pending_human_wait: true]
  --plan-approved-->          guard: plan.md Status == Approved
SPEC-PLAN-APPROVED         [pending_human_wait: false]
  --plan-locked-->            guard: spec.md Status==Approved + plan check-current --require-schedule
CODE-IMPLEMENTATION
  --wave-complete-->
CODE-VERIFICATION
  --wave-passed-->   CODE-IMPLEMENTATION
  --gates-clean-->   CODE-REVIEW
  --gates-failed-->  CODE-IMPLEMENTATION
CODE-REVIEW
  --reviewers-clean-->        guard: spec.md Status == Shipped
CODE-HUMAN-GATE            [pending_human_wait: true]
  --done-->
DONE

Rejection paths (both modes):
  SPEC-HUMAN-GATE  --spec-rejected--> SPEC-PLAN-DRAFTING
  PLAN-HUMAN-GATE  --plan-rejected--> SPEC-PLAN-DRAFTING
```

**Updated spec-plan-mode FSM (6 states):**

```
SPEC-PLAN-DRAFTING
  --spec-ready-->
SPEC-PLAN-REVIEW
  --reviewers-clean-->
SPEC-HUMAN-GATE            [pending_human_wait: true]
  --spec-approved-->          guard: spec.md Status == Approved
PLAN-HUMAN-GATE            [pending_human_wait: true]
  --plan-approved-->          guard: plan.md Status == Approved
SPEC-PLAN-APPROVED         [pending_human_wait: false]
  --plan-locked-->            guard: spec.md Status==Approved + plan check-current (no schedule)
DONE
```

**New G-plan sequence (canonical home: `SKILL.md` Step 1 PLAN, item 12 — this block is a design reference):**

```
# 1. Spec approver writes Status: Approved in spec.md.
python scripts/loop-engine.py transition <spec-dir> spec-approved
  # → PLAN-HUMAN-GATE; pending_human_wait: true

# 2. Plan approver writes Status: Approved in plan.md.
python scripts/loop-engine.py transition <spec-dir> plan-approved
  # → SPEC-PLAN-APPROVED; pending_human_wait: false

# 3. Cohort records the approved baseline:
python scripts/loop-cohort.py approve-plan <spec-dir> --expect-run-id <run_id>
  # → records approved_spec_hash, approved_plan_hash; idempotent on replay

# 4. code mode only:
python scripts/loop-cohort.py schedule <spec-dir> --expect-run-id <run_id>

# 5. Seal the baseline:
python scripts/loop-engine.py transition <spec-dir> plan-locked
  # code mode → CODE-IMPLEMENTATION; write Status: Implementing before code
  # spec-plan mode → DONE; retain Status: Approved in both files
```

### Interfaces & contracts

`check-spec-status.py` updated CLI:

```
check-spec-status.py <spec-dir> [--expect <status>] [--file <filename>]
```

- `--expect` omitted → defaults to `Shipped`.
- `--file` omitted → defaults to `spec.md`.
- `--file plan.md --expect Approved` → reads `<spec-dir>/plan.md`, checks `Status: Approved`.

`plan.md` template gains `Approved` in status comment:

```
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
```

`loop-cohort approve-plan` idempotency contract (unchanged from original design):

```
plan_review_status == pending
  → record hashes; mark approved; exit 0

already approved + same run_id + spec.md hash unchanged + plan.md hash unchanged
  → idempotent no-op; exit 0

already approved + any hash differs
  → exit non-zero; no mutation

run_id mismatch
  → exit non-zero; no mutation
```

`loop-cohort status --json` adds `plan_review_status` to output dict.

### Failure, edge cases & resilience

- Guard failure leaves `engine-state.json` unchanged (atomic write; guard runs before write). AC2/AC4.
- Crash after writing spec.md `Status: Approved` but before `spec-approved`: resumption detects `SPEC-HUMAN-GATE` + Status `Approved` → auto-fires `spec-approved`. AC6.
- Crash after `spec-approved` but before plan.md `Status: Approved`: `PLAN-HUMAN-GATE` + plan Status `Drafting` → continues waiting. AC6.
- Crash after plan.md `Status: Approved` but before `plan-approved`: resumption detects `PLAN-HUMAN-GATE` + plan Status `Approved` → auto-fires `plan-approved`. AC6.
- Crash after `plan-approved` but before `approve-plan`: `SPEC-PLAN-APPROVED` + `plan_review_status=pending` → re-runs `approve-plan` (normal first write). AC6.
- Crash after `approve-plan` but before `plan-locked`: `SPEC-PLAN-APPROVED` + `plan_review_status=approved` + hashes unchanged → `approve-plan` is no-op; `plan-locked` runs normally. AC6.

## Tasks

### T1: Spec contract, status semantics, and normative FSM

**Depends on:** none

**Tests:**
- Content assertion: `docs/CONVENTIONS.md` and `packs/core/seeds/docs/CONVENTIONS.md` both contain an `Approved` definition covering its roles in both `spec.md` and `plan.md`. Grep-based goal-check.
- Content assertion: The plan-vocabulary parenthetical in both CONVENTIONS.md files (the line listing `Drafting | Executing | Done`) now reads `Drafting | Approved | Executing | Done`. Grep-based goal-check.
- `packs/core/.apm/skills/new-spec/assets/plan.md` status comment includes `Approved` (i.e., `Drafting | Approved | Executing | Done`). Grep-based goal-check.
- `lint-spec-status.py` vocabulary includes `Approved`. Grep-based goal-check.
- RFC/ADR regression (AC8): existing RFC and ADR template files use `Accepted`; no template sets `Approved` as an RFC/ADR lifecycle value. Grep-based goal-check.

**Approach:**
- Write this spec.md and plan.md (already done).
- In `docs/CONVENTIONS.md`: (a) update the plan-vocabulary parenthetical (the line listing plan statuses) from `Drafting | Executing | Done` to `Drafting | Approved | Executing | Done`; (b) add adjacent definition "`Approved` means the spec/plan contract has received human approval. In `spec.md` it means the scope is accepted; in `plan.md` it means the implementation strategy is accepted. Before code changes begin, an implementation run moves `spec.md` to `Implementing`."
- Apply the identical two-part change to `packs/core/seeds/docs/CONVENTIONS.md`.
- In `packs/core/.apm/skills/new-spec/assets/plan.md`: update the Status comment from `Drafting | Executing | Done` to `Drafting | Approved | Executing | Done`.
- Verify `lint-spec-status.py` already lists `Approved` in its `VALID_STATUSES` set.

**Done when:** `grep "Approved means" docs/CONVENTIONS.md packs/core/seeds/docs/CONVENTIONS.md` returns the definition in both files; `grep "Approved" packs/core/.apm/skills/new-spec/assets/plan.md` returns the updated status comment; `SKIP_SAST=1 make build-check` passes.

**Touches:** `docs/CONVENTIONS.md`, `packs/core/seeds/docs/CONVENTIONS.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `docs/specs/loop-approved-spec-state/spec.md`, `docs/specs/loop-approved-spec-state/plan.md`

---

### T2: Engine two-gate states, events, guards, and check-spec-status

**Depends on:** T1

**Tests (TDD — write stubs before production change):**

FSM table tests:
- `test_legal_reviewers_clean_to_spec_human_gate` — both modes.
- `test_legal_spec_approved_to_plan_human_gate_code` — code mode: `SPEC-HUMAN-GATE + spec-approved → PLAN-HUMAN-GATE` (spec Status=Approved).
- `test_legal_spec_approved_to_plan_human_gate_spec_plan` — spec-plan mode: same.
- `test_legal_plan_approved_to_spec_plan_approved_code` — code: `PLAN-HUMAN-GATE + plan-approved → SPEC-PLAN-APPROVED` (plan Status=Approved).
- `test_legal_plan_approved_to_spec_plan_approved_spec_plan` — spec-plan: same.
- `test_legal_plan_locked_code` — code: `SPEC-PLAN-APPROVED + plan-locked → CODE-IMPLEMENTATION`.
- `test_legal_plan_locked_spec_plan` — spec-plan: `SPEC-PLAN-APPROVED + plan-locked → DONE`.
- `test_legal_spec_rejected` — both modes: `SPEC-HUMAN-GATE + spec-rejected → SPEC-PLAN-DRAFTING`.
- `test_legal_plan_rejected` — both modes: `PLAN-HUMAN-GATE + plan-rejected → SPEC-PLAN-DRAFTING`.
- `test_illegal_plan_approved_from_spec_human_gate` — non-zero, no mutation.
- `test_illegal_plan_rejected_from_spec_human_gate` — cross-rejection; non-zero, no mutation. (Guards that the deleted old `plan-rejected` edge stays deleted.)
- `test_illegal_spec_approved_from_plan_human_gate` — non-zero, no mutation.
- `test_illegal_spec_rejected_from_plan_human_gate` — cross-rejection; non-zero, no mutation.
- `test_illegal_spec_approved_from_spec_plan_approved` — non-zero, no mutation.
- `test_illegal_plan_locked_from_human_gates` — parameterized; non-zero, no mutation.
- `test_illegal_plan_locked_from_code_states` — parameterized; non-zero, no mutation.
- `test_illegal_wave_events_from_spec_plan_approved` — parameterized.
- Refusal bytes: each illegal transition leaves `engine-state.json` byte-identical.

Human-state visibility tests:
- `test_spec_human_gate_pending_human_wait_true`
- `test_plan_human_gate_pending_human_wait_true`
- `test_spec_plan_approved_pending_human_wait_false`
- `test_spec_approved_fields` — `state=PLAN-HUMAN-GATE`, `last_event=spec-approved`.
- `test_plan_approved_fields` — `state=SPEC-PLAN-APPROVED`, `last_event=plan-approved`.

Status guard tests:
- `test_spec_approved_guard_accepts_approved`
- `test_spec_approved_guard_refuses_draft`
- `test_spec_approved_guard_refuses_implementing`
- `test_spec_approved_guard_refuses_malformed`
- `test_plan_approved_guard_accepts_approved` — reads plan.md, not spec.md.
- `test_plan_approved_guard_refuses_drafting`
- `test_plan_approved_guard_refuses_done`
- `test_plan_approved_guard_refuses_malformed`
- `test_plan_locked_guard_code_approved` — spec Status=Approved + schedule → succeeds.
- `test_plan_locked_guard_spec_plan_approved` — plan.md Status=Approved + plan approved → succeeds.
- `test_plan_locked_guard_refuses_wrong_spec_status`
- `test_plan_locked_guard_code_requires_schedule`
- `test_reviewers_clean_still_requires_shipped` — unchanged.

`check-spec-status.py` tests:
- `test_check_spec_status_expect_approved_spec_md`
- `test_check_spec_status_expect_approved_plan_md` — `--file plan.md`.
- `test_check_spec_status_expect_shipped_spec_md`
- `test_check_spec_status_no_flags_defaults_shipped_spec_md`

**Approach:**
- Anchor-test sweep first: grep `test-loop-engine.py` for all references to `SPEC-PLAN-HUMAN-GATE` and `plan-approved` (old guard); list every location before touching production code.
- In `loop-engine.py`:
  - Rename `"SPEC-PLAN-HUMAN-GATE"` → `"SPEC-HUMAN-GATE"` throughout (transition tables, `_HUMAN_WAIT_STATES`, any string literals).
  - Add `"PLAN-HUMAN-GATE"` to `_HUMAN_WAIT_STATES`.
  - Move `("SPEC-HUMAN-GATE", "spec-approved"): "PLAN-HUMAN-GATE"` into `_BOTH_TRANSITIONS`.
  - Move `("PLAN-HUMAN-GATE", "plan-approved"): "SPEC-PLAN-APPROVED"` into `_BOTH_TRANSITIONS`.
  - Add `("SPEC-PLAN-APPROVED", "plan-locked"): "CODE-IMPLEMENTATION"` to `_CODE_TRANSITIONS`.
  - Add `("SPEC-PLAN-APPROVED", "plan-locked"): "DONE"` to `_SPEC_PLAN_TRANSITIONS`.
  - Add `("SPEC-HUMAN-GATE", "spec-rejected"): "SPEC-PLAN-DRAFTING"` and `("PLAN-HUMAN-GATE", "plan-rejected"): "SPEC-PLAN-DRAFTING"` to `_BOTH_TRANSITIONS`.
  - **Delete** (do not rename) the old `("SPEC-PLAN-HUMAN-GATE", "plan-rejected")` entry — after the rename it would become `("SPEC-HUMAN-GATE", "plan-rejected")` which is an illegal cross-rejection and must not exist in the table.
  - Remove old `("SPEC-PLAN-HUMAN-GATE", "plan-approved")` entries.
  - Add `_guard_spec_approved` (calls `check-spec-status.py --expect Approved`); register as `("code", "spec-approved")` and `("spec-plan", "spec-approved")`.
  - Add `_guard_plan_approved` (calls `check-spec-status.py --expect Approved --file plan.md`); register as `("code", "plan-approved")` and `("spec-plan", "plan-approved")`.
  - Add `_guard_plan_locked_code` (spec Status=Approved + `plan check-current --require-schedule`); register as `("code", "plan-locked")`.
  - Add `_guard_plan_locked_spec_plan` (spec Status=Approved + `plan check-current`); register as `("spec-plan", "plan-locked")`.
  - Remove old `("code", "plan-approved")` and `("spec-plan", "plan-approved")` guard entries (schedule-requirement guards).
  - Update module-level docstring: "ten-state code-mode FSM" / "six-state spec-plan FSM"; remove any reference to deprecated event names.
- **Retarget existing tests and helpers** that encode the old FSM edges/guards:
  - `test_legal_plan_approved_spec_plan_mode` — update target from `DONE` to `SPEC-PLAN-APPROVED`; guard now checks plan.md Status.
  - `test_spec_plan_full_walk` — update `plan-approved` step: now exits `PLAN-HUMAN-GATE → SPEC-PLAN-APPROVED`; add `plan-locked` to reach `DONE`.
  - `test_guard_plan_check_current_fires_for_spec_plan_mode` — move guard to `plan-locked`, not `plan-approved`.
  - `test_guard_plan_check_current_require_schedule_fires_for_code_mode` — same.
  - `make_crash_window_run` helper — adopt new G-plan order: `spec-approved` → `plan-approved` → `approve-plan`/`schedule` → `plan-locked` → wave event.
  - `make_code_review_run` helper — same.
- In `check-spec-status.py` (currently reads `sys.argv[1]` directly with no argparse):
  - Introduce `argparse`: positional `spec_dir`, optional `--expect` (default `"Shipped"`), optional `--file` (default `"spec.md"`).
  - Read `<spec_dir>/<args.file>` instead of hardcoded `spec.md`.
  - Replace hard-coded `!= "Shipped"` with `token != args.expect`.
  - Preserve bare positional invocation (`check-spec-status.py <spec-dir>`) — argparse default values cover it.
  - Update docstring and stderr messages.

**Done when:** `python3 packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py` exits 0; all new stubs pass; the retargeted existing tests pass against the new FSM; no unexpected regressions; module docstring updated. (SKILL.md content-assertion tests at lines 1835–1910 cover `findings-remain`/`reviewers-clean` rows — see spec.md Assumptions; update those assertions if prose in those rows changes.)

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py`, `packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py`

---

### T3: Safe approval replay and cohort status visibility

**Depends on:** none

**Tests (TDD — write stubs before production change):**
- `test_approve_plan_first_write` — pending → records hashes; exit 0.
- `test_approve_plan_idempotent_no_op` — same run_id + same current hashes → exit 0; state bytes unchanged.
- `test_approve_plan_refuses_changed_spec` — spec.md modified after approval → non-zero; no mutation.
- `test_approve_plan_refuses_changed_plan` — plan.md modified after approval → non-zero; no mutation.
- `test_approve_plan_refuses_run_id_mismatch` — non-zero; no mutation.
- `test_approve_plan_state_preserved_on_refusal` — raw state bytes identical before/after refused call.
- `test_cohort_status_json_includes_plan_review_status_pending`
- `test_cohort_status_json_includes_plan_review_status_approved`
- `test_crash_after_plan_approved_before_approve_plan` — real subprocess; resume succeeds.
- `test_crash_after_approve_plan_before_schedule` — real subprocess; resume succeeds.
- `test_crash_after_schedule_before_plan_locked` — real subprocess; resume succeeds.

**Approach:**
- In `loop-cohort.py` `cmd_approve_plan`:
  - After run_id validation, read `plan_review_status`.
  - If `"approved"`: compute current hashes; if run_id matches AND hashes unchanged → no-op exit 0; else → stop with message.
  - Else (`"pending"`) → status-field guard first: read spec.md and plan.md Status via `_read_md_status`; if either is not `Approved`, stop non-zero (crash-window guard). Then existing write path.
- In `loop-cohort.py` `cmd_status`:
  - Add `"plan_review_status": state.get("plan_review_status", "pending")` to result dict.
- In `test-loop-cohort.py`: write all stubs before touching production code.

**Done when:** `python3 packs/core/.apm/skills/work-loop/scripts/test-loop-cohort.py` exits 0; all new test functions pass.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`, `packs/core/.apm/skills/work-loop/scripts/test-loop-cohort.py`

---

### T4: Resumption guidance, conventions, architecture, and evals

**Depends on:** T2, T3

**Tests (goal-based content assertions + TDD for legacy compat):**

SKILL.md assertions:
- Contains `SPEC-HUMAN-GATE` and `PLAN-HUMAN-GATE` in the G-plan / session-resumption section. Grep.
- Step 1 PLAN, item 12 contains `spec-approved` before `plan-approved`. Grep.
- Session-resumption table has rows: `spec-approved | PLAN-HUMAN-GATE`, `plan-approved | SPEC-PLAN-APPROVED`, `plan-locked | CODE-IMPLEMENTATION`, `plan-locked | DONE`. Grep.
- Contains `Mode: light (no risk trigger fired)` with routing by Status. Grep.
- Contains `resume at Step 2 EXECUTE` near `Status: Approved` in light-mode section (AC7.1).
- Contains `Status: Implementing` in the light-mode `Approved` branch (AC7.1 write-before-code clause).
- Contains `resume PLAN` near `Status: Draft` in light-mode section (AC7.2).
- Contains `Implementing` reconstruct-progress routing in light-mode section (AC7.3).
- Contains surface-rather-than-guess clause for ambiguous-mode case (AC7.5).
- Contains guard against using light-mode inference when `engine-state.json` is present (AC7.4).

Architecture and schema:
- `loop-infrastructure.md` contains `SPEC-HUMAN-GATE` and `PLAN-HUMAN-GATE`. Grep.
- `state-schema.md` contains `SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `spec-approved`, `plan-locked`. Grep.

RFC/ADR regression:
- `! grep -rq "Status.*Approved" packs/governance-extras/.apm/skills/new-rfc/ packs/governance-extras/.apm/skills/new-adr/` exits 0 (AC8.1/8.2 — verifies RFC/ADR templates; command errors gracefully if directories absent).
- `! grep -rq "RFC.*Approved\|ADR.*Approved\|set.*RFC.*Approved\|set.*ADR.*Approved" packs/core/.apm/skills/work-loop/ packs/core/.apm/skills/new-spec/` exits 0 (AC8.4 — verifies no work-loop or new-spec prose instructs setting an RFC/ADR to Approved).

Legacy compat tests (TDD, in `test-loop-engine.py`):
- `test_legacy_code_impl_plan_approved_readable` — `engine-state.json` with `state: CODE-IMPLEMENTATION, last_event: plan-approved` → `loop-engine status` exits 0.
- `test_legacy_done_plan_approved_readable` — same with `state: DONE`.

Light-mode routing assertions (AC7 — all grep):
- SKILL.md `Status: Approved` branch names `Status: Implementing` before code.
- SKILL.md `Status: Implementing` branch names reconstruct-progress.
- SKILL.md ambiguous-mode branch surfaces rather than guessing.

AC6 session-resumption manual QA (visual / manual QA — recorded in `notes/manual-qa.md`):
- Resume from `SPEC-HUMAN-GATE` with spec `Status: Draft`: verify waits; no auto-fire.
- Resume from `SPEC-HUMAN-GATE` with spec `Status: Approved`: verify `spec-approved` auto-fired; engine reaches `PLAN-HUMAN-GATE`.
- Resume from `SPEC-HUMAN-GATE` with spec `Status: Implementing`: verify surface-and-stop.
- Resume from `PLAN-HUMAN-GATE` with plan `Status: Drafting`: verify waits; no auto-fire.
- Resume from `PLAN-HUMAN-GATE` with plan `Status: Approved`: verify `plan-approved` auto-fired; engine reaches `SPEC-PLAN-APPROVED`.
- Resume from `PLAN-HUMAN-GATE` with plan `Status: Done`: verify surface-and-stop.
- Resume from `SPEC-PLAN-APPROVED`: verify cohort ops proceed; no second human signal.
- Resume from `CODE-IMPLEMENTATION + last_event: plan-locked` (new-sequence): EXECUTE proceeds normally.
- Resume from `DONE + last_event: plan-locked` (new-sequence spec-plan terminal): valid terminal.
- Resume from pre-upgrade `SPEC-PLAN-HUMAN-GATE` (AC6 migration): every event returns "illegal transition"; verify SKILL.md guidance directs `reset` + re-init.
- Resume from legacy `CODE-IMPLEMENTATION + last_event: plan-approved` (AC6.10): `loop-engine status` exits 0; `Status: Implementing` required before EXECUTE.
- Resume from legacy `DONE + last_event: plan-approved` (AC6.11): `loop-engine status` exits 0; valid terminal; no reset required.
For each scenario: record initial `engine-state.json` fixture, command sequence, observed stdout/exit code.

**Approach:**
- In `packs/core/.apm/skills/work-loop/SKILL.md`:
  - **Step 1 PLAN, item 12 G-plan sequence:** Replace both mode blocks with the new two-gate sequence (spec-approved → plan-approved → approve-plan → optional schedule → plan-locked). Add note: "`spec-approved` represents the scope decision. `plan-approved` represents the build-strategy decision. `plan-locked` seals the approved baseline and hands off to implementation."
  - **Active-state routing section** (currently around line 509 — contains `SPEC-PLAN-HUMAN-GATE` among active routing states): update the state name to `SPEC-HUMAN-GATE`; add `PLAN-HUMAN-GATE` alongside it.
  - **Session Resumption table:** Add rows: `spec-approved | PLAN-HUMAN-GATE | Proceed; plan approval still needed.`; `plan-approved | SPEC-PLAN-APPROVED | Proceed to cohort operations (approve-plan + optional schedule + plan-locked). Do not wait for another human signal.`; `plan-locked | CODE-IMPLEMENTATION | New-sequence code run. EXECUTE proceeds normally.`; `plan-locked | DONE | New-sequence spec-plan terminal.` Update legacy `plan-approved | CODE-IMPLEMENTATION` and `plan-approved | DONE` rows with "(legacy)" labels. Add upgrade-path row: `SPEC-PLAN-HUMAN-GATE | (any event) | Pre-upgrade parked run. Events return illegal-transition. Run reset + re-init on the new two-gate sequence; spec.md and plan.md are preserved.`
  - **Light-mode resumption subsection:** Add (or update) routing keyed on spec Status values.
- In `docs/architecture/loop-infrastructure.md`:
  - Update FSM text diagrams for both modes.
  - Update G-plan sequence code block.
  - Update `check-spec-status.py` description to note `--expect` and `--file` flags.
- In `packs/core/.apm/skills/work-loop/references/state-schema.md`:
  - Add `SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `SPEC-PLAN-APPROVED` to legal `state` values.
  - Document `spec-approved`, `plan-approved`, `plan-locked` events.
- Work-loop evals: update any fixture that references the old G-plan sequence order.
- Find `new-rfc` and `new-adr` skills; confirm templates use `Accepted`; record in notes.

**Done when:** All grep content assertions pass; `python3 test-loop-engine.py` passes legacy tests; `SKIP_SAST=1 make build-check` passes; `grep -rn SPEC-PLAN-HUMAN-GATE packs/core/.apm/skills/work-loop/ docs/architecture/loop-infrastructure.md` returns only the one intentional SKILL.md legacy-row entry and any intentional architecture-doc migration note — no other live references in operative source (excludes `.claude/`, `.agents/`, and `docs/specs/` which legitimately retain the old name for historical context).

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `docs/architecture/loop-infrastructure.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py` (legacy tests), `packs/core/.apm/skills/work-loop/evals/` (if fixture update needed)

---

### T5: Integration, legacy compatibility, projections, release, and gates

**Depends on:** T2, T3, T4

**Tests:**
- Integration paths (visual / manual QA via real subprocesses, AC9).
- Legacy compat: stubs and production code live in T4; verify they still pass here (`test_legacy_code_impl_plan_approved_readable`, `test_legacy_done_plan_approved_readable`).
- Version and projection checks (goal-based):
  - `grep "^version" packs/core/pack.toml` returns `2.0.0`.
  - `grep "version" packs/core/.claude-plugin/plugin.json` returns `2.0.0`.
  - `make build-self` exits 0.
  - `SKIP_SAST=1 make build-check` exits 0.
  - Changelog entry exists.
  - `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` on `docs/specs/loop-approved-spec-state/spec.md` exits 0.

**Approach:**
- Run `python3 test-loop-engine.py` and `python3 test-loop-cohort.py` — both must be clean.
- Create `notes/` directory; run both end-to-end flows via temp dirs using subprocess; record in `notes/manual-qa.md`.
- Bump `packs/core/pack.toml`: `version = "1.0.4"` → `version = "2.0.0"`.
- Bump `packs/core/.claude-plugin/plugin.json` version field to `2.0.0`.
- Add changelog entry.
- Run `make build-self` to regenerate projections.
- Run `SKIP_SAST=1 make build-check`.
- Run `lint-spec-status.py` on this spec.
- Set `Status: Shipped` in spec.md and `Status: Done` in this plan.

**Done when:** All tests pass; `make build-self` exits 0; `SKIP_SAST=1 make build-check` exits 0; spec lint clean; spec Status `Shipped`; plan Status `Done`.

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/CHANGELOG.md`, `.claude/` (generated), `.agents/` (generated), `docs/specs/loop-approved-spec-state/notes/manual-qa.md` (new)

## Rollout

Pure behavior change to loop infrastructure scripts and skill guidance. Backward compat:
- Legacy `engine-state.json` files with `CODE-IMPLEMENTATION + last_event: plan-approved` or `DONE + last_event: plan-approved` remain readable (documented compatibility rows; no script change needed).
- New runs must use the new two-gate sequence.
- No data migration; no rollback complexity.

## Risks

- **Rename of `SPEC-PLAN-HUMAN-GATE`:** touches test helpers, test assertions, and SKILL.md content-assertion tests (see spec.md Assumptions for line reference). The anchor-test sweep in T2 Approach must enumerate all locations before any production change.
- **G-plan sequence confusion on resume:** agents trained on the old order may resume mid-sequence incorrectly. Mitigated by explicit legacy-compatibility rows in the resumption table (T4) and crash-window tests (T3).
- **Version collision on rebase:** if another PR bumps core pack concurrently, use `--ours` on the version line.

## Changelog

- 2026-08-02: Redesigned to two human gates (SPEC-HUMAN-GATE + PLAN-HUMAN-GATE); renamed `approval-committed` → `plan-locked`; previous single-gate design superseded.
- 2026-08-01: Initial plan.
