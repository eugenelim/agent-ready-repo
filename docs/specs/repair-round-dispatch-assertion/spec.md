# Spec: repair-round dispatch assertion

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md) (Option A: a transition permits a change and never causes one, so no cohort write may become a side effect of firing an edge); `wave-complete-dispatch-receipts` (Shipped and frozen — it owns the receipt data model, the accounting predicate, and the wave-exit verdict table this spec leaves intact. Its § Ask first requires human sign-off for *scoping a record to a repair round* — the substantive permission this delivery uses, granted by the owner on 2026-09-23 — and separately for *any change to the review-phase guards*, also granted, which covers the `findings-remain` entry. The new `gates-failed` and `blocker-applied` guard entries are the mechanism of the first permission, not review-phase guards. Its § Never do forbids removing a record by any path but the three it names, and that rule is not reachable by sign-off, so this delivery removes no record)
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

A maintainer running the work loop in full mode cannot discharge the current
wave's exit twice from a single set of dispatch records: `gates-failed`,
`findings-remain` from code review, and `blocker-applied` each require that wave
to be reopened first, which marks its records superseded so they account for
nothing further. A repair round therefore exits only by recording a fresh
assertion for every task in that wave, and the refusal names the tasks that
still lack one.

## What Changes

- A wave-reopen mutation verb that marks the current wave's records superseded and removes none — `loop-cohort.py`, beside `wave check` and `wave advance`
- One clause in the shared accounting predicate, so a superseded record accounts for no task — `unaccounted_wave_tasks` in `_loop_guards.py`
- A fifth `check --phase` value, its verdict, and its membership of the schema-exempt phase set — `loop-cohort.py`'s `PHASES`, and `_loop_guards.py`'s `_SCHEMA_EXEMPT_PHASES`
- Guard entries on the three named edges, discriminated by source state, including the first guard `blocker-applied` has ever carried — `loop-engine.py`'s `_GUARDS`
- The controller's repair-round protocol, which now runs the reopen before firing the edge — three fenced blocks in `references/full-mode-engine.md`, two in `references/finding-adjudication.md`, `SKILL.md`'s repair-round paragraphs, and two rows of `references/session-resumption.md`: `wave-complete`, which fires `gates-failed`, and `reviewers-clean`, which fires `blocker-applied`
- A `superseded` member on a dispatch record, whose absence means live — `references/state-schema.md`'s `dispatch_receipts` row, which today tells adopters that a receipt and a decline "both count as accounted for"
- A committed oracle that walks the repair-round verdict over the frozen spec's declared field axes — this spec's `notes/`
- A mutation record for every new guard clause, verb clause, and the accounting predicate's superseded clause — this spec's `notes/verification-ledger.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The re-entry edges and the two lock domains are described there, and the description becomes wrong without this | `docs/architecture/loop-infrastructure.md` §§ 4, 6 | maintainer | The section names the reopen obligation and which edges carry it | The named sections describe the shipped edges |
| Maintainer procedure | A controller that does not run the reopen cannot re-enter implementation, so the procedure is not optional | `references/full-mode-engine.md` and `references/finding-adjudication.md` for the fenced blocks; `references/pre-execute-review.md` for the one that must stay unguarded; `SKILL.md`'s repair-round paragraphs; and `references/session-resumption.md`'s `wave-complete` and `reviewers-clean` rows | maintainer | Each unconditionally guarded block runs the reopen above its transition; the two `finding-adjudication.md` blocks carry it under a stated `CODE-REVIEW` condition; and the two `SPEC-PLAN-REVIEW` blocks carry none | Demoted working material: the pack suite's content pin holds it, no criterion does |
| Interface compatibility | A new CLI verb and a new `--phase` value are published interfaces of the packaged scripts | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | maintainer | Both carry one patch above the merge-base and agree | The two versions are equal and one patch above the merge-base |
| Release history | Pack content changed | `docs/product/changelog.md`, one `## [core][x.y.z]` heading | maintainer | The entry names the new refusal a controller will meet | One core heading for the branch, topmost beneath `[Unreleased]` |
| Reusable learning | The eval harness is the pack's contract record for a non-cosmetic update | `packs/core/.apm/skills/work-loop/evals/evals.json` | maintainer | An entry covering the repair-round obligation | The entry exists; it is never counted as verification |
| Interface documentation | `references/state-schema.md` is packaged and read by adopters, and its `dispatch_receipts` row states a rule the superseded clause makes false | `packs/core/.apm/skills/work-loop/references/state-schema.md` | maintainer | The row describes the `superseded` member, its absence rule, and what now counts as accounted for | The row agrees with `unaccounted_wave_tasks` |
| Verification evidence | The mutation record is a criterion, so it needs a home a later reader can find | `docs/specs/repair-round-dispatch-assertion/notes/verification-ledger.md` | maintainer | One entry per new guard clause, verb clause, and the accounting predicate's superseded clause: the clause, the edit that removed it, the test that turned red, the observed failure | Every new clause has an entry and none left the suite green |
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
- Any change to the `wave-passed` guard. `wave-complete-dispatch-receipts` § Ask first states it as its own item, and this delivery does not reach it.

