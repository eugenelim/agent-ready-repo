# Spec: design-craft-pack (v1)

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0033, RFC-0007 (the user-scope refusal-rails + grep-enforcement pattern), RFC-0004 (install-scope-per-pack, reused not changed), RFC-0032 (skill-vs-agent ceiling reading, reused not changed)
- **Brief:** none
- **Contract:** none <!-- a pack of pure-markdown skills + a shared checklist; exposes no machine interface, so no contract type applies -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An interaction/visual designer — solo, a design-eng hybrid, or one of a design
team — installs an opt-in, user-scope `design-craft` pack and gets a lightweight,
recognizable, **framework-agnostic** discipline for the core design-craft loop:
**direct** (aesthetic direction) → **systematize** (design-system foundations) →
**structure** (layout & information architecture) → **critique** (heuristic
review). The pack ships **four skills** — `aesthetic-direction`,
`design-system-foundations`, `layout-and-information-architecture`,
`design-critique` — plus a shared **`quality-floor` checklist** (handle-all-states
+ accessibility floor + "motion communicates state, honor reduced-motion"),
referenced by the authoring skills and applied by `design-critique`. Every skill
is stripped to portable **method**: zero React/Vue/Tailwind/CSS, no Framer Motion,
and **no static reference-data tables** (px/ms/hex/easing/breakpoint values, fixed
token sets) — it ships the method to *derive* those values, never the values.
Success: the adopter can run any of the four disciplines, produce durable
**design-intent** artifacts that live in the repo and steer the UI build (an
aesthetic-direction doc, a token-taxonomy rationale, an IA), and never meet a
stack assumption, a values cheat-sheet, or a tool they must wire up first. The
pack is **habits, not infrastructure**: no hooks, no engine, no validators *in the
pack*, no `work-loop` reviewer subagents. The `design-craft` `design-reviewer`
subagent (the RFC-0032 twin) is explicitly **out of scope** for v1 (RFC-0033
OQ#2).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep each skill's `SKILL.md` **under 100 lines**; push depth (the interrogation
  sequence, the derivation method, the heuristic set, the `quality-floor`
  checklist) into `references/`, loaded on demand.
- Keep the pack **pure markdown** and **habits-shaped**: skills + `references/` +
  skill `assets/` only.
- Keep every skill **framework-agnostic** — portable method only, per RFC-0033's
  two guardrails: **Guardrail A** (point to external standards — WCAG, the W3C
  Design Tokens interchange shape — never reprint a ratio/px/hex/ms table) and
  **Guardrail B** (concepts, not platform primitives — wayfinding as orientation,
  never ARIA roles or CSS grid; motion as the reduced-motion *principle*, never a
  `@media` query).
- Anchor skill and field names to **recognized vocabulary** (verb-noun like
  `aesthetic-direction`; `aesthetic direction`, `design tokens`, `information
  architecture`, `heuristic evaluation`, `severity rating`).
- Carry any template (e.g. the aesthetic-direction doc) as a **skill asset** the
  skill copies into the repo at runtime, so the template travels user-scope and
  the filled doc lands repo-scope with no scope conflict.

### Ask first

- Before adding any **fifth skill** to the pack (v1 is exactly four).
- Before promoting the agnosticism stack-token lint from a **pack-scoped check**
  (a grep over `packs/design-craft/`) into a **repo-wide convention** — that is a
  separate RFC, decided on its own merits (RFC-0033 Follow-on artifacts).
- Before changing the `quality-floor` checklist's contents beyond the three lines
  RFC-0033 names (all-states, accessibility floor, reduced-motion principle).

### Never do

- **Never** ship a hook, an engine, a validator/linter script *inside the pack*,
  or a `work-loop` reviewer subagent in this pack (habits, not infrastructure; the
  three-reviewer ceiling stands — RFC-0033 §4). The agnosticism lint is a
  **catalogue-governance tool under `tools/`**, not a pack primitive.
- **Never** ship a **`seeds/`** directory — a pack with non-empty `seeds/` cannot
  declare `"user" ∈ allowed-scopes` (RFC-0004 Rail A); templates ride as skill
  `assets/`.
