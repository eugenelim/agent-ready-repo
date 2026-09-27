# Delivery-system coexistence

- **Slug:** `external-tracker-projection`
- **Status:** Accepted
- **Accepted:** 2026-09-23 by eugenelim, lifecycle owner, on owner authority, and re-accepted the same day after a material change: the projection rule is now stated for the authority mode it governs, and the managed-unit floor question is recorded as answered by ADR-0127. The basis: the riskiest assumption was tested under `de-risk-intent` against a kill condition predeclared before the evidence returned, and survived; the altitude was re-tested under `frame-intent` and held at `capability` on two discriminators drawn from the parent's own recorded reasoning; and Core's `shaping-reviewer` returned a clean intent-mode pass at revision `deba52f7bd484622`. A review result sets no status — this line is the owner's act, and the reviews are evidence for it.
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc
- **De-risked:** 2026-09-23
- **Shaping-reviewed:** 2026-09-23
- **Decomposed:** 2026-09-23 children

> **Widened 2026-09-23, from outbound projection to coexistence.** This intent
> was framed on 2026-09-18 as *External tracker projection* — rendering the
> canonical graph outward. It carried no de-risk, no children and no delivery,
> so it was widened in place rather than given a peer. The outcome now covers
> the whole seam between repository-canonical product intent and a team's
> normal delivery-management system: the working view, delivery state and flow,
> and timeline and strategic-progress review. The original outbound-projection
> scope is unchanged and is now one of three children. The slug is unchanged
> because twenty artifacts reference it; see § Unresolved questions.

## Outcome

- **Steerable input:** How much a team must maintain by hand to keep its
  delivery system useful over repository-canonical intent. Two things are paid
  today and both are movable: the effort to make canonical intent visible and
  answerable in Jira, GitHub Issues + Projects or Linear, and the number of
  times a tracker's vocabulary, hierarchy or reporting need is answered by
  reshaping the product model rather than absorbing it at the edge. The second
  is the one that compounds, because each time it happens the model is
  permanently worse.
- **Lagging outcome:** A team keeps product intent, outcome, scope and
  decomposition canonical in the repository while running operational
  coordination, Kanban flow, timelines and progress reporting in the delivery
  system it already uses — and can answer *when will this land* and *how far
  toward the outcome are we* without either being answered by ticket counts.
- **Guardrail:** The repository stays the authority for product meaning. A
  tracker may own operational observation and never silently rewrites canonical
  intent — and, in the other direction, the canonical artifact does not go
  stale while the tracker item quietly accrues the real scope. Agent plans, subagent jobs, retries and implementation microtasks do
  not become management tickets in order to make reporting work. Delivery
  completion and outcome progress stay separately reported. A fixed business
  date is never rendered as a forecast, nor a forecast as a commitment. No new
  daemon, control plane, database or scheduler appears. Existing human-control
  boundaries on remote mutation hold. `core` gains no Jira-, GitHub- or
  Linear-specific coupling, and the intent model gains no provider-specific
  hierarchy.

## Opportunity

- **Functional job:** Run the team's normal delivery coordination — a board, a
  standup, a timeline, a status report to leadership — over work whose meaning
  is defined somewhere else, without maintaining a second model of that work.
- **Emotional job:** Answer "can you put this in our tracker" without fearing
  that the answer reshapes what the product means, and answer "so when does it
  land" without either guessing or pretending a forecast is a commitment.
- **Social job:** Be legible to an organisation that runs on a tracker and to
  leadership that asks about strategic outcomes, while keeping the account of
  the work defensible on its own terms.
