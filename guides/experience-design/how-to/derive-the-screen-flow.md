---
title: Derive the screen flow
summary: Set content and copy intent, then derive a screen flow and per-screen briefs from the customer journey.
pack: experience-design
kind: how-to
order: 2
---

# Derive the screen flow

**Step 2 of 5 — Derive the screen flow**
<!-- rung: JOURNEY stage 2 -->

**What changes:** The journey becomes screen-level content intent, copy constraints, a sequenced flow, and briefs for every screen and state.
<!-- rung: JOURNEY stage 2 -->

**What you need first:** The journey’s key touchpoints; when a content brief or copy evidence is absent, the skills elicit it.
<!-- rung: JOURNEY stage 2 -->

*Skipping costs:* Screen structure can drift away from the customer outcome, and failure routes can remain unnamed.
<!-- rung: JOURNEY stage 2 -->

**Concepts:**
<!-- rung: authored -->

- [The experience thread](../explanation/the-experience-thread.md) distinguishes flow across screens from behavior within one screen.

## What you will run

| Skill | What it produces | Needed? |
| --- | --- | --- |
| `content-design` | A content brief: what the surface says, to whom, in what form. | Required |
| `copy-direction` | Ranked copy goals and arbitration rules for one marketing surface. | Optional |
| `tone-of-voice` | The cross-surface voice all per-surface copy decisions reference. | Optional |
| `user-flow` | The screen inventory, the state each screen handles, and the transitions. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<output_dir>` is the design output directory
this pack is configured to write to, and `<slug>` is the short name you give
this piece of work.

<!-- rung: packs/experience-design/JOURNEY.md -->

## Run `content-design` — the content brief

**You type:**
<!-- rung: content-design SKILL.md -->

```
Define what this account-setup surface should say, for whom, and to what objective.
```

**Agent returns:**
<!-- rung: content-design SKILL.md -->

> **Agent:** A content brief for this surface.

**You push back:**
<!-- rung: content-design SKILL.md -->

> “This brief covers setup, billing, and support as one surface. Keep setup here and split the other two into their own briefs.” The agent narrows the brief and records only setup’s reader, objective, and section jobs.

**Output varies** with the audience, surface type, communication mode, and intended objective.
<!-- rung: content-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (sufficient-for-next):** Ask which reader, task, and content priority should constrain the flow; this surfaces a brief that is too broad to sequence.
<!-- rung: authored -->

**Watch out for:** A finished-looking brief can hide unresolved audience priority or combine several surfaces. Notice competing section jobs or more than one primary surface, then narrow the brief or split it before continuing.
<!-- rung: content-design SKILL.md -->

**Where it lands:** `<output_dir>/content/<slug>.md`.
<!-- rung: content-design SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/content-design/assets/content-brief-template.md -->

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

## Run `copy-direction` — copy goals for one surface

**You type:**
<!-- rung: copy-direction SKILL.md -->

```
Name the ranked copy goals for this account-setup surface.
```

**Agent returns:**
<!-- rung: copy-direction SKILL.md -->

> **Agent:** Ranked per-surface copy goals, stable referents, and arbitration rules.

**You push back:**
<!-- rung: copy-direction SKILL.md -->

> “You wrote a headline instead of direction. Remove the finished copy and state the goal, its referent, and what wins when goals conflict.” The agent replaces the line with a ranked rule the later writing can apply.

**Output varies** with the surface, reader language, and available brand register.
<!-- rung: copy-direction SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (grounded):** Ask what reader language or stable referent supports each goal; this surfaces preferences presented as direction.
<!-- rung: copy-direction SKILL.md -->

**Watch out for:** Goals can sound authoritative while resting on a general copy pattern. Notice goals with no cited reader language, precedent quality, or standard; argue with those first and replace them with grounded referents.
<!-- rung: copy-direction SKILL.md -->

**Where it lands:** `<output_dir>/copy/<slug>.md`.
<!-- rung: copy-direction SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md -->

- `Copy direction: <surface name>`
- `Reader map`
- `Named copy goals (ranked)`
- `What each goal means`
- `Dominant goal`
- `Brand-register consistency`
- `Plain-language floor notes`
- `Open questions`

## Run `tone-of-voice` — the brand copy register

**You type:**
<!-- rung: tone-of-voice SKILL.md -->

```
Name the brand-level copy register for this product.
```

**Agent returns:**
<!-- rung: tone-of-voice SKILL.md -->

> **Agent:** A brand register with ranked copy goals, referents, and arbitration rules.

**You push back:**
<!-- rung: tone-of-voice SKILL.md -->

> “You made the register specific to the setup screen. Rewrite it as a cross-surface brand register and leave setup choices to `copy-direction`.” The agent removes per-surface decisions and keeps the shared register.

**Output varies** with the brand, readers, voice-of-customer evidence, and stable referents.
<!-- rung: tone-of-voice SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (testable):** Put two plausible copy choices in conflict and ask which ranked goal wins; this surfaces an unranked register that cannot arbitrate.
<!-- rung: tone-of-voice SKILL.md -->

**Watch out for:** Without voice-of-customer evidence, general-pattern goals can read like validated brand truth. Notice the “directional” marker, challenge those lines first, and supply reader language when available.
<!-- rung: tone-of-voice SKILL.md -->

**Where it lands:** `<output_dir>/copy/brand-register.md`, with `<output_dir>` replaced for this project.
<!-- rung: tone-of-voice SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/tone-of-voice/assets/tone-of-voice-template.md -->

- `Brand register: <brand or product name>`
- `Reader map`
- `Named copy goals (ranked)`
- `What each goal means`
- `Dominant goal`
- `Plain-language floor notes`
- `Open questions`

## Run `user-flow` — the screen inventory

**You type:**
<!-- rung: JOURNEY stage 2 -->

```
Turn the approved journey into screens, transitions, failure routes, and one brief per screen.
```

**Agent returns:**
<!-- rung: JOURNEY stage 2 -->

> **Agent:** A screen inventory, sequenced transitions, a state matrix, and per-screen briefs.

**You push back:**
<!-- rung: user-flow SKILL.md -->

> “The connection failure has no destination, and the service-check step happens in parallel with the progress screen. Add the failure route and show the parallel work without inventing another screen.” The agent repairs the whole-flow walk and affected brief.

**Output varies** with the journey, surface, navigation model, and genre.
<!-- rung: user-flow SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 2 -->

**Check (observable):** Walk every action, including one failure, to a named screen or state; this surfaces dead ends, orphan screens, and missing recovery routes.
<!-- rung: user-flow SKILL.md -->

**Watch out for:** A complete inventory is not a complete flow. Notice transitions with no destination, briefs with no journey action, or a confident happy path that omits errors; re-run with the failing action and required destination.
<!-- rung: user-flow SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-flow.md` and `<output_dir>/screens/<slug>/<screen>.md`; replace each bracketed segment.
<!-- rung: user-flow SKILL.md -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md -->

- Per-screen brief — the unit `user-flow` emits per screen
- `Template`
- `Screen brief: <screen-name> · <product-slug> · surface: <responsive-web | iOS | Android | cross-platform>`
- `Place in the whole`
- `Job`
- `States (defer to the shared quality floor — name which apply)`
- `Data & actions (each action names its backing service)`
- `Interaction & behavior (from interaction-design — referenced, enriched there)`
- `Copy (from ux-writing; per state)`
- `Shared contract — REFERENCE, do not restate`
- `Consistency invariants`
- `Done`
- `Genre-specific notes`
- `How it fits the flow`

## Where this leads

**Next:** [Establish design intent](establish-design-intent.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/user-flow/SKILL.md`
<!-- rung: authored -->
