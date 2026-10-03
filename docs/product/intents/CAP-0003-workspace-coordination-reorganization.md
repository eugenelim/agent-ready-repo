# Workspace coordination reorganization

- **Slug:** `workspace-coordination-reorganization` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc
- **De-risked:** 2026-10-02
- **Decomposed:** 2026-10-02 children

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

- Which canonical owner receives each workspace-only fact when more than one destination is lawful, especially priority and dependency choices.
- Whether the repository inventory is complete for external adopter behavior that cannot be observed from tracked files.
- Whether array order is load-bearing beyond index-based duplicate identity.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Constraints inherited from the parent's de-risk

Both were found while testing the parent's assumption and are recorded here so they travel with the work.

- **C1 — position is an in-run join key.** `_surviving_work` in `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` matches closeout verdicts by `(collection, entry_index)` rather than by any entry value, because no value is unique: a legacy `"spec/x"` string and a canonical `{path = "spec/x", kind = "defect"}` entry share a raw path. Both sides walk the same in-memory arrays in one parse and agree by construction, so this is a join inside one derivation and not a durable stored identity. Any reorganization must supply a stable per-entry identity or preserve single-parse enumeration. The file's own contract also says list order is non-semantic for routing, so the two statements have to be reconciled before a shape is chosen.
- **C2 — a retained field with no reader.** For `repo-origin` entries the registry's `source.revision` is compared against nothing: the `provenance_mismatch` revision check is guarded by `entry.source.mode == "tracker-origin"`. 89 of the 107 registered canonical intent entries carry a revision. Whether that field is an admission pin worth keeping is an open decision, and no consumer may be assumed.

## Assumptions

- The non-derivable operational state is small enough that relocating it is cheaper than living with the contention. **Disproved as stated.** The fresh inventory below found a broad operative surface. The surviving target is a staged, gated retirement whose specification assigns each fact and consumer before removal; it is not a small or direct relocation.
- Every repository reader, writer, projection, fixture, seed, and guide can be inventoried, and an equivalence corpus can be built before a replacement shape is chosen. **Supported for tracked repository consumers by the closed inventory below.** External adopter behavior remains `to-validate` through the compatibility review and equivalence replay.
- Whether array order is a priority anywhere beyond index-based duplicate identity and the `next_queue` projection is an open question the survey recorded and did not close. **Untested**, and it needs permutation or metamorphic tests over every parser and writer.
- Removing the contention does not merely relocate it to an assembly or regeneration step that needs a single owner. The survey found this relocation in four independent prior-art families. **Untested here.**
- **Knowledge surface:** in-repo skill implementations, package projections, manifests, tests, fixtures, seeds, guides, and governance records that read or name `workspace.toml` or `workspace-status`.

## De-risk record

- **Status:** survived on 2026-10-02 as a staged, gated retirement; external-adopter closure remains `to-validate`
- **Reversibility triage:** one-way door. Removing a published coordination format and its safety behavior is expensive to reverse after adopters and workflows migrate.
- **Prototype-approach:** `validate-first`. The cheapest probe that can fail is a closed consumer-and-state inventory over the current repository, followed by an ownership disposition for each required behavior.

### Riskiest assumption

Every required behavior and non-derivable fact currently carried by `workspace.toml` and `workspace-status` can be inventoried and assigned to a canonical artifact, an owning lifecycle workflow, an external projection, or an explicitly retained compatibility seam without recreating another repository-wide mutable registry.

What would have to be true: the repository's readers, writers, projections, fixtures, seeds, and guidance form a closed discoverable set; each dependency, priority, provenance, lifecycle, cooling, dispatch, repair, rollback, and prune responsibility has a lawful owner; and removing the hot file does not move the same write contention into a generated replacement.

### Kill condition, predeclared 2026-10-02

Kill full workspace retirement as one feature and recut the capability around a retained narrow compatibility record if either condition holds:

1. the fresh tracked-file inventory cannot reduce every operative `workspace.toml` or `workspace-status` consumer to a named reader, writer, projection, fixture, seed, guide, or historical-only reference; or
2. any required current behavior or non-derivable fact has no destination outside a repository-wide mutable registry and no separately accepted removal authority.

One unowned required behavior is enough to kill. The line is recorded before the consumer inventory and disposition run; the earlier corpus-size survey is grounding only.

### Probe

A fresh tracked-file inventory reduced the operative surface to seven named consumer classes:

1. the `workspace-status` skill, its reconciliation engine, repair-plan/apply, rollback, and prune paths;
2. lifecycle readers and writers in `work-intake`, `author-delivery-brief`, `work-loop`, `close-work`, `new-spec`, and `new-rfc`;
3. runtime and generated projections, including the workspace MCP surface and packaged workspace engines;
4. the core manifest, workspace seed, install snapshots, and build checks;
5. tracker-ingress and status routes that register or report work;
6. focused tests, fixtures, roster checks, and tool tests; and
7. current guides and architecture documents, separated from frozen historical records.

The same inventory assigned each behavior or fact to a destination class without requiring a replacement repository-wide mutable registry:

- identity, lifecycle, altitude, and parentage belong to canonical artifact metadata and `navigate-intents`;
- dependency and priority need an accepted canonical owner or external projection before migration;
- dispatch readiness remains with specs, plans, and `work-loop` preflight;
- cooling and retirement remain with closeout and lifecycle records;
- repair, reconcile, rollback, and prune move only to the workflow that owns the affected artifact or lifecycle;
- tracker-origin refresh remains an ingress or tracker-projection responsibility; and
- legacy records may use a temporary compatibility seam until the closure gate removes it.

### Verdict — survived, with the migration shape narrowed

Neither predeclared kill condition fired. Every operative tracked-file reference fit a named consumer class, and no required behavior or fact lacked a non-registry destination class or an accepted-removal route. Full retirement therefore remains a viable target and may decompose into one staged migration feature governed by RFC-0105's four gates.

The probe did disprove the smaller assumption that this is a cheap relocation: the consumer surface is broad. The child must treat consumer inventory, state disposition, behavioral equivalence, and compatibility closure as acceptance gates, and must retain the old surfaces until all four pass. The later maintainer review and external-adopter check remain open validation rather than being inferred from repository search.

### Validation hook

```yaml
validation_hook:
  assumption: Workspace coordination can retire without losing required behavior or recreating its contention elsewhere.
  kill_condition: Any operative consumer or required behavior is absent from the migration inventory, or a replay differs without an accepted removal decision.
  activity: to-validate — maintainers review the closed inventory, then replay the equivalence corpus through the old and replacement paths before the retiring change is approved.
```

## Decomposition

- [Workspace registry retirement](FEAT-0030-workspace-registry-retirement.md) — the staged migration and gated retirement of `workspace-status` and `workspace.toml`, including consumer inventory, fact disposition, behavioral equivalence, and compatibility closure.

### Decomposition decisions

- **One child owns one irreversible migration outcome.** Splitting by reader, writer, or storage layer would create technical slices that cannot retire anything safely on their own. The four RFC-0105 gates remain acceptance gates inside one feature.
- **The child is staged, not small.** The de-risk inventory disproved a cheap-relocation assumption and found a broad surface. One feature keeps the evidence and final retirement decision coherent while allowing its specification and delivery plan to sequence many slices.
- **Intent navigation is a sibling feature under another capability.** It can replace read-only orientation only after its own intent lifecycle passes; this child owns removal of the old compatibility surfaces, not the new navigator's implementation.
- **No replacement registry is implied.** Each fact moves to a canonical artifact, an owning lifecycle workflow, an external projection, temporary migration state, or accepted removal. A central mutable replacement would fail the capability guardrail.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
