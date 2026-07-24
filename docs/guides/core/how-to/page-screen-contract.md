# How to fill the page/screen contract

## When to use this guide

Use the page/screen contract before writing HTML for a new page, route, or
significant surface. The contract is proportional to risk — not a ritual for
every change.

**Fill the full contract when:**
- Building a new route or page
- Adding a significant feature to an existing page (a new onboarding step, a feature-gating screen, a key conversion surface)
- Working on a surface that handles a destructive action or requires form input

**Skip or abbreviate when:**
- Adding a single form field to an existing form (inherit the parent contract)
- Updating a tooltip, badge, or minor component variant
- Making a visual-only change (colour, spacing, typography) with no behavioural changes

When in doubt: a 15-minute contract conversation saves hours of rework.

## Prerequisites

- You have completed the shared pre-flight (named aesthetic reference, seed tokens, state matrix) from the `frontend-engineering` skill
- You know who the primary user is and what they are trying to accomplish on this surface

## Result

A completed 12-field contract recorded in the spec before any HTML is written. The contract is the surface's requirements document — it answers the questions that an implementation will otherwise answer arbitrarily.

---

## The 12 fields

### 1. target user

Who specifically will use this surface. Be precise — "enterprise admin" or "first-time developer" not "user". If multiple user types land here, name the primary one; other types are edge cases.

*Example:* `target user: engineering manager evaluating the tool for their team`

### 2. primary job

The one thing the user comes here to do. A surface with two primary jobs has no primary job — it needs to be split or one job demoted. Write it as a job-to-be-done: "[verb] [outcome]".

*Example:* `primary job: evaluate whether this tool fits their team's workflow`

### 3. primary action

The single most important action available on this surface — the one the surface is designed to drive. If there are multiple actions, one is primary; the rest are secondary.

*Example:* `primary action: click "Start free trial"`

### 4. expected result

What the user has or sees immediately after completing the primary action. This defines success for the surface and drives the success state design.

*Example:* `expected result: account creation confirmation + first step of the onboarding flow`

### 5. next action

What the user does after the primary action is complete. Knowing the next action prevents dead ends — every surface should have a clear path forward.

*Example:* `next action: complete the first onboarding step (create a project)`

### 6. first-screen content

What must be visible above the fold without scrolling. List the specific elements: headline, primary CTA, proof signal, etc. This drives the above-fold layout and prioritization.

*Example:* `first-screen content: product headline, primary CTA ("Start free trial"), number of teams currently using the product`

### 7. product proof

The value signal present above the fold. This should be specific and credible — a number, a recognisable logo, a third-party rating. Vague claims ("trusted by thousands") are not proof.

*Example:* `product proof: "2,400 engineering teams" adjacent to the primary CTA`

### 8. read/write consequence

Whether the primary action reads or mutates data, and what happens on error. This determines what error handling the surface needs and whether undo/confirmation is required.

*Example:* `read/write consequence: writes — creates an account; on error: show inline error with specific reason (email already in use, invalid format, server error)`

### 9. critical states

Which of the 18 states in the state matrix this surface must handle. Every surface handles loading and error at minimum. List the specific states and what they mean for this surface.

*Example:* `critical states: loading (form submission in flight), error (form validation + server errors), success (account created), first-run (shown to users who haven't completed onboarding)`

### 10. responsive behavior

How the layout adapts across breakpoints. Name what collapses, reorders, or hides at each significant breakpoint. If the surface is fixed-dimension (PPT/PDF), state that explicitly.

*Example:* `responsive behavior: mobile (375px): headline + CTA full-width, proof signal moves below CTA, social logos collapse to 2-up grid; desktop (1280px): two-column layout — copy left, hero image right`

### 11. a11y requirements

WCAG 2.2 AA baseline applies to all surfaces. Note any state-specific accessibility requirements: focus management needs (modal, route change), live region announcements (form errors, async updates), or specific contrast requirements for surface-specific colours.

*Example:* `a11y requirements: WCAG 2.2 AA; on form submit error: focus moves to error summary; form errors announced via aria-live="assertive"`

### 12. measurement event

The analytics event that fires when the user completes the primary action. This ensures instrumentation is designed into the surface, not bolted on after. Name the event and its key properties.

*Example:* `measurement event: trial_signup_completed { source: "marketing_homepage", plan: "free", timestamp }`

---

## Proportional application examples

### Lightweight: single significant component (abbreviated contract)

Context: adding a new "Invite team member" modal to an existing settings page.

Fill only the fields that are non-obvious or at risk:

```
target user: workspace admin
primary job: invite a colleague to the workspace
primary action: send invitation email
expected result: confirmation toast + invited user appears as "pending" in team list
read/write consequence: writes — creates invitation record; on error: show inline error (invalid email, already a member, invite limit reached)
critical states: loading (invitation sending), error (validation + server), success (invite sent)
a11y requirements: WCAG 2.2 AA; focus moves to first field on modal open; returns to "Invite" button on close; error summary announced
measurement event: member_invite_sent { method: "email", workspace_id }
```

Fields like `first-screen content`, `product proof`, and `responsive behavior` are inherited from the parent settings page — no need to re-specify.

### Full contract: significant new page (complete contract)

Context: building a new pricing page from scratch.

Fill all 12 fields. This contract becomes the source of truth for the designer, the implementer, and the reviewer.

```
target user: technical evaluator (developer or engineering manager) comparing paid plans
primary job: determine which plan fits their team's size and usage
primary action: click "Get started" on the recommended plan
expected result: plan selection recorded + redirect to account creation or upgrade flow
next action: account creation (new user) or payment confirmation (existing user upgrading)
first-screen content: plan comparison table (3 columns), primary CTA per plan, monthly/annual toggle, social proof (logos of known customers)
product proof: 3 recognisable customer logos above the fold; star rating from G2 adjacent to the top plan CTA
read/write consequence: reads — no mutation on pricing page itself; primary action writes on next surface
critical states: loading (plan data, if fetched from API), error (API failure — show cached or static fallback), content (plans loaded)
responsive behavior: mobile: single-column plan cards, horizontal scroll on feature comparison table; tablet: 2-column; desktop: 3-column with feature comparison sticky header
a11y requirements: WCAG 2.2 AA; monthly/annual toggle: aria-pressed, announces selection to screen reader; plan comparison table: proper th scope and caption
measurement event: pricing_plan_cta_clicked { plan_name, billing_period, source_page }
```

---

## Cross-reference

The page/screen contract is part of `### Mode: create` in the `frontend-engineering` skill. See that skill for the full 18-state matrix, GATES verification commands, and evidence manifest requirements.
