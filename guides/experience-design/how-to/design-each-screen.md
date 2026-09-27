---
title: Design each screen
summary: Apply the genre-aware structure pass, then design behavior for every screen and state.
pack: experience-design
kind: how-to
order: 4
---

# Design each screen

**Step 4 of 5 — Design each screen**
<!-- rung: JOURNEY stage 4 -->

**What changes:** Each screen receives a structure suited to its job and genre, followed by behavior for its states, feedback, validation, recovery, and motion.
<!-- rung: JOURNEY stage 4 -->

**What you need first:** A per-screen brief, content intent, approved design intent, and the screen’s surface genre.
<!-- rung: JOURNEY stage 4 -->

*Skipping costs:* Important states can lack settled structure or behavior, and genre assumptions can displace the screen’s actual job.
<!-- rung: JOURNEY stage 4 -->

**Concepts:**
<!-- rung: authored -->

- [The experience thread](../explanation/the-experience-thread.md) explains the quality floor and the boundary between structure and behavior.

Choose `information-architecture` for the structure pass. It applies the
general method or the matching genre method from the screen's
`surface-genre:` field. Then run `interaction-design`.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `information-architecture` | The per-screen brief and surface genre | Layout zones, information hierarchy, and genre-fit structure for one screen. | Required |
| `interaction-design` | The screen's structure and state matrix | States, transitions, and feedback patterns against WCAG 2.2 AA. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<output_dir>` is the design output directory
this pack is configured to write to, `<slug>` is the short name you give
this piece of work, and `<screen>` is the screen name as the per-screen brief names it.

<!-- rung: packs/experience-design/JOURNEY.md -->

## Run `information-architecture` — layout zones and hierarchy

**You type:**
<!-- rung: JOURNEY stage 4 -->

```
Organize this screen around its primary task, content rank, recovery paths, and wayfinding.
```

**Agent returns:**
<!-- rung: information-architecture SKILL.md -->

> **Agent:** Done — I've written a hierarchy, reading flow, disclosure plan, navigation, wayfinding, and per-state layout rationale to `<output_dir>/screens/<slug>-ia.md`.

**You push back:**
<!-- rung: information-architecture SKILL.md -->

> **You:** You designed only the default state. Add the empty, loading, and error layouts, and preserve a route back to the wider product.
>
> **Agent:** I extended the same hierarchy across those states.

**Output varies** with the screen’s job, audience, content, surface, and genre.
<!-- rung: information-architecture SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (sufficient-for-next):** Ask how the hierarchy changes in an empty or error state; this surfaces structure that works only for representative content.
<!-- rung: information-architecture SKILL.md -->

**Watch out for:** A confident layout can guess at content rank. Notice prominence with no link to the screen job or representative content; challenge those general-pattern choices first, then supply real content and re-run.
<!-- rung: information-architecture SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-ia.md`.
<!-- rung: information-architecture SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Screen framing
## Content rank
## Reading pattern
## Progressive disclosure
## Navigation and wayfinding
## Per-state layout notes
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `interaction-design` — states and behaviours

**You type:**
<!-- rung: JOURNEY stage 4 -->

```
Design the behavior for <screen>, including feedback, validation, recovery, and motion.
```

**Agent returns:**
<!-- rung: JOURNEY stage 4 -->

> **Agent:** Done — I've written the per-screen brief enriched with an in-component state machine, feedback timing, validation flow, motion rationale, and accessibility constraints to `<output_dir>/screens/<slug>/<screen>.md`.

**You push back:**
<!-- rung: interaction-design SKILL.md -->

> **You:** You routed an error to another screen and redefined the state list here. Keep cross-screen routing in `user-flow`, reference the quality floor, and design only the in-screen transition and recovery.
>
> **Agent:** I restored the boundary.

**Output varies** with the screen’s state matrix, platform, actions, and interaction constraints.
<!-- rung: interaction-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (testable):** For each action, ask what visible response occurs, what guard applies, and how recovery works; this surfaces silent transitions and behavior with no failure route.
<!-- rung: interaction-design SKILL.md -->

**Watch out for:** Motion and state-library details can make a draft look specific while leaving behavior unresolved. Notice durations, easing values, library APIs, or cross-screen routes; remove them and restate the in-component behavior and still alternative.
<!-- rung: interaction-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>/<screen>.md` — it fills the brief's `## Interaction & behavior` section and produces no file of its own.
<!-- rung: user-flow SKILL.md -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md -->

```markdown
## Interaction & behavior  (from interaction-design — referenced, enriched there)
- <feedback & timing · input/validation flow · the component state machine
  (mermaid stateDiagram-v2) · motion purpose + reduced-motion · gesture — or:
  see interaction-design enrichment>
```

*The section this skill enriches, excerpted from the per-screen brief template. Confirm the surrounding brief against what `user-flow` produced.*

## Where this leads

**Done with this step:** You can move on when every screen handles its empty, loading, error and success states, and each has both structure and behaviour.
<!-- rung: authored -->

Stage 4 of five. The next step is the last inside this pack.

**Next:** [Review independently](review-independently.md).
<!-- rung: authored -->

**Go deeper:** [the `experience-design` skill reference](../reference/experience-design.md) — every skill this step runs, with its inputs, outputs and write boundary.
<!-- rung: authored -->
