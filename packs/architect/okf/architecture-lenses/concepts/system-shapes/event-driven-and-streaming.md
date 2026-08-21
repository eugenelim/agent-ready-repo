---
title: "Event-driven and streaming systems"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SS-E1
  - SS-E1b
---
# Event-driven and streaming systems

## Scope and routing signals

Use when events, messages, streams, change data, queues, or asynchronous consumers are primary coordination mechanisms.

## Decisions and minimum evidence

Supports delivery semantics, state, replay, ordering, schema, and ownership decisions. Minimum evidence covers producer/consumer ownership, event semantics/schema, broker topology, partition/order, delivery guarantee, idempotency, retries/dead letters, replay, retention, backpressure, observability, and reconciliation.

## Architectural questions

- Is the event a fact, command, notification, or state transfer, and who owns its meaning?
- What happens on duplicate, missing, late, reordered, malformed, or poison messages?
- Can replay reproduce authorized side effects safely?

## Mechanisms and trade-offs

Queues, logs, pub/sub, outbox/inbox, idempotency keys, schema evolution, watermarks, dead letters, and backpressure trade decoupling/scalability against delayed consistency and operational complexity.

## Evidence and counter-evidence

Seek schemas, broker config, producers/consumers, offset/state stores, retry/dead-letter paths, replay tooling, traces, and incident evidence. Counter-evidence includes implicit payload contracts and unbounded retry.

## Failure modes and false positives

A queue does not guarantee decoupling or exactly-once effects; durable messages do not guarantee durable consumer state; dead letters can become silent data loss.

## Confirmation scenarios

Inject duplicate, delay, reorder, schema change, poison message, consumer crash after effect, replay, and broker unavailability; verify state and audit.

## Related concepts and escalation

Pair with background work, data integrity, reliability, interfaces, and distributed services.

## Provenance and lifecycle

Synthesized from cloud event-driven architecture guidance and reliability/data principles. Confidence: high; review annually.

Research claim trace: `SS-E1`, `SS-E1b`; see the living source packet with the same concept path.
