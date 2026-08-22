---
title: "Provider and platform operating models"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - PP-1
  - PP-1b
---
# Provider and platform operating models

## Scope and routing signals

Use when shared cloud, data, developer, security, identity, or AI platforms mediate application capabilities and constraints.

## Decisions and minimum evidence

Supports deciding which responsibilities belong to workload teams versus platform/provider layers. Minimum evidence names service boundary, owner, consumer contract, control plane, support, tenancy, cost, limits, escape path, and change process.

## Architectural questions

- Which guarantees are provided and which remain with the workload?
- How are tenant, identity, policy, cost, and lifecycle isolated?
- What happens when the platform or provider changes or fails?

## Mechanisms and trade-offs

Managed services and internal platforms reduce repeated operations but introduce dependency, lock-in, shared-blast-radius, and queueing trade-offs.

## Evidence and counter-evidence

Seek service catalogues, SLOs, provider contracts, paved roads, tenancy models, incident records, adoption data, and exit plans. Counter-evidence includes undocumented responsibilities or direct provider bypasses.

## Failure modes and false positives

A platform name does not prove platform product behavior; central ownership does not guarantee enforceable policy or reliable support.

## Confirmation scenarios

Trace provisioning, normal use, policy enforcement, failure, upgrade, and exit for one platform capability from a consumer's perspective.

## Related concepts and escalation

Pair with current landscape, local patterns, cost, operability, and binding provider grounding. Escalate current limits to authoritative provider sources.

## Provenance and lifecycle

Synthesized from AWS, Azure, and Google operating-model and well-architected guidance. Confidence: moderate; review annually and verify provider contracts at use time.

Research claim trace: `PP-1`, `PP-1b`; see the living source packet with the same concept path.
