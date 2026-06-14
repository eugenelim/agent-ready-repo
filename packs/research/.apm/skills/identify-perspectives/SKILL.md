---
name: identify-perspectives
description: Enumerate the named camps on a contested topic before research begins. Builds the perspective scaffold that `/source-map` and `/compare-hypotheses` consume downstream in the decision pipeline. Grounded in Wikipedia NPOV (neutral point of view — fairly represent significant views) and ACH (competing hypotheses — surface all explanations before evaluating). Produces `perspectives.md` listing each camp's name, its core claim, and representative voices, plus a tension map of the irreducible disagreements — the conditions under which each position holds and what forced resolution would destroy. Depth cues — `quickly`, `top three`, `briefly` for the dominant few; `comprehensively`, `exhaustively`, `in depth`, `extensive` for fringe and dissenting positions too.
---

# /identify-perspectives

The first step in the decision pipeline. Enumerates the named camps on
a contested topic so downstream skills can survey sources per camp and
compare hypotheses across them.

## When to invoke

- At the start of the decision pipeline, before `/source-map`.
- Any time a research question has known controversy and the right
  answer depends on which lens you're using.
- Not for descriptive factual questions (those go straight to
  `/research`).

## Methodology

Two convergent disciplines:

1. **Wikipedia NPOV (Neutral Point of View)** — fairly represent all
   significant views proportionally to their prominence in reliable
   sources. The pack borrows the *representation* discipline: every
   significant camp gets named, not just the camp the model finds most
   credible.

2. **ACH (Analysis of Competing Hypotheses)** — surface all viable
   explanations *before* evaluating any of them. ACH's failure mode is
   premature dismissal; enumerating first protects against it.

The output is a scaffold of camps, not a verdict on which is right.
Evaluation is `/compare-hypotheses`'s job downstream.

## Procedure

1. **Restate the question** as one decisive choice or one factual
   contention.
2. **Enumerate camps** by name. A camp is a position with a
   recognisable label inside the community discussing the topic — not
   a position the model invented. If you have to invent a camp name,
   it probably isn't a real camp.
3. **For each camp**, record:
   - Core claim (one sentence).
   - Representative voices (people, institutions, publications known to
     hold the camp's position).
   - One adjacent or fringe variant the camp tolerates.
4. **Look for missing camps** — quiet positions, dissenting minorities,
   contrarian-but-credentialed. The biggest NPOV failure is
   *omission*, not bias.
5. **Map the irreducible tensions.** Camps that genuinely conflict are
   the point of the artifact, not a defect to adjudicate here. For each
   *preserved* disagreement — one where both camps hold real ground —
   record the **conditions under which each position holds** (the
   boundary that makes each camp right *somewhere*) and **what forced
   resolution would destroy** (the distinction that collapsing to one
   camp would erase). A disagreement that dissolves once its conditions
   are named was never a real tension — fold it back into the camps. One
   that *sharpens* under that test is irreducible — preserve it. See
   *Tension map* below.
6. **Write `perspectives.md`**.

## Tension map

Naming the camps says *what* the positions are; the tension map says
*why the disagreement persists*. It is the difference between a list and
an explanation, and it is the habit that keeps this skill from quietly
collapsing a live controversy into the camp the model finds most
credible.

A tension belongs on the map when both positions are defensible and each
is right under different conditions — not when one is simply better
supported (that is `/compare-hypotheses`'s call, downstream). The map
extends NPOV's *representation* discipline one step: from "every
significant camp gets named" to "the boundary between camps gets named,
so the disagreement survives the trip downstream intact."

## `perspectives.md` output schema

```markdown
# Perspectives — <question>

## Camp: <name>

- **Core claim:** <one sentence>.
- **Representative voices:** <person/institution>, <person/institution>.
- **Adjacent variants:** <one fringe or modified position>.

## Camp: <name>

(same shape)

## Possibly-missing camps

- <one-line description of a position that might be under-represented>.

## Tension map

### Tension: <camp A> vs <camp B>

- **Holds for A when:** <the regime / conditions under which A is right>.
- **Holds for B when:** <the regime / conditions under which B is right>.
- **Forced resolution would destroy:** <the distinction lost if the
  pipeline collapsed this to one answer>.
```

## Citation discipline

Naming a camp's "representative voices" is a factual claim — cite the
voice or mark it `[synthesis]` (a synthesis across multiple cited
positions) / `[inference]` (a defensible deduction from voice patterns
the model has seen across cited material).

## Depth cues

- `quickly`, `top three`, `briefly` — return the dominant two or three
  camps only; skip the missing-camps survey.
- `summary only` — same; one-line per camp.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` —
  enumerate every named camp, including fringe and dissenting ones;
  spend real effort on the missing-camps survey.
