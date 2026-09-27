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
throughout. In the paths below, `<slug>` is this piece of work's short
kebab-case name, fixed at step 1 so every later artifact traces back to it; `<initiative>` is the discovery initiative's kebab-case directory slug; `<output_dir>` is
where this repository keeps product artifacts, and the agent asks when it is
not configured; `<discovery_dir>` is where the discovery loop keeps its
initiative directories, defaulting to `docs/discovery/`. The agent tells you
which path it wrote to.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md -->
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/references/agentbundle-layout.md -->

<!-- rung: packs/product-engineering/JOURNEY.md -->

## Run `identify-opportunities` — where the value is

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

```
Identify the opportunities in this situation and assess each one.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md -->

> **Agent:** Done — I've written an opportunity assessment with each opportunity's value and the confidence behind it to `<output_dir>/shaping/<slug>/opportunity-assessment.md`.

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

**Where it lands:** `<output_dir>/shaping/<slug>/opportunity-assessment.md`.
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

> **Agent:** Done — I've written to `<output_dir>/shaping/<slug>/solution-options.md` several candidate approaches that differ structurally rather than cosmetically.

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

**Where it lands:** `<output_dir>/shaping/<slug>/solution-options.md`.
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md -->

```markdown
---
type: solution-options
slug: pe-shaping-memory
opportunity: "PEs spend 60–80% of shaping time re-explaining context to agents at each session start, with no durable per-initiative memory of prior framing decisions."
date: 2026-07-21
recommendation: Workspace.toml shaping section
---

# Solution Options: pe-shaping-memory

## Opportunity

PEs spend 60–80% of shaping time re-explaining context to agents at each session
start, with no durable per-initiative memory of prior framing decisions.

## Options

### Option A: Structured shaping log

**Approach:** PEs maintain a freeform markdown journal per initiative. Agents
read it at session start.
**Key bets:**
- PEs will consistently update the log after sessions.
- Freeform prose is retrieval-friendly enough for agent context surfacing.
**Trade-offs:** Lowest tooling investment; highest maintenance burden. Drift-prone
under pressure. No staleness signal.
**Status:** parked
```

*An excerpt of the example the skill ships. The remaining options, the recommendation, the residual bets and the `workspace.toml` suggestion continue in the same shape.*

## Run `explore-options` — test them against reality

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

```
Explore these candidates against our real constraints and tell me which survive.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

> **Agent:** Done — I've recorded each candidate examined against the constraints, with the ones that do not survive named and why, onto the loop's plan tree.

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

**Where it lands:** `<discovery_dir>/<initiative>/_state/plan-tree.json` — the candidate set and the selection go onto the plan-tree node.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/references/agentbundle-layout.md -->
<!-- rung: packs/product-engineering/.apm/skills/explore-options/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/assets/plan-tree.md -->

```json
{
  "id": "intent:cap.household-coordination",
  "type": "intent",
  "altitude": "capability",
  "parent_id": "intent:vision",
  "lifecycle": "diverging",
  "validation_status": "hypothesis",
  "round": 1,
  "round_cap": 12,
  "cost_spent": 0.8,
  "candidates": [
    {"id": "cand.kitchen-draft-approve", "altitude": "narrow-slice", "mechanic": "draft-and-approve", "riskiest_assumption": "users want approval-gated drafting", "status": "rejected", "rationale": "myopic — misses whole-household altitude"},
    {"id": "cand.whole-household-coord", "altitude": "whole-domain", "mechanic": "coordination-layer", "riskiest_assumption": "one assistant can span calendar+travel+budget", "status": "selected"}
  ],
  "selection": "cand.whole-household-coord",
  "validation_hook": {
    "assumption": "a household will delegate cross-domain coordination to one assistant",
    "kill_condition": "<3/8 pilot households delegate beyond one domain",
    "activity": "diary study + Wizard-of-Oz coordination pilot"
  }
}
```

*A divergence node, excerpted from the plan-tree template. This step fills `candidates` and `selection` — each candidate with its own riskiest assumption, a status, and a rationale on the rejected ones. The `validation_hook` shown here is filled later, at step 3; yours will still be `null`.*

## Where this leads

**Done with this step:** You can move on when every eliminated candidate names a confirmed constraint that eliminated it.
<!-- rung: authored -->

Stage 2 of four, and the pack's second gate. What you eliminate matters as much as what you keep.

**Next:** [Commit and de-risk](commit-and-de-risk.md).
<!-- rung: authored -->

**Go deeper:** [the `product-engineering` intent-fields reference](../reference/intent-fields-and-modes.md) — the fields, modes and projection profiles these skills read and write.
<!-- rung: authored -->
