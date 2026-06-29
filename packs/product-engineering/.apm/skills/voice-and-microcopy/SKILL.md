---
name: voice-and-microcopy
description: Use when shaping the actual words a user reads in a product's UI — characterizing the product's voice, writing the recurring UI-state microcopy (error, empty, button, label), or reviewing copy before it ships. Triggers on "what should this error say", "write the empty-state copy", "name this button", "characterize our product voice", "make this microcopy blame-free", "review this copy". Characterizes voice along a few axes, writes each UI state from a blame-free + actionable formula, and runs a content checklist. When a screen flow and per-screen state matrix are present (from `experience`'s `map-screen-flow`), writes copy per screen × state keyed to the matrix; when absent, behaves as today. Do NOT use to frame the intent behind the feature (use `frame-intent`), to make visual or layout design decisions (this is words only), or to write documentation prose (that is `new-guide`'s clear-prose craft).
---

# Skill: voice-and-microcopy

Shape product intent into the **words a user reads** in the UI. The pack frames,
de-risks, and decomposes intent into shippable features; this skill writes the
copy those features render. The method is three moves: **characterize the voice**
along a few axes, **write each UI state** from a blame-free, actionable formula,
and **run a content checklist** before the copy ships. It is a method, not a word
bank — framework-agnostic, and it never mandates a schema. The voice axes are in
`references/voice-axes.md`, the per-state formulas in
`references/microcopy-formulas.md`, the checklist in `references/content-checklist.md`.

When a **per-screen state matrix** from `experience`'s `map-screen-flow` is
present, this skill writes copy **per screen × state** — one copy entry per
screen/state cell in the matrix — and keys every string to the matrix row. When
the matrix is absent the skill is still fully useful: it writes copy for the
states you name directly (detect-and-degrade; no screen flow required).

> **Design-seat pairing.** This skill is the content layer of the design seat;
> the design methods and screen-flow artifacts live in the `experience` pack. See
> the `experience` pack's `map-screen-flow` skill for the per-screen state matrix
> this skill can consume.

## When to invoke

Before writing, confirm:

1. The ask is about the **words users read**, not the *intent* behind the feature
   (route to `frame-intent`) and not visual or layout design (out of scope — this
   skill shapes text only).
2. There is a real **UI surface with copy** to write or review — an error, an
   empty state, a button, a label, or a screen full of them. If there's no
   user-facing text yet, there's nothing to shape; say so.

## Procedure

1. **Characterize the voice — once per product, then reuse.** Place the product
   on a few axes (humor, formality, respect, enthusiasm) and record it in a
   **voice chart** — copy `assets/voice-chart-template.md` to
   `docs/product/voice/<slug>.md`. If a chart already exists, **reuse it**; don't
   re-derive. Voice is **constant**; **tone flexes by context** — the same
   product is calm and plain in an error, warmer in a success. See
   `references/voice-axes.md`. A half-filled chart is normal input — offer a
   default, don't block.

2. **Write each UI state from its formula.** Identify the state and apply its
   shape (`references/microcopy-formulas.md`):
   - **Error** — *what happened, plainly* + *what to do next*. **Blame-free**:
     describe the situation, never fault the user ("That code has expired —
     request a new one", not "You entered an invalid code").
   - **Empty state** — *orient* (what belongs here) + *invite the first action*.
     Never a decorative dead end.
   - **Button / CTA** — *verb + object* matching the user's goal ("Send invite",
     not "Submit" / "OK").
   - **Label** — concise, scannable, front-loaded keyword; one term per concept.

   **When a per-screen state matrix is present** (produced by `map-screen-flow`
   in the `experience` pack): write copy **per screen × state**. For each screen
   in the matrix, write one copy entry per applicable state (empty / loading /
   error / success / partial / disabled / permission-denied), applying the
   formula above. Key each entry to its matrix cell — screen name + state name —
   so the output maps directly back to the matrix. States that don't apply to a
   given screen are skipped; don't pad.

   **When no matrix is present** (standalone use): name the states yourself and
   write copy for each, as above. The skill is fully useful without a screen flow.

3. **Run the content checklist before it ships** (`references/content-checklist.md`):
   voice-consistent, blame-free, actionable, concise, and
   terminology-consistent. Run it on any string before it lands; fix the misses.

## Anti-patterns to refuse

- **Blaming the user.** "You entered the wrong password" faults the reader;
  "That password didn't match — try again or reset it" states the situation and
  the next step. Error copy is blame-free, full stop.
- **Dead-end copy.** An error or empty state that names the problem but not the
  next action strands the user. Every dead end gets a way forward.
- **Cleverness over clarity.** A joke that costs a beat of comprehension fails —
  voice serves the user, not the writer. Wit is welcome only when it doesn't slow
  the read.
- **Ignoring emotional context.** A playful product is still calm and plain when
  a payment fails. Voice is constant; tone flexes — don't joke in a crisis.
- **Writing copy with no voice characterized.** Without a chart, terminology and
  formality drift string to string. Characterize first, or reuse the chart.
- **Mandating the chart as a schema.** The voice chart is a prompt sheet; a
  half-filled one is fine. Blocking on empty fields is the failure mode.
- **Restating the docs-prose craft.** Clear-prose rules for *documentation* live
  in `new-guide`'s `clear-prose.md`; cross-reference shared items, don't fork them.
