# Spec: docs-wayfinding-cluster

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs-site-design-refresh`](../docs-site-design-refresh/spec.md), [`docs-site` aesthetic direction](../docs-site-design-refresh/creative-direction.md), [`guides-sidebar-generation`](../guides-sidebar-generation/spec.md), [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md)
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A reader can choose a useful documentation path within the first viewport,
move to the adjacent guide in the published reading order, and identify the
current page's place in the docs hierarchy. The landing, pager, and breadcrumb
trail express the docs surface's dominant goal of instrument-grade clarity
while retaining its established typography, palette, and accessibility floor.

This spec closes the three ordered wayfinding follow-ups registered by the
2026-08-14 tech-site design review. It defines their shared acceptance contract
without duplicating the register-owned problem statements or prescribed fixes.

## Boundaries

### Always do

- Verify user-visible behavior against a cache-cleared built site using the
  canonical `web` then `docs-site` build order.
- Preserve the generated guide sidebar's current slugs, labels, ordering,
  `_shared` placement, `_reference` placement, current-page state, and
  active-ancestor expansion.
- Keep the docs palette self-contained and cool-neutral/cobalt, retain the
  display serif only at display roles, and hold the existing responsive,
  focus-visible, reduced-motion, and WCAG AA floors.
- Record every added or changed dependency on pinned Starlight route data in
  `docs-site/AGENTS.md`.

### Ask first

- Any change to guide taxonomy, sidebar generation, guide labels, or published
  guide order.
- Any change to `web/` or to the visual relationship between the two site
  surfaces.
- Any guide prose, frontmatter, or route change.

### Never do

- Name the external reference site in a tracked file or Git artifact.
- Align docs colors to `web/`'s amber system, add a CSS framework, or add an npm
  dependency.
- Rework the shipped description/deck plumbing, inline-code treatment, mobile
  marketing hero, marketing CTA hierarchy, or drawer touch targets.
- Rebuild the already-shipped guide inventory or sidebar projection to restore
  pagination.

## Testing Strategy

The landing and breadcrumb treatments use a named **Playwright / axe built-site
journey** against the real rendered site because hierarchy, above-fold
orientation, wrapping, focus, overflow, and theme quality are browser outcomes.
Built-HTML integration assertions provide the repeatable floor for card count
and descriptions, CTA hierarchy, breadcrumb semantics, retained sidebar state,
and pager adjacency.

Pagination uses a **goal-based integration check**: every sidebar-backed guide
page in the built tree exposes the expected `rel="prev"` and/or `rel="next"`
links from sidebar order. Repository gates cover source-link validity,
guide-title consistency, contrast, type/build correctness, and serious or
critical accessibility violations.

## Acceptance Criteria

- [x] **AC1 — Landing orientation.** At 1440×900 with the page at scroll top,
  the docs landing shows its title, one-line deck, start action, prominent
  Pagefind search, and the first outcome-card row within the viewport; its title
  uses the docs heading scale, not marketing display scale. “Prominent search”
  means the full text-labelled search trigger—not its compact icon-only form—is
  visible and entirely inside the first viewport.
- [x] **AC2 — Outcome entry points.** The landing renders one description-
  bearing link card for each of the seven canonical outcome labels asserted by
  `tools/test_catalogue_navigation.py`; every card resolves to an existing docs
  route, and the already-designated flagship build loop is visually primary
  rather than presenting seven equal-weight choices. The flagship is the first
  card in a dedicated full-row lead region; the other six follow in a separate
  supporting grid, and its primacy does not rely on color alone.
- [x] **AC3 — CTA hierarchy.** The landing renders exactly one primary action;
  the browse action uses Starlight's minimal/text-link treatment rather than a
  second filled action.
- [x] **AC4 — Guide pagination.** Every sidebar-backed guide page in the built
  site renders at least one adjacent-page link, and each interior guide page's
  `rel="prev"` and `rel="next"` targets match its immediate neighbors in the
  generated sidebar order.
- [x] **AC5 — Sidebar preservation.** The generated guide navigation retains
  exact leaf slug/label order, current-page marking, and open ancestors on a
  representative nested guide page; `tools/build-site.py` and `site.toml`
  remain unchanged.
- [x] **AC6 — Breadcrumb coverage.** Every non-home built docs page that renders
  `h1#_top` also renders one `nav[aria-label="Breadcrumb"]`; the docs home
  renders none.
- [x] **AC7 — Breadcrumb semantics.** A nested guide trail contains a linked
  Docs root, its guide and pack ancestry, its quadrant, and one unlinked current
  item marked `aria-current="page"`. The detached site-wide platform back-link
  is absent.
- [x] **AC8 — Responsive and accessibility floor.** The landing and a nested
  guide introduce no horizontal body overflow at 375 px in either theme,
  keyboard focus remains visible, breadcrumb content wraps without clipping,
  and axe reports zero serious or critical violations. A tracked Playwright
  journey runs this route × theme matrix against the built site and also checks
  the AC1/AC2 desktop layout postconditions.
- [x] **AC9 — Pinned-contract record.** `docs-site/AGENTS.md` records the Footer
  pagination and breadcrumb route-data touchpoints alongside the existing
  PageTitle and markdown-pipeline contracts.
- [x] **AC10 — Built delivery.** The cache-cleared full build, rendered-output
  suite, guide-title lint, documentation-entry link checks, contrast gate, and
  relevant repository lint all pass; the product changelog records the
  reader-visible wayfinding change.

## Assumptions

- Technical: the surface is Astro 7.1.0 with exact-pinned Starlight 0.41.4;
  Footer pagination and sidebar ancestry are available through typed
  `Astro.locals.starlightRoute` data (source: `docs-site/package.json` and
  installed Starlight 0.41.4 route-data/default-component sources).
- Technical: the landing can use Starlight's shipped `CardGrid`/`LinkCard`
  components and the Hero action's supported `minimal` variant without a new
  dependency (source: installed Starlight 0.41.4 component/schema sources).
- Product: adopting engineers are primary, and instrument-grade clarity
  outranks display gravitas for navigation decisions (source:
  `docs/specs/docs-site-design-refresh/creative-direction.md`).
- Product: the batch proceeds without first shaping cross-surface principles;
  broader palette, illustration, and typography questions remain open (source:
  `workspace.toml`; user confirmation 2026-08-15).
- Process: the work runs in full mode with separate scope and plan approval
  gates, built-output verification, and no Git ref mutation (source:
  `AGENTS.md`, `docs/CONVENTIONS.md`, and enterprise session constraints).
- Process: docs retain their cobalt/cool-neutral palette; `web/` appearance and
  previously shipped polish work stay out of scope (source:
  `docs-site/AGENTS.md` and `docs/specs/tech-site-polish-batch/spec.md`).
