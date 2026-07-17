# Plan: platform-site

- **Spec:** [spec.md](spec.md)
- **Status:** Executing

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The platform site ships in four phases gated by content readiness, not technical complexity. Phase 0 (CSS token alignment) is mostly complete; the remaining fix — a global `.md-button--primary` override to prevent Material's `palette.primary: indigo` from leaking into primary buttons outside the hero — is the first executable task.

Phase 1 scaffolds the Astro marketing site in `web/`. The hard constraint: **`web/` is a new top-level directory requiring an RFC before the first commit** (AGENTS.md § Check before acting). Until the RFC is accepted, Phase 1 EXECUTE is blocked; Phase 0b is the only deliverable in the current PR.

The riskiest implementation detail is build pipeline order: Astro's `astro build` cleans its output directory on each run. MkDocs must write to `build/docs/` *after* Astro has finished — if the order is wrong, MkDocs output is silently wiped. The fix is strict pipeline sequencing: Astro → `tools/build-site.py` → MkDocs, with `site_dir: ../build/docs` in `mkdocs.yml`.

Declined: a monorepo workspace setup at the repo root (`package.json` + `workspaces`). Unnecessary — only one JS package (`web/`) exists now; the single-package `npm --prefix web` pattern is simpler and avoids touching the root.

Declined (overrides homepage-screen-flow.md §3): JavaScript for install-tab switching and catalogue show-all toggle. `homepage-screen-flow.md` mentions JS for these interactions; this plan supersedes that with CSS-only patterns (`<details>`, `:has()`) — no runtime JS dependency on marketing pages improves load performance and removes a JS-disabled failure mode.

## Constraints

- AGENTS.md § "Check before acting": new top-level directory `web/` requires an RFC before Phase 1 EXECUTE
- `aesthetic-direction.md`: Option B confirmed; no aesthetic changes without amending that doc
- `design-system-foundations.md`: `--ds-*` tokens are the sole color/spacing authority on the Astro surface
- `homepage-screen-flow.md`: 9 sections in fixed order; changes require human sign-off per Boundaries
- GitHub Pages is static-only: no server-side rendering, no API routes

## Construction tests

**Integration (Phase 1):** After T7 (CI wiring), the GitHub Actions build exits 0 on a branch push. Manual end-to-end: `open http://localhost:4321` → `/packs/core` → `/journeys/core` → nav "Docs" link → `/docs/` loads. All four routes resolve.

**Manual verification:**
- Homepage: all 9 sections render in order; no layout gap between dark hero and light content
- Accessibility: `npx pa11y --standard WCAG2AA` exits 0 on homepage, pack index, one journey page
- Reduced-motion: disable animations in browser preferences; confirm no motion on card hover or hero fade-in

## Design (LLD)

### Component / module decomposition

```
web/src/
├── components/layout/
│   ├── SiteLayout.astro      — <html lang>, head, tokens + base imports, <slot/>
│   ├── SiteNav.astro         — Logo | How it works | Packs | Journeys | Docs ↗ | [Install →]
│   └── SiteFooter.astro      — minimal footer; links to /docs/, GitHub, PyPI
├── components/marketing/
│   ├── Hero.astro             — dark zone; headline, subhead, CTA pair; one-shot fade-in
│   ├── StatStrip.astro        — dark zone; 4-stat strip with · separators
│   ├── TheProblem.astro       — light zone; problem framing (section 3)
│   ├── ThreeLoops.astro       — light zone; pipeline visual (section 4)
│   ├── HumanGates.astro       — light zone; amber-bordered gate cards (section 5)
│   ├── AdapterMatrix.astro    — light zone; 7-agent table (section 6)
│   ├── InstallTerminal.astro  — light zone; 4-tab install (section 7)
│   └── PackCatalogue.astro    — light zone; 3-always + expand (section 8)
├── components/pack/
│   ├── PackCard.astro         — used on catalogue section + /packs/ index
│   └── PackHero.astro         — /packs/[slug] header
├── components/journey/
│   ├── JourneyHero.astro
│   ├── JourneyStage.astro     — one stage in the sequence narrative
│   └── GateDetail.astro       — gate card with expandable "what to check"
├── content/
│   ├── config.ts              — Zod schemas: packsCollection + journeysCollection
│   ├── packs/                 — 14 .md files
│   └── journeys/              — core.md, discovery.md, release.md (Phase 2)
├── pages/
│   ├── index.astro
│   ├── packs/
│   │   ├── index.astro
│   │   └── [pack].astro       — getStaticPaths from packs collection
│   └── journeys/
│       ├── index.astro
│       └── [journey].astro    — getStaticPaths from journeys collection
└── styles/
    ├── tokens.css             — --ds-* custom properties (from design-system-foundations.md)
    ├── base.css               — reset + body/h*/a base styles using --ds-* tokens
    └── global.css             — @import tokens, base
```

