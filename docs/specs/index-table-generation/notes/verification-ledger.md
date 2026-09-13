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

## 2026-09-13 — the consumer sweep undercounted; ADR-0112's Context is wrong

**Observation.** ADR-0112 states the spec index's "only two mechanical readers"
are `tools/test_guide_typed_asides.py` and the `close-work` roster test.
Execution found **five**:

| Reader | What it asserted |
| --- | --- |
| `tools/test_guide_typed_asides.py` | its own spec's row: status, AC/task counts |
| `tests/roster/test_close_work_extraction_and_immediate_disposition.py` | its own spec's row: status, Constrained by |
| `tests/roster/test_agent_skill_engineering_consumer_integrations.py` ×2 | AC14's verification, and a bare-slug over-count control |
| `tests/roster/test_rfc0099_fixture_register.py` | that its spec appears in the index |
| `tests/roster/test_tdd_stub_lifecycle_contract.py` | RFC-index row prose (`PLAN-contained`) |

**Why the sweep missed three.** All three name the file through a module
constant built from path segments — `ROOT / "docs" / "specs" / "README.md"` —
so a search for the literal `docs/specs/README.md` never reached them. A
filtered grep is not an exhaustive consumer list.

**Does the decision still hold?** Yes, and the corrected count strengthens it
rather than weakening it. Every one of the five asserted either its own spec's
row or hand-written index prose. None read the index to find something. The
finding that no instruction anywhere tells an agent to read the index is
unchanged, and remains the discriminator ADR-0112 rests on.

**Disposition.** ADR-0112 is Accepted and its body is frozen; `CONVENTIONS.md`
admits only a Status-line edit. The count is wrong in a Context sentence, not in
the Decision, the drivers, or the consequences, and no later reader is misled
about what was decided. Recorded here rather than corrected in place, and not
worth a superseding ADR. A future ADR touching this area should cite this entry
for the real number.

**Generalizable lesson.** When a sweep's conclusion is load-bearing for a
decision, search for the *symbol* as well as the literal: a path assembled from
segments, or bound to a constant, is invisible to a string search for the
assembled form.
