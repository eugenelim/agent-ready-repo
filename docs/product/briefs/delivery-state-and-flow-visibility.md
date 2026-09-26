# Brief: where work stands means the same thing whatever tracker you run

- **Slug:** `delivery-state-and-flow-visibility`
- **Received:** 2026-09-23
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Ready
- **Ready confirmed:** 2026-09-24 by eugenelim, lifecycle owner, **on owner authority over an open review**. Bound to revision `074c89b407fba6e7`, which returned `Findings` — one independent review round returning 9 findings, nine of them recorded and unresolved at this transition. `author-delivery-brief` requires a revision-bound `Clean`; the owner took the gate instead, and this line is the record of that. Slice membership and status are the Spec map's; this line does not restate them.
- **Parent intent:** intent:delivery-state-and-flow-visibility

**How the specs from this brief cite.** A spec names a governing artifact by
its record and clause, and states the one thing the spec must do because of it.
It does not restate what that artifact says. A paraphrase sealed inside a
frozen contract drifts from its source and is then read as authority in its own
right. A spec cites the artifact and clause directly. § Governance references below
collects what each one obliges *this brief*, for a reader of this brief; it is
not a substitute source for a spec to cite. This brief is not bound by that constraint: it states
what a source says wherever a reader needs it to follow the argument.

## Outcome

A team reads where its work stands and what is holding it up, and gets the
same meaning whichever delivery system it runs. The reading covers any scope a
delivery system can express; restricting it to intent-backed work is a filter
the caller applies, and omitting that filter is the default. **Amended
2026-09-24** under
[ADR-0126](../../adr/0126-integration-packs-standalone-value-and-bridge-skills.md),
which obliges an integration pack to return value with none of this
repository's machinery installed — an intent-backed-only reading returns
nothing for a team that has adopted nothing.

Today that question is answerable on Jira Software and nowhere else. The
steerable input is how much of the answer depends on which system a team
happens to use.

## Success metrics

- **A manager comparing two teams on different systems reads the same numbers
  the same way**, with no translation step and no footnote explaining why one
  team's figures are not comparable. This is the parent's own proof signal.
- **Every reported statistic names the sample it rests on.** A number without
  its `n` is the defect this brief exists to prevent.
- **An observation never acquires authority.** Nothing read back from a tracker
  changes canonical intent. ADR-0077 D6–D12 and ADR-0019 D5 govern this; the
  obligation is not to contradict them.
- **Nothing below a resolved floor is counted.** ADR-0125 D4 bounds the
  denominator; a trace is readable and must not enter a statistic. Absence of
  intent linkage does not establish absence of a floor — D5 resolves a floor
  from whether work crosses a repository boundary — so work whose floor cannot
  be resolved is excluded and named rather than counted.

## Scope / Non-goals

**In scope.** Reading delivery state and flow over any scope a delivery system
can express, with intent-backing available as a caller-supplied filter, and
fixing what each observation *means* so the reading survives a change of
system. Resolving intent linkage belongs to a declared bridge skill, never to
the reading itself.

**Out of scope, each with an owner.**

- **Making work intent-backed in the first place.** Owned by
  [FEAT-0011](../intents/FEAT-0011-intent-backed-working-view.md) and its brief.
- **Forecast and outcome review.** Owned by
  [FEAT-0013](../intents/FEAT-0013-timeline-and-strategic-progress-review.md).
- **Where the floor sits.** Owned by ADR-0125. This brief consumes it.
- **Any new daemon, control plane, database or scheduler.** Owned by
  [CAP-0004](../intents/CAP-0004-external-tracker-projection.md)'s guardrail. A
  reading is computed when asked and is as of a stated moment.
- **Writing to a tracker.** This brief reads. The write surfaces belong to
  FEAT-0011's brief.

## Current-state evidence

Measured or read on 2026-09-23.

- **Flow measurement exists on one delivery system only.**
  `packs/atlassian/.apm/skills/flow-metrics` computes nine metrics from Jira
  changelogs — cycle time, lead time, throughput, WIP, flow load, rework rate,
  flow efficiency, flow distribution and defect ratio — and reports its
  percentiles at p50, p75 and p90. Its own description rules it out for any
  tracker that is not Jira. The consequence is that a cross-system vocabulary
  must reconcile with those nine definitions rather than author its own.
