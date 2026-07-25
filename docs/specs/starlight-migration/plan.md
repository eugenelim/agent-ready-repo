# Plan: Starlight Migration

Spec: `docs/specs/starlight-migration/spec.md`

Verification mode for all tasks: **goal-based check** (build command + file-existence assertions).

Declined:
- Tempted to use Option A (Starlight integrated into `web/`): declining — Starlight 0.41 has no `routePrefix`; the injected `[...slug]` catch-all route conflicts with marketing pages.
- Tempted to add a full Python admonition/tab converter: declining — 0 admonitions in content, only 8 tab instances in 2 static files (manual rewrite is faster).
- Tempted to self-host mermaid.js as a fontsource-style local package: declining — mermaid ships a large bundle; CDN is standard for docs sites and the trade-off is already noted in spec Boundaries.
- Tempted to extract a shared Vite plugin for tokens.css: declining — a simple file copy in build-site.py is sufficient for one consumer.

---

## T1: Create `docs-site/` Astro + Starlight scaffold

Depends on: none

Files touched: `docs-site/package.json`, `docs-site/astro.config.ts`, `docs-site/.gitignore`, `docs-site/tsconfig.json`, `docs-site/src/content.config.ts`

Approach:
- Create `docs-site/package.json`:
  - `scripts.build = "astro build"`, `scripts.dev = "astro dev"`, `scripts.preview = "astro preview"`
  - Dependencies: `astro: "7.1.0"`, `@astrojs/starlight: "0.41.4"` (Starlight bundles MDX internally via `@astrojs/mdx`; no separate MDX dep needed)
  - `engines: { node: ">=24.0.0" }`
- Write `docs-site/astro.config.ts`:
  - `site: 'https://eugenelim.github.io/agent-ready-repo'` (matches web/ convention)
  - `base: '/agent-ready-repo/docs'`
  - `outDir: '../build/docs'`
  - `trailingSlash: 'always'`
  - Starlight integration: `title: 'agent-ready-repo'`, `customCss`, full `sidebar` ported from `site/mkdocs.yml` nav (all sections and items), `components: { Footer: './src/components/Footer.astro' }`, `banner`, mermaid remark plugin in `markdown.remarkPlugins`.
- Write `docs-site/src/content.config.ts`:
  ```ts
  import { defineCollection } from 'astro:content';
  import { docsLoader } from '@astrojs/starlight/loaders';
  import { docsSchema } from '@astrojs/starlight/schema';
  export const collections = { docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }) };
  ```
- Write `docs-site/.gitignore`:
  ```
  node_modules/
  dist/
  src/content/docs/packs/
  src/content/docs/guides/
  src/content/docs/changelog.md
  src/content/docs/contributing.md
  src/styles/tokens.css
  ```
- Run `npm install --prefix docs-site`.

Done when: `npm install --prefix docs-site` completes; `docs-site/node_modules/@astrojs/starlight` exists.

---

## T2: Migrate static docs content (index, getting-started)

Depends on: T1

Files created: `docs-site/src/content/docs/index.mdx`, `docs-site/src/content/docs/getting-started/index.mdx`, `docs-site/src/content/docs/getting-started/install.md`, `docs-site/src/content/docs/getting-started/three-loops.md`

Approach:

**`index.mdx`** — rewrite from `site/docs/index.md`:
- Frontmatter: `title: "Reference documentation"`, `description: "Pack reference, getting-started guides, and the full skill catalogue."`, plus Starlight hero config (`hero.actions` with Getting started + Browse packs buttons).
- Port the Quick Install section: replace `=== "Tab"` with Starlight `<Tabs>` component. Import `{ Tabs, TabItem } from '@astrojs/starlight/components'`.
- Port the Packs section table as plain markdown.
- Drop all MkDocs-specific HTML classes (`.hero-section`, `.md-button--primary`, `.hero-actions`, etc.) — Starlight's hero handles the visual layout.

**`getting-started/index.mdx`** — rewrite from `site/docs/getting-started/index.md`:
- Frontmatter: `title: "Get Started"`.
- Replace `=== "Tab"` with `<Tabs><TabItem label="…">` — 4 tab entries.
- Adjust relative links: `install.md` → `../getting-started/install/` style links are fine since Starlight resolves them.

**`getting-started/install.md`** — copy from `site/docs/getting-started/install.md` with frontmatter prepended (`title: "Install"`) — Starlight's `docsSchema` requires `title`; it does NOT infer it from H1.

**`getting-started/three-loops.md`** — copy from `site/docs/getting-started/three-loops.md` with frontmatter prepended (`title: "The Three Loops"`).

Done when: `ls docs-site/src/content/docs/getting-started/` shows 3 files; files are valid MDX/MD.

---

## T3: Apply amber brand theme via Starlight CSS

Depends on: T1

Files created/touched: `docs-site/src/styles/starlight.css`, `docs-site/astro.config.ts` (customCss field)

