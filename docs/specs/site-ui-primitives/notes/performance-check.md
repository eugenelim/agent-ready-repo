# Performance check — site-ui-primitives

Verified 2026-07-28. `npm run build` run in web/ before recording these
measurements.

---

## JavaScript bundle sizes

**Criterion:** No new JavaScript bundles > 5 kB gzipped introduced.

| Bundle | Size (uncompressed) | Notes |
|--------|---------------------|-------|
| *(none)* | — | `build/_astro/` contains no `.js` files |

The web site produces **zero JavaScript bundle files**. All component behavior
is delivered via inline `<script>` tags (< 200 bytes each) scoped to the pages
that need them:

- `CopyButton.astro` — clipboard write + live-region injection (~180 bytes)
- `TaskSwitcher.astro` (`type="tabs"` only) — ARIA tab management (~170 bytes)

These are not separate files; they are embedded in the page HTML. They do not
appear as `.js` entries in `build/_astro/`.

**Result: PASS** — AC15 criterion met; no new JS bundles introduced.

---

## docs-site JavaScript

Starlight ships its own JS (pagefind search, theme toggle, table-of-contents).
These are pre-existing and not introduced by this spec. The primitive components
added to `docs-site/src/components/primitives/` are CSS-only and add no JS to
the docs bundle.

---

## Console errors and network errors (browser check)

**Criterion:** Zero new console errors or network errors on fixture page or any
existing public page.

**Status:** Partial — browser-side check deferred to T20 (Playwright). The
static HTML output has been reviewed and no obvious error conditions are present
(no missing `src` attributes, no broken internal asset references).

---

## Layout shift (CLS)

**Criterion:** CLS = 0 on fixture page.

**Status:** Pending T20 (Playwright). Components use fixed heights or
`min-height` where content varies (WriteConfirmation, DecisionBand, StatusChip).
No lazy-loaded images or late-resolving fonts are introduced by the primitives
(fonts are self-hosted via `@fontsource`; tokens.css extension adds
CSS custom properties only).

---

## CSS bundle sizes

| File | Size (uncompressed) |
|------|---------------------|
| SiteLayout.css | 68 K |
| primitives-fixture.css | 24 K |
| \_pack\_.css | 8 K |
| index.css (catalogue) | 20 K |
| index.css (home) | 8 K |
| \_journey\_.css | 12 K |

The 24 K `primitives-fixture.css` is fixture-page-only (noindex, not linked from
nav). Production page CSS bundles are unchanged in size relative to pre-change
baseline (fixture CSS is not loaded on any public page).
