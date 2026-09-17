# Review handoff — wave-complete dispatch receipts

Run `2fbae32e-0dc7-4e27-b80e-d9c34451a693`. Engine left at `SPEC-PLAN-REVIEW`
with sustained findings open, which is the correct resumable state: a resuming
session fires `findings-remain` before revising.

## Status: a snapshot taken at the round below the table's last row

This file is the state at the point it was written, not the current state. Later
rounds are recorded in the plan's revision history, which is the live home.
Rounds 7 onward ran on Codex reviewers rather than Claude subagents; round 10
used two reviewers with disjoint focus sets, one on contract and verification
mechanism, one on secure design. The
conclusion recorded here — that the next step was a spike rather than another
round — was acted on; the open blockers below are the ones that were open then.

The table records one row per pre-EXECUTE review round on both lanes
(`adversarial-reviewer` and `security-reviewer`, spec-stage secure-design mode).
Round 1's findings were adjudicated by `finding-adjudicator`; the rounds after
it were verified against code directly.

| Round | Adversarial | Security | Where the blockers sat |
| --- | --- | --- | --- |
| 1 | 6 blockers, 5 concerns, 3 nits | 3 blockers, 6 concerns | original draft |
| 2 | 6 blockers, 5 concerns, 2 nits | 3 blockers, 5 concerns | inside round-1 repairs |
| 3 | 4 blockers, 10 concerns, 2 nits | 2 blockers, 4 concerns, 1 nit | inside round-2 repairs |
| 4 | 5 blockers, 5 concerns, 2 nits | 4 blockers, 3 concerns, 1 nit | inside round-3 repairs, plus one external caller |
| 5 | 4 blockers, 6 concerns, 3 nits | 1 blocker, 6 concerns, 1 nit | inside round-4 repairs |
| 7 | adjudicated | adjudicated | round-6 repairs |
| 9 | 15 findings | 9 findings | mixed: round-8 repairs and pre-existing |
| 10 | 2 blockers, 5 concerns | 1 blocker, 2 concerns, 1 nit | both blockers were round-9 drift |

Round 1 adjudication refuted 4 of 23 findings, so the reviewers are not simply
always right. The sustained rate is high and the pattern did not break.

**The class, stated once.** Each round's central design decision was invalidated
by a fact about the surrounding system that surfaced only when a reviewer pointed
at it. The instances differ; the cause does not. The spec was written against a
model of the engine, the guard layer, and the skill, and the model was wrong in
a different place each time:

- Round 2: a passing `GuardResult` cannot carry a `reason`, so the disclosure
  channel did not exist.
- Round 3: `cmd_check` *can* emit on a pass via `message`, so the impossibility
  claimed in round 2's repair was itself wrong.
- Round 4: `pre-pr.py` runs `check --phase implement` for every spec directory
  on every push, ungated, so putting the accounting there is a push gate.
- Round 5: GATES runs *after* `wave-complete`, so the caller added in round 4's
  repair is in the wrong section; and the new phase inherits a `schema_version`
  refusal the `implement` phase is deliberately exempt from, so the retarget
  changes the transition's verdict for pre-Phase-1 state from pass to refuse.

Specifying further against the same model will keep producing this. The next
step is to establish the model first.

## The spike this needs before any more specification

Read and record, before writing another criterion:

1. **Every caller of the guard surface.** `pre-pr.py` was found by reading, not
   grepping, because the phase name reaches the argument list through a loop
   variable. Enumerate every invocation of `loop-cohort check`, every entry in
   `loop-engine.py`'s guard table, and every hook, script, or workflow that
   reaches either — in `tools/`, `packs/core/.apm/hooks/`, and the projections.
2. **Every site that fires `wave-complete`.** Round 5 found four:
   `references/supervisor-mode.md`, `references/session-resumption.md`,
   `SKILL.md`'s two repair paths, and `references/finding-adjudication.md`.
   Three are in no task's `Touches`. Establish which sections run before the
   transition and which after — GATES runs after.
3. **The `schema_version` axis.** `check_phase` refuses any phase but
   `implement` on an unsupported schema, and
   `packs/core/tests/skills/work-loop/test_loop_guards.py` pins that asymmetry
   as deliberate and load-bearing. Decide what the wave exit owes for that state
   class before choosing a phase, because the choice of phase decides it.
4. **Every statement in the tree that asserts `implement` guards
   `wave-complete`.** Round 5 found three: `check_phase`'s docstring,
   `cmd_check`'s docstring, and a test docstring. A retarget falsifies all
   three and orphans `_guard_check_phase_implement`.
5. **Every surface that enumerates the phase list.** `PHASES`, the argparse
   choices, `loop-cohort.py`'s usage block, and
   `references/state-schema.md`'s `check` exit contract.
6. **The truncation and bounding contract for refusal text.**
   `_MAX_REASON_CHARS` is 4000 and `_scalar` caps at 120, both in
   `_loop_guards.py`; `_diag` in `loop-cohort.py` has no length bound at all.
   A refusal that must "name every unaccounted task" collides with these.

## The simplification the last round found, which should survive

