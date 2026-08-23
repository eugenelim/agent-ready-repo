---
title: "Governance, ownership, and team patterns"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - OM-1
  - OM-1b
---
# Governance, ownership, and team patterns

## Scope and routing signals

Use when responsibility, decision rights, team boundaries, support ownership, or cross-team coordination shape system behavior.

## Decisions and minimum evidence

Supports locating accountable owners and testing whether architecture boundaries align with decision and operational responsibility. Minimum evidence names owners, decision rights, escalation, support model, dependencies, and observed coordination load.

## Architectural questions

- Who can decide, fund, change, deploy, and operate each boundary?
- Where does shared ownership create delay or unsafe gaps?
- Does team coupling mirror runtime and data coupling?

## Mechanisms and trade-offs

Service ownership, platform teams, enabling teams, federated governance, and explicit decision forums trade local speed against consistency and coordination cost.

## Evidence and counter-evidence

Seek ownership maps, on-call rotations, code ownership, decision records, delivery dependencies, and incident handoffs. Counter-evidence includes nominal ownership without authority or support capacity.

## Failure modes and false positives

Repository CODEOWNERS does not prove operational ownership; many teams are not automatically a design flaw, and one team does not prove low coupling.

## Confirmation scenarios

Trace one consequential change and one incident across every team handoff, decision, deployment, and recovery boundary.

## Related concepts and escalation

Pair with local constraints, system landscape, modularity, and delivery/change safety. Escalate unclear accountability to the organization.

## Provenance and lifecycle

Synthesized from DORA team-coupling research, cloud adoption operating-model guidance, and architecture stakeholder principles. Confidence: moderate; review annually.

Research claim trace: `OM-1`, `OM-1b`; see the living source packet with the same concept path.
