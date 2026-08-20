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

- [ ] `site.toml` is the sole renderer-neutral source for shared destination
  IDs, labels, targets, groups, order, and internal/external kind; it contains
  no CSS, token, breakpoint, state, or component prescription.
- [ ] Generator validation rejects duplicate destination/group IDs, missing
  group references, unknown destination references in groups and in the ordered
  header and docs-navigation lists, repeated entries in those lists, invalid
  target kinds, and invalid internal target shape, and projects deterministic
  renderer-local data. Drift from the approved vocabulary — labels, targets,
  kinds, and header, group, and docs-navigation order — is rejected by a
  merge-blocking anchor test rather than by generator logic, because AC1 makes
  `site.toml` the sole source of that order; target resolution is rejected by
  `tools/check-rendered-site-links.py`.
- [ ] Marketing header and mobile disclosure emit the exact six destinations,
  order, labels, targets, and existing CTA treatment approved above.
- [ ] Marketing and docs footers emit the exact Product, Docs, and Project
  groups; marketing retains its brand/tagline, while docs uses the approved
  subordinate renderer-native treatment after Starlight pagination.
- [ ] Desktop docs emits the exact non-sticky product-orientation band above one
  unchanged sticky Starlight header, with Product home and Docs current
  treatment as specified.
- [ ] Phone docs emits the exact Product disclosure beside the independent Docs
  menu, with the approved landmark, item order, and isolated disclosure state.
- [ ] Internal and external links follow the exact kind, base, same-tab, glyph,
  accessible-name, and relationship-metadata rules above; Docs is internal and
  only GitHub and PyPI are external.
- [ ] Skip, focus-visible, exact-page `aria-current`, category-current, footer
  current, and homepage-fragment rules match the approved behavior and do not
  rely on color alone.
- [ ] Starlight remains the singular owner of its title/header, search, theme,
  docs menu, sidebar, breadcrumbs, page title/description, table of contents,
  edit control, pagination, skip link, and content layout on home and nested
  guide routes.
- [ ] Neither emitted project shares or imports the other renderer's CSS,
  components, palette, tokens, spacing, breakpoints, focus implementation,
  disclosure state, JavaScript, or Starlight internals.
- [ ] `/now/` exists before shared navigation adopts it, `/work/` is absent
  from public shared chrome, all other existing routes/sidebar/pagination links
  still resolve, and combined page/fragment checks pass.
- [ ] At 360, 375, 390, 414, and 1440 CSS-pixel widths in the approved themes,
  chrome has at most 1px horizontal overflow, is fully keyboard-usable, has
  visible focus, and produces zero serious or critical axe findings.
- [ ] Recorded design review finds no Major issue against either renderer's
  named aesthetic direction or the four tech-site principles.

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
