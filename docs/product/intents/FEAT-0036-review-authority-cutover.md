# Review-authority cutover

- **Slug:** review-authority-cutover
- **Level:** feature
- **Owner:** Platform Core maintainer
- **Status:** Draft

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
