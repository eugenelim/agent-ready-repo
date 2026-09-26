# Intent: a team runs its day on a board it never had to build

- **Slug:** `intent-backed-working-view`
- **Status:** Accepted
- **Accepted:** 2026-09-24 by eugenelim, lifecycle owner. The basis: framed and reviewed clean in intent mode at revision `ce13cf8603d54841`; de-risked over two probes, killed on this repository's corpus and surviving on the enterprise population the owner set as governing; reframed to the projected range ADR-0125 then decided; and decomposed into a delivery brief. The reframe carries a `to-validate` hook — no adopter has run it.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:external-tracker-projection
- **Shaping-reviewed:** 2026-09-23
- **De-risked:** 2026-09-23
- **Decomposed:** 2026-09-23 brief

## Outcome

- **Input (steerable):** How much a person must create or update by hand to keep
  the team's board true to the canonical work. This is the metric that decides
  whether the practice survives: the measured failure for this class of change
  is pilot-then-abandon, and the predictor is whether keeping the artifact
  current is a byproduct of work someone had to do anyway or a separate act of
  maintenance. Drive it toward byproduct.
- **Outcome (lagging):** A team runs its day — picking work up, seeing what
  moved, flagging what is stuck — from its own delivery system, over work whose
  meaning lives in the repository, with no second model of that work maintained
  anywhere. **The signal accepted as proof is qualitative and falsifiable:**
  nobody on the team is keeping a parallel hand-built hierarchy, and nobody
  needs to talk a newcomer through why the board is not quite right.
- **Guardrail:** Three things must not get worse. Nothing agent-internal becomes
  a managed item — the floor holds. Nothing done on the board rewrites canonical
  intent, so authority does not move. And the count of items a person is asked
  to manage stays inside what that person actually manages: **a faithful
  projection that doubles the board is a failure even if every item on it is
  correct.**

## Opportunity

- **Functional job:** Run my day over work whose meaning is defined somewhere
  else — pick up what is mine, see what has moved, flag what is stuck, show
  someone the state — without re-entering that work by hand first.
- **Emotional job:** Trust that the board is telling the truth about what is
  happening, and not feel that keeping it true is a second job I do after the
  real one.
- **Social job:** Show the board to a colleague, a manager or a stakeholder and
  have it be the real picture, rather than a maintained fiction I have to talk
  them through.
- **Struggling moment:** The board has two settings and neither works. Hand-kept,
  it drifts the first week someone is busy, and the upkeep is a tax somebody
  quietly pays until they stop. Fed from execution, it fills with things nobody
  schedules, assigns or unblocks. There is no setting that is both true and
  manageable — and agentic execution widens the gap, because the things that
  move fastest are the things least worth managing.

## Boundary

Owns what crosses the seam outward, in both directions of content flow:

- **Which rungs of the canonical hierarchy become tracker-visible, and at what
  granularity** — including the managed-unit floor that keeps agent plans,
  subagent jobs, retries and implementation microtasks off the board.
- **How each provider's hierarchy and vocabulary is absorbed at the edge**
  rather than in the product model.
- **How a tracker-side item names its canonical origin**, so the relationship is
  readable from both ends.
- **The return leg: shaped intent reaching the item itself.** A team whose only
  touchpoint is the tracker should find the outcome, scope and criteria on the
  item, without visiting the repository. The parent's decomposition log places
  this here rather than in a separate child, because it serves this feature's
  outcome by a different route.

Delivery systems are **variants inside this feature**, not separate features.
How the work is *sliced* is the brief's to decide and it cuts one spec per
delivery system, with the first setting a pattern the rest conform to — that is
a delivery shape, not a second feature. The outcome has to be real on at least
one delivery system before it ships.

Does not own delivery-state or flow observation
([FEAT-0011](FEAT-0012-delivery-state-and-flow-visibility.md)), forecast or
outcome review
([FEAT-0012](FEAT-0013-timeline-and-strategic-progress-review.md)), or intent
identity and placement
([FEAT-0001](FEAT-0001-intent-identity-and-registration.md)).

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Framing