- **Struggling moment:** The two halves are answered in different places with no
  relation between them, so a team that wants both ends up modelling the work in
  the tracker — and the tracker becomes the authority for product meaning by
  default rather than by decision.

  Three specific gaps sit behind that. **Nothing renders outward.** The
  repository has a canonical recursive intent tree and three tracker packs, but
  every one of them pulls work *in* (`jira-brief-intake`,
  `github-brief-intake`, `linear-brief-intake`) or writes limited coordination
  *back* (`jira-refresh`, `github-refresh`, `linear-brief-sync`); no surface
  renders the canonical tree into a working view, and twelve intents currently
  say so in identical words in their own `## Projection` sections.
  **Flow is one provider deep.** `packs/atlassian/.apm/skills/flow-metrics`
  computes cycle time, lead time, throughput, WIP and flow efficiency from Jira
  changelogs and states in its own description that it must not be used for a
  tracker that is not Jira; a GitHub or Linear team has no equivalent.
  **Nothing relates forecast to outcome.** No surface puts a delivery forecast,
  known scope and risk, and evidence of outcome movement in the same view, so
  "percent of tickets closed" is the only number available and it gets read as
  progress toward the goal.

  Agentic execution sharpens all three, because it breaks the unit of
  management. An agent's plan tasks, subagent jobs and retries are not things a
  person schedules, assigns or unblocks. A tracker fed at that granularity fills
  with items nobody manages; a tracker fed nothing goes silent while the work
  proceeds. Neither is a coordination surface.

## Boundary

This capability owns the seam between repository-canonical product intent and a
delivery-management system used for operational coordination. Within the
parent's outcome and exclusions, it owns:

- **What crosses the seam outward, and at what granularity** — which parts of
  the canonical hierarchy become tracker-visible and actionable, and where the
  floor sits so agent-internal work does not become management tickets.
- **How each provider's hierarchy and vocabulary is absorbed at the edge**
  rather than in the product model, for Jira / Jira Software, GitHub Issues +
  Projects, and Linear at minimum.
- **What crosses the seam inward as observation** — workflow state, assignment,
  blocking and timestamps a tracker legitimately owns, and the limit that keeps
  observation from becoming authority.
- **How delivery forecast, scope and risk, and outcome evidence are reviewed
  together**, including the two separations that review must preserve.
- **Imported-field authority and refresh** for a projected or imported object,
  consistent with ADR-0077's repo-origin and tracker-origin modes and its
  lifecycle-tightening table.

It does not own identity or placement
([FEAT-0001](FEAT-0001-intent-identity-and-registration.md)), the derived graph
it projects from ([FEAT-0002](FEAT-0002-intent-graph-navigation.md)), the
intent-to-delivery mapping
([FEAT-0003](FEAT-0003-intent-delivery-traceability.md)), operational
coordination state
([CAP-0003](CAP-0003-workspace-coordination-reorganization.md)), or the path a
noticed-but-undone item takes
([CAP-0005](CAP-0005-work-item-capture-and-disposition.md)).

It does not decide mechanism. No projection schema, lifecycle-event schema,
adapter shape, pack topology, hierarchy mapping table, flow-calculation home,
capability-negotiation protocol, or synchronisation direction beyond the
accepted one-way rule is chosen at this altitude.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- ~~Whether the slug should be reissued.~~ **Decided 2026-09-23 by the
  lifecycle owner: it is not.** `external-tracker-projection` stays the
  canonical identity even though it now names one of three children rather than
  the capability. The slug is declared independent of the filename ordinal and
  of the heading, and the heading carries the accurate name, so a reader is not
  misled. Reissuing would cost a tombstone and twenty inbound reference updates
  against a renumber-and-reissue workflow that is itself still Draft. The debt
  is a canonical identifier that under-describes its artifact; it is accepted
  knowingly rather than left open. Changing it now is a governed reissue
  ([FEAT-0001](FEAT-0001-intent-identity-and-registration.md) owns that route),
  not an edit.
- Whether the named delivery systems' hierarchies are all reachable from one
  canonical model without a provider-specific rung.
- Whether ADR-0077's two origin modes represent each provider's authority
  lifecycle without a source-specific exception. ADR-0077 names this as its own
  revisit condition.
- Whether a working view is useful without a status round-trip. ADR-0019 D5
  forbids one under repo-origin; ADR-0077 D7, D9 and D10 admit reviewed
  source-owned fields, reviewed deltas and a bounded Shipped write-back under
  tracker-origin, so the question is live only for repo-origin work.