### Never do

- Never move `SCHEMA_VERSION`.
- Never change what `check --phase implement` returns for any state. `wave-complete-dispatch-receipts` § Never do owns this rule and states why: local `make pre-pr` and the always-run `build-check` pull-request gate run that phase for every spec directory with no state-machine gate.
- Never widen `DECLINE_REASONS`; `wave-complete-dispatch-receipts` § Ask first owns that decision and this delivery does not reopen it.
- Never remove a dispatch record. `wave-complete-dispatch-receipts` § Never do owns this rule and names the only three paths that may: a `schedule` run under a different partition, a contract amendment, and `loop-cohort reset`. Superseding a record is not removing it.
- Never add a row to, remove a row from, or change the precondition of any row in `_wave_exit_verdict`.
- Never write cohort state as a side effect of an engine transition; the reopen is a skill-invoked mutation, as ADR-0061 Option A requires.
- Never add a new top-level directory, module boundary, or dependency.

## Testing Strategy

- **The accounting predicate's superseded clause: TDD.** One clause with two shipped consumers — the wave exit and `wave advance` — is exactly the shape where a change verified through one consumer passes while the other disagrees, so both are driven.
- **The reopen verb's effect on cohort state: TDD.** Marking every record in one wave while leaving every sibling record and every other key byte-identical is a compressible invariant over a structure the suite can build directly.
- **The reopen verdict table: TDD, plus a committed oracle walk.** Each row is unit-testable, but "exactly one row applies to any state" is a property over a state space no example set covers; the oracle is what decides it, the way `walk_verdict_partition.py` decides the wave-exit partition.
- **The three edges refusing and then admitting: TDD at integration surface.** Each edge only proves out across the engine, the guard layer, and cohort state together, so the check drives `loop-engine transition` against a real spec directory rather than calling the guard directly.
- **The frozen contract's model, unchanged: goal-based check.** The committed oracle prints its own comparison values, so re-running it and diffing the report is the one-liner. It establishes that this delivery did not redefine a record, a wave or a partition — not that the partition is immutable, which it is not: the superseded clause deliberately moves states from R7 to R8.
- **The documented repair-round procedure: goal-based check, against a content pin rather than a criterion.** The obligation is demoted working material: no acceptance criterion reads it, so what stands between it and silent removal is a prose assertion in the pack suite. § Controller-facing surfaces records the demotion and its authority.
- **Projection parity after `make build-self`: goal-based check.** Its three-copy parity check is the observable outcome, not the exit code.

## Acceptance Criteria

The three edges this contract names are `gates-failed` from `CODE-VERIFICATION`,
`findings-remain` from `CODE-REVIEW`, and `blocker-applied` from
`CODE-HUMAN-GATE`. `wave-passed` is not among them; § Follow-ons records why.

### The repair-round verdict

