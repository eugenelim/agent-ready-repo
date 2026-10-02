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
> retry affordance). The card sits in a 360px-wide sidebar column. The surface
> is an operations console for warehouse dispatch staff who read it over a full
> shift.

---

## Step 1. Load the skill and select the mode

Tell your agent:

```
Load frontend-engineering in create mode.
```

The skill loads. You are now in the PLAN phase.

---

## Step 2. Resolve visual authority (step 1 of the pre-flight)

> Two sequences run here, and this tutorial keeps them apart by case.
> **Step N** with a capital is a step of this tutorial. **step N** in lower case
> is a step of the skill's pre-flight, which each heading names in brackets.

The pre-flight's first step (step 0) reads a design handoff when your repository
configures one. This tutorial does not, so that step records its skip —
`design handoff: no [design] section configured`. Visual authority then resolves
down the precedence chain: no visual target recorded as `visual_target: confirmed`, no direction or taxonomy,
and — for this walkthrough — no incumbent system to extend. That lands on the
terminal rung, `local-premise`, which is the rung an adopter without a design
tree actually walks. If your team does keep design work in a configured
directory, read
[Read the design handoff](../how-to/read-the-design-handoff.md) first: authority
would resolve higher and this step would record which rung supplied it.

A premise states the qualities the surface wants. It never names a product to
copy. Derive it from the surface's own subject matter — who reads it, what
they are doing, what the work is like.

From the brief: dispatch staff reading a console across a full shift. That
argues for low-glare surfaces, a restrained palette that lets one status colour
carry meaning, and type sized for glances rather than reading.

Then check it once: could someone guess this premise from the category alone, or
from the obvious reaction against it? "Dark dashboard" is the category default
and "playful pastel ops tool" is the predictable reaction — both are defaults
rather than choices. The shift-length reading condition is what makes this
premise specific, so keep that and drop the rest.

Record this in the spec:

```
visual authority: composition local-premise / values local-premise — no design
handoff resolved, no incumbent system. Premise: a low-glare console read across
a full shift; one reserved status colour; type sized for glances.
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

## Step 4. Resolve token values (step 2 of the pre-flight)

Values come from the highest source that supplies them. No taxonomy resolved in
step 0 and there is no incumbent token system here, so this walkthrough reads
the fallback block from
`references/fallback-tokens.md` — that is step 2's condition and the only one.
Record the namespace you resolved (`--ds-*` from the fallback here); the craft
rules and the token gates mean *that* namespace, not a literal prefix.

The shipped block is a **light** surface with a placeholder ink accent
(`--ds-color-primary: #1f2933`, marked replace-do-not-ship, because an accent is
a decision to make rather than a value to inherit). Start from it and record
every value the premise changes, so a reader can see which numbers were decided
and which were inherited.

This surface departs from it in five places. Three are premise decisions; two
are adjustments the premise forces once the surface is dark:

- **Surface goes dark** (`#ffffff` → `#0d0d0d`). Step 2 rejected "dark
  dashboard" as a category default, and this is not that: it is the low-glare
  half of the premise, for a console read in a dispatch bay across a night
  shift. The reasoning matters more than the value — a dark surface chosen
  because dashboards are dark is a default; one chosen because the room is dim
  and the shift is long is a decision, and it is the one that survives the
  counterfactual check.
- **The accent becomes the reserved status colour** (`#1f2933` → `#8b93e8`).
  This is the replacement the reference instructs, and the premise says what it
  is for: one accent, doing one job.
- **Radii tighten** (`4px`/`8px` → `3px`/`6px`), so the status colour carries
  the emphasis rather than the shape.
- **Error is re-toned for the dark surface** (`#dc2626` → `#f87171`). The
  fallback's red is chosen against white; on `#0d0d0d` it loses contrast, so the
  lighter tone restores it. Not a premise decision — a consequence of the first
  one.
- **A success role is added** (`--ds-color-success: #4ade80`), which the shipped
  fallback does not define. The state matrix in step 5 needs it; when a surface
  needs a role the fallback has no token for, add it to the semantic layer rather
  than reaching for a raw value at the point of use.

