# Brief: a progress answer that cannot hide behind one number

- **Slug:** `timeline-and-strategic-progress-review`
- **Received:** 2026-09-23
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Ready
- **Ready confirmed:** 2026-09-24 by eugenelim, lifecycle owner, **on owner authority over an open review**. Bound to revision `d32f24b3bdf7c8b8`, which returned `Findings` — one independent review round returning 8 findings, eight of them recorded and unresolved at this transition. `author-delivery-brief` requires a revision-bound `Clean`; the owner took the gate instead, and this line is the record of that. Slice membership and status are the Spec map's; this line does not restate them.
- **Parent intent:** intent:timeline-and-strategic-progress-review

**How the specs from this brief cite.** A spec names a governing artifact by
its record and clause, and states the one thing the spec must do because of it.
It does not restate what that artifact says. A paraphrase sealed inside a
frozen contract drifts from its source and is then read as authority in its own
right. A spec cites the artifact and clause directly. § Governance references below
collects what each one obliges *this brief*, for a reader of this brief; it is
not a substitute source for a spec to cite. This brief is not bound by that constraint: it states
what a source says wherever a reader needs it to follow the argument.

## Outcome

A team and the people it reports to can see, at once, when work is likely to
land and whether the outcome is actually moving — as two separate answers that
cannot be collapsed into one.

The steerable input is how often a progress answer rests on a single number
doing a job it cannot do.

## Success metrics

- **A sponsor can state the forecast's uncertainty back in their own words**,
  and can say what would count as the outcome moving, separately from what would
  count as the work finishing. This is the parent's proof signal.
- **"We do not know whether it worked" renders as a result, not an error.** The
  parent's de-risk reframed the deliverable to exactly this: an empty outcome
  column beside a confident delivery number is itself the finding, and is the
  one thing a completion metric can never produce.
- **A fixed business date and a probabilistic forecast are never
  interchangeable** in anything this produces.
- **No forecast outruns its sample.** The parent inherits the ladder its sibling
  established; a forecast states the sample it rests on.

## Scope / Non-goals

**In scope.** Carrying evidence that a declared outcome moved, producing a
delivery forecast with its uncertainty, and the review that places them beside
known scope and risk without either collapsing into the other.

**Out of scope, each with an owner.**

- **Defining what an outcome *is*.** Owned by the intent model. This brief
  consumes its steerable-input, lagging-outcome and guardrail vocabulary and
  must not invent a parallel one.
- **The observations a forecast counts.** Owned by
  [FEAT-0012](../intents/FEAT-0012-delivery-state-and-flow-visibility.md) and
  its brief.
- **Making work visible in a tracker.** Owned by
  [FEAT-0011](../intents/FEAT-0011-intent-backed-working-view.md).
- **Attribution.** Whether delivered work *caused* an observed movement is
  harder than sourcing the evidence and is excluded by the parent's boundary.
- **Any new daemon, data platform or analytics stack.** Owned by
  [CAP-0004](../intents/CAP-0004-external-tracker-projection.md)'s guardrail,
  and independently unnecessary — no method surveyed requires one.

## Current-state evidence

Measured or read on 2026-09-23.

- **The model declares outcomes and has nowhere to record whether they moved.**
  `## Outcome` appears 152 times across `docs/product/intents/`. Of the 14
  intents that reached `Fulfilled`, none records whether its declared outcome
  moved. Those 14 carry 34 distinct section types between them and not one is a
  post-ship outcome check. The gap is in the vocabulary, not in anyone's
  diligence.
- **No method requires a platform.** MSP 5th edition, PRINCE2 7, PMI's
  benefits-realisation framework and Scrum.org's Evidence-Based Management all
  describe the same shape — an owner-led review against pre-agreed baselines
  and measures, with named owners and review dates — and none of the four
  requires a data platform. No retrieved source establishes that buying one
  improves review completion. Survey F18, `[moderate]`.
