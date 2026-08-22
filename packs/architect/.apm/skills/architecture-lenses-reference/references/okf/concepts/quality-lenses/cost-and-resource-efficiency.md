---
title: "Cost and resource efficiency"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - QL-C1
  - QL-C1b
---
# Cost and resource efficiency

## Scope and routing signals

Use when spend, resource consumption, utilization, sustainability, or unit economics influences architecture or investment.

## Decisions and minimum evidence

Supports optimization, growth, and disposition decisions. Minimum evidence covers workload outcome, allocation, unit cost, fixed/variable drivers, idle/peak capacity, data/egress/licensing/people costs, forecast, and quality trade-offs.

## Architectural questions

- What outcome and tenant/capability consumes each major cost driver?
- Which cost is architectural, contractual, operational, or temporary migration overlap?
- What quality, risk, or optionality would a reduction trade away?

## Mechanisms and trade-offs

Rightsizing, autoscaling, scheduling, storage lifecycle, caching, batching, commitment, and platform sharing trade flexibility, performance, resilience, lock-in, and engineering effort.

## Evidence and counter-evidence

Seek bills/cost allocation, usage metrics, workload outcomes, contracts, capacity, and experiment results. Counter-evidence includes unallocated shared cost and temporary anomalies.

## Failure modes and false positives

High spend is not automatically waste; low utilization may buy resilience; cheaper unit price may increase total complexity or egress.

## Confirmation scenarios

Measure one unit of useful outcome end to end, vary the top driver, and compare total cost plus service, risk, and operational consequences.

## Related concepts and escalation

Pair with optimization, growth, provider/platform, and disposition. Current pricing must come from authorized authoritative sources.

## Provenance and lifecycle

Synthesized from independent cloud cost-efficiency pillars and portfolio guidance. Confidence: high; review annually and verify prices at use time.

Research claim trace: `QL-C1`, `QL-C1b`; see the living source packet with the same concept path.
