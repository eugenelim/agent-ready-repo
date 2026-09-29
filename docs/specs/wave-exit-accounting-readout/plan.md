# Plan: A per-wave dispatch accounting readout

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/core/.apm/skills/work-loop/references/state-schema.md`
  (the receipts data model and the two tolerated wave-exit classes);
  `unaccounted_breakdown` and `superseded_wave_tasks` in `_loop_guards.py` as the
  two existing derivations from the declared accounting predicate —
  `superseded_wave_tasks` covered by
  `tests/roster/test_repair_round_predicate_parity.py`'s
  `test_superseded_wave_tasks_is_a_subset_of_unaccounted`, and
  `unaccounted_breakdown` by its cross-consumer pin in
  `packs/core/tests/skills/work-loop/test_loop_cohort.py`; the named uncertainty is
  whether the absent-container row is reachable from any current writer, recorded
  under Risks.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/wave-exit-accounting-readout/notes/verification-ledger.md`.

## Approach

`unaccounted_wave_tasks` is THE accounting predicate, declared once so the
wave-exit guard and `wave advance` cannot disagree. Its two existing consumers
relate to it differently, and the difference matters here.
`unaccounted_breakdown` calls it and adds no walk of its own.
`superseded_wave_tasks` calls it *and* walks the container a second time, and its
docstring says so in terms — "a SECOND statement of the one in
`unaccounted_wave_tasks`, and that is a real seam" — with
`test_superseded_wave_tasks_is_a_subset_of_unaccounted` in
`tests/roster/test_repair_round_predicate_parity.py` as the control that catches
the two drifting apart.

This change adds a third derivation, and it opens a third instance of that seam
rather than avoiding one: separating `receipts` from `declines` means classifying
the record at each task key, which traverses the same two-key path. What is
different is the control. Where `superseded_wave_tasks` is covered by a subset
assertion over one property, the new walk ranges over a generated domain and
asserts, on every state it produces, both the arithmetic invariant and agreement
with the guard's outstanding count. A third walk that drifts from the predicate —
reading the wrong key, returning nothing, or disagreeing about which tasks are
live — reddens on some generated state rather than waiting for a hand-chosen
fixture to happen to cover it.

Every count is taken on the predicate's own basis: one pass over the wave's task
list by position, classifying the record at each task key through the same record
predicate the accounting predicate applies. `unaccounted` and `superseded` still
come from the declared helpers; `receipts` and `declines` are the live
complement, counted positionally. On that single basis
`receipts + declines + unaccounted == tasks` holds by construction rather than by
assertion, a wave listing one identifier twice counts it twice on both sides, and
a container key naming a task outside the wave is never reached.

Nothing new is emitted. Every number the readout prints is already in
`state.json`; what the run lacked was a surface that reads it. That is why this
route touches no transition, no effect registry, and no engine write authority.

**Assumption trio.**

- *Files touched:* `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`,
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`,
  `packs/core/.apm/skills/work-loop/references/state-schema.md`,
  `packs/core/tests/skills/work-loop/test_wave_accounting_walk.py` (new),
  `packs/core/tests/skills/work-loop/test_loop_cohort.py`,
  `packs/core/tests/skills/work-loop/test_loop_guards.py`,
  `docs/adr/0061-loop-infrastructure-phase-1.md`, `docs/product/changelog.md`,
  `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
  `packs/core/.apm/skills/work-loop/evals/evals.json`,
  `docs/specs/wave-exit-accounting-readout/notes/verification-ledger.md`, and the
  `.claude/` and `.agents/` projections `make build-self` regenerates.
- *Tests that demonstrate done:* a new generated-domain walk over the summary
  helper in `packs/core/tests/skills/work-loop/test_wave_accounting_walk.py`,
  with named cases beside it; the extended
  `test_status_tells_a_declined_wave_from_an_implemented_one`, which keeps
  its existing `dispatch_receipts_enforced` equality assertion and gains an
  inequality assertion on the new field; and the two export anchors in
  `test_loop_guards.py`.
