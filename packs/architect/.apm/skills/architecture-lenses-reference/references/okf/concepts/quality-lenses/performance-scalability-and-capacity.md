---
title: "Performance, scalability, and capacity"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - QL-P1
  - QL-P1b
---
# Performance, scalability, and capacity

## Scope and routing signals

Use when latency, throughput, concurrency, saturation, workload growth, or provider/resource limits drive a decision.

## Decisions and minimum evidence

Supports current optimization and future runway decisions. Minimum evidence names workload distribution, end-to-end target, critical path, resource utilization, queueing, concurrency/state constraints, capacity model, and representative measurements.

## Architectural questions

- Where does time or queue depth accumulate end to end?
- Which resource or serialized boundary saturates first?
- How does workload shape change under peaks, skew, retries, and growth?

## Mechanisms and trade-offs

Caching, batching, parallelism, partitioning, elasticity, backpressure, indexing, and resource sizing trade freshness, consistency, complexity, cost, and failure behavior.

## Evidence and counter-evidence

Seek traces, profiles, workload histograms, capacity/load tests, queue metrics, query plans, and current provider contracts. Counter-evidence includes averages hiding tails and synthetic workload mismatch.

## Failure modes and false positives

A large file or dependency count is not a bottleneck; low CPU does not imply spare capacity; microbenchmarks may not move user latency.

## Confirmation scenarios

Reproduce one representative and one peak/skewed workload, locate the limiting mechanism, vary it, and observe end-to-end outcome plus cost/reliability regressions.

## Related concepts and escalation

Pair with optimization, growth, transactional/event workloads, and cost. Ground provider limits at assessment time.

## Provenance and lifecycle

Synthesized from independent cloud performance-efficiency frameworks and ATAM scenarios. Confidence: high; review annually.

Research claim trace: `QL-P1`, `QL-P1b`; see the living source packet with the same concept path.
