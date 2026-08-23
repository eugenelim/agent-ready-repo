---
title: "Delivery, runtime, and development patterns"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - DD-1
  - DD-1b
---
# Delivery, runtime, and development patterns

## Scope and routing signals

Use when build, test, release, environment, runtime, and developer-workflow structures determine change safety or operating cost.

## Decisions and minimum evidence

Supports evaluating path-to-production and environment/runtime alignment. Minimum evidence names source ownership, build unit, test gates, artifact identity, deployment unit, configuration, promotion, rollback, runtime owner, and feedback signals.

## Architectural questions

- Can one bounded change be built, verified, deployed, observed, and rolled back independently?
- Where do development and production topology diverge?
- Which manual or shared steps dominate lead time and risk?

## Mechanisms and trade-offs

Trunk or branch flows, pipelines, immutable artifacts, progressive delivery, environment parity, and developer platforms trade governance, speed, infrastructure cost, and cognitive load.

## Evidence and counter-evidence

Seek pipeline definitions, artifact metadata, environment configuration, deployment history, rollback evidence, test ownership, and developer feedback. Counter-evidence includes unused pipelines or manual out-of-band release.

## Failure modes and false positives

A large pipeline is not necessarily slow; many repositories do not imply independent deployability; local convenience does not prove production parity.

## Confirmation scenarios

Follow one representative change from edit through test, artifact, deployment, observation, and rollback, including a failed gate.

## Related concepts and escalation

Pair with testability/change safety, monorepo/platform shape, and operational reality. Escalate infrastructure reliability to operational review.

## Provenance and lifecycle

Synthesized from DORA delivery capabilities and independent well-architected operational guidance. Confidence: high; review annually.

Research claim trace: `DD-1`, `DD-1b`; see the living source packet with the same concept path.
