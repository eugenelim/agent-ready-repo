# Spec: loop-approved-spec-state

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061
- **Brief:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `loop-engine` FSM splits the single `SPEC-PLAN-HUMAN-GATE` into two distinct human-wait states — `SPEC-HUMAN-GATE` (scope decision: does this spec define the right thing to build?) and `PLAN-HUMAN-GATE` (build decision: does this plan describe the right way to build it?) — reflecting that these are separate stakeholder decisions in any multi-person team. The spec approver writes `Status: Approved` in `spec.md` to exit `SPEC-HUMAN-GATE`; the plan approver writes `Status: Approved` in `plan.md` to exit `PLAN-HUMAN-GATE`. Both rejections return to `SPEC-PLAN-DRAFTING` because the spec and plan are often reviewed together and a plan rejection sometimes requires a spec revision.

After both approvals, a durable `SPEC-PLAN-APPROVED` state records that the full contract has been accepted before the mechanical cohort operations (`approve-plan`, `schedule`) run. The `plan-locked` event seals the approved baseline and hands off to implementation. A crash anywhere between `PLAN-HUMAN-GATE` and the start of implementation is recoverable without human re-approval.

`loop-cohort approve-plan` is idempotent across the approved state: same run ID + same hashes = no-op; hash changed = refuse. `check-spec-status.py` gains an `--expect` flag and a `--file` flag so the `plan-approved` guard can check `plan.md` independently of the `spec-approved` guard.

The spec-vocabulary meaning of `Approved` is explicit for both artifacts: in `spec.md` it means the scope is accepted; in `plan.md` it means the implementation strategy is accepted. `plan.md` gains `Approved` as a lifecycle status between `Drafting` and `Executing`. Light-mode resumption routes on `spec.md Status` when no `engine-state.json` exists.

## Boundaries

### Always do

- Keep `loop-engine` as the sole writer of `engine-state.json`; keep `loop-cohort` as the sole writer of `state.json`.
- Use `SPEC-HUMAN-GATE` for the scope-approval wait and `PLAN-HUMAN-GATE` for the build-approval wait; never merge them back into one state.
- Enforce the respective guard on `spec-approved` (reads `spec.md`) and `plan-approved` (reads `plan.md`) before writing any transition.
- Exit non-zero with no `engine-state.json` mutation on every guard failure.
- Keep both `SPEC-HUMAN-GATE` and `PLAN-HUMAN-GATE` in `_HUMAN_WAIT_STATES`.
- Leave `SPEC-PLAN-APPROVED` out of `_HUMAN_WAIT_STATES`.
- Use the shared canonical parser (`parse_status` from `lint-spec-status.py`) for every status read.

### Ask first

