# Intent: a team gets a real answer from its own tracker before it adopts anything

- **Slug:** `tracker-native-value-before-adoption`
- **Status:** Accepted
- **Accepted:** 2026-09-24 by eugenelim, lifecycle owner. The basis: framed and
  reviewed cold in intent mode at revision `57c8f6c2fb29b024`, which returned
  that mode's empty pass; de-risked with a surviving verdict measured over the
  repository's own 154-intent corpus against a line set before the
  measurement; and decomposed into a single delivery contract for `new-spec`.
  The surviving verdict rests on desk evidence, so its validation hook stays
  `to-validate`.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:external-tracker-projection
- **Shaping-reviewed:** 2026-09-24
- **De-risked:** 2026-09-24
- **Decomposed:** 2026-09-24 spec

## Outcome

- **Input (steerable):** How much a team has to adopt before a delivery-system
  pack answers a question it actually has. For a flow view with outcomes
  attached the answer today is *all of it*: every one of the ten specs in
  flight under this capability assumes the intent tree exists. This is directly
  movable, because the tracker already holds enough to answer.
- **Outcome (lagging):** A team that has adopted nothing installs the pack for
  its own delivery system, asks where its work stands and what that work was
  meant to change, and gets both answers from the tracker it already runs.
  **The signal accepted as proof is qualitative and falsifiable:** a team uses
  the view more than once with no repository artifact of ours in existence, and
  can say in its own words what adopting the intent system would add.
- **Guardrail:** Three things must not get worse. The view stays read-only, so
  looking costs a team nothing it has to undo. Adoption stays optional rather
  than a prerequisite in disguise — no capability here quietly returns nothing
  when the intent tree is absent. And the outcome shown is never authored by
  us: it is elicited from the team or read from what the tracker already holds,
  because an outcome we invented would make the view a demonstration rather
  than a tool.

## Opportunity

- **Functional job:** See where the team's work stands and what that work is
  supposed to change, in one place, using the system the team already runs.
- **Emotional job:** Confident the picture is real, and not anxious that
  taking on a new way of working is the price of seeing it.
- **Social job:** Able to show a manager or a stakeholder a picture that needs
  no explanation of the tooling behind it.
- **Struggling moment:** The team can already see throughput, cycle time and a
  board. Nothing on any of them says what the work was *for*, so the review
  becomes a status recital — and every tool that would fix it asks the team to
  move its work somewhere else first.

## Framing

Run under `frame-intent` on 2026-09-24, occasioned by
[ADR-0126](../../adr/0126-integration-packs-standalone-value-and-bridge-skills.md),
which obliges an integration pack to return usable value with none of this
repository's machinery installed.

Reviewed cold in `shaping-reviewer` intent mode on 2026-09-24 at revision
`57c8f6c2fb29b024`, which returned the empty pass that mode uses for a clean
result. The reviewer read this intent, its parent and the field contract; the
revision is recorded here because an empty pass carries no bytes to bind
itself to.

## Boundary

Owns what a delivery-system pack returns before anything of this repository is
installed: a flow and state view over the tracker's own hierarchy, with an
outcome attached at a rung the tracker already has.

Does not own the intent-backed view
([FEAT-0010](FEAT-0010-intent-backed-working-view.md)), the cross-system
observation vocabulary
([FEAT-0011](FEAT-0011-delivery-state-and-flow-visibility.md)), or the review
that places a forecast beside a declared outcome
([FEAT-0012](FEAT-0012-timeline-and-strategic-progress-review.md)). Those
three each assume the intent tree; this one assumes its absence.

Does not own how a pack declares a bridge skill or what may appear in one.
[ADR-0126](../../adr/0126-integration-packs-standalone-value-and-bridge-skills.md)
settles that, and this feature is the first thing obliged by it rather than the
place it is decided.

**Explicit non-goals.** No write of any kind, so no projection, no create, no
comment and no transition. No repository artifact — no intent tree, no
`docs/product/`, no `workspace.toml`, no mapping file keyed by a tracker
object, because a mapping is machinery by another name. No outcome authored by
this feature. No cross-system claim: a second delivery system is a later cut,
not a condition of this one working.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Projection

Outbound projection is unshaped for this intent, and deliberately so: this
feature is read-only and tracker-origin, so it projects nothing.

## Assumptions

What must be true for this bet to pay off. Not tested here.

