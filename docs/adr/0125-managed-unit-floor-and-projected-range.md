# ADR-0125: What projects into a delivery system: a range from the tree's top down to a floor

- **Status:** Accepted
- **Date:** 2026-09-23
- **Areas:** shaping, workspace
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0019 (the one-way rule this rests on); ADR-0077 (feature projection and tracker authority — D2 supplies the cross-repository brief's coordination identity); ADR-0033 (Level is an open set, so a missing provider rung is named rather than derived)

## Decision summary

- **Decision:** The canonical intent tree projects into a delivery system as a *range* — from the tree's top down to a floor that sits at the delivery brief where work crosses a repository boundary, and at the feature intent otherwise.
- **Because:** Truncating at any single rung breaks a different reader. Cutting below the feature intent fills a board with items nobody manages; cutting above it leaves every component repo with a local view and nobody with the rollup.
- **Applies to:** every outbound projection of the canonical tree onto Jira, Jira Align, GitHub Issues + Projects and Linear, and to anything that counts projected items.
- **Tradeoff accepted:** the projected item set is coarser than a story-tier board, so flow readings are quarterly-grained and sample thresholds bind.
- **Revisit if:** an adopter's feature-tier completions fall below the sample thresholds `delivery-state-and-flow-visibility` depends on, or a provider's hierarchy cannot carry the floor.

## Context

The repository models work as a recursive intent tree and treats a tracker as a
one-way render of it (ADR-0019 D5). What that render should *contain* has never
been decided, and three artifacts now depend on the answer.

`intent-backed-working-view`'s de-risk tested the obvious candidate and killed
it. Against a predeclared line, the median shipped spec in this repository lives
**4 days** and exposes **2** distinct `Status` values, and the only grouping
beneath it — the wave — is rebuilt from index zero on every re-schedule, because
`schedule_unfinished_plan` drops completed tasks before `topological_waves`
recomputes frontiers. Nothing below the intent tier has durable identity.

A second probe against enterprise evidence survived: feature-tier paths span
**four to five states**, one study recorded **7.56 state visits per issue** over
a six-state dominant path, and epic changes occur at a **median 81 days** after
creation. Items at that tier dwell.

Two further facts bound the decision. This repository's operating model crafts
work in a solution repository and hands delivery briefs to component
repositories, so cross-repository work is the normal case rather than an edge
one. And `decompose-intent`'s shipped tracker-projection reference already maps
the two product rungs onto a Theme/Strategy tier and capability onto a portfolio
Epic — a decision that stopped at the feature intent would override a shipped
artifact by omission.

## Decision

**We will project a range of the canonical tree, bounded below by a floor whose
position depends on whether work crosses a repository boundary.**

- **D1:** The projected range runs from the canonical tree's top rung down to a
  floor. The floor rung projects as a **managed item**. Every rung above it is
  **represented** on the target with its rollup intact; D3 decides which carrier
  represents it, and a rung carried on a label is in the range like any other.
- **D2:** The floor is the **delivery brief** where the work it carries crosses
  a repository boundary, and the **feature intent** otherwise. ADR-0077 D2
  already grants the cross-repository brief a distinct coordination identity —
  it is the sole case in which a one-spec brief is permitted — and that brief is
  the unit its component team coordinates around.
- **D3:** Above the floor, rungs **collapse** onto whatever depth the target
  provider carries; they are never **truncated**. A provider with fewer native
  levels flattens intervening rungs onto labels or an equivalent carrier, and
  the rollup survives.
- **D4:** Below the floor nothing is a **managed item** — nothing scheduled,
  assigned, unblocked, counted in work-in-progress, or admitted to a flow or
  forecast statistic. A spec, plan, wave, task, subagent job or retry **may**
  appear below the floor as a **trace object**, linked from its item and
  readable, provided it is neither managed nor counted. This is the distinction
  `decompose-intent`'s shipped profile table already draws, where a
  story-as-trace is "a traceability lens projected *from* a spec, never the
  decomposition primitive."
- **D4a:** A **same-repository delivery brief does not project at all**, as
  either a managed item or a trace. It decomposes a feature intent already
  projected at the same location, so projecting both would count one piece of
  work twice.
- **D5:** The floor is fixed, not negotiated per team. Its discriminator is a
  fact about the work — whether it crosses a repository boundary — and not
  whether a brief happens to exist or how a delivery was sliced.

## Decision drivers

- **Items must dwell.** A unit that appears and completes without occupying a
  state produces no observable flow.
- **Enough items must complete** to support whatever statistic is claimed over
  them.
- **The unit must be one a person schedules, assigns and unblocks.**
- **Every consumer must count the same thing**, or their numbers cannot be
  compared across teams.
- **Each reader must be served at their own altitude** — a component team at its
  brief, a programme at the capability, leadership at the product rungs.

## Consequences

**Positive.**

- One countable unit per location, shared by every downstream consumer.
- Agent-internal churn stays off the board by construction rather than by
  discipline.
- The rollup survives a shallow provider, because D3 collapses rather than
  truncates.
- A component team sees the unit it actually works, without needing the solution
  repository open.

**Negative.**

- The projected set is coarser than a story-tier board. Flow readings are
  quarterly-grained.
- **Projection above the feature tier buys structure, not statistics.** A
  distribution-free p90 needs 29 completed items at 95% confidence,
  and this repository holds 17 capability intents in total, ever. A capability
  item is a container and a rollup target; a percentile computed on one would be
  decoration.
- A team that genuinely manages at story level gets no *managed* projection at
  that level, only a trace, and must move its management up to the floor.
- Cross-repository projection inherits ADR-0077 D4 and D5: each repository brief
  must name the same durable parent, and nothing may read another repository
  live to resolve it.

**Revisit if:** an adopter's feature-tier completions fall below the sample
thresholds `delivery-state-and-flow-visibility` depends on, or a provider's
hierarchy cannot carry the floor.

## Alternatives considered

- **Floor at the spec or slice.** Rejected against *items must dwell*: measured
  at 4 days and 2 states in this repository, with no durable grouping beneath
  it.
- **Floor at the plan task or agent execution unit.** Rejected against *the unit
  must be one a person schedules*: these are not scheduled, assigned or
  unblocked by anyone. An adjacent system that orchestrates coding agents
  independently places its own floor above this line.
- **Floor at the capability.** Rejected against *enough items must complete*: 17
  capability intents exist in total, far below the threshold for any percentile
  claimed over them.
- **Feature intent as both floor and ceiling.** Rejected against *each reader
  must be served at their own altitude*. This was the first draft of this
  record, and it failed the operating model it was written for: with work
  crafted in a solution repository and handed to component repositories,
  truncating at the feature tier leaves each component repository a local view
  and no reader the rollup.
- **A per-team negotiable floor.** Rejected against *every consumer must count
  the same thing*: it makes flow and forecast numbers incomparable across teams,
  which removes the reason to compute them.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** every rung in the range is present on the target, as a native
  level or as a label, and the rollup resolves from the floor to the top rung;
  no *managed* item maps to a rung below the floor D2 sets for that work; and
  no same-repository brief projects alongside its parent feature intent. A
  trace object below the floor is not a violation; a trace that is
  assigned, scheduled or counted is one, because that is what makes it managed.
- **Owner:** eugenelim

A lint becomes possible only once an outbound projection ships; none exists
today, so the check is a reviewer's at spec stage. This is stated rather than
left implicit, so no reader assumes a mechanical guard is in place.

## References

This record rests on a reframe that carries a `to-validate` hook: no adopter has
run it, and whether a repository-canonical feature intent behaves like an
enterprise epic once projected is unmeasured. The evidence is recorded in
`docs/product/research/tracker-coexistence-adoption-survey.md` and in the
de-risk sections of `docs/product/intents/FEAT-0010-intent-backed-working-view.md`
and `docs/product/intents/FEAT-0011-delivery-state-and-flow-visibility.md`.
