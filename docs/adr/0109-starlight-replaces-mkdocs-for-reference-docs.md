# ADR-0109: Starlight replaces MkDocs for reference docs — Astro+Node.js only pipeline

- **Status:** Accepted
- **Date:** 2026-07-25
- **Areas:** documentation, experience
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0050
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** ADR-0085
- **Related:** RFC-0061
- **Renumbered:** issued as ADR-0055 and moved to ADR-0109 on 2026-09-12. Two records had been accepted under 0055 independently; the one that reached the default branch first keeps the ordinal. Only this record's identifier changed — its decision text is unaltered.

## Decision summary

- **Decision:** The reference documentation site is built with **Astro + Starlight** in a new top-level `docs-site/` directory, replacing MkDocs Material. Both the marketing site (`web/`) and the docs site (`docs-site/`) now use the same Node.js / Astro toolchain. The Python MkDocs toolchain (`site/`) is removed entirely.
- **Because:** Starlight 0.41 is purpose-built for reference docs on top of Astro — the same framework already used by the marketing site — and allows sharing the design token system (`tokens.css`). Removing the Python stack eliminates a second runtime and simplifies CI (one `npm ci` per project, no pip install or virtual-env management).
- **Applies to:** this repo's own web surface only — same scope as ADR-0050.
- **Tradeoff accepted:** a second Node.js project (`docs-site/`) enters the repo, adding a second `package-lock.json` and dependency-update surface. The `docs-site/` top-level directory requires a follow-up RFC mirroring RFC-0061 (tracked: `backlog:starlight-migration-rfc`).
- **Revisit if:** Starlight and Astro diverge on peer-dependency requirements, requiring separate Node.js versions for each project.

## Context

ADR-0050 adopted Astro for the marketing site and retained MkDocs for `/docs/`. That decision explicitly called out "a second language toolchain (Node.js alongside Python) enters CI" as the accepted tradeoff.

Starlight 0.41 — compatible with Astro 7.x already in use — removes the tradeoff: both surfaces are now one toolchain. The MkDocs Python stack (`site/requirements.txt`, `site/mkdocs.yml`, `site/overrides/`) is deleted.

## Decision

- **D1:** The reference documentation site is built with Astro + Starlight in a new top-level `docs-site/` directory, replacing MkDocs Material.
- **D2:** The Python MkDocs toolchain (`site/`) is removed entirely, so the pipeline requires Node.js only.
- **D3:** Both the marketing site (`web/`) and the docs site (`docs-site/`) run on the same Node.js / Astro toolchain, one `npm ci` per project.
- **D4:** `docs-site/` writes its output into `build/docs/`, and `web/` builds first because its build cleans `build/` on every run.
- **D5:** The docs site is a separate Astro instance with `base` scoping rather than a Starlight integration inside `web/`.

## Build ordering

Build order remains load-bearing: `web/` build runs first (it cleans `build/` on every run), then `docs-site/` writes into `build/docs/`. See `.github/workflows/pages.yml`.

## Consequences

**Revisit if:** Starlight and Astro diverge on peer-dependency requirements, forcing separate Node.js versions for the two projects (D3), or the `docs-site/` top-level directory does not get the follow-up RFC mirroring RFC-0061 that it depends on (`backlog:starlight-migration-rfc`, D1).

## Option considered and rejected

**Integrate Starlight into `web/` (Option A):** Starlight 0.41 injects a catch-all `[...slug]` route that conflicts with the marketing site's existing pages. Separate Astro instances with `base` scoping is the documented pattern and keeps each site's ownership clean.
