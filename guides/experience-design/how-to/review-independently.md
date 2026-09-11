---
title: Review independently
summary: Run the authoring-time design review before an independent, read-only review of the completed design set.
pack: experience-design
kind: how-to
order: 5
---

# Review independently

**Step 5 of 5 — Review independently**

Review the completed design work against its principles, quality floor, and concrete user task. Then request the independent reviewer described by the journey.

**You need:** a screen, flow, or design set and the user task it serves.

*Skipping costs:* unresolved state, accessibility, or coherence gaps can enter build planning.

**Concepts:**

- [The experience thread](../explanation/the-experience-thread.md) explains the quality floor and why the independent reviewer reads artifacts cold.

#### Run `design-review`

**You type:** `Review this screen against the quality floor, heuristics, and grounded direction.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** severity-rated findings tied to a principle, floor commitment, heuristic, or grounded aesthetic goal. *(Rung: SKILL.md.)*

**Output varies** with the screen, its genre, and the evidence available for review. *(Rung: authored.)*

**You decide:** act on blockers before design proceeds to build planning. *(Rung: JOURNEY stage 5.)*

**Check (falsifiable):** Can each finding name what was observed and the rule or commitment it violates? *(Rung: authored.)*

**If it fails:** supply the screen state, user task, or missing design artifact and re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/screens/<slug>-review.md`. *(Rung: authored; SKILL.md specifies the review record but not its output path.)*

**Expect these headings:**

- `Review scope`
- `Findings by severity`
- `Quality-floor findings`
- `Heuristic findings`
- `Genre-rubric findings`
- `Taste findings`
- `Director’s notes`

*Source:* `authored` *(Rung: SKILL.md defines the review record; no asset template exists.)*

The journey then calls `experience-reviewer`, the independently run, read-only reviewer. It returns findings rather than changing artifacts; act on its blockers before design feeds the build loop. *(Rung: JOURNEY stage 5.)*

**Next:** continue with the build workflow after the independent findings are resolved. *(Rung: authored.)*
