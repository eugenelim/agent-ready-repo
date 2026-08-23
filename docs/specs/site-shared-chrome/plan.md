# Plan: Site shared chrome

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Capture the exact approved destination taxonomy in `site.toml`, validate it in
the existing stdlib generation path, and project renderer-local data for Astro
and Starlight. Wait for `/now/`, then adapt both renderers in one wave without
sharing presentation or state. Prove exact emitted content, internal/external
semantics, singular Starlight controls, routes, keyboard/focus behavior, and
responsive quality against the combined build.

## Constraints

- `docs/design/principles/tech-site.md` arbitrates cross-surface decisions.
- RFC-0089 and ADR-0085 own renderer autonomy, ordered build, independent docs
  palette, and pinned Starlight boundaries.
- `docs/specs/platform-site/aesthetic-direction.md` owns marketing appearance;
  `docs/specs/docs-site-design-refresh/creative-direction.md` owns docs
  appearance.
- [`spec.md`](spec.md) contains the exact content and behavior contract;
  implementation does not reopen labels, order, footer treatment, mobile
  disclosure, focus/current semantics, or ownership.
- `/now/` must exist before either renderer links to it.
- No dependency, palette unification, shared renderer code, restored `/work/`,
  or route change beyond the separately approved `/now/` replacement.

## Construction tests

**Integration tests:** build marketing first and docs second, enumerate both
renderers' exact emitted chrome from one canonical fixture, assert singular
Starlight controls, and run combined page/fragment checks against the complete
route inventory.

**Manual verification:** record design review in marketing and both docs themes
at compact and wide widths; physical-device chrome review remains the
programme's manual release check.

## Design (LLD)

### Design decisions

- `site.toml` stores only renderer-neutral destination data. Generator-owned
  projection is chosen over one renderer importing the other. Traces to:
  AC1, AC2, AC10.
- Renderer-local components retain independent visual and state systems.
  Shared CSS/components/tokens and custom replacements for Starlight controls
  are rejected. Traces to: AC4-AC6, AC9, AC10.
- The desktop docs band scrolls away above the sticky Starlight header; compact
  Product disclosure is independent of the Docs menu. Traces to: AC5, AC6.

### Data & schema

- Destination records carry stable ID, label, target, and kind. Group records
  carry stable ID and ordered destination references. Presentation and
  responsive behavior remain renderer-local. Traces to: AC1, AC2.
- Kind, not hostname comparison, owns internal/external behavior. Traces to:
  AC7.

### Component / module decomposition

- `tools/build-site.py` validates and projects the destination contract.
- Marketing `SiteNav` and `SiteFooter` consume the marketing projection.
- A docs-specific supported `PageFrame` override composes the orientation band
  above the default header; the docs footer consumes local projected data after
  native pagination. Traces to: AC3-AC10.

### State & control flow

- Static data flows from `site.toml` into both builds. Marketing mobile state,
  docs Product disclosure, and Starlight Docs/search/theme/sidebar state remain
  separate renderer-local owners. Traces to: AC3, AC5, AC6, AC10.
- Current state derives from the emitted route/category contract. Homepage
  fragments remain non-current without client-side fragment evidence. Traces
  to: AC8.

### Quality attributes (NFRs)

- Emitted browser checks enforce keyboard, focus, overflow, and axe thresholds
  on the approved route/theme matrix. Traces to: AC12.

## Tasks

### T1: Invalid shared destination contracts fail before projection

**Depends on:** none

**Touches:** site.toml, tools/build-site.py, tools/test_build_site_routing.py

**Tests:**
- TDD: fail duplicate IDs, missing group members, unsupported kinds, unknown
  internal targets, and order drift (AC1, AC2).
- TDD: project one exact canonical fixture into deterministic renderer-local
  data and reject presentation/state fields (AC1, AC2, AC10).

**Approach:**
- Add the smallest destination/group tables required by the two current
  consumers.
- Encode the exact header and footer taxonomy and explicit target kind from the
  spec, without presentation data or a new package.

**Done when:** malformed fixtures fail actionably and the exact fixture yields
stable independent projections.

### T2: Marketing chrome consumes the approved contract

**Depends on:** T1, spec:site-now-surface/T2

**Touches:** web/src/components/layout/SiteNav.astro, web/src/components/layout/SiteFooter.astro, web/src/**/*.generated.*

**Tests:**
- Goal-based: assert the exact six-item header/mobile order, labels, targets,
  CTA, three footer groups, brand/tagline, target kinds, base qualification,
  external treatment, and current states in emitted HTML (AC3, AC4, AC7,
  AC8).
