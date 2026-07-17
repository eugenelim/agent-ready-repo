# Plan: <feature name>

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

<!-- **Light-mode lean fill.** For low-risk work running the `work-loop`
skill's light mode, only Approach + a short Tasks list are required.
**Constraints**, **Risks**, **Changelog**, and the whole `## Design (LLD)`
section are optional — keep them only if they earn their place. Any risk
trigger (see the `work-loop` skill) escalates to full mode, where every
section is filled. -->

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
— derived from `docs/architecture/reference.md` when that file is present (use
its components, stereotypes, and standards by name), otherwise from the
established repo (lockfiles, build files, imports) or elicited when unclear. The
headings themselves stay universal.

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
