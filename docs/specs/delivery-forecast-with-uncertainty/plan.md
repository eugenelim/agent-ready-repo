# Plan: delivery forecast with uncertainty

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/specs/flow-distribution-sample-honest/`
  (the ladder and the completion sample this reads);
  `packs/atlassian/.apm/skills/flow-metrics/SKILL.md` (percentiles computed at
  p50, p75 and p90 by `statistics.quantiles`, so the derivation has a shipped
  precedent in one pack); `tests/roster/test_intent_template_shape_conformance.py`
  (the pattern for a cross-pack assertion). Named deviation: no repository
  precedent renders a refusal in place of a number.


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

The forecast is the thinnest possible layer over the sibling slice's
distribution: take the completion sample, take the percentile the ladder
supports, render it as a range with its sample size. There is no model and no
simulation, so there is very little to get wrong in the arithmetic and almost
all the risk is in the rendering.

That is deliberate. The failure this slice exists to prevent is a reader
carrying away a date, and a date is produced by rendering, not by statistics.
So the rendering checks are goal-based and run over the rendered output rather
than over the values, because a correct range presented with a headline date is
exactly the failure and a value-level assertion cannot see it.

Build the derivation and the refusal first, then each provider's wiring. The
refusal is as much of the contract as the number: below the threshold this
slice must say what would make a forecast possible, not go quiet.

## Constraints

- **ADR-0125 D4** bounds the denominator: nothing below the floor is counted.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler.
- **No shared implementation across delivery systems.** Each provider pack
  holds its own copy; neither depends on the other.
- The ladder and the confidence level belong to
  `flow-distribution-sample-honest` and are consumed, not redefined.
- The observation vocabulary belongs to `delivery-state-observation`.

## Construction tests

- A derivation fixture over a known completion sample with a hand-checked
  percentile.
- A rendering check over rendered output asserting a range and a sample size
  are both present.
- A headline check over rendered output asserting no single date leads.
- A refusal fixture below the threshold asserting a named refusal and the
  absence of any number.
- A cross-provider fixture: one completion set in both systems, same forecast.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Derivation and refusal | T1 | derivation and refusal fixtures green |
| Rendering contract | T2 | rendering and headline checks green |
| Jira forecast | T3 | provider fixtures green |
| GitHub forecast | T4 | provider fixtures green |
| Cross-system agreement | T5 | identical forecasts from one completion set |
| Changelog entries and the user-facing promise | T5 | one entry per pack; the distinction drafted |

## Design (LLD)

### Design decisions

- **Empirical percentile, not Monte Carlo.** Simulation assumes a roughly
  stable item-size distribution, and item size is measured changing character
  under agentic work — 20% larger pull requests in one corpus, 154% in another.
  An empirical percentile over the real sample needs no such assumption. No
  retrieved source tests either method against agent-driven throughput, so the
  method that assumes less is the one to take.
- **The rendering is checked, not the values.** A correct range whose output
  opens with a standalone date is the failure mode, and it passes every
  value-level assertion. "Headline" is defined as the first forecast-bearing
  statement so the check locates a region rather than judging emphasis.
- **Refusal carries a remedy.** "No forecast" sends a reader back to guessing;
  "no forecast until 5 completions, and there are 3" does not.

### Data & schema

Input is the completion sample from the observation vocabulary. Output carries
the range, the percentile it represents, the sample size, and the moment the
sample was taken.

### Interfaces & contracts

No new interface. Each provider reads its own distribution.

### Component / module decomposition

Derivation and rendering duplicated in `packs/atlassian/` and `packs/github/`;
agreement assertion in `tests/roster/`.

### State & control flow

Computed on invocation. The completion sample may arrive from
`flow-metrics`' on-disk cache, so the moment carried with a forecast is the
moment that sample was **acquired from the provider**, not the moment the
forecast was rendered or the cache was read. The two are verified
independently. No resident state beyond that cache.

### Behavior & rules

A completion below ADR-0125's floor never enters the sample. Cross-team
borrowing to reach a threshold is refused rather than offered.

### Failure, edge cases & resilience

An empty sample produces the refusal with a sample size of zero, not an error.
A provider error is surfaced rather than rendered as an empty sample, because
"no completions" and "could not reach the tracker" are different facts.

### Quality attributes (NFRs)

The rendering criteria carry the pass/fail bar: range present, sample present,
no date as headline, on every rendered forecast.

### Dependencies & integration

No new dependency.

## Tasks

### T1: the derivation produces a percentile or a refusal that names its remedy

**Depends on:** spec:flow-distribution-sample-honest/T1

**Tests:**
- Empirical percentile over a hand-checked sample.
- Below threshold, a refusal naming what would make a forecast possible.
  Verifies *a refusal that names what would make a forecast possible*.
- Below threshold, no number of any confidence appears.
- No completion below the floor enters the sample.

**Done when:** the refusal fixture asserts both the named remedy and the
absence of a number.

**Touches:** packs/atlassian/.apm/skills/**, packs/github/.apm/skills/**

### T2: every rendered forecast carries its range and sample and leads with neither a date

**Depends on:** T1

**Tests:**
- Rendered output carries a range. Verifies *no rendered forecast omits its range*.
- Rendered output carries a sample size. Verifies *no rendered forecast omits the sample size*.
- The first forecast-bearing statement carries a range or a refusal; a
  fixture leading with a standalone date fails. Verifies *the first
  forecast-bearing statement contains either a range or a refusal*.
- Rendered output states the sample's moment.

**Approach:**
- The checks run over rendered output, not over the value object, because the
  failure is a presentation failure and is invisible at the value level.

**Done when:** all four checks run over rendered output and a fixture rendering
a headline date fails them.

**Touches:** packs/atlassian/.apm/skills/**, packs/github/.apm/skills/**

### T3: Jira Software forecasts from its own distribution

**Depends on:** T2, spec:flow-distribution-sample-honest/T2

**Tests:**
- Provider fixtures produce a forecast meeting the rendering contract.

**Done when:** the Jira fixtures are green.

**Touches:** packs/atlassian/.apm/skills/**

### T4: GitHub Issues + Projects forecasts from its own distribution

**Depends on:** T2, spec:flow-distribution-sample-honest/T3

**Tests:**
- The same obligations as T3, against GitHub completions.
- Neither pack imports from the other.

**Done when:** the GitHub fixtures are green with no reference to
`packs/atlassian`.

**Touches:** packs/github/.apm/skills/**

### T5: one completion set yields identical forecasts on both systems

**Depends on:** T3, T4

**Tests:**
- The cross-provider fixture yields identical forecasts.
- A forecast leaves no resident process.

**Done when:** the repository-level assertion is green, both packs lead a
changelog entry, and the range-not-a-date distinction is drafted on the
user-facing surface.

**Touches:** tests/roster/**, packs/atlassian/CHANGELOG.md, packs/github/CHANGELOG.md

## Rollout

T1 and T2 are inert until a provider calls them. T3 and T4 are independent.
T5 gates.

## Risks

- **A correct range read as a commitment.** Mitigated by the headline check and
  by the user-facing promise being a durable output rather than a footnote.
- **Refusal becomes silence.** Mitigated by asserting the named remedy, not the
  absence of a number.
- **Empirical percentiles may degrade under agentic throughput too.** Recorded
  as an open assumption; no source tests it either way, and taking the method
  that assumes least is the response available now.

## Changelog

- 2026-09-24 — plan drafted.
