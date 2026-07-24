---
name: frontend-engineering
description: Load when a task's primary output is HTML, CSS, or JS. Provides design pre-flight, codified craft rules, GATES verification commands, and an evidence manifest for that surface. Four modes — create (new surface), retrofit (improving existing), audit (review only), verify (run gates and manifest).
---

# Skill: frontend-engineering

Load this skill when a task's primary output is HTML, CSS, or JS — a new page,
component, slide deck, dashboard, email template, or any standalone web artifact.
It carries the design pre-flight requirements (named aesthetic reference, seed
token block, state matrix), the craft rules that govern EXECUTE, and the GATES
verification commands. It is not needed for incidental HTML edits to an existing
surface already covered by a grounded aesthetic reference.

## Mode selection

Before starting, select the mode that matches the work:

| Mode | When to use | Required outputs |
|---|---|---|
| **create** | Building a new surface or significant new component | Page/screen contract (proportional to risk), evidence manifest |
| **retrofit** | Improving or extending an existing surface | Brownfield inspection, evidence manifest |
| **audit** | Reviewing an existing surface without writing code | Audit report |
| **verify** | Running the full gate suite on a completed surface | Evidence manifest |

Proceed to the shared pre-flight (PLAN phase) regardless of mode. Mode-specific steps follow the shared pre-flight and the state matrix.

---

## PLAN phase — Shared Pre-flight (all modes)

Complete all four steps before writing any code (create/retrofit) or running any gates (audit/verify). These are the shared foundation for all modes.

### 1. Named aesthetic reference

State a named product reference — not an adjective. The model has learned
visual vocabulary from extensively documented products; vague adjectives
produce the purple-gradient default (Tailwind's `bg-indigo-500` saturated
training data, so "nice", "clean", "modern" all converge there).

**Canonical reference set:**

| Goal | Use |
|---|---|
| Professional / executive SaaS | Linear, Stripe, Vercel |
| Data-dense / terminal | Raycast, Arc |
| Minimal / editorial | Notion |
| Warm / human | Toss |

Name the reference in the spec: `Aesthetic reference: Linear (professional SaaS —
dark surface, high contrast, no gradients)`. If the target must match an existing
user-provided theme (e.g. a PPT brand), describe its key token values instead.

### 1b. Genre routing (T2 — requires experience-design pack)

After naming the aesthetic reference, route to the XD discipline skill that
matches your surface's primary purpose. These skills add surface-specific IA,
structure, and conversion principles on top of the generic design pre-flight.

**Check availability:** the experience-design pack is installed if skill
`conversion-design` appears in your available skills. If absent, record a named
skip in the spec — `XD genre routing: skipped (experience-design pack absent)` —
and proceed to step 2. A named skip is not a failure; it is honest accounting.

**Load the skill that matches your surface (name it by name in the spec):**

| Surface type | Load |
|---|---|
| Marketing page, landing page, pricing page, acquisition flow | `conversion-design` |
| Documentation site, help centre, API reference, technical guide | `documentation-design` |
| Dashboard, reporting view, analytics screen, monitoring surface | `analytical-design` |
| Article page, editorial page, blog, long-form content page | `informational-design` |
| Form flow, component state machines, transitions, interactions | `interaction-design` |
| Content strategy — what the surface says and for whom | `content-design` |
| Token foundation setup, semantic alias layer, light/dark theme tokens | `design-system-foundations` |

Load the matched skill inline before writing code. Record the result in the spec
as either `XD genre routing: <skill-name> loaded` or `XD genre routing: skipped
(experience-design pack absent)`.

### 2. Seed token block

Provide a CSS custom properties block before writing any HTML. The model
selects from `var(--ds-color-primary)` rather than fabricating `#5e6ad2` per
session — token-seeding is the single strongest lever for visual consistency.

**Three-tier architecture (one-way dependency):**
```
Primitive  →  Semantic  →  Component
(raw hex)      (role)       (usage)
```
Only the semantic layer goes in the seed block; primitives are defined once
at the top of the CSS file and referenced by semantics.

**Minimum viable property set** (`--ds-` prefix for namespace clarity):

