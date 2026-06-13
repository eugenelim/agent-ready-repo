# The intent tree — level-agnostic product shaping

> **Diátaxis: explanation.** Why the `product-engineering` pack shapes work the way it does. For the step-by-step, see the how-to *Shape a feature intent*; for field definitions, the reference *Intent fields and modes*.

## The problem it solves

A repo set up for engineering agents can take a *brief* and build it (`receive-brief` → `new-spec` → `work-loop`). But where does the brief come from? The expensive product failures live *upstream* of the brief — building the wrong thing, un-validated bets, requirements with no outcome. The `product-engineering` pack is that upstream, expressed as habits rather than infrastructure.

## One artifact, every level

The pack has a single artifact: the **`intent`** — a level-tagged statement of an outcome and the opportunity behind it. The insight that makes it work is that a *capability intent*, a *feature intent*, and a *PRD* are not three artifact types. They are the same artifact at different **levels**; a PRD is just a feature intent written as a document. So you never choose which to write — you write an intent at the level you're operating at, and it forms a recursive tree whose leaf is a shippable spec:

```text
  intent (capability)
      ├── intent (feature)
      │       ├── intent (feature)
      │       └── spec / slice (leaf) ──► core: receive-brief → new-spec → work-loop
      └── intent (feature)
              └── spec / slice (leaf) ──► core: receive-brief → new-spec → work-loop

  same artifact at every level — it just stops recursing when the leaf is
  a spec your delivery loop can build.
```

Two things fall out of the recursion. **Decomposition** produces the *next level down*, one level at a time — deep at business-unit scale, often one level at app scale. And **assumptions are de-risked per intent at its own level** — capability bets are architectural/adoption questions, feature bets are desirability questions, and the same `de-risk-intent` habit handles both.

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
