# Choose the right copy skill

**Use this when:** you have a copy task and need to know whether to invoke `copy-direction`, `tone-of-voice`, `content-design`, or `ux-writing`.
**Prerequisites:** `experience-design` pack and `product-engineering` pack installed.
**Result:** one clear skill invocation for your copy task, with no wasted round-trips.

:::note
**How-to** — task-oriented. Picks the right copy skill for your situation.
:::

## Decision table

| Task | Skill | Pack |
|------|-------|------|
| Name the brand-level copy register — cross-surface voice personality all per-surface copy references | `tone-of-voice` | experience-design |
| Name the copy goals and arbitration rules for a specific marketing or acquisition surface (pricing page, campaign landing page, product launch page, onboarding flow copy voice) | `copy-direction` | experience-design |
| Decide what a surface should say, for whom, in what form, and to what objective — before any wireframe starts | `content-design` | experience-design |
| Write product UI copy strings — error messages, empty states, button labels, form labels | `ux-writing` | product-engineering |

## Onboarding tri-point

Onboarding tasks split across three skills by sub-task:

| Onboarding sub-task | Skill |
|---------------------|-------|
| Narrative arc and content structure of the onboarding flow | `content-design` |
| Copy voice and register for onboarding (what tone the copy should have) | `copy-direction` |
| UI-state strings within onboarding screens (loading, error, empty) | `ux-writing` |

## Chain order

When you need all three layers for an acquisition surface, run them in this order:

1. `content-design` — decide what the surface must say and to whom
2. `tone-of-voice` (optional, if no brand-register doc exists yet) — name the brand-level copy register
3. `copy-direction` — name the per-surface copy goals, grounded in the content brief and the brand register
4. `ux-writing` — write the UI-state strings the surface renders

`copy-direction` references the `content-design` output as a structured upstream and the `tone-of-voice` brand-register doc as a brand referent. Neither is required — `copy-direction` degrades gracefully when either is absent.

## When to skip directly to copy-direction

If a brand-register doc already exists, skip `tone-of-voice` and go directly to `copy-direction`. The brand register is a once-per-brand artifact; running `tone-of-voice` again would amend it, not create a new one.

## Common wrong turns

| Situation | Wrong call | Right call |
|-----------|------------|------------|
| "Name the copy vibe for our pricing page" | `tone-of-voice` | `copy-direction` (per-surface) |
| "Write the hero headline" | `copy-direction` | Neither — both produce direction, not finished copy. Use `copy-direction` to name the goals, then write the copy yourself against those goals. |
| "What should our onboarding copy sound like?" | `ux-writing` | `copy-direction` (copy voice) |
| "Write the error message for failed login" | `copy-direction` | `ux-writing` (UI copy state) |
| "What should our brand sound like across all channels?" | `copy-direction` | `tone-of-voice` (brand-level) |
