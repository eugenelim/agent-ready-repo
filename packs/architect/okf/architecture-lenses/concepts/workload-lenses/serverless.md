---
title: "Serverless workloads"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-S1
  - WL-S1b
---
# Serverless workloads

## Scope and routing signals

Use when functions, managed event sources, workflow services, autoscaled ephemeral compute, or provider-managed control planes dominate runtime behavior.

## Decisions and minimum evidence

Supports event contract, concurrency, state, limits, security, cost, and operability decisions. Minimum evidence covers triggers, identity, tenancy, deployment unit, concurrency, timeout, retries, ordering, idempotency, state/external effects, cold start, quotas, observability, dead letters, cost, and provider responsibility.

## Architectural questions

- Which provider delivery, timeout, concurrency, retry, and scaling contracts are binding?
- Where does ephemeral execution store durable progress and coordinate effects?
- How do shared quotas, identities, and control planes affect isolation?

## Mechanisms and trade-offs

Managed triggers, functions, workflows, queues, reserved concurrency, idempotency, external state, and event destinations trade operations effort against provider coupling, limits, latency variance, and observability complexity.

## Evidence and counter-evidence

Seek infrastructure definitions, trigger config, IAM, handler code, state stores, retries/destinations, concurrency settings, traces, cost, incidents, and current provider contracts. Counter-evidence includes defaults not deployed.

## Failure modes and false positives

Stateless compute does not make the workflow stateless; automatic scaling does not remove downstream capacity; provider retry can duplicate effects.

## Confirmation scenarios

Exercise burst concurrency, cold start, timeout after effect, duplicate event, poison input, quota exhaustion, partial provider outage, deployment rollback, and dead-letter recovery.

## Related concepts and escalation

Pair with event/background workloads, reliability, cost, security, and current provider contract grounding.

## Provenance and lifecycle

Synthesized from independent cloud serverless and well-architected guidance. Confidence: moderate; verify provider behavior at use time and review annually.

Research claim trace: `WL-S1`, `WL-S1b`; see the living source packet with the same concept path.
