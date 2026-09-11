---
title: Derive the screen flow
summary: Set content and copy intent, then derive a screen flow and per-screen briefs from the customer journey.
pack: experience-design
kind: how-to
order: 2
---

# Derive the screen flow

**Step 2 of 5 — Derive the screen flow**

Turn the journey into screen-level intent and a flow that includes normal and failure routes.

**You need:** the journey’s key touchpoints; a content brief can be elicited when absent.

*Skipping costs:* screen structure can drift away from the customer outcome.

**Concepts:**

- [The experience thread](../explanation/the-experience-thread.md) distinguishes macro flow across screens from behavior inside one screen.

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

#### Run `content-design`

**You type:** `Define what this surface should say, for whom, and to what objective.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** a content brief for the surface.
<!-- rung: SKILL.md -->

**Output varies** with the audience, surface, and intended objective.
<!-- rung: authored -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (sufficient-for-next):** Does the brief give a screen-flow author a clear reader, task, and content priority?
<!-- rung: authored -->

**If it fails:** name the missing audience or surface objective and re-prompt.
<!-- rung: authored -->

**You now hold:** `<output_dir>/content/<slug>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Content brief: <surface name>`
- `Surface objective`
- `Audience awareness level`
- `Narrative arc selection`
- `Scroll sections`
- `Above-fold structure`
- `CTAs`
- `Success metric`
- `User task`
- `Content format`
- `Content hierarchy`
- `Completion metric`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/content-design/assets/content-brief-template.md`
<!-- rung: asset template -->

#### Run `copy-direction`

**You type:** `Name the copy goals for this acquisition surface.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** ranked per-surface copy goals and arbitration rules.
<!-- rung: SKILL.md -->

**Output varies** with the surface, reader, and available brand register.
<!-- rung: authored -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (grounded):** Are the goals tied to named reader language or another stable referent?
<!-- rung: authored -->

**If it fails:** provide reader language or a referent and re-prompt.
<!-- rung: authored -->

**You now hold:** `<output_dir>/copy/<slug>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Copy direction: <surface name>`
- `Reader map`
- `Named copy goals (ranked)`
- `What each goal means`
- `Dominant goal`
- `Brand-register consistency`
- `Plain-language floor notes`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md`
<!-- rung: asset template -->

#### Run `tone-of-voice`

**You type:** `Name the brand-level copy register for this product.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** a brand register with ranked copy goals and arbitration rules.
<!-- rung: SKILL.md -->

**Output varies** with the brand, readers, and available evidence.
<!-- rung: authored -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (testable):** Can a copy conflict be resolved against the dominant goal?
<!-- rung: authored -->

**If it fails:** add a conflicting copy choice and re-prompt for arbitration.
<!-- rung: authored -->

**You now hold:** `<output_dir>/copy/brand-register.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `Brand register: <brand or product name>`
- `Reader map`
- `Named copy goals (ranked)`
- `What each goal means`
- `Dominant goal`
- `Plain-language floor notes`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/tone-of-voice/assets/tone-of-voice-template.md`
<!-- rung: asset template -->

#### Run `user-flow`

**You type:** `user-flow`.
<!-- rung: JOURNEY stage 2 -->

**Agent returns:**

> **Agent:** a screen inventory, transitions, per-screen briefs, and a state matrix.
<!-- rung: JOURNEY stage 2, separately attributed from your request -->

**Output varies** with the journey, surface, and genre.
<!-- rung: authored -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (observable):** Can you follow every transition, including an error route, to a named screen or state?
<!-- rung: authored -->

**If it fails:** give the failing action and its destination, then re-prompt.
<!-- rung: authored -->

**You now hold:** `<output_dir>/screens/<slug>-flow.md` and `<output_dir>/screens/<slug>/<screen>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- Per-screen brief — the unit `user-flow` emits per screen
- `Template`
- `Screen brief: <screen-name>   ·   <product-slug>   ·   surface: <responsive-web | iOS | Android | cross-platform>`
- `Place in the whole`
- `Job`
- `States  (defer to the shared quality floor — name which apply)`
- `Data & actions  (each action names its backing service — traceability ↓)`
- `Interaction & behavior  (from interaction-design — referenced, enriched there)`
- `Copy  (from ux-writing; per state)`
- `Shared contract — REFERENCE, do not restate`
- `Consistency invariants`
- `Done`
- `Genre-specific notes`
- `How it fits the flow`

*Source:* `../../../packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md`
<!-- rung: asset template -->

**Next:** [establish design intent](establish-design-intent.md).
<!-- rung: authored -->
