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

- Anchor a reader or navigation decision on [the prime journey](../docs/design/journeys/team-orientation-future-state.md),
  not a content brief: this surface owns its stages 4-5, `web/` owns 1-3, and
  changing a stage re-gates through `approve-journey`.
- Generate content before starting the docs development server.
- The repository, not Starlight, checks rendered internal links after both builds.
- Styling changes must preserve no horizontal scroll at 375 px, usable focus in
  both themes, and reduced-motion behavior.
- Run `python3 tools/lint-npm-allow-scripts.py`; when it fires, add a reviewed
  `allowScripts` entry or repin the dependency so it dedupes to a reviewed version.
- `astro.config.ts` imports `@astrojs/markdown-remark` directly to build the
  site's Markdown processor with `unified({...})` as `markdown.processor`. Astro
  and Starlight carry it as an *optional* peer, so npm neither installs it nor
  warns on drift: the build once worked only because npm hoisted `@astrojs/mdx`'s
  transitive copy to the root, and exited 1 once npm nested that copy instead.
  The `package.json` declaration is what makes root placement a requirement
  rather than a hoisting accident. Keep the pin exact and equal across the
  manifest and the lockfile's two copies, and satisfying the peer astro and
  Starlight each declare; `tools/test_browser_gate_subset.py` refuses the lot
  from `gate-main`. Astro declared that peer exactly until 7.2.9 and as a caret
  from 7.2.10 — expect the shape to change, not just the number.
- The remark plugin that turns ```mermaid fences into placeholders is registered
  through that processor, and it has silently no-opped before. Nothing caught
  it, because no published page carried a fence. `getting-started/three-loops`
  now does, and `web/src/test/rendered-output.test.ts` asserts the emitted
  `.mermaid-diagram[data-mermaid]` — so keep at least one fence in the
  published corpus, or the plugin becomes unverifiable again.
- Under an agent, `astro dev` forks a detached server and returns at once, recorded
  in `.astro/` — so the server § Build tells you to start is not the process you
  launched. A *live* orphan blocks the next start on *any* port, and deleting the
  record frees nothing; stop it: `npm exec --prefix docs-site -- astro dev stop
  --root docs-site`. `--root` is load-bearing — astro resolves the project from the
  working directory, not `--prefix`; without it the command reports nothing running.
- After a Starlight upgrade, re-verify integration contracts against the vendored
  components. 0.42 swapped `<starlight-menu-button>` and its `aria-expanded` for
  the native popover API, silently breaking `PageFrame.astro`'s CSS reveal and
  every selector keyed to the old markup. That pane is `popover="manual"`, not
  `auto`, because an auto popover light-dismisses on the Product summary, which
  `site-shared-chrome` forbids; manual costs UA Escape, restored in that component.
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
