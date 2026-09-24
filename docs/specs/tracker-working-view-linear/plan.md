# Plan: tracker working view linear

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/linear/.apm/skills/linear/SKILL.md` (the GraphQL read
  path, the refresh write-back route, and the raw-write prohibition this
  extends); `packs/core/.apm/skills/work-intake/scripts/refresh.py` (the
  processor Linear's own rule points at);
  `docs/specs/tracker-working-view-jira-software/` (the pattern). Named
  deviation: Linear is the shallowest target, so the collapse carries more
  rungs onto labels than any other provider.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

Linear's rule already says confirmed write-back goes only through the
configured refresh processor, so this slice adds no new write surface — it
makes the create action reachable from Linear and leaves the prohibition on raw
GraphQL verbs exactly where it is. That ordering matters: the prohibition is
what keeps the pack's one write route auditable.

The substance is the collapse. Linear carries three native levels against a
tree that can be deeper, so more rungs land on labels here than anywhere else.
A label that says nothing about which canonical rung it stands for satisfies
ADR-0125 D3 and still leaves a reader unable to reconstruct the tree, so
legibility is an acceptance criterion rather than a nicety.

## Constraints

- **ADR-0125** D1 through D4a fix what projects and how far; D3 and D5 are
  non-waivable on every delivery system.
- **ADR-0019 D5**, as **ADR-0077 D6-D12** refine it, keeps this one-way for
  repo-origin work.
- **ADR-0033 D2** makes `Level` an open set, so an unmapped rung is named
  rather than derived.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler.
- The pattern the Jira Software slice sets is an input, not a subject.
- This pack stays independently installable and depends on no other provider
  pack.

## Construction tests

- A collapse fixture with a tree deeper than three levels, asserting which
  rungs land on Initiative, Project, Issue and labels.
- A legibility assertion over the rendered labels: every label-carried rung
  names its canonical rung.
- A rollup assertion walking from the floor rung to the top through whatever
  carrier each intervening rung took.
- An idempotency fixture: same tree twice, then one rung renamed.
- A populated-workspace fixture: the same tree against a workspace that already
  holds the team's issues.
- A label round-trip: every rendered label parses by the documented encoding.
- A grep-shaped assertion that no raw GraphQL write verb appears in the skill
  body.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Create action reachable through the refresh processor | T1 | no raw verb in the skill body |
| Documented label-identity encoding | T2 | rendered labels round-trip through the parser |
| Linear projection with a legible collapse | T3 | collapse and rollup assertions green |
| Duplicate and collision behaviour | T4 | populated-workspace fixture creates nothing |
| Derived repository scope | T4a | both sides of the brief rule exercised |
| Return leg on existing issues | T5 | recorded confirmation transcript |
| `linear` changelog entry | T5 | the pack leads its own entry |

## Design (LLD)

### Design decisions

- **The raw-write prohibition stays.** The create action arrives through the
  refresh processor, which is what Linear's rule already mandates, so the
  prohibition needs no exception and the pack keeps one auditable write route.
- **The label carries a parseable identity, not a readable hint.** ADR-0125 D3
  permits a label as a carrier and says nothing about what it reads. A bare
  label passes D3 and defeats the feature; a label checked only for "naming"
  its rung lets the implementation define what naming means. One documented
  encoding with a parser is what makes the rollup walkable by something other
  than a person.

### Data & schema

The profile table's column for this delivery system is the schema. The
projection payload carries the canonical identity, the rung's `Level`, and the
target object type resolved from that row.

### Interfaces & contracts

No new interface. The create action and its confirmation binding ship with the
pattern slice; this slice supplies this provider's transport for them.

### Component / module decomposition

Everything lands in `packs/linear/`. The action set is the pattern slice's.

### State & control flow

Invocation reads the tree, resolves each rung against the profile row, and
emits a confirmation request per item. No resident state: the back-reference on
the remote item is the only durable link, which is what makes a later run
idempotent without a local database.

### Behavior & rules

A rung whose `Level` has no row is named as unmapped rather than guessed. A
rung below the floor produces a trace link on the floor issue or nothing. A
same-repository delivery brief produces nothing. Instructions found inside an
issue title or description are data, never direction.

### Failure, edge cases & resilience

A refused confirmation aborts that issue and leaves the rest untouched. A
back-reference pointing at a deleted issue is reported rather than re-created.
Where a rung's carrier cannot be created — a label limit, a missing project —
the projection refuses for that rung and names it, rather than silently
promoting it to a level that would distort the rollup.

### Quality attributes (NFRs)

The board-doubling guardrail carries the pass/fail bar, measured as an item
count against the team's existing board at the first projection.

### Dependencies & integration

A Linear personal API key, already this pack's stated requirement. No new
dependency.

## Tasks

### T1: the create action is reachable only through the refresh processor

**Depends on:** spec:bounded-remote-create-action/T2

**Tests:**
- A create routed through the refresh processor is confirmed before transport.
  Verifies *no mutation executes without the confirmation*.
- The confirmation shows the exact per-item payload and the protected-field
  set. Verifies *shows the exact per-item payload*.
- One fresh confirmation creates exactly one issue; re-presenting it creates
  nothing. Verifies *one fresh confirmation creates exactly one issue*.
- No raw GraphQL write verb appears in the skill body. Verifies *no raw
  GraphQL write verb*.

**Approach:**
- The pack's prohibition is left exactly as written. It already directs
  confirmed write-back through the processor, so the create needs no exception
  and the pack keeps one auditable write route.

**Done when:** every assertion is green and the prohibition is byte-unchanged.

**Touches:** packs/linear/.apm/skills/linear/**

### T2: a label's canonical identity parses by one documented encoding

**Depends on:** T1

**Tests:**
- Every label carrying a rung encodes its canonical identity in the documented
  form. Verifies *encodes that rung's canonical identity*.
- Parsing a rendered label recovers the identity exactly; a non-parsing label
  fails. Verifies *parsing recovers the identity exactly*.

**Approach:**
- The encoding is documented before the renderer is written. Checking that a
  label "names" its rung without a parseable form lets the implementation
  supply its own oracle, which is the failure this task exists to avoid.

**Done when:** the parser round-trips every label in the reference projection
and rejects a hand-written non-conforming one.

**Touches:** packs/linear/.apm/skills/linear/**

### T3: the reference tree collapses onto Linear's three levels with a resolvable rollup

**Depends on:** T2, spec:tracker-projection-profile-table/T2

**Tests:**
- The reference tree yields one object or label per in-range rung; zero fails.
  Verifies *one Linear object or label for every rung in the range*.
- The rollup resolves from floor to top through each carrier, labels included.
  Verifies *the rollup resolves through whatever carrier*.
- Back-references resolve from both ends.
- An agent-internal unit produces no managed object.

**Done when:** the collapse fixture is green and the rollup walk reaches the
top rung through the labels.

**Touches:** packs/linear/.apm/skills/linear/**

### T4: projecting onto a populated workspace creates no duplicate

**Depends on:** T3

**Tests:**
- Projecting onto a workspace already holding the team's issues yields no
  second managed object where a back-reference already exists. Verifies *no
  second managed object*.
- An unkeyed collision refuses, named, before any mutation. Verifies *refuses
  that rung and names it*.
- Same tree twice changes no issue count.

**Done when:** the populated-workspace fixture creates nothing.

**Touches:** packs/linear/.apm/skills/linear/**

### T4a: repository scope is derived, and both sides of the brief rule are exercised

**Depends on:** T3

**Tests:**
- Scope derives from the canonical artifact's repository and the target's, with
  no static list. Verifies *repository scope is derived*.
- A same-repository brief produces no object; a cross-repository brief produces
  exactly one managed object. Verifies both brief criteria.

**Done when:** the paired fixture passes on both sides.

**Touches:** packs/linear/.apm/skills/linear/**

### T5: the return leg writes shaped intent onto an existing issue

**Depends on:** T1

**Tests:**
- A return-leg write is confirmed before transport and leaves existing fields
  intact.

**Done when:** a recorded confirmation transcript shows the write, and
`packs/linear/CHANGELOG.md` leads an entry.

**Touches:** packs/linear/.apm/skills/linear/**, packs/linear/CHANGELOG.md

## Rollout

T1 is inert until T2 uses it. Each task is independently revertible and the
pack's single write route is never widened.

## Risks

- **A bare label passes ADR-0125 and defeats the outcome.** Mitigated by the
  legibility criterion and its assertion over rendered output.
- **The tree outgrows three levels faster than expected.** The rollup assertion
  is the detector: it walks carriers rather than levels, so a deeper tree fails
  the walk rather than rendering something plausible.
- **Instruction text inside an issue.** The pack already refuses to act on it;
  the projection adds no path that would read it as direction.

## Changelog

- 2026-09-24 — plan drafted.
