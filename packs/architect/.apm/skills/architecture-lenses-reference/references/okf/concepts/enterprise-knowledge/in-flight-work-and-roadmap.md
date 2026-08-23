---
title: "In-flight work and roadmap"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - RW-1
  - RW-1b
---
# In-flight work and roadmap

## Scope and routing signals

Use when active migrations, incidents, deprecations, platform changes, product
commitments, experiments, or funded roadmap work alter assessment priority.

## Decisions and minimum evidence

Supports sequencing and no-regret action decisions. Minimum evidence identifies
work owner, status, dependency, committed outcome, decision date, rollout/rollback,
evidence of progress, and uncertainty.

## Architectural questions

- Which current finding is already being contained or superseded?
- What changes the target boundary, platform contract, or evidence baseline soon?
- Which actions conflict, duplicate effort, or depend on an unproven milestone?

## Mechanisms and trade-offs

Use roadmap overlays, dependency maps, decision gates, and transition states.
Accounting for change avoids duplicate work but can defer urgent containment if
plans are mistaken for delivered controls.

## Evidence and counter-evidence

Seek approved plans, active changes, release evidence, migration state, and
owner updates. Counter-evidence includes stale roadmaps, unfunded intent,
blocked dependencies, and deployed work without adoption.

## Failure modes and false positives

Planned work is not current architecture. A merged change may not be deployed;
an announced migration may not reduce present risk.

## Confirmation scenarios

For one hot spot, compare current exposure, interim controls, delivery evidence,
target state, rollback, and the point at which assessment conclusions change.

## Related concepts and escalation

Pair with decisions/rationale, growth, transformation, and action-wave planning.
Escalate ownership or delivery ambiguity to the named program owner.

## Provenance and lifecycle

Synthesized from continuous-improvement, modernization-roadmap, and portfolio
guidance. Confidence: high for method; review annually.

Research claim trace: `RW-1`, `RW-1b`; see the living source packet with the same concept path.
