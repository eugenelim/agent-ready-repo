# Spec: flow distribution sample honest

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0127
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

A team sees cycle time, throughput and their distribution over its work, and
never sees a number its data cannot support. The computation works over any
scope the delivery system can express; restricting it to intent-backed work
is a filter a caller may apply, not what the computation is. Success is
that a thin sample produces a weaker claim rather than a confident one, and
never silence.

## What Changes

- Percentile reporting is gated by a sample-size table derived from the
  distribution-free tolerance bound `n >= ln(1 - g) / ln(p)` at the confidence
  the parent records, which yields 5 completions for a median, 11 for p75 and
  29 for p90 — `packs/atlassian/`, `packs/github/`
- Jira Software's distribution is computed over the observation vocabulary —
  `packs/atlassian/`
- GitHub Issues + Projects gets its own distribution computation, independently
  — `packs/github/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — a fifth delivery system needs to know the ladder and the degradation rule | each provider pack's SKILL.md | this spec | the ladder and the degradation order stated per pack | both packs state the same thresholds |
| Release history | Applicable — `atlassian` and `github` both change | each pack's changelog | this spec | one entry per pack | each changed pack leads its own entry |
| Current architecture | Not applicable — the observation vocabulary is the sibling slice's output and this consumes it | — | — | — | — |
| Decision rationale | Not applicable — the ladder is arithmetic from a distribution-free tolerance bound, not a choice between options | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Report the strongest claim the sample supports, and name the sample size
  beside it.
- Degrade rather than refuse: below the median threshold, a count, a range or
  a mean is still reportable.
- State the moment the sample was taken.
- Compute against the observation vocabulary rather than a provider's own
  metric names.

### Ask first

- Reporting at a confidence other than 95%. The parent records 95% as the
  owner's choice and carries the 90% column beside it.
- Adding a percentile beyond p50, p75 and p90.

### Never do

- Render a percentile whose sample is below its threshold.
- Report silence when the sample is thin. A thin sample is labelled thin.
- Violate ADR-0127 D4 by counting anything below the floor.
- Render a throughput comparison across windows, or call a throughput figure
  an improvement. The parent's guardrail is that a rise is never reported as
  an improvement when the unit itself got bigger, and no measure available
  from a delivery system establishes that the unit was unchanged between two
  windows. A cycle-time distribution does not: a longer cycle time is equally
  consistent with bigger items and with a slower process. The guardrail is
  therefore discharged by not making the comparison, not by pairing it with a
  proxy.
- Borrow or aggregate another team's completions to reach a threshold.
- Share an implementation between provider packs, or make one depend on
  another.

## Testing Strategy

- **The gating table: TDD.** The thresholds are computed from the tolerance
  bound at the recorded confidence, and the test drives the computation rather
  than the resulting integers — so changing the confidence moves the table and
  the test with it. Both sides of every boundary in the emitted set are
  enumerated.
- **Degradation order: TDD.** At `n` below 5 the output is a count, a range or
  a mean, and never empty.
- **Per-provider computation: TDD**, against recorded completion fixtures.
- **Cross-system agreement: TDD, integration surface.** Agreement is asserted
  at every threshold boundary in the emitted set, not at one convenient sample
  size — two copies can agree at n=50 and disagree at n=11. This is what makes
  the duplicated arithmetic safe.
- **Filter default: TDD, one fixture, one variable.** Both runs derive from
  one recorded completion set with one recorded acquisition moment, and
  membership is asserted by identity. Asserting that two runs "differ" passes
  when they differ because of acquisition time, cache state or a provider
  change, none of which is the filter.
- **Freshness under cache: TDD.** A cache-hit fixture asserts the original
  acquisition moment survives and does not become render time.
- **Single-window interface: TDD.** A request naming a second window is
  asserted to refuse, and every output form is checked for a cross-window
  value. Checking the rendered view alone leaves the comparison computable
  and returnable by another path.

## Acceptance Criteria

- [ ] The gating table is computed from `n >= ln(1 - g) / ln(p)` at the
      recorded confidence and the emitted percentile set, not written as
      literals in either pack.
- [ ] That computation yields a threshold of 5 for the median, 11 for p75 and
      29 for p90 at 95% confidence.
- [ ] For every percentile in the emitted set, a sample one below its computed
      threshold renders no value for that percentile.
- [ ] For every percentile in the emitted set, a sample at its computed
      threshold renders a value for that percentile.
- [ ] A sample below the median threshold renders a count, a range or a mean
      rather than nothing.
- [ ] Every rendered percentile names the sample size behind it.
- [ ] Every rendered reading states the moment the sample was acquired from
      the provider, not the moment it was rendered.
- [ ] A reading served from `flow-metrics`' on-disk cache carries the
      original acquisition moment, and it is distinguishable from render
      time.
- [ ] Both packs derive their gating table from the same formula and confidence
      and produce the same thresholds.
- [ ] At each threshold boundary in the emitted set, the same completion set
      represented in both delivery systems yields identical output from both
      computations.
- [ ] Every completion is classified into exactly one of four dispositions:
      provider-native and non-projected; projected with a resolved floor and
      at or above it; projected with a resolved floor and below it; or origin
      or floor unresolved.
- [ ] A provider-native, non-projected completion is included. Absence of intent
      linkage is not by itself proof of this: ADR-0127 D5 resolves a floor
      from whether work crosses a repository boundary.
- [ ] A projected completion at or above its resolved floor is included.
- [ ] A projected completion below its resolved floor is excluded.
- [ ] An completion whose origin or floor cannot be resolved is excluded and named
      in the output, never silently dropped and never counted.
- [ ] No completion falls outside the four dispositions. A fixture containing one
      of each, plus one contrived to escape them, fails on the last.
- [ ] Both filter runs derive from one recorded completion set with one
      recorded acquisition moment, and nothing but the filter varies between
      them.
- [ ] Over a non-empty provider-native set, omitting the filter includes
      every completion in it, asserted by exact membership rather than by the
      two runs differing.
- [ ] Over a mixed set, the omitted-filter run's membership is the whole set
      and the supplied-filter run's membership is exactly the intent-backed
      subset, both asserted by identity.
- [ ] Resolving intent linkage happens in a skill the pack declares as a
      bridge, never in this computation.
- [ ] Throughput renders as a count for one stated window, with its sample.
- [ ] The interface accepts exactly one window. A request naming a second
      window, or a comparison window, is refused.
- [ ] No output of any form — rendered, structured, or returned to a caller —
      carries a cross-window throughput value, delta, percentage change or
      trend indicator. Forbidding it only in the rendered view would leave an
      implementation free to compute and return it elsewhere.
- [ ] No rendered output characterises a throughput figure as an
      improvement, a regression, or progress.
- [ ] Neither provider pack imports from the other, and neither declares the
      other as a dependency.
- [ ] A computation runs only when invoked and leaves no resident process.

## Follow-ons

- eugenelim: a throughput trend across windows. It becomes renderable once a
  size measure exists that can establish the unit was unchanged between them.
  No delivery system supplies one today; the survey's item-size evidence is a
  pull-request measure, which is a code signal rather than a tracker one.

## Assumptions

none
