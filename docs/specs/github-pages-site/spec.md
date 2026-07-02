# Spec: GitHub Pages Publishing Toolchain

**Mode: full** (new dependency: mkdocs-material; structural: new top-level dir + GH Actions workflow; public interface: published site)

- **Status:** Shipped

## Objective

Ship a professional MkDocs Material documentation site under `site/` that aggregates content from the repo's existing guides, packs, and product docs. Provide a `make site-sync/build/serve/deploy` toolchain so the site can be rebuilt from a single command and deployed automatically via GitHub Actions on every push to `main`.

## Acceptance Criteria

- [x] `site/mkdocs.yml` configures MkDocs Material with dark/light toggle, search, code copy, navigation tabs
- [x] `site/requirements.txt` pins mkdocs-material and plugins
- [x] `site/docs/index.md` is a rich hero landing page (three loops, pack catalogue, install command)
- [x] `site/docs/getting-started/index.md` walks through quick start → first loop
- [x] `site/docs/stylesheets/extra.css` adds custom polish on top of Material
- [x] `tools/build-site.py` copies packs/*/README.md → site/docs/packs/<name>.md, docs/guides/** → site/docs/guides/**, changelog + contributing
- [x] `tools/build-site.py` generates a `site/docs/packs/index.md` pack catalogue summary
- [x] `make site-sync` runs the aggregation script
- [x] `make site-build` runs site-sync then `mkdocs build`
- [x] `make site-serve` runs site-sync then `mkdocs serve` for local dev
- [x] `.github/workflows/pages.yml` builds and deploys to GitHub Pages on push to main
- [x] `site/built/` and generated docs subdirs are gitignored
- [x] Site builds clean (`mkdocs build --strict` passes)

## Boundaries

**Touching:** `site/` (new), `tools/build-site.py` (new), `.github/workflows/pages.yml` (new), `Makefile` (additive), `.gitignore` (additive), `docs/specs/github-pages-site/` (this spec)

**Not touching:** existing `docs/` (read-only source), existing `packs/` (read-only source), existing Makefile targets, any pack source files

## Testing Strategy

Verification mode: goal-based check + visual/manual QA

- `python tools/build-site.py` exits 0 and populates `site/docs/packs/`, `site/docs/guides/`
- `mkdocs build --config-file site/mkdocs.yml` exits 0 (strict mode)
- `mkdocs serve` starts and the landing page renders correctly

## Assumptions (verified)

- Python 3 is available (`python3` in PATH) — confirmed from repo's existing Makefile convention
- GitHub repo is `eugenelim/agent-ready-repo` — confirmed from pack README link
- `packs/` contains exactly 14 packs — confirmed from exploration
- All 14 packs have `README.md` — to be confirmed by build-site.py at runtime (skip missing, warn)
- `docs/guides/` is the full user-facing guide tree — confirmed (107 .md files mirrored by build-site.py)

## Declined patterns

- Astro/Starlight — adds Node.js build dependency to a Python repo; MkDocs fits the stack
- Jekyll — GH-native but limited; Material's feature set is substantially better
- Copying ALL of docs/ — most is internal governance (ADRs, RFCs, specs); only guides + product docs are user-facing
- Custom theme from scratch — Material is already the best; custom overrides only
- Committing generated content — CI regenerates on every push; no double-maintenance
- mkdocs-gen-files plugin — unnecessary complexity when a simple Python script suffices

## Resolve-vs-surface disposition

| Item | Disposition |
|---|---|
| GitHub Pages URL for site_url | Resolved: `https://eugenelim.github.io/agent-ready-repo/` (from pack README link) |
| Whether to use `--strict` | Resolved: yes in CI, not in serve (strict blocks warnings in dev) |
| Nav: auto vs explicit | Resolved: explicit nav for key pages, auto for guide sub-pages |
| Generated content: committed vs gitignored | Resolved: gitignored; CI runs sync then build |
