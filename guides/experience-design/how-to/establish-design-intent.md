---
title: Establish design intent
summary: Derive durable principles, an aesthetic direction, and a token taxonomy before screen craft begins.
pack: experience-design
kind: how-to
order: 3
---

# Establish design intent

**Step 3 of 5 — Establish design intent**
<!-- rung: JOURNEY stage 3 -->

**What changes:** Journey evidence becomes decision rules, a grounded aesthetic direction, and a token taxonomy that constrain screen work.
<!-- rung: JOURNEY stage 3 -->

**What you need first:** Journey pains and peak moments, the target surface, and any stable persona, precedent, brand, or platform referents.
<!-- rung: design-principles and creative-direction SKILL.md -->

*Skipping costs:* Screen choices become local preferences with no shared way to resolve conflicts.
<!-- rung: JOURNEY stage 3 -->

**Concepts:**
<!-- rung: authored -->

- [The experience thread](../explanation/the-experience-thread.md) explains how principles, direction, and tokens constrain screen craft.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `design-principles` | The journey's pains and peak moments | 3–5 named principles, each grounded in a journey moment. | Optional |
| `creative-direction` | The audience and any brand or precedent referents | Named emotional and brand goals grounded in stable referents. | Required |
| `design-system` | The approved aesthetic direction | Primitive and semantic tokens derived from the aesthetic direction. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<output_dir>` is the design output directory
this pack is configured to write to, and `<slug>` is the short name you give
this piece of work.

<!-- rung: packs/experience-design/JOURNEY.md -->

## Run `design-principles` — 3–5 decision rules

**You type:**
<!-- rung: design-principles SKILL.md -->

```
Turn these journey pains and peak moments into three to five design principles.
```

**Agent returns:**
<!-- rung: design-principles SKILL.md -->

> **Agent:** Done — I've written named, ranked decision rules with rationale, arbitration tests, and known trade-offs to `docs/design/principles/<slug>.md`.

**You push back:**
<!-- rung: design-principles SKILL.md -->

> **You:** ‘Be trustworthy’ is a brand value, not a rule that distinguishes two screen choices. Derive a testable principle from the setup failure moment.
>
> **Agent:** I replaced it with a product-specific rule and an opposing case.

**Output varies** with the journey’s peak moments, highest-opportunity pains, and recurring disputes.
<!-- rung: design-principles SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 3 -->

**Check (testable):** Apply each principle to two plausible screen choices; this surfaces slogans and universal heuristics that cannot decide between them.
<!-- rung: design-principles SKILL.md -->

**Watch out for:** A polished principle set may be generic everywhere. Notice brand values, copied heuristics, or more than five rules; replace them with a smaller ranked set grounded in this journey.
<!-- rung: design-principles SKILL.md -->

**Where it lands:** `docs/design/principles/<slug>.md`, with `<slug>` replaced for this product.
<!-- rung: design-principles SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# <Principle title>

## Known tradeoffs
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Run `creative-direction` — the aesthetic direction

**You type:**
<!-- rung: JOURNEY stage 3 -->

```
Set a visual direction for this surface from its audience, persona, precedents, and platform conventions.
```

**Agent returns:**
<!-- rung: JOURNEY stage 3 -->

> **Agent:** Done — I've written a named, ranked aesthetic direction grounded in stable referents to `<output_dir>/aesthetic/<slug>.md`.

**You push back:**
<!-- rung: creative-direction SKILL.md -->

> **You:** ‘Clean and modern’ could describe any product. Ground each goal in a named audience need or precedent quality, rank them, and say what you are not borrowing.
>
> **Agent:** I replaced the generic direction with specific, bounded goals.

**Output varies** with the audience, referents, target surface, and genre.
<!-- rung: creative-direction SKILL.md -->

**You decide:** Approve a specific aesthetic direction before screen design begins. This is the pack's `approve-aesthetic-direction` gate, and it covers the token set below too — one decision, not two.
<!-- rung: JOURNEY stage 3 -->

**Check (grounded):** Ask what persona, precedent quality, standard, or platform convention supports each goal; this surfaces fresh opinion presented as direction.
<!-- rung: creative-direction SKILL.md -->

**Watch out for:** Confident aesthetic language can conceal guesses. Notice goals with no referent and lines borrowed from a general genre pattern; argue with those first, and reject any direction that conflicts with the quality floor.
<!-- rung: creative-direction SKILL.md -->

**Where it lands:** `<output_dir>/aesthetic/<slug>.md`.
<!-- rung: authored; creative-direction SKILL.md declares the record but not its path -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md -->

```markdown
# Aesthetic direction: <surface or product name>

<!--
  Copied into your repo by the `creative-direction` skill. Fill the angle-
  bracket prompts and delete this comment. This doc names *direction* — the
  emotional and brand goals the build steers by. It holds NO palette, font,
  or values; those are derived later by `design-system`. Keep it
  short enough that a non-designer reads it in two minutes.
-->

## Surface

<!-- The target platform for this direction. One of:
     responsive-web | iOS | Android | cross-platform
     This changes which platform standards ground each goal. -->

**Target surface:** <responsive-web | iOS | Android | cross-platform>

## Named goals (ranked)

<!-- 3–5 goals, each a noun phrase a non-designer can recall. Ranked: #1 is
     the dominant goal that wins when goals conflict. Each goal lists what
     grounds it — persona, precedent, standards, and platform conventions.
     A goal with no stable referent is still a fresh opinion; ground it first. -->

1. <dominant goal — e.g. "Quiet confidence">
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Run `design-system` — the token set

**You type:**
<!-- rung: JOURNEY stage 3 -->

```
Derive the semantic token and scale taxonomy from the approved aesthetic direction.
```

**Agent returns:**
<!-- rung: JOURNEY stage 3 -->

> **Agent:** Done — I've written a semantic token and scale taxonomy whose roles trace to the approved direction to `<output_dir>/aesthetic/<slug>-tokens.md`.

**You push back:**
<!-- rung: design-system SKILL.md -->

> **You:** The accent color appears as an isolated value with no semantic role. Replace it with a role derived from the direction, and keep implementation values out of this taxonomy.
>
> **Agent:** I repaired the role and its rationale.

**Output varies** with the direction’s named goals, surface needs, and accessibility constraints.
<!-- rung: design-system SKILL.md -->

**You decide:** The same `approve-aesthetic-direction` gate as above closes here, once the token roles trace to the direction you approved.
<!-- rung: JOURNEY stage 3 -->

**Check (grounded):** Ask which named aesthetic goal explains each token role; this surfaces arbitrary values and roles imported from a generic system.
<!-- rung: design-system SKILL.md -->

**Watch out for:** A complete-looking taxonomy may contain roles projected from general design-system patterns. Notice any role with no direction rationale or accessibility constraint; challenge those lines first and remove unsupported tokens.
<!-- rung: design-system SKILL.md -->

**Where it lands:** `<output_dir>/aesthetic/<slug>-tokens.md`.
<!-- rung: authored; design-system SKILL.md declares the taxonomy but not its path -->

**What it looks like:**
<!-- rung: authored -->

```markdown
# Token taxonomy
## Semantic roles
## Scale rationale
## Accessibility constraints
## Composition rules
```

*Section shape only. This skill ships no output template, so the guide cannot show you real content here — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when each principle decides between two real screen choices and each token role traces to a named aesthetic goal.
<!-- rung: authored -->

Stage 3 of five, and the pack's second human gate. Nothing below this point should be re-litigating the direction.

**Next:** [Design each screen](design-each-screen.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/creative-direction/SKILL.md`
<!-- rung: authored -->
