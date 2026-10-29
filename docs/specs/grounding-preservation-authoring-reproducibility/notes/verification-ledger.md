# Verification ledger: reproducible preservation authoring on the shared-graph case

## Dispatch, 2026-10-29

The owner (Platform Core) directed the controller to implement T1–T4 itself;
each task's dispatch receipt is recorded as `human-directed`.

## T1 — reference edits and content pins, 2026-10-29

- Red: the four new `RULES` phrases in
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`
  failed on the unedited reference (4 failed, 11 passed).
- Green: after Edits 1–3, `packs/core/tests/skills/new-spec/` and
  `packs/core/tests/skills/work-loop/test_preservation_evidence_reference.py`
  pass (297 passed, 82 subtests, 77 s).
