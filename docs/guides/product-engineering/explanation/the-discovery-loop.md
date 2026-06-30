# The discovery loop — from a raw idea to a build-ready brief

> **Diátaxis: explanation.** Why the discovery loop is shaped the way it is. For the step-by-step, see the how-to [*Run a discovery*](../how-to/run-a-discovery.md) and the tutorial [*Walk a discovery end-to-end*](../tutorials/walk-a-discovery-end-to-end.md); for the slots and roster, the reference [*The discovery sidecar and roster*](../reference/discovery-sidecar-and-roster.md). For the upstream shaping model it builds on, see [*The intent tree*](the-intent-tree.md).

## The problem it solves

A repo set up for engineering agents can take a *brief* and build it (`work-loop`). But turning a **raw idea** into a brief worth building is its own loop — and the expensive failures live there: building the wrong thing, committing to the first idea, shipping a plan that was never validated. The **discovery loop** is that upstream loop, run by the **`discovery-lead`** agent. It is the *peer* of `work-loop`'s downstream loop; the two meet at **G3**.

## The coordinator contract — content, not a runtime

The whole capability is **content**: a `discovery-lead` agent definition, a `discovery-loop` skill, and a carried, versioned sidecar schema. The harness you already run executes them. There is **no new engine, scheduler, service, message bus, or convergence solver** — a spike confirmed none is needed, walking the loop as *one reasoning context editing plain files plus a ~60-line connectedness lint*. What the charter forbids is the harness; we do not ship one.

## Divergence → convergence → validation

The loop is a three-stage arc:

1. **Divergence.** Before committing, `explore-options` generates several candidate product shapes across two axes — **altitude** (a narrow slice ↔ the whole domain) and **mechanic** (draft-and-approve / coordination-layer / knowledge-graph-first / ambient-capture). This is the forcing function against **myopic-greedy commitment** — locking onto the first coherent framing and missing both a higher altitude and a deeper sub-domain.
2. **Convergence.** The chosen spine runs through a lens roster (research, product, UX, architecture, safety) that writes onto a shared **blackboard**, bouncing off each other only through an **open-questions queue — never free-form chat** (the failure mode multi-agent systems thrash on).
3. **Validation.** The brief is emitted as a **connected hypothesis**: every load-bearing assumption carries a **validation hook** (a kill condition + the real-world activity that would confirm it), and every node is labelled **grounded** / **surfaced** / **to-validate**.

## Converged ≠ validated

The load-bearing idea: a converged blackboard is internally *coherent* but **not validated**. Desk-grounding is not validation — only real users confirm demand. The loop makes that a **structural property** of the tree (a validation-status field per node), so a brief cannot quietly present a guess as a fact. `plan-validation` scaffolds the instruments (interview guide, usability-test plan); a human runs them — running the sessions is out of charter.

## Recursion is data, not runtime

Real product work is recursive: an idea ("household assistant") contains sub-ideas ("recipe integration"), each warranting its own divergence → convergence → validation walk. This needs **no state-machine engine**. The pattern is **Hierarchical-Task-Network planning over a blackboard**: a plan tree held as *data*, walked depth-first by one controller that updates status fields. A sub-idea is a node (`parent_id`), not a new project. The honest caveat: the controller choosing the next node *is* a kind of scheduling, so the no-engine win is a **bet on a shallow tree**, gated by depth/breadth bounds; scheduling many concurrent threads stays the harness's job.

## The human stays in three places

The loop pauses at three **consent gates** — G0 (the value seed), G1.5 (the altitude/MVP bet), G2 (the "what"). A gate is a *pause*, not a runtime: the loop writes an option card and waits. The human's answer is a **typed verdict** (approve / approve-with-constraint / redirect / explore-alternatives / abandon / park / extend), written through a channel **the agent has no token for** — so a sign-off cannot be forged. Bounds (rounds, cost, concentration, depth) are pause-and-confirm gates too, never silent stops.

## Where it sits

The discovery loop is the upstream half of a two-loop operating model. It hands a build-ready brief to `work-loop` at G3; `work-loop` builds it; the release loop ships it. It does not replace classic requirements work (BRD/PRD/SRS/RTM) — it maps onto those artifacts, ingests them, and can emit them for sign-off.
