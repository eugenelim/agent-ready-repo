---
title: Design each screen
summary: Apply the general or genre-specific structure pass, then design behavior for every screen and state.
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

Choose `information-architecture` for the general structure pass, or one genre-specific structure skill. Then run `interaction-design`. A genre-specific skill replaces only the general structure pass.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `analytical-design` | The per-screen brief, genre `analytical` | Dashboard IA, widget hierarchy, and role-based views. | Choose one |
| `conversion-design` | The per-screen brief, genre `marketing` | Above-fold contract, scroll story, and social-proof architecture. | Choose one |
| `documentation-design` | The per-screen brief, genre `documentation` | Content hierarchy and navigation strategy from Diátaxis typing. | Choose one |
| `informational-design` | The per-screen brief, genre `informational` | Typographic hierarchy, reading-pattern calibration, and editorial grid. | Choose one |
| `marketplace-design` | The per-screen brief, genre `marketplace` | Listing card IA, filter and facet architecture, and the transaction bridge. | Choose one |
| `workspace-design` | The per-screen brief, genre `workspace` | Context persistence, attention zones, and interrupt design. | Choose one |
| `information-architecture` | The genre skill's output, above | Layout zones and information hierarchy for one screen. | Required |
| `interaction-design` | The screen's structure and state matrix | States, transitions, and feedback patterns against WCAG 2.2 AA. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<output_dir>` is the design output directory
this pack is configured to write to, and `<slug>` is the short name you give
this piece of work.

<!-- rung: packs/experience-design/JOURNEY.md -->

## Run `analytical-design` — dashboard structure

**You type:**
<!-- rung: analytical-design SKILL.md -->

```
Design this dashboard around the named business questions and domain model.
```

**Agent returns:**
<!-- rung: analytical-design SKILL.md -->

> **Agent:** Done — I've written a widget hierarchy, spatial layout grammar, role-based views, and per-widget state handling to `<output_dir>/screens/<slug>-analytical.md`.

**You push back:**
<!-- rung: analytical-design SKILL.md -->

> **You:** You chose charts before naming the questions they answer. Remove the orphan widgets, state three to five role-and-action questions, then rebuild the hierarchy.
>
> **Agent:** I reversed the sequence and traced each widget to a question.

**Output varies** with the business questions, roles, domain objects, and actions.
<!-- rung: analytical-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (falsifiable):** Ask which named business question each widget answers and what action follows; this surfaces widget-first design and passive data display.
<!-- rung: analytical-design SKILL.md -->

**Watch out for:** A familiar dashboard pattern can make guessed widgets look inevitable. Notice widgets with no role, question, or domain object; argue with those general-pattern choices first and remove or ground them.
<!-- rung: analytical-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-analytical.md`.
<!-- rung: authored; analytical-design SKILL.md declares the specification but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Business questions
## Domain model
## Widget hierarchy
## Spatial layout grammar
## Role-based views
## Per-widget states
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `conversion-design` — marketing-page structure

**You type:**
<!-- rung: conversion-design SKILL.md -->

```
Structure this acquisition surface around its content brief and design principles.
```

**Agent returns:**
<!-- rung: conversion-design SKILL.md -->

> **Agent:** Done — I've written a hero approach, above-fold contract, scroll story, and social-proof architecture to `<output_dir>/screens/<slug>-conversion.md`.

**You push back:**
<!-- rung: conversion-design SKILL.md -->

> **You:** The hero opens with our product and a feature list. Lead with the reader’s evidenced pain or goal, then move features to the point where they answer a reader question.
>
> **Agent:** I resequenced the surface.

**Output varies** with visitor awareness, the offer, the content brief, and available evidence.
<!-- rung: conversion-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (observable):** Ask where the visitor sees their situation and next action above the fold; this surfaces product-first structure and buried action.
<!-- rung: conversion-design SKILL.md -->

**Watch out for:** A persuasive-looking hero can invent a pain or proof claim. Notice claims not present in the brief or evidence; remove those general-pattern lines and return to the content brief.
<!-- rung: conversion-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-conversion.md`.
<!-- rung: authored; conversion-design SKILL.md declares the specification but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Hero approach
## Above-fold contract
## Scroll story
## Social-proof architecture
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `documentation-design` — documentation structure

**You type:**
<!-- rung: documentation-design SKILL.md -->

```
Design the hierarchy and navigation for this documentation surface and its reader goal.
```

**Agent returns:**
<!-- rung: documentation-design SKILL.md -->

> **Agent:** Done — I've written a content hierarchy, navigation strategy, reading route, and documentation architecture to `<output_dir>/screens/<slug>-documentation.md`.

**You push back:**
<!-- rung: documentation-design SKILL.md -->

> **You:** You mixed tutorial steps into the reference path. Separate the page types, then give the reader a visible route between them.
>
> **Agent:** I corrected the architecture around reader posture.

**Output varies** with the reading goal, content types, entry routes, and documentation set.
<!-- rung: documentation-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (sufficient-for-next):** Ask how a reader arriving from search reaches the right page type and exits to the product; this surfaces missing wayfinding and mixed content contracts.
<!-- rung: documentation-design SKILL.md -->

