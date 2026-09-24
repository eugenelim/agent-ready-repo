# full-mode-engine — the `loop-engine` / `loop-cohort` state machine

> **Loaded when:** a full-mode run needs to fire a transition or record cohort
> state. `SKILL.md` keeps the loop's shape — PLAN, EXECUTE, GATES, REVIEW,
> DECIDE — and the decisions each step owns. The commands that move the
> persisted state machine live here.
> **Why progressive disclosure:** light mode never runs this machine, and a
> full-mode run needs each sequence only at the step that fires it. Keeping
> the commands inline made the state machine read as the loop's conceptual
> model rather than as one mode's implementation.

Never edit `state.json` by hand. Field-level detail,
mutation rules, and troubleshooting: [`state-schema.md`](state-schema.md).
Rejected spec and plan gates use the exact reset commands in
[`delivery-contract-lifecycle.md`](delivery-contract-lifecycle.md).

## PLAN — init pair, or resume

If `engine-state.json` already exists in the spec dir, this is a **resume** — follow the [Session Resumption protocol](session-resumption.md) instead of running init. For a **new run** (no engine-state.json), if `state.json` is present (orphaned cohort from a prior partial run) — **Surface to human**: run `loop-cohort status docs/specs/<feature>` to show the orphaned state, describe it, and wait for explicit authorization before running the destructive reset pair (`loop-cohort reset` then `loop-engine reset`). Once authorized, run the **init pair** (engine then cohort, in order), then fire `spec-ready`:
```
# Use --mode spec-plan for spec/plan-only work; --mode code for implementation work.
python '<skill-dir>/scripts/loop-engine.py' init docs/specs/<feature> --mode <mode> --json
# ↑ Parse run_id from the JSON output; carry it for all --expect-run-id arguments.
python '<skill-dir>/scripts/loop-cohort.py' init docs/specs/<feature> --run-id <run_id>
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-ready
```
Then run `python '<skill-dir>/scripts/loop-cohort.py' plan check-current docs/specs/<feature>`.
Exit 1 (`plan_review_status: pending`) is the expected signal to run
pre-EXECUTE review — it does not trigger termination.


## PLAN — pre-EXECUTE review transitions

These fire around the reviewer passes that `SKILL.md` Step 1 item 11 governs.
That item owns which reviewers are mandatory, how a report is classified, and
when an indeterminate stops; only the transitions are here.

```
# On findings: revise spec/plan
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> findings-remain
# ... revise ...
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-ready
```
After all fired reviewers produce direct or adjudicated Clean results, fire the spec-review transition:
```
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> reviewers-clean
```


## PLAN — the G-plan sequence and its two human approvals

The **G-plan sequence** — two human approvals required, run in order. Branch by the mode used at init:

**`code` mode** (implementation work):
```bash
# 1. Spec approver writes Status: Approved in spec.md, and adds the
#    spec-approval entry to plan.md's Changelog (form: the plan
#    template's Changelog note).
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-approved
# → PLAN-HUMAN-GATE; pending_human_wait: true

# 2. Plan approver writes Status: Approved in plan.md, and adds the
#    plan-approval entry to its Changelog in the SAME edit — step 3
#    pins plan content and splices out only the status token, so an
#    entry written after it invalidates the baseline hash.
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> plan-approved
# → SPEC-PLAN-APPROVED; pending_human_wait: false

# 3. Cohort records the approved baseline — call immediately after plan-approved; do not modify either file between steps.
#    On crash-resume from SPEC-PLAN-APPROVED, call approve-plan first: it refuses a non-Approved status (status-field guard) and is a no-op when statuses and hashes are unchanged.
python '<skill-dir>/scripts/loop-cohort.py' approve-plan docs/specs/<feature> \
    --expect-run-id <run_id>

# 4. Schedule waves:
python '<skill-dir>/scripts/loop-cohort.py' schedule docs/specs/<feature> \
    --expect-run-id <run_id>

# 5. Seal and hand off:
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> plan-locked
# → CODE-IMPLEMENTATION; write Status: Implementing before any code
```

