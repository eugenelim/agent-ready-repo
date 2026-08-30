# Plan: <feature name>

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** <task-relevant architecture/convention source;
  one or two analogous production implementations; corresponding tests or
  construction path; named uncertainty/deviation — or `none — non-structural`>

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (or the adopter repository's equivalent document-lifecycle guidance).

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling
spec is the durable behavior contract. Eligible direct-light work does not
create this artifact. -->

## Approach

<!--
A paragraph describing the strategy. What's the shape of the change? What's
the order of operations? What's the riskiest part?

A reader should finish this section knowing roughly what files will move and
what the testing story is, without yet seeing the detailed task list.
-->

## Constraints

<!--
What ADRs, RFCs, or other commitments shape this implementation? Cite them.
This is what keeps the plan from contradicting prior decisions.
-->

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`
subsections). This top-level section is only for cross-cutting tests that
span tasks.

<!--
Construction tests guide implementation. They sit in two layers:

1. **Per-task tests** (the majority) live under each Task below, in the
   `Tests:` subsection. That's where unit, edge-case, and property tests
   for a single task go.
2. **Cross-cutting tests** (this section) live here, listed once: integration
   tests that span tasks, end-to-end smoke tests, and any manual verification
   steps.

Designed up front, before EXECUTE. Revisable if a test over-specifies an
internal detail the plan later changes. The contract itself lives in
`spec.md` (Acceptance Criteria + Testing Strategy); construction tests
that verify it live here.

**Integration tests:** <list, or "none beyond per-task tests">
**Manual verification:** <list, or "none">
-->

## Durable-output map

<!--
This section maps each task to the spec's Durable Outputs table so closeout can
verify planned output, implementation evidence, and closeout evidence without
copying requirements into a second record.

For each output, name:

- planned output
- implementing task(s)
- implementation evidence
- closeout evidence
- unresolved destination or freshness blocker, if any

If the plan's Design (LLD) contains a non-inferable design fact, map it to its
semantic owner here. Mechanically evident details may stay with code, types,
docstrings, and tests; one-off construction order may remain delivery residue.
-->

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| <semantic role / destination> | <Tn> | <test, build, guide, contract, or review artifact> | <what close-work verifies> |

## Design (LLD)

The low-level design — the *how*, below the Approach and above the per-task
steps. **Optional and shape-pruned:** scaffold only the sub-sections the spec's
`Shape:` selects, and delete the rest. A one-file change keeps this section thin
or empty; a heavyweight feature fills most of it. The spec stays the contract —
**no acceptance criterion lives here**; each sub-section instead **traces to the
AC(s) it satisfies and the `contracts/` it implements**, so the design is always
anchored to something verifiable.

Stack-neutral by construction: these are the *kinds* of design decision every
build makes, never a framework. Name your actual stack *inside* each sub-section
from the repository's mapped architecture and convention sources. If none are
usable, use manifests/build files and, for structural work, one or two analogous
production implementations with their tests or construction path; elicit any
unresolved load-bearing choice. The headings themselves stay universal.

<!-- Shape → sub-sections (a guide, not a gate):
  ui          → decomposition, state & control flow, behavior & rules, quality attributes
  service     → interfaces & contracts, data & schema, failure & resilience, quality attributes
  data        → data & schema, interfaces & contracts
  integration → dependencies & integration, interfaces & contracts, failure & resilience
  mixed/unsure→ scaffold all, then prune.
Delete every sub-heading the shape doesn't select. -->

### Design decisions
<!-- optional — the load-bearing choices and the alternatives rejected, one line
of why each. Traces to: <AC(s) this satisfies> · <contracts/… it implements>. -->

### Data & schema
<!-- optional — entities, fields, types, ownership, migrations, retention.
Traces to: <AC(s)> · <contracts/…>. -->

### Interfaces & contracts
<!-- optional — the surfaces this feature exposes or consumes (REST API, event
interface, BFF, RPC). Point at the `contracts/<type>/` file each implements.
Traces to: <AC(s)> · <contracts/…>. -->

### Component / module decomposition
<!-- optional — the parts and their responsibilities; what's new vs. reused; for
UI, the component tree. Traces to: <AC(s)> · <contracts/…>. -->

### State & control flow
<!-- optional — state model and transitions; sequencing across components; for
UI, screen states and navigation. Traces to: <AC(s)> · <contracts/…>. -->

### Behavior & rules
<!-- optional — the business and validation rules and the decisions they drive.
Traces to: <AC(s)> · <contracts/…>. -->

### Failure, edge cases & resilience
<!-- optional — what can go wrong and the response: retries, fallbacks, timeouts,
partial failure, idempotency, degraded modes. Traces to: <AC(s)> · <contracts/…>. -->

### Quality attributes (NFRs)
<!-- optional — how the design meets each NFR-with-a-bar from the spec's
Acceptance Criteria (performance, accessibility, security posture, operability).
Traces to: <AC(s)> · <contracts/…>. -->

### Dependencies & integration
<!-- optional — external systems, services, and libraries this design leans on,
and the coupling between them. (Reuse `Depends on:` / `Touches:` on the tasks
below for *execution* ordering; this sub-section is for *design*-level coupling.)
Traces to: <AC(s)> · <contracts/…>. -->

> **Rollout & deployment** — the tenth design dimension — is **not** a
> sub-heading here. It is realized by [`## Rollout`](#rollout) below (infra,
> external-system integration, deployment sequencing). Cross-link it from the
> relevant sub-sections; never duplicate it.

