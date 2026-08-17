# Plan: Site shared chrome

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Capture the approved destination taxonomy in `site.toml`, validate it in the
existing stdlib generation path, and project renderer-local data for Astro and
Starlight. Adapt each renderer's existing chrome without sharing runtime code,
then prove emitted labels, links, routes, accessibility, and responsive
behavior across the combined build.

## Constraints

- `docs/design/principles/tech-site.md` arbitrates cross-surface decisions.
- RFC-0089 must be Accepted before implementation; it owns renderer autonomy
  and the ordered single-artifact boundary.
- `docs/specs/platform-site/aesthetic-direction.md` owns marketing appearance;
  `docs/specs/docs-site-design-refresh/creative-direction.md` owns docs
  appearance.
- `docs-site/AGENTS.md` governs the docs palette and pinned Starlight contracts.
- No dependency, route, palette unification, or shared renderer component.

## Construction tests

**Integration tests:** build marketing first and docs second, inspect both
renderers' emitted chrome from one canonical fixture, and run the combined
page-and-fragment checker against the complete route inventory.

**Manual verification:** recorded design review in marketing and both docs
themes at compact and wide widths; physical-device chrome review remains the
programme's manual release check.

## Design (LLD)

### Design decisions

- `site.toml` stores renderer-neutral destination data; generator-owned
  projection is chosen over importing one renderer into the other. Traces to:
  AC1, AC2, AC7.
- Renderer-local components keep independent visual systems. Shared CSS or a
  cross-workspace component package is rejected. Traces to: AC5-AC7, AC10.

### Component / module decomposition

- `tools/build-site.py` validates and projects the destination contract.
- Marketing `SiteNav` and `SiteFooter` consume the marketing projection.
- A docs-specific orientation-band override and existing docs footer consume
  the docs projection while Starlight retains native controls. Traces to:
  AC1-AC7.

### State & control flow

- Static destination data flows from `site.toml` through generation into both
  builds. Mobile disclosure, Starlight search/theme, and pagination keep their
  existing state owners. Traces to: AC3, AC5, AC8, AC9.

### Behavior & rules

- Target kind, not hostname comparison in a component, determines
  internal/external treatment. Internal targets keep base-path qualification;
  external targets keep the repository's current safe relationship handling.
  Traces to: AC2, AC4, AC6.

### Quality attributes (NFRs)

- Emitted browser checks enforce keyboard, overflow, and axe thresholds on the
  approved route/theme matrix. Traces to: AC9.

## Tasks

### T1: Invalid shared destination contracts fail before projection

**Depends on:** none

**Touches:** site.toml, tools/build-site.py, tools/test_build_site_routing.py

**Tests:**
- TDD: add failing fixtures for duplicate IDs, missing group members, unsupported
  target kinds, and unknown internal destinations (AC1, AC2).
- TDD: add one canonical fixture and assert stable group/destination ordering in both
  renderer projections (AC1, AC6).

**Approach:**
- Add the smallest renderer-neutral tables needed for destinations and groups.
- Validate through the existing Python generation boundary without a new
  package.

**Done when:** malformed fixtures fail with actionable messages and the valid
fixture yields deterministic renderer inputs.

### T2: Marketing chrome consumes the shared contract without behavior drift

**Depends on:** T1

**Touches:** web/src/components/layout/SiteNav.astro, web/src/components/layout/SiteFooter.astro, web/src/**/*.generated.*

**Tests:**
- Goal-based: assert current primary-nav order, CTA, footer taxonomy, hrefs, and base-path
  qualification in emitted marketing HTML (AC3, AC4, AC6, AC8).
- TDD: seed a stale literal in a fixture and prove projection consistency fails
  (AC1).

**Approach:**
- Replace duplicated destination literals with generated renderer-local data.
- Remove external-only treatment from the internal Docs link.

**Done when:** emitted marketing chrome matches the approved contract and every
existing destination resolves.

### T3: Docs gains renderer-native orientation and the shared footer taxonomy

**Depends on:** T1

**Touches:** docs-site/astro.config.mjs, docs-site/src/components/*.astro, docs-site/src/**/*.generated.*

**Tests:**
- Goal-based: assert the orientation band and footer consume the canonical labels, order,
  targets, and target kinds (AC4-AC6).
- Goal-based: assert title, search, theme, sidebar, and pagination controls remain present
  and singular on home and nested guide pages (AC5, AC8).

**Approach:**
- Add a thin docs-specific override at the supported Starlight component seam.
- Extend the existing docs footer without importing marketing components or
  tokens.

**Done when:** docs exposes product orientation and the shared taxonomy while
all pinned Starlight controls remain intact.

### T4: Combined emitted chrome passes route, browser, and design evidence

**Depends on:** T2, T3, spec:site-browser-quality-gate/T2

**Touches:** web/src/test/e2e/**/*.ts, tools/test_check_rendered_site_links.py

**Tests:**
- Goal-based: build both sites and run complete page/fragment and route checks (AC8).
- Goal-based E2E: exercise the approved route/theme/viewport matrix for keyboard use, overflow,
  and axe thresholds (AC9).
- Visual/manual QA: record renderer-specific design review against the named directions and
  principles (AC10).

**Approach:**
- Verify emitted behavior; do not use source-shape or screenshot-existence
  assertions as proof.
- Keep optional screenshots outside required CI and tracked output.

**Done when:** combined link, route, browser, and recorded design-review gates
all pass.

## Rollout

Land contract/projection support before renderer consumption, then ship both
renderer adaptations in the same completion wave so vocabulary cannot drift.
Rollback is a normal source revert; no infrastructure or dependency change.

## Risks

- Over-generalizing the contract could create a new navigation framework; the
  tables stay limited to the two current consumers and approved taxonomy.
- A docs override can accidentally replace framework behavior; explicit
  presence-and-singularity tests protect the pinned controls.

## Changelog

- 2026-08-17: initial plan after approval of the shared-IA, separate-renderer
  contract.
