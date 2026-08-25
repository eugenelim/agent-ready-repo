# Plan: Site browser quality gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done (§ Tasks' register anchors `print-audit-page-break-quality` and `print-chrome-paint-inventory` were both closed on 2026-08-25 and are recorded in `workspace.toml [backlog].closed`; the first on owner review of regenerated print evidence, the second retired won't-do. No body line here changed. Not a supersession — every decision here stands)

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Build mutation-sensitive browser helpers, run the exact 60-case emitted-site
matrix, and use a real browser runtime to complete the tap-target and print
audits. Classify evidence before fixing anything. Product defects return to the
spec that owns their behavior; deterministic coverage gaps stay here; an
independently shippable remediation gets a new spec only after it is observed.
Then wire the clean deterministic subset into required CI. Screenshot-writing
tests remain separate.

## Constraints

- The accepted
  [`docs-tap-target-audit`](notes/docs-tap-target-audit.md) is a measured
  prerequisite for target-size assertions and exemptions.
- [`print-audit.md`](notes/print-audit.md) decides `close-stale` or a narrowly
  scoped `shape` outcome from rendered print evidence.
- The combined site builds marketing first and docs second before preview.
- Use the existing Playwright/axe dependency and Chromium project only.
- No screenshot baseline, new browser engine, dependency, broad exemption,
  inferred responsive fix, route change, or speculative print rule.

## Construction tests

**Integration tests:** the focused Playwright subset runs against the complete
emitted artifact and seeds one failure for each required behavioral assertion.
The workflow construction test proves path filters and blocking invocation.

**Manual verification:** an exposed browser runtime supplies tap-target and
print measurements. The two-device compact-browser release gesture is required
release evidence but not an automated CI precondition.

## Design (LLD)

### Design decisions

- One data-driven deterministic subset owns the 60-case route matrix; existing
  screenshot capture stays opt-in and separate. Traces to: AC1-AC11.
- Base paths come from the preview/config contract, not hard-coded deployment
  repository names. Traces to: AC3.
- Framework ownership is recorded separately from WCAG classification and
  never creates an exemption by itself. Traces to: AC7, AC8, AC14.
- Print rules are conditional output of a representative-page audit, not a
  presumed stylesheet. Traces to: AC12, AC13.

### Dependencies & integration

- The gate consumes the combined build, accepted audit evidence, existing
  Playwright Chromium project, and axe bundle. It integrates with the required
  site workflow and its path filters. Traces to: AC3, AC7, AC10.

### Interfaces & contracts

- A named package command invokes only deterministic spec files. CI calls it
  after building and before artifact deployment. Traces to: AC10, AC11.
- Audit rows carry route, width, theme, selector/content context, target box,
  spacing, classification, rationale, owner, and exact remediation. Traces to:
  AC7, AC8.

### Failure, edge cases & resilience

- Page and console errors are collected per matrix case with route/theme/width
  context. A missing browser or failed preview startup fails closed rather than
  skipping. Traces to: AC3, AC9, AC10.
- Serious/critical axe findings, overflow beyond 1px, missing focus, broken
  keyboard paths, and unstable controls are defects unless one exact accepted
  criterion-grounded exception applies. Traces to: AC4-AC9, AC14.

## Tasks

### T0: The docs tap-target audit classifies every in-scope candidate

**Depends on:** none

**Touches:** docs/specs/site-browser-quality-gate/notes/docs-tap-target-audit.md

**Tests:**
- Visual/manual QA: measure every candidate on both approved docs routes at all
  five widths and both themes and record every required field (AC7, AC8).
- Goal-based: reject blank fields, broad selectors, CSS-inferred geometry,
  framework-ownership-only rationale, or an unowned failure/exemption (AC7,
  AC8).

**Approach:**
- Use an actually exposed browser runtime.
- Classify each candidate as conforming, demonstrated non-exempt failure,
  inline-content exception, user-agent/framework-controlled exception,
  equivalent-control exception, or essential exception.
