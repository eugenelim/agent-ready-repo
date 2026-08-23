---
title: "Reliability, resilience, and recovery"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - QL-R1
  - QL-R1b
---
# Reliability, resilience, and recovery

## Scope and routing signals

Use when failure tolerance, continuity, recovery, consistency during fault, or service commitments are architecturally significant.

## Decisions and minimum evidence

Supports adequacy and hardening decisions against named failure scenarios. Minimum evidence covers dependency failure modes, redundancy domains, timeouts, retries, idempotency, state durability, recovery objectives, restore/failover exercise, and residual single points.

## Architectural questions

- Which failures are isolated, propagated, retried, or recovered?
- What state or side effect can be lost, duplicated, or corrupted?
- Have recovery objectives been exercised under representative conditions?

## Mechanisms and trade-offs

Redundancy, queues, retries, circuit breakers, graceful degradation, backups, replication, and failover trade cost, consistency, complexity, latency, and recovery certainty.

## Evidence and counter-evidence

Seek failure-path code/configuration, dependency contracts, incident evidence, restore tests, fault injection, and service-level outcomes. Counter-evidence includes shared failure domains and untested automation.

## Failure modes and false positives

Retries can amplify outages and duplicate effects; backups do not prove restore; multi-zone labels do not prove independent state or control planes.

## Confirmation scenarios

Inject one dependency, process, zone, and state-recovery failure at a time; verify bounded impact, correct state, observability, and recovery objective.

## Related concepts and escalation

Pair with background work, distributed systems, data integrity, and operational reality. Escalate detailed failure engineering to operational review.

## Provenance and lifecycle

Synthesized from AWS, Azure, and Google reliability guidance plus scenario evaluation. Confidence: high; review annually.

Research claim trace: `QL-R1`, `QL-R1b`; see the living source packet with the same concept path.
