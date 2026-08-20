# Spec: Site shared chrome

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0089, ADR-0085
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Readers can move between the marketing and documentation sites through one
clear destination vocabulary without having to relearn the product map. A
small renderer-neutral information-architecture contract drives both projects;
marketing keeps its product-oriented chrome and docs keeps its pinned
Starlight reading experience and independent palette.

## Boundaries

### Always do

- Store only destination IDs, labels, targets, groups, order, and target kind
  in `site.toml`; project renderer-local data through the existing generator.
- Use the exact approved taxonomy, copy, renderer treatments, focus/current
  semantics, and mobile disclosure behavior below.
- Preserve Starlight ownership of documentation navigation and controls.
- Render both projects independently in their existing palettes, components,
  tokens, spacing, and responsive systems.

### Ask first

- Add, remove, rename, or reorder a destination beyond this approved contract.
- Change the docs palette, supported Starlight override boundary, marketing
  CTA, current-location rules, or external-link treatment.
- Make the two renderers share runtime code, CSS, components, tokens, state, or
  breakpoint logic.

### Never do

- Align docs colors or components with `web/` merely to create visual
  similarity.
- Replace a Starlight-native title, search, theme, docs menu, sidebar,
  breadcrumb, table of contents, pagination, edit control, skip link, or content
  layout.
- Treat an internal combined-site path as external or expose renderer-specific
  presentation in the shared data contract.
- Add a dependency or restore `/work/` as a public destination.

## Approved content and behavior

### Marketing header

Render this exact order and destination contract:

1. **How it works** → `/#three-loops`
2. **Use cases** → `/#use-cases`
3. **Catalogue** → `/catalogue/`
4. **Now** → `/now/`
5. **Docs** → `/docs/`
6. **Try the build loop** → `/#install` as the existing CTA

Desktop and marketing-mobile disclosure use the same order and labels.

### Shared destination groups

Both renderer-specific footers use these exact groups and order:

- **Product:** How it works, Use cases, Catalogue, Packs, Journeys.
- **Docs:** Get started, Install, The three loops, All docs.
- **Project:** Now, Changelog, Contributing, Claude plugins, GitHub, PyPI.

| Group | Label | Target |
| --- | --- | --- |
| Product | How it works | `/#three-loops` |
| Product | Use cases | `/#use-cases` |
| Product | Catalogue | `/catalogue/` |
| Product | Packs | `/packs/` |
| Product | Journeys | `/journeys/` |
| Docs | Get started | `/docs/getting-started/` |
| Docs | Install | `/docs/getting-started/install/` |
| Docs | The three loops | `/docs/getting-started/three-loops/` |
| Docs | All docs | `/docs/` |
| Project | Now | `/now/` |
| Project | Changelog | `/docs/changelog/` |
| Project | Contributing | `/docs/contributing/` |
| Project | Claude plugins | `/plugins/` |
| Project | GitHub | existing canonical repository URL, unchanged |
| Project | PyPI | existing canonical package URL, unchanged |

Marketing keeps its existing brand and tagline:
`agent-ready-repo` and “The supervised AI operating model for software teams.”

The docs footer follows Starlight previous/next navigation, uses the same three
groups in the docs palette and content width, then ends with the quiet line
`© <year> · agent-ready-repo`. It does not repeat the marketing brand block or
tagline. At wide widths the groups form three columns; at phone widths they
form one readable sequence with no footer disclosures.

### Docs product orientation

Above the Starlight header, render one non-sticky product-orientation band:

> **Product** | How it works · Use cases · Catalogue · Now · **Docs**

`Product` links to `/`. `Docs` is the current destination on docs pages. The
band scrolls away; the pinned Starlight header remains sticky and singular.

At approved phone widths, show a **Product** disclosure beside the independent
**Docs** menu. The Product trigger is not a direct link. Its expanded contents
are Product home, How it works, Use cases, Catalogue, and Now, in that order,
inside a landmark named **Product navigation**. Opening or closing it does not
open, close, rename, or replace Starlight's Docs menu.

