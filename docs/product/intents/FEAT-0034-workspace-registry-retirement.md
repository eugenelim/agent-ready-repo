# Workspace registry retirement

- **Slug:** `workspace-registry-retirement`
- **Status:** Draft
- **Level:** feature
- **Owner:** Platform Core maintainer
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:workspace-coordination-reorganization
- **Shaping-reviewed:** 2026-10-02
- **Decomposed:** no

## Outcome

- **Steerable input:** Reduce the share of coordination operations that require an edit to one repository-wide mutable registry while assigning every retained fact and behavior to a named owner.
- **Lagging outcome:** People and agents coordinate, dispatch, and close repository work with fewer shared-file conflicts and no loss of coordination safety or duplicated inventory.
- **Guardrail:** Retirement fails closed until the consumer inventory, state disposition, behavioral-equivalence evidence, and compatibility closure are complete. No dependency, priority, provenance, dispatch, lifecycle, cooling, repair, rollback, prune, legacy, or external-adopter behavior disappears by inference.

## Opportunity

- **Functional job:** Coordinate, dispatch, and close repository work without every participant editing one shared registry or losing the safety behavior it currently carries.
- **Emotional job:** Remove the hot file with confidence that a hidden reader, writer, or workspace-only fact has not been missed.
- **Social job:** Show maintainers and adopters a reviewable migration record that names where every old responsibility went and proves the retained behavior.
- **Struggling moment:** `workspace.toml` duplicates artifact identity and lifecycle while also carrying real non-derivable choices. Its readers and writers span skills, runtime projections, manifests, seeds, tests, and guides, so deleting the file or replacing only its read-only view would strand accepted coordination behavior.

## Boundary

This feature owns the gated retirement path required by [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md):

1. a closed inventory of every operative reader, writer, projection, fixture, seed, guide, and adopter-facing promise;
2. a per-fact disposition into canonical artifact metadata, derived state, external projection, temporary migration state, or deliberate removal under accepted authority;
3. equivalence evidence for required reconciliation, dependency, provenance, dispatch, lifecycle, cooling, repair, rollback, and prune outcomes; and
4. compatibility closure for legacy entries, public activation, manifests, seeds, operative references, corpus gates, and final deletion.

It also owns the transition sequencing that keeps `workspace-status` and `workspace.toml` supported until all four gates pass. Mutation moves only to the workflow that owns the affected artifact or lifecycle; it does not move into `navigate-intents`.

It does not own the `navigate-intents` feature, intent identity or graph rules, tracker projection, lifecycle policy, renderer design, or changes to accepted behavior without separate authority. It does not choose a replacement repository-wide registry. Where priority, dependency, or another workspace-only fact has more than one lawful destination, the accepted specification must choose an owner before migration.

The feature must preserve the parent's two inherited constraints: any replacement must either provide stable per-entry identity or preserve safe single-parse enumeration, and it must decide whether repo-origin `source.revision` is an admission pin before retaining or removing that field.

## Owner

- Platform Core maintainer. Accountable for the inventory, per-fact decisions, equivalence evidence, and certification that all four retirement gates passed.

## Unresolved questions

- Which accepted artifact or external projection owns human priority and dependency choices after the registry retires.
- Whether any external adopter depends on behavior not visible in tracked repository files.
- Whether array order carries priority anywhere beyond the known index-based join and `next_queue` projection.
- Which legacy records require a temporary compatibility seam, and what evidence closes it.
- Which accepted sibling contracts require an amendment or superseding authority before their workspace writer or dependency behavior can change.

## Cascading intent impacts

This retirement changes the future owner of coordination behavior; it does not make every historical `workspace.toml` locator stale today. The migration inventory distinguishes current contracts from historical provenance and updates only the current owner when its gate passes.

- [Intent graph navigation](FEAT-0002-intent-graph-navigation.md) owns the artifact-derived read-only orientation successor. It must remain independent of `workspace.toml`; this feature owns retiring the old orientation surface after parity, not implementing the new navigator.
- [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md) currently renames an intent and its workspace path reference together. That lockstep write remains required during compatibility, then disappears only when the registry path ceases to be operative.
- [Single-ladder migration](FEAT-0004-single-ladder-migration.md) depends on initiative-free registration today. Its end state must instead use canonical intent parentage and artifact lifecycle, with any workspace registration treated as transitional compatibility rather than the new ladder's authority.
- [Lifecycle and closure](FEAT-0005-lifecycle-and-closure.md) is Accepted and currently assigns a terminal registration move to `close-work`. This feature cannot silently rewrite that contract. The retirement specification must preserve the writer during compatibility, then cite accepted authority for its amendment or removal when canonical lifecycle no longer needs a workspace collection move.
- [External tracker projection](CAP-0004-external-tracker-projection.md) and its children consume dependency, priority, and observation state that may currently be joined through workspace entries. State disposition must name the canonical or external owner before the registry stops supplying those joins.

Frozen records and completed intents that name `workspace.toml` only as their historical source remain unchanged. Operative guides, routes, manifests, tests, and current intent contracts move only when the four retirement gates prove their replacement.

## Projection

No tracker projection is selected. Tracker-origin refresh and human selection may be assigned to an external projection only through the state-disposition decision; this feature does not presume that owner.

## Assumptions

- **Riskiest assumption:** Every operative consumer, including external adopter promises, can be named and migrated or explicitly retired under accepted authority.
- Priority, dependency, provenance, lifecycle, cooling, dispatch, and cleanup facts can each receive one canonical owner without recreating a repository-wide mutable registry.
- A frozen equivalence corpus can distinguish preserved behavior from an intentional, separately authorized removal.
- The migration can preserve safe duplicate handling and stable per-entry identity without relying on array position across independent reads.
- Removing the hot file will not relocate the same contention to a generated assembly step or another single-owner projection.
- **Knowledge surface:** in-repo workspace implementations, package projections, manifests, tests, fixtures, seeds, guides, RFC-0105, and the workspace-coordination capability probe.

**Not de-risked.** The parent proved that a staged retirement has a viable destination class for every tracked repository responsibility. This child must still test the migration across external adopters, per-fact ownership choices, equivalence replay, and contention relocation before it becomes a specification.

## Shaping review

The isolated intent-mode review completed cleanly on 2026-10-02 using an attributed packet derived from artifact revision `sha256:1c3a2709165c3c9b629ba5f490308b1fec4f4a9aef34e39f29dc6cb582a9d29a`. Stamping the review date and this binding note is nonmaterial; it changes no outcome, opportunity, assumption, altitude, boundary, or projection. The later cascading-impact section only identifies consumers already covered by the closed-inventory boundary; it adds no retirement authority and does not alter that review's contract.

## Decomposition

None yet. Re-enter `de-risk-intent` before producing a delivery brief or specification.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md`
- **Authority:** Platform Core maintainer

Framed from RFC-0105 D3 and its four retirement gates on 2026-10-02. The RFC establishes full retirement as the target but leaves every current surface supported until the accepted specification proves inventory, disposition, equivalence, and closure.