**Run under `frame-intent` on 2026-09-23**, replacing the placeholder measures
the parent's decomposition seeded on the same day.

**Scale `app`, inferred not asked** — one repository publishing one product,
consistent with every sibling in this corpus. **Maturity `brownfield`** — both
sides of this seam already have shipped parts.

**Altitude `feature`, tested rather than inherited.** The shippability test
asks whether this reduces to a single vertical slice. It does: for one
provider, take one canonical feature intent and its specs and make the
corresponding items exist and carry a back-reference at a stated floor — that
ships and tests on its own. The remaining providers and the return leg are
further slices of the same outcome, not different outcomes. Several
independently shippable changes in one repository projects to a brief with
specs beneath it under ADR-0077 D1; that is the expected shape at this
altitude and is not a signal the altitude is wrong.

**Knowledge surface: in-repo doc set** (`docs/adr/`, `docs/product/`, the three
provider packs, `packs/product-engineering/`). No MCP knowledge tool and no
internal CLI was present. The in-flight check found no outbound projection
shipping today and no artifact in the corpus carrying a non-`repo-origin`
source mode.

**Brownfield current-state inputs, taken as constraints rather than targets.**
Two existing journeys bound this feature and neither is something to pave
further. [pm-intakes-from-tracker](../journeys/pm-intakes-from-tracker.md)
documents the inbound half of this seam as it works today, and this feature
must not contradict it.
[team-evaluates-and-adopts](../journeys/team-evaluates-and-adopts.md) records
the reversion pattern at its embedding stage — engineers hit friction on a
non-standard case and return to the old workflow — which is the same failure
this intent's steerable input is aimed at.

### Optional Core shaping review — intent mode, clean

Dispatched to Core's `shaping-reviewer` in `intent` mode on 2026-09-23 against
revision `ce13cf8603d54841`, with one attributed evidence packet: this intent,
its Accepted parent, its two siblings, the survey it cites by finding number,
and the four installed-skill contracts it must satisfy. The packet was supplied
as data and the reviewer was told not to retrieve beyond it. The brief asked it
to check, among the field rules, that each survey finding cited by number says
what this intent claims it says.

**Result: no `MALFORMED` tokens.** Empty token output is this mode's pass
state, and completion was read from this caller's host rather than inferred
from the output. The file was unchanged between dispatch and this record, so
the reviewed revision is the current one and no nonmaterial-correction caveat
applies.

A review result sets no status and makes no decision. This intent stays
`Draft`; `de-risk-intent` runs next.

## Assumptions

What must be true for this bet to pay off. Not tested here; `de-risk-intent`
picks the riskiest and predeclares a kill condition for it.

- **A team will work a board it did not build by hand, provided the items are
  the right size.** This is the feature's desirability bet and the likeliest
  candidate for the riskiest assumption.
- **A granularity exists that is both stable enough to project without churn and
  frequent enough to be worth looking at.** If the only stable unit is too
  coarse to show movement and the only unit that moves is too volatile to
  manage, this feature has nothing to stand on.
- **Partial beats faithful.** Teams want the meaningful rungs, not the whole
  tree; a complete projection would be rejected as noise. This is the assumption
  behind the item-count guardrail.
- **A back-reference is enough to make the relationship trustworthy.** People do
  not need the tracker to reproduce the tree, only to say where an item came
  from.
- **Provider differences can be absorbed at the edge without the team noticing
  which compromise was made** for their provider.
- **The return leg is valued on its own.** Better content on an item a team
  already has is useful before any hierarchy is projected — which, if true,
  makes it the cheapest first stage rather than the second one, because it asks
  nothing of the reporting layer.
- **Knowledge surface:** in-repo doc set; none other detected.

### Inherited from the parent

