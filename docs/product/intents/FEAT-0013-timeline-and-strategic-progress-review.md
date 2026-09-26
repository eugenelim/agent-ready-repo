# Intent: no single number is asked to answer two different questions

- **Slug:** `timeline-and-strategic-progress-review`
- **Status:** Accepted
- **Accepted:** 2026-09-24 by eugenelim, lifecycle owner. The basis: framed and reviewed clean in intent mode at revision `260890bd565a58fa`, including a check that every threshold it borrows from its sibling matches that record; de-risked with a surviving verdict that reframed the deliverable to making an unchecked outcome visible; and decomposed into a delivery brief. **The shaping review predates the later addition of the ADR-0127 range**, so it is evidence for the bet rather than for the current text.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:external-tracker-projection
- **Shaping-reviewed:** 2026-09-23
- **De-risked:** 2026-09-23
- **Decomposed:** 2026-09-23 brief

## Outcome

- **Input (steerable):** How often a progress answer rests on one number doing a
  job it cannot do. Two collapses account for almost all of it — completion
  standing in for outcome, and a forecast being read as a commitment — and both
  are movable by making the second number available rather than by arguing
  about the first.
- **Outcome (lagging):** A team and the people it reports to leave a review with
  one shared picture: when the work is likely to land and with how much
  uncertainty, what scope and risk are known, and what evidence exists that the
  product outcome is actually moving. **The signal accepted as proof is
  qualitative and falsifiable:** afterwards the sponsor can state the forecast's
  uncertainty back in their own words, and can say what would count as the
  outcome moving — separately from what would count as the work finishing.
- **Guardrail:** Three things must not get worse. A fixed business date and a
  probabilistic forecast stay distinguishable in everything this produces.
  Delivery completion and outcome progress stay two numbers and are never
  merged into one. And **no forecast is offered that its sample cannot
  support** — the thresholds are inherited, not invented here, and a review that
  cannot meet them says so rather than rendering a confident range.

## Opportunity

- **Functional job:** Bring *when will it land*, *what do we know is risky*, and
  *is it actually working* into one conversation, so the three can be decided
  against each other instead of separately and at different times.
- **Emotional job:** Not be trapped into a date I do not believe, and not have
  to choose between being honest and being useful.
- **Social job:** Be the person whose forecast is trusted *because* it carries
  error bars rather than in spite of them — and be able to say "we shipped it
  and the outcome did not move" without that being a career event.
- **Struggling moment:** The conversation has one number available and it
  answers neither question well. Percent of tickets closed is cheap to produce,
  poor at predicting a date, and not an answer at all about the outcome.
  Agentic execution has widened the gap rather than closed it: pull requests
  merged rose 98% with no measurable org-level movement, a 180% commit increase
  yielded 30% more releases, and one four-marketplace analysis found total usage
  did not move at all. So a programme can read 80% complete against an outcome
  that has not shifted, and will rationally fund the last 20% rather than ask
  whether the bet was right. The number does not just mislead; it selects the
  wrong decision.

## Boundary

Owns the review itself: what a delivery forecast, known scope and risk, and
evidence of outcome movement look like placed side by side, and the two
separations that placement must preserve.

Does not own the observations it reads
([FEAT-0011](FEAT-0011-delivery-state-and-flow-visibility.md)), the projection
that made work visible in the first place
([FEAT-0010](FEAT-0010-intent-backed-working-view.md)), or how an outcome and
its guardrail are *stated* — that belongs to the intent model, which this
feature consumes rather than defines.

Provider differences are handled by what it reads, not here. A review that
worked for only one provider would fail its own outcome.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Framing

**Run under `frame-intent` on 2026-09-23**, replacing the placeholder measures
seeded by the parent's decomposition.

**Scale `app`**, inferred. **Maturity `brownfield`** — the delivery half of this
review has parts today; the outcome half has none.

**Altitude `feature`, tested.** It reduces to a vertical slice: for one team and
one initiative, produce a review that puts the three things side by side with
both separations preserved. That ships and tests alone.