`_schedule_run_impl` sets `current_wave_index = 0` unconditionally. A
re-schedule therefore means every wave is re-executed, so records written before
it describe work that must be redone. That makes **`schedule` clearing the
receipts container** correct rather than destructive — and once it clears, the
partition digest has no remaining job.

Removing the digest removes, in one move: the digest helper, digest-keyed
records, the stale-record pruning rule, the amendment clear, the "one live
partition so no size cap" argument and its collision with the 1 MiB amendment
ceiling, the pointer-rewind pre-discharge, and the criterion about a
partition-preserving re-schedule. Every one of those was generating findings in
rounds 4 and 5. Records become keyed by wave index and task identifier alone.

An amendment empties `schedule_waves` and forces a re-approval and re-schedule
before implementation continues, so it inherits the clear and needs no rule of
its own.

## The verification lesson, which is the reusable part

The recurring gap was not in the predicates but in the **domain they were
checked over**. Each successive walk drew its domain from the predicates under
test, so each could find overlaps and never gaps. Verification ledger § 4 owns
the full roster; the progression that matters here is:

- 480 states over my own row conditions — found the row-2/row-3 overlap, missed
  the malformed wave element.
- 1,152 states over field *types* — found the malformed wave element, missed
  malformed container interiors and record leaves.
- 1,800 states over the literal spec wording — found two wording ambiguities,
  still missed record `kind` and record shape, which both lanes then reported.

A domain sourced from the thing under test cannot exhibit a gap outside it. The
domain has to be generated over arbitrary values at every position the predicate
reads, and the predicate has to be total by construction rather than bounded one
level at a time.

## Open blockers at the point of stopping

1. The pre-exit check is specified in GATES, which runs after `wave-complete`.
   It belongs at every site that fires the transition, and most of those sites
   were in no task's `Touches`. Verification ledger § 2 owns the measured site
   set.
2. The `wave-exit` phase inherits `check_phase`'s `schema_version` refusal,
   which `implement` is exempt from, so the retarget silently changes the
   transition's verdict for pre-Phase-1 state. The rows do not model the axis
   and the constructed domain does not vary it.
3. Well-formedness is defined only at the container's top level. A record that
   is not a mapping, or whose `kind` is outside the closed set, either
   fail-opens into "accounted for" or raises into the opaque `@contained`
   refusal the named rows exist to replace. Both lanes reported this
   independently.
4. Testing Strategy promises the pre-PR hook's verdict is unchanged, and no
   task's `Tests`, `Done when`, or `Touches` covers it.

## Open concerns worth keeping

- Three code comments and a test docstring assert that `implement` guards
  `wave-complete`; a retarget falsifies them and orphans
  `_guard_check_phase_implement`.
- The phase enumeration in `loop-cohort.py`'s usage block and the `check` exit
  contract in `references/state-schema.md` are not required to learn the phase.
- The digest-versus-`plan_hash` criterion has no assertion that exercises a
  `plan.md` edit, so it would stay green under a `plan_hash`-keyed
  implementation.
- The `implement`-unchanged criterion supplies its own comparison value for the
  per-row states, and its stated rationale names the rows when the shared
  preamble is what could actually move that phase's verdict.
- "Bounds the class" overstates the in-flight-upgrade window: `schedule` runs
  only on a plan change or amendment, so a run that never re-schedules keeps
  enforcement off for its whole life. The mid-upgrade re-schedule case — an
  empty container against a non-empty partition, needing after-the-fact
  declines for already-implemented tasks — is in no enumerated list.
- The verb interpolates unbounded state-derived text into refusals through
  `_diag`, which has no length bound, while the guard layer's `_scalar` caps at
  120 and `GuardResult` truncates at 4000. "Name every task" is unsatisfiable at
  the cap and currently fails toward silent under-reporting.
- The absent-container notice's only caller is a prose step addressed to the
  party the guard constrains, and skipping it is silent and undetectable — the
  same weakness the change exists to remove, now carrying the disclosure half.
- `cmd_reset` is a third record-removal path the `Never do` rule does not name.
- Two pinned task obligations — the eval case and the manifest bump — trace to
  `packs/AGENTS.md` rather than to an acceptance criterion.
- The Objective's "four limits" is a closed count that goes stale each time a
  fifth is found; state the positive property and group exceptions by
  consequence instead.

## What is settled and should not be relitigated

- Per-task granularity, not per-wave. The wave's task list is the denominator.
- A record is an assertion, not proof of dispatch, and the spec says so.
- Any actor that can read `run_id` can write a record, including a dispatched
  `implementer`; nothing scopes a record to the task its writer was dispatched
  for. Accepted, because scoping it means establishing caller identity.
- The accounting must not live in `--phase implement`, because `pre-pr.py` makes
  that phase a push gate.
- ADR-0061 Option A holds: explicit cohort mutation, read-only guard, no
  `pending_transition`, no idempotency key.
- Round-1 refutations: declines need no corroboration mechanism here, and a
  provenance marker cannot replace key-absence.
- Round-2 refutations: the version-bump level is fixed at patch by
  `packs/AGENTS.md` itself, and the measurement's two homes are the template's
  own shape.