Carried, not restated in full — [CAP-0004](CAP-0004-external-tracker-projection.md)'s
§ Assumptions holds the whole set. The five that bind this child directly:
canonical meaning stays in the repository; tracker activity never silently
rewrites it (ADR-0019 D5 one-way for repo-origin, as ADR-0077 D6–D12 refine
it into two authority modes); agent-internal work is not
a management unit; no new daemon, control plane, database or scheduler; and
`core` gains no provider-specific coupling while the intent model gains no
provider-specific hierarchy.

## De-risk — two probes, 2026-09-23

**Governing verdict: SURVIVES** on the enterprise population, which is the
design population. Probe 1 killed the bet on this repository's own corpus;
probe 2 tested the same assumption on enterprise evidence and it survived. The
owner reweighted the corpus on 2026-09-23 — see § Weighting. Both probes are
recorded in full; neither line was edited after its result.

### Probe 1 — this repository's corpus: KILLED

**Reversibility triage: one-way door**, so `validate-first` — the default and
what ran. The feature itself is reversible while nothing ships, but a
granularity choice is not: once a team's board is built at a floor, moving the
floor re-cuts every item on it. The bet was therefore tested before building.

### The riskiest assumption

*A projection granularity exists that is simultaneously stable enough to
project without churn, coarse enough not to be an agent-internal unit, and
frequent enough that a board built on it is worth a person's attention.*

This displaced the candidate the framing flagged — "a team will work a board it
did not build by hand, provided the items are the right size." Teams already
work boards they did not build; the whole load sits on *the right size*, so
that assumption collapses into this one.

**What would have to be true:** either the stable canonical unit (the
spec/slice) moves often enough to show flow, **or** an intermediate unit exists
between the spec and the agent task whose identity survives replanning.

### The kill condition, predeclared blind

Written at **2026-09-23T16:08:50Z**, before any measurement was run and before
the external evidence for the parent's de-risk had returned. Reproduced
verbatim; not edited after the result:

> KILLED if BOTH hold over this repository's own real delivery history:
> (i) the median shipped spec produces fewer than 3 observable state changes
> across its lifetime, or its median lifetime exceeds 14 days — i.e. a weekly
> board built on specs is substantially static; AND (ii) no intermediate unit
> between spec and agent task has identity that survives a replan — i.e. the
> only finer unit churns.
> SURVIVES if either (i) is false or (ii) is false.

### The probe, and the instrument check that preceded it

Corpus: this repository, which [STRAT-0001](STRAT-0001-graph-powered-sdlc.md)
nominates as the only corpus available to falsify the design. 474 specs, 437
having reached `Shipped`; random sample of 60, seed `20260923`.

**Before trusting the measure:** the proxy for "observable state change" is the
distinct values of the durable `- **Status:**` field across a spec's git
history. That is the right instrument, because nothing in the work-loop scripts
*writes* that field — the engine only reads and guards it — and the engine's own
richer phase state lives in per-spec `engine-state.json` / `state.json`, which
`.gitignore` declares "per-spec scratch, never committed." There is no richer
durable state a projection could read.

**(i) TRUE.** Median distinct `Status` values per shipped spec: **2** (mean
1.6); only **4 of 60** reached 3 or more. The first clause is satisfied, so
(i) holds. The second clause is not: median lifetime is **4 days** (mean 13.9,
max 87), with **45 of 60** completing inside 14 days.

**(ii) TRUE.** The only unit between the spec and the agent task is the
**wave**, and it has no identity. `topological_waves` builds waves as a plain
list of frontiers computed from the dependency graph and numbered from zero;
`schedule_unfinished_plan` first drops every completed task, so a re-schedule
recomputes waves over a strictly smaller graph. Wave 1 before an amendment is
not wave 1 after it. On a contract amendment the state sets `schedule_waves: []`
and `current_wave_index: 0` explicitly. Task IDs *do* survive — an amendment
preserves `completed_task_ids` — but a plan task is an agent-execution unit, and
this intent's own guardrail forbids projecting one.

### Verdict

Both conditions hold. The kill required both. **KILLED.**

