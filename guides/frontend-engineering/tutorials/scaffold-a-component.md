---
title: Scaffold a component from a screen brief
summary: A worked tutorial — receive a screen brief, run the pre-flight, write the HTML/CSS, implement all states, run the gates, and produce an evidence manifest.
pack: frontend-engineering
kind: tutorial
---

# Scaffold a component from a screen brief

This tutorial walks the full `frontend-engineering` create-mode workflow on a
concrete example: a **notification card** component with loading, empty,
content, and error states. By the end you will have a gate-passing component
and a completed evidence manifest.

**Time:** ~45 minutes for the first attempt; ~20 minutes once the workflow
is familiar.

**What you need:** the `frontend-engineering` pack installed, a project with
HTML/CSS output.

---

## The screen brief

You received this brief from your design collaborator:

> **Notification card** — shows the user's most recent notification. States:
> loading (skeleton while fetching), empty (no notifications yet, first-run),
> content (notification with title, body, and timestamp), error (fetch failed,
> retry affordance). The card sits in a 360px-wide sidebar column. Aesthetic
> reference: Linear (professional dark-surface SaaS).

---

## Step 1. Load the skill and select the mode

Tell your agent:

```
Load frontend-engineering in create mode.
```

The skill loads. You are now in the PLAN phase.

---

## Step 2. Name the aesthetic reference

From the brief: **Linear** — professional SaaS, dark surface, high contrast,
no gradients.

Record this in the spec:

```
Aesthetic reference: Linear (professional SaaS — dark surface, high contrast,
no gradients, sharp edges, monochrome icon treatment)
```

---

## Step 3. Genre routing (step 1b — requires experience-design)

This is a product UI component, not a marketing, documentation, or analytical
surface. None of the XD genre skills apply. Record:

```
XD genre routing: not applicable — product UI component (no genre-specific
surface type)
```

If `experience-design` is not installed, record:
```
XD genre routing: skipped (experience-design pack absent)
```

---

## Step 4. Seed the token block

Provide the CSS custom properties block before writing HTML. Based on the
Linear aesthetic reference, seed a dark-surface token block:

```css
:root {
  /* Color — dark surface, Linear aesthetic */
  --ds-color-surface:      #0d0d0d;
  --ds-color-surface-alt:  #141414;
  --ds-color-on-surface:   #e2e8f0;
  --ds-color-on-surface-2: rgba(255, 255, 255, 0.50);
  --ds-color-primary:      #8b93e8;
  --ds-color-on-primary:   #0d0d0d;
  --ds-color-error:        #f87171;
  --ds-color-on-error:     #0d0d0d;
  --ds-color-outline:      rgba(255, 255, 255, 0.10);
  --ds-color-success:      #4ade80;

  /* Spacing — 4px base, 8-step scale */
  --ds-space-1:  4px;
  --ds-space-2:  8px;
  --ds-space-3:  12px;
  --ds-space-4:  16px;
  --ds-space-5:  24px;
  --ds-space-6:  32px;

  /* Type scale */
  --ds-text-sm:   0.75rem;
  --ds-text-base: 0.875rem;
  --ds-text-lg:   1rem;
  --ds-font-regular: 400;
  --ds-font-medium:  500;
  --ds-leading-tight:  1.25;
  --ds-leading-normal: 1.5;

  /* Radius — sharp edges match Linear aesthetic */
  --ds-radius-sm: 3px;
  --ds-radius-md: 6px;

  /* Motion */
  --ds-duration-moderate: 200ms;
  --ds-ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
}
```

Record the token block in the spec.

---

## Step 5. Enumerate the state matrix

From the brief, the notification card requires these states:

| State | Treatment |
|---|---|
| loading | Skeleton matching the card shape — title line, body line, timestamp line; `aria-busy="true"` on the container |
| empty (first-run) | "No notifications yet" message + optional CTA to explore |
| content | Notification with title, body, and timestamp |
| error | "Could not load notifications" + retry button |

States not applicable to this component: partial, disabled, success, no-results,
permission/denied, offline, blocked, destructive-confirmation, long-content,
large-data-set. Note in spec: "states omitted — not applicable to a single
notification card fetch."

States that are applicable and must be tested:
- high-zoom: verify layout at 200% zoom
- reduced-motion: animation on state transitions must be guarded
- keyboard-only: verify focus states are visible; no interactions require pointer

---

## Step 6. Fill the page/screen contract

```
target user: Authenticated product user checking for updates
primary job: See the most recent notification and act on it
primary action: Click through to the referenced item (if in content state)
expected result: User navigates to the notification's context
next action: Clear the notification or take the referenced action
first-screen content: Notification title + body snippet + timestamp
product proof: n/a — this is a utility component
read/write consequence: Read-only fetch; error shows retry affordance
critical states: loading, first-run, content, error
responsive behavior: Fixed at 360px column width; no breakpoint changes
a11y requirements: WCAG 2.2 AA; aria-busy on loading; live region for
  async state changes; focus managed on retry click
measurement event: notification_card_viewed, notification_card_clicked
```

---

## Step 7. Write the HTML

With the pre-flight complete, write the HTML for all four states. The
states can be toggled via a data attribute (`data-state="loading"` etc.)
or rendered as separate elements — choose the pattern that matches your
templating system.

