# ADR-0050: Astro for the marketing site, co-deployed with MkDocs in one GitHub Pages origin

- **Status:** Accepted
- **Date:** 2026-07-16
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0061](../rfc/0061-web-top-level-directory.md), [`docs/specs/platform-site/`](../specs/platform-site/spec.md), [`web/AGENTS.md`](../../web/AGENTS.md)

## Decision summary

- **Decision:** The platform marketing site is built with **Astro** (a static-site generator) in a new top-level `web/` directory, and co-deployed with the existing MkDocs reference docs into **one** GitHub Pages origin — Astro at `/`, MkDocs at `/docs/` — via a single `build/` artifact.
- **Because:** the accepted marketing design (dark full-bleed hero, alternating bands, display type, CSS-only interactive components) cannot be expressed within MkDocs Material's theme, and one origin keeps cross-links same-origin and content ownership unified.
- **Applies to:** this repo's own web surface only — **not** a primitive, template, or framework prescribed to adopters.
- **Tradeoff accepted:** a second language toolchain (Node.js alongside Python) enters CI, with its own dependency-update surface.
- **Revisit if:** a second JS package appears (reconsider a root workspace), or the production deploy moves off the `/agent-ready-repo/` project sub-path (revisit Astro `base`).

## Context

The [platform-site spec](../specs/platform-site/spec.md) establishes a marketing homepage as the catalogue's anchor at `/`, with the MkDocs reference docs becoming a `/docs/` subsection. The design system (Option B — Alternating Conviction) requires surface control MkDocs Material does not offer.

[RFC-0061](../rfc/0061-web-top-level-directory.md) (Accepted 2026-07-16) approved `web/` as a new top-level directory and the Node.js build dependency it carries. Per `docs/CONVENTIONS.md` § 3, an accepted RFC's architectural decisions are recorded in an ADR; per AGENTS.md § "Check before acting", a new dependency is recorded before it is added. This ADR is that record; the in-package dependency detail lives in [`web/AGENTS.md`](../../web/AGENTS.md).

## Decision

**Astro builds the marketing site into `build/` first; MkDocs then writes the reference docs into `build/docs/`; a single GitHub Pages deploy serves the combined artifact.**

Concretely:

- The Astro project lives in top-level `web/`, built as a **single npm package** (`npm --prefix web`) — not a root monorepo workspace, because only one JS package exists.
- `web/astro.config.ts` sets `outDir: '../build'`; `site/mkdocs.yml` sets `site_dir: ../build/docs`.
- **Build order is load-bearing:** `astro build` cleans its `outDir` (`build/`) on every run, so Astro MUST build before MkDocs writes into `build/docs/` — otherwise MkDocs output is silently wiped. `.github/workflows/pages.yml` sequences Node/Astro steps before the Python/MkDocs steps and uploads `./build`.
- The design-system `--ds-*` token block is the sole colour/spacing authority on the Astro surface; **no CSS framework** (Tailwind, Bootstrap, UnoCSS) is used.
- For Phase 1 the Astro `base` is left at `/` (root-served); the production sub-path (`/agent-ready-repo/`) is still to be confirmed (information-architecture.md) and is the trigger to set `base`.

## Decision drivers

- **Design fidelity.** The marketing anchor's design is unachievable within MkDocs Material's theme.
- **One origin.** The spec's Boundaries forbid separate deployments; same-origin keeps `/` ↔ `/docs/` cross-links and content ownership simple.
- **Minimal footprint.** One isolated JS package, no root workspace, no second Pages deploy, no SSR (GitHub Pages is static-only).
- **Charter neutrality.** The charter's "not a framework that picks your tech stack" governs what we prescribe to adopters, not our own build infrastructure (which already picks Python/MkDocs for `site/`).

## Consequences

**Positive:**
- The marketing surface gets full template/design freedom without fighting a docs theme.
- Astro at `/` and MkDocs at `/docs/` ship from one artifact and one deploy — no cross-origin seams.
- The JS toolchain is isolated in `web/`; the Python packages and MkDocs build are untouched beyond the `site_dir` retarget.

**Negative:**
- A second language toolchain in CI (Node alongside Python) — more moving parts, a second dependency-update surface, longer CI.
- The Astro-first build order is a sequencing constraint that, if inverted, wipes MkDocs output (loud failure, caught on first CI run).

**Revisit if:** a second JS package appears (a root workspace may then earn its cost), or the production deploy moves off the project sub-path (set Astro `base` accordingly).

## Confirmation

- **Mode:** reviewer-checked + CI-gated
- **Signal:** `astro build` exits 0 and emits `build/index.html`; the full pipeline produces both `build/index.html` (Astro) and `build/docs/index.html` (MkDocs), proving the Astro-first order preserves MkDocs output; the GitHub Actions run is green. A reviewer confirms the workflow orders Node/Astro before Python/MkDocs and uploads `./build`.
- **Owner:** eugenelim

## Alternatives considered

- **Express the marketing site within MkDocs only.** Rejected: cannot achieve the accepted design within the theme; the anchor page the spec is built around never ships.
- **Nest the Astro project under `site/` or `packages/`.** Rejected: `site/` means "the MkDocs docs site"; `packages/` is publishable Python sub-projects. Either conflates toolchains and erodes what the directory means. (See RFC-0061 options A–E.)
- **Separate repo / separate GitHub Pages deploy.** Rejected: two deploys, split content ownership, cross-origin cross-links; the spec's Boundaries forbid it.
- **Root npm workspace (monorepo).** Rejected for now: npm workspaces manage *multiple* packages; with one JS package the single-package pattern is simpler.

## References

- RFC-0061 (the accepted proposal — options matrix, charter-neutrality de-risk, and the single-package vs. workspace analysis).
- [platform-site spec](../specs/platform-site/spec.md) and its design docs (aesthetic-direction, design-system-foundations, information-architecture, homepage-screen-flow).
- [Astro configuration reference — `outDir`](https://docs.astro.build/en/reference/configuration-reference/#outdir).
- [npm workspaces documentation](https://docs.npmjs.com/cli/v10/using-npm/workspaces).
