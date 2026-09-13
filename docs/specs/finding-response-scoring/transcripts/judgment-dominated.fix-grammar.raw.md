# Answer: judgment-dominated (fix-grammar)

## F1
Repair the cooling implementation as specified: add the string and 255-code-point guard before every `ZoneInfo` call, and catch `OSError` at `validate_payload`, `compute_review_on`, and `is_due` so each returns its existing seam-specific refusal code. The specification already requires both controls through AC1–AC7, especially AC5's no-lookup proof and AC6's substituted-`OSError` proof, so it needs no new or changed criterion. The implementation change makes the published bound effective and prevents an errno or filesystem path from escaping an untrusted-input seam.

## F2
Repair the Follow-ons register. Replace all seven pre-change line anchors with current targets and correct the three function names that disagree with their surrounding prose. The register is durable technical context, so an anchor that points at the wrong place or names the wrong function defeats its purpose. This is a documentation correction only and does not change the delivery contract.

## F3
Repair `plan.md` by replacing each of its eight stale `cooling.py` line citations with a file-and-symbol citation to the intended code. A plan must let an implementer locate its evidence after unrelated insertions, and symbol citations preserve that link without creating another line-number maintenance obligation. This changes the plan, not an acceptance criterion.

## F4
Repair the `_close_work()` follow-on to say that `enrol` calls `_resolve_destination` before its `try` block and therefore does not wrap that dependency. The current statement is factually false about shipped control flow; the correction preserves the follow-on's risk assessment rather than changing the scope of this specification.

## F5
Repair the same `_close_work()` follow-on by adding `_resolve_destination` as the fifth uncaught path and changing the stated count from four to five. It is a reachable escape path of the dependency and must be recorded with the other four so a later owner does not under-scope the repair. This records a follow-on; it does not add current delivery work or a criterion.

## F6
Repair the specification's citation style throughout: replace line-number citations with file-and-symbol citations. This eliminates the repeated source of staleness while preserving the intended code references. Apply this to the Follow-ons corrections in F2, so the one style change resolves the individual stale anchors as well as preventing recurrence. No acceptance criterion changes because the cited follow-ons and assumptions remain the same obligations and observations.

## Acceptance-criteria count after these decisions
24, from a starting count of 24.