**Knowledge surface: in-repo doc set** plus the parent's commissioned research
and its second round. No MCP knowledge tool or internal CLI detected.

**Brownfield current-state input, as a constraint:** the intent model already
defines what an outcome *is* — a steerable input, a lagging outcome, a
guardrail. This feature must read that vocabulary rather than invent a parallel
one, and the fact that those fields are **declared but nowhere measured** is the
constraint, not an oversight to route around.

### What this inherits from its two siblings

Both are settled and both bind here harder than they bound anywhere else.

**The unit is the feature intent.** FEAT-0010's de-risk killed the spec tier and
reframed to it. A forecast counts units, so this feature counts those.

**The projected range is decided, and it bounds what this feature counts.**
[ADR-0127](../../adr/0127-managed-unit-floor-and-projected-range.md) settled the
question FEAT-0010's kill opened: the projection is a range, floored at the
feature intent for same-repository work and at the delivery brief where work
crosses a repository boundary. D4 bounds the denominator — a trace below the
floor is readable and must not be counted — so a forecast may count only what
the range admits as managed.

**The sample thresholds are arithmetic, not preference.** FEAT-0011's de-risk
established what an honest statistic needs at this tier: five completions for a
median, **eleven for p75** at 95% confidence and twenty-nine for p90 — the
percentile set `flow-metrics` emits. The clearest published minimum for a Monte
Carlo forecast is
eleven recent observations. Against that, observed Agile Release Trains carry
roughly 20–46 features per Program Increment — so the bar is clearable, but it
is a bar, and **this is the most sample-hungry feature in the tree.** A flow
chart over five items is thin; a forecast over five items is meaningless.

### Optional Core shaping review — intent mode, clean

Dispatched to Core's `shaping-reviewer` in `intent` mode on 2026-09-23 against
revision `260890bd565a58fa`, with one attributed evidence packet: this intent,
its Accepted parent, both siblings, the survey it cites by finding number, and
the four installed-skill contracts. Supplied as data; the reviewer was told not
to retrieve beyond it.

Two accuracy checks were asked for beyond the field rules, because the same
author wrote both sides of each: that findings F10, F12, F13 and F17 say what
this intent claims, and that **every threshold attributed to FEAT-0011 — five,
eleven, twenty-nine, and 20–46 features per Program Increment —
matches that record exactly, confidence levels included.** A transcribed
threshold is where a quiet error survives: a 90%-confidence figure cited as 95%
reads as perfectly normal.

**Result: no `MALFORMED` tokens.** Empty token output is this mode's pass
state; completion was read from this caller's host. The file was unchanged
between dispatch and this record, so no nonmaterial-correction caveat applies.

A review result sets no status. This intent stays `Draft`; `de-risk-intent`
runs next, and its target is already named — whether the outcome half has a
data source at all.

## Assumptions

What must be true for this bet to pay off. Not tested here.

- **The outcome half has a data source at all.** The likeliest candidate for the
  riskiest assumption, and it is specific to this feature. Delivery data exists —
  the tracker holds it and FEAT-0011 reads it. Evidence that an *outcome* moved
  lives somewhere else entirely: analytics, revenue, support volume, adoption.
  The intent model declares a lagging outcome and a guardrail and **measures
  neither**. If nothing supplies that side, this feature produces an excellent
  forecast beside an empty column — which is the conflation it exists to
  prevent, reached by a longer route.
- **Throughput-based forecasting stays valid when item size changes character.**
  Monte Carlo assumes a roughly stable item-size distribution, and agentic
  execution is measurably changing it. No source tests this; it is an open risk
  rather than a settled one.
- **A forecast's uncertainty survives being pasted into a slide.** If a range
  collapses to its optimistic end the moment it leaves the room, the separation
  is notional.
- **A fixed date and a forecast can share one view** without either being read
  as the other.
- **Sponsors want the two numbers together.** If the demand is only ever for the
  single completion figure, this feature is answering a question nobody is
  asking.
