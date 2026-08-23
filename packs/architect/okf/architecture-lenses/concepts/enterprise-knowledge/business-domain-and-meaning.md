---
title: "Business domain and meaning"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - BD-1
  - BD-1b
---
# Business domain and meaning

## Scope and routing signals

Use when system purpose, critical workflows, vocabulary, value, obligations, or
risk tolerance determine which architecture concerns matter.

## Decisions and minimum evidence

Supports boundary and priority decisions. Minimum evidence identifies users,
outcomes, critical capabilities, domain terms, consequences of failure, and the
decision sponsor; repository proxies alone are insufficient.

## Architectural questions

- Which user or business outcome does each major capability protect?
- Which concepts and invariants have domain meaning rather than technical convenience?
- What loss, delay, misuse, or obligation defines consequence?

## Mechanisms and trade-offs

Use capability maps, domain language, critical journeys, and outcome measures.
Business simplification can clarify architecture; overfitting current process can
freeze accidental organizational structure into software.

## Evidence and counter-evidence

Seek charters, service definitions, policies, product metrics, process records,
and stakeholder confirmation. Counter-evidence includes unused features,
ambiguous terms, conflicting KPIs, and code boundaries that do not match domain ownership.

## Failure modes and false positives

Names do not prove bounded contexts or ownership. Revenue, traffic, or executive
attention alone does not establish technical criticality.

## Confirmation scenarios

Trace one critical outcome through domain decisions, data, and failure impact;
confirm terminology and priority with an accountable source.

## Related concepts and escalation

Pair with current landscape, ownership patterns, and the selected assessment
intent. Escalate unresolved business value to portfolio or product owners.

## Provenance and lifecycle

Synthesized from architecture stakeholder/concern standards, ATAM business-driver
elicitation, and organizational-profile guidance. Confidence: high; review annually.

Research claim trace: `BD-1`, `BD-1b`; see the living source packet with the same concept path.
