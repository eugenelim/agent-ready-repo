# Intent-to-delivery traceability

- **Slug:** `intent-delivery-traceability` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** repository-work-graph — [Repository work graph](CAP-0001-repository-work-graph.md)

## Outcome

- **Steerable input:** Reduce the effort needed to go from a feature intent to the change that ships it, and back, without reading the corpus or asking the author.
- **Lagging outcome:** Feature intents visibly map to an independently shippable spec or, when coordination requires it, a delivery brief and its child specs.
- **Guardrail:** ADR-0077's projection rule is preserved — a feature projects by shippability and coordination need, so a one-spec brief stays permitted only as a repository projection of cross-repository work. Existing briefs, specs, and their registered memberships keep their meaning, and the mapping is visible without restating any artifact's status.

## Opportunity

- **Functional job:** Follow a shaped outcome down to the change that delivers it, and follow a change back up to the outcome it serves.
- **Emotional job:** Be confident that shaped work has a delivery home, and that an intent with no downstream artifact is visibly unstarted rather than silently lost.
- **Social job:** Show a maintainer or a reviewer that a change is authorized by a shaped outcome, and show an outcome's owner where it stands in delivery.
- **Struggling moment:** The edge barely exists. Measured 2026-09-18 across all 484 specs: **409 (84%) carry no up-edge of any kind**, 29 name a `Brief:`, 32 a `Contract:`, 14 a `Discovery:` — and **not one names a `Parent intent:`**, although `lint-traceability.py` already recognises that field on a spec. A brief's coverage map owns its specs' status from above, nothing joins the two ends, and so an intent with no spec and an intent whose spec shipped read identically from the intent.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- the **up-edge on the spec itself**: a spec references its parent brief and/or its parent intent where one exists, so the edge is readable from the delivering artifact and not only from above. This is the bottom step of the capability's fulfilment rollup — without it a closing spec cannot say which feature it fulfils, and the walk upward has nowhere to start;
- the visible mapping from a feature intent to the independently shippable spec that delivers it;
- the visible mapping from a feature intent to a delivery brief and its child specs when coordination requires that shape;
- how the projection choice between those two is recorded, consistent with ADR-0077 D1 and D2.

It does not own identity or placement (`intent-identity-and-registration`), the graph view that displays the mapping (`intent-graph-navigation`), operational coordination state (`workspace-coordination-reorganization`), or tracker rendering (`external-tracker-projection`). It does not author specs, briefs, or their contracts, and it does not change the delivery loop. It does not decide the mechanism: no field, lint, or generator is chosen at this altitude.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether a feature intent can carry a downstream pointer without restating the spec's or brief's status.
- Whether the existing corpus of feature intents can be mapped incrementally.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Assumptions

- A feature intent can carry a visible downstream pointer without restating the spec's or brief's status, so status keeps the single home `docs/product/AGENTS.md` gives it. **Untested.**
- ADR-0077's shippability-and-coordination projection rule can be made visible from the intent side without changing how a brief or spec is authored. **Untested.**
- The existing corpus of feature intents can be mapped incrementally, so an unmapped legacy intent is shown as unmapped rather than blocking the surface. **Untested.**

**Not de-risked.** No assumption above has been tested, and no kill condition has been declared for any of them. The parent's surviving verdict covers the parent's own bet, not this one. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