```css
:root {
  /* Color roles — semantic, not raw hex */
  --ds-color-surface:      #ffffff;
  --ds-color-surface-alt:  #f8fafc;
  --ds-color-on-surface:   #1a202c;
  --ds-color-on-surface-2: rgba(0, 0, 0, 0.60);
  --ds-color-primary:      #5e6ad2;
  --ds-color-on-primary:   #ffffff;
  --ds-color-error:        #dc2626;
  --ds-color-on-error:     #ffffff;
  --ds-color-outline:      rgba(0, 0, 0, 0.12);

  /* Spacing — 4 px base, 8-step scale */
  --ds-space-px: 2px;
  --ds-space-1:  4px;
  --ds-space-2:  8px;
  --ds-space-3:  12px;
  --ds-space-4:  16px;
  --ds-space-5:  24px;
  --ds-space-6:  32px;
  --ds-space-7:  48px;
  --ds-space-8:  64px;

  /* Type scale */
  --ds-text-sm:   0.75rem;
  --ds-text-base: 0.875rem;
  --ds-text-lg:   1rem;
  --ds-text-xl:   1.125rem;
  --ds-text-2xl:  1.25rem;
  --ds-font-regular: 400;
  --ds-font-medium:  500;
  --ds-font-bold:    600;
  --ds-leading-tight:  1.25;
  --ds-leading-normal: 1.5;
  --ds-leading-loose:  1.75;

  /* Radius */
  --ds-radius-sm: 4px;
  --ds-radius-md: 8px;
  --ds-radius-lg: 12px;
  --ds-radius-full: 9999px;

  /* Shadow */
  --ds-shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --ds-shadow-md: 0 4px 8px rgba(0,0,0,0.08);
  --ds-shadow-lg: 0 8px 24px rgba(0,0,0,0.10);

  /* Motion */
  --ds-duration-quick:    120ms;
  --ds-duration-moderate: 200ms;
  --ds-duration-gentle:   300ms;
  --ds-ease-standard:     cubic-bezier(0.4, 0, 0.2, 1);
  --ds-ease-decelerate:   cubic-bezier(0, 0, 0.2, 1);
}
```

#### Print / PPT token block

When the output targets a PPT slide or PDF export, add this block and use
`pt` for typographic values:

```css
@page {
  size: 960px 540px; /* 16:9 slide — standard widescreen */
  margin: 0;
}

* {
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact; /* preserve background fills */
}

@media print {
  :root {
    --ds-color-surface:    #ffffff;
    --ds-color-on-surface: #000000;
    --ds-shadow-sm: none;
    --ds-shadow-md: none;
    --ds-shadow-lg: none;
  }

  .slide            { page-break-after: always; }
  h2, h3, figure,
  table, blockquote { page-break-inside: avoid; }
}
```

**Print safety:** `box-shadow` and `text-shadow` are unreliable across
renderers (Chrome/WeasyPrint differ) — use `--ds-shadow-*: none` in the
print override and rely on borders for separation instead. Avoid Tailwind
responsive variants (`sm:`, `md:`) for fixed-dimension artifacts.

### 3. State matrix

Enumerate all states for every async component as a table in the spec.
LLMs are trained predominantly on happy-path code; they will not generate
missing-state branches without explicit enumeration. A 2025 study of
50 AI-generated dashboards found 92% had no empty state and 78% had no
error state.

The canonical 18-state set for this skill, aligned with the XD quality-floor:

| State | Treatment |
|---|---|
| loading | Skeleton screen matching the final layout (use spinner only when shape is unknown); add `aria-busy="true"` and `aria-label="Loading <thing>"` to the skeleton container |
| empty | Illustration or icon + label describing the empty condition + primary CTA |
| error | Preserve prior content; show inline error message + retry affordance |
| partial | Pagination or load-more with a record count; mark missing segments clearly |
| disabled | Render it disabled with `aria-disabled="true"` and a tooltip or label explaining why |
| content | The normal loaded state — spec this too so the skeleton shape is known |
| success | Action completed: confirm visibly and proportionately (subtle toast for low-stakes; prominent banner for high-stakes) |
| first-run | Never had data — orient the user and invite the first meaningful action; do not show the generic empty state |
| no-results | A filter or search emptied the set — show what query was applied and how to recover |
| permission/denied | Unauthorized or locked view: show a read-only or locked state with a recoverable note (who can act, how to request access); never a blank screen |
| offline | Network unavailable — show cached content where possible; provide a manual retry; indicate stale status |
| blocked | Action cannot proceed due to an external dependency or policy — name the blocker and the resolution path |
| destructive-confirmation | Action has irreversible consequences — require explicit confirmation with a clear statement of what will be destroyed; provide a safe default (cancel) |
| long-content | Content significantly longer than typical — offer progressive disclosure, a table of contents, or pagination |
| large-data-set | Query returns more records than the UI can show — implement virtual scrolling, pagination, or sampling; never slice silently |
| high-zoom | Surface used at 200–400% zoom — test that text reflows, controls remain operable, and no horizontal scrolling is required |
| reduced-motion | User has requested reduced motion — all animations replaced with instant or cross-fade transitions; no sliding, scaling, or spinning |
| keyboard-only | All interactions reachable and completable via keyboard alone — no pointer dependency; logical tab order; visible focus indicators at all times |

**Skeleton vs spinner rule:** use a skeleton when the content shape is
predictable (table rows, card grids, profile cards). The skeleton must
match the final layout so there is no layout shift on load. Use a spinner
only when shape is genuinely unknown.

Not all states apply to every surface — omit states that are genuinely inapplicable and note why in the spec.

---

### Mode: create

Use when building a new surface or significant new component.

#### Step 0. Page/screen contract (required before significant UI code)

Before writing HTML for a new page or significant surface, fill the
page/screen contract. This contract is proportional to risk and scope — a
new route, a key onboarding surface, or a feature-gating screen warrants
the full 12-field contract. A single new form field, a tooltip, or a minor
component variant does not.

**Page/screen contract template (12 fields):**

| Field | What to specify |
|---|---|
| target user | The specific user type or persona this surface serves |
| primary job | The one job the user comes here to complete |
| primary action | The single most important action available on this surface |
| expected result | What the user sees/has after completing the primary action |
| next action | What the user does after the primary action is complete |
| first-screen content | What must be visible above the fold without scrolling |
| product proof | The value signal (stat, social proof, outcome indicator) present above the fold |
| read/write consequence | Whether the primary action reads or mutates data; what happens on error |
| critical states | Which of the 18 states this surface must handle (minimum: loading, empty or first-run, error, content) |
| responsive behavior | How layout adapts across breakpoints; what collapses, reorders, or hides |
| a11y requirements | WCAG 2.2 AA — note any state-specific requirements (focus management, live regions) |
| measurement event | The analytics event that fires on primary action completion |

Record the completed contract in the spec before writing HTML.

#### Steps 1–3. Proceed through the shared PLAN phase pre-flight

Run steps 1, 1b, 2, and 3 from the shared pre-flight above (aesthetic reference, genre routing, seed tokens, state matrix).

#### EXECUTE and GATES

Proceed to the EXECUTE phase (Craft Rules) and GATES phase below. Produce an evidence manifest at completion.

---

### Mode: retrofit

Use when improving or extending an existing surface without building from scratch.

#### Step 1. Brownfield inspection checklist

Before touching any code, run this inspection against the existing surface. Record findings for each item:

| Item | What to inspect |
|---|---|
| what-to-preserve | What currently works well and must not regress — visual patterns users rely on, established keyboard flows, screen-reader compatibility |
| duplicated-systems | Parallel implementations of the same component, token, or logic that this change could consolidate or that it must not fork further |
| hard-coded values | CSS values that should be design tokens (`#5e6ad2`, `margin: 13px`) — note them for opportunistic migration |
| a11y-debt | Accessibility failures already present — note which ones this change must not worsen, and which it can address as a ride-along |
| responsive-debt | Viewport breakpoints that fail at current state — note which this change must not worsen |
| visual-regression-risk | Downstream components or pages that share styling with the modified surface and could be visually affected |

#### Step 2. Proceed through the shared PLAN phase pre-flight

Run steps 1, 1b, 2, and 3 from the shared pre-flight (aesthetic reference, genre routing, seed tokens, state matrix). For retrofit work, focus the state matrix on states that are absent or broken — not a full re-enumeration unless the surface is substantially rebuilt.