- [ ] The repair-round check refuses when all of the following hold of a readable cohort state, and passes otherwise: `schema_version` is the supported value; `dispatch_receipts` is present; the container is well-formed at the declared key path; `schedule_waves` is a non-empty list; `current_wave_index` is a non-negative integer and an index into it; the wave at that index is well-formed; and at least one task in that wave carries a record that is not superseded.
- [ ] The read refusal is unchanged: an unreadable cohort state is refused by the shared reader before the verdict runs, exactly as it is for `check --phase wave-exit` today, and the verdict is never reached for one.
- [ ] Its refusal names the verb that supersedes the records and the wave index the refusal is about.
- [ ] `check --phase wave-reopen` reaches the verdict for a state whose `schema_version` is not the supported value, instead of being refused by the phase dispatcher's schema check before the verdict runs.
- [ ] For every state the oracle below walks that has a `state.json`, the file is byte-identical before and after a `check --phase wave-reopen` invocation.

### The reopen verb

- [ ] `loop-cohort wave reopen <spec-dir> --expect-run-id <id>` marks every record held under the live partition digest at `current_wave_index` superseded, and leaves every other wave index, every other partition digest, and every other top-level key in `state.json` byte-identical.
- [ ] The count of records in `state.json` is equal before and after every successful reopen, and every record that was present before is still present and still satisfies `is_dispatch_record`.
- [ ] After a reopen, `check --phase wave-exit` refuses and names the wave's tasks, including when the reopened wave's records were the container's only content.
- [ ] A second reopen against a state whose current wave is already wholly superseded exits zero and leaves `state.json` byte-identical.
- [ ] Recording a fresh dispatch record for a superseded task, through the existing `dispatch-receipt` verb and with no new flag, makes that task account again.
- [ ] `wave reopen` refuses, and leaves `state.json` byte-identical, when `--expect-run-id` does not match `run_id`, when `schedule_waves` is not a non-empty list, when `current_wave_index` is not an index into it, and when `dispatch_receipts` is malformed; each refusal names the mismatch or the field.

### The accounting predicate

- [ ] `loop-cohort wave advance`'s advancing branch refuses a wave whose records are all superseded, so the predicate's second consumer agrees with the wave exit that the first group already pins.
- [ ] The wave-exit refusal and the `wave advance` refusal each distinguish a superseded record from an absent one, so a controller is not told a record is missing when one is present and superseded.
- [ ] `unaccounted_wave_tasks` treats a record carrying no `superseded` member as live, so every `state.json` written before this change means what it meant before it.
- [ ] `references/state-schema.md`'s `dispatch_receipts` row describes the `superseded` member and its absence rule, and no longer states that a receipt and a decline both count as accounted for without qualification.

### The three edges

- [ ] Each of the three named edges is refused while the repair-round verdict refuses, and admitted once it passes, the run re-entering `CODE-IMPLEMENTATION`.
- [ ] `findings-remain` fired from `SPEC-PLAN-REVIEW` in a code-mode run is admitted while live dispatch records are present for the current wave, both before the run has ever reached `CODE-IMPLEMENTATION` and after a `contract-amendment` has returned it to `SPEC-PLAN-DRAFTING`.
- [ ] A state failing any one conjunct of the repair-round verdict is admitted on all three edges with no reopen, except where that edge's existing guard refuses it on that guard's own terms.
- [ ] `gates-failed` and `findings-remain` evaluate the guard they already carry first, so a state failing both that guard and the repair-round verdict is refused with the existing guard's reason.
- [ ] `findings-remain --allow-retry-cap-override` waives the review retry cap alone, and is still refused while the repair-round verdict refuses.
- [ ] `wave-passed` and `gates-clean` are admitted, with their reasons unchanged, from the same `CODE-VERIFICATION` cohort state that the repair-round verdict refuses `gates-failed` from — the state that distinguishes discriminating on source state alone from discriminating on the source state and the event together.

### Controller-facing surfaces

Demoted out of this contract on 2026-09-23 by the owner, who holds the authority
to remove an accepted obligation. Three forms of the criterion — a count
equality, a fenced-block search, and an enumeration with conditional markers —
each failed because "this prose instructs a reader to fire this edge" is a
judgement no check decides. **Destination:** the plan's § Design (LLD) now owns
the documented procedure, and `plan.md` T4 produces it. **Pin:** a content test
under `packs/core/tests/pack/` asserts the prose the plan specifies, so its
removal reds a suite even though no criterion reads it.

### Proof

