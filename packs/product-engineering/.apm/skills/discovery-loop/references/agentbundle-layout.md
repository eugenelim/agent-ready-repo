# `agentbundle-layout.toml` — the `[discovery]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). This page **mints and documents** the `[discovery]` section
that `discovery-loop` (and the discovery-side skills `frame-domain` /
`explore-options` / `plan-validation`) read — the discovery-tree layout key
RFC-0048 § Amendments (DRIFT-C) assigns this implementing spec to mint, on the
`[experience]` precedent.

> **Why its own table, not `[product-engineering]` or `[pack.layout]`.** The
> `[<pack>]` *adopter-file* table is the read target (not the manifest-side
> `[pack.layout]`). `product-engineering`'s file-per-slug `[product-engineering]`
> table (intents / rollups) **cannot host a per-initiative tree** — a discovery
> initiative is a *directory* (`<initiative-slug>/_state/` + committed artifacts),
> not a single file. So the discovery tree gets its **own** `[discovery]` key.

## The `[discovery]` table

One key:

```toml
[discovery]
parent = "docs/discovery"   # a base directory; one subdirectory per initiative goes *under* it
```

- **`parent` is a base, not the leaf.** Each initiative is a subdirectory:
  `<parent>/<initiative-slug>/`, holding the Tier-1 working sidecar in `_state/`
  (`blackboard.json`, `open-questions.json`, `traceability.json`,
  `decision-log.json`, `meta.json`, `plan-tree.json`) and the Tier-2 committed
  durable artifacts beside it (`domain-framing.md`, `scope-boundary.md`,
  `journey-map.md`, `service-blueprint.md`, `screens/`, `decision-brief.md`,
  `backlog.md`). See [`sidecar-schema.md`](sidecar-schema.md).
- **One tree per initiative — a forest.** `parent` holds many initiative
  directories; they cross-link by stable id, never by sharing a tree.
- **Lazy creation.** Directories are created on first write, never up front.

## Three-tier resolution (RFC-0040)

`discovery-loop` resolves the discovery root in this order — **config → designed
default → discover-by-marker** — and surfaces ambiguity rather than guessing:

1. **Config** — the `[discovery] parent` key above, if the adopter has bound it.
2. **Designed default** — `docs/discovery/` (repo mode) or `.context/discovery/`
   (non-repo / scratch). **This is the fallback in force until the key is bound** —
   the loop works with no config at all.
3. **Discover-by-marker** — find an initiative by its `_state/` subdir + the
   typed-artifact `type:` markers; the **marker, not the path, is the contract**, so
   the traceability lint and downstream consumers find the workspace wherever the
   adopter's layout puts it.

## The traceability sidecar key (separate, the consumer's)

The **traceability lint** reads its own optional `[traceability].sidecar` key
(and defaults to `docs/discovery/**/_state/traceability.json`) — that is the
*consumer's* discovery, documented in the lint, distinct from the `[discovery]
parent` *writer* key here. Binding `[discovery] parent` does not require binding
`[traceability].sidecar`; the lint's default discovery already finds the
`_state/traceability.json` under `docs/discovery/`.

## Two locations, repo overrides user

A repo-root `agentbundle-layout.toml` overrides a `~/.agentbundle/` one, the same
precedence every adopter-file table uses. A user-scope discovery (an Obsidian
vault, a non-repo store) sets `[discovery] parent` in the user-scope file; a
repo-scoped one sets it at the repo root.
