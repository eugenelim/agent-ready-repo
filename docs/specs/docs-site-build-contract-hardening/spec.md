# Spec: Docs-site build contract hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0089, ADR-0085
- **Brief:** docs/product/briefs/tech-site-completion.md
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
- Deploy-workflow inclusion, ordering, and path-trigger behavior use TDD
  construction tests over `pages.yml`, each proven by seeded deletion — the step
  and the filters already exist in part, so a presence assertion alone would not
  detect removal.
- Representative table keyboard behavior in both docs themes remains browser
  evidence owned by the site browser quality gate.

## Acceptance Criteria

- [x] `tools/build-site.py` neither reads, requires, copies, nor writes
  `web/src/styles/tokens.css` or `docs-site/src/styles/tokens.css`.
- [x] Site generation succeeds when the marketing token file is absent from an
  isolated construction fixture, and it does not create a docs token copy.
- [x] `docs-site/AGENTS.md` describes the docs palette as self-contained and no
  longer claims generation copies or docs CSS imports marketing tokens.
- [x] `docs-site/package.json` exposes a focused plugin-test command implemented
  with Node's built-in test runner and the existing Node 24 runtime; dependency
  manifests and lockfiles gain no package.
- [x] Unit tests prove that `rehypeScrollableTables` wraps an unwrapped table in
  one focusable labelled region, wraps a table nested inside a blockquote or
  aside (the non-root, non-wrapper parent case its register entry named), leaves
  an existing wrapper unchanged, leaves a root-level table with no parent or
  index unchanged, derives labels from nested heading text, disambiguates
  repeated labels, and resets label counts for each transformed document.
- [x] A seeded mutation to wrapper class, `tabIndex`, role, accessible label, or
  idempotence causes the focused plugin suite to fail.
- [x] The deploy workflow's `build` job runs the focused plugin-test command
  after the docs dependency install and before artifact upload, so a failing
  plugin test blocks upload and deployment. Its existing `paths:` filters already
  cover the plugin, the docs package/configuration, and the workflow itself, so
  that half is proven by seeded deletion rather than asserted as present.
  Residual, stated deliberately: `pages.yml` is NOT a required merge context —
  branch protection requires only `make build-check`, `gate-main`, `gate-sast`,
  and `gate-export-boundary` — so this gate blocks deployment, not merge. It
  cannot move to `build-check.yml`: that workflow must carry no `paths:` filter
  (a filtered required context leaves non-matching PRs permanently unmergeable)
  and deliberately provisions no Node.
- [x] The existing rendered-output test still verifies every emitted Markdown
  table is inside the expected focusable region; unit tests do not replace this
  integration contract.
- [x] The canonical marketing-first, docs-second build completes, the combined
  route/link/fragment checks pass, and the docs contrast checker reports every
  approved pair at or above 4.5:1 in both themes.
- [x] Existing marketing and docs routes and the docs-specific palette remain
  unchanged, proven by an emitted route-set diff (membership, not count) and by
  the contrast checker. Pinned Starlight behavior is verified per control:
  sidebar and pagination by the existing assertions in
  `web/src/test/rendered-output.test.ts`; title, search, and theme control by a
  diff-scope check showing no change to `docs-site/astro.config.ts`,
  `docs-site/src/components/**`, or `docs-site/src/styles/starlight.css` — their
  behavioural coverage is browser-only, which the brief bars from required CI.

## Assumptions

- Technical: `docs-site/src/styles/starlight.css` no longer imports the copied
  marketing token file and locally defines its docs and compatibility tokens
  (source: repository inspection and `docs-site/AGENTS.md` on 2026-08-17).
- Technical: `tools/build-site.py` still copies the vestigial file and exits
  with a false dependency error when the marketing source is missing (source:
  repository inspection on 2026-08-17).
- Technical: the Node runtime floor is whatever `docs-site/package.json`'s
  `engines` field declares (>=24 today); that file is the canonical statement and
  the other mentions here defer to it. Built-in type stripping runs the
  TypeScript test file directly, verified on the installed runtime.
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
