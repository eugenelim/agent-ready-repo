# Verification ledger — lifecycle-transition-contract

Execution observations. The approved `spec.md` and `plan.md` carry obligations;
this file carries what running them produced. Not hash-pinned, so recording an
observation here amends neither approved artifact.

## T3 — delivered, and accepted as not machine-recorded (2026-09-24)

**Delivered** in commit `d00f39e34`. The pre-rule derivation reported both sets
the spec's § What Changes names: **14 artifacts refused and 10 never `Accepted`**
before the migration, **0 and 0** after. `notes/migration-record.md` carries one
entry per artifact in the second set, naming the branch taken and the owner
waiver it rests on.

**Accepted risk — read this before scheduling a wave.** The cohort's
`completed_task_ids` is empty, because this run's engine was initialised fresh
and the `contract-amendment` transition that populates that field is reachable
only from `CODE-IMPLEMENTATION`. No `loop-cohort` verb writes it, and the skill
forbids hand-editing `state.json`. **So a resumed run will schedule T3 again.**
The owner accepted this on 2026-09-24 in preference to a hand edit or a
re-entered no-op wave.

If a wave emits T3: **do not re-execute it.** Its pre-rule derivation now passes
vacuously on the corpus it produced, so the task has no check that can fail.
Verify instead by reading `notes/migration-record.md` and commit `d00f39e34`,
then record a dispatch-receipt.
