---
title: "Durable agent-run state and recovery"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-A2
  - WL-A2b
---
# Durable agent-run state and recovery

## Scope and routing signals

Use when an agent plans, acts, waits, delegates, streams, retries, resumes, or persists multi-step run state.

## Decisions and minimum evidence

Supports recovery without unauthorized or duplicate effects. Minimum evidence covers durable run/step states, atomic transitions, command/result records, leases/concurrency, idempotency, retry classification, deadlines/cancellation, provider acceptance uncertainty, approvals, version records, immutable history, and restart/resume.

## Architectural questions

- Which states and transitions are durable, atomic, and externally observable?
- What happens if the process dies after an action but before state persistence?
- Can redelivery, lease expiry, or concurrent workers repeat or widen authority?

## Mechanisms and trade-offs

State machines, transition guards, leases, idempotency keys, effect receipts, outbox/inbox, checkpoints, compensations, and immutable audit trade throughput, storage, latency, and design complexity.

## Evidence and counter-evidence

Seek state schemas, transition code, workers, leases, retries, cancellation propagation, effect records, approval state, audit history, and fault tests. Counter-evidence includes process-local memory and blanket retries.

## Failure modes and false positives

A durable queue does not make steps idempotent; provider timeout may occur after acceptance; resuming a model stream can repeat downstream actions.

## Confirmation scenarios

Terminate after external effect before persistence, redeliver, restart during streaming, cancel during action, expire lease under a live worker, and time out after provider acceptance; verify no duplicate or unauthorized effect.

## Related concepts and escalation

Pair with background work, tool authorization, model access, reliability, and data integrity.

## Provenance and lifecycle

Synthesized from agentic threat guidance, distributed reliability patterns, and cloud agent governance. Confidence: high; review at least annually.

Research claim trace: `WL-A2`, `WL-A2b`; see the living source packet with the same concept path.
