# Spec: voice-and-microcopy (product-engineering content layer)

- **Status:** Shipped (2026-06-14) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0030 (product-engineering pack), ADR-0019
- **Brief:** none
- **Contract:** none <!-- a pure-markdown skill; exposes no machine interface, so new-spec step 4b is skipped -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product person running the `product-engineering` pack has framed, de-risked,
and decomposed an intent down to a shippable feature — but the pack stops at the
*structure* of the work and says nothing about the **words a user actually
reads** in the UI. Today there is no home in the catalogue for shaping product
intent into copy: `frame-intent` is deliberately solution-independent,
`decompose-intent` cuts structure not content, and the `house-voice-writing-craft`
work is about *documentation prose*, a different audience. This spec adds a fifth
pure-markdown skill, **`voice-and-microcopy`**, that closes that gap: the adopter
characterizes their product's **voice** along a few axes, writes the recurring
UI-state microcopy (**error, empty, button, label**) from blame-free, actionable
formulas, and runs a **content checklist** before copy ships. It is a *method*,
not reference data — fully framework-agnostic, habits-shaped, and consistent with
the pack's "never mandate a schema / SKILL.md under 100 lines / depth in
references" design. Success: the adopter can ask "what should this error say?"
or "characterize our product voice" and get a repeatable discipline that lands
consistent, kind, actionable copy.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.

### Always do

- Keep `SKILL.md` **under 100 lines**; push depth (the voice axes, the per-state
  microcopy formulas, the content checklist) into `references/`, loaded on demand.
- Keep the skill **pure markdown** and **habits-shaped**: `SKILL.md` +
  `references/` + an `assets/` template only. No engine, hook, validator,
  subagent, or seed.
- Ship the voice-chart template in the skill's **`assets/`** (it travels with the
  skill, like `frame-intent`'s `intent-template.md`), copied at runtime to
  `docs/product/voice/<slug>.md` — so the pack stays user-scope and ships no `seeds/`.
- Edit pack content at its **`.apm/` source** under
  `packs/product-engineering/.apm/skills/voice-and-microcopy/`, never a projected
  copy. `make build` re-aggregates `dist/`; the committed root
  `.claude-plugin/marketplace.json` is a self-host projection, refreshed with
  `make build-self FORCE=1` (the pack's skills are not projected to `.claude/`, so
  the only resulting drift is the marketplace version line).
- Bump the pack version in **both** `pack.toml` `[pack] version` **and**
  `.claude-plugin/plugin.json`, and add an `[Unreleased]` changelog entry.
- Add per-pack **Diátaxis guide coverage** for the new skill (a how-to + an index
  entry in the guides README) under `docs/guides/product-engineering/`.
- Frame the voice as **constant**, the tone as **context-flexed** — error copy is
  calm even in a playful product.
- Make every error and empty-state formula **blame-free and actionable** — name
  what happened and the next action; never blame the user.
- Where a content-checklist item overlaps `new-guide`'s `clear-prose.md` (e.g.
  "concise / omit needless words"), **cross-reference it, don't restate it** —
  this skill owns product UI copy, that one owns documentation prose.

### Ask first

- Adding a **sixth skill** or splitting this one — the pack grows one skill at a
  time, each clearing the four charter bars.
- Introducing any **adapter-specific primitive** (agent, hook, command) to the
  pack — it is pure-markdown by design (RFC-0030).
- Changing the behavior of an **existing** product-engineering skill (this spec
  is additive).

### Never do

