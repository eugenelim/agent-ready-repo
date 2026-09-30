# Spec: delivery state observation

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0127; ADR-0077; ADR-0019
- **Brief:** brief:delivery-state-and-flow-visibility
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

A team reads where its work stands and what is holding it up, and gets the
same meaning whether it runs Jira Software or GitHub Issues + Projects. The
reading works over any scope the delivery system can express; restricting it
to intent-backed work is a filter a caller may apply, not what the reading
is. Success is that a manager comparing two teams on different delivery
systems reads the same numbers the same way, with no translation step and no
footnote explaining why one team's figures are not comparable.

## What Changes

- A provider-neutral vocabulary fixes what state, assignment, blocking and
  elapsed time mean for any work a delivery system holds — `docs/architecture/`
- Jira Software reads those four observations against that vocabulary —
  `packs/atlassian/`
- GitHub Issues + Projects reads the same four, independently, against the same
  vocabulary — `packs/github/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — the vocabulary is this slice's durable output and it binds two packs that share no code | `docs/architecture/` | this spec | the vocabulary document, defining each observation independently of any provider | every term is defined without naming a provider's field |
| Maintainer procedure | Applicable — each provider's reading is a procedure a maintainer extends for a fifth system | each provider pack's SKILL.md | this spec | the reading documented per pack | each pack states which vocabulary term each read satisfies |
| Release history | Applicable — `atlassian` and `github` both change | each pack's changelog | this spec | one entry per pack | each changed pack leads its own entry |
| Decision rationale | Deferred — whether the vocabulary binds beyond this feature, and so belongs in a decision record, is the owner's call once its reach is visible | — | lifecycle owner | — | the owner decides after this slice ships |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Define each observation so it can be evaluated against a delivery system
  neither pack supports today — neither by a provider's field name nor by a
  semantic only that provider has.
- State the moment a reading was taken. A reading has a freshness and never
  implies currency.
- Answer at zero completed items. Every observation here is a read of current
  state, not an estimate of a distribution.
- Name which vocabulary term each provider read satisfies.

### Ask first

- Adding a fifth observation to the vocabulary. Three of the four exist because
  a team asks for them daily; a fourth term changes what every future provider
  owes.
- Defining a term that only one of the two providers can satisfy.

### Never do

- Violate ADR-0019 D5 as ADR-0077 D6-D12 refine it, by letting a reading
  acquire authority over canonical intent.
- Violate ADR-0127 D4 by counting anything below the floor.
- Define a term by one provider's semantics and require the other to translate
  into it.
- Share an implementation between provider packs, or make one depend on
  another.
- Violate CAP-0004's no-new-runtime guardrail.

## Testing Strategy

- **The vocabulary: goal-based check.** Each term is checked to be defined
  without naming a provider field. A definition that names one fails.
- **Each provider's reading: TDD**, against recorded fixtures of that
  provider's real response shape.
- **Cross-system agreement: TDD, integration surface.** One **canonical work
  record** is the source of both provider representations, and its expected
  vocabulary values are declared beside it rather than inside either provider
  fixture. Each reading is compared against those declared values, not against
  the other reading — two representations hand-authored to agree would pass a
  reading-to-reading comparison and prove nothing. This is the criterion the
  slice exists for, and neither provider's own suite can see it.
- **Freshness: goal-based.** Every rendered reading is checked to carry the
  moment it was acquired from the provider.
- **Filter default: TDD, one fixture, one variable.** Both runs derive from
  one recorded provider response with the acquisition moment held fixed, and
  membership and observation values are asserted by identity. "The two runs
  differ" passes on timestamp drift alone, which is not the filter acting.

## Acceptance Criteria

- [ ] Every vocabulary term is defined without naming a provider's field.
- [ ] Over a non-empty scope containing only provider-native work, every
      reading returns a populated result with no repository artifact present.
      An empty scope does not satisfy this.
- [ ] Both filter runs derive from one recorded provider response with one
      recorded acquisition moment, and nothing but the filter varies between
      them.
- [ ] Over a mixed scope, the omitted-filter reading's item set is the whole
      scope and the supplied-filter reading's is exactly the intent-backed
      subset, both asserted by identity and by observation value rather than
      by the two readings differing.
- [ ] Resolving intent linkage happens in a skill the pack declares as a
      bridge, never in these readings.
- [ ] No vocabulary term's truth depends on a provider-specific semantic or
      capability. A term that cannot be evaluated against a delivery system
      neither pack supports fails.
- [ ] Each term carries at least one worked positive and one worked negative
      example, both stated in provider-neutral language.
- [ ] Jira Software reports state, assignment, blocking and elapsed time
      against the vocabulary.
- [ ] GitHub Issues + Projects reports the same four against the same
      vocabulary.
- [ ] Both provider representations in the agreement fixture derive from one
      canonical work record, and each carries the identity of that record.
- [ ] The expected vocabulary values for that record are declared outside both
      provider fixtures.
- [ ] Each reading matches those independently declared expected values.
- [ ] A representation that cannot prove it is that canonical record fails
      rather than being compared.
- [ ] A reading taken when no item has completed still returns all four
      observations.
- [ ] Every rendered reading states the moment it was taken.
- [ ] Every item is classified into exactly one of four dispositions:
      provider-native and non-projected; projected with a resolved floor and
      at or above it; projected with a resolved floor and below it; or origin
      or floor unresolved.
- [ ] A provider-native item and a projected item at or above its resolved
      floor are both read. Absence of intent linkage is not by itself proof
      of provider-native origin: ADR-0127 D5 resolves a floor from whether
      work crosses a repository boundary.
- [ ] No reading returns a value for a projected item below its resolved
      floor.
- [ ] An item whose origin or floor cannot be resolved is excluded and named
      in the output, never silently dropped.
- [ ] No item falls outside the four dispositions. A fixture containing one
      of each, plus one contrived to escape them, fails on the last.
- [ ] Nothing read from a delivery system updates a canonical artifact.
- [ ] Neither provider pack imports from the other, and neither declares the
      other as a dependency.
- [ ] A reading runs only when invoked and leaves no resident process.

## Follow-ons

- eugenelim: `docs/product/briefs/delivery-state-and-flow-visibility.md` —
  whether the vocabulary binds beyond this feature and belongs in a decision
  record rather than a spec. Decidable once its reach is visible.

## Assumptions

- Whether a provider-neutral definition of *blocked* survives contact with a
  third delivery system. Jira and GitHub both carry an explicit flag, and
  Linear's model was not examined for this slice. If it does not, the term
  needs either a wider definition or an explicit per-provider absence, and the
  Linear slice's author is the first to find out.