**`spec-plan` mode** (spec/plan-only work — no implementation tasks):
```bash
# 1. Spec approver writes Status: Approved in spec.md, and adds the
#    spec-approval entry to plan.md's Changelog (form: the plan
#    template's Changelog note).
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> spec-approved
# → PLAN-HUMAN-GATE

# 2. Plan approver writes Status: Approved in plan.md, and adds the
#    plan-approval entry to its Changelog in the SAME edit — step 3
#    pins plan content and splices out only the status token, so an
#    entry written after it invalidates the baseline hash.
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> plan-approved
# → SPEC-PLAN-APPROVED

# 3. Cohort records baseline — call immediately after plan-approved; do not modify either file between steps. On crash-resume, call approve-plan first (refuses if changed, no-op if not).
python '<skill-dir>/scripts/loop-cohort.py' approve-plan docs/specs/<feature> \
    --expect-run-id <run_id>

# 4. Seal (no schedule in spec-plan mode):
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> plan-locked
# → DONE; retain Status: Approved in both files
```

`spec-approved` = the scope decision. `plan-approved` = the build-strategy decision. `plan-locked` = baseline sealed, ready for implementation.


## GATES — wave routing

**Full mode — after gates pass (wave routing):**
```
# More waves remain — fire wave-passed, advance cohort wave pointer, return to EXECUTE:
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> wave-passed \
    --wave-index <n>   # guard: wave check --expect more
# Accounting precondition: the advancing branch refuses a wave whose tasks are not accounted for
# — every task in wave <n> needs a dispatch-receipt record, receipt or decline.
# Re-issuing an advance that already landed stays a no-op.
python '<skill-dir>/scripts/loop-cohort.py' wave advance docs/specs/<feature> \
    --from-index <n> --expect-run-id <run_id>

# Final wave — fire gates-clean, proceed to REVIEW:
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> gates-clean
                   # guard: wave check --expect last
```

**Full mode — if gates fail:**
`wave reopen` supersedes the current wave's dispatch records so the repair round starts without a stale live record; `gates-failed` refuses if a live record exists.
```
python '<skill-dir>/scripts/loop-cohort.py' wave reopen docs/specs/<feature> \
    --expect-run-id <run_id>
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> gates-failed
python '<skill-dir>/scripts/loop-cohort.py' record-attempt docs/specs/<feature> \
    --phase implement --cycle-id <run_id>:<seq> --expect-run-id <run_id>
```
Fix the failure and return to EXECUTE.


## REVIEW and the human gate

`SKILL.md` Step 4 owns which reviewers are warranted and what counts as a
clean result. This section owns the order in which the transition and the
recording fire once that conclusion is reached.

**When every warranted mandatory reviewer has completed with no unresolved Blocker or Concern — clean, or carrying only deferred Nits recorded with their citations — and every non-mandatory reviewer is in that state or a named skip** — for a spec-backed run, normally write `Status: Shipped` in `spec.md`, then fire
`reviewers-clean` and, if at least one reviewer produced a clean report, record
it (transition first; record is non-idempotent — recording first then crashing
leaves CODE-REVIEW with the audit count already moved; the default guard
requires Status: Shipped). A direct-light run has no spec status to write and
fires no engine or cohort transition:
```
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> reviewers-clean
# The transition must succeed before recording. It prints `(seq=N)`; pass that N
# as the operation id's sequence so a resuming session recomputes the same id.
# If at least one reviewer produced the exact direct-clean sentinel, persist
# that reviewer's complete return to the ignored session path first, then name
# the file; the command reads its bytes and compares them to the sentinel, so a
# recorded clean never rests on the controller's own account of what was said:
python '<skill-dir>/scripts/loop-cohort.py' review record docs/specs/<feature> \
    --direct-clean-file .context/reviews/<run-id>/<n>-post-gates-<role>-raw.md \
    --expect-run-id <run_id> --operation-id <run_id>:<seq>
# If it is clean but not byte-exact (a trailing newline, say). Refuses a report
# carrying a `## Not checked` footer: that always takes the adjudicator path.
# This form re-classifies the persisted artifact itself, and takes the same
# operation id so a replay is a no-op rather than a second round:
python '<skill-dir>/scripts/loop-cohort.py' review record docs/specs/<feature> \
    --structural-clean-file .context/reviews/<run-id>/<n>-post-gates-<role>-raw.md \
    --expect-run-id <run_id> --operation-id <run_id>:<seq>
# Otherwise, if clean exists only through adjudication:
python '<skill-dir>/scripts/loop-cohort.py' review record docs/specs/<feature> \
    --report <adjudication-report-path> --adjudication \
    --expect-run-id <run_id> --operation-id <run_id>:<seq>
# Only if every warranted reviewer was non-mandatory and a named skip:
python '<skill-dir>/scripts/loop-cohort.py' review record docs/specs/<feature> \
    --all-skipped --expect-run-id <run_id> --operation-id <run_id>:<seq>
