# Session resumption

When `engine-state.json` is present, do **not** call `loop-engine init`. Instead:

1. `loop-engine status docs/specs/<feature> --json` → read `state`, `last_event`,
   `last_event_context`, `run_id`, `pending_human_wait`. Non-zero exit means
   the state file is missing or unreadable — **Surface to human**: describe the
   error, wait for explicit authorization before running the destructive reset
   pair (`loop-cohort reset` then `loop-engine reset`) and starting a new run.
2. `loop-cohort identity docs/specs/<feature> --expect-run-id <run_id>` →
   verify the pair. Surface and stop if non-zero.
3. `loop-engine status docs/specs/<feature> --json` → read `transition_sequence`.
   `loop-cohort status docs/specs/<feature> --json` → read `current_wave_index`,
   `schedule_waves`, `review_retry_count`, `implementation_retry_count`.
4. If `pending_human_wait` is true, inspect the persisted artifact status before deciding whether to wait:
   - **`SPEC-HUMAN-GATE`** — read `spec.md` Status: `Draft` → continue waiting; `Approved` → check `plan.md`'s Changelog carries the spec-approval entry, then fire `spec-approved` (crash-recovery: approver wrote Approved before the session ended). Status `Approved` with no entry → **Surface and stop**: the approver's handle cannot be inferred, and pinning an approval nobody is recorded as having given is the gap the entry exists to close; `Implementing` or `Shipped` → **Surface and stop** (spec advanced past approval without completing the plan gate — describe the state and wait for direction); `Archived` → **Surface and stop** (terminal — this spec will not proceed through the approval gates).
   - **`PLAN-HUMAN-GATE`** — read `plan.md` Status: `Drafting` → continue waiting; `Approved` → check its Changelog carries the plan-approval entry, then fire `plan-approved` (crash-recovery). Status `Approved` with no entry → **Surface and stop**, for the reason above; `Executing` or `Done` → **Surface and stop** (plan advanced past approval state).
   - **`CODE-HUMAN-GATE`** → wait for the human merge decision; no artifact to inspect.
5. Route by `last_event` to pick up where the session left off:

   | `last_event` | `state` | Action |
   |---|---|---|
   | `reviewers-clean` | `SPEC-HUMAN-GATE` | Apply step 4 spec-gate check first. If `Draft`: wait — spec approver writes `Status: Approved` in spec.md **and adds the spec-approval entry to plan.md's Changelog in the same edit**, then fire `spec-approved`. |
   | `spec-approved` | `PLAN-HUMAN-GATE` | Apply step 4 plan-gate check first. If `Drafting`: wait — plan approver writes `Status: Approved` in plan.md **and adds the plan-approval entry to its Changelog in the same edit**, then fire `plan-approved`. |
   | `plan-approved` | `SPEC-PLAN-APPROVED` | Both approved. Proceed to cohort operations: `approve-plan` + (code mode) `schedule` + `plan-locked`. No second human signal needed. |
   | `plan-locked` | `CODE-IMPLEMENTATION` | New-sequence code run. EXECUTE proceeds normally. Write `Status: Implementing` before code. |
   | `plan-locked` | `DONE` | Spec-plan terminal. If implementation is later requested: **Surface** — describe the destructive reset and wait for explicit confirmation, then `loop-cohort reset` + `loop-engine reset`, then re-init with `--mode code` (spec.md and plan.md are preserved). |
   | `plan-approved` | `CODE-IMPLEMENTATION` | **(legacy)** Pre-split run. Recognized as valid legacy code-mode run; ensure `Status: Implementing` before EXECUTE continues. |
   | `plan-approved` | `DONE` | **(legacy)** Pre-split spec-plan terminal. If implementation is later requested: **Surface** — describe the destructive reset and wait for explicit confirmation, then `loop-cohort reset` + `loop-engine reset`, then re-init with `--mode code` (spec.md and plan.md are preserved). |
   | `done` | `DONE` | **code-mode terminal** — loop ended after human approved merge; PR/merge only |
   | `wave-passed` | `CODE-IMPLEMENTATION` | Resume EXECUTE. If the session died before engine-state was written, re-issue the same `loop-engine transition ... wave-passed --wave-index <last_event_context.completed_wave_index>` command; the cohort history makes the wave advance a no-op when it already landed. Do not run `loop-cohort wave advance` separately. |
   | `gates-failed` | `CODE-IMPLEMENTATION` | Resume EXECUTE. If the session died before engine-state was written, re-issue the same `loop-engine transition ... gates-failed` command; the cohort history makes the attempt record a no-op when it already landed. Do not run `loop-cohort record-attempt` separately. |
   | `findings-remain` | `CODE-IMPLEMENTATION` | Resume implementation. If the session died before engine-state was written, re-issue the same `loop-engine transition ... findings-remain --fingerprint ...` payload; the transition id is also the review operation id, so the review round is not counted twice. Do not run `loop-cohort review record` separately; that old manual replay is what created stale fingerprint baseline and under-count risk. |
   | `blocker-applied` | `CODE-IMPLEMENTATION` | Resume implementation directly (Status: Shipped stays; do not rewrite) |
   | `reviewers-clean` | `CODE-HUMAN-GATE` | Wait for human signal. **Approved (merge confirmed):** fire `done`. **Changes requested:** run `loop-cohort wave reopen <spec-dir> --expect-run-id <run_id>` then fire `blocker-applied` → apply fix → run `loop-cohort check <spec-dir> --phase wave-exit` → fire `wave-complete` → re-run GATES → REVIEW (adversarial first). If the session died before engine-state was written, re-issue the same `loop-engine transition ... reviewers-clean` payload (`--all-skipped`, `--direct-clean-file`, `--structural-clean-file`, or `--report --adjudication`); the transition id is also the review operation id, so no human authorization gate is needed for a matching replay. Do not run `loop-cohort review record` separately. |
   | `wave-complete` | `CODE-VERIFICATION` | Re-run gates; fire `wave-passed` or `gates-clean`, or — for a failure — run `loop-cohort wave reopen <spec-dir> --expect-run-id <run_id>` then fire `gates-failed` |
   | `gates-clean` | `CODE-REVIEW` | Re-run reviewer fan-out and `review inspect` |
   | any — when `state.json.pending_transition` is set | any | A registered cohort effect may have been prepared while the engine was interrupted. Re-issue the same `loop-engine transition ...` command with the same payload. The engine reclassifies under the cohort lock, applies the effect at most once, clears the marker, and writes engine state last. Do not hand-write `state.json` or run the registered cohort verb separately. |

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
