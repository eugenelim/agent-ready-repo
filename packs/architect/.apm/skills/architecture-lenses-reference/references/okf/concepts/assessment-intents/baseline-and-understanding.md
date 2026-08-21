---
title: "Baseline and understanding"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - AI-B1
  - AI-B1b
---
# Baseline and understanding

## Scope and routing signals

Use when the primary decision is shared understanding: what the system is, how it works, what is architecturally significant, and what remains unknown.

## Decisions and minimum evidence

Supports a correctable current-state model and evidence-acquisition plan. Minimum evidence covers boundary, major views, representative paths, declared/implemented/exercised/observed tiers, and material unknowns; it does not require a remediation verdict.

## Architectural questions

- What entity and decision horizon are being described?
- Which mechanisms and dependencies are architecturally significant?
- Where does confidence stop and which drill-down would change it?

## Mechanisms and trade-offs

A survey map, evidence ledger, attention heat, and bounded drill-down hypotheses trade speed against completeness. Survey depth should stop before unverified action claims.

## Evidence and counter-evidence

Seek topology, interfaces, state, delivery, runtime, decisions, and representative traces. Counter-evidence includes conflicting views, inactive code, and uncovered subsystems.

## Failure modes and false positives

Baseline is not a lower-quality hardening or modernization report. Attention is not severity, and unknowns are not defects.

## Confirmation scenarios

Correct the conceptual model with the user, then trace one normal, mutation, and failure path and state remaining coverage.

## Related concepts and escalation

Pair with all foundations and triggered shape/workload lenses. Route a named threshold, improvement, future scenario, transformation, or investment decision to another intent.

## Provenance and lifecycle

Synthesized from ISO architecture-description and SEI evaluation methods plus practitioner progressive-assessment research. Confidence: high; review annually.

Research claim trace: `AI-B1`, `AI-B1b`; see the living source packet with the same concept path.