- **Never** ship any **stack specifics or a values table** — no React/Vue/
  Tailwind/CSS, no animation library, no px/ms/hex/easing/breakpoint table, no
  fixed token set (the charter's "not a framework that picks your tech stack").
- **Never** add a **new top-level directory**; the pack lives at
  `packs/design-craft/`, its guides under the existing `docs/guides/`, its lint
  under the existing `tools/`.
- **Never** make `core` (or any other pack) import from or depend on this pack —
  `design-craft` stands alone.

## Testing Strategy

This is a content/skill pack (an LLM workflow), like `product-engineering` /
`research`, so there is no compressible-invariant logic to TDD; verification is
goal-based for structure and the agnosticism floor, and manual-QA for judgment.

- **Pack scaffold, skill files, the shared checklist, `marketplace.json`
  registration: goal-based check.** Files exist at their conventional paths with
  the documented shape; `tools/lint-skill-spec.py` passes on every `SKILL.md`;
  `lint-packs`, `validate`, `build`, and the package `pytest` suite are green;
  every `SKILL.md` is `<100` lines. No production test asserts what file-presence
  + the existing linters already prove.
- **Framework-agnosticism floor: goal-based check (the load-bearing automated
  gate).** A pack-scoped stack-token lint (`tools/lint-design-craft-agnostic.py`,
  Python for Windows portability) greps `packs/design-craft/**` for stack tokens
  (React/Vue/Tailwind/CSS, Framer Motion, ARIA roles, `@media`, and
  values-table shapes like hex/px/ms/easing literals) and exits non-zero on any
  hit; it runs as a `Tests:` entry on the relevant tasks and in CI
  (`build-check.yml` + `build-check-windows.yml`), mirroring the converters
  attribution/Rail-C scrubs.
- **Skill behavior — interrogation, derivation, IA method, heuristic critique:
  manual QA.** Walk a worked example through each skill and record the result; the
  skills' judgment is not unit-testable without asserting mock shapes.
- **Diátaxis guides: goal-based for existence, manual QA for accuracy.** The guide
  files exist at their `docs/guides/design-craft/` quadrant paths (goal-based);
  each reads accurately against the shipped skills (manual review recorded in the
  build PR). *(Guide authoring lands in the build PR, not this spec/plan PR.)*

## Acceptance Criteria

<!-- These are the v1 *pack* contract. v1 ships in two PRs: this spec/plan PR
(authors the spec + plan, registers the spec index — no AC marks a doc into
existence), and the build PR (satisfies every AC below). The plan's Rollout
records the split. The spec stays Draft → Approved here and flips to Shipped in
the build PR (memory: set-final-status-in-the-implementing-PR). -->

- [ ] A new pack ships at **`packs/design-craft/`** with `pack.toml`,
  `.claude-plugin/plugin.json`, and a `README.md`, **registered in
  `.claude-plugin/marketplace.json`** (name `design-craft`, with a description +
  version), **user-scope-default** (`default-scope = "user"`,
  `allowed-scopes = ["user","repo"]`, `[pack.adapter-contract] version = "0.12"`
  matching `research`, `allowed-adapters` = all seven shipped adapters), like
  `architect`/`research`.
- [ ] **`aesthetic-direction`** ships at
  `packs/design-craft/.apm/skills/aesthetic-direction/SKILL.md` (`<100` lines,
  valid frontmatter passing `tools/lint-skill-spec.py`) and documents: the
  interrogation sequence that turns a vague "vibe" into **named emotional/brand
  goals**, the **aesthetic-direction doc** shape downstream work references, and
  **coherence arbitration** (which goal wins when choices conflict, and why) —
  method only, no palette/font.
- [ ] **`design-system-foundations`** ships (same constraints) and documents the
  **derivation method** for a token/scale taxonomy from intent: semantic-over-
  literal naming, ratio-as-*concept* scales, accessibility-as-floor, contrast
  budgets, "purpose before token," and the **atomic-composition** model ("build
  systems, not pages"); it **points to** WCAG (contrast floor) and the W3C Design
  Tokens interchange shape and **never reprints a values table** (Guardrail A).
- [ ] **`layout-and-information-architecture`** ships (same constraints) and
  documents hierarchy, depth-vs-breadth, **reading patterns** (F/Z scanning),
  **progressive disclosure**, and platform-neutral **wayfinding/orientation** as
  *concepts* — never ARIA roles or CSS grid (Guardrail B); no layout code.
- [ ] **`design-critique`** ships (same constraints) and documents structured
  **heuristic evaluation**: review against recognized usability principles, map
  each issue to the violated principle, assign a **severity rating**, and produce
  a prioritized findings list with recommendations; it **applies the shared
  `quality-floor` checklist** as part of the pass. It is a **skill** (interactive,
  authoring-time), **not** a `work-loop` reviewer subagent.
- [ ] A shared **`quality-floor` checklist** ships as a `references/` file
  (referenced by the authoring skills, applied by `design-critique`) covering:
  **handle all states** (empty/loading/error/success/partial/disabled), the
  **accessibility floor** (points to the recognized standard, does not reprint
  ratios), and **"motion communicates state, honor reduced-motion"** (the
  principle, not a CSS media query).
- [ ] Any **template the pack ships** (e.g. the aesthetic-direction doc) rides as
  a **skill `assets/`** file the skill copies into the repo at runtime — the pack
  ships **no `seeds/`** (RFC-0004 Rail A; grep-verified).
- [ ] A **pack-scoped agnosticism lint** (`tools/lint-design-craft-agnostic.py`)
  greps `packs/design-craft/**` for stack tokens and a values-table shape, exits
  non-zero on any hit, has its own self-test, and is **wired into CI**
  (`build-check.yml` + `build-check-windows.yml`) — the RFC-0007 enforcement
  pattern, Python for Windows portability. It is **not** promoted to a repo-wide
  `CONVENTIONS` lint (that would be a separate RFC).
- [ ] **Diátaxis guides** exist under `docs/guides/design-craft/` at their quadrant
  paths — an **explanation** (the design-craft loop and why portable discipline),
  **how-to(s)** (per skill or grouped), and a **reference** (the four skills + the
  `quality-floor` checklist) — each reading accurately against the shipped skills
  (manual-QA recorded in the build PR).
- [ ] An **ADR** records the "design-craft serves designers as upstream
  design-intent authors" scope decision + the strict-agnosticism guardrails
  (lands with the build PR, per the RFC-0030 / RFC-0032 precedent where the ADR
  ships with the build).
- [ ] **No hook / engine / in-pack validator / reviewer subagent / new top-level
  dir** is introduced; the pack is pure markdown; no pack depends on `core` and
  `core` does not depend on this pack (grep-verified); a
  **`docs/product/changelog.md` `[Unreleased]`** entry records the new pack; and
  `make lint-packs`, `make validate`, `make build`, `tools/lint-skill-spec.py`,
  the agnosticism lint, and the package `pytest` suite are **green**, with every
  shipped `SKILL.md` `<100` lines.

## Assumptions

- Process: spec is constrained by RFC-0033 (Accepted 2026-06-14) — the design (audience, roster, scope, agnosticism, skill-vs-agent) is settled there, not re-litigated here (source: docs/rfc/0033-design-craft-pack.md).
- Process: the immediate follow-on after RFC acceptance is spec + plan only; the ADR, guides authoring, version bump, and pack build land in the build PR (source: docs/specs/architect-design-reviewer/ shipped spec+plan only in commit 89824a6/#316; RFC-0030's ADR-0019 landed with the build in ce8ce45; user confirmation 2026-06-14).
- Process: a new pack ships via a spec; the charter caps reviewers at three and forbids infra-shaped additions, and RFC-0032 scoped that ceiling to the core code-review lenses (source: docs/CHARTER.md §Principles; docs/specs/product-engineering-pack/; RFC-0033 §4).
- Technical: user-scope pack shape is pack.toml + .claude-plugin/plugin.json + .apm/skills/ + README, with no seeds/ (RFC-0004 Rail A); templates ride as skill assets/ (source: packs/architect/pack.toml; docs/specs/product-engineering-pack/spec.md enriched-pack-manifest note).
- Technical: [pack.adapter-contract] version 0.12 matches research per RFC-0033 OQ#1 default (source: packs/research/pack.toml).
- Technical: user-scope-default packs aggregate in .claude-plugin/marketplace.json but are not projected to this repo's working tree, so the gate is lint-packs + validate + build + pytest, not build-self (source: .claude-plugin/marketplace.json; architect precedent; memory project_self_host_pack_scope).
- Technical: the agnosticism stack-token check wires into CI analogous to the converters attribution/Rail-C scrubs (source: .github/workflows/build-check.yml:197-229); as a new tool it is Python, not inline bash, for Windows portability (source: memory feedback_new_tools_python_not_bash, feedback_lint_bash_to_py_windows_trap).
- Technical: guides land under docs/guides/design-craft/<quadrant>/ via new-guide and are repo-owned (not projected) (source: docs/guides/architect/ structure; memory reference_self_host_projected_readme_allowlist).
- Technical: SKILL.md <100 lines with depth in references/ is the house pattern; a docs/product/changelog.md [Unreleased] entry is required for the new pack (source: packs/architect/README.md; memory feedback_changelog_for_skill_changes).
- Product: audience is interaction/visual designers + design-eng hybrids, authors of upstream design intent the build consumes; v1 is four skills + one shared checklist, no subagent (source: RFC-0033 decisions 2/3/5; user confirmation 2026-06-14).
