# ADR-0077: Feature projection is gated; tracker authority follows lifecycle

- **Status:** Accepted
- **Date:** 2026-08-09
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0083](../rfc/0083-work-intake-and-artifact-routing.md),
  [ADR-0019](0019-product-intent-ontology-and-brief-projection.md),
  [ADR-0033](0033-intent-level-open-recognized-set-decoupled-from-scale.md),
  [ADR-0076](0076-briefs-persist-dispatch-starts-from-specs.md),
  [RFC-0068](../rfc/0068-linear-pack.md)

## Decision summary

- **Decision:** Feature intents project according to shippability and
  coordination need, while imported-field authority follows explicit
  repo-origin or tracker-origin lifecycle rules.
- **Because:** Artifact identity and requirement authority must remain stable
  when an adopter changes tracker vocabulary or delivery shape.
- **Applies to:** intents, briefs, specs, tracker intake and refresh, source
  provenance, cross-repository coordination, and post-delivery write-back.
- **Tradeoff accepted:** routing and refresh require explicit projection,
  provenance, ownership, and conflict-decision records.
- **Revisit if:** independently shippable work routinely cannot be classified
  without a wrapper brief, or the two origin modes cannot represent a supported
  source's authority lifecycle without source-specific exceptions.

## Context

ADR-0019 models product shaping as a recursive intent tree and originally makes
an app-scale feature intent identical to a repository brief. It also treats
trackers as one-way projections. Those defaults keep the repository independent
of tracker hierarchy, but two later observations expose where they are too
broad.

First, not every feature benefits from a brief. One independently shippable and
verifiable change already has a complete local delivery unit: its spec. Adding a
brief creates a wrapper with no decomposition or coordination value. Conversely,
a feature with several independently shippable changes or work spanning several
repositories needs a durable envelope for shared outcome, deferred scope, and
coordination. ADR-0076 further establishes that such a brief may persist without
specs and that dispatch begins only after a selected slice becomes a spec/plan
pair.

Second, a universal one-way tracker rule does not describe existing reviewed
delta synchronization. Some work is authored locally and projected outward;
other work enters from an external source whose named fields remain authoritative
while the local artifact is Draft. Treating either case as universal makes
refresh behavior ambiguous and risks an external edit silently changing an
accepted or executing local contract.

RFC-0083 resolves both questions. This ADR records its durable projection and
authority decision. It refines only ADR-0019's unconditional feature-to-brief
identity and universal one-way tracker projection; ADR-0019's recursive intent
ontology, repository spec-context boundary, and staged contract maturity remain
in force.

## Decision

**We will project a feature intent according to shippability and coordination
need, and we will govern imported requirements through explicit repo-origin or
tracker-origin authority that tightens with local lifecycle.**

Feature projection follows this gate:

| Feature shape | Projection |
| --- | --- |
| One independently shippable change in one repository | Feature intent → spec |
| Multiple independently shippable changes in one repository | Feature intent → brief → specs |
| Work spanning multiple component repositories | Feature intent → one brief per affected repository → specs |

A one-spec brief is permitted only when it is a repository projection of a
cross-repository feature and preserves concrete parent identity, sibling
coordination, affected-repository scope, ordering, or closure evidence. Ordinary
source provenance, a tracker reference, or an external object's type does not
justify a wrapper brief.

Cross-repository coordination is local and reviewable. Each repository brief
names the same durable parent and coordination reference. A remote prerequisite
is represented by a reviewed local receipt that pins its locator, accepted
revision, reported terminal status, reviewer, and date. Dispatch never reads
another repository live to decide whether the prerequisite is satisfied.

Source authority has two modes:

- **Repo-origin:** the local canonical artifact owns its requirements. A tracker
  is an external coordination projection. Tracker-authored requirement changes
  do not overwrite the artifact.
- **Tracker-origin:** named imported fields remain source-owned while the local
  artifact is Draft. The artifact records the source locator, compared revision,
  accepted revision when applicable, and per-field ownership.

The canonical artifact owns the detailed authority record. `workspace.toml` may
mirror only the origin mode, locator, and revision required for routing and
display; it is not a second field-ownership map.

Every tracker-origin refresh is an explicit reviewed delta. The local actor
authorized to accept the artifact is also the only actor who may accept that
delta or resolve a requirements conflict. Authority then tightens by lifecycle:

| Local lifecycle | Requirements refresh | Authority rule |
| --- | --- | --- |
| Draft | Permitted after authorized review | Accepted changes update source-owned fields; local fields remain local; the decision and compared revision are recorded. |
| Accepted intent or Ready brief | Gated | Accepted requirements are local-owned; each source change requires a recorded `keep-local`, `accept-source`, or `revise-both` decision. |
| Approved spec | Gated | The spec and plan are local-owned; the same recorded conflict decision is required before execution. |
| Implementing spec or Executing brief | Locked | Requirements refresh is refused while the local execution contract is active. |
| Shipped | Locked | Local-to-tracker writes are limited to trace links, status, comments, pull-request links, and closure. |

At Accepted, Ready, or Approved, accepted requirement fields transfer to local
ownership and the reviewed revision is pinned. A later conflict decision is
append-only and records source revision, field, decision, authorized approver,
and date. `accept-source` and `revise-both` change the local value only through
that review; neither restores silent source authority over an accepted field.

When an Executing brief returns to Ready after a delivery batch, refresh may
affect only not-yet-materialized scope and must pass the Ready-state conflict
gate. Shipped child specs never change. A source delta that would rewrite
completed behavior becomes new intake or a defect report rather than a refresh.

## Decision drivers

- **Artifact value:** a brief must add decomposition or coordination value, not
  exist because of a source label.
- **Source-independent identity:** equivalent content must route the same way
  across repositories and tracker profiles.
- **Stable execution contracts:** accepted and executing local requirements
  cannot change through unattended synchronization.
- **Reviewable authority transfer:** every change in ownership or conflict
  outcome must have durable provenance and an authorized human decision.
- **Offline determinism:** cross-repository prerequisites must be decidable from
  reviewed local evidence rather than live remote reads.

## Consequences

**Positive:**

- One-change features avoid empty wrapper briefs.
- Multi-spec and cross-repository work retains a durable shared envelope.
- Tracker names, hierarchy levels, labels, and collection types cannot redefine
  repository artifact identity.
- Imported requirements have an explicit owner at every lifecycle state.
- Execution and shipped history are protected from silent source changes.
- Cross-repository dispatch remains reproducible offline.

**Negative:**

- Intake must evaluate coherence, shippability, and coordination rather than
  applying a source-type lookup.
- Tracker-origin artifacts need source revisions, per-field ownership, and
  append-only conflict decisions.
- Refresh processors must implement lifecycle-specific refusal and conflict
  behavior rather than a generic synchronization operation.
- Cross-repository work carries reviewed receipt bookkeeping in each affected
  repository.

**Revisit if:** independently shippable work routinely cannot be classified
without a wrapper brief, or the two origin modes cannot represent a supported
source's authority lifecycle without source-specific exceptions.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** a shared fixture corpus proves direct-spec, multi-spec, and
  cross-repository projection independent of tracker type; lifecycle fixtures
  prove reviewed Draft refresh, recorded post-acceptance conflict decisions,
  execution lock, and the exact Shipped write-back allowlist; cross-repository
  dependencies resolve only from pinned local receipts.
- **Owner:** maintainers

## Alternatives considered

**Always create a brief.** Rejected because a one-change feature gains no
decomposition or coordination value and pays for an empty wrapper.

**Never create a brief.** Rejected because multi-spec outcomes need a durable
home for shared scope and cross-repository work needs local coordination
envelopes.

**Let tracker or document type determine projection.** Rejected because the
same substantive work would change identity when an adopter changes external
vocabulary or profile.

**Keep universal repository authority.** Rejected because it cannot represent
source-owned Draft fields or the existing reviewed delta-sync precedent.

**Keep universal tracker authority.** Rejected because an external edit could
change an accepted or executing local contract.

**Allow unrestricted bidirectional synchronization.** Rejected because
conflicts would have no durable owner, authorization point, or stable execution
boundary.

## References

- [RFC-0083](../rfc/0083-work-intake-and-artifact-routing.md) — accepted routing,
  projection, authority, and migration decision.
- [ADR-0019](0019-product-intent-ontology-and-brief-projection.md) — recursive
  intent ontology and the rules refined here.
- [ADR-0033](0033-intent-level-open-recognized-set-decoupled-from-scale.md) —
  open recognized intent levels, independent of scale.
- [ADR-0076](0076-briefs-persist-dispatch-starts-from-specs.md) — persistent
  briefs and spec/plan-only dispatch.
- [RFC-0068](../rfc/0068-linear-pack.md) — reviewed tracker-origin delta-sync
  precedent.
