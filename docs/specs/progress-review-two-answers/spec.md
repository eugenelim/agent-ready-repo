# Spec: progress review two answers

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0125
- **Brief:** brief:timeline-and-strategic-progress-review
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

A team and the people it reports to get two answers in one place — when work is
likely to land, and what the work was supposed to change — without either
standing in for the other. Success is that an outcome nobody has checked is as
visible as one that moved.

## What Changes

- A review renders an intent's declared outcome verbatim beside the delivery
  answer — `packs/product-engineering/`
- An outcome with nothing recorded against it renders as its declaration above
  an explicit nothing, never as a blank or an omitted row —
  `packs/product-engineering/`
- A review with no forecast available says so rather than dropping the
  delivery answer — `packs/product-engineering/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the review is a skill an adopter runs and extends | `packs/product-engineering/` | this spec | the skill, stating both answers and both degradations | the skill names what it renders when each input is absent |
| User promise | Applicable — the review is read by people outside the team, and the two separations are the promise | the established user-documentation surface | this spec | the separations stated where a reader meets a review | drafted before implementation approval |
| Release history | Applicable — `product-engineering` changes | `packs/product-engineering/CHANGELOG.md` | this spec | one entry | the pack leads its own entry |
| Current architecture | Not applicable — the review composes existing surfaces and introduces no new structure | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Render each in-scope intent's whole `## Outcome` section verbatim, whatever
  it contains, labelled as declared.
- State the review's scope as a closed, enumerable set, and render every intent
  in it.
- Render the outcome answer without interpreting whether a reading exists. The
  repository defines no reading representation, so the review reports the
  section and adds nothing.
- Keep the two answers in separate parts of the review, each readable alone.
- Resolve the intent tree through the adopter's configured `[product]
  output_dir`, not an assumed path.
- Say which inputs were present and which were absent.

### Ask first

- Rendering a third answer. Two is the contract, and a third invites the
  collapse the review exists to prevent.
- Reading anything a delivery system holds. The review reads repository
  artifacts and takes a forecast as supplied input.

### Never do

- Grade, score or judge what an `## Outcome` section contains. The review
  renders what is there.
- Define, require or detect a reading representation inside `## Outcome`. That
  section's contract belongs to `frame-intent`, and the accepted cut carries no
  slice that adds one.
- Omit an in-scope intent for any reason, including that its outcome section
  carries nothing beyond its declarations.
- Present delivery completion as evidence of outcome movement.
- Present a forecast as a committed date.

- Call a delivery-system skill, or depend on a provider pack.
- Violate CAP-0004's no-new-runtime guardrail.

## Testing Strategy

- **Outcome rendering: goal-based check.** The rendered review is checked
  against the intent's `## Outcome` text for verbatim reproduction. A
  paraphrase fails.
- **Scope completeness: TDD.** Over a fixture tree, removing any single intent
  from the rendered review fails the check. Asserting that *an* intent appears
  would pass while another is silently dropped, which is the selection effect
  this slice exists to defeat.
- **Degradation: TDD.** With no forecast supplied, the review renders the
  delivery answer as unavailable and still renders the outcome answer.
- **Separation: goal-based check.** The two answers are checked to occupy
  distinct parts of the rendered review, so neither can be read as the other.
- **Path resolution: TDD.** The intent tree resolves through the configured
  `output_dir`, including when it is absolute and when it is unset.

## Acceptance Criteria

- [ ] The review states its scope as a closed, enumerable set of intents.
- [ ] Every intent in that scope appears in the rendered review. Omitting any
      one fails.
- [ ] Each appearing intent's whole `## Outcome` section is reproduced
      verbatim, labelled as declared.
- [ ] An intent whose `## Outcome` section carries nothing beyond its declared
      measures renders those measures above an explicit statement that the
      repository records nothing further, rather than a blank or an omitted
      row.
- [ ] The review classifies no intent as checked or unchecked, and renders no
      such label.
- [ ] The delivery answer and the outcome answer occupy distinct parts of the
      rendered review.
- [ ] With no forecast supplied, the review states the delivery answer is
      unavailable and still renders the outcome answer.
- [ ] With no intent tree resolvable, the review says so rather than rendering
      an empty review.
- [ ] No rendered review presents delivery completion as outcome movement.
- [ ] No rendered review presents a forecast as a committed date.
- [ ] The review renders no score, grade or judgement of a recorded reading.
- [ ] The intent tree resolves through the adopter's configured `[product]
      output_dir`.
- [ ] The review calls no delivery-system skill, and
      `packs/product-engineering` declares no provider pack as a dependency.
- [ ] A review runs only when invoked and leaves no resident process.

## Follow-ons

none

## Assumptions

- What counts as evidence that an outcome moved. The accepted cut carries no
  slice that adjudicates it, so it is a judgement made by whoever writes into
  an intent's `## Outcome` section. The review reproduces that section without
  grading it, so an unconvincing entry and a strong one look the same.
  Answerable only once adopters have written some.
- Whether reproducing a whole `## Outcome` section verbatim stays readable as
  the reviewed set grows. Truncating it would reintroduce a judgement about
  what matters, which this slice refuses, so the trade-off is visible rather
  than resolved.
