---
title: "Evidence, confidence, and coverage"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - EC-1
  - EC-2
  - EC-3
---
# Evidence, confidence, and coverage

## Scope and routing signals

Use for every assessment to separate what is declared, implemented, exercised,
and observed. Route here when a conclusion relies on names, diagrams, tests, or
operational claims whose coverage is uncertain.

## Decisions and minimum evidence

Supports confidence and investigation-scope decisions, not a pass/fail verdict.
Minimum evidence names the assessed entity, representative paths, evidence tier,
counter-evidence, uncovered areas, and the validation that would change the claim.

## Architectural questions

- What directly demonstrates the mechanism rather than merely describing it?
- Which important paths, environments, tenants, or failure modes remain unseen?
- Does independent evidence agree, and is it current for the decision horizon?

## Mechanisms and trade-offs

Use a claim ledger with evidence tier, scope, confidence, and falsifier. Stronger
evidence costs more to acquire; breadth without path depth and depth without
coverage both create false assurance.

## Evidence and counter-evidence

Seek code and configuration, exercised tests, runtime records, incidents, and
stakeholder decisions. Counter-evidence includes stale documentation, mocked
boundaries, unexecuted paths, sampling bias, and conflicting production signals.

## Failure modes and false positives

Folder names are not components, test presence is not exercised behavior, and a
single successful path is not system coverage. Missing evidence is an unknown,
not automatically a defect.

## Confirmation scenarios

Trace one normal path, one consequential mutation, and one failure/recovery path;
record where each claim changes evidence tier and where proof stops.

## Related concepts and escalation

Pair with boundaries and current-state views, quality-attribute scenarios, and
the selected intent. Escalate to runtime or specialist review when repository
evidence cannot support a consequential decision.

## Provenance and lifecycle

Synthesized from ISO architecture-description, SEI architecture-evaluation, and
major well-architected guidance. Confidence: high for evidence separation;
review annually for method evolution.

Research claim trace: `EC-1`, `EC-2`, `EC-3`; see the living source packet with the same concept path.
