# Spec: A per-wave dispatch accounting readout

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061; ADR-0125 D2; `docs/specs/durable-transitions/spec.md` AC-0003
- **Brief:** none
- **Discovery:** none
- **Contract:** none — this changes a repository-owned CLI's read-only report, not a mapped `contracts/` protocol
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without a
> review round. A review finding against working material is advisory — it
> cannot block, because nothing gates the text it cites.

## Outcome

Someone reading a finished work-loop run can tell, wave by wave, whether its
tasks were implemented, declined, reopened, or never accounted for. Success is
that a wave whose every task was declined no longer reads identically to one
whose every task was implemented.

## What Changes

- A per-wave accounting summary — counts of live receipts, live declines,
  superseded records, and unaccounted tasks — derived from the declared
  accounting predicate, in `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`.
- A `wave_dispatch_accounting` key carrying one entry per scheduled wave, in
  `loop-cohort status`'s default and `--json` output. It sits beside the
  `current_wave_index` the payload already reports, which is what lets a reader
  separate a wave the run has not yet reached from one it reached and left
  unaccounted; the pointer is unchanged by this delivery and carries no
  criterion of its own.
- A generated-domain walk proving the summary's partition and invariants, in
  `packs/core/tests/skills/work-loop/test_wave_accounting_walk.py`.
- The field's meaning, the state classes it cannot read, and the fact that it
  reflects the live partition at read time, in
  `packs/core/.apm/skills/work-loop/references/state-schema.md`.
