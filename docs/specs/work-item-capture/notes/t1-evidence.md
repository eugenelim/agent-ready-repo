# T1 completion evidence

**Task:** v2 schema exists and a record is validated by the version it names.
**Completed:** 2026-09-20. Amended twice during execution (001, 002).

## What shipped

- The capture payload version is `knowledge-captured-observation.v2` in the
  canonical schema and the packaged mirror, byte-identical —
  `check_contract_parity.py` exits 0, "18 contract file(s) synced".
- `CAPTURE_VALIDATORS` maps each known version to its validator, with **no
  default and no fallback**, and `select_validator` dispatches on a record's
  own version field. An unknown version and an absent one are both refused;
  a record with no `request` object returns `None` and never reaches capture
  version selection.
- `select_validator(..., require_writable=True)` refuses a non-writable
  version. Binding that to the write path is T4's, per amendment 002.
- `validate_capture_request` is deliberately **version-agnostic**: the store
  calls it from the read path too, and requiring writability there refused
  every stored legacy record.

## Verification

- `packs/core/tests/skills/project-knowledge/test_contracts.py` and
  `tests/roster/test_project_knowledge_capture_contract.py`: 16 passed.
- Full `packs/core/tests/skills/project-knowledge/` suite: **220 passed**,
  4m37s.
- Red-before-green confirmed: the new tests were run against the pre-T1
  validator and failed.
- **Checked against real data, not the suite:** a stored v1 payload taken
  from `docs/knowledge/**/*.jsonl` reads clean through
  `validate_capture_request`. This is the check that caught the read-path
  regression a 221-test green suite did not.

## Known gap, owned elsewhere

The write path does not yet refuse a non-writable version. That moved to T4
with amendment 002, because the one function serves both read and write call
sites in a module T1 may not edit.
