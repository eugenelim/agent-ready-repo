# Verification ledger — conventions-retirement

Execution observations. The spec and plan are frozen; this file carries what
execution measured and recorded.

## T0 — guard module, anchor resolver, canary

Built `tests/roster/test_conventions_retirement.py`. Four guards green, one
deliberately red.

- `test_scan_predicate_matches_its_approved_form` — green. Pins the scan's
  digest. A class-by-class canary cannot see an exclusion class added after it
  was written.
- `test_guard_invokes_the_scan_rather_than_restating_it` — green. The pathspec
  needle is assembled at runtime; a guard searching its own source for a literal
  it must contain always finds itself. Found and fixed during T0.
- `test_scan_reports_in_domain_and_excludes_historical_records` — green.
  Positive and negative control on the predicate.
- `test_resolver_accepts_a_heading_that_exists` — green. Positive control, so a
  resolver red because it crashes is distinguishable from one red because the
  work is undone.
- `test_every_recorded_anchor_use_resolves` — **RED, as required.** Every
  failure line reads "row records no destination heading", because
  `anchor-map.txt` leaves the heading column empty until an owning task writes
  back the heading it chose against the real destination.

Recorded red: `1 failed, 4 passed` on
`tests/roster/test_conventions_retirement.py`, failing node
`test_every_recorded_anchor_use_resolves`, expected failure identity
"unresolved anchor uses:" followed by one line per recorded use.

## T1 — seed AGENTS.md line cap

Measured rather than estimated, per the task's own test.

| Promoted block, as rendered today | Lines |
| --- | ---: |
| § Commits rule | 17 |
| The four pull-request questions | 10 |
| The never-commit and privacy rule (repo rendering) | 6 |
| § Documentation table | 13 |
| The four development-workflow bullets | 7 |
| The three coding-convention rules | 10 |
| **Added across T2-T7** | **63** |
| Removed by T8: the optional-guidance comment, seed lines 124-143 | 20 |
| **Net delta** | **+43** |

Seed is 144 lines today, so the projected final length is **187**.

`MAX_SEED_LINES` is raised from 150 to 200. That is 13 lines above the measured
projection, to absorb re-rendering: the procedure requires each promoted block
land "in that destination's own voice" rather than being pasted, so the rendered
length is not the source length. The margin is stated rather than hidden because
§ Boundaries makes raising the cap beyond what the relocated rules need an
ask-first action.

One correction worth recording, since it changed the number. A first measurement
counted `CONVENTIONS` § Privacy whole at 16 lines, but the promotion is of the
rule, which the repo renders in 6. A second counted the removal by matching the
first `<!--` in the seed, which is the `readability:exclude` block at line 15,
giving a nonsensical 128-line removal. Both were caught by reading the output
rather than trusting it.
