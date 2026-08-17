# ADR-0055: Starlight replaces MkDocs for reference docs — Astro+Node.js only pipeline

- **Status:** Accepted — **partially amended:** the **shared palette and design-token sub-decision** (docs-site consuming `web/`'s design tokens) is **superseded by [ADR-0085](0085-docs-rendering-is-site-local.md)** (docs rendering is site-local; the docs palette is self-contained, 2026-08-17); every other decision in this ADR — Starlight replacing MkDocs, the Astro+Node.js-only pipeline, the docs mount point, and the build order — stands.
- **Date:** 2026-07-25
- **Decision-makers:** eugenelim
- **Supersedes:** [ADR-0050](0050-astro-marketing-site-toolchain-and-deploy.md)
- **Related:** [RFC-0061](../rfc/0061-web-top-level-directory.md), [`docs/specs/starlight-migration/`](../specs/starlight-migration/spec.md)

## Decision summary

- **Decision:** The reference documentation site is built with **Astro + Starlight** in a new top-level `docs-site/` directory, replacing MkDocs Material. Both the marketing site (`web/`) and the docs site (`docs-site/`) now use the same Node.js / Astro toolchain. The Python MkDocs toolchain (`site/`) is removed entirely.
- **Because:** Starlight 0.41 is purpose-built for reference docs on top of Astro — the same framework already used by the marketing site — and allows sharing the design token system (`tokens.css`). Removing the Python stack eliminates a second runtime and simplifies CI (one `npm ci` per project, no pip install or virtual-env management).
- **Applies to:** this repo's own web surface only — same scope as ADR-0050.
- **Tradeoff accepted:** a second Node.js project (`docs-site/`) enters the repo, adding a second `package-lock.json` and dependency-update surface. The `docs-site/` top-level directory requires a follow-up RFC mirroring RFC-0061 (tracked: `backlog:starlight-migration-rfc`).
- **Revisit if:** Starlight and Astro diverge on peer-dependency requirements, requiring separate Node.js versions for each project.

## Context

ADR-0050 adopted Astro for the marketing site and retained MkDocs for `/docs/`. That decision explicitly called out "a second language toolchain (Node.js alongside Python) enters CI" as the accepted tradeoff.

Starlight 0.41 — compatible with Astro 7.x already in use — removes the tradeoff: both surfaces are now one toolchain. The MkDocs Python stack (`site/requirements.txt`, `site/mkdocs.yml`, `site/overrides/`) is deleted.

## Build ordering

Build order remains load-bearing: `web/` build runs first (it cleans `build/` on every run), then `docs-site/` writes into `build/docs/`. See `.github/workflows/pages.yml`.

## Option considered and rejected

**Integrate Starlight into `web/` (Option A):** Starlight 0.41 injects a catch-all `[...slug]` route that conflicts with the marketing site's existing pages. Separate Astro instances with `base` scoping is the documented pattern and keeps each site's ownership clean.
