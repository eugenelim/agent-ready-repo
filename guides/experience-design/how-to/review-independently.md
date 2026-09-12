---
title: Review independently
summary: Run the authoring-time design review before an independent, read-only review of the completed design set.
pack: experience-design
kind: how-to
order: 5
---

# Review independently

**Step 5 of 5 — Review independently**
<!-- rung: JOURNEY stage 5 -->

**What changes:** The completed design set is checked against its principles, quality floor, user task, and grounded direction before it enters build planning.
<!-- rung: JOURNEY stage 5 -->

**What you need first:** The screen, flow, or design set; the user task it serves; its principles; and its grounded aesthetic direction.
<!-- rung: design-review SKILL.md -->

*Skipping costs:* Missing states, accessibility failures, and cross-screen inconsistencies can enter build planning as untested assumptions.
<!-- rung: JOURNEY stage 5 -->

**Concepts:**
<!-- rung: authored -->

- [The experience thread](../explanation/the-experience-thread.md) explains the quality floor and why the independent reviewer reads artifacts cold.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `design-review` | The finished screens, plus the principles and direction | Findings against the quality floor before the independent review. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<output_dir>` is the design output directory
this pack is configured to write to, and `<slug>` is the short name you give
this piece of work.

<!-- rung: packs/experience-design/JOURNEY.md -->

## Run `design-review` — your own pass first

**You type:**
<!-- rung: design-review SKILL.md -->

```
Review this design set against its user task, principles, quality floor, genre rubric, and grounded aesthetic direction.
```

**Agent returns:**
<!-- rung: design-review SKILL.md -->

> **Agent:** Done — I've written severity-rated findings tied to observed evidence and a principle, floor commitment, heuristic, genre rule, or grounded aesthetic goal to `<output_dir>/screens/<slug>-review.md`.

**You push back:**
<!-- rung: design-review SKILL.md -->

> **You:** You called the empty state clean, but the flow says a new account has no connected source and the screen offers no recovery action. Re-review that state against the user task.
>
> **Agent:** I recorded the missing recovery as a finding and cited the observed state.

**Output varies** with the review scope, screen genre, supplied states, and grounded evidence.
<!-- rung: design-review SKILL.md -->

**You decide:** Resolve blockers before the design enters build planning, then review the independently returned findings — the pack's `review-experience-designs` gate.
<!-- rung: JOURNEY stage 5 -->

**Check (falsifiable):** Ask what was observed and which rule or commitment each finding violates; this surfaces taste presented as a defect and findings with no evidence.
<!-- rung: design-review SKILL.md -->

**Watch out for:** A uniformly confident review may be guessing where states or source artifacts are absent. Notice findings that cite no observed screen state or grounded rule; supply the missing evidence, discard unsupported taste claims, and re-run the affected scope.
<!-- rung: design-review SKILL.md -->

**Where it lands:** `<output_dir>/screens/<slug>-review.md`.
<!-- rung: authored; design-review SKILL.md declares the review record but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Review scope
## Findings by severity
## Quality-floor findings
## Heuristic findings
## Genre-rubric findings
## Taste findings
## Director’s notes
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

The journey then invokes the read-only `experience-reviewer` in an independent context. It is a reviewer role, not a skill you type. Resolve its blockers before design feeds the build loop.

## Where this leads

**Done with this step:** You are done when every blocker is resolved and the remaining findings are ones you have consciously accepted.
<!-- rung: authored -->

This closes the `experience-design` thread. The reviewed design set is the input to the build loop — where engineering picks it up.

**Next:** [P3 · Build it](../../README.md#p3--build-it--2-hours), after the independent findings are resolved.
<!-- rung: authored -->

**Go deeper:** [the `experience-design` skill reference](../reference/experience-design.md) — every skill this step runs, with its inputs, outputs and write boundary.
<!-- rung: authored -->