- ~~Whether the managed-unit floor can be stated once, or has to be negotiated
  per provider and per team.~~ **Answered by
  [ADR-0127](../../adr/0127-managed-unit-floor-and-projected-range.md).** The
  projection is a range from the tree's top down to a floor that sits at the
  delivery brief where work crosses a repository boundary and at the feature
  intent otherwise; the floor is fixed rather than negotiated per team, and
  rungs above it collapse onto provider depth rather than truncating. The
  answer carries a `to-validate` hook: no adopter has run it.
- **Whether repo-canonical authority still reads as the default.**
  [OpenAI Symphony](https://github.com/openai/symphony) (Apache-2.0, engineering
  preview) monitors a Linear board for work and spawns agents against it —
  tracker-as-source, the direction this capability refuses. It corroborates the
  managed-unit floor, since "manage work instead of supervising coding agents"
  is the same problem stated the same way. But a high-visibility project
  normalising the opposite authority direction makes repo-first the position
  that must be argued rather than assumed, and this intent does not yet argue
  it for an outside reader.
- **Whether a client that reads the intent tree is inside the no-runtime
  guardrail.** A user-invoked desktop application that navigates the tree and
  shells out to headless Claude or Codex is a client, not a daemon, control
  plane, database or scheduler, so it is arguably admitted. The part that is
  not settled is synchronisation: "do the sync deterministically" is governed
  by the projection rule for this capability's authority mode — ADR-0019 D5
  under repo-origin, as refined by ADR-0077's two modes — not by what the
  client is. Symphony is
  specification-based and permissively licensed, so it is a plausible interop
  target rather than something to rebuild. Raised by the lifecycle owner on
  2026-09-23 as a medium-term direction, deliberately not decided here.
- **How the other drift direction is caught.** The guardrail now names it — the
  canonical artifact going stale while the tracker accrues the real scope — but
  nothing in this capability detects it. GitHub's own `spec-kit` community is
  arguing about exactly this under the name "spec drift", with no consensus.

## Projection

Not yet selected. The outbound surface is this capability's own first child and
is not yet shaped, so no target exists to project to.

## Assumptions

Carried as constraints rather than as a chosen solution. None of these is a
mechanism decision; each bounds what a mechanism may do.

- Product intent, outcome, scope and decomposition stay durable repository
  knowledge. A delivery system holds a render of them, never the original.
- A tracker legitimately owns operational observations — workflow state,
  assignment, blocking, timestamps — and those are the only fields it authors.
- Tracker activity never silently rewrites canonical product intent. ADR-0077
  D6–D12 already encodes this as accepted policy, with refresh tightening by
  local lifecycle and locking during execution.
- Agent plans, subagent jobs, retries and implementation microtasks are not
  management units and do not become tickets to make reporting work.
- Delivery completion and strategic or outcome progress are different measures
  and are reported as two numbers, never one.
- A fixed business date and a probabilistic delivery forecast are distinguishable
  in anything this capability produces.
- No new daemon, control plane, database, scheduler or other runtime is
  introduced to keep these concepts in step. The repository's charter forbids
  it, and the graph-powered-SDLC research already rules out an
  always-current index as unreachable rather than deferred.
- Existing human-control boundaries on remote mutation are preserved. Every
  shipped write-back surface today is confirmation-gated and narrow; nothing
  here widens that.
- `core` acquires no dependency on Jira, GitHub or Linear specifically, and the
  product-engineering intent model acquires no provider-specific hierarchy.
- The named delivery systems can be served by one model with provider handling at
  the edge. **Untested.** `decompose-intent`'s existing tracker-projection
  reference covers Linear and Jira Align as opposite ends of a collapse-or-expand
  axis; GitHub Issues + Projects and Jira Software are unexamined.
- **A regulated adopter may not be reachable by this capability at all.** Where
  the ticket is the audited control artifact — SOX change-to-ticket linkage,
  IEC 62304 / FDA device traceability — the claim that a repository artifact
  satisfies the obligation is vendor-asserted and, in everything retrieved,
  never regulator-confirmed. An academic proposal exists to add traceability
  tooling to GitHub precisely because plain git history does not suffice, and a
  compliance-tooling market exists to bridge the same gap. This is a boundary,
  not a risk to sequence through: such an adopter may need the tracker to
  remain the system of record, which this capability's guardrail forbids.
