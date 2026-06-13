# Spec: value-stream-meta-repo (product-engineering phase 2)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0030 (decision #9 + Appendix A), ADR-0022, ADR-0019, ADR-0008 (contract seam reused, not changed), RFC-0016 (currency/doc-drift discipline), RFC-0020 (`reference.md` architect seam)
- **Brief:** none
- **Contract:** none <!-- a pack of markdown skills + seeds; exposes no machine interface, so new-spec step 4b is skipped -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A business-unit, value-stream, or product-org adopter — already running the
`product-engineering` pack at app scale — installs the same pack and gets the
**cross-component** layer: a discipline for shaping a capability that fans out
across **many component repos**, without inventing a runtime coordination hub.
They stand up a **value-stream meta-repo** (a coordinating repo with no app code)
that holds the cross-component intents, a **Backstage**-anchored
System/Component/API catalog, the canonical shared contracts (or a reference to
where they live), the C4/bounded-context architecture, and a **cross-component
delivery rollup**. A de-risked feature intent is **sliced per component** into one
`core` brief per repo, each carrying a `parent-intent:` provenance pointer and a
**version-pinned contract reference plus a read-only courier snapshot**; each
brief crosses into its component repo where `receive-brief` → `new-spec` →
`work-loop` already take it the rest of the way. As the slices ship, the meta-repo
**rolls up** "is the whole feature intent delivered across all components?" by
aggregating each repo's own (auto-derived) brief coverage.

Success: the adopter can (a) stand up and keep current a meta-repo via a new
**`align-value-stream`** skill; (b) slice a feature intent into per-component
briefs via `decompose-intent`'s business-unit branch, which reads the catalog and
contract references from the meta-repo and seeds the rollup; (c) reference a shared
contract by version with a courier snapshot, never forking it; and (d) read a
whole-feature rollup — all in **pure markdown**, with **no live API**, **no runtime
hub**, **no validator**, and **no new subagent**, and with the **hard limits**
(no atomic cross-repo commit, no shared release train, the rollup is a snapshot)
stated honestly. The only `core` change is one additive optional brief field
(`parent-intent:`). Scale is resolved **once** at the first `frame-intent` intake
and carries through; `frame-intent`/`de-risk-intent` are otherwise unchanged.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.

### Always do

- Keep each `SKILL.md` (the new `align-value-stream`, the extended
  `decompose-intent`) **under 100 lines**; push depth (Backstage ontology, the
  shared-contract handoff, the rollup mechanics, catalog currency) into
  `references/`, loaded on demand.
- Keep the pack **pure markdown** and **habits-shaped**: skills + `references/` +
  seeds only. Reuse Backstage's ontology, the existing `Contract:` seam,
  `receive-brief`'s per-repo coverage, and `monorepo-extras` for structuring —
  extend, don't fork.
- Anchor every cross-component term to **recognized vocabulary**: Backstage
  Domain/System/Component/API + `providesApi`/`consumesApi`; provider-contract-first
  / CDC; value stream / coordinating repo (Team Topologies).
- Make the new skills **cross-reference each other**: `decompose-intent`'s BU
  branch reads the catalog/contract references from `align-value-stream` and seeds
  the rollup; `align-value-stream` documents that the slices it rolls up come from
  `decompose-intent`.
- Keep all seeds **placeholder-shaped** (no `RFC-NNNN`, no `agent-ready-repo`), so
  `lint-seeds` passes; register each new seed in `tools/lint-seeds.py`.
- Treat the per-component slice as a **normal `core` brief** plus the one additive
  optional `parent-intent:` field — so `receive-brief` consumes it unchanged and
  never interprets the field.
- State the **hard limits** (no atomic cross-repo commit, no shared release train,
  the rollup is a snapshot not a live feed) explicitly in the skills and the guide.

### Ask first

- Before adding any **skill beyond** the one new `align-value-stream` (this phase
  adds exactly one new skill + the `decompose-intent` BU branch).