- A further erratum, dated 2026-09-28, recording that `pending_transition` now
  exists and that emitted state still cannot reach either tolerated wave-exit
  row, in `docs/adr/0061-loop-infrastructure-phase-1.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — two ADR-0061 errata rest on a prerequisite that has since shipped | `docs/adr/0061-loop-infrastructure-phase-1.md` | spec author | A further erratum, dated 2026-09-28, recording that `pending_transition` has shipped and stating per row what each tolerated wave-exit case does and does not gain | The erratum is present and identifies both occurrences of the superseded sentence |
| Current product truth | Applicable — the status payload gains a field an adopter reads | `packs/core/.apm/skills/work-loop/references/state-schema.md`, as prose inside the existing `dispatch_receipts` row | spec author | A sentence describing `wave_dispatch_accounting`, the inputs it reports no summary for, and its read-time partition scope | The prose matches the shipped payload and claims no `state.json` field |
| Release history | Applicable — a pack behaviour change | `docs/product/changelog.md` | spec author | An entry under the shipped core version | The entry names the new field |
| Interface compatibility | Applicable — an additive key on a published CLI report | `packs/core/tests/skills/work-loop/test_loop_cohort.py` | spec author | Tests asserting the field's presence, shape, and the decline/receipt differential | The tests run in the targeted suite |
| Interface compatibility | Applicable — the helper's partition and invariants need coverage no fixture list supplies | `packs/core/tests/skills/work-loop/test_wave_accounting_walk.py` | spec author | A generated-domain walk that proves its own record-class coverage | The walk runs in the targeted suite and its coverage assertion is present |
| Reusable learning | Not applicable — no new technique; the change reuses an existing declared predicate | — | — | — | — |

## Agent Rules

### Always do

- Derive `unaccounted` and `superseded` from the guard layer's declared
  accounting predicate rather than from an independent reading of the receipts
  container, so the readout and the wave-exit guard cannot disagree about which
  tasks a wave still owes.
- Count every reported figure once per position in the wave's task list, on the
  same basis the accounting predicate uses.
- Keep the summary total over any value cohort state can hold: no input raises,
  and a wave whose accounting cannot be read yields an explicit absent summary
  rather than zeroed counts.
- Rename `test_status_cannot_tell_a_declined_wave_from_an_implemented_one` to
  `test_status_tells_a_declined_wave_from_an_implemented_one` and extend it, in
  `packs/core/tests/skills/work-loop/test_loop_cohort.py` rather than writing a
  parallel test; the differential it pins is this defect's subject. It is the
  only test in that file this delivery modifies.

### Ask first

- Any change to `_wave_exit_verdict`, to `check --phase wave-exit`'s exit code,
  or to which states either tolerates.
- Any addition to the engine effect registry, which would require amending
  ADR-0125 D2 and the shipped `durable-transitions` AC-0003.
- Any relaxation of `loop-cohort status`'s refusal on an unsupported
  `schema_version`, which AC-0010 pins shut.

### Never do

- Make the unsupported-schema row or the absent-container row refuse. Both pass
  deliberately so a run already in flight when receipts shipped still reaches
  its wave boundary; making either refuse is a regression, not a fix.
- Write to cohort `state.json` from `check --phase wave-exit`. The phase is
  read-only and the pre-PR hook runs its sibling phase on every push.
- Migrate cohort state across the schema-version boundary in either direction.

## Testing Strategy

Coverage of the universal claims below is established by a **mechanism, not a
list**: a committed walk over a generated domain of cohort-state values, in
`packs/core/tests/skills/work-loop/test_wave_accounting_walk.py`. The domain is
generated from the declared receipt key path and the guard's own precondition
inputs, and the walk proves its own coverage. This is the canonical statement of
that coverage rule; the plan cites it rather than restating it.

Each generated **record** value must be *counted* in at least one present
summary — read through a mapping subtree and classified — not merely present in
a state whose summary is present, because a container that is empty, keyed to a
superseded digest, or not a mapping yields a present summary in which no record
is read at all. Each value of **every other axis** must appear in at least one
generated state, and, where it forces an absent summary, in at least one state
whose summary is absent. Both rules are per axis **value**, so an axis that
drops all but one value fails rather than shrinking the domain silently.

Coverage of predicate *combinations* is not coverage of predicate *branches*:
two record values can share an outcome while taking different arms, as a
string reason outside the closed set and an unhashable non-string reason do.
The record axis therefore carries one value per branch of each record
predicate, and the unhashable-reason value is what reaches the arm the guard
guards against raising on.

- **The accounting summary (AC-0002, AC-0004, AC-0005): TDD at the module
  surface, verified by the walk.** The walk asserts its domain is non-empty,
  that every generated state yields either a present summary or an absent one
  and never both, that both outcomes are reached, and that no state raises. On
  every present state it asserts the arithmetic invariant and agreement with the
  guard's outstanding count; on every absent state it asserts the guard reports
  nothing outstanding.
- **What that last pairing covers, and what it does not.** It fires when the
  helper treats a state as unreadable that the guard still reads — the helper
  reports absent while the guard returns outstanding tasks. It does **not** fire
  in the opposite direction: if the guard grows a precondition the helper does
  not, the helper calls the state present, the absent-state assertion never
  evaluates, and neither present-state assertion reddens, because `unaccounted`
  is derived from the guard's own predicate and the invariant survives. That
  direction is an accepted residual of this delivery, recorded here rather than
  claimed covered, and it is **unbounded**: this spec's Agent Rules govern only
  its own implementing change, a later delivery editing the accounting predicate
  answers to its own contract, and no standing test fails when both the guard and
  the helper share a new precondition.
- **Named cases beside the walk (AC-0001, AC-0003, AC-0006, AC-0007): TDD.** The
  walk proves the partition and the invariants; it does not prove any particular
  case reports the figures a reader expects. Separate cases pin an all-receipt
  wave, an all-decline wave, a superseded record, a duplicated identifier, an
  out-of-wave container key, a non-mapping container subtree, and a non-record
  value at one task key of a wave whose every other task holds a live record.
- **The status payload (AC-0008 through AC-0011): TDD at the CLI surface.** In
  `test_status_tells_a_declined_wave_from_an_implemented_one` — the renamed
  `test_status_cannot_tell_a_declined_wave_from_an_implemented_one` — the existing
  `dispatch_receipts_enforced` equality assertion is **retained** and a new
  inequality assertion on `wave_dispatch_accounting` is added beside it; the
  equality is what pins that field to container presence rather than to
  accounting, so replacing it would drop live regression cover.
  `test_status_refuses_the_oldest_state_the_wave_exit_tolerates` already drives
  both AC-0010 and AC-0011 and is not modified.
- **Guard non-disturbance (AC-0012): goal-based check.** The committed partition
  oracle is confirmed unedited against the base ref and re-run.
- **Published-copy parity (AC-0013): goal-based check.** `make build-self`'s
  three-copy parity check over the source and both projections.
- **Reader-visible outcome (AC-0014): visual / manual QA.** The real
  `loop-cohort status` CLI is driven against an all-declined fixture and an
  all-implemented fixture, and the two recorded outputs are compared.

## Acceptance Criteria

- [x] **AC-0001.** For each wave whose summary is present,
  `wave_dispatch_accounting` reports that wave's `tasks`, `receipts`,
  `declines`, `superseded`, and `unaccounted`.
- [x] **AC-0002.** A wave's summary is present exactly when the receipts
  container key is present in cohort state, `schedule_waves` is a list, the wave
  index is in range for it, and the wave at that index is a non-empty list of
  task identifiers; it is absent otherwise. A present summary is never zeroed
  counts standing in for an absent one.
- [x] **AC-0003.** Every reported figure is counted once per position in that
  wave's task list rather than once per key in the receipts container: a wave
  listing one task identifier twice reports `tasks: 2` for that wave, and a
  container key naming a task the wave does not list changes no reported figure.
- [x] **AC-0004.** `receipts + declines + unaccounted == tasks` for every present
  summary the committed walk generates.
- [x] **AC-0005.** `unaccounted` equals the number of the wave's task positions
  the guard layer reports as outstanding, for every present summary the
  committed walk generates.
- [x] **AC-0006.** A task whose record is marked superseded counts toward
  `superseded` and toward `unaccounted`, and toward neither `receipts` nor
  `declines`.
- [x] **AC-0007.** A receipts subtree that is not a mapping yields a present
  summary reporting every task in that wave as unaccounted, while a subtree that
  is a mapping holding a live record for every task position but one, whose
  remaining position holds a value that is not a dispatch record, leaves exactly
  that one task unaccounted.
- [x] **AC-0008.** `loop-cohort status` reports `wave_dispatch_accounting` in
  both its default and `--json` output, as a list whose length equals
  `len(schedule_waves)` when that value is a list, and `[]` otherwise.
- [x] **AC-0009.** Two states alike but for the record kind — one wave all live
  receipts, one wave all live declines — produce different
  `wave_dispatch_accounting` values, while `dispatch_receipts_enforced` stays
  equal for both.
- [x] **AC-0010.** `loop-cohort status` refuses a cohort state whose
  `schema_version` it does not support.
- [x] **AC-0011.** `check --phase wave-exit` passes a cohort state whose
  `schema_version` it does not support.
- [x] **AC-0012.** `docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py`
  is unedited against the base ref, and reports 35,728 states walked, 0
  overlapping, and 0 uncovered. The unedited clause is load-bearing: without it
  an implementer who changes the oracle supplies the comparison value the
  criterion is checked against.
- [x] **AC-0013.** The source, `.claude/`, and `.agents/` work-loop copies are
  byte-equivalent after `make build-self`.
- [x] **AC-0014.** Driven through the installed CLI against an all-declined and
  an all-implemented fixture, `loop-cohort status --json` returns
  `wave_dispatch_accounting` values a reader can tell apart without opening
  `state.json`.

## Follow-ons

- eugenelim: `docs/adr/0061-loop-infrastructure-phase-1.md` erratum — the
  residual differs by row and the erratum records it per row. The
  absent-container row gains a reader here, because `status` succeeds on that
  state and the readout distinguishes it from an accounted wave; what it still
  lacks is a trace of any past exit. The unsupported-schema row gains neither,
  because `status` refuses before building the payload.
- Plan width in `docs/architecture/loop-parallelism.md` § 3, the wave-decision
  contract in § 4, and any change to ADR-0061 D5 remain separate decisions.

## Assumptions

none