**Watch out for:** A tidy tree can still reflect the author’s organization rather than reader goals. Notice category labels that do not answer a reader question; replace them with task or content-type routes.
<!-- rung: documentation-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-documentation.md`.
<!-- rung: authored; documentation-design SKILL.md declares the specification but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Content hierarchy
## Navigation strategy
## Reading goal
## Documentation architecture
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `informational-design` — editorial structure

**You type:**
<!-- rung: informational-design SKILL.md -->

```
Design the reading hierarchy and editorial grid for this informational surface.
```

**Agent returns:**
<!-- rung: informational-design SKILL.md -->

> **Agent:** Done — I've written a typographic hierarchy, calibrated reading pattern, editorial grid, and onward reading route to `<output_dir>/screens/<slug>-informational.md`.

**You push back:**
<!-- rung: informational-design SKILL.md -->

> **You:** The grid treats every section as equal, but readers scan for the reported finding first. Re-rank the hierarchy around that reading goal.
>
> **Agent:** I changed the typographic emphasis and sequence.

**Output varies** with the editorial structure, content length, and reader goal.
<!-- rung: informational-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (observable):** Ask a reader to locate the primary finding and the next relevant item; this surfaces hierarchy that does not support the intended scan.
<!-- rung: informational-design SKILL.md -->

**Watch out for:** An editorial grid can be visually coherent but unsupported by real content. Notice repeated placeholder-sized blocks or equal emphasis; supply a representative section and re-run.
<!-- rung: informational-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-informational.md`.
<!-- rung: authored; informational-design SKILL.md declares the specification but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Typographic hierarchy
## Reading-pattern calibration
## Editorial grid
## What’s next
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `marketplace-design` — marketplace structure

**You type:**
<!-- rung: marketplace-design SKILL.md -->

```
Design the listing, filter, comparison, and transaction structure for this marketplace surface.
```

**Agent returns:**
<!-- rung: marketplace-design SKILL.md -->

> **Agent:** Done — I've written listing-card hierarchy, filter architecture, comparison affordances, and a transaction bridge to `<output_dir>/screens/<slug>-marketplace.md`.

**You push back:**
<!-- rung: marketplace-design SKILL.md -->

> **You:** A buyer must open every card to see the deciding attribute, and zero results has no recovery. Move qualification data onto the card and add clear-filter or partial-match routes.
>
> **Agent:** I repaired both browse and failure states.

**Output varies** with buyer behavior, the listing model, and whether discovery is browse-first or search-first.
<!-- rung: marketplace-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (grounded):** Ask which buyer criterion justifies each card field and facet; this surfaces decoration and filters unrelated to a real decision.
<!-- rung: marketplace-design SKILL.md -->

**Watch out for:** Card density can look deliberate while assuming the wrong discovery mode. Notice browse-first pages shaped like dense search results, or zero results with no explanation; correct the mode or recovery route.
<!-- rung: marketplace-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-marketplace.md`.
<!-- rung: authored; marketplace-design SKILL.md declares the specification but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Listing card IA
## Filter and facet architecture
## Comparison affordances
## Transaction bridge
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `workspace-design` — workspace structure

**You type:**
<!-- rung: workspace-design SKILL.md -->

```
Design the context, attention, and interruption structure for this workspace surface.
```

**Agent returns:**
<!-- rung: workspace-design SKILL.md -->

> **Agent:** Done — I've written a session arc, context-persistence architecture, attention zones, and interrupt design to `<output_dir>/screens/<slug>-workspace.md`.

**You push back:**
<!-- rung: workspace-design SKILL.md -->

> **You:** The draft preserves the open document but loses the active task and selection when the user returns. Carry all three through the session arc.
>
> **Agent:** I added the missing working context.

**Output varies** with the session arc, collaboration model, roles, and interruption cost.
<!-- rung: workspace-design SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 4 -->

**Check (observable):** Ask a returning user to identify prior context and the active task; this surfaces state that was visible only in the previous session.
<!-- rung: workspace-design SKILL.md -->

**Watch out for:** A plausible workspace layout can guess which context deserves persistence. Notice zones or interrupts with no session evidence; challenge those general-pattern choices first and provide a real return scenario.
<!-- rung: workspace-design SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-workspace.md`.
<!-- rung: authored; workspace-design SKILL.md declares the specification but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Session arc
## Context-persistence architecture
## Attention zones
## Interrupt design
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

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
<!-- rung: authored; information-architecture SKILL.md declares the record but not its path -->

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

> **Agent:** Done — I've written the per-screen brief enriched with an in-component state machine, feedback timing, validation flow, motion rationale, and accessibility constraints to `<output_dir>/screens/<slug>.md`.

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

**Where it lands:** `<output_dir>/screens/<slug>.md`.
<!-- rung: authored; interaction-design SKILL.md declares the behavior enrichment but not its output path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# States and transitions
## Feedback and validation
## Motion and reduced-motion
## Navigation behavior
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when every screen handles its empty, loading, error and success states, and each has both structure and behaviour.
<!-- rung: authored -->

Stage 4 of five. The next step is the last inside this pack.

**Next:** [Review independently](review-independently.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/interaction-design/SKILL.md`
<!-- rung: authored -->
