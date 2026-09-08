# Agent-skill consumers enforce provider-result boundaries

- **Status:** Draft
- **Level:** feature

## Outcome

The work-loop and architect-design consumers prove their provider-absence behavior, holding the selection, containment, and prose-gating boundaries that closed on 2026-09-08.

## Boundary

- Provider-absence validation for work-loop and architect-design, and any regression that would reopen the three controls closed on 2026-09-08.
- Provider implementation, provider discovery, provider contract changes, and unrelated agent-skill-engineering delivery remain outside this intent.

## Owner

- Agent-skill-engineering consumer-integration maintainers; no individual owner is recorded.

## Unresolved questions

- None recorded. Provider absence uses a pre-registered fixture and expected result judged by an independent reviewer, not a new executable harness.

## Projection

- One focused implementation specification for the provider-absence obligation, with the fixture and its expected result fixed before approval. The three closed controls need no projection; they need only to stay closed.

## Opportunity

This intent absorbs the four follow-ons the consumer-integrations slice registered. Three of them — `agent-skill-engineering-consumer-response-envelope`, `agent-skill-engineering-consumer-provider-ambiguity`, and `agent-skill-engineering-consumer-boundary-tests` — closed on 2026-09-08 by commits a895dd306, c4f641a43, and 0c89bb605: both consumer steps now delimit provider content in the `knowledge-evidence.v1` envelope, close all five candidate-eligibility failures before invocation including excess declared authority, and are gated by per-consumer boundary modules that `make ci` collects, each mutation-proven. Their dispositions are recorded in [`docs/specs/agent-skill-engineering-consumer-integrations/notes/consumer-security-review-closures.md`](../../specs/agent-skill-engineering-consumer-integrations/notes/consumer-security-review-closures.md).

`agent-skill-engineering-provider-absence-behaviour` remains open and is the whole of the live outcome. RFC-0097:189's behavioural half — "tested without this pack installed" — is not discharged: for a prose consumer there is no runtime to exercise, and `verify_catalogue` over a provider-less catalogue runs a strict subset of the provider-present checks. RFC-0097:575 offers a cheaper mode than an executable harness — a fixture versioned with its expected result before the implementation runs, judged by an independent reviewer — which that slice did not evaluate.

## Assumptions

- ADR-0097 keeps these controls on the consumer side.
- Provider absence is a behavioural obligation, not a security boundary; the security edge in this seam was candidate eligibility, and that control is closed.


## Source

- Mode: repo-origin
- Locator: docs/specs/agent-skill-engineering-consumer-integrations/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
