---
title: "Security, privacy, and trust boundaries"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - QL-S1
  - QL-S1b
---
# Security, privacy, and trust boundaries

## Scope and routing signals

Use when identity, authorization, sensitive data, integrity, isolation, abuse, or privacy consequences cross architecture boundaries.

## Decisions and minimum evidence

Supports risk and boundary decisions, not a substitute for specialist review. Minimum evidence identifies assets/data, actors, trust boundaries, identity propagation, policy enforcement, secret/credential resolution, audit, retention, threat scenarios, and exercised denials.

## Architectural questions

- Who can act on which resource under which scoped identity?
- Where can untrusted input or content influence a privileged decision or sink?
- What fails closed when policy, identity, or verification is absent?

## Mechanisms and trade-offs

Least privilege, defense in depth, isolation, policy-enforcing gateways, encryption, minimization, approval, and audit trade usability, latency, cost, and operational complexity.

## Evidence and counter-evidence

Seek threat models, authn/authz code, policy tests, data classifications, tenancy tests, secret handling, audit events, and incident evidence. Counter-evidence includes bypass paths and ambient credentials.

## Failure modes and false positives

Authentication is not authorization; encryption is not isolation; compliance documentation is not exercised control effectiveness.

## Confirmation scenarios

Attempt missing/wrong identity, cross-tenant access, policy dependency failure, malicious input, and privileged side effects; verify denial before effect and useful audit.

## Related concepts and escalation

Pair with hardening and data governance. Route detailed security/privacy assessment to specialist workflows and current checklists.

## Provenance and lifecycle

Synthesized from NIST risk/profile guidance, OWASP agentic guidance where applicable, and cloud security pillars. Confidence: high; review at least annually.

Research claim trace: `QL-S1`, `QL-S1b`; see the living source packet with the same concept path.
