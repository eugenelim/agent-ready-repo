# Plan: GitHub Pages Publishing Toolchain

## Tasks

### T1 — Scaffold site directory structure
**Depends on:** none  
**Verification:** goal-based check (`ls site/mkdocs.yml site/requirements.txt site/docs/index.md`)  
**Done when:** site/ exists with mkdocs.yml, requirements.txt, docs/index.md, docs/getting-started/, docs/stylesheets/

### T2 — Write MkDocs Material config
**Depends on:** T1  
**Verification:** goal-based (`mkdocs build --config-file site/mkdocs.yml --strict` exits 0 after T6)  
**Done when:** site/mkdocs.yml has theme config, full nav, markdown extensions, plugins

### T3 — Write hand-crafted site pages
**Depends on:** T1  
**Verification:** visual/manual QA (mkdocs serve, inspect landing page)  
**Done when:** index.md hero page, getting-started/{index,install,three-loops}.md, stylesheets/extra.css all present and render correctly

### T4 — Write tools/build-site.py content aggregation script
**Depends on:** none  
**Verification:** goal-based (`python tools/build-site.py` exits 0; site/docs/packs/ and site/docs/guides/ populated)  
**Done when:** script copies all 14 pack READMEs, mirrors guides/, copies changelog + contributing, generates packs/index.md, rewrites broken links (cross-pack, governance, stale)

### T5 — Add Makefile targets
**Depends on:** T2, T4  
**Verification:** goal-based (`make site-sync` runs build-site.py; `make site-build` runs mkdocs --strict)  
**Done when:** site-sync, site-build (--strict), site-serve, site-deploy targets present

### T6 — Wire GitHub Actions deployment workflow
**Depends on:** T2, T4  
**Verification:** goal-based (workflow YAML validates; permissions correctly scoped)  
**Done when:** .github/workflows/pages.yml builds + deploys on main push, scoped permissions

### T7 — Update .gitignore for generated content
**Depends on:** T4  
**Verification:** goal-based (`git status` after build-site.py shows no unexpected tracked changes)  
**Done when:** site/built/, site/docs/packs/, site/docs/guides/, site/docs/changelog.md, site/docs/contributing.md are gitignored

### T8 — Full strict build passes clean
**Depends on:** T2, T3, T4, T5, T6, T7  
**Verification:** goal-based (`mkdocs build --config-file site/mkdocs.yml --strict` exits 0)  
**Done when:** zero warnings, zero errors in strict build

## Declined patterns

- Social card plugin: requires `cairosvg` system library in CI (libcairo2 apt dep); not worth the CI complexity for a docs site
- Astro/Starlight: Node.js build dependency in a Python repo
- Committing generated content: double-maintenance; CI regenerates on every push
- mkdocs-redirects: no page renames anticipated at this stage
