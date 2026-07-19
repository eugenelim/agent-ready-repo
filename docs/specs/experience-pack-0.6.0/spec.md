# Spec: Experience pack 0.6.0 — surface-genre uplift

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0066, ADR-0038, ADR-0024
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

<!-- Mode: Full — risk triggers fired: structural (7 new module directories within
     packs/experience/.apm/skills/); public-interface (9 skill renames affecting
     adopters); multi-feature with dependent tasks (renames must precede new
     skill authoring and extensions). -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The experience pack gains a surface-genre contract, a Define-phase skill, six
genre-specific design skills, seven agency-practice extensions across six existing
skills, and nine canonical renames — moving from 11 skills at version 0.5.0 to
18 skills at version 0.6.0. A design team working on any marketing, documentation,
analytical, marketplace, informational, or workspace surface can declare the genre
once in the screen brief and receive genre-appropriate methodology from every
downstream skill in the chain. A team adopting the renamed skills finds canonical
industry names (journey-mapping, service-blueprint, user-flow, creative-direction,
information-architecture, design-review, design-system, process-mapping,
tone-of-voice) rather than the pack's invented slugs.

## Boundaries

### Always do

- Follow ADR-0038's alias-free rename procedure: rename the live surface, bridge
  frozen governance with a new ADR, no install-time alias. Run the post-rename grep
  (RFC-0066 D7 step 8) before declaring the rename task done.
- Run `tools/lint-experience-agnostic.py packs/experience/` after every new or
  modified skill to confirm ADR-0024 compliance (no values tables, no platform
  primitives).
- Update `content-design/SKILL.md` cross-references in the rename sweep:
  `copy-direction` → `tone-of-voice`; leave `voice-and-microcopy` references
  unchanged (that rename is deferred to a separate product-engineering RFC per D7).
- Create ADR-0052 (nine experience-pack skill renames) in the implementation PR,
  following ADR-0038's shape exactly: Status: Accepted, 9-row old→new mapping
  table, frozen-governance bridge statement, no alias.

### Ask first

- Any change to `content-design`'s existing 2-type copy-layer surface routing
  (acquisition / product-reference) — explicitly out of scope per RFC-0066 D6.
- Any addition to the 7-type surface-genre taxonomy beyond the 7 types in D2.
- Any prescriptive reference to a specific framework, library, CMS, or tooling
  as a required implementation target inside a new or modified skill (would
  violate ADR-0024). Practitioner sites named as "canonical aesthetic reference"
  study subjects (per D5f, D4) are permitted under ADR-0024 when framed as
  "internalize the philosophy, not copy the surface"; ask first if the framing
  is unclear.
- Any change to `voice-and-microcopy` or its cross-references in experience skills
  (lives in product-engineering; its rename is deferred to a separate RFC).

### Never do

- Add an install-time alias mapping old skill names to new ones — ADR-0038
  precedent is alias-free; no alias mechanism exists in this repo (grep-confirmed
  in RFC-0048).
- Create a new top-level directory outside `packs/experience/.apm/skills/` without
  an RFC.
- Add a new dependency (package, tool, or runtime) — skills are pure markdown.
- Edit frozen governance docs (ADRs, accepted/rejected RFCs) except to update
  status fields and add new-ADR bridge entries.

## Testing Strategy

All skill content is pure markdown — no runtime code. Two verification modes apply:

**Goal-based check** (structural / mechanical outcomes):
- Post-rename grep must return zero results after T1.
- `python tools/lint-experience-agnostic.py packs/experience/` must exit 0 after
  each task that modifies skills.
- `grep 'version = "0.6.0"' packs/experience/pack.toml` must match.
- `ls packs/experience/.apm/skills/ | wc -l` must equal 18 after T4.
- `grep 'surface-genre:' packs/experience/.apm/skills/user-flow/assets/screen-brief-template.md`
  must match.

**Manual QA** (content correctness):
- Each of the 7 new skills is read end-to-end to verify: methodology is complete,
  no platform-specific references violating ADR-0024, cross-references use
  canonical (post-rename) slugs.
- The `## Genre-specific notes` section in the screen-brief template has all 7
  genre sub-sections as comment blocks.
- The 7 D5 extensions are verified present in the 6 extended skills.
- ADR-0052 has the full 9-row old→new mapping table.

## Acceptance Criteria