- **A team will supply an outcome for a tracker rung it already manages.**
  This is the riskiest assumption, and it is specific to this feature. The
  delivery half is nearly free — `jira-team-status` and `flow-metrics` ship
  today — so the whole added value rests on the outcome half, and the outcome
  half rests on somebody typing one sentence per Epic. If teams will not, this
  feature ships a kanban view that is marginally better than the one they
  already have and an empty column beside it. Survey F18 cuts both ways here:
  it found that outcome review needs no platform, which is why this is
  possible at all, and that the discipline lapses anyway, which is why it may
  not happen.
- **Knowledge surface consulted:** the in-repository document set —
  `docs/adr/`, `docs/product/` and `packs/*/.apm/skills/` — was the surface
  used. No MCP knowledge tool or internal CLI was detected, so the domain and
  in-flight context here come from repository evidence and the lifecycle
  owner rather than from an enterprise system.
- A delivery system's own hierarchy carries a rung coarse enough to hang an
  outcome on. Verified for Jira Software: three levels, Epic at L1, Story at
  L0, Subtask at L-1, from Atlassian's own documentation.
- A team will state an outcome for that rung when asked, or has already written
  one somewhere the tracker holds. If neither is true the view has a delivery
  half and an empty outcome half, which is a weaker product than it looks.
- An Epic-level outcome is coarse enough to be useful. It is certainly coarser
  than an intent-level one, and whether the loss matters is the thing the first
  slice finds out.
- Standalone value does not reduce adoption of the intent system. The opposite
  is assumed — that a team which can see the gap at Epic granularity wants it
  at intent granularity — but nothing in the record establishes it, and the
  reverse is a coherent outcome.
- The delivery half needs little new work on Jira. `jira-team-status` already
  reports readiness, blocked, in-progress, unassigned, stale and dependency
  risk; `flow-metrics` already computes nine metrics at p50, p75 and p90 from
  changelogs. Whether the same holds for a second delivery system is unknown:
  `linear` and `github` ship no standalone skill at all today.

## De-risk — SURVIVES, 2026-09-24

**Reversibility triage: two-way door.** A read-only skill in one pack, no
migration, no public contract, nothing written anywhere. If nobody uses it,
delete it. That default would be `prototype-led`; it is overridden to
`validate-first`, because a corpus probe is cheaper than a prototype here and
can genuinely kill the bet.

### The riskiest assumption

A team will supply an outcome for a tracker rung it already manages. The
delivery half is nearly free — `jira-team-status` and `flow-metrics` ship
today — so the whole added value rests on somebody typing one sentence per
Epic.

**What would have to be true.** First, that the *declaring* act — stating an
outcome once, when prompted — is reliably performed by a population that has
to live with the result. Second, that what gets declared is substantive rather
than template text.

This is deliberately not the *checking* act.
[FEAT-0012](FEAT-0012-timeline-and-strategic-progress-review.md)'s de-risk
already established that checking is never done here. FEAT-0013 asks only for
the declaration.

### The predeclared line

Set 2026-09-24 before any measurement, in a qualitative bar with corpus counts
as its currency:

> KILLED if either holds over this repository's own intent corpus: fewer than
> 80% of intents declare an outcome at all, or more than 30% of those that do
> are placeholder rather than a stated result. SURVIVES only if both are
> false.

80%, because the ask is a single prompted field performed by the population
most motivated to comply; one that cannot clear 80% gives no reason to expect
an unmotivated team to clear anything. 30%, because a template-junk
declaration is worse than an absent one — it reads as answered.

### The result

Over all 154 intents in `docs/product/intents/`:

| Measure | Result | Line |
| --- | --- | --- |
| Declares an outcome at all | **153 of 154 — 99.4%** | kill below 80% |
| Placeholder share of those | **2 of 153 — 1.3%** | kill above 30% |

One intent has no outcome section; two are thin. Substantive declarations run
a median of 26 words.

**The contrast is the finding.** The same population, on the same artifact,
performs one act almost without exception and the other never: **declaring an
outcome, 153 of 154; checking whether it moved, 0 of 14 Fulfilled.** FEAT-0013
asks only for the act that already happens.

A first instrument measured the `**Outcome (lagging):**` sub-field and
returned 6%. That was a template-version marker rather than the declaring act,
and most of the corpus predates the three-part outcome shape while still
stating an outcome in prose. The line was not moved; the instrument was
corrected.

### What the result does not establish

