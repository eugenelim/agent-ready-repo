# Spec: Marketing Website — Catalogue Consolidation & Funnel Improvements

- **Status:** Shipped
- **Owner:** eugenelim
- **Mode:** full (risk triggers: structural change — new `/catalogue/` URL; multi-feature/dependent tasks)

## Objective

Improve the marketing site's activation funnel and reduce cognitive load by consolidating the separate Packs and Plugins pages into a unified Catalogue, adding copy ergonomics to the install terminal, rewriting the core journey to present-tense active voice, improving journey index cards with outcome text, and flipping the hero subhead to pain-first framing.

## Boundaries

- **Never do:** add new npm dependencies to `web/package.json`.
- **Always do:** use `withBase()` for all internal hrefs — no hardcoded `/agent-ready-repo/` prefixes.
- **Never do:** modify `/packs/[pack].astro` (detail pages stay at their current URLs).

## Assumptions

- Pack detail pages (`/packs/[pack]/`) stay at their current URLs — only the index redirects.
- The plugins page card pattern (name, tagline, scope, skill count, copy button) is the design model for the catalogue.
- `withBase()` handles all path prefixing.

## Acceptance Criteria

- [x] `/catalogue/` page exists and lists all packs with CLI install command and Plugin install command, each with a working copy button
- [x] Nav shows `Catalogue` (single entry) instead of `Packs` and `Plugins` (two entries)
- [x] `/packs/` and `/plugins/` redirect to `/catalogue/`
- [x] Core journey body (`journeys/core.md`) is present tense throughout; journey frontmatter skill array includes all 8 skills matching `packs/core.md`
- [x] Install terminal (`InstallTerminal.astro`) has copy-to-clipboard on the active tab's command
- [x] Journey index cards show tagline text under the pack name; CTA is outcome-oriented, not passive
- [x] Hero subhead is pain-first (leads with self-certification problem before naming the mechanism)
- [x] `npm run build` passes with no TypeScript errors

## Task list

1. Create `web/src/pages/catalogue/index.astro` — unified catalogue page
2. Replace `web/src/pages/packs/index.astro` with redirect stub
3. Replace `web/src/pages/plugins/index.astro` with redirect stub
4. Update `web/src/components/layout/SiteNav.astro` — Catalogue replaces Packs + Plugins
5. Update `web/src/components/marketing/Hero.astro` — pain-first subhead
6. Update `web/src/components/marketing/InstallTerminal.astro` — add copy button
7. Update `web/src/pages/journeys/index.astro` — add taglines, improve CTA
8. Update `web/src/content/journeys/core.md` — present-tense rewrite, 8 skills

## Declined patterns

- Tempted to redesign `/packs/[pack].astro` detail pages — declining; out of scope, already readable.
- Tempted to add `/catalogue/[pack].astro` alias detail routes — declining; canonical detail URL stays at `/packs/`.
- Tempted to add search/filter to the catalogue grid — declining; hypothetical future requirement.
- Tempted to animate tab transitions in the install terminal — declining; CSS-only, no looping animation per aesthetic-direction.md.
- Tempted to rewrite all 14 journey files to present tense — declining; separate task (audit Part B template covers it).
- Tempted to add live GitHub stars / PyPI download counts — declining; requires build-time API call, separate PR.

## Testing strategy

Verification mode: Visual / manual QA (primary HTML/CSS output)
- `npm run build` passes (typecheck + Astro compile) — verified
- Build output contains `/catalogue/index.html` with both install blocks and copy buttons
- Build output for `/packs/index.html` and `/plugins/index.html` contains redirect markup
- SiteNav renders with `Catalogue` link, no `Packs` or `Plugins` links
