# Plan: docs-wayfinding-cluster

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as we learn.

## Approach

Implement the three registered follow-ups sequentially in the requested order,
without treating that delivery order as an artifact dependency. First, turn
the docs home into a compact orientation hub using Starlight's existing hero
and link-card primitives. Second, repair the custom Footer's route-data access
so the existing generated sidebar order produces the pager it already defines.
Third, replace the detached Banner with a semantic breadcrumb child inside the
existing PageTitle override. Extend the built-output regression suite after
each slice and inspect the cache-cleared built surface, not generated source.

## Assumption trio

**Files I'll touch**

- `workspace.toml` — correct the stale canonical sidebar/pagination brief and,
  at ship time, close the three delivered backlog entries.
- `docs-site/src/content/docs/index.mdx` and
  `docs-site/src/styles/starlight.css` — landing hierarchy and card treatment;
  removal of obsolete Banner styling.
- `docs-site/src/components/Footer.astro` — pinned route-data pagination repair.
- `docs-site/src/components/Breadcrumbs.astro` (new),
  `docs-site/src/components/PageTitle.astro`,
  `docs-site/src/components/Banner.astro` (removed), and
  `docs-site/astro.config.ts` — breadcrumb integration and Banner retirement.
- `docs-site/AGENTS.md` — pinned Starlight touchpoint record.
- `web/src/test/rendered-output.test.ts` and
  `web/src/test/e2e/docs-wayfinding.spec.ts` (new) — built-output construction
  checks and the browser-level route × theme journey.
- `docs/product/changelog.md`, `docs/specs/README.md`, and this spec directory —
  product and lifecycle records.

**What demonstrates done**

A cache-cleared `build-site.py` → web build → docs build, followed by the
rendered-output suite and source gates, proves seven described landing cards,
one primary CTA, sidebar-order pagination, semantic breadcrumb coverage, and
unchanged sidebar leaves. The tracked Playwright journey measures 1440×900 and
375 px in both themes to prove above-fold orientation including the full
labelled search control, the dedicated flagship lead region, wrapping,
overflow, focus, and axe floors.

**What I am not changing**

Guide content, frontmatter, routes, sidebar generation/order/placement,
`site.toml`, `tools/build-site.py`, the docs palette, `web/` production code,
dependencies, or the already-shipped polish work named in the spec boundaries.

## Declined patterns

- **Shape `site-design-principles` first.** The existing docs-specific aesthetic
  direction settles every decision this batch crosses; cross-surface principles
  remain a separate open design item.
- **Rebuild the guide tree to recover pagination.** The built tree is complete;
  duplicating its shipped generator would miss the Footer contract defect.
- **Invent a Starlight breadcrumb override key.** Version 0.41.4 exposes no such
  slot; a child of the supported PageTitle override is smaller and typed.
- **Import the default Pagination component and accept its visual reset.** The
  existing custom pager markup already matches the docs language; reading the
  same typed route data as Starlight restores behavior without restyling it.
- **Add a shared navigation abstraction or dependency.** The three surfaces
  already expose the required data and have no second caller needing a new
  layer.

## Constraints

- The problem/fix briefs entered through the three wayfinding entries formerly
  registered in `workspace.toml [backlog].open`; this completed spec closes
  those historical inputs without duplicating them here.
- `docs-site-design-refresh` and its aesthetic direction govern typography,
  palette, and accessibility. `guides-sidebar-generation` governs all sidebar
  leaves and order.
- Starlight 0.41.4 is an exact-pinned styling and route-data contract. The
  installed source is the T1 oracle; Footer uses
  `Astro.locals.starlightRoute.pagination`, while Breadcrumbs consumes the
  normalized `sidebar` entries (`group.entries`, `link.href`,
  `link.isCurrent`).
- No reference-architecture document exists; the established Astro/Starlight
  stack and current overrides are the implementation frame.
- No external reference name appears in tracked content or Git artifacts.

## Construction tests

**Integration tests:** extend `web/src/test/rendered-output.test.ts` against
`build/docs/` to assert AC2–AC7 from emitted HTML and generated sidebar order.
The suite's existing `SCAN_TIMEOUT_MS = 60_000` applies to whole-site scans.

