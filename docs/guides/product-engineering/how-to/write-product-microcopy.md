# How to write a product's voice and microcopy

**Use this when:** You have a shaped feature with a spec and need the actual words users read — errors, empty states, buttons, and labels — written consistently with the product's voice.
**Prerequisites:** `product-engineering` pack installed; a shaped feature with a spec; a voice chart (created once on first use of the skill and reused across all subsequent features).
**Result:** UI-state copy — errors, empty states, CTAs, and labels — that passes the content checklist and is consistent with the product's documented voice chart.

> **Diátaxis: how-to.** A goal-oriented walk through the `ux-writing`
> skill — characterizing a product's voice, then writing the recurring UI-state
> copy. For shaping the *intent* behind a feature, see the how-to
> [*Shape a feature intent*](shape-a-feature-intent.md); for the field tables, the
> reference [*Intent fields and modes*](../reference/intent-fields-and-modes.md).

You've shaped a feature down to a spec, and now it needs the actual words a user
reads — the error when something fails, the empty state before there's data, the
button that commits the action. Install the `product-engineering` pack, then:

## 1. Characterize the product's voice — once

Invoke **`ux-writing`**. The first time, it characterizes your product's
**voice** along a few axes — humor, formality, respect, enthusiasm — and records
it in a **voice chart** (the skill ships the template at
`ux-writing/assets/voice-chart-template.md`; copy it to
`docs/product/voice/<slug>.md`). Place the product on each axis with a one-line
rationale and a real sample string. Do this once and **reuse the chart** across
every feature — don't re-derive it per screen.

The key distinction: **voice is constant, tone flexes by context.** The same
product is warm in a success message and calm, plain, and blame-free in an error.
The higher the user's stress, the closer the tone moves to plain — even for a
playful product.

## 2. Write each UI state from its formula

For the copy in front of you, the skill applies the formula for that UI state:

- **Error** — *what happened, plainly* + *what to do next*, blame-free. "That code
  has expired — request a new one", never "You entered an invalid code".
- **Empty state** — *orient* (what belongs here) + *invite the first action*. Never
  a blank panel or a lone illustration.
- **Button / CTA** — *verb + object* that names the goal. "Send invite", not
  "Submit".
- **Label** — concise, keyword front-loaded, one term per concept.

Each formula ships with a before → after in
`ux-writing/references/microcopy-formulas.md`.

## 3. Run the content checklist before it ships

Before the copy lands, the skill runs the **content checklist**
(`ux-writing/references/content-checklist.md`): voice-consistent,
blame-free, actionable, concise, terminology-consistent, scannable, inclusive. Run
it deliberately on the strings that carry weight — errors, empty states, primary
buttons, destructive confirmations — and fix the misses.

---

**Not documentation prose.** This skill shapes the words *inside the product*. For
writing the *docs* about your product, the clear-prose craft lives in the
`user-guide-diataxis` pack's `new-guide` skill — a different artifact and audience.
