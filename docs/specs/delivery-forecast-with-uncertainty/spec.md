# Spec: delivery forecast with uncertainty

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

A team and the people it reports to see when work is likely to land, as a range
with the sample behind it, and cannot mistake it for a date somebody committed
to. Success is that a reader who wanted a single date leaves with a range they
can act on rather than a number they will quote back.

## What Changes

- A forecast is derived from the observed completion distribution by empirical
  percentile, with no simulation — `packs/atlassian/`, `packs/github/`
- Every rendered forecast carries its range and its sample size —
  `packs/atlassian/`, `packs/github/`
- A forecast is refused where the sample cannot support one, rather than
  rendered at low confidence — `packs/atlassian/`, `packs/github/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — a fifth delivery system needs the derivation and the refusal rule | each provider pack's SKILL.md | this spec | the derivation stated per pack | both packs state the same derivation |
| Release history | Applicable — `atlassian` and `github` both change | each pack's changelog | this spec | one entry per pack | each changed pack leads its own entry |
| User promise | Applicable — a forecast is read by people outside the team and the range-not-a-date distinction is the promise | the established user-documentation surface | this spec | the distinction stated where a reader meets a forecast | drafted before implementation approval |
| Decision rationale | Applicable — choosing empirical percentiles over Monte Carlo rests on a measured absence and should not be silently re-litigated | recorded in this spec's assumptions and the plan's design decisions | this spec | the reason stated with its evidence | the plan names why simulation was not used |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive the forecast from the observed completion distribution, by empirical
  percentile over the real sample.
- Render the range and the sample size together, in the same view as the
  forecast.
- State the moment the sample was taken.
- Refuse where the sample cannot support a forecast, and say what would make
  one possible.

### Ask first

- Reporting at a confidence other than the one the sibling slice's ladder uses.
- Presenting more than one risk-appetite pair, which practitioners use but
  which adds a second thing a reader can misquote.

### Never do

- Run a Monte Carlo simulation or any method assuming a stable item-size
  distribution.
- Lead a rendered forecast with a standalone date. The first forecast-bearing
  statement carries a range or a refusal.
- Render a forecast without its range or without its sample size.
- Violate ADR-0125 D4 by counting anything below the floor.
- Borrow another team's completions to make a forecast possible.
- Share an implementation between provider packs, or make one depend on
  another.

## Testing Strategy

- **Derivation: TDD.** Empirical percentile over a completion sample is a pure
  function with a compressible invariant.
- **Rendering completeness: goal-based check.** Every rendered forecast is
  parsed and checked to carry both a range and a sample size. A render missing
  either fails.
- **Headline shape: goal-based check.** The first forecast-bearing statement
  in rendered output is located and asserted to contain a range or a refusal.
  "Headline" is that first statement, not a judgement about emphasis.
- **Refusal: TDD.** A sample below the threshold produces a refusal naming what
  would make a forecast possible, never a low-confidence number and never
  silence.
- **Cross-system agreement: TDD, integration surface.** One completion set
  represented in both systems yields the same forecast from both computations.

## Acceptance Criteria

- [ ] A forecast is derived by empirical percentile over the observed
      completion sample.
- [ ] The range is bounded by two named percentiles from the set the sibling
      slice emits, and both endpoints are rendered.
- [ ] Each endpoint is rendered with its percentile and the schedule risk
      that percentile represents. Percentile and sample-support confidence
      are stated as separate things: the ladder's confidence is the same for
      both endpoints and says nothing about which end carries more risk.
- [ ] A forecast renders only when the sample supports both endpoint
      percentiles at their own thresholds.
- [ ] A sample supporting one endpoint but not the other yields the refusal,
      naming which endpoint is unsupported and what sample would support it.
      It is not a partial forecast and emits no forecast number.
- [ ] No rendered forecast omits its range.
- [ ] No rendered forecast omits the sample size behind it.
- [ ] The first forecast-bearing statement in a rendered forecast contains
      either a range or a refusal. A rendered forecast whose first such
      statement is a standalone date fails.
- [ ] A sample below the threshold produces a refusal that names what would
      make a forecast possible.
- [ ] A sample below the threshold produces no forecast number of any
      confidence.
- [ ] Every rendered forecast states the moment its sample was acquired from
      the provider, not the moment the forecast was rendered.
- [ ] A forecast built on a cached completion sample carries that sample's
      original acquisition moment unchanged.
- [ ] Every completion is classified into exactly one of four dispositions:
      provider-native and non-projected; projected with a resolved floor and
      at or above it; projected with a resolved floor and below it; or origin
      or floor unresolved.
- [ ] A provider-native completion and a projected completion at or above its
      resolved floor both enter the sample. Absence of intent linkage is not
      by itself proof of provider-native origin.
- [ ] A projected completion below its resolved floor never enters the
      sample.
- [ ] A completion whose origin or floor cannot be resolved is excluded and
      named, never counted.
- [ ] No completion falls outside the four dispositions. A fixture containing
      one of each, plus one contrived to escape them, fails on the last.
- [ ] Both filter runs derive from one recorded completion set with one
      recorded acquisition moment, and nothing but the filter varies between
      them.
- [ ] Over a provider-native set large enough to support both range
      endpoints, omitting the filter forecasts every completion in it,
      asserted by exact membership.
- [ ] Over a mixed set, the omitted-filter run's membership is the whole set
      and the supplied-filter run's is exactly the intent-backed subset, both
      asserted by identity. Whether the two forecasts differ is a
      consequence, not the assertion.
- [ ] Resolving intent linkage happens in a skill the pack declares as a
      bridge, never in this forecast.
- [ ] The same completion set, represented in both delivery systems, yields
      identical forecasts.
- [ ] Neither provider pack imports from the other, and neither declares the
      other as a dependency.
- [ ] A forecast runs only when invoked and leaves no resident process.

## Follow-ons

none

## Assumptions

- Whether forecast accuracy holds under agent-driven throughput. No dated
  source between 2023 and 2026 tests any throughput-based forecasting method
  against agent-driven data, and the absence was searched for directly. Item
  size is meanwhile measured changing character, which is the assumption a
  simulation would rest on — which is why this slice does not simulate. The
  open question is whether empirical percentiles degrade too, and only an
  adopter running this over a real agent-driven sample can answer it.
