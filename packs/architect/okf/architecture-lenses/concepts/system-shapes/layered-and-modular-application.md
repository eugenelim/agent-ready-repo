---
title: "Layered and modular applications"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SS-M1
  - SS-M1b
---
# Layered and modular applications

## Scope and routing signals

Use when one deployable or process organizes responsibilities into layers, modules, bounded components, or plugins.

## Decisions and minimum evidence

Supports dependency-direction, transaction, modularity, and extraction decisions. Minimum evidence covers entry points, application orchestration, domain rules, ports/contracts, persistence/external adapters, dependency direction, shared state, transactions, build/test units, and exceptions.

## Architectural questions

- Which layer owns business decisions versus transport or storage concerns?
- Where can callers bypass the intended application boundary?
- Do modules encapsulate state and policy or only add forwarding files?

## Mechanisms and trade-offs

Layering, ports/adapters, modules, dependency injection, transaction boundaries, and import rules trade clarity/testability against indirection and local convenience.

## Evidence and counter-evidence

Seek import graphs, constructors, use cases, transactions, policy placement, repository interfaces, module tests, and bypass baselines. Counter-evidence includes re-exports and service layers that preserve direct coupling.

## Failure modes and false positives

A folder structure does not prove layering; direct imports are not always architectural violations; more classes can increase ceremony without changing responsibilities.

## Confirmation scenarios

Trace one read, write, failure, and background path from entry through decisions, state, and external effects; compare intended and actual dependency direction.

## Related concepts and escalation

Pair with maintainability, transactional/background workloads, and transformation. Route target restructuring to architect-design.

## Provenance and lifecycle

Synthesized from architecture style guidance, ISO viewpoints, and change-coupling research. Confidence: moderate; review annually.

Research claim trace: `SS-M1`, `SS-M1b`; see the living source packet with the same concept path.
