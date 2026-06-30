# How to run a discovery end-to-end

> **Diátaxis: how-to.** A goal-oriented walk through the discovery loop. For *why* it is shaped this way, see the explanation [*The discovery loop*](../explanation/the-discovery-loop.md); for a fully worked example, the tutorial [*Walk a discovery end-to-end*](../tutorials/walk-a-discovery-end-to-end.md); for the slots and roster, the reference [*The discovery sidecar and roster*](../reference/discovery-sidecar-and-roster.md).

You have a raw product idea and you want a ratified, build-ready decision brief — without skipping the thinking. Install the `product-engineering` pack, then:

## The one-prompt form (recommended start)

You do **not** need to break the idea into pieces up front. Name it and ask `discovery-lead` to scaffold it:

> *Use the discovery-loop to scaffold the product vision for a household executive-assistant AI — diverge on the product shape first, then converge to a decision brief, and flag what needs validation.*

That single prompt exercises the whole arc: the loop **diverges** into candidate shapes, **surfaces the altitude bet** to you at G1.5, **converges** the one you pick, and **emits a provisional spine** with validation hooks. You answer at three gates; the loop does the rest.

## Answer at the three consent gates

- **G0 (the value seed)** — confirm the outcome is worth pursuing.
- **G1.5 (altitude / MVP)** — this is the load-bearing call: pick the altitude (the narrow slice, or the whole domain) and the MVP boundary, with the candidate shapes as your referent.
- **G2 (the "what")** — ratify the decision brief and adjudicate any value conflict the lenses surfaced (security says no, product says ship).

Your answer is a **typed verdict**, not just yes/no — you can `approve`, `approve-with-constraint` (a scope cut), `redirect`, `explore-alternatives` (reopen divergence), `park`, `abandon`, or `extend` (past a bound). Any answer that would invalidate work **shows you the blast radius first** and waits for your confirmation.

## Targeted phase prompts (redo or deepen one stage)

> - *Diverge only: give me 4–5 candidate product shapes across altitude × mechanic, each with its riskiest assumption — don't converge yet.*
> - *Take the chosen spine to a decision brief, and emit the validation plan (each assumption → kill condition → the real-world activity that would confirm it).*

## Recurse into a sub-idea

A sub-idea is a **node on the same tree**, not a separate project:

> *Recurse into a sub-idea: run a full divergence walk on **recipe integration** as a sub-idea of the household assistant — it becomes a resumable node, not a new discovery.*

The loop walks it depth-first under the same gate ladder and the same outer cap. Park it (`park`) and it persists in the sub-idea index, resumable later.

## Resume — the loop checks before it starts

On a *start* request, `discovery-lead`'s first action is to **scan for in-progress or parked discoveries and offer to resume** before scaffolding a new tree:

> **You:** *Start a discovery for a household assistant.*
> **Loop:** *You have 1 discovery in progress (`household-assistant`, paused at G2) and 2 parked sub-ideas. Resume one, or start new?*

To resume directly: *Resume the `household-assistant` discovery.* The loop loads the workspace, re-runs the connectedness lint, and drops you back where you left off.

## Fold in existing requirements

If you already have a BRD / PRD / SRS, **seed the loop with it** rather than starting from scratch: hand it to `receive-brief` + `frame-intent`'s brownfield ingest. The loop then validates and enriches it — `frame-domain` grounds it, the lenses add the journey/architecture the doc lacks, `de-risk-intent` surfaces the assumptions it states as fact. The **traceability slot serves as your RTM**. Where governance needs a formal BRD/SRS/RTM with sign-off back out, the loop projects its brief + traceability matrix through the converters (md-to-office) path — not a discovery skill. Full crosswalk: the discovery-loop skill's `references/requirements-crosswalk.md`.

## When it hands off

At **G3** the brief decomposes into an ordered, dependency-aware backlog (parked sub-ideas carried as first-class entries); `loop-cohort` orders it; `work-loop` pulls one item at a time. The brief carries a **required success-metrics / North-Star slot** — it cannot reach G3 without a done-criterion the build loop can iterate against.
