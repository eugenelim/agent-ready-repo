---
title: "Find the opportunities"
summary: "Rank where the value is, then produce approaches that differ in kind rather than in detail."
pack: product-engineering
kind: how-to
order: 2
---

# Find the opportunities

**Step 2 of 4 — Find the opportunities**
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What changes:** An approved intent becomes ranked opportunities and candidate approaches tested against real constraints.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What you need first:** An approved intent, and any evidence about users or the current system.
<!-- rung: authored -->

*Skipping costs:* The first plausible idea becomes the plan, and nothing records what else was considered.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The discovery loop](../explanation/the-discovery-loop.md) explains how a raw idea becomes a build-ready brief.
- [The intent tree](../explanation/the-intent-tree.md) explains why a vision, a strategy, a capability and a feature are the same shape at different levels.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `identify-opportunities` | A framed situation or intent | Assessed opportunities, ranked by value and confidence. | Required |
| `diverge-solutions` | A chosen opportunity | Genuinely different approaches, not variations on one. | Required |
| `explore-options` | Candidate approaches | Each candidate examined against constraints and evidence. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work, and it
stays the same from the intent through to the brief, which is how the
traceability lint follows one thread.

<!-- rung: packs/product-engineering/JOURNEY.md -->

## Run `identify-opportunities` — where the value is

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

```
Identify the opportunities in this situation and assess each one.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

> **Agent:** Done — I've written an opportunity assessment with each opportunity's value and the confidence behind it to `docs/discovery/<initiative>/opportunity-assessment.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

> **You:** Every opportunity is rated high value and high confidence. Rank them against each other and say what separates first from second.
>
> **Agent:** I ranked them and named the separator for each pair; two dropped to medium confidence once I had to say why.

**Output varies** with how much evidence exists and how well the situation is framed.
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (grounded):** Ask what evidence supports the confidence rating on the top opportunity; this surfaces confidence assigned by enthusiasm.
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

**Watch out for:** Uniform ratings mean nothing was compared. Notice a list where everything is high value — the ranking is the product, not the list.
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

**Where it lands:** `docs/discovery/<initiative>/opportunity-assessment.md`.
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/assets/opportunity-assessment-template.md -->

```markdown
---
type: opportunity-assessment
slug: <slug>
date: <YYYY-MM-DD>
source: <situation-framing | free-form>
---

# Opportunity Assessment: <topic>

> Opportunity score = importance + max(importance − satisfaction, 0)
> Ratings labelled (agent-estimated) were inferred from context rather than PE-supplied.

## Functional Jobs

Jobs users are trying to **accomplish** — the outcome, not the means.

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Run `diverge-solutions` — more than one option

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

```
Diverge on this opportunity — give me approaches that differ in kind, not in detail.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

> **Agent:** Done — I've written several candidate approaches that differ structurally rather than cosmetically. Nothing was written to disk.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

> **You:** These are three versions of the same idea. Give me one that solves it without building anything, and one that changes the process instead of the product.
>
> **Agent:** I replaced two near-duplicates with a no-build option and a process-change option.

**Output varies** with how constrained the problem is and how much solution space exists.
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (falsifiable):** Ask what each option assumes that the others do not; this surfaces variations dressed as alternatives.
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

**Watch out for:** Divergence is the step most often skipped by producing three shades of the first idea. Notice options that would be built by the same team in the same way.
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Candidates — <opportunity>

## Candidate A: <name>

- **Approach:** <how it solves the opportunity>
- **Differs by:** <what makes it structurally different from B and C>

## Candidate B: <name>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `explore-options` — test them against reality

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

```
Explore these candidates against our real constraints and tell me which survive.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

> **Agent:** Done — I've written each candidate examined against the constraints, with the ones that do not survive named and why. Nothing was written to disk.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

> **You:** You eliminated the cheapest option on a constraint we have not confirmed. Check it before ruling it out.
>
> **Agent:** I checked and the constraint does not apply as stated, so that option is back in with a note on what we confirmed.

**Output varies** with how many constraints are real and how many are assumed.
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

**You decide:** Select the candidate to carry forward — the pack's `select-candidate` gate. Eliminations are as load-bearing as the selection.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**Check (testable):** Ask which constraint eliminated each rejected option, and whether that constraint is confirmed; this surfaces eliminations resting on assumption.
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

**Watch out for:** An option eliminated on an unconfirmed constraint is eliminated for no reason. Notice rejections with no evidence behind the constraint that killed them.
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Exploration — <opportunity>

## Candidate A — <survives | eliminated>

- **Constraint tested:** <constraint> — <confirmed | assumed>
- **Result:** <what it means for this candidate>
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when every eliminated candidate names a confirmed constraint that eliminated it.
<!-- rung: authored -->

Stage 2 of four, and the pack's second gate. What you eliminate matters as much as what you keep.

**Next:** [Commit and de-risk](commit-and-de-risk.md).
<!-- rung: authored -->

**Go deeper:** [the `product-engineering` intent-fields reference](../reference/intent-fields-and-modes.md) — the fields, modes and projection profiles these skills read and write.
<!-- rung: authored -->
