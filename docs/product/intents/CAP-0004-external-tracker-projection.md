# External tracker projection

- **Slug:** `external-tracker-projection` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc

## Outcome

- **Steerable input:** Reduce the hand work needed to show repository work in whichever tracker a stakeholder already uses, and reduce how often a tracker's vocabulary has to be answered by reshaping the repository model.
- **Lagging outcome:** The canonical repository graph can be projected into Linear, GitHub, Jira, or Jira Align without importing each tracker's hierarchy into the product model.
- **Guardrail:** The repository graph stays canonical and the tracker stays a render. A tracker's flatness or depth never becomes the product model, projection never silently changes an accepted or executing local contract, and imported-field authority follows ADR-0077's explicit repo-origin or tracker-origin rules.

## Opportunity

- **Functional job:** Give a stakeholder the view of repository work they can already read, in the tool they already use, without maintaining a second model.
- **Emotional job:** Answer "can you put this in our tracker" without fearing that the answer reshapes the repository's own model.
- **Social job:** Look legible to an organization that runs on a tracker, while keeping the account of the work defensible on its own terms.
- **Struggling moment:** ADR-0019 D5 and ADR-0077 already establish that a tracker is a render and never the source, and `decompose-intent` ships a tracker-projection reference covering none, Linear, and Jira Align. What is missing is the projection from a canonical graph: today a projection is rendered from whatever a decomposition happened to produce, so there is no one canonical shape to project, and each tracker's vocabulary is answered case by case.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- projecting the canonical repository graph onto Linear, GitHub, Jira, and Jira Align;
- how each tracker's own hierarchy vocabulary is absorbed at the projection edge rather than in the product model;
- how imported-field authority and refresh behave for a projected object, consistent with ADR-0077's two origin modes.

It does not own identity or placement (`intent-identity-and-registration`), the derived graph it projects from (`intent-graph-navigation`), the intent-to-delivery mapping (`intent-delivery-traceability`), or operational coordination state (`workspace-coordination-reorganization`). It does not generate tracker objects at this altitude, and it does not decide the mechanism: no profile format, API client, or sync direction is chosen here beyond the accepted one-way rule.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether the four named trackers' hierarchies are all reachable from one canonical graph.
- Whether ADR-0077's repo-origin and tracker-origin modes represent each tracker's authority lifecycle.
- Whether a projection is useful without the status round-trip ADR-0019 D5 forbids.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Assumptions

- The four named trackers' hierarchies can all be reached from one canonical graph, so no tracker needs a rung the graph does not have. **Untested** — `decompose-intent`'s existing reference covers Linear and Jira Align and treats them as opposite ends of a collapse-or-expand axis; GitHub and Jira are unexamined.
- ADR-0077's repo-origin and tracker-origin modes can represent each tracker's authority lifecycle without a source-specific exception. ADR-0077 names that as its own revisit condition, so it is an open bet rather than settled. **Untested.**
- A projection can be useful without round-tripping status, which ADR-0019 D5 forbids. **Untested** against a real stakeholder expectation.

**Not de-risked.** No assumption above has been tested, and no kill condition has been declared for any of them. The parent's surviving verdict covers the parent's own bet, not this one. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