- *Not changing:* `_wave_exit_verdict` and every row in it; `check --phase
  wave-exit`'s exit codes;
  `test_status_refuses_the_oldest_state_the_wave_exit_tolerates`, which already
  drives AC-0010 and AC-0011 as written; the effect registry; cohort
  `SCHEMA_VERSION`; the `state.json` on-disk shape.

**Tempted and declined.** Each line names the rung whose text decides it.

- A durable `wave_exit_verdict` field written at the wave exit — declined at
  rung 1 ("skip an addition that is not genuinely needed, and say so once"). The
  reader gap this spec closes needs no new stored field, because every figure it
  reports is already in `state.json`. Its infeasibility for an unsupported-schema
  state is a separate fact, recorded under Risks rather than used as the rung.
- Adding `wave-complete` to the engine effect registry — declined because an
  accepted governance record forbids it, not by a ladder rung: ADR-0125 D2 closes
  the eligible set and the shipped `durable-transitions` AC-0003 enumerates it.
- Relaxing `loop-cohort status`'s refusal on an unsupported `schema_version` so
  that class gains a partial reader — declined at rung 1. It needs no write
  authority and no registry change, so it was a live route; it is declined
  because reading an unsupported schema means reading fields whose shape that
  version does not specify, which is the breakage the wave-exit table's own
  schema row exists to prevent. AC-0010 pins the refusal.
- A dedicated human-readable renderer for the new field — declined at rung 1.
  `cmd_status`'s existing loop already prints every key, so the reader is already
  served and a second rendering path would be the only key not printed like its
  siblings.
- Reusing `unaccounted_breakdown` for the summary — declined at rung 2 (one
  bounded search for an adequate repository solution, then move on after a
  decisive result). It is an adequate solution for a different outcome: it
  returns a bounded prose fragment built for a refusal message, and counts parsed
  back out of prose would be a second predicate.

## Constraints

- ADR-0125 D2: the eligible set for engine-applied cohort effects is closed and
  enumerated. This change adds no member and takes no write authority.
- `durable-transitions` AC-0003 is shipped and unamended: every event outside
  the registry leaves cohort state byte-identical during the cohort-effect
  phase. This change writes no cohort state at all.
- `durable-transitions` AC-0016 obliges the two wave-exit rows to keep passing
  "with no overlap and no uncovered row introduced **if the verdict
  implementation is touched**". This plan does not touch it, so the conditional
  does not fire; AC-0012 re-runs the oracle anyway as non-disturbance evidence.

## Construction tests

Every task is TDD except T3 and T4, which are goal-based, and T5, which is
manual QA. The stub for T1 is recorded under that task.

## Durable-output map

| Role | Destination | Task |
| --- | --- | --- |
| Decision rationale | `docs/adr/0061-loop-infrastructure-phase-1.md` | T3 |
| Current product truth | `.../work-loop/references/state-schema.md` | T3 |
| Release history | `docs/product/changelog.md` | T4 |
| Interface compatibility | `.../tests/skills/work-loop/test_wave_accounting_walk.py` | T1 |
| Interface compatibility | `.../tests/skills/work-loop/test_loop_cohort.py` | T2 |

## Design (LLD)

### Design decisions

- **One counting basis, taken from the predicate.** Every figure is counted once
  per position in the wave's task list. `unaccounted` and `superseded` come from
  the declared helpers; `receipts` and `declines` are counted in one positional
  pass classifying the record at each task key. A key-based count over the
  container subtree would diverge from the predicate on two states the summary
  must still answer for — a wave listing an identifier twice, and a container key
  naming a task the wave does not list — and the arithmetic invariant would fail
  on a correct implementation. *Owned by:* T1.
- **The present/absent partition is stated once, in AC-0002, and this plan does
  not restate it.** An earlier draft carried the partition in three places and
  the copies drifted. What belongs here is only the consequence for the code: the
  helper evaluates those four conditions itself, because the guard's predicate
  returns the same empty result for a precondition violation and for a fully
  accounted wave and so cannot supply the distinction. That is a restatement of
  the guard's precondition block, recorded rather than claimed away.
  *Owned by:* T1.
