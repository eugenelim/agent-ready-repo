---
title: "Background, batch, and scheduled work"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-B1
  - WL-B1b
---
# Background, batch, and scheduled work

## Scope and routing signals

Use when jobs, workers, schedulers, executors, callbacks, recovery loops, or long-running tasks operate outside the initiating request.

## Decisions and minimum evidence

Supports identity, durability, retry, recovery, and side-effect decisions. Minimum evidence covers job creation context, durable command/state, queue/schedule, worker identity, lease/concurrency, idempotency, retries, deadlines/cancellation, progress, expected row/effect counts, recovery, audit, and dead-letter handling.

## Architectural questions

- Which tenant, actor/service principal, run/job, privilege, and trace context is captured immutably?
- What happens on crash after effect but before progress persistence?
- How are duplicate delivery, stale leases, cancellation, and poison work handled?

## Mechanisms and trade-offs

Durable queues, job state machines, leases, idempotency keys, bounded retry, checkpoints, compensations, and recovery workers trade throughput, latency, storage, and implementation complexity.

## Evidence and counter-evidence

Seek every background entry mechanism, job schemas, context propagation, worker/session factories, state transitions, retry policy, recovery logic, and fault tests. Counter-evidence includes process-local threads and singleton context.

## Failure modes and false positives

Scanning only scheduler registrations misses threads, executors, callbacks, and startup workers. A zero-row write may be a silent context failure, not success.

## Confirmation scenarios

Kill the worker after an external effect, redeliver, expire a lease, restart, disable the originating user, cancel mid-step, and verify no unauthorized or duplicate effect.

## Related concepts and escalation

Pair with reliability, data integrity, hardening, event-driven systems, and durable agent-run state when applicable.

## Provenance and lifecycle

Synthesized from distributed reliability patterns, operational guidance, and the motivating invariant audit. Confidence: high; review annually.

Research claim trace: `WL-B1`, `WL-B1b`; see the living source packet with the same concept path.
