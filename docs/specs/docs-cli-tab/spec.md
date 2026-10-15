# Spec: docs-cli-tab

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs-site-rail-shell`](../docs-site-rail-shell/spec.md), [`docs/design/direction/docs-site.md`](../../design/direction/docs-site.md)
- **Brief:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. `Agent Rules`,
> `Testing Strategy` and `Acceptance Criteria` are contract; the rest is working
> material.

## Outcome

The docs site's CLI tab holds four task pages — Install agentbundle, Install
packs for your agent, Configure agentbundle, Upgrade packs — and a Reference
group. They replace nine scattered install, configure, and upgrade pages. Every
old URL still reaches the page that absorbed it.

## What Changes

- New pages in `guides/_shared/how-to/`: `install-agentbundle`, `install-packs`,
  `configure-agentbundle`; `upgrade-packs` is rewritten in place.
- Merged and deleted: `explanation/install-routes`, `how-to/configure-adapter`,
  `how-to/preview-install-or-upgrade`, `how-to/install-a-profile`,
  `how-to/install-user-scope-pack-into-codex`, `how-to/install-user-scope-pack-into-kiro`,
  `how-to/install-agentbundle-from-clone`, `how-to/install-the-whole-lifecycle`,
  and `docs-site/src/content/docs/getting-started/install.md`.
- The CLI tab's sidebar lists the four pages, then Reference: Command reference,
  Adapter support, File safety.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User documentation | The change is user documentation | the four pages above | this spec | built pages | pages build and link-check clean |
| Route continuity | URLs move | `aliases:` on each new page; `docs-site/astro.config.ts` redirect for `getting-started/install/` | this spec | redirect stubs in `build/docs` | every old URL resolves |

## Agent Rules

### Always do

- Ground every command, flag, config key, and file name in `packages/agentbundle/`
  or the current reference page.
- Keep every command, flag, path, warning, and limit from the merged pages.

### Ask first

- Deleting a page not listed in What Changes.

### Never do

- Invent a flag or behaviour.
- Edit skill files under `packs/*/.apm/`.

## Testing Strategy

- **Goal-based check** — build both sites; `tools/lint-guide-titles.py`; the
  build-site, guide, and entry-link pytest suites; web vitest; `make site-link-check`.

## Acceptance Criteria

- [ ] **AC1 — Four task pages.** The CLI tab sidebar lists Install agentbundle,
  Install packs for your agent, Configure agentbundle, Upgrade packs, then a
  Reference group with Command reference, Adapter support, and File safety, and
  each page builds.
- [ ] **AC2 — Old URLs resolve.** For each of the nine merged pages, the built
  site serves a page at its old URL that redirects to the page that absorbed it.
- [ ] **AC3 — Nothing lost.** Every `agentbundle` and `claude plugin` command
  that appears in the nine merged pages appears in one of the four pages or the
  Command reference.
- [ ] **AC4 — Links clean.** `make site-link-check` reports no broken links.
- [ ] **AC5 — Plain prose.** None of the four pages uses "surface", "canonical",
  "converge", "bounded", "durable", "load-bearing", "genuinely", "first-class",
  "seamless", "robust", or "leverage" outside a code span.
