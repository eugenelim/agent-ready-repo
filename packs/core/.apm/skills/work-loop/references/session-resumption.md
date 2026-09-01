# Session resumption

When `engine-state.json` is present, do **not** call `loop-engine init`. Instead:

1. `loop-engine status docs/specs/<feature> --json` → read `state`, `last_event`,
   `last_event_context`, `run_id`, `pending_human_wait`. Non-zero exit means
   the state file is missing or unreadable — **Surface to human**: describe the
   error, wait for explicit authorization before running the destructive reset
   pair (`loop-engine reset` then `loop-cohort reset`) and starting a new run.
2. `loop-cohort identity docs/specs/<feature> --expect-run-id <run_id>` →
   verify the pair. Surface and stop if non-zero.
3. `loop-engine status docs/specs/<feature> --json` → read `transition_sequence`.
   `loop-cohort status docs/specs/<feature> --json` → read `current_wave_index`,
   `schedule_waves`, `review_retry_count`, `implementation_retry_count`.
4. If `pending_human_wait` is true, inspect the persisted artifact status before deciding whether to wait:
   - **`SPEC-HUMAN-GATE`** — read `spec.md` Status: `Draft` → continue waiting; `Approved` → fire `spec-approved` immediately (crash-recovery: approver wrote Approved before the session ended); `Implementing` or `Shipped` → **Surface and stop** (spec advanced past approval without completing the plan gate — describe the state and wait for direction); `Archived` → **Surface and stop** (terminal — this spec will not proceed through the approval gates).
   - **`PLAN-HUMAN-GATE`** — read `plan.md` Status: `Drafting` → continue waiting; `Approved` → fire `plan-approved` immediately (crash-recovery); `Executing` or `Done` → **Surface and stop** (plan advanced past approval state).
   - **`CODE-HUMAN-GATE`** → wait for the human merge decision; no artifact to inspect.
