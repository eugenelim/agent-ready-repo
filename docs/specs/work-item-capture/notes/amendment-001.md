# Amendment 001 — widen T1 to reach the write-path refusal

**Authorised by:** eugenelim, 2026-09-20
**Against:** approved_plan_hash 271e96b0bb27f208

## What the criterion requires and what shipped

The criterion states that a submission naming a non-writable contract version
is **refused at the write path**, rather than validated under that version's
rules and emitted at the writable one.

T1 shipped the refusal at `select_validator(..., require_writable=True)`.
Nothing on the write path calls it. `validate_capture_request` — the function
`knowledge_store.py` invokes at both `_check_pre_admission` and
`_validate_event` — dispatches a v1 submission to the v1 validator and admits
it. Verified by reading the shipped function, not from the report.

So a producer submitting a legacy-version record can still write one today.
The criterion is not satisfied.

## Why T1 could not satisfy it

Enforcing the refusal inside `validate_capture_request` reds every fixture
that writes a legacy-version record through the real path. Those fixtures
live in `packs/core/tests/skills/project-knowledge/knowledge_test_support.py`,
which is in no task's `Touches:`. The implementer stopped at the boundary and
reported it rather than crossing it, which is the frozen plan working.

Scope measured, not estimated: exactly two files carry
`knowledge-captured-observation.v1` fixtures —
`packs/core/tests/skills/project-knowledge/test_contracts.py`, already in
T1's `Touches:`, and `knowledge_test_support.py`, which is not.

## The amendment

Add `packs/core/tests/skills/project-knowledge/knowledge_test_support.py` to
T1's `Touches:`. One file. T1 then wires the refusal into
`validate_capture_request` and migrates that module's fixtures to v2.

No criterion changes. No other task's boundary changes. T3 and T5 also touch
`test_contracts.py` but sit in later waves, so no same-wave collision is
introduced.

## Evidence the blast radius is measurable

The full `packs/core/tests/skills/project-knowledge/` suite passes today —
220 tests, 4m34s — so any breakage the wiring causes is attributable to this
amendment rather than to pre-existing state.
