---
title: "Decisions, constraints, and cross-cutting concerns"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - DC-1
  - DC-2
  - DC-3
---
# Decisions, constraints, and cross-cutting concerns

## Scope and routing signals

Use when behavior spans components or when implemented choices cannot be
understood from local code alone: identity, policy, data, observability,
configuration, transactions, delivery, and governance.

## Decisions and minimum evidence

Supports reconstructing why constraints and shared mechanisms exist. Minimum
evidence distinguishes imposed constraints, chosen decisions, accidental
structure, current exceptions, owners, and the consequences of reversal.

## Architectural questions

- Which concerns must remain consistent across every execution boundary?
- Where is the policy or decision structurally enforced rather than conventional?
- Is the original rationale still applicable to the current environment?

## Mechanisms and trade-offs

Central contracts and policy-enforcing adapters improve consistency but can
create bottlenecks or inappropriate uniformity. Local autonomy improves speed
but needs explicit invariants, compatibility rules, and exception governance.

## Evidence and counter-evidence

Seek decision records, shared types, middleware, schemas, policy tests, build
rules, and exception manifests. Counter-evidence includes bypass paths, stale
records, duplicated policy, and behavior that contradicts the declared rule.

## Failure modes and false positives

A shared utility is not necessarily an architecture contract. A decision record
may describe a target never implemented; widespread repetition may reflect a
missing boundary or an intentionally decentralized mechanism.

## Confirmation scenarios

Trace identity, data, policy, telemetry, and failure handling through one normal
and one background or asynchronous path; identify every enforcement discontinuity.

## Related concepts and escalation

Pair with enterprise constraints, interface contracts, and the relevant workload
lens. Escalate policy specifics to security, privacy, or operations specialists.

## Provenance and lifecycle

Synthesized from ISO architecture-description and decision concepts, SEI
evaluation methods, and well-architected cross-cutting guidance. Confidence:
high; review annually.

Research claim trace: `DC-1`, `DC-2`, `DC-3`; see the living source packet with the same concept path.
