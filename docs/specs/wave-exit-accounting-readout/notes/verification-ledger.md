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

| Mutation | Result |
| --- | --- |
| classify records on `kind` alone (`accounts_for_task` → `is_dispatch_record`) | `test_present_summaries_hold_the_arithmetic_invariant` red: `assert ((2 + 0) + 1) == 2` — a superseded receipt counted as a receipt *and* as unaccounted |
| read `superseded` by truthiness rather than the declared `is not True` | same assertion red — `superseded: "yes"` is live, so a truthy read loses a live receipt |
| restored | 14 passed |

Both are the hazards the positional, predicate-based counting basis exists to
prevent, and both are caught by the generated domain rather than by a fixture
someone remembered to write.

## Mutation proof — T2, the status writer

`wave_dispatch_accounting` replaced with a constant `[]`. Result:
`test_status_tells_a_declined_wave_from_an_implemented_one` red —
`wave_dispatch_accounting does not distinguish them: {'receipt': [], 'decline': []}`.
Restored by editing back; 2 passed.

## Gate results

| Gate | Result |
| --- | --- |
| `make lint-ruff lint-mypy` | pass — "All checks passed!", "Success: no issues found in 149 source files" |
| `test_wave_accounting_walk.py` | 14 passed, 1,120 generated states |
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