### What the kill actually taught, which is not what it predicted

The predeclared line guessed the failure would be *staleness* — a board where
nothing moves. The measurement says the opposite: specs are **fast**, with a
median life of four days. The failure is that **nothing dwells**. A board earns
its keep when items sit in columns long enough to be seen ageing, blocking and
queueing; items that appear and complete inside a week while exposing two
states never occupy a column. Flow is invisible not because the work is slow
but because the unit is too short-lived to observe.

That reframes what a fix would have to do, and the candidate is specific: stop
treating the **spec** as the projected item. The **feature intent** is durable,
human-meaningful, lives for weeks, is above the agent-internal floor by
construction, and carries a real lifecycle vocabulary. Specs would become
evidence attached to an item rather than items themselves. This is a candidate,
not a decision — it belongs to a fresh `frame-intent`, not to this record.

### Scope of the kill — what it does and does not establish

It establishes that the granularity does not exist **in this corpus**, which is
the corpus the strategy nominated as its falsifier. It does **not** establish
that no adopter has such a unit: this repository is the extreme agentic case,
and a traditional-SDLC team whose stories sit in columns for weeks may well
have one. That possibility is untested and is not offered as consolation.

### This kill bubbles up

Per `de-risk-intent`, a killed child bubbles to its parent rather than being
absorbed here. Three consequences, none actioned in this record:

- **[CAP-0004](CAP-0004-external-tracker-projection.md) is Accepted**, and
  carries "whether the managed-unit floor can be stated once, or has to be
  negotiated per provider and per team" as an **unresolved question**. This
  probe answers it. Recording that answer on an Accepted intent is the
  lifecycle owner's decision, because a change to an intent's unresolved
  questions is material and returns it to `Draft`.
- **[FEAT-0011](FEAT-0012-delivery-state-and-flow-visibility.md)** reads flow
  over these items. If nothing dwells, there is little flow to observe.
- **[FEAT-0012](FEAT-0013-timeline-and-strategic-progress-review.md)** counts
  units for a forecast. Monte Carlo assumes a stable item-size distribution.

```
validation_hook:
  assumption: a projection granularity exists that is stable, above the
    agent-internal floor, and frequent enough to be worth watching
  kill_condition: as predeclared 2026-09-23T16:08:50Z above
  status: KILLED on this repository's corpus
  activity: before any reframe is trusted, measure the same two conditions at
    one traditional-SDLC adopter — item dwell time per column and whether an
    intermediate grouping survives replanning. The kill here is one corpus
  untested: whether the feature-intent tier clears both conditions. It is the
    obvious candidate and has not been measured
```

### Weighting — the corpus is low-weight, by owner decision

Recorded 2026-09-23 by the lifecycle owner: **this repository's corpus carries
low weight for this intent**, because the kit is deployed broadly and the
design population is adopting teams, not its solo maintainer. Probe 1's corpus
is one team at extreme velocity — a median shipped spec of four days is a
property of that maintainer, not of the artifact class.

Probe 1's verdict is **not reversed and not rewritten**. It stands as a true
finding about that corpus and as the reason the reframe below exists. What
changed is which population governs, and that is an owner call about scope, not
a relitigation of a predeclared line.

### Probe 2 — the enterprise population: SURVIVES

**Kill condition predeclared 2026-09-23T20:07:45Z**, before any retrieval was
dispatched. Reproduced verbatim:

> KILLED if BOTH hold across the retrieved evidence: (i) published enterprise
> delivery data shows the comparable managed unit does NOT dwell —
> operationally, reported median cycle time for a story/feature-class item is
> <= 5 days AND typical items are reported to occupy fewer than 3 distinct
> workflow states in practice; AND (ii) no intermediate grouping between the
> managed item and execution detail (epic, feature, sprint, increment) is
> reported to retain identity across replanning.
> SURVIVES if EITHER (i) is false or (ii) is false.