- Before changing **`receive-brief`'s behavior** beyond the single additive
  optional `parent-intent:` field + a one-line note (the brief contract is
  `core`'s).
- Before changing the **contract-authority decision** from *elicited, default
  meta-repo, reference-by-version + courier snapshot* (the location is org-specific
  by ADR-0022 part 3).
- Before introducing a **mode beyond** the existing Scale (global) + per-intent
  maturity / reversibility / prototype-approach.

### Never do

- **Never** ship a hook, an engine, a **validator/linter script**, a **runtime
  hub / live-poll service**, a **live tracker or coverage API**, or a new subagent
  in this pack (habits, not infrastructure; the 3-reviewer ceiling stands).
- **Never** add a new **top-level directory**; the pack lives at
  `packs/product-engineering/`, seeds under its `seeds/`, guides under the
  existing `docs/guides/`.
- **Never** make `core` import from or depend on this pack — `core` stands alone;
  `parent-intent:` is additive and never interpreted by `receive-brief`.
- **Never** **attach a contract as authority** (copy it into the brief) — reference
  by version, carry a read-only courier snapshot only.
- **Never** **re-author** per-repo catalog or coverage in the meta-repo — federate
  (reference each repo's `catalog-info.yaml` and its own coverage).
- **Never** **duplicate** the monorepo-vs-polyrepo *structuring* guidance that
  lives in `monorepo-extras` — meet it only at "where the shared contract lives."
- **Never** mandate a schema or reject a half-formed intent/brief/catalog entry —
  the templates are prompt sheets, not gates.

## Testing Strategy

This is a content/skill pack (an LLM workflow), like v1 / `receive-brief` /
`research-pack`, so there is no compressible-invariant logic to TDD; verification
is goal-based for structure and manual-QA for judgment.

- **Pack files, the new/extended skills, seeds, `marketplace.json` re-aggregation,
  the `core` brief field, version bump: goal-based check.** Files exist at their
  conventional paths with the documented shape; `tools/lint-skill-spec.py` passes
  on every `SKILL.md`; `lint-packs`, `validate`, `build`, `lint-seeds`, and
  `pytest` are green; `make build-self FORCE=1` re-aggregates `marketplace.json`
  with `product-engineering` at the new version; every `SKILL.md` is <100 lines.
  No production test asserts what file-presence + the existing linters already prove.
- **Skill behavior — meta-repo setup, catalog, contract-authority elicitation,
  per-component slicing, the rollup: manual QA.** Walk a worked example end to end
  (a capability intent → sliced per-component briefs → a rollup) and record the
  result; the skills' judgment is not unit-testable without asserting mock shapes.
- **The new skills cross-reference correctly: goal-based check.** A grep proves
  `decompose-intent`'s BU branch names `align-value-stream` (catalog/contract read +
  rollup seed) and that `align-value-stream` names `decompose-intent` as the slice
  source.
- **`core` is touched only by the additive `parent-intent:` field: goal-based
  check.** A grep proves the only `packs/core/` diff is the optional `parent-intent:`
  brief-template field (+ a one-line `receive-brief` note), that no pack file makes
  `core` depend on `product-engineering`, and that `receive-brief` still consumes a
  brief unchanged.
- **No infrastructure is introduced: goal-based (structural) check.** A grep of the
  pack tree confirms **no `hooks/`, no `agents/`, no `*.py` validator/poller**, and
  that the diff adds **no new top-level directory**.
- **Diátaxis guide: goal-based for existence, manual QA for accuracy.** The phase-2
  how-to (the v1 forward-flagged stub, now filled) exists at its quadrant path and
  reads accurately against the shipped skills; the reference guide is updated.

## Acceptance Criteria

- [x] A new skill **`align-value-stream`** ships at
  `packs/product-engineering/.apm/skills/align-value-stream/SKILL.md` (<100 lines,
  valid frontmatter passing `tools/lint-skill-spec.py`) and documents: the
  **value-stream meta-repo** as a coordinating repo with no app code; the
  **Backstage** Domain→System→Component→API catalog, **federated** (references each
  component repo's `catalog-info.yaml`, never re-authored); the **contract-authority
  decision** (explain in plain language → default meta-repo → list alternatives →
  elicit → reference-by-version + courier snapshot regardless of location); the
  `providesApi`/`consumesApi` provider/consumer roles + compatibility direction; the
  **C4/bounded-context architecture** living here (the `architect` seam); and the
  **cross-component rollup**. Its anti-patterns refuse a **runtime hub / live API**,
  **re-authoring** federated data, and **attach-as-authority** contracts.
- [x] **`decompose-intent` gains the business-unit slicing branch** (still <100
  lines): at `business-unit` Scale a de-risked feature intent is sliced into **one
  `core` brief per affected component**, each carrying an optional **`parent-intent:`**
  pointer, a **version-pinned contract reference + courier snapshot**, and a
  provider/consumer role; the branch **reads the catalog and contract references
  from `align-value-stream`** and **seeds the rollup rows**. The v1 app-scale path is
  unchanged. (De-stubbing every "phase 2 / out of scope / deferred" mention of the BU
  path now that it ships — across `decompose-intent`'s `SKILL.md` +
  `recursive-decomposition.md` and `frame-intent`'s `scale-intake.md` — is a
  construction check in plan T4, not a contract clause. `tracker-projection.md`'s
  *live-API* deferral is **not** a BU stub and stays.)
- [x] **`core`'s brief template gains an optional `parent-intent:` field** at
  `packs/core/seeds/docs/product/briefs/_template.md` — additive, placeholder-shaped,
  documented as the product-pack intent the slice was projected from, **distinct from
  `Epic:`** (external coordinator) — plus a one-line `receive-brief` note that the
  field is an optional upward pointer it carries but never interprets. **No other
  `core` change**; `core` imports nothing from the pack (grep-verified).
- [x] A **cross-component rollup** template ships **with the `align-value-stream`
  skill** at
  `packs/product-engineering/.apm/skills/align-value-stream/assets/rollup-template.md`
  — a **markdown** table (one row per component slice → its brief → status snapshot
  + pointer). The skill copies it to `docs/product/rollups/<slug>.md` at runtime.
  <!-- enriched-pack-manifest (2026-06-13): relocated from a repo `seeds/docs/product/rollups/`
  seed to a skill asset (and de-registered from `tools/lint-seeds.py`). A pack shipping
  `seeds/` cannot declare user scope (RFC-0004 Rail A), which contradicted product-engineering's
  user-scope skills; carrying the template as a skill asset realizes RFC-0030's "skills travel"
  intent. --> (The capability intent at the
  meta-repo's top reuses the `frame-intent` skill's `intent-template.md` asset — no separate template. The
  federated **`catalog-info.yaml`** is Backstage-native and lives at each component
  repo's root, outside the "seeds land in `docs/product/`" convention, so it ships
  as a **sample in `align-value-stream/references/`**, not a projected seed.) The
  rollup template states how a row whose authoritative source is **absent** — a
  component repo with no `catalog-info.yaml` or no auto-derived coverage yet — is
  represented: an explicit **`unknown / not-yet-catalogued`** status, **never**
  silently counted as delivered (so the "AND across rows" answer is never falsely
  green).
- [x] **`align-value-stream` references** ship under its skill dir documenting, at
  depth: the **Backstage ontology** + federation (including a worked
  `catalog-info.yaml` **sample** in `references/backstage-ontology.md` — the
  federated entity shape, since it is not a projected seed); the **shared-contract
  handoff**
  (reference-by-version, courier snapshot, provider-contract-first default +
  per-relationship CDC override, `providesApi`/`consumesApi`, compatibility
  direction); the **cross-component rollup** mechanics (snapshot + pointer, AND
  across rows, no runtime hub); and **catalog currency** (the RFC-0016 doc-drift
  discipline). The `monorepo-extras` seam is **referenced, not restated**.
- [x] **The two new skills cross-reference each other** (grep-verified):
  `decompose-intent`'s BU branch names `align-value-stream`; `align-value-stream`
  names `decompose-intent` as the source of the slices it rolls up.
- [x] **The hard limits are stated honestly** in the skills and the guide: **no
  atomic cross-repo commit**, **no shared release train**, and the rollup is a
  **snapshot, not a live feed**.
- [x] **The Diátaxis guides are updated**: a new phase-2 **how-to** page ships at
  `docs/guides/how-to/<problem-named>.md` ("run a capability across a value stream /
  many component repos") reading accurately against the shipped skills; the v1
  **forward references** in `docs/guides/how-to/shape-a-feature-intent.md` — **both**
  the header blurb ("that path is phase 2") and the footer note ("specified but not
  yet shipped — see RFC-0030 Appendix A") — are updated to point at the new page, with
  the stale "phase 2" / "not yet shipped" wording removed; and the
  **reference** guide (`docs/guides/reference/intent-fields-and-modes.md`) gains the
  BU-scale fields (`parent-intent:`, the rollup, the catalog). Manual-QA recorded in
  the PR.
- [x] **The pack version bumps** to `0.2.0` (`pack.toml` + `.claude-plugin/plugin.json`),
  the README's "what's NOT in this pack" moves the BU cross-component layer **out of
  "phase 2"** (and into what ships), and `make build-self FORCE=1` re-aggregates
  `.claude-plugin/marketplace.json` to the new version.
- [x] **No hook / engine / validator / poller / live API / subagent / new top-level
  directory** is introduced; the pack stays pure markdown (grep-verified).
- [x] A **`docs/product/changelog.md` `[Unreleased]`** entry records the phase-2 layer.
- [x] `make lint-packs`, `make validate`, `make build`, `tools/lint-seeds.py`,
  `tools/lint-skill-spec.py`, the package `pytest` suite (incl. the inner
  `packages/agentbundle/agentbundle/build/tests/` root), and `make build-self FORCE=1`
  are **green**; every shipped `SKILL.md` is <100 lines; the spec is added to
  `docs/specs/README.md`.

## Assumptions

- Process: phase 2 is pre-accepted by RFC-0030 (decision #9 + Appendix A) and deferred by ADR-0019; it is recorded in ADR-0022, so no new RFC is needed (source: docs/rfc/0030-product-engineering-pack.md §9/§A; docs/adr/0019-product-intent-ontology-and-brief-projection.md §Consequences; docs/adr/0022-value-stream-meta-repo-cross-component-layer.md).
- Process: a phase-2 ADR (ADR-0022) records the durable decisions ADR-0019 left open — the meta-repo, the contract-authority location, and `parent-intent:` (source: docs/adr/0019 §Consequences "Neutral/to revisit"; docs/adr/ ended at 0019 before this).
- Technical: this extends the existing `product-engineering` pack (version 0.1.0 → 0.2.0, minor); user-scope-default, not projected to the working tree, so `marketplace.json` re-aggregates via `make build-self FORCE=1` (source: packs/product-engineering/pack.toml; memory project_self_host_pack_scope + v1 build learnings).
- Technical: phase 2 adds an optional `parent-intent:` field to `core`'s brief template — additive, distinct from the existing `Epic:` pointer; ADR-0019 corollary 2 named it the one ever-needed addition (source: docs/adr/0019 Decision part 2; packs/core/seeds/docs/product/briefs/_template.md has `Epic:`, no `parent-intent:`).
- Technical: new seeds register in tools/lint-seeds.py REQUIRED_PLACEHOLDERS and must be placeholder-shaped (source: tools/lint-seeds.py:81-105; v1 build learnings).
- Technical: Backstage ontology = Domain→System→Component→API with relations `providesApi`/`consumesApi` (source fields `spec.providesApis`/`spec.consumesApis`) — author-verified in RFC-0030 (source: docs/rfc/0030 §A.2).
- Technical: `receive-brief` already owns a per-repo coverage rollup (`scripts/lint-brief-coverage.py`) answering "is this repo's brief delivered?"; the cross-component rollup aggregates above it and no single repo can produce it (source: packs/core/.apm/skills/receive-brief/SKILL.md §Coverage; docs/rfc/0030 §A.5).
- Technical: the wire-contract seam is the existing `contracts` pack (`api-contract`/`event-contract`) reused at the spec stage; phase 2 adds no contract machinery and stays behavioral (source: docs/rfc/0030 §6; docs/adr/0008-contract-authoring-seam.md; packs/contracts/.apm/skills/).
- Technical: monorepo-vs-polyrepo structuring lives in `monorepo-extras` (`new-package`); the two packs meet only at "where the shared contract lives" (source: packs/monorepo-extras/.apm/skills/new-package; docs/rfc/0030 §A.6).
- Process: the contract-authority *location* is org-specific and elicited at use time (default meta-repo); the reference-by-version + courier-snapshot *shape* is the constant (source: docs/rfc/0030 open question #2; user direction 2026-06-13).
- Design: the new skill is named `align-value-stream` and owns the meta-repo's shared artifacts (catalog, contracts, architecture, rollup) unified by currency; the rollup is folded into it rather than a 5th skill; `decompose-intent` calls it and it calls back (source: user confirmation 2026-06-13).
- Design: the catalog is federated (per-repo `catalog-info.yaml`); the rollup is a markdown snapshot with a pointer (no runtime hub, no YAML-that-invites-a-validator); the architecture `reference.md` lives in the meta-repo (source: user confirmation 2026-06-13; A.7 resolutions).
- Product: the phase-2 adopter is a BU / value stream / product org running one coordinating meta-repo that fans work out to many component repos (polyrepo) (source: user confirmation 2026-06-13).