- [ ] AC1: `user-flow/assets/screen-brief-template.md` frontmatter has
      `surface-genre: <marketing | documentation | informational | analytical |
      transactional-journey | marketplace | workspace>` and a
      `## Genre-specific notes` section with all 7 genre sub-sections as comment
      blocks.
- [ ] AC2: `user-flow/SKILL.md` "When to invoke" section has a 5th item
      confirming surface genre before drafting briefs, including the inline
      elicitation fallback ("What kind of surface is this?").
- [ ] AC3: `design-principles/SKILL.md` exists with: NNGroup 4-step derivation
      (insight → user-grounded → arbitration-aware → team-owned); the arbitration
      test ("given two wireframes, can this principle distinguish between them?");
      evidence-level carry-through from journey map; chain position (consumed by
      creative-direction, information-architecture, content-design, design-review).
- [ ] AC4: Six new SKILL.md files exist — `conversion-design`,
      `documentation-design`, `analytical-design`, `marketplace-design`,
      `informational-design`, `workspace-design` — each passes
      `lint-experience-agnostic.py` with zero violations.
- [ ] AC5: Seven D5 additions are present across six extended skills:
      - `journey-mapping/SKILL.md`: peak-moments step (5b), `evidence-level:`
        frontmatter field declaration, surface-genre confirmation in step 1 with
        link to `references/surface-genre-journeys.md`.
      - `interaction-design`: 5 new pattern families in `references/pattern-families.md`
        (wizard-and-stepper, data-table, destructive-action 5-tier escalation,
        save-state, analytical-dashboard-widgets).
      - `service-blueprint/SKILL.md`: evidence-of-service row and fail-point
        marking with design-priority annotation (critical / high / medium).
      - `information-architecture/SKILL.md`: success-metric binding in
        "When to invoke" item 4; genre routing in procedure step 1 for all 7
        genres.
      - `design-review/SKILL.md`: design-principles integration chain as
        mandatory procedure step (load artefact → map every finding to a principle
        → unfound findings route to quality-floor or new-principle decision).
      - `creative-direction/SKILL.md`: genre canonical reference tier for all
        7 genres.
      - `design-review/SKILL.md`: genre-specific rubrics for 6 genres
        (documentation, marketing, analytical, informational, marketplace,
        workspace).
- [ ] AC6: Nine skill directories renamed; post-rename grep for old slugs returns
      zero results across `packs/experience/` and `docs/guides/experience/` in all
      file types (`*.md`, `*.toml`, `*.json`); cross-pack inbound references in
      `packs/core/`, `packs/product-engineering/`, and `packs/research/` that name
      old experience-pack slugs as imperative invocations are updated to canonical
      names (or explicitly recorded in `docs/backlog.md` if prose-only mentions).
- [ ] AC7: `packs/experience/pack.toml` version field is `0.6.0`; `[pack.evals]`
      skills list uses canonical (post-rename) slugs; description updated to
      reflect the 18-skill chain; `packs/experience/.claude-plugin/plugin.json`
      version and description updated to match; `make build-self` run to
      re-aggregate `marketplace.json`.
- [ ] AC8: `python tools/lint-experience-agnostic.py packs/experience/` exits 0
      with zero violations.
- [ ] AC9: `docs/adr/0052-nine-experience-pack-skill-renames.md` exists with
      Status: Accepted, full 9-row old→new mapping table, frozen-governance bridge
      statement, no-alias statement.
- [ ] AC10: `docs/product/changelog.md` has a 0.6.0 entry listing all 9 renames
      and 7 new skills.
- [ ] AC11: `docs/rfc/README.md` has an RFC-0066 row with title, status
      (Accepted), and date closed.
- [ ] AC12: All 4 `docs/guides/experience/` files (README.md,
      explanation/the-experience-thread.md, how-to/author-design-intent.md,
      reference/experience.md) use canonical skill slugs; zero old-slug references.
- [ ] AC13: `content-design/SKILL.md` reference to `copy-direction` updated to
      `tone-of-voice`; references to `voice-and-microcopy` left unchanged.
- [ ] AC14: `web/` marketing site files that reference experience pack skills use
      canonical (post-rename) skill names; zero old-slug references in the 6
      identified files (`web/src/content/packs/experience.md`,
      `web/src/content/journeys/experience.md`,
      `web/src/components/layout/Section.astro`,
      `web/src/components/marketing/HumanGates.astro`,
      `web/src/components/marketing/Hero.astro`,
      `web/src/components/marketing/BuildYourOrg.astro`).
