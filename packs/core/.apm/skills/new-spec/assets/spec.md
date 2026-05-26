# Spec: <feature name>

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** <!-- ADR-NNNN, RFC-NNNN, or "none" -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

<!--
One paragraph. What are we building, who is the user, and what does success
look like for them? Frame from the user's perspective, not the implementer's.
Implementation detail belongs in `plan.md`.
-->

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

<!-- Defaults the agent applies without asking. -->

-
-
-

### Ask first

<!-- Changes that need human sign-off before proceeding. -->

-
-
-

### Never do

<!-- Hard rules. No exceptions, no clever workarounds. -->

-
-
-

## Testing Strategy

Name the verification mode(s) this spec uses. The
`work-loop` skill defines three:

- **TDD** — for logic with a compressible invariant.
- **Goal-based check** — a one-liner verifies the outcome (a build
  command, a `grep`, a typecheck).
- **Visual / manual QA** — a recorded gesture and an observable
  outcome, for UX flows.

A spec may pick one or mix them. State which mode each behavior falls
under, and why.

<!--
e.g. "Validation rules: TDD. Config wiring: goal-based. End-to-end signup
flow: manual QA." If you can't pick a mode for a behavior, the behavior is
too vague — sharpen it before moving on.
-->

## Acceptance Criteria

<!--
The verifiable goals that close this spec. Each item should be checkable
without subjective judgement — a reviewer can read it and know whether it
holds.

- [ ] <observable outcome>
- [ ] <observable outcome>
- [ ] <observable outcome>
-->

## Assumptions

<!--
Audit trail for the assumption-surfacing checkpoint that ran when this
spec was drafted (see `new-spec` SKILL.md step 3). Each item names how
it was settled. This section is *not* the contract — it's the frame the
contract was written under. The contract lives above (Objective,
Boundaries, Testing Strategy, Acceptance Criteria).

Format: `- <category>: <fact> (source: <path | URL | probe | user
confirmation YYYY-MM-DD>)`

- Technical: <fact> (source: <…>)
- Process: <fact> (source: <…>)
- Product: <fact> (source: user confirmation YYYY-MM-DD)

If an assumption later turns out wrong, fix the spec body in the same
PR and add a one-line note here recording what changed and why.
-->