#### EXECUTE and GATES

Proceed to the EXECUTE phase (Craft Rules) and GATES phase below. Produce an evidence manifest at completion.

---

### Mode: audit

Use when reviewing an existing surface without writing code. The output is a structured audit report, not code.

#### Audit procedure

1. **Run the state matrix audit.** Compare the surface against all 18 states in the state matrix. For each applicable state, mark: Covered / Absent / Broken. Note the specific issue for Absent and Broken.
2. **Run the accessibility audit.** Check against WCAG 2.2 AA. Use the GATES accessibility tools (pa11y or axe-core). Note which WCAG 2.2 success criteria require manual verification because tooling caps at wcag21aa.
3. **Check the CWV targets.** Measure or estimate LCP ≤2.5s / INP ≤200ms / CLS ≤0.1 at p75 (mobile and desktop separately where field data exists). Note any category over budget.
4. **Run the brownfield inspection checklist.** Use the same 6-item checklist from retrofit mode.

#### Audit report format

Return findings as a prioritised list with severity (Blocker / Major / Minor / Note). Each finding maps to the state, criterion, or checklist item it violates, with one concrete recommendation.

Record findings in the evidence manifest under `known exceptions` and `unverified items`.

---

### Mode: verify

Use when a completed surface needs gates run and an evidence manifest generated.

#### Verification procedure

Run the full GATES suite in order:

1. **Structural HTML validation** (GATES phase step 1)
2. **Accessibility audit** (GATES phase step 2) — note that WCAG 2.2 AA is our declared baseline; the tooling caps at wcag21aa; two success criteria require manual verification: 2.4.11 Focus Appearance and 2.5.8 Target Size Minimum
3. **CSS token enforcement** (GATES phase step 3, if stylelint is configured)
4. **Visual QA checklist** (GATES phase step 4) — confirm all 18 applicable states are present

After running all four gates, generate the evidence manifest (see Evidence manifest section below) with the results.

---

## EXECUTE phase — Craft Rules

### Avoid the AI Aesthetic

AI-generated UI has recognisable failure patterns. Refuse all of them:

| Pattern | Why it's a problem | Instead |
|---|---|---|
| Purple / indigo everything | Models default to `bg-indigo-500` — every generated app looks identical | Use the project's token palette; derive from the named aesthetic reference |
| Excessive gradients | Add visual noise; clash with most design systems | Flat colour or a single subtle gradient matching the system |
| Rounded everything (`rounded-2xl` / `border-radius: 16px` on all elements) | Ignores the radius hierarchy in real designs — cards, buttons, and inputs each have a distinct radius | Use the `--ds-radius-*` scale; vary by element type |
| Generic hero sections | Template-driven layout with no connection to actual content or user need | Content-first layout driven by what the user needs to do |
| Lorem ipsum placeholder copy | Hides layout problems that real content reveals (wrapping, overflow, long names) | Realistic-length placeholder text that approximates actual content |
| Oversized equal padding everywhere | Destroys visual hierarchy; wastes screen space | Use the spacing scale; vary padding by component level |
| Uniform card grids | Ignores information priority and scanning patterns | Purpose-driven layouts — group by relationship, not by grid slot |
| Shadow-heavy design | Layered shadows compete with content; slow on low-end devices | Use `--ds-shadow-sm` sparingly; flat or a single elevation level |

### HTML element selection rules

Rules are in **WRONG → RIGHT** form. "Use semantic HTML" is not a rule;
the specific forms below are.

#### Interactive elements

- WRONG: `<div onclick="…">`, `<span onclick="…">` / RIGHT: `<button type="button">` for any action
- WRONG: `<a href="#" onclick="…">` for actions / RIGHT: `<a href="…">` for navigation only; `<button>` for actions — never cross them
- WRONG: `<div role="button">` with no keyboard handler / RIGHT: `<button>` — it receives keyboard, focus, and activation natively; avoid `role="button"` on a non-button element unless a framework absolutely requires it, and then you must add `tabindex="0"` and `onkeydown` handlers for both Enter and Space

#### Landmark elements

