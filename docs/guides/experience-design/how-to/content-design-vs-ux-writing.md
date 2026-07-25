# Choose between content-design and ux-writing

**Use this when:** you have a copy task and are not sure whether it belongs to `content-design` or `ux-writing` — or you want to understand why those two skills are in different packs.
**Prerequisites:** `experience-design` pack installed (for `content-design` and `tone-of-voice`); `product-engineering` pack installed (for `ux-writing`).
**Result:** the right skill invoked from the start, with no copy work handed to the wrong layer.

> **How-to** — task-oriented. Decide which skill to reach for on a given copy task.
> For the full three-way boundary that also covers `copy-direction`, read [Three-Way Copy Boundary](copy-layer-boundary.md).

## The boundary in one line

`content-design` decides **what a surface should say** — structure, narrative arc, section jobs, audience awareness level — before any words are written. `ux-writing` writes **the exact words a user reads** in a UI state at a specific screen moment.

They operate at different altitudes and different times in the design thread.

## Why ux-writing lives with the component

`ux-writing` belongs to the `product-engineering` pack because UI copy is inseparable from the component that renders it. An error message is a UI state, not a content decision: it must be blame-free, actionable, and consistent with every other string in the same interaction surface. The constraint set — voice axes, microcopy formulas, content checklist — is tightly coupled to the component's state machine. Keeping `ux-writing` in the product-engineering pack means the copy and the component are owned and reviewed together.

## Why content-design is upstream

`content-design` belongs to the `experience-design` pack because it runs **before** screens exist. It answers: what is the narrative arc of this surface? What does the above-fold section need to communicate? What does the reader need to carry away from the page? Those are structural decisions that constrain every downstream design choice — screen flow, component selection, and the copy that fills each state. Moving `content-design` downstream would reverse that causal flow.

## Decision table

| Stimulus | Reach for |
|---|---|
| "I need to write the error message for a failed login" | `ux-writing` (product-engineering pack) |
| "I don't know what sections this landing page needs" | `content-design` (experience-design pack) |
| "What should the empty state say when there are no projects?" | `ux-writing` (product-engineering pack) |
| "What is the narrative arc for our feature announcement?" | `content-design` (experience-design pack) |
| "How should our brand voice feel across all surfaces?" | `tone-of-voice` (experience-design pack) |
| "Write the confirmation dialog copy for a destructive action" | `ux-writing` (product-engineering pack) |
| "What does the above-fold hero on our onboarding page need to communicate?" | `content-design` (experience-design pack) |

## What each skill produces

**`content-design`** produces a content brief — a text-first document that names what the surface must say, the narrative arc, the section jobs, the audience awareness level, and the completion metric. It does not produce finished copy strings. Once the brief exists, it becomes the upstream input that constrains voice (`tone-of-voice`) and per-state copy (`ux-writing`).

**`tone-of-voice`** produces a doc of named, ranked copy goals grounded in stable referents (persona language, copy precedents, persuasion standards), plus arbitration rules. It covers the across-all-surfaces brand register — not specific copy strings.

**`ux-writing`** produces the exact copy strings for UI states: error messages, empty states, button labels, form labels, confirmation dialogs. It operates from a blame-free, actionable formula per state type, and runs a content checklist before the copy ships.

## The onboarding tri-point

Onboarding surfaces are a common source of confusion because they involve all three skills:

- Onboarding **narrative arc and structure** → `content-design` (what each step needs to communicate, in what order, to what objective)
- Onboarding **copy voice and register** → `tone-of-voice` (how it should sound, what goals win when they conflict)
- Onboarding **UI-state strings** (loading, error, empty) → `ux-writing` (the exact copy for each state the user sees)

A first-run empty state ("You haven't added any projects yet — create one to get started") is `ux-writing`. Deciding that the onboarding flow needs a value-framing step before the first action prompt is `content-design`.

## How the skills connect

When both a content brief and a per-screen state matrix are present, the skills compose:

1. **`content-design`** — decides the surface's narrative arc and section jobs (what to say)
2. **`tone-of-voice`** — names the copy voice goals and arbitration rules (how to say it)
3. **`ux-writing`** — writes per-state copy for each UI state, keyed to the state matrix from `user-flow`

`ux-writing` can also be used standalone — it does not require upstream content-design output. The skills are each independently useful; they are not a mandatory sequence.

## Where to go next

- For the full three-way boundary that includes `copy-direction` (surface-specific marketing copy voice): [Three-Way Copy Boundary](copy-layer-boundary.md)
- For the `experience-design` pack's full skill reference: [Experience Design Pack](../reference/experience-design.md)
- For `ux-writing` capability details: see the product-engineering pack's reference documentation
