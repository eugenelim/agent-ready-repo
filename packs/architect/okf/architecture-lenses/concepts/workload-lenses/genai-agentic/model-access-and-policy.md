---
title: "Model access and policy"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-A1
  - WL-A1b
---
# Model access and policy

## Scope and routing signals

Use when applications or agents call language, vision, embedding, reranking, or multimodal model providers through synchronous, asynchronous, streaming, tool-use, or computer-use capabilities.

## Decisions and minimum evidence

Supports whether every model invocation receives consistent policy and evidence. Minimum evidence separates provider, capability, and transport; identifies sanctioned adapter construction; budget/token controls; PII/safety handling; tenant/run correlation; model/prompt version; usage/cost; timeout/retry/cancellation; and exception governance.

## Architectural questions

- Can any raw provider client be constructed or invoked outside the policy boundary?
- Do async, streaming, tool-use, and computer-use paths receive equivalent controls?
- How are retries, partial streams, cancellation, and usage accounting correlated without double count?

## Mechanisms and trade-offs

Capability-oriented gateways, provider adapters, shared policy middleware, construction checks, exception manifests, and per-run budgets trade flexibility, provider feature access, latency, and central coupling.

## Evidence and counter-evidence

Seek all provider imports/constructors/invocations, dependency wiring, gateway middleware, exception records, path matrix tests, telemetry, and failure handling. Counter-evidence includes wrappers that apply only token caps or omit safety/PII/usage.

## Failure modes and false positives

Computer use is a capability, not a provider. Moving a raw client into config does not enforce policy; import grep alone misses re-exports or injected clients.

## Confirmation scenarios

Exercise sync, async, streaming, tool calling, computer use, provider failure/retry, cancellation, and budget exhaustion; confirm policy and trace outcomes on each.

## Related concepts and escalation

Pair with tool authorization, evaluation/observability, security/privacy, and provider/platform operating model. Specialist AI security review may be required.

## Provenance and lifecycle

Synthesized from NIST GenAI profile, OWASP LLM/agentic guidance, and cloud agent governance guidance. Confidence: high; review at least annually.

Research claim trace: `WL-A1`, `WL-A1b`; see the living source packet with the same concept path.
