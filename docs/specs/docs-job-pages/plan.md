# Plan: docs-job-pages

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `guides/AGENTS.md` § Job pages; exemplars
  `guides/_shared/how-to/{install-agentbundle,install-packs,configure-agentbundle,upgrade-packs}.md`,
  `guides/product-strategy/how-to/run-a-market-and-competitive-analysis.md`,
  `docs-site/src/packs-page.md`.

## Approach

Rewrite by group in parallel worktrees, each group owning disjoint files. The
controller owns `docs-site/astro.config.ts`, `site.toml`, cross-group links, the
Operating model, and the guidebook machinery, and integrates the groups.

## Tasks

### T1: Set up and Decide pages meet the standard
**Depends on:** none
**Tests:** AC1, AC2, AC3, AC6 over these pages. **Done when:** gates in the spec pass on the group's branch.

### T2: Shape pages meet the standard
**Depends on:** none
**Tests:** as T1. **Done when:** as T1.

### T3: Build and Ship pages meet the standard
**Depends on:** none
**Tests:** as T1. **Done when:** as T1.

### T4: Author and Catalogue System pages meet the standard
**Depends on:** none
**Tests:** AC1, AC6. **Done when:** as T1.

### T5: Pack pages follow the template
**Depends on:** none
**Tests:** AC4. **Done when:** as T1, and the core-release roster test passes.

### T6: Integration — navigation, Operating model, guidebook retirement, links
**Depends on:** T1-T5
**Tests:** all ACs. **Done when:** every spec gate passes.

## Changelog

- 2026-10-15: spec approved by eugenelim (delegated in session: "audit every other page and rewrite")
- 2026-10-15: plan approved by eugenelim (same delegation)