- **The discipline lapses anyway, and the lapse is selective.** Ten Norwegian
  public IT projects measured about a year after completion — when their plans
  expected nearly all benefits to exist — had realised an average of 45%, while
  their owners still expected eventual realisation of 92%; only two of the ten
  had a complete written measurement plan. In a separate Australian study of 69
  organisations, 26.2% admitted their process overstated benefits to obtain
  approval, and among those only 50% routinely reviewed benefits afterwards
  against 84.6% of the rest. Survey F18 and F19, both `[moderate]`; F19 is a
  single 2003 study with self-reported overstatement, which if anything
  understates the rate.
- **Output rises without outcomes following.** Faros AI telemetry across
  roughly 10,000–22,000 developers found high-AI-adoption teams completing 21%
  more tasks and merging 98% more pull requests while review time rose 91%, pull
  request size 154% and bug count 9% — and org-level DORA metrics did not move.
  DORA 2025, at about 5,000 professionals, reports AI adoption still correlating
  with lower delivery stability. METR's randomised study found developers using
  AI took 19% longer while believing they were 20% faster. Survey F12,
  `[moderate]`; the Faros and Greptile counts are vendor telemetry over their
  own corpora. The consequence here is that delivery completion cannot stand in
  for outcome progress even when it is the only number available.
- **Forecasting under agentic work is untested.** No dated source between 2023
  and 2026 tests Monte Carlo or throughput-based forecasting against agent-driven
  throughput and reports whether forecast accuracy held; the absence was searched
  for directly and targeted searches against named forecasting practitioners
  returned nothing on topic. Item size is meanwhile measured changing character
  — 20% larger pull requests at Greptile, 154% at Faros — and a stable item-size
  distribution is what Monte Carlo assumes. Survey F13 labels the resulting
  degradation an inference, not a retrieved result. The consequence is that a
  forecast must state its sample rather than imply a validated method.

## Constraints / Appetite

- **Non-waivable: the two separations hold in every artifact that carries both
  numbers.** Fixed date apart from forecast; delivery completion apart from
  outcome movement. Scoped to artifacts that carry both, because a slice
  producing neither a date nor a forecast cannot fail it.
- **Non-waivable: a voluntary review is not sufficient.** Two converging lines say review completion is lowest exactly where the claims
  most need checking: survey F19, and this repository's own terminal intents,
  none of which records an outcome check. Neither line carries the constraint
  alone — F19 is one old study and the repository is one maintainer — and the
  pair is what it rests on.
  A design that relies on someone choosing to look will be used by the honest
  and skipped by the rest, so the absence of a check must be as visible as its
  result.
- **No new runtime**, and none is needed: outcome evidence is sourced from
  measures an organisation already has.
- **The sample ladder is inherited, not re-derived.** FEAT-0012 fixed
  it; this brief enforces it for forecasts.
- **Appetite: the first slice must make the gap visible before anything
  improves it.** Recording that an outcome was never checked is worth shipping
  on its own.

## Assumptions / Risks

- **[Inherited, survived]** Outcome evidence can be sourced without a platform.
  Parent's de-risk; `to-validate`, no adopter has run it.
- **[Open, and no confirmed slice settles it]** A declared outcome can carry a
  measure, a baseline, an owner and a due date that a later reader can act on.
  The cut carries no recording slice, so nothing here adds those fields; the
  review renders whatever an outcome section holds. Owner: the lifecycle
  owner, who decides whether that gap ever becomes a slice. The parent's
  own corpus is the first test: of 14 intents that reached a terminal status,
  zero record whether the outcome moved.
- **[Risk]** The selection effect applies to this repository too. A slot nobody
  fills reproduces the 14-terminal-intents-to-zero result with extra machinery.
- **[Risk]** A forecast range collapses to its optimistic end when transcribed
  into a slide, which makes the separation notional rather than real.

## Spec map

Slices confirmed 2026-09-24 by the lifecycle owner. The Status column is
derived from each spec and is not hand-edited; it is the only home for a
slice's state.

| Spec | Status |
| --- | --- |
| `delivery-forecast-with-uncertainty` | <auto> |
| `progress-review-two-answers` | <auto> |
## The cut, and why it goes this way

**Two slices.** Confirmed 2026-09-24; the Spec map above owns membership and
status.

- `delivery-forecast-with-uncertainty` — the date half
- `progress-review-two-answers` — the review that keeps the two answers apart

