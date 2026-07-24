---
name: explore-options
description: Use to generate multiple candidate product shapes before the discovery loop converges on one — the divergence stage that guards against myopic-greedy commitment. Triggers on "give me candidate product shapes", "diverge on the product shape", "what are the options before we commit", "explore alternatives for X", "don't converge yet". Generates N candidates across altitude × mechanic, each with its riskiest assumption, then frames an explicit compare-and-choose. Do NOT use to break down a chosen approach (use `decompose-intent`), to critique one produced artifact (use `devils-advocate`), or to converge (that is the discovery loop's job).
---

# Skill: explore-options

**Generate multiple candidate product shapes *before* the loop commits to one.**
This is the discovery loop's **divergence** stage (pre-G1.5), and it exists because
every other phase of the gate ladder is *convergent* — left alone the loop locks
onto the first coherent framing and commits early (**myopic-greedy commitment**,
the loop's headline risk). The Double Diamond and Design Sprint treat forced
divergence as non-optional; this skill is that forcing function.

It is **prompt-only** (CHARTER Principle 3): no engine, no scorer, no candidate
generator script — the agent following this body writes the candidates as
blackboard slots. **No new agent, no new reviewer.**

## Output rendering

Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## When to invoke

1. There is a **framed intent** to diverge on (from `frame-intent`) — you are
   generating *solution shapes* for a stated outcome, not shaping the outcome
   itself.
2. The loop has **not yet converged** — divergence runs before G1.5. If the team
   already committed and wants to *re-open*, that is the `explore-alternatives`
   verdict routing back here.
3. You want **breadth, not a single answer.** If the shape is genuinely obvious and
   the appetite is tiny, say so — manufacturing five candidates for a one-shape
   problem is waste.

## The two axes

Generate **N candidate shapes (4–5 is the useful range)** across two axes — this is
what stops the candidates from being trivial variations of one idea:

- **Altitude** — narrow-slice ↔ whole-domain. The myopic default picks the narrow
  slice (a kitchen "draft-and-approve" assistant); force the **higher altitude**
  (the whole household — calendar, travel, vendors, budget) *and* the **deeper
  sub-domain** (meal → recipe → ingredient → store sourcing).
- **Mechanic** — the interaction model: `draft-and-approve` / `coordination-layer`
  / `knowledge-graph-first` / `ambient-capture` (illustrative, not closed). The
  same outcome under a different mechanic is a different product.

## Procedure

1. **Generate the candidate set.** For each candidate, write a blackboard
   `intent`-variant slot under the `diverging` parent (the plan-tree's `candidates`
   array — see the discovery-loop asset). Each candidate carries:
   - `altitude` and `mechanic` (where it sits on the two axes);
   - a one-line **shape** (what the product *is* under this framing);
   - its **riskiest assumption** — the one that, if wrong, sinks it (front it with
     *what would have to be true*).
2. **Reuse, don't reinvent.** Pressure and rank with the skills that already exist —
   you are *generating*; they *select* and *stress*:
   - `compare-hypotheses`' ACH matrix to **select** among the shapes;
   - `devils-advocate` to **pressure** each candidate;
   - `de-risk-intent` to **risk** the chosen one (and to seed each candidate's
     riskiest assumption);
   - the discovery loop's **scenario-variation** self-coverage module to widen the
     set along persona / state / scale / adversarial edges.
3. **Frame an explicit compare-and-choose.** Divergence ends in a *selection*, not a
   pile. Recommend one shape and say why, but **retain the not-chosen as `rejected`
   / `parked` with rationale** — never deleted, so they stay revivable (the loop's
   persistence + `decision-archaeology`'s revival check). The **altitude bet is a
   value/scope call — surface it at G1.5**, do not resolve it silently.

## What you write

The candidate set + the selection on the plan-tree node (the discovery loop's
[`plan-tree` asset](../discovery-loop/assets/plan-tree.md) `candidates` +
`selection`). A candidate slot:

```
- id: cand.<slug>
  altitude: narrow-slice | whole-domain | <a point between>
  mechanic: draft-and-approve | coordination-layer | knowledge-graph-first | ambient-capture | <other>
  shape: <one line — what the product is under this framing>
  riskiest_assumption: <what would have to be true>
  status: selected | rejected | parked
  rationale: <why selected / retained-not-chosen>
```

## Anti-patterns to refuse

- **Generating trivial variations of one idea.** If every candidate sits at the
  same altitude with the same mechanic, you diverged on the label, not the shape.
  Span both axes.
- **Deleting the not-chosen.** Retain rejected/parked candidates with rationale —
  they are revivable, and deleting them re-creates the myopic commitment divergence
  exists to prevent.
- **Resolving the altitude bet silently.** Altitude is a value/scope call — surface
  it at G1.5, with the candidates as the referent.
- **Re-implementing selection or critique.** Reuse `compare-hypotheses` /
  `devils-advocate` / `de-risk-intent`; this skill *generates*.
- **Building a generator engine.** Prompt-only — the agent writes the candidates;
  there is no scorer or candidate-synthesis script.
