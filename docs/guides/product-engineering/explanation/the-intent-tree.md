# The intent tree — level-agnostic product shaping

> **Diátaxis: explanation.** Why the `product-engineering` pack shapes work the way it does. For the step-by-step, see the how-tos [*Frame a product vision*](../how-to/frame-a-product-vision.md), [*Shape a product strategy*](../how-to/shape-a-product-strategy.md), and [*Shape a feature intent*](../how-to/shape-a-feature-intent.md); for field definitions, the reference [*Intent fields and modes*](../reference/intent-fields-and-modes.md). For how these product altitudes meet the architecture concept at the start of an engagement, see [*Shaping a new engagement*](../../_shared/explanation/shaping-a-new-engagement.md).

## The problem it solves

A repo set up for engineering agents can take a *brief* and build it (`receive-brief` → `new-spec` → `work-loop`). But where does the brief come from? The expensive product failures live *upstream* of the brief — building the wrong thing, un-validated bets, requirements with no outcome. The `product-engineering` pack is that upstream, expressed as habits rather than infrastructure.

## One artifact, every level

The pack has a single artifact: the **`intent`** — a level-tagged statement of an outcome and the opportunity behind it. The insight that makes it work is that a *product-vision intent*, a *product-strategy intent*, a *capability intent*, a *feature intent*, and a *PRD* are not five artifact types. They are the same artifact at different **levels**; a PRD is just a feature intent written as a document. So you never choose which to write — you write an intent at the level you're operating at, and it forms a recursive tree whose leaf is a shippable spec:

```text
  intent (product-vision)                 why this product should exist
      └── intent (product-strategy)       the path: challenge, policy, actions
              └── intent (capability)
                      ├── intent (feature)
                      │       └── spec / slice (leaf) ──► core: receive-brief → new-spec → work-loop
                      └── intent (feature)
                              └── spec / slice (leaf) ──► core: receive-brief → new-spec → work-loop

  same artifact at every level — it just stops recursing when the leaf is
  a spec your delivery loop can build.
```

`Level` is an **open recognized set** — `product-vision › product-strategy › capability › feature` — not a closed enum: these are the altitudes the pack seeds and prompts for, but you can name an intervening one (an `initiative`, an `epic`) when your org has it. The two **product altitudes** sit above engineering work: **`product-vision`** is the *existence bet* (why this product should exist, for whom, through what wedge), and **`product-strategy`** is the *path* (the central challenge, the guiding policy, the coherent actions, and the problem/segment sequence). You enter at the altitude you're operating at — a greenfield product concept at the top, a known feature partway down.

Crucially, **`Level` is decoupled from `Scale`.** Scale (app ↔ business-unit) still decides where the work lives and how the leaf projects, but it only *suggests* a starting altitude now — it no longer stamps one. An app-scale effort can be a `product-vision` bet (a greenfield concept) or a `feature` (a known build); you pick, and override the suggestion in a word.

Two things fall out of the recursion. **Decomposition** produces the *next level down*, one level at a time — deep at business-unit scale, often one level at app scale. And **assumptions are de-risked per intent at its own level** — product-level bets are **market-existence** questions (will anyone want this at all, *and* can it be a business — tested once at the top, distinct from feature desirability), capability bets are architectural/adoption questions, feature bets are desirability questions, and the same `de-risk-intent` habit handles all of them.

## Why "shape, then de-risk, then decompose"

The three skills are the three moves of shaping, in order:

1. **`frame-intent`** — name the outcome (a steerable input, a lagging result, a guardrail) and the solution-independent opportunity. Resolve **Scale** once.
2. **`de-risk-intent`** — test the riskiest assumption against a **predeclared kill condition**, under a **prototype-approach** you choose by reversibility. This is the guard against shipping confident, un-validated bets.
3. **`decompose-intent`** — break the survived intent into the next level, until the leaf is a spec. At app scale that leaf *is* a `core` brief.

Every node in the tree runs the same three moves before it splits:

```text
  frame-intent          de-risk-intent              decompose-intent
  ──────────────        ────────────────────        ──────────────────
  name the         ──►  test the riskiest      ──►  break into the next
  outcome + the         assumption against           level down
  opportunity,          a predeclared
  resolve Scale         kill condition
                              │
                        survives? ──no──► kill or pivot (don't build)
                              │ yes
                              └──────────► decompose
```

## What it deliberately is *not*

It is **habits, not infrastructure** — no engine, no hooks, no validators, no subagents. It does not model work in a tracker; trackers are one-way *projections* of the intent tree (the tree is deeper than any of them). It does not author wire contracts; those are pinned later, at the spec stage. And the business-unit, cross-component layer — a coordinating meta-repo and cross-repo contracts — is a later phase. v1 keeps the whole loop in one repo, where it earns its place first.