### State & control flow

Fully static Astro site. Client-side interactivity is minimal and JS-free where possible:
- **Catalogue expand:** `<details>/<summary>` — native, no JS
- **Install tabs:** CSS-only tab pattern using `:has()` or `<details>` — no JS
- **Mobile nav:** `<details>` hamburger — no JS
- **Hero fade-in:** CSS `@keyframes` behind `@media (prefers-reduced-motion: no-preference)` — no JS

### Quality attributes (NFRs)

- WCAG 2.2 AA: verified contrast in design-system-foundations.md; pa11y 0 errors per phase
- Reduce-motion: all `animation`, `transition`, `transform` guarded with `@media (prefers-reduced-motion: no-preference)`
- Build time: `astro build` < 30s locally on standard dev machine

## Tasks

### T0b: Global primary button override (Phase 0 remaining fix)

**Depends on:** none

**Tests:**
- Goal-based: `grep 'md-button--primary' site/docs/stylesheets/extra.css` returns the global rule (distinct from the `.hero-section .md-button--primary` rule)
- Visual/manual QA: `mkdocs serve`, navigate to `/getting-started/` or any page with a primary CTA outside the hero; button renders amber-gold (`#e8952b`), not indigo

**Approach:**
- Add a `/* ── Global primary CTA … */` section to `site/docs/stylesheets/extra.css` with a `.md-button--primary` rule: `background-color: #e8952b !important`, `color: #0b0e12 !important`, `border-color: #e8952b !important`
- Add matching hover rule: `background-color: #f5bc6a !important`
- The more-specific `.hero-section .md-button--primary` rule already in place takes precedence inside the hero (higher specificity + `!important`); no conflict

**Done when:** primary buttons outside `.hero-section` render amber-gold in `mkdocs serve`; Phase 0 AC "Primary buttons outside hero use amber-gold" is met.

---

### T1: RFC for `web/` top-level directory

**Depends on:** none

**Tests:**
- Process: RFC document exists at `docs/rfc/` proposing `web/` as the Astro marketing site directory
- Process: RFC status is Accepted before T2 EXECUTE begins

**Approach:**
- Invoke `new-rfc` skill: title "Add `web/` top-level directory for the Astro marketing site"
- Rationale in RFC: platform site requires Astro for full design freedom; `web/` is the conventional sibling to `site/` (the MkDocs source); the marketing surface cannot be fully expressed within MkDocs constraints; new dependency (Node.js) acknowledged

**Done when:** RFC document exists and reaches Accepted status (or user explicitly approves proceeding before full RFC ceremony).

---

### T2: Astro scaffold + design tokens

**Depends on:** T1 (RFC accepted)

**Tests:**
- Goal-based: `cd web && npm run build` exits 0; `../build/index.html` exists
- Goal-based: `web/astro.config.ts` contains `outDir: '../build'`
- Goal-based: `web/src/styles/tokens.css` contains `--ds-hero-bg: #0b0e12`
- Goal-based: `web/src/styles/base.css` sets `body { font-family }` using `--ds-*` tokens, not raw values

