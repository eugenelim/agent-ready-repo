# Agent-skill consumers enforce provider-result boundaries

- **Status:** Draft
- **Level:** feature

## Outcome

The work-loop and architect-design consumers reject ineligible provider candidates before invocation, delimit returned provider content as untrusted evidence, gate their prose contracts, and prove their provider-absence behavior.

## Boundary

- Consumer-side selection, response containment, prose-boundary regression coverage, and provider-absence validation for work-loop and architect-design.
- Provider implementation, provider discovery, provider contract changes, and unrelated agent-skill-engineering delivery remain outside this intent.

## Owner

- Agent-skill-engineering consumer-integration maintainers; no individual owner is recorded.

## Unresolved questions

- None recorded. Provider absence uses a pre-registered fixture and expected result judged by an independent reviewer, not a new executable harness.

## Projection

- One focused security-boundary implementation specification covering both consumers and all four absorbed follow-ons, with the provider-absence fixture and expected result fixed before approval.

## Opportunity

This intent absorbs agent-skill-engineering-consumer-response-envelope, agent-skill-engineering-consumer-provider-ambiguity, agent-skill-engineering-consumer-boundary-tests, and agent-skill-engineering-provider-absence-behaviour. The shipped consumer steps do not yet delimit provider responses, enforce all five candidate-eligibility failures, protect their refusal and diagnostic prose with reached tests, or behaviorally prove the provider-absent path.

## Assumptions

- ADR-0097 keeps these controls on the consumer side.
- The authority-changing fixture makes candidate eligibility a security boundary and requires a security-design review in the projected specification.


## Source

- Mode: repo-origin
- Locator: docs/specs/agent-skill-engineering-consumer-integrations/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