```
A mandatory named skip blocks before `Status: Shipped`, `reviewers-clean`, or the `--all-skipped` path; do not let verdict emission discover that failure only after the state machine has advanced.
For an intermediate review unit whose required work is not yet complete,
leave `spec.md` at `Status: Implementing` and declare that boundary explicitly:
```
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> reviewers-clean \
    --intent-incomplete
```
This opt-in accepts `Implementing` only; it does not disable the status guard or
permit another status. The next required unit still returns through
`blocker-applied` and receives GATES, REVIEW, and a human gate of its own. This
intermediate human gate is not a finish: do not mark the spec `Shipped`, run
`done` (which refuses until the spec is `Shipped`), or apply the Finish
checklist's intent-completion item. After the human
gate, fire `blocker-applied` to begin the next unit.
Engine is now in `CODE-HUMAN-GATE`. For a final unit, **before waiting: complete
the [Finish checklist](../SKILL.md#finish-checklist) and open the PR.** Then wait for human
response:
- **Approved (merge confirmed):** fire `done`.
  ```
  python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> done
  ```
- **Changes requested:** fire `blocker-applied`, apply the fix, then fire `wave-complete` to reach `CODE-VERIFICATION` before GATES, then re-enter REVIEW (adversarial first).
  ```
  python '<skill-dir>/scripts/loop-cohort.py' wave reopen docs/specs/<feature> \
      --expect-run-id <run_id>
  python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> blocker-applied
  # Apply the fix, then fire wave-complete (gates-clean/gates-failed are legal
  # only from CODE-VERIFICATION, not CODE-IMPLEMENTATION). Run the wave-exit
  # check first: it prints the absent-container notice the transition cannot.
  python '<skill-dir>/scripts/loop-cohort.py' check docs/specs/<feature> --phase wave-exit
  python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> wave-complete
  # Re-run GATES → fire gates-clean or gates-failed → re-enter REVIEW.
  ```
- **Further required review unit:** when an included discovery is required
  and needs its own independently reviewed unit, use the same
  `blocker-applied` return edge, then apply that unit, run `loop-cohort check
  <spec-dir> --phase wave-exit`, fire `wave-complete`, and run GATES, REVIEW,
  and the human gate again. A discovery that is not required opens no unit.
  A separate review unit does not defer or complete the required work.

For direct-light, do not fire engine or cohort transitions: once the rounds
rule in [`light-mode.md`](light-mode.md) is satisfied,
complete the Finish checklist and produce the five-field final handoff.

### Specialist findings

If a specialist adjudication sustains findings, first exit `CODE-REVIEW` via `findings-remain` and record only their fingerprints (same as the adversarial-findings path above), then apply the fixes, fire `wave-complete` to reach `CODE-VERIFICATION`, re-run GATES, then re-enter REVIEW.
`wave reopen` supersedes the current wave's dispatch records before `findings-remain`; the transition refuses if a live record exists.
```
# Never record when the transition is refused: it carries the retry-cap guard,
# and `review record --fingerprint` carries its own cap too. The caps are belt
# and braces, but the rail is not only about the cap -- record after ANY refused
# transition and the cohort ends a round ahead of the engine, a desync only a
# forbidden `state.json` hand-edit reconciles.
# The transition prints `(seq=N)`. Record only if it succeeded, and pass that
# N: a resuming session reads the same value from `loop-engine status`, so the
# operation id it recomputes matches and the round is not written twice.
python '<skill-dir>/scripts/loop-cohort.py' wave reopen docs/specs/<feature> \
    --expect-run-id <run_id>
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> findings-remain
python '<skill-dir>/scripts/loop-cohort.py' review record docs/specs/<feature> \
    --fingerprint <fp1> --fingerprint <fp2> ... --expect-run-id <run_id> \
    --operation-id <run_id>:<seq>
# Apply the specialist's fixes, then fire wave-complete (required to reach
# CODE-VERIFICATION before gates-clean/gates-failed). Run the wave-exit check
# first: it prints the absent-container notice the transition cannot.
python '<skill-dir>/scripts/loop-cohort.py' check docs/specs/<feature> --phase wave-exit
python '<skill-dir>/scripts/loop-engine.py' transition docs/specs/<feature> wave-complete
# Re-run GATES → fire gates-clean or gates-failed → re-enter REVIEW.
```
