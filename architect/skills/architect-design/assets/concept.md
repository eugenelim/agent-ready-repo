<!-- Stage-0 architecture concept — the ≤½-page shaping artifact drafted
     BEFORE the full design doc. Spirit of arc42's Architecture Communication
     Canvas: travel-light, elevator-pitch, "zip version" of the architecture.
     This is NOT a second design doc — it carries NONE of design-doc.md's heavy
     sections (no full proposal, no alternatives-with-rejection, no risks table,
     no rollout). Depth belongs in design-doc.md after the concept is agreed. -->

# Concept — <one-phrase name>

## Problem & context

<The user-visible problem and why now, in two or three sentences. What we're
building and who's affected.>

## Constraints

<The hard edges: deadline, budget, team shape, regulatory, existing-system
shape. At least one should be non-obvious.>

## Candidate shapes (1–2)

- **<Shape A — one line.>**
- **<Shape B — one line, if there's a real second option.>**

## Provider / provider-class

<AWS / Azure / GCP, a primitives provider (Hetzner-class), local-first, or
"none / not cloud". One **by-construction** line: which pillars are met by
*managed services* vs. which you must *build yourself* (primitives), or the
local→production delta (local-first).>

## Top 2–3 prioritized quality attributes

<Ranked by business-importance × architectural-risk — the utility-tree-lite
pass. Each with a one-line *why it ranks here*.>

1. **<Attribute>** — <why it's top.>
2. **<Attribute>** — <why.>

## Key tradeoff / open decision(s)

<The one or two decisions that shape this design — each a tradeoff (two pillars
pulling opposite ways) or an open call the human must make. This is what the
full doc and the convergence loop will turn on.>

## Open questions (optional)

<Only real unknowns, each with who/what could answer it. Drop the section if
there are none — don't pad.>

## Knowledge surface (optional)

<If you consulted an enterprise knowledge-retrieval surface to ground this
concept, name it here (or "none detected") — the audit home for the
architect-design knowledge-surface consult (see references/knowledge-surfaces.md).
"none detected" is the trigger for the ask-and-lower-confidence path. Drop the
section if no surface was relevant.>
