# Intent: a captured work item reaches the owner that handles work of its shape

- **Slug:** `work-item-promotion-routing` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** `feature`
- **Owner:** eugenelim
- **Kind:** `opportunity`
- **Scale:** `app`
- **Maturity:** `brownfield`
- **Parent intent:** work-item-capture-and-disposition — [Work-item capture and disposition](CAP-0005-work-item-capture-and-disposition.md)
- **Depends on:** docs/product/intents/FEAT-0006-work-item-capture-contract.md <!-- stated for a reader; the enforceable edge is a typed `needs` entry on the workspace registration, which does not exist yet -->

## Outcome

A captured work item stops sitting in the store: it either reaches the owner
that already handles work of its shape, or is closed because it should not go
anywhere — and either way the observation that produced it records that it has
left.

**How we will know.** One outcome, with a guardrail — not two outcomes.

- **The result.** The share of captured items still untriaged after a drain.
- **The guardrail.** The share of *dispositioned* items an informed reader
  agrees went where they should — routed to the right owner, or closed for a
  reason that holds. Without it the result is satisfiable by routing everything
  somewhere or closing everything, and with it alone nothing has to move at all.

## Opportunity

Capture without a handoff is an inflow with no exit. The sibling feature accepts
that as an interim; this one closes it.

The destinations already exist. `work-intake` classifies six input shapes today:

| Input shape | Artifact | Membership | Processor |
| --- | --- | --- | --- |
| Explicit bounded direct-light start | none | none | `work-loop` |
| Bounded work needing durability or elevated assurance | spec | current durable path | `new-spec` |
| Coherent multi-slice or cross-repository outcome | brief | current brief path | `author-delivery-brief create` or `continue` |
| Remember for later | intent or capture path | non-dispatchable | none |
| Cited regression or defect evidence | defect | ready only after canonical context exists | `bug-fix` |
| Incomplete or ambiguous input | named-gap behavior | non-dispatchable | none |

Two properties of that table are easy to get wrong and are load-bearing here.
The defect route **materialises an artifact and registers a workspace entry** —
it is not a bare handoff to a processor. The remember route does the same, as a
Draft registered non-dispatchable. Several routes perform no transaction or
registration — direct-light among them, alongside the non-mutating status and
refresh paths and a named gap that can return without writing. What matters
here is the converse: the routes a promotion would use do write. Promotion therefore always writes something. An
earlier draft of this intent asserted the opposite and built a rationale on it.

The defect route's readiness condition — canonical context must exist first — is
the seam between this feature and its dependency, and whether the captured
record satisfies it is not yet established either way.

An item can terminate as `promoted`, `duplicate`, `routed`, `rejected` or
`superseded`. The store refuses a second terminal event for a capture that
already has one.

Not every item should be routed. An item can be overtaken by work that shipped,
superseded by a later item, or made false by a change to the thing it described
— and forcing such an item to a destination is worse than closing it, because it
creates work from a premise that no longer holds. Closing without routing is
therefore part of this outcome rather than a missing case.

The store's terminal vocabulary already carries values for some of that. It has
no value meaning *discarded as no longer worth doing*, which the sink model
depends on, so either one is added or an existing value is designated to mean
it. That mapping is this feature's to settle.

What is missing is the step that hands a triaged item to a classifier at all,
and commits the terminal disposition once it has gone — by either route.

## What exists today

**Snapshot taken 2026-09-19.** These are locations, not contents. Each names a
file and why this intent cares about it, and deliberately reproduces no value,
status, field content or count from it — a copy would be a second home for
another artifact's state, and the date would record only when the copy was made,
not whether it still holds. Open them.

- **The classifier.** `packs/core/.apm/skills/work-intake/SKILL.md`. Its
  classify table is the authority on which input shapes exist and what each
  produces. This intent quotes it above as illustration; the table is the source.
- **The routing code.** `intake_router.py` in that skill's `scripts/`. Several
  branches decide artifact and membership, not one map — read the whole function
  rather than any single table.
- **The defect processor.** `packs/core/.apm/skills/bug-fix/SKILL.md`.
- **Disposition rules.**
  `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`. Read it
  for the terminal vocabulary and for what happens on a second terminal event.
- **How a route would be sized.** The delimited risk-triggers block in
  `packs/core/.apm/skills/work-loop/SKILL.md`, which declares itself the
  canonical and only home; cite it, never copy it.
- **When a dependency counts as satisfied.** The workspace status engine under
  `packs/core/.apm/skills/workspace-status/scripts/`.
## Upstream state, 2026-09-21

`docs/specs/work-item-capture/spec.md` ships, so the record this child
routes now exists and its shape is fixed. Four consequences for this child:

**What it will receive.** A `work-item` record carrying a closed `shape`
and `blocker`, a per-shape required-field set, and an optional
`verification_route` whose `command` is a bounded argv array — four tools,
no options, a positive character class, a repository-path rule.

**Six residual controls are handed to this child by name**, and its
criteria carry them: post-resolution repository confinement, environment
neutralisation, a resource cap, a re-check of the stored command against
§ D6's argv rules before it runs, which matcher `grep` uses, and the
treatment of the command's output.

**One residual is not handed over and has no owner.** The argv rules
confine every stored path to the repository; they do not decide whether an
in-repository file is sensitive, so `credentials.json`, `keys/id_rsa`,
`config/prod.env` and `.env` are all admissible. This is **not** covered by
this child's post-resolution confinement obligation, which refuses a path
resolving *outside* the repository — an in-repository file never does. That
routing was asserted and withdrawn twice upstream. If this child is to own
it, it needs a criterion of its own, not the existing one.

