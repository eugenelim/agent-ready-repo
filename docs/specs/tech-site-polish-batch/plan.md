# Plan: tech-site-polish-batch

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** implementation strategy; allowed to change as we learn.

## Assumption trio

**Files I'll touch**

- `tools/build-site.py` — H1 strip on the frontmatter-preserving path; `summary` → `description` mapping.
- `tools/lint-guide-titles.py` *(new)* — AC2 lint. Python per the repo's "new tool scripts: Python, not bash" rule; **not** pure-stdlib — it parses frontmatter with `yaml.safe_load` so the gate and `build-site.py` agree on what a title is, and its CI job installs `tools/requirements.txt` accordingly.
- `.github/workflows/docs.yml` — register the lint in the docs CI path.
- `docs-site/astro.config.ts` — rehype plugin wrapping wide tables.
- `docs-site/src/components/PageTitle.astro` *(new override)* — deck line.
- `docs-site/src/styles/starlight.css` — inline-code neutralisation, deck styling, table-scroll region styling.
- `web/src/components/marketing/Hero.astro` — mobile type scale, CTA weight.
- `web/src/components/layout/SiteNav.astro` — drawer touch targets.
- `web/src/components/layout/SiteFooter.astro` — labelled columns.
- `web/src/test/rendered-output.test.ts` *(new)* — committed AC harness.
- `tools/test_lint_guide_titles.py` *(new)* — tests for the lint and for
  `build-site.py`'s H1 / summary transforms.
- `docs-site/src/plugins/rehype-scrollable-tables.ts` *(new)* — the table
  wrapper, extracted from the config.
- `docs-site/package.json`, `docs-site/AGENTS.md` — declare `unist-util-visit`,
  record the two new Starlight touchpoints.
- `guides/AGENTS.md` — the authoring rule this change introduces.
- `docs/product/changelog.md` — user-visible entries.
- `tools/check-docs-contrast.py` — the two pairs this change creates.
- `.github/workflows/pages.yml` — run the harness where `build/` exists.
- `guides/**` (9 files) — H1 reconciled with the frontmatter title.
- `web/src/components/marketing/{AdapterMatrix,InstallTerminal}.astro`,
  `web/src/components/primitives/CopyButton.astro` — the three floor fixes
  found while measuring the baselines.
- `workspace.toml`, `docs/knowledge/patterns.jsonl` — deferrals and learnings.

**What demonstrates done**

Full build (`build-site.py` → `web` → `docs-site`), then: a Python parse of
`build/docs/**/index.html` showing 0 multi-`h1` pages and ≥47 pages carrying a
non-empty meta description; the new lint failing on a divergent fixture and
passing on the tree; a Playwright + axe sweep over both surfaces at
360/375/390/414/1440 px reporting 0 body overflow, 0 serious violations, and
the hero primary CTA bottom ≤ 844 at 390×844.

**What I am not changing**

Sidebar IA, breadcrumbs, the docs landing layout, guide prose, the 74
blockquote callouts, the two colour palettes' separation, and the 142 guides
that carry no frontmatter.

## Declined patterns

- **A shared design-token package across `web/` and `docs-site/`.** Tempting
  while touching both palettes; `docs-site/AGENTS.md` deliberately forbids
  coupling them, and nothing in this batch needs it.
- **A generic `<Callout>` primitive while in `starlight.css`.** The typed-aside
  conversion is a separate, larger finding; building the component now would
  ship an abstraction with no callers.
- **Refactoring `_inject_frontmatter` and `_strip_guide_metadata` into one
  pipeline.** They have genuinely different inputs; merging them is a
  restructure this batch does not need, and it would widen the blast radius on
  a generator that feeds 216 published pages.
- **Making the deck a new frontmatter field (`deck:`/`standfirst:`).** Starlight
  already has `description`, which also feeds meta and search. One field, three
  jobs — a second field would need a reason it does not have.
- **Auto-generating `summary:` for the 142 guides from their first paragraph.**
  Cheap to write, and it would ship 142 unreviewed descriptions into meta tags
  and social previews. Backfill stays a human-reviewed follow-up.
- **Fixing the sidebar while in `astro.config.ts`.** Adjacent and sorely
  needed, but it is an IA decision the spec explicitly routes to Ask-first.

## Approach

