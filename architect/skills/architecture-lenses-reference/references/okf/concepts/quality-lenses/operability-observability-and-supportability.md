---
title: "Operability, observability, and supportability"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - QL-O1
  - QL-O1b
---
# Operability, observability, and supportability

## Scope and routing signals

Use when diagnosis, deployment, configuration, support, incident response, or routine operation determines service outcomes.

## Decisions and minimum evidence

Supports whether operators can understand and safely control the system. Minimum evidence covers ownership, runbooks, health semantics, logs/metrics/traces, correlation, alerting, change/deployment, configuration, capacity, maintenance, and tested operational actions.

## Architectural questions

- Can operators distinguish symptom, cause, affected scope, and user impact?
- Can one change or control action be performed, verified, and reversed safely?
- Which critical states and decisions are invisible or unactionable?

## Mechanisms and trade-offs

Structured telemetry, correlation, service objectives, health models, runbooks, automation, feature controls, and progressive delivery trade signal cost, cognitive load, and implementation effort.

## Evidence and counter-evidence

Seek telemetry schemas, dashboards, alert history, runbooks, incident timelines, deployment outcomes, and support toil. Counter-evidence includes unowned alerts and uncorrelated logs.

## Failure modes and false positives

Telemetry volume is not observability; a health endpoint may ignore dependencies; a runbook may be stale or inaccessible during failure.

## Confirmation scenarios

Diagnose and mitigate one representative failure using only operator surfaces, then verify recovery and audit without source-author memory.

## Related concepts and escalation

Pair with operational reality, delivery patterns, reliability, and agent evaluation. Escalate live-environment checks to deep mode with authorization.

## Provenance and lifecycle

Synthesized from AWS, Azure, and Google operational excellence guidance. Confidence: high; review annually.

Research claim trace: `QL-O1`, `QL-O1b`; see the living source packet with the same concept path.
