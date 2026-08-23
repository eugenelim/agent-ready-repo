---
title: "Operational reality"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - OR-1
  - OR-1b
---
# Operational reality

## Scope and routing signals

Use when production load, service objectives, incidents, toil, recovery,
capacity, support, or deployment behavior could confirm or contradict repository claims.

## Decisions and minimum evidence

Supports assurance, optimization, and readiness decisions. Minimum evidence
names environment, time window, workload, user impact, operating owner, service
target, incidents, change behavior, and missing telemetry.

## Architectural questions

- What actually fails, saturates, pages, or requires manual intervention?
- Which recovery and scaling mechanisms have been exercised under relevant conditions?
- Are signals correlated across request, dependency, data, and deployment boundaries?

## Mechanisms and trade-offs

Use service objectives, incident review, traces, capacity records, recovery
exercises, and toil data. Operational access strengthens confidence but expands
sensitivity, cost, and authorization requirements.

## Evidence and counter-evidence

Seek telemetry, incident timelines, on-call records, deployment outcomes,
capacity plans, and restore tests. Counter-evidence includes short windows,
sampling loss, alert gaps, synthetic-only checks, and undocumented manual work.

## Failure modes and false positives

No incident does not prove resilience; high alert volume does not prove high user
impact. A dashboard's existence does not prove signals are actionable.

## Confirmation scenarios

Select one known failure and reconstruct detection, containment, recovery,
learning, and recurrence prevention across architecture boundaries.

## Related concepts and escalation

Pair with reliability, performance, operability, and delivery lenses. Deep mode
requires separate authorization for live operational surfaces.

## Provenance and lifecycle

Synthesized from AWS, Azure, and Google well-architected operational guidance.
Confidence: high; review annually because operational practices evolve.

Research claim trace: `OR-1`, `OR-1b`; see the living source packet with the same concept path.