**Approach:**
- `npm create astro@latest web -- --template minimal --typescript strict --no-install`
- Set `outDir: '../build'` in `astro.config.ts`; `site` to the GitHub Pages URL
- Copy the full `--ds-*` primitive + semantic token block from `design-system-foundations.md` into `web/src/styles/tokens.css`
- `base.css`: CSS reset + `body { font-family: Inter, ... }`, `code { font-family: JetBrains Mono, ... }` using `--ds-*` tokens only
- `global.css`: `@import './tokens.css'; @import './base.css';`
- Add Inter + JetBrains Mono via `<link>` in SiteLayout (Google Fonts) or self-hosted in `web/public/fonts/`

**Touches:** `web/astro.config.ts`, `web/package.json`, `web/src/styles/tokens.css`, `web/src/styles/base.css`, `web/src/styles/global.css`

**Done when:** `npm run build` exits 0 in `web/`; `build/index.html` is a minimal Astro page; no hardcoded hex in base.css.

---

### T3: SiteLayout + SiteNav components

**Depends on:** T2

**Tests:**
- Visual/manual QA: `astro dev` → `/`; nav renders `Logo | How it works | Packs | Journeys | Docs ↗ | [Install →]`
- Accessibility: `<nav aria-label="Primary">` present; skip-nav link at top of page
- Visual/manual QA: at ≤ 768px hamburger appears; drawer stacks 5 items + CTA at bottom
- Reduced-motion: nav open/close transition guarded

**Approach:**
- `SiteNav.astro`: semantic `<nav aria-label="Primary">`; 5 items + amber `[Install →]` CTA right-anchored; `Docs ↗` has `rel="noopener"`, visual external-link affordance
- Mobile nav: `<details>/<summary>` hamburger — zero JS
- `SiteLayout.astro`: `<html lang="en">`, `<head>` with charset/viewport/title, Google Fonts link, `<link rel="stylesheet" href="/styles/global.css">`, `<slot/>`
- `SiteFooter.astro`: minimal; links to GitHub, PyPI, `/docs/`

**Touches:** `web/src/components/layout/SiteLayout.astro`, `SiteNav.astro`, `SiteFooter.astro`, `web/src/pages/index.astro`

**Done when:** nav correct on desktop and mobile; pa11y 0 errors on the skeleton page.

---

### T4: Homepage hero + stat strip

**Depends on:** T3

**Tests:**
- Visual/manual QA: hero background is `#0b0e12`; continuous from viewport top to end of stat strip; no white gap between header and hero
- Visual/manual QA: headline "The supervised AI operating model for software teams" (per [homepage-screen-flow.md](homepage-screen-flow.md)); subhead and two CTA buttons (amber primary, transparent secondary)
- Visual/manual QA: stat strip reads `3 supervised loops · 7 adapters · 1 pip install · 0 self-certified builds`
- Accessibility: one `<h1>` on page; heading level correct; CTAs are `<a href>` not `<div onclick>`
- Reduced-motion: hero opacity fade-in behind `@media (prefers-reduced-motion: no-preference)`; stat strip static

**Approach:**
- `Hero.astro`: full-bleed dark zone; grid texture + radial amber glow matching MkDocs `extra.css` hero; `<h1>`, `<p>`, two `<a>` CTAs in `.hero-actions`; `@keyframes fadeIn` opacity 0→1 300ms ease behind reduced-motion guard
- `StatStrip.astro`: `<p>` with four stat segments joined by `·`; `#0b0e12` background; `rgba(248,250,252,0.65)` text color

**Touches:** `web/src/components/marketing/Hero.astro`, `StatStrip.astro`, `web/src/pages/index.astro`

**Done when:** full-bleed dark zone from viewport top to stat strip end; correct stat text; fade-in fires on load; no layout gap.