- [ ] AC15: `docs/guides/experience/reference/experience.md` lists all 18 skills with
      canonical names and one-line descriptions; `docs/guides/experience/explanation/the-experience-thread.md`
      and `docs/guides/experience/how-to/author-design-intent.md` read correctly with
      renamed skill names and updated chain structure.
- [ ] AC16: In `docs/product/journeys/`, all imperative old-skill-slug invocations
      are updated to canonical names; zero imperative old-slug references remain;
      prose-only mentions in educational callouts are recorded in `docs/backlog.md`
      under `experience-pack-rename-journey-prose` (acceptable deferred cleanup).
      Pre-0.6.0 stage tables and Mermaid diagrams in `designer-designs-surface.md`
      that document the historical baseline are preserved, not overwritten.
- [ ] AC17: `docs/product/journeys/designer-designs-surface.md` reflects the
      as-built state of experience 0.6.0:
      (a) Frontmatter `status:` promoted from `planned` to `live`.
      (b) The prereq-table row for experience (approximately line 41) updated from
          "current (0.5.0) | 11 skills" to "live (0.6.0) | 18 skills".
      (c) The "planned (0.6.0 — RFC-0066)" status-table cell (approximately line 42)
          updated to "live".
      (d) The `### To-be state — experience 0.6.0 (after RFC-0066)` header
          present-tensed to `### Shipped state — experience 0.6.0`.
      (e) All six per-stage `### Now (experience 0.5.0)` headers (Stages 1–6), the
          `### Current state — experience 0.5.0 (before RFC-0066)` Mermaid section,
          and the `**As-is setup (experience 0.5.0)**` prose block (~lines 44–47) are
          preserved as historical baseline — they document the pre-0.6.0 state for
          contrast and must not be overwritten. **Historical-section definition (applies
          to T9 steps 2–3):** any section whose heading or bold label carries an
          `(experience 0.5.0)`, `(before RFC-0066)`, or `As-is` marker.
      Completed after T1–T8 confirm the as-built state.

## Assumptions

- Technical: Experience pack version is 0.5.0
  (source: `packs/experience/pack.toml`)
- Technical: Pack has exactly 11 skills pre-rename: aesthetic-direction,
  blueprint-service, content-design, copy-direction, design-critique,
  design-system-foundations, interaction-design, layout-and-information-architecture,
  map-customer-journey, map-internal-process, map-screen-flow
  (source: `packs/experience/.apm/skills/` directory listing)
- Technical: `tools/lint-experience-agnostic.py` is the mechanical agnosticism gate;
  `tools/test-lint-experience-agnostic.py` provides its test suite
  (source: `tools/` directory listing)
- Technical: `docs/guides/experience/` has exactly 4 .md files in the rename sweep:
  README.md, explanation/the-experience-thread.md, how-to/author-design-intent.md,
  reference/experience.md (source: `find docs/guides/experience/ -name "*.md"`)
- Technical: Next available ADR ordinal is 0052 (latest is 0051)
  (source: `docs/adr/` directory listing)
- Process: ADR-0038's alias-free precedent governs skill renames: rename live
  surface, bridge frozen governance with new ADR, no alias
  (source: `docs/adr/0038-rename-design-craft-pack-to-experience.md`, Status: Accepted)
- Process: ADR-0024's two guardrails (no values tables; no platform primitives)
  constrain all new and modified skills
  (source: `docs/adr/0024-design-craft-upstream-intent-and-agnosticism.md`)
- Technical: 6 `web/` files reference old experience skill slugs and require
  updating in this PR: `web/src/content/packs/experience.md`,
  `web/src/content/journeys/experience.md`,
  `web/src/components/layout/Section.astro`,
  `web/src/components/marketing/HumanGates.astro`,
  `web/src/components/marketing/Hero.astro`,
  `web/src/components/marketing/BuildYourOrg.astro`
  (source: `grep -r <old-slugs> web/ -l`)
- Technical: Cross-pack inbound references (packs/core/, packs/product-engineering/,
  packs/research/) may contain old experience-pack slug references as imperative
  invocations; T1 sweep determines whether they are imperative (must update) or
  prose-only (record in backlog as acceptable deferred follow-on)
  (source: adversarial-reviewer finding #1, 2026-07-19)
- Process: Journey doc update (`docs/product/journeys/designer-designs-surface.md`)
  is in-scope as AC17 / T9, completed after all implementation tasks confirm the
  as-built state (source: user direction 2026-07-19)
