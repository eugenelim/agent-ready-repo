# Verification ledger — wave-exit-accounting-readout

Execution observations for this delivery. The spec and plan are hash-pinned;
this file is where evidence lands instead.

## AC-0014 — the reader-visible differential, through the installed CLI

Two fixtures, alike but for the record kind, under `.context/fx/` (gitignored).
Both waves `[["T1","T2"],["T3"]]`, pointer at 0, every task of wave 0 recorded.
Driven through `.claude/skills/work-loop/scripts/loop-cohort.py` after
`make build-self`, so this is the projected copy an adopter runs, not the source.

| Fixture | `dispatch_receipts_enforced` | `wave_dispatch_accounting[0]` |
| --- | --- | --- |
| every task a receipt | `True` | `{"tasks": 2, "receipts": 2, "declines": 0, "superseded": 0, "unaccounted": 0}` |
| every task a decline | `True` | `{"tasks": 2, "receipts": 0, "declines": 2, "superseded": 0, "unaccounted": 0}` |

The flag is identical across both arms — which is the defect as registered. The
new field separates them. The same two values came back byte-identical from the
source script before the build and from the projection after it.

`wave_dispatch_accounting[1]` reads
`{"tasks": 1, "receipts": 0, "declines": 0, "superseded": 0, "unaccounted": 1}`
in both arms: wave 1 was never reached. `current_wave_index: 0` in the same
payload is what separates that from a reached-and-unaccounted wave.

Both surfaces carry the key. The default surface prints
`wave_dispatch_accounting: [{'tasks': 2, 'receipts': 0, ...}]` for the declined
fixture; `--json` carries the same value.

## AC-0010 and AC-0011 — the disclosed asymmetry, measured

Same fixture with `schema_version: 99`:

- `loop-cohort status` — exit 1, `status: unsupported schema_version=99
  (expected 2); run 'loop-cohort reset' then 'loop-engine reset'`
- `loop-cohort check --phase wave-exit` — exit 0

The row the guard passes most permissively is the one cohort state offers no
reader for. Unchanged by this delivery and recorded as standing in ADR-0061's
2026-09-28 erratum.

## Mutation proof — T1, the summary helper

Both mutations applied by editing `_loop_guards.py` and reverted by editing it
back; never `git checkout`, `reset` or `stash`. After each revert the file was
confirmed byte-identical to a pre-mutation copy.

| Mutation (applied at the call site inside `wave_accounting_summary`) | Tests that redden |
| --- | --- |
| classify records on `kind` alone (`accounts_for_task` → `is_dispatch_record`) | `test_present_summaries_hold_the_arithmetic_invariant` (`assert ((2 + 0) + 1) == 2` — a superseded receipt counted as a receipt *and* as unaccounted) and `test_a_superseded_record_counts_as_superseded_and_unaccounted` |
| read `superseded` by truthiness rather than the declared `is not True` | `test_present_summaries_hold_the_arithmetic_invariant` and `test_a_non_true_superseded_value_stays_live`. The hand-written superseded case does **not** fire: a truthy read and `is not True` agree on `superseded: True`, so only a non-`True` value separates them |
| restored | 17 passed |

Both are the hazards the positional, predicate-based counting basis exists to
prevent. Detection is attributed per mutation above, measured rather than
assumed: the first is caught by a hand-written fixture as well as the walk, the
second only by the walk's invariant and by the case written specifically to pin
`is not True` with literal expected figures. Two earlier versions of this
paragraph were wrong — the first credited the generated domain alone, the second
credited the hand-written fixture for both.

## Mutation proof — T2, the status writer

`wave_dispatch_accounting` replaced with a constant `[]`. Result:
`test_status_tells_a_declined_wave_from_an_implemented_one` red —
`wave_dispatch_accounting does not distinguish them: {'receipt': [], 'decline': []}`.
Restored by editing back; 2 passed.

## Gate results

