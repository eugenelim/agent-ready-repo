# T2 completion evidence

**Task:** the `work_item` object and its per-shape required fields.
**Completed:** 2026-09-20. No amendment needed — the first task to run inside
its boundary unaided, because amendment 003 had already given it the shared
fixture module.

## What shipped

- `work_item` in both schema copies with the base required set and three
  shape-conditioned blocks, following the `if`/`then` precedent the schema
  already used for the git-blob digest rather than inventing a shape.
- `lesson` moved from unconditionally required to required only when the kind
  is not the work-item kind.
- A closed shape table plus `_validate_work_item`, wired into the request
  validator. `significance` is enum-checked at the field level.
- `work_item` added to the capture-id preimage.
- Shared fixture helpers for a valid work item, added to the module
  amendment 003 put in scope.

## Verification, checked by the controller

- Full `packs/core/tests/skills/project-knowledge/` suite: **283 passed, 0
  failed**, against a 270 baseline. Roster test passes. Contract parity exits
  0.
- **A real stored legacy record still reads** through
  `validate_capture_request`. Run every wave, because a 221-test green suite
  once hid exactly this regression.
- **The argv derivation still reproduces**: all 46 case rows through the
  shipped validator, 0 mismatches. T2 touched the same module, so this
  confirms it did not disturb T3's boundary.
- **The shared path helper is still unwidened** — `.ssh/id_rsa` admitted —
  so the committed store stays readable.

## Scope carried forward to T4, confirmed benign

T2 widened the kind vocabulary at the schema copies and the request
validator — two or three of the five capture-kind sites the plan assigns to
T4 — because without the value being accepted, every T2 admission test is
refused by the pre-existing kind gate and never reaches the new shape logic.
Vacuous tests are worse than a tidy boundary.

`knowledge_store.py`'s partition allowlist and kind enumerator are
**untouched**, verified: the string does not appear in that file. T4 still
owns them, still owns the five-site inventory check, and that check verifies
all five sites agree regardless of which task edited which — so nothing T4
must prove has been pre-empted.

## Carried forward

`_deterministic_privacy_scan` gained a one-line guard for an absent `lesson`,
needed for T2's own tests. The full six-field work-item scan remains T5's.
