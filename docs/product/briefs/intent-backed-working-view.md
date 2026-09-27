# Brief: a team works its canonical intent from inside its own tracker

- **Slug:** `intent-backed-working-view`
- **Received:** 2026-09-23
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Ready
- **Ready confirmed:** 2026-09-24 by eugenelim, lifecycle owner, **on owner authority over an open review**. Bound to revision `8787933d9d4a6bf2`, which returned `Findings` — five independent review rounds, the last returning 11 findings, eleven of them recorded and unresolved at this transition. `author-delivery-brief` requires a revision-bound `Clean`; the owner took the gate instead, and this line is the record of that. Slice membership and status are the Spec map's; this line does not restate them.
- **Parent intent:** intent:intent-backed-working-view

**How the specs from this brief cite.** A spec names a governing artifact by
its record and clause, and states the one thing the spec must do because of it.
It does not restate what that artifact says. A paraphrase sealed inside a
frozen contract drifts from its source and is then read as authority in its own
right. A spec cites the artifact and clause directly. § Governance references below
collects what each one obliges *this brief*, for a reader of this brief; it is
not a substitute source for a spec to cite. This brief is not bound by that constraint: it states
what a source says wherever a reader needs it to follow the argument.

## Outcome

A team runs its day from its own delivery system, over work whose meaning lives
in the repository, with no second model of that work maintained by hand.

The steerable input is how much a person must create or update by hand to keep
the board true. The measured failure for this class of practice is
pilot-then-abandon, and the predictor is whether keeping the artifact current is
a byproduct of work someone already had to do or a separate act of maintenance.
Every slice below is judged against that.

The delivery systems in play are **Jira Software**, **Jira Align**, **GitHub
Issues + Projects** and **Linear**. The `none` rendering — the tree stays in
`docs/product/` and a person projects by hand — stays first-class alongside
them.

## Success metrics

- **Nobody maintains a parallel hierarchy.** The falsifiable signal the parent
  intent accepts as proof: no second hand-built tree exists, and nobody has to
  talk a newcomer through why the board is not quite right.
- **A projected item names its canonical origin, readably from both ends.** A
  reader on the tracker side can reach the intent; a reader in the repository
  can tell what was projected.
- **Nothing agent-internal is managed or counted, and no same-repository
  delivery brief appears at all.** ADR-0127 D4 and D4a set the line. The
  obligation here is that each slice's output is checked against them before it
  ships, and that the check is named in its spec.
- **Projecting must not double the board.** FEAT-0011's guardrail states the
  comparison this brief can hold and fail: a faithful projection that doubles
  the board is a failure even if every item on it is correct. It is measurable
  at the first projection against the team's existing board, with no new
  measurement origin. An absolute per-person bound is a different claim, is not
  fixed by any measurement in the record, and is owned by the Jira Software
  slice as the first that emits items.

## Scope / Non-goals

**In scope.** Returning shaped intent onto items a team already holds;
projecting the canonical tree outward across ADR-0127's range as items carrying
a back-reference; and the per-system hierarchy profiles that let either happen
without the product model absorbing a provider's shape.

**Out of scope, and each names where it is owned.**

- **What projects, and how far.** ADR-0127. This brief implements it and does
  not re-open it.
- **Delivery-state and flow observation.**
  [`FEAT-0012`](../intents/FEAT-0012-delivery-state-and-flow-visibility.md).
- **Forecast and outcome review.**
  [`FEAT-0013`](../intents/FEAT-0013-timeline-and-strategic-progress-review.md).
- **Intent identity and placement.**
  [`FEAT-0001`](../intents/FEAT-0001-intent-identity-and-registration.md).
- **Any new daemon, control plane, database or scheduler.** Owned by
  [`CAP-0004`](../intents/CAP-0004-external-tracker-projection.md)'s guardrail.
  A projection runs when invoked.
