# Spec: xd-skill-boundaries

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** project-maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0071
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter evaluating or invoking the `experience-design` pack can describe a
natural design job and identify the right one of the pack's 20 skills without
crossing into product strategy, product-engineering shaping, or routine frontend
implementation. The four copy-layer skills make their sequence and ownership
explicit in frontmatter. The marketing pack page and documentation reference
present the same 20-skill boundary model, preserve the established platform-site
visual system, and let a cold evaluator answer what the pack does, who it serves,
and which skill family to choose before reading the full inventory. The shared
pack-page Markdown container supplies the spacing and containment needed for
that authored hierarchy to remain legible after the global CSS reset.

## Boundaries

### Always do

- Benchmark all 20 manifest-listed skills before editing and reconcile every
  finished description, activation fixture, and adopter-facing claim against the
  final boundary matrix.
- Keep each frontmatter description natural-request-first and explicit about its
  output, closest intra-pack neighbors, and the adjacent discipline requests it
  must route away.
- Synchronize the marketing page and documentation reference from the canonical
  `.apm` descriptions, then verify the real rendered surfaces.

### Ask first

- Any change to a skill workflow body, output artifact, runtime behavior, or
  reviewer contract discovered during the boundary audit.
- Any skill addition, removal, rename, or change to the established 20-skill
  manifest inventory.
- Any further visual-system, layout-template, navigation, or cross-pack change
  beyond the approved shared pack-description typography fix.

### Never do

- Replay the obsolete same-slug implementation as the contract; it is evidence
  only and does not satisfy the current queue or RFC scope.
- Apply one universal copy-direction guard to unrelated skills or blur the
  distinct roles of `tone-of-voice`, `content-design`, `copy-direction`, and
  `ux-writing`.
- Add a dependency, a top-level directory, a new shared routing abstraction, an
  unshipped-skill reference, or repository-internal governance citations in
  shipped pack content.
- Edit generated documentation or adapter projections as independent sources.

## Testing Strategy

- **Goal-based checks** verify the 20-skill boundary matrix, frontmatter and eval
  coverage, four-way copy boundary, version synchronization, guide validity,
  catalogue projection, and repository gates. These are declarative contracts,
  so a structural check and the existing catalogue validators prove them better
  than mock-shaped unit tests.
- **Visual / manual QA** exercises the built marketing pack page and generated
  documentation reference at 375px and 1280px. A cold evaluator must identify
  the pack's purpose, audience, skill-family entry points, and adjacent-discipline
  exits without encountering page-level overflow or an open in-scope
  severity-3-or-higher design-review finding. `qa.md` names the session boundary,
  including findings documented but not exercised because they belong to
  another approved scope. The shared pack-description typography is exercised
  on the experience-design page and checked against representative existing
  pack content because it is now part of the approved implementation scope.
- **Activation evidence** uses benchmark-derived additions to every affected
  skill's `eval_queries.json` plus deep catalogue validation. The repository's
  model-backed pack-eval runner remains report-only; its availability is not
  substituted with a fabricated routing claim.
- **TDD is not used.** The change adds no runtime logic with a compressible
  invariant.

## Acceptance Criteria

- [x] AC1: `benchmark.md` inventories all 20 skills named by
  `packs/experience-design/pack.toml`, records each current and final
  frontmatter disposition, and maps natural requests plus strategy,
  product-shaping, routine-frontend, and copy-layer near misses to canonical
  skill or pack evidence. It quotes the controlling RFC-0071 Area D scope and
  its 2026-08-02 erratum, and types every proposed positive and negative eval
  fixture against one of those derived boundary classes.

- [x] AC2: Every manifest-listed experience-design `SKILL.md` description starts
  from a natural user request, names the skill's resulting artifact or decision,
  and explicitly routes product-strategy, product-engineering shaping, and
  routine frontend implementation requests away where applicable. All
  descriptions pass deep catalogue lint and the description-length contract.

- [x] AC3: The frontmatter descriptions for `tone-of-voice`, `content-design`,
  and `copy-direction`, together with the named `ux-writing` neighbor, make the
  four-way boundary explicit: brand register, surface content structure,
  per-surface acquisition copy goals, and product UI strings respectively. No
  other skill claims one of those jobs.

- [x] AC4: Every changed skill's `eval_queries.json` gains at least one
  benchmark-derived natural-request positive and one adjacent-discipline
  negative. Across the 20-skill set, negative fixtures cover strategy,
  product-shaping, routine frontend implementation, and all copy-layer
  near-misses; JSON parsing and deep catalogue validation pass.