Approach:
- `tools/build-site.py` is updated (T6) to copy `web/src/styles/tokens.css` → `docs-site/src/styles/tokens.css` (gitignored).
- `docs-site/src/styles/starlight.css`:
  1. `@import './tokens.css';` (same directory, resolves cleanly within Vite).
  2. Map Starlight CSS variables to `--ds-*` tokens in `:root` and `.sl-theme-dark` blocks:
     - `--sl-color-accent: var(--ds-accent);` (amber-400 = `#e8952b`)
     - `--sl-color-accent-low: var(--prim-amber-10);`
     - `--sl-color-accent-high: var(--ds-accent-deep);` (amber-700 = `#8b5e0a`)
     - `--sl-color-bg-nav: var(--prim-dark-950);` (dark header)
     - `--sl-color-white: #ffffff;`
     - `--sl-font: 'Inter Variable', sans-serif;`
     - `--sl-font-mono: 'JetBrains Mono', monospace;`
  3. Add Inter + JetBrains Mono `@font-face` imports pointing at `web/src/` (or declare in `<head>` via fontsource).
- `customCss: ['./src/styles/starlight.css']` in Starlight config.

Done when: `starlight.css` file exists; `@import './tokens.css'` is present.

---

## T4: Add footer and banner

Depends on: T1

Files created: `docs-site/src/components/Footer.astro`; touched: `docs-site/astro.config.ts`

Approach:

**`Footer.astro`**: An Astro component that outputs:
```html
<footer class="sl-footer">
  <div class="sl-footer-inner">
    <p class="sl-footer-brand">agent-ready-repo</p>
    <nav aria-label="Site footer">
      <a href="https://eugenelim.github.io/agent-ready-repo/" rel="noopener">Platform</a>
      <a href="https://github.com/eugenelim/agent-ready-repo" rel="noopener">GitHub</a>
      <a href="https://pypi.org/project/agentbundle/" rel="noopener">PyPI</a>
    </nav>
    <p class="sl-footer-copy">© 2026 · The supervised AI operating model for software teams.</p>
  </div>
</footer>
```
Wire via `components: { Footer: './src/components/Footer.astro' }` in Starlight config.

**Banner** (back-link to platform):
```ts
banner: {
  content: '<a href="https://eugenelim.github.io/agent-ready-repo/">← Platform</a>',
}
```

Done when: `grep "Platform\|GitHub\|PyPI" docs-site/src/components/Footer.astro` returns 3 matches; `astro.config.ts` contains `banner:` and `Footer:`.

---

## T5: Add mermaid support via remark plugin

Depends on: T1

Files created: `docs-site/src/scripts/mermaid-init.ts`; touched: `docs-site/astro.config.ts`

Approach:

**Remark plugin** (inline in `astro.config.ts`, using `unist-util-visit` already bundled with Starlight):
```ts
import { visit } from 'unist-util-visit';

function remarkMermaid() {
  return (tree: any) => {
    visit(tree, 'code', (node: any, index: number, parent: any) => {
      if (node.lang === 'mermaid') {
        parent.children[index] = {
          type: 'html',
          value: `<div class="mermaid-diagram" data-mermaid="${encodeURIComponent(node.value)}"></div>`,
        };
      }
    });
  };
}
```

Add to `markdown: { remarkPlugins: [remarkMermaid] }` in `astro.config.ts`. This transforms mermaid blocks to a plain HTML `<div>` before Expressive Code processes anything — EC never sees `language-mermaid`.

**Client-side init script** — inlined directly in Starlight's `head` config (avoids the URL-delivery problem; Astro does NOT auto-serve `src/scripts/*.ts` at a public URL):
```ts
head: [
  {
    tag: 'script',
    attrs: { type: 'module' },
    content: `
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
      mermaid.initialize({ startOnLoad: false, theme: 'neutral' });
      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.mermaid-diagram[data-mermaid]').forEach(async (el) => {
          const id = 'mermaid-' + Math.random().toString(36).slice(2);
          const { svg } = await mermaid.render(id, decodeURIComponent(el.getAttribute('data-mermaid')));
          el.innerHTML = svg;
        });
      });
    `,
  }
]
```

Done when: `build/docs/packs/core/index.html` contains `class="mermaid-diagram"`.

---

## T6: Update `tools/build-site.py` to target `docs-site/`

Depends on: T1

Files touched: `tools/build-site.py`