- **The thin-sample question is closed by computation, not open for design.**
  Against the distribution-free tolerance bound at 95% confidence, a median
  needs 5 completions, p75 needs 11 and p90 needs 29 — the percentile set
  `flow-metrics` already emits, so the threshold and the incumbent surface
  describe the same numbers. Below five, no percentile claim is supported at
  that confidence. 95% is a recorded owner choice; the parent carries the 90%
  column beside it. **The ladder is the parent's own computation, not a
  retrieved finding — no published source states it.** The parent records the spike and its
  disposition.
- **Most of the daily question needs no sample at all.** WIP, work-item age,
  blocked-and-since-when and what-moved are reads of current state rather than
  estimates of a distribution. They are available at `n = 0`.
- **Observed enterprise items dwell**, which is what makes the reading worth
  taking. Process mining over 14,739 Jira issues at one manufacturer found
  feature paths commonly spanning four states, or five where testing occurred,
  with about 10% of one team's features moving backwards out of Done; an IEEE
  case study reconstructing 795 complete issue histories recorded 7.56 state
  visits per issue along a dominant six-status path. A 2025 dissertation over
  public Jira repositories puts recorded epic changes at a median 81 days after
  creation and resolution changes at 164. Survey F15 and F16, both `[moderate]`:
  two studies rather than a survey, no cross-enterprise distribution exists to
  borrow, and the epic figure measures change timing rather than lifespan.
- **Agentic execution moves throughput without moving outcomes.** Faros AI
  telemetry across roughly 10,000–22,000 developers found high-AI-adoption teams
  completing 21% more tasks and merging 98% more pull requests while review time
  rose 91%, pull request size 154% and bug count 9%, with org-level DORA metrics
  unmoved. Survey F12, `[moderate]`; those counts are vendor telemetry over a
  vendor's own corpus. The consequence here is that a rising count must never be
  reported as an improvement while the unit's comparability between windows
  is unproved, and no measure a delivery system supplies proves it. What a
  slice does about that — decline the comparison, or carry a size measure
  that establishes comparability — is the spec's to decide.

## Constraints / Appetite

- **Non-waivable: an observation stays an observation.** ADR-0077 D6–D12 and
  ADR-0019 D5, for repo-origin work, set the authority boundary.
- **Non-waivable: the meaning is fixed once, not per system.** The parent's
  outcome is that the same observation carries the same meaning everywhere, so a
  system-specific definition is out of contract even where it is convenient.
- **Non-waivable: no statistic outruns its sample.** The ladder above is
  arithmetic; a surface reports the strongest claim its `n` supports and names
  the `n`.
- **Non-waivable: no shared implementation across delivery systems.** Every
  delivery-system pack installs at user scope and carries its own skill, so a
  provider's reads and its distribution computation live in that provider's own
  pack. Nothing is factored into a shared pack and no pack depends on another
  for this work, even where the arithmetic is identical. What is shared is the
  vocabulary, not the code. The consistency this costs is the price of packs an
  adopter can install one at a time.
- **No new runtime**, so a reading has a freshness and must state it rather than
  imply currency.
- **Appetite: the first slice must be useful before any statistic exists.** The
  spike establishes that the non-distributional half needs no sample, so a team
  gets value on day one or the cut is wrong.

## Assumptions / Risks

- **[Inherited — survived on feasibility, `to-validate` on desirability]**
  Enough items exist at the projected tier for a statistic to mean something.
  The parent's standing caveat travels with it: a survive establishes the
  statistic *can* be honest at this tier, not that anyone will act on it.
  Success metric 1 measures the untested half, and every slice inherits this. Parent's de-risk; the ladder above is what makes
  it operable rather than assumed.
- **[Open, and slice 1 settles it]** A cross-system meaning exists for state,
  assignment, blocked and elapsed that is not a lowest common denominator so
  thin that no team uses it. This is the brief's central bet.
- **[Risk]** A provider may not expose an observation another does. The
  degradation is the same shape as the sample ladder: report what the source
  supports and name what is missing.
- **[Risk]** The meaning, once published, is expensive to change — every number
  already read under it was read under the old definition.

## Spec map

Slices confirmed 2026-09-24 by the lifecycle owner. The Status column is
derived from each spec and is not hand-edited; it is the only home for a
slice's state.

| Spec | Status |
| --- | --- |
| `delivery-state-observation` | <auto> |
| `flow-distribution-sample-honest` | <auto> |
## The cut, and why it goes this way

**Two slices, cut along the line the spike exposed.** Confirmed 2026-09-24;
the Spec map above owns membership and status.

- `delivery-state-observation` — **the meaning, and the half that needs no
  sample**
