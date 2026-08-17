# Spec: Docs-site build contract hardening

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0089, ADR-0085
- **Brief:** tech-site-completion
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Contributors can trust the Starlight build boundary because generation no
longer depends on an unused marketing token file, the table accessibility
plugin has fast behavioral unit coverage, and required CI proves those
contracts before deployment. The docs palette, routes, and pinned Starlight
behavior remain unchanged.

## Boundaries

### Always do

- Keep the docs palette self-contained and independent from marketing tokens.
- Test the rehype plugin through emitted HAST behavior using Node's built-in
  test runner under the existing Node 24 contract.
- Retain full built-site assertions as integration evidence after adding unit
  coverage.

### Ask first

- Change table-region labels, focus behavior, wrapper markup, or Starlight's
  table-scroll ownership contract.
- Change the docs palette, a pinned Starlight override, route, or build output
  directory.
- Move the plugin to another runner or package.

### Never do

- Add a dependency or copy marketing palette tokens into `docs-site/`.
- Replace emitted-site evidence with source-shape or unit tests alone.
- Make the two renderer projects share CSS, components, or runtime code.

## Testing Strategy

- Generator decoupling and rehype transform invariants use TDD with seeded
  failure fixtures.
- Build order, routes, table markup, links, contrast, and palette independence
  use goal-based integration checks against the combined emitted site.
- Representative table keyboard behavior in both docs themes remains browser
  evidence owned by the site browser quality gate.

## Acceptance Criteria

- [ ] `tools/build-site.py` neither reads, requires, copies, nor writes
  `web/src/styles/tokens.css` or `docs-site/src/styles/tokens.css`.
- [ ] Site generation succeeds when the marketing token file is absent from an
  isolated construction fixture, and it does not create a docs token copy.
- [ ] `docs-site/AGENTS.md` describes the docs palette as self-contained and no
  longer claims generation copies or docs CSS imports marketing tokens.
- [ ] `docs-site/package.json` exposes a focused plugin-test command implemented
  with Node's built-in test runner and the existing Node 24 runtime; dependency
  manifests and lockfiles gain no package.
- [ ] Unit tests prove that `rehypeScrollableTables` wraps an unwrapped table in
  one focusable labelled region, leaves an existing wrapper unchanged, handles
  a table with no writable parent safely, derives labels from nested heading
  text, disambiguates repeated labels, and resets label counts for each
  transformed document.
- [ ] A seeded mutation to wrapper class, `tabIndex`, role, accessible label, or
  idempotence causes the focused plugin suite to fail.
- [ ] Required site CI runs the focused plugin-test command when the plugin,
  docs package/configuration, or owning workflow changes, and test failure
  blocks deployment.
- [ ] The existing rendered-output test still verifies every emitted Markdown
  table is inside the expected focusable region; unit tests do not replace this
  integration contract.
- [ ] The canonical marketing-first, docs-second build completes, the combined
  route/link/fragment checks pass, and the docs contrast checker reports every
  approved pair at or above 4.5:1 in both themes.
- [ ] Existing marketing and docs routes, the docs-specific palette, and pinned
  Starlight title/search/theme/sidebar/pagination behavior remain unchanged.

## Assumptions

- Technical: `docs-site/src/styles/starlight.css` no longer imports the copied
  marketing token file and locally defines its docs and compatibility tokens
  (source: repository inspection and `docs-site/AGENTS.md` on 2026-08-17).
- Technical: `tools/build-site.py` still copies the vestigial file and exits
  with a false dependency error when the marketing source is missing (source:
  repository inspection on 2026-08-17).
- Technical: `rehypeScrollableTables` is a pure tree transform whose only
  package import is already declared, and the repository's Node contract is
  version 24 or newer (source: plugin and `docs-site/package.json`).
- Product: Node's built-in runner is the approved test-runner choice and no
  dependency is added (source: user approval of
  `docs/product/briefs/tech-site-completion.md`).
- Product: docs colors do not align with `web/` unless a later approved
  decision changes that rule (source: `docs-site/AGENTS.md` and RFC-0089 D2).
- Process: full emitted-site verification remains mandatory for future
  implementation (source: `docs/product/briefs/tech-site-completion.md`).
