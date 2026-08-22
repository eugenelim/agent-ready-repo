---
title: "Current system landscape"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SL-1
  - SL-1b
---
# Current system landscape

## Scope and routing signals

Use when neighboring systems, shared platforms, duplicate capabilities, data
flows, ownership, lifecycle, or portfolio dependencies affect the assessment.

## Decisions and minimum evidence

Supports system-boundary, integration, reuse, and disposition decisions. Minimum
evidence identifies active systems, owners, purposes, lifecycle, critical
dependencies, authoritative data, and confidence in inventory currency.

## Architectural questions

- Which external systems and shared services are operationally load-bearing?
- Where do capability, data, or platform responsibilities overlap?
- Which dependencies constrain migration, recovery, or retirement?

## Mechanisms and trade-offs

Use a scoped landscape map and dependency register. Central inventories improve
coordination but age quickly; local discovery is current but misses portfolio context.

## Evidence and counter-evidence

Seek catalogues, diagrams, interface registries, deployment inventories, data
lineage, and named owners. Counter-evidence includes dead entries, shadow systems,
undocumented batch exchange, and runtime calls absent from the catalogue.

## Failure modes and false positives

An inventory record does not prove a live dependency. Similar product names do
not prove duplication, and a shared database does not by itself define ownership.

## Confirmation scenarios

Reconcile one critical external path across the landscape record, repository
configuration, runtime evidence, and owners on both sides.

## Related concepts and escalation

Pair with boundaries/views, interfaces/contracts, and disposition. Escalate
unresolved portfolio authority to enterprise or domain architecture owners.

## Provenance and lifecycle

Synthesized from ISO architecture views, cloud adoption portfolio guidance, and
well-architected documentation practice. Confidence: high; review annually.

Research claim trace: `SL-1`, `SL-1b`; see the living source packet with the same concept path.
