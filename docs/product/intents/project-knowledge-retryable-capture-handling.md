# Project-knowledge retryable capture handling

- **Slug:** `project-knowledge-retryable-capture-handling`
- **Level:** feature
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: capture instructions provide one visible identical-request retry only for retryable deadlines and an honest unsuccessful-retention fallback, proven by 660 project-knowledge tests and three seeded source replays.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Owner:** eugenelim


## Outcome

The project-knowledge skill exposes one visible caller retry when capture returns
both `reason_code=deadline_exceeded` and `retryable=true`. It resubmits the exact
same request and reports unsuccessful recovery without claiming retention.

## Boundary

- The project-knowledge skill’s capture instructions own recovery; work-loop and
  the CLI implementation are unchanged.
- One announced caller retry only. The CLI keeps zero internal automatic retries.
- Do not retry lock diagnostics, non-retryable refusals, or other reason codes.
- Preserve admission checks, request identity, privacy, confinement, storage, and
  diagnostic schemas. No fallback store.

## Owner

eugenelim, repository maintainer.


## Unresolved questions

None for this slice. Readiness selects the project-knowledge skill as caller,
one visible retry, and an explicit unsuccessful-retention fallback.

## Projection

Direct-light instruction and eval changes in project-knowledge. No integration
spec, work-loop capture behavior, or CLI retry implementation is required.

## Opportunity

The CLI preserves timeout diagnostics but does not retry internally. The skill
can consume the deadline/retryable pair while preserving that CLI contract.

## Assumptions

- The shipped deadline classification and bounded project-knowledge operations remain authoritative.
- This intent does not reactivate the separate external-capture-backend proposal.


## Source

- Mode: repo-origin
- Locator: docs/specs/ci-gate-parallelization/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Readiness

Decision 2026-11-05, narrowed on 2026-11-12 by the implementation brief: the
project-knowledge skill owns one user-visible retry for the deadline/retryable
pair only. Resubmit the exact request, including identity fields and timestamps.
A successful or replay receipt proves capture; a failed retry stops with the
observation not confirmed retained. A timeout alone cannot establish whether
the first attempt wrote, so do not assert definite absence.

**Proof:** transient-timeout, persistent-timeout, and non-deadline refusal evals,
plus section-bounded instruction pins and the existing project-knowledge suite.
Eval definitions are not proof of live instruction-following execution.

**Riskiest assumption:** a visible identical resubmission can recover a transient
deadline while replay identity prevents a duplicate. The store’s replay contract
remains authoritative; this slice does not extend recovery to lock failures.
