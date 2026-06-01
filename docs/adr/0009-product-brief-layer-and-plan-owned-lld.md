# ADR-0009: A product-brief layer sits between roadmap and spec; the low-level design lives in the plan with a derived (never baked) stack

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-01
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0019 (product-brief intake + LLD-aware spec/plan — the accepted proposal these decisions record); RFC-0020 (reference-architecture foundation — the LLD reads `reference.md` when present); RFC-0021 (greenfield inception — produces the first brief); `product-brief-intake` spec; `lld-aware-spec-plan` spec; ADR-0008 (contract authoring seam — the prior "agnostic, convention-first core seam" precedent); `docs/CHARTER.md` §Principles

## Context

`core` (always installed) ships spec-driven delivery: `new-spec` authors one
`spec.md` + `plan.md` pair, `work-loop` builds it. `CONVENTIONS.md` §4 sizes a
spec at **one feature, days-to-weeks**, and `work-loop` runs **per spec**.

Two gaps follow from that shape, both sharpened where an organization separates
the product and engineering functions — i.e. in the enterprise:

1. **No inbox for the product→engineering handoff.** Enterprise adopters don't
   author all their own work; they *receive* an externally-authored,
   multi-feature product brief (a PRD, a solution handoff). A multi-feature
   brief is months across features — it provably cannot be one spec without
   breaking both the sizing rule and the per-spec `work-loop`. So any
   multi-feature input structurally forces a layer *above* the spec, and core
   ships none. The adopter either crams the brief into one oversized spec or
   fires `new-spec` N times by hand with nothing recording the why, the
   decomposition, or the coverage.
2. **No home for the low-level design.** An enterprise build needs an LLD —
   screen states, component decomposition, data model, sequence, resilience,
   security, deployment sequencing. The plan is the natural design step, but
   core's `plan.md` has no LLD section, and deployment sequencing in particular
   has no home anywhere today.

Three constraints bound any answer. (a) `core` must stay **universal** across
tech stacks (Charter Principle 1) — no stack may be baked into a shipped
template. (b) Changes to `spec.md` / `plan.md` are the **widest blast radius**
in the repo: those templates are the contract for *every* adopter and the
self-host projection, so even an additive change touches everyone. (c) The
**compose-around-core** model holds — packs don't import each other.

## Decision

> We add a product **brief** artifact at a new altitude **between roadmap and
> spec** — `docs/product/briefs/<slug>.md`, shipped in `core` — that receives an
> externally-authored multi-feature brief, owns only **this repo's slice**, and
> is decomposed and executed through the existing `new-spec` → `work-loop`
> pipeline; and we locate the **low-level design in `plan.md`** (a stack-neutral
> `## Design (LLD)` section), with stack-specific content **derived** at
> authoring time and **never baked** into the template.

Specifically:

1. **Brief altitude + carrier.** A new `brief` artifact (not an extension of
   roadmap, backlog, or the spec) holds the received *what/why* (outcome,
   success metrics, scope/non-goals, appetite) and a **coverage map** whose
   status is **auto-rolled-up from its child specs** by a lint — so "is this
   brief delivered?" stays answerable with no hand-maintenance. The brief slots
   between roadmap (which references briefs) and the specs (which roll up to it).
2. **Own-the-slice scope.** We ingest only this repo's portion and point upward
   to an external coordinator (Jira, GitHub Projects, an integration repo) via
   an **optional `Epic:`** pointer carried in from the brief. We do **not** build
   a cross-repo coordination hub.
3. **Linkage by reference, not nesting.** A derived spec references its brief
   through a new `Brief:` front-matter field; an optional `Satisfies: US-n`
   marker traces an acceptance criterion to a user story. Specs stay flat under
   `docs/specs/<feature>/`; a spec may predate its brief. This mirrors RFC-0017's
   many-specs-reference-one-contract precedent and keeps `Brief:` (product
   provenance) distinct from `Constrained by:` (governance constraints).
4. **LLD in the plan, contract in the spec.** `plan.md` gains a `## Design (LLD)`
   section built from **ten stack-neutral categories**, **shape-selected** and
   optional; the existing `## Rollout` expands to cover infra / external-system
   integration / deployment sequencing. `spec.md` gains only a light, stack-neutral
   `Shape:` field and AC guidance (UI state/trigger/outcome as an AC; NFRs with a
   pass/fail bar as ACs) — **no LLD body migrates into the spec**; it stays the
   contract. No separate `design.md` tier.
