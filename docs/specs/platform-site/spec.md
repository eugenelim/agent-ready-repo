# Spec: platform-site

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)
- **Constrained by:** [aesthetic-direction.md](aesthetic-direction.md), [design-system-foundations.md](design-system-foundations.md), [information-architecture.md](information-architecture.md), [homepage-screen-flow.md](homepage-screen-flow.md), [journey-page-template.md](journey-page-template.md), [RFC-0061](../../rfc/0061-web-top-level-directory.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Site inventory

A complete map of every page, content type, and shared surface this spec covers.

### Pages

15 packs exist in `packs/`; 14 are included in the platform site. `catalogue-curation` (v0.1.1) is excluded until its MkDocs reference page is authored — it has no `/docs/packs/catalogue-curation` page yet. The inventory below reflects 14 published packs.

Two journey slugs differ from their pack slugs: `discovery` → `product-engineering` pack; `release` → `release-engineering` pack. `getStaticPaths` must handle the mapping explicitly; see T9.

| Route | Surface | Phase | Content source |
|---|---|---|---|
| `/` | Marketing homepage (9 sections) | 1 | `web/src/pages/index.astro` |
| `/packs/` | Pack catalogue index | 2 | Astro content collection |
| `/packs/core/` | Pack detail | 2 | `web/src/content/packs/core.md` |
| `/packs/product-engineering/` | Pack detail | 2 | `web/src/content/packs/product-engineering.md` |
| `/packs/release-engineering/` | Pack detail | 2 | `web/src/content/packs/release-engineering.md` |
| `/packs/research/` | Pack detail | 2 | `web/src/content/packs/research.md` |
| `/packs/architect/` | Pack detail | 2 | `web/src/content/packs/architect.md` |
| `/packs/experience/` | Pack detail | 2 | `web/src/content/packs/experience.md` |
| `/packs/contracts/` | Pack detail | 2 | `web/src/content/packs/contracts.md` |
| `/packs/converters/` | Pack detail | 2 | `web/src/content/packs/converters.md` |
| `/packs/atlassian/` | Pack detail | 2 | `web/src/content/packs/atlassian.md` |
| `/packs/figma/` | Pack detail | 2 | `web/src/content/packs/figma.md` |
| `/packs/governance-extras/` | Pack detail | 2 | `web/src/content/packs/governance-extras.md` |
| `/packs/credential-brokers/` | Pack detail | 2 | `web/src/content/packs/credential-brokers.md` |
| `/packs/monorepo-extras/` | Pack detail | 2 | `web/src/content/packs/monorepo-extras.md` |
| `/packs/user-guide-diataxis/` | Pack detail | 2 | `web/src/content/packs/user-guide-diataxis.md` |
| `/journeys/` | Journey index | 2 | `web/src/pages/journeys/index.astro` |
| `/journeys/core/` | Journey detail | 2 | `web/src/content/journeys/core.md` |
| `/journeys/discovery/` | Journey detail | 2 | `web/src/content/journeys/discovery.md` |
| `/journeys/release/` | Journey detail | 2 | `web/src/content/journeys/release.md` |
| `/journeys/research/` | Journey detail | 3 | `web/src/content/journeys/research.md` |
| `/journeys/architect/` | Journey detail | 3 | `web/src/content/journeys/architect.md` |
| `/journeys/experience/` | Journey detail | 3 | `web/src/content/journeys/experience.md` |
| `/journeys/contracts/` | Journey detail | 3 | `web/src/content/journeys/contracts.md` |
| `/journeys/converters/` | Journey detail | 3 | `web/src/content/journeys/converters.md` |
| `/journeys/atlassian/` | Journey detail | 3 | `web/src/content/journeys/atlassian.md` |
| `/journeys/figma/` | Journey detail | 4 | `web/src/content/journeys/figma.md` |
| `/journeys/governance-extras/` | Journey detail | 4 | `web/src/content/journeys/governance-extras.md` |
| `/journeys/credential-brokers/` | Journey detail | 4 | `web/src/content/journeys/credential-brokers.md` |
| `/journeys/monorepo-extras/` | Journey detail | 4 | `web/src/content/journeys/monorepo-extras.md` |
| `/journeys/user-guide-diataxis/` | Journey detail | 4 | `web/src/content/journeys/user-guide-diataxis.md` |
| `/docs/` | MkDocs reference (existing) | 0 | `site/docs/` — unchanged |

### Served artifacts (non-page)

| Artifact | Phase | Source |
|---|---|---|
| `/sitemap.xml` | 4 | `@astrojs/sitemap` integration |
| `/robots.txt` | 4 | `web/public/robots.txt` |
| `/social.png` | 4 | `web/public/social.png` (1200×630 og:image) |
| `/404.html` | 1 | `web/src/pages/404.astro` (Astro emits `404.html` only when this page exists — not automatic); GitHub Pages uses it for unknown routes |

### Shared surfaces

| Surface | Used by | Style source |
|---|---|---|
| SiteNav | All Astro marketing pages | `web/src/styles/tokens.css` |
| SiteFooter | All Astro marketing pages | `web/src/styles/tokens.css` |
| MkDocs header + tabs | All `/docs/` pages | `site/docs/stylesheets/extra.css` |

### Phase summary

| Phase | Scope | Status |
|---|---|---|
| 0 — MkDocs token alignment | Amber-gold CSS swap; global primary button override | Complete (all ACs met) |
| 1 — Astro scaffold + homepage | Astro in `web/`, 9 homepage sections, CI pipeline | In progress (this PR — homepage + CI built; `/packs/` and `/journeys/` routes land in Phase 2) |
| 2 — Pack catalogue + core journeys | 14 pack pages + journey index + 3 core journey pages | Planned |
| 3 — Priority-2 journeys | research, architect, experience, contracts, converters, atlassian | Planned (content-gated) |
| 4 — Remaining journeys + SEO | figma, governance-extras, credential-brokers, monorepo-extras, user-guide-diataxis; SEO metadata + sitemap | Planned (content-gated) |

## Objective

Build the agent-ready-repo platform site — a marketing-anchored home for the catalogue that converts a browsing senior engineer or engineering lead into a curious installer in under 90 seconds. The surface is two co-deployed builds sharing one GitHub Pages origin: an Astro marketing site at `/` (homepage, `/packs/`, `/journeys/`) as the anchor, and the existing MkDocs reference documentation at `/docs/`. The aesthetic is Option B — Alternating Conviction: `#0b0e12` dark hero zone, `#fafaf9` warm near-white content sections, `#e8952b` amber-gold as the sole chromatic accent. All user-facing surfaces apply the token palette from [design-system-foundations.md](design-system-foundations.md) and the ranked goals from [aesthetic-direction.md](aesthetic-direction.md).

## Boundaries

### Always do

- Apply the amber-gold token palette from `design-system-foundations.md` to every surface — no hardcoded hex or spacing values outside the token block
- Follow the alternating-band layout: dark hero zone (`#0b0e12`), light content sections (`#fafaf9`), dark footer-adjacent closer
- Build Astro first in the CI pipeline, then MkDocs — Astro's `astro build` cleans the output directory; MkDocs must write to `build/docs/` after Astro writes `build/`
- Honour WCAG 2.2 AA: body text ≥ 4.5:1; large text / UI components ≥ 3:1 (verified ratios in design-system-foundations.md)
- Link every pack page to its journey page, and every journey page back to its pack and to `/docs/`

### Ask first

- Changes to the GitHub Actions workflow that affect the deploy path or artifact name
- Any new top-level directory beyond `web/` (each requires an RFC per AGENTS.md § Check before acting)
- Changes to the homepage screen-flow section ordering from [homepage-screen-flow.md](homepage-screen-flow.md)
- Changes to the navigation structure from [information-architecture.md](information-architecture.md)

### Never do

- Use a CSS framework (Tailwind, Bootstrap, UnoCSS) that would override the `--ds-*` token system
- Add server-side runtime components — GitHub Pages is static-only; no server endpoints, no SSR
- Serve the Astro site and MkDocs from separate GitHub Pages deployments
- Hardcode color or spacing values outside the design-system-foundations token block
- Use ambient looping animations — static by default; one-shot 300ms opacity fade-in on load is the permitted ceiling (Calabro 2024 research: looping animation causes 26% comprehension reduction in task-focused audiences)

## Testing Strategy

This spec uses goal-based checks and visual/manual QA. The Astro marketing site has no unit test suite; verification is build-success + browser observation + accessibility audit.

- **Phase 0 (CSS token swap):** Goal-based — `grep -rE 'indigo|#5e6ad2|#818cf8|#4c5bbc' site/docs/stylesheets/extra.css` returns zero matches. Visual/manual QA: `mkdocs serve` confirms amber-gold in header, hero, cards, buttons, links.
- **Phase 1 (Astro homepage):** Goal-based — `astro build` exits 0; `build/index.html` exists. Visual/manual QA — `astro dev`, confirm all 9 sections render in order with correct zone colors; all interactions (install tabs, catalogue expand) work without JavaScript. Accessibility — `npx pa11y http://localhost:4321 --standard WCAG2AA` exits 0 errors.
- **Phase 2 (Pack catalogue + journeys):** Goal-based — `astro build` generates all 14 pack routes and 3 journey routes. Visual/manual QA — spot-check pack index, one pack detail, one journey page; confirm pack detail shows a conditional "Journey coming soon" state for Phase-3 journeys. Accessibility — pa11y on pack index and one journey page, 0 errors.
- **Phase 3 (Priority-2 journeys):** Goal-based — `astro build` generates all 6 new journey routes. Visual/manual QA — spot-check `research` and `atlassian` journey pages for all 8 sections. Accessibility — pa11y on each new journey page, 0 errors each.
- **Phase 4 (Remaining journeys + SEO):** Goal-based — `build/sitemap.xml` lists all Astro routes; `build/robots.txt` and `build/social.png` exist; every Astro page includes `og:title`, `og:description`, `og:image`, `<link rel="canonical">`.
- **CI pipeline:** Goal-based — GitHub Actions build exits 0 on `main`; `build/` contains `index.html` at root and `docs/index.html` from MkDocs.

## Acceptance Criteria

### Phase 0 — MkDocs token alignment

- [x] `extra.css` contains no indigo hex values (`#5e6ad2`, `#818cf8`, `#4c5bbc`) or their rgba forms
- [x] Dark zone background is `#0b0e12` in header, tabs, and hero
- [x] Amber-gold accent `#e8952b` is the sole chromatic token across light and dark mode
- [x] `--md-typeset-a-color` is `#8b5e0a` in light mode (≥ 6:1 contrast on `#fafaf9`) and `#f5bc6a` in dark mode
- [x] Hero CTA primary button uses amber-gold fill with `#0b0e12` text
- [x] Mermaid pipeline diagram uses amber-gold fills (`fill:#e8952b`)
- [x] Reduce-motion guard present for card hover transitions
- [x] Primary buttons outside `.hero-section` use amber-gold fill (not Material's indigo default from `palette.primary: indigo`)

### Phase 1 — Astro marketing homepage

- [x] `astro build` exits 0; output lands in `build/` with Astro files at root
- [x] Homepage renders all 9 sections from [homepage-screen-flow.md](homepage-screen-flow.md) in order
- [x] Dark hero section (`#0b0e12`) runs continuously from viewport top to end of stat strip with no gap — nav, hero, and stat strip all use `--ds-hero-bg` with no inter-band margin
- [x] Stat strip text reads: `3 supervised loops · 7 adapters · 1 pip install` — rendered as number + label pairs separated by the design system's vertical rule (the `·` is notation for the stat row; separator is `1px solid --ds-hero-border` per design-system-foundations.md). The `0 self-certified builds` stat from the original screen-flow was dropped at owner request (2026-07-16); design-system-foundations.md permits a three-or-four-item strip.
- [x] Content sections between hero and footer-adjacent closer use the **light zone** (`--ds-surface` `#fafaf9` / `--ds-surface-alt` `#f0efed` for band alternation, per homepage-screen-flow.md §4/§7) — never a dark band; the Human Gates section is light zone with amber-bordered cards
- [x] Catalogue section shows exactly 3 pack cards always visible; expand affordance (`<details>` with a visible "See all 14 packs →" summary) reveals the remaining 11
- [x] Install section renders 4 tabs: Flagship loop, With discovery, Full inception, Solution architect (CSS-only radio-group tabs, zero JS)
- [x] Nav matches [information-architecture.md](information-architecture.md): `Logo | How it works | Packs | Journeys | Docs ↗ | [Install →]`
- [x] No inline `style=""` attributes and no hardcoded color values outside the token block; layout spacing (section/card padding, gaps, margins) uses the `--ds-space-*` / `--ds-radius-*` scale, except values the scale does not cover: media-query breakpoints, 1px/2px hairline borders, decorative icon sizing, component `max-width`s, the CTA padding `0.7rem 1.6rem` from design-system-foundations.md, and the sub-`--ds-space-1` micro-padding on inline chips/badges/pills, inline code, and the compact nav CTA (values below the 4px scale floor, where a token would be less legible than the literal)
- [x] `npx pa11y http://localhost:4321 --standard WCAG2AA` exits with 0 errors
- [x] `/404.html` branded 404 page emitted (via `web/src/pages/404.astro`)

### Phase 2 — Pack catalogue and journey pages

- [ ] `/packs/` renders an index of all 14 packs with name, scope tag, and tagline
- [ ] Each of the 14 packs has a `/packs/[slug]` page with: header, scope badge, skill list, install command, and journey link
- [ ] Each pack detail page shows: pack name, scope badge (`user`|`repo`), full skill list, install command, and a link to its journey page (or a "coming soon" state for packs whose journey page is not yet live)
- [ ] Journey page template renders the 8-section structure from [journey-page-template.md](journey-page-template.md)
- [ ] Three core journey pages authored: `/journeys/core`, `/journeys/discovery`, `/journeys/release`

### Phase 3 — Priority-2 journey pages

- [ ] Six journey pages authored and live: `/journeys/research`, `/journeys/architect`, `/journeys/experience`, `/journeys/contracts`, `/journeys/converters`, `/journeys/atlassian`
- [ ] Each of the six pages renders the full 8-section structure from [journey-page-template.md](journey-page-template.md)
- [ ] Journey index at `/journeys/` links to all 9 live journey pages (3 from Phase 2 + 6 from Phase 3); the remaining 5 show as "coming soon"
- [ ] The six corresponding pack detail pages (`/packs/research`, `/packs/architect`, `/packs/experience`, `/packs/contracts`, `/packs/converters`, `/packs/atlassian`) show an active journey link (not "coming soon")
- [ ] `npx pa11y http://localhost:4321/journeys/research --standard WCAG2AA` exits with 0 errors (verified on `research`; same template applies to all 6)

### Phase 4 — Remaining journey pages + SEO

- [ ] Five final journey pages authored: `/journeys/figma`, `/journeys/governance-extras`, `/journeys/credential-brokers`, `/journeys/monorepo-extras`, `/journeys/user-guide-diataxis`
- [ ] All 14 journey pages are live; journey index links to all 14
- [ ] `sitemap.xml` generated and served at `/sitemap.xml` listing all Astro routes
- [ ] `robots.txt` present at `/robots.txt`
- [ ] Every Astro page has a complete `<head>`: `<meta name="description">`, `<meta property="og:title">`, `<meta property="og:description">`, `<meta property="og:image">`; og:image is a static `social.png` in `web/public/`
- [ ] `<link rel="canonical">` on every Astro page resolving to the correct GitHub Pages URL

### CI + deploy (Phase 1 prerequisite)

- [x] GitHub Actions workflow: Astro builds first → MkDocs builds second → artifact uploaded from `build/` (verified locally end-to-end: `build/index.html` and `build/docs/index.html` coexist, proving Astro's outDir clean does not wipe MkDocs output)
- [x] `site/mkdocs.yml` `site_dir` is `../build/docs`
- [ ] Single GitHub Pages deploy serves Astro at `/` and MkDocs at `/docs/` (deferred: github-pages-first-deploy-verification — artifact structure verified locally, live serving confirmed on first deploy from `main`)

## Assumptions

- Technical: MkDocs `site_dir` is currently `built` — must change to `../build/docs` before CI wiring (source: `site/mkdocs.yml:9`)
- Technical: No Node.js or `web/` directory at repo root; Astro adds a Node.js build dependency — acknowledged, intentional (source: `ls` probe, `.github/workflows/pages.yml`)
- Technical: `.github/workflows/pages.yml` is Python-only; Node.js setup step must be added for Astro (source: `.github/workflows/pages.yml`)
- Technical: `tools/build-site.py` aggregates pack docs into `site/docs/` before MkDocs — continues unchanged in the new architecture (source: `.github/workflows/pages.yml`)
- Technical: `web/` is a new top-level directory requiring an RFC per AGENTS.md before Phase 1 EXECUTE begins (source: `AGENTS.md:184`)
- Product: Marketing site is the anchor; MkDocs reference docs are a subsection at `/docs/` (user confirmation 2026-07-16)
- Product: Option B — Alternating Conviction — amber-gold accent, dark hero + light content + dark closer (user confirmation 2026-07-16)
- Product: Primary audience is senior engineers and engineering leads evaluating adoption (user confirmation 2026-07-16)
- Process: Feature specs live under `docs/specs/<feature>/` per `docs/CONVENTIONS.md`
- Process: Shape is `mixed` — Astro marketing UI surface + GitHub Actions CI/CD integration
