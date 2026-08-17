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

Readers can move between the marketing and documentation sites without having
to relearn destination names or wonder whether they have left the product. A
small shared information-architecture contract drives both renderers, while
each site keeps the visual system and native controls suited to its reading
mode.

## Boundaries

### Always do

- Share destination labels, targets, grouping, and internal/external semantics
  through repository-owned data rather than duplicated renderer literals.
- Preserve the marketing route contract and Starlight's title, search, theme,
  sidebar, and pagination behavior.
- Render the shared contract independently in each site's existing palette and
  component system.

### Ask first

- Add, remove, rename, or reorder a destination beyond the approved current
  marketing taxonomy.
- Change the docs palette, Starlight override boundary, or marketing CTA.
- Introduce a new route or make the two renderers share runtime code or CSS.

### Never do

- Align docs colors or tokens with `web/` merely to create visual similarity.
- Replace a Starlight-native control with custom shared chrome.
- Add a dependency or treat an internal path as an external destination.

## Testing Strategy

- Canonical navigation parsing, validation, and renderer projection use TDD
  through generator construction tests.
- Labels, hrefs, order, internal/external treatment, routes, and fragments use
  goal-based assertions against emitted HTML from both sites.
- Responsive layout, keyboard behavior, and visual identity use deterministic
  browser checks plus recorded design review in each renderer's own themes.

## Acceptance Criteria

- [ ] `site.toml` is the canonical repository source for shared product
  destination labels, targets, group order, and internal/external semantics
  consumed by both renderers.
- [ ] Generator validation rejects duplicate destination IDs, duplicate group
  IDs, missing group references, invalid target kinds, and internal targets
  outside the approved existing route inventory.
- [ ] Marketing primary navigation retains the current destination order and
  CTA, and every pre-change href still resolves.
- [ ] The Docs destination is treated as internal in the combined site: it has
  no external-link glyph, new-tab behavior, or external-only relationship
  metadata.
- [ ] The docs site adds a thin product-orientation band driven by the shared
  destination contract without displacing or duplicating Starlight's title,
  search, theme control, or sidebar.
- [ ] Marketing and docs footers expose the same approved destination taxonomy,
  labels, group order, targets, and internal/external semantics.
- [ ] Marketing chrome continues to use the platform design system, and docs
  chrome continues to use the docs-specific palette and pinned Starlight
  contracts; no CSS, component, or color-token implementation is shared across
  renderers.
- [ ] Every existing public route, sidebar entry, pagination link, and
  navigation destination still resolves, and combined rendered page/fragment
  checking passes.
- [ ] At 360, 375, 390, 414, and 1440 CSS-pixel widths, chrome has at most 1px
  horizontal overflow, is fully keyboard-usable, and produces zero serious or
  critical axe findings on the approved route/theme matrix.
- [ ] Recorded design review finds no Major issue against either renderer's
  named aesthetic direction or the four tech-site principles.

## Assumptions

- Technical: the marketing renderer currently owns navigation/footer literals,
  the docs renderer owns a custom Starlight footer, and `site.toml` already
  drives cross-renderer site generation (source: repository inspection on
  2026-08-17).
- Technical: build order remains marketing first and docs second into one Pages
  artifact (source: `.github/workflows/pages.yml` and repository build scripts).
- Process: implementation does not begin until RFC-0089 is Accepted (source:
  RFC-0089 lifecycle contract).
- Product: shared chrome means shared information architecture and destination
  vocabulary, not shared CSS or component implementations (source: user
  approval of `docs/product/briefs/tech-site-completion.md`).
- Product: docs adds a thin product-orientation band, footers share destination
  taxonomy, and Docs receives internal-link treatment (source:
  `docs/product/briefs/tech-site-completion.md`).
- Product: existing destination order, routes, and marketing CTA are the
  approved contract (source: user confirmation 2026-08-17).
- Process: the platform and docs aesthetic directions remain authoritative on
  their owning renderers (source: user confirmation 2026-08-17).
