# Spec: evaluator platform-lead journey

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0076
- **Brief:** brief:catalogue-evaluator-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the journey is a design document, and the check it adds reads files only
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without
> a review round.

## Outcome

The `/evaluate/` page has a named reader: a platform lead deciding whether their organisation should build and own a catalogue, with the nine claims they check written down in one journey. A repository check keeps that journey complete, so the page's spec can freeze its reader from it.

## What Changes

- A platform-lead journey stub — `docs/design/journeys/platform-lead-evaluates-catalogue.md`, next to the four existing journeys.
- A check that the stub names its reader, their decision, and each of the nine claims — a new lint under `tools/`.
- The check reaches the gate that already runs doc-tree linters on `docs/**` changes — `.github/workflows/docs.yml`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable: the journey records the reader and claims the page serves | `docs/design/journeys/platform-lead-evaluates-catalogue.md` | eugenelim | The check passes on the file | The file names the reader and nine claims |
| Maintainer procedure | Applicable: a new lint needs a pointer where journeys are kept | `docs/design/README.md` | eugenelim | The README names the check | A reader of the journeys directory finds it |
| Current product truth | Not applicable: no shipped behaviour changes | none | none | none | none |

## Agent Rules

### Always do

- Follow the frontmatter shape the existing journeys carry: `type`, `slug`, `persona`, `outcome`, `surface`, `genre`, `state`, `evidence-level`, `evidence_note` and `updated`.
- Mark every emotion and pain as assumption-based unless an observation is cited.

### Ask first

- Amend an existing journey, including the adoption-champion map `team-orientation-future-state.md`.
- Treat the stub as gate-approved. Approval runs through `approve-journey` and is the owner's.

### Never do

- Never add a new top-level dependency or a new directory under `docs/`.
- Never name a claim the nine do not cover, or a destination for one; the destinations belong to the `/evaluate/` page spec.

## Testing Strategy

- **Journey completeness:** TDD. The check is tested against a fixture journey that passes and fixtures that each omit one required element.
- **Real file:** goal-based. The check runs on the committed journey and exits 0.
- **Gate wiring:** goal-based. A grep-level test confirms the workflow runs the check, following the pattern of `tools/test_intent_corpus_gate.py`.

## Acceptance Criteria

- [ ] `docs/design/journeys/platform-lead-evaluates-catalogue.md` exists with frontmatter keys `type: customer-journey`, a `persona` naming a platform lead, an `outcome`, `state`, `evidence-level` and `updated`.
- [ ] The journey names each of the nine RFC-0076 D10 claims by its label: open file-based formats, versioned contracts, deterministic verification and packaging, human gates, source ownership, adapter projection, release integrity, optional composition, technical evidence.
- [ ] The check exits non-zero on a journey missing any one of the frontmatter keys above, and on a journey missing any one of the nine claim labels, with a message that names the missing item.
- [ ] The check exits 0 on the committed journey.
- [ ] `.github/workflows/docs.yml` runs the check, and its `paths` filter covers `docs/design/journeys/**` and the check's own file.

## Follow-ons

- eugenelim: `brief:catalogue-evaluator-delivery` slice E3 — the `/evaluate/` page spec that consumes this journey.

## Assumptions

- Defaulted: Product: the stub is a future-state journey and is not approved through `approve-journey` in this slice — default: approval is a separate owner gesture; if wrong: the slice adds an approval step before the page spec freezes its reader (settled by: eugenelim).
- Defaulted: Technical: the claim labels are matched as the nine strings above, case-insensitively — default: the labels in the parent intent's `What the decision requires` are the authority; if wrong: the check reads the labels from one list the page spec also uses (settled by: eugenelim).
- Technical: whether the new lint belongs in `tools/` with a CI step, or as a test under `tools/` run by the existing doc-tree job — default: a lint plus a workflow step, matching `lint-agents-md.py` (settled by: eugenelim, at plan time).
