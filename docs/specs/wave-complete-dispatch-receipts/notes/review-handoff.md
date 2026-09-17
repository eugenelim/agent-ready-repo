# Review handoff — wave-complete dispatch receipts

Run `2fbae32e-0dc7-4e27-b80e-d9c34451a693`. Engine left at `SPEC-PLAN-REVIEW`
(seq 5) with sustained findings open, which is the correct resumable state: a
resuming session fires `findings-remain` before revising.

## Why this stopped rather than continuing

Three pre-EXECUTE review rounds ran on both lanes (`adversarial-reviewer` and
`security-reviewer`, spec-stage secure-design mode). Round 1's findings were
adjudicated by `finding-adjudicator`; rounds 2 and 3 were verified against code
directly.

Every round found its blockers inside the previous round's repairs:

| Round | Adversarial | Security | Where the blockers sat |
| --- | --- | --- | --- |
| 1 | 6 blockers, 5 concerns, 3 nits | 3 blockers, 6 concerns | original draft |
| 2 | 6 blockers, 5 concerns, 2 nits | 3 blockers, 5 concerns | inside round-1 repairs |
| 3 | 4 blockers, 10 concerns, 2 nits | 2 blockers, 4 concerns, 1 nit | inside round-2 repairs |

Adjudication in round 1 refuted 4 of 23 findings, so the reviewers are not
simply always right — but the sustained rate is high and the pattern is stable.

**The class, stated once:** criteria were authored as assertions about desired
outcomes and only afterwards checked against the code that would satisfy them.
Round 1 produced claims stronger than their mechanism. Round 2 produced criteria
whose mechanism did not exist. Round 3 produced criteria that contradict each
other because each was written as an unconditional predicate over a state space
that overlaps its neighbours — and one round-3 "verified mechanism fact" was
itself over-generalized (see below). Patching individual criteria has not
touched this, because the defect is in how the criteria are derived.

## The recommended next move

Rewrite the Acceptance Criteria block for the guard as an explicit **decision
table over cohort state**, not a list of independent sentences. Columns: the
state predicate, the exit code, the channel the message uses, and the criterion
that owns it. Rows must partition the state space, so exactly one row applies to
any cohort state. That form makes the round-3 blocker class unrepresentable:
overlapping antecedents with opposite consequents cannot be written down.

Enumerate the state space at least over: unreadable or missing `state.json`;
`schedule_waves` empty; `schedule_waves` non-empty with the container absent;
container present and `current_wave_index` out of range; container present,
pointer valid, every task accounted for; same but at least one task unaccounted;
and a container or `schedule_waves` whose type is wrong.

Derive each row's channel from the code before writing it, not after.

## Corrections to carry forward

- **`cmd_check` can emit on a passing guard.** `GuardResult` carries `message`
  alongside `reason`, and `cmd_check` calls `_emit(result.message)` for a
  passing result. What is true is narrower: a passing `GuardResult` may not
  carry a `reason` (`__post_init__` raises unless `ok` is true exactly when
  `reason` is None), and `loop-engine._guard_reason` returns None for any
  passing result, so the *engine* cannot surface a passing guard's text. The
  spec's Boundary and Assumption are correctly scoped to the engine; the plan's
  Design decision generalises wrongly and must be corrected.
- **The owner chose `loop-cohort status`** as the absent-container disclosure
  channel, over widening scope to the engine's shared guard adapter
  (2026-09-17). That decision stands. Only its stated rationale was wrong.
- **`cmd_status` refuses on `schema_version != 1`** while the `implement` guard
  deliberately skips schema validation, so for the oldest state class the guard
  tolerates, `status` produces no signal at all. The disclosure channel does not
  cover the whole class it was chosen to serve.
- **The frozen golden row is an unscheduled state.** `check/implement-ok`
  supplies `schedule_waves: []` and `current_wave_index: 0`. The fixture is
  generated once and deliberately never regenerated, and a preserved row
  asserts both streams byte-for-byte, so no row may be added or rewritten. A
  guard that passes silently on an unscheduled state preserves it.
- **`cmd_schedule` resets the wave pointer under an unchanged `run_id`** and
  re-derives `plan_hash`. So the run identifier cannot scope a record across a
  re-schedule, and `plan_hash` can also change for an ordinary prose edit to
  `plan.md` — which invalidates correct records without the partition changing.
- **`cmd_wave_advance` is not coupled to the implement check**, so a wave can be
  advanced past without ever being accounted for.

## Open blockers at the point of stopping

1. Criteria for the guard overlap with opposite consequents; a test written
   literally from the out-of-range criterion reddens the frozen golden row.
   Subsumed by the decision-table rewrite above.
2. A receipt is recordable for a wave the run has not yet entered, so one
   up-front batch could discharge every wave exit in the run. Bound the index to
   the current wave or one already left.
3. "`schedule` leaves the container present" is satisfied by an unconditional
   assignment that erases every existing record. Needs a preservation criterion
   with a test that reddens on overwrite.
4. The no-output criterion has no assertion on the accounted-for passing path,
   and its stated basis is the false generalisation above.
5. The dispatch-rate measurement is promised as a durable output but no task's
   `Done when` requires it.
6. The `loop-cohort status` assertion has no owning test file in any `Touches`,
   and `test_loop_cohort_schedule.py` — the existing schedule suite — is
   unaccounted for by the task that changes `cmd_schedule`.

## Open concerns worth keeping

- The closed decline set is enforced only on the write path; the guard counts a
  record without inspecting its reason, so free text or a third code already in
  `state.json` would be honoured.
- No criterion places receipt authorship with the controller, though
  `SKILL.md` already declares what the controller retains, so saying it is prose
  rather than a new trust mechanism.
- Re-entry into `CODE-IMPLEMENTATION` via `gates-failed` or `findings-remain`
  does not move `current_wave_index`, so a repair round exits through a guard the
  first pass's receipts already satisfy — and repair rounds are where the
  controller most often works alone.
- The key-agreement criterion may be unfalsifiable if the container key is
  single-sourced, which is the natural implementation.
- The no-write invariant is appended to five refusal criteria instead of being
  one criterion over the enumerated refusal set.
- A malformed container or `schedule_waves` falls past every branch into the
  accounting arm; `@contained` turns it into an opaque `internal-error` refusal
  that no criterion enumerates.
- T6 does not pin the bump class, and this change adds a new CLI verb and a new
  state field.

## What is settled and should not be relitigated

- Per-task granularity, not per-wave. The wave's task list is the denominator.
- The receipt is an assertion, not proof of dispatch, and the spec says so.
- Any actor that can read `run_id` can write a record, including a dispatched
  `implementer`; nothing scopes a record to the task its writer was dispatched
  for. Accepted, because scoping it means establishing caller identity.
- ADR-0061 Option A holds: explicit cohort mutation, read-only guard, no
  `pending_transition`, no idempotency key.
- Round-1 refutations: declines need no corroboration mechanism here, and a
  provenance marker cannot replace key-absence.
