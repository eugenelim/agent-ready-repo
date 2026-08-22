---
title: "Monorepos, platforms, and infrastructure systems"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SS-P1
  - SS-P1b
---
# Monorepos, platforms, and infrastructure systems

## Scope and routing signals

Use when one repository coordinates many packages, services, infrastructure modules, generators, adapters, or developer-platform capabilities.

## Decisions and minimum evidence

Supports ownership, dependency, build, release, compatibility, and platform-product decisions. Minimum evidence covers repository units, dependency rules, source/generated ownership, build graph, test ownership, release/versioning, deployment mapping, shared tooling, consumer contracts, tenancy, and governance.

## Architectural questions

- Which boundaries are source, package, deployment, ownership, or platform-service boundaries?
- Can affected units be built, tested, released, and rolled back without whole-repo coupling?
- Which generated or shared surface has one authoritative producer?

## Mechanisms and trade-offs

Workspace graphs, explicit package contracts, affected builds, code ownership, version policies, generators, paved roads, and policy checks trade consistency and reuse against central complexity and blast radius.

## Evidence and counter-evidence

Seek manifests, build/test graphs, release automation, ownership, generated markers, dependency lint, consumer docs, and change history. Counter-evidence includes undeclared reach-through and manual projections.

## Failure modes and false positives

One repository is not one deployable; many packages are not independent; centralized tooling is not automatically a platform product; generated files are not authoring sources.

## Confirmation scenarios

Change one shared contract and one leaf unit; trace affected build, tests, versions, generated outputs, consumers, deployment, rollback, and ownership.

## Related concepts and escalation

Pair with delivery patterns, maintainability, platform operating model, and infrastructure operational/security specialist checks.

## Provenance and lifecycle

Synthesized from DORA loose-coupling, cloud platform/operating guidance, and repository-grounded source/generated ownership principles. Confidence: moderate; review annually.

Research claim trace: `SS-P1`, `SS-P1b`; see the living source packet with the same concept path.