### Link, focus, and current-location rules

- All combined-site links are internal, base-qualified, open in the same tab,
  and have no external glyph or external-only relationship metadata.
- GitHub and PyPI are the only external shared-chrome destinations. They open
  in the same tab and append an `aria-hidden` `↗` plus visually hidden
  “external” text.
- Link kind is declared in canonical data, not inferred from hostname in a
  renderer. Starlight-managed content links keep native treatment.
- Each renderer supplies a visible `:focus-visible` outline and offset that is
  not color-only, clipped, or hidden; each existing skip link remains the first
  focusable control.
- Opening the Product disclosure leaves focus on its trigger, and native tab
  order exposes its links next. Open, hover, focus, and current states remain
  visually distinct.
- Exact destination pages use `aria-current="page"`. Catalogue uses
  `aria-current="location"` on pack and journey descendants. Docs uses
  `aria-current="page"` on `/docs/` and `aria-current="location"` throughout
  nested docs. Now uses `aria-current="page"` only on `/now/`. Homepage
  fragment destinations do not claim current state without client-side
  route/fragment evidence.
- Current state is distinguishable by shape or weight, not color alone, and the
  same semantic rule applies in footers.

### Explicitly not shared

CSS, components, color or type tokens, palettes, spacing, breakpoints, focus
implementation, disclosure state, JavaScript, Starlight internals, content
layout, and renderer-specific footer appearance are not shared. Shared chrome
means only the destination architecture and vocabulary above.

## Testing Strategy

- Canonical parsing, validation, ordering, and renderer projection use TDD in
  generator construction tests.
- Exact labels, hrefs, group/order, target kind, current semantics, route
  preservation, singular controls, and fragments use emitted HTML from both
  sites.
- Responsive disclosure, keyboard paths, focus visibility, overflow, and axe
  results use the `site-browser-quality-gate` matrix and recorded
  renderer-specific design review.

## Acceptance Criteria

- [x] `site.toml` is the sole renderer-neutral source for shared destination
  IDs, labels, targets, groups, order, and internal/external kind; it contains
  no CSS, token, breakpoint, state, or component prescription.
- [x] Generator validation rejects duplicate destination/group IDs, missing
  group references, unknown destination references in groups and in the ordered
  header and docs-navigation lists, repeated entries in those lists, invalid
  target kinds, and invalid internal target shape, and projects deterministic
  renderer-local data. Drift from the approved vocabulary — labels, targets,
  kinds, and header, group, and docs-navigation order — is rejected by a
  merge-blocking anchor test rather than by generator logic, because AC1 makes
  `site.toml` the sole source of that order; target resolution is rejected by
  `tools/check-rendered-site-links.py`.
- [x] Marketing header and mobile disclosure emit the exact six destinations,
  order, labels, targets, and existing CTA treatment approved above.
- [x] Marketing and docs footers emit the exact Product, Docs, and Project
  groups; marketing retains its brand/tagline, while docs uses the approved
  subordinate renderer-native treatment after Starlight pagination.
- [x] Desktop docs emits the exact non-sticky product-orientation band above one
  unchanged sticky Starlight header, with Product home and Docs current
  treatment as specified.
- [x] Phone docs emits the exact Product disclosure beside the independent Docs
  menu, with the approved landmark, item order, and isolated disclosure state.
- [x] Internal and external links follow the exact kind, base, same-tab, glyph,
  accessible-name, and relationship-metadata rules above; Docs is internal and
  only GitHub and PyPI are external.
- [x] Skip, focus-visible, exact-page `aria-current`, category-current, footer
  current, and homepage-fragment rules match the approved behavior and do not
  rely on color alone.
- [x] Starlight remains the singular owner of its title/header, search, theme,
  docs menu, sidebar, breadcrumbs, page title/description, table of contents,
  edit control, pagination, skip link, and content layout on home and nested
  guide routes.