- **The failure to design against is pilot-then-abandon, not rejection.** Half
  of 921 repositories adopting decision records hold one to five. The
  repository's own [graph-powered SDLC survey](../research/graph-powered-sdlc-survey.md)
  names the predictor: an edge survives when producing it is a byproduct of
  work someone had to do anyway, and dies when it is a separate act of
  documentation. Projection must be a byproduct.
- **Knowledge surface:** in-repo doc set (`docs/adr/`, `docs/product/`,
  `packs/product-engineering/`, `packs/atlassian/`, `packs/github/`,
  `packs/linear/`, `packs/core/`, `workspace.toml`). No MCP knowledge tool or
  internal CLI was present, and no external retrieval was run.

## Framing

### The run — `frame-intent`, 2026-09-23

This intent was widened by hand earlier the same day, from the narrower
*external tracker projection* outcome it was framed with on 2026-09-18, without
re-entering the skill that owns authoring an outcome at an altitude. This is
that run.

**Scale: `app`, inferred and confirmed.** The workspace has application code in
one component — one repository publishing one product — rather than a set of
component pointers. Every sibling intent in this corpus carries `Scale: app`.
Not ambiguous, so it was inferred rather than asked.

**Maturity: `brownfield`.** The seam this intent describes already has shipped
parts on both sides.

**Knowledge surface: in-repo doc set** (`docs/adr/`, `docs/product/`,
`packs/product-engineering/`, `packs/core/`, the three provider packs,
`workspace.toml`). No MCP knowledge tool and no internal CLI was present; a
public web search is not an internal surface and was not counted as one, though
it was used separately for the de-risk. Business domain and meaning came from
ADR-0019, ADR-0033, ADR-0077, ADR-0098 and ADR-0121 and the intent model.
In-flight and roadmap were checked to avoid framing a bet already being
delivered: no artifact in the corpus carries a non-`repo-origin` source mode, so
the inbound authority machinery has never run against a real artifact, and no
outbound surface ships.

**Brownfield current-state input, taken as a constraint rather than a target:**
the [pm-intakes-from-tracker journey](../journeys/pm-intakes-from-tracker.md)
documents the inbound half of this seam as it works today. It is a constraint
because this intent must not contradict it, and not a target because paving it
further is not the outcome.

### The altitude was re-tested and stays `capability`

The sibling-spawn detector fired — three children each serving a different
reader looks like three independent value bets, which is the signal a
`product-strategy` rung is missing. **On examination it is a false positive**,
on two independent discriminators, and it is recorded here so it is not
re-litigated.

**The strategy rung is not missing; it exists and already claims this surface.**
[STRAT-0001](STRAT-0001-graph-powered-sdlc.md)'s fourth coherent action is
"project the canonical graph outward to whichever tracker an organisation
already runs." Promoting this intent to `product-strategy` would nest a strategy
under a strategy and duplicate one of its parent's own coherent actions.

**The children fail independent enterability, which is the parent's own test
for its capability children.** STRAT-0001's Horizon states that "each capability
below is independently enterable and independently valuable." This intent's
three children are chained — flow visibility has nothing to observe until work
is intent-backed, and the review has no forecast to read until flow exists. That
dependency is recorded in `workspace.toml` as `needs` edges, not only in prose.
A chain is the signature of architectural slices of one buildable thing, which
is what a capability parent is for; independent bets are what a strategy parent
is for. This intent's cut is the first.

What misled the detector was reader diversity — a delivery team, a delivery
manager and a sponsor. Serving three readers is ordinary for one capability and
is not the test.

**One word from the lifecycle owner overrides this.** The altitude is a
declared fact about the owner's product tree, not a derivation, and
`frame-intent` treats the inference as a suggestion the owner corrects.

### Optional Core shaping review — intent mode, clean

Dispatched to Core's `shaping-reviewer` in `intent` mode on 2026-09-23 against
revision `deba52f7bd484622`, with one attributed evidence packet: this intent,
its declared parent and three children, the de-risk survey it cites, and the
three installed-skill contracts it must satisfy. The packet was supplied as
data and the reviewer was told not to retrieve beyond it.

