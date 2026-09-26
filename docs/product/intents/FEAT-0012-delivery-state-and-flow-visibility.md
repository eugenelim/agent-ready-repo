# Intent: "where is this, and what's stuck" has the same answer whatever tracker you run

- **Slug:** `delivery-state-and-flow-visibility`
- **Status:** Accepted
- **Accepted:** 2026-09-24 by eugenelim, lifecycle owner. The basis: framed and reviewed clean in intent mode at revision `7341e0ff7c3a3d7b`; de-risked with a surviving verdict on published minimums and a computed tolerance ladder; the thin-sample question closed by spike rather than deferred; and decomposed into a delivery brief. **The shaping review predates later material edits** — the ADR-0125 range, the D4 counting bound and the spike disposition — so it is evidence for the bet rather than for the current text.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:external-tracker-projection
- **Shaping-reviewed:** 2026-09-23
- **De-risked:** 2026-09-23
- **Decomposed:** 2026-09-23 brief

## Outcome

- **Input (steerable):** How much of the answer to *where is this, and what is
  holding it up* depends on which delivery system the team happens to run.
  Today that dependence is close to total: the question is answerable on Jira
  and not answerable at all on GitHub Issues + Projects or Linear.
- **Outcome (lagging):** A team sees where its intent-backed work actually
  stands and what is blocking it, acts on that, and gets the same meaning
  whichever delivery system it runs. **The signal accepted as proof is
  qualitative and falsifiable:** a manager looking across two teams on
  different providers reads the same numbers the same way, with no translation
  step and no footnote explaining why one team's figures are not comparable.
- **Guardrail:** Three things must not get worse. An observation stays an
  observation — nothing read back from a tracker acquires authority over
  canonical intent. The measure stays honest when the work changes character,
  so a throughput rise is never reported as an improvement when the unit
  itself got bigger. And **no number is reported that its data cannot support**:
  a thin sample is labelled thin rather than rendered as a confident
  percentile.

## Opportunity

- **Functional job:** Know where the work actually stands and what is holding
  it up, without having to become an expert in my tracker's reporting
  machinery to find out.
- **Emotional job:** Stop guessing, and stop having to defend a number I do not
  myself believe.
- **Social job:** Give a straight answer to "are we on track" — one I would
  stand behind in front of the team and in front of the sponsor, who will read
  it differently.
- **Struggling moment:** Two failures land at once. The question is only
  *askable* on one provider: the existing flow surface computes cycle time,
  lead time, throughput, WIP and flow efficiency from Jira changelogs and
  states in its own description that it must not be used for a tracker that is
  not Jira, so a GitHub or Linear team cannot ask it at all. And where the
  numbers do exist, agentic execution has pulled them away from the truth —
  pull requests merged rose 98% and review time rose 91% while org-level
  delivery metrics did not move — so the available number and the honest answer
  have come apart. A team is left choosing between a figure it cannot compute
  and a figure it should not trust.

## Boundary

Owns: which observations a delivery system legitimately authors; what those
observations mean in a way that holds across providers; reading delivery state
and flow over intent-backed work whatever the provider is; and the limit that
keeps an observation from becoming authority over canonical intent.

Delivery systems are **variants inside this feature**, not separate features,
because the same observation must carry the same meaning across them. That is a
statement about the outcome, not about slicing: this feature has not been
decomposed, and how its work is cut is a later decision.

Does not own the working view that made the work intent-backed
([FEAT-0010](FEAT-0010-intent-backed-working-view.md)), forecast or strategic
progress ([FEAT-0012](FEAT-0013-timeline-and-strategic-progress-review.md)), or
operational coordination state inside the repository
([CAP-0003](CAP-0003-workspace-coordination-reorganization.md)).

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Framing

**Run under `frame-intent` on 2026-09-23**, replacing the placeholder measures
seeded by the parent's decomposition.

**Scale `app`, inferred not asked** — one repository publishing one product.
**Maturity `brownfield`** — a flow surface already exists for one provider.

**Altitude `feature`, tested.** It reduces to a vertical slice: for one
provider, read the observations for intent-backed items and answer *where is
this and what is stuck* with a stated meaning. That ships and tests alone; the
other providers are further slices of the same outcome.

**Knowledge surface: in-repo doc set** plus the parent's commissioned research.
No MCP knowledge tool or internal CLI detected.

**Brownfield current-state input, taken as a constraint:** the existing
Jira-only flow surface is the thing this feature generalises, and its metric
definitions are the incumbent vocabulary. It is a constraint because a
provider-neutral meaning has to reconcile with it, not a target because
reproducing it three times is the failure mode, not the goal.