- **The control for that restatement is the walk, not a row list.** For every
  state in the generated domain the walk asserts the summary is present or absent
  and never both, and that an absent summary coincides with the guard reporting
  nothing outstanding. A precondition the guard adds for an input nobody
  enumerated still lands inside the generated domain, so the drift reddens there
  rather than escaping a fixed table. An earlier draft asserted this over four
  hand-picked rows, which is exactly as wide as the enumeration it was meant to
  backstop. *Owned by:* T1.
- **The payload key is positional.** `wave_dispatch_accounting[i]` describes
  `schedule_waves[i]`, both printed in the same payload alongside
  `current_wave_index`, so a reader needs no key convention to line them up and
  can tell an unreached wave from a reached one. *Owned by:* T2.

### Data & schema

Cohort `state.json` is unchanged. The report gains one key:

```
wave_dispatch_accounting: list[dict | None]
  # len == len(schedule_waves) when that is a list, else []
  # element i describes schedule_waves[i]:
  {"tasks": int, "receipts": int, "declines": int,
   "superseded": int, "unaccounted": int}
  # or None when that wave's accounting cannot be read
```

### Interfaces & contracts

`loop-cohort status` and `loop-cohort status --json` gain the key additively.
No existing key changes name, type, or meaning.

### Component / module decomposition

The helper lives in `_loop_guards.py` beside its two sibling derivations and is
exported through `__all__`. `loop-cohort.py` re-binds it in both halves of the
existing guards-available / guards-unavailable import branch, matching every
other member of the receipts data model.

### Failure, edge cases & resilience

The helper is total over any value cohort state can hold and raises for no input.
AC-0002 owns which inputs yield a present summary and which yield an absent one;
this section adds only what is easy to misread from it. A receipts container that
is present but holds no subtree for the live partition — including the empty
container the initial state asset ships, and a container whose only digest key is
a superseded partition's — yields a **present** summary reporting every task
unaccounted, because the container key is present and the other three conditions
hold. It is not an absent summary.

## Tasks

### T1: the summary helper is total and agrees with the predicate

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/scripts/_loop_guards.py,
packs/core/tests/skills/work-loop/test_wave_accounting_walk.py,
packs/core/tests/skills/work-loop/test_loop_guards.py

**Tests:**
- The walk, in a new `test_wave_accounting_walk.py`: a domain whose axes are
  derived from the guard's own conjuncts and predicates rather than from an
  authored list of interesting cases. **`schedule_waves`:** a list and a
  non-list, so the `isinstance(waves, list)` conjunct is reached — the wave axis
  varies only the value at the index and cannot reach it. **Container:** absent,
  present-but-empty, keyed to a superseded digest, non-mapping, malformed at
  each level of the declared key path, and well-formed. **Wave** — one value per
  conjunct of `wave_is_well_formed`, which requires a list, non-empty, and every
  element a string: well-formed, non-list, empty, holding a non-string element,
  and holding a duplicated identifier. **Record** — values chosen to reach every
  branch of both record predicates: a live receipt and a live decline; a record
  carrying `superseded: True`, accepted as a record but not live; a record
  carrying a non-`True` `superseded` value, which stays live because the check
  is `is not True` rather than truthiness; a decline whose `reason` is a string
  outside the closed set; a decline whose `reason` is an unhashable non-string,
  which takes the `isinstance(reason, str)` arm the guard's docstring names as
  the raise hazard; and a value that is not a mapping at all. **Index:** in
  range and out of range.
- The walk's coverage assertions, exactly as the spec's Testing Strategy states
  them. That section is canonical for both rules — what each record value must
  reach, what each other axis value must reach, and that both are per value
  rather than per axis — and this plan adds nothing to it.
