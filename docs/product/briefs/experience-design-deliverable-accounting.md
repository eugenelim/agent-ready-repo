# Brief: a practitioner can account for every deliverable the experience-design pack owes

- **Slug:** `experience-design-deliverable-accounting`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/experience-design-delivery-packet.md`](../intents/experience-design-delivery-packet.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** capability:experience-design-delivery-packet

## Outcome

A designer who ran an agency engagement can mark every deliverable they expect as owned by a skill, satisfied by an existing artifact, or declared out of scope in the pack documentation, and can find a guide that teaches each owned one. The audience is the design consultancy baseline; enterprise operating additions are declared out of scope (owner decision, 2026-11-05).

## Success metrics

- A cited deliverable inventory has no line marked missing and unexplained.
- Every owned line has a guide that teaches it, checked by a test over the inventory.
- The pack documentation lists the enterprise additions as out of scope.

## Scope / Non-goals

**In scope:**

- A cited agency-baseline deliverable inventory; each baseline line cites an external source (a published agency deliverable list or standard), not only this repository.
- Out-of-scope statement in the pack docs and guide.
- Guide pages for owned lines that lack one, authored through the `docs-job-pages` guide conventions (`docs-job-pages` superseded `pack-guidebook-walkability` on 2026-10-15).
- The `experience-design` version bump that ships the pack-doc change.
- A reference route from `journey-mapping` `evidence-level` to `plan-validation`.

**Non-goals:**

- New reference documents for gaps D1 finds; each becomes a follow-up intent.
- Accessibility conformance reporting, research repository with consent and personal data, design-ops intake, versioned design system with contribution model, localisation, instrumentation.
- New skills; each gap is first argued as a reference.
- Any step that supplies observational evidence without a human.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| D1 | Deliverable inventory (a gap that would need a new reference is marked out of scope here and becomes a follow-up intent, except the evidence seam that D3 owns): agency baseline lines, each marked owned, referenced or out of scope with a citation to a skill, artifact or document. | A script resolves every repository citation to an existing path or skill, owned lines name a registered skill, and every baseline line carries an external source; the script fails on a line with none | none | none |
| D2 | Pack-doc out-of-scope statement and the `experience-design` version bump that ships it, plus guide pages for owned lines that no guide teaches, and the uplift of every existing guide under `guides/experience-design/` (nine files today, including the README) to all five affordances (parent step 4). | A test reads the inventory and fails on an owned line with no guide link, and the affordance audit runs over the new pages and over every uplifted existing page; guide-index check; `tools/audit-guide-affordances.py` shows each new page carrying all five affordances (A to E: chat input, demonstrated input, sample output, stated outcome, job to be done) | D1 | none |
| D3 | Evidence seam: a reference that routes `evidence-level: observational` journeys to `plan-validation`, which scaffolds and synthesises and never runs sessions. | An offline test pins the reference text: it names `plan-validation` for `evidence-level: observational` journeys and states that sessions are run by a person | none | none |

### Manual or live residue, split off as non-blocking follow-ups

- Model-run eval that an observational-level request names `plan-validation` and does not claim to supply observations: owner-run, non-blocking.
- Practitioner walkthrough of the inventory by a human design lead. Replaced by the cited inventory and the guide-coverage test; the walkthrough is a non-blocking confirmation.

## Decisions

Decided 2026-11-05 by eugenelim: D2 writes new guide pages only for lines the inventory shows as unguided, following the `docs-job-pages` conventions, and does not reopen that spec's scope. The separate uplift of the existing guides is the parent's step 4, not part of this decision.

## Constraints / Appetite

Three small to medium sessions after D1. D1 starts from the pack's current registered skill list.

## Assumptions / Risks

- Riskiest assumption: most gaps are already owned or referenced. D1 measures that before any addition is argued.
- Parent kill assumption 1: a stable agency deliverable set exists. If D1 finds sources disagree on the set, stop and return to the parent intent.
- Risk: compliance artifacts imply assurance; they stay out of scope.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

- Parent intent: [`experience-design-delivery-packet.md`](../intents/experience-design-delivery-packet.md).
