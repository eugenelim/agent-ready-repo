# Graph-powered SDLC

- **Slug:** `graph-powered-sdlc` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-09-19 by eugenelim, on owner authority over a split gate verdict. Revision `3c6ceb8abb357ee2` drew `MALFORMED(children)` on one substantive independent review run and a clean pass on another of the same content; the preceding revision `67a1a0bc4d6cbc56` passed cleanly. Conditions 1–4 and 6 were clean throughout. The lifecycle owner holds this gate, and a review result alone never sets a status.

- **Nonmaterial correction 2026-09-19 by eugenelim, lifecycle owner.** `Unresolved questions`, `Projection` and `Source` were backfilled to meet ADR-0098 D2's admission contract, which this family met only in part because it was framed by `frame-intent` and never admitted through `intake-intent`. `intake-intent` classes a change to projection, unresolved questions or source authority as material, which would return this intent to `Draft`; the lifecycle owner recorded it as nonmaterial because the sections record open matters and provenance that already existed in the artifact, and decide nothing new. Prior review evidence stands.
- **Kind:** opportunity <!-- chain rung: the need this strategy addresses on the opportunity-solution tree; orthogonal to Level -->
- **Level:** product-strategy
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** outcome:ai-native-ecosystem
- **Shaping-reviewed:** 2026-09-19
- **Decomposed:** 2026-09-19 children

## Outcome

- **Steerable input:** Reduce what an agent or a person must rediscover at the start of a piece of work — what exists, at what altitude, under what parent, in what state, constrained by which decisions, and where it lands in delivery.
- **Lagging outcome:** The repository's work, decisions, and delivery state are one navigable graph derived from its own artifacts, so orientation, traceability, and constraint-awareness are reads rather than reconstructions.
- **Guardrail:** Canonical artifacts stay authoritative and the graph stays derived. No tracker's hierarchy becomes the product model, no coordination file becomes a contention point, and deterministic discovery, lifecycle integrity, provenance, dependency checking, and dispatch safety do not weaken.

## Opportunity

- **Functional job:** Know the shape of the work before touching it — what it is part of, what has already been decided about it, and what shipping it means.
- **Emotional job:** Trust that the repository's account of itself is current, because it is derived from the artifacts rather than maintained beside them.
- **Social job:** Show a maintainer, a reviewer, or a stakeholder a defensible account of what is being built and why, in their own tools when they need it.
- **Struggling moment:** Every session reconstructs the same shape by hand, and the reconstruction is not reusable by the next session. Two competing ladders — the recursive intent tree and the initiative bucket — describe the same work in different vocabularies, so even the reconstruction is ambiguous.

## Product-strategy fields

- **Central challenge (diagnosis):** The repository's work is a set of documents, not a graph. Relationships exist — parentage, supersession, delivery mapping, constraint — but only as prose in headers, so nothing can traverse them. Every consumer re-derives, and no two derive the same way.
- **Guiding policy:** Model work, decisions, and delivery as **one recursive intent graph derived from the artifacts**, with exactly one vocabulary. Coordination state keeps only what cannot be derived. Trackers and human views are projections of that graph, never sources.
- **Coherent actions:**
  1. Make the work artifacts a graph — identity, navigation, and delivery traceability.
  2. Make accepted decisions a graph, so constraints can be read rather than rediscovered.
  3. Move operational coordination off a single contended file while keeping dispatch safe.
  4. Project the canonical graph outward to whichever tracker an organisation already runs.
- **Problem / segment sequence:** The repository itself first, because it is the only corpus available to falsify the design; then adopters, who arrive with an empty corpus and no shaping history. Now, because two ladders currently describe the same work and the ambiguity is already producing registration failures.
- **Horizon:** Multi-quarter. Each capability below is independently enterable and independently valuable.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this strategy's outcome and the only party who may accept it.

## Unresolved questions

- The riskiest assumption carries no kill condition and is not claimed as delivered by any child.
- Whether intent-to-code mapping can be extracted upward for organizational portfolio and investment use.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Boundary

Includes the canonical model and its derived surfaces — **reading** the governance record corpus as constraints, where [Platform Core](STRAT-0002-platform-core.md) owns authoring it: intent discovery and registration; identity and typed ordinals; parent and related edges; the accepted decision corpus as constraints; generated graph and status views; mappings from intents to briefs and specs; repository versus personal locations; workspace coordination state; and external tracker projection.

Excludes: implementation mechanism at this altitude; a tracker's hierarchy as the canonical model; wholesale methodology replacement; any persisted graph artifact — the graph is derived from artifact headers on demand, never committed, with the corresponding guardrail that graph metadata lives in preamble fields and never in artifact bodies.

## Riskiest assumption

**Graph-shaped repository state unlocks downstream capability — architecture, specs and implementations that are aware of accepted decisions and can apply them as policy.**

This is the bet the strategy exists to make. Every capability beneath it produces a more coherent model of the work; none of them is worth building if a more coherent model changes nobody's behaviour. If this is wrong, the result is a well-formed graph that no agent consults and no decision is shaped by — correct, maintained, and inert.

It is untested, and the external evidence is unhelpful in the honest direction rather than the encouraging one. [The graph-powered SDLC survey](../research/graph-powered-sdlc-survey.md) found **no published evaluation of a repository-artifact graph** for any of these unlocks; every transferable finding in it is an analogy from an adjacent domain. The one closely-adjacent measured result is negative — a February 2026 evaluation reports plain VectorRAG beating standard GraphRAG for a fraction of the cost — which is why that survey ranks agent grounding last among the opportunities rather than first.

