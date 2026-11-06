# Spec: Intent indexes for the three remaining doctrine packs

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** RFC-0071 M6 (ordering waived for this slice, recorded in the brief); ADR-0020
- **Brief:** brief:digital-product-guides-delivery
- **Discovery:** intent:digital-product-guides-update
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

An adopter of `product-strategy`, `product-engineering` or `frontend-engineering` finds a pack-wide index that routes each thing they want to do to a registered skill. Every route in each index resolves, and a test fails on a dead route.

## What Changes

- A pack-wide intent index in each of `guides/product-strategy/`, `guides/product-engineering/` and `guides/frontend-engineering/`, shaped like the existing `guides/experience-design/README.md` start-here and more lists.
- A test that reads each index and checks every route names a registered skill and an existing guide page.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Adopters route from intent to skill | The three pack guide READMEs | eugenelim | The test and the rendered links | close-work verifies the test passes |
| Guide index | `tools/check-guide-index.py` already requires a home link per pack | `guides/README.md` unchanged | eugenelim | Guide-index check passes | none |

## Agent Rules

### Always do

- Follow the `docs-job-pages` page conventions.
- Write each index entry as a user intent, not a skill name.
- Reuse the skill description phrases, verbatim where they carry a quoted example.

### Ask first

- Changing `docs-job-pages` structure.
- Adding a new frontmatter key.

### Never do

- Index a skill that is not registered in the pack manifest.
- Touch `packs/` content.

## Testing Strategy

Goal-based: the new route test passes on the tree and fails on a seeded dead route. Guide-index check passes. The audit tool shows the new indexes without regressing any file.

## Acceptance Criteria

- [ ] **AC1.** Each of the three guide READMEs lists at least one route per registered skill of its pack, or marks the skill as covered by a named route.
- [ ] **AC2.** A test fails when a route names an unregistered skill and when a route names a missing guide page.
- [ ] **AC3.** `python3 tools/check-guide-index.py` exits zero.
- [ ] **AC4.** The audit tool reports no regression in any existing guide file's affordances.

## Follow-ons

- eugenelim: `brief:digital-product-guides-delivery` slices G2 and G3.

## Assumptions

- Open question for eugenelim: where the route test lives. Recommended default: a new test under `tools/` next to `check-guide-index.py`, not under `packs/`.
- The experience-design README is the shape reference; the other three packs' skills count (strategy 9 skills, product-engineering 12, frontend 9) is read from each pack manifest at authoring time.
