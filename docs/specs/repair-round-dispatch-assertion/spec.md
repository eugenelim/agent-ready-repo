# Spec: repair-round dispatch assertion

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md) (Option A: a transition permits a change and never causes one, so no cohort write may become a side effect of firing an edge); `wave-complete-dispatch-receipts` (Shipped and frozen — it owns the receipt data model, the accounting predicate, and the wave-exit verdict table this spec leaves intact — its § Ask first requires human sign-off for *scoping a record to a repair round* and for *any change to the review-phase guards*, and the owner granted both on 2026-09-23)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without
> a review round. A review finding against working material is advisory — it
> cannot block, because nothing gates the text it cites.

## Outcome

A maintainer running the work loop in full mode cannot discharge the **current**
wave's exit twice from a single set of dispatch records: every edge that
re-enters code implementation without moving the wave pointer first requires
that wave to be reopened, and reopening empties its records. A repair round
therefore exits only by recording a fresh assertion for every task in that wave,
and the refusal names the tasks that still lack one.

## What Changes

- A wave-reopen mutation verb — `loop-cohort.py`, beside `wave check` and `wave advance`
- A fifth `check --phase` value, its verdict, and its membership of the schema-exempt phase set — `loop-cohort.py`'s `PHASES`, and `_loop_guards.py`'s `_SCHEMA_EXEMPT_PHASES`
- Guard entries on the three re-entry edges, discriminated by source state, including the first guard `blocker-applied` has ever carried — `loop-engine.py`'s `_GUARDS`
- The controller's repair-round protocol, which now runs the reopen before firing the edge — every `work-loop` prose and eval site that directs a reader to fire one of the three edges, found by search rather than by a remembered list
- A committed oracle that walks the repair-round verdict over the frozen spec's declared field axes — this spec's `notes/`
- A mutation record for every new guard and verb clause — this spec's `notes/verification-ledger.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The re-entry edges and the two lock domains are described there, and the description becomes wrong without this | `docs/architecture/loop-infrastructure.md` §§ 4, 6 | maintainer | The section names the reopen obligation and which edges carry it | The named sections describe the shipped edges |
| Maintainer procedure | A controller that does not run the reopen cannot re-enter implementation, so the procedure is not optional | `packs/core/.apm/skills/work-loop/SKILL.md` and `references/full-mode-engine.md`, `references/session-resumption.md` | maintainer | Each of the three edges states the reopen step in its own command sequence | Every documented sequence that fires one of the three edges runs the reopen first |
| Interface compatibility | A new CLI verb and a new `--phase` value are published interfaces of the packaged scripts | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | maintainer | Both carry one patch above the merge-base and agree | The two versions are equal and one patch above the merge-base |
| Release history | Pack content changed | `docs/product/changelog.md`, one `## [core][x.y.z]` heading | maintainer | The entry names the new refusal a controller will meet | One core heading for the branch, topmost beneath `[Unreleased]` |
| Reusable learning | The eval harness is the pack's contract record for a non-cosmetic update | `packs/core/.apm/skills/work-loop/evals/evals.json` | maintainer | An entry covering the repair-round obligation | The entry exists; it is never counted as verification |
| Verification evidence | The mutation record is a criterion, so it needs a home a later reader can find | `docs/specs/repair-round-dispatch-assertion/notes/verification-ledger.md` | maintainer | One entry per new guard and verb clause: the clause, the edit that removed it, the test that turned red, the observed failure | Every new clause has an entry and none left the suite green |
| Decision rationale | None — this follows ADR-0061 Option A rather than departing from it, and adds no key to cohort state | not applicable | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Run the frozen wave-exit oracle before and after every predicate change and compare every figure it prints against the baseline this spec's criteria state.
- Derive container depth from `len(RECEIPT_KEY_PATH)` and task accounting from `unaccounted_wave_tasks`; call the declared predicate rather than restating it.
- Decide the repair-round guard from the engine's source state, never from the run mode: `_GUARDS` is keyed by `(mode, event)`, so the mode alone cannot tell a code-mode `findings-remain` fired from `SPEC-PLAN-REVIEW` from one fired from `CODE-REVIEW`.