5. Route by `last_event` to pick up where the session left off:

   | `last_event` | `state` | Action |
   |---|---|---|
   | `reviewers-clean` | `SPEC-HUMAN-GATE` | Apply step 4 spec-gate check first. If `Draft`: wait — spec approver writes `Status: Approved` in spec.md, then fire `spec-approved`. |
   | `spec-approved` | `PLAN-HUMAN-GATE` | Apply step 4 plan-gate check first. If `Drafting`: wait — plan approver writes `Status: Approved` in plan.md, then fire `plan-approved`. |
   | `plan-approved` | `SPEC-PLAN-APPROVED` | Both approved. Proceed to cohort operations: `approve-plan` + (code mode) `schedule` + `plan-locked`. No second human signal needed. |
   | `plan-locked` | `CODE-IMPLEMENTATION` | New-sequence code run. EXECUTE proceeds normally. Write `Status: Implementing` before code. |
   | `plan-locked` | `DONE` | Spec-plan terminal. If implementation is later requested: **Surface** — describe the destructive reset and wait for explicit confirmation, then `loop-cohort reset` + `loop-engine reset`, then re-init with `--mode code` (spec.md and plan.md are preserved). |
   | `plan-approved` | `CODE-IMPLEMENTATION` | **(legacy)** Pre-split run. Recognized as valid legacy code-mode run; ensure `Status: Implementing` before EXECUTE continues. |
   | `plan-approved` | `DONE` | **(legacy)** Pre-split spec-plan terminal. If implementation is later requested: **Surface** — describe the destructive reset and wait for explicit confirmation, then `loop-cohort reset` + `loop-engine reset`, then re-init with `--mode code` (spec.md and plan.md are preserved). |
   | `done` | `DONE` | **code-mode terminal** — loop ended after human approved merge; PR/merge only |
   | `wave-passed` | `CODE-IMPLEMENTATION` | Re-issue `python '<skill-dir>/scripts/loop-cohort.py' wave advance docs/specs/<feature> --from-index <last_event_context.completed_wave_index> --expect-run-id <run_id>` (idempotent); resume EXECUTE |
   | `gates-failed` | `CODE-IMPLEMENTATION` | Re-issue `python '<skill-dir>/scripts/loop-cohort.py' record-attempt docs/specs/<feature> --phase implement --cycle-id <run_id>:<transition_sequence> --expect-run-id <run_id>` where `transition_sequence` was read from `loop-engine status` in step 3 (idempotent); resume EXECUTE |
   | `findings-remain` | `CODE-IMPLEMENTATION` | Read `last_review_record_operation_id` from `state.json` and compare it with `<run_id>:<transition_sequence>` from step 3. Equal → the round is recorded and re-issuing the identical payload under that id is a no-op; continue. Absent or different → the round was not recorded under that id, so a re-issue writes a new round and increments both counters; stale fingerprint baseline and possible under-count; do NOT auto-reissue. A round recorded before this field existed also reads as absent. **Surface to human**. |
   | `blocker-applied` | `CODE-IMPLEMENTATION` | Resume implementation directly (Status: Shipped stays; do not rewrite) |
   | `reviewers-clean` | `CODE-HUMAN-GATE` | Wait for human signal. **Approved (merge confirmed):** fire `done`. **Changes requested:** surface `review record --direct-clean-file/--structural-clean-file/--report` audit risk first — without a matching `--operation-id` both are non-idempotent, and a replay may double-increment `review_round_count` and overwrite one level of fingerprint audit history; explicit human authorization required before any such replay; if authorized, read `last_review_clean_source` from `state.json` and replay that form — `"direct-clean"` → `--direct-clean-file <raw-path>`, `"structural-clean"` → `--structural-clean-file <raw-path>`, `"report"` → `--report <adjudication-path> --adjudication` — passing `--operation-id <run_id>:<transition_sequence>`. That makes the replay a no-op only when `last_review_record_operation_id` already equals that id and the artifact the form names is still on disk; a clean round recorded flaglessly, or one whose gitignored artifact has been evicted, still refuses or still counts a round, so the authorization above is not optional; `null` means no clean round was recorded, so Surface rather than guess; then fire `blocker-applied` → apply fix → fire `wave-complete` → re-run GATES → REVIEW (adversarial first) |
   | `wave-complete` | `CODE-VERIFICATION` | Re-run gates; fire `wave-passed` or `gates-clean` or `gates-failed` |
   | `gates-clean` | `CODE-REVIEW` | Re-run reviewer fan-out and `review inspect` |

6. States in `{SPEC-PLAN-DRAFTING, SPEC-PLAN-REVIEW, SPEC-HUMAN-GATE, PLAN-HUMAN-GATE}` →
   resume spec/plan work per skill prose; no pending cohort mutation in Phase 1. A run
   parked at `state: SPEC-PLAN-HUMAN-GATE` (pre-upgrade engine-state.json) returns
   "illegal transition" on every event — the state no longer exists in the FSM table.
   **Surface** this to the human: describe the legacy state, explain that the following
   reset will delete `state.json` and `engine-state.json` (retry/review progress lost;
   spec.md and plan.md are preserved), and wait for explicit confirmation before
   proceeding. Then: `loop-cohort reset docs/specs/<feature>` → `loop-engine reset
   docs/specs/<feature>` → re-init on the new two-gate sequence.

## Legacy light mode

Legacy light-mode resumption applies only to a persisted spec with no
`engine-state.json` that carries `Mode: light (no risk trigger fired)`. These
existing specs remain readable, valid, and resumable; direct-light itself does
not create or resume one:

| spec `Status` | Resume at |
|---|---|
| `Draft` | resume PLAN. |
| `Approved` | Resume at Step 2 EXECUTE. Write `Status: Implementing` before any code change. |
| `Implementing` | Reconstruct progress from the task list and working tree. |
| `Shipped` / `Archived` | Terminal. No further work needed. |

**If `engine-state.json` is present**: use the full-mode protocol even if spec Status is `Approved`. Never infer light mode from spec Status alone when engine state files exist.

**Ambiguous** (no `Mode: light` line AND no `engine-state.json`): surface to the human rather than guessing.
