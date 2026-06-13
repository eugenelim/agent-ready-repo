---
name: align-value-stream
description: Use at business-unit scale to stand up and keep current a value-stream meta-repo — a coordinating repo with no app code that holds the cross-component artifacts a polyrepo has nowhere else to put (the federated Backstage catalog, the shared-contract authority, the C4/bounded-context architecture, and the cross-component delivery rollup). Triggers on "set up a value-stream meta-repo", "coordinate across component repos", "stand up the cross-component catalog", "where does the shared contract live", "is this feature delivered across all the repos". Reads the per-component slices that decompose-intent produces and rolls up their delivery. Do NOT use at app scale (use decompose-intent — the leaf is one repo's brief) or to author an intent (use frame-intent).
---

# Skill: align-value-stream

Stand up and keep current a **value-stream meta-repo** — a coordinating repo with
**no application code** that sits above many component repos and holds the
cross-cutting artifacts a polyrepo has nowhere else to put: the cross-component
(capability) intents, the **federated catalog**, the **canonical shared
contracts** (or a reference to where they live), the **C4 / bounded-context
architecture**, and the **cross-component delivery rollup**. It is a *place you
read and edit*, never a running service. The slices it rolls up are produced by
`decompose-intent`'s business-unit branch; its spine is **currency** — a stale
map is the dominant failure mode. Depth lives in `references/`.

## When to invoke

Before aligning, confirm:

1. The work is at **`business-unit` Scale** (set by `frame-intent`) — a product
   org whose work fans out to many component repos. At `app` Scale there is no
   meta-repo; `decompose-intent`'s leaf is one repo's brief.
2. You're in (or standing up) a **coordinating repo with no app code**. If app
   code lives here, it's a component repo, not the meta-repo.

## Procedure

1. **Confirm the meta-repo and Scale.** Name the value stream and the component
   repos it coordinates. The meta-repo holds only cross-cutting artifacts.

2. **Federate the catalog.** Anchor to Backstage's **Domain → System → Component
   → API** ontology, but **reference** each component repo's own
   `catalog-info.yaml` rather than re-authoring it here — federate, never copy.
   See `references/backstage-ontology.md` (with a worked `catalog-info.yaml`
   sample, since it is Backstage-native and lives at each repo's root, not as a
   seed).

3. **Settle where the shared contract lives.** Explain the choice in plain
   language, **default to the meta-repo**, list the alternatives (a dedicated
   contracts/interface repo, a schema registry), and **elicit** the org's home.
   Regardless of location, the *shape* is constant: each per-component brief
   **references `contract@version`** and carries a **read-only courier snapshot**
   — never attach-as-authority. Provider/consumer roles mirror Backstage's
   `providesApi`/`consumesApi`; each relationship carries a
   compatibility/upgrade direction. See `references/shared-contract-handoff.md`.

4. **Anchor the system architecture.** The C4 / bounded-context `reference.md`
   lives **here**; each component repo's own `reference.md` links to and conforms
   to it rather than re-deriving the system view. This is the `architect` seam.

5. **Keep the rollup current.** Maintain the cross-component rollup (copy the
   `docs/product/rollups/_template.md` seed): one row per slice `decompose-intent`
   produced → its brief → a **status snapshot + a pointer** to that repo's own
   auto-derived coverage. The **AND across rows** is the answer; an absent-source
   row is `unknown / not-yet-catalogued`, never silently delivered. See
   `references/cross-component-rollup.md` and, for the discipline that keeps every
   artifact above honest, `references/catalog-currency.md`.

## Hard limits — state them honestly

The coordination pattern has real costs an adopter must accept, not engineered
away: **no atomic cross-repo commit**, **no shared release train**, and the
rollup is a **snapshot, not a live feed**. Name them when you stand the meta-repo
up.

## Anti-patterns to refuse

- **Building a runtime hub or a live coverage API.** The meta-repo is a repo you
  read and edit, not a service that polls component repos. A live rollup needs
  auth, polling, and rate limits — that's infrastructure, deferred to a later
  pack. Snapshot + pointer is the in-charter answer.
- **Re-authoring federated data.** Copying a component repo's `catalog-info.yaml`
  or coverage into the meta-repo forks it and guarantees drift. Reference it;
  cache only a snapshot.
- **Attaching a contract as authority.** Copying a contract into a brief forks it
  N ways. Reference `contract@version`; carry a read-only courier snapshot only.
- **Duplicating monorepo-vs-polyrepo structuring.** That decision lives in
  `monorepo-extras` (`new-package`); meet it only at "where the shared contract
  lives," and reference it — don't restate it.
- **Letting the map go stale.** Currency is the whole value. A catalog, contract,
  or rollup nobody reconciles is worse than none — agents follow it confidently.
