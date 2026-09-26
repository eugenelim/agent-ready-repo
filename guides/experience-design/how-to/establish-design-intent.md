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

> **Agent:** Done — I've written named, ranked decision rules with rationale, arbitration tests, and known trade-offs to `<output_dir>/principles/<slug>.md`.

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

**Where it lands:** `<output_dir>/principles/<slug>.md`, with `<slug>` replaced for this product.
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

> **Agent:** Done — I've written a named, ranked aesthetic direction grounded in stable referents to `<output_dir>/direction/<slug>.md`.

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

**Where it lands:** `<output_dir>/direction/<slug>.md`.
<!-- rung: creative-direction SKILL.md -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md -->

```markdown
---
type: creative-direction
slug: "<kebab-case-slug — the surface or product this direction serves>"
# surface: the target platform this direction is for. It changes which
# platform standards ground each goal below.
surface: "<responsive-web | iOS | Android | cross-platform>"
date: "<YYYY-MM-DD>"
# status: `converge` writes `proposed` when it captures a direction the human
# has not yet confirmed — including a choice recorded as delegated — and
# `selected` once a human confirms. The `inherit` route writes no doc, so
# there is no `inherited` value.
status: "<proposed | selected>"
---

# Aesthetic direction: <surface or product name>

<!--
  Copied into your repo by the `creative-direction` skill. Fill the angle-
  bracket prompts and delete this comment. This doc names *direction* — the
  emotional and brand goals the build steers by. It holds NO palette, font,
  or values; those are derived later by `design-system`. Keep it
  short enough that a non-designer reads it in two minutes.
-->

## Named goals (ranked)

<!-- 3–5 goals, each a noun phrase a non-designer can recall. Ranked: #1 is
     the dominant goal that wins when goals conflict. Each goal lists what
     grounds it — persona, precedent, standards, and platform conventions.
     A goal with no stable referent is still a fresh opinion; ground it first. -->

1. <dominant goal — e.g. "Quiet confidence">
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

### How the skill routes a request

When you invoke `creative-direction`, it first checks whether the target surface already has a direction document. That lookup determines which route applies:

- **inherit** — a section, component, state, or feature added inside a surface that already has a direction. The skill frames the brief against the direction that already governs the surface, with no divergence round and no visual step, and hands back a scoping answer: which existing goals and axis tokens govern the new element. It writes nothing. A surface with a direction gets no second direction doc.
- **extend** — a new surface added to a product that already has a visual system. The skill frames the brief, explores candidate directions, and converges on one.
- **originate** — a surface in a product with no visual system yet, the highest-invention route. The skill frames, explores, makes a candidate concrete enough to support a compositional commitment, then converges.

### What the five operations do

Each request maps to one of five named operations before any reference is loaded:

- **frame** — establishes the brief from the felt vibe. Sets audience and ranked jobs-to-be-done, target surface, incumbent constraints, intended effect, what must stay recognisable, what would read as generic, and the named goals the interrogation produces. Does not recreate product discovery or journey design.
- **explore** — generates materially different candidate directions, each as a filled direction sheet held in the session, then scores them for distinctness. Nothing is written to disk at this stage.
- **visualize** — makes a candidate concrete enough to support a compositional commitment. It runs on any harness: a text schematic is the default representation. A rendered comp is produced only when the route is `originate` and the harness can produce one, and its absence is a named skip, not a blocker. Writes nothing of its own.
- **converge** — selects a direction, grounds and ranks the goals, fills the direction sheet across all fifteen axes, runs the counterfactual check, holds the quality floor, and captures the direction document. This is the only operation that writes a file. It will not choose between materially different directions for you: it presents the survivors at equal salience and waits. Picking one sets the document's `status` to `selected`; asking the agent to decide is recorded as a delegated choice and leaves it `proposed`.
- **refine** — takes a requested change in plain words, maps it to the axes that may move, and records the amendment in the existing direction document without writing a second direction doc.

### Make the direction discriminating

The direction sheet turns a felt brief into choices that another designer can
inspect. Ask for it directly:

```
Turn this visual brief into a direction sheet. Ground every choice in the
audience and referents, then show what needs revision after a counterfactual
check.
```

It records fifteen axes. The first seven are structural because structure
carries at least as much of a first impression as colour does. Each commitment
cell starts with its bracketed tokens, then says in prose what that
choice means for this surface. Grid grammar, alignment and equilibrium, and
section and scroll rhythm take two ordered tokens; every other axis takes one.
`[platform-default]` means the platform's usual
convention remains in force because you have not made a direction-specific
choice. It is a recorded undecided state, never an empty cell.

The first three rows below are filled as a worked example for a long-form
reading surface. The remaining twelve show the vocabulary with the commitment
column as the template ships it — fill each the same way.

| Axis | Token vocabulary | This direction commits to |
| --- | --- | --- |
| Grid grammar | `[manuscript]` `[column]` `[modular]` `[hierarchical]` `[compound]` `[broken]` `[platform-default]`, then `[rigid]` `[relaxed]` `[platform-default]` | `[column]` `[rigid]` — a three-track grid that never reflows into an asymmetric split, so a long reading column stays predictable between sections |
| Alignment and equilibrium | `[edge]` `[centred]` `[baseline]` `[platform-default]`, then `[symmetric]` `[asymmetric]` `[platform-default]` | `[baseline]` `[asymmetric]` — one baseline grid governs every text block; weight sits left of centre so the eye starts in the same place on each screen |
| Spatial density | `[sparse]` `[comfortable]` `[dense]` `[platform-default]` | `[sparse]` — at most two content groups per screenful, because the reader is deciding rather than scanning |
| Whitespace distribution | `[compact]` `[even]` `[expansive]` `[platform-default]` | `[platform-default]` <macro margins, gutters, section gaps; micro spacing> |
| Hierarchy and scale contrast | `[flat]` `[moderate]` `[steep]` `[platform-default]` | `[platform-default]` <hero dominance; span and size jumps> |
| Containment and boundary strength | `[open-field]` `[ruled]` `[panelled]` `[carded]` `[platform-default]` | `[platform-default]` <whether overlap is permitted> |
| Section and scroll rhythm | `[continuous]` `[episodic]` `[platform-default]`, then `[regular]` `[varied]` `[platform-default]` | `[platform-default]` `[platform-default]` <bleed cadence; pacing of a long page> |
| Type voice | `[serif]` `[sans-geometric]` `[sans-humanist]` `[monospace]` `[mixed]` `[platform-default]` | `[platform-default]` <the weight and width range used> |
| Type hierarchy | `[flat]` `[moderate]` `[dramatic]` `[platform-default]` | `[platform-default]` <the scale relationship; how many levels> |
| Chromatic intensity | `[monochrome]` `[restrained]` `[saturated]` `[high-chroma]` `[platform-default]` | `[platform-default]` <how many hues; tonal range; where accent is spent> |
| Form | `[rectilinear]` `[softened]` `[organic]` `[platform-default]` | `[platform-default]` <corner treatment across the scale; icon stroke character> |
| Material and depth | `[flat]` `[layered]` `[deep]` `[platform-default]` | `[platform-default]` <how many elevation levels; how depth is signalled> |
| Ornament and texture | `[none]` `[pattern]` `[grain]` `[illustration]` `[platform-default]` | `[platform-default]` <the ratio of image to text> |
| Image treatment | `[photographic]` `[illustrative]` `[abstract]` `[none]` `[platform-default]` | `[platform-default]` <how images are cropped; how they are toned> |
| Motion character | `[still]` `[productive]` `[expressive]` `[platform-default]` | `[platform-default]` <how far things move; relative duration; continuous or discrete> |

#### Run the counterfactual check

Name a comparator — a similar brief you could plausibly have been given — and
take it through the same direction work. Anything that matches what the
comparator produced is a default, not a choice. Revise that axis or goal, then
record the comparator, what it produced, the revision, and why the new
direction suits this brief. An unnamed comparator or an empty table means the
check has not run; neither means no revision was needed.

Use the resulting direction when you review the screen. The authoring-time
taste critique may call out a contradiction only when the recorded goal and
its grounding referent support that call. It does not add a new preference.

#### Start from a preset, then make it yours

The three presets are useful precedent referents: Swiss / International
Typographic for disciplined information order, editorial broadsheet for ranked
stories and their relationships, and Bauhaus for function-led composition.
Each is a starting direction, never a finished one. Add the persona, standards,
and platform grounding for your surface, then run the counterfactual check.

#### Audit several candidate directions

When you have several candidates, run a divergence audit over their direction
sheets. Compare only the bracketed token tuples on every axis, including both
tokens in the three rows that have two independent parameters. Prose does not
create a difference.

The audit reports the closest pair across the set, not the average. A pair is
distinct when it differs on at least six of the fifteen axes. If the closest
pair falls below that mark, revise the named axes before you treat the set as
meaningfully different.

## Run `design-system` — the token set

**You type:**
<!-- rung: JOURNEY stage 3 -->

```
Derive the semantic token and scale taxonomy from the approved aesthetic direction.
```

**Agent returns:**
<!-- rung: JOURNEY stage 3 -->

> **Agent:** Done — I've written a semantic token and scale taxonomy whose roles trace to the approved direction to `<output_dir>/tokens/<slug>.md`.

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

**Where it lands:** `<output_dir>/tokens/<slug>.md`.
<!-- rung: design-system SKILL.md -->

**What it looks like:**
<!-- rung: packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md -->

```markdown
---
type: token-taxonomy
slug: "<kebab-case-slug — the system this taxonomy serves>"
direction: "<name of the aesthetic direction this taxonomy derives from>"
date: "<YYYY-MM-DD>"
---