- Add or remove any FSM state or event beyond the seven named changes here (`SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `SPEC-PLAN-APPROVED`, `spec-approved`, `spec-rejected`, `plan-approved`, `plan-locked`).
- Add in-place replanning after the engine has entered `SPEC-PLAN-APPROVED`.
- Change the approved-baseline fields (`approved_spec_hash`, `approved_plan_hash`) outside of `approve-plan`.
- Change what `check-spec-status.py` defaults to when `--expect` or `--file` is omitted.

### Never do

- Let `loop-engine` write `state.json`.
- Silently rebaseline approved artifact hashes after `approve-plan` has recorded them.
- Remove `SPEC-HUMAN-GATE` or `PLAN-HUMAN-GATE` from `_HUMAN_WAIT_STATES`.
- Add `SPEC-PLAN-APPROVED` to `_HUMAN_WAIT_STATES`.
- Route `spec-rejected` or `plan-rejected` to any state other than `SPEC-PLAN-DRAFTING`.
- Call `loop-cohort schedule` in spec-plan mode or in spec-plan mode's `plan-locked` guard.
- Change the RFC or ADR status vocabularies; `Approved` remains spec/plan-only.

## Testing Strategy

All FSM transition enforcement, guard logic, idempotency rules, and status parsing use **TDD**: a failing test for each invariant is written before the production change, with separate red/green commits. Each AC in the FSM, guard, approval-replay, and legacy-compatibility groups maps to a test in `test-loop-engine.py` or `test-loop-cohort.py` (exercised via real subprocesses and fresh processes).

Session-resumption guidance in `SKILL.md` and architecture documentation (AC6 SKILL.md prose, AC7 light-mode routing) are prose obligations; these use **goal-based content assertions** (`grep`-verified phrases in the existing SKILL.md content tests).

CLI integration flows (code-mode and spec-plan-mode approval paths, AC9) and session-resumption scenarios (AC6 — `SPEC-HUMAN-GATE` with various spec Status values, `PLAN-HUMAN-GATE` with various plan Status values, `SPEC-PLAN-APPROVED` resume, new-sequence `plan-locked` resume for both modes, and legacy `plan-approved` runs) use **visual / manual QA**: end-to-end subprocess sequences are run, observed exit codes and engine/cohort states recorded in `notes/manual-qa.md`.

Projection correctness and version-bump consistency use **goal-based check**: `make build-check` passes clean; grep confirms version strings match across `pack.toml`, `plugin.json`, and the changelog.

## Acceptance Criteria

### AC1 — FSM transitions

- [x] `SPEC-PLAN-REVIEW + reviewers-clean → SPEC-HUMAN-GATE` in both modes (exit 0).
- [x] `SPEC-HUMAN-GATE + spec-approved → PLAN-HUMAN-GATE` in both modes (exit 0; guard: spec.md `Status: Approved`).
- [x] `PLAN-HUMAN-GATE + plan-approved → SPEC-PLAN-APPROVED` in both modes (exit 0; guard: plan.md `Status: Approved`).
- [x] `SPEC-PLAN-APPROVED + plan-locked → CODE-IMPLEMENTATION` in code mode.
- [x] `SPEC-PLAN-APPROVED + plan-locked → DONE` in spec-plan mode.
- [x] `SPEC-HUMAN-GATE + spec-rejected → SPEC-PLAN-DRAFTING` in both modes (exit 0; no guard required).
- [x] `PLAN-HUMAN-GATE + plan-rejected → SPEC-PLAN-DRAFTING` in both modes (exit 0; no guard required).
- [x] `SPEC-HUMAN-GATE + spec-approved` always targets `PLAN-HUMAN-GATE`; it never skips to `SPEC-PLAN-APPROVED` or `CODE-IMPLEMENTATION` in any mode.

### AC2 — Illegal transitions

- [x] `SPEC-HUMAN-GATE + plan-approved` is illegal in both modes (non-zero, no mutation).
- [x] `SPEC-HUMAN-GATE + plan-rejected` is illegal in both modes (non-zero, no mutation).
- [x] `PLAN-HUMAN-GATE + spec-approved` is illegal in both modes (non-zero, no mutation).
- [x] `PLAN-HUMAN-GATE + spec-rejected` is illegal in both modes (non-zero, no mutation).
- [x] `SPEC-PLAN-APPROVED + spec-approved`, `+ plan-approved`, `+ spec-rejected`, `+ plan-rejected` are each illegal (non-zero, no mutation).
- [x] `SPEC-PLAN-APPROVED + wave-complete`, `wave-passed`, `gates-clean`, `gates-failed`, `findings-remain`, `reviewers-clean` are each illegal (non-zero, no mutation).
- [x] `plan-locked` from any `CODE-*` state is illegal (non-zero, no mutation).
- [x] `plan-locked` from `SPEC-HUMAN-GATE` or `PLAN-HUMAN-GATE` is illegal (non-zero, no mutation).
- [x] Every refused transition leaves `engine-state.json` byte-identical to its pre-transition content.

### AC3 — Human-state visibility

- [x] `SPEC-HUMAN-GATE` reports `pending_human_wait: true`; `last_event: reviewers-clean`.
- [x] After `spec-approved`, engine reports `state: PLAN-HUMAN-GATE`, `last_event: spec-approved`, `pending_human_wait: true`.
- [x] After `plan-approved`, engine reports `state: SPEC-PLAN-APPROVED`, `last_event: plan-approved`, `pending_human_wait: false`.

### AC4 — Status guards

- [x] `spec-approved` guard: accepts spec.md `Status: Approved`; refuses `Draft`, `Implementing`, `Shipped`, malformed, or missing `**Status:**` line (non-zero, no mutation).
- [x] `plan-approved` guard: accepts plan.md `Status: Approved`; refuses `Drafting`, `Executing`, `Done`, malformed, or missing `**Status:**` line (non-zero, no mutation).
- [x] `plan-locked` guard (code mode): requires spec.md `Status: Approved` + `plan check-current --require-schedule` to pass.
- [x] `plan-locked` guard (spec-plan mode): requires spec.md `Status: Approved` + `plan check-current` (no `--require-schedule`).
- [x] `reviewers-clean` guard (`CODE-REVIEW → CODE-HUMAN-GATE`): continues requiring spec.md `Status: Shipped` — unchanged.
- [x] `check-spec-status.py <spec-dir> --expect Approved` exits 0 when spec.md Status is `Approved`; non-zero otherwise.
- [x] `check-spec-status.py <spec-dir> --expect Approved --file plan.md` exits 0 when plan.md Status is `Approved`; non-zero otherwise.
- [x] `check-spec-status.py <spec-dir>` (no flags) defaults to `--expect Shipped --file spec.md` — backward-compatible.

### AC5 — Safe approval replay

- [x] `loop-cohort approve-plan` when `plan_review_status == pending`: records hashes, marks approved, exits 0.
- [x] `loop-cohort approve-plan` when already approved with the same run ID and unchanged current hashes: exits 0 as an idempotent no-op; state bytes not rewritten.
- [x] `loop-cohort approve-plan` when already approved but `spec.md` has changed: exits non-zero without mutation.
- [x] `loop-cohort approve-plan` when already approved but `plan.md` has changed: exits non-zero without mutation.
- [x] `loop-cohort approve-plan` with a mismatched run ID: exits non-zero without mutation.
- [x] `loop-cohort status <spec-dir> --json` output includes `plan_review_status`.

### AC6 — Full-mode session resumption

- [x] Resuming `SPEC-HUMAN-GATE` with spec.md `Status: Draft`: continue waiting; do not auto-fire `spec-approved`.
- [x] Resuming `SPEC-HUMAN-GATE` with spec.md `Status: Approved`: fire `spec-approved` automatically (crash-recovery for the window between human writing `Approved` and the engine event).
- [x] Resuming `SPEC-HUMAN-GATE` with incompatible spec Status (`Implementing`, `Shipped`): surface and stop.
- [x] Resuming `PLAN-HUMAN-GATE` with plan.md `Status: Drafting`: continue waiting; do not auto-fire `plan-approved`.
- [x] Resuming `PLAN-HUMAN-GATE` with plan.md `Status: Approved`: fire `plan-approved` automatically.
- [x] Resuming `PLAN-HUMAN-GATE` with incompatible plan Status (`Executing`, `Done`): surface and stop.
- [x] Resuming `SPEC-PLAN-APPROVED`: proceed to cohort operations without requiring another human signal.
- [x] A run parked at `state: SPEC-PLAN-HUMAN-GATE` (pre-upgrade engine-state.json): every event returns "illegal transition" because the state no longer exists in the table; the resumption guidance directs `reset` + re-init on the new two-gate sequence, with no data loss (spec.md and plan.md are preserved).
- [x] Resuming `CODE-IMPLEMENTATION` with `last_event: plan-locked` (new-sequence code run): EXECUTE proceeds normally.
- [x] Resuming `DONE` with `last_event: plan-locked` (new-sequence spec-plan terminal): recognized as valid terminal state.
- [x] Resuming `CODE-IMPLEMENTATION` with `last_event: plan-approved` (legacy): recognized as valid legacy code-mode run; `Status: Implementing` ensured before EXECUTE continues.
- [x] Resuming `DONE` with `last_event: plan-approved` (legacy spec-plan terminal): recognized as valid legacy terminal state; no destructive reset required.

### AC7 — Light-mode resumption

- [x] A spec with `Mode: light (no risk trigger fired)` and `Status: Approved` resumes at Step 2 EXECUTE and writes `Status: Implementing` before any code change.
- [x] `Mode: light` + `Status: Draft` resumes PLAN.
- [x] `Mode: light` + `Status: Implementing` reconstructs progress from the task list and working tree.
- [x] Full-mode state files (`engine-state.json`) present → full-mode protocol applies even if spec Status is `Approved`; light-mode inference is NOT used.
- [x] Ambiguous mode (no `Mode: light` line, no `engine-state.json`) → skill surfaces rather than guessing.

### AC8 — RFC/ADR regression

- [x] RFC template (in the skill that authors it) uses `Accepted`, not `Approved`, as a lifecycle value.
- [x] ADR template uses `Accepted`, not `Approved`.
- [x] Spec template and `lint-spec-status.py` vocabulary include `Approved`.
- [x] No `work-loop` or `new-spec` prose instructs setting an RFC or ADR to `Approved`.

### AC9 — Integration paths

- [x] Code-mode end-to-end: `reviewers-clean → SPEC-HUMAN-GATE → spec-approved → PLAN-HUMAN-GATE → plan-approved → SPEC-PLAN-APPROVED → approve-plan → schedule → plan-locked → CODE-IMPLEMENTATION → Status: Implementing` — all steps exit 0; observed states recorded in `notes/manual-qa.md`.
- [x] Spec-plan-mode end-to-end: `reviewers-clean → SPEC-HUMAN-GATE → spec-approved → PLAN-HUMAN-GATE → plan-approved → SPEC-PLAN-APPROVED → approve-plan → plan-locked → DONE` — all steps exit 0; spec.md `Status: Approved` and plan.md `Status: Approved` remain; recorded.

### AC10 — Documentation and projections

- [x] `loop-engine.py` module-level docstring names the ten-state code-mode FSM and six-state spec-plan FSM, and does not reference deprecated events or state names.
- [x] `docs/architecture/loop-infrastructure.md` FSM diagrams reflect both new states for both modes (ten-state code-mode, six-state spec-plan mode).
- [x] `SKILL.md` Step 1 PLAN, item 12 (G-plan sequence) matches the new two-gate approval flow and `plan-locked` event.
- [x] `SKILL.md` session-resumption table includes `SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, and `SPEC-PLAN-APPROVED` routing, plus `plan-locked | CODE-IMPLEMENTATION` and `plan-locked | DONE` rows for new-sequence runs.
- [x] `SKILL.md` contains an explicit light-mode resumption protocol keyed on spec Status values.
- [x] `references/state-schema.md` documents `SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `SPEC-PLAN-APPROVED`, `spec-approved`, `plan-approved`, and `plan-locked`.
- [x] `docs/CONVENTIONS.md` and `packs/core/seeds/docs/CONVENTIONS.md` define `Approved` for both `spec.md` and `plan.md` lifecycles, and the plan-vocabulary parenthetical reads `Drafting | Approved | Executing | Done` in both files.
- [x] `packs/core/.apm/skills/new-spec/assets/plan.md` status comment reads `Drafting | Approved | Executing | Done`.
- [x] `.claude/` and `.agents/` projections regenerated (`make build-self` passes).
- [x] Core pack version incremented (major bump — `SPEC-PLAN-HUMAN-GATE` removal is a breaking FSM interface change; `pack.toml` + `plugin.json` consistent at 2.0.0).
- [x] Product changelog updated.

## Assumptions

- Technical: `loop-engine.py` tables are `_BOTH_TRANSITIONS`, `_CODE_TRANSITIONS`, `_SPEC_PLAN_TRANSITIONS`; `SPEC-PLAN-HUMAN-GATE` is renamed to `SPEC-HUMAN-GATE` and `PLAN-HUMAN-GATE` added as a new state. (source: `packs/core/.apm/skills/work-loop/scripts/loop-engine.py:50–78`)
- Technical: `_HUMAN_WAIT_STATES` currently `{"SPEC-PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"}`; after this change `{"SPEC-HUMAN-GATE", "PLAN-HUMAN-GATE", "CODE-HUMAN-GATE"}`. (source: `loop-engine.py:81`)
- Technical: `check-spec-status.py` currently hardcodes `spec.md` and `!= "Shipped"` with no `--expect` or `--file` flag. (source: `check-spec-status.py:78`)
- Technical: `loop-cohort approve-plan` writes unconditionally; no idempotency. (source: `loop-cohort.py:517–526`)
- Technical: `loop-cohort status --json` does not expose `plan_review_status`. (source: `loop-cohort.py:454–473`)
- Technical: `test-loop-engine.py` helpers `make_crash_window_run` and `make_code_review_run` encode the old G-plan order and must be updated. (source: `test-loop-engine.py:1354,1387`)
- Technical: Core pack is `version = "1.0.4"`. (source: `packs/core/pack.toml`)
- Process: ADR and RFC lifecycles use `Accepted`; spec lifecycle uses `Approved`; plan lifecycle gains `Approved`. (source: `docs/CONVENTIONS.md:163,199`)
- Process: Adding a new FSM state is an "Ask first" boundary per Phase 1 spec; this follow-on spec is the authorized vehicle. (source: `docs/specs/loop-infrastructure-phase-1/spec.md § Boundaries`)