Three independent retrievals ran against published enterprise data — two
Claude subagents and one Codex worker on a different model and search path.
**The independence earned its cost:** the two Claude retrievals concluded that
state occupancy had no quantitative evidence at all, and the Codex worker
found two peer-reviewed process-mining studies that measure it directly. The
correlated-search failure that a single retrieval path would have produced is
recorded here because it nearly inverted the strength of this verdict.

**(ii) is FALSE — this is the deciding leg, and it rests on positive
evidence.** An intermediate grouping is reported to retain identity: a SAFe
epic "spans at least two PIs" and may extend across two or more years, being
*refined* at each PI boundary rather than replaced. Independently, PMO
practitioner material converges on enterprises tracking and reporting at the
**epic tier** while story-level detail stays at team level. So the tier exists,
persists across replanning cycles, and is the tier organisations already manage
at.

**(i) is FALSE on measured, peer-reviewed, non-vendor evidence.** Its two
clauses are an AND, and the state-occupancy clause is directly refuted.

A 2023 process-mining study at **Thermo Fisher Scientific** — a real
enterprise, 14,739 nonduplicate Jira issues across 24 teams and 74
repositories — found feature paths commonly spanning **four states** (Inbox,
To Do, In Progress, Done), or five where testing occurred, with about 10% of
one team's features moving backwards from Done to In Test. An earlier IEEE
case study reconstructed full status histories for 795 completed issues and
recorded 6,011 status events — **7.56 state visits per issue**, with the
dominant path traversing **six distinct statuses** and 176 distinct path
variants observed. Neither is vendor-published.

Four to six distinct states is not "fewer than 3." The clause is refuted, so
the conjunction fails and the kill does not fire.

The cycle-time clause remains unestablished rather than refuted: the hard
numbers available measure the **pull-request sub-interval**, not the full
ticket lifecycle — a median full PR cycle time of 83 hours across several
hundred organisations, and an average of about 7 days across roughly 3,000
teams, of which about 4 days is waiting on review. Full-ticket dwell wraps
that interval plus queueing before and after, so it is longer by an unmeasured
amount. That clause did not need to resolve, because the conjunction was
already broken.

What does **not** exist is a representative cross-enterprise *distribution* of
states occupied per item. Team-level and single-enterprise measurements exist;
a benchmark to borrow does not.

**Both conditions false. The kill required both. SURVIVES.**

### Counter-evidence carried, not buried

Three findings cut against the surviving verdict and belong with it.

- **The (ii) evidence is part normative and part proxy; hierarchy churn itself
  is still unmeasured.** SAFe *prescribes* epic durability. A 2025 University
  of Hamburg dissertation supplies a measured lifespan proxy from public Jira
  repositories: recorded epic changes occur at a **median 81 days after
  creation**, epic workflow-field changes at 118 days, and resolution changes
  at 164 days, with epics and new features carrying roughly five more field
  changes than other requirement types. Epics are therefore demonstrably
  touched for months, not weeks. But that is public open-source Jira rather
  than enterprise delivery data, and it measures change *timing*, not
  end-to-end lifespan. No study measures split, merge, re-parent or renumber
  rates — a related 2022 paper characterises the *static* structure of 607,208
  Jira links (97.7% of composition-link graphs are hierarchical trees) without
  measuring how those trees change through replanning. The dataset behind it
  holds 2.7 million issues and 32 million historical changes, so the churn
  question is technically answerable and simply has not been asked.
- **The same framework builds in drift.** SAFe separates committed from
  uncommitted PI objectives precisely because a train that commits to
  everything has no slack for mid-increment variance, and unfinished sprint
  work is re-estimated at the boundary. The container is stable; its contents
  are expected to move.
- **A commercial value-stream product declined to trust native hierarchy.**
  Planview/Tasktop's Flow Framework defines its own normalized *flow item*
  (feature, defect, risk, debt) rather than reporting against each tool's epic
  and story tiers — so that metrics survive differences and instability between
  them. That a vendor had to invent a hierarchy-independent unit is inference
  about native-tier reliability, not a measurement, and it points the same way
  as probe 1.

