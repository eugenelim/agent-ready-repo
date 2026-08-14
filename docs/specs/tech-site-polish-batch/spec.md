# Spec: tech-site-polish-batch

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0061 (`web/` top-level directory), platform-site spec, [`docs-site-design-refresh`](../docs-site-design-refresh/spec.md) (docs palette divergence)
- **Brief:** in-session design review (2026-08-14) of both site surfaces rendered at 1440×900 and 360/375/390/414 phone widths, light and dark, benchmarked against an external reference docs site (supplied in-session; deliberately not named in-tree). The review produced 2 blockers, 7 majors, 8 minors; this spec takes the mechanical subset — the items that need no new IA, no new convention, and no design direction.
- **Contract:** none
- **Shape:** build

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Objective

Close the measured, mechanical defects on both site surfaces so the rendered
output matches the design intent already recorded in the platform-site and
`docs-site-design-refresh` specs.

Three of these are floor breaches with observable failure, not polish:
38 of 216 generated docs pages render two `<h1>` elements (usually with
divergent text); wide markdown tables in the docs scroll horizontally but
cannot be reached by keyboard; and the marketing hero pushes its primary CTA
roughly 450 px below the fold on a common phone viewport. The remainder are
visual-hierarchy defects with the same character: the intent exists in the
design system, the rendered page does not honour it.

## Boundaries

### Always do

- Verify every claim against the **rendered build**, not the source. Each
  acceptance criterion below is measured from built HTML or a real browser.
- Hold the existing floors: no horizontal body scroll at 375 px; text pairs
  ≥ 4.5:1 in both themes; `:focus-visible` visible; transitions stay inside
  `@media (prefers-reduced-motion: no-preference)`.
- Keep the two palettes separate. `docs-site/AGENTS.md` forbids aligning docs
  colour to `web/`'s amber system without a new spec; this spec does not
  amend that and must not work around it.
- Re-run `python3 tools/check-docs-contrast.py` after any docs palette touch.

### Ask first

- Any change to sidebar IA, breadcrumb structure, or the docs landing page
  layout — all three are real findings from the same review, all three need
  design decisions, and all three are explicitly **out of this spec**.
- Backfilling `summary:` frontmatter into the 142 guides that have none.

### Never do

- Add a CSS framework — banned by the platform-site spec.
- Add a runtime CDN call, or a new npm dependency, to either site.
- Name the reference site in any tracked file or commit message.
- Rewrite guide prose to fit a template. This spec changes rendering and
  generation only; guide bodies are edited solely where a duplicate heading is
  removed **or reconciled with the frontmatter title**. Nine guides took the
  reconciliation path — the H1 now repeats the title verbatim, which always
  meant adopting the shorter of the two strings. `guides/_shared/**` ships
  verbatim into adopter catalogues where frontmatter never renders, so deleting
  those headings was not an option. Which of the two strings is the *better*
  title is an editorial call this spec does not make; it is queued as
  `guide-title-wording-review`.

## Acceptance criteria

- [x] **AC1 — No generated docs page renders more than one `<h1>`.** Measured
  by parsing `build/docs/**/index.html`: pages with `len(<h1> in <main>) > 1`
  is `0` (baseline: 38 of 216).
- [x] **AC2 — Title divergence is a gate, not a silent double.** A repo lint
  fails when a guide's frontmatter `title` and its body `# ` heading differ
  beyond case and punctuation normalisation, so the two cannot drift apart
  again. The lint runs in the docs CI path.
- [x] **AC3 — Guide `summary` reaches the rendered page as `description`.**
  Every guide that declares `summary:` emits a non-empty
  `<meta name="description">` in its built page (baseline: 0 of 46), and the
  same string renders as a visible deck directly under the page title.
- [x] **AC4 — Marketing primary CTA is above the fold at 390×844.** The
  bounding box of the hero's primary CTA has `bottom <= 844` with the page
  scrolled to top (baseline: top edge ≈ 1290).
- [x] **AC5 — Hero has one primary CTA.** The secondary action renders at a
  visibly lower weight than the primary (not a second filled or equally
  sized button).
