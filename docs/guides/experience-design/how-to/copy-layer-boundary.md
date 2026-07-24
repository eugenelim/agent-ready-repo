# The three-way copy boundary: copy-direction, voice-and-microcopy, and content-design

**Use this when:** You need to decide which copy skill to run on a new task — and the task is somewhere in the space of "what should this say and how should it sound."
**Prerequisites:** `experience-design` pack installed.
**Result:** clarity on which skill to invoke, with no copy work handed to the wrong layer.

> **How-to** — task-oriented. Pick the right skill for your copy task.
> For *why* the thread is shaped this way, read [The experience thread](../explanation/the-experience-thread.md).

## The three layers

Three skills divide the copy work in the experience-design pack:

| Layer | Skill | What it produces | When to use it |
|---|---|---|---|
| Copy voice direction | `copy-direction` | Named, ranked copy goals for a specific marketing or acquisition surface, plus arbitration rules | Before writing any hero copy, positioning copy, or above-fold narrative |
| Content structure | `content-design` | A content brief — what a surface should say, in what form, to what objective | Before any wireframe or screen flow for an acquisition or reference surface |
| Per-state UI copy | `voice-and-microcopy` (product-engineering pack) | Blame-free, actionable copy for UI states: error messages, empty states, button labels, form labels | When writing the specific copy for product UI interactions |

## Decision tree

**Is the task about what a surface says — its sections, narrative arc, and scroll structure?**
→ Use `content-design`.

**Is the task about how a specific marketing or acquisition surface sounds — its copy voice, register, and arbitration rules?**
→ Use `copy-direction`.

**Is the task about the exact copy string for a UI state — an error message, an empty state, a label?**
→ Use `voice-and-microcopy` in the `product-engineering` pack.

## When to use `copy-direction`

Use `copy-direction` when you are about to write or brief copy for a marketing or acquisition surface and need to name the copy voice goals first:

- "What should our landing page copy sound like?"
- "How does our hero copy differ from our competitors?"
- "Before we brief the writer, what are our copy goals for the announcement?"
- "What should win when urgency conflicts with warmth on our pricing page CTA?"

`copy-direction` produces a `copy-direction.md` doc with named goals, each grounded in a stable referent (persona language, a copy precedent, a persuasion standard), plus the arbitration rules that resolve conflicts. It does NOT produce finished copy strings, formula tables, or SEO keyword targeting.

## When to use `content-design`

Use `content-design` when you do not yet know what a surface should *say* — its job, audience, narrative arc, or section structure:

- "What should this landing page say — what's the narrative arc?"
- "Help me decide the above-fold structure for our onboarding flow."
- "What does this feature help page need to communicate?"

`content-design` runs before `copy-direction` on acquisition surfaces: it names *what* the surface says (sections, jobs, audience awareness level, narrative arc); `copy-direction` names *how* it sounds.

## When to use `voice-and-microcopy`

Use `voice-and-microcopy` when writing the specific copy for a product interaction state:

- "Write the error message for when login fails."
- "What should the empty state say when there are no projects?"
- "Write the confirmation dialog copy for a destructive action."

`voice-and-microcopy` is in the `product-engineering` pack, not the `experience-design` pack. It specializes in UI state copy — copy that must be precise, blame-free, and actionable at a specific screen moment. It is not for positioning copy, above-fold narrative, or brand voice direction.

## How the layers work together

The typical sequence for an acquisition surface:

1. **`content-design`** — decides what the surface needs to say (narrative arc, section jobs, CTA, audience awareness level)
2. **`copy-direction`** — names the copy voice goals and arbitration rules (how the copy sounds, what wins when goals conflict)
3. **Writer or `voice-and-microcopy`** — writes the final copy, consulting the content brief for structure and the copy-direction doc for voice

For a product surface (help page, feature reference):
1. **`content-design`** — decides content structure (content hierarchy, user task, completion metric)
2. **`voice-and-microcopy`** — writes per-state UI copy for the interaction layer

`copy-direction` is not needed for internal product UI surfaces; it focuses on marketing and acquisition copy voice.

## Common mistakes

**Running `voice-and-microcopy` for marketing copy.** `voice-and-microcopy` is designed for UI states: precise, brief, actionable strings for specific moments. Marketing copy needs voice direction first (`copy-direction`) and structural direction (`content-design`); applying `voice-and-microcopy` patterns produces copy that is accurate but inert — it passes the checklist but cannot persuade a cold reader.

**Running `content-design` without `copy-direction` for marketing surfaces.** `content-design` decides the structure; if the copy voice is not named separately, the writer defaults to generic marketing language. For above-fold surfaces, copy voice is as load-bearing as structure.

**Running `copy-direction` for product UI copy states.** `copy-direction` is for the marketing voice of a surface — its claim structure, register, and what wins when tone goals conflict. It is not designed for the precision constraints of error messages, empty states, or confirmations. Use `voice-and-microcopy` for those.

**Using `tone-of-voice` for a specific surface.** `tone-of-voice` covers general brand voice — the across-all-surfaces register. For a specific marketing surface where copy voice goals and arbitration rules matter, use `copy-direction`; it is surface-specific and produces the per-surface arbitration rules the build needs.