---

### T5: Homepage content sections (light zone, sections 3–8)

**Depends on:** T4

**Tests:**
- Visual/manual QA: all 6 content sections render on `#fafaf9` surface
- Visual/manual QA: Human Gates section uses amber-bordered gate cards on `#fafaf9` — NOT dark background
- Visual/manual QA: catalogue section shows exactly 3 pack cards always visible; expand affordance reveals 11 more
- Visual/manual QA: install section shows 4 tabs with correct code blocks
- Accessibility: pa11y 0 errors on full homepage; tabs keyboard-navigable; expand affordance via `<details>` or `aria-expanded`

**Approach:**
- `TheProblem.astro`: 2-column text block introducing the supervised-loop proposition (section 3)
- `ThreeLoops.astro`: static pipeline SVG with amber loop nodes matching the Mermaid diagram (section 4); inline SVG, no runtime Mermaid
- `HumanGates.astro`: 3 gate preview cards, `border-left: 3px solid #e8952b`, light zone `#fafaf9` background (section 5)
- `AdapterMatrix.astro`: HTML table, 7 agents × 4 capabilities, from `index.md` adapter table (section 6)
- `InstallTerminal.astro`: 4-tab install code blocks (Flagship / With discovery / Full inception / Solution architect); CSS-only tabs using `:has()` or `<details>`; code blocks styled with `--ds-*` tokens (section 7)
- `PackCatalogue.astro`: first 3 pack cards (Core, Product Engineering, Release Engineering) always visible; `<details>` expander for remaining 11 (section 8)

**Touches:** `web/src/components/marketing/` (6 components), `web/src/pages/index.astro`

**Done when:** all 6 sections render on `#fafaf9`; pa11y 0 errors; Human Gates is light zone; catalogue expand works without JS.

---

### T6: Footer-adjacent closer + "Build Your Org" section

**Depends on:** T5

**Tests:**
- Visual/manual QA: section 9 ("Build Your Org" / "A foundation to build on") uses `#0b0e12` dark zone
- Visual/manual QA: dark zone picks up directly below the light content area with no gap
- Accessibility: CTA in the closer is an `<a>` not `<div onclick>`

**Approach:**
- `SiteFooter.astro`: dark zone closer (section 9 content + footer links); `background-color: #0b0e12`
- Include the "Adopt the catalogue as-is, or fork it" copy and the "How to build your org's catalogue" CTA from MkDocs `index.md`

**Touches:** `web/src/components/layout/SiteFooter.astro`, `web/src/pages/index.astro`

**Done when:** dark closer section visible; CTA links to `/docs/guides/_shared/how-to/build-an-org-stack-pack/`.

---

### T7: CI pipeline + mkdocs.yml site_dir

**Depends on:** T2 (Astro builds successfully)

**Tests:**
- Goal-based: `site/mkdocs.yml` line 9 reads `site_dir: ../build/docs`
- Goal-based: `.github/workflows/pages.yml` contains `actions/setup-node@v4` step before the Astro build step
- Goal-based: `build/` contains both `index.html` (Astro) and `docs/index.html` (MkDocs) after a full build run locally or on a branch
- Goal-based: GitHub Actions workflow exits 0 on a `main` push

**Approach:**
- Update `site/mkdocs.yml`: `site_dir: built` → `site_dir: ../build/docs`
- Update `.github/workflows/pages.yml` — the live workflow uses `actions/upload-pages-artifact` + `actions/deploy-pages`, not peaceiris; keep that mechanism and only adjust the steps:
  1. Add `actions/setup-node@v4` with `node-version: '22'` before the content-aggregate step
  2. Add `npm ci --prefix web` + `npm run build --prefix web` (Astro first — must run before MkDocs)
  3. Keep existing `pip install` + `python tools/build-site.py` + `mkdocs build` (MkDocs second)
  4. Change `path: site/built/` on `upload-pages-artifact` to `path: ./build`
