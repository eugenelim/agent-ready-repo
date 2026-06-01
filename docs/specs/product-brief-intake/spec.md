# Spec: product-brief-intake

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0019, ADR-0009
- **Contract:** none <!-- the brief is a markdown artifact and receive-brief is a skill; neither exposes a machine interface, so new-spec step 4b is skipped -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter who **receives** an externally-authored, multi-feature product brief
(a PRD, a solution handoff) today has no home for it: `core` jumps straight to
the single-feature `new-spec`, so the product→engineering handoff is either
crammed into one oversized spec (breaking the days-to-weeks sizing rule and the
per-spec `work-loop`) or fired through `new-spec` N times by hand with nothing
recording the why, the decomposition, or the coverage.

This feature gives that handoff a home. A new **brief** artifact at
`docs/product/briefs/<slug>.md` (shipped in `core`) records the received
*what/why* — outcome, success metrics, scope/non-goals, appetite — plus a
**coverage map** that answers "is this brief delivered?" and stays current
**automatically**. A new `receive-brief` skill **elicits** the brief's
load-bearing fields conversationally (never rejecting input for
non-conformance), **decomposes** the brief into independently-shippable,
feature-sized slices, and **executes** each through the existing
`new-spec` → `work-loop` pipeline — stamping a `Brief:` back-link on every
derived spec. Success for the adopter: they can take a brief that spans several
features, run one skill, and end up with feature-sized specs in the normal
delivery loop and a coverage map that rolls up from those specs without
hand-maintenance. The repo owns only its own slice; an optional `Epic:` pointer
names an external coordinator when the brief is one part of a cross-repo epic.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Elicit only the **load-bearing** fields (outcome, scope); offer the rest;
  surface gaps. Meet a half-formed brief where it is.
- Decompose by the **shippability test** — independently-shippable,
  independently-testable feature slices — and surface the proposed cut for
  human confirmation before scaffolding any spec.
- Stamp the `Brief:` back-link on every derived spec; in Shape B (story-list)
  also stamp `Satisfies: US-n` on each satisfying acceptance criterion.
- Keep the coverage map **auto-derived** — read child specs' existing `Status:`
  fields via `Brief:` back-links; never hand-write a child's status.

### Ask first

- Before treating an epic-sized story (one too big to fit a single feature-sized
  spec) as a single spec — flag it for splitting and surface.
- Before flagging an outcome in the brief as uncovered by any slice — surface
  the gap rather than silently dropping it.
- Before the auto-rollup lint reads anything beyond existing `Status:` fields and
  `Brief:` back-links (e.g. inferring status from git history) — that is new
  state and needs sign-off.

### Never do

- **Never** build cross-repo coordination (a hub). Own this repo's slice only;
  point upward via the optional `Epic:` pointer.
- **Never** mandate a brief schema or reject input for non-conformance — the
  shape is a guide, not a gate.
- **Never** add a new top-level directory: the brief lives under the existing
  `docs/product/` bucket and the skill under `packs/core/.apm/skills/`. **Never**
  add a cross-pack code import — `core` imports nothing from another pack.
- **Never** hand-maintain the coverage map or write a child spec's status into
  the brief by hand — drift the moment a spec ships is the failure this avoids.

## Testing Strategy

- **Auto-rollup lint logic: TDD.** A pure function reads `Status:` fields,
  follows `Brief:` back-links, rolls each brief's coverage map up from its
  children, no-ops when no brief exists, and reports an un-back-linked spec as
  untracked. It has a compressible invariant — the default for testable logic.
- **Brief template, `receive-brief` skill file, `examples/`, field additions:
  goal-based check.** Verify the files exist at their conventional paths with
  the documented fields, the skill frontmatter passes `lint-skill-spec`, the two
  examples are present and labelled as examples, and `make build-self` projects
  the new core primitives cleanly. No production test asserts what file-presence
  and the existing linters already prove.
- **`receive-brief` elicit / decompose / execute behavior: manual QA.** The skill
  is an LLM workflow; its judgment (elicitation, the decomposition cut) is
  verified by walking the two shipped worked examples end to end and recording
  the result, not by a unit test that would only assert mock shapes.
- **Adopter guides: goal-based check for existence, manual QA for accuracy.**
  The three guide files existing at their Diátaxis paths is a goal-based check;
  whether each reads accurately against the shipped skill + template is a manual
  review recorded in the PR.

## Acceptance Criteria

- [ ] A **brief template** ships as a `core` seed at
  `packs/core/seeds/docs/product/briefs/` carrying the documented fields:
  Outcome, Success metrics, Scope / Non-goals, Appetite, optional User stories,
  optional `Epic:`, and the Spec map (coverage table).
- [ ] The **`receive-brief`** skill ships at
  `packs/core/.apm/skills/receive-brief/SKILL.md` with valid frontmatter that
  passes `tools/lint-skill-spec.py`.
