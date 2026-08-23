---
title: "Tool authorization and credentials"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-A3
  - WL-A3b
---
# Tool authorization and credentials

## Scope and routing signals

Use when a model or agent requests actions against code, files, browsers, APIs, databases, communication channels, infrastructure, or external systems.

## Decisions and minimum evidence

Supports whether requested and executed actions are separately authorized, contained, and audited. Minimum evidence covers action schema, required permission, tenant/resource scope, read/write/reversibility, approval, credential class and runtime resolution, allowed destinations, isolation, time/step/spend caps, validation, result trust, and audit.

## Architectural questions

- Who authorizes the requested action, and who authorizes execution against the specific resource?
- Can delegated or model-selected arguments widen identity, destination, or privilege?
- What contains filesystem, network, process, credential, and resource blast radius after authorization?

## Mechanisms and trade-offs

Typed action contracts, policy decision/enforcement points, least-privilege capability grants, runtime credential resolution, allowlists, sandboxing, approvals, dry runs, and action receipts trade autonomy, latency, usability, and implementation cost.

## Evidence and counter-evidence

Seek tool registry, permission policy, credential broker, argument validation, destination controls, sandbox limits, approval flow, audit records, and negative tests. Counter-evidence includes credentials in prompts/jobs or model-gateway-only authorization.

## Failure modes and false positives

A model gateway cannot authorize tool effects; tool registration is not containment; a human approval without exact action/resource context can be meaningless.

## Confirmation scenarios

Attempt unauthorized tenant/resource, mutating action without approval, credential substitution, forbidden destination, prompt-injected arguments, timeout, cancellation, and delegated privilege widening; verify denial before effect.

## Related concepts and escalation

Pair with model access, security/trust, durable run state, and knowledge isolation. Route security-boundary depth to specialist review.

## Provenance and lifecycle

Synthesized from OWASP LLM and Agentic Top 10, NIST GenAI profile, and secure agent reference guidance. Confidence: high; review at least annually.

Research claim trace: `WL-A3`, `WL-A3b`; see the living source packet with the same concept path.
