# Observed mutation results

`plan.md` is hash-pinned once `loop-cohort approve-plan` persists it, so the
observed red for each row of its mutation table is recorded here instead. One
row per guard, filled in during EXECUTE.

| Guard | Mutation applied | Observed result |
| --- | --- | --- |
| The schema's grammars equal the lifecycle record's | Changed one character in the receipt's `evidence_ref` pattern in `workspace-entry.schema.json`: `commit` became `commix`. | `FAILED tests/roster/test_dependency_scoped_completion_receipts.py::test_the_receipt_grammars_equal_the_lifecycle_records` with `AssertionError: assert '^(?:commix:[...|run:[0-9]+)$' == '^(?:commit:[...|run:[0-9]+)$'` (`1 failed in 0.81s`). Restoring `commix` to `commit` returned the full receipt suite to `26 passed in 0.75s`. |