- One `<main>` per page, no exceptions
- One `<h1>` per page
- Heading levels are sequential — never skip (h1 → h3 is wrong; heading level = outline position, never visual size)
- `<section>` only when it has a heading as its first child; otherwise use `<div>`
- Multiple `<nav>` elements require `aria-label` distinguishing them: `aria-label="Primary"`, `aria-label="Breadcrumb"`
- `<article>` for self-contained distributable content; `<aside>` for tangentially related content

#### Forms

- WRONG: `<input placeholder="Email">` with no label / RIGHT: `<label for="email">Email</label><input id="email">` or `aria-labelledby`; `placeholder` is not a label — it fails WCAG 1.3.1 and disappears on input
- WRONG: `aria-describedby` pointing to an element not yet in the DOM / RIGHT: place the target element in the DOM before the input receives focus; inject empty containers on page load
- WRONG: ungrouped checkboxes/radios / RIGHT: `<fieldset><legend>…</legend>…</fieldset>` for every checkbox or radio group
- `autocomplete` attribute is required on personal-data fields: `name`, `email`, `tel`, `current-password`, `new-password`, address fields

#### Images and media

- WRONG: `alt="image"`, `alt="photo of a dog"` / RIGHT: descriptive text without "image of" / "photo of" prefixes; `alt=""` for decorative images; max ~150 chars — use `<figcaption>` for longer descriptions
- WRONG: `<img>` for decorative backgrounds / RIGHT: CSS `background-image` — the element is removed from the accessibility tree automatically
- SVG used as a meaningful image: add `role="img"` and a `<title>` as the first child
- SVG that is decorative: `aria-hidden="true"`

#### Content

- WRONG: lorem ipsum placeholder text / RIGHT: realistic-length placeholder text that approximates what real content looks like — long names, multi-line descriptions, edge-case values

### CSS rules

- WRONG: `color: #5e6ad2`, `background: #f8fafc`, `margin: 13px` / RIGHT: all colour and spacing values via `var(--ds-*)` — no hardcoded hex, rgb, hsl, or magic pixel values
- WRONG: `z-index: 9999` / RIGHT: define a named z-index scale: `--z-base: 0; --z-overlay: 100; --z-modal: 200; --z-toast: 300` — use named custom properties only
- WRONG: `line-height: 24px` / RIGHT: unitless — `line-height: var(--ds-leading-normal)` or `line-height: 1.5`
- WRONG: `#nav {}`, `ul.nav {}` / RIGHT: class selectors only; no ID selectors; no qualified selectors
- WRONG: selector depth > 3 levels / RIGHT: max 3 levels of nesting
- WRONG: `tabindex="2"`, `tabindex="5"` (positive values) / RIGHT: `tabindex="0"` to enter tab order; `tabindex="-1"` for programmatic focus targets only; never positive values — they disrupt the natural tab sequence
- WRONG: `.btn:hover { … }` with no focus style / RIGHT: every `:hover` rule has a matching `:focus` or `:focus-visible` rule
- WRONG: `outline: none` / RIGHT: replace with a visible alternative — `outline: 2px solid var(--ds-color-primary); outline-offset: 2px` or a `box-shadow` equivalent

### Accessibility rules

**Default baseline: WCAG 2.2 AA.** WCAG 2.2 AA is our baseline — it exceeds the WCAG 2.1 minimum currently cited by EU EAA, ADA, and AODA. Two success criteria are new in 2.2 and require manual verification because automated tooling (pa11y/axe-core) caps at wcag21aa: **2.4.11 Focus Appearance** (visible focus indicator with sufficient size and contrast) and **2.5.8 Target Size Minimum** (interactive targets ≥24×24 CSS pixels). Mark these explicitly in the evidence manifest under `a11y result`.

**Browser policy: Baseline Widely Available.** Target only features in the Baseline Widely Available set (features shipping in all major browsers for at least 30 months). Check baseline status at web.dev/baseline before using any feature not in the baseline set.

#### ARIA discipline

**First Rule of ARIA:** if a native HTML element provides the semantics and
behaviour, use it — do not bolt ARIA onto a generic element.

