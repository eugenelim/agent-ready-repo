# Spec: Site browser quality gate

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0089
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Contributors receive a deterministic required-CI signal when a representative
marketing, catalogue, pack, journey, Now, or documentation page becomes
inaccessible or unusable at an approved viewport. The gate exercises the
combined emitted site, consumes measured and criterion-grounded tap-target
evidence, and leaves physical-device review as a visible release
responsibility.

## Boundaries

### Always do

- Exercise emitted pages after the marketing-first, docs-second combined build.
- Resolve every route through the configured deployment base rather than a
  repository-name literal.
- Record route, viewport, theme, selector/content context, target geometry,
  spacing, WCAG 2.2 classification, rationale, owner, and exact remediation for
  every tap-target candidate.
- Audit print output before deciding whether any print rule exists.

### Ask first

- Change the approved route, theme, width, accessibility-severity, overflow,
  tap-target, or representative-print contract.
- Add a browser engine, visual-regression baseline, dependency, framework
  exception, broad selector exemption, or screenshot-writing required test.
- Materialize a remediation spec before emitted evidence demonstrates an
  independently shippable defect.

### Never do

- Treat screenshot existence, a truthy path, source shape, or inferred CSS
  geometry as proof of browser behavior.
- Write tracked screenshot artifacts in required CI.
- Silently suppress an axe rule or classify framework ownership itself as a
  WCAG exception.
- Approve a broad selector exemption, an unmeasured responsive fix, or a
  general print stylesheet without an observed failure.

## Testing Strategy

- Browser helper invariants and seeded failure fixtures use TDD.
- The exact route/theme/viewport matrix is an E2E goal-based check against the
  combined emitted preview.
- Tap-target and print outcomes require measurements from an actually exposed
  browser runtime; absence of that runtime is recorded as missing evidence,
  never converted into an inferred result.
- Physical-device review is recorded manual QA and remains outside
  deterministic CI.

## Acceptance Criteria

- [x] Required CI exercises these marketing routes at 360, 375, 390, 414, and
  1440 CSS-pixel widths without theme mutation: `/`, `/catalogue/`,
  `/packs/core/`, `/journeys/`, `/journeys/core/`,
  `/journeys/product-engineering/`, `/journeys/release-engineering/`, and
  `/now/`.
- [x] Required CI exercises `/docs/` and
  `/docs/guides/core/how-to/start-a-project/` at all five approved widths in
  both the light and dark docs themes.
- [x] Every route is base-qualified from configuration and reaches its expected
  emitted page without an HTTP error, client error, or unhandled page error.
- [x] Every matrix case has no more than 1px document-level horizontal overflow.
- [x] Every matrix case reports zero serious or critical axe findings; any
  accepted lower-severity result is exact, owned, and linked to audit evidence.
- [x] Representative primary navigation, mobile disclosure, docs search/theme
  controls, decision-to-gate links, and footer links are keyboard reachable,
  operable, and visibly focused on the routes where they appear. Decision-to-gate
  coverage is written and passing-when-present but currently **inert**: semantic
  `#decision-<id>` chips are `journey-page-completion`'s contract and are not
  emitted yet, so those six cases skip loudly rather than assert a shape this spec
  does not own. They begin gating the moment that slice lands.
- [x] The accepted tap-target audit classifies every candidate as conforming,
  demonstrated non-exempt failure, inline-content exception,
  user-agent/framework-controlled exception, equivalent-control exception, or
  essential exception and records all required geometry, spacing, context,
  rationale, owner, and remediation fields.
- [x] No tap-target exemption is broad, selector-only, inferred from CSS, or
  justified solely by framework ownership; every demonstrated failure is
  covered by a construction test before remediation and by emitted-browser
  proof afterward.
- [x] A seeded overflow, broken route, serious axe violation, missing focus
  state, broken keyboard path, and broken fragment each cause the focused suite
  to fail with route, width, and theme context.
- [x] The required workflow runs the deterministic subset on relevant site,
  guide, generator, test, dependency-lock, configuration, and workflow changes,
  and a failure blocks the workflow.
- [x] Screenshot capture remains optional, runs outside the required subset,
  and writes no tracked files during CI.
- [x] Print evidence covers `/`, `/docs/`, the ordinary, code-heavy,
  aside-heavy, and long-table guide routes named in
  [`notes/print-audit.md`](notes/print-audit.md), including navigation removal,
  content, links, code, asides, tables, clipping, overlap, and page breaks.
- [x] Print closes stale when browser/framework defaults satisfy that contract;
  otherwise the audit names each exact failure and the smallest narrow rule
  boundary before a conditional remediation spec is created.
- [x] Any observed serious/critical axe failure, overflow beyond 1px, missing
  focus indication, broken keyboard path, or unstable framework-owned control
  is recorded as a demonstrated defect or exact accepted exception—never a
  speculative visual preference.
- [x] The release checklist records a physical-device pass for one compact iOS
  browser and one compact Android browser, or the exact blocker and owner before
  release approval. Satisfied by the second branch, deliberately:
  [`docs/guides/how-to/verify-a-site-release.md`](../../guides/how-to/verify-a-site-release.md)
  records an explicit **Blocked** row — no physical iOS or Android device is
  reachable from this environment — with owner and the requirement that it be
  performed before the next site release is approved. No pass is claimed.

## Assumptions

- Technical: the repository already depends on Playwright and axe and has a
  Chromium project under `web/playwright.config.ts`; no new test dependency is
  required (source: repository inspection on 2026-08-17).
- Technical: existing docs E2E coverage already exercises the selected docs
  home and nested core-guide routes (source:
  `web/src/test/e2e/docs-wayfinding.spec.ts`).
- Product: the exact routes, five widths, docs themes, 1px overflow ceiling,
  and zero serious/critical axe ceiling are fixed (source: approved brief and
  user confirmations 2026-08-17).
- Product: zero tap-target exemptions and zero responsive defects are accepted
  during shaping because no geometry was measured; the final table in the
  owning audit records this evidence state (source: user approval 2026-08-17).
- Product: framework ownership identifies an owner, not an automatic WCAG
  exception (source: user approval 2026-08-17).
- Process: no browser-control runtime is exposed in this shaping session, so
  geometry, axe, overflow, focus, keyboard, and print results remain execution
  evidence rather than inferred shaping claims (source: active managed tool
  surface on 2026-08-17).
