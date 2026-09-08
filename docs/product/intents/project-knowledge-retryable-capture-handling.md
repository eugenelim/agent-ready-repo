# Project-knowledge retryable capture handling

- **Status:** Draft


## Outcome

Workflows that consume project-knowledge capture diagnostics expose a bounded recovery path when a timeout returns `retryable=true`, without recasting the timeout as an invalid request.

## Boundary

- Caller behavior only; do not change project-knowledge storage, its diagnostic schema, or timeout classification.
- No silent, automatic, or unbounded retry loop; shaping must choose a retry budget and a user-visible fallback.
- Do not add an external store or weaken confinement, privacy, or malformed-input refusals.

## Owner

Not yet assigned

## Unresolved questions

- Which caller owns the first retry-handling implementation: work-loop, the project-knowledge CLI, or both?
- Should recovery be user-invoked or automatic within a fixed retry budget?

## Projection

- Shape one focused work-loop/project-knowledge integration spec after an owner and retry budget are chosen.

## Opportunity

The timeout fix now emits an honest retryable diagnostic, but no caller consumes that field, so recovery metadata does not yet change workflow behavior.

## Assumptions

- The shipped deadline classification and bounded project-knowledge operations remain authoritative.
- This intent does not reactivate the separate external-capture-backend proposal.


## Source

- Mode: repo-origin
- Locator: docs/specs/ci-gate-parallelization/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
