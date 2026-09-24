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
