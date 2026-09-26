# Spec: tracker working view jira align

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0127; ADR-0077; ADR-0019; ADR-0033
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

A programme running Jira Align sees its canonical intent tree rendered at the
portfolio depth Jira Align actually carries, so the rollup a programme reports
on is the tree rather than a hand-built parallel. Success is that the two
product rungs land above the portfolio Epic rather than being flattened into
it.

## What Changes

- A Jira Align projection renders ADR-0127's range across the Theme, Epic,
  Feature and Story tiers with a back-reference — `packs/atlassian/`
- The Jira Align column in the shared profile table is reconciled against
  ADR-0127's range — authored by the pattern slice, exercised here

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the projection uses the Jira Align client's record creation, and its refresh processor stays fail-closed | `packs/atlassian/.apm/skills/jira-align/` | this spec | creation confirmed through the bounded action set; the refresh processor unchanged | no return-leg action is added to a fail-closed processor by this slice |
| Maintainer procedure | Applicable — the Jira Align column predates ADR-0127 | `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md` | pattern slice | the column resolves against a real Jira Align render | the render matches every row |
| Release history | Applicable — `atlassian` changes | `packs/atlassian/CHANGELOG.md` | this spec | one entry | the pack leads its own entry |
| Current architecture | Not applicable — this slice conforms to the pattern the Jira Software slice documents | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Expand onto Jira Align's depth rather than collapsing: the two product rungs
  land above the portfolio Epic, at the Theme or Strategy tier.
- Carry the canonical identity on every projected record, and the record
  identity where a repository reader can find it.
- Treat the back-reference as the projection key.
- Name the Jira Align tier a rung landed on, because the same word names a
  different tier in Jira Software.

### Ask first

- Using the Capability or Solution tier, which applies to multi-ART programmes
  and not to every adopter.
- Any change to the Jira Align refresh processor's fail-closed refusal.

### Never do

- Violate ADR-0019 D5 as ADR-0077 D6-D12 refine it, by letting anything read
  off the tracker acquire authority over canonical intent.
- Violate ADR-0127 D4 by projecting an agent-internal unit as a managed item,
  or D4a by projecting a same-repository delivery brief.
- Violate CAP-0004's no-new-runtime guardrail.
- Re-decide a variation point the Jira Software slice's pattern already settles.
- Add a return-leg write action to the Jira Align refresh processor. It refuses
  by design, because the client exposes generic record updates rather than a
  bounded set, and this slice does not carry that work.
- Assume a Jira Align Feature and a Jira Software Epic are the same object.

## Testing Strategy

- **Tier expansion: TDD.** Which rung lands on Theme, Epic, Feature or Story is
  a pure function of the tree and the profile row, including the case where the
  tree is shallower than Jira Align's depth. The positive criteria are driven
  by one **reference tree** carrying every rung in the range, so a projector
  that emits nothing fails rather than passing the exclusions.
- **Idempotency: TDD**, against fixtures, reusing the pattern slice's shape.
- **Return-leg refusal: goal-based.** A return-leg action against Jira Align is
  asserted to refuse, so the fail-closed behaviour is pinned rather than
  assumed.
- **The write path: goal-based, manual QA**, evidenced by a recorded
  confirmation transcript.

## Acceptance Criteria

- [ ] Projecting the reference tree yields one Jira Align record for every rung
      in ADR-0127's range, down to and including the floor rung. A run yielding
      zero records fails.
- [ ] The rollup from the floor rung to the top rung of that projection
      resolves across the Jira Align tiers.
- [ ] A projected Jira Align record names the canonical artifact it came from.
- [ ] A repository reader can determine which Jira Align record a rung was
      projected to, from the repository alone.
- [ ] Each projected record records the Jira Align tier it occupies, by tier
      name rather than by work-type word.
- [ ] The two product rungs project above the portfolio Epic rather than onto
      it.
- [ ] A tree shallower than Jira Align's depth leaves the unused tiers empty
      rather than inventing a rung to fill them.
- [ ] Record creation refuses without a single-use, session-fresh confirmation
      carrying approver evidence and showing the exact payload.
- [ ] One fresh confirmation creates exactly one intended record.
- [ ] Projecting an unchanged tree a second time changes no record count.
- [ ] A return-leg action against Jira Align refuses, and the refusal names
      that the processor is fail-closed.
- [ ] The Jira Align profile declares the create capability and no return-leg
      action, so the fail-closed refusal survives this slice.
- [ ] Before that declaration lands, the create action refuses for Jira Align
      even though it is present in the shared action set.
- [ ] Repository scope is derived from the canonical artifact's owning
      repository and the projection target's, not from a hand-maintained list.
- [ ] A delivery brief whose work stays in the canonical artifact's own
      repository produces no Jira Align object.
- [ ] A delivery brief whose work crosses a repository boundary produces
      exactly one managed Jira Align record.
- [ ] An agent-internal unit produces no Jira Align object that is scheduled,
      assigned or counted.
- [ ] Projection runs only when invoked and leaves no resident process.

## Follow-ons

- eugenelim: `docs/product/briefs/intent-backed-working-view.md` — a Jira Align
  return leg needs the fail-closed processor to gain a bounded action set, which
  is not this slice's work and has no spec.

## Assumptions

- Whether a Jira Align Feature is a Jira Software Epic on sync. The shipped
  profile table states it as fact; survey F6 records it as resting on a search
  snippet rather than a verified read. It decides whether a tree projected to
  both systems produces one object or two at that tier, and only a read against
  a live Jira Align to Jira Software sync settles it.