### The tier moved, and it moves this feature's ground

[FEAT-0010](FEAT-0010-intent-backed-working-view.md) was reframed on
2026-09-23 and
[ADR-0125](../../adr/0125-managed-unit-floor-and-projected-range.md) then
decided the result: the projection is a **range**, floored at the feature intent
for same-repository work and at the delivery brief where work crosses a
repository boundary, with the rungs above it projecting too and nothing below it
managed or counted. This feature observes flow over whatever the range admits,
so the change is not neutral here — it is load-bearing, in both directions.
**ADR-0125 D4 is what bounds this feature's denominator**: a trace below the
floor is readable and must not be counted.

**It is what makes flow readable at all.** Flow metrics need items that
*dwell*. Ageing charts, time-in-state and blocked-duration all require an item
to sit somewhere long enough to be seen sitting. An item that appears and
completes inside four days never occupies a column, which is exactly why the
spec tier failed FEAT-0010's probe. The enterprise measurement behind the
reframe describes items that do dwell: feature paths spanning four to five
states, 7.56 recorded state visits per issue on a six-state dominant path, and
epic changes recorded at a median 81 days after creation. Slow is not a problem
for this feature; slow is the precondition.

**It introduces the opposite risk, and that risk is new.** Few items. A team
may hold a handful of feature intents in flight at once, and flow statistics
over a handful of long-lived items are thin to the point of dishonesty —
percentiles over five items are decoration. The spec tier had the opposite
shape: many items, too short-lived. Neither tier is comfortable, and this
feature inherits whichever discomfort the reframe chose. That is the origin of
this intent's third guardrail clause and of its likeliest riskiest assumption.

### Optional Core shaping review — intent mode, clean

Dispatched to Core's `shaping-reviewer` in `intent` mode on 2026-09-23 against
revision `7341e0ff7c3a3d7b`, with one attributed evidence packet: this intent,
its Accepted parent, both siblings, the survey it cites by finding number, and
the four installed-skill contracts. The packet was supplied as data and the
reviewer was told not to retrieve beyond it. Two checks were asked for beyond
the field rules — that findings F12, F13, F15 and F16 say what this intent
claims, and that its characterisation of FEAT-0010's reframe matches what
FEAT-0010 actually records.

**Result: no `MALFORMED` tokens.** Empty token output is this mode's pass
state; completion was read from this caller's host rather than inferred from
the output. The file was unchanged between dispatch and this record, so the
reviewed revision is the current one and no nonmaterial-correction caveat
applies.

A review result sets no status. This intent stays `Draft`; `de-risk-intent`
runs next.

## Assumptions

What must be true for this bet to pay off. Not tested here; `de-risk-intent`
picks the riskiest and predeclares a kill condition for it.

- **There are enough items at the projected tier for a flow statistic to mean
  anything.** The likeliest candidate for the riskiest assumption, and it is
  created by FEAT-0010's reframe rather than inherited from the seed.
- **A provider-neutral meaning exists for the observations that matter** —
  state, assignment, blocked, elapsed — that is not a lowest common denominator
  so thin that no team uses it.
- **Items at the projected tier dwell long enough to produce readable flow.**
  Supported by enterprise measurement rather than assumed; see § Evidence.
- **Reading a tracker observation does not grant it authority.** The boundary
  has to be enforceable in the mechanism, not merely declared in prose, because
  ADR-0077's whole apparatus exists for how silently that step happens.
- **Teams want flow at the tier they manage, not at the tier work executes.**
  If a delivery manager actually wants per-commit movement, this feature is
  aimed at the wrong altitude.
- **Freshness can be stated rather than guaranteed.** No daemon may exist, so a
  reading is as of a moment and must say which moment.
- **Knowledge surface:** in-repo doc set; none other detected.

### Inherited from the parent

Carried, not restated — [CAP-0004](CAP-0004-external-tracker-projection.md)'s
§ Assumptions holds the set. The four binding this child: a tracker authors
workflow state, assignment, blocking and timestamps and only those; tracker
activity never silently rewrites canonical intent; agent-internal work is not a
management unit, so flow measured over it measures the wrong thing; and no new
daemon, control plane, database or scheduler, which rules out an
always-current cache.

## De-risk — SURVIVES, 2026-09-23

