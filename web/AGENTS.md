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
- Launch with `channel="chrome"`: no `ms-playwright` browser binaries are installed.
- Full Playwright runs rewrite tracked snapshots; stage files explicitly, never `git add -A`.
- Check `allowScripts` against install-script entries by eye when the lockfile moves.
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
