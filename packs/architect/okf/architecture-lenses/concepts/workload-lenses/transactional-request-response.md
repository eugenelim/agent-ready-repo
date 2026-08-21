---
title: "Transactional request/response workloads"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-T1
  - WL-T1b
---
# Transactional request/response workloads

## Scope and routing signals

Use when synchronous requests, commands, APIs, UI actions, or transactions expect a bounded immediate response.

## Decisions and minimum evidence

Supports boundary, transaction, latency, consistency, and failure decisions. Minimum evidence covers entry/auth, validation, application decision, state transaction, external effects, timeout/cancellation, idempotency, response/error contract, observability, and retries by callers.

## Architectural questions

- Where is the authoritative transaction boundary and what lies outside it?
- What occurs if a dependency accepts work but the caller times out?
- How are identity, tenant, policy, and trace context preserved end to end?

## Mechanisms and trade-offs

Transactions, optimistic concurrency, idempotency, timeouts, cancellation, synchronous calls, outbox, and compensating actions trade latency, consistency, availability, and complexity.

## Evidence and counter-evidence

Seek route/handler code, use cases, database boundaries, external clients, schemas, traces, timeout/retry config, and integration tests. Counter-evidence includes hidden asynchronous side effects and framework defaults.

## Failure modes and false positives

HTTP success does not prove durable effect; database rollback cannot undo remote effects; client retries can duplicate a non-idempotent command.

## Confirmation scenarios

Exercise normal read/write, validation denial, concurrent update, timeout before/after effect, dependency failure, retry, cancellation, and rollback.

## Related concepts and escalation

Pair with client/server or layered/distributed shapes, data integrity, reliability, and security context propagation.

## Provenance and lifecycle

Synthesized from cloud reliability/data guidance and architecture scenario methods. Confidence: high; review annually.

Research claim trace: `WL-T1`, `WL-T1b`; see the living source packet with the same concept path.
