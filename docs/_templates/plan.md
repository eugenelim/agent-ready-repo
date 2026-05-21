# Plan: <feature name>

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

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
If this affects production behavior: how does it ship? Behind a flag? Big bang?
Gradual? Reversible?
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