- `flow-distribution-sample-honest` — the half that is sample-gated

**Why this line and not one spec per delivery system.** The parent's outcome is
that an observation carries the same meaning everywhere. Cutting per system
invites each system's spec to define its own meaning, which is the failure the
feature exists to prevent — the opposite of FEAT-0011, where per-system slices
are safe because each renders the same canonical tree rather than defining what
it means. Delivery systems are variants inside both slices here. Slice 1
carries two of them — Jira Software and GitHub Issues + Projects — because the
vocabulary is
that slice's durable output, and a vocabulary drawn from a single system is an
assumption rather than a result. Jira Software is implemented first within the
slice and GitHub Issues + Projects is reconciled against it; every system after
those two conforms to the pair.

**Why observation ships first.** It is useful with no completed items at all,
where the distributional half is inert until a team has five. It also produces
the cross-system vocabulary the second slice needs before it can label a
percentile as meaning the same thing on two trackers.

**What each slice owns.**

- **`delivery-state-observation`** — which observations a delivery system
  legitimately authors, what each means across systems, and the reading of
  state, assignment, blocking and elapsed time over any scope that system can
  express. Provider-native work is included; intent-backing is a
  caller-supplied filter that defaults off, and resolving the linkage belongs
  to a declared bridge skill. Its durable output is the vocabulary. Accepted against: the same reading taken on
  Jira Software and on GitHub Issues + Projects returns the same meaning
  without translation.
- **`flow-distribution-sample-honest`** — cycle time, throughput and their
  percentiles over the same observations, with the ladder enforced and the
  sample named. Accepted against: a sample below a threshold yields the weaker
  claim rather than a confident one, and never silence.

**One decision this cut does not settle.** Whether the cross-system vocabulary
binds beyond this feature — FEAT-0013's forecast reads it — and therefore
whether it belongs in a decision record rather than a spec. It has the same
shape as the floor question that became ADR-0125. Slice 1 produces it; whether
it is promoted is the owner's call once its reach is visible.

## Governance references

This section collects what each governing artifact obliges here, in one place,
so a spec can cite into it rather than restate the source.

- **[ADR-0125](../../adr/0125-managed-unit-floor-and-projected-range.md)** — the
  projection is a range floored at the feature intent for same-repository work
  and at the delivery brief where work crosses a repository boundary (D1, D2).
  Below the floor nothing is managed or counted, though a trace may be readable
  (D4). D4 is what bounds this brief's denominator.
- **[ADR-0077](../../adr/0077-feature-projection-and-tracker-authority.md)** —
  D6–D12 govern imported-field authority and lifecycle-gated refresh, and define
  the two authority modes.
- **[ADR-0019](../../adr/0019-product-intent-ontology-and-brief-projection.md)
  D5** — one-way projection for repo-origin work, as ADR-0077 refines it into
  two modes.
- **[FEAT-0012](../intents/FEAT-0012-delivery-state-and-flow-visibility.md)** —
  the parent. It owns the outcome, the guardrails, the de-risk verdict and the
  spike that closed the thin-sample question.
- **[FEAT-0011](../intents/FEAT-0011-intent-backed-working-view.md) and
  [FEAT-0013](../intents/FEAT-0013-timeline-and-strategic-progress-review.md)** —
  siblings. FEAT-0011 makes work intent-backed and owns every write surface;
  FEAT-0013 reads this brief's observations into a forecast.
- **[CAP-0004](../intents/CAP-0004-external-tracker-projection.md)** — the
  capability. It owns the no-new-runtime guardrail.
- **Installed-skill references.** `packs/atlassian/.apm/skills/flow-metrics` is
  the incumbent metric vocabulary any cross-system meaning must reconcile with.
  It is not generalised or moved: it sits inside a provider pack, so it stays
  Jira's implementation and a second provider gets its own in its own pack.
- **[Tracker-coexistence adoption survey](../research/tracker-coexistence-adoption-survey.md)**
  — the findings this brief cites are named where they do work. Each carries
  its own confidence
  grade and downgrade reason; read the finding before relying on it.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/FEAT-0012-delivery-state-and-flow-visibility.md`
- **Authority:** eugenelim, lifecycle owner

Projected from that intent on 2026-09-23 under ADR-0077 D1, which routes several
independently shippable changes in one repository to a brief with specs beneath
it. That clause is superseded in part by ADR-0098 D1, which lets sufficient
direct artifact authority bypass feature-intent creation; the row this brief
relies on is unaffected.