Two independent halves — the generation half (`tools/`, `docs-site/`) and the
marketing-CSS half (`web/`) — with no shared files, so a failure in one does
not block the other. Within the generation half, T1 must land before T2:
stripping the duplicate H1 is what makes room for the deck.

**Contract grounding (verified in-session against installed sources):**
`@astrojs/starlight@0.41.4` exposes `PageTitle` as an overridable component
(`docs-site/node_modules/@astrojs/starlight/components/PageTitle.astro`); it
reads `Astro.locals.starlightRoute.entry.data.title` and its style sits in
`@layer starlight.core`, so unlayered custom CSS wins. `description` is part
of Starlight's `docsSchema()` and already feeds `<meta name="description">`;
it is not rendered in the page body, which is why the deck needs the override.
`unist-util-visit` is already imported by `astro.config.ts` for the mermaid
remark plugin, so the table-wrapping rehype plugin adds no dependency.

The root cause of AC1 is documented in the generator itself:
`_strip_guide_metadata`'s docstring states it "preserves H1 headings in the
body (guide authors who add explicit frontmatter are responsible for removing
the H1)". That contract is what produced 38 divergent doubles; T1 inverts it
and T2's lint keeps it inverted.

## Tasks

### T1 — Strip the body H1 on the frontmatter-preserving path
*Depends on: none*

**Tests:** goal-based. `Done when:` after a full build, a Python parse of
`build/docs/**/index.html` reports `0` pages whose `<main>` contains more than
one `<h1>` (baseline 38 of 217).

**Approach:** in `_strip_guide_metadata`, after the frontmatter block is
parsed, remove the first `^#\s+` heading from the body the same way
`_inject_frontmatter` already does, and reconcile the docstring. Pages whose
frontmatter carries no `title` keep the H1 as the title source — check that
case explicitly rather than assuming.

### T2 — Title-divergence lint
*Depends on: T1*

**Tests:** TDD. Fixtures: (a) frontmatter title and body H1 identical → pass;
(b) differing beyond case/punctuation ("freshly installed" vs
"freshly-installed") → fail with both strings in the message; (c) no body H1
→ pass; (d) no frontmatter → pass. (Written after the lint, in response to a review finding — not
red-stub-first as originally planned.)

**Approach:** `tools/lint-guide-titles.py` walks `guides/**.md`,
normalises case, hyphens, and terminal punctuation, exits non-zero on
divergence. Register in `.github/workflows/docs.yml` with a `python3 <script>`
invocation so the existing `paths:` trigger convention holds.

### T3 — `summary` → `description`, and render the deck
*Depends on: T1*

**Tests:** goal-based + visual QA. `Done when:` every guide declaring
`summary:` emits a non-empty `<meta name="description">` in its built page
(baseline 0 of 47), and a screenshot shows the string as a muted line between
the title and the first body paragraph.

**Approach:** keep `summary` in `_GUIDE_ONLY_FIELDS` and copy it onto
`description` before the strip, when the guide does not already declare one.
(No guide declares an explicit `description` today; the branch exists so that a
future one wins over its `summary`.) Add `docs-site/src/components/PageTitle.astro` rendering the
title plus, when present, the description as a deck; register it in the
`components` map. Style the deck in `starlight.css` at the muted foreground
token, re-running `check-docs-contrast.py`.

### T4 — Wide docs tables become keyboard-reachable scroll regions
*Depends on: none*

**Tests:** goal-based. `Done when:` axe reports no
`scrollable-region-focusable` violation on the built
`guides/_shared/reference/agentbundle` page at 360/375/390/414 px (baseline
1–3).

**Approach:** rehype plugin in `src/plugins/rehype-scrollable-tables.ts`,
wired from `astro.config.ts`, wrapping each `<table>` in a
`<div class="table-scroll" tabindex="0" role="region" aria-label="…">`; move
the horizontal scroll onto the wrapper in `starlight.css` and give it a
visible `:focus-visible` ring. Build-time, no runtime JS. Starlight already
gives `<pre>` blocks `tabindex="0" role="region"` — match that treatment
rather than inventing a second one.

### T5 — Mobile hero type scale and CTA weight
*Depends on: none*