- [x] AC5: `web/src/content/packs/experience-design.md` lists all 20 manifest
  skills exactly once and, before the inventory, routes evaluators by natural
  job family and names the strategy, shaping, frontend, and copy-layer exits.
  A five-second scan answers what the pack is, who it serves, and which family
  to choose. The shared pack-description container preserves visible grouping
  between its headings, paragraphs, and lists at 375px and 1280px.

- [x] AC6: `guides/experience-design/README.md` routes readers by job family and
  states the correct 20-skill inventory, while
  `guides/experience-design/reference/experience-design.md` lists all 20 skills
  and mirrors the final trigger, output, and nearest-boundary meaning of their
  canonical frontmatter. The guide home and reference keep their Diátaxis roles,
  all links resolve, and guide plus guide-index validation pass.

- [x] AC7: The experience-design pack receives a synchronized patch bump from
  `2.0.0` to `2.0.1` in `pack.toml` and `plugin.json`; the changelog records the
  boundary, eval, and adopter-facing updates; generated marketplace and
  self-host projections are current.

- [x] AC8: Site generation and the marketing/docs builds succeed. The rendered
  marketing page and generated documentation reference both expose the same
  20-skill inventory and boundary terminology.

- [x] AC9: Catalogue lint, deep catalogue lint, catalogue verification,
  contract-drift checks, self-host drift checks, and the repository build check
  pass on the final tree.

- [x] AC10: `qa.md` records the baseline and final design-review results, build
  commands and exits, routes, 375px and 1280px observations, and screenshot or
  DOM evidence. It explicitly separates the in-scope content and shared
  pack-description typography session from documented-but-not-exercised
  cross-pack concerns. The three in-scope baseline findings—incorrect 19-skill
  claims, inventory-before-routing comprehension, and collapsed Markdown
  rhythm—are resolved, no page-level overflow is present, and no in-scope
  severity-3-or-higher finding remains open.

- [x] AC11: No skill workflow body, reviewer body, skill directory/name,
  dependency, navigation, visual token, or file outside the spec,
  experience-design pack, its marketing/reference content, the shared
  pack-description styles in `web/src/pages/packs/[pack].astro`, changelog,
  workspace lifecycle, and generator-owned projections changes.

- [x] AC12: After every other criterion passes, `workspace.toml` moves
  `spec/xd-skill-boundaries` from `ini-003.work.queue` to
  `ini-003.work.shipped` while preserving downstream dependency references.

## Assumptions

- Technical: the current experience-design manifest lists 20 skills and both
  pack manifests are synchronized; AC7 is the canonical release-version contract
  (source:
  `packs/experience-design/pack.toml` and
  `packs/experience-design/.claude-plugin/plugin.json`).
- Technical: the canonical editable skill descriptions and eval fixtures live
  under `packs/experience-design/.apm/skills/`; adapter projections are generated
  (source: `packs/AGENTS.md` and `packs/AGENTS.local.md`).
- Technical: the marketing page is hand-authored at
  `web/src/content/packs/experience-design.md`, while the documentation surfaces
  are generated from `guides/experience-design/README.md` and
  `guides/experience-design/reference/experience-design.md` (source:
  `web/AGENTS.md`, `docs-site/AGENTS.md`, and the current files).
- Process: RFC-0071 is Accepted and requires natural-language trigger
  descriptions plus near-miss guards across the experience-design skills, with
  a per-spec version bump (source: `docs/rfc/0071-digital-experience-doctrine.md`).
- Process: this is full-mode work because it changes published skill interfaces
  and contains dependent pack, eval, documentation, and rendered-QA tasks
  (source: `AGENTS.md` and the `work-loop` risk triggers).
- Product: the current queue/RFC contract is authoritative; commit `f7c24faa`
  is an obsolete same-slug partial used only as evidence (source: user
  confirmation 2026-08-09).
- Product: marketing and documentation updates preserve the established visual
  system and receive baseline plus final design review; the approved template
  amendment is limited to token-based rich-text rhythm and containment inside
  the existing pack-description container (source: user confirmation
  2026-08-10).
- Product: the baseline rendered pack page's incorrect 19-skill claim,
  inventory-first routing, and collapsed Markdown rhythm are in-scope findings
  (source: design-review baseline and user-confirmed scope amendment
  2026-08-10).