- Add `web/package-lock.json` to the repo (generated by `npm install`)
- Pin the Astro version in `web/package.json` to a specific minor — not a floating range that could break CI

**Touches:** `site/mkdocs.yml`, `.github/workflows/pages.yml`, `web/package-lock.json`

**Done when:** GitHub Actions CI passes end-to-end; `build/docs/index.html` exists alongside `build/index.html`.

---

### T8: Content collections schema + pack pages

**Depends on:** T3

**Tests:**
- Goal-based: `web/src/content/config.ts` defines `packsCollection` with fields: `name`, `scope` (`user|repo`), `tagline`, `skills` (string[]), `installCommand`, `docsUrl`, `journeyUrl` (optional)
- Goal-based: `astro build` generates `/packs/index.html` and 14 `/packs/[slug]/index.html` files
- Visual/manual QA: pack index shows all 14 pack cards with name, scope badge, tagline
- Visual/manual QA: `core` detail page shows skill list, install command, link to `/journeys/core`

**Approach:**
- `web/src/content/config.ts`: define `packsCollection` Zod schema; `collections: { packs: packsCollection }`
- Author 14 `.md` files under `web/src/content/packs/` — one per pack; frontmatter matches schema; body = short description paragraph
- `web/src/pages/packs/index.astro`: `getCollection('packs')`, render grid of `PackCard` components
- `web/src/pages/packs/[pack].astro`: `getStaticPaths()` from packs collection; render `PackHero`, skill list, install block, journey link

**Touches:** `web/src/content/config.ts`, `web/src/content/packs/*.md` (14 files), `web/src/pages/packs/index.astro`, `web/src/pages/packs/[pack].astro`, `web/src/components/pack/PackCard.astro`, `PackHero.astro`

**Done when:** `astro build` generates all 14 pack routes; `core` and `research` detail pages render correctly.

---

### T9: Journey pages

**Depends on:** T8

**Tests:**
- Goal-based: `journeysCollection` schema in `config.ts` includes the full [journey-page-template.md](journey-page-template.md) fields: `humanGates` array with `id`, `globalGate`, `label`, `trigger`, `duration`, `whatToCheck`, `whatGoodLooksLike`, `whatBadLooksLike`, `consequence`; plus `skills`, `typicalSession`, `prerequisitePacks`, `docsUrl`, `packUrl`, `relatedJourneys`
- Goal-based: `astro build` generates `/journeys/core/index.html`, `/journeys/discovery/index.html`, `/journeys/release/index.html`
- Visual/manual QA: `core` journey page renders all 8 sections from [journey-page-template.md](journey-page-template.md); gate cards on light `#fafaf9` background with amber left border
- Visual/manual QA: `discovery` journey page links to `/packs/product-engineering` (not `/packs/discovery`); `release` links to `/packs/release-engineering`

**Approach:**
- Extend `web/src/content/config.ts` with `journeysCollection` Zod schema containing all fields from [journey-page-template.md](journey-page-template.md) frontmatter (see schema detail above in T9 schema note)
- Two journey slugs ≠ pack slugs: `discovery` → `product-engineering` pack, `release` → `release-engineering` pack; `getStaticPaths` derives `packUrl` from a static slug-to-pack mapping, not identity
- Author 3 `.md` files: `web/src/content/journeys/core.md`, `discovery.md`, `release.md`; frontmatter matches schema; body = staged narrative text (Section 4 of template)
- `web/src/pages/journeys/[journey].astro`: `getStaticPaths()` from journeys collection; renders all 8 sections using `JourneyHero`, `JourneyStage`, `GateDetail` components; all sections use light zone `#fafaf9` — no dark band on journey pages
- `web/src/pages/journeys/index.astro`: links to 3 Phase-2 journeys; remaining 11 shown as "coming soon"
- `GateDetail.astro`: renders `trigger`, `duration`, `whatGoodLooksLike`, `whatBadLooksLike`, `consequence` expandable; amber left border on light background

