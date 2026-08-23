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
- `@astrojs/markdown-remark` is a direct dependency that nothing here imports,
  and it must stay declared. Astro and Starlight have carried it as an
  *optional* peer since before astro 7.2, and the build worked only because npm
  hoisted `@astrojs/mdx`'s transitive copy to the root, where astro resolved it.
  npm later placed that copy under `@astrojs/mdx/node_modules/` instead and
  `astro build` exited 1, because `astro.config.ts`'s
  `markdown.remarkPlugins`/`rehypePlugins` fail config validation when the
  package is unresolvable. The declaration turns root placement from luck into
  a requirement. Two duties come with it: keep the pin equal to `astro`'s exact
  optional-peer version — `tools/test_browser_gate_subset.py` refuses from
  `gate-main` when the manifest, the lockfile and that peer disagree, or when
  Starlight's declared range stops accepting the pin — and expect an astro major
  to arrive alone and need both moved together.
- `markdown.remarkPlugins` and `markdown.rehypePlugins` are deprecated — every
  docs build prints so. The migration is `markdown.processor: unified({...})`
  from `@astrojs/markdown-remark`; until it happens, an astro major can drop
  the legacy keys and break this build.
- Under an agent, `astro dev` forks a detached server and returns at once with
  JSON output, leaving it recorded in `.astro/` — so the development server the
  § Build commands tell you to start is not the process you launched. A *live*
  orphan blocks the next start on *any* port, so stop it rather than deleting
  the record, which frees nothing: `npm exec --prefix docs-site -- astro dev
  stop --root docs-site`. `--root` is load-bearing — astro resolves the project
  from the working directory, not from `--prefix`, so without it the command
  reports nothing running and leaves the orphan holding the port.
- After a Starlight upgrade, re-verify dependent integration contracts against
  vendored `node_modules/@astrojs/starlight` components.

## Deeper pointers

Use `make site-link-check` for rendered-link verification. Current site architecture
belongs in `docs/architecture/`; style and component implementation stays with code.
