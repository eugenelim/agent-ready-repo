# Spec: <feature name>

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** <!-- ADR-NNNN, RFC-NNNN, or "none" -->

> **Spec contract:** this document defines what "done" means. The implementing PR
> must match this spec, or update it. Tests must be derivable from it.

## What this is

<!--
One paragraph. What does this feature do, from the perspective of someone who
will use it? No implementation detail.
-->

## Why

<!--
What problem does this solve? Link to the spec/RFC/issue that motivates it.
Two sentences.
-->

## Users and use cases

<!--
Who uses this, and what are they trying to accomplish? List the top 2-5 use
cases by priority. The first one is the one we will not compromise on.
-->

## Behavior

<!--
The contract, in prose, from the perspective of a caller/user.

One paragraph per coherent piece of behaviour. What inputs produce what
outputs, what side effects, what guarantees. No internals. No test syntax —
the test list lives in "Contract tests" below.

**Frame behaviors at the boundary your users actually observe.**
- API behaviors as request → response, or input → effect with status
  codes and error shapes.
- UI behaviors as user gesture → visible outcome (not "form validates
  required fields" but "user sees inline error next to empty required
  field on submit").
- CLI behaviors as command → exit code / stdout / stderr.
- Agentic behaviors as input → evaluable outcome (e.g. "given prompt
  X, the agent's output passes eval Y" or "agent calls tool T at most
  N times per turn before returning").

Implementation details ("the form validates required fields", "the
handler short-circuits on auth failure") belong in `plan.md`;
behaviors are what users perceive.

The reader of this section should understand what the feature does without
caring how the test runner is wired up.
-->

### Inputs

<!-- Shape of inputs (request bodies, function arguments, config). -->

### Outputs

<!-- Shape of outputs (response bodies, return values, side effects). -->

### Errors and edge cases

<!-- What can go wrong, and what the user/caller sees when it does. -->

## Contract tests

<!--
The concrete test list — the gate for "done". Black-box: each test exercises
behaviour described above, not internals. Any valid implementation must pass
all of them.

Designed up front, *with the spec* — before plan.md or any code. If you
can't write the test for a Behavior bullet, the bullet is too vague;
sharpen it before moving on.

One bullet per test. Each bullet should be concrete enough that an
implementer can name a test function for it. Format:

- **`<test_name>`** — Given <preconditions>, when <action>, then <observable result>.
- **`<test_name>`** — rejects <invalid input> with <specific error>.
- **`<test_name>` (property)** — for all <input shape>, <invariant> holds.

These tests are stable against *implementation* change. They evolve with
*spec* change (behaviour change) during the living phase and freeze when
the spec freezes. Construction tests — per-step units, fixtures, internal
helpers — live in `plan.md`, not here.
-->

## Non-goals

<!--
What are we explicitly NOT doing? This is the section that prevents scope
creep — both from humans and from agents who'd otherwise "helpfully" expand
the feature.
-->

## Open questions

<!-- Anything not yet decided. Resolve these before status moves past Draft. -->

## Acceptance criteria

<!--
The non-test checklist for "done". Tests are already covered by the Contract
tests section above (the test list IS the test gate). This section captures
*everything else* a shipping feature needs:

- [ ] All Contract tests pass (the test gate)
- [ ] Public API documented in <location>
- [ ] CHANGELOG entry
- [ ] Migration guide / runbook updated (if applicable)
- [ ] Feature flag / rollout plan (if applicable)
-->
