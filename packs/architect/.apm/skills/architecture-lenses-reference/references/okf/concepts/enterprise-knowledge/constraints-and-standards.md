---
title: "Enterprise constraints and standards"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - CS-1
  - CS-1b
---
# Enterprise constraints and standards

## Scope and routing signals

Use when legal, regulatory, security, privacy, data, platform, procurement,
delivery, residency, accessibility, or lifecycle rules constrain options.

## Decisions and minimum evidence

Supports eligibility and assurance decisions. Minimum evidence identifies the
authoritative rule, owner, scope, effective date, applicability, required
control/outcome, exception path, and evidence expected.

## Architectural questions

- Which obligation applies to this entity, data, user, and environment?
- Is the rule outcome-based or does it mandate a mechanism?
- Where is compliance structurally enforced and how are exceptions governed?

## Mechanisms and trade-offs

Use policy-as-code, approved platforms, control mappings, and exception records.
Standardization reduces variation and review cost but can preserve stale choices
or misfit diverse workloads.

## Evidence and counter-evidence

Seek current policy, scope statements, control evidence, exceptions, and named
authority. Counter-evidence includes outdated guidance, inherited templates,
ambiguous applicability, and implemented controls that meet the outcome differently.

## Failure modes and false positives

A framework recommendation is not automatically an enterprise mandate. A local
standard that conflicts with implementation is a context conflict until
applicability and authority are confirmed.

## Confirmation scenarios

Map one material obligation from authoritative text to enforcement point,
evidence, exception handling, and residual risk.

## Related concepts and escalation

Pair with decisions/cross-cutting concerns and the applicable quality lens.
Escalate interpretation to accountable legal, risk, security, or platform owners.

## Provenance and lifecycle

Synthesized from NIST profile tailoring, ISO stakeholder concerns, and cloud
governance guidance. Confidence: high for acquisition method; review annually.

Research claim trace: `CS-1`, `CS-1b`; see the living source packet with the same concept path.
