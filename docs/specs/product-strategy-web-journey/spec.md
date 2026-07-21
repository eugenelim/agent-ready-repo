# Spec: product-strategy-web-journey

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim

**Mode:** light (no risk trigger fired)

## Objective

Create `web/src/content/journeys/product-strategy.md` — the public web journey page for the product-strategy pack. The pack is already in the catalogue (9 skills, 3 pillars: market strategy, UX strategy, content strategy) and has an internal journey at `docs/product/journeys/product-strategist-sets-direction.md`, but no web-facing journey page exists. Follow the existing journey schema (pack/scope/tagline/prerequisitePacks/whatChanges/skills/humanGates/typicalSession frontmatter + stage prose) defined in `web/src/content.config.ts`.

## Acceptance Criteria

- [x] File exists at `web/src/content/journeys/product-strategy.md`
- [x] Frontmatter satisfies the Zod journey schema (all required fields present, correct types)
- [x] Skills array lists all 9 skills from the pack in logical order (market strategy → UX strategy → content strategy)
- [x] Three human gates: G-situation (after SWOT), G-prfaq (after PRFAQ), G-cascade (before workspace.toml write)
- [x] Stage prose provides actionable guidance across 4 stages matching the pack's workflow
- [x] `npm run build` in `web/` succeeds with no content validation errors on the new file

## Tasks

1. Write `web/src/content/journeys/product-strategy.md` — all frontmatter + stage prose
2. Verify: `cd web && npm run build` exits 0 with no Zod errors
