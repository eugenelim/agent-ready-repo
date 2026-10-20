---
title: How to map capabilities
summary: Convert a committed bet into a dependency-aware capability map with maturity, criticality, disposition, and build order.
pack: product-engineering
kind: how-to
---

# How to map capabilities

**Use this when:** You have a committed bet from `place-bet` and need to enumerate what to build, buy, or adopt — and in what order — before any spec or initiative brief is written.
**Prerequisites:** `product-engineering` pack installed; a committed `bet.md` from `place-bet` (step 5 of the shaping sequence).
**Result:** A capability map with Wardley-stage and strategic-criticality annotations, a dependency-ordered build sequence, ready for `intent decompose`.

**Goal:** You have a committed bet and need to enumerate all the capability areas
the initiative implies — what to build, what to buy or adopt, and in what order
to build — before any spec or brief is written.

**Skill:** `map-capabilities` (PE pack, user scope)

```text
Map our capabilities for a self-service export-retention service for workspace owners.
```

---

## When to run `map-capabilities`

Run `map-capabilities` after `place-bet`.
It is step 6 of the PE six-step shaping sequence:

```
frame-situation → identify-opportunities → diverge-solutions
  → validate → place-bet → map-capabilities
```

The longer route then continues: its next step is `intent decompose`, which takes
`capability-map.md` as input and turns each Build capability into a child intent.

This guide belongs to the [robust shaping path](../explanation/the-intent-tree.md#light-and-robust-shaping-paths).

You need a committed bet before running this skill. The bet provides the option,
appetite, and rationale that anchor the capability domains the skill proposes.
If you do not yet have a bet, run `place-bet` first.

**Not the right skill if:**

- You are working on a single feature or screen → use `intent frame`.
- You want to author the initiative brief → use `lean-canvas` for the one-page initiative brief or
  `author-delivery-brief` for the delivery brief (neither replaces this skill).

---

## How to read the Wardley and strategic-criticality annotations

Each capability entry in the map carries two annotations — Wardley stage and
strategic criticality — that together tell you how mature the capability is and
how much to invest in it.

### Wardley stage

The Wardley stage describes how evolved a capability is in the market:

| Stage | What it means | Typical implication |
|-------|--------------|---------------------|
| **Genesis** | Novel; no standard approach exists yet | Explore; expect high uncertainty and iteration |
| **Custom-built** | Better understood but still bespoke | Build if differentiating; invest carefully |
| **Product** | Standardised solutions exist | Buy or adopt unless you have a specific differentiating reason to build |
| **Commodity** | Utility-grade; interchangeable suppliers | Adopt or outsource; competing here wastes energy |

### Strategic criticality

Strategic criticality describes how much competitive weight the capability carries:

| Criticality | What it means | Typical implication |
|-------------|--------------|---------------------|
| **Differentiating** | Creates or sustains competitive advantage | Prioritise for Build; invest to lead |
| **Parity** | Must match market standard to be credible | Meet the bar; don't over-invest |
| **Utility** | Necessary overhead with no competitive value | Minimise cost; prefer Adopt or Buy |

### Reading them together

The combination tells you the most important strategic signals:

- **Custom-built + Differentiating** → your highest-value Build candidates; these go to the top of the build sequence.
- **Commodity + Utility** → adopt or outsource; never build these from scratch.
- **Commodity + Differentiating** → a *strategic tension*. The skill will flag this and ask for your acknowledgement before finalising the entry. Either your differentiation claim is wrong (the market has commoditised it) or you have a genuine reason to own the commodity (rare — name it explicitly).
- **Product + Parity** → the default Buy zone; a commercial solution handles it adequately.

---

## How to use the suggested build sequence

The suggested build sequence at the bottom of the capability map lists
**Build-disposition capabilities only**, ordered dependency-first then by
Wardley maturity (Genesis / Differentiating capabilities first).

It is a **recommendation, not a mandate** — the product team holds final
sequencing authority.

### Ordering the child intents

`intent decompose` turns each Build capability into a capability-level child
intent. Use the build sequence to order those child intents. Specs enter the
`workspace.toml` queue only when a child intent reaches its own leaf and hands
off through `work-intake`; the capability map never seeds the spec queue
directly.

**Non-Build capabilities (Buy / Partner / Adopt)** appear in the domain tables
but are excluded from the build sequence — their disposition *is* the action.
Add procurement decisions to your team's acquisition plan; child intents name them as dependencies.

### What comes next

After the capability map is committed:

1. Run `intent decompose` on `capability-map.md`. Each Build capability becomes a capability-level child intent, which then runs `intent frame`, `intent de-risk`, and `intent decompose`.
2. Use the build sequence to order those child intents.

A brief is a separate path: `lean-canvas` writes the one-page initiative brief, and `author-delivery-brief` owns the delivery brief.

---

## See also

- `place-bet` — step 5; produces the `bet.md` this skill reads
- `intent decompose` — the next step; turns each Build capability into a child intent
- `lean-canvas` — writes the one-page initiative brief
- `frame-situation` — step 1; provides Wardley capability assessments the map reads opportunistically
- `intent de-risk` — step 4 (validate); runs assumption tests before the bet is placed
- `workspace-status` — surfaces the spec queue once child intents hand off their specs

## What you have now

- A capability map with maturity, criticality, disposition, and dependency-aware build order.
- Its Build capabilities are ready for `intent decompose`, in build order.