**Browser integration:** `web/src/test/e2e/docs-wayfinding.spec.ts` serves the
completed built tree through the existing Playwright preview harness. It checks
the docs home and one representative nested guide at 375 px in light and dark,
including body overflow, visible keyboard focus, breadcrumb wrapping, and zero
serious/critical axe violations. At 1440×900 it also asserts that the full
text-labelled Pagefind trigger is entirely within the viewport and that the
dedicated flagship lead card precedes the six-card supporting grid.

## Acceptance commands

Run these commands in order and read each exit code. The first command is the
required cache reset before the acceptance build.

```bash
rm -rf docs-site/.astro docs-site/node_modules/.astro
python3 tools/build-site.py
npm run build --prefix web
npm run build --prefix docs-site
python3 tools/check-rendered-site-links.py --build-dir build
npm test --prefix web
npm exec --prefix web -- playwright test --config web/playwright.config.ts docs-wayfinding.spec.ts
python3 tools/lint-guide-titles.py
python3 tools/test_documentation_entry_links.py
python3 tools/check-docs-contrast.py
python3 tools/lint-agents-md.py
SKIP_SAST=1 make build-check
git diff --check
```

## Design (LLD)

### Design decisions

- **Landing taxonomy:** the seven outcome labels already shared by the authored
  docs home and canonical marketing navigation become description-bearing
  `LinkCard` entries. The existing `flagship` designation makes the supervised
  build loop the lead card; the remaining six form its supporting grid. This
  preserves source-test alignment, avoids a second pack taxonomy, and prevents
  an equal-weight link wall. Traces to AC1–AC3.
- **Landing hierarchy:** retain Starlight's Hero data contract, reduce it to the
  docs heading scale, set the browse action to `minimal`, keep the existing
  Pagefind control prominent, and place the lead card plus supporting outcome
  grid first in the content body. Traces to AC1–AC3.
- **Pagination:** keep the existing custom two-card markup and replace its
  incorrect `Astro.props` read with the typed
  `Astro.locals.starlightRoute.pagination` contract. Traces to AC4–AC5.
- **Breadcrumbs:** a dedicated child component recursively finds the current
  link in normalized Starlight sidebar entries. It renders Docs, ancestor
  groups, and the current page; an ancestor is linked only when a direct
  overview child is also a URL ancestor of the current page. The outer Docs
  root is always linked, duplicate current ancestors are suppressed, and the
  current page is unlinked. Traces to AC6–AC8.

### Component / module decomposition

- `index.mdx` owns landing copy, links, the dedicated flagship lead region, and
  the six-card supporting grid; `starlight.css` owns only surface-level sizing
  and layout.
- `Footer.astro` owns pager markup plus the existing brand footer and reads no
  component props.
- `Breadcrumbs.astro` owns trail derivation and semantic markup;
  `PageTitle.astro` composes it before the required `h1#_top` and existing deck.
- `Banner.astro` and its config registration disappear because no site-wide
  content remains for that slot.

### State & control flow

For each built page, Starlight resolves the current route, sidebar tree, and
pagination before component rendering. Footer renders zero, one, or two pager
cards from that route state. Breadcrumbs returns no markup for the docs root;
otherwise it walks sidebar entries once, resolves the unique current path, and
renders the trail before the page title. Traces to AC4, AC6, and AC7.

### Behavior & rules

- Seven landing cards carry non-empty descriptions and valid docs links; the
  recorded flagship is visually primary without relying on color alone.
- Exactly one Hero action is primary; the browse action is minimal.
- Breadcrumb groups without a canonical overview remain plain text rather than
  linking to an arbitrary first page.
- Current breadcrumb text uses the page title and is marked `aria-current`;
  ancestor text uses navigation labels.
- Sidebar content and ordering are inputs, never rewritten by this batch.

### Quality attributes (NFRs)

Semantic `nav`/`ol` markup, visible focus, theme-token-only colors, wrapping at
375 px, zero horizontal body overflow, and zero serious/critical axe findings
cover AC8. The recursive breadcrumb walk is bounded by the rendered sidebar
size and executes at build time, adding no client JavaScript.

## Tasks

### T1: The docs landing is an above-fold orientation hub

**Depends on:** none

**Touches:** docs-site/src/content/docs/index.mdx,
docs-site/src/styles/starlight.css, web/src/test/rendered-output.test.ts,
web/src/test/e2e/docs-wayfinding.spec.ts

**Tests:**

