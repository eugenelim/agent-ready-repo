# Single-ladder migration

- **Slug:** `single-ladder-migration` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:repository-work-graph

## Outcome

- **Steerable input:** Reduce the number of vocabularies that describe the same repository work from two to one, and remove the artifacts and folders that only the retired vocabulary needs.
- **Lagging outcome:** The recursive intent graph is the only ladder. Initiative ceases to be a canonical repository artifact and an ownership boundary; the shaping folder's content lives as intents; and nothing points at a vocabulary that no longer exists.
- **Guardrail:** No shaped content is lost in the move — every initiative and shaping document is either extracted to an intent or explicitly retired with its reason recorded. Existing registered work keeps its meaning through the transition, and no dangling reference is created or left behind.

## Opportunity

- **Functional job:** Describe a piece of repository work once, in one vocabulary, and have every consumer agree on what it is.
- **Emotional job:** Stop having to know which of two ladders a thing is on before you can reason about it.
- **Social job:** Present one coherent ontology to a maintainer or an adopter rather than an apparent choice between two.
- **Struggling moment:** The initiative vocabulary survives in four places. `docs/product/initiatives/` still holds `_template.md` and `ini-009-agent-skill-engineering.md`, an initiative document with no intent level. `docs/product/shaping/` still holds `product-vision-INI-001.md` and `ecosystem-overview.md`. `docs/product/initiatives/_template.md` still points at `CONVENTIONS.md §5b` for its altitude hierarchy, and a Shipped spec retired that file, so the definition of "altitude-1" has no surviving home. `workspace.toml` still holds five initiative tables (`ini-002`, `ini-003`, `ini-007`, `ini-009`, `ini-010`) beside the `backlog` table. The strategy intents the initiatives once carried are extracted: `STRAT-0002-platform-core.md` is the former `ini-002` strategy.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- recording the remaining strategic paths (coding-CLI adapters, remote agent runtime, infrastructure and observability, control plane) as captured items rather than intents. Platform core already has `STRAT-0002`;
- retiring `docs/product/initiatives/` once its content has a canonical home, including the template that cites a retired document, and moving the two existing documents out of `docs/product/shaping/`. The `shaping/` folder itself stays: it is the live output directory of the `product-strategy` pack;
- retiring the `ini-*` sections as an ownership boundary, so an intent's product parent comes from `Parent intent:` and its lifecycle state comes from the canonical intent record. Any `workspace.toml` registration is transitional compatibility while [Workspace registry retirement](FEAT-0034-workspace-registry-retirement.md) remains open, never the new ladder's authority;
- reconciling the two vocabularies wherever they are cited, so no artifact refers to an initiative as a canonical level.

It does not own where non-derivable operational coordination state lives after the buckets go — that is `workspace-coordination-reorganization`. During compatibility it may still owe a workspace registration, but its end state depends on [Workspace registry retirement](FEAT-0034-workspace-registry-retirement.md) assigning or removing that responsibility under the four retirement gates. It does not own the identity or ordinal scheme the migrated corpus adopts, which is `intent-identity-and-registration`. It does not re-shape the extracted content: an extraction is faithful, and refreshing a stale bet is a separate act of framing.

## Non-goals

- Deciding where non-derivable coordination state lives after the buckets go: that is `workspace-coordination-reorganization`.
- Choosing the identity or ordinal scheme of the migrated corpus: that is `intent-identity-and-registration`.
- Extracting the remaining strategic paths into intents (owner-approved cut, 2026-11-05).

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether the migration can complete while workspace registration is still a compatibility requirement, and which retirement gate removes that requirement. Dependent on `FEAT-0034`. [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md) D1 answers it: intent registration stops in the release in which every responsibility intent entries feed has a replacement or an accepted removal. Orientation's replacement is the intent navigation delivery brief's slice 1, the others are FEAT-0034 specifications, and lifecycle collection moves need none.
- Whether retiring the shaping folders breaks any consumer. No inventory has been taken.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Assumptions

- Every current initiative and shaping document reduces to an intent at some altitude, a delivery brief, or an explicit retirement. **Partly evidenced** — four of the five known cases have been classified by inspection; the fifth, INI-003's double meaning, has not.
- The ladder can move to canonical intent parentage and lifecycle before the workspace registry retires, using a bounded compatibility registration that does not regain authority over either fact. **Settled; no longer at risk** — `backlog.open` is currently the only initiative-free collection and admits a non-defect entry at `Status: Draft` only, so a Ready or Accepted artifact has no initiative-free compatibility home today. Under RFC-0106, the end state needs no such home, because an intent's lifecycle comes from its own `Status:` and intents stop being registered; until its replacements ship, the constraint stands.
- Retiring the folders breaks no consumer. **Untested** — an inventory of what reads `docs/product/initiatives/` and `docs/product/shaping/` has not been taken.

The compatibility-registration assumption is settled: intent registration has stopped (RFC-0106 D1, `workspace.toml` retirement slice 7), so it is no longer a risk. The one open risk is the Readiness section's **Riskiest assumption:**, that retiring the two folders breaks no reader.

## Readiness

- **Riskiest assumption:** retiring `docs/product/initiatives/` and moving the two `shaping/` documents breaks no reader. Agent-only test: `rg` for those paths finds only records marked historical, and `tests/roster/test_registry_upgrade_notes.py` passes after its path list is updated.
- **Route:** new-spec, one session, after PR 1689 merges (it removes the `ini-*` tables when it deletes `workspace.toml`). Until then only a de-risk read is useful.
- **Verified current truth (2026-11-05):** the two folders hold four files. No script reads them. The only checks on them are `tests/roster/test_registry_upgrade_notes.py` (lines 265, 321, 324, which list the paths) and prose in historical specs, journeys, `docs/product/roadmap.md` and `web/src/content/packs/product-strategy.md`.
- **Scope cut (owner-approved):** extracting the five strategic paths into intents is dropped from this intent. Platform core already has `STRAT-0002`. Adapters, remote runtime, infrastructure and observability, and control plane become one captured item each if a maintainer still wants them.
- **First slice:** move `ini-009-agent-skill-engineering.md` to a brief or retire it with a reason, move the `shaping/` pair into intents or retire them with a reason, and retire `_template.md`, repoint the dead `CONVENTIONS.md §5b` citation, and update the roster test's path list.
- **Agent-only proof:** `rg` finds no live reference to either folder outside records marked historical, and the roster test and `make lint-ruff lint-mypy` pass.
- **Unresolved question 2 answered:** retiring the folders breaks no reader. The one test that names the paths is updated in the same change.

## De-risk result

- **Date:** 2026-11-05. **Ran:** `rg -l` for `product/initiatives`, `product/shaping`, `ini-009-agent-skill` and `initiatives/_template` over the whole repository, excluding the retirement specs and `workspace.toml`; then read each non-record hit.
- **Observed:** 40 files match. The `initiatives/` paths are named only by prose, a roster test (`tests/roster/test_registry_upgrade_notes.py`), historical specs, journeys and the roadmap. The `shaping/` path is a live output location: `packs/product-strategy/pack.toml` sets `output_dir = "docs/product/shaping"`, `packages/agentbundle/agentbundle/workspace_mcp.py` (lines 91 and 109) and its test name the same pattern, and 16 `guides/product-strategy` and pack pages tell users results go there.
- **Verdict:** the assumption only partly holds, so `De-risked` is not set. Retiring the `shaping/` folder would break the `product-strategy` pack. The intent now retires `initiatives/` and moves the two existing `shaping/` documents only. Re-run the `rg` test after that narrower cut.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