- **Knowledge surface:** in-repo doc set; none other detected.

### Inherited from the parent

Carried, not restated — [CAP-0004](CAP-0004-external-tracker-projection.md)'s
§ Assumptions holds the set. The four binding this child: delivery completion
and outcome progress are two measures reported as two numbers; a fixed date and
a probabilistic forecast stay distinguishable; agent-internal work is not a
management unit and so not a forecasting unit; and no new daemon, so a forecast
is computed when asked from evidence that already exists.

## De-risk — SURVIVES, and the survival is a warning, 2026-09-23

**Reversibility triage: two-way door, overridden to `validate-first`.** A review
artifact can be withdrawn. But the failure here is a review that exists, looks
complete, and quietly has nothing in its outcome column — invisible by
construction, so building it would not reveal it.

### The riskiest assumption

*The outcome half has a data source at all.* Delivery data exists; evidence that
a declared outcome **moved** lives outside anything this capability touches.

### Kill condition, predeclared 2026-09-23T01:32:39Z

Before any probe ran. Verbatim, unedited:

> KILLED if BOTH hold: (i) the repository's intent corpus records NO instance of
> a declared lagging outcome being checked against reality — every terminal
> intent records that work shipped and none records whether the outcome moved;
> AND (ii) the documented practice for connecting outcome evidence to a delivery
> review REQUIRES a data platform or instrumentation layer that this
> capability's no-new-runtime guardrail forbids.
> SURVIVES if EITHER is false.

**On corpus weighting.** The owner set internal-corpus weight low on
2026-09-23, because the corpus is one maintainer and the kit ships broadly.
That governs questions about *adopter behaviour*. Probe (i) is not one: it asks
whether the kit's own artifact model carries outcome evidence — a property of
the schema, for which this corpus is the reference implementation and the only
instance. Weight is therefore high for (i), and the departure was recorded in
the predeclaration rather than taken silently.

### (i) is TRUE — the model declares outcomes and never closes the loop

Across the corpus, `## Outcome` appears **152 times**: every intent declares a
steerable input, a lagging outcome and a guardrail. Of the **14 intents that
reached `Fulfilled`**, **zero** record whether the declared outcome moved.

**The instrument was checked before its verdict**, because zero-of-fourteen is
the kind of result a narrow pattern produces by accident. Reading the section
structure rather than pattern-matching prose: those 14 intents carry **34
distinct section types** between them — `Validation evidence`, `De-risk
verdict`, `Riskiest assumption`, `Validation hook`, `Disposition — shipped`,
`Coverage` — and not one is a post-ship outcome check. The gap is in the
*vocabulary*, not in one author's diligence. This repository is unusually
rigorous about testing assumptions **before** building and has no artifact at
all for checking **after**.

A worked example: [STRAT-0002](STRAT-0002-platform-core.md) declares the lagging
outcome that "an engineering layer carries work from raw idea to deploy-ready
change without first inventing the process to do it." That is checkable. It was
declared, work shipped against it, and nothing ever asked whether it came true.

### (ii) is FALSE — no platform is required, on four independent methods

MSP 5th edition, PRINCE2 7, PMI's benefits-realisation framework and
Scrum.org's Evidence-Based Management all prescribe the *same shape* — an
owner-led review against pre-agreed baselines and measures, with named owners
and review dates — and **none prescribes a product**. EBM deliberately defines
no mandatory measures. PMI's plan chooses "whatever tools and resources are
necessary." Australia's national audit office found one agency's measurement
deliberately reusing existing tools and surveys. And no source establishes that
buying a benefits platform improves review completion: the guidance is an
evidence and governance obligation, not a technology architecture.

**Both conditions were required. (ii) is false. SURVIVES.**

### The survival is the warning

Outcome evidence can be sourced without a platform — which means **this was
never a tooling problem**, and building the surface does not solve it. Benefits
realisation is a decades-old, tool-independent discipline aimed at precisely
this question, and it lapses:

