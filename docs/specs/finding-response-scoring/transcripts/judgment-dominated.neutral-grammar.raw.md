# Answer: judgment-dominated (neutral-grammar)

## F1
Accept. The specification already requires this outcome, so I would not add a
criterion. AC1 through AC4 require the over-length refusals at each public
seam, AC5 requires the bound before lookup, AC6 requires containment of a
lookup `OSError`, AC7 covers non-string input, and AC9 prohibits diagnostic
data in the result. The implementation must therefore add the common guard and
catch `OSError` at every listed resolving seam, returning `record-invalid` for
the payload seams and `unknown-timezone` for the review seams. This preserves
the published 255-character contract and prevents the filesystem error from
crossing the public boundary.

## F2
Accept. I would replace all seven Follow-ons code citations with stable,
symbol-based references and correct each cited function name to match the claim
it supports. A Follow-ons register is durable repository reasoning, so a stale
or mismatched anchor makes it misleading even though the work remains outside
this delivery's implementation scope.

## F3
Accept. I would replace each of the eight `cooling.py` line-number references
in `plan.md` with a stable file-and-symbol reference, adding the relevant local
condition where a symbol alone is not unique. Line numbers cannot meet the
plan's durability requirement because unrelated insertions detach them from the
code they were intended to identify.

## F4
Accept. I would correct the `_close_work()` Follow-ons entry to say that
`enrol` calls `_resolve_destination` before opening its `try` block and thus
does not contain that dependency failure. This is the accurate control-flow
statement and avoids claiming a protection the shipped code does not provide.

## F5
Accept. I would change the `_close_work()` Follow-ons entry from four to five
uncaught paths and explicitly include `_resolve_destination` itself. The
register must enumerate the complete known reach of the failure, because the
omitted path changes the follow-on's scope and priority.

## F6
Accept. I would add AC23: all code citations in this specification and its
`plan.md` use stable file-and-symbol references rather than line-only anchors;
the seven Follow-ons references and eight `cooling.py` plan references identify
the claimed current symbol and remain valid after unrelated line insertions.
This makes the citation-style correction verifiable, covers F2 through F5 as
well as the drift mechanism, and avoids relying on another manual repair after
the next insertion.

## Acceptance-criteria count after these decisions
25, from a starting count of 24.
