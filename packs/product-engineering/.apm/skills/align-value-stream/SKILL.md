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

5. **Keep the rollup current.** Resolve `parent` using the config-driven
   procedure below, then maintain the cross-component rollup (copy this skill's
   `assets/rollup-template.md` to `<parent>/rollups/<slug>.md`): one row per
   slice `decompose-intent` produced → its brief → a **status snapshot + a
   pointer** to that repo's own auto-derived coverage. The **AND across rows** is
   the answer; an absent-source row is `unknown / not-yet-catalogued`, never
   silently delivered. See `references/cross-component-rollup.md` and, for the
   discipline that keeps every artifact above honest, `references/catalog-currency.md`.

## Where the rollup lives — config-driven, `docs/product` by default

Resolve the rollup **parent** directory in this order, **in this skill body**.
Reading is **prompt-only** (Charter Principle 3): this skill reads a file and
reasons about a path — there is no engine, index, daemon, or watcher behind it,
and the only code that ever *writes* the layout file is the install-time append.
See [`references/agentbundle-layout.md`](references/agentbundle-layout.md) for the
`[product-engineering]` section's full schema.

1. **Read `agentbundle-layout.toml`'s `[product-engineering]` table** if the
   adopter created one. Two locations, **repo-root overrides user-profile per
   table**: the repo-root `./agentbundle-layout.toml` `[product-engineering]`
   table if present, else the user-profile
   `~/.agentbundle/agentbundle-layout.toml` `[product-engineering]` table. The
   file is **adopter-owned**, never shipped into a projected path. Its `parent`
   key is a **base** directory under which rollups are written as individual
   files — never a per-topic folder:

   ```toml
   # agentbundle-layout.toml (adopter-created; optional)
   [product-engineering]
   parent = "docs/product"   # a base; rollups land at <parent>/rollups/<slug>.md
   ```

2. **Fall back to the pack's own default** — `docs/product`.
3. **Elicit** if neither resolves — ask the user where rollups should live.

**Anchor `parent` by the layout file's own location**, never against the ambient
cwd: a **repo-root** file's `parent` is **repo-root-relative** (an absolute value
is permitted but warn it as non-portable); a **user-profile** file's `parent`
**must be an explicit absolute path** (`~`-anchored is fine), and a *relative*
value there is an Ask-first deviation, never silently resolved.

**Resolve, then surface, then write.** After anchoring, resolve `parent` to its
**full absolute path** — `~`-expand it and **realpath-resolve it** so any symlink
in the path is made visible and never silently followed out of the intended root
— and **reject any `..` escape**. The `..` rejection and the realpath happen
**after** anchoring, so a relative repo-file value that escapes via `..` (e.g.
`parent = "../../etc"`) is caught regardless of which file supplied it; anchoring
never blesses a `..`-bearing value as in-tree. Then **surface the resolved
absolute path to the adopter before creating the rollup file** — the first write
is always preceded by the path you are about to write under.

**A repo-root-sourced `parent` that resolves outside the repo tree** — or whose
resolution required following a symlink out of the intended root — is
**untrusted-origin**: a cloned, untrusted repo can carry a hostile `parent`
(`../../etc`, `~/.ssh`, an out-of-tree symlink). **Confirm the resolved absolute
path with the adopter before writing.** The user-profile file is foot-gun-only
(the adopter authored it), but still surface its resolved path.

**Output shape — file-per-slug, not a per-topic folder.** Rollup files live
directly under `<parent>/rollups/<slug>.md`. A per-topic folder is deliberately
**not** used: each rollup is a single file. `decompose-intent`'s
`docs/product/briefs/<slug>.md` output stays **pinned** — that path is the
hand-off to core's `receive-brief` and is not governed by this config (RFC-0040
non-goal).

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
