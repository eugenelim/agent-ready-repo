# Spec: <feature name>

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** <!-- ADR-NNNN, RFC-NNNN, or "none" -->
- **Brief:** <!-- optional: the product brief this spec was derived from (`docs/product/briefs/<slug>.md`); stamped by receive-brief. Omit, or "none", for a spec authored directly. Distinct from Constrained by: this is product provenance, not a governance constraint. -->
- **Discovery:** <!-- optional: the upstream discovery artifact this spec descended from (a decision brief / intent produced by an upstream discovery process), named by its stable id; the discovery-side sibling of Brief: (the spec→discovery up-edge a traceability check walks). Omit, or "none", for a spec authored without an upstream discovery. -->
- **Contract:** <!-- contracts/<type>/<name> this spec defines or touches (see new-spec step 4b / CONVENTIONS § 4 Contracts), or "none" for a non-API feature. A contract surface is not just a synchronous REST API — an event interface or a backend-for-frontend (BFF) boundary is a contract too; name it here and author it under contracts/<type>/. -->
- **Shape:** <!-- optional: ui | service | data | integration | mixed — selects which `## Design (LLD)` sub-sections scaffold in plan.md (e.g. ui pulls in component decomposition + state & control flow; service pulls in interfaces & contracts + data & schema + resilience — the plan template carries the authoritative map). Omit, or "mixed", when the feature spans several or you're unsure; the plan then scaffolds the full set and you prune. Stack-neutral: it names the *kind* of work, never a framework. -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- **Light-mode lean fill.** For low-risk work running the `work-loop`
skill's light mode, only Objective + Acceptance Criteria + a short task list
(in `plan.md`) are required. **Boundaries**, **Testing Strategy**, and
**Assumptions** are optional — keep them only if they earn their place. Any
risk trigger (see the `work-loop` skill) escalates to full mode, where every
section is filled. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
changelog. This applies to the spec body only — `plan.md` keeps its own
changelog of how the approach evolved. -->

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
under, and why. These three modes are the *altitude* of a check, not its
*surface*: a goal-based or manual-QA behavior may be verified by an
**integration** test (two components together) or an **end-to-end (E2E)**
test (the whole journey, as the user drives it) rather than a unit test —
name that surface when a behavior only proves out across a boundary or a
full flow.

<!--
e.g. "Validation rules: TDD. Config wiring: goal-based. End-to-end signup
flow: manual QA, exercised by an E2E test. Cross-service order placement:
goal-based, exercised by an integration test." If you can't pick a mode for
a behavior, the behavior is too vague — sharpen it before moving on.
-->

## Acceptance Criteria

<!--
The verifiable goals that close this spec. Each item should be checkable
without subjective judgement — a reviewer can read it and know whether it
holds. Notation: `- [ ]` open, `- [x]` met (see CONVENTIONS § 4 Spec
metadata contract).

Two recurring sources of criteria, so they don't slip into the plan as
mere design detail:

- A **UI state** is an acceptance criterion: phrase it as
  *state / trigger / outcome* — "given <state>, when <trigger>, the user
  sees <outcome>" (e.g. "given an empty cart, when the page loads, the
  user sees the empty-state illustration and a 'browse' link"). The
  per-screen design itself lives in the plan's `## Design (LLD)`; the
  observable state belongs here.
- A **non-functional requirement with a pass/fail bar** is an acceptance
  criterion: it must name a threshold a test or audit can check —
  "meets WCAG 2.2 AA", "p99 latency under 200ms at 1k rps", "zero criticals
  in the dependency scan". An NFR with no bar ("should be fast") is not a
  criterion; give it a number or move it to the plan.

- [ ] <observable outcome>
- [ ] <observable outcome>
- [ ] <observable outcome>

A criterion that ships unmet *on purpose* is never left silently unchecked —
mark it deferred with an inline anchor into the backlog register:

- [ ] <observable outcome> (deferred: <backlog-anchor>)

where <backlog-anchor> resolves to a heading in `docs/backlog.md`.

Optional story trace: when this spec was derived from a product brief that
carries user stories (Shape B; see receive-brief), append `Satisfies: US-n`
to each acceptance criterion that satisfies that story, so coverage is
story-granular:

- [x] <observable outcome>. Satisfies: US-2

The marker is optional — omit it for a no-stories brief (Shape A) or a spec
authored directly.
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
