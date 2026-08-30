# Spec: <feature name>

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** <!-- ADR-NNNN, RFC-NNNN, or "none" -->
- **Brief:** <!-- optional: the delivery brief this spec was derived from (`docs/product/briefs/<slug>.md`); stamped by author-delivery-brief continue. Omit, or "none", for a spec authored directly. Distinct from Constrained by: this is product provenance, not a governance constraint. -->
- **Discovery:** <!-- optional: the upstream discovery artifact this spec descended from (a decision brief / intent produced by an upstream discovery process), named by its stable id; the discovery-side sibling of Brief: (the spec→discovery up-edge a traceability check walks). Omit, or "none", for a spec authored without an upstream discovery. -->
- **Contract:** <!-- contracts/<type>/<name> this spec defines or touches (see new-spec step 4b / CONVENTIONS § 4 Contracts), or "none" for a non-API feature. A contract surface is not just a synchronous REST API — an event interface or a backend-for-frontend (BFF) boundary is a contract too; name it here and author it under contracts/<type>/. -->
- **Shape:** <!-- optional: ui | service | data | integration | mixed — selects which `## Design (LLD)` sub-sections scaffold in plan.md (e.g. ui pulls in component decomposition + state & control flow; service pulls in interfaces & contracts + data & schema + resilience — the plan template carries the authoritative map). Omit, or "mixed", when the feature spans several or you're unsure; the plan then scaffolds the full set and you prune. Stack-neutral: it names the *kind* of work, never a framework. -->
<!-- If this spec intentionally has no criteria, remove the section below and add `- **Acceptance Criteria:** none — <one-line reason>` to the metadata header. -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Objective, Boundaries, Testing
Strategy, Acceptance Criteria, and Assumptions to the depth the durable work
requires. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

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

## Durable Outputs

<!--
Plan the lasting records this delivery must create or update before the spec is
approved. This is repository-specific, not a fixed checklist. Consider user
promise, current product truth, current architecture, decision rationale,
interface compatibility, operations, maintainer procedure, release history, and
reusable learning. Include only applicable roles.

For each row, name:

- Semantic role
- Applicability
- Destination
- Owner
- Expected evidence
- Closeout condition

If no durable output is applicable, write `none` with an explicit rationale.
If a destination is ambiguous or absent, record the still-required decision as
the closeout blocker; do not guess or create a placeholder. Read each applicable
existing human-readable surface as a whole and name any refresh work before
approval. For user-facing behavior, draft the established user-documentation
surface before implementation approval.
-->

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| <role> | <why applicable / why absent> | <resolved path, external locator, or required decision> | <owner role or workflow> | <test, guide, contract, release, or review evidence> | <what close-work must verify> |

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
metadata contract). A newly Shipped spec has no open Acceptance Criteria.

Two recurring sources of criteria, so they don't slip into the plan as
mere design detail:

- An **output-channel constraint** (e.g., "no sensitive data on stdout")
  must enumerate *every* channel the consuming context makes user-visible
  (stdout, stderr, logs, skill output surfaced to the agent). Apply the
  same constraint to each one explicitly — a constraint named on one
  channel only is silently violated if the caller also sees another.

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

- A criterion that needs "and" to join two **different predicates** is two
  criteria: a conjunction is where a coverage check silently passes while half
  the criterion is unimplemented. A criterion is more than one when its parts
  have separate failure modes with separate remedies. Where the parts read as one
  constraint over a set, rewrite the criterion as a single predicate with a
  member substituted in; it stays one criterion only if that predicate is
  checkable as written at every member rather than expanding into a different
  check per member. The worked examples below fix where this boundary falls;
  where the cue and an example conflict, the examples govern.

  - **E1 — splits.** "`writer.py` emits `manifest.json` with keys in byte-sorted
    order, and `--dry-run` prints that manifest without writing a file." Two
    different predicates; no single sentence covers both. The base case where the
    conjunction cue and the split test agree.
  - **E2 — stays one.** "no sensitive data reaches stdout, stderr, logs, or skill
    output surfaced to the agent." One predicate substituted at each member of an
    enumerated set, checkable as written at every member.
  - **E3 — stays one.** "the digest preimage is the u64be path length, the path
    bytes, the execute byte, the u64be content length, then the content bytes."
    One comparison value expressed in parts — the split test never engages,
    because there is one failure and one remedy.
  - **E4 — splits.** "the same constraint, correctness, holds across stdout and
    the exit code." "X is correct" is not checkable as written: it expands into a
    different check per member. This is the anti-licence against reframing a
    bundle as one constraint over a domain, and without it E2's shape is available
    to any author.
  - **E5 — stays one.** "session cookies are set `Secure` and `HttpOnly`."
    Different failure modes (interception, script access) but one substitutable
    predicate and one remedy. Shows that separate failure modes alone do not
    split when the predicate survives substitution.

- A universal claim enumerates its closed set or names the mechanism that makes
  coverage exhaustive: without one, a reviewer cannot tell which members the
  claim covers or whether an omitted member is a defect.

- A new claim becomes a new checklist item, never a lettered or semicolon
  graft: a graft hides a separately reviewable outcome inside an existing
  criterion and makes its completion ambiguous.

- For every numeric limit a criterion states, record the input that makes the
  limit fire first and the enforcement mechanism that makes that ordering true;
  a limit missing **either** fact is not yet a criterion. Where one quantity has
  two limits, either order them so each is reachable for some input, or declare
  one non-binding on that route and name the limit that fires instead.

- A criterion stating a limit names the reference point it is measured from.
  Choose an origin that gives the same input the same measurement however the
  subject is organised; an unstated origin is not yet a criterion. A criterion
  requiring a limit states its value and never asks an implementer to supply one:
  a value invented to satisfy an unspecified requirement is worse than an absent
  limit, because it reads as a decision that was made.

- Make every claim earn its place by making a wrong implementation detectable.
  Delete rationale, history, reassurance, restated context, and a figure that
  merely explains where a threshold came from when it does not help establish the
  outcome. Keep any claim that is the only written form of a comparison value,
  such as a byte layout, exact key order, literal token, collection floor, or
  stated bar. Ask: "could a wrong implementation now pass this?"

- A criterion names an observable outcome. Naming a function's parameters, a
  helper, or a call sequence is the give-away that the content belongs in the
  plan. See the Objective guidance and `SKILL.md`'s design-doc anti-pattern for
  the document-level distinction.

- [ ] <observable outcome>
- [ ] <observable outcome>
- [ ] <observable outcome>

Do not use `(deferred: <slug>)` as a new shipping exception. If an accepted AC
is still required, keep the spec `Implementing` and resume it. If a separable
item no longer belongs in the final accepted contract, pause for a reviewed
spec/plan amendment, remove it from this checklist, and record it under
`Follow-ons` with its owner and stable artifact or external evidence reference.
Historical frozen specs may still contain older `(deferred: <slug>)` markers;
do not copy that pattern into new shipped work.
-->

<!--
Optional story trace: when this spec was derived from a product brief that
carries user stories (Shape B; see author-delivery-brief continue), append `Satisfies: US-n`
to each acceptance criterion that satisfies that story, so coverage is
story-granular:

- [x] <observable outcome>. Satisfies: US-2

The marker is optional — omit it for a no-stories brief (Shape A) or a spec
authored directly.
-->

## Follow-ons

<!--
Separately scoped work that does not belong to the final accepted AC set. Each
entry needs an owner and a stable work-intake artifact or external evidence
reference. Do not use this section to hide unfinished accepted intent.

- <owner>: <stable artifact or external ref> — <one-sentence scope>
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