- Of **ten Norwegian public IT projects** studied about a year after completion —
  when their own plans expected nearly all benefits to exist — an average of
  **45% had been realised**, while project owners still expected eventual
  realisation of **92%**. **None of the ten quantified benefit uncertainty, and
  only two had a complete written measurement plan.**
- A systematic review of **47 empirical software and IT studies** found benefit
  overstatement reported by 26–48% of respondents in four studies and 54–70% in
  two others, with the reviewers cautioning that most used small convenience
  samples and low response rates.
- In a Norwegian survey (n ≤ 71), **40% reported deliberate overstatement** to
  secure approval.

**And the selection effect is the finding this feature must answer.** In an
Australian study of 69 organisations, 26.2% admitted their process overstated
benefits to win approval — and among those, **only 50% routinely reviewed
benefits afterwards, against 84.6% of the rest.** The review lapses hardest
exactly where it is most needed. A voluntary outcome review will be completed by
the honest and skipped by the inflated.

That converges with (i) at n=1: this repository declares 152 outcomes and checks
zero, and it is not an undisciplined repository. The audited organisations are
not less rigorous than us — they are the same phenomenon at scale.

### What this changes about the feature

**The deliverable is not the review; it is the visible emptiness.** If outcome
evidence is absent, the honest output is a forecast beside a column that says so
— because an empty outcome column next to a confident delivery number is itself
the finding, and is the one thing that cannot be produced by the completion
metric this feature exists to displace. Shaping should treat "we do not know
whether it worked" as a first-class, renderable result rather than an error
state.

### Carried against the verdict

- **The first retrieval's headline figures are dropped, not used.** UK national
  audit numbers (8% of spend with robust evaluation plans, 64% with none)
  appeared only as secondhand search summaries; every primary document returned
  403 or unreadable PDF. A second, differently-routed worker searching the same
  question reported **no quantitative evidence** for the exact proportion that
  declares benefits and never checks them, noting that self-reported surveys run
  much higher than file-based audits and that a generic post-implementation
  review often does not test benefits at all. The numbers above are the
  peer-reviewed ones that survived that second pass.
- **Overstatement evidence is largely self-reported**, with small convenience
  samples. Attribution between honest optimism and deliberate misrepresentation
  is contested; selection effects can produce the same signature.
- **The largest dataset is vendor-published.** A frequently-cited figure of 56%
  less value than forecast across 5,400+ projects comes from consultancy
  research whose data and methods are not fully public, and is not relied on
  here.
- **The standing caveat, predeclared:** a survive establishes outcome evidence
  can be **sourced**, not that it will be **true or attributable**. Whether this
  work caused that movement is a separate and harder problem this probe did not
  touch.

```
validation_hook:
  assumption: the outcome half has a data source at all
  kill_condition: as predeclared 2026-09-23T01:32:39Z above
  status: SURVIVES — sourcing is possible without new runtime; the binding
    risk moved from availability to completion
  activity: at the first adopting team, agree the outcome measure and its
    baseline BEFORE delivery starts, then check at the review whether anyone
    went and looked. The measure is not the test; the looking is
  watch_for: the selection effect. Track whether reviews are completed on the
    initiatives whose outcomes were most confidently claimed at approval —
    published evidence says those are the ones that get skipped
  unmeasured: attribution. Whether delivered work caused an observed movement
    is out of this probe's reach and out of this feature's boundary
```

## Open for shaping

Deliberately undecided.

- The forecasting approach, and whether the repository supplies one at all
  rather than reading the provider's.
- **What counts as evidence of outcome movement.** The intent's own lagging
  outcome and guardrail are candidate anchors, not a decision. This is the open
  question the riskiest assumption sits on, and it stays open: no slice
  adjudicates it. The accepted cut carries no recording slice, so what counts
  as evidence is a judgement made by whoever writes a reading into an intent's
  `## Outcome` section, and the review renders what is there without grading
  it. **Where it comes from is no longer open:** the accepted
  cut, 2026-09-24, holds outcome evidence to measures an organisation already
  has, because the capability admits no new runtime.
