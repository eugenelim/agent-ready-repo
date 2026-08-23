# Plan: docs-site markdown processor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

The change to `astro.config.ts` is four lines. Everything else in this plan
exists because those four lines are, on this site, unverifiable — and were
already shipped wrong once in exactly this shape.

So the ordering is inverted from the obvious one. **The control lands before
the change it guards.** T1 puts a real Mermaid fence on a published page and
asserts the emitted placeholder over `build/docs`, against the *current*
configuration. That run is the one that proves the assertion has contact with
reality: if it were green for the wrong reason, it would be green here too, and
the mutation in T1 is what separates the two. T2 then performs the migration
with a live control watching. T3 corrects the two `docs-site/AGENTS.md` bullets
the migration falsifies. T4 is the browser pass, which is unavoidable because
the client-side render in `Footer.astro` has never executed on a published page.

The riskiest part is not the config. It is that T1 might reveal the mermaid
render path is broken independently of this work, in which case *The Three
Loops* would ship worse than it is today. T4 is placed before the finish
checklist rather than after it for that reason, and the fallback is stated in
Risks.

## Constraints

- No ADR or RFC governs this. `docs/CONVENTIONS.md` § Document lifecycle governs
  the spec/plan pair.
- `docs/design/principles/tech-site.md` arbitrates the published-page change;
  `docs-site/AGENTS.md` § Action-changing traps carries the
  no-horizontal-scroll-at-375 px floor and the load-bearing build order.
- `docs-site/AGENTS.md` is the canonical home for the `@astrojs/markdown-remark`
  duty; the pin-equality gate added alongside this work lives in
  `tools/test_browser_gate_subset.py`. Neither is restated here.

## Construction tests

**Integration tests:** the end-to-end assertion in T1 is the only cross-cutting
one; it spans T1 and T2 and must be green at the end of both.

**Manual verification:** T4's browser pass — four viewport/theme combinations
plus a JavaScript-disabled load.

## Design (LLD)

### Design decisions

- **Pass the plugins to `unified({...})` rather than leaving the shim to do it.**
  astro's `coerceLegacyMarkdownPlugins` already constructs `unified()` and pushes
  the same plugins onto `target.options` before Starlight appends its own, so the
  migrated shape is byte-for-byte the same pipeline; the difference is only that
  it survives a major. Rejected: pinning astro below the major that removes the
  keys — that trades a four-line edit for an indefinite upgrade block.
  Traces to: AC1, AC2.
- **Assert the emitted placeholder, not the plugin.** A unit test over
  `remarkMermaid` is green whether or not astro's processor invokes it, which is
  the shape of the defect `astro.config.ts`'s own comment records. Rejected:
  extracting the plugin to `src/plugins/` and unit-testing it there — more
  structure, and it would not have caught the original defect.
  Traces to: AC3, AC4.
- **Replace the fixed-width block rather than adding a diagram beside it.**
  Duplicating the same content in two forms is a drift pair. The block being
  replaced already fails docs-site's 375 px floor.
  Traces to: AC6, AC7.

### State & control flow

Config load → `validateConfigRefined` → (today: `coerceLegacyMarkdownPlugins`
synthesises `markdown.processor`; after T2: the config supplies it directly) →
Starlight's `astro:config:setup` reads `config.markdown.processor` and appends
its own remark/rehype plugins via `applyStarlightMarkdownPlugins` → build →
`remarkMermaid` replaces each `code` node with `lang === 'mermaid'` by an HTML
node carrying `class="mermaid-diagram" data-mermaid="<encoded source>"` →
`Footer.astro`'s client script finds those nodes and renders, or falls back to a
`<pre>`.

The migration removes exactly one hop from that chain — the shim — and nothing
downstream of it can tell the difference. That is the claim T1's assertion
exists to check rather than assert.

### Quality attributes (NFRs)

- **No horizontal scroll at 375 px** (`docs-site/AGENTS.md`): the replaced block
  is fixed-width preformatted text and is the reason this constraint currently
  fails on this page; the Mermaid SVG scales. Verified in T4, not asserted.
  Traces to: AC7.
- **Graceful degradation:** `Footer.astro:99-114` writes the decoded source into
  a `<pre>` when `import('mermaid')` rejects, so a reader without JavaScript
  still gets the content — the property the fixed-width block had for free and
  which this change must not lose. Traces to: AC7.

### Dependencies & integration

`@astrojs/markdown-remark@7.2.2`, already a declared direct dependency of
`docs-site/`, pinned equal to astro's exact optional-peer range. No dependency
moves; neither lockfile changes.

## Tasks

### T1: the emitted Mermaid placeholder is asserted, and the assertion can fail

**Depends on:** none

**Touches:** docs-site/src/content/docs/getting-started/three-loops.md, web/src/test/rendered-output.test.ts

