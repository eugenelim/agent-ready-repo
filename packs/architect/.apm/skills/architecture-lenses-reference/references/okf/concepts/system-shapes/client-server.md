---
title: "Client/server systems"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SS-C1
  - SS-C1b
---
# Client/server systems

## Scope and routing signals

Use when separately deployed clients and servers coordinate through network contracts, shared identity, caching, synchronization, or version skew.

## Decisions and minimum evidence

Supports contract, trust, deployment, and compatibility decisions. Minimum evidence covers client types/versions, server APIs, identity/session, data ownership, offline/cache behavior, retries, error semantics, rollout compatibility, telemetry, and update control.

## Architectural questions

- Which decisions and sensitive state belong on the trusted server boundary?
- How do old and new clients coexist during rollout?
- What happens under offline, duplicate, delayed, or partially failed requests?

## Mechanisms and trade-offs

Versioned APIs, backward compatibility, server-side policy, client caches, optimistic updates, idempotency, and feature negotiation trade responsiveness, complexity, consistency, and release independence.

## Evidence and counter-evidence

Seek API schemas, client/server call sites, auth flows, cache/sync code, compatibility tests, rollout records, and correlated telemetry. Counter-evidence includes undocumented clients and server assumptions about immediate upgrade.

## Failure modes and false positives

TLS does not make a client trusted; validation on the client is not enforcement; an API version label does not prove behavioral compatibility.

## Confirmation scenarios

Run version-skew, offline/reconnect, duplicate mutation, expired identity, server degradation, and rollback scenarios across both sides.

## Related concepts and escalation

Pair with interfaces, security/trust, data integrity, transactional workload, and delivery patterns.

## Provenance and lifecycle

Synthesized from Azure architecture styles and independent cloud reliability/security guidance. Confidence: high; review annually.

Research claim trace: `SS-C1`, `SS-C1b`; see the living source packet with the same concept path.
