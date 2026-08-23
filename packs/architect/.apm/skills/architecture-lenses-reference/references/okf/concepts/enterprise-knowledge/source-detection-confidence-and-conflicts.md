---
title: "Enterprise source detection, confidence, and conflicts"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - SD-1
  - SD-1b
---
# Enterprise source detection, confidence, and conflicts

## Scope and routing signals

Use when local standards, landscape, ownership, operations, decisions, or plans
could change the assessment. This concept supplies acquisition questions only;
it never supplies an organization's facts.

## Decisions and minimum evidence

Supports whether and how to use enterprise context. Minimum evidence names the
authorized surface, source locator, owner/authority cue, retrieval date,
applicability, corroboration, conflict, and confidence.

## Architectural questions

- Is the surface in-repo or a governed, pre-authenticated knowledge capability?
- Who owns the source, what scope does it govern, and how current is it?
- Does implemented behavior agree, and which owner can resolve a conflict?

## Mechanisms and trade-offs

Discover capabilities, ask before private retrieval, select only relevant
knowledge areas, and preserve attribution. More context improves local fit but
increases privacy, freshness, and instruction-injection risk.

## Enterprise knowledge-area taxonomy

Each area answers one distinct acquisition question. Select only the areas the
current architecture decision turns on.

| # | Area | The question it answers |
|---|---|---|
| 1 | Business domain & meaning | What do the terms, capabilities, and business rules *mean*? |
| 2 | Current landscape | What systems, services, data, and ownership *exist* today? |
| 3 | Interfaces & contracts | What can I integrate with, and on what *terms*? |
| 4 | Operational reality | How does it *behave* in production (SLOs, incidents, failure modes)? |
| 5 | Constraints & standards | What *must / must-not* I do (policies, approved tech, security rules)? |
| 6 | Patterns & references | How is this *done well* here (reference architectures, golden paths)? |
| 7 | Decisions & rationale | *Why* is it this way; what's *deprecated*? |
| 8 | In-flight & roadmap | What's *changing* or being built in parallel? |

## Evidence and counter-evidence

Seek authoritative policies, inventories, decisions, operational records, and
named owners. Counter-evidence includes stale pages, search summaries, one-off
team practice, contradictory implementation, and unclear applicability.

## Failure modes and false positives

Public web content is not organization knowledge. A detected generic fetcher is
not an eligible internal surface. Conflict is not automatically non-compliance;
the source may be stale or scoped elsewhere.

## Confirmation scenarios

Query one selected area, attribute the result, compare it with repository
evidence, and show how confidence changes without copying sensitive content.

## Related concepts and escalation

Routes to the eight enterprise knowledge areas. Escalate unresolved authority,
access, sensitivity, or conflict to the source owner; fail closed on eligibility.

## Provenance and lifecycle

Synthesized from NIST profiles, ISO concern/viewpoint principles, and cloud
operating-model guidance. Confidence: high; review annually.

Research claim trace: `SD-1`, `SD-1b`; see the living source packet with the same concept path.
