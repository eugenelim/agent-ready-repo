# New-spec positive case reproducibility

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/specs/grounding-preservation-review/notes/verification-ledger.md

## Summary

The frozen `new-spec` case `shared-substrate-change-expands-preservation-proof` held 6 of 6 once on Core 3.1.33 but scored 5, 4, and 5 of 6 on unchanged `new-spec` guidance in C3's graded runs: outputs omit that the consumer map is disposable, or leave bounded invalidation as a named gap instead of a criterion. Until it reproduces, the repository-grounding-preservation brief's C3 "integrated positive fixture" proof is unmet. Owner: Platform Core.
