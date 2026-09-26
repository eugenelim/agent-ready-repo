# Spec: workflow-page-design

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Documentation maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`../docs-site-design-refresh/creative-direction.md`](../docs-site-design-refresh/creative-direction.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. The other sections orient the work and may be corrected before
> approval as repository evidence sharpens the design.

## Outcome

An engineer arriving with work can choose between shaping an uncertain idea
and building a known change, then understand the chosen path from one screen.
The representative Core page explains the route to a checked change and a
human merge decision without requiring pack or skill knowledge.

## What Changes

- The docs home presents two primary routes before its supporting tasks:
  shape an unclear idea or start a known software change.
- The existing Core start-work guide becomes a compact, outcome-led workflow
  page at its current URL.
- The maintainer guide records a reusable narrative convention for operational
  pages without imposing seven visible labels.
- The docs theme gains a restrained, scoped category palette for orientation
  surfaces while cobalt remains the global action and link color.
- Rendered-output and browser checks enforce the new hierarchy, navigation,
  accessibility, and responsive behavior.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Public entry point | Readers need to choose shape or build before learning internal taxonomy. | `docs-site/src/content/docs/index.mdx` | Documentation maintainers | Rendered-output and browser tests | Both routes precede supporting tasks in the built home page. |
| Representative workflow | The slice must prove the convention on one Core page. | `guides/core/how-to/start-or-remember-work.md` | Core guide maintainers | Guide linters, built page, browser inspection | The opening answers the workflow scan questions and the current URL remains valid. |
| Authoring convention | Later pages need one compact rule set rather than copied headings. | `docs/guides/how-to/author-product-documentation.md` | Product documentation maintainers | Documentation review | The convention states expected content, optional content, order, and omission rules. |
| Visual direction | Category color is a scoped exception to the site's single-accent rule. | `docs/specs/docs-site-design-refresh/creative-direction.md` | Docs design maintainers | Source review and contrast checks | The direction distinguishes global action color from redundant category cues. |
| Regression evidence | The hierarchy and responsive floor are user-visible behavior. | `web/src/test/rendered-output.test.ts`, `web/src/test/e2e/docs-wayfinding.spec.ts` | Site maintainers | Passing source and browser suites | The tests exercise both primary routes and the representative guide. |

## Agent Rules

### Always do

- Lead with user outcomes and natural-language prompts; introduce skill names
  only where invocation, reference, or debugging needs them.
- Preserve the public `/guides/core/how-to/start-or-remember-work/` URL even
  though the visible page title no longer promotes remembering work.
- Describe Product Engineering as the route for shaping an open problem and
  Core as the route for delivering a known change.
- Pair every category color with text and structure, preserve cobalt for links
  and actions, and meet the existing contrast and focus floors in both themes.
- Edit handwritten sources and regenerate projections through the repository's
  existing build path.

### Ask first

- Adding another public workflow page to this migration.
- Changing the docs sidebar, public route names, or the global site palette.
- Changing runtime routing, workspace state, skill names, or approval gates.

### Never do

- Present remembering or resuming work as a primary product promise.
- Require readers to understand packs, skills, processors, authority modes, or
  workspace internals before they can start.
- Turn the convention into a schema, component framework, or rigid set of
  visible headings.
- Mechanically migrate other workflow pages or edit generated guide sources.
- Use color as the only way to distinguish a route.

## Testing Strategy

- **Content and route checks (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005,
  AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0013).** Goal-based
  checks read the source and built site to verify hierarchy, content order,
  route integrity, migration scope, and the automated gate set.
- **Rendered QA (AC-0012, AC-0014, AC-0015).** Playwright verifies focus,
  accessibility, theme behavior, and overflow. A real-browser inspection covers
  the built home and Core page at the repository's declared wide and narrow
  channels in both themes.

## Acceptance Criteria

- [x] **AC-0001.** The built docs home renders exactly two primary route cards before any
  supporting task cards: `Shape an idea` links to the Product Engineering
  shaping guide, and `Build a known change` links to the existing Core
  start-work URL.
- [x] **AC-0002.** The built docs home contains links to every member of this
  closed href set: `/guides/core/how-to/start-or-remember-work/`,
  `/guides/product-engineering/how-to/shape-a-feature-intent/`,
  `/guides/core/how-to/bug-fix/`,
  `/guides/architect/how-to/assess-a-repository/`,
  `/guides/architect/how-to/shape-an-architecture-concept/`,
  `/guides/desk-research/how-to/run-the-research/`,
  `/guides/release-engineering/how-to/run-a-release/`,
  `/guides/core/how-to/adapt-to-project/`, `/getting-started/`,
  `/guides/#the-install-to-ship-walkthrough`, `/guides/`, `/packs/`,
  `/getting-started/three-loops/`,
  `/guides/_shared/reference/agentbundle/`,
  `/guides/_shared/explanation/pack-catalogue/`, and
  `/guides/_shared/how-to/create-a-catalogue/`, each qualified by the deployed
  site base. Setup and reference links render below the task chooser.
- [x] **AC-0003.** The Core guide's visible title is `Start a software change`; its first
  operational section contains a natural-language prompt followed by a
  three-step account of what Core does.
- [x] **AC-0004.** Before its first deep-reference section, the Core guide shows the route
  for an open product question, names the human commitment boundary, states
  what a durable route writes, gives a recognizable completion signal, and
  points to the normal next action.
- [x] **AC-0005.** The Core guide accurately distinguishes immediate work from durable
  spec or delivery-brief routes, without changing work-intake or work-loop
  behavior.
- [x] **AC-0006.** The contributor convention requires an outcome and promise, a runnable
  natural-language prompt, a short narrative spine, meaningful decisions and
  outputs, a completion signal, and a next move; it marks decision/state detail
  optional when absent and does not require fixed visible labels.
- [x] **AC-0007.** The orientation palette defines separate build, shape, investigate, and
  operate cues for both themes, while normal links and primary actions continue
  to use the global cobalt accent.
- [x] **AC-0008.** Every category wrapper contains a visible text heading that
  names the route category, so removing category color does not remove the
  distinction.
- [x] **AC-0009.** The current Core start-work URL, every modified link, and every generated
  table-of-contents anchor resolve in the built site.
- [x] **AC-0010.** Only the representative Core workflow page adopts the new opening
  pattern; no other workflow page is mechanically migrated and no unrelated
  generated documentation changes.
- [x] **AC-0011.** The docs build, rendered-site link check, relevant guide linters,
  rendered-output tests, Playwright wayfinding suite, Ruff, and mypy pass.
- [x] **AC-0012.** Browser evidence covers the docs home and representative Core
  page in light and dark themes at 480×600, 480×900, 1024×600, and 1024×900.
  Each route, theme, and viewport has an at-rest capture at scroll position 0
  plus a scrolled capture at scroll position greater than 0, or records
  `page-scrollable: no` for that viewport. Each capture records its route,
  viewport width and height, scroll position, and whether the page is
  scrollable. The completed inspection reports no unresolved layout finding
  where one element covers another or content is hidden at the at-rest top of
  the content area.
- [x] **AC-0013.** Every category text/fill pair reaches a contrast ratio of at
  least 4.5:1 in both themes, measured from computed browser styles by the
  Playwright wayfinding suite.
- [x] **AC-0014.** Keyboard focus on both primary home routes and the first
  breadcrumb link on the Core page retains a visible focus indicator at least
  2px thick with at least 3:1 contrast in both themes.
- [x] **AC-0015.** The docs home and representative Core page produce no more
  than 1 CSS pixel of horizontal body overflow at a 375 CSS-pixel viewport.

## Follow-ons

- Apply the proven convention to other workflow pages only after this slice is
  reviewed in use.
- Shape
  [`FEAT-0010-product-documentation-page-design.md`](../../product/intents/FEAT-0010-product-documentation-page-design.md)
  so `author-product-docs` can work from any code-backed product surface, with
  pack documentation as one supported case.
- Evaluate whether the category palette improves other orientation surfaces;
  do not extend it from this slice by default.

## Assumptions

- The docs home and the current Core start-work URL are the two page surfaces
  in scope.
- The existing Product Engineering shaping and Core delivery guides remain the
  behavioral authorities; this slice changes explanation and wayfinding only.
- No `[design]` output is configured, so the repository's existing creative
  direction and this plan hold the design handoff.
- Frontend mode is `retrofit`; `documentation-design` is the loaded genre
  discipline for this documentation surface.