## Tasks

The work-breakdown. Tasks are sized so each one is a coherent commit or PR.
**Phrase each task as a verifiable goal, not a procedure.** The task name
*is* the success criterion: *"Add validation"* → *"All invalid-input tests
pass"*; *"Refactor X"* → *"Tests for X green before and after; public
surface unchanged"*. **Within each task, `Tests:` comes before `Approach:`** —
tests drive implementation, not the other way around. Use red-green-refactor
with separate commits when the change is non-trivial.

**Every task must declare `Depends on:` explicitly** — list prior task IDs
or `none`. Don't omit the field; "obvious from order" is the failure mode
that hides serial-by-default thinking. `none` is a valid and common answer.

Planning is sufficient when the plan supplies an observable contract, owner,
boundaries, ordering, discovery predicates where a seam is not grounded,
required outcomes, and verification modes adequate to begin safely. It need
not settle a helper name, symbol, fixture-internal detail, or complete edge-case
matrix before implementation. Such questions are build-time guidance unless
their absence makes the plan unable to start or verify the contract.

Keep observable behavior in `spec.md`. Use an exact path or symbol here only
when repository evidence grounds it. For an implementation-discovered callable
seam, record `no stub (implementation-discovered)` and its discovery predicate,
constraint, required outcome, and verification mode; do not invent a helper,
fixture, module, path, or symbol.

**`Depends on:` grammar** (so the supervisor-mode scheduler —
`loop-cohort schedule` — can read it). The field is a comma-separated list of:
local task IDs (`T1`, `T1a`), ranges (`T1-T6`), or a **cross-spec marker**
`spec:<name>/TN` for a dependency on another spec's task (e.g.
`spec:auth-tokens/T7`). Parenthetical prose after the IDs is
ignored, so `T11 (lands after the shim)` is fine. Cross-spec deps are
*spec-sequencing*, not intra-plan waves, and are excluded from this plan's
DAG. The scheduler **fails on a dependency cycle** and **warns on a
forward-reference** (a dep authored later — it still schedules correctly by
running the dep first).

**Optional `Touches:` grammar** (read by `loop-cohort schedule`).
A task *may* add a `**Touches:**` line listing the file globs it expects to
touch — a comma-separated list of paths/globs (`src/api/*.py, docs/api.md`),
trailing prose ignored. `loop-cohort schedule` uses it to predict, per wave,
`predicted-disjoint: yes|no|unknown` **before** dispatch — a cheap
*serialize-only* screen. It **never greenlights** parallel: a predicted overlap
serializes early, but `yes`/`unknown` still require the authoritative post-write
`git merge-tree` check to actually parallelize (under-declaration is unsafe).
The field is **optional** — omit it freely; a task with no `Touches:` makes its
wave `unknown`, never an error.

<!--
Order matters — list tasks in the order they should be done. Mark
dependencies inline. Format each task so a contributor (human or agent)
could pick it up and complete it without follow-up questions:

### T1: <task name>

**Depends on:** <none | T0, ...>

**Tests:**
- <test 1 — behaviour, edge case, or property; reference the Acceptance
  Criterion from spec.md this step verifies, if any>
- <test 2>
<!-- For an already-grounded callable seam or coherent TDD task family, include
     one compilable red contract-surface assertion (`stub: true`). It need not
     encode the finished edge-case matrix. -->

**Approach:**
- <step 1>
- <step 2>

**Done when:** <name a concrete observable — specific test green, gate
  passing, behaviour visible at <surface>. Not "looks good" or "feature
  works".>

### T2: <task name>

...
-->


## Rollout

<!--
How this ships — the tenth design dimension, realized here rather than as a
`## Design (LLD)` sub-heading (cross-linked from there, never duplicated). Cover
the dimensions that apply; a pure-logic change with none of them says so in one
line.

- **Delivery:** behind a flag? big bang? gradual / canary? Reversible — what is
  the rollback, and what's irreversible (a data migration, a published event)?
- **Infrastructure:** new or changed infra this needs (compute, storage, queues,
  network, secrets, IAM) and how it's provisioned.
- **External-system integration:** third-party or sibling-service dependencies
  that must be live, migrated, or version-matched before this can ship.
- **Deployment sequencing:** the order steps must ship in when one depends on
  another — schema migration before the code that reads it, consumer before
  producer, dark-launch before cutover. This is the dimension with no other home.
-->

## Risks

<!--
What could go wrong during implementation (vs. risks of the design itself,
which belong in the spec)? Things like: "this migration is online and could
slow the database", "this changes a behavior X teams depend on".
-->

## Changelog

<!--
When the plan changes meaningfully, add a dated entry. This isn't bureaucracy —
it's how a reviewer (or a returning agent) understands why the current plan
looks different from yesterday's plan.

- YYYY-MM-DD: initial plan
- YYYY-MM-DD: switched from approach A to B because <reason>
-->
