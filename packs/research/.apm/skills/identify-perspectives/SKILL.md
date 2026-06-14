---
name: identify-perspectives
description: Enumerate the named camps on a contested topic before research begins. Builds the perspective scaffold that `/source-map` and `/compare-hypotheses` consume downstream in the decision pipeline. Grounded in Wikipedia NPOV (neutral point of view — fairly represent significant views) and ACH (competing hypotheses — surface all explanations before evaluating). Produces `perspectives.md` listing each camp's name, its core claim, and representative voices, plus a tension map recording which disagreements are irreducible (both sides right under different conditions) and what a forced resolution would destroy. Depth cues — `quickly`, `top three`, `briefly` for the dominant few; `comprehensively`, `exhaustively`, `in depth`, `extensive` for fringe and dissenting positions too.
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
5. **Map the tensions** — for each pair of camps that genuinely
   disagree, decide whether the disagreement *resolves* (one camp is
   right, the other is wrong, and evidence settles it) or is
   **irreducible** (both camps are right under different conditions, and
   the disagreement is in the world, not in a gap in the evidence). For
   every irreducible disagreement, record the conditions under which
   each side holds, and what a forced resolution would destroy. This is
   the step that *marks* an irreducible tension so it is not silently
   flattened downstream — `/compare-hypotheses` is built to pick a
   winner, so a disagreement that *shouldn't* have a winner needs to
   carry that marking before it reaches that skill, so a reader (or a
   future `/compare-hypotheses` pass) can refuse to collapse it.
6. **Write `perspectives.md`**.

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

- **<camp A> vs. <camp B>** — irreducible.
  - **<camp A> holds when:** <the conditions / regime / scope under which A is right>.
  - **<camp B> holds when:** <the conditions under which B is right>.
  - **Forced resolution would destroy:** <what picking one side erases — a
    real distinction, a context where the loser is correct, a constraint
    that only the loser respects>.
- **<camp C> vs. <camp D>** — resolves (defer to `/compare-hypotheses`).
```

The tension map is **not** a relabelling of the camp list above it. The
camp list answers *"what are the positions?"*; the tension map answers
*"which disagreements between them have no single right answer, and
why?"* A camp can appear in the list and never reach the tension map
(it doesn't conflict with another camp); a disagreement reaches the
tension map only when it is **irreducible** — both sides survive
because they are right under different conditions, not because the
evidence is too thin to choose (that latter case is a confidence
question for `/research`, not a tension). Marking the irreducible ones
here is what lets a reader — or a future `/compare-hypotheses` pass —
refuse to collapse them to a verdict; today `/compare-hypotheses` ranks
unconditionally, so the marking is the record that a ranking would be
the wrong move, not yet a mechanism that prevents one.

## Citation discipline

Naming a camp's "representative voices" is a factual claim — cite the
voice or mark it `[synthesis]` (a synthesis across multiple cited
positions) / `[inference]` (a defensible deduction from voice patterns
the model has seen across cited material).

## Depth cues

- `quickly`, `top three`, `briefly` — return the dominant two or three
  camps only; skip the missing-camps survey and the tension map.
- `summary only` — same; one-line per camp.
- `comprehensively`, `exhaustively`, `in depth`, `extensive` —
  enumerate every named camp, including fringe and dissenting ones;
  spend real effort on the missing-camps survey and the tension map.
