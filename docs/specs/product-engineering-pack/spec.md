# Spec: product-engineering-pack (v1)

- **Status:** Shipped (2026-06-13) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0030, ADR-0019, ADR-0008 (contract seam reused, not changed)
- **Brief:** none
- **Contract:** none <!-- a pack of markdown skills + seeds; exposes no machine interface, so new-spec step 4b is skipped -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product person — solo dev, product-engineering hybrid, or a PM — installs an
opt-in `product-engineering` pack and gets a lightweight, recognizable discipline
for shaping product **intent** into the specs `core` already builds. They author an
`intent` (an outcome + the opportunity behind it) at whatever **level** they're
working — a capability or a single feature — de-risk its riskiest assumption with a
**choosable prototype approach**, and decompose it one level at a time until the
leaf is a shippable spec. v1 serves the **app/solo, single-component** case: the
whole flow lives in one repo, and a feature-level intent *is* the `core` brief that
`receive-brief` → `new-spec` → `work-loop` already take to delivery — no change to
`core` required, because `receive-brief` always receives a brief for its own repo. Success: the
adopter can run `frame-intent` → `de-risk-intent` → `decompose-intent`, end up with
a brief (or specs) in the normal loop, and never meet a forced schema, a tracking
pyramid, or a tool they must wire up first. The business-unit, cross-component
value-stream layer is explicitly **out of scope** (phase 2, RFC-0030 Appendix A).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.

### Always do

- Keep each skill's `SKILL.md` **under 100 lines**; push depth (the intent model,
  scale-intake, mode tables, projection profiles) into `references/`, loaded on demand.
- Keep the pack **pure markdown** and **habits-shaped**: skills + `references/` + seeds only.
- Anchor skill and field names to **recognized vocabulary** (verb-noun like
  `frame-intent`; `intent`, `outcome`, `opportunity`, `assumption`, `spec`).
- Keep `docs/product/` seeds **placeholder-shaped** (no `RFC-NNNN`, no `agent-ready-repo`),
  so `lint-seeds` passes.
- Treat a feature-level intent at app scale as **a normal `core` brief** — same fields,
  no new field — so `receive-brief` consumes it unchanged.

### Ask first

- Before adding any **fourth skill** to the pack (v1 is exactly three).
- Before changing **`receive-brief`'s behavior** beyond the one additive note + the
  optional brief fields (the brief contract is `core`'s, not the pack's).
- Before introducing a **mode beyond** Scale (global) + per-intent maturity /
  reversibility / prototype-approach.

### Never do

- **Never** ship a hook, an engine, a validator/linter script, or a new subagent in
  this pack (habits, not infrastructure; the 3-reviewer ceiling stands).
- **Never** add a new top-level directory; the pack lives at `packs/product-engineering/`,
  seeds under its `seeds/docs/product/`, guides under the existing `docs/guides/`.
- **Never** make `core` import from or depend on this pack — `core` stands alone.
- **Never** build the cross-component / value-stream / meta-repo layer, live tracker
  API sync, or wire-contract authoring here (phase 2 / existing seams own those).
- **Never** mandate an intent/brief schema or reject a half-formed intent — the
  template is a prompt sheet, not a gate.

## Testing Strategy

This is a content/skill pack (an LLM workflow), like `receive-brief` / `research-pack`,
so there is no compressible-invariant logic to TDD; verification is goal-based for
structure and manual-QA for judgment.

- **Pack scaffold, skill files, seeds, `marketplace.json` registration, core brief
  fields: goal-based check.** Files exist at their conventional paths with the
  documented shape; `tools/lint-skill-spec.py` passes on every `SKILL.md`;
  `lint-packs`, `validate`, `build`, `lint-seeds`, and `pytest` are green; every
  `SKILL.md` is <100 lines. No production test asserts what file-presence + the
  existing linters already prove.
- **Skill behavior — frame/de-risk/decompose judgment, Scale intake, mode routing,
  prototype-approach, brief projection: manual QA.** Walk the shipped worked
  example(s) end to end and record the result; the skills' judgment is not unit-testable
  without asserting mock shapes.
- **Diátaxis guides: goal-based for existence, manual QA for accuracy.** The guide
  files exist at their Diátaxis paths (goal-based); each reads accurately against the
  shipped skills (manual review recorded in the PR).
- **`core` is untouched in v1: goal-based check.** A grep proves the diff adds nothing
  under `packs/core/` and that no pack file makes `core` depend on `product-engineering`;
  the existing brief + `receive-brief` consume an app-scale feature intent as-is.

## Acceptance Criteria

- [x] A new pack ships at **`packs/product-engineering/`** with `pack.toml`,
  `.claude-plugin/plugin.json`, and a `README.md`, and is **registered in
  `.claude-plugin/marketplace.json`** (name `product-engineering`, with a description
  + version), user-scope-default like `architect`/`research`.
- [x] **`frame-intent`** ships at `packs/product-engineering/.apm/skills/frame-intent/SKILL.md`
  (<100 lines, valid frontmatter passing `tools/lint-skill-spec.py`) and documents:
  authoring an `intent` at any level (outcome incl. a guardrail + opportunity);
  the **Scale-resolution intake** (infer → confirm → ask) stamping `scale:`; and the
  per-intent **maturity** flag gating current-state inputs (process map / journey map).
