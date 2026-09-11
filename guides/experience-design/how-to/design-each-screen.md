---
title: Design each screen
summary: Apply the general or genre-specific structure pass, then design behavior for every screen and state.
pack: experience-design
kind: how-to
order: 4
---

# Design each screen

**Step 4 of 5 — Design each screen**

Use the per-screen brief with the approved direction and token taxonomy. Pick one structural pass for the screen’s genre, then design its behavior.

**You need:** a per-screen brief, content intent, and established design intent.

*Skipping costs:* the screen can lack a settled structure or behavior for important states.

**Concepts:**

- [The experience thread](../explanation/the-experience-thread.md) explains the quality floor and the difference between structure and behavior.

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

The six genre-direct skills replace `information-architecture` only. They do not replace the rest of this thread: keep the content, design-intent, and interaction work in place.

#### Run `information-architecture`

**You type:** `information-architecture` — decide what goes where, in what order, and how people stay oriented. *(Rung: JOURNEY stage 4.)*

**Agent returns:**

> **Agent:** a hierarchy, reading-flow, navigation, wayfinding, and state-layout rationale. *(Rung: SKILL.md.)*

**Output varies** with the screen’s job, audience, content, and genre. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (sufficient-for-next):** Does the hierarchy make the screen’s primary task and recovery paths understandable to an interaction pass? *(Rung: authored.)*

**If it fails:** supply representative content or the primary task and re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-ia.md`. *(Rung: authored; SKILL.md specifies the IA document but not its output path.)*

**Expect these headings:**

- `Screen framing`
- `Content rank`
- `Reading pattern`
- `Progressive disclosure`
- `Navigation and wayfinding`
- `Per-state layout notes`

*Source:* `authored` *(Rung: SKILL.md defines the written IA contents; no asset template exists.)*

#### Run `conversion-design`

**You type:** `Structure this landing page around the content brief and design principles.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** an above-fold contract, scroll story, and social-proof architecture. *(Rung: SKILL.md.)*

**Output varies** with the visitor’s awareness, offer, and evidence. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (observable):** Can a visitor’s next action be located in the resulting above-fold structure? *(Rung: authored.)*

**If it fails:** identify the uncertain visitor question and re-prompt with it. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-conversion.md`. *(Rung: authored; SKILL.md specifies the structural specification but not its output path.)*

**Expect these headings:**

- `Hero approach`
- `Above-fold contract`
- `Scroll story`
- `Social-proof architecture`

*Source:* `authored` *(Rung: SKILL.md defines the structural specification; no asset template exists.)*

#### Run `documentation-design`

**You type:** `Design the structure and navigation for this documentation surface.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** a content hierarchy, navigation strategy, and documentation architecture. *(Rung: SKILL.md.)*

**Output varies** with the reading goal, content type, and documentation set. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (sufficient-for-next):** Does the proposed navigation give the reader a clear route to the right content type? *(Rung: authored.)*

**If it fails:** state the reader’s goal and the missing navigation path, then re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-documentation.md`. *(Rung: authored; SKILL.md specifies the structural specification but not its output path.)*

**Expect these headings:**

- `Content hierarchy`
- `Navigation strategy`
- `Reading goal`
- `Documentation architecture`

*Source:* `authored` *(Rung: SKILL.md defines the structural specification; no asset template exists.)*

#### Run `marketplace-design`

**You type:** `Design the listing, filter, and transaction structure for this marketplace surface.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** listing-card hierarchy, filter architecture, and a transaction bridge. *(Rung: SKILL.md.)*

**Output varies** with buyer behavior and the listing model. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (grounded):** Does the card order reflect the buyer’s stated decision criteria? *(Rung: authored.)*

**If it fails:** name the missing decision criterion and re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-marketplace.md`. *(Rung: authored; SKILL.md specifies the structural specification but not its output path.)*

**Expect these headings:**

- `Listing card IA`
- `Filter and facet architecture`
- `Transaction bridge`

*Source:* `authored` *(Rung: SKILL.md defines the structural specification; no asset template exists.)*

#### Run `informational-design`

**You type:** `Design the reading hierarchy and editorial grid for this informational surface.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** a typographic hierarchy, reading-pattern calibration, and editorial grid. *(Rung: SKILL.md.)*

**Output varies** with the editorial structure and reader goal. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (observable):** Does the reading pattern match how the reader will scan this content? *(Rung: authored.)*

**If it fails:** provide the reading goal and a representative content section, then re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-informational.md`. *(Rung: authored; SKILL.md specifies the structural specification but not its output path.)*

**Expect these headings:**

- `Typographic hierarchy`
- `Reading-pattern calibration`
- `Editorial grid`
- `What’s next`

*Source:* `authored` *(Rung: SKILL.md defines the structural specification; no asset template exists.)*

#### Run `analytical-design`

**You type:** `Design this dashboard around the business questions and domain model.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** a widget hierarchy, spatial layout grammar, and role-based view architecture. *(Rung: SKILL.md.)*

**Output varies** with the business questions, roles, and domain model. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (falsifiable):** Can every proposed widget answer one named business question? *(Rung: authored.)*

**If it fails:** remove the unsupported widget or state the question it must answer, then re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-analytical.md`. *(Rung: authored; SKILL.md specifies the structural specification but not its output path.)*

**Expect these headings:**

- `Business questions`
- `Domain model`
- `Widget hierarchy`
- `Spatial layout grammar`
- `Role-based views`

*Source:* `authored` *(Rung: SKILL.md defines the structural specification; no asset template exists.)*

#### Run `workspace-design`

**You type:** `Design the context and attention structure for this workspace surface.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** context-persistence, attention-zone, and interrupt-design architecture. *(Rung: SKILL.md.)*

**Output varies** with the session arc and collaboration model. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (observable):** Can a returning user identify their prior working context and the active task? *(Rung: authored.)*

**If it fails:** describe the return scenario and re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-workspace.md`. *(Rung: authored; SKILL.md specifies the structural specification but not its output path.)*

**Expect these headings:**

- `Session arc`
- `Context-persistence architecture`
- `Attention zones`
- `Interrupt design`

*Source:* `authored` *(Rung: SKILL.md defines the structural specification; no asset template exists.)*

#### Run `interaction-design`

**You type:** `interaction-design [/screen]`. *(Rung: JOURNEY stage 4.)*

**Agent returns:**

> **Agent:** a screen design covering states, feedback, and motion. *(Rung: JOURNEY stage 4, separately attributed from your request.)*

**Output varies** with the screen’s state matrix, platform, and interaction constraints. *(Rung: authored.)*

**No decision gate at this step.** *(Rung: JOURNEY stage 4.)*

**Check (testable):** Can each state transition be described with a visible response and a recovery path? *(Rung: authored.)*

**If it fails:** provide the missing state or failed action and re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>.md`. *(Rung: authored; SKILL.md specifies the behavior enrichment but not its output path.)*

**Expect these headings:**

- `States and transitions`
- `Feedback and validation`
- `Motion and reduced-motion`
- `Navigation behavior`

*Source:* `authored` *(Rung: SKILL.md defines the behavior enrichment; no asset template exists.)*

**Next:** [review independently](review-independently.md). *(Rung: authored.)*