- WRONG: `<div role="button" onclick="…">` — no keyboard, no activation, no inherited states / RIGHT: `<button>`
- WRONG: `aria-label="Submit"` on a `<button>Submit</button>` with visible text / RIGHT: omit `aria-label` — it overrides the visible label and breaks voice control ("Submit" no longer activates the button by name in Dragon NaturallySpeaking)
- WRONG: `<input aria-label="Email" placeholder="Email">` when a visible label exists / RIGHT: use the `<label>` and omit the redundant `aria-label`

**Dynamic ARIA state must update** — these are not static attributes:

- `aria-expanded="false"` on a closed accordion must flip to `"true"` when open
- `aria-selected` must update as tabs are navigated
- `aria-sort` must update as columns are sorted
- Setting them once in the HTML and never updating them with JS is wrong

**`aria-live` regions:**

- The container must be in the DOM *before* content is injected into it — add it empty on page load and update its text content to trigger the announcement; injecting a live region and populating it simultaneously causes the announcement to be dropped silently in most screen readers
- `aria-live="polite"` for informational updates (toast success, search result counts)
- `aria-live="assertive"` + `aria-atomic="true"` for errors and time-critical alerts (session timeout, form validation summary)

#### WCAG contrast floor (WCAG 1.4.3 / 1.4.11)

| Element | Minimum ratio |
|---|---|
| Body text | 4.5 : 1 |
| Large text (≥ 18 pt or ≥ 14 pt bold) | 3 : 1 |
| UI components (borders, focus rings, icons, input outlines) | 3 : 1 |
| Placeholder text | 4.5 : 1 (counts as text) |

Verify contrast at derivation time — never eyeball it.

#### Reduced motion

Every `animation`, `transition`, and `transform` must be guarded. Default to
no motion; enable only when the user has not requested reduced motion:

```css
/* Default: no motion */
.element {
  transition: none;
  animation: none;
}

/* Motion only when the user permits */
@media (prefers-reduced-motion: no-preference) {
  .element {
    transition: opacity var(--ds-duration-moderate) var(--ds-ease-standard);
  }
}
```

Properties to guard: `animation`, `transition`, `transform` (slides, scales,
rotates), `scroll-behavior: smooth`. Colour and opacity changes that carry
meaning do not need guarding — only motion.

#### Modal / dialog keyboard pattern (W3C APG)

```
role="dialog" + aria-modal="true" + aria-labelledby="<title-id>"
On open:   move focus to first focusable element inside the dialog
Tab:       cycle forward through focusable elements inside only (trap)
Shift+Tab: cycle backward (trap)
Escape:    close the dialog
On close:  return focus to the element that opened the dialog
```

#### Tabs keyboard pattern (W3C APG)

```
Tab:         moves focus into the tablist, then out to the tabpanel — never between tabs
Left/Right:  navigate between tabs (wrapping); activate on focus (auto-activation)
Home/End:    jump to first / last tab
```

#### Programmatic focus — when it is required

Move focus programmatically when:
- A modal opens (to first focusable element inside) or closes (back to invoking element)
- A SPA route changes (to the page `<h1>` or a skip-nav landmark with `tabindex="-1"`)
- An inline error appears after form submit (to first invalid field or error summary)
- Async content is inserted and the user needs to interact with it immediately

---

## GATES phase — Verification

Run these after implementation, before review. Record actual command output —
do not assert on internal state.

### 1. Structural HTML validation (no browser required)

```bash
npx html-validate --preset standard,a11y --max-warnings 0 <file.html>
```

Catches without a browser: landmark structure (one `<main>`, unique landmarks),
heading hierarchy (no skipped levels), label associations, ARIA role validity,
`alt` attribute presence, and WCAG H-technique violations. Exits non-zero on any
error.

### 2. Accessibility audit (requires Chromium — runs headless, no display server)

Either tool works; pa11y is lighter, axe-core has more rules:

```bash
# pa11y — local files via file:// path
npx pa11y "file:///$(pwd)/file.html" --standard WCAG2AA --reporter cli

# axe-core/cli — URL or file, CI-safe Chromium flags
npx axe "file:///$(pwd)/file.html" \
  --tags wcag21aa \
  --chrome-options="no-sandbox,disable-setuid-sandbox,disable-dev-shm-usage"
```