- Record source ownership separately from classification. No site source
  changes occur during classification.

**Done when:** the audit is Accepted, every matrix candidate is measured and
classified, and every failure or exception has an exact owner and disposition.

### T1: Browser assertions fail on seeded emitted-behavior defects

**Depends on:** none

**Touches:** web/src/test/e2e/**/*.ts, web/playwright.config.ts

**Tests:**
- TDD: independently seed overflow, a broken route, a serious axe violation,
  missing focus indication, a broken keyboard path, and a broken fragment
  (AC9).
- TDD: assert helpers report route, theme, and width and reject a hard-coded
  deployment base (AC3, AC9).

**Approach:**
- Consolidate reusable overflow, axe, page-error, focus, keyboard, and link
  assertions without coupling them to screenshots.
- Keep failure fixtures outside public route inventory.

**Done when:** every seeded defect fails for the intended reason and clean
fixtures pass.

### T2: The exact 60-case matrix passes against emitted output

**Depends on:** T1, spec:site-now-surface/T2

**Touches:** web/src/test/e2e/site-quality-gate.spec.ts, web/src/test/e2e/docs-wayfinding.spec.ts

**Tests:**
- Goal-based E2E: exercise all eight marketing routes at five widths with no
  theme mutation (AC1, AC3-AC6).
- Goal-based E2E: exercise both docs routes at five widths in light and dark
  themes (AC2-AC6).

**Approach:**
- Declare logical paths and qualify them through one configuration-aware
  helper. `/now/` replaces the rejected public `/work/` destination.
- Use roles and landmarks for representative keyboard journeys.

**Done when:** all 60 cases pass overflow, axe, page-error, focus, keyboard,
and route assertions against the combined preview.

### T3: Measured tap-target outcomes receive the smallest owned response

**Depends on:** T0, T1, T2