This population is prompted by a skill, motivated, and one maintainer. A Jira
team is unprompted, unmotivated and plural. Desk-grounding is not validation,
so the hook below stays `to-validate`.

```yaml
validation_hook:
  status: to-validate
  assumption: >
    A team will supply an outcome for a tracker rung it already manages.
  kill_condition: >
    Predeclared 2026-09-24: fewer than 80% declare an outcome when prompted,
    or more than 30% of declarations are placeholder rather than a stated
    result.
  activity: >
    Sit with two or three teams running Jira. Ask each to write an outcome for
    five live Epics. Record how many complete it, how long it takes, and what
    they write when they cannot — the last is the one that tells you whether
    the prompt is wrong or the ask is.
```

## Decomposition

**One slice, `jira-epic-outcome-view`**, handed to `new-spec` as a delivery
contract rather than through a delivery brief. A brief coordinates a
multi-spec or cross-repository outcome; this is one independently shippable
feature in one pack, and 187 of the repository's 230 registered specs already
take the direct route.

### Why one and not several

Three cuts were considered and dropped.

- **The composed view first, outcomes second.** Rejected: the view without
  outcomes is barely more than running `jira-team-status` and `flow-metrics`
  separately, so the first slice would carry almost no delta and the second
  would carry the whole bet.
- **Outcome capture first, the view second.** Rejected for the mirror reason:
  capture alone produces outcome text nobody reads. Neither half is
  independently valuable, which is the test for whether they are one slice.
- **One slice per delivery system.** Not cut yet rather than rejected. This
  feature is provider-general and Jira Software is its first slice; a second
  provider becomes a second slice when someone wants it, which this intent's
  non-goals already state. Cutting it now would emit a spec with no demand
  behind it.

### Also considered, and it belongs elsewhere

A conformance lint for
[ADR-0126](../../adr/0126-integration-packs-standalone-value-and-bridge-skills.md)'s
D1 through D4 — the ADR names `lint/CI` as its Confirmation mode and no such
lint exists. It is deliberately **not** in this feature's cut: a repository-wide
governance check is not this feature's outcome, and putting it here would give
a product slice an obligation it does not own. It also cannot land green today,
because `linear` and `github` each ship zero standalone skills and would fail
D1 on the first run. It needs its own item, sequenced after those packs gain a
standalone skill or given an explicit waiver route.

### The delivery contract

- **Outcome.** A team running Jira Software, having adopted nothing of this
  repository, reads where its work stands and what that work was meant to
  change, in one view, from its own tracker.
- **Success signal.** Qualitative and falsifiable: the view is used more than
  once with no repository artifact of ours in existence, and the team can say
  what adopting the intent system would add.
- **In scope.** Composing the state and flow readings that already ship with an
  outcome attached at the Epic rung; eliciting that outcome from the team when
  the tracker does not already hold one; rendering both together so neither
  answer stands in for the other.
- **Non-goals.** Any write to Jira. Any repository artifact, including a
  mapping file keyed by an Epic. Any outcome authored by this feature rather
  than by the team. Any second delivery system. Any dependency on the intent
  tree, `docs/product/`, `workspace.toml` or the `work-intake` route.
- **Dependencies.** None of this repository's machinery, by contract. It
  composes `packs/atlassian/.apm/skills/jira-team-status` and
  `packs/atlassian/.apm/skills/flow-metrics`, both of which carry zero coupling
  references today, and reads Jira through the shipped `jira` client.
- **Design context.** Jira Software carries three levels — Epic at L1, Story at
  L0, Subtask at L-1 — so the Epic is the coarsest rung a team already manages
  and the natural place to hang an outcome. `flow-metrics` emits nine metrics
  at p50, p75 and p90; a percentile rendered below its sample threshold is the
  known failure mode, and the thresholds are 5, 11 and 29 at 95% confidence.
- **Delivery questions for the spec stage.** Where an elicited outcome lives
  between one invocation and the next, given no repository artifact is
  permitted and no write to Jira is either — the honest answers are "nowhere,
  it is re-elicited" or "the team writes it into Jira themselves, and this
  reads it." Which of those the slice takes is the spec's first decision, and
  it is the decision that determines whether the view is useful on its second
  use.
- **Provenance.** This intent, de-risked 2026-09-24 with a surviving verdict;
  ADR-0126, Accepted 2026-09-24; survey findings F18 and F19 in
  [`docs/product/research/tracker-coexistence-adoption-survey.md`](../research/tracker-coexistence-adoption-survey.md).
