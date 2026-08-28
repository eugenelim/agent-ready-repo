# Decision: the timezone bound is code-side only

**Question.** Does the timezone bound belong in
`contracts/jsonschema/delivery-lifecycle-record.schema.json` as well as in
`cooling.py`?

**Decision.** No. The bound is added to the code only. The published contract is
not touched, and its `x-spec` continues to name only
`docs/specs/thirty-day-cooling-and-retirement/`.

## Why the code-side bound is sufficient

The contract already declares the bound. At `97a0b6ad` the schema reads:

```json
"timezone": {"type": "string", "minLength": 1, "maxLength": 255}
```

So this is not a proposal to add a published constraint. It is the discovery
that the validator never enforced a constraint the contract has published since
Wave 5 shipped. `cooling.py` runs no JSON Schema validator — `validate_payload`
is a hand-written closed-shape check — so a declared bound only exists at
runtime if the hand-written check reproduces it. For `timezone` it did not.

Adding `maxLength: 255` to a schema that already says `maxLength: 255` is a
no-op. Changing it to any other number would be a published-contract change: it
would alter what a conforming producer may emit, and would require the `x-spec`
co-ownership the brief describes. Nothing here needs that. The correct repair is
to make the validator honour the number the contract already publishes.

This keeps the delivery off the published-contract path entirely. AC12 makes
that mechanical: the schema file's SHA-256 must still equal
`8bb85ebde713c3b9f6bdd4aeca8b50dfb8291608c731607a426517e7f474a6f3`, its value at
`97a0b6ad`.

## Why the bound alone is not the whole fix

A bound of 255 removes the `ENAMETOOLONG` shape on platforms whose `NAME_MAX` is
255, because every component of a key inside the bound is inside `NAME_MAX`. It
does not remove `OSError` as a class. The adjudicator made this point directly:
enforcing the bound "would have to be duplicated at three call sites and still
leaves other `OSError` shapes from the same call uncaught."

So the repair is both halves, and each is proven independently:

- The bound, proven by AC5, which counts calls to `ZoneInfo` and requires zero
  for a 256-character key — a bound that ran *after* the lookup would fail it.
- The `OSError` arm, proven by AC6, which forces `ZoneInfo` to raise
  `OSError(63, ...)` for a three-character key. AC6 cannot be satisfied by the
  bound, so the bound cannot make the arm vacuous.

## Keeping the two from drifting again

Wave 5's review found the schema and the validator diverging on both `locator`
and `timezone`, and nothing checked that they matched. AC8 and AC9 close that
for the numeric bounds by reading them out of the schema file and comparing them
to the module's constants, so a future edit to either side that is not mirrored
fails a test rather than shipping.

Two limits worth stating plainly:

- The parity check covers the numeric bounds only. The `locator` *pattern*
  divergence is real and is recorded as a follow-on: the contract's pattern
  rejects the C0 control range and `U+007F` which `_is_locator` admits, and
  `_is_locator` rejects a `.` segment which the pattern admits. Reconciling
  those changes behaviour, and the change needs a spec that decides which side
  is right.
- Parity is not conformance. Nothing here starts running a real JSON Schema
  validator against the payload; that would be a new dependency, which AC15
  forbids.