**Touches:** `web/src/content/config.ts`, `web/src/content/journeys/*.md` (3 files), `web/src/pages/journeys/`, `web/src/components/journey/*.astro`

**Done when:** 3 journey pages render all 8 sections; gate cards are light-zone with amber borders; `discovery` and `release` pack links resolve correctly.

### T10: Priority-2 journey pages (Phase 3)

**Depends on:** T9

**Tests:**
- Goal-based: `astro build` generates all six routes: `/journeys/research`, `/journeys/architect`, `/journeys/experience`, `/journeys/contracts`, `/journeys/converters`, `/journeys/atlassian`
- Visual/manual QA: spot-check `research` and `atlassian` journey pages for all 8 sections; gate cards on light background with amber borders
- Goal-based: journey index at `/journeys/` links to all 9 live journey pages; remaining 5 show "coming soon"
- Goal-based: the 6 corresponding pack pages (`/packs/research`, `/packs/architect`, `/packs/experience`, `/packs/contracts`, `/packs/converters`, `/packs/atlassian`) now show active journey links (not "coming soon")
- Goal-based: `npx pa11y http://localhost:4321/journeys/research --standard WCAG2AA` exits 0 errors

**Approach:**
- Author 6 `.md` files under `web/src/content/journeys/` — one per pack; frontmatter matches the full `journeysCollection` schema from T9; body = staged narrative authored from each pack's skill list and gate definitions in the existing MkDocs docs (`/docs/guides/<pack>/`)
- Update `/journeys/index.astro` to show all 9 live journeys; mark the remaining 5 as "coming soon"
- Update the 6 corresponding pack content files (`web/src/content/packs/*.md`) to set `journeyUrl` to the now-live journey URL (removing the "coming soon" flag)

**Touches:** `web/src/content/journeys/research.md`, `architect.md`, `experience.md`, `contracts.md`, `converters.md`, `atlassian.md`; `web/src/content/packs/research.md`, `architect.md`, `experience.md`, `contracts.md`, `converters.md`, `atlassian.md`; `web/src/pages/journeys/index.astro`

**Done when:** `astro build` generates all 6 routes; pa11y 0 errors on `research` journey; 6 pack pages show active journey links.

---

### T11: Final journey pages (Phase 4)

**Depends on:** T10

**Tests:**
- Goal-based: `astro build` generates all 5 remaining routes: `/journeys/figma`, `/journeys/governance-extras`, `/journeys/credential-brokers`, `/journeys/monorepo-extras`, `/journeys/user-guide-diataxis`
- Goal-based: journey index links to all 14 journey pages
- Goal-based: every pack detail page links to its corresponding live journey page (no "coming soon" links on pack pages)

**Approach:**
- Author 5 `.md` files under `web/src/content/journeys/`
- Update `/journeys/index.astro` to show all 14 live journeys (no "coming soon")
- Update each pack detail page's journeyUrl frontmatter to resolve to the now-live journey

**Touches:** `web/src/content/journeys/` (5 files), `web/src/pages/journeys/index.astro`

**Done when:** all 14 journey pages live; journey index complete; no "coming soon" placeholders remaining.

---

### T12: SEO metadata + sitemap + robots.txt (Phase 4)

**Depends on:** T11

**Tests:**
- Goal-based: `build/sitemap.xml` exists and contains all Astro routes (home, /packs/index, 14 pack detail, /journeys/index, 14 journey detail)
- Goal-based: `build/robots.txt` exists; allows all crawlers; references `sitemap.xml`
- Goal-based: `grep 'og:title' build/index.html` returns a non-empty content value
- Goal-based: `build/social.png` exists in `build/` as the og:image target
- Goal-based: every Astro page has `<link rel="canonical">` resolving to the correct GitHub Pages URL

