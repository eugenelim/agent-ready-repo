# Workspace coordination reorganization

- **Slug:** `workspace-coordination-reorganization` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc

## Outcome

- **Steerable input:** Reduce the share of coordination edits that must land in one large shared registry file, and reduce the rebase conflicts those edits produce.
- **Lagging outcome:** Repository coordination no longer depends on one large, frequently edited `workspace.toml`, while dispatch, provenance, lifecycle, and dependency safety remain intact.
- **Guardrail:** Every current reconciliation verdict, dependency check, provenance check, and dispatch decision keeps working, including for the legacy compatibility records the file retains deliberately. No entry loses its identity, and no reader, writer, projection, fixture, or external adopter is broken without being inventoried first.

## Opportunity

- **Functional job:** Register, update, and close coordination state for a piece of work without editing the same file every other concurrent author is editing.
- **Emotional job:** Land a registration without expecting a rebase conflict, and resolve one without wondering whether the resolution was semantically right.
- **Social job:** Show that the coordination mechanism scales with the number of people and agents working at once, rather than serializing them.
- **Struggling moment:** `workspace.toml` is 1,559 lines and every registration edits it. Over the 30 days measured on 2026-09-13, 20 of 51 rebases that had to replay a `workspace.toml` edit conflicted. How many of those resolutions were performed incorrectly is not measurable from a textual replay, so the quality cost of the conflicts is unknown rather than zero.

## Boundary

Inherits the parent's outcome, boundary, and exclusions. Within them, this child owns:

- where non-derivable operational coordination state lives and how it is written, given that the parent's de-risk established the artifacts can hold the inventory and the graph;
- entry identity, duplicate handling, lifecycle collection membership, precedence, dependency validation, and stable tie-breaking for whatever shape that state takes;
- the compatibility inventory of every reader, writer, projection, fixture, and external adopter that the change must not break.

It does not own the intent corpus's identity or placement (`intent-identity-and-registration`), the derived graph (`intent-graph-navigation`), the intent-to-delivery mapping (`intent-delivery-traceability`), or tracker projection (`external-tracker-projection`). It does not decide the mechanism: whether the state is assembled into a checked-in compatibility file, loaded directly from fragments, or reached through a non-positional registry is a solution choice, not part of this outcome.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether the non-derivable operational state is small enough that relocating it beats living with the hot file.
- Whether every reader, writer, projection, fixture and external adopter of `workspace.toml` can be inventoried.
- Whether array order is load-bearing beyond index-based duplicate identity.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Constraints inherited from the parent's de-risk

Both were found while testing the parent's assumption and are recorded here so they travel with the work.

- **C1 — position is an in-run join key.** `_surviving_work` in `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` matches closeout verdicts by `(collection, entry_index)` rather than by any entry value, because no value is unique: a legacy `"spec/x"` string and a canonical `{path = "spec/x", kind = "defect"}` entry share a raw path. Both sides walk the same in-memory arrays in one parse and agree by construction, so this is a join inside one derivation and not a durable stored identity. Any reorganization must supply a stable per-entry identity or preserve single-parse enumeration. The file's own contract also says list order is non-semantic for routing, so the two statements have to be reconciled before a shape is chosen.
- **C2 — a retained field with no reader.** For `repo-origin` entries the registry's `source.revision` is compared against nothing: the `provenance_mismatch` revision check is guarded by `entry.source.mode == "tracker-origin"`. 89 of the 107 registered canonical intent entries carry a revision. Whether that field is an admission pin worth keeping is an open decision, and no consumer may be assumed.

## Assumptions

- The non-derivable operational state is small enough that relocating it is cheaper than living with the contention. **Untested** — the parent's de-risk classified the state but did not size the change.
- Every reader, writer, projection, fixture, and external adopter of `workspace.toml` can be inventoried, and an equivalence corpus can be built before any shape is chosen. The 2026-09-13 survey names this inventory as required and does not supply it. **Untested.**
- Whether array order is a priority anywhere beyond index-based duplicate identity and the `next_queue` projection is an open question the survey recorded and did not close. **Untested**, and it needs permutation or metamorphic tests over every parser and writer.
- Removing the contention does not merely relocate it to an assembly or regeneration step that needs a single owner. The survey found this relocation in four independent prior-art families. **Untested here.**

**Not de-risked.** No assumption above has been tested, and no kill condition has been declared for any of them. The parent's surviving verdict covers the parent's own bet, not this one. Re-enter `frame-intent` → `de-risk-intent` → `decompose-intent` before decomposing this intent.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