**Why no slice records an outcome.** An intent's `## Outcome` section already
declares the input, the lagging outcome and the guardrail at framing. What is
missing is not a place to write a reading but a moment where the declaration
is put in front of someone looking at delivery, and that is the review's job.
Recording a reading stays prose in `## Outcome`, written by whoever has the
number, with no schema and no obligation to come back.

**Why the forecast is separable.** It is separable from its sibling in this
brief, not from everything: a team gets a forecast with its uncertainty whether
or not any outcome evidence exists. It is not separable from FEAT-0012, whose
distributional slice authors the throughput it reads, so it cannot be built
before that slice lands.

**Why the review is a slice rather than an assembly.** The two separations live
there. A review that merely displays both numbers has not done the work; keeping
them from collapsing into each other is the feature's entire point, and that is
sufficient reason on its own.

**What each slice owns.**

- **`delivery-forecast-with-uncertainty`** — a forecast with its range and its
  sample, distinguishable from a committed date, over any scope the delivery
  system can express. Provider-native completions are forecast; intent-backing
  is a caller-supplied filter that defaults off, and resolving the linkage
  belongs to a declared bridge skill. Accepted against: no rendered forecast
  omits either its range or the sample size behind it, and no single date is
  emitted as the headline value.
- **`progress-review-two-answers`** — the review placing the forecast beside
  the intent's declared outcome, read verbatim from `## Outcome`, with both
  separations intact. **This slice owns the selection-effect constraint**:
  showing a declared outcome with nothing recorded under it is what makes an
  unchecked outcome as visible as a checked one, and it is the reason the
  review cannot be an assembly of two numbers. Accepted against: a reader can
  state the two answers separately, and an outcome with no reading renders as
  its declaration above an explicit nothing rather than as a blank or an
  omitted row.

## Governance references

This section collects what each governing artifact obliges here, in one place,
so a spec can cite into it rather than restate the source.

- **[ADR-0125](../../adr/0125-managed-unit-floor-and-projected-range.md)** — D4
  bounds what may be counted: below the floor a trace is readable and must not
  enter a statistic, so a forecast counts only managed items within a resolved
  range. Absence of intent linkage does not establish absence of a floor —
  D5 resolves one from whether work crosses a repository boundary — so a
  provider-native completion is counted and a projected completion whose floor
  cannot be resolved is excluded and named. **Amended 2026-09-24** under
  ADR-0126, which obliges a pack to return value with none of this
  repository's machinery installed.
- **[FEAT-0013](../intents/FEAT-0013-timeline-and-strategic-progress-review.md)** —
  the parent. It owns the outcome, the two separations, the de-risk verdict that
  reframed the deliverable to visible emptiness, and the attribution exclusion.
- **[FEAT-0012](../intents/FEAT-0012-delivery-state-and-flow-visibility.md)** —
  sibling. It owns the observations a forecast counts and the sample ladder this
  brief enforces rather than re-derives.
- **[FEAT-0011](../intents/FEAT-0011-intent-backed-working-view.md)** — sibling.
  It owns making work visible in a delivery system.
- **[CAP-0004](../intents/CAP-0004-external-tracker-projection.md)** — the
  capability. It owns the no-new-runtime guardrail and the rule that completion
  and outcome progress are reported as two numbers.
- **Installed-skill references.** `frame-intent`'s `references/intent-model.md`
  defines the outcome vocabulary this brief consumes and must not duplicate.
- **[Tracker-coexistence adoption survey](../research/tracker-coexistence-adoption-survey.md)**
  — the findings this brief cites are named where they do work. Each carries
  its own confidence grade
  and downgrade reason; read the finding before relying on it.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/FEAT-0013-timeline-and-strategic-progress-review.md`
- **Authority:** eugenelim, lifecycle owner

Projected from that intent on 2026-09-23 under ADR-0077 D1, which routes several
independently shippable changes in one repository to a brief with specs beneath
it. That clause is superseded in part by ADR-0098 D1, which lets sufficient
direct artifact authority bypass feature-intent creation; the row this brief
relies on is unaffected.