**Volume is lower than this child assumes.** See the parent's measurement.

## Non-goals

- **Governance items.** Where a decision is the deliverable, the destination is
  a sibling's to settle. Until it does, such items stay in the store.
- **Telling whether an existing artifact already covers the item.** A sibling's.
- **Whether a separate findings register should exist.** Its seed and schema are
  recorded as completed in the governing RFC; that RFC's open item asks only
  whether the register should move into the shaping queue. Not this intent's,
  and not as broad as an earlier draft claimed.

## Assumptions

- Size and blocked-state are independent. An item may be blocked and trivial, or
  ready and large. The record carries what blocks it.
- Promotion writes. Every route but one materialises or registers something, so
  this is a transaction, not a message.

## Decomposition

None — one outcome, measured with a guardrail. An item leaving the well is one
outcome whether it leaves by routing or by closure; the two share a
disposition, a guardrail and a failure mode, and splitting them would let a
green result on routing hide an item that should have been closed and was not.

Two failures remain distinct from a valid closure, and neither is what this
outcome permits: an item handed to an owner while its capture stays open has
not left the well, and a capture closed while the work was still wanted has
lost it. A closure whose stated ground holds is neither — it is the outcome.

An earlier draft claimed the handoff and the capture's closure were indivisible.
They are not, and this intent's own atomicity discussion says so: they are
separate effects, and each can occur without the other. What makes them one
outcome is that either alone is a defect rather than a partial delivery — an
item handed off without its capture closing has not left the store, and a
capture closed without a handoff has lost the work. Sequencing them is the
spec's; delivering only one of them is not a smaller version of this.

## De-risk

**Reversibility: mixed.** Route rules are cheap to change. What routing has
already emitted is not — a defect artifact and a workspace entry, a spec, a
Draft intent — and un-routing does not un-write them. The terminal disposition
is the harder half: the store refuses a second terminal event against a capture,
so a mis-routed item cannot be re-dispositioned, only annotated by a later
observation.

**Riskiest assumption, and it is this intent's own rather than inherited.** *A
drain can infer the correct destination from a record written earlier by a
session that no longer exists.*

The destination depends on facts about the work as it stands when it starts —
its risk, durability need and scope. The drain has only the record. This is
adjacent to the dependency's bet and is not the same one: a working reproduction
command establishes that a defect can be seen again, and says nothing about
whether the work needs a durable contract. An earlier draft called it inherited,
which would have let a green result there stand in for a test here.

**Kill condition, with its basis.** Of the first ten items a drain routes, three
or more go to a shape an informed reader would not have chosen. The basis for
three is that the routing table has six shapes and a wrong route is recoverable
but costly — it creates an artifact in the wrong place and closes the capture
that would have prompted a correction. At one in three the drain is worse than
leaving items for a human, which is today's behaviour and the thing it must
beat.

**A second half, because the first is gameable.** A drain that holds every hard
item and routes only the obvious ones scores perfectly on route correctness
while delivering nothing. So the same ten are drawn from what the drain was
*offered*, not from what it routed, and an item it held that the reader judges
routable counts against it exactly as a wrong route does.

**The adjudicator is the repository owner**, named so the test can run twice and
mean the same thing. That names the judgement without making it reproducible
across readers: one adjudicator gives no inter-rater agreement, so a second
run by a different person is a different test. A spec that wants a durable
measure needs either a written rubric or a second reader, and this intent
supplies neither.

**A drain's held-to-routed ratio is not a hook.** It turns on which kinds happen
to have been captured that week, so it measures the period, not the design.

```
validation_hook:
  assumption: a drain can infer the correct destination from a record written
    by a session that no longer exists
  kill_condition: of 10 items the drain was offered, 3 or more are either
    routed to a shape an informed reader would not have chosen, or held when
    that reader judges them routable
  activity: after one drain, have a named adjudicator read the original work
    behind ten offered items and judge the drain's disposition of each
  adjudicator: the repository owner
  known_gap: a single adjudicator, so the measure is not reproducible across
    readers; a rubric or a second reader is what would make it so
```

## For the spec to decide

- **When routing happens, and what invokes it.** Whether the classifier is
  extended or called, and at what point in a drain, is a delivery decision.
- **Atomicity across the writes.** Artifact creation, registration, handoff and
  the terminal disposition are separate effects with one irreversible member. A
  crash between them either creates work without closing the capture or closes
  it without the handoff.
- **The trust boundary on captured content.** Prose, paths and commands written
  by an earlier session become inputs to a classifier here.
- **Which captured fields determine each destination**, and what happens when
  they are absent, stale, or contradict each other.
- **What justifies closing an item rather than routing it**, and who may do
  it. Overtaken, superseded and falsified are three different grounds with
  three different tests, and an unjustified closure is indistinguishable from
  losing the work this feature exists to keep.
- **The disposition for a discarded item** — whether the terminal vocabulary
  gains a value, or one or more existing values are designated to mean it.
  Without that mapping the sink's prune half is unrecordable, and the parent
  capability's kill condition cannot be read. The parent states the obligation
  and leaves the option set here, so this is its only home.
- **The adjudicator and rubric** the routing measure depends on.
- **Attended versus unattended operation** — who may confirm a route, and what
  must remain held when nobody can.
