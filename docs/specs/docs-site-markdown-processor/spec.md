# Spec: docs-site markdown processor

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The documentation site's Markdown pipeline is configured the way astro 7 asks
for it: `docs-site/astro.config.ts` builds its own processor with
`unified({...})` from `@astrojs/markdown-remark` and hands it to
`markdown.processor`. A maintainer running `npm run build --prefix docs-site`
sees a clean build with no deprecation notice, and an astro major that drops the
legacy `markdown.remarkPlugins` / `markdown.rehypePlugins` / `markdown.remarkRehype`
keys cannot break this site.

Both plugins the site depends on keep working, and — for the first time — both
are provably working. The rehype plugin's proof already exists: every Markdown
table on every docs page sits in a focusable scroll region. The remark plugin
gets the same treatment, and the published corpus carries the diagram that makes
that proof possible.

That diagram sits in *The Three Loops* § How the loops connect, where the reader
has already met the pack names, agent names and gate codes it uses, and where
the relationship it draws is the section's own subject. It shows three peer
loops, each ending at a consent gate, joined by the G3 and G4 handoffs and by
the findings path that returns inward — a cycle, not a line, because the page's
claim is that the loops are peers rather than a pipeline. An italic caption
below it states the same relationships in prose, so a reader using a screen
reader, or one whose browser ran no JavaScript, gets the diagram's reading
rather than a gap. A migration that silently stopped running the remark plugin
turns a page red instead of shipping.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Build `web/` before `docs-site/`. The marketing build cleans repository
  `build/` on every run, so the reverse order deletes `build/docs/` and every
  assertion over it measures nothing.
- Land the end-to-end placeholder assertion against the *current* configuration
  and watch it pass there, before changing `astro.config.ts`. A control first
  observed after the change it guards cannot distinguish "still works" from
  "never worked".
- Exercise the rendered page in a real browser — both themes, 1440 px and
  375 px — before declaring done. The client-side render path in
  `docs-site/src/components/Footer.astro` has never run on a published page.

### Ask first