- [ ] `receive-brief`'s documented procedure includes an explicit
  **never-reject / elicit-load-bearing-fields-only** step (insist on outcome +
  scope; offer the rest; surface gaps), verified by a manual-QA walk-through of
  the two examples.
- [ ] `receive-brief` documents **decomposition by the shippability test** and
  **surfaces the proposed cut** for confirmation; in Shape B it groups stories
  into specs and flags any epic-sized story for splitting.
- [ ] `receive-brief` documents the **execute** spine: chain `new-spec` per
  slice, stamp the `Brief:` back-link (and `Satisfies: US-n` on ACs in Shape B),
  hand off to `work-loop`.
- [ ] The **`spec.md` template and `new-spec`** gain an optional `Brief:`
  front-matter field (sibling to `Constrained by:` / `Contract:`); the change is
  additive and specs authored before it stay valid.
- [ ] The optional **`Satisfies: US-n`** acceptance-criterion marker and the
  optional **`Epic:`** brief field are documented in their conventional places.
- [ ] **`examples/`** ships **two** worked briefs — a no-stories outcome brief
  (Shape A) and a story-list brief (Shape B) — each carrying a header that
  clearly labels it an **example demonstrating the shape, not a schema**.
- [ ] An **auto-rollup lint** reads every `docs/specs/*/spec.md` `Status:` field,
  follows `Brief:` back-links, and rolls each brief's Spec map up from its
  children; a brief whose every child spec is `Shipped` reports *delivered*.
- [ ] A brief whose Spec map has **no mapped child specs** reports **not
  delivered** (not vacuously delivered) — an empty rollup is never *delivered*.
- [ ] The lint **no-ops cleanly when no brief exists** — exit 0, no diagnostic —
  verified against this repo (which ships no brief).
- [ ] A spec whose `Brief:` back-link is **missing** shows as **untracked** in
  the brief's map, not as a lint error.
- [ ] The lint is wired into **`make build-check`** (fail-closed) and passes on
  this repo.
- [ ] The **`CONVENTIONS.md` seed amendment** — `briefs/` added to the
  document-hierarchy diagram under `product/`, the `Brief:` field on specs, and
  the `roadmap → brief → spec → AC` altitude — lands in this spec's implementing
  PR (it documents artifacts this spec creates, so it ships atomically with them).
- [ ] **No new top-level directory and no cross-pack import** are introduced; the
  brief lives under `docs/product/`, the skill under `packs/core/.apm/skills/`.
- [ ] **`make build-self`** projects the new core primitives (skill + seed)
  cleanly and `make build-check` is green.
- [ ] Three adopter-facing **guide files exist** under `docs/guides/` at their
  Diátaxis paths — a how-to ("Receive a product brief and decompose it into
  specs"), a reference (brief fields incl. `Epic:` + the spec map; the `Brief:` /
  `Satisfies:` fields), and an explanation ("Why a brief layer"). *(Authored in
  this catalogue repo via `new-guide`, which lives in the non-core
  `user-guide-diataxis` pack; guide authoring is not a capability `core` ships to
  adopters — per RFC-0019's "guides in this catalogue repo" scoping.)*
- [ ] Each of the three guides **reads accurately** against the shipped skill +
  template (manual-QA review recorded in the implementing PR).

## Assumptions

- Process: spec is constrained by RFC-0019 (Accepted 2026-06-01); Decision 3
  (ship in `core`) and the frequency bet (Assumption 1) are settled by the RFC's
  acceptance, not re-litigated here (source: docs/rfc/0019-product-brief-intake.md).
- Process: the brief layer, `Brief:` linkage, and own-the-slice boundary are
  recorded in ADR-0009 (source: docs/adr/0009-product-brief-layer-and-plan-owned-lld.md).
- Technical: the `receive-brief` skill lands at
  `packs/core/.apm/skills/receive-brief/`, alongside the four existing core
  skills (source: `ls packs/core/.apm/skills/`).
- Technical: the brief artifact + examples ship as a `core` seed under
  `packs/core/seeds/docs/product/briefs/`, joining `roadmap.md` / `changelog.md`
  in that bucket (source: `ls packs/core/seeds/docs/product/`).
- Technical: a lint that must reach adopters ships as a skill-bundled script
  (projects to every adapter, like `lint-spec-status.py`), wired into
  `make build-check` in this repo (source:
  `.claude/skills/work-loop/scripts/lint-spec-status.py` precedent; Makefile
  `build-check` runs both the lint and its co-located self-test).
- Technical: no `new-spec` step 4b contract — the brief and the skill expose no
  machine interface (source: new-spec SKILL.md step 4b conditional).
- Process: Open questions 1–3 resolved by the Approver on 2026-06-01 — lint in
  `make build-check` (Q1, overriding the RFC's advisory default), skill name
  `receive-brief` (Q2), and `examples/` ships both shapes clearly labelled (Q3)
  (source: user confirmation 2026-06-01).
- Product: the adopters served are enterprises that separate the product and
  engineering functions and receive externally-authored multi-feature briefs
  (source: RFC-0019 Problem & goals; user confirmation 2026-06-01).
