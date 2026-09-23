# Decision graph

- **Slug:** `decision-graph` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc

## Outcome

- **Steerable input:** Reduce the number of record headers a person or agent must open to learn which accepted decisions constrain an area, what superseded what, and why a call was made.
- **Lagging outcome:** The accepted decision corpus is navigable as a graph derived from record headers on demand, so a working session reads the constraints that apply instead of rediscovering them from prose headers.
- **Guardrail:** The records stay authoritative and immutable; the graph is derived from their headers on demand, never hand-maintained and never persisted. Record bodies are not read to build it. No decision is restated in the view, no edge is invented where the record does not assert one, and an unvalidated edge is not presented as if it were checked. Adding the view changes no record, no authoring skill, and no gate.

## Opportunity

- **Functional job:** Find out what has already been decided about the thing I am about to change, and why, before I change it.
- **Emotional job:** Trust that a decision I am relying on is current rather than superseded, without reading its whole lineage.
- **Social job:** Show a reviewer or a maintainer that a change respects the accepted record, and show where a decision came from when challenged.
- **Struggling moment:** Decisions are records, not a graph. Their relationships live only in prose header fields, so every session that needs the constraints around an area reconstructs them by reading headers — and the reconstruction is not reusable by the next session.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- a read-only view over the accepted decision corpus, **derived from record headers on demand and never persisted**, exposing each record's identity, status, area, reversibility, date, and decision statement where the record carries one;
- the supersession lineage, so a reader can tell a live decision from a superseded or partly-superseded one;
- weaker adjacency from the free-form `Related` field, carried **on the node as unresolved text rather than in the edge set**. Giving an unvalidated entry the same shape as a checked one invites every consumer that walks edges to treat it as one, and the unvalidated entries outnumber the checked ones by roughly ten to one. A consumer that wants to resolve one does so deliberately;
- how a record with a lean header, which carries no decision statement, appears in the view without being misrepresented as richer or poorer than it is.

It does not own the intent corpus or its identity (`intent-identity-and-registration`), the intent graph (`intent-graph-navigation`), the intent-to-delivery mapping (`intent-delivery-traceability`), workspace coordination (`workspace-coordination-reorganization`), or tracker projection (`external-tracker-projection`).

Explicitly out of scope for this child:

- **Changing any record.** ADR bodies are frozen, and this child adds no field and edits no header.
- **Persisting a generated index.** This corpus is derived on demand from record headers like the rest of the graph, for the reasons `intent-graph-navigation` § Settled design decisions records. Nothing is committed and nothing is written to disk, so there is no index to go stale, no generated file to collide on across worktrees, and no second home for a status that `docs/adr/README.md` already owns.
- **A decision-to-file scope index, and any pre-edit conflict gate built on one.** The natural next step is to ask which decisions govern a path being edited, and to warn or block. That needs a machine-resolvable scope link, which the corpus does not have — `Applies to:` is prose. Naming it here as the deliberate next increment keeps it out of a lightweight first cut.
- **Always-on capture, elicitation of missing header fields, or any background process.** Decisions enter this repository through a deliberate, reviewed authoring act. A daemon, watcher, or hook that captures or completes decisions is a different bet and is contrary to the charter's habit-not-infrastructure principle.
- **A hosted or cross-repository decision store.** This repository is one repository and its records are files.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether a read-only view is worth shipping before any gate.
- Not de-risked: no assumption carries a kill condition.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Grounding

Three facts about the current corpus and its tooling, checked rather than assumed. They are why the boundary above is drawn where it is, not open bets.

- The supersession lineage is trustworthy enough to be the backbone. **Evidenced.** `lint-adr-shape.py` enforces ADR-S008 (no shared ordinal across full and partial supersession), ADR-S009 (a cited decision identifier exists in the record the entry names) and ADR-S010 (a supersession entry has its mirrored counterpart), so these edges are typed and checked in both directions.
- `Related` cannot carry the same weight. **Evidenced.** `lint-adr-shape.py` parses `Related` as a field name but defines no rule over it, so those edges are unvalidated, may dangle, and may contain no record reference at all — ADR-0108's own `Related` names a file and a phrase and no record. The edge population is skewed towards exactly this weakest type: of 490 extractable edges across 170 records, **444 are `Related`** (260 RFC, 184 ADR) against **46 supersession** edges (21 `Supersedes in part`, 21 `Superseded in part`, 2 `Supersedes`, 2 `Superseded by`).
- A generated view is the permitted shape. **Evidenced.** ADR-0112 D1 requires an index over a document corpus to be generated or absent, never hand-maintained. ADR-0112 D3 separately pins the existing flat index's columns to `#`, `Title`, `Status` and `Date`, so relationship columns must not be added there; a distinct generated view is the compatible route.

## Research

[Graph-powered SDLC — applied survey](../research/graph-powered-sdlc-survey.md) supports two calls already made here and adds one. It supports carrying `Related` on the node rather than in the edge set — the gated-versus-ungated split in this repository's own corpus (46 checked supersession edges against 444 unvalidated `Related` entries) reproduces the decay pattern the literature predicts. It supports supersession refusal as the cheapest real capability, with a multi-decade working precedent in IETF `Obsoletes`, which survived because a publication-time authority enforces it. What it adds is **negative decisions** — recording a rejected alternative with a discriminating trigger, so an agent does not re-propose what the team already killed. That is the node type with total agent-versus-human asymmetry, and it is not yet in this intent's boundary.

## Assumptions

- The existing header fields are a sufficient node source for a useful first view. **Partly evidenced.** Measured 2026-09-18 across 118 ADRs and 102 RFCs: `Status`, `Date`, `Areas`, `Reversibility` and `Decision-makers` are present on **100%** of ADRs, while `Decision`, `Because` and `Applies to` reach only **61%** because the template carries a deliberate lean-versus-full split. RFCs are far weaker — `Status` at 99% and a decision statement at 41%, with no `Date`, `Areas`, `Reversibility` or `Decision-makers` at all. So node richness is heterogeneous by construction, and the view must render a lean record honestly rather than assume parity.
- A read-only view is worth shipping before any gate. **Untested.** The value of answering "what constrains this" without also blocking a conflicting edit has not been measured here.

**Not de-risked.** No assumption above has a kill condition, and the two that carry measurements are evidenced rather than tested. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent. The riskiest assumption is likely the last one, because it decides whether a lightweight first cut is useful on its own or only as scaffolding for a gate.

The three checked facts that used to sit here are grounding, not assumptions, and the **Grounding** section above owns them.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