- Whether this is a generated artifact, a conversational review, or both.
- How uncertainty is expressed so it survives transcription.
- Where this sits relative to the intent tree's altitudes, since a strategic
  outcome may span several capabilities and this feature reads only one.
- ~~What a review does when the sample is below threshold — refuse the range,
  widen the window, or state the median only.~~ **Closed by
  [FEAT-0011](FEAT-0011-delivery-state-and-flow-visibility.md)'s spike,
  2026-09-23.** None of the three candidates was chosen, because the question
  assumed a design choice where the ladder is arithmetic: report the strongest
  distributional claim the sample supports and name the sample size beside it,
  and report the non-distributional observations always. This feature inherits
  that disposition rather than re-deciding it.

## Starting points in this repository

Locations, not contents.

- `packs/product-engineering/.apm/skills/frame-intent/references/intent-model.md`
  — where a lagging outcome and guardrail are defined. The source of the
  distinction this feature must not blur, and the place to check whether
  anything measures them.
- `packs/atlassian/.apm/skills/flow-metrics/` — the only existing quantitative
  delivery surface, and a worked example of metrics defined with no
  outcome-side counterpart.
- [`FEAT-0011`](FEAT-0011-delivery-state-and-flow-visibility.md)'s § De-risk —
  the sample-size table this feature's third guardrail clause points at.

## Evidence now available

From the parent's de-risk and both research rounds, 2026-09-23/24 —
[applied survey](../research/tracker-coexistence-adoption-survey.md).

- **Output rises and outcome does not follow.** The measured basis for this
  feature's existence: +98% pull requests with no org-level DORA movement; a
  180% commit rise yielding 30% more releases; a four-marketplace analysis where
  usage did not move. Mik Kersten names the thesis from 8,000+ value streams.
  Survey F12.
- **Forecasting under agentic work is untested, and it was searched for.** No
  dated 2023–2026 source tests Monte Carlo against agent-driven throughput.
  Survey F13.
- **The date-versus-forecast pattern and its politics.** Risk-appetite pairs —
  "50% by June, 85% by August" — with the standing objection that a committee
  which asked for a date reads a distribution as evasion. Survey F13.
- **The one named probabilistic-forecasting case omits its politics.** A
  consultancy-reported adoption where estimation would have consumed ~10% of
  annual capacity; two deadline-dependent initiatives delivered on time with no
  estimation sessions — and no account of stakeholder resistance at all, which
  is conspicuous given that resistance is the risk. Survey F10.
- **Reference-class borrowing is evidenced, with a failure rate.** Cross-company
  models held or improved performance on 10× fewer local projects in 15 of 18
  cases, and **failed in 3 of 18** where external evidence was sparse, old or
  unstable. Relevant if this feature ever borrows a comparison class to
  compensate for a thin sample. Survey F17's round.

## Decomposition

Decomposed 2026-09-23 into a **delivery brief** —
[a progress answer that cannot hide behind one number](../briefs/timeline-and-strategic-progress-review.md).
It carries a candidate cut of three slices; nothing is confirmed and no spec
exists. The brief owns slice membership.

### Why the cut goes this way

- **The de-risk moved the deliverable, and the cut follows it.** The binding
  constraint is completion rather than availability: the discipline exists,
  needs no tooling, and is skipped anyway. So the first slice is the one that
  makes an unchecked outcome recordable, not the one that builds the review.
- **The slot is separable and is the smallest change that alters the
  incentive.** Nothing in the model can currently record that an outcome went
  unchecked, which is why 152 declarations produced zero checks — the absence is
  invisible and therefore costless.
- **The forecast is separable** because it reads the sibling's throughput and
  answers the date question alone.
- **The review is a slice, not an assembly.** The two separations live there,
  and keeping them from collapsing is the feature's whole point rather than a
  rendering detail.
- **Considered and rejected: folding the slot into the review.** It would make
  the outcome column structurally empty on day one, which is indistinguishable
  from the status quo and defeats the reframe the de-risk produced.
