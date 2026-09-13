---
title: "Set the direction"
summary: "Write the direction as if it already shipped, so the customer benefit has to be stated plainly."
pack: product-strategy
kind: how-to
order: 2
---

# Set the direction

**Step 2 of 3 — Set the direction**
<!-- rung: packs/product-strategy/JOURNEY.md -->

**What changes:** A strategy position becomes a concrete direction someone outside the team can read and restate.
<!-- rung: packs/product-strategy/JOURNEY.md -->

**What you need first:** An approved situation, and a product concept you can describe.
<!-- rung: authored -->

*Skipping costs:* The direction stays in internal language, and the OKR cascade derives work from something nobody agreed.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) explains why this layer sits upstream of product discovery rather than inside it.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `write-prfaq` | An approved situation and a product concept | The press release and the FAQ, written as if the thing already exists. | Required |

Prompts go into an AI agent session with this pack installed — the same session
throughout. Every artifact below commits to `docs/product/shaping/`, which is the
path downstream packs read by name, so the filenames are fixed rather than
project-specific.

<!-- rung: packs/product-strategy/JOURNEY.md -->

## Run `write-prfaq` — the direction, as if shipped

**You type:**
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

```
Write the PRFAQ for this concept — press release first, then the customer and internal FAQs.
```

**Agent returns:**
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

> **Agent:** Done — I've written a press release and both FAQs written as if the product already shipped, plus the quality-bar check to `docs/product/shaping/prfaq.md`.

**You push back:**
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

> **You:** The press release describes features. Rewrite the opening around the customer problem and what changes for them, and move the features into the FAQ.
>
> **Agent:** I rewrote the opening around the customer's problem and the change, and moved the feature detail into the customer FAQ.

**Output varies** with how well formed the concept is and how much customer evidence exists.
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

**You decide:** Approve the PRFAQ before it routes to work — the pack's `approve-prfaq` gate. This is the direction the OKR cascade will derive from.
<!-- rung: packs/product-strategy/JOURNEY.md -->

**Check (testable):** Read only the press release to someone outside the team and ask what the product does; this surfaces internal language and a benefit nobody can restate.
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

**Watch out for:** A confident press release can invent a customer quote or a number. Notice any claim that would need evidence if a journalist asked, and mark it as an assumption or remove it.
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

**Where it lands:** `docs/product/shaping/prfaq.md`.
<!-- rung: packs/product-strategy/.apm/skills/write-prfaq/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# <Headline: product name and customer benefit, one sentence>

### <Subheadline: target customer and key differentiator>

<Summary — dateline, what it is, who it is for, why it matters.>
<Problem — the customer's pain, in the customer's words.>
<Solution — what it does, and why it beats the alternative.>

> "<Leadership quote naming the strategic rationale>" — <role>

<How to get started — the customer's next action.>

> "<Customer quote — a beta customer's outcome>" — <customer, title>

## Customer FAQ

**<Q: pricing, switching cost, or how it compares to what I use today>**
<honest answer, including the trade-off>

## Internal FAQ

**<Q: riskiest assumption, hardest technical problem, success metric>**
```

*Section shape only, following Amazon's Working Backwards PR/FAQ. Its hard conventions: the press release is one page, the whole document about six, and it is written as if the product already shipped. This pack ships no template — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when someone outside the team can read the press release alone and say what the product does and for whom.
<!-- rung: authored -->

Stage 2 of three, and the pack's second gate. This is what the cascade derives from.

**Next:** [Route it to work](route-it-to-work.md).
<!-- rung: authored -->

**Go deeper:** [the `product-strategy` frameworks and artifacts reference](../reference/frameworks-and-artifacts.md) — every framework this step runs, and the artifact it commits.
<!-- rung: authored -->