One more token appears below that the fallback does not ship:
`--ds-duration-skeleton`, added in the motion section for the reason stated
there.

Error and success are not premise decisions — they are quality-floor obligations
every surface owes, and they stay reserved for state rather than emphasis. The
fallback's remaining tokens (its shadows, its wider type and space scales) come
through unchanged and are omitted below only for length:

```css
:root {
  /* Color — low-glare surface, one reserved status accent */
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

  /* Type scale — "sized for glances" puts the card's own body at --ds-text-lg,
     one step above the app default, and reserves -sm for the timestamp */
  --ds-text-sm:   0.75rem;
  --ds-text-base: 0.875rem;
  --ds-text-lg:   1rem;
  --ds-font-regular: 400;
  --ds-font-medium:  500;
  --ds-leading-tight:  1.25;
  --ds-leading-normal: 1.5;

  /* Radius — restrained, so status colour carries the emphasis */
  --ds-radius-sm: 3px;
  --ds-radius-md: 6px;

  /* Motion — the skeleton pulse gets its own slower token: at 200ms it cycles
     about five times a second, which a low-glare shift-long surface should not
     do, and which sits near the flashing threshold WCAG 2.3.1 guards */
  --ds-duration-moderate: 200ms;
  --ds-duration-skeleton: 1600ms;
  --ds-ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
}
```

Record the token block and the resolved namespace in the spec.

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
target user: Warehouse dispatch staff, reading the console across a full shift
primary job: See the most recent notification and act on it without losing the
dispatch view
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

**Error state.** `role="alert"` announces the failure, and `tabindex="-1"` lets
the retry handler move focus here so a keyboard user is not stranded where the
skeleton used to be. That focus move is the contract's "focus managed on retry
click" — it is JavaScript this tutorial does not write, so it is recorded below
as unverified rather than claimed.

```html
<article class="notif-card notif-card--error" role="alert" tabindex="-1">
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
  animation: none; /* default; the guarded rule below opts in */
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
    animation: shimmer var(--ds-duration-skeleton) var(--ds-ease-standard) infinite;
  }
}

/* Target size — WCAG 2.2 SC 2.5.8 (AA) wants at least 24x24 CSS px. Set it
   here rather than leaving it to a later "if needed": the manifest records a
   measured value, and a measurement needs code that produced it. */
.notif-card__retry {
  min-block-size: 40px;
  min-inline-size: 32px;
}

/* Focus styles — verified below as WCAG 2.2 SC 2.4.13 Focus Appearance (AAA enhancement) */
.notif-card__retry:focus-visible,
.notif-card__link:focus-visible,
.notif-card__cta:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
```

---

## Step 9. Render, observe, correct

Before the gates, look at what you built against the authority you inherited.
This is the loop the skill runs during EXECUTE, and it is not the rendered-page
inspection in Step 10's gate 5: that one runs after the code is done and asks
whether anything is reader-visibly broken. This one asks whether the surface
looks like what step 2 committed to.

Render a representative state — content is the right one here, because it is the
state the premise describes — and compare:

- **Is the premise visible?** A low-glare console read across a full shift means
  no bright field, one accent doing one job, and a timestamp that recedes.
- **Did anything default in?** The most common divergence is a value nobody
  decided: a stock indigo accent, a heading at twice body for no stated reason.
- **What is the signature decision?** On this card it is the restraint — the
  status colour is the only saturated thing on the surface.

Correct once where the difference is material, then render again to check. The
bound is one correction pass and one verification render; anything still
diverging is recorded rather than iterated on. A further pass happens only if
you ask for one.

This card needed one correction: the first pass gave the timestamp the same
weight as the body, which fought "sized for glances". Dropping it to
`--ds-text-sm` resolved it, and the verification render confirmed the hierarchy.

---

## Step 10. Run the GATES

After the HTML and CSS are written, run the five GATES in order:

**Gate 1 — HTML validation:**
```bash
npx html-validate --preset standard,a11y --max-warnings 0 notification-card.html
```

**Gate 2 — Accessibility audit.** The automated run checks the WCAG 2.1 AA
ruleset; WCAG 2.2 AA is the target, and the delta is the two manual checks below
plus the gap recorded in the manifest.

