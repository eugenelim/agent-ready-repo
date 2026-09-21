# T5 completion evidence

**Task:** a refusal returns a code from the closed catalog, and the privacy
scan covers every free-text field.
**Completed:** 2026-09-20. Three criteria moved out by amendment 005.

## What shipped

- The scanned free-text set is **derived from the schema document at test
  time**, resolving each property's `$ref` — every field is a shared string
  definition, not an inline type — filtering to string-typed with no enum,
  and comparing that against production's tuple. Mechanism, not outcome: a
  schema walk against production, never a second hand list against the
  first.
- A companion test walks **every** `work_item` property, not only the
  string-typed ones, and asserts the partition is total: scanned, or
  excluded on a stated ground. That closes the array-of-free-text gap the
  spec names — a property added later as an array is excluded by
  "string-typed", reaches no scan, and the derived comparison still passes.
- The eleven reason codes added to the catalog, with the seven command codes
  derived from the generated case table rather than a second hand list.
- The per-element assertion is on **which scan function each element
  reached**, not on a refusal: most discriminating strings are refused by the
  argv rules before any scan runs, so a refusal assertion passes with the
  wrong scan wired.

## Verification, checked by the controller

- Full suite: **300 passed, 0 failed**, against a 288 baseline.
- **Both directions of the write/read split still hold** against the
  committed corpus — a real stored legacy record admitted at read, a legacy
  submission refused at write. Checked every wave.
- Argv derivation: 46 rows, **0 mismatches** through the shipped validator.
- Catalog is 26 codes; the scanned set is the six named fields.

## Mutation check the implementer ran

Removed one field from the scanned set and confirmed both the derivation
test and the per-field test went red, then restored. That discharges the
task's own "removing any one field turns the suite red" condition by
demonstration rather than assertion.

## Moved out

The instruction-shape refusal, the necessity razor and the shape threshold
all assert against a reasoning dispatch T5 cannot reach — it holds no
work-loop file and the dispatch is built in the next wave. Amendment 005
moves them to that task.
