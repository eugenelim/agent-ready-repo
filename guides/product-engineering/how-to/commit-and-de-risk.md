---
title: "Commit and de-risk"
summary: "Place the bet with its falsifying signal, then rank what could make it wrong."
pack: product-engineering
kind: how-to
order: 3
---

# Commit and de-risk

**Step 3 of 4 — Commit and de-risk**
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What changes:** A selected candidate becomes a stated bet with the assumptions it rests on and a plan to test them.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**What you need first:** A selected candidate and the constraints you confirmed.
<!-- rung: authored -->

*Skipping costs:* The bet cannot be lost, only extended, and the riskiest assumption is discovered late.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The discovery loop](../explanation/the-discovery-loop.md) explains how a raw idea becomes a build-ready brief.
- [The intent tree](../explanation/the-intent-tree.md) explains why a vision, a strategy, a capability and a feature are the same shape at different levels.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `place-bet` | A selected candidate | The bet, what it assumes, and what would falsify it. | Required |
| `de-risk-intent` | A placed bet | The riskiest assumptions, ranked, with how to test each. | Required |
| `plan-validation` | Ranked assumptions | What to test, in what order, and what result decides what. | Optional |
| `map-capabilities` | A placed bet | The capabilities the bet requires, and which exist today. | Optional |

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

## Run `place-bet` — commit, with the reasoning

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

```
Place the bet on this candidate — what are we committing to, and what would tell us we were wrong?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

> **Agent:** Done — I've written to `<output_dir>/shaping/<slug>/bet.md` the bet, the assumptions it rests on, and the signal that would falsify it.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

> **You:** There is no falsifying signal, just success metrics. Name what we would see if this were the wrong bet.
>
> **Agent:** I added the falsifying signal and the point at which we would act on it, separate from the success metrics.

**Output varies** with how much evidence the candidate carries and how reversible the commitment is.
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

**You decide:** Approve the decision brief — the pack's `approve-decision-brief` gate, after the full lens-roster pass on the surviving candidates. This is the last point at which the bet is cheap to change.
<!-- rung: packs/product-engineering/JOURNEY.md -->

**Check (falsifiable):** Ask what observation would make you stop; this surfaces a bet with no losing condition.
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

**Watch out for:** A bet with only success metrics cannot be lost, only extended. Notice the absence of a stopping signal — that absence is the finding.
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

**Where it lands:** `<output_dir>/shaping/<slug>/bet.md`.
<!-- rung: packs/product-engineering/.apm/skills/place-bet/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/place-bet/examples/placing-a-bet.md -->

```markdown
---
type: bet
slug: batch-export-v2
date: 2026-07-21
option: Direct download with streaming
option-source: docs/product/shaping/batch-export-v2/solution-options.md
confidence: high
appetite: 3 weeks
---

# Bet: batch-export-v2

## Option chosen
Direct download with streaming — the user initiates export and receives the
file immediately via the browser, served from the CDN.

## Rationale
Provides immediate, user-controlled export with the lowest ops overhead.
Email delivery (Option A) adds async complexity the UX doesn't need; an
API-first approach (Option C) over-engineers for current usage patterns
(95th-percentile export size is under 50 MB; no downstream consumers
requiring webhooks have been identified).

```

*An excerpt of the example the skill ships. Risks accepted, assumptions, the kill condition, the next step and the `workspace.toml` transition continue below it.*

## Run `de-risk-intent` — attack the assumptions

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

```
De-risk this bet — what are the riskiest assumptions, and how would we test each cheaply?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

> **Agent:** Done — I've ranked the assumptions by risk, each with a test that would resolve it, and carried the validation hook onto the intent.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

> **You:** The riskiest assumption is ranked third because it is the hardest to test. Rank by risk, and let the test cost be a separate column.
>
> **Agent:** I re-ranked by risk alone and moved test cost into its own column, which changed what we should test first.

**Output varies** with how novel the bet is and how much of it rests on unverified belief.
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Ask which assumption, if wrong, costs the most to discover late; this surfaces a ranking sorted by convenience.
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

**Watch out for:** Assumptions get ranked by how easy they are to test rather than by risk, which puts the dangerous one last. Notice a ranking that matches test cost exactly.
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

**Where it lands:** `<output_dir>/intents/<slug>.md` — no new file; the verdict and a `validation_hook` go back onto the intent.
<!-- rung: packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md -->
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md -->

