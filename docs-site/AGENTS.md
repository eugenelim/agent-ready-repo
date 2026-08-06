# AGENTS.md — `docs-site/` (Starlight tech docs)

The technical documentation site, served at `/agent-ready-repo/docs/`. Built
with Astro + Starlight; content under `src/content/docs/` is largely
generated from `guides/**` and `packs/**` by `tools/build-site.py`.
Styling is governed by the `docs-site-design-refresh` spec
(`docs/specs/docs-site-design-refresh/`).

## Dependencies (recorded per repo AGENTS.md § "Check before acting")

All exact-pinned. Fonts are self-hosted (no runtime font CDN calls);
mermaid is bundled (no runtime script CDN calls).

| Dependency | Version | Why |
| --- | --- | --- |
| [`astro`](https://astro.build) | `7.1.0` | Static-site generator |
| [`@astrojs/starlight`](https://starlight.astro.build) | `0.41.4` | Docs framework (sidebar, search, i18n-ready shell) |
| [`@fontsource-variable/source-serif-4`](https://fontsource.org/fonts/source-serif-4) | `5.3.0` | Display serif for h1/h2/wordmark. **Wire the `opsz.css` entry, not `index.css`** — the default stylesheet is `wght`-only and silently drops optical sizing |
| [`@fontsource-variable/inter`](https://fontsource.org/fonts/inter) | `5.3.0` | Body/UI sans (`'Inter Variable'`), matches `web/` |
| [`@fontsource/jetbrains-mono`](https://fontsource.org/fonts/jetbrains-mono) | `5.3.0` | Code mono (weights 400/500/600/700), matches `web/` |
| [`mermaid`](https://mermaid.js.org) | `11.16.1` | Diagram rendering — bundled + lazy-imported in `src/components/Footer.astro` with `securityLevel: 'strict'`; replaced the former jsdelivr runtime script |

Supply-chain posture: the lockfile's only `"hasInstallScript": true`
entries must stay within the versioned `allowScripts` keys in
`package.json` (`esbuild@0.28.1`, `fsevents@2.3.3`). **Known gap
(deferred, `workspace.toml [backlog]` slug `docs-site-npm-sca-gap`):** no
SCA scanner (npm audit/Dependabot) is wired repo-wide; bundling mermaid
vendors its transitive tree into shipped output, so that unscanned surface
is net-new until a scanner lands.

## Styling: the docs palette deliberately diverges from `web/`

`src/styles/starlight.css` is a **self-contained** token sheet (`--doc-*`
primitives → `--sl-*` Starlight slots): enterprise cobalt on cool neutral
grounds, Source Serif 4 display headings. It does **not** import the
`tokens.css` that `tools/build-site.py` still copies from `web/` (copy is
vestigial; removal deferred). Do not re-import it; do not "align" docs
colors to `web/`'s amber system without a new spec.

The primitive components (`src/components/primitives/*.astro`) still
consume `web/`-style `--ds-*` token names; a compatibility block at the
bottom of `starlight.css` re-derives exactly the consumed names onto the
doc palette. **Semantic state tokens (`--ds-state-*`) stay hue-distinct**
(green/red/orange/blue/gray) — never collapse them into the accent. If you
add a primitive that consumes a new `--ds-*` name, define it in the
compatibility block (the extraction check below is the contract).

Contrast floor: every text/ground pair ≥ 4.5:1 in both themes; measured
values live in the spec's `plan.md` LLD tables. Re-run the check when
touching palette values.

```bash
# extraction check: every consumed token name must be defined locally
python3 - <<'PY'
import re, pathlib
consumed=set()
for f in pathlib.Path('src').rglob('*.astro'):
    consumed |= set(re.findall(r'var\((--(?:ds|prim)-[a-z0-9-]+)', f.read_text()))
css=pathlib.Path('src/styles/starlight.css').read_text()
consumed |= set(re.findall(r'var\((--(?:ds|prim)-[a-z0-9-]+)', css))
defined=set(re.findall(r'(--(?:ds|prim)-[a-z0-9-]+)\s*:', css))
print(sorted(consumed-defined) or "OK")
PY
```

## Build (canonical build-order fact)

**Order is load-bearing:** the `web/` Astro build cleans `build/` (repo
root) on every run, so it MUST run before this site writes into
`build/docs/`. Full sequence (mirrors `.github/workflows/pages.yml`):

```bash
python tools/build-site.py            # sync generated content into src/
npm run build --prefix web            # cleans + writes build/
npm run build --prefix docs-site      # writes build/docs/
```

`web/AGENTS.md` references this section rather than restating it.

## Development

```bash
python tools/build-site.py   # first — generated content + tokens.css copy
npm run dev --prefix docs-site
```

Mermaid blocks in content are transformed at build time into
`.mermaid-diagram[data-mermaid]` placeholders (remark plugin in
`astro.config.ts`) and rendered client-side by the bundled loader in
`Footer.astro`, which re-renders on theme toggle.

## Broken links

Starlight does not fail the build on broken internal links (unlike the
previous MkDocs `--strict` mode). Broken anchors and cross-page links in
`guides/**` must be caught by manual review or a link-checker tool. To
check locally: run the build sequence above and inspect `build/docs/`.

## What to verify on styling changes

- No horizontal body scroll at 375 px on content pages.
- Both themes (`data-theme` light/dark) fully mapped — no half-themed
  surface, including the pagefind search overlay and mermaid diagrams.
- `:focus-visible` visible in both themes; transitions stay inside
  `@media (prefers-reduced-motion: no-preference)`.
- Starlight is pinned; its internal class names (`.site-title`,
  `.sidebar-content`, `.sl-markdown-content`, …) are a styling contract —
  re-verify against `node_modules/@astrojs/starlight` after any upgrade.