```bash
npx pa11y "file:///$(pwd)/notification-card.html" --standard WCAG2AA --reporter cli
```

Then manually verify:
- WCAG 2.5.8 Target Size (Minimum), AA: `.notif-card__retry` is at least
  24×24 CSS px. Step 8 sets `min-block-size: 40px; min-inline-size: 32px`, so
  this check confirms a value the stylesheet states rather than one you add now.
- WCAG 2.4.13 Focus Appearance, AAA enhancement: the `.notif-card__retry`
  and `.notif-card__link` focus rings are at least 2px, with 3:1 contrast
  against the adjacent surface.

**Gate 3 — CSS token enforcement:**
```bash
grep -E "#[0-9a-fA-F]{3,6}|rgba?\(|hsl\(|[0-9]+px" notification-card.css
```

Expect two kinds of hit, and nothing else: the `:root` token definition block,
and the small set of geometry values a token system does not own — the 1px
hairline border, the 2px focus ring and its offset, and the target-size minimums.
Those are structural, not thematic. A hit that is a colour, a spacing step or a
type size is the real finding this gate is looking for.

**Gate 4 — Visual QA checklist:**
- [ ] All 4 states are present in the HTML (loading, first-run, content, error)
- [ ] No hardcoded values outside the `:root` block
- [ ] Skeleton shape matches the content layout (no layout shift on load)
- [ ] Screenshot taken for each state
- [ ] Rendered-page inspection run and its observations recorded — a screenshot
      filename is not an observation. See
      [Inspect the rendered page](../how-to/inspect-the-rendered-page.md)

**Gate 5 — Rendered-page inspection:**

Run it and record what you saw — the result state and the verdict, not a list of
filenames: [Inspect the rendered page](../how-to/inspect-the-rendered-page.md).

---

## Step 11. Produce the evidence manifest

After gates pass, fill the evidence manifest:

```
routes: notification-card.html
viewports: 390px (mobile), 1280px (desktop)
browsers: Chrome (Baseline Widely Available policy)
states: loading, first-run, content, error, high-zoom (200%), reduced-motion,
  keyboard-only
visual authority: composition local-premise / values local-premise — no design
  handoff resolved and no incumbent system, so the premise recorded in step 2
  supplied both. Token namespace --ds-* from the fallback block
screenshots: loading-state.png, empty-state.png, content-state.png, error-state.png
inspection observations: completed / pass — nothing reader-visible wrong across
  the four required captures at 390x600 and 1280x900, at rest and scrolled
a11y result:
  pa11y wcag21aa: 0 errors, 0 warnings
  manual 2.5.8 Target Size (Minimum) (AA): pass — retry button 32×40px, from the
    min-inline-size/min-block-size pair Step 8 sets
  manual 2.4.13 Focus Appearance (AAA enhancement): pass — 2px outline;
    --ds-color-primary #8b93e8 on --ds-color-surface-alt #141414 computes
    6.52:1, above the 3:1 floor. Computed, not eyeballed
  WCAG 2.2 AA gap: 2.4.11, 2.5.7, 3.2.6, 3.3.7, 3.3.8 not yet checked
perf result: component-level; no CWV measurement for isolated component
console/network result: no console errors; fetch mock active during review
analytics events: notification_card_viewed fires on content state render
known exceptions: none
unverified items: the retry focus move and the loading-to-content announcement
  are contract requirements living in the component's JavaScript, which this
  tutorial does not write. Verify both with a screen reader before release
```

---

## What you have built

A notification card component that:
- Implements all 4 applicable states
- Passes HTML validation, pa11y WCAG2AA, and the two named WCAG 2.2 manual checks
- Has no hardcoded values — all colour and spacing through tokens
- Has a skeleton that matches the content layout
- Has guarded animations (respects `prefers-reduced-motion`)
- Has visible focus styles meeting WCAG 2.4.13 Focus Appearance (AAA enhancement)
- Has a completed evidence manifest

This is the workflow for every component and surface built with the
`frontend-engineering` pack.
