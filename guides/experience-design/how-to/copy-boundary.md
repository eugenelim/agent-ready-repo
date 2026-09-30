---
title: Choose the right copy mode
summary: Route a copy task to one of content design's three modes, or to product microcopy, without duplicating work.
pack: experience-design
kind: how-to
---

# Choose the right copy mode

**Use this when:** you have a copy task and need to know which `content-design` mode it belongs to, or whether it belongs to `ux-writing` instead.
**Prerequisites:** `experience-design` pack and `product-engineering` pack installed.
**Result:** one clear invocation for your copy task, with no wasted round-trips.

:::note
**How-to** — task-oriented. Picks the right copy mode for your situation.
:::

The copy layer is one skill, `content-design`, with three modes. You do not choose between skills; you choose a mode, and `content-design` selects it from your request. The one real boundary is with `ux-writing`, which lives in a different pack and owns the strings a user reads in the product interface.

## Decision table

| Task | Where it goes | Pack |
|------|---------------|------|
| Decide what a surface should say, for whom, in what form, and to what objective — before any wireframe starts | `content-design` → **message and narrative structure** | experience-design |
| Name the copy goals and arbitration rules for a specific marketing or acquisition surface (pricing page, campaign landing page, product launch page, onboarding flow copy voice) | `content-design` → **per-surface acquisition copy goals** | experience-design |
| Name the brand-level copy register — cross-surface voice personality all per-surface copy references | `content-design` → **brand-level register** | experience-design |
| Write product UI copy strings — error messages, empty states, button labels, form labels | `ux-writing` | product-engineering |

Each mode still writes its own artifact, at its own path. Folding the three registrations into one skill did not merge their outputs.

| Mode | Artifact |
|------|----------|
| message and narrative structure | `<output_dir>/content/<slug>.md` |
| per-surface acquisition copy goals | `<output_dir>/copy/<surface-slug>.md` |
| brand-level register | `<output_dir>/copy/brand-register.md` |

## Onboarding tri-point

Onboarding tasks split three ways by sub-task — two of them inside one skill:

| Onboarding sub-task | Where it goes |
|---------------------|---------------|
| Narrative arc and content structure of the onboarding flow | `content-design` → message and narrative structure |
| Copy voice and register for onboarding (what tone the copy should have) | `content-design` → per-surface acquisition copy goals |
| UI-state strings within onboarding screens (loading, error, empty) | `ux-writing` |

## Chain order

When you need every layer for an acquisition surface, run them in this order:

1. `content-design`, **message and narrative structure** — decide what the surface must say and to whom
2. `content-design`, **brand-level register** — optional, if no brand-register document exists yet
3. `content-design`, **per-surface acquisition copy goals** — grounded in the content brief and the brand register
4. `ux-writing` — write the UI-state strings the surface renders

The per-surface mode reads the content brief as a structured upstream and the brand register as a brand referent. Neither is required; the mode degrades gracefully when either is absent.

## When to skip the brand register

If a brand-register document already exists, skip step 2 and go straight to the per-surface mode. The brand register is a once-per-brand artifact: running the brand-level register mode again amends it rather than creating a second one. Asking for a per-surface record under the reserved `brand-register` slug is refused, not repaired — the skill asks you for a different surface slug.

## Common wrong turns

| Situation | Wrong call | Right call |
|-----------|------------|------------|
| "Name the copy vibe for our pricing page" | brand-level register | per-surface acquisition copy goals |
| "Write the hero headline" | per-surface acquisition copy goals | Neither — every mode produces direction, not finished copy. Name the goals, then write the copy yourself against them. |
| "What should our onboarding copy sound like?" | `ux-writing` | per-surface acquisition copy goals |
| "Write the error message for failed login" | per-surface acquisition copy goals | `ux-writing` (UI copy state) |
| "What should our brand sound like across all channels?" | per-surface acquisition copy goals | brand-level register |
