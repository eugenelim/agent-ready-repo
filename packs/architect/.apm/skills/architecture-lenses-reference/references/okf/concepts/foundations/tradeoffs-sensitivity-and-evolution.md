---
title: "Trade-offs, sensitivity, and evolution"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - TS-1
  - TS-2
  - TS-3
---
# Trade-offs, sensitivity, and evolution

## Scope and routing signals

Use when a mechanism affects multiple quality attributes, when future scenarios
may cross a limit, or when a recommendation assumes one option is universally
better.

## Decisions and minimum evidence

Supports option comparison and staged-change decisions. Minimum evidence names
the competing scenarios, mechanism, benefits, costs, assumptions, sensitivity
point, trigger threshold, and reversible next step.

## Architectural questions

- Which parameter or dependency causes the architecture to change behavior?
- What benefit is purchased, and which cost or quality absorbs the trade?
- Can the decision be delayed safely until an observable trigger occurs?

## Mechanisms and trade-offs

Use scenario comparison, option tables, sensitivity points, and evolutionary
fitness signals. Premature flexibility adds complexity; irreversible choices
need stronger evidence and explicit escape paths.

## Evidence and counter-evidence

Seek measured limits, provider contracts, change history, experiments, and
option costs. Counter-evidence includes speculative scale, benchmark mismatch,
hidden migration cost, and an existing seam that makes replacement cheaper.

## Failure modes and false positives

Coupling is not automatically harmful; duplication may buy autonomy; a managed
service limit may be irrelevant to projected demand. Avoid scoring trade-offs
without stakeholder priorities.

## Confirmation scenarios

Vary the top workload, team, failure, and compliance assumptions and record the
point at which the preferred option changes.

## Related concepts and escalation

Pair with quality scenarios, decisions/constraints, growth readiness, and
transformation. Ground binding provider claims in current authoritative sources.

## Provenance and lifecycle

Synthesized from SEI ATAM, architecture options workshops, and cloud design-for-
change guidance. Confidence: high; review annually and when source frameworks change.

Research claim trace: `TS-1`, `TS-2`, `TS-3`; see the living source packet with the same concept path.