**Touches:** web/src/test/e2e/site-quality-gate.spec.ts, docs/product/findings/**, conditional owning specs

**Tests:**
- TDD: reproduce each demonstrated non-exempt failure before remediation and
  prove the fixed emitted target afterward (AC8).
- TDD: prove every accepted exception matches only its exact recorded
  selector/content context and criterion class (AC7, AC8).

**Approach:**
- Encode only the accepted audit rows.
- Route shared destination/chrome defects to `site-shared-chrome`, journey-chip
  defects to `journey-page-completion`, and deterministic assertion gaps here.
  Create a separate remediation spec only for an independently shippable defect
  not already owned by those contracts.
- Mark a remediation mechanical only when intended behavior and boundary are
  fully decided by measured evidence; otherwise retain judgment-led ownership.

**Done when:** all observed outcomes are conforming, exactly exempt, or covered
by a named owning spec with red construction evidence and post-fix browser
proof.

### T4: Representative print output decides close-stale or narrow shaping

**Depends on:** T2

**Touches:** docs/specs/site-browser-quality-gate/notes/print-audit.md

**Tests:**
- Visual/manual QA: print the six exact representative routes and record the four
  axes in [`notes/print-audit.md`](notes/print-audit.md) § Measured axes (AC12).
  Vertical overlap and page-break quality are out of scope — `[backlog].open` slug
  `print-audit-page-break-quality`.
- Goal-based: reject any proposed print rule that lacks an exact observed route,
  failure, and smallest owning selector boundary (AC13).

**Approach:**
- Accept browser/framework defaults when the contract passes and record
  `close-stale`.
- If a failure is observed, record `shape` and materialize only the narrow,
  independently shippable remediation required by that evidence.

**Done when:** the print audit records one evidence-backed disposition with no
general stylesheet proposal.

### T5: Required CI blocks on the focused deterministic subset

**Depends on:** T2, T3

**Touches:** web/package.json, .github/workflows/pages.yml, tools/test_*.py

**Tests:**
- TDD: prove the combined build precedes the focused command, the command is
  blocking, and relevant path filters include all owners (AC10).
- Goal-based: prove the command excludes screenshot-writing specs and leaves
  the tracked tree clean (AC11).

**Approach:**
- Add one named package command and one required workflow step using existing
  dependency and browser-provisioning conventions.
- Keep optional screenshot evidence separately invokable.

**Done when:** construction tests pass and a seeded deterministic failure
blocks the local workflow-equivalent command.

### T6: Physical-device release evidence is explicit and reproducible

**Depends on:** T2, T3

**Touches:** docs/guides/**, docs/product/changelog.md

**Tests:**
- Visual/manual QA: perform the documented gesture on one compact iOS browser
  and one compact Android browser and record device/browser and outcome (AC15).

**Approach:**
- Add the smallest maintainer-facing instruction at the existing release
  workflow home.
- Record a blocker and owner rather than claiming a pass when access is absent.

**Done when:** the release record contains two passes or an explicit blocker
and owner.

## Rollout

Land deterministic coverage before making the CI step required. Complete the
measured audits and route each demonstrated defect before enabling the required
gate. Rollback removes only the workflow invocation while retaining useful
tests and evidence; there is no production infrastructure change.

## Risks

- A 60-case matrix can become slow or flaky; shared setup, deterministic waits,
  and one browser bound cost without weakening coverage.
- Framework-owned geometry can invite blanket suppression; exact measured rows
  and criterion-grounded classifications prevent it.
- Print preferences can expand into redesign; the six-route evidence contract
  permits only demonstrated minimal rules.

## Changelog

- 2026-08-17: initial plan after approval of the exact browser matrix and
  thresholds.
- 2026-08-17: replaced `/work/` with `/now/`, fixed the measured tap-target and
  exemption contract, added print disposition evidence, and routed conditional
  remediation by owning behavior.
- 2026-08-18: implemented. Measured outcomes, recorded here because several close
  tasks by finding nothing:
  - **T0 (tap-target audit): zero demonstrated failures.** Every distinct
    undersized candidate conforms through SC 2.5.8's Inline or Spacing clause on
    measured geometry; the audit's § Evidence availability is the single home for
    the counts, so they are not restated here to drift against it. THREE
    measurement traps were corrected first, not two — ancestor adjacency, unpainted
    overlay targets settled by `elementFromPoint` rather than geometry, and
    hover-revealed targets that an `opacity === 0` filter had dropped without a
    recorded rule. The third also required the target set to be restated as one
    definition rather than a filter chain, because trap 2 excludes
    painted-but-unreachable while trap 3 admits unpainted-but-reachable.
  - **T2 (60-case matrix): passes.** 0px document overflow and zero
    serious/critical axe on all 60. One accepted moderate result,
    `landmark-unique` ×8, traced to `@expressive-code/core`'s runtime module and
    accepted on severity plus exact cause, not on ownership.
  - **T3: no remediation.** Nothing was demonstrated, so nothing returned to an
    owning spec and no conditional remediation spec was materialized. The docs
    footer rows and the absent product-orientation band are flagged for
    re-measurement when `site-shared-chrome` lands.
  - **T4 (print): `close-stale`, with two axes not delivered.** Six routes, measured
    on the four axes in [`notes/print-audit.md`](notes/print-audit.md) § Measured
    axes; `close-stale` rests on axes 1 and 2. No print CSS added. AC12 ships
    deferred: per-route navigation visibility is withdrawn
    (`print-chrome-paint-inventory`) and page-break quality was never measured
    (`print-audit-page-break-quality`).
  - **T6: blocked, not passed.** No physical device is reachable; the release
    checklist records the blocker and owner rather than a pass.
- 2026-08-18: T1's scope grew by one file. `web/src/test/e2e/site-base.ts` derives
  the deployment base from `web/astro.config.ts`, because the repository-name
  literal was in seven places — `playwright.config.ts` twice, including the
  `webServer.url` that starts the preview server, and five route constants across
  three spec files. AC3 requires configuration-derived qualification; without this
  a base change would have hung the preview poll with no test predicting it.