**Result: no `MALFORMED` tokens.** Empty token output is this mode's pass
state. Completion was read from this caller's own host rather than inferred
from the output, because a pass carries no bytes to carry it.

**One correction followed the dispatch, and it is recorded as nonmaterial by
this caller.** The framing record and the altitude resolution were moved from
`###` subsections under `## Decomposition` to this top-level `## Framing`
section. The prose is byte-identical; only its heading level and position
changed. Nothing in the outcome, opportunity, assumptions, altitude, evidence
or projection moved, so the review result is retained rather than re-run.

No post-correction digest is recorded here. A file cannot carry its own hash —
writing one changes the bytes it claims to measure, so the value is wrong the
instant it lands. The reviewed content is revision `deba52f7bd484622` plus the
one re-homing described above; `git log` on this path is the durable record of
what changed after it.

A review result changes no status or decision on its own. Lifecycle authority
stays with the owner.

## De-risk

**Run 2026-09-23 under the `de-risk-intent` contract. Verdict: survived, desk-grounded.**
Evidence: [Moving product authority out of the tracker — applied survey](../research/tracker-coexistence-adoption-survey.md),
fourteen findings from four independent retrievals plus this repository's own
[platform-adoption evaluation survey](../research/platform-adoption-evaluation-survey.md).

**Reversibility triage: one-way door**, so the default approach is
`validate-first`, and that is what ran. The artifact itself is reversible —
withdrawing it re-homes three children and changes no state. Two consequences
of delivering it are not: objects created in someone else's tracker persist
after withdrawal, and a team that has moved its operating habits onto a working
view does not move them back for free.

### An earlier candidate was refuted on mechanism, not on evidence

The first riskiest assumption recorded here was *a team keeps product authority
in the repository once the delivery system is its daily surface*. The lifecycle
owner refuted it on 2026-09-23: repo-first is not a bet this capability could
lose, because the agentic loops read canonical repository artifacts in order to
execute. Product-first breaks intent-driven engineering outright, so authority
in the repository is a precondition of the operating model rather than a
preference within it. The failure that assumption feared — silent authority
drift — is additionally forbidden by the mechanism: if the repository is what
the agents build from, drift surfaces as built-wrong, quickly and loudly.

It is recorded rather than deleted because a later reader will propose it again.

### The architectural half takes the fast path

Whether one canonical model can serve the named delivery systems with the hierarchy
absorbed at the edge is cheap to test by building the narrowest version and
reversible if wrong. `Level` is an open field by ADR-0033 D2, so "a provider
needs a rung the model lacks" is answered by naming one — a dependency with a
known shape, not an open bet. ADR-0019 D5 as refined by ADR-0077 D6–D12 is
already in
force, and three provider packs ship intake and narrow write-back against real
APIs. Under `de-risk-intent`'s own rule, no experiment is manufactured for a
cheap reversible bet.

## Riskiest assumption

*A team running a traditional SDLC — Jira-centric, ticket-as-unit, sprint
ceremonies, velocity and RAG reporting — can reach this operating model through
a **staged** change journey in which each stage pays for itself, without a
big-bang change to where scope is negotiated and how progress is reported.*

**What would have to be true.** A first stage exists that returns value without
requiring the PMO or reporting layer to change. Existing reporting and
governance obligations can still be met during the transition. The most
affected roles do not lose standing. Reversion pressure at first friction is
survivable.

**Kill condition, predeclared 2026-09-23 before the external retrievals
returned** — reproduced verbatim, and not edited to fit the result:

> KILLED if BOTH hold across the retrieved prior art: (i) NO staged adoption
> path is evidenced — every documented success of moving authoritative product
> meaning out of the incumbent tracker required the reporting/governance layer
> to change at the same time; AND (ii) the dominant documented failure mode for
> this class of migration is organisational authority/mandate, NOT tooling
> friction. SURVIVES if EITHER a staged path with per-stage value is evidenced,
> OR the documented failures are attributable to causes this capability's
> design can address.

