# Walk a discovery end-to-end

**What you'll build:** A complete discovery artifact set — decision brief, intent tree, journey maps, ordered backlog, and validation plan — by running the full discovery loop from a raw product idea to a G3 handoff.
**Prerequisites:** `product-engineering` pack installed; a harness that supports human-in-the-loop gate pauses with an append-only decision log that the agent cannot edit.
**Time:** 60 minutes (nine guided steps covering G0 through G3, with three gate decisions and one rejection-recovery scenario).

> **Diátaxis: tutorial.** A single guided path you can follow start to finish. By the end you'll have run one full discovery — from a raw idea to a ratified decision brief handed to `work-loop` — and seen each gate, a divergence, a rejection/recovery, and the validation hooks. For the *why*, read the explanation [*The discovery loop*](../explanation/the-discovery-loop.md) afterward; for the slot shapes, the reference [*The discovery sidecar and roster*](../reference/discovery-sidecar-and-roster.md). This walk uses a household-assistant example throughout; substitute your own idea and the steps are identical.

**Before you start:** install the `product-engineering` pack, and run in a harness that can pause for human input and write your verdict into a store the agent cannot edit (the discovery loop relies on that channel — see the explanation).

## 1. Start the loop

Give `discovery-lead` one prompt:

> *Use the discovery-loop to scaffold the product vision for a household executive-assistant AI — diverge on the product shape first, then converge to a decision brief, and flag what needs validation.*

The loop first **scans for existing discoveries** (none yet), then scaffolds a new initiative: it copies the plan-tree template into `docs/discovery/household-assistant/_state/` and opens at **G0**.

## 2. Ratify the value seed (G0)

`frame-intent` writes a `product-vision` intent slot — *an assistant that helps a household run food, calendar, vendors, and budget by drafting and acting only on approval*. The loop pauses with an **option card** and waits. You read it and reply **approve**. The verdict + your rationale land in the (append-only) decision log.

## 3. See the divergence (pre-G1.5)

This is the step that earns the loop its keep. `explore-options` generates candidate shapes across **altitude × mechanic** — for example:

| Candidate | Altitude | Mechanic | Riskiest assumption |
| --- | --- | --- | --- |
| Kitchen draft-and-approve | narrow-slice | draft-and-approve | users want approval-gated meal drafting |
| Whole-household coordinator | whole-domain | coordination-layer | one assistant can span calendar + travel + budget |
| Knowledge-graph-first | whole-domain | knowledge-graph-first | a household will maintain a structured graph |

The narrow kitchen slice is the *myopic* default; divergence forces the higher altitude (the whole household) and a deeper sub-domain (meal → recipe → ingredient → sourcing) onto the table. The not-chosen candidates are **retained** as `parked`/`rejected` with rationale — revivable later.

## 4. Make the altitude bet (G1.5)

The loop **surfaces the altitude bet to you** — it is a value/scope call, not something a referent decides. You pick **whole-household coordinator**. `frame-domain` then grounds *how a household actually coordinates* (wrapping `research`) and writes the **scope boundary** — the MVP out-of-scope register. You **approve-with-constraint**: "MVP excludes third-party fulfillment." The loop records the constraint and does not advance until the reduced surface re-converges.

## 5. Converge through the lenses

On the chosen spine, the lenses run as parallel writers onto the blackboard — product (`decompose-intent`), UX (`map-customer-journey`, `map-screen-flow`), tech (architecture, contracts) — bouncing off each other only through the **open-questions queue**. The security lens raises an open question (OQ): *approved-learning needs an audit trail.* The controller resolves it by adding an `audit-view` screen + an `audit` service — no agent-to-agent chat.

## 6. Watch a rejection cascade (recovery)

Suppose a `fulfillment` screen slipped in despite the G1.5 constraint. At reconcile, the controller (or your `redirect`) rejects `cap.external-fulfillment`. The loop **shows you the blast radius first** (`screen:fulfillment` + `service:fulfillment` will go stale), waits for your confirm, then **walks the traceability out-edges**, marks those slots `stale`, drops their edges, and **re-runs only the UX lens** on the reduced surface. The edge set scoped the blast radius — that is why the matrix is typed.

## 7. Self-coverage, then the reviewers (pre-G2)

The loop runs the full **self-coverage gate** (pre-mortem, the discovery-risk taxonomy, scenario-variation, fresh-context, domain-grounding, resolve-vs-surface) and writes a **coverage record**. Then the **required** discovery reviewers fire as forked-context lenses: `discovery-threat-reviewer` (threat model + compliance) and `discovery-reliability-reviewer` (failure modes + observability). The traceability lint reports **no orphans** — every node has a producer and a consumer.

## 8. Ratify the brief (G2)

`discovery-lead` renders the blackboard into a **decision brief** — emitted as a **connected hypothesis**: each load-bearing assumption carries a validation hook (kill condition + the real-world activity, scaffolded by `plan-validation`), and every node is labelled **grounded**, **surfaced**, or **to-validate**. The brief carries the required **success-metrics / North-Star slot**. You read it, adjudicate the one value tension the lenses surfaced, and **approve**.

## 9. Hand off to the build loop (G3)

The brief decomposes into an **ordered, dependency-aware backlog**; `loop-cohort` orders it; `work-loop` pulls the first item. You're done — you turned a raw idea into a build-ready brief, and the audit trail (the decision log + coverage record) records every gate.

## What you have now

- A committed `docs/discovery/household-assistant/` with the decision brief, the intent tree, the journey/blueprint/screens, and the backlog.
- A validation plan naming what still needs real users to confirm — because *converged ≠ validated*.
- Parked sub-ideas (e.g. recipe integration) you can resume any time with *Resume the parked `recipe-integration` sub-idea.*

To go deeper on any stage, re-run it with a targeted prompt (see the how-to [*Run a discovery*](../how-to/run-a-discovery.md)).
