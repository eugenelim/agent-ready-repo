# Plan: flow distribution sample honest

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/atlassian/.apm/skills/flow-metrics/SKILL.md`
  (nine metrics from Jira changelogs at p50, p75 and p90; Jira-only by pack, so
  it is extended here and not moved); `docs/specs/delivery-state-observation/`
  (the vocabulary this computes over);
  `tests/roster/test_intent_template_shape_conformance.py` (the pattern for a
  cross-pack assertion). Named deviation: the GitHub computation has no
  incumbent to extend and is written from the ladder.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

The ladder is the whole contract and it is arithmetic, not a policy: against a
distribution-free tolerance bound at 95% confidence, 5 completions support a
median, 11 a p75 and 29 a p90. Those thresholds land on the percentile set
`flow-metrics` already emits, so the gate and the incumbent surface describe
the same three numbers.

Build the ladder first, as a provider-free function of sample size, then wire
it into each provider's computation. Jira's extends `flow-metrics` in place.
GitHub's is written fresh in its own pack, because `flow-metrics` sits inside a
provider pack and does not move.

The riskiest part is degradation. The failure this slice exists to prevent is a
confident percentile over four items; the failure it must not introduce is
silence, which sends the reader back to guessing. So every below-threshold case
has a named weaker output, and the tests assert the output rather than the
absence of the percentile.

## Constraints

- **ADR-0127 D4** bounds the denominator: nothing below the floor is counted.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler.
- **No shared implementation across delivery systems.** `flow-metrics` stays in
  `packs/atlassian` and GitHub gets its own copy; neither pack depends on the
  other.
- 95% confidence is the owner's recorded choice; the parent carries the 90%
  column beside it and changing it is an ask-first.
- The observation vocabulary is the sibling slice's output and is consumed, not
  re-defined.

## Construction tests

- The gating table computed from the tolerance bound at the recorded
  confidence, asserted to yield 5, 11 and 29 at 95%.
- Both sides of every boundary the computed table produces, since an off-by-one
  here renders a confident number over a sample that cannot carry it.
- A degradation fixture at `n` below 5 asserting a count, a range or a mean is
  present.
- Per-provider completion fixtures.
- A cross-provider fixture at each computed boundary: the same completion set
  in both systems, asserted to yield identical output. One sample size is not
  enough — two copies can agree at n=50 and disagree at n=11.
- A throughput fixture asserting no second-window figure, delta, percentage
  change or trend indicator appears in rendered output.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Computed gating table and degradation rule | T1 | no literal thresholds; both sides of every boundary green |
| Jira distribution | T2 | provider fixtures green |
| GitHub distribution | T3 | provider fixtures green |
| Cross-system agreement | T4 | identical output at every computed boundary |
| Changelog entries for `atlassian` and `github` | T4 | one entry per pack |

## Design (LLD)

### Design decisions

- **The table is computed, not written.** The thresholds follow from
  `n >= ln(1 - g) / ln(p)` at the recorded confidence and the emitted
  percentile set. Written as literals they are three scalars that decay
  silently if the confidence or the percentile set changes at source; computed,
  they move with it.
- **The gate is a function of sample size alone.** It takes no provider and no
  metric, so both packs can hold identical copies that are trivially
  comparable.
- **Degradation is specified per band, not as a fallback.** "Below 5" has a
  named output rather than a default, because a default is what becomes silence
  under an edge case nobody enumerated.
- **The derivation is duplicated, not shared.** Two copies of one formula is
  the cost of independent packs; the boundary-by-boundary cross-provider
  assertion is what keeps them equal.
- **Throughput renders for one window and is never compared.** The parent's
  guardrail is that a rise is not reported as an improvement when the unit
  grew. No measure a delivery system supplies establishes that the unit was
  unchanged between two windows — a cycle-time distribution does not, since a
  longer cycle time fits bigger items and a slower process equally. Pairing
  the count with a proxy would look like a discharge and not be one, so the
  slice declines the comparison instead.

### Data & schema

Input is a set of completions drawn from the observation vocabulary, each with
a start and an end moment. Output carries the percentile values that the sample
supports, the sample size, and the moment the sample was taken.

### Interfaces & contracts

No new interface. Each provider computes through the client its pack ships.

### Component / module decomposition

Jira computation extends `packs/atlassian/.apm/skills/flow-metrics/`; GitHub
computation lands in `packs/github/`; the agreement assertion in
`tests/roster/`.

### State & control flow

A distribution is computed on invocation. The Jira source reads through
`flow-metrics`, which serves an on-disk cache at
`.context/flow-metrics/cache/`, so a sample may be cached and the moment
carried with the result is the moment the sample was **acquired from the
provider**, not the moment it was rendered. Retaining that distinction needs
the acquisition moment stored in the cached record rather than recomputed on
read. No resident state beyond that cache.

### Behavior & rules

Every completion takes exactly one of four dispositions, and one whose
origin or floor cannot be resolved is excluded and named rather than counted.
Throughput is computed for one window only: the interface accepts no second
window, so no cross-window value exists to render. Cross-team aggregation to
reach a threshold is refused rather than offered.

### Failure, edge cases & resilience

An empty completion set returns a count of zero with all percentiles absent,
which is a valid answer. A provider error is surfaced rather than rendered as a
zero sample, because zero completions and an unreachable provider are different
facts that a reader would act on differently.

### Quality attributes (NFRs)

The ladder is the pass/fail bar: no percentile renders below its threshold, at
any of the three boundaries.

### Dependencies & integration

No new dependency. Both packs already hold their transport.

## Tasks

### T1: the gating table is computed from the bound and gates every percentile

**Depends on:** none

**Tests:**
- The table is computed from `n >= ln(1 - g) / ln(p)`, with no literal
  thresholds in either pack. Verifies *computed from the bound, not written as
  literals*.
- At 95% the computation yields 5, 11 and 29. Verifies *yields a threshold of
  5, 11 and 29*.
- For every percentile in the emitted set, one below its computed threshold
  renders nothing for it and the threshold itself renders a value. Verifies
  both boundary criteria.
- Below the median threshold, a count, a range or a mean is present. Verifies
  *renders a count, a range or a mean rather than nothing*.

**Approach:**
- The test drives the computation, not the resulting integers, so changing the
  recorded confidence moves the table and the assertions together.
- Written as a function of sample size with no provider argument, so both packs
  hold comparable copies.

**Done when:** no threshold appears as a literal, both sides of every computed
boundary are asserted, and the below-threshold case asserts an output rather
than an absence.

**Touches:** packs/atlassian/.apm/skills/flow-metrics/**, packs/github/.apm/skills/**

### T2: Jira Software reports a gated distribution over the vocabulary

**Depends on:** T1, spec:delivery-state-observation/T2

**Tests:**
- Completion fixtures produce gated percentiles naming their sample size and
  the moment it was taken.
- No completion below the floor enters the sample.
- Throughput renders as a count for one stated window with its sample, and
  rendered output carries no cross-window comparison and no improvement
  characterisation. Verifies those three criteria.

**Done when:** the Jira fixtures are green and `flow-metrics` reports the gate
rather than bare percentiles.

**Touches:** packs/atlassian/.apm/skills/flow-metrics/**

### T3: GitHub Issues + Projects reports its own gated distribution

**Depends on:** T1, spec:delivery-state-observation/T3

**Tests:**
- The same fixture obligations as T2, against GitHub completions.
- Neither pack imports from the other.
- Both packs derive the table from the same formula and produce the same
  thresholds. Verifies *both packs derive their gating table from the same
  formula*.

**Approach:**
- Written from the ladder and the vocabulary rather than from T2's code, since
  `flow-metrics` does not leave `packs/atlassian`.

**Done when:** the GitHub fixtures are green with no reference to
`packs/atlassian`.

**Touches:** packs/github/.apm/skills/**

### T4: one completion set yields identical percentiles on both systems

**Depends on:** T2, T3

**Tests:**
- At each computed boundary, the same completion set in both systems yields
  identical output. Verifies *at each threshold boundary ... identical output
  from both computations*.
- A computation leaves no resident process.

**Done when:** the repository-level assertion is green and both packs lead a
changelog entry.

**Touches:** tests/roster/**, packs/atlassian/CHANGELOG.md, packs/github/CHANGELOG.md

## Rollout

T1 lands first and is inert until a provider calls it. T2 and T3 are
independent. T4 gates: until it is green the two copies of the ladder are only
believed to agree.

## Risks

- **An off-by-one at a boundary.** Mitigated by asserting both sides of every
  computed boundary rather than spot-checking one.
- **Degradation becomes silence under an unenumerated case.** Mitigated by
  asserting the presence of a weaker output rather than the absence of a
  percentile.
- **The two copies drift at a boundary the fixture does not visit.** Mitigated
  by asserting agreement at every computed boundary rather than at one
  convenient sample size.

## Changelog

- 2026-09-24 — plan drafted.