- The walk's partition and invariant assertions: the domain is non-empty, every
  generated state yields either a present summary or an absent one and never
  both, both outcomes are reached, no state raises, and on every present summary
  the arithmetic invariant holds and `unaccounted` agrees with the guard's
  outstanding count; on every absent summary the guard reports nothing
  outstanding (AC-0002, AC-0004, AC-0005).
- Named cases beside the walk, each pinning figures the walk does not: an
  all-receipt wave, an all-decline wave, a wave whose only record is superseded
  (AC-0006), a wave listing one identifier twice and a container key naming a
  task outside the wave (AC-0003), a non-mapping subtree and a non-record value
  at one task key of a wave whose every other task holds a live record
  (AC-0007), and the five reported keys (AC-0001).
- Stub (`stub: true`). It calls the **guard module**, not the loop-cohort
  module: `wave_accounting_summary` is declared in `_loop_guards.py`, and the
  `loop-cohort.py` re-bind belongs to T2, so a stub reaching through the CLI
  module would be red for T2's change rather than T1's. The new file loads the
  guard module by the same literal-component path anchor `test_loop_guards.py`
  documents for the pack-test boundary lint, and builds its own fixtures rather
  than importing `test_loop_cohort.py`'s module-level helpers, which are private
  to that module.

```python
def test_wave_accounting_summary_is_present_for_a_readable_wave() -> None:
    g = load_guards()
    waves = [["T1", "T2"]]
    decline = {"kind": g.DECLINE_KIND, "reason": g.DECLINE_REASONS[0]}
    state = {
        "schema_version": g.SCHEMA_VERSION,
        "schedule_waves": waves,
        "current_wave_index": 0,
        g.RECEIPTS_KEY: {
            g.partition_digest(waves): {"0": {"T1": dict(decline),
                                              "T2": dict(decline)}},
        },
    }
    assert g.wave_accounting_summary(state, 0) is not None
```

**Approach:**
- The walk asserts rather than prints, so a generator that produces nothing fails
  instead of reporting success vacuously. That failure mode is the reason the
  sibling oracle at
  `docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py`
  exists in the shape it does; this walk differs by living in the test suite and
  calling the shipped helper, because its subject is the helper's behaviour
  rather than a transcription of spec wording.
- Two anchors in `test_loop_guards.py` move with the export: the exact
  `set(g.__all__)` equality, and the companion name list whose AST check forbids
  `loop-cohort.py` from declaring any listed name a second time. That check is
  silent when a name is absent from the CLI entirely — `superseded_wave_tasks` is
  in both the export set and the name list yet bound in neither half of the
  import branch — so it constrains the form of a binding, not its presence. The
  new helper is re-bound anyway because `cmd_status` calls it; the re-bind and
  the unavailable-branch placeholder both satisfy the check.

**Done when:** the walk and the named cases are green, both `test_loop_guards.py`
anchors pass with the new name, and `make lint-ruff lint-mypy` passes.

### T2: status reports the readout and tells a decline from a receipt

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py,
packs/core/tests/skills/work-loop/test_loop_cohort.py

**Tests:**
- `test_status_cannot_tell_a_declined_wave_from_an_implemented_one`, renamed to
  `test_status_tells_a_declined_wave_from_an_implemented_one` and extended:
  its existing `dispatch_receipts_enforced` equality assertion is retained, and a
  new assertion requires `wave_dispatch_accounting` to differ across the two arms
  (AC-0009). The test is renamed to
  `test_status_tells_a_declined_wave_from_an_implemented_one`, the name the spec's
  Agent Rules and Testing Strategy already carry.
- Payload shape: length equals `len(schedule_waves)`, and `[]` for a non-list, on
  both the default and `--json` surfaces (AC-0008).

**Approach:**
- The key is appended to `cmd_status`'s `result` dict after
  `dispatch_receipts_enforced`, so the two receipts-derived fields read together.

**Done when:** the extended tests are green and a mutation that breaks the
writer — editing the summary to return a constant — turns the differential test
red.

### T3: the reader-facing records say what the field means and what it cannot reach

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/references/state-schema.md,
docs/adr/0061-loop-infrastructure-phase-1.md