- Mandate the voice chart as a **schema** or block on a half-filled one — a
  partial chart is normal input (the pack's never-mandate-a-schema rule).
- Add **tech-specific** guidance (a CSS framework, a component library, a
  specific i18n tool) — the method is framework-agnostic.
- Duplicate the `house-voice-writing-craft` **documentation-prose** checklist —
  this skill is about *product UI copy*, a different artifact and audience.
- Write microcopy **examples that blame the user** or dead-end without a next
  action, even as "before" samples without a paired "after".

## Testing Strategy

This is a pure-markdown skill addition; there is no runtime logic to unit-test.
Verification is **goal-based**, exercised by the catalogue's existing gates:

- **Lint / structure:** `make lint-packs` and `tools/lint-agent-artifacts.py`
  validate frontmatter, description cap, and skill structure — goal-based check.
- **Build / aggregation:** `make build` regenerates `marketplace.json` with the
  bumped version — goal-based check (clean `git status`, version present).
- **SKILL.md line budget:** `wc -l` under 100 — goal-based check.
- **Content correctness** (axes present, four UI states covered, checklist
  blame-free + actionable): manual QA against the Acceptance Criteria, confirmed
  by the `adversarial-reviewer` pass.

## Acceptance Criteria

- [x] A new skill exists at
  `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md` with valid
  frontmatter (`name`, `description` with trigger phrases and `Do NOT` cross-refs
  to the sibling skills), under 100 lines.
- [x] `SKILL.md` documents a procedure covering all three deliverables:
  characterize **voice** along axes, write **microcopy** for the recurring UI
  states, and run the **content checklist**.
- [x] A `references/voice-axes.md` defines the voice axes (e.g. humor, formality,
  respect, enthusiasm), how to place a product on them, and the
  **voice-is-constant / tone-flexes-by-context** distinction.
- [x] A `references/microcopy-formulas.md` gives a formula **and** a paired
  before/after for each of the four recurring UI states: **error** (blame-free +
  actionable), **empty state** (orient + invite the first action), **button/CTA**
  (verb + object), **label** (concise, consistent, scannable).
- [x] A `references/content-checklist.md` provides a pre-ship checklist whose
  items include (at least) voice-consistent, blame-free, actionable, concise, and
  terminology-consistent.
- [x] An `assets/voice-chart-template.md` ships a copy-to-`docs/product/voice/<slug>.md`
  template that is explicitly a prompt sheet, not a schema.
- [x] The pack version is bumped in both `pack.toml` and the pack's
  `.claude-plugin/plugin.json`; `dist/` reflects it after `make build` and the
  committed root `.claude-plugin/marketplace.json` after `make build-self FORCE=1`.
- [x] The pack `description` (in `pack.toml` and `plugin.json`) is updated so its
  skill enumeration is no longer stale once the fifth skill lands.
- [x] `docs/product/changelog.md` carries an `[Unreleased] → Added` entry for the
  new skill (with the pack version).
- [x] The pack `README.md` skill table lists `voice-and-microcopy`, and
  `docs/guides/product-engineering/` gains a how-to plus a row under the
  `## How-to` heading of `docs/guides/product-engineering/README.md`.
- [x] `make lint-packs`, `make build`, `make validate`, and
  `tools/lint-agent-artifacts.py` all pass; `git status` is clean.

## Assumptions

- Process: the pack is user-scope-default and **not projected** into this repo's
  `.claude/skills/`. `make build` refreshes `dist/`; the committed root
  `.claude-plugin/marketplace.json` is a self-host projection refreshed by
  `make build-self FORCE=1`, whose only drift here is the version line (source:
  memory `self_host_pack_scope` + `nonprojected_pack_bump_drifts_marketplace`,
  probe of `.claude/skills/` + build-self dry-run).
- Product: adding this fifth skill is authorized despite the v1 spec's "ask first
  before a fourth skill" boundary — `align-value-stream` already cleared that gate
  via `value-stream-meta-repo`; this is the sanctioned next step (source: user
  prompt 2026-06-14).
- Technical: `house-voice-writing-craft` covers **documentation prose**, a
  distinct artifact and audience, so this skill does not duplicate it (source:
  probe of `docs/specs/house-voice-writing-craft/spec.md`).
- Technical: voice axes and UI-state formulas are framework-agnostic (no
  tech-specific content to strip) (source: user prompt + design).