Note: tooling currently caps at `wcag21aa` — WCAG 2.2 AA is our declared baseline (it exceeds the wcag21aa minimum). Two WCAG 2.2-only success criteria require **manual verification**: **2.4.11 Focus Appearance** and **2.5.8 Target Size Minimum**. Record the manual-check outcome in the evidence manifest under `a11y result`.

### 3. CSS token enforcement (optional — run if stylelint is already configured)

```json
{
  "plugins": ["stylelint-declaration-strict-value"],
  "rules": {
    "scale-unlimited/declaration-strict-value": [
      ["color", "background-color", "border-color", "font-size"],
      {
        "ignoreValues": ["inherit", "transparent", "currentColor"],
        "message": "Use design tokens (var(--ds-*)) — no hardcoded values"
      }
    ]
  }
}
```

Install: `npm install --save-dev stylelint stylelint-declaration-strict-value`

### 4. Visual QA checklist (agent-executable, no tooling)

- [ ] All applicable states from the 18-state matrix are present in the HTML — not just the happy path; check each applicable state by reading the HTML
- [ ] No hardcoded colour or spacing values outside the token-definition block — grep: `grep -E "#[0-9a-fA-F]{3,6}|rgba?\(|hsl\(|[0-9]+px" <file.css>` should return only the `:root` / primitive token-definition block, no other hex, rgb, or px values
- [ ] Print output correct: if PPT/PDF context, open in browser and trigger print preview — check slide boundaries, colour preservation, no overflow
- [ ] Screenshot taken and observed: Playwright headless (`page.screenshot()`) or browser devtools screenshot — assert on what you see, not on internal state

---

## Performance targets

### Core Web Vitals (CWV)

Targets at p75, evaluated separately for mobile and desktop where field data exists:

| Metric | Target | What it measures |
|---|---|---|
| LCP (Largest Contentful Paint) | ≤2.5s | Perceived load speed — when the main content appears |
| INP (Interaction to Next Paint) | ≤200ms | Responsiveness — how fast the page responds to interactions |
| CLS (Cumulative Layout Shift) | ≤0.1 | Visual stability — how much content moves unexpectedly |

Measure using Lighthouse, Chrome DevTools Performance panel, or WebPageTest.

### Asset budgets

Enforce these per route. The seven asset budget categories to track are: JS budget (JavaScript parse+execute per route), images budget (total image payload per route), fonts (web font files transferred), third-party scripts (analytics, tags, widgets), hydration (client-side hydration cost for SSR/islands), route-level loading (per-route code-split chunks), and long tasks (main-thread tasks blocking >50ms).

| Budget category | What to measure | Notes |
|---|---|---|
| JS (JavaScript) | Total JavaScript transferred and parsed per route | Prioritise code-splitting; defer non-critical bundles |
| images | Total image payload per route | Use modern formats (WebP/AVIF); serve appropriate sizes via `srcset` |
| fonts | Web font files transferred | Self-host; `font-display: swap` or `optional`; subset aggressively |
| third-party scripts | Analytics, tag managers, widgets | Audit regularly; defer or facade heavy embeds |
| hydration | Client-side hydration cost (SSR / islands) | Islands architecture preferred; measure Time to Interactive delta |
| route-level loading | Per-route code-split chunk sizes | Each route chunk should be independently cacheable |
| long tasks | Main-thread tasks > 50ms | Use `scheduler.yield()` or `setTimeout` chunking to break up long tasks |

---

## Evidence manifest

FE cannot claim completion (create or retrofit) or a passing gate run (verify) without an evidence manifest. The manifest is a structured record of what was tested and what was found.

**Required fields (all 11 must be present):**

| Field | What to record |
|---|---|
| routes | List of routes/URLs or file paths tested |
| viewports | Viewport widths tested (e.g. 375px mobile, 768px tablet, 1280px desktop) |
| browsers | Browsers or rendering engines tested (per Baseline Widely Available policy) |
| states | Which of the 18 states were exercised during testing |
| screenshots | Evidence of rendered states — filenames, Playwright capture, or devtools screenshots |
| a11y result | Output of the accessibility gate (pa11y/axe-core); include manual-check outcome for WCAG 2.4.11 and 2.5.8 |
| perf result | CWV measurement or Lighthouse score; include mobile and desktop values where available |
| console/network result | No console errors; network requests match expected; no unexpected third-party calls |
| analytics events | Confirmation of measurement events firing on primary action completion |
| known exceptions | Documented, accepted gaps with rationale and owner — not a place to hide problems |
| unverified items | Items that could not be verified in this session with reason (no Chromium, no network, etc.) |

