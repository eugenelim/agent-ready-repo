# Finding-code review

## Reviewed addition

The task owner explicitly approved adding `invalid_completion_receipt` in the
accepted T2 contract. The code keeps malformed local completion receipts
separate from `invalid_receipt`, whose one emitter remains the
cross-repository receipt validator.

The refusal is dependency-scoped. Its path is the dependency target, its safe
action is to replace the receipt with a valid reviewed completion receipt, and
it never removes the citing entry during parsing.

## Frozen predecessor

`workspace-routing-invariants` requires explicit review before a finding code
is added. Its § Canonical findings table does not enumerate
`invalid_completion_receipt`. That directory is frozen: its spec is
`Shipped` and its plan is `Done`. The omission is deliberate, not missed;
the living finding tables in `workspace-status` and the adopter reference
carry the new public refusal.
