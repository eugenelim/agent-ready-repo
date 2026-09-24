# Verification ledger — repair-round dispatch assertion

Execution observations. The spec and plan carry the contract; this file carries
what running the work established, in the order it was established.

## Mutation record

Method: edit the clause out of the source, run the suites, read the failure,
edit the clause back, and assert the file is byte-identical to what it was. No
`git checkout`, `git reset` or `git stash` at any point — the stash stack is
shared across worktrees.

Suites: `guards` = `packs/core/tests/skills/work-loop/test_loop_guards.py`;
`cli` = `packs/core/tests/skills/work-loop/test_loop_cohort.py`;
`parity` = `tests/roster/test_repair_round_predicate_parity.py`;
`oracle` = `notes/walk_reopen_partition.py`.

### T1 — the accounting clause and the repair-round verdict

Run 2026-09-24 against `_loop_guards.py`. Six clauses, six reds, none survived.

| # | Clause removed | Mutation applied | Suites that turned red |
| --- | --- | --- | --- |
| M1 | `accounts_for_task`'s superseded test | `return is_dispatch_record(value)` | guards, cli, parity |
| M2 | the `is True` strictness in that test | `not value.get(SUPERSEDED_KEY)` | **parity only** |
| M3 | `unaccounted_wave_tasks` calling the helper | reverted to `is_dispatch_record` | guards, cli, parity |
| M4 | the verdict's refusal branch | `if live:` → `if False:` | guards, cli, parity |
| M5 | the verdict's absent-container pass | made it refuse | guards, cli, parity |
| M6 | `wave-reopen` in `_SCHEMA_EXEMPT_PHASES` | removed from the frozenset | **cli only** |

Two of the six are caught by exactly one suite, and each justifies a design
choice that would otherwise look like surplus:

- **M2 is caught only by `parity`.** It needs a record carrying a *truthy
  non-`True`* `superseded` value, which exists only because the oracle's domain
  varies that member by type and value rather than by presence alone. Every
  example-based test in `guards` and `cli` uses `True` or omits the member, so
  all of them stay green while accounting silently turns on truthiness — and a
  record is data another process wrote.
- **M6 is caught only by `cli`.** `check_phase` refuses a non-exempt phase on a
  schema mismatch *before* the phase dispatch, so the verdict's own
  unsupported-schema row becomes unreachable through the verb while every test
  that calls the verdict function directly still passes.

`oracle` turned red for none of the six, which is correct rather than a gap: it
imports nothing from the implementation, by the norm
`wave-complete-dispatch-receipts`'s own walk states. Detecting a change to the
shipped predicate is `parity`'s job, and M1, M2, M3, M4 and M5 all turned it red.

## Observations

- **The frozen oracle cannot see this change, and its criterion says so.**
  `docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py`
  re-implements the accounting predicate locally rather than importing
  `_loop_guards`. Re-run 2026-09-24, unedited, and its report is unchanged:
  35,728 states, 0 overlapping, 0 uncovered, R1 17864 / R2 13398 / R3 3829 /
  R4 49 / R5 384 / R6 108 / R7 4 / R8 92. That establishes this delivery did not
  redefine a record, a wave or a partition. It establishes nothing about the
  shipped guard.
- **The repair-round oracle's first form could not fail.** It asserted
  `refuses == conjunction` where the conjunction was an inline restatement of
  the function's own body. Replaced before it was committed with properties that
  can fail: a read refusal never reaches the verdict; every refusal names a live
  record read from the container; superseding clears every refusal and creates
  none; only R7 moves at the wave exit, and it moves to R8; and both sides of
  the predicate are non-empty in the domain.
- **The oracle's transcription was wrong once, and the parity test found it.**
  The first version omitted the absent-container exemption that the shipped
  predicate carries inside itself, and 32 states disagreed. Fixed by moving the
  exemption inside the transcribed `unaccounted`, which is where the frozen
  spec's § Always do requires it to live.

### T2 — the reopen verb

Run 2026-09-24 against `plan_wave_reopen` in `loop-cohort.py`. Seven clauses,
seven reds, none survived.

| # | Clause removed | Mutation applied | Test(s) that turned red | Observed failure |
| --- | --- | --- | --- | --- |
| M1 | the usable-partition refusal | `if False:` in place of the `not isinstance(waves, list) or not waves` guard | `test_wave_reopen_refuses_a_malformed_partition[not-a-list]`, `[empty]` | `not-a-list`: exits 0 (silently reopens nothing, since no wave record keys under a string-keyed digest); `empty`: falls through to the pointer check and refuses with the WRONG reason (`current_wave_index=0 is not an index into schedule_waves (len=0)`) instead of naming `schedule_waves`/`unusable` |
| M2 | the malformed-container refusal | `if False:` in place of the `malformed is not None` guard | `test_wave_reopen_refuses_a_malformed_container` (all four depths) | `AttributeError: 'int' object has no attribute 'get'` — an unhandled crash, not a clean refusal, once the container's own hostile shape reaches the marking code unchecked |
| M3 | the pointer-type refusal | `if False:` in place of the `isinstance(index, str)` guard | `test_wave_reopen_refuses_a_pointer_not_an_index[string]`, `[float]`, `[bool]` | `TypeError: '>=' not supported between instances of 'str' and 'int'` — the reason string `non_negative_int` returns reaches the `>=` comparison unchecked |
| M4 | the pointer-range refusal | `if False:` in place of the `index >= len(waves)` guard | `test_wave_reopen_refuses_a_pointer_not_an_index[past-the-end]` | exits 0 instead of refusing — no wave-records key exists at the out-of-range index, so nothing to mark and no crash either |
| M5 | the marking assignment | `record[SUPERSEDED_KEY] = True` replaced with `pass` | `test_wave_reopen_marks_only_the_live_digest_and_current_wave`, `test_wave_reopen_then_wave_exit_refuses_and_names_tasks`, `test_wave_reopen_then_fresh_receipt_accounts_again` | exits 0 but no record gains `superseded`; a subsequent `check --phase wave-exit` still PASSES, because every record reads as live |
| M6 | the live-digest scoping (`container.get(digest, ...)`) | replaced with a loop over every digest in the container | `test_wave_reopen_marks_only_the_live_digest_and_current_wave` | a record under a stale, non-live partition digest was superseded too: `{'0': {'T1': {'kind': 'receipt', 'superseded': True}}}` where the fixture asserts it untouched |
| M7 | the current-wave-index scoping (`.get(str(index))`) | replaced with a loop over every wave index under the live digest | `test_wave_reopen_marks_only_the_live_digest_and_current_wave` | the sibling wave index's record was superseded too: `{'T3': {'kind': 'receipt', 'superseded': True}}` where the fixture asserts it untouched |

Each mutation was reverted immediately after its red was observed and the file
diffed byte-identical against its pre-mutation copy before the next mutation
began. No `git checkout`, `git reset` or `git stash` was used at any point.

M6 and M7 are the two halves of the criterion the multi-wave, multi-digest
fixture exists to catch: marking by digest alone (M6) or by wave index alone
(M7) instead of the `(digest, wave index)` pair together, per plan.md T2's own
call-out that this is "the only fixture shape that can catch" either defect.
