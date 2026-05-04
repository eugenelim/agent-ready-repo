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
The contract. This is the section the implementation must match.

Structure as a list of behavioral statements that are individually testable:

- Given <preconditions>, when <action>, then <result>.
- The system rejects <invalid input> with <specific error>.
- <Field X> is required; <field Y> defaults to <value>.

Specificity beats prose here. If a behavior can be tested, write it as a
testable statement.
-->

### Inputs

<!-- Shape of inputs (request bodies, function arguments, config). -->

### Outputs

<!-- Shape of outputs (response bodies, return values, side effects). -->

### Errors and edge cases

<!-- What can go wrong, and what the user/caller sees when it does. -->

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
The checklist for "done". Usually one or two items per behavioral statement
above, plus tests, docs, and any migration steps.

- [ ] All behavioral statements have at least one test
- [ ] Public API documented in <location>
- [ ] CHANGELOG entry
- [ ] ...
-->
