---
title: "Rationalization, disposition, and due diligence"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - AI-R1
  - AI-R1b
---
# Rationalization, disposition, and due diligence

## Scope and routing signals

Use when the primary decision is whether to retain, invest, consolidate, acquire/integrate, replace, or retire a system.

## Decisions and minimum evidence

Supports portfolio and investment disposition, not only technical remediation. Minimum evidence covers business criticality/value, strategic fit, usage, total cost, redundancy, technical health, obligations, ownership, exit dependencies, and option risk.

## Architectural questions

- What capability and obligation would be lost or duplicated under each option?
- Which costs and risks are technical, operational, contractual, organizational, or data-retention related?
- What evidence is missing for an irreversible investment or retirement decision?

## Mechanisms and trade-offs

Portfolio scoring, option economics, capability overlap, dependency analysis, and staged due diligence trade speed and comparability against context loss and false quantification.

## Evidence and counter-evidence

Seek usage/value evidence, portfolio maps, cost, incidents, architecture health, contracts, retention duties, and dependency owners. Counter-evidence includes repository-only proxies and sunk-cost reasoning.

## Failure modes and false positives

Poor code quality does not prove low business value; high spend does not prove replacement benefit; modernization is not the decision until disposition is settled.

## Confirmation scenarios

Compare retain/harden, invest/modernize, consolidate, replace/acquire, and retire against one shared evidence set and explicit uncertainty.

## Related concepts and escalation

Pair with business meaning, landscape, cost, data lifecycle, and decisions. If retained and structural change is selected, hand off to transformation.

## Provenance and lifecycle

Synthesized from cloud portfolio/rationalization guidance, migration strategies, and architecture options workshops. Confidence: moderate because the six-intent MECE set is synthesized; review annually.

Research claim trace: `AI-R1`, `AI-R1b`; see the living source packet with the same concept path.
