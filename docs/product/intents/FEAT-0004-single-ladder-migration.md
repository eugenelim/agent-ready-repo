# Single-ladder migration

- **Slug:** `single-ladder-migration` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** repository-work-graph — [Repository work graph](CAP-0001-repository-work-graph.md)

## Outcome

- **Steerable input:** Reduce the number of vocabularies that describe the same repository work from two to one, and remove the artifacts and folders that only the retired vocabulary needs.
- **Lagging outcome:** The recursive intent graph is the only ladder. Initiative ceases to be a canonical repository artifact and an ownership boundary; the shaping folder's content lives as intents; and nothing points at a vocabulary that no longer exists.
- **Guardrail:** No shaped content is lost in the move — every initiative and shaping document is either extracted to an intent or explicitly retired with its reason recorded. Existing registered work keeps its meaning through the transition, and no dangling reference is created or left behind.

## Opportunity

- **Functional job:** Describe a piece of repository work once, in one vocabulary, and have every consumer agree on what it is.
- **Emotional job:** Stop having to know which of two ladders a thing is on before you can reason about it.
- **Social job:** Present one coherent ontology to a maintainer or an adopter rather than an apparent choice between two.
- **Struggling moment:** The same body of work is described twice and the descriptions disagree. INI-001 is a product vision living under `shaping/`; `ini-002-initiative-brief.md` is a `Level: product-strategy` intent living under `intents/`; INI-009 is an initiative document with no intent level at all; and INI-003 names two different things in two namespaces. The initiative template points at `docs/CONVENTIONS.md §5b` for its altitude hierarchy, and that file was retired by a Shipped spec, so the definition of "altitude-1" has no surviving home.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- extracting the remaining strategic paths — platform core, coding-CLI adapters, remote agent runtime, infrastructure and observability, control plane — from the initiative sections and the shaping overview into intents at their true altitude;
- retiring `docs/product/initiatives/` and `docs/product/shaping/` once their content has a canonical home, including the template that cites a retired document;
- retiring the `ini-*` sections as an ownership boundary, so an intent registers directly and its product parent comes from `Parent intent:` while its lifecycle state comes from the workspace record;
- reconciling the two vocabularies wherever they are cited, so no artifact refers to an initiative as a canonical level.

It does not own where operational coordination state lives after the buckets go — that is `workspace-coordination-reorganization`, and this feature depends on it for the registration half. It does not own the identity or ordinal scheme the migrated corpus adopts, which is `intent-identity-and-registration`. It does not re-shape the extracted content: an extraction is faithful, and refreshing a stale bet is a separate act of framing.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether registration without an initiative bucket is achievable. Dependent on `CAP-0003`.
- Whether retiring the shaping folders breaks any consumer. No inventory has been taken.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Assumptions

- Every current initiative and shaping document reduces to an intent at some altitude, a delivery brief, or an explicit retirement. **Partly evidenced** — four of the five known cases have been classified by inspection; the fifth, INI-003's double meaning, has not.
- Registration without an initiative bucket is achievable. **Untested here and dependent** — `backlog.open` is currently the only initiative-free collection and admits a non-defect entry at `Status: Draft` only, so a Ready or Accepted artifact has no initiative-free home today. This is the concrete blocker the migration must clear.
- Retiring the folders breaks no consumer. **Untested** — an inventory of what reads `docs/product/initiatives/` and `docs/product/shaping/` has not been taken.

**Not de-risked.** No assumption above carries a kill condition. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent. The riskiest is likely the second, because it is the one that is already producing failures rather than merely predicted to.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
