# The shared-contract handoff — referenced, never forked

A polyrepo has no shared tree, so the cross-cutting wire contract that several
components depend on has nowhere obvious to live. This is the one place the
`product-engineering` pack and `monorepo-extras` meet: **where the shared
contract lives**. (In a monorepo it's an in-tree interface library; in a polyrepo
it's the meta-repo or a dedicated contracts repo — `monorepo-extras` owns that
structuring decision, referenced here, not restated.)

## Authority: one home, elicited

Contract **authority** lives in **one** shared, version-pinned home. The
*location* is org-specific — settle it explicitly:

1. **Explain** the choice in plain language (one authority, referenced by every
   consumer, so a change is made once and propagates by version bump).
2. **Default** to the meta-repo.
3. **List alternatives**: a dedicated contracts/interface repo; an external
   schema registry.
4. **Elicit** the org's home and record it.

The *location* varies; the **shape is constant** regardless of where authority
lives (the next section).

## The reference-by-version + courier-snapshot shape

Each per-component brief that `decompose-intent` emits:

- **References `contract@version`** — a pointer to the authority at a pinned
  version, never a copy that becomes a fork.
- **Carries a read-only courier snapshot** — a frozen copy *for provenance only*,
  clearly marked read-only, so the slice records exactly what it was built
  against without becoming a competing authority.

**Never attach-as-authority** (copy the live contract into the brief): that forks
it N ways and drift is immediate. This mirrors the rollup pattern — reference the
authority, cache a snapshot, never fork it.

## Direction: provider-contract-first, with a CDC override

- **Default — provider-contract-first.** The provider defines the surface,
  including for not-yet-built consumers. This is what enables parallel
  development across components that don't exist yet.
- **Per-relationship override — consumer-driven contracts (CDC).** Where one
  provider serves a known, fixed set of collaborating consumers, let those
  consumers drive the contract for that relationship. The override is
  per-relationship, not global.

## Roles and compatibility direction

Provider/consumer roles mirror Backstage's `providesApi` / `consumesApi` (see
`backstage-ontology.md`) — the provider is the authority for the contract its
component `providesApi`; consumers `consumesApi` it by reference. Each
relationship also carries a **compatibility / upgrade direction**: who upgrades
first, and which side must stay backward-compatible across a version bump. Record
it alongside the reference so a slice knows whether it leads or follows a change.

## Contract maturity is unchanged

This layer adds **no new contract machinery**. Maturity stays staged as in the
app-scale path: behavioral at the intent, interaction/consumer-expectation at the
brief, the **detailed wire contract at the spec stage** (the existing `Contract:`
seam — REST/OpenAPI, events/AsyncAPI, and so on), verified at build. The
meta-repo references that detailed contract; it does not author it.
