---
title: Establish design intent
summary: Derive durable principles, an aesthetic direction, and a resolved design system before screen craft begins.
pack: experience-design
kind: how-to
---

# Establish design intent

Turn journey evidence into decision rules, a grounded aesthetic direction, and a resolved design system that constrain screen work. You need the journey's pains and peak moments, the target surface, and any stable persona, precedent, brand, or platform referents, with the `experience-design` pack [installed](../../_shared/how-to/install-packs.md). Skipping this step leaves screen choices as local preferences with no shared way to resolve conflicts; [the experience thread](../explanation/the-experience-thread.md) explains how principles, direction, and tokens constrain screen craft.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `design-principles` | The journey's pains and peak moments | 3–5 named principles, each grounded in a journey moment. | Optional |
| `creative-direction` | The target surface and whatever evidence you have | A product-specific visual direction. | Required |
| `design-system` | The approved direction, plus any system the product already has | A project-specific design system. | Conditional |

Prompts go into one agent session with this pack installed. `<output_dir>` is the design output directory the pack writes to, and `<slug>` is the short name you give this piece of work.

Run `design-system` when a direction exists and neither a completed design system
nor a coherent incumbent system supplies every concrete value the surface needs.
It remains optional when an incumbent system that already covers the work is in
place.

## Write the design principles

Ask for three to five decision rules grounded in the journey:

```text
Turn these journey pains and peak moments into three to five design principles.
```

The agent writes ranked principles with their rationale and arbitration tests to `<output_dir>/principles/<slug>.md`. There is no decision gate at this step. Check each principle by applying it to two plausible screen choices: a principle that cannot decide between them is a slogan, so replace it with a rule grounded in a journey moment.

## Set the aesthetic direction

Ask for a direction grounded in your audience, mechanism, and proof:

```text
Set a visual direction for this surface from its audience, product mechanism,
available proof, surface genre, and any approved visual target (`visual_target: confirmed`). We have direct
answers, not an upstream product brief.
```

The agent writes the direction to `<output_dir>/direction/<slug>.md`. Approve a specific direction before screen design begins; this is the pack's `approve-aesthetic-direction` gate. Ask what audience situation, product mechanism, or precedent supports each goal, and reject a direction that could be relabeled for a category peer without changing its evidence or choices.

## Resolve the design system

Ask for the design system once a direction exists:

```text
Turn the approved aesthetic direction into the design system we can build.
```

The agent writes the system to `<output_dir>/tokens/<slug>.md`. Every role traces to a goal in the approved direction, and each value records the ranked source behind it, which the skill calls a rung. A domain no source reaches is recorded as unresolved, not guessed. The same gate closes here. Challenge any role with no direction rationale, and any set of role names whose values are left for later.

You are done when each principle decides between two real screen choices and each token role traces to a named aesthetic goal. This is stage 3 of five and the pack's second human gate; later stages should not reopen the direction.

## What this job does not do

It does not design individual screens; that is the next step. It does not invent evidence: a direction goal with no audience, mechanism, precedent, or platform referent has not passed. [The design intent reference](../reference/design-intent-reference.md) has the sample exchanges, checks, templates, routes, and operations, and [the `experience-design` skill reference](../reference/experience-design.md) lists every skill this step runs.

Next, [design each screen](map-the-customer-journey.md#design-each-screen).