**Approach:**
- `SiteLayout.astro`: accept `title`, `description`, `ogImage` props; emit `<title>`, `<meta name="description">`, `og:title`, `og:description`, `og:image`, `<link rel="canonical">`; default ogImage to `/social.png`
- Create `web/public/social.png` — a static 1200×630 social card (dark zone `#0b0e12` background, site name, tagline in white/amber)
- Install `@astrojs/sitemap` integration; configure in `astro.config.ts` with the GitHub Pages `site` URL
- Create `web/public/robots.txt`: `User-agent: *`, `Allow: /`, `Sitemap: https://<org>.github.io/agent-ready-repo/sitemap.xml`
- Update every page to pass correct `title` + `description` props to `SiteLayout`

**Touches:** `web/src/components/layout/SiteLayout.astro`, `web/public/social.png`, `web/public/robots.txt`, `web/astro.config.ts`, all page files for title/description props

**Done when:** sitemap.xml lists all routes; every page has og:title + canonical; robots.txt present.

## Rollout

- **Delivery:** per-phase PRs; Phase 0b is the current PR; Phase 1 is a standalone PR after T1 RFC is accepted; Phases 2–4 are content-gated PRs
- **Infrastructure:** GitHub Pages; existing deploy; pipeline change in T7 is the structural gate for first live deploy
- **Sequencing:** T7 must ship before any Phase 1 content is served live; Phases 2 content files can be authored before T7 if kept on a branch
- **Rollback:** revert the PR; the previous MkDocs-only pipeline (before T7) is the fallback; `site_dir: built` revert restores the prior working state

## Risks

- **Build pipeline order:** if MkDocs runs before Astro, Astro's clean step wipes `build/docs/`. Loud failure (wrong CI artifact), caught immediately.
- **Node.js in CI:** first Node.js run in this CI; `actions/setup-node@v4` is stable but requires `.nvmrc` or a pinned `engines.node` in `web/package.json` to prevent version drift.
- **RFC gate on `web/`:** Phase 1 EXECUTE cannot begin until the RFC is accepted. If the RFC cycle takes time, T0b is the only deliverable in the current PR.

## Changelog

- 2026-07-16: initial plan; Phase 0 (CSS token swap) complete except T0b; Phase 1 and Phase 2 tasks fully planned
- 2026-07-16: Phase 1 build (T2–T7). Deviations from the plan as written, all
  minor: (a) T6 section 9 ("Build Your Org") lives in its own homepage-scoped
  `BuildYourOrg.astro` rendered last in `index.astro` — NOT in `SiteFooter.astro`
  as decomposed — because `SiteFooter` is shared across all marketing pages and
  section 9 is homepage-specific; it still merges visually with the dark footer.
  (b) Added a reusable `Section.astro` band wrapper (not in the decomposition) to
  keep the six content sections DRY. (c) `astro.config` is `.ts` per the plan;
  `base` left at `/` for Phase 1 (root-served, matching the pa11y gate) — the
  production sub-path is still to be confirmed (information-architecture.md).
  (d) RFC-0061 accepted; its follow-on ADR (Astro SSG + one-Pages-deploy + Node
  dependency) and `web/AGENTS.md` dependency record co-land in this PR.
  (e) PackCatalogue uses a `<details>` expander with a visible "See all 14 packs →"
  summary (satisfying the spec's 3-visible + expand-11 AC and screen-flow's
  "label visible in initial render" requirement), but does NOT implement the
  finer "peek" refinement from homepage-screen-flow.md §8 (first Tier-2 row
  partially visible behind a fade). Deferred: the peek adds meaningful CSS
  complexity for a marginal disclosure gain; the visible summary already signals
  more content. Revisit if the expander's discoverability tests poorly.
  (f) Added `web/src/pages/404.astro` (Phase-1 spec-inventory deliverable;
  Astro emits `404.html` only when this page exists).