### The standing caveat, predeclared so it could not be dropped

A survive here is **conditional**, and the condition was written into the line
before the evidence returned: the items this capability would project are *our*
canonical artifacts, not the enterprise's own Jira stories. Evidence that an
enterprise epic dwells does not establish that a repository-canonical artifact
would dwell at an enterprise adopter. That remains unmeasured and no adopter
exists to measure it.

### The reframe the two probes together produce

Probe 1 said the **spec** is the wrong unit: four days, two states, and the
only grouping beneath it — the wave — is renumbered from zero on every
re-schedule. Probe 2 said a durable tier **does** exist in enterprise practice
and names where: the epic/feature tier, which is also where PMOs already
report.

**The projected managed unit is the feature intent, not the spec.** A feature
intent is durable, human-meaningful, sits above the agent-internal floor by
construction, and carries a real lifecycle vocabulary. **Superseded in scope by
[ADR-0125](../../adr/0125-managed-unit-floor-and-projected-range.md), which
decided a range rather than a single rung**: the feature intent is the floor for
same-repository work, the delivery brief is the floor where work crosses a
repository boundary, and the rungs above the floor project too. The reframe this
records is what the ADR built on; read the ADR for what governs. Specs, plans, waves and
tasks become **execution evidence attached to an item**, never items
themselves.

Four independent lines converge on that tier: the enterprise epic tier that
PMOs report at; Planview's feature-level flow item, chosen specifically to be
hierarchy-independent; Symphony's placement of the floor at the work item with
the agent run below it (survey F14); and probe 1's finding that everything
below the intent tier is too short-lived to watch.

**This is a reframe, not a validated design.** It is written into § Outcome and
§ Boundary above, and it inherits the standing caveat: no adopter has run it.

```
validation_hook:
  assumption: the feature-intent tier is stable and long-lived enough to be
    the projected managed unit, and specs below it are evidence rather than
    items
  kill_condition: at the first adopting enterprise, if feature-intent-tier
    items do not dwell long enough to occupy a board column, or if teams
    insist on managing at spec granularity anyway, the reframe fails the same
    way the spec tier did
  status: to-validate. Probe 2 survived on published evidence about the
    enterprise epic tier, not about this repository's artifacts projected
    into it
  activity: measure item dwell time per column and state occupancy at one
    adopting enterprise, against its own tenant data. No external benchmark
    for state occupancy exists to borrow — the research established that
    absence directly
  unmeasured: whether a repo-canonical feature intent behaves like an
    enterprise epic once projected. There is no adopter and no proxy
```

## Open for shaping

Deliberately undecided. Each belongs to shaping, spec or architecture.

- The normalized projection schema, and whether one exists at all.
- The exact per-provider hierarchy mapping, including Jira Software's, which the
  existing `decompose-intent` tracker-projection reference does not cover.
- Whether new GitHub or Linear packs are required, or the existing thin ones
  extend.
- Write-versus-read mechanics, and how far the accepted one-way rule reaches.
- Provider capability negotiation.
- ~~Where the managed-unit floor sits, and whether it is one rule or negotiated
  per team.~~ **Answered by
  [ADR-0125](../../adr/0125-managed-unit-floor-and-projected-range.md),
  Accepted 2026-09-23.** The projection is a range running from the tree's top
  rung down to a floor that sits at the delivery brief where work crosses a
  repository boundary and at the feature intent otherwise. The floor is fixed
  rather than negotiated per team, and rungs above it collapse onto provider
  depth rather than truncating. The answer carries a `to-validate` hook: no
  adopter has run it.
- ~~Which of the two directions ships first.~~ **Dissolved by the accepted cut,
  2026-09-24.** Neither does: each slice carries one delivery system's outward
  projection and its return leg together, and the Jira Software slice ships
  first and sets the pattern the other three conform to. That pairing is
  recorded as the owner's cut and is not tested — whether a projection and its
  return leg are one shippable slice or two is a spec-stage question.