- TDD: seed a stale literal and prove projection consistency fails (AC1).

**Approach:**
- Replace duplicated literals with generated marketing-local data.
- Replace Work with Now and remove external treatment from Docs.
- Preserve marketing component, palette, focus implementation, and mobile
  disclosure ownership.

**Done when:** emitted marketing chrome exactly matches the contract, `/work/`
is absent from public chrome, and every destination resolves.

### T3: Docs gains product orientation and its renderer-native footer

**Depends on:** T1, spec:site-now-surface/T2

**Touches:** docs-site/astro.config.mjs, docs-site/src/components/*.astro, docs-site/src/**/*.generated.*

**Tests:**
- Goal-based: assert the desktop band, compact Product disclosure, landmark,
  item order, link kinds, current state, and exact footer groups/content (AC4-
  AC8).
- Goal-based: assert one title/header, search, theme control, Docs menu,
  sidebar, breadcrumbs, table of contents, edit control, pagination, skip link,
  and content layout owner on home and nested guide routes (AC9).
- Goal-based: assert Product and Docs disclosure states are independent (AC6).

**Approach:**
- Compose a docs-local orientation wrapper at the pinned supported header seam;
  keep the band non-sticky and the default Starlight header sticky.
- Extend the docs-local footer after native pagination without importing
  marketing components, palette, tokens, layout, or state.

**Done when:** docs exposes the approved product map and subordinate footer
while every pinned Starlight affordance remains present, singular, and native.

### T4: Combined emitted chrome passes route, browser, and design evidence

**Depends on:** T2, T3, spec:site-browser-quality-gate/T2

**Touches:** web/src/test/e2e/**/*.ts, tools/test_check_rendered_site_links.py

**Tests:**
- Goal-based: build both sites, enumerate the exact content/kind/current
  contract, and run complete page/fragment and route checks (AC3-AC11).
- Goal-based E2E: exercise the approved route/theme/viewport matrix for skip
  order, focus visibility, keyboard paths, independent disclosures, overflow,
  and axe thresholds (AC5-AC8, AC12).
- Visual/manual QA: record renderer-specific design review against the named
  directions and principles (AC13).

**Approach:**
- Verify emitted behavior; source shape and screenshot existence are not proof.
- Keep optional screenshots outside required CI and tracked output.

**Done when:** exact emitted content, combined links/routes, browser behavior,
and renderer-specific design reviews pass.

## Rollout

Land the data contract and projection support first. After `/now/` exists,
ship both renderer adaptations in the same completion wave so vocabulary cannot
drift. Browser verification follows the deterministic gate foundation.
Rollback is a normal source revert; no dependency or infrastructure changes.

## Risks

- Over-generalizing the contract could create a navigation framework; fields
  remain limited to the two current consumers and approved taxonomy.
- A docs override could duplicate framework controls; presence-and-singularity
  and independent-state tests protect the pinned behavior.
- Current-state logic can overclaim homepage fragments; the exact route rules
  prohibit inferred client state.

## Changelog

- 2026-08-17: initial plan after approval of the shared-IA,
  separate-renderer contract.
- 2026-08-17: fixed the exact Now-based taxonomy, both footer treatments, docs
  desktop/mobile behavior, link/focus/current semantics, Starlight ownership,
  non-shared boundary, and `/now/` dependency.
- 2026-08-20: T2, T3 and T4 shipped (#1060, #1062, #1067). All thirteen
  acceptance criteria are met. AC13 was answered by a recorded human design
  review — no Major issue — kept in
  [`notes/design-review.md`](notes/design-review.md) rather than asserted here,
  because it is a judgement no gate can stand in for. The deferred
  `tap-target-audit-remeasure-after-shared-chrome` backlog item was answered and
  closed: no demonstrated non-exempt failure, with all 22 shared-chrome
  candidates conforming through SC 2.5.8's Spacing clause.
- 2026-08-20: corrected the docs seam during T3. The LLD named a "supported
  header override"; the seam is a supported `PageFrame` override. Verified
  against installed Starlight 0.41.4: `Header.astro` declares no slots and
  renders inside `PageFrame`'s header, so a band composed there is inside the
  pinned header's sticky region and cannot scroll away as the spec requires.
  `PageFrame` is the only supported seam that renders above it. The native
  `<Header slot="header" />` is preserved unchanged, so Starlight remains the
  singular owner of its header; only the layout wrapper is docs-local, and its
  outer header is `position: sticky` rather than Starlight's `position: fixed`
  because the spec requires the band to scroll away while the header stays
  sticky. No acceptance criterion changed.
