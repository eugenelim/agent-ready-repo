# Spec: Site browser quality gate

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Contributors receive a deterministic required-CI signal when a representative
marketing, catalogue, pack, journey, work, or documentation page becomes
inaccessible or unusable at an approved viewport. The gate exercises the
combined emitted site, uses explicit framework and inline-content exemptions,
and leaves physical-device review as a visible release responsibility.

## Boundaries

### Always do

- Exercise emitted pages after the marketing-first, docs-second combined build.
- Resolve every route through the configured deployment base rather than a
  repository-name literal.
- Consume the approved tap-target audit's rule and exemption record.

### Ask first

- Change the approved route, theme, width, accessibility-severity, overflow, or
  tap-target contract.
- Add a browser engine, visual-regression baseline, or framework exception.
- Make a screenshot-writing test required CI.

### Never do

- Treat a screenshot's existence, a truthy path, or source shape as proof of
  browser behavior.
- Write tracked screenshot artifacts in required CI.
- Add a dependency, silently suppress an axe rule, or classify a failure as a
  framework exception without the accepted audit record.

## Testing Strategy

- Browser helper invariants and seeded failure fixtures use TDD.
- The route/theme/viewport matrix is an E2E goal-based check against the
  combined emitted preview.
- Physical-device review is a recorded manual QA gesture and remains outside
  deterministic CI.

## Acceptance Criteria

- [ ] Required CI exercises these marketing routes at 360, 375, 390, 414, and
  1440 CSS-pixel widths without theme mutation: `/`, `/catalogue/`,
  `/packs/core/`, `/journeys/`, `/journeys/core/`,
  `/journeys/product-engineering/`, `/journeys/release-engineering/`, and
  `/work/`.
- [ ] Required CI exercises `/docs/` and
  `/docs/guides/core/how-to/start-a-project/` at all five approved widths in
  both the light and dark docs themes.
- [ ] Every route is base-qualified from configuration and reaches its expected
  emitted page without an HTTP error, client error, or unhandled page error.
- [ ] Every matrix case has no more than 1px document-level horizontal overflow.
- [ ] Every matrix case reports zero serious or critical axe findings; any
  accepted lower-severity or framework exception is named, scoped, and linked
  to its owning audit evidence.
- [ ] Representative primary navigation, mobile disclosure, docs search/theme
  controls, decision-to-gate links, and footer links are keyboard reachable,
  operable, and visibly focused on the routes where they appear.
- [ ] Demonstrated non-exempt tap-target failures from the approved
  `docs-tap-target-audit` are asserted by the gate; legitimate inline-content
  and framework-owned exemptions remain narrowly enumerated.
- [ ] A seeded overflow, broken route, serious axe violation, missing focus
  state, and broken fragment each cause the focused suite to fail.
- [ ] The required workflow runs the deterministic subset on relevant site,
  guide, generator, test, dependency-lock, configuration, and workflow changes,
  and a failure blocks the workflow.
- [ ] Screenshot capture remains optional, runs outside the required subset,
  and writes no tracked files during CI.
- [ ] The release checklist records a physical-device pass for one compact iOS
  browser and one compact Android browser, or records the exact blocker and
  owner before release approval.

## Assumptions

- Technical: the repository already depends on Playwright and axe and has a
  Chromium project under `web/playwright.config.ts`; no new test dependency is
  required (source: repository inspection on 2026-08-17).
- Technical: existing docs E2E coverage already exercises the selected docs
  home and nested core-guide routes (source:
  `web/src/test/e2e/docs-wayfinding.spec.ts`).
- Product: the exact routes, five widths, and docs theme matrix are approved
  (source: user confirmation 2026-08-17).
- Product: the overflow ceiling is 1px and the axe ceiling is zero serious or
  critical findings (source: user approval of
  `docs/product/briefs/tech-site-completion.md`).
- Product: WCAG 2.2 tap-target classification permits recorded legitimate
  inline-content and framework exemptions (source:
  `docs/product/briefs/tech-site-completion.md`).
- Process: no browser-control runtime is exposed in the shaping session, so
  physical-device execution belongs to future release evidence rather than
  this non-implementation session (source: active managed tool surface on
  2026-08-17).