Changes:
1. `SITE_DOCS = REPO_ROOT / "docs-site" / "src" / "content" / "docs"` (was `site/docs`).
2. **Redirect** (not add) the tokens.css copy: change the existing copy target from `SITE_DOCS/stylesheets/tokens.css` to `REPO_ROOT / "docs-site" / "src" / "styles" / "tokens.css"`. Remove the old `stylesheets/` path from `generated` list.
3. **Remove `write_siteignore()`** call and its `generated` list. This is a MkDocs-only mechanism; Starlight ignores `.siteignore`.
4. **Add `title` frontmatter to `PACK_INDEX_HEADER`**: prepend `---\ntitle: "Pack Catalogue"\n---\n\n` to the generated `packs/index.md` content (in `build_pack_index()`).
5. **Rename `README.md` → `index.md`** for all aggregated files:
   - In `copy_file()` call for pack READMEs: destination `packs_out / f"{slug}.md"` is already a rename (stays as-is, already not `README.md`).
   - In `mirror_dir()` (guides): rename `README.md` → `index.md` when copying.
4. **Inject frontmatter** for all aggregated files that lack a YAML front-matter block. In the copy/mirror helpers, if the output file doesn't start with `---`, prepend a minimal frontmatter block:
   ```python
   def _inject_frontmatter(text: str, path: Path) -> str:
       if text.startswith('---'):
           return text  # already has frontmatter
       # Extract first H1 as title
       import re
       m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
       title = m.group(1).strip().replace('"', '\\"') if m else path.stem.replace('-', ' ').title()
       return f'---\ntitle: "{title}"\n---\n\n' + text
   ```
5. **Strip `.md` suffixes from intra-site links** in aggregated guides and packs. Add a rewriter pass:
   ```python
   def _strip_md_suffix(text: str) -> str:
       # Rewrite markdown links: [label](path.md) → [label](path/) and [label](path.md#anchor) → [label](path/#anchor)
       # Do not rewrite http(s):// links
       import re
       return re.sub(r'\((?!https?://)([^)]+?)\.md(#[^)]*)?\)', lambda m: f'({m.group(1)}/{m.group(2) or ""})', text)
   ```

Done when: `python tools/build-site.py --dry-run` shows all copy targets under `docs-site/src/content/docs/`; dry-run output includes `tokens.css` copy.

---

## T7: Update `.github/workflows/pages.yml`

Depends on: T1

Files touched: `.github/workflows/pages.yml`, `web/CLAUDE.md`

Changes to `pages.yml`:
- **Load-bearing ordering**: `web/` Astro build runs first (it writes `build/` and cleans it); `docs-site/` Astro build runs after it writes `build/docs/`. This invariant is unchanged from the current MkDocs ordering. Explicitly update the load-bearing comment to say "web build first — it cleans build/; docs-site build second — writes build/docs/".
- Remove the Python setup block (`actions/setup-python@v5`, `pip install`, `mkdocs build`).
- Add a second `actions/setup-node@v4` step (or extend the existing one) for `docs-site/`:
  ```yaml
  - uses: actions/setup-node@v4
    with:
      node-version: "24"
      cache: npm
      cache-dependency-path: docs-site/package-lock.json
  - name: Install docs-site dependencies
    run: npm ci --prefix docs-site
  ```
- Replace `Aggregate content` step (keep the `python tools/build-site.py` command — Python is pre-installed on `ubuntu-latest`).
- Replace `Build site` with `Build docs site`: `npm run build --prefix docs-site`.
- Update comments referencing MkDocs to reference Starlight.

Changes to `web/CLAUDE.md`:
- Update § "Broken links in MkDocs docs": replace `mkdocs build --strict` instruction with a note that Starlight does not enforce strict link checking; broken links must be caught manually or via a link-checker tool.
- Remove the reference to `site/AGENTS.md`.
- Update the comment in § "Build" that references the Astro-must-run-before-MkDocs ordering.

Done when: `grep "mkdocs\|pip install\|site/requirements" .github/workflows/pages.yml` returns empty; `grep "npm run build --prefix docs-site" .github/workflows/pages.yml` returns a match.

---

## T8: Remove `site/` MkDocs artifacts

Depends on: T6, T7

Approach: `rm -rf site/`

Done when: `test ! -d site` passes.

---

## T9: Build and verify

Depends on: T2, T3, T4, T5, T6, T7, T8

Approach:
1. `python tools/build-site.py` — aggregates content.
2. `npm run build --prefix web` — marketing site builds clean.
3. `npm run build --prefix docs-site` — docs site builds clean.
4. Run all AC verification commands from spec:
   - `test -f build/docs/pagefind/pagefind.js` (AC3)
   - `grep -l "sl-theme-dark" build/docs/index.html` (AC4)
   - `grep -r "sl-color-accent" build/docs/_astro/ --include="*.css" | wc -l` ≥ 1 (AC5)
   - `grep -c "mermaid-diagram" build/docs/packs/core/index.html` (AC6)
   - `grep -c "starlight-tabs" build/docs/getting-started/index.html` (AC7)
   - `grep -c "Platform" build/docs/index.html` (AC8)
   - Spot-check for `← Platform` or equivalent (AC9)
   - `find build/docs -name "*.html" | wc -l` ≥ 185 (AC12)

Done when: All spot-checks pass.
