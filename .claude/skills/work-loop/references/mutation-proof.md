# Mutation proof

A mutation proof shows that a test detects removal of one stated property.

## Proof record

Each proof states:

- **Invariant:** the property that must survive.
- **Catching test:** the test that must catch the property's removal.
- **Exact mutation:** the single change made to remove the property.
- **Expected failure:** the test and assertion expected to fail.
- **Observed failure:** the test and assertion that failed during the proof.
- **Placement:** Follow the [verification-ledger procedure](delivery-contract-lifecycle.md#verification-ledger).

## Mutation and restoration

A proof reverts to the pre-fix implementation, never a do-nothing stub.
A mutation that deletes a whole construct proves nothing about a sub-property.
Restore the implementation only by editing; never use `git checkout`, `git reset`, or `git stash`.
Removing a temporary mutation copy is cleanup, not implementation restoration.
A test that still passes under its mutation is not proof.
