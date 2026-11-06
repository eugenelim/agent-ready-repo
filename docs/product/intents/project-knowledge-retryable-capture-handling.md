# Project-knowledge retryable capture handling

- **Slug:** `project-knowledge-retryable-capture-handling`
- **Level:** feature
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Owner:** eugenelim


## Outcome

Workflows that consume project-knowledge capture diagnostics expose a bounded recovery path when a timeout returns `retryable=true`, without recasting the timeout as an invalid request.

## Boundary

- Caller behavior only; do not change project-knowledge storage, its diagnostic schema, or timeout classification.
- No silent, automatic, or unbounded retry loop; shaping must choose a retry budget and a user-visible fallback.
- Do not add an external store or weaken confinement, privacy, or malformed-input refusals.

## Owner

eugenelim, repository maintainer.


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

## Readiness

Decision 2026-11-05 (recommended default; the owner may overrule): the first caller is the project-knowledge skill and CLI instructions only, not work-loop. On `retryable=true` the caller retries once, tells the user, then reports the observation as not retained. No automatic loop, no storage or schema change. Route: direct-light, one session. Agent-only proof: an eval case with a seeded retryable diagnostic. Checked 2026-11-05: `retryable` is emitted in `knowledge_store.py` and `project_knowledge.py` and tested, and no caller reads it.

**Riskiest assumption:** a single bounded retry by the skill or CLI caller recovers a `retryable=true` timeout often enough to be worth the added path, without hiding a real failure. Tested agent-only by an eval case with a seeded retryable diagnostic and one with a seeded persistent failure that must report not retained after one retry.
