---
title: "Quality-attribute scenarios"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - QA-1
  - QA-2
  - QA-3
---
# Quality-attribute scenarios

## Scope and routing signals

Use when terms such as scalable, secure, reliable, maintainable, or fast need to
become testable architecture concerns.

## Decisions and minimum evidence

Supports prioritization and adequacy decisions. A minimum scenario names source,
stimulus, environment, affected artifact, expected response, and measurable
response target, plus the business consequence of missing it.

## Architectural questions

- Under what operating or failure condition must the response hold?
- Which mechanism produces the response and what other quality does it trade?
- What observation would demonstrate the target rather than intent alone?

## Mechanisms and trade-offs

Scenario workshops convert broad goals into comparable pressure tests. Precise
targets improve decisions but can overfit uncertain demand; retain assumptions
and ranges where the organization cannot justify a single number.

## Evidence and counter-evidence

Seek service objectives, load/fault tests, threat models, recovery exercises,
change data, support records, and user-impact evidence. Counter-evidence includes
untested targets, synthetic-only loads, and metrics detached from user outcomes.

## Failure modes and false positives

Framework pillar checklists do not replace scenarios. A mechanism may improve one
quality while damaging another; absence of a target is an elicitation gap, not
proof that current behavior is unacceptable.

## Confirmation scenarios

Select one architecturally significant scenario, trace its mechanisms and
sensitivity points, then identify the cheapest representative exercise.

## Related concepts and escalation

Pair with the relevant quality lens and trade-off analysis. Route detailed
security or operational verification to its specialist workflow.

## Provenance and lifecycle

Grounded in SEI ATAM and ISO architecture-evaluation concepts, triangulated with
well-architected workload guidance. Confidence: high; review annually.

Research claim trace: `QA-1`, `QA-2`, `QA-3`; see the living source packet with the same concept path.
