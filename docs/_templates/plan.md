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

## Tasks

<!--
The work-breakdown. Tasks are sized so each one is a coherent commit or PR.

Format each task as something a contributor (human or agent) could pick up
and complete without asking follow-up questions. Order matters — list them
in the order they should be done. Mark dependencies inline.

- [ ] T1: <task> — <one-line description>
- [ ] T2: <task> — depends on T1
- [ ] T3: <task> — can be done in parallel with T2
-->

## Testing strategy

<!--
How do we know it works?

- Unit tests for: <list>
- Integration tests for: <list>
- Manual verification: <list>

The spec has acceptance criteria; this section says how we'll satisfy them.
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
