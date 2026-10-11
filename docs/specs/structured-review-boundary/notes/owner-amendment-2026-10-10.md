# Owner amendment decision — 2026-10-10

The scope owner chose to amend Slice 2 rather than perform the review-authority
cutover in this delivery.

## Question put to the owner

How should T7 (review-authority cutover and durable outputs) proceed?

## Owner answer

"Amend: ship boundary (Recommended)". This is the option the owner was shown:

> Owner-approved contract amendment: Slice 2 ships the structured boundary +
> compatibility with legacy review authority retained. AC-0010 is bounded to the
> review runtime and review-policy data (already proven by AST tests). The skill
> rewrite and engine switch become a named follow-on cutover slice. T7 =
> architecture, contracts registry, version bump, evals, changelog. Needs spec
> re-review and your re-approval; smallest risk.

## Evidence shown with the question

- VI-1013 parity: the closed Compatibility corpus, crash/replay, and
  authority-isolation fixtures pass against the active legacy path.
- No authority switch exists yet, so tested reversal evidence for a cutover
  does not exist.
- The literal AC-0010 and "Maintainer procedure" durable output would require
  removing reviewer-specific procedure from the canonical work-loop skill and
  its references, and switching the engine review gate to structured
  readiness.

## Effect

This record authorizes only the controlled `contract-amendment` transition and
the amendment of the protected spec sections it names. It approves neither the
amended spec nor the amended plan. Both human gates run again after
pre-EXECUTE review.
