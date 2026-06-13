# How to run a capability across a value stream (many component repos)

> **Diátaxis: how-to.** A goal-oriented walk through the `product-engineering` loop at **business-unit scale** — one capability that fans out across many component repos, coordinated from a value-stream meta-repo. For app scale (one repo, one feature) see the how-to *Shape a feature intent*; for the fields, the reference *Intent fields and modes*; for the why, the explanation *The intent tree*.

You run a product org whose work spans many component repos (a polyrepo), and a capability you want to ship cuts across several of them. You want to shape it, slice it per component, and track whether the whole thing is delivered — without standing up a runtime coordination service. Install the `product-engineering` pack, then:

```text
  value-stream meta-repo  (no app code)
  ├── federated Backstage catalog  (references each repo's catalog-info.yaml)
  ├── shared-contract authority    (contract@version + read-only snapshots)
  ├── C4 / bounded-context reference.md
  └── cross-component delivery rollup ◄───────────────────────┐
                                                              │ status per slice
  capability intent                                           │
    frame ─► de-risk ─► decompose ─► slice per component      │
                                          │                   │
          ┌───────────────────────────────┼───────────────────────────┐
          ▼                               ▼                            ▼
    brief → repo A                  brief → repo B               brief → repo C
    receive-brief                   receive-brief                receive-brief
      → new-spec                      → new-spec                   → new-spec
      → work-loop                     → work-loop                  → work-loop
          │                               │                            │
          └─────────────── delivered? = AND across all rows ───────────┘
```

## 1. Stand up the value-stream meta-repo

Invoke **`align-value-stream`** in (or to create) a **coordinating repo with no app code**. It holds the cross-cutting artifacts a polyrepo has nowhere else to put:

- a **federated Backstage catalog** — it *references* each component repo's own `catalog-info.yaml` (Domain → System → Component → API), never re-authoring it;
- the **shared-contract authority** — you settle where it lives (default: the meta-repo), and every consumer references `contract@version` with a read-only courier snapshot, never a fork;
- the **C4 / bounded-context architecture** `reference.md` (the `architect` seam);
- the **cross-component delivery rollup** (step 3).

Its spine is **currency**: a stale catalog or contract is the dominant failure mode, so reconcile the meta-repo whenever a coordinated change lands.

## 2. Frame, de-risk, then slice the capability per component

Frame the capability with **`frame-intent`** (Scale resolves to `business-unit` at intake) and de-risk its riskiest assumption with **`de-risk-intent`**, exactly as at app scale. Then **`decompose-intent`** produces feature intents and, at the leaf, **slices each feature per component** — one `core` **brief per affected repo**. Each slice carries:

- a **`parent-intent:`** pointer to the intent it came from (provenance only),
- a **`contract@version`** reference + read-only courier snapshot, and
- a **provider/consumer role** (`providesApi` / `consumesApi`) with a compatibility direction.

Each brief crosses into its component repo, where the loop you already have — **`receive-brief` → `new-spec` → `work-loop`** — takes it the rest of the way, unchanged. The detailed wire contract is pinned there, at the spec stage.

## 3. Roll up "delivered across all components?"

Each component repo answers "is *my* slice shipped?" via `receive-brief`'s own coverage. The meta-repo's **cross-component rollup** — a markdown table, one row per slice → its brief → a status snapshot + a pointer to that repo's coverage — answers the level above: the **AND across rows**. A row whose source isn't catalogued yet shows `unknown / not-yet-catalogued`, never silently delivered, so a half-catalogued value stream never reports a false green.

## The hard limits — accept them honestly

This coordinates **without a runtime hub**, and that has real costs you should state up front:

- **No atomic cross-repo commit** — a contract change and its consumers can't land in one PR.
- **No shared release train** — each component releases on its own cadence.
- **The rollup is a snapshot, not a live feed** — you reconcile it by hand; a live rollup that polls every repo is infrastructure, deferred to a later pack.

These are the inherent cost of a polyrepo, surfaced rather than engineered away.