- No stub (goal-based + browser QA). Extend the built-output suite to
  assert seven canonical card labels with non-empty descriptions and valid
  hrefs, exactly one primary Hero action, and one minimal browse action (AC2,
  AC3).
- In the tracked Playwright journey, assert at 1440×900 that the full labelled
  Pagefind trigger and first card row are inside the viewport and the dedicated
  flagship lead precedes the supporting grid; cover 375 px focus and overflow
  in both themes (AC1, AC2, AC8).

**Approach:** import Starlight `CardGrid` and `LinkCard`, convert the existing
seven outcome routes into cards without changing their canonical labels, lead
with the already-designated flagship build loop, set the second Hero action to
`minimal`, and compact only the docs Hero/card selectors in `starlight.css`.

**Done when:** AC1–AC3 built assertions and browser journey pass.

### T2: Every sidebar-backed guide exposes its adjacent pages

**Depends on:** none

**Touches:** docs-site/src/components/Footer.astro, docs-site/AGENTS.md, web/src/test/rendered-output.test.ts

**Tests:**

- No stub (goal-based integration). Flatten generated guide sidebar leaves and
  assert every interior built page's `rel="prev"`/`rel="next"` targets equal its
  immediate neighbors; edge pages expose their available neighbor (AC4).
- Assert the representative nested page still has identical sidebar leaf order,
  `aria-current="page"`, and open ancestor details (AC5).

**Approach:** source `pagination` from `Astro.locals.starlightRoute`, retain the
existing custom pager markup/styles, and record Footer's pinned contract in the
docs-site agent context. Do not touch the generator or recipe.

**Done when:** cache-cleared built guide pages render the expected two-card
pager and the generated tree preservation check passes.

### T3: Every titled docs page carries a semantic location trail

**Depends on:** none

**Touches:** docs-site/src/components/Breadcrumbs.astro,
docs-site/src/components/PageTitle.astro, docs-site/src/components/Banner.astro,
docs-site/astro.config.ts, docs-site/src/styles/starlight.css,
docs-site/AGENTS.md, web/src/test/rendered-output.test.ts,
web/src/test/e2e/docs-wayfinding.spec.ts, docs/product/changelog.md

**Tests:**

- No stub (goal-based integration + browser QA). Scan built pages with
  `h1#_top` for one semantic breadcrumb, assert none on the docs root, and check
  a nested guide's linked ancestry, unlinked current item, and absence of the
  detached back-link (AC6, AC7).
- Run the tracked Playwright route × theme journey at 375 px for wrapping,
  keyboard focus, overflow, and axe, plus its 1440×900 hierarchy assertions
  (AC1, AC2, AC8).
- Run the exact acceptance-command block above, including
  `tools/lint-guide-titles.py` and `npm test --prefix web` with its 60-second
  scan budget.

**Approach:** add the typed recursive Breadcrumbs child, compose it in
`PageTitle.astro`, remove the custom Banner registration/file/styles, document
the new route-data touchpoint, and add the user-visible changelog entry.

**Done when:** AC6–AC10 and the full cache-cleared built-site journey pass.

## Rollout

Static-site delivery is atomic with the normal Pages artifact. There is no
infrastructure, migration, flag, or external-system sequencing. Reverting the
three authored UI slices restores the prior build; generated guide content and
published routes remain unchanged.

## Risks

- Starlight route-data and sidebar-entry shapes are pinned internals; an upgrade
  can break Footer or breadcrumb derivation. The AGENTS record makes both
  explicit re-verification points.
- Breadcrumb labels can duplicate page titles when an overview link is current.
  The derivation suppresses an ancestor whose resolved href equals the current
  href, and built fixtures cover both index and nested pages.
- The landing can become another equal-weight card wall. The existing flagship
  signal, supporting-card grid, compact Hero, and first-viewport QA hold the
  hierarchy without creating another taxonomy.
- Astro content caching can produce false verification. Both cache directories
  are removed before every acceptance build.

## Changelog

- 2026-08-15: Initial full-mode plan. Corrected the stale sidebar brief to the
  actual Footer pagination defect and chose to proceed without first shaping
  cross-surface site design principles.
- 2026-08-15: Design review made the existing flagship outcome visually primary
  and added explicit above-fold Pagefind verification.
- 2026-08-15: Adversarial review converted visual goals into browser-observable
  postconditions, added a tracked route/theme journey, removed false task
  dependencies, and made the complete acceptance command set executable.
