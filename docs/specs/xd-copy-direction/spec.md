# Spec: xd-copy-direction

**Mode:** Full (risk triggers: structural/public-interface change — new skill; multi-feature — skill + references + evals + pack metadata + web + site + guides + workspace.toml)

- **Status:** Shipped
- **Author:** eugenelim
- **Governance:** RFC-0062 (Accepted 2026-07-23)
- **Related:** RFC-0071 (Digital Experience Doctrine — accepts RFC-0062; ini-003 M3a prerequisite), spec/digital-experience-contract (Shipped — dependency satisfied)
- **Date opened:** 2026-07-23
- **Date shipped:** 2026-07-23

## Objective

Implement the `copy-direction` skill in the `experience-design` pack per RFC-0062. This is the surface-specific copy twin of `creative-direction` — turns a vague "how should our marketing copy sound" into named, ranked copy voice goals grounded in stable referents, and records copy arbitration rules the rest of the build references. Settles the three-way copy boundary (copy-direction / voice-and-microcopy / content-design) required before spec/xd-skill-boundaries (M3a) can install frontmatter near-miss guards.

## Acceptance Criteria

- [x] AC1: `copy-direction` SKILL.md exists at `packs/experience-design/.apm/skills/copy-direction/SKILL.md` with frontmatter `name: copy-direction` and description and trigger language from RFC-0062.
- [x] AC2: The skill procedure follows the 8-step structure (audience map → interrogation → grounding → ranking → arbitration → capture → floor check → hand-off), structurally twinning `creative-direction`.
- [x] AC3: The skill produces `<output_dir>/copy-direction/<slug>.md` with frontmatter `type: copy-direction`, resolved via `references/agentbundle-layout.md`.
- [x] AC4: Three core reference files exist: `references/copy-jtbd.md`, `references/copy-grounding.md`, `references/copy-arbitration.md`.
- [x] AC5: Supporting reference files exist: `references/interrogation-sequence.md`, `references/plain-language-floor.md`, `references/agentbundle-layout.md`.
- [x] AC6: Asset template exists: `assets/copy-direction-template.md`.
- [x] AC7: Activation eval exists at `evals/eval_queries.json` with ≥10 positive queries and ≥10 negative queries (cross-boundary coverage: voice-and-microcopy, content-design, and tone-of-voice negatives included).
- [x] AC8: LLM-judge rubric exists at `evals/evals.json` with at least one eval fixture covering the happy-path output (named goals, ranking, referents, arbitration rules, no copy strings).
- [x] AC9: `packs/experience-design/pack.toml` version bumped from 1.1.1 → 1.2.0; `copy-direction` added to `[pack.evals].skills` list.
- [x] AC10: `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` frontmatter `description:` includes a near-miss guard directing surface-specific marketing copy voice to `copy-direction`.
- [x] AC11: `packs/experience-design/.apm/skills/content-design/SKILL.md` frontmatter `description:` includes near-miss guards directing copy voice direction to `copy-direction` and per-state UI strings to `voice-and-microcopy`.
- [x] AC12: `web/src/content/packs/experience-design.md` `skills:` list includes `copy-direction`.
- [x] AC13: `web/src/content/journeys/experience-design.md` updated to include copy-direction in the design thread (step 1 narrative alongside content-design and tone-of-voice).
- [x] AC14: How-to guide `docs/guides/experience-design/how-to/copy-layer-boundary.md` created, covering the three-way copy boundary (copy-direction / voice-and-microcopy / content-design).
- [x] AC15: `site/mkdocs.yml` nav updated to list the new how-to guide under Experience Design → How-to.
- [x] AC16: `workspace.toml` entry for `spec/xd-copy-direction` moved from `["ini-003".work].queue` to `["ini-003".work].shipped`.
- [x] AC17: `python3 tools/check-contract-drift.py --root .` exits 0.
- [x] AC18: `make build-check` exits 0.

## Boundaries

**In scope:**
- New `copy-direction` skill (SKILL.md + reference tree + assets + evals)
- Pack version bump (1.1.1 → 1.2.0)
- Near-miss guard additions to tone-of-voice and content-design frontmatter (description field only; no body changes)
- web/ and site/ pack page, journey page, and how-to guide updates
- workspace.toml queue→shipped move

**Not in scope:**
- Changes to `voice-and-microcopy` SKILL.md (scope boundary note is spec/xd-skill-boundaries work)
- SEO keyword targeting guidance (deferred per RFC-0062 D5)
- Changes to any PE pack skills
- Content changes to creative-direction or design-system
- Changes to tone-of-voice or content-design beyond the near-miss guard additions

## Assumptions

1. `tone-of-voice` and `copy-direction` coexist with distinct jobs: tone-of-voice handles general brand voice; copy-direction handles surface-specific marketing/acquisition copy voice goals for a particular surface (above-fold, landing page, positioned copy).
2. The output path for copy-direction is `<output_dir>/copy-direction/<slug>.md` (distinct from tone-of-voice's `copy/<slug>.md`) to avoid type ambiguity.
3. The interrogation sequence and plain-language floor references are adapted from tone-of-voice with copy-direction-specific scope notes.
4. `make build-check` does not include MkDocs build; the Python/pack gates are the build-check contract.

## Declined patterns

- Tempted to rename/merge tone-of-voice into copy-direction; declining — they serve different scope-breadths (brand-level vs. surface-specific), tone-of-voice has an established install base.
- Tempted to add copy-direction content to PE skill body text; declining — beyond near-miss guards is spec/xd-skill-boundaries territory.
- Tempted to write a multi-fixture LLM judge rubric for v1; declining — one happy-path fixture is sufficient; additional fixtures belong in the eval rollout backlog item.
- Tempted to restructure `author-design-intent.md` to include copy-direction; declining — the three-way boundary deserves its own discoverable how-to.

## Testing Strategy

Mode: **Visual / manual QA** (skill artifacts; no runtime test suite)

All ACs are goal-based checks:
- File existence and content spot-check via Read + grep
- AC9: `grep "copy-direction" packs/experience-design/pack.toml` + version string check
- AC17: `python3 tools/check-contract-drift.py --root .` exit 0
- AC18: `make build-check` exit 0
