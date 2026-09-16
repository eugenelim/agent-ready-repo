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

## A test that cannot fail

A passing test is evidence only if the property it names is what produced the
pass. Reading a suite does not reveal one that cannot fail; mutating the subject
does.

Four shapes recur:

- **An unreachable path.** The fixture cannot produce the finding the assertion
  denies, so the denial holds under every implementation. A row-count case
  stating its count as "both rows" -- a phrase the rule cannot read -- compared
  no count at all, and its silence looked like agreement.
- **An absence something else guarantees.** The asserted string cannot appear
  whatever the subject prints, because a layer in between removes it. A test
  harness that decodes with universal newlines makes an assertion about a
  carriage return unfalsifiable.
- **Two sufficient mechanisms.** Either alone upholds the property, so no single
  mutation changes an outcome and the test pins neither one. Cut one and the
  survivor becomes catchable.
- **A message from a different rule.** The assertion names a string the code
  under test never emits, so it survives the mutation it was written to catch.

Ask one question per assertion: what single mutation reds it? Where no mutation
can be named, run one and watch. An assertion that survives every mutation of
the property it names is documentation, not a test.