**Tests:**
- New case in `web/src/test/rendered-output.test.ts`, beside "AC8: every markdown
  table sits in a focusable scroll region": every `.mermaid-diagram` in
  `build/docs` carries a `data-mermaid` attribute that `decodeURIComponent`s to
  a non-empty string, and the docs corpus contains at least one such element.
  Verifies spec AC3 and AC4.
- The existing AC8 case stays green at 230 tables / 230 wrappers, unmodified.
  This is the rehype half of the same claim and the baseline it must return to.

**Approach:**
- Replace lines 8-14 of
  `docs-site/src/content/docs/getting-started/three-loops.md` with a fenced
  ```mermaid block carrying the three packs, three lead agents and six gate
  labels the block carries today (spec AC6).
- Add the assertion. The "at least one" half is load-bearing and separate from
  the per-element half: an empty corpus satisfies a `for` loop vacuously, which
  is the state the site is in today.
- Run the full gate sequence: `python3 tools/build-site.py --journeys-only`,
  `npm run build --prefix web`, `npm run test:plugins --prefix docs-site`,
  `python3 tools/build-site.py`, `npm run build --prefix docs-site`,
  `npm test --prefix web`.
- **Mutation:** comment `remarkMermaid` out of the config's `remarkPlugins`,
  rebuild, and confirm the new case goes red and AC8 stays green. Restore, and
  confirm `git status` is clean of the mutation before continuing.

**Done when:** `npm test --prefix web` reports 129 passed / 0 skipped against a
freshly built site, and the mutation above has been observed to turn the new
case red and only that case.

### T2: the site builds on `markdown.processor` with no deprecation notice

**Depends on:** T1

**Touches:** docs-site/astro.config.ts

**Tests:**
- T1's assertion, unmodified, still green — this is the whole point of T1
  landing first. Verifies spec AC3.
- AC8 still green at 230/230. Verifies the rehype half survived.
- The build's own output: no line matching `\[astro\].*deprecated`. Verifies
  spec AC2.

**Approach:**
- Import `unified` from `@astrojs/markdown-remark` in
  `docs-site/astro.config.ts`.
- Replace the `markdown: { remarkPlugins, rehypePlugins }` block with
  `markdown: { processor: unified({ remarkPlugins: [remarkMermaid],
  rehypePlugins: [rehypeScrollableTables] }) }`.
- Rewrite the comment above it. The current comment records the historical
  silent no-op of a `unified({...})` wrapper — the same construct being
  reintroduced here — so it must now say what changed and point at the
  assertion that would catch a repeat, rather than warning against the shape.
- Re-run the full gate sequence from T1 and capture the build output to confirm
  the deprecation line is absent.

**Done when:** a full `npm run build --prefix docs-site` emits 225 pages with no
`[astro] ... deprecated` line, and `npm test --prefix web` is 129 / 0 skipped.

### T3: `docs-site/AGENTS.md` describes the configuration that exists

**Depends on:** T2

**Touches:** docs-site/AGENTS.md

**Tests:**
- `grep -n "nothing here imports" docs-site/AGENTS.md` returns nothing.
- `grep -n "are deprecated" docs-site/AGENTS.md` returns nothing that claims
  this site still uses the deprecated keys.
- `grep -n "markdown-remark" docs-site/AGENTS.md` shows a bullet naming
  `astro.config.ts` as the importer. Verifies spec AC8.

**Approach:**
- Rewrite the `@astrojs/markdown-remark` bullet. Its current premise — "a direct
  dependency that nothing here imports … reads as unused" — is false after T2,
  and the hoisting story it tells is no longer the reason the declaration
  matters. Keep the surviving duty (pin equality) and point at the gate that now
  enforces it rather than restating it as prose.
- Delete the deprecation bullet, which T2 resolves. Do not replace it with a
  "migrated on <date>" note — the spec body is the record and
  `docs-site/AGENTS.md` is present-tense guidance.
- Re-run `make lint-ruff` and the AGENTS.md lint suite
  (`tools/test_lint_agents_md_*.py`), which gate this file's block structure.

**Done when:** the three greps above give the stated answers and the AGENTS.md
lint suite passes.

### T4: the diagram renders for a reader

**Depends on:** T2

**Touches:** none

**Tests:** none — this task's mode is visual / manual QA by construction. Its
subject is a client-side dynamic import that no build-time assertion reaches.

**Approach:**
- Serve the built site and load
  `/agent-ready-repo/docs/getting-started/three-loops/`.
- Record the observed result at 1440 px and 375 px, in light and dark theme:
  is there a rendered SVG, and does the document scroll horizontally?
- Load once more with JavaScript disabled and record what a reader sees.
- If the client render is broken, stop and surface: that is a pre-existing
  defect this work is the first to hit, and the decision to fix it or to keep
  the fixed-width block is the owner's. See Risks.

**Done when:** the six observations above are recorded in the PR, showing a
rendered diagram with no horizontal document scroll in all four
viewport/theme combinations, and a readable caption with JavaScript off.

### T5: the figure survives an experience review

**Depends on:** T4

**Touches:** docs-site/src/content/docs/getting-started/three-loops.md, docs-site/src/styles/starlight.css, docs-site/astro.config.ts, web/src/test/rendered-output.test.ts

**Tests:**
- The caption assertion added to
  `web/src/test/rendered-output.test.ts`, proven by deleting the caption and
  observing that one case go red.
- The placeholder assertion from T1, unchanged and still green.

**Approach:**
- Dispatch `experience-reviewer` against the *rendered* page with the grounded
  references (`docs/design/principles/tech-site.md`, the docs-site
  creative-direction doc), not against the diff.
- Address its findings. The Blocker is the load-bearing one: a left-to-right
  row of three boxes is the canonical rendering of a pipeline, and this page
  says "peers, not a hierarchy" twice.
- Re-measure in the browser after the redesign rather than assuming the fix
  landed.

**Done when:** the diagram reads as a cycle of peers, every loop shows its own
gate, the figure sits in § How the loops connect, a caption carries the
scriptless and screen-reader reading, and the browser pass is re-run clean.

## Rollout

Delivery is a big bang and fully reversible: the whole change is three tracked
text files and one test, and reverting the commit restores the previous
rendering on the next Pages deploy. No infrastructure, no external system, no
sequencing constraint beyond the build order already stated in Boundaries. Note
that the job which runs these builds — pages.yml's `build` — is not a required
status check, so a merge cannot rely on CI to catch a regression here; the local
gate sequence is the gate.

## Risks

- **The mermaid client render has never executed on a published page.** T1 is
  the first time it will. If it fails, `Footer.astro`'s fallback shows the
  source as text — degraded but not broken — and T4 surfaces the choice rather
  than the plan silently absorbing a second piece of work.
- **The page-count and table-count baselines (225, 230/230) drift** whenever
  content lands from another branch. They are stated as the values to compare
  against a same-session baseline build, not as constants to assert; a
  difference means re-baseline on the merge-base, not a finding.
- **The local browser gate is unreliable on the development host, and astro
  daemonises `preview` under an agent.** A timeout here is not evidence about
  the change; `web/playwright.config.ts` sets `ASTRO_PREVIEW_BACKGROUND` for the
  gate, and a hand-run preview must be stopped with
  `npm exec --prefix web -- astro preview stop --root web`.

## Changelog

- 2026-08-23: initial plan. Control-before-change ordering (T1 before T2) chosen
  deliberately over the obvious migrate-then-verify order, because the site has
  already shipped a silently-inert `unified({...})` wrapper once and a control
  first observed after the change cannot tell "still works" from "never worked".
- 2026-08-23: added T5. T4's browser pass was expected to confirm the client
  render and instead surfaced two consequences of publishing the site's first
  diagram, so the plan grew a review-and-respond task rather than absorbing
  design decisions inside T4.

  Three measurements drove it, each of which contradicted something believed
  when the plan was written:

  1. **A no-JavaScript reader saw a blank gap.** `Footer.astro`'s `<pre>`
     fallback fires only when `import('mermaid')` *rejects*; with scripts off
     the script never runs at all, so nothing replaced the empty placeholder.
     The first fix — emitting the Mermaid source into the placeholder at build
     time — was itself measured and rejected: 410 px tall, and 577 px wide in a
     341 px column at a 375 px viewport, a 236 px overflow of exactly the kind
     the change set out to remove. The shipped answer is an author-written
     caption, which is legible in every state and doubles as the figure's
     description.
  2. **astro's content cache served a stale render across a config-only
     change.** Adding the fallback changed no Markdown, so `docs-site/.astro`
     and `node_modules/.astro` replayed the previous render and the emitted HTML
     did not move. Every build-output claim in this spec was therefore re-taken
     from a cold cache. A config change to a remark plugin does not invalidate
     that cache.
  3. **The first diagram contradicted the page.** `flowchart LR` renders three
     boxes joined left to right, which is the canonical shape of a pipeline, on
     a page whose thesis is stated twice as "peers, not a hierarchy". The
     redesign moves the gates inside each loop as stops, so no loop is drawn
     ungated and no gate label sits over a subgraph fill, and adds the inward
     `findings` edge — which is what makes the figure a cycle rather than a
     line. dagre then places `core` as the hub, which matches the inner/outer
     split the section states three lines below. Declaring the feedback edge
     first was tried and produces an identical layout, so the ordering is
     dagre's cycle-breaking and not something the source controls.
