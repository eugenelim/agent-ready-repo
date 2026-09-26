# Intent graph navigation

- **Slug:** `intent-graph-navigation` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph

## Outcome

- **Steerable input:** Reduce the number of files a reader must open, and the amount of shape they must reconstruct by hand, to learn what intents exist and how they relate.
- **Lagging outcome:** People and agents can inspect intent altitude, status, parent, related edges, direct features, and unclassified legacy intents through a graph derived from artifact headers on demand — an agent through a bounded query, a person through a single-file view — with no persisted graph artifact in the repository.
- **Guardrail:** The graph is derived from artifact headers on demand and never persisted, so it cannot go stale while reading as current and adds no generated file for concurrent work to collide on. Graph metadata stays in preamble fields; artifact bodies are never read to build it. The artifacts stay authoritative, status keeps its single home, and an unclassified legacy intent is shown as unclassified rather than given an inferred altitude.

## Opportunity

- **Functional job:** See the whole body of repository work at once — what exists, at what altitude, under what parent, next to what, and in what state — and find the part that matters now.
- **Emotional job:** Trust the view, because it is derived from the same files that hold the work.
- **Social job:** Hand a maintainer or a reviewer one place to look, instead of a list of files and an explanation of how to read them.
- **Struggling moment:** The shape is mostly unrecorded rather than merely unindexed. Of 130 intent files, 119 carry a `Level:` and only 9 carry a `Parent intent:`, so a reader cannot tell a direct feature from an unclassified legacy intent without reading each file. `lint-traceability.py` already derives a graph from the artifacts — 599 nodes, 85 edges — but it is a structural-orphan lint rather than a navigation surface, and it recognizes an intent as a graph node only when it carries `Kind: outcome`, `Kind: opportunity`, or `Level: capability`.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- the graph over the intent corpus, **derived from artifact headers on demand and never persisted**, and what it must expose: altitude, status, parent, related edges, direct features, and intents that carry no classification;
- the **two surfaces over that one derivation**: a bounded query that returns identities, header facts, edges and paths but never artifact bodies, and a human view emitted on demand as a single self-contained file to a scratch location, leaving no repository footprint. The view is a consumer of the derivation, never a second source of truth;
- the view's design route — `analytical-design` owns its structure and widget hierarchy, `interaction-design` its behaviour, and `frontend-engineering` the single-file build; `workspace-design` is the alternative owner if it proves to be a sustained-work surface rather than a read-and-act one;
- how a related-intent edge is recorded on the artifact and read into the view;
- how an unclassified legacy intent is surfaced without inventing an altitude for it.

It does not own identity or placement (`intent-identity-and-registration`), the downstream mapping to a brief or spec (`intent-delivery-traceability`), operational coordination state (`workspace-coordination-reorganization`), or rendering the graph into a tracker (`external-tracker-projection`). It does not decide the mechanism: no generator, format, or hosting surface is chosen at this altitude.


**Inbound 2026-09-24 — a second consumer already builds part of this graph, and the convergence is recorded here because nothing re-reads that consumer's boundary when this intent is shaped.** [FEAT-0005](FEAT-0005-lifecycle-and-closure.md) § Boundary was amended that day to move eligibility computation into that child, because this intent is `Status: Draft` with `Decomposed:` absent and its closure check could not wait. That child may build an **in-memory descendant set** by inverting declared up-edges, bounded by three conditions that [FEAT-0005](FEAT-0005-lifecycle-and-closure.md) § Boundary states and owns. They are deliberately not reproduced here — read them there, because a copy would drift the moment that section is amended. Persistence, publication and any surface a second consumer reads remain this intent's, undiminished, and **no ordering edge runs in either direction**. When this capability lands, treat that child's per-decision resolution as a candidate consumer to absorb rather than a rival to leave standing — otherwise the repository keeps two independent edge-inversion implementations.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether an intent recording neither parent nor altitude is a permanent first-class category rather than a defect to migrate away.
- Whether a related-intent edge can be recorded without becoming a dependency edge.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Hard dependency

This child depends on the cross-artifact reference grammar owned by [`intent-identity-and-registration`](FEAT-0001-intent-identity-and-registration.md). It is the one real dependency in this family, and it was discovered after the family was cut.

`resolve_endpoint` in `lint-traceability.py` resolves a bare-slug pointer by suffix-matching every node id and choosing among multiple hits by sort order, so an ambiguous pointer produces a wrong-but-stable edge rather than an error. The corpus already holds **6 cross-type slug collisions**: two shared between an intent and a brief, four between an intent and a spec. Four of those are latent only because feature intents are not graph nodes — and making them nodes is exactly what this child does, so this child activates the ambiguity it would then suffer from.

One of the six already fired during this family's shaping, taking `lint-traceability` to exit 1 on a self-referential brief edge. That is the failure mode at one collision; this child would expose six.

This dependency is recorded here and in the parent's decomposition log rather than as a `needs` edge, because the intended delivery order already places the grammar first and a blocking edge would add nothing the order does not already give.

## Settled design decisions

Decided 2026-09-18 by the owner, after two independent design passes that disagreed on the central question. Recorded here because they constrain this child and its two siblings; the reasoning that is specific to one sibling sits on that sibling.

