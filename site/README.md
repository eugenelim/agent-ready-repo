# Site

MkDocs Material documentation site for agent-ready-repo.

## Prerequisites

```bash
pip install -r site/requirements.txt
```

One-time. The three packages are `mkdocs-material`, `mkdocs-minify-plugin`, and `pymdown-extensions`.

## Local development

```bash
make site-serve
```

Opens a live-reload server at **`http://127.0.0.1:8000/agent-ready-repo/`** (subpath mirrors the GitHub Pages URL). Edits to hand-crafted pages under `site/docs/` rebuild immediately; changes to source files in `packs/` or `docs/guides/` require re-running `make site-sync` to re-aggregate.

## Build the static output

```bash
make site-build        # → site/built/
open site/built/index.html
```

Strict mode — same flags as CI. Any warning is a build failure.

## Workflow

| Command | What it does |
|---|---|
| `make site-sync` | Aggregate repo content into `site/docs/` (copies pack READMEs, mirrors guides, rewrites cross-tree links) |
| `make site-build` | `site-sync` + `mkdocs build --strict` → `site/built/` |
| `make site-serve` | `site-sync` + `mkdocs serve` with live reload |
| `make site-deploy` | `site-sync` + `mkdocs gh-deploy` (manual fallback; CI uses `pages.yml`) |

## What's committed vs generated

**Committed** (hand-crafted, edit these):
- `site/mkdocs.yml` — theme, nav, plugins
- `site/requirements.txt` — Python deps
- `site/docs/index.md` — hero landing page
- `site/docs/getting-started/` — quick start, install routes, three-loops explainer
- `site/docs/stylesheets/extra.css` — custom CSS

**Generated** by `make site-sync` (gitignored, don't edit):
- `site/docs/packs/` — sourced from `packs/*/README.md`
- `site/docs/guides/` — sourced from `docs/guides/`
- `site/docs/changelog.md` — sourced from `docs/product/changelog.md`
- `site/docs/contributing.md` — sourced from `CONTRIBUTING.md`
- `site/built/` — MkDocs output

## Deployment

Push to `main`. The `.github/workflows/pages.yml` workflow runs `build-site.py` then `mkdocs build --strict` and deploys via `actions/deploy-pages`.

Enable in repo settings → Pages → Source → **GitHub Actions**.