## Starting points in this repository

Locations, not contents — open them when shaping.

- `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
  — the existing level-to-object profile table for `none`, Linear and Jira
  Align, and its statement of what v1 does and does not ship.
- `packs/atlassian/.apm/skills/jira-story-triage/` — the only shipped outbound
  content path. Its five-question readiness bar, its per-item confirmation
  showing exact fields and old values, and its protected-field set are the
  working precedent for the return leg.
- `packs/linear/`, `packs/github/` — the two provider packs with no equivalent,
  which is where the asymmetry sits.
- `docs/adr/0077-feature-projection-and-tracker-authority.md` — the accepted
  authority and refresh rules this feature must not contradict.

## Evidence now available

From the parent's de-risk, 2026-09-23 —
[applied survey](../research/tracker-coexistence-adoption-survey.md).

- **The managed-unit floor has prior art pointing the same way.** OpenAI's
  Symphony ("manage work instead of supervising coding agents") places the floor
  at the tracker work item with the agent run below the line. It gets there by
  making the tracker the queue agents pull from — the opposite authority
  direction to this one. Survey F14.
- **Projection must be a byproduct, not a separate act.** Half of 921
  repositories adopting decision records hold one to five: pilot, then
  abandonment. This is the origin of the steerable input above. Survey F3.
- **Hierarchy limits are partly pinned.** GitHub sub-issues: maximum depth 8,
  maximum 100 per level, single parent only. Jira Software's native depth and
  the Jira → Jira Align tier rename could not be verified and are recorded as
  open. Survey F6.
- **One-way projection is corroborated from outside.** Named bidirectional
  failure mechanisms, and two independent teams choosing one-way. Survey F5.
- **The first stage must not require the reporting layer to move.** Staged
  adoption is the only documented pattern, and organisational friction — not
  technical difficulty — is the top-ranked blocker at 47%. Survey F2, F7.

## Decomposition

Decomposed 2026-09-23 into a **delivery brief** —
[a team works its canonical intent from inside its own tracker](../briefs/intent-backed-working-view.md).
ADR-0077 D1 selects that shape: several independently shippable changes in one
repository become a brief, not a bare spec.

Slice membership, ordering and the candidate cut are the brief's. Nothing is
materialized beneath it: no slice is confirmed and no spec exists. Read the
brief; this record does not carry a second copy.

```
FEAT-0010  Intent-backed working view
└─ brief: intent-backed-working-view
   └─ candidate cut, nothing confirmed — see the brief
```

### Why a brief rather than a spec

Framing rationale only. Each point below explains the decomposition; none of
them decides membership.

- **2026-09-23 — the managed-unit floor belongs in a decision record, not in a
  slice.** It is architecturally significant, expensive to reverse once a team's
  board is built on it, and it constrains work beyond this feature:
  [FEAT-0011](FEAT-0012-delivery-state-and-flow-visibility.md)'s flow readings
  and [FEAT-0012](FEAT-0013-timeline-and-strategic-progress-review.md)'s
  forecast both count whatever the floor admits. Burying a decision that three
  artifacts depend on inside one spec's body is how it becomes unfindable. It
  is now [ADR-0125](../../adr/0125-managed-unit-floor-and-projected-range.md).
- **2026-09-23 — a decomposition that ships no code can still be a slice.** With
  a hierarchy mapping stated, a team can project by hand, which is exactly the
  `none` rendering the shipped `decompose-intent` reference treats as
  first-class. That is a deliverable outcome, not documentation attached to
  another one.
- **2026-09-23 — decomposing against a reframe that no adopter has run is a
  deliberate, recorded choice.** The de-risk verdict is `SURVIVES`, so the entry
  condition is met. But the surviving bet rests on a reframe — the feature-intent
  tier — carrying a `to-validate` hook. Whatever slices the brief carries
  inherit that, and the brief states it rather than letting a spec read as
  though the tier were settled.
