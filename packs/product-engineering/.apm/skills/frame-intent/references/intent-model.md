# The intent model

The `intent` is the pack's one artifact. It is **recursive** and **level-tagged**.

## What an intent is

A level-tagged statement of an outcome and the opportunity behind it. It carries
four things as fields:

- **Outcome** — a steerable *input* metric, the *lagging* outcome it drives, and
  a *guardrail* that must not get worse (qualitative-but-falsifiable is fine in
  0-to-1).
- **Opportunity** — the solution-independent need (a job to be done).
- **Assumptions** — what must be true for the bet to pay off.
- **Decomposition** — its children: lower-level intents, or, at the leaf, a
  spec/slice.

## The same artifact at every level

A capability intent and a feature intent are the *same shape* — only `Level:`
differs. A PRD is a feature intent rendered as a document. So you never choose
"do we write a capability intent or a feature intent or a PRD" — you write an
intent at the level you're operating at, and the recursion handles the rest:

```
intent (level: capability)        "self-serve billing platform"
  ├─ intent (level: feature)      "dunning & retries"
  │     └─ spec / slice (leaf)    the shippable, agent-buildable unit
  └─ intent (level: feature)
        └─ spec / slice
```

## Two consequences

- **Decomposition is recursive.** `decompose-intent` produces the *next level
  down* — child intents, or specs at the leaf — never a fixed depth. At `app`
  Scale the tree is often one level deep; at `business-unit` Scale, three.
- **Assumptions are de-risked per intent, at its level.** The *kind* of
  assumption shifts with the level: capability-level assumptions are
  architectural / adoption ("can these services coordinate?", "will teams
  adopt this?"); feature-level assumptions are desirability ("do users want
  this?"). `de-risk-intent` always operates on *this* intent at its level.

## The leaf is a spec

The tree bottoms out at a shippable spec/slice — the unit your delivery loop
builds. At `app` Scale a leaf feature intent *is* an ordinary `core` brief;
`receive-brief` → `new-spec` → `work-loop` take it from there. The tree is
deeper than any tracker, and projects **one-way** onto trackers (see
`decompose-intent`'s `references/tracker-projection.md`).