| Gate | Result |
| --- | --- |
| `make lint-ruff lint-mypy` | pass — "All checks passed!", "Success: no issues found in 149 source files" |
| `test_wave_accounting_walk.py` | 17 passed. The generator emits 2,520 tuples over five axes; deduplicated these are **207 distinct `(state, index)` pairs**, of which **75 yield a present summary** and **50 of those sit at a non-zero wave index**. All three figures are distinct-pair counts. Two earlier versions of this row were wrong: the first reported the raw tuple count as coverage, the second mixed tuple counts (336, 240) into a distinct-pair sentence and so claimed more present summaries than there were distinct states. |
| `test_loop_guards.py` | 163 passed |
| `test_loop_cohort.py` | 238 passed |
| `walk_verdict_partition.py` | unedited against `origin/main`; 35,728 states walked, 0 overlapping, 0 uncovered — identical to the baseline captured before any change |
| `make build-self` (FORCE=1) | three-copy parity confirmed by digest for `loop-cohort.py`, `_loop_guards.py`, `state-schema.md` and `evals.json` |

## Degradation recorded

T1, T3 and T4 were implemented by the controller rather than dispatched to an
`implementer` subagent, which was installed and available. T2 was dispatched.
Their dispatch receipts read `decline (human-directed)`, which is the closest
value in a closed set of two and is not an accurate description of what
happened; the accurate description is this paragraph.

## Post-review repairs, and the mutations that now fail

Two post-GATES reviews found that several walk assertions could not fail. Each
repair below is recorded with the mutation that previously survived and now
reddens. All mutations applied to a scratch copy or reverted by editing back;
the source was confirmed byte-identical afterwards.

| Previously survived | Now |
| --- | --- |
| `str(wave_index)` → `"0"` in the container walk — **252 tests stayed green**, so a wave's summary could be read out of wave 0's subtree | `test_a_summary_reads_its_own_wave_not_wave_zero` red. Wave 1 carries different task names and record kinds, so reading the wrong subtree reports the wrong figures |
| deleting `isinstance(waves, list)` from the precondition | `test_every_axis_value_reaches_the_outcome_it_forces` red, 8 failures. The schedule axis gained a non-`Sized` value (`5`); the previous `"not-a-list"` was `Sized` and the range check absorbed it |
| deleting an axis value such as `live-decline` from a generator | `test_the_generators_match_the_declared_axis_values` red. Expectations now come from a literal table, not from the generator being checked |
| rewriting `accounts_for_task` to a truthiness read of `superseded` | `test_a_non_true_superseded_value_stays_live` red. Its expected figures are literals, so it does not move with the predicate |
| deleting the `isinstance` guard in `cmd_status` | `test_status_wave_dispatch_accounting_shape` red. The non-list arm now drives `schedule_waves: "abc"`, present and not a list; an absent key defaulted to `[]` and hid the guard |

A sixth finding — that the record-coverage assertion credited an axis label
rather than evidence the record was read — is repaired by taking credit from the
subtree the generator actually built, and by placing the record at the wave's
first *distinct* task so a duplicated identifier cannot overwrite it.

The container walk is stated three times across `superseded_wave_tasks`,
`unaccounted_wave_tasks` and `wave_accounting_summary`. The third copy now has
the control the second one has: the non-zero-index case above fails if it
descends to the wrong key.

## Deletion sweep over the domain's axis values

The walk's coverage rule is only as good as its ability to notice a missing axis
value. Independently re-measured at `e2e8069c7`: each of the **23 declared axis
values** was deleted from its own generator in turn, one at a time, across
`_schedules`, `_containers`, `_waves_at_index`, `_records` and `_indices`.
**Zero survivors** — every deletion reddens, with
`test_the_generators_match_the_declared_axis_values` firing in all 23. Failure
counts vary by value rather than by axis: deleting `"list"` from `_schedules`
gives 6, `"unsized-non-list"` gives 2, `"out-of-range"` from `_indices` gives 2,
`"in-range-0"` and `"in-range-1"` give 3 each.

This is what the earlier arrangement could not do. Before the repair, three of
the five axes compared a generator against itself and the other two were driven
straight off the expectation table, so 16 of 22 values were deletable in
silence — and deleting `"unsized-non-list"` re-opened the
`isinstance(waves, list)` mutation it had been added to close.
