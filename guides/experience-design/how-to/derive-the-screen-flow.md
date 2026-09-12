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

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `content-design` | The surface and its audience | A content brief: what the surface says, to whom, in what form. | Required |
| `tone-of-voice` | Voice-of-customer evidence, if you have it | The cross-surface voice all per-surface copy decisions reference. | Optional |
| `copy-direction` | The content brief; the brand register if it exists | Ranked copy goals and arbitration rules for one marketing surface. | Optional |
| `user-flow` | The journey map from step 1 | The screen inventory, the state each screen handles, and the transitions. | Required |

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

> **Agent:** Done — I've written a content brief for this surface to `<output_dir>/content/<slug>.md`.

**You push back:**
<!-- rung: content-design SKILL.md -->

> **You:** This brief covers setup, billing, and support as one surface. Keep setup here and split the other two into their own briefs.
>
> **Agent:** I narrowed the brief and recorded only setup’s reader, objective, and section jobs.

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

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/content-design/assets/content-brief-template.md -->

```markdown
---
type: content-brief
surface-type: <acquisition | product-or-reference>
persona: <short persona name or pointer to persona artifact>
date: <YYYY-MM-DD>
---

# Content brief: <surface name>

<!--
  Written by the `content-design` skill. Fill the angle-bracket prompts and
  delete this comment. This doc names *content direction* — what the surface
  must say, for whom, in what form, and to what objective. It does not contain
  finished copy, design values, or implementation details. Keep it short enough
  that a non-writer reads it in three minutes.

  Delete the variant sections that do not apply to this surface type.
-->

## Surface objective

**Surface type:** <acquisition | product-or-reference>

**Primary reader:** <who arrives here; role + context that brought them>

**Objective:** <the single outcome this surface must drive — one verb phrase>
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `tone-of-voice` — the brand copy register

**You type:**
<!-- rung: tone-of-voice SKILL.md -->

```
Name the brand-level copy register for this product.
```

**Agent returns:**
<!-- rung: tone-of-voice SKILL.md -->

> **Agent:** Done — I've written a brand register with ranked copy goals, referents, and arbitration rules to `<output_dir>/copy/brand-register.md`.

**You push back:**
<!-- rung: tone-of-voice SKILL.md -->

> **You:** You made the register specific to the setup screen. Rewrite it as a cross-surface brand register and leave setup choices to `copy-direction`.
>
> **Agent:** I removed per-surface decisions and kept the shared register.

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

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/tone-of-voice/assets/tone-of-voice-template.md -->

```markdown
---
type: tone-of-voice
scope: brand-level
persona: <short persona name or pointer to persona artifact>
date: <YYYY-MM-DD>
---

# Brand register: <brand or product name>

<!--
  Written by the `tone-of-voice` skill. Fill the angle-bracket prompts and
  delete this comment. This doc names the brand-level copy register — the
  cross-surface copy personality that all per-surface copy decisions reference.
  It holds NO finished copy, formula tables, or per-surface direction strings.
  Per-surface copy direction lives in copy/<surface-slug>.md (copy-direction skill).
  Keep this doc short enough that a writer picks up the brand register in two minutes.
-->

## Reader map

| Reader type | Copy JTBD sentence | Rank |
|---|---|---|
| <reader type — role + context> | When [situation], I want to [action with this copy], so that [goal]. | Primary |
| <reader type> | When [situation], I want to [action], so that [goal]. | Secondary |

## Named copy goals (ranked)
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `copy-direction` — copy goals for one surface

**You type:**
<!-- rung: copy-direction SKILL.md -->

```
Name the ranked copy goals for this account-setup surface.
```

**Agent returns:**
<!-- rung: copy-direction SKILL.md -->

> **Agent:** Done — I've written ranked per-surface copy goals, stable referents, and arbitration rules to `<output_dir>/copy/<slug>.md`.

**You push back:**
<!-- rung: copy-direction SKILL.md -->

> **You:** You wrote a headline instead of direction. Remove the finished copy and state the goal, its referent, and what wins when goals conflict.
>
> **Agent:** I replaced the line with a ranked rule the later writing can apply.

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

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md -->

```markdown
---
type: copy-direction
surface-slug: <kebab-case surface name — e.g. landing-page, pricing-page, onboarding-hero>
date: <YYYY-MM-DD>
---

# Copy direction: <surface name>

<!--
  Written by the `copy-direction` skill. Fill the angle-bracket prompts and
  delete this comment. This doc names *copy direction* for one specific surface —
  the goals and arbitration rules that steer every copy choice here. It holds NO
  finished copy, formula tables, or pre-written strings. Keep it short enough
  that a writer picks up direction in two minutes.
-->

## Reader map

| Reader type | Copy JTBD sentence | Rank |
|---|---|---|
| <reader type — role + context on this surface> | When [situation on this surface], I want to [action with this copy], so that [goal]. | Primary |
| <reader type> | When [situation], I want to [action], so that [goal]. | Secondary |

## Named copy goals (ranked)

<!-- 3–5 goals, each a noun phrase a non-designer can recall. Ranked: #1 is
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `user-flow` — the screen inventory

**You type:**
<!-- rung: JOURNEY stage 2 -->

```
Turn the approved journey into screens, transitions, failure routes, and one brief per screen.
```

**Agent returns:**
<!-- rung: JOURNEY stage 2 -->

> **Agent:** Done — I've written a screen inventory, sequenced transitions, a state matrix, and per-screen briefs to `<output_dir>/screens/<slug>-flow.md`.

**You push back:**
<!-- rung: user-flow SKILL.md -->

> **You:** The connection failure has no destination, and the service-check step happens in parallel with the progress screen. Add the failure route and show the parallel work without inventing another screen.
>
> **Agent:** I repaired the whole-flow walk and affected brief.

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

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md -->

````markdown
---
type: screen-flow-brief
screen: <screen-name>
flow: <slug>
surface: <responsive-web | iOS | Android | cross-platform>
surface-genre: <marketing | documentation | informational | analytical | transactional-journey | marketplace | workspace>
---

# Screen brief: <screen-name>   ·   <product-slug>   ·   surface: <responsive-web | iOS | Android | cross-platform>

## Place in the whole
<!-- Traceability marker. The structural-orphan lint reads this exact bold-body
     field (NOT the frontmatter `type:`) to recognize this artifact as a `screen`
     chain node — by marker, not path. Keep the value exactly `screen-brief`. -->
- **Type:** screen-brief
- Journey step(s): <which step(s) of the journey this serves>
- Enters from: <screen(s) / entry points>      Exits to: <screen(s) / next actions>
- Traces to outcome: <the outcome/JTBD this screen advances>   (traceability ↑)
- Surface genre: <genre> — determines design patterns and IA approach

## Job
<One sentence: the single job this screen does for the user.>

## States  (defer to the shared quality floor — name which apply)
````

*One of these per screen. The agent replaces every `<…>`; the shared design contract is referenced, never copied into each brief.*

## Where this leads

**Done with this step:** You can move on when every action, including at least one failure, reaches a named screen or state, and every screen has a brief.
<!-- rung: authored -->

Stage 2 of five. The briefs produced here are what every later step reads.

**Next:** [Establish design intent](establish-design-intent.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/user-flow/SKILL.md`
<!-- rung: authored -->