What the survey does support is narrower and worth holding onto: reverse traversal is the one unlock evidenced in every domain it examined, and the repository's own generated-work volume is the measured reason to want it. So the bet is better stated as *which* unlock lands, not whether any does.

**Two assumptions were considered and are not the riskiest.** That a derived graph over header metadata suffices without a persisted index is partly evidenced — a header-only derivation runs in well under a second. And that one vocabulary is achievable is a **dependency with a known shape rather than a risk**: `_TOP_LEVEL_ENTRY_COLLECTIONS` offers only `backlog.open` outside an initiative and it admits `Status: Draft` alone, so every spec at any status, every non-Draft brief, and every terminal intent currently lacks an initiative-free home. Closing that is bounded schema work owned by [Workspace coordination reorganization](CAP-0003-workspace-coordination-reorganization.md), not an open question.

## Assumptions

- A derived graph over header metadata is enough to power orientation, traceability and constraint-awareness, without a persisted index or a service. **Partly evidenced** — a header-only derivation over the current corpus runs in well under a second, roughly an order of magnitude cheaper than the existing whole-file walk.
- One vocabulary is achievable: the initiative ladder can be retired into the intent graph without losing the coordination it currently provides. **A dependency, not a risk** — the shape of the gap is known and enumerated above, and `CAP-0003` and the migration feature carry it.
- The riskiest assumption above. **Untested**, and deliberately not claimed as delivered by any child below.
- Intent-to-code mapping can be extracted upward for organizational use — a portfolio, investment or compliance answer derived from delivery reality rather than re-gathered by hand. **Untested and completeness-requiring**, which puts it on the wrong side of the sparsity split: a portfolio view over a partly-mapped corpus does not read as partial, it reads as the answer. Its precondition is that the mapping is a byproduct of shipping, cited at merge and never reconstructed — retrospective assembly is precisely how requirements traceability became theatre.
- **Knowledge surface:** in-repo doc set (`docs/adr/`, `docs/rfc/`, `docs/product/`, `packs/`), plus two agent-run external desk-research passes recorded in [Graph-powered SDLC — applied survey](../research/graph-powered-sdlc-survey.md). No MCP knowledge tool or internal CLI was present.

### What the research changed

The survey is this strategy's evidence base, and three of its findings bear directly on the guiding policy.

- **The management case is the strategic case, and it is a scale argument.** Every external measurement found was run at one agent, where a capable model can read the prose directly. What prose cannot do is answer across a corpus growing faster than anyone reads it — which items duplicate, which are superseded by shipped work, which are downstream of a decision that just changed. This repository already carries 165 open backlog entries, 184 initiative-queue entries, 484 specs and 338 spec notes at roughly one agent. That is the generated-work problem before any multiplication, and it is the reason to build. It is also the least externally evidenced claim here, so the survey names its falsifier: measure whether generated work is compounding faster than it is closed.
- **Durability comes from a forcing function, not from discipline.** The only graphs that survived decades had mechanical derivation or a publication-time editorial authority. Voluntary upkeep decayed everywhere it was studied — fewer than 2% of repositories with ADRs sustain more than 25 records. A CI gate on dangling and non-reciprocal edges is this repository's substitute for an editor, and it is the only substitute available.
- **Agent value and human value sit in different edges.** Scope and supersession are where an agent's value concentrates; parentage and rationale are where a human's does. The four altitudes are a human-facing orientation structure, and this strategy does not claim them as an agent capability.

Two things the research rules out as unreachable rather than deferred: write-back actions with atomic multi-system effects, and any always-current or incrementally-maintained index. Both need a runtime the charter forbids, and the degraded local version of each is a graph that looks populated and is wrong.

**Not de-risked at this altitude.** The riskiest assumption above carries no kill condition and no probe has run against it. `CAP-0001`'s architectural assumption was tested and survived, but that verdict is about the work-graph capability, not about this strategy's own bet. Re-enter `de-risk-intent` here before treating the strategy as tested.

## Decomposition

Four capability children, each an independent architectural bet with its own de-risk, each pointing back here through `Parent intent:`.

- [Repository work graph](CAP-0001-repository-work-graph.md) — the work artifacts as a graph; carries a surviving de-risk verdict and three feature children.
- [Decision graph](CAP-0002-decision-graph.md) — accepted ADRs and RFCs as navigable constraints.
- [Workspace coordination reorganization](CAP-0003-workspace-coordination-reorganization.md) — operational state off the contended file.
- [External tracker projection](CAP-0004-external-tracker-projection.md) — canonical graph rendered outward.

### Decomposition decisions

- **2026-09-18 — this strategy was extracted above an existing capability, not framed first.** The work began at `repository-work-graph`, which was framed as a capability, briefly promoted to product-strategy, and then returned to capability when the pack's own cut test was applied: identity, navigation and traceability are *architectural slices of one buildable thing*, while decision graph, workspace coordination and tracker projection are *independent value bets*. The first grouping is what a capability parent is for; the second is what a strategy parent is for. This intent is the missing strategy rung that the second grouping had been hanging from incorrectly.
- **2026-09-18 — the decision graph is a capability here, not a governance strategy of its own.** It graphs constraints rather than deliverables, which argued for separating it, but it shares the derivation mechanism and the consumer with the other three, and its value is that architecture, specs and implementations become decision-aware — which is this strategy's guiding policy, not a separate one.
- **2026-09-18 — migration is a feature, not a capability.** Retiring the initiative ladder, retiring the shaping folder, and unifying the vocabulary are bounded, one-time work in service of the single-graph policy rather than a durable capability the repository keeps. It sits under `CAP-0001` as `FEAT-0004`.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
