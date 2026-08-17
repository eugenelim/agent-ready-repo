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
| [`unist-util-visit`](https://github.com/syntax-tree/unist-util-visit) | `5.1.0` | AST walker for the two markdown-pipeline plugins in `astro.config.ts` (mermaid fences, `src/plugins/rehype-scrollable-tables.ts`). Previously resolved only through transitive hoisting; declared explicitly so an `npm install` dedupe cannot redden the docs build |

Supply-chain posture, two controls:

- **Known-CVE scanning is wired** (ADR-0083, `docs/specs/npm-sca-gate/`).
  `tools/audit-npm.py` runs `npm audit --audit-level=moderate` over this
  lockfile as a leg of `make sast`, so it gates locally and in
  `build-check.yml`. Both lockfiles are in the Makefile's `SAST_CONFIG`,
  so a lockfile-only diff still triggers the gate. Fix a finding with
  `npm audit fix --package-lock-only`; suppress one only when there is no
  fix, via a reasoned entry in `tools/npm-audit-allowlist.toml`.
  The gate audits a known-vulnerable **canary** pin first — a mirror whose
  advisory endpoint returns 200-with-nothing produces a report identical to
  a clean one, so a green run is only trustworthy if the canary reported.
  Exit 2 (tool error) is distinct from exit 1 (findings); never read it as
  a pass.
- **Install-script vetting is still by hand.** The lockfile's only
  `"hasInstallScript": true` entries must stay within the versioned
  `allowScripts` keys in `package.json` (`esbuild@0.28.1`,
  `fsevents@2.3.3`). Nothing enforces that yet — machine enforcement is
  deferred under `workspace.toml [backlog]` slug
  `npm-allowscripts-enforcement`. Check it by eye when the lockfile moves.

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
values live in the spec's `plan.md` LLD tables. When touching palette
values, re-run `python3 tools/check-docs-contrast.py` (from the repo
root) — it resolves the themed tokens from `starlight.css` and fails on
any pair below the floor.

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
`build/docs/`. Valid local full-generation sequence (`make site-link-check`
runs it and then the link checker):

```bash
python tools/build-site.py            # sync generated content into src/
npm run build --prefix web            # cleans + writes build/
npm run build --prefix docs-site      # writes build/docs/
```

CI is **not** identical — `.github/workflows/pages.yml` splits generation in two
(`build-site.py --journeys-only`, marketing build, full `build-site.py`, docs
build) and is canonical for the CI order; this section is canonical for the local
order and the marketing-before-docs invariant. Both run the checker after both builds.

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
previous MkDocs `--strict` mode), so the repository gates them after both
builds with `tools/check-rendered-site-links.py` — the implementation
authority for page and fragment resolution. Run `make site-link-check`.

## What to verify on styling changes

- No horizontal body scroll at 375 px on content pages.
- Both themes (`data-theme` light/dark) fully mapped — no half-themed
  surface, including the pagefind search overlay and mermaid diagrams.
- `:focus-visible` visible in both themes; transitions stay inside
  `@media (prefers-reduced-motion: no-preference)`.
- Starlight is pinned; its internal class names (`.site-title`,
  `.sidebar-content`, `.sl-markdown-content`, …) are a styling contract —
  re-verify against `node_modules/@astrojs/starlight` after any upgrade.
  Four touchpoints depend on Starlight internals beyond class names and need
  the same re-verification: the `PageTitle` override in
  `src/components/PageTitle.astro` reads `Astro.locals.starlightRoute.entry.data`
  and must keep `id="_top"` on the `<h1>` (Starlight's `PAGE_TITLE_ID`, which
  its skip link and on-this-page overview both target); the `Footer` override in
  `src/components/Footer.astro` reads
  `Astro.locals.starlightRoute.pagination` because Starlight does not pass
  pagination through component props; the `Breadcrumbs` child in
  `src/components/Breadcrumbs.astro` reads the normalized route-data sidebar
  union (`group.label`, `group.entries`, `link.href`, `link.isCurrent`),
  `entry.data.title`, and `siteTitleHref` to derive and label the current trail
  inside the supported `PageTitle` override; and the
  `rehypeScrollableTables` plugin (`src/plugins/rehype-scrollable-tables.ts`,
  wired in `astro.config.ts`) wraps markdown tables in a focusable scroll
  region, and the paired rule in our `src/styles/starlight.css` overrides
  Starlight's own `table { display: block; overflow: auto }` — which lives in
  `node_modules/@astrojs/starlight/style/markdown.css`, not in our file — so
  the wrapper, not the table, is the scroll container.
