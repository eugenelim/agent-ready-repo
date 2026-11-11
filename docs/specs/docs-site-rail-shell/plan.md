# Plan: docs-site-rail-shell

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs-site/AGENTS.md` (build order, traps);
  `docs-site/src/components/PageTitle.astro` and `TableOfContents.astro` (the
  existing Starlight override pattern); tests in
  `web/src/test/rendered-output.test.ts` and `web/src/test/e2e/site-quality-gate.spec.ts`.
  Deviation: the shell overrides `Header`, `Sidebar`, and `ThemeSelect`, which
  `site-shared-chrome` AC9 had reserved for Starlight; recorded as a
  superseded-in-part note on that spec.

> **Plan contract:** this is the implementation strategy.

## Approach

Build the shell from the one Starlight sidebar array: its top level is the tab
set, and `rail.ts` reads tabs, the current tab, and the current stage from it.
The header, sidebar, page title, and a route middleware for pagination all call
`rail.ts`, so they cannot disagree. The look is one stylesheet, `rail.css`,
loaded after `starlight.css`, which re-points the existing `--doc-*` and
`--sl-*` tokens rather than rewriting every rule.

Removing the product strip removes the only reason for the `PageFrame`
override (its manual popover existed to keep the Product disclosure and the
Docs menu independent), so the override and the header-clearance tokens that
compensated for the strip are deleted and Starlight's own frame returns.

## Constraints

- No new dependency; Starlight 0.42 supports component overrides and
  `routeMiddleware`.
- No guide URL changes.
- Every text colour ≥ 4.5:1 on ground and subtle surface in both themes.

## Construction tests

Goal-based and visual; no TDD stubs (no compressible invariant beyond what the
built-HTML assertions state).

## Durable-output map

See the spec's Durable Outputs table.

## Design (LLD)

### Design decisions

- **Tabs from the sidebar array, not a second config.** One source; a tab
  cannot exist without its sidebar.
- **Stage by group label.** `STAGES` in `rail.ts` maps the five labels to
  keys. A renamed label loses its colour, which the AC4 test catches.
- **Theme toggle replaces `ThemeSelect` globally**, so the phone menu footer
  (Starlight's `MobileMenuFooter`) gets the same control without a second
  override.
- **Stage chip replaces the breadcrumb** on stage pages; one wayfinding row
  per page.

### Component / module decomposition

| Unit | Role |
| --- | --- |
| `src/components/rail.ts` | Tab, stage, and current-page lookups |
| `src/components/Header.astro` | Top bar |
| `src/components/Sidebar.astro` | Current tab, stage lines, phone tab row |
| `src/components/ThemeToggle.astro` | Light/dark icon button |
| `src/components/PageTitle.astro` | Stage chip or breadcrumb, title, deck |
| `src/routeData.ts` | Tab-scoped pagination |
| `src/styles/rail.css` | Rail line tokens and styling |
| `src/content/docs/index.mdx` | Intro |

### Failure, edge cases & resilience

- A page in no tab (most guides until the merge): renders the Docs tab, no
  current link, no pagination, breadcrumb kept.
- A resting outline width hides the focus ring's gain; header controls zero it
  when not focused.

## Tasks

### T1: The shell renders one top bar, the current tab's sidebar, the stage chip, and tab-scoped pagination

**Depends on:** none
**Touches:** `docs-site/astro.config.ts`, `docs-site/src/components/*`, `docs-site/src/routeData.ts`, `docs-site/src/styles/starlight.css`

**Tests:** rendered-output AC1, AC3, AC4, AC5, AC6; browser gate chrome and keyboard checks.

**Done when:** `npm run build --prefix docs-site` exits 0 and the named tests pass.

### T2: The Rail line look ships and its colours are measured

**Depends on:** T1
**Touches:** `docs-site/src/styles/rail.css`, `tools/check-docs-contrast.py`, `tools/test_check_docs_contrast.py`

**Tests:** `tools/test_check_docs_contrast.py`; `python3 tools/check-docs-contrast.py` lists every Rail pair.

**Done when:** the checker exits 0 and screenshots at 1440 px (both themes) and 390 px are recorded.

### T3: The docs home is the Intro

**Depends on:** T1
**Touches:** `docs-site/src/content/docs/index.mdx`

**Tests:** rendered-output AC7 and the install-to-ship walkthrough AC9.

**Done when:** both pass.

### T4: Every suite that pinned the old shell asserts the new one

**Depends on:** T1, T2, T3
**Touches:** `web/src/test/rendered-output.test.ts`, `web/src/test/e2e/site-quality-gate.spec.ts`, `web/src/test/e2e/guidebook-walk.spec.ts`, `tools/test_build_site_routing.py`

**Tests:** `npx vitest run` (web), `npm run test:e2e:gate --prefix web` plus `docs-asides.spec.ts`, the build-site Python suites.

**Done when:** all pass.

### T5: The records match the shell

**Depends on:** T1
**Touches:** `docs/design/direction/docs-site.md`, `docs/design/journeys/team-orientation-future-state.md`, superseded spec notes, `docs-site/AGENTS.md`

**Tests:** `lint-spec-status.py`; read-through.

**Done when:** the lint passes and every Durable Outputs row is present.

## Rollout

- **Delivery:** big bang on merge; the Pages workflow rebuilds both sites.
  Reversible by revert.

## Risks

- Guides outside the new nav are reachable only by search and links until the
  merge PRs land. Accepted: the merge is the next unit of work.

## Changelog

- 2026-10-15: spec approved by eugenelim (delegated in session: "Go with your recommendation for all open items. Proceed." and "no need to ask, keep going")
- 2026-10-15: plan approved by eugenelim (same delegation)