- [x] **`de-risk-intent`** ships (same constraints) and documents: reversibility triage
  (one-way/two-way door); the riskiest assumption fronted by "what would have to be true";
  a **predeclared kill condition in the test's own currency**; and the **choosable
  prototype-approach** (`prototype-led` ↔ `validate-first`) baked into its behavior,
  defaulted by reversibility, overridable, ending in a survive/kill verdict.
- [x] **`decompose-intent`** ships (same constraints) and documents: recursive
  decomposition (next level down — child intents, or specs/slices at the leaf);
  **the brief as a feature-intent projected onto a repo**; and **one-way** tracker
  projection profiles (`none` / Linear-lean / Jira-Align-deep) with no live API.
- [x] An **`intent` artifact template** ships as a seed at
  `packs/product-engineering/seeds/docs/product/intents/_template.md` with the documented
  fields (level, outcome incl. input/lagging/guardrail, opportunity, assumptions,
  decomposition/children, optional parent-intent), placeholder-shaped (`lint-seeds` passes).
- [x] An **example** worked intent ships under a skill dir at
  `packs/product-engineering/.apm/skills/frame-intent/examples/` (app-scale feature
  intent → `core`-shaped brief), clearly labelled an example demonstrating the shape,
  not a schema — following the `receive-brief` examples precedent (skill content that
  travels with the skill, not a seed projected into the adopter's `docs/product/`).
- [x] **v1 introduces no change to `core`.** A feature-level intent at app scale *is* a
  normal `core` brief (no new field — `receive-brief` is level-agnostic by construction
  and always receives a brief "for its own repo"), so `receive-brief` consumes it
  unchanged. Brief-level provenance (`parent-intent:`, for a BU cross-repo slice to name
  its parent intent) is a **phase-2 concern**, not v1. Grep proves `core` is untouched and
  imports nothing from the pack.
- [x] **Diátaxis guides** exist under `docs/guides/` at their quadrant paths — an
  **explanation** ("the intent tree & level-agnostic shaping"), a **how-to** ("shape a
  feature in an app repo"; the BU/cross-component how-to is a forward-flagged stub since
  BU is phase 2), and a **reference** (intent fields, modes, projection profiles) — each
  reading accurately against the shipped skills (manual-QA recorded in the PR).
- [x] **No hook / engine / validator / subagent / new top-level dir** is introduced; the
  pack is pure markdown; `core` does not depend on it (grep-verified).
- [x] A **`docs/product/changelog.md` `[Unreleased]`** entry records the new pack.
- [x] `make lint-packs`, `make validate`, `make build`, `lint-seeds`, `lint-skill-spec`,
  and the package `pytest` suite are **green**; every shipped `SKILL.md` is <100 lines.

## Assumptions

- Process: spec is constrained by RFC-0030 (Accepted 2026-06-13) and ADR-0019 (Accepted) — the design is settled there, not re-litigated here (source: docs/rfc/0030-product-engineering-pack.md, docs/adr/0019-product-intent-ontology-and-brief-projection.md).
- Process: a new pack ships via a spec (source: docs/specs/research-pack/, docs/specs/converters-pack/); the charter caps reviewers at three and forbids infra-shaped additions (source: docs/CHARTER.md §Principles).
- Technical: pack shape is pack.toml + .claude-plugin/plugin.json + .apm/skills/ + seeds/ + README (source: packs/architect/, packs/research/ trees).
- Technical: packs register in .claude-plugin/marketplace.json as {name, description, version}; user-scope-default packs aggregate there but are not projected to this repo's working tree, so the gate is lint-packs + validate + build + pytest, not build-self (source: .claude-plugin/marketplace.json; memory project_self_host_pack_scope).
- Technical: SKILL.md <100 lines with depth in references/ is the house pattern (source: packs/architect/README.md §Design principles).
- Technical: pack seeds must be placeholder-shaped — lint-seeds forbids RFC-NNNN refs and the literal agent-ready-repo (source: tools/lint-seeds.py).
- Technical: a feature-level intent at app scale maps onto the existing core brief shape (Slug/Received/Owner/Epic/Outcome/Success metrics/Scope-Non-goals/Appetite/User stories/Spec map) with no new field, so v1 adds nothing to core (source: packs/core/seeds/docs/product/briefs/_template.md).
- Technical: contract maturity reuses the existing spec-stage Contract: seam; this pack adds no contract machinery (source: docs/adr/0008-contract-authoring-seam.md, new-spec step 4b).
- Technical: new-guide (user-guide-diataxis pack) authors guides in this catalogue repo; guide authoring is not a capability core ships (source: docs/specs/product-brief-intake/spec.md guide ACs).
- Product: adopters are PM + product-eng hybrid + solo/owner; v1 = app/solo + single-component, BU-scale meta-repo deferred to phase 2 (source: user confirmation 2026-06-12; RFC-0030).
- Process: `receive-brief` is level-agnostic by construction — it always receives a brief for its own repo — so v1 changes nothing in `core`; brief-level provenance (`parent-intent:`) is a phase-2 BU concern, not v1 (source: user direction 2026-06-13, refining RFC-0030 §5 / ADR-0019 corollary 2).