**Reversibility triage: two-way door by cost of reversal, overridden to
`validate-first`.** A flow reading can be switched off. What cannot be undone
is a number a sponsor believed — the failure here is silent, a statistic that
looks authoritative and is not, so it is not discoverable by building. There is
also nothing to prototype against: no adopter exists, and this repository's own
throughput is unmeasurable (below). The override is recorded rather than left
implicit.

### The riskiest assumption

*There are enough items at the feature-intent tier for a flow statistic to mean
anything.* Created by [FEAT-0010](FEAT-0010-intent-backed-working-view.md)'s
reframe, which bought dwell and spent item count.

### Kill condition, predeclared 2026-09-23T01:14:55Z

Before any retrieval was dispatched. Verbatim, unedited after the result:

> KILLED if BOTH hold: (i) published flow-forecasting or flow-metrics guidance
> specifies a minimum sample that a typical enterprise team does NOT reach at
> the feature/epic tier within one planning period (a quarter); AND (ii) NO
> documented mitigation exists for small-N flow measurement — no aggregation
> across teams or periods, no small-sample-appropriate statistic, and no
> established practice of measuring flow at the feature/epic tier despite
> sparsity.
> SURVIVES if EITHER is false.

### The internal measurement failed, and is discarded rather than weighted

The corpus holds **130 feature-level and 17 capability-level intents** — the
tier is not sparse. But the throughput-relevant subset (24 at a terminal or
committed status) is unusable: **all 24 show a last-touch in the same quarter**,
which is the signature of this repository's corpus-wide intent-reference-grammar
migration, not of 24 completions. Git-derived throughput does not survive a bulk
rewrite. Reporting it would have shown a healthy sample and meant nothing.

### The published minimums are low — (i) is FALSE

A second, independent retrieval reached tighter numbers than the first and they
supersede it. **Magennis's clearest published minimum for Monte Carlo is 11
recent observations**, not the 3-to-start figure secondary summaries repeat.
**Vacanti's rule of thumb for a high-percentile cycle time is roughly 11–12
minimum, usually no more than 30** — explicitly a rule of thumb, not a
demonstrated boundary. The Kanban Guide 2025.5 deliberately gives **no number
at all**, saying only to use historical cycle time for a service-level
expectation and a best guess until there is "enough" of it. For a median, 5
points bound it with ~93.75% confidence on an order-statistics argument.

Eleven to thirty is reachable. The premise that a team cannot reach the minimum
is unsupported.

### Measuring at this tier is documented practice — (ii) is FALSE

The Flow Framework applies Flow Load, Velocity, Time, Efficiency and
Distribution at the value-stream level, which is feature-tier or coarser. An
independent practitioner account (ASOS Tech Blog) reports moving flow metrics
to the epic and feature tier deliberately, "because the real value comes at this
level," and pairs it with the mitigation that actually matters: **sizing** —
features capped at roughly two months and epics at four months of cycle time, to
keep the tier meaningful rather than to grow the sample.

**Both conditions false. The kill required both. SURVIVES.**

### The number the sources would not give, computed here

No retrieved source derives a confidence bound for an *extreme* percentile —
every figure quoted is for the median or for a range. That matters, because the
a high percentile is what practitioners actually report, and "5 points bound
the median" does not license it.

It is computable. For a distribution-free one-sided tolerance bound, the largest
of `n` observations bounds proportion `p` of the population with confidence
`1 − pⁿ`, so `n ≥ ln(1−γ) / ln(p)`:

**Computed against the percentile set `flow-metrics` already emits** — p50, p75
and p90, at `statistics.quantiles` indices 49 / 74 / 89 — rather than a set
invented here, so the threshold and the incumbent surface describe the same
numbers.

| Percentile | Items needed, 90% confidence | Items needed, 95% confidence |
| --- | ---: | ---: |
| p50 (median) | 4 | 5 |
| p75 | 9 | **11** |
| p90 | 22 | **29** |

**The instrument was checked before its verdict:** the formula reproduces the
~93.75%-at-five-points figure the practitioner sources cite for the median, which
is `1 − 0.5⁴`. It agrees with them where they overlap, which is why its
extrapolation is worth something.

This is **this author's calculation, not a retrieved finding.** No source states
it. It is labelled as such because the rest of this record is sourced and this
is not.

**Two independent routes reached the same concern.** The second retrieval
observed, without computing anything, that "at 11–12 completions the empirical
P85 is controlled by roughly the two slowest observations; even 30 gives only
about 4–5 observations in the upper 15%." That is the qualitative form of the
table above. Note also where the numbers land: Vacanti's 11–12 rule of thumb
sits between the p75 rows — 9 at 90% confidence and 11 at 95% — so the
practitioner rule is real and lands near the middle of the ladder rather than
at its top.

