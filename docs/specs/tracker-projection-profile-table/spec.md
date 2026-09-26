# Spec: tracker projection profile table

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0127; ADR-0033
- **Brief:** brief:intent-backed-working-view
- **Discovery:** none
- **Contract:** none
- **Shape:** integration


> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->


## Outcome

Anyone projecting a canonical intent tree onto a delivery system can read, from
one table, which object each rung becomes and whether that object is managed.
Success is that the answer is the same for a person projecting by hand and for
a runner checking a projection, because both read the same classification.

## What Changes

- Every cell of the level-to-object profile table carries an explicit
  `managed | trace | none` classification —
  `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
- The table's leaf and story-as-trace rows stop classifying below-floor objects
  as managed, and the canonical column gains a cross-repository delivery-brief
  rung — same file
- Jira Software gains a column — same file
- A runner resolves every row against ADR-0127 by reading classifications —
  `packs/product-engineering/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the table is the procedure a person follows to project by hand, and today its cells are free prose | `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md` | this spec | the classified, reconciled table | every row resolves against ADR-0127 by classification |
| Release history | Applicable — `product-engineering` changes | `packs/product-engineering/CHANGELOG.md` | this spec | one entry | the pack leads its own entry |
| Current architecture | Not applicable — this slice changes a reference table, not a structure | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Give every cell exactly one classification from the closed set.
- Keep one spelling per provider-object token across the whole table.
- Resolve each row against ADR-0127 D1 through D4a from the classifications.

### Ask first

- Adding a column for a delivery system whose own slice has not started.
- Changing a classification that a shipped projection already relies on.

### Never do

- Violate ADR-0127 D4 by classifying a below-floor object as `managed`, or
  D4a by giving a same-repository delivery brief any row.
- Decide the classification by reading a cell's prose.
- Add a fifth classification value.

## Testing Strategy

- **Classification coverage: goal-based check.** Every cell is parsed for a
  value from the closed set; an unclassified cell fails.
- **Token consistency: goal-based check.** Each provider-object token is
  asserted to have one spelling and one classification table-wide. The shipped
  table holds 19 distinct free-text tokens across four columns, including two
  spellings of the same object and a name carrying bold markup, so this check
  is what makes the rest mechanizable.
- **Clause resolution: goal-based check.** One runner resolves every row
  against ADR-0127 D1 through D4a from the classifications, and fails on a
  below-floor `managed`.

## Acceptance Criteria

- [ ] Every cell of the profile table carries an explicit classification from
      the closed set `managed | trace | none`, in a form a runner parses
      without interpreting prose.
- [ ] Each provider-object token appears with exactly one spelling and one
      classification across the whole table.
- [ ] Every row resolves against ADR-0127 D1 through D4a by reading those
      classifications. The runner reads no free text to decide whether an
      object is managed.
- [ ] No table cell maps a rung below the floor to an object its provider
      schedules, assigns or counts.
- [ ] The table carries a canonical rung for a cross-repository delivery brief.
- [ ] The table carries a Jira Software column.
- [ ] The runner reads the table file, so a column a later slice adds is
      covered without editing the runner.

## Follow-ons

- eugenelim: `docs/specs/tracker-working-view-github/spec.md` — the GitHub
  column is that slice's to add, and this runner covers it when it lands.

## Assumptions

none