- [ ] `docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py` is unedited, and reports 35,728 states walked, 0 overlapping, 0 uncovered, and per-row reachability R1 17864, R2 13398, R3 3829, R4 49, R5 384, R6 108, R7 4, R8 92. That artifact transcribes the frozen spec's words and imports nothing from the implementation, so an unchanged report establishes that this delivery did not redefine what a record, a wave or a partition is — not that the shipped predicate is unchanged, which it cannot see.
- [ ] A committed oracle under this spec's `notes/` walks the repair-round verdict over a domain built by varying the axes that `wave-complete-dispatch-receipts` § Acceptance Criteria declares to be the single canonical enumeration, **extended with a superseded axis over each record varied by type and value as well as presence**, with container values generated from the declared key path rather than hand-built at a literal depth. It decides only what a transcription can decide alone: no state the shared reader refuses reaches the verdict; every refusal names at least one task whose stored record still accounts, read from the container rather than from the refusal condition; superseding every record clears every refusal and creates none; and both the refusing and passing sets are non-empty over the domain. The oracle does not compare the verdict against the conjunction it is transcribed from — that restates its own body and cannot fail — and the criterion below owns the falsifiable form of that comparison.
- [ ] That same oracle reports the row each state reaches in `_wave_exit_verdict`, and every state reaching R7 with live records reaches R8 instead once those records are superseded — the row movement the superseded clause causes, stated in the same scheme the criterion above uses.
- [ ] This spec's oracle transcribes the predicates from this contract's words and imports nothing from the implementation, as the frozen walk does and for the reason that walk states — a notes script under `docs/` does not import `_loop_guards`. The coupling to the shipped code is carried instead by an assertion under `tests/roster/`, which is where it has to live: it reads `docs/` and `packs/` together, and `tools/lint-pack-test-boundary.py` forbids a pack test from reading above its own pack. That assertion drives the transcribed rule and the shipped `accounts_for_task` and `unaccounted_wave_tasks` over every state in the oracle's domain and refuses any state they decide differently, in both directions.
- [ ] A mutation record in this spec's `notes/verification-ledger.md` names each new guard clause, each new verb clause, and the accounting predicate's superseded clause, together with the edit that removed it, the test that turned red, and the observed failure, with no clause whose removal left the suite green.

## Follow-ons

- eugenelim: `workspace.toml` `[backlog].open`, the entry on `docs/adr/0061-loop-infrastructure-phase-1.md` whose summary opens "Leave a durable trace when a wave exit passes" — unchanged by this spec and still open.
- eugenelim: **`wave-passed` is a fourth edge with this defect's shape, and needs its own register entry.** It fires before its cohort advance, so the run re-enters `CODE-IMPLEMENTATION` with the pointer unmoved and that wave's records live; a controller that does not then run `wave advance` can discharge the same wave's exit again. It is excluded here because the register entry this spec closes names three edges, because its guard is a separate § Ask first item in the frozen spec, and because the advance that follows it is what the fix has to reason about. Discovered by the round-2 spec review, 2026-09-23.
- eugenelim: `docs/architecture/loop-parallelism.md` § 1 — per-round dispatch history. A superseded record survives, but re-recording the same task replaces it, so an earlier round's assertion is still not recoverable once the task is re-recorded. § 1's unified transition history is where a durable per-round record would live; it is blocked on governance records that do not exist, and this spec does not depend on it.
- eugenelim: `workspace.toml` `[backlog].open` — repair work that lands in an already-passed wave carries no fresh assertion, because the reopen reaches only the wave at `current_wave_index`.

## Assumptions

- Technical: the controller runs the reopen before firing the edge — the guard reads cohort state as it stands before the transition, so a reopen run afterwards supersedes records the guard has already read. The guard enforces the ordering; it is recorded here because the documented procedure is what has to carry it.
- Technical: at each of the three source states, `current_wave_index` still addresses the wave whose tasks the repair round edits. True today because no edge between them moves the pointer; a future edge that did would need this contract revisited.
- Technical: an unsupported `schema_version` leaves receipts unenforced at the wave exit as well, by the frozen verdict's own second row, so passing that class here re-opens nothing — there is no enforced exit for a stale record to discharge. Recorded because a reader checking only this contract would read the pass as a gap.
