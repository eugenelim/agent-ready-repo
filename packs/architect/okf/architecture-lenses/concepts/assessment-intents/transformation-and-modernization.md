---
title: "Transformation and modernization"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - AI-T1
  - AI-T1b
---
# Transformation and modernization

## Scope and routing signals

Use when a system that remains needed may move to a materially different architecture, platform, data model, or delivery model.

## Decisions and minimum evidence

Supports comparative transition strategy. Minimum evidence names drivers, target constraints, current seams/contracts, characterization coverage, data migration, compatibility, skills, cutover, rollback, option cost, and retained capabilities.

## Architectural questions

- Which current constraints or risks require structural change rather than local improvement?
- What stable seams permit incremental transition?
- How do retain/harden, incremental modernization, targeted replacement, and rewrite compare?

## Mechanisms and trade-offs

Strangler transitions, modular extraction, replatforming, rehosting, refactoring, replacement, and rewrite trade speed, dual-running cost, compatibility, learning, and cutover risk.

## Evidence and counter-evidence

Seek dependency/data maps, characterization tests, change/incidents, platform contracts, team skills, option estimates, and rollback evidence. Counter-evidence includes fashion-driven targets and underestimated data/behavior migration.

## Failure modes and false positives

Age, size, language, or coupling alone cannot justify rewrite. A service layer that only forwards calls is not modernization.

## Confirmation scenarios

Pilot one high-value seam with compatibility, data reconciliation, rollback, and operational comparison before scaling the roadmap.

## Related concepts and escalation

Pair with disposition first when retain/replace/retire is unresolved; pair with decisions, delivery, data, and current/future scenarios. Hand target design to architect-design.

## Provenance and lifecycle

Synthesized from AWS/Microsoft migration strategies and SEI modernization roadmapping. Confidence: high; review annually.

Research claim trace: `AI-T1`, `AI-T1b`; see the living source packet with the same concept path.