**Tests:** no stub (goal-based). T3's `Done when` below is the whole of its
verification. `lint-spec-status.py` covers `docs/specs/*/spec.md` only and its
dangling-reference invariant is warn-only, so it reads neither destination.
`lint-adr-shape.py` does read `docs/adr` — `tests/roster/test_lint_adr_shape_corpus.py`
runs it over the real corpus as a named CI step — but it asserts that each record
is readable, refused, or unreadable, not what any erratum says, so it cannot
grade this erratum's content either.

**Approach:**
- The erratum identifies the superseded sentence by quotation rather than
  editing the 2026-09-24 erratum body, matching how that erratum handled its own
  predecessor.
- `state-schema.md` is shipped pack content, so it states each rule directly and
  cites no ADR, spec, or acceptance criterion.

**Done when:** `state-schema.md` describes `wave_dispatch_accounting` as prose
inside the existing `dispatch_receipts` row — the placement its sibling report
key `dispatch_receipts_enforced` already uses, because every table in that
document is scoped to a persisted file's fields and this is a report key, not a
`state.json` field — and that prose (a) names the inputs the field reports no
summary for, and (b) states that the value
reflects the live partition at read time and is not a record of what any past
exit saw — because `schedule` keeps only the live partition digest's records, so
a run whose partition changed reports its earlier waves as unaccounted; and
ADR-0061 carries a further erratum, dated 2026-09-28, recording that
`pending_transition` has since shipped and stating per row what each tolerated
wave-exit case does and does not gain. The claim it supersedes is asserted twice
in that ADR — in the 2026-08-31 erratum and again in the 2026-09-24 one — and the
new erratum identifies both occurrences, because a reader landing at either
would otherwise take a false fact as current. ADR-0061 already carries three
errata, so this one is identified by its date and those two sentences rather than
by an ordinal.

### T4: the release surface and the projections agree

**Depends on:** T3

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json,
docs/product/changelog.md, packs/core/.apm/skills/work-loop/evals/evals.json

**Tests:** no stub (goal-based).

**Done when:** `make build-self` reports three-copy parity (AC-0013), the two
version files agree on a version derived from a fresh `git fetch origin`,
`docs/product/changelog.md` carries its entry, and the partition oracle
satisfies AC-0012, which owns both the unedited clause and the three numbers.

### T5: a reader can tell the two runs apart through the real CLI

**Depends on:** T4

**Touches:** docs/specs/wave-exit-accounting-readout/notes/verification-ledger.md

**Tests:** no stub (manual QA).

**Done when:** the installed `loop-cohort status --json` has been driven against
an all-declined and an all-implemented fixture and both outputs are recorded in
the verification ledger with the differing values quoted (AC-0014).

## Rollout

Additive. A consumer that does not read the new key is unaffected; no cohort
state is rewritten, so no run in flight changes behaviour.

## Risks

- **The absent-container row may be unreachable from any current writer.**
  `assets/state.json` ships `"dispatch_receipts": {}`, `cmd_init` copies the
  template unchanged, and `schedule` restores the container. Cohort schema 2
  postdates receipts, so a schema-2 state lacking the container has no producer.
  The row stays as found — this plan does not touch the verdict table — but the
  readout must not assume the row is dead.
- **No durable trace is reachable for the unsupported-schema row.** Every cohort
  mutation verb refuses that state, and migration is forbidden in both
  directions, so no marker can be written into it and `status` cannot read it.
  That is why this delivery closes the reader gap and records the residual rather
  than emitting state; T3's erratum is where the residual lands.
- **The extended differential test gains an assertion rather than replacing one.**
  Replacing the existing equality would drop the pin that ties
  `dispatch_receipts_enforced` to container presence. T2's mutation proof covers
  the new assertion: with the writer broken the test must be red.

## Changelog

- 2026-09-28 — Drafted.
- 2026-09-28 — Spec approved by eugenelim.
- 2026-09-28 — Plan approved by eugenelim.
- 2026-09-29 — Shipped.
