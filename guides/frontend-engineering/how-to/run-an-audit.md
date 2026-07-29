---
title: Run an Audit
summary: How to run the full frontend-engineering audit on an existing surface — what to run, in what order, what each gate catches, how to read the output, and what to record in the evidence manifest.
pack: frontend-engineering
kind: how-to
---

# How-to: Run a frontend-engineering audit

Use this guide when you need to audit an **existing surface** — a component,
a page, or a set of pages you did not build. The output is an audit report and,
after any necessary fixes, a baseline evidence manifest.

**When to audit:** before starting significant new work on an existing surface,
before a release on a surface with no prior gate history, or when a surface has
reported a11y or performance complaints.

**Skill to load:** `frontend-engineering` in `audit` mode. (If the surface
has no gate history, also load `fe-status` first to understand what's known.)

---

## Before you start

1. **Orient with `fe-status`** — if the surface has an evidence manifest,
   read it first. `fe-status` returns a summary of covered states, last gate
   results, known exceptions, and the highest-priority next action. If no
   manifest exists, `fe-status` will tell you so.

2. **Identify the surface scope** — which routes, files, or components are
   in scope for this audit? Name them. An audit of "the whole product" is not
   a single audit; scope it to one route or feature area.

3. **Collect the files** — locate the HTML, CSS, and JS source files for the
   surface. For a server-rendered page, build it to static HTML first.

---

## Step 1. State matrix audit

Compare the surface against all 18 states in the state matrix. For each
applicable state, mark: **Covered** / **Absent** / **Broken**.

The 18 states: loading, empty, error, partial, disabled, content, success,
first-run, no-results, permission/denied, offline, blocked,
destructive-confirmation, long-content, large-data-set, high-zoom,
reduced-motion, keyboard-only.

To check state coverage, read the HTML. A state is covered if its HTML exists.
A state is absent if there is no HTML for it. A state is broken if the HTML
exists but is incorrect (e.g., a loading state with no `aria-busy`, an error
state with no retry affordance).

**What this catches:** surfaces that only handle the happy path, missing
first-run states (often confused with empty), and missing keyboard-only or
reduced-motion states.

**Time required:** 15–30 minutes for a single-page surface.

---

## Step 2. Accessibility audit

Run both automated tools and the two manual checks.

**Automated (run either or both):**

```bash
# pa11y — lighter, good for single files
npx pa11y "file:///$(pwd)/page.html" --standard WCAG2AA --reporter cli

# axe-core — more rules, better for complex pages
npx axe "file:///$(pwd)/page.html" \
  --tags wcag21aa \
  --chrome-options="no-sandbox,disable-setuid-sandbox,disable-dev-shm-usage"
```

**How to read the output:**
- Each finding shows the WCAG success criterion (e.g., `WCAG2AA.Principle1.Guideline1_4.1_4_3`), the failing element, and a description. Fix blockers (contrast violations, missing labels) before anything else.
- Findings tagged `wcag21aa` are WCAG 2.1 AA violations. Note that WCAG 2.2 AA is the declared baseline — all 2.1 findings are also 2.2 findings.
- After automated tools pass, two WCAG 2.2 criteria still require manual checks.

**Manual check 1 — WCAG 2.4.11 Focus Appearance:**
For every interactive element, tab to it and inspect:
- Is a focus indicator visible?
- Is the focus ring at least 2px in width?
- Does the focus ring have at least 3:1 contrast against the adjacent background?

Record: pass / fail for each interactive element type.

**Manual check 2 — WCAG 2.5.8 Target Size Minimum:**
For every interactive element, measure in DevTools:
- Is the target at least 24×24 CSS pixels? Or if smaller, does it have
  24px of spacing from the nearest adjacent interactive element?

Record: pass / fail for each interactive element type.

**What this catches:** missing labels, contrast failures, missing focus
styles, unlabeled form controls, live-region problems, and the two WCAG 2.2
items automated tools miss.

---

## Step 3. CWV measurement

Measure LCP, INP, and CLS at p75 (mobile and desktop separately where
field data exists).

**Lighthouse (lab data, good for a baseline):**
```bash
npx lighthouse <url> --output json --output-path ./lighthouse-report.json
# Open the HTML report: npx lighthouse <url>
```

Targets: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1.

**How to read the output:**
- Lighthouse shows a score per metric. A score below 90 on LCP or CLS is
  worth investigating. INP is not scored by Lighthouse (field metric only);
  check the "Total Blocking Time" as a proxy.
- Each failing metric has linked audits that explain contributing factors
  (e.g., "Eliminate render-blocking resources" for LCP).

If CWV are already within targets, note the result and move on. If any metric
is out-of-budget, load `fe-performance` for a structured diagnosis.

---

## Step 4. CSS token compliance check

```bash
grep -E "#[0-9a-fA-F]{3,6}|rgba?\(|hsl\(|[0-9]+px" <file.css>
```

Output should return only the `:root` / primitive token-definition block.
Any hardcoded colour or spacing value outside that block is a violation.

Triage priority: colour values first (affect theming and contrast), then
magic spacing pixels.

---

## Step 5. Brownfield inspection

Walk the six-item brownfield checklist from `frontend-engineering` retrofit
mode:

| Item | What to check |
|---|---|
| what-to-preserve | What works and must not regress |
| duplicated-systems | Parallel implementations that could be consolidated |
| hard-coded values | CSS values that should be tokens |
| a11y-debt | Pre-existing a11y failures — note which this audit can address |
| responsive-debt | Viewport breakpoints that fail |
| visual-regression-risk | Downstream components that share styling |

---

## Step 6. Write the audit report

Return findings as a prioritised list with severity:

- **Blocker** — must be fixed before the surface ships in its current form
  (new WCAG violation, missing critical state)
- **Major** — materially weakens the surface; should be fixed soon
- **Minor** — improvement; reviewer will not block on
- **Note** — informational

Each finding maps to the step that caught it (state matrix, a11y, CWV, tokens,
brownfield), with one concrete recommendation.

---

## Step 7. Record the baseline evidence manifest

After the audit, record what was tested — even if findings exist. The manifest
is a factual record, not a certificate of completion.

```
routes: [list of routes/files audited]
viewports: [viewport widths tested]
browsers: [browsers tested]
states: [which of the 18 states were present and which were absent/broken]
screenshots: [filenames or notes on captured states]
a11y result:
  pa11y/axe-core wcag21aa: [pass/fail + finding count]
  manual 2.4.11 Focus Appearance: [pass/fail + notes]
  manual 2.5.8 Target Size Minimum: [pass/fail + notes]
perf result: [LCP / INP / CLS values from Lighthouse; mobile and desktop]
console/network result: [console error count; unexpected third-party calls]
analytics events: [which measurement events were verified]
known exceptions: [documented, accepted gaps with rationale and owner]
unverified items: [items not verifiable in this session + reason]
```

Record Blockers and Majors in `known exceptions` with a rationale and planned
resolution if they are accepted for now. Do not silently omit them.

---

## What you have at the end

An audit report with severity-tagged findings plus a baseline evidence
manifest. The manifest is the ground truth for this surface's gate history
— future work on the surface starts from `fe-status` reading this manifest,
not from re-running the full audit from scratch.