# Token taxonomy: <system or product name>

<!--
  Written by the `design-system` skill. Fill the angle-bracket prompts and
  delete this comment. This doc holds the *taxonomy* — the roles, the layering,
  and the scale relationships expressed symbolically. It holds NO resolved
  values: no palette, no spacing sheet, no type sheet, no timing table. You
  record the method and the shape; whoever builds resolves the numbers for
  their medium and density, and records them in the interchange file, not here.
-->

## Direction this derives from

<!-- Name the goals from the aesthetic direction. Every role and every scale
     decision below traces back to one of them. A taxonomy with no named goal
     behind it is arbitrary. -->

- **<goal 1>** — <one line on what it asks of the system>
```

*The agent replaces every `<…>`. This is the opening of the template the skill writes from; the artifact continues in the same shape.*

## Where this leads

**Done with this step:** You can move on when each principle decides between two real screen choices and each token role traces to a named aesthetic goal.
<!-- rung: authored -->

Stage 3 of five, and the pack's second human gate. Nothing below this point should be re-litigating the direction.

**Next:** [Design each screen](design-each-screen.md).
<!-- rung: authored -->

**Go deeper:** [the `experience-design` skill reference](../reference/experience-design.md) — every skill this step runs, with its inputs, outputs and write boundary.
<!-- rung: authored -->
