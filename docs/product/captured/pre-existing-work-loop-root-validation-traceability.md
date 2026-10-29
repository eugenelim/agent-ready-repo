# Pre-existing: work-loop root validation fails on lint-traceability duplicate contract IDs

- **Status:** Open
- **Kind:** defect

## Summary

`tests/roster/test_work_loop_root_validation.py` fails 3 of 8 cases on a clean `origin/main` checkout at `c8d1d817a`, including `test_relative_root_unchanged`. Each case runs `lint-traceability.py --root`, which exits 1 with 8 hard `DUPLICATE ID` violations: `contract:adapter.schema`, `catalogue-index.schema`, `catalogue-manifest.schema`, `catalogue.schema`, `pack.schema`, `profile.schema`, `skill-manifest.schema` and `skill.schema` are each derived by two artifacts of kind `contract`.