```
validation_hook:
  assumption: <the riskiest assumption, restated>
  kill_condition: <the predeclared line, in the test's own currency>
  activity: <the real-world activity that confirms or enriches it>
```

*The validation hook the skill carries onto the intent. The kill condition is stated in the test's own currency, so the result settles the bet rather than inviting another round of argument.*

## Run `plan-validation` — how we will find out

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

```
Plan the validation — what do we test first, and what result changes our mind?
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

> **Agent:** Done — I've written a validation sequence naming what each test would settle and what result would change the decision into the loop's `validation-plan` slot.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

> **You:** Each test says what we will learn but not what we will do about it. State the decision each result triggers.
>
> **Agent:** I added the triggered decision for each outcome, and one test turned out to change nothing either way, so I cut it.

**Output varies** with how testable the assumptions are and what access to users you have.
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (sufficient-for-next):** Ask what decision each result triggers; this surfaces tests that produce interesting information and no decision.
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

**Watch out for:** A test whose outcomes both lead to the same action is not a test. Notice any step with no branching consequence.
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

**Where it lands:** `<discovery_dir>/<initiative>/_state/` — the `validation-plan` slot, plus a `validation_status` and `validation_hook` on each plan-tree node.
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/references/agentbundle-layout.md -->
<!-- rung: packs/product-engineering/.apm/skills/plan-validation/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/discovery-loop/references/sidecar-schema.md -->

```markdown
- **`validation-plan`** — the assumption → kill-condition → real-world-activity
  ledger `plan-validation` produces. Each entry `{assumption, kill_condition,
  activity, validation_status}` where `validation_status ∈ hypothesis →
  validating → validated | refuted`. This makes *converged ≠ validated* a
  **structural property** of the workspace.
```

*The slot's declared shape. Each entry pairs an assumption with the condition that would kill it and the activity that settles it, and `validation_status` is what keeps converged and validated apart.*

## Run `map-capabilities` — what we must be able to do

**You type:**
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

```
Map the capabilities this bet requires, and mark which ones we already have.
```

**Agent returns:**
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

> **Agent:** Done — I've written a capability map with each capability's current state to `<output_dir>/shaping/<slug>/capability-map.md`.

**You push back:**
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

> **You:** Everything is marked partial. Say what would have to be true for each to count as present, then re-mark.
>
> **Agent:** I defined the bar for each, and three moved to absent once there was a bar to fail.

**Output varies** with how much of the product exists and how well current capability is understood.
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (observable):** Ask what evidence shows a capability is present; this surfaces optimism about what already works.
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

**Watch out for:** "Partial" is where uncertainty hides. Notice a map with no absent capabilities — the bet would not be a bet if we could already do all of it.
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

**Where it lands:** `<output_dir>/shaping/<slug>/capability-map.md`.
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/SKILL.md -->

**What it looks like:**
<!-- rung: packs/product-engineering/.apm/skills/map-capabilities/assets/capability-map-template.md -->

```markdown
---
type: capability-map
slug: <slug>
date: <YYYY-MM-DD>
bet-source: <path/to/bet.md>
vision: <1–2 sentence product vision>
---

# Capability Map: <initiative name>

## Disposition vocabulary

| Term | Definition |
|------|-----------|
| **Build** | Internal development; team owns full lifecycle; Genesis or Custom-built stage; core to competitive differentiation. |
| **Buy** | Commercial licence or SaaS subscription; Product or Commodity stage; standard function not worth building. |
| **Partner** | Co-developed with an external partner or contract firm; mid-maturity; external expertise accelerates delivery under shared governance. |
| **Adopt** | Open-source or open-standard solution; minimal customisation required. Distinct from Buy: no licence cost, but carries an ongoing maintenance obligation. |
```

*The agent replaces every `<…>`. This is the template the skill writes from; the artifact continues in the same shape.*

## Where this leads

**Done with this step:** You can move on when the bet names what would tell you it was wrong, and by when.
<!-- rung: authored -->

Stage 3 of four, and the pack's third gate.

**Next:** [Hand it to build](hand-it-to-build.md).
<!-- rung: authored -->

**Go deeper:** [the `product-engineering` intent-fields reference](../reference/intent-fields-and-modes.md) — the fields, modes and projection profiles these skills read and write.
<!-- rung: authored -->
