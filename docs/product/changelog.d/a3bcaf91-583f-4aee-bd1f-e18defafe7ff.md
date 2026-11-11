+++
schema = 1
id = "a3bcaf91-583f-4aee-bd1f-e18defafe7ff"
anchor = "core3130--2026-10-28-a3bcaf91583f4aeebd1fe18defafe7ff"
date = 2026-10-28
[[packages]]
name = "core"
version = "3.1.30"
+++
## Highlights
- The acceptance evaluator now has tests proving it can represent and decide the six preservation properties a shared-model change can disturb, with no schema change.

## Changed
- `packs/core/tests/skills/work-loop/test_preservation_contract_proof.py`: valid, rejected, and mutated preservation samples through the acceptance evaluator, plus pins for what the evaluator does not read. No skill or script changes.