---

## Conditional public-surface guidance

*Applies only when the surface will be publicly indexed (marketing pages, documentation, product landing pages). Skip for internal tools, authenticated dashboards, and surfaces behind login.*

For publicly indexed surfaces, add these items to the spec and verify them before merge:

- **Metadata**: `<title>` (60 chars max), `<meta name="description">` (155 chars max), Open Graph tags (`og:title`, `og:description`, `og:image`) for link previews
- **Canonical URLs**: `<link rel="canonical" href="…">` on every public page; avoid duplicate content from trailing slashes, `www` vs non-`www`, or protocol variants
- **Sitemaps**: ensure the route is included in the sitemap or explicitly excluded; no orphaned pages
- **Structured data**: appropriate schema.org type for the surface (`Article`, `Product`, `FAQPage`, `HowTo`) implemented as JSON-LD; validate at schema.org/validator
- **Search indexing intent**: confirm `robots` meta or `X-Robots-Tag` header is set correctly — `index, follow` for pages that should rank; `noindex` for pagination, internal search results, thin pages

---

## Multi-surface shell contract

*Applies when building or reviewing a product with multiple web surfaces (e.g. marketing site + web app + documentation site).*

Multi-surface products must maintain coherence across surfaces. Apply these constraints regardless of which surface you are currently building:

- **Shared tokens**: all surfaces draw from the same design token contract (same `--ds-*` custom property names, same primitive values, same semantic assignments). A surface that redefines shared tokens independently forks the product's visual identity.
- **Navigation patterns**: primary navigation, breadcrumb, and footer patterns must be consistent across surfaces — same structure, same interaction model, same terminology for shared destinations.
- **Consistent product terminology**: the names of features, entities, and actions must be the same across surfaces. Maintain a terminology list in the project and use it before naming anything.

---

## Anti-patterns to refuse

| Rationalisation | Reality |
|---|---|
| "Accessibility is a nice-to-have for now" | WCAG 2.2 AA is our baseline — it exceeds the WCAG 2.1 minimum currently cited by EU EAA, ADA, and AODA — and it is an engineering quality standard, not a feature |
| "We'll make it responsive later" | Retrofitting responsive design is 3× harder than building it from the start; skip this step only if the output is explicitly fixed-dimension (PPT/PDF) |
| "This is just a prototype" | Prototypes become production code; the AI aesthetic baked in at prototype stage is the AI aesthetic shipped |
| "The AI aesthetic is fine for now" | It signals low quality to every reviewer who sees it and anchors the design in a direction that is expensive to undo |
| "I'll add the empty and error states later" | They will not be added; they are spec ACs, not follow-ons |
| "Skip the design pre-flight — the spec is clear enough" | Technically correct output with no design sense is the exact failure mode this pre-flight prevents; the spec cannot substitute for token constraints |
| "Use a spinner, it's simpler" | Spinners produce layout shift and feel slower than skeleton screens; use a skeleton when the content shape is known |

---

## Red flags

A reviewer should treat any of these as a blocker:

- Inline `style="…"` attributes or arbitrary pixel values not on the spacing scale
- Any state from the applicable 18-state matrix missing from the implementation — check by reading the HTML, not by reasoning about the code
- `outline: none` or `outline: 0` with no visible replacement focus style
- Color used as the sole state indicator (red/green without accompanying text, icon, or pattern)
- Generic AI aesthetic visible in the output (purple gradients, equal oversized padding, `border-radius: 16px` on every element, shadow on every card)
- `aria-expanded`, `aria-selected`, or `aria-sort` set once and never updated
- A `<div onclick>` where a `<button>` would serve
- FE completion claimed without an evidence manifest
- Multi-surface product with inconsistent shared tokens, navigation patterns, or product terminology across surfaces
