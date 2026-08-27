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
- Run `python3 tools/lint-npm-allow-scripts.py`; when it fires, add a reviewed
  `allowScripts` entry or repin the dependency so it dedupes to a reviewed version.
- `astro.config.ts` imports `@astrojs/markdown-remark` directly — it builds the
  site's Markdown processor with `unified({...})` and passes it as
  `markdown.processor`. Astro and Starlight both carry the package as an
  *optional* peer, so npm neither installs it nor warns when the versions
  drift, and the build once worked only because npm hoisted `@astrojs/mdx`'s
  transitive copy to the root. When npm later placed that copy under
  `@astrojs/mdx/node_modules/` instead, `astro build` exited 1: config
  validation fails when the package is unresolvable from the root. The
  declaration in `package.json` is what makes root placement a requirement
  rather than a hoisting accident. Two duties come with it — keep the pin equal
  to astro's exact optional-peer version, which
  `tools/test_browser_gate_subset.py` refuses from `gate-main` when the
  manifest, the lockfile and that peer disagree or when Starlight's declared
  range stops accepting the pin; and expect an astro major to arrive alone and
  need both moved together.
- The remark plugin that turns ```mermaid fences into placeholders is registered
  through that processor, and it has silently no-opped before. Nothing caught
  it, because no published page carried a fence. `getting-started/three-loops`
  now does, and `web/src/test/rendered-output.test.ts` asserts the emitted
  `.mermaid-diagram[data-mermaid]` — so keep at least one fence in the
  published corpus, or the plugin becomes unverifiable again.
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
- Starlight's `print:hidden` does **not** suppress an element whose own component
  `<style>` sets `display`, and it fails silently: both compile unlayered at
  `(0,1,0)` — Astro's `:where()` adds no specificity — and the print sheet links
  first, so the component wins. Suppress in that component's own `<style>`.
  Native Starlight components are unaffected; theirs sit in `@layer
  starlight.core`, which the unlayered utility outranks. Never fix this by
  layering a `docs-site` rule: `src/styles/starlight.css` is deliberately
  unlayered, and layering an override drops its `:focus-visible` `outline-offset`
  3px→2px, which no gate catches — `web/src/test/e2e/quality-assertions.ts` never
  reads `outlineOffset`. Full reasoning: the comment in `Footer.astro`.
- `docs-site` carries exactly one `@media print` rule, in `Footer.astro`, hiding
  the footer's nav groups (`spec/docs-site-print-chrome-suppression`). The frozen
  `site-browser-quality-gate/notes/print-audit.md` says "no print CSS from this
  programme" and is still correct — that is a different, earlier programme.

## Deeper pointers

Use `make site-link-check` for rendered-link verification. Current site architecture
belongs in `docs/architecture/`; style and component implementation stays with code.
