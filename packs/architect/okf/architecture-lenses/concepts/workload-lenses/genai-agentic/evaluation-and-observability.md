---
title: "Agent evaluation and observability"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-A5
  - WL-A5b
---
# Agent evaluation and observability

## Scope and routing signals

Use when model, knowledge, tool, policy, cost, safety, or run-quality behavior must be measured across a changing agent system.

## Decisions and minimum evidence

Supports release, assurance, optimization, and incident decisions. Minimum evidence correlates request, run, step, model call, knowledge retrieval, tool decision, tool execution, transaction, versions, policy outcomes, approvals, cost, latency, retry/recovery, result quality, and evaluation dataset provenance.

## Architectural questions

- Can one outcome be traced to model/prompt, retrieved sources, tool decisions/effects, policy, and state transitions?
- Which operational and quality signals detect regressions without exposing sensitive content?
- Do offline, adversarial, shadow, and production evaluations represent consequential scenarios?

## Mechanisms and trade-offs

End-to-end traces, structured events, evaluation datasets, scenario suites, adversarial cases, human review, online feedback, budgets, and release gates trade coverage, cost, privacy, and metric gaming.

## Evidence and counter-evidence

Seek trace schemas, correlation propagation, model/prompt/tool/knowledge versions, evaluation cases, graders and human checks, cost/latency, policy outcomes, incidents, and rollback criteria. Counter-evidence includes provider usage only and tautological model judging.

## Failure modes and false positives

Token telemetry is not agent observability; aggregate pass rate can hide severe scenario failures; model-as-judge without calibration can reward its own style.

## Confirmation scenarios

Reproduce one success, unsupported answer, policy denial, prompt injection, tool failure, duplicate recovery, stale retrieval, and cost regression end to end with attributable evidence.

## Related concepts and escalation

Pair with model access, durable state, knowledge isolation, operability, and testability. Escalate evaluation design to quality and AI risk specialists.

## Provenance and lifecycle

Synthesized from NIST GenAI profile, OWASP agentic guidance, and cloud agent governance/observability guidance. Confidence: high; review at least annually.

Research claim trace: `WL-A5`, `WL-A5b`; see the living source packet with the same concept path.
