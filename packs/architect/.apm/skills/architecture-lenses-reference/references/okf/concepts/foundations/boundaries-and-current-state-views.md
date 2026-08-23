---
title: "Boundaries and current-state views"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - BV-1
  - BV-2
  - BV-3
---
# Boundaries and current-state views

## Scope and routing signals

Use when reconstructing what the assessed system is, what surrounds it, and how
its principal runtime, data, deployment, and development structures relate.

## Decisions and minimum evidence

Supports entity scoping and view selection. Minimum evidence identifies users
and external systems, major responsibilities, dependency direction, data stores,
runtime placement, delivery units, and explicit exclusions.

## Architectural questions

- Where do responsibility, trust, data ownership, and deployment boundaries differ?
- Which view answers each stakeholder concern without pretending to be complete?
- What crosses the boundary, under which identity and failure contract?

## Mechanisms and trade-offs

Use a small related view set: context, containers/components, runtime interaction,
data ownership/flow, deployment, and code/development structure. More views add
cost; one overloaded diagram hides distinctions and creates false precision.

## Evidence and counter-evidence

Seek manifests, entry points, interface schemas, deployment definitions, storage
configuration, dependency files, and representative traces. Counter-evidence is
runtime composition or ownership that contradicts the apparent source layout.

## Failure modes and false positives

A repository boundary may not equal a system or deployment boundary. Shared
libraries are not automatically services; directories are not automatically
modules; infrastructure definitions may describe inactive environments.

## Confirmation scenarios

Follow one user or event from entry through state and external effects, then map
the same path across source, runtime, data, and deployment views.

## Related concepts and escalation

Pair with evidence/confidence and the detected system shape. Use diagramming only
after the conceptual model is corrected; escalate unresolved ownership to local
enterprise context.

## Provenance and lifecycle

Synthesized from ISO/IEC/IEEE 42010 and established cloud architecture view
guidance. Confidence: high; review annually.

Research claim trace: `BV-1`, `BV-2`, `BV-3`; see the living source packet with the same concept path.
