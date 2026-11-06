# ADR-0161: RFC-0114 supersedes the shipped criteria that pin the old RFC template and governance target

- **Status:** Accepted
- **Date:** 2026-11-06
- **Areas:** governance, rfc
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0114 (the proposal this records); ADR-0089 (already replaced AC5 and the no-tier-drops-a-check rule of AC6 in `new-rfc-two-humans`); spec `lighter-rfc-delivery` (the contract that implements RFC-0114)

## Decision summary

- **Decision:** We will mark each shipped acceptance criterion that RFC-0114 contradicts as superseded in part by this ADR, and leave every other criterion standing.
- **Because:** The frozen specs pin the old template, guide, eval and governance wording, and the lighter-RFC change makes those pins false.
- **Applies to:** Three specs: `new-rfc-two-humans`, `new-rfc-readability` and `new-rfc-governance`.
- **Tradeoff accepted:** Three frozen specs gain a pointer in their Status line.
- **Revisit if:** A later change moves a criterion number named below, or restores a superseded template element.

## Context

RFC-0114 replaces the Reviewer brief and the decisions table with a lighter template, rewrites the guide and the first eval for it, makes governance mode's default text the seeded starter, and lets an existing governance file at an allowed location be the target. Each of these contradicts a criterion that a shipped spec still states as true, and the `new-rfc` pack tests pin some of them. The specs are frozen, so the correction is recorded in one decision record and pointed to from each spec's Status line. Criterion numbers below were checked against the current spec text on 2026-11-06.

## Decision

We will treat the criteria in the table as superseded in part by this ADR, effective when RFC-0114's change ships.

- **D1:** In `new-rfc-two-humans`, these are superseded:

  | Criterion | Scope superseded | What replaces it |
  | --- | --- | --- |
  | AC2 | Whole criterion (`## Reviewer brief` above "The ask") | The template has no Reviewer brief. |
  | AC3 | Whole criterion (decisions as a table in "The ask") | The decisions are no longer a table in "The ask". |
  | AC6 | Only the clause that the completeness checklist's YES/NO items "survive verbatim" | "Approver named" becomes "who decides is clear". |
  | AC7 | Whole criterion (guide describes the Reviewer brief and the decisions table) | The guide stops describing both. |
  | AC9 | Only the eval assertions about the old template (the Reviewer brief and decisions-table assertions), not its Decision-weight assertion | The first eval is rewritten for the new template and still asserts the Decision weight field. |

- **D2:** In `new-rfc-readability`, AC3 is superseded only in the clause "fuller explanation living in 'The ask'", because there is no "The ask". The short-title guidance and the cue in `assets/rfc.md` stand.
- **D3:** In `new-rfc-governance`, two items are superseded:

  | Item | Scope superseded | What replaces it |
  | --- | --- | --- |
  | AC-0065, and the test that pins it (`test_governance_section_pins_ac_0065`) | The sentence "Put `GOVERNANCE.md` next to the charter when one exists, and at the repository root otherwise." | An existing governance file at an allowed location is the target. |
  | The "governance draft" definition (three owned-path names) | The exact owned-path requirement | Governance mode's default text and the seeded starter become one text, so the draft check is relaxed. |

Every other criterion in these specs stands, including `new-rfc-two-humans` AC1 and the optional `Decision weight` line, `new-rfc-readability` AC6, and `new-rfc-governance` AC-0044. `new-rfc-two-humans` AC5 and AC6's no-tier-drops-a-check rule stay superseded by ADR-0089, not by this ADR.

## Consequences

**Positive:**
- A reader of any of the three specs finds which criteria no longer hold and where the replacement is recorded.
- One record covers the change, so the specs need only a Status pointer.

**Negative:**
- The three specs carry a Status pointer that a reader must follow to learn what still holds.

**Revisit if:** A later change moves a criterion number named above, or restores a superseded template element.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `tests/roster/test_lighter_rfc_delivery.py` checks that each spec's Status line points to this ADR and that this ADR lists each criterion in `docs/rfc/0114-notes/superseded-criteria.md`.
- **Owner:** eugenelim
