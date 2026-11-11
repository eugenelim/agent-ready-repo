# Spec: Operating-model canvas, marketing route and README embed

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** `cohort-orientation-surfaces` intent; `docs/design/direction/marketing-site.md`; RFC-0076 D10
- **Brief:** brief:cohort-orientation-surfaces-delivery
- **Discovery:** intent:cohort-orientation-surfaces
- **Depends on:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

An adoption champion can explain the AI-supervised operating model from one published canvas without translating internal gate codes. The canvas appears on a marketing route and in the README with a complete text alternative.

## What Changes

- A canvas carrier decision (one paper-first SVG, no dark variant) and a token-backed generator that produces every rendering from one source.
- A marketing route for the canvas and a README embed with a text alternative that names the five relationships (stations in order, work sequence inside proving the model, human decisions, repository as source of truth with one-way tracker projection, no autonomous approval, merge or production ship).
- An exact-markup regression test for the README and a contrast check.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Operating-model explanation | Marketing route and `README.md` | eugenelim | Rendered-output test and markup test | close-work verifies the tests pass |
| Decision rationale | Carrier decision | This spec and the canvas design record | eugenelim | Decision recorded | none |

## Agent Rules

### Always do

- Generate every rendering from the paper-first tokens.
- Keep the text alternative complete.
- Apply 4.5:1 for text and 3:1 for non-text pairs, as the marketing direction's section "The press state is a ground shift" applies.

### Ask first

- Editing `site.toml` shared chrome; slice C3 is its single editor.
- Shipping the headline before the owner approves it.

### Never do

- Add a dark variant.
- Hand-edit a generated asset.

## Testing Strategy

TDD for the generator reproducibility and the contrast script; goal-based for the README markup test and the `web` build with the rendered-output test.

## Acceptance Criteria

- [ ] **AC1.** The generator output is byte-identical on two runs.
- [ ] **AC2.** All text pairs meet 4.5:1 and all non-text pairs meet 3:1, checked by script.
- [ ] **AC3.** The README embed passes an exact-markup test against GitHub's sanitiser rules recorded in the canvas design record.
- [ ] **AC4.** The text alternative names all five relationships.
- [ ] **AC5.** The `web` build and rendered-output test pass with the marketing route present.
- [ ] **AC6.** The owner approves the drafted headline before ship.

## Follow-ons

- eugenelim: raster and unfurl export; visual review; reader test (`brief:cohort-orientation-surfaces-delivery` follow-ups).

## Assumptions

- Open question for eugenelim: the headline wording; recommended default is an agent draft to the design packet's contract (at most ten words, the team's situation before any mechanism), approved before ship.
- Ordering waiver and C3's single-editor rule are recorded in the brief; this slice does not touch `site.toml`.