- [x] **AC6 — Inline code in docs prose is not accent-tinted.** Inline
  `<code>` outside `<pre>` uses a neutral ground and neutral text in both
  themes, and its contrast against that ground stays ≥ 4.5:1.
- [x] **AC7 — Marketing footer carries labelled link columns** covering the
  navigable surfaces that exist today (product, docs, project), replacing the
  current flat three-link row.
- [x] **AC8 — Every horizontally scrollable region in the docs is keyboard
  reachable.** axe reports no `scrollable-region-focusable` violation on a
  built guide page containing wide tables (baseline: 1–3 violations on
  `guides/_shared/reference/agentbundle`), at 360/375/390/414 px.
- [x] **AC9 — Marketing mobile drawer items are full-width touch targets.**
  With the drawer open at 375 px, every drawer link's bounding box is
  ≥ 44 px tall and spans the drawer's content width (baseline: 17 px tall,
  49–87 px wide).
- [x] **AC10 — No regression on the floors.** Across both surfaces at
  360/375/390/414 px and 1440 px: body horizontal overflow is `0`, and axe
  reports zero serious-or-critical violations.

## Testing strategy

| AC | Mode | Mechanism |
| --- | --- | --- |
| AC1, AC3 | Goal-based | Python parse of `build/docs/**/index.html` after a full build |
| AC2 | TDD | New lint script with fixture cases (matching pair passes, divergent pair fails) |
| AC4, AC5, AC7, AC9 | Visual / manual QA | Playwright measurement + screenshot of the real built pages |
| AC6 | Visual / manual QA | Computed-style read in both themes + `check-docs-contrast.py` |
| AC8, AC10 | Goal-based | axe-core sweep across both surfaces at five viewports |

The measurement harness used to produce the baselines already exists in this
session's scratch directory; it is re-run unchanged to demonstrate each
criterion, and the AC-bearing subset is committed under `web/src/test/` so the
result is reproducible rather than a one-off observation.

## Assumptions

- Starlight's `description` frontmatter field is the correct carrier for the
  guide `summary` string; no separate deck field is introduced.
- The 142 guides with no frontmatter keep rendering without a deck until the
  separate backfill lands. AC3 is scoped to guides that declare `summary:`.
- `docs-site` already emits a sitemap via Starlight's bundled
  `@astrojs/sitemap` (verified in this session) — nothing to do here.

## Out of scope (findings from the same review, deferred deliberately)

The register is `workspace.toml [backlog].open`, under the
`Tech-site design review 2026-08-14` header — it is canonical, and each slug
carries the context a cold-start session needs. Restating the set here would
give it two owners and guarantee drift, so this section names the slugs only:

`docs-landing-orientation-hub`, `docs-sidebar-guide-tree`,
`docs-breadcrumb-trail`, `guide-typed-asides-conversion`,
`guide-summary-backfill`, `site-shared-chrome-band`,
`guide-title-wording-review`, `rehype-plugin-unit-tests`,
`docs-tap-target-audit`, `site-design-principles`.

## Verified measurements (against the built output, 2026-08-14)

| AC | Baseline | After |
| --- | --- | --- |
| AC1 multi-`h1` pages | 38 of 216 | **0 of 216** |
| AC2 title-divergence lint | none | 9 divergences found and reconciled; lint green, wired into `docs.yml` |
| AC3 guide pages with their own meta description | 0 | **46**; deck renders |
| AC4 hero primary CTA at 390×844 | top ≈ 1290 | **bottom = 499** |
| AC5 hero primary CTAs | 2 filled | **1** |
| AC6 inline code ground | accent tint (dark) | neutral in both themes; contrast gate green |
| AC7 footer | 3 flat links | **3 labelled columns, 14 links** |
| AC8 `scrollable-region-focusable` on the wide-table guide | 1–3 at 360/375/390/414 | **0 at all four** |
| AC9 drawer link targets at 375 px | 17 px tall, 49–87 px wide | **44 px tall, 335 px wide (full width)** |
| AC10 floors, both surfaces × 5 viewports | 114 px overflow on `/`; 2 serious axe | **0 overflow, 0 serious axe** |

Gates at completion: `vitest` 61/61, `lint-ruff` 0, `lint-guide-titles` 0,
`check-docs-contrast` 0.
