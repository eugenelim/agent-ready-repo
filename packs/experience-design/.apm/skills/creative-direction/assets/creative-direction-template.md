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
2. <goal>
3. <goal>

## What each goal means

<!-- For each goal: one line on what it means here, one line on what would
     VIOLATE it, and its grounding referents. -->

- **<goal 1>** — means: <one line>. Violated by: <the opposite that breaks it>.
  - *Persona:* <who this goal serves — one phrase or pointer to the full persona>
  - *Precedent:* <one or two examples that carry this quality; name the attribute taken, not the product whole>
  - *Standards:* <named guidance or principle this goal aligns with — pointer, not reprint>
  - *Platform conventions:* <how the target surface's guidance shapes this goal>
- **<goal 2>** — means: <one line>. Violated by: <…>.
  - *Persona:* <…>
  - *Precedent:* <…>
  - *Standards:* <…>
  - *Platform conventions:* <…>
- **<goal 3>** — means: <one line>. Violated by: <…>.
  - *Persona:* <…>
  - *Precedent:* <…>
  - *Standards:* <…>
  - *Platform conventions:* <…>

## Direction sheet

<!-- Fifteen axes; the first seven are structural. Each cell OPENS with its
     tokens in square brackets from that row's vocabulary, then prose
     saying what it means here. Tokens are what the divergence audit compares;
     the prose is not compared. Every cell ships filled with its
     [platform-default] token — replace it, never blank it.
     Arity is fixed, because the divergence audit compares complete tuples:
     Grid grammar, Alignment and equilibrium, and Section and scroll rhythm
     take exactly two ordered tokens; every other axis takes exactly one. -->

| Axis | Token vocabulary | This direction commits to |
| --- | --- | --- |
| Grid grammar | `[manuscript]` `[column]` `[modular]` `[hierarchical]` `[compound]` `[broken]` `[platform-default]`, then `[rigid]` `[relaxed]` `[platform-default]` | `[platform-default]` `[platform-default]` <track count; which transformations are permitted> |
| Alignment and equilibrium | `[edge]` `[centred]` `[baseline]` `[platform-default]`, then `[symmetric]` `[asymmetric]` `[platform-default]` | `[platform-default]` `[platform-default]` <how many distinct axes> |
| Spatial density | `[sparse]` `[comfortable]` `[dense]` `[platform-default]` | `[platform-default]` <information and group count per screenful> |
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

## Counterfactual check

<!-- Name a comparator brief, work it through, and compare. Any part of this
     direction that matches what the comparator produced is a default, not a
     choice. Revise it, then record the change. An unnamed comparator or an
     empty table means the check has not run — neither means nothing needed
     revision. -->

**Comparator brief:** <the similar brief you tested against — name it, so a
reader can tell whether it was a real test or a convenient one>

| Axis or goal | What the comparator produced | What it became | Why |
| --- | --- | --- | --- |

## Dominant goal for arbitration

<!-- The #1 goal, plus the recorded trade-offs: when two goals conflict on a
     real choice, which wins and why. The build reads this instead of re-
     arguing taste. -->

**Dominant goal:** <goal #1>

Resolved trade-offs:

- When **<goal A>** and **<goal B>** conflict on <kind of choice>,
  **<winner>** wins — because <one-line reason tied to the ranking>.

## Open questions

<!-- What's unresolved, including any goal that pulls against the shared
     quality-floor (accessibility, all-states, meaningful motion). The floor
     is never traded away — record how the direction clears it. Also list
     any grounding referents that are still missing (e.g. persona not yet
     fully defined). -->

- <open question — e.g. "How do we read as premium while clearing the
  contrast floor?">
- <missing grounding — e.g. "Persona not yet fully defined; sketch recorded inline; full persona work deferred.">

## Borrowed discipline

<!-- Recorded by `converge`. Name one discipline taken from a rejected
     candidate, or state explicitly that none was taken. A discipline is
     a mechanism or structural approach — not a visual value — that the
     rejected candidate handled better than the selected direction did. -->

**Donor candidate:** <which rejected candidate this discipline came from, or "none">
**Discipline taken:** <the mechanism or structural approach borrowed from the donor, or "none">

## Compositional commitments

<!-- Recorded by `visualize` when an approved visual target exists. These
     commitments bind composition only. They do not bind colour, type,
     spacing, or motion values — those remain for `design-system` to derive. -->

<describe the compositional commitments the approved visual target establishes>

## Refinement amendment

<!-- Recorded by `refine` each time an axis moves. Add one row per axis that
     changed. Axes not listed here are unchanged from the direction sheet. -->

| Axis | From | To | Why |
| --- | --- | --- | --- |
