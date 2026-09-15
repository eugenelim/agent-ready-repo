# Spec-mode confirming review — findings round

Revision reviewed: 5e390f5f3. Result: Findings (1 Major, 1 Minor, no Blocker).

1. Major — AC-0022's successor map under-named AC-0003 for the predecessor's
   AC-0002. That criterion is a band claim, not only a count claim: the drop
   falsifies "exactly two", and the clamp independently falsifies "at most 480
   CSS pixels" under a 480 minimum with nothing dropped. None of AC-0022's three
   roster tests can catch an under-complete map.
2. Minor — two pieces of draft narration in plan.md: a superseded round-5 premise
   recorded as current material in T4, and a stale round count in the changelog
   preamble.

Disposition: both repaired at 43516f986, plus the reviewer's implementation
constraint that the section 5a row stays a declared-breakpoint example.