- Any edit to *The Three Loops* beyond exchanging the diagram — the surrounding
  prose is published product copy. (Asked and granted 2026-08-23: moving the
  figure into § How the loops connect, and removing the fixed-width block from
  the page's opening, are both within scope.)
- Any change to `docs-site/package.json`, either lockfile, or the docs-site
  palette, type scale, or component styling.
- Extracting `remarkMermaid` out of `astro.config.ts` into `src/plugins/`.

### Never do

- Add a dependency, a new module boundary, or a new top-level directory.
  `@astrojs/markdown-remark` is already declared and `remarkMermaid` stays
  inline in `astro.config.ts`.
- Set `markdown.processor` and any of `markdown.remarkPlugins`,
  `markdown.rehypePlugins`, `markdown.remarkRehype` at the same time. astro
  accepts the pair and warns; the configuration is then ambiguous to a reader
  and its behaviour depends on plugin-count bookkeeping inside astro.
- Substitute a unit test of `remarkMermaid` for the build-output assertion. A
  unit test passes when the processor never invokes the plugin, which is
  precisely the failure this site has already shipped once.
- Weaken or delete an existing assertion to make a build pass.

## Testing Strategy

- **The configuration migration — goal-based check.** `npm run build --prefix
  docs-site` completes, emits 225 pages, and its output contains no
  `[astro] ... are deprecated` line naming the markdown keys. There is no
  invariant to compress here; the build either accepts the config and stays
  quiet or it does not.
- **The remark plugin still runs — goal-based check, exercised by an
  end-to-end test.** Asserted over emitted HTML in
  `web/src/test/rendered-output.test.ts`, which scans `build/docs`. This
  behaviour is only observable across the boundary: whether astro's processor
  invokes a configured remark plugin is not visible from the plugin, from the
  config file, or from any unit surface.
- **The rehype plugin still runs — unchanged.** `web/src/test/rendered-output.test.ts`
  "AC8: every markdown table sits in a focusable scroll region" is the existing
  end-to-end proof and is not modified.
- **The diagram's caption — goal-based check, exercised by the same end-to-end
  test.** The caption is the diagram's reading for a screen reader and for a
  client that ran no JavaScript, so its presence is asserted rather than left to
  the author's memory. `accDescr` is *not* asserted: mermaid renders it into the
  SVG, which exists only once scripts run, so it cannot carry the guarantee.
- **The rendered diagram — visual / manual QA.** A recorded browser gesture:
  load the page at 1440 px and 375 px in light and dark, and again with
  JavaScript disabled. The client-side render has no automated surface and is
  not made to have one here.
- **The corrected `docs-site/AGENTS.md` prose — goal-based check.** A `grep`
  confirms the false claims are gone.

## Acceptance Criteria

- [x] `docs-site/astro.config.ts` passes its two plugins through
  `markdown.processor: unified({ remarkPlugins: [remarkMermaid], rehypePlugins:
  [rehypeScrollableTables] })`, importing `unified` from
  `@astrojs/markdown-remark`, and sets none of `markdown.remarkPlugins`,
  `markdown.rehypePlugins`, `markdown.remarkRehype`.
- [x] `npm run build --prefix docs-site` emits 225 pages and its output contains
  no line matching `\[astro\].*deprecated`.
- [x] `build/docs/getting-started/three-loops/index.html` contains at least one
  element matching `.mermaid-diagram[data-mermaid]` whose `data-mermaid`
  attribute decodes to a non-empty Mermaid source.
- [x] A test in `web/src/test/rendered-output.test.ts` asserts the criterion
  above over the emitted site and fails when the remark plugin does not run —
  demonstrated by reverting the plugin's registration and observing the test go
  red.
- [x] `npm test --prefix web` reports 129 passed and 0 skipped, including
  "AC8: every markdown table sits in a focusable scroll region" at 230 tables
  and 230 wrappers.
- [x] The Mermaid source on *The Three Loops* names all three packs
  (`product-engineering`, `core`, `release-engineering`), all three lead agents
  (`discovery-lead`, `work-loop supervisor`, `release-lead`), and all six gate
  labels (`G0`, `G1.5`, `G2`, `G3`, `G4`, `G5`) — every fact the fixed-width
  block it replaces carried.
- [x] The diagram draws the three loops as peers joined by a cycle, not as a
  left-to-right spine: each loop ends at its own gate, and a `findings` edge
  returns from production inward to `core`. The page states "peers, not a
  hierarchy" twice, so a diagram that reads as a pipeline contradicts it.
- [x] The diagram carries `accTitle` and `accDescr`, and an italic caption
  immediately follows it in the Markdown source.
- [x] Loaded in a browser at 1440 px and at 375 px, in light and dark theme, the
  page shows a rendered diagram with no horizontal scroll on the document; at
  1440 px it renders unscaled. With JavaScript disabled the caption is present
  and the document still does not scroll horizontally.
- [x] A test in `web/src/test/rendered-output.test.ts` fails when the caption is
  removed, demonstrated by removing it and observing the test go red.
- [x] `.mermaid-diagram` aligns to the left edge of the prose column, as every
  other block on a docs page does.
- [x] `docs-site/AGENTS.md` states that `astro.config.ts` imports
  `@astrojs/markdown-remark`, and carries no claim that nothing imports it or
  that the site is on the deprecated markdown keys.
- [x] `make ci` is green, and `python3 -m pytest tools/test-pages-workflow.py
  tools/test_browser_gate_subset.py tools/test_playwright_evidence_lifecycle.py`
  passes.

## Assumptions

- Technical: `unified` and `isUnifiedProcessor` are public exports of
  `@astrojs/markdown-remark@7.2.2`, and `unified(opts)` returns the processor
  `markdown.processor` expects (source:
  `docs-site/node_modules/@astrojs/markdown-remark/dist/index.d.ts:19` and
  `dist/processor.d.ts`, whose docstring shows this exact call shape).
- Technical: the migration is behaviour-preserving, not merely supported —
  astro's compatibility shim constructs the same `unified()` processor and
  pushes the same plugins in the same order Starlight then appends to (source:
  `docs-site/node_modules/astro/dist/core/config/validate.js:39-77`;
  `@astrojs/starlight/index.ts:96,122`;
  `@astrojs/starlight/integrations/markdown-plugins.ts:33`).
- Technical: nothing in the published corpus exercises `remarkMermaid` today —
  `guides/**` contains no fenced Mermaid block, and the four real ones live
  under `docs/architecture/binder-publishing/`, which the site does not publish
  (source: `git grep -n '^```mermaid' -- guides/`, no matches).
- Technical: the client render degrades rather than disappearing — an
  `import('mermaid')` failure writes the decoded source into a `<pre>` (source:
  `docs-site/src/components/Footer.astro:99-114`).
- Technical: no dependency moves, so neither lockfile changes and the SAST leg's
  lockfile trigger is not tripped (source: `Makefile:205` `SAST_CONFIG`;
  `@astrojs/markdown-remark` is already in `docs-site/package.json`).
- Process: this change is not covered by RFC-0088's added-paths control, which
  is round tooling for that RFC rather than a repository gate — the shared
  helper has two callers, its own test and `Makefile:447` (source: `git grep -n
  'branch_added_paths'`).
- Process: the published surface is governed by
  `docs/design/principles/tech-site.md` and, for docs-site specifically,
  `docs/specs/docs-site-design-refresh/creative-direction.md`; the diagram
  exchange is arbitrated by "Lead with the user's job; reveal the system
  second" and by docs-site's stated no-horizontal-scroll-at-375 px floor
  (source: those two files; `docs-site/AGENTS.md` § Action-changing traps).
- Product: *The Three Loops* is the page that receives the diagram, replacing
  the fixed-width block at lines 8-14 (source: user confirmation 2026-08-23).
- Product: the figure belongs in § How the loops connect rather than at the
  page's opening, and the full set of experience-review findings is addressed in
  this change rather than deferred (source: user confirmation 2026-08-23, after
  an `experience-reviewer` pass returned SHIP WITH CHANGES against
  `docs/design/principles/tech-site.md`).
- Product: a reader without JavaScript gets the author's caption, not a dump of
  the diagram's source. The alternative was measured and rejected: emitting the
  Mermaid source as a `<pre>` produced 410 px of grammar overflowing its column
  by 236 px at 375 px (source: user confirmation 2026-08-23; measurement in
  `plan.md` § Changelog).