**Result.** Condition (i) is **false**: staged adoption is the only documented
pattern — heavy-first then light-later, across Rust, Stedi, Peloton and Klarna,
plus a formal five-level adoption model that explicitly sanctions stopping
partway. Condition (ii) is **true**: organisational friction is the top-ranked
adoption blocker at 47%, and the measured failure is pilot-then-abandon — half
of 921 repositories that adopted decision records hold only one to five.

The kill required both. **Survived.**

**Three qualifications travel with the verdict, and none is cosmetic.**

1. **The staged evidence is an analogy.** It comes from decision records and
   RFCs — *decisions* in the repository — not from product scope and
   decomposition. Two retrievals searched independently for a named
   organisation that moved product scope out of a tracker and neither found
   one. There is no published precedent for the move this capability makes.
2. **Survival does not extend to regulated adopters.** Where the ticket is the
   audited control artifact, staging is not the issue. See § Assumptions.
3. **The verdict says the journey *can* be staged. It does not say anyone
   completed it.** Desk-grounding is not validation.

```
validation_hook:
  assumption: a traditional-SDLC team can reach this operating model through a
    staged change journey in which each stage pays for itself
  kill_condition: as predeclared above, 2026-09-23
  status: to-validate — survived on desk evidence only
  activity: with the first adopting team, agree the stage boundaries in
    advance and check at each one whether that stage returned value without
    requiring the reporting or governance layer to change. The failure to
    watch for is pilot-then-abandon, not rejection
  analogy_risk: every staged-adoption source concerns decisions in the
    repository, not product scope. The transfer is an inference this
    capability makes deliberately and has not tested
  out_of_scope: regulated adopters where the ticket is the audited control
    artifact. Not a stage to sequence through
```

## Decomposition

**Four feature children**, cut by the job each makes possible rather than by
pack, layer or provider. Each carries a `Parent intent:` back-link here and
re-enters the loop at `frame-intent`. All four are Accepted, de-risked
and decomposed — the first three into delivery briefs, the fourth into a
single delivery contract.

- [Intent-backed working view](FEAT-0011-intent-backed-working-view.md) — a team
  makes the meaningful parts of its canonical intent hierarchy visible and
  actionable in its chosen delivery system, at a granularity worth managing,
  without moving product authority there.
- [Delivery-state and flow visibility](FEAT-0012-delivery-state-and-flow-visibility.md)
  — a team observes real delivery state, blockers, elapsed time and flow across
  its intent-backed work, with the same meaning whether the system is Jira,
  GitHub or Linear.
- [Timeline and strategic-progress review](FEAT-0013-timeline-and-strategic-progress-review.md)
  — a team and its leadership review delivery forecast, known scope and risk,
  and actual outcome evidence together, with fixed dates distinguishable from
  forecasts and completion never standing in for outcome.
- [Tracker-native value before adoption](FEAT-0014-tracker-native-value-before-adoption.md)
  — a team that has adopted nothing installs the pack for its own delivery
  system and gets a flow view with outcomes attached, answered from the tracker
  it already runs. Added 2026-09-24 under
  [ADR-0126](../../adr/0126-integration-packs-standalone-value-and-bridge-skills.md),
  which obliges an integration pack to return value with none of this
  repository's machinery installed. The other three children each assume the
  intent tree exists, so none of them discharges that obligation.

### Decompose ran before de-risk

`decompose-intent`'s first entry condition is that the riskiest assumption has
survived. The children were created on 2026-09-23 while this intent carried
`De-risked: no`; the de-risk ran afterwards the same day and survived. The
order was wrong and the outcome was lucky — a killed bet would have left three
children hanging off it. Nothing needs undoing; the sequencing is recorded so a
later reader does not infer the gate was met when it was not.

### Decomposition decisions

- **2026-09-23 — the cut is by job, not by provider.** Jira, GitHub and Linear
  are **provider variants inside each child**, not children of their own. A
  per-provider cut was considered and rejected: the three would be the same
  product bet tested three times, so a green result on one would stand in for
  the others, and `decompose-intent` refuses a cut by component when the bet is
  shared. That the code will have provider-specific adapters is an
  implementation fact and is not a reason to cut here. The cut does not forbid
  shipping one provider first — sequencing inside a child is that child's to
  decide, and the shippability test each child must pass is that its outcome is
  real for at least one provider end to end.