### Ask first

- Adding, renaming, or removing any key in cohort `state.json`.
- Changing what `is_dispatch_record` accepts.
- Any further change to the `wave-passed` guard, beyond the review-phase-guard change the owner signed off on 2026-09-23.

### Never do

- Never move `SCHEMA_VERSION`.
- Never change what `check --phase implement` returns for any state. `wave-complete-dispatch-receipts` § Never do owns this rule and states why: local `make pre-pr` and the always-run `build-check` pull-request gate run that phase for every spec directory with no state-machine gate.
- Never widen `DECLINE_REASONS`; `wave-complete-dispatch-receipts` § Ask first owns that decision and this delivery does not reopen it.
- Never add a row to, remove a row from, or change the precondition of any row in `_wave_exit_verdict`.
- Never write cohort state as a side effect of an engine transition; the reopen is a skill-invoked mutation, as ADR-0061 Option A requires.
- Never add a new top-level directory, module boundary, or dependency.

## Testing Strategy

- **The reopen verb's effect on cohort state: TDD.** Removing one subtree while leaving every sibling byte-identical is a compressible invariant over a structure the suite can build directly.
- **The reopen verdict table: TDD, plus a committed oracle walk.** Each row is unit-testable, but "exactly one row applies to any state" is a property over a state space no example set covers; the oracle is what decides it, the way `walk_verdict_partition.py` decides the wave-exit partition.
- **The three edges refusing and then admitting: TDD at integration surface.** Each edge only proves out across the engine, the guard layer, and cohort state together, so the check drives `loop-engine transition` against a real spec directory rather than calling the guard directly.
- **The wave-exit partition's immutability: goal-based check.** The committed oracle already prints the comparison values; re-running it and diffing its report is the one-liner.
- **Projection parity after `make build-self`: goal-based check.** Its three-copy parity check is the observable outcome, not the exit code.

## Acceptance Criteria

### The repair-round verdict

- [ ] The repair-round check refuses when all of the following hold, and passes otherwise: the cohort state was readable; `schema_version` is the supported value; `dispatch_receipts` is present; the container is well-formed at the declared key path; `schedule_waves` is a non-empty list; `current_wave_index` is a non-negative integer and an index into it; the wave at that index is well-formed; and at least one task in that wave carries a dispatch record.
- [ ] Its refusal names the verb that clears the records and the wave index the refusal is about.
- [ ] `check --phase wave-reopen` reaches that verdict for a state whose `schema_version` is not the supported value, instead of being refused by the phase dispatcher's schema check before the verdict runs.
- [ ] For every state the oracle below walks that has a `state.json`, the file is byte-identical before and after a `check --phase wave-reopen` invocation.

### The reopen verb

- [ ] `loop-cohort wave reopen <spec-dir> --expect-run-id <id>` deletes the record subtree held under the live partition digest at `current_wave_index`, and leaves every other wave index, every other partition digest, and every other top-level key in `state.json` byte-identical.
- [ ] `dispatch_receipts` is present in `state.json` after every successful reopen, including one whose removed subtree was the container's only content.
- [ ] After a reopen whose removed subtree was the container's only content, `check --phase wave-exit` refuses and names the wave's tasks, rather than printing its not-enforced notice.
- [ ] A second reopen against a state whose current wave holds no records exits zero and leaves `state.json` byte-identical.
- [ ] `wave reopen` refuses, and leaves `state.json` byte-identical, when `--expect-run-id` does not match `run_id`, when `schedule_waves` is not a non-empty list, when `current_wave_index` is not an index into it, and when `dispatch_receipts` is malformed; each refusal names the mismatch or the field.

### The three edges

