# Spec: lld-aware-spec-plan

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0019, ADR-0009
- **Contract:** none <!-- this enriches the spec/plan templates and two skills; it exposes no machine interface, so new-spec step 4b is skipped -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An enterprise build needs a **low-level design** — for UI, screen states,
component decomposition, state management, navigation, accessibility; for
backend, data model, sequence, resilience, security, deployment sequencing.
Core's `plan.md` has no home for it today, and deployment sequencing in
particular has no home anywhere. This feature enriches the spec/plan templates
so an LLD fits — **without baking any one tech stack into a universal template**.

The author (human or agent, via `new-spec` or `receive-brief`) gets: a
stack-neutral `Shape:` field on the spec that selects which design sub-sections
scaffold; a `## Design (LLD)` section in the plan built from **ten stack-neutral
categories** (nine scaffold as Design sub-headings; the tenth — rollout &
deployment — lives in the expanded `## Rollout`) — optional and shape-pruned, so
a one-file change keeps a thin plan; and an expanded `## Rollout` that finally covers infra, external-system
integration, and deployment sequencing. The **spec stays the contract** — it
gains only the light `Shape:` selector and AC guidance (a UI state/trigger/
outcome becomes an acceptance criterion; an NFR with a pass/fail bar becomes
one); **no LLD body migrates into it**. The design lives in the plan.

The stack-specific content is **derived, never shipped**: `new-spec` and
`receive-brief` read `docs/architecture/reference.md` (RFC-0020) and conform to
it when present, and degrade to established-repo detection plus elicitation when
absent. Success for the adopter: a heavyweight feature records a real,
stack-correct LLD in its plan, while a trivial change still gets a thin plan and
no adopter inherits a stack they don't use.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep every template change **additive** — add an optional field or section;
  never remove or rename an existing spec/plan section.
- Make the `## Design (LLD)` sub-sections **optional and shape-pruned** — scaffold
  only the categories the `Shape:` selects, so a thin change keeps a thin plan.
- **Derive** stack-specific content: read `docs/architecture/reference.md` and
  conform when present; degrade to repo detection + elicitation when absent.

### Ask first

- Before adding any category beyond the ten stack-neutral ones — that contests
  the abstraction and needs sign-off.
- Before the derivation step *invents* a stack when detection is ambiguous —
  elicit from the user instead.
- Before changing the `## Rollout` section's existing meaning (vs. expanding its
  coverage) — existing plans depend on it.

### Never do

- **Never** bake a tech stack into the shipped template — no React, TanStack,
  Kafka, Spring, or any concrete framework/library name appears in the template;
  it ships only the universal category *names*.
- **Never** move an LLD body into `spec.md` — the spec stays the contract; the
  design lives in `plan.md`.
- **Never** add a separate `design.md` tier or a new top-level directory — the
  plan is the design home; net new surface is one section added, one expanded.
- **Never** add a new dependency tier or testing tier — reuse `Depends on:` /
  `Touches:` for dependencies and `Construction tests` + the spec's `Testing
  Strategy` for testing.

## Testing Strategy

- **Template enrichment (`Shape:` field, `## Design (LLD)` categories, expanded
  `## Rollout`, AC guidance): goal-based check.** Verify the `spec.md` /
  `plan.md` templates carry the new optional field/section with the ten category
  names and the expanded Rollout coverage, that no concrete stack string appears
  in the templates (a `grep` for framework names returns nothing), and that
  `lint-spec-status.py` / `lint-skill-spec.py` still pass. File-presence + grep +
  existing linters prove these; no production test asserts what they already do.
- **Backward compatibility / additivity: goal-based check.** Confirm prior specs
  and plans (the existing spec dirs) remain valid and `make build-self`
  projects the enriched templates cleanly with no unexpected reverts.
- **Shape/stack-derivation step in `new-spec` and `receive-brief`: manual QA.**
  The derivation is LLM judgment; verify by walking two worked cases — one with a
  `docs/architecture/reference.md` present (LLD conforms, referencing named
  components) and one without (LLD degrades to repo detection + elicited gaps) —
  recording the result. A unit test here would only assert prose shape.

## Acceptance Criteria

- [x] The **`spec.md` template** gains an optional, stack-neutral `Shape:` field
  (`ui | service | data | integration | mixed`) documented as selecting which
  plan `## Design (LLD)` sub-sections scaffold.
- [x] The spec's **AC guidance** is extended so a UI **state / trigger / outcome**
  lands as an acceptance criterion and an **NFR with a pass/fail bar** (e.g.
  WCAG-AA, p99 latency) is an acceptance criterion.
- [x] The `spec.md` template's `Testing Strategy` comment names **integration /
  E2E** and its `Contract:` comment names **events / BFF** as verification
  surfaces (grep-verifiable in the shipped template).
