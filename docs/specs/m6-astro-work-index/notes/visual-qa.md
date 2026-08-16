# Visual QA: Astro work index

Date: 2026-08-15

## Session scope

This session verifies the static populated and empty `/work/` states produced by
the build-time projection. Live dispatch, refresh, write-back, telemetry, and the
control plane are outside this session and remain outside the feature.

The current runtime exposes no browser-control tool, so this record contains
only evidence available from component rendering, accessibility analysis, the
Astro build, generated HTML, and CSS inspection. No screenshot, viewport render,
pointer interaction, or measured browser overflow result is claimed.

## Fixture driver

`web/src/test/work-index.test.ts` renders `WorkIndex.astro` directly through the
Astro container. Its populated fixture covers all six counts, active/ready/
attention ordering, finding-provided next actions, separated brief/shaping/
backlog context, and inert markup payloads. Its empty fixture sets all six
collections to zero and checks the `work-intake` and `workspace-status` guidance.
No fixture route or fake workspace record ships in the site.

## Evidence

- `npm test --prefix web -- --run src/test/work-index.test.ts` passed 9 tests.
  The rendered fragment passed `axe-core` with zero violations; the test also
  checks the heading/section structure and both navigation render paths.
- `npm run build --prefix web` built 47 pages and emitted
  `build/work/index.html`. The route was generated from a real invocation of the
  production workspace-status CLI through `tools/export_work_index.py`.
- `make site-link-check` rebuilt both Astro sites after the exporter timeout
  regression fix and checked 55,014 emitted links across 266 pages with no
  failures.
- Static generated-HTML inspection found the snapshot qualifier, all six count
  labels, delivery buckets in active/ready/attention order, canonical finding
  codes and next actions, and separate upstream-context disclosures. It found no
  `<script>` element in `build/work/index.html`.
- Static CSS inspection found a 760 px breakpoint that reduces the six-count row
  to two columns, `min-width: 0` on grid children, and `overflow-wrap: anywhere`
  on repository-derived paths and labels. These are the intended 375 px
  containment controls; actual horizontal body overflow was not measurable
  without a browser runtime.
- Keyboard behavior is native HTML: primary navigation uses links and the
  context disclosures use `<details>/<summary>`. Focus treatment comes from the
  shared site layout. No new motion is present; the existing navigation
  transition remains confined to `prefers-reduced-motion: no-preference`.
- Static design-intent inspection found no severity-3-or-higher issue against
  precision authority or staged revelation: canonical status and next action
  lead, repository identifiers follow, and the 133-item backlog stays collapsed
  under explicitly non-executable context. This is not a browser-based visual
  review.

## Browser-only follow-up

On 2026-08-16, the user opened `/work/` in a browser, reported that tab
navigation works through the page, and found the rendered page visually sound.
The user then confirmed all three remaining checks: no horizontal body scroll
at 375 px, no new motion with reduced motion enabled, and status that remains
understandable without relying on color. This closes the browser-only checks
for the populated route. The empty-state evidence remains the component render
and automated accessibility check described above; no public fixture route or
fake workspace record was added for a browser preview.
