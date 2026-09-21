# T6 completion evidence

**Task:** the close-time rule branches for specific blocked work.
**Completed:** 2026-09-20. Amendment 004 followed from it.

## What shipped

- A four-row branch table in the work-loop skill's capture section, routing a
  note by what it is: generalisable practice keeps its existing route; a
  specific blocked item is captured; a specific ready-now item is dispatched
  in session; a specific item failing the razor is refused non-silently.
- The detail — what blocked means, what a capture must carry, what the razor
  checks — moved to a new reference rather than inflating the skill body.
- A test parsing both the shipped table and the spec's and asserting they
  agree, normalising only the internal decision-label citation that shipped
  pack prose may not carry.

## Verification

- Skill body length **read from the linter**, not from any figure in the
  spec or plan, because the file had changed since those were written: 965
  lines before, 979 after. Warning threshold 500, error threshold 1000 — no
  error-severity finding.
- Work-loop suite: 1230 passed, 5 skipped.

## What it got wrong, and what followed

It wrote its test into a directory another task owns, outside its own file
list, and flagged the crossing rather than hiding it. Crossing was the wrong
call — the boundary exists so plan defects surface — but the plan put it
there: its test section demanded a comparison and its file list named no
test location at all. Amendment 004 corrected that and audited every task
for the same shape.

## A regression it caused, found later

Widening the routing prose to the spec's four blockers broke a byte-pinned
clause belonging to `docs/specs/ride-along-admission-test/`, which freezes
the three-blocker wording across every site. Our change is correct and the
pin is stale; amendment 006 moves both pinned sites to the four-blocker
wording. Recorded here because it was this task's edit, found two tasks
later.
