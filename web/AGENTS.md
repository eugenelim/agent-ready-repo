# AGENTS.md — `web/` (Astro marketing site)

The platform-site marketing anchor, served at `/`. Approved as a new top-level
directory by [RFC-0061](../docs/rfc/0061-web-top-level-directory.md); scope,
content, and aesthetics are defined by the
[platform-site spec](../docs/specs/platform-site/spec.md).

## Dependencies (recorded per repo AGENTS.md § "Check before acting")

This directory introduces the repo's first Node.js build toolchain. New
dependencies are recorded here before they are added.

| Dependency | Version | Why |
| --- | --- | --- |
| Node.js | `>=24.0.0` (see `package.json` `engines`) | Astro build/runtime toolchain |
| [`astro`](https://astro.build) | pinned `7.1.0` (exact, not a range) | Static-site generator for the marketing pages; pinned for reproducible CI |
| [`@astrojs/sitemap`](https://docs.astro.build/en/guides/integrations-guide/sitemap/) | pinned `3.7.3` (exact, not a range) | Generates `sitemap-index.xml` + `sitemap-0.xml` at build time for SEO (Phase 4) |
| [`@fontsource-variable/inter`](https://fontsource.org/fonts/inter) | pinned `5.3.0` (exact, not a range) | Self-hosts the Inter variable font (wght 100–900), replacing the `fonts.googleapis.com` runtime call. Family registers as `'Inter Variable'` |
| [`@fontsource/jetbrains-mono`](https://fontsource.org/fonts/jetbrains-mono) | pinned `5.3.0` (exact, not a range) | Self-hosts JetBrains Mono (weights 400/500/600/700/800 — the set the components actually use) for code/mono type, replacing the `fonts.googleapis.com` runtime call |

Build-time only. This is our own site infrastructure — not a primitive or
framework prescribed to adopters (see RFC-0061's charter-neutrality analysis).
No CSS framework (Tailwind, Bootstrap, UnoCSS): the `--ds-*` token system in
`src/styles/` is the sole color/spacing authority (platform-site spec, Boundaries).

## Test dependencies

Added for `site-ui-primitives` Phase 2C (T1). All are `devDependencies` — zero
runtime impact.

| Dependency | Version | Why |
| --- | --- | --- |
| [`vitest`](https://vitest.dev) | pinned `4.1.10` | Unit test runner; replaces no prior runner |
| [`@vitest/ui`](https://vitest.dev/guide/ui) | pinned `4.1.10` | Optional browser UI for vitest |
| [`jsdom`](https://github.com/jsdom/jsdom) | pinned `30.0.0` | DOM environment for vitest tests of `.astro`-rendered HTML |
| [`axe-core`](https://github.com/dequelabs/axe-core) | pinned `4.12.1` | Accessibility engine; used directly in tests via `import axe from 'axe-core'` |
| [`@playwright/test`](https://playwright.dev) | pinned `1.62.0` | Browser automation; config at `playwright.config.ts`. Run the deploy-blocking subset with `npm run test:e2e:gate` — see § Browser gate below. `npx playwright test` runs EVERYTHING, including two specs that write PNGs into tracked `docs/specs/**`. |

Note: `@axe-core/vitest` does not exist on npm (verified 2026-07-28). `axe-core` is
used directly. Test entry point: `npm test` (`vitest run`); browser gate below.

## Browser gate

`spec/site-browser-quality-gate`. Deploy-blocking subset: `npm run test:e2e:gate`.
It is an explicit ALLOWLIST of read-only specs — **not** `npx playwright test`, which
also runs the two specs that write PNGs into tracked `docs/specs/**` while required CI
must leave the tree clean. Adding a spec to the gate means editing
`scripts["test:e2e:gate"]` here AND `EXCLUDED` in
`tools/test_browser_gate_subset.py`; that test asserts the allowlist both ways, and
`tools/test-pages-workflow.py` pins the script and step posture with a mutation
self-test. It reads the emitted artifact, so the combined build must run first in its
mandated order — commands and the reason in
[`docs/guides/how-to/verify-a-site-release.md`](../docs/guides/how-to/verify-a-site-release.md).
Route strings come from `src/test/e2e/site-base.ts`; never write
`/agent-ready-repo/` into a spec.

## Supply-chain posture

Two controls, only one of them automated:

- **Known-CVE scanning is wired** (ADR-0083, `docs/specs/npm-sca-gate/`).
  `tools/audit-npm.py` runs `npm audit --audit-level=moderate` over this lockfile as
  a leg of `make sast`, so it gates locally and in `build-check.yml`. Both npm
  lockfiles are in the Makefile's `SAST_CONFIG`, so a lockfile-only diff still
  triggers the gate. Fix a finding with `npm audit fix --package-lock-only`;
  suppress one only when there is no fix, via a reasoned entry in
  `tools/npm-audit-allowlist.toml`. The gate audits a known-vulnerable
  **canary** pin first — a mirror whose advisory endpoint returns
  200-with-nothing produces a report identical to a clean one, so a green run
  is only trustworthy if the canary reported. Exit 2 (tool error) is distinct
  from exit 1 (findings); never read it as a pass.
- **Install-script vetting is by hand, and this lockfile already diverges.**
  `package.json` `allowScripts` vets `esbuild@0.28.1` and `fsevents@2.3.3`, but
  the lockfile also carries `playwright/node_modules/fsevents@2.3.2`, which is
  outside those keys — hence the `npm warn allow-scripts` on install. It is
  accepted as-is (a Playwright transitive on a devDependency path); machine
  enforcement is deferred under `workspace.toml [backlog]` slug
  `npm-allowscripts-enforcement`, which is also where closing this divergence
  belongs. Check the set by eye when the lockfile moves.

## Build

- `npm run build` emits into `../build/` (repo root), NOT `web/dist/`
  (`astro.config.ts` `outDir`).
- Build order relative to the docs site is load-bearing; the canonical
  build-order fact lives in [`docs-site/AGENTS.md`](../docs-site/AGENTS.md)
  § Build — read it before touching either build.
- Two inputs to this build are generated, both by
  `tools/build-site.py --journeys-only`:
  `web/src/content/journeys/` from `packs/*/JOURNEY.md`, and
  `web/src/lib/now-highlights.generated.json` from released `Highlights` in
  `docs/product/changelog.md`. Running `npm run build --prefix web` without that
  step will fail if either is absent. The `pages.yml` CI job runs it before the
  Astro build automatically.
- Both are committed, and both are checked for drift: a changelog edit that is
  not re-projected fails
  `tools/test_build_site_routing.py::test_the_committed_now_projection_matches_the_changelog_source`.
  The projection runs in the `--journeys-only` pass rather than the full pass
  because the full pass runs AFTER this build, so a projection emitted only
  there would always be one build stale for the renderer reading it.

## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.


## Mobile viewport

The viewport meta tag (`width=device-width, initial-scale=1`) is set in
`src/components/layout/SiteLayout.astro`. Do not add it elsewhere or duplicate it.

**What to verify on every change:** check that no element causes horizontal
scroll of the page body at 375 px width. Code blocks inside `<Content />`
rendered markdown use the base `pre { overflow-x: auto }` rule — they scroll
internally, not the page.

## Links in markdown content

Links inside markdown files rendered via `<Content />` (pack and journey bodies)
**cannot** use Astro's `withBase()` — they are plain HTML after rendering.

- Use **relative paths** for cross-site links (e.g., `../../docs/guides/atlassian/`).
- Absolute paths starting with `/` are resolved against the origin root, not the
  subpath base (`/agent-ready-repo`), and will 404 on GitHub Pages.
- The `docsUrl` and `journeyUrl` frontmatter fields are the canonical navigation
  entry points and are already processed through `withBase()` by the template.

## Navigation cohesion

Every pack that has documentation must set `docsUrl` in its frontmatter. Every
pack with a journey narrative must set `journeyUrl`. These are the two navigation
entry points the pack template exposes; leave neither empty if the content exists.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles](https://docs.astro.build/en/guides/styling/)