- **Reading requirement changes back off the tracker.** Owned by ADR-0077 D6.
  Survey F5 corroborates it: bidirectional sync fails by named mechanisms —
  races on overwrite where arrival order decides the value, echo loops,
  cross-field constraint breakage, mapping drift mid-flight and duplicate side
  effects — and Canonical's GitHub-to-Jira sync was archived in 2025 and
  replaced with another one-way bot rather than upgraded. The corroboration is
  bounded to *naive* bidirectional sync: Unito and Exalate are years-viable
  commercial products over narrow field sets, so the claim is that the naive
  shape fails, not that every bidirectional shape does.
- **Which existing write route a return leg extends.** A spec decision. This
  brief fixes only the human-control boundary below.

## Current-state evidence

Measured or read on 2026-09-23. Locations and findings, not restated status.

- **Nothing renders outward today.** Every shipped intake skill pulls work *in*
  or writes narrow coordination *back*, and intents across the corpus carry an
  identical `## Projection` line recording the outbound surface as unshaped.
- **The shipped profile table covers some delivery systems and not others.**
  `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
  maps `none`, Linear and Jira Align. Jira Software and GitHub Issues + Projects
  have no columns.
- **Applying ADR-0127 D1 through D4a to every row of that table finds conflicts
  at and below the floor, and none above it.** Reported row by row.
  - Its `spec / slice (leaf)` row maps the leaf onto a Linear **Issue** and a
    Jira Align **Story**. Both are scheduled, assigned and counted on their
    providers.
  - Its `story-as-trace (optional)` row maps onto a Linear **sub-issue** and a
    Jira Align **Story / sub-task**. These are also schedulable and countable,
    and the row states no condition of the kind D4 requires below the floor.
    **ADR-0127 D4 cites this row approvingly**, resting on the § *What v1 ships*
    sentence rather than on the cells. The slice acts on the cells: they name
    managed objects, so the row needs the not-managed condition stated or its
    cells changed.
  - Every rung at or above the feature intent clears, on D1 and D3 — the two
    clauses that reach above the floor. D1 asks each rung to be represented
    with its rollup intact rather than to be a managed item, and D3 decides the
    carrier, so the `extra intervening intents` row flattening onto labels and
    sub-issues is what that pair prescribes rather than a conflict. The two
    product rungs clear on the same reading, where Linear carries them on an
    Initiative or a label.
  - Separately, the table's canonical column carries no rung for a delivery
    brief, so the cross-repository floor has no rendering.
  - The table's § *What v1 ships* asserts that "the spec/slice is the unit".
    That sentence, not either table row, is the direct claim ADR-0127
    displaces.
- **One gated outbound content path exists, and only on Jira Software.**
  `jira-story-triage` reviews items against a five-question readiness bar,
  drafts an improved summary, description and acceptance criteria, and writes
  through `jira: update-issue` **only after per-item confirmation** showing
  exact fields, old values, and the protected set — status, assignee, sprint,
  priority, labels — it will not touch. Jira Align, GitHub and Linear have no
  equivalent.
- **A narrower write-back path also exists.** `jira-refresh` and
  `github-refresh` support comment, trace-link, display-status and closure.
- **GitHub's sub-issue limits and Jira Software's hierarchy are both now
  established against each vendor's own documentation.** Survey F6. GitHub
  sub-issues carry a maximum depth of 8 levels, a maximum of 100 sub-issues per
  level, and a single parent only — maintainers rejected multi-parent requests
  outright. Jira provides three levels, Epic at level 1, Story at level 0 and
  Subtask at level -1, with both extra work types at the Epic level and any
  additional level gated behind Jira Cloud Premium or Enterprise, new levels
  added at the top rather than the bottom, and no stated maximum. Neither
  slice's hierarchy inputs are an open prerequisite any more.
- **Atlassian's current vocabulary is "work type", not "issue type".** Survey
  F6. The consequence is that the profile table's Jira rows must use current
  vendor terminology rather than the term the table was written with.
- **One hierarchy claim is still unverified** — the Jira Epic to Jira Align
  Feature rename. Survey F6; it rests on a search snippet, and the Jira Align
  slice inherits it as an open input.
- **No artifact in the corpus carries a non-`repo-origin` source mode.** The
  inbound authority machinery has never run against a real artifact, so
  ADR-0077's refresh behaviour is unexercised in practice.

## Constraints / Appetite

- **Non-waivable: every remote mutation keeps the human-control boundary
  `jira-story-triage` already sets.** Exact payload shown, per-item
  confirmation, protected fields named. This is an obligation on work not yet
  built: only Jira Software has a gated content-write path today. A projection
  that writes without the boundary is out of contract regardless of convenience.
- **Non-waivable: `core` gains no provider-specific coupling**, and the
  product-engineering intent model gains no provider-specific hierarchy. A
  provider's shape is absorbed at the edge.
- **Non-waivable: ADR-0127 D3 and D5 hold on every delivery system.** The
  obligation is that a slice refuses to ship a rendering that violates either,
  rather than shipping it with the deviation noted.
- **Non-waivable: one-way, for repo-origin work.** ADR-0019 D5 as ADR-0077
  D6–D12 refine it.
  The obligation here: this brief's projections write outward only, and nothing
  written here binds a later tracker-origin adopter, whose lifecycle is
  ADR-0077's. The decision itself is not reopened.
- **Projection must be a byproduct, not a separate act of documentation.**
  Survey F3 names the failure this designs against: across 921 GitHub
  repositories that had adopted architecture decision records, roughly half
  contain only one to five records in total — the practice adopted, then
  abandoned. Its downgrade is that open-source repositories are not enterprise
  delivery teams and a record count proxies practice health rather than
  measuring it. A slice whose upkeep is somebody's second job has already
  failed.
- **Appetite, held as an assumption: adoption has to be stageable.** Survey F7
  measures the blocker as organisational: the CNCF 2025 survey ranks cultural
  change with the development team top at 47%, ahead of security and training at
  36% and technical complexity at 34%, and DORA 2024 finds user-centric
  platforms outperform mandated ones, which closes the top-down remedy. F2
  supplies the staging remedy — every retrieved case started with one
  heavyweight format for high-stakes decisions and added a lighter one later,
  and no case ran big-bang — downgraded because those cases come largely from a
  single secondary compilation and all concern decisions rather than product
  scope. F1 found no published precedent for this migration across two
  independent retrievals, and F17 marks agreeing-retrieval absences provisional
  after two were refuted by a differently-routed worker. The obligation is
  therefore weakly grounded and stated as an assumption: one slice must pay for
  itself without the reporting layer
  moving, and in the cut below that is the Jira Software slice's return leg.

## Assumptions / Risks

- **[Inherited, survived on desk evidence]** A traditional-SDLC team can reach
  this operating model through a staged journey. CAP-0004's de-risk;
  `to-validate`, no adopter has run it.
- **[Inherited, `to-validate`]** FEAT-0011's de-risk killed the spec tier and
  reframed the projected unit upward, and ADR-0127 D2 fixes the floor there. The
  reframe carries a `to-validate` hook that no adopter has discharged. Every
  slice below inherits it, and a spec must not read as though the tier were
  settled.
- **[Open risk, owned by the first slice]** Whether each delivery system's
  hierarchy can carry the range at all. ADR-0127 keeps this as a standing
  revisit trigger, and D3's collapse rule answers it only where a native carrier
  exists. Adding a canonical rung does not create a provider rung, so this is
  not answerable from the intent model and is discovered per system.
- **[Risk]** No mechanical guard exists for the floor until a projection ships.
  The first slice that emits items is the first chance to make the check
  mechanical, and nothing forces it to take that chance.
- **[Risk]** The return leg improves items a team already has, which makes it
  cheap to adopt and also cheap to *stop*. Its value has to be visible in the
  item itself, not in a report about the item.
- **[Risk]** A provider's write surface can change under us. The human-control
  boundary bounds the blast radius to a refused write rather than a corrupted
  item, but only on paths that implement it.

## Direction, and why the repository is canonical

The return leg writes product meaning onto a tracker item so a team need never
open the repository. That is the configuration survey F4 names: an in-repo
artifact and a tracker item describing the same work, diverging silently while
humans and agents edit each. CAP-0004's guardrail protects one direction only —
the tracker must not rewrite canonical intent — and F4's drift runs the other
way, needing no tracker write at all. This brief takes a position rather than
recording a risk.

**The recommendation: one way, outward, and the repository is canonical.** The
projected content on a tracker item is a render. It is marked as projected, it
is overwritten on the next projection, and an edit made to it is an edit to a
render — not a proposal against the source.

**Why the repository and not the tracker, given what this catalogue actually
ships.** The argument is not that a repository is a better database. It is that
every machine that acts on product meaning here reads repository artifacts, and
none of them can read a tracker field.

- **The build loop executes from the repository.** `new-spec` and `work-loop`
  take a spec and a plan from disk. Meaning that lives only in a tracker
  description is meaning no agent can build from, so a tracker-canonical model
  breaks execution rather than merely relocating authorship.
- **The shaping loop produces things a description field cannot hold.** A
  predeclared kill condition is only evidence if it demonstrably predates its
  result; an append-only conflict decision is only a control if nothing can
  rewrite it; a review binds to a revision. A mutable field carries none of
  these, and this brief's own parent is the worked example — its verdict rests
  on a line timestamped before the evidence returned.
- **Authority transfer is already specified for this direction.** ADR-0077
  D6–D12 govern imported-field authority and lifecycle-gated refresh; the
  inverse has no specification and would need one.
- **Provenance survives.** A repository artifact carries its source, its
  revision and its supersession; a tracker item carries its last editor.

**What this costs, and why the cost is temporary rather than principled.** A
team whose only touchpoint is the tracker cannot change product meaning from
there. Today that restriction bites harder than the authority model requires,
for a reason worth separating out: **the tracker is simply the more usable
surface right now**, because it has an interface and the canonical tree does
not. Authorship in the repository currently means a text editor and a skill,
which is a fine fit for a maintainer and a poor one for a product owner between
meetings.

That is an interface gap, not an authority argument, and conflating the two
would bake a temporary limitation into a durable decision. An interface over the
canonical tree closes it without moving authority anywhere, and none of the
reasoning above changes when one exists.

Two things bound the cost meanwhile. The return leg exists precisely so a
tracker-only reader sees current meaning without leaving the tracker — usability
where the user is, authority where the machinery is. And a projected section
edited locally is detectable by comparison against its source, because every
projected item carries a back-reference.

**What is left to the slice.** Whether an edited projection is reported, warned
on, or silently overwritten on the next run, and whether detection is offered at
all in the first release. F4's maintainer counter-position applies to that
choice: the failure is unlabelled redirection rather than divergence as such, so
whatever the slice does, a projected region must be recognisable as one.

## Spec map

Slices confirmed 2026-09-24 by the lifecycle owner. The Status column is
derived from each spec and is not hand-edited; it is the only home for a
slice's state.

| Spec | Status |
| --- | --- |
| `tracker-projection-profile-table` | <auto> |
| `bounded-remote-create-action` | <auto> |
| `tracker-working-view-jira-software` | <auto> |
| `tracker-working-view-jira-align` | <auto> |
| `tracker-working-view-github` | <auto> |
| `tracker-working-view-linear` | <auto> |
## The cut, and why it goes this way

**Two shared slices, then one spec per delivery system with Jira Software
first.** The cut was confirmed on 2026-09-24 and revised the same day when
spec authoring separated the shared work. The Spec map above owns membership
and status.

- `tracker-projection-profile-table` — the shared table, and the only slice
  that touches `product-engineering`
- `bounded-remote-create-action` — the shared write contract, and the only
  slice that touches `core`
- `tracker-working-view-jira-software` — **the pattern**
- `tracker-working-view-jira-align` — conforms
- `tracker-working-view-github` — conforms
- `tracker-working-view-linear` — conforms

**The shape, and why these are not independent bets.** Each slice makes the
outcome real on one delivery system, end to end: the profile rows for
ADR-0127's range, the outward projection carrying a back-reference, and the
return leg onto items that team already holds. The Jira Software slice ships
first and sets the pattern — the normalized shape a profile carries, where a
rung collapses when a provider is shallow, how a below-floor object is rendered
without being managed, and the confirmed-write boundary. The other three
conform to that pattern rather than re-deciding it. A green result on one is
therefore evidence about the pattern rather than a stand-in for the others.

**On the set this cuts across.** ADR-0127's *Applies to* fixes the delivery
systems at Jira Software, Jira Align, GitHub Issues + Projects and Linear.
FEAT-0011 § Boundary enumerates none and defers to that set; its completion
condition — the outcome real on at least one delivery system before shipping —
is met by the Jira Software slice alone.

**Why Jira Software is the initial target.** It is the only delivery system with
a gated outbound content path already shipping, so the return leg has a working
precedent there and nowhere else. Its hierarchy depth is also the least
established, so the pattern is set against the hardest case rather than the
easiest.

**The `none` rendering.** It is not a delivery system and gets no slice. Its
profile row is part of the shared table work the Jira Software slice carries,
and FEAT-0011 treats a mapping-only rendering as a deliverable outcome rather
than documentation, so nothing about it is excluded — only unsliced.

**What each slice owns.** Its own delivery system's rows in the shared profile
table, its own projection, its own return leg, and its own completion condition
— that system works end to end. FEAT-0011 requires the outcome to be real for at
least one delivery system before this feature ships, and the Jira Software slice
alone satisfies that.

**Shared work is its own two slices**, revised 2026-09-24 after spec authoring
showed what it touches. The profile table is `product-engineering` work and
the bounded create action is `core` work; neither is Jira work, and bundling
them into the Jira slice meant approving a change to a contract four providers
route writes through under the heading of one delivery system. Each is
independently shippable and independently testable — the create action is
inert until a provider declares the capability — and all four provider slices
already depend on them as separate units. Both are accepted against ADR-0127
and the shared write contract rather than against a provider's documentation,
while the Jira Software slice is accepted against the Atlassian hierarchy
constraints recorded in § Current-state evidence above.

**What this cut does not settle.** Whether one delivery system's projection and
return leg are one shippable slice or two is a spec-stage question. This brief
records the pairing as the owner's cut and does not test it.

## Governance references

This section collects what each governing artifact obliges here, in one place,
so a spec can cite into it rather than restate the source.

- **[ADR-0127](../../adr/0127-managed-unit-floor-and-projected-range.md) — what
  projects, and how far.** The canonical tree projects as a **range** (D1), from
  its top rung down to a floor that sits at the **delivery brief** where work
  crosses a repository boundary and at the **feature intent** otherwise (D2).
  Rungs above the floor **collapse** onto whatever depth the provider carries
  and are never truncated (D3). Below the floor nothing is **managed or
  counted**, though a spec, plan, wave or task may hang off an item as a
  readable **trace** (D4). A **same-repository delivery brief does not project
  at all** (D4a). The floor is fixed rather than negotiated per team (D5). It
  applies to Jira, Jira Align, GitHub Issues + Projects and Linear, and to
  anything that counts projected items. Its reach is wider than this brief:
  FEAT-0012's flow readings and FEAT-0013's forecast both count whatever the
  range admits.
- **[ADR-0077](../../adr/0077-feature-projection-and-tracker-authority.md)** —
  D1 gates feature projection on shippability and coordination need, and is
  **superseded in part by ADR-0098**; § Source records what that refines and
  why the multi-change-in-one-repository row still holds. D2 grants
  the cross-repository brief a distinct coordination identity, which is what
  ADR-0127 D2 rests on. D4 and D5 require every repository brief to name the
  same durable parent and forbid reading another repository live to resolve it.
  D6–D12 govern imported-field authority and lifecycle-gated refresh, including
  the tracker-origin modes that refine ADR-0019 D5.
- **[ADR-0019](../../adr/0019-product-intent-ontology-and-brief-projection.md) D5** —
  the original universal one-way tracker rule. Its own header records ADR-0077
  replacing universal one-way projection with lifecycle authority modes.
- **[ADR-0033](../../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md)
  D2** — `Level` is an open recognized set on the canonical intent, checked for
  presence and never for membership. Its Consequences also settle the
  tracker-projection rows for the two product rungs to a higher/intervening-tier
  default — Jira Align Theme/Strategy tier, Linear Initiative or label, `none`
  markdown — and defer the mechanical rows to the implementing spec. Those are
  rows the profile reconciliation must not silently re-decide.
- **[ADR-0098](../../adr/0098-artifact-admission-and-delivery-brief-lifecycle.md)
  and [ADR-0121](../../adr/0121-a-repository-intent-declares-its-altitude.md)** —
  ADR-0098 refines ADR-0077's feature-projection table — in its § Clause-level
  replacements, which carries no clause number — so sufficient direct
  artifact authority may bypass feature-intent creation; its D6 and D7 hold that
  a Ready brief may carry zero specs and that a brief's map separates governance
  references from delivery slices. ADR-0121 D1 makes `Level` required. Neither
  reaches the projection row this brief rests on.
- **[FEAT-0011](../intents/FEAT-0011-intent-backed-working-view.md)** — the
  parent. It owns the outcome, the guardrails this brief inherits, the de-risk
  verdict and its `to-validate` hook, and the boundary condition that the
  outcome be real on at least one delivery system before shipping.
- **[FEAT-0012](../intents/FEAT-0012-delivery-state-and-flow-visibility.md) and
  [FEAT-0013](../intents/FEAT-0013-timeline-and-strategic-progress-review.md)** —
  siblings. They own flow observation and forecast review respectively, and both
  count whatever ADR-0127's range admits, which is why the floor is not this
  brief's to move.
- **[CAP-0004](../intents/CAP-0004-external-tracker-projection.md)** — the
  capability. It owns the no-new-runtime guardrail and the authority constraints
  this brief does not restate.
- **Installed-skill references.** `decompose-intent`'s
  `references/tracker-projection.md` is the shipped profile table the
  reconciliation targets. `jira-story-triage` is the only shipped gated
  outbound content path and sets the confirmed-write boundary. `author-delivery-brief`
  owns this brief's lifecycle, its Ready gate and its slice-confirmation step.
  These carry no clause numbers, so a citation names the file and the one thing
  it decides for this brief.
- **[Tracker-coexistence adoption survey](../research/tracker-coexistence-adoption-survey.md)**
  — the findings this brief cites are named where they do work, and each carries
  its own confidence grade, downgrade reason and source list in that document;
  read the finding before relying on it. **F4** is the one with a consequence
  large enough to name here: it records spec drift as live and unsolved, and
  that CAP-0004's guardrail addresses only the inbound direction. § Direction
  takes this brief's position on the outbound one.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/FEAT-0011-intent-backed-working-view.md`
- **Authority:** eugenelim, lifecycle owner

Projected from that intent on 2026-09-23 under ADR-0077 D1: several
independently shippable changes in one repository become a brief with specs
beneath it.

**Disclosure on that citation.** ADR-0077 D1 is superseded in part: ADR-0098's
header lists `ADR-0077 D1` among what it supersedes in part, and ADR-0077's
header names `ADR-0098 D1` in return. What ADR-0098 refines is the
feature-projection table, so that sufficient direct artifact authority may
bypass feature-intent creation. That bypass concerns whether a feature intent is
created at all; it leaves untouched the row this brief relies on, which routes
several independently shippable changes in one repository to a brief with specs
beneath it. ADR-0098 in turn carries `Superseded in part: ADR-0121 D3`. Chased and bounded:
that header pointer names the record, and the superseding clause is **ADR-0121
D1**, which makes `Level` required and supersedes ADR-0098 D3's grouping of
`level` with optional enrichment. Neither reaches the projection gate. Recorded
so the next reader need not re-derive the chain.