### The graph is derived on demand and never persisted

No generated index file is committed, and none is written to disk. The graph is derived from artifact headers each time it is asked for, which is ADR-0112 D1's **absent** branch rather than its generated branch: there is no index, so there is nothing to go stale.

Four reasons, each independently sufficient:

- **Cost is not the constraint.** A header-only derivation over the whole corpus takes well under a second, roughly an order of magnitude cheaper than the existing whole-file walk in `lint-traceability.py`. The argument for persisting rested on the expensive walk's cost, which is an artefact of reading whole files rather than a property of deriving the graph.
- **The runner objection is already settled.** ADR-0006 establishes that adopters have no guaranteed Python runtime, which appears to forbid a derive-on-demand script. ADR-0007 narrowed exactly that: D1 ships such a script to adopters as a skill script, D2 makes it agent-invoked rather than fail-closed, D3 keeps the fail-closed gate inside this catalogue, and D4 states the narrowing explicitly. ADR-0006 constrains hooks and gates, not agent-invoked scripts, and pack skills already ship many of them.
- **A committed index cannot be kept untracked in an adopter repository.** No pack seeds a `.gitignore`, so the disposable-local-accelerator route is unavailable downstream. A generated graph would have to be committed, which makes collision unavoidable rather than mitigable.
- **A committed generated file is a contention surface, and this work exists to remove one.** Concurrent work across multiple worktrees would each regenerate it, so every merge carries a conflict on a file nobody authored. `lint-generated-path-ownership.py` would also require it to declare exactly one producer, on the principle that no generated projection is an authoring dependency.

Two consequences follow and are not separately decided. Status keeps the single home `docs/product/AGENTS.md` gives it, because there is no second generated projection that could own it — a derived answer echoes the artifact's status and never caches it. And there is no index location to choose.

### Graph metadata lives in headers, never in bodies

This is the constraint that keeps the decision above true, so it is a guardrail rather than a preference. Derivation reads each artifact's preamble fields and stops; artifact bodies are more than an order of magnitude larger than their headers and are never read to build the graph. Any future graph metadata — related edges, altitude, area, lifecycle — is added as a preamble field. **If graph metadata ever moves into prose, the cost model inverts and the no-persistence decision has to be reopened.** That is the condition that would falsify it.

### The query and the human view are two surfaces over one derivation

They have different consumers and different shapes, and conflating them makes the agent surface unbounded — an agent asking about one node would pay whole-corpus cost.

- **The query** answers a bounded question and returns node identities, header facts, edges and paths, never bodies; the reader opens the artifact for detail. "Show me every in-flight capability" is a query, not a view.
- **The human view** is a **single self-contained file, emitted on demand** to a scratch location rather than into the repository, so it leaves no tracked or untracked footprint and needs no second distribution surface. It is a consumer of the derivation and never a second source of truth.

The view is a designed surface, not an incidental dump. Its structure and widget hierarchy route through `analytical-design`, which owns how a view carries a reader from a status signal to a diagnostic to an action; its interactive behaviour routes through `interaction-design`; and the single-file build is `frontend-engineering`'s, since its primary output is HTML, CSS and JS. If the view turns out to be a sustained-work surface rather than a read-and-act one, `workspace-design` is the alternative owner — the two skills' scopes overlap here and the call belongs to whoever shapes the view.

### Two hazards the implementation must respect

- **Do not reuse the discovery sidecar's filename or `schema_version` namespace.** `discover_sidecar` in `lint-traceability.py` discovers `_state/traceability.json` through three tiers, the last a bounded tree-wide glob and never a hardcoded path, and `load_sidecar` then treats what it finds as **authoritative**, replacing artifact derivation. A derived graph written to that name anywhere in the tree would make the lint read this capability's own output as authority — a control that cannot fail.
- **Reuse that sidecar's vocabulary, though.** Its node and edge shape is already defined and already consumed, so the derived in-memory graph should speak the same words at a different scope rather than inventing a rival vocabulary.

## Assumptions

- ADR-0112 D1 applies here: an index table over a document corpus is generated from that corpus or does not exist, so a hand-maintained intent index is not an option. This is an accepted decision rather than an open bet, and it constrains the shape rather than needing a test.
- An intent that records no parent and no altitude is a **permanent first-class category**, not a backlog to burn down, so the view must represent unclassified honestly rather than compensate for its absence. This is structural, not a property of today's corpus: ADR-0033 D2 keeps `Level` an open field that no lint closes, and `decompose-intent`'s retroactive-parent affordance is an offer that never blocks, so an unparented intent stays valid indefinitely. Today's low parent coverage is evidence that the category is occupied, not a target to drive to zero. **Untested** is whether a view is useful while the category is large.
- A related-intent edge can be recorded on the artifact without turning it into a dependency edge that a reconciler reads as blocking. **Untested.**
- The typed reference grammar exists before feature intents become graph nodes. **This is a hard dependency on** `intent-identity-and-registration`, not an assumption this child can test on its own.
- A generated view can expose altitude and status without restating either, so status keeps the single home `docs/product/AGENTS.md` gives it. **Untested.**

**Not de-risked.** No assumption above has been tested, and no kill condition has been declared for any of them. The parent's surviving verdict covers the parent's own bet, not this one. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
