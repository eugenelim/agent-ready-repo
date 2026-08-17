# Plan: Site browser quality gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Extract deterministic browser assertions from the useful parts of current E2E
coverage, prove each one with a seeded failure, and run the explicit route
matrix against the combined emitted preview. Add tap-target assertions only
after the audit fixes the rule and exemption set, then wire this focused subset
as a required, path-filtered CI step. Screenshot-writing tests remain separate.

## Constraints

- The accepted
  [`docs-tap-target-audit`](notes/docs-tap-target-audit.md) is a shaping
  prerequisite for target-size assertions and exemptions.
- The combined site builds marketing first and docs second before preview.
- Use the existing Playwright/axe dependency and Chromium project only.
- No screenshot baseline, new browser engine, dependency, or route change.

## Construction tests

**Integration tests:** the focused Playwright subset runs against the complete
emitted artifact and seeds one failure for each required behavioral assertion.
The workflow construction test proves path filters and blocking invocation.

**Manual verification:** execute and record the two-device compact-browser
release gesture; this is required release evidence but not an automated CI
precondition.

## Design (LLD)

### Design decisions

- One data-driven deterministic subset owns the route matrix; existing
  screenshot capture stays opt-in and separate. Traces to: AC1-AC10.
- Base paths come from the preview/config contract, not hard-coded deployment
  repository names. Traces to: AC3.

### Dependencies & integration

- The gate consumes the combined build, the approved tap-target audit, the
  existing Playwright Chromium project, and axe bundle. It integrates with the
  required site workflow and its path filters. Traces to: AC3, AC7, AC9.

### Interfaces & contracts

- A named package command invokes only the deterministic spec files. CI calls
  that command after building and before artifact deployment. Traces to: AC9,
  AC10.

### Failure, edge cases & resilience

- Page and console errors are collected per matrix case with route/theme/width
  context. A missing browser or failed preview startup fails closed rather than
  skipping. Traces to: AC3, AC8, AC9.

## Tasks

### T0: The docs tap-target audit classifies every in-scope target and exemption

**Depends on:** none

**Touches:** docs/specs/site-browser-quality-gate/notes/docs-tap-target-audit.md

**Tests:**
- Visual/manual QA: measure interactive targets on both approved docs routes at
  all five widths and both themes, recording target geometry, spacing, and
  observed behavior in the audit artifact (AC7).
- Goal-based: verify every exemption records its WCAG 2.2 class, exact selector
  or content context, owner, and rationale; a blank or broad exemption fails
  audit acceptance (AC5, AC7).

**Approach:**
- Classify each candidate as conforming, demonstrated non-exempt failure,
  legitimate inline-content exception, framework/user-agent exception,
  equivalent-control exception, or essential exception.
- Record evidence without changing site source; fixes belong to later tasks or
  a narrowly scoped conditional remediation spec.

**Done when:** the audit artifact is Accepted with every in-scope target
classified and every failure or exemption carrying an owner.

### T1: Browser assertions fail on seeded emitted-behavior defects

**Depends on:** none

**Touches:** web/src/test/e2e/**/*.ts, web/playwright.config.ts

**Tests:**
- TDD: add fixtures or local test pages that independently seed overflow, a broken
  route, a serious axe violation, a missing focus indication, and a broken
  fragment (AC8).
- TDD: assert helpers report route, theme, and width in failures and reject a hard-
  coded deployment base (AC3, AC8).

**Approach:**
- Consolidate reusable overflow, axe, page-error, keyboard, and link assertions
  without coupling them to screenshots.
- Keep failure fixtures outside public route inventory.

**Done when:** every seeded defect fails for the intended reason and clean
fixtures pass.

### T2: The exact route, theme, and width matrix passes against emitted output

**Depends on:** T1

**Touches:** web/src/test/e2e/site-quality-gate.spec.ts, web/src/test/e2e/docs-wayfinding.spec.ts

**Tests:**
- Goal-based E2E: exercise all eight marketing routes at five widths with no theme mutation
  (AC1, AC3-AC6).
- Goal-based E2E: exercise both docs routes at five widths in light and dark themes (AC2-AC6).

**Approach:**
- Declare logical paths and qualify them through one configuration-aware helper.
- Use role/landmark assertions for representative keyboard journeys.

**Done when:** the full 60-case matrix passes overflow, axe, page-error, and
keyboard assertions against the combined preview.

### T3: Tap-target assertions implement the accepted audit and only its exemptions

**Depends on:** T0, T1

**Touches:** web/src/test/e2e/site-quality-gate.spec.ts, docs/product/findings/**

**Tests:**
- TDD: reproduce every demonstrated non-exempt target-size failure before its fix and
  prove the fixed emitted target passes (AC7).
- TDD: prove each exception matches only its recorded inline-content or
  framework-owned selector/context (AC5, AC7).

**Approach:**
- Encode the audit's accepted WCAG 2.2 classification and narrow allowlist.
- Do not invent a global minimum-size assertion that misclassifies inline text.

**Done when:** all demonstrated failures are covered and no unrecorded
exemption suppresses a result.

### T4: Required CI blocks on the focused deterministic subset

**Depends on:** T2, T3

**Touches:** web/package.json, .github/workflows/pages.yml, tools/test_*.py

**Tests:**
- TDD: add a workflow construction test that proves the combined build precedes the
  focused command, the command is not tolerated on failure, and relevant path
  filters include all owners (AC9).
- Goal-based: assert the command excludes screenshot-writing specs and does not dirty the
  tracked tree (AC10).

**Approach:**
- Add one named package command and one required workflow step using existing
  dependency installation and browser provisioning conventions.
- Keep optional screenshot evidence separately invokable.

**Done when:** construction tests pass and a seeded deterministic failure blocks
the local workflow-equivalent command.

### T5: Physical-device release evidence is explicit and reproducible

**Depends on:** T2, T3

**Touches:** docs/guides/**, docs/product/changelog.md

**Tests:**
- Visual/manual QA: perform the documented gesture on one compact iOS browser and one compact
  Android browser, recording device/browser and observed result (AC11).

**Approach:**
- Add the smallest maintainer-facing release-check instruction at the existing
  release workflow home.
- Record a blocker and owner rather than claiming a pass when access is absent.

**Done when:** the release record contains two passes or an explicit blocker
and owner.

## Rollout

Land deterministic coverage before making the CI step required. Enable the
required step only after the tap-target audit contract and clean baseline pass.
Rollback removes the workflow invocation while retaining locally useful tests;
there is no production infrastructure change.

## Risks

- A 60-case matrix can become slow or flaky; shared setup, deterministic waits,
  and one browser bound cost without weakening coverage.
- Framework-owned target geometry can create false positives; audit-owned,
  selector-scoped exemptions prevent blanket suppression.

## Changelog

- 2026-08-17: initial plan after approval of the exact browser matrix and
  thresholds.
