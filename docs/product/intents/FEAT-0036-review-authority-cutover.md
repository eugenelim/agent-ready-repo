# Review-authority cutover

- **Slug:** review-authority-cutover
- **Level:** feature
- **Owner:** Platform Core maintainer
- **Status:** Withdrawn

## Disposition — withdrawn 2026-10-11, folded into Slice 4

**Do not shape this intent on its own.** The owner folded the review-gate switch
into Slice 4 of
[`acceptance-centered-work-loop`](../briefs/acceptance-centered-work-loop.md),
delivered by
[`execution-supervisor-review-gate`](../../specs/execution-supervisor-review-gate/spec.md) and [`execution-supervisor-cutover`](../../specs/execution-supervisor-cutover/spec.md).
[ADR-0144](../../adr/0144-work-loop-supervisor-owns-procedure.md) D8 records the
decision: review closure derives only from structured review readiness, every
reviewer role switches at once, and reviewer-specific procedure leaves the skill.
No execution evidence existed when it was withdrawn. Its two unresolved
questions are answered there: all roles switch together, and reversal is
reinstalling the prior Core release (ADR-0144 D7).

## Outcome

The work-loop review gate decides from structured review readiness (selected obligations, current typed reports, actual-failure assessments, and authorized dispositions) instead of the legacy raw-classify and adjudication path, after a fresh owner cutover approval and with a tested reversal path.

## Boundary

- Owns the engine review-gate switch, its owner cutover receipt, and its reversal path.
- Owns removing reviewer-specific procedure (reviewer-role conditions, adjudication grammar, retry caps, session mechanics) from the canonical work-loop skill and its owned references, with their pinned tests, projections, and evals.
- Preserves the legacy plan lock, task and cohort writer, procedure authority, and provider authority.
- Adds no agentbundle or other repository-package runtime dependency.
- Depends on the shipped structured review boundary and its compatibility adapter (docs/specs/structured-review-boundary/spec.md).

## Unresolved questions

- Which reversal evidence the owner will accept before approving the cutover.
- Whether the cutover moves every reviewer role at once or role by role.

## Projection

- Shape into one delivery spec under docs/product/briefs/acceptance-centered-work-loop.md when the owner schedules it; not queued.


## Source

- Mode: repo-origin
- Locator: docs/specs/structured-review-boundary/notes/owner-amendment-2026-10-10.md
- Revision: working-tree-2026-10-10
- Authority: repo-origin
