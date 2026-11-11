# Spec: Experience-design agency-baseline deliverable inventory

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** `experience-design-delivery-packet` intent (consultancy baseline decision, 2026-11-05)
- **Brief:** brief:experience-design-deliverable-accounting
- **Discovery:** capability:experience-design-delivery-packet
- **Depends on:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

A designer who ran a consultancy engagement can read one cited inventory of the deliverables they expect and see, for each, whether a skill owns it, an artifact satisfies it, or it is out of scope. No line is missing and unexplained.

## What Changes

- A deliverable inventory document under `docs/product/research/`, one line per agency-baseline deliverable, each marked owned, referenced or out of scope, each with an external source and, where owned or referenced, a repository citation.
- A check script that resolves every repository citation and fails on a line with no external source.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Inventory states what the pack owns | `docs/product/research/experience-design-deliverable-inventory.md` | eugenelim | Check script passing | close-work verifies the script passes |
| Decision rationale | Gaps needing a new reference become follow-up intents | Follow-ons below | eugenelim | Intent files exist | none |

## Agent Rules

### Always do

- Cite a published agency deliverable list or standard for every baseline line.
- Start from the pack's registered skill list in its manifest.
- Mark a gap that would need a new reference as out of scope and name a follow-up intent.

### Ask first

- Declaring the audience question reopened; the consultancy baseline is decided.
- Adding enterprise additions (accessibility conformance reporting, research repository, design-ops, localisation, instrumentation) to the baseline.

### Never do

- Add a skill or a reference in this slice.
- Invent a source.
- Run an external fetch without citing the retrieved source and date.

## Testing Strategy

Goal-based: the check script passes on the inventory and fails on a seeded line with no external source, a seeded citation to a missing skill, and a seeded owned line that names an unregistered skill.

## Acceptance Criteria

- [ ] **AC1.** The inventory has one line per baseline deliverable, each marked owned, referenced or out of scope.
- [ ] **AC2.** Every baseline line carries an external source.
- [ ] **AC3.** Every repository citation resolves to an existing path or registered skill.
- [ ] **AC4.** Every owned line names a registered `experience-design` skill.
- [ ] **AC5.** The check script fails on a line with no external source.
- [ ] **AC6.** If sources disagree on the baseline set, the inventory records the disagreement and stops; it does not choose silently.

## Follow-ons

- eugenelim: `brief:experience-design-deliverable-accounting` slices D2 and D3.

## Assumptions

- Open question for eugenelim: which external sources count as the agency baseline. Recommended default: two or more published deliverable lists from named design consultancies or a recognised design-process standard, recorded with retrieval date.
- Parent kill assumption 1 (a stable agency set exists) is tested by this slice; if it fails, work returns to the parent intent.
