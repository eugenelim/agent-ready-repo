# Recursion, state, and resource management — research

> RESEARCH NOTE (RFC-0053). Grounds two things the body asserts: (1) that **recursive,
> multi-level discovery needs no state-machine engine** (Decision 1's recursion pressure test),
> and (2) the **right shape for the round cap + cost budget under recursion** (Decision 4).
> Desk research from the main thread, 2026-06-29/30 (subagent web is blocked here — see the
> repo's reference note on that).

## 1. Recursion is native to product discovery (not an edge case)

Teresa Torres's **opportunity-solution tree** (introduced 2016; *Continuous Discovery Habits*,
2021) is **recursive by construction**: an outcome branches into opportunities, which branch into
**sub-opportunities**, which branch into experiments/solutions. "Parent opportunities and child
opportunities… opportunities can be broken down into smaller sub-opportunities that are more
manageable." So a sub-idea ("add recipe integration") spawning its own exploration is the *normal*
case, not a special one — which is why a flat "one idea → one brief" model under-serves.
[Torres, Product Talk — `https://www.producttalk.org/opportunity-solution-trees/`]

## 2. Does recursion need a state-machine engine? No — it *strengthens* the no-engine claim

**The proven pattern is Hierarchical-Task-Network planning over a blackboard.** HTN solves a complex
task by **recursively decomposing** it into a *plan tree* (data), which a **single controller** walks
depth-first — interleaving decomposition and execution, selecting the next task, applying a method if
compound, an operator if primitive, updating state on the blackboard. The blackboard pattern: "a
central data store updated by higher-level reasoning… lower-level agents follow the posted plans." So
the "state machine" is **data the controller reads** (a tree + per-node status), not an executed
engine. [Hierarchical Multi-Agent Systems taxonomy, arXiv:2508.12683; HTN literature]

**Building it as an explicit nested state machine would be the wrong move on the merits.** The
behavior-trees-vs-finite-state-machines literature finds FSMs don't scale to nested complexity:
adding/removing states forces reworking many transitions, and **hierarchical FSMs "shift the
modularity problem to inner layers"** with hand-crafted hierarchies — which is exactly why robotics
and games moved to behavior-trees / data-driven control for anything that grows. [Comparison between
Behavior Trees and Finite State Machines, arXiv:2405.16137]

**Conclusion (feeds Decision 1):** recursion is handled by *recursive data (the plan tree) + one
controller + per-node status*, **no engine** — and an explicit nested-FSM engine would actively hurt.
The contract therefore adds **data, not runtime**: `parent_id` nesting, a per-node status lifecycle,
and a sub-idea index.

## 3. Resource management under recursion — the cap/budget shape (feeds Decision 4)

Once sub-ideas spawn sub-walks, the round cap + cost budget (Decision 4) must say *how they apply to
a tree*. Three viable shapes:

| Option | Shape | Pros | Cons |
| --- | --- | --- | --- |
| **A. Flat per-initiative budget** | one `cost_budget` for the whole tree; global `cost_spent`; hard stop → stall + surface | dead simple; one number; the real safety valve (total spend on one idea) | a deep branch can **silently drain** it before siblings are seen; coarse — you learn only at global exhaustion |
| **B. Nested per-sub-walk shares** | each sub-walk gets a pre-allocated sub-budget; exhausting a share stalls that node | hard per-branch bounds | **share-allocation problem** — a depth-first single controller discovers sub-ideas *as it goes*, so it can't sensibly pre-split a budget; most accounting; over-built for this topology |
| **C. Flat budget + per-node spend + concentration-surface + structural bounds** ★ | one enforced `cost_budget` (A), **plus** each node records its own `cost_spent` (observability), **plus** a *concentration threshold* that surfaces when one sub-walk exceeds a configurable fraction of the budget, **plus** structural depth/breadth caps on the tree | keeps A's simple enforcement; prevents the silent-drain via a **reactive surface** (no pre-allocation); bounds tree *shape* against nesting explosion; **reuses the existing cascade circuit-breaker "surface on threshold" pattern** | a threshold + two structural counters more than A — but all cheap, data-only |

**Why C over B for this architecture.** B's pre-allocated shares assume you know the sub-tree up
front; a **depth-first single controller** (the HTN pattern, §2) discovers sub-ideas incrementally, so
pre-splitting is guesswork. C gets B's protection (no silent drain) *reactively* — surface when one
branch dominates spend — which fits discover-as-you-go and mirrors the security contract's
**cascade-invalidation circuit-breaker** (surface when fan-out exceeds a threshold) rather than
inventing a new mechanism.

**The unifying behaviour: every bound is a pause-and-confirm/override gate — never an auto-terminal.**
The loop **never silently stops *or* silently continues** at a bound. On hitting *any* of the bounds
below it **pauses and surfaces the situation + the options**, and the human picks — reusing D3's
verdict machinery plus one new verdict:

- **extend / override** *(new verdict)* — grant more budget/rounds (or lift the bound) and continue;
- **narrow** — `approve-with-constraint`: cut scope so it can converge within the existing budget;
- **park** — defer the node (it's remembered, D3 persistence);
- **abandon** — kill it.

This makes "stall-at-cap" not a terminal dead-end but **another consent gate** (Decision 3), which is
why it composes cleanly with resume: a paused-at-bound initiative resumes once the human overrides or
narrows.

**Recommended shape (C), concretely — all `meta`/per-node counters, no runtime; every bound pauses
for confirm/override:**
- **Per-initiative enforcement:** one `cost_budget` + `round_cap`; on hit-with-unconverged → **pause
  + surface** the extend/narrow/park/abandon choice (not a silent `stalled` walk-away).
- **Per-node convergence round cap:** each sub-walk's convergence loop is bounded by `round_cap`; the
  initiative-level cap bounds the whole; either hit → pause + confirm/override.
- **Observability:** each plan-tree node records `cost_spent` (which branch is eating the budget).
- **Concentration bound:** when a single sub-walk's `cost_spent` exceeds a configurable fraction
  (default ~40%) of the budget → **pause + surface** ("recipe-integration is dominating the budget —
  extend / cap / park?") before it drains the rest.
- **Structural bounds:** max sub-walk **depth** + max **open sub-ideas** (breadth); hitting either →
  pause + confirm/override — the cheap guard against nesting explosion (the HFSM lesson, §2).

So `stalled-at-cap` is recorded as a **paused-awaiting-human** state with a typed option card, not a
terminal stall. Defaults (round cap, budget, ~40% concentration, depth/breadth) are tunable at the
implementing spec; the *shape* (C) + the *pause-and-confirm/override at every bound* is what Decision 4
should adopt.

## Sources

- [Torres — Opportunity Solution Trees](https://www.producttalk.org/opportunity-solution-trees/)
- [A Taxonomy of Hierarchical Multi-Agent Systems (HTN + blackboard), arXiv:2508.12683](https://arxiv.org/abs/2508.12683)
- [Comparison between Behavior Trees and Finite State Machines, arXiv:2405.16137](https://arxiv.org/abs/2405.16137)
