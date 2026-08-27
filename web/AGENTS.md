# AGENTS.md — `web/`

Applies to `web/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Site boundary

`web/` is the marketing site served at `/`. Package manifests own dependencies;
`tools/build-site.py --journeys-only` generates committed journeys and highlights
used by this site. Do not edit generated inputs by hand.

## Action-changing traps

- Build marketing before docs: the web build cleans repository `build/`.
- Markdown content uses relative cross-site links; origin-root paths fail under a
  subpath deployment.
- Keep pack `docsUrl` and `journeyUrl` populated when those materials exist.
- Use the e2e gate command, not the unrestricted browser suite, for deploy checks.
- Gate browser: the Playwright-managed Chromium `playwright.config.ts` declares; never
  substitute `channel="chrome"`, which is not the engine the deploy is judged on.
- A missing browser is routine, not a finding — `tools/repo/frontend_runtime.py browsers`
  reports the resolved cache, `install-browsers` provisions it. Never record install
  state here: it is machine-local and inverts without warning.
- Full Playwright runs rewrite tracked snapshots; stage files explicitly, never `git add -A`.
- Run `tools/lint-npm-allow-scripts.py`; when it fires, add a reviewed
  `allowScripts` entry or repin the dependency so it dedupes to a reviewed version.
- Keep `web/package.json`'s `fsevents@2.3.3` override: Playwright pins 2.3.2 exactly;
  the override collapses its nested copy so the `allowScripts` gate can be enforced.
- Under an agent, `astro dev` and `astro preview` fork a detached server and
  return at once with JSON output. The corollary is the reason this gets closed
  as "works for me": a human running the identical command in the identical
  worktree will **not** reproduce it, because the fork is keyed on agent
  detection rather than on anything about the command or the tree. Report it
  with that stated, or the first reply is a screenshot of it working. The gate
  is insulated (`playwright.config.ts`
  sets `ASTRO_PREVIEW_BACKGROUND`); a hand-run `npm run preview` is not, and
  leaves a *live* orphan recorded in `.astro/` that blocks the next start on
  *any* port. `preview`'s foreground path ignores `--force` despite its own
  error text recommending it, so stopping it is the only route, and deleting the
  record frees nothing: `npm exec --prefix web -- astro preview stop --root web`.
  `--root` is load-bearing — astro resolves the project from the working
  directory, not from `--prefix`.
- This site sets no `markdown` config, so it renders through astro's default
  processor while `docs-site/` pins the legacy `unified()` one. The two
  co-deployed sites are deliberately on different engines; do not assume output
  parity when moving content between them.
- Define the viewport meta tag once in `src/components/layout/SiteLayout.astro`; never duplicate it.

## Essential commands

```bash
npm run build --prefix web
npm run test:e2e:gate --prefix web
```

## Deeper pointers

The canonical local build order is [docs-site Build](../docs-site/AGENTS.md#build).
Current site architecture belongs in `docs/architecture/`; component details belong
beside their implementation and tests.