- [ ] `gates-failed` from `CODE-VERIFICATION`, `findings-remain` from `CODE-REVIEW`, and `blocker-applied` from `CODE-HUMAN-GATE` are each refused while the repair-round verdict refuses, and each admitted once it passes, the run re-entering `CODE-IMPLEMENTATION`.
- [ ] `findings-remain` fired from `SPEC-PLAN-REVIEW` in a code-mode run is admitted while dispatch records are present for the current wave, both before the run has ever reached `CODE-IMPLEMENTATION` and after a `contract-amendment` has returned it to `SPEC-PLAN-DRAFTING`.
- [ ] A state failing any one conjunct of the repair-round verdict is admitted on all three edges with no reopen.
- [ ] `gates-failed` and `findings-remain` evaluate the guard they already carry first, so a state failing both that guard and the repair-round verdict is refused with the existing guard's reason.
- [ ] `findings-remain --allow-retry-cap-override` waives the review retry cap alone, and is still refused while the repair-round verdict refuses.

### Controller-facing surfaces

- [ ] Every site under `packs/core/.apm/skills/work-loop/` that instructs a reader to fire `gates-failed`, `findings-remain` from `CODE-REVIEW`, or `blocker-applied` shows the reopen immediately before that instruction, and the site set is produced by a search over that tree rather than from a list written in advance.
- [ ] The number of sites instructing one of those three edges equals the number instructing a reopen before it.
- [ ] `references/session-resumption.md` states, in each of the three events' rows, the reopen step and where it falls relative to the transition.
- [ ] `evals/evals.json` carries an entry covering the repair-round obligation, and every expected output in it that names one of the three edges agrees with the shipped instruction.

### Proof

- [ ] `docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py` reports 35,728 states walked, 0 overlapping, 0 uncovered, and per-row reachability R1 17864, R2 13398, R3 3829, R4 49, R5 384, R6 108, R7 4, R8 92.
- [ ] A committed oracle under this spec's `notes/` checks the repair-round verdict over a domain built by varying the axes that `wave-complete-dispatch-receipts` § Acceptance Criteria declares to be the single canonical enumeration, with container values generated from the declared key path rather than hand-built at a literal depth, and reports that the verdict refuses on exactly the states satisfying the conjunction stated above and passes on every other state in the domain.
- [ ] A mutation record in this spec's `notes/verification-ledger.md` names each new guard clause and each new verb clause, the edit that removed it, the test that turned red, and the observed failure, with no clause whose removal left the suite green.

## Follow-ons

- eugenelim: `workspace.toml` `[backlog].open`, the entry on `docs/adr/0061-loop-infrastructure-phase-1.md` whose summary opens "Leave a durable trace when a wave exit passes" — unchanged by this spec and still open.
- eugenelim: `docs/architecture/loop-parallelism.md` § 1 — per-round dispatch history. Reopening discards the previous round's records, so no reader can recover who was dispatched in an earlier round, and a reopen that lands before an unfired `blocker-applied` leaves that loss behind when the run is instead discharged through `done`. § 1's unified transition history is where a durable per-round record would live; it is blocked on governance records that do not exist, and this spec does not depend on it.
- eugenelim: `workspace.toml` `[backlog].open` — repair work that lands in an already-passed wave carries no fresh assertion, because the reopen clears only the wave at `current_wave_index` and the earlier wave's exit is never re-examined. The register entry this spec closes is scoped to the current wave, so this is a separate limit rather than unfinished scope.

## Assumptions

- Technical: the controller runs the reopen before firing the edge — the guard reads cohort state as it stands before the transition, so a reopen run afterwards clears records the guard has already read. This is checked by the guard itself rather than assumed, and it is stated here because the ordering is what the documented procedure has to carry.
- Technical: at each of the three source states, `current_wave_index` still addresses the wave whose tasks the repair round edits. True today because no edge between them moves the pointer; a future edge that did would need this contract revisited.