**Tests:** visual QA. `Done when:` at 390×844 with the page at scroll top, the
hero's primary CTA bounding box has `bottom <= 844` (baseline top ≈ 1290), and
a screenshot shows the secondary action at visibly lower weight than the
primary.

**Approach:** step the hero headline and deck down at the mobile breakpoint
using existing `--ds-type-*` steps — no new tokens. Demote the secondary CTA
from an outlined button to a text link with the existing arrow affordance,
keeping its 44 px touch height.

### T6 — Marketing mobile drawer touch targets
*Depends on: none*

**Tests:** visual QA. `Done when:` with the drawer open at 375 px, every
drawer link's box is ≥ 44 px tall and spans the drawer content width
(baseline 17 px tall, 49–87 px wide).

**Approach:** make drawer links `display: block` with vertical padding to the
44 px minimum and full width, and give them a hairline separator consistent
with the dark zone. Desktop nav links are unaffected — the rule lives inside
the existing `@media (max-width: 768px)` block.

### T7 — Neutralise inline-code chips
*Depends on: none*

**Tests:** visual QA. `Done when:` computed style of an inline `<code>` outside
`<pre>` shows a neutral (non-accent) background and colour in both themes,
`check-docs-contrast.py` passes, and a screenshot of the how-to page shows
prose no longer reading as a chip mosaic.

**Approach:** in `starlight.css`, retarget the inline-code rule from the accent
tint to the neutral surface/foreground pair already defined for the docs
palette. Code inside `<pre>` is Expressive Code's and is not touched.

### T8 — Marketing footer columns
*Depends on: none*

**Tests:** visual QA. `Done when:` the footer renders labelled column groups
covering the surfaces that exist today, and a screenshot at 1440 px and 375 px
shows the columns stacking without overflow.

**Approach:** restructure `SiteFooter.astro` into labelled groups (product /
docs / project) built from the routes that actually exist — catalogue,
journeys, packs, docs, changelog, contributing, GitHub, PyPI. Link only
targets present in the build; verify each resolves before committing.

### T9 — Record the new Starlight touchpoints in `docs-site/AGENTS.md`
*Depends on: T3, T4*

**Tests:** goal-based. `Done when:` `docs-site/AGENTS.md` names the
`PageTitle` override and the table-wrapper rehype plugin in its
"Starlight is pinned; its internal class names are a styling contract"
paragraph, so the next upgrade re-verifies them.

**Approach:** extend the existing paragraph rather than adding a section —
the file is already near its purpose and the repo caps subdirectory
`AGENTS.md` at 150 lines.

### T10 — Commit the AC harness
*Depends on: T1–T9*

**Tests:** goal-based. `Done when:` the committed test runs in `npm test
--prefix web`, is invoked by `pages.yml` after both builds, and asserts the
AC1/AC3/AC5/AC7/AC8 measurements against the built output. AC10 (body overflow
and the axe sweep across five viewports) needs a real browser and is **not**
asserted here — jsdom cannot measure layout; it stays a manual gate until an
e2e spec is added.

**Approach:** port the session's measurement script into
`web/src/test/rendered-output.test.ts`, reading from `build/`. Use
`describe.skipIf` rather than an early `return` — a returning vitest body
reports a green pass for a test that asserted nothing. Parse `<main>` as a
DocumentFragment for the 216-page scans (216 full JSDOM windows exhaust the
worker) and full documents only for the targeted assertions. Derive AC3's
expected set from the source guides, honouring `slug:` overrides, so the
assertion cannot go permanently green.

## Risks

- **Generator blast radius.** T1 and T3 change every generated page. Mitigated
  by measuring the built tree before and after rather than reasoning about the
  transform, and by T9 committing that measurement.
- **Starlight internals are a styling contract.** `PageTitle` override and the
  table wrapper depend on pinned-version internals; `docs-site/AGENTS.md`
  already records that re-verification is required after any Starlight upgrade.
  Add the two new touchpoints to that note.
- **~~`title`-less guides.~~ Resolved at PLAN.** Enumerated before editing: all
  47 guides carrying frontmatter declare a `title`, and 38 of them also carry a
  body H1. T1's strip therefore never removes a page's only heading source. The
  38th duplicate is the generated `packs/index.md`, which builds its own H1 on
  top of a frontmatter title — a separate line in the same generator, fixed in
  T1 alongside the guide path.
