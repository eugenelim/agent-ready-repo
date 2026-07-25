---
id: starlight-migration
title: Migrate docs site from MkDocs Material to Starlight
status: Shipped
---

- **Status:** Shipped <!-- [x] set Shipped when all ACs pass — lint-spec-status invariant (a) -->
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)

Mode: full (new dependency, structural change, destructive operation)

**Objective**: Replace the MkDocs Material Python docs build (`site/`) with a standalone Astro + Starlight project (`docs-site/`), preserving all content, URLs, and the amber brand theme. Remove all MkDocs Python tooling.

Governance note: `docs-site/` is a new top-level directory. AGENTS.md § "Check before acting" requires an RFC for new top-level directories; `web/` was gated by RFC-0061. The user's brief explicitly authorised this approach (Option B); this implementation proceeds under that authorisation, and a follow-up RFC should be opened. (deferred: starlight-migration-rfc)

## Acceptance Criteria

- [x] AC1: All docs pages from the MkDocs nav tree are reachable under the same URL paths (`/agent-ready-repo/docs/...`). NOTE: `README.md` section-index files are renamed to `index.md` during aggregation, preserving the directory-index URL (e.g. `guides/core/` not `guides/core/readme/`).
- [x] AC2: The docs root (`/agent-ready-repo/docs/`) renders the home page with Quick Install tabs and Packs table.
- [x] AC3: Pagefind search index is generated — `build/docs/pagefind/pagefind.js` exists.
- [x] AC4: Dark mode toggle/CSS is present — `build/docs/index.html` contains `data-theme` attribute references or `.sl-theme-dark` class.
- [x] AC5: The amber/dark colour palette from `web/src/styles/tokens.css` is applied — `build/docs/_astro/*.css` contains `--sl-color-accent` mapped to amber values. (grep target: `grep -r "sl-color-accent" build/docs/_astro/ --include="*.css"`)
- [x] AC6: Mermaid diagrams render: `build/docs/packs/core/index.html` contains a `<div class="mermaid-diagram"` element (remark-injected placeholder), confirming mermaid blocks reach the client-side renderer.
- [x] AC7: Tabs in `getting-started/index.mdx` and `index.mdx` render using Starlight `<Tabs>` — the built HTML contains `starlight-tabs` attribute (Starlight's tab component marker).
- [x] AC8: Footer shows brand name, Platform link, GitHub link, PyPI link — `build/docs/index.html` contains all four strings.
- [x] AC9: Header/banner shows a back-link to the platform site — `build/docs/index.html` contains `← Platform` or `&larr; Platform`.
- [x] AC10: CI YAML has no `pip install`, no `mkdocs build`, and does contain `npm ci --prefix docs-site` and `npm run build --prefix docs-site`.
- [x] AC11: `site/` directory is fully removed — `ls site/` returns "No such file or directory".
- [x] AC12: `build/docs/` contains ≥ 185 HTML pages (`find build/docs -name "*.html" | wc -l`). Actual: 201 pages built.
- [x] AC13: Marketing site build is unchanged — `npm run build --prefix web` succeeds with no errors.

## Integration approach decision

**Option B — standalone Astro + Starlight project at `docs-site/`.**

Justification over Option A (Starlight integrated into `web/`):
- Starlight 0.41 has no `routePrefix` option; it injects a catch-all `[...slug]` route that would conflict non-trivially with the marketing site's existing `src/pages/` routes.
- The current build already has two steps (Astro marketing, then MkDocs); Option B replaces Python with Node.js without changing the separation model.
- Starlight owns its own Astro instance — `base: '/agent-ready-repo/docs'`, `outDir: '../build/docs'` — clean, documented, no undocumented routing behavior.

## Component mapping

| MkDocs construct | Starlight equivalent |
|---|---|
| `!!! note/warning/tip/danger` | Not used in current content (0 instances in guides + packs) |
| `=== "Tab"` tabbed syntax | Starlight `<Tabs><TabItem label="…">` MDX — only in 2 static files |
| Mermaid code blocks | Remark plugin transforms to `<div class="mermaid-diagram" data-mermaid="…">` + client-side mermaid.js |
| MkDocs nav YAML | Starlight `sidebar` config in `docs-site/astro.config.ts` |
| `extra_css: [tokens.css, extra.css]` | Starlight `customCss: [...]` pointing at `docs-site/src/styles/starlight.css` |
| `main.html` announce block | Custom `Banner` component override (Starlight 0.33+ removed top-level `banner` config) |
| `overrides/partials/footer.html` | Starlight `components: { Footer }` override |
| `packs/*/README.md` aggregation | `tools/build-site.py` adapted: targets `docs-site/src/content/docs/packs/`, renames READMEs to index.md, injects frontmatter (strips H1 from body to avoid duplicate heading), strips .md link suffixes |

## URL structure

- Docs home: `https://eugenelim.github.io/agent-ready-repo/docs/`
- All child pages: `https://eugenelim.github.io/agent-ready-repo/docs/<slug>/`
- Astro config: `site: 'https://eugenelim.github.io/agent-ready-repo'` (matches web/ convention; base is an absolute path so Astro's `new URL(pathname, site)` resolves correctly), `base: '/agent-ready-repo/docs'`, `outDir: '../build/docs'`

## Theming

`docs-site/src/styles/starlight.css` imports `tokens.css` (copied to `docs-site/src/styles/` by `build-site.py` at build time) and maps the amber palette to Starlight CSS variables:
- `--sl-color-accent` → amber value from design tokens
- `--sl-color-accent-low` → lower-contrast amber
- `--sl-color-accent-high` → higher-contrast amber
- Fonts: Inter, JetBrains Mono

## CI change

Replace:
```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- name: Install site dependencies
  run: pip install -r site/requirements.txt
- name: Aggregate content
  run: python tools/build-site.py
- name: Build site
  run: mkdocs build --config-file site/mkdocs.yml --strict
```

With:
```yaml
- uses: actions/setup-node@v4
  with:
    node-version: "24"
    cache: npm
    cache-dependency-path: docs-site/package-lock.json
- name: Install docs-site dependencies
  run: npm ci --prefix docs-site
- name: Aggregate content
  run: python tools/build-site.py
- name: Build docs site
  run: npm run build --prefix docs-site
  env:
    ASTRO_TELEMETRY_DISABLED: "1"
```

Python is available on `ubuntu-latest` without a setup step; `tools/build-site.py` only needs stdlib. If Python is not pre-installed, add a lightweight `actions/setup-python@v5` step without pip cache.

## Boundaries

**Always:**
- Preserve exact MkDocs nav structure → Starlight sidebar (same order, same labels).
- Rename `README.md` → `index.md` in aggregated packs and guides (URL preservation).
- Inject minimal Starlight frontmatter (`title:` extracted from first H1, H1 stripped from body) in aggregated files that lack it.
- Strip `.md` suffixes from intra-site links during aggregation.

**Ask-first:**
- Any change to `web/src/styles/tokens.css` or `web/src/components/marketing/`.
- Adding a third-party CDN dependency beyond mermaid (those are concurrent PR territory).

**Never do:**
- Add a CSS framework (Tailwind, Bootstrap, UnoCSS) — design tokens are the sole colour/spacing authority.
- Fork `tokens.css` — it is the canonical source in `web/src/styles/`.
- Touch `docs/guides/**` source markdown — only the aggregation layer (build-site.py) is in scope.

## Testing strategy

**Goal-based check** for all ACs (build command + grep/find assertions):
- AC1–2, AC10–13: `npm run build --prefix docs-site` succeeds; HTML spot-checks pass.
- AC3: `test -f build/docs/pagefind/pagefind.js`
- AC4: `grep -l "sl-theme-dark\|data-theme" build/docs/index.html`
- AC5: `grep -r "sl-color-accent" build/docs/_astro/ --include="*.css" | wc -l` ≥ 1
- AC6: `grep -c "mermaid-diagram" build/docs/packs/core/index.html`
- AC7: `grep -c "starlight-tabs" build/docs/getting-started/index.html`
- AC8: `grep -c "Platform\|GitHub\|PyPI" build/docs/index.html` (expect ≥ 3)
- AC9: `grep "← Platform\|&larr;" build/docs/index.html`
- AC12: `find build/docs -name "*.html" | wc -l` ≥ 185