- [x] Neither emitted project shares or imports the other renderer's CSS,
  components, palette, tokens, spacing, breakpoints, focus implementation,
  disclosure state, JavaScript, or Starlight internals.
- [x] `/now/` exists before shared navigation adopts it, `/work/` is absent
  from public shared chrome, all other existing routes/sidebar/pagination links
  still resolve, and combined page/fragment checks pass.
- [x] At 360, 375, 390, 414, and 1440 CSS-pixel widths in the approved themes,
  chrome has at most 1px horizontal overflow, is fully keyboard-usable, has
  visible focus, and produces zero serious or critical axe findings.
- [ ] Recorded design review finds no Major issue against either renderer's
  named aesthetic direction or the four tech-site principles.

## Acceptance evidence

Recorded 2026-08-20 against `main` at `fe26b042` plus this task's change. Each
criterion names what was run, not what was intended. AC13 is unticked: it is a
human judgement and is not self-certifiable.

| AC | Evidence |
| --- | --- |
| 1 | `site.toml [shared_chrome]` carries only `id`/`label`/`target`/`kind`/`group`; `validate_shared_chrome_contract` rejects unknown fields. Both renderers read projected inputs, not literals: `test_the_committed_marketing_shared_chrome_projection_matches_site_toml` and its docs counterpart fail on a hand-edited projection (mutation-proved). |
| 2 | Duplicate IDs, missing group members, unknown references in `header`/`docs_band`/`docs_product_navigation`, repeats, bad kinds and bad internal target shape each have a rejecting test in `tools/test_build_site_routing.py`. Vocabulary drift is caught by the merge-blocking anchor test; target resolution by `tools/check-rendered-site-links.py` — 63920 links across 270 pages, clean. |
| 3 | `rendered-output.test.ts` compares the emitted `.nav__links` and `.nav__drawer` against the projection: exact six destinations, order, labels, targets, and the CTA retaining `nav__cta`. |
| 4 | `rendered-output.test.ts` asserts the three marketing footer groups plus brand and tagline against the projection, and the same three groups in docs. Docs order is asserted as a relation, not a presence check: Starlight's `.pagination-links` must appear *before* the first shared group in document order, so a reversed footer fails. The quiet line `© <year> · agent-ready-repo` is asserted, as is the absence of the marketing brand block and tagline. |
| 5 | e2e `expectDocsChromeIsWellPlaced` over 20 docs cases relates the band to the header rather than querying each alone: `compareDocumentPosition` requires the band to precede the Starlight header, and where the band is displayed its top must be above the header's. `header.header` computes `position: sticky`; the band is never `position: fixed`; exactly one `header.header > div.header`. Removing `.main-frame`'s padding fails 16 of 20 (mutation-proved). |
| 6 | e2e `docs Product and Docs disclosures stay independent` drives BOTH controls at 360/375/390/414: opening Product leaves the Docs menu closed and its sidebar hidden; opening Docs leaves Product open and its trigger unrenamed; closing either leaves the other untouched. Coupling the two fails it (mutation-proved). |
| 7 | Kind is read from the data, never a hostname: `chromeHref` branches on `link.kind`, and `web/src/test/shared-chrome.test.ts` pins the discriminating case — a declared-external target without an http scheme is admissible data, since `_validate_internal_shared_target` runs only under `if kind == "internal"`. Emitted checks assert same-tab, base-qualification and no `rel` on internal links in **both** footers, and require the accessible name to read exactly `<label> external` with an `aria-hidden` `↗` on GitHub and PyPI only. Asserted semantically rather than by class name, because marketing and docs each hide the word with their own CSS and requiring one shared class would mandate the shared CSS AC10 forbids. |
| 8 | Emitted `aria-current` measured from the build: `/catalogue/` and `/now/` = 3× `page`; `/packs/core/` and `/journeys/core/` = 3× `location`; homepage fragment destinations carry none. Footer-scoped counts are asserted separately in both renderers, because the nav and mobile drawer alone satisfy any whole-document count, and no docs-footer `aria-current` may sit on a fragment target. Current state is carried by weight and underline, not colour alone. `expectSkipLinkFirst` runs on all 20 docs cases, and `expectVisibleFocusIndicator` requires each focused chrome control to *gain* an indicator it lacked at rest — suppressing docs focus styling fails it (mutation-proved). |
| 9 | `rendered-output.test.ts` asserts every control AC9 names on **both** the docs home and a nested guide route: one Starlight header, title, search, Docs-menu trigger, sidebar, skip link, `h1`, meta description, table of contents, mobile ToC, content layout, footer — plus the edit control and pagination where they render. The expected counts come from a control build with the `PageFrame` override disabled, so they record native Starlight behaviour: `starlight-theme-select` renders **twice** natively and `a[href="#_top"]` three times, and `.header` is not a singularity proxy since Starlight's Header emits `<div class="header">` and Expressive Code emits `<figcaption class="header">`. Native EditLink, LastUpdated and Pagination replaced the previously hand-rolled prev/next markup. |
| 10 | `test_neither_renderer_imports_the_other_renderers_chrome` sweeps **every** hand-written `.astro`/`.ts`/`.js`/`.css`/`.json` file under both `web/src` and `docs-site/src` — not a named-file list — for any JS import, re-export, `require`, CSS `@import`, or `url()` whose path climbs into the other renderer's tree. A cross-renderer CSS `@import`, and an import in a component the earlier named-list guard never covered, both fail it (mutation-proved). `test_each_renderer_reads_its_own_projected_input` adds that each renderer reads only its own projection and the docs projection exposes no `header` key. The palette half is additionally held by the existing no-marketing-token-dependency tests. |
| 11 | `/now/` exists and is linked; `test_the_public_work_surface_is_gone_from_marketing_inputs` checks the retired routes, the projection, and the marketing component sources for a `/work/` literal — the source scan fails when one is reintroduced (mutation-proved). `check-rendered-site-links.py` resolves every page and fragment. |
| 12 | `npm run test:e2e:gate --prefix web`. The docs matrix is 20 cases — `/docs/` and `/docs/guides/core/how-to/start-a-project/` × 360/375/390/414/1440 × light/dark — each asserting ≤1px horizontal overflow, zero serious or critical axe findings, resolvable fragments, and skip-link-first. Keyboard operability is asserted by operating the controls, not by inference: `expectDocsChromeIsKeyboardOperable` focuses the band link, the Product trigger and Starlight's Docs-menu trigger, opens the disclosure with **both** Enter and Space, requires focus to stay on the trigger, requires the disclosed links to follow it in tab order, and requires a visible focus indicator at each stop. Giving the disclosed links `tabindex="-1"` fails 16 of 20 (mutation-proved). Tap targets were re-measured across the same 20 cases: no demonstrated non-exempt failure, all 22 shared-chrome candidates conforming through SC 2.5.8's Spacing clause at 35.2–69.8px against a 24px threshold. |
| 13 | **Open.** Requires a recorded human design review against each renderer's named aesthetic direction and the four tech-site principles. Not self-certifiable. |

## Assumptions

- Technical: marketing owns current navigation/footer components, docs owns a
  custom Starlight footer, and `site.toml` already drives cross-renderer site
  generation (source: repository inspection on 2026-08-17).
- Technical: the docs product band can compose the pinned default header at a
  supported Starlight override seam without replacing its behavior (source:
  pinned Starlight contract and approved design decision 2026-08-17).
- Product: the complete taxonomy, wording, mobile behavior, link treatment,
  current/focus semantics, footer treatments, and non-shared boundaries above
  are accepted (source: user approvals 2026-08-17).
- Product: `/now/` is owned by `site-now-surface`; this spec consumes it only
  after the route exists and never restores public `/work/` (source: user
  approval 2026-08-17).
- Process: RFC-0089 and ADR-0085 remain ratified and preserve separate renderer
  projects, docs palette independence, and pinned Starlight behavior.