**Skeleton loading state:**
```html
<article
  class="notif-card notif-card--loading"
  aria-busy="true"
  aria-label="Loading notifications"
>
  <div class="notif-card__skeleton">
    <div class="notif-card__skeleton-title"></div>
    <div class="notif-card__skeleton-body"></div>
    <div class="notif-card__skeleton-meta"></div>
  </div>
</article>
```

**First-run (empty) state:**
```html
<article class="notif-card notif-card--empty">
  <p class="notif-card__empty-msg">No notifications yet.</p>
  <a href="/explore" class="notif-card__cta">Explore what's new</a>
</article>
```

**Content state:**
```html
<article class="notif-card notif-card--content">
  <h3 class="notif-card__title">Your export is ready</h3>
  <p class="notif-card__body">The CSV export you requested finished. 1,204 records.</p>
  <time class="notif-card__time" datetime="2026-07-25T08:34:00Z">
    8:34 AM
  </time>
  <a href="/exports/123" class="notif-card__link">View export</a>
</article>
```

**Error state:**
```html
<article class="notif-card notif-card--error" role="alert">
  <p class="notif-card__error-msg">Could not load notifications.</p>
  <button type="button" class="notif-card__retry">Retry</button>
</article>
```

---

## Step 8. Write the CSS

Key rules from the token block and craft rules:

```css
.notif-card {
  --notif-bg:           var(--ds-color-surface-alt);
  --notif-border:       var(--ds-color-outline);
  --notif-text:         var(--ds-color-on-surface);
  --notif-text-muted:   var(--ds-color-on-surface-2);
  --notif-radius:       var(--ds-radius-md);
  --notif-padding:      var(--ds-space-4);

  background-color:  var(--notif-bg);
  border:            1px solid var(--notif-border);
  border-radius:     var(--notif-radius);
  padding:           var(--notif-padding);
}

/* Skeleton animation — guarded for reduced motion */
.notif-card__skeleton-title,
.notif-card__skeleton-body,
.notif-card__skeleton-meta {
  background-color: var(--ds-color-outline);
  border-radius: var(--ds-radius-sm);
}

/* Default: no animation */
.notif-card__skeleton-title,
.notif-card__skeleton-body,
.notif-card__skeleton-meta {
  animation: none;
}

@media (prefers-reduced-motion: no-preference) {
  @keyframes shimmer {
    0%   { opacity: 0.5; }
    50%  { opacity: 1; }
    100% { opacity: 0.5; }
  }
  .notif-card__skeleton-title,
  .notif-card__skeleton-body,
  .notif-card__skeleton-meta {
    animation: shimmer var(--ds-duration-moderate) var(--ds-ease-standard) infinite;
  }
}

/* Focus styles — WCAG 2.2 AA */
.notif-card__retry:focus-visible,
.notif-card__link:focus-visible,
.notif-card__cta:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
```

---

## Step 9. Run the GATES

After the HTML and CSS are written, run the four GATES in order:

**Gate 1 — HTML validation:**
```bash
npx html-validate --preset standard,a11y --max-warnings 0 notification-card.html
```

**Gate 2 — Accessibility audit:**
```bash
npx pa11y "file:///$(pwd)/notification-card.html" --standard WCAG2AA --reporter cli
```

Then manually verify:
- WCAG 2.4.11: the `.notif-card__retry` and `.notif-card__link` focus rings are
  at least 2px, with 3:1 contrast against the adjacent surface.
- WCAG 2.5.8: `.notif-card__retry` button is at least 24×24 CSS px
  (add `min-height: 32px; min-width: 32px` if needed).

**Gate 3 — CSS token enforcement:**
```bash
grep -E "#[0-9a-fA-F]{3,6}|rgba?\(|hsl\(|[0-9]+px" notification-card.css
```

Output should return only the `:root` token definition block.

**Gate 4 — Visual QA checklist:**
- [ ] All 4 states are present in the HTML (loading, first-run, content, error)
- [ ] No hardcoded values outside the `:root` block
- [ ] Skeleton shape matches the content layout (no layout shift on load)
- [ ] Screenshot taken for each state

---

## Step 10. Produce the evidence manifest

After gates pass, fill the evidence manifest:

```
routes: notification-card.html
viewports: 375px (mobile), 1280px (desktop)
browsers: Chrome (Baseline Widely Available policy)
states: loading, first-run, content, error, high-zoom (200%), reduced-motion,
  keyboard-only
screenshots: loading-state.png, empty-state.png, content-state.png, error-state.png
a11y result:
  pa11y wcag21aa: 0 errors, 0 warnings
  manual 2.4.11 Focus Appearance: pass — 2px outline at 4.8:1 contrast
  manual 2.5.8 Target Size Minimum: pass — retry button 32×40px, link 32×24px
perf result: component-level; no CWV measurement for isolated component
console/network result: no console errors; fetch mock active during review
analytics events: notification_card_viewed fires on content state render
known exceptions: none
unverified items: none
```

---

## What you have built

A notification card component that:
- Implements all 4 applicable states
- Passes HTML validation, pa11y WCAG2AA, and the two WCAG 2.2 manual checks
- Has no hardcoded values — all colour and spacing through tokens
- Has a skeleton that matches the content layout
- Has guarded animations (respects `prefers-reduced-motion`)
- Has visible focus styles meeting WCAG 2.4.11
- Has a completed evidence manifest

This is the workflow for every component and surface built with the
`frontend-engineering` pack.