- [x] The spec gains **no LLD body** — only the `Shape:` field and AC guidance;
  the design lives in the plan (reviewer-verifiable negative criterion).
- [x] The **`plan.md` template** gains a `## Design (LLD)` section **before
  `## Tasks`** carrying **nine** of the ten stack-neutral categories as optional,
  shape-selected `###` sub-headings: design decisions; data & schema; interfaces
  & contracts; component / module decomposition; state & control flow; behavior &
  rules; failure, edge cases & resilience; quality attributes (NFRs);
  dependencies & integration. The tenth category — **rollout & deployment** — is
  **not** a Design sub-heading; it is realized by the expanded `## Rollout` (which
  lives after `## Tasks` in the template), referenced as a cross-link, never
  duplicated.
- [x] Each `## Design (LLD)` sub-section's guidance says it **traces to the AC(s)
  it satisfies and the `contracts/` it implements**.
- [x] The existing **`## Rollout`** section is **expanded** to cover infra,
  external-system integration, and deployment sequencing (the rollout &
  deployment category is realized here, not duplicated as a Design sub-heading).
- [x] **No new dependency tier or testing tier** is added — `Depends on:` /
  `Touches:` carry dependencies; `Construction tests` + the spec's `Testing
  Strategy` carry testing (reviewer-verifiable negative criterion).
- [x] **`new-spec`** gains a shape/stack-derivation step: derive the `Shape:`
  (from the brief or by asking) and the stack.
- [x] The derivation step **reads `docs/architecture/reference.md` when present**
  and conforms the LLD to it (referencing its components/stereotypes/standards by
  name); **when absent it degrades** to established-repo detection (lockfiles /
  build files / imports) and/or brief-intake context, eliciting gaps.
- [x] **`receive-brief`** gains the same shape/stack-derivation step when it
  scaffolds specs (depends on `receive-brief` existing — `product-brief-intake`).
- [x] The **shipped templates contain only the universal category names** — no
  concrete framework/library/stack string appears (Principle 1; grep-verifiable).
- [x] Every change is **additive**: no existing spec/plan section removed or
  renamed; all prior specs/plans stay valid; `make build-self` projects the
  enriched templates cleanly.
- [x] The **`CONVENTIONS.md` seed amendment** documenting the LLD enrichment in §4
  (the `Shape:` field, the `## Design (LLD)` categories, stack-derivation) lands
  in this spec's implementing PR (it documents artifacts this spec creates).
- [x] **`make build-check`** is green.
- [x] The adopter-facing **reference / explanation guides** covering the spec/plan
  LLD additions (`Shape:`, the `## Design (LLD)` categories, stack-derivation) are
  authored via `new-guide`, coordinated with `product-brief-intake`'s guide work.
  *(Authored in this catalogue repo; `new-guide` lives in the non-core
  `user-guide-diataxis` pack and is not a capability `core` ships to adopters.)*

## Assumptions

- Process: spec is constrained by RFC-0019 (Accepted 2026-06-01), Decisions 8
  (LLD locus = enrich `plan.md` + light `spec.md`) and 9 (stack derived, not
  baked) (source: docs/rfc/0019-product-brief-intake.md).
- Process: the plan-owned LLD and derived-stack decisions are recorded in
  ADR-0009 (source: docs/adr/0009-product-brief-layer-and-plan-owned-lld.md).
- Technical: the ten categories are stack-neutral — validated in RFC-0019 against
  two real enterprise LLDs (a UI per-screen LLD and a backend LLD); every item
  mapped, deployment sequencing was the only previously-homeless dimension
  (source: RFC-0019 Evidence & prior art, Assumption 4).
- Technical: the spec/plan templates are pack-source at
  `packs/core/.apm/skills/new-spec/assets/`, projected to
  `.claude/skills/new-spec/assets/`; edits go to source then `make build-self`
  (source: new-spec SKILL.md step 2; memory: self-host projection).
- Technical: the `docs/architecture/reference.md` foundation is defined by
  RFC-0020 (Accepted); the derivation step's present/absent branch is the seam
  that lets RFC-0019 and RFC-0020 land in either order (source: RFC-0019
  Decision 9; RFC-0020).
- Technical: no `new-spec` step 4b contract — this enriches templates and skills,
  exposing no machine interface (source: new-spec SKILL.md step 4b conditional).
- Process: this spec's `receive-brief` derivation task depends on
  `product-brief-intake` having shipped `receive-brief` (source: RFC-0019
  Follow-on artifacts; sibling spec).
- Product: the adopters served are enterprises whose builds carry a real LLD that
  must conform to an established or reference architecture (source: RFC-0019
  Problem & goals; user confirmation 2026-06-01).