**It converts this intent's third guardrail from a principle into a
threshold.** At the feature-intent tier: a median is honest at five completions,
p75 needs eleven, and p90 needs twenty-nine and should not be offered below
that. **95% confidence is a recorded owner choice, not a derived constant** —
the 90% column moves every number, and the table carries both so the choice
stays visible. That is the difference between an
honest flow surface and a decorative one, and it is now a number a spec can
enforce.

### Carried against the verdict

- **Every numeric minimum is secondary or vendor-adjacent.** Primary texts
  (Vacanti's books, Scrum.org's series, Magennis's own site) were not directly
  retrievable; the figures come from summaries. Treat 3, 5, 7–15 as plausible
  and unverified against primary text. One outlier — "30+ items" — was
  **rejected**, being vendor-published with no methodology shown.
- **Vendor incentive runs one way.** ProKanban (Vacanti-affiliated, sells
  training), 55degrees (sells the tool) and Planview (sells the framework) all
  benefit from flow metrics looking practical at low sample sizes.
- **The reach is now partly measured, and it clears the bar.** A consultancy
  observing SAFe adoptions reports most first PI-planning events carrying
  **20–30 prepared features**, and one nine-team Agile Release Train averaging
  **46 features per PI across four PIs**. A Program Increment is 8–12 weeks, so
  that is roughly a quarter. Those counts clear the 29 needed for a p90
  percentile. Held loosely: consultancy observation with no sample frame,
  roughly 2016 and therefore stale, one ART for the 46 figure, and *prepared* is
  not *completed*. Planview analysed 3,600+ value streams across 34
  organisations and published no absolute distribution of items per stream.
- **Small-N technique is NOT a gap — an earlier draft of this record said it was,
  and that was wrong.** Peer-reviewed work exists and one result is directly
  usable: Minku's Dycom combined local and cross-company models and **maintained
  or improved performance using 10× fewer local training projects in 15 of 18
  cases**, drawing on 184 within-company and 826 cross-company projects — and
  **failed in 3 of 18** when the external evidence was sparse, old or unstable,
  which is the honest boundary on borrowing. Song, Minku and Yao evaluated
  Bayesian-plus-bootstrap prediction intervals across 11 datasets of 21–162
  projects; the smallest is 21, so it does not validate forecasting from a
  handful. Batselier and Vanhoucke found reference-class forecasting best among
  several approaches on real project data, though not software-specific and with
  no minimum class size. What remains genuinely absent is any study validating an
  high-percentile feature forecast from one team's handful of items alone.
- **The standing caveat, predeclared:** a survive establishes the statistic *can*
  be honest at this tier, not that anyone will act on it. Whether a delivery
  manager uses a quarterly-granularity flow reading is the desirability half, and
  this probe did not test it.

```
validation_hook:
  assumption: enough items exist at the feature-intent tier for a flow
    statistic to mean anything
  kill_condition: as predeclared 2026-09-23T01:14:55Z above
  status: SURVIVES on published evidence plus one computed threshold;
    to-validate on the desirability half
  reads_back_to: ADR-0125, whose revisit trigger fires when an adopter's
    feature-tier completions fall below this ladder. The comparison has no
    owner until an adopter exists; whoever runs the activity below owns it,
    and a below-threshold result is an ADR revisit rather than a local fix
  activity: at the first adopting team, count completed feature-tier items per
    quarter against the table above, and separately watch whether anyone acts
    on the reading. The first is arithmetic; the second is the untested half
  unmeasured: features completed per planning period at this tier. No
    published count exists for SAFe PIs or Flow Framework value streams
```

## Open for shaping

Deliberately undecided.

- The lifecycle-event schema, and whether one exists at all.
- ~~Where shared flow-metric calculation lives, given it sits inside a provider
  pack today.~~ **Answered by the lifecycle owner, 2026-09-24: nowhere — it is
  not shared.** Delivery-system packs install at user scope and stay
  independently installable, so each carries its own computation in its own
  pack and none depends on another. The vocabulary is what crosses systems; the
  code does not. Nothing mechanically holds the implementations consistent,
  which is an accepted cost.
- How provider capability differences are negotiated when one provider cannot
  supply an observation another can.
- Read-versus-write mechanics and their human-control boundaries.
- Whether a provider-neutral state vocabulary is a mapping, a lowest common
  denominator, or something else.
- ~~What a thin sample does.~~ **Dispositioned by spike, 2026-09-23. Closed —
  do not re-open as a slice decision.**

  The question assumed a design choice existed. It does not, on two grounds the
  spike established by computation rather than by preference.

  **Most of what a team asks for needs no sample.** How many items are in
  flight, how long each has sat where it is, which are flagged blocked and since
  when, what moved since the last look — these are reads of current state, not
  estimates of a distribution. They are available at **n = 0** and the
  thin-sample question never touched them.

  **For the distributional half the ladder is arithmetic, not a preference.**
  Against the distribution-free tolerance bound, at 95% confidence: **5**
  completions support a median, **11** p75 and **29** p90 — the percentile set
  `flow-metrics` already emits. Below five, no *percentile* claim is supported
  at that confidence; a count, a range or a mean still is.

  **Disposition:** report the strongest distributional claim the sample
  supports and name the sample size beside it; report the non-distributional
  observations always. Neither refusal nor cross-team aggregation is required,
  and the cross-company borrowing the survey evidences carries a 3-in-18 failure
  rate where external evidence is sparse, old or unstable — a cost with no
  benefit here, since graceful degradation needs no borrowed data.

  This also corrects this intent's third guardrail clause, which implied the
  surface can be left with nothing to say. It cannot.

## Starting points in this repository

Locations, not contents — open them when shaping.

- `packs/atlassian/.apm/skills/flow-metrics/` — the Jira-only implementation:
  which metrics it defines, how it derives time-in-state from changelogs, and
  its own statement that it must not be used for a non-Jira tracker.
- `packs/atlassian/.apm/skills/jira-refresh/`, `packs/github/.apm/skills/github-refresh/`,
  `packs/linear/.apm/skills/linear-brief-sync/` — the three existing read and
  narrow write-back surfaces, and the confirmation gates they impose.
- `docs/adr/0077-feature-projection-and-tracker-authority.md` — the accepted
  limit on what an imported field may do.

## Evidence now available

From the parent's de-risk and its second round, 2026-09-23 —
[applied survey](../research/tracker-coexistence-adoption-survey.md).

- **Enterprise items dwell, and this is measured rather than asserted.** A
  process-mining study of 14,739 Jira issues across 24 teams and 74
  repositories found feature paths spanning four to five states, with about 10%
  of one team's features moving backwards from Done to In Test; an earlier
  study recorded 7.56 state visits per issue across a six-state dominant path
  and 176 distinct path variants. Survey F15.
- **Epics persist for months.** Recorded epic changes at a median 81 days after
  creation, workflow-field changes at 118, resolution changes at 164. Survey
  F16.
- **Flow metrics become more necessary under agentic execution, not less** —
  "AI makes starting work feel almost free", and local speedups collapse at
  review, architecture and validation bottlenecks that remain human. Survey
  F13.
- **The numbers to design against.** High-AI-adoption teams: +21% tasks, +98%
  pull requests merged, review time +91%, PR size +154%, bugs +9%, and no
  measurable org-level DORA movement. Survey F12.
- **No benchmark exists to borrow for state occupancy.** Team-level and
  single-enterprise measurements exist; a representative cross-enterprise
  distribution does not. A team's own tenant data is the only source. Survey
  F15.

## Decomposition

Decomposed 2026-09-23 into a **delivery brief** —
[where work stands means the same thing whatever tracker you run](../briefs/delivery-state-and-flow-visibility.md).
It carries a candidate cut of two slices; nothing is confirmed and no spec
exists. The brief owns slice membership.

### Why the cut goes this way

- **The spike moved the line.** Dispositioning the thin-sample question
  exposed that this feature has two halves with different sample requirements:
  reads of current state need none, and distributional claims need a determined
  minimum. That is a shippability boundary, so the cut follows it.
- **Not one spec per delivery system, unlike the sibling.** FEAT-0010 can cut
  that way safely because each of its slices renders the same canonical tree.
  This feature's outcome is that an observation *means* the same thing
  everywhere, so a per-system cut would invite each spec to define its own
  meaning — the failure the feature exists to prevent. Systems are variants
  inside both slices, with the first implemented setting the vocabulary.
- **Observation ships before distribution** because it is useful at zero
  completed items and produces the vocabulary the second slice needs.
- **One question deliberately left open:** whether the cross-system vocabulary
  binds beyond this feature and therefore belongs in a decision record. It has
  the shape of the floor question that became ADR-0125. The brief records it.