5. **Stack derived, not baked.** The LLD's stack-specific content is **derived**:
   read `docs/architecture/reference.md` (RFC-0020) and conform to it **when
   present**; otherwise degrade to established-repo detection and/or brief-intake
   context, eliciting gaps. The template ships only the universal category names.
   This check is the seam that lets RFC-0019 and RFC-0020 land in either order.
6. **Pack = `core`; template changes additive-only.** The handoff and the LLD
   categories are stack-agnostic, so they belong in the universal base. Every
   `spec.md` / `plan.md` change is additive — a new optional field or section,
   nothing removed or renamed — so specs and plans authored before this change
   stay valid and the self-host projection re-renders cleanly.

## Consequences

**Positive:**
- The product→engineering handoff gains a home; coverage is answerable and stays
  current automatically (the brief is a live tracker, not a stale document).
- The enterprise LLD gains a home in the plan, including deployment sequencing,
  which had none.
- The templates stay universal — no stack is shipped, so no adopter inherits a
  stack they don't use.
- The pack model holds: convention-coupling (the `Brief:` back-link, the
  `contracts/`-style location convention for `briefs/`), no cross-pack imports.
- Both capabilities land standalone via the degrade path and conform to a
  reference architecture automatically the day `docs/architecture/reference.md`
  appears (RFC-0020), in either landing order.

**Negative:**
- `core` grows past "just specs": one more artifact, one more skill
  (`receive-brief`), and a new auto-rollup lint in the gate set.
- The `spec.md` / `plan.md` change touches *every* adopter and the self-host
  projection; the additive-only rule bounds but does not erase that blast radius.
- The frequency bet — that enough adopters receive externally-authored
  multi-feature briefs to earn a *core* primitive (Charter Principle 4) — is
  **not settled by a spike**; it is accepted on the Approver's judgment. The
  *structural* claim (a multi-feature brief cannot be one spec) is settled; the
  *frequency* claim is the open product call and is kept separate.

**Neutral / to revisit:**
- Delta-expressed / always-living specs (OpenSpec, Intent) were considered and
  **deferred** — they would reshape `spec.md` for every adopter and conflict with
  the deliberate "frozen after ship" stance; a future RFC if pursued, not a rider.
- A portfolio / multi-brief rollup layer above the brief is out of scope; one
  received brief is the ceiling here.
- The auto-rollup lint runs in `make build-check` (fail-closed local gate) per
  the `product-brief-intake` spec's resolution of RFC-0019 Open Q1; it must no-op
  cleanly where no brief exists.

## Alternatives considered

- **Build a cross-repo coordination hub** — duplicates Jira / GitHub Projects and
  breaks the single-repo install model. Rejected; we own the slice and point up.
- **Carry the brief in `roadmap.md` / `backlog.md`, or absorb it into the spec** —
  roadmap is a flat forward list, backlog is open-items-by-spec, and a spec is
  single-feature; none can hold a multi-feature why + a closed→delivered coverage
  map. Rejected for a dedicated artifact.
- **Ship in `governance-extras` or a new `product` pack** — `governance-extras` is
  not installed by every adopter, which recreates the exact gap this closes; a
  whole pack for one artifact + one skill is heavier and fragments the product
  surface `core` already ships. Rejected for `core`.
- **Mandate a fixed brief schema** — rejects real-world briefs that arrive
  half-formed and contradicts the elicit intent. Rejected for elicit + example.
- **Nest specs under the brief directory** — couples a spec to exactly one brief
  and changes `new-spec`'s flat path. Rejected for reference via `Brief:`.
- **A separate `design.md` tier, or LLD inside the spec** — a new per-spec
  artifact and review gate for every adopter, or conflation of contract with
  design that bloats the single-feature spec. Rejected for plan-owned LLD.
- **Bake a stack into the template, or make every adopter hand-author a stack
  template** — violates universality, or imposes setup on everyone. Rejected for
  derive-with-elicit-fallback.
- **Do nothing** — keeps `core` lean but leaves the most common enterprise
  scenario ("an architect handed us a design, now build it") with no supported
  path and the build that follows with no place to record its design.

## References

- RFC-0019 — Decisions 1–9 (scope, carrier, pack, input posture, user stories,
  linkage, coverage tracking, LLD locus, stack source) and the accepted
  frequency caveat (Assumption 1).
- RFC-0020 — the `docs/architecture/reference.md` foundation the LLD conforms to
  when present.
- `docs/specs/product-brief-intake/spec.md` and `docs/specs/lld-aware-spec-plan/spec.md`
  — the implementation contracts.
- ADR-0008 — the prior "agnostic, convention-first seam in `core`" precedent this
  decision follows for `Brief:` linkage and `briefs/` location convention.
