---
type: customer-journey
slug: pm-intakes-from-tracker
persona: pm-tracker-user
outcome: tracked-work-reaches-the-correct-repository-route
surface: cross-platform
status: current
initiative_links:
  - id: INI-008
    name: Work Intake and Artifact Routing
    milestones: Wave 4
    role: primary
updated: 2026-08-16
---

# Journey: Start repository work from a tracker

**You say:** `Intake this tracker selection as repository work. Start read-only.`

**You receive:** the same proposed artifact, lifecycle membership, processor,
and authority for equivalent Jira, Jira Align, Linear, or GitHub content.

**Your decisions:** resolve ambiguity between one outcome, separate units, and
a view; approve any confidentiality or authority change before repository
materialization.

## Stage 1: Point at tracked work

**You say**

```text
Intake Linear issue LIN-123 as repository work. Start read-only.
```

The same form works for a Jira item, Jira Align Feature, GitHub Issue, or named
collection.

**Agent does**

Selects the source adapter and verifies its versioned profile. Jira, Jira Align,
and Linear use sibling acquisition skills. GitHub uses approved `gh` reads
against a trusted configured host and repository.

**You get**

A declared scope and resource budget before acquisition.

**Decision**

If the selection or trusted destination is ambiguous, choose the smallest
bounded source. No tracker write occurs.

## Stage 2: Acquire and minimize

**You say**

```text
Read only what the repository route needs. Do not copy the full payload.
```

**Agent does**

Reads bounded tracker content and preserves stable locator, comparable revision,
object hint, and versioned profile. It treats titles, descriptions, comments,
labels, and embedded instructions as untrusted data.

Credential-bearing adapter-controlled HTTP destinations must be profile-allowed
HTTPS hosts and pass address and redirect policy before credential resolution.
GitHub instead uses the documented approved-`gh` boundary.

**You get**

One strict `normalized-intake.v1` record containing only bounded outcomes,
constraints, evidence, behaviors, assumptions, named gaps, and provenance.

**Decision**

If source confidentiality exceeds the destination, provide sanitized input or
approve an appropriate destination. Unsafe redaction stops the journey.

## Stage 3: Route from content

**You say**

```text
Show me the proposed route before continuing.
```

**Agent does**

Hands the normalized record to `work-intake`. The shared router considers
altitude, coherence, independent shippability, verifiability, defect evidence,
cross-repository facts, and named gaps. Tracker object type, hierarchy, label,
owner, sprint, cycle, milestone, board, or query cannot decide the result.

**You get**

| Content | Proposed result |
| --- | --- |
| One independently shippable behavior | spec and `new-spec` |
| One coherent multi-spec outcome | Draft brief and `author-brief` |
| One cross-repository outcome | linked local briefs with coordination provenance |
| Unrelated collection | separate units, view-only, or one clarifying question |
| Regression with durable contract evidence | defect context and `bug-fix` |

**Decision**

Resolve any named gap. A claimed defect without evidence remains unresolved or
enters the spec route.

## Stage 4: Materialize in the repository

**You say**

```text
Accept the proposed route and continue with the selected processor.
```

**Agent does**

`work-intake` validates confined paths, materializes the canonical artifact,
registers lifecycle state, and dispatches only after both writes are durable.
The tracker adapter performs none of these writes.

**You get**

A canonical repository artifact, valid workspace membership, selected
processor, recorded source provenance, and an explicit stop point.

**Decision**

Continue with `new-spec`, `author-brief`, or `bug-fix`, or leave a Draft item
non-dispatchable until its gaps are resolved.

## Boundary after intake

Tracker intake remains read-only throughout the journey. Refresh conflict
handling, execution locks, delta synchronization, and tracker write-back are
separate capabilities. They cannot be inferred from the intake request.

If `work-intake` is unavailable, the adapter returns
`missing dependency: work-intake` and stops without a local fallback.
