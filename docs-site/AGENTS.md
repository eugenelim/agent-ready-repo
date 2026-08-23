# AGENTS.md — `docs-site/`

Applies to `docs-site/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Site boundary

`docs-site/` is the technical documentation site. `tools/build-site.py` generates
much of `src/content/docs/` from `guides/**` and `packs/**`; edit sources, not
generated content. Package manifests own dependency versions.

## Build

Build order is load-bearing: `web/` cleans repository `build/`, so build it before
this site writes `build/docs/`.

```bash
python3 tools/build-site.py
npm run build --prefix web
npm run build --prefix docs-site
```

## Action-changing traps

- Generate content before starting the docs development server.
- The repository, not Starlight, checks rendered internal links after both builds.
- Styling changes must preserve no horizontal scroll at 375 px, usable focus in
  both themes, and reduced-motion behavior.
- Check `allowScripts` against install-script entries by eye when the lockfile moves.
- After a Starlight upgrade, re-verify dependent integration contracts against
  vendored `node_modules/@astrojs/starlight` components.

## Deeper pointers

Use `make site-link-check` for rendered-link verification. Current site architecture
belongs in `docs/architecture/`; style and component implementation stays with code.
