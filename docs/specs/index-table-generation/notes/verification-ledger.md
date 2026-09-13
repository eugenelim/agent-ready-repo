# Verification ledger — index-table-generation

Execution observations. The approved `spec.md` and `plan.md` hold obligations;
this file holds what running them produced.

## 2026-09-13 — T1 stub materialization and red

Materialized all four approved stub blocks from `plan.md ## Construction tests`
into `tests/roster/test_index_records.py` (7,000 bytes, 4 blocks). Observed red
before any implementation: `18 failed in 2.57s`.

After implementing `index-records.py`: `17 passed, 1 failed`.

## 2026-09-13 — an approved stub assertion is unsatisfiable (amendment AM-001)

**Observation.** `test_a_delimiter_bearing_title_renders_one_escaped_cell`
asserts `row.split("|")[2].strip() == "[Choose A \| B](0001-r.md)"`. The
generator emits the GFM-correct row:

```text
| 0001 | [Choose A \| B](0001-r.md) | Accepted | 2026-01-01 |
```

which renders as one cell reading `Choose A | B`. But an escaped `\|` still
contains a literal `|`, so `str.split("|")` cuts the title cell at index 2 and
yields `'[Choose A \'`. No implementation can both escape correctly and satisfy
the assertion: the defect is in the stub's parsing method, not in the
implementation or in AC6.

**Why the red proof did not catch it.** The PLAN-phase scratch validation proved
each case goes red, and that was recorded as the red being earned. A red-only
proof cannot separate "red because unimplemented" from "red because
unsatisfiable": the scratch `render` returned no rows, so this case red at
`assert rows` and never reached the escaping assertion. Round 4 of spec review
flagged this same assertion as unsatisfiable; the repair changed the parse from
a pipe count to a pipe split and carried the flaw forward. Third generation on
one line.

**Deviation from the task row's literal method.** `tdd-stubs.md` materializes an
approved stub unchanged. This stub is amended instead, under owner authority
given 2026-09-13.

**Remedy.** `row.split("|")[2]` becomes `row.split(" | ")[1]`. The escaped
sequence `\|` never contains the ` | ` delimiter, so the split is escape-safe.
No acceptance criterion changes; AC6's contract is untouched.

**Generalizable lesson.** A stub proven only red is proven only to fail. Where an
assertion's expected value is authored rather than observed, prove it can also go
green — against a scratch implementation that returns a plausible value, not one
that returns nothing.