- **2026-09-23 — the cut is not by pack or by technical layer.** A
  `product-engineering` / `core` / `atlassian` cut, and a `schema` / `events` /
  `adapter` / `reporting` cut, were both considered and rejected. Neither
  produces a child that is independently meaningful to a team, and both decide
  mechanism this altitude deliberately leaves open.
- **2026-09-23 — flow and forecast are two children, not one.** Merging them was
  considered: both are read-side, both consume the same observations. They are
  separate because they fail differently and serve different readers. Flow
  visibility fails if a team cannot see where work actually stands; the review
  fails if leadership reads completion as outcome. One child would let a working
  board stand in for an honest strategic answer, which is the exact conflation
  this capability's guardrail forbids.
- **2026-09-23 — the working view is a child rather than this capability's whole
  scope.** That was this intent's original framing. It was demoted to a child
  because it answers only the outward half: a team with a perfect working view
  and no flow or forecast surface still reports progress by counting tickets.
- **2026-09-23 — the tracker-first path is mostly already served, and the real
  gap is the return leg.** Raised by the lifecycle owner, and corrected the same
  day after checking what ships.

  **Inbound is covered, symmetrically.** Existing prose from a delivery item
  already becomes a repository artifact: `jira-brief-intake`,
  `jira-align-brief-intake`, `github-brief-intake` and `linear-brief-intake`
  read bounded tracker content into one `normalized-intake.v1` record, and
  `work-intake` routes it on content — not on tracker object type, hierarchy,
  label, sprint or board — to a spec, a Draft brief, linked cross-repository
  briefs, separate units, or a defect. The
  [pm-intakes-from-tracker journey](../journeys/pm-intakes-from-tracker.md)
  documents that end to end. `frame-intent` likewise authors an intent from
  whatever prose it is given, and `intake-intent` admits it. So an organisation
  that works tracker-first can already get its work shaped into canonical
  repository artifacts today.

  **What is missing is the return leg, and its provider symmetry.** Only Jira
  has an outbound content path: `jira-story-triage` reviews items against a
  five-question agent-execution readiness bar, names which question failed and
  the specific gap, drafts an improved summary, description and acceptance
  criteria, and writes through `jira: update-issue` only after per-item
  confirmation showing exact fields, old values and the protected set (status,
  assignee, sprint, priority, labels) it will not touch. GitHub and Linear have
  no equivalent. And that bar is *readiness for agent execution*, not intent
  shaping — it does not return outcome, opportunity or assumptions to the item.

  **This is therefore not a fourth child.** It is scope inside
  [FEAT-0010](FEAT-0011-intent-backed-working-view.md), which already owns what
  crosses the seam outward: returning shaped intent to the item so a team whose
  only touchpoint is the tracker sees it there, while authority stays in the
  repository. The adoption evidence (survey F2, F7) makes that the strongest
  candidate for the first stage that pays for itself.

  **One thing stays out on a mechanism argument.** A de-risk record does not go
  into a tracker field. Predeclaration is the load-bearing guard of
  `de-risk-intent`, and a mutable description cannot evidence that a kill
  condition was written *before* the result; ADR-0077 D11 already makes
  conflict decisions append-only for the same reason. Run the de-risk from a
  tracker-side conversation if that suits the team, and keep its record in the
  repository with at most a pointer projected out.

  Note the two outbound paths differ: refresh write-back is narrow (comment,
  trace-link, display-status, closure) while story-triage writes content
  through a separately gated route. A return leg would extend the second.
- **2026-09-23 — the order below is dependency, not priority.** The working view
  first, because the other two read work it makes intent-backed. Flow second,
  because the review reads its observations. No ranking rubric was applied;
  dependencies already order the three, which is `decompose-intent`'s own reason
  to skip the optional ranking step.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d7aa82b8d`
- **Authority:** eugenelim, lifecycle owner

Framed in this repository's shaping loop on 2026-09-18 under
[ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md),
and widened to delivery-system coexistence on 2026-09-23 in the same loop.
