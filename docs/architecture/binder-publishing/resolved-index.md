# Resolved index and renderer plan

> The two output contracts and the invariant that separates them.
> Part of [binder publishing architecture](README.md).

## Resolved binder index

`binder-index.json` is a **public, versioned renderer interface with stability
guarantees**: additive-only within a major version; a consumer written against
version 1 keeps working across every 1.x emission. It is the answer to the
brief's question, chosen deliberately over "internal format" because invariant 3
gives it a second consumer by definition.

### Two artifacts, because one of them is not renderer-neutral

A resolved index that carried `.qmd` filenames, pandoc anchor syntax, and a line
map produced by the Quarto transformer would be a Quarto file wearing a neutral
name — and it could not be written by `binder resolve`, which is specified to run
on a machine with no Quarto at all. So the resolution output is **two files with
two owners**:

| File | Written by | Contains | Contract |
|---|---|---|---|
| `binder-index.json` | `resolve` (core) | identity, sections, order, selection reasons, metadata, `sha256`, `assets`, `links[].target-node`, diagnostics | **public, versioned, stable** |
| `renderer-plan.json` | `build` (adapter) | `staged-path`, `line-map`, `links[].rewritten`, emitted figure labels | **adapter-private; no stability guarantee** |

> **Invariant 22.** `binder build` writes **no field of `binder-index.json`.** The
> index is complete when `resolve` returns, and `build` reads it. A second
> renderer writes its own plan file beside it; nothing in the index needs to
> change to admit one.

This is what makes invariant 3 hold in both directions: the adapter cannot
rediscover sources (it is given no source root), and the core cannot leak
renderer detail (it emits no renderer-shaped field).

`figures[]` (**Phase 2**, with captions) will sit in the index because ordinal,
caption, and fence content-hash describe *source content and editorial intent*;
the `fig-…` label derived from them is a pandoc cross-reference convention and
lives in the plan. v1 emits no `figures` key at all.

### `binder-index.json`

```json
{
  "schema-version": "1",
  "binder": {
    "id": "payments-review",
    "title": "Payments Migration Review",
    "subtitle": "Architecture review board packet",
    "purpose": "Decide whether to approve the payments migration for build.",
    "audience": ["architecture review board", "engineering leads", "security reviewer"],
    "subject": "payments-migration",
    "status": "for-review"
  },
  "recipe": {
    "path": "binders/payments-review.binder.toml",
    "extends": [],
    "params": { "subject": "payments-migration" }
  },
  "content-root": ".",
  "source-roots": ["docs", "notes"],
  "profile": "strict",
  "renderer": "quarto",
  "renderers": { "quarto": { "mermaid-theme": "neutral", "toc-depth": 3 } },
  "extensions": {},

  "nodes": [
    {
      "node-id": "n008",
      "type": "source",
      "content-id": "docs/rfc/0091-payments-migration.md",
      "source-path": "docs/rfc/0091-payments-migration.md",
      "sha256": "4f2c…",
      "section": "proposal",
      "part": null,
      "position": 1,
      "numbered": true,
      "label": "RFC-0091: Payments migration",
      "source-title": "RFC-0091: Payments migration to the ledger service",
      "metadata": {
        "kind": "rfc",
        "status": { "raw": "Accepted", "normalized": "current" },
        "producer": "governance-extras",
        "subject": ["payments-migration"],
        "metadata-source": "sidecar"
      },
      "selection": {
        "reason": "explicit-path",
        "rule": "binders/payments-review.binder.toml#sections[2].items[0]",
        "required": true
      },
      "ordering": { "base-index": 0, "weight": 0, "constraints": [], "final": 1 },
      "assets": ["docs/rfc/img/ledger-topology.png"],
      "links": [
        { "raw": "../adr/0044-ledger-boundary.md", "target-node": "n011" },
        { "raw": "https://example.com/spec", "target-node": null }
      ]
    },
    {
      "node-id": "n001",
      "type": "editorial",
      "content-id": "binders/editorial/payments-exec-summary.md",
      "source-path": "binders/editorial/payments-exec-summary.md",
      "sha256": "9ab1…",
      "section": "summary",
      "position": 1,
      "numbered": false,
      "label": "Executive summary",
      "role": "executive-summary",
      "authored-by": "editor",
      "review-state": "unreviewed",
      "selection": { "reason": "editorial-node", "rule": "…#sections[0].items[0]" }
    },
    {
      "node-id": "n012",
      "type": "generated",
      "generator": "source-inventory",
      "section": "provenance",
      "numbered": false,
      "label": "Source inventory and provenance"
    }
  ],

  "structure": {
    "parts": [ { "id": "evidence", "title": "Part I — Evidence", "sections": ["context"] } ],
    "sections": [ { "id": "summary", "title": "Executive summary", "kind": "editorial", "numbered": false, "intro-node": null } ],
    "appendices": ["provenance"]
  },

  "diagnostics": {
    "warnings": [],
    "excluded": [
      { "content-id": "docs/rfc/0088-payments-migration-draft.md",
        "reason": "explicit-exclude", "rule": "…#exclude[0]", "note": "superseded by RFC-0091" }
    ],
    "gaps": [
      { "expected": "security assessment for payments-migration",
        "rule": "…#sections[6].items[0]", "severity": "optional" }
    ],
    "unknown-status": []
  }
}
```

Three properties make the format implementable by a second renderer:

- **Link targets are pre-resolved, link *syntax* is not.** Deciding whether
  `../adr/0044-ledger-boundary.md` names a document that is *in this binder* is a
  selection-aware question, so `target-node` belongs in the resolver. Turning that
  into `#sec-adr-0044` is pandoc syntax, so it belongs in the plan.
- **Every node's content is hashed and its figures enumerated**, so a renderer
  knows what it is rendering and a CI job can tell whether a publication is stale
  — without either needing to re-read the sources.
- **No absolute paths, no timestamps, no renderer-shaped fields.**
  Byte-reproducible for identical inputs (invariant 21) and renderer-neutral by
  construction (invariant 22).

### Index surface — what a second renderer may rely on

A contract specified only by example is not a contract. Required (**R**) means a
producer always emits it and a consumer may assume it; optional (**O**) means it
may be absent.

| Field | `source` | `editorial` | `generated` | Notes |
|---|---|---|---|---|
| `node-id` | R | R | R | `n` + the zero-padded 1-based position of the node **in the `nodes[]` array**, assigned by `resolve` over resolved nodes only. It has nothing to do with staged filenames, which are the adapter's and are numbered over a different set (they interleave part pages the core does not know about). **Stable across runs with identical inputs** (invariant 21); not stable across a change to the resolved node set. |
| `type` | R | R | R | closed set: `source` \| `editorial` \| `generated` |
| `content-id`, `source-path`, `sha256` | R | R | — | a generated node has no source |
| `section`, `numbered`, `label` | R | R | R | |
| `position` | R | R | O | **1-based index within the containing `section`**, not global reading order; global order is the `nodes[]` array order. Absent on appendix-level generated nodes. |
| `part` | O | O | O | `null` when the section is not in a part |
| `source-title` | O | O | — | present when the source had an H1 |
| `metadata` | O | O | — | absent entirely at Level 0 |
| `selection` | R | R | — | `reason` + `rule`; `required` optional |
| `ordering` | R | R | — | |
| `assets`, `links` | O | O | — | absent when empty, not `[]`. **`assets` is derived** as the set of inline-image destinations in the CommonMark AST that resolve to a relative path beneath the content root; reference-style images resolve first, and `<img>` never appears because control 13 rejects it. |
| `figures` | — | — | — | **Phase 2.** Added additively when captions ship; v1 has no consumer for `fence-sha256` or `caption-binding`, and emitting them would be the circularity D13 removed for `--if-stale`. |
| `role` | O | O | — | |
| `authored-by`, `review-state` | — | R | — | editorial only |
| `generator` | — | — | R | names the compiler routine |

`content-root` is **always the literal `"."`** — the index is absolute-path-free by
invariant 21, so it cannot carry the real root. A consumer receives that
out-of-band: from `--root`, or from the location of the index file itself. Stating
it is necessary, because a second renderer handed only the index would otherwise
have paths it cannot resolve.

Top level: `schema-version`, `binder`, `recipe`, `content-root`, `source-roots`,
`profile`, `renderer`, `nodes`, `structure`, `diagnostics` are **R**;
`renderers` and `extensions` are **O**.

`authored-by` is **compiler-derived** from the containing section's `kind`, not
authored — a recipe cannot claim a source document was written by the editor.
`review-state` is the one field a human sets by hand in the recipe.

**Forward compatibility, both directions:** a consumer **MUST** ignore unknown
fields and unknown `diagnostics` codes; a producer **MUST NOT** remove a field,
retype one, or narrow a closed set within major version 1. That pairing is what
makes "additive-only" a usable promise rather than a slogan.

### `renderer-plan.json` — adapter-owned, not a contract

Written by `build` into the workspace beside the index. One entry per node:

```json
{
  "plan-version": "1",
  "index-sha256": "e91b…",
  "nodes": {
    "n008": {
      "staged-path": "008-docs-rfc-0091-payments-migration.qmd",
      "line-map": [[1, 1], [9, 5], [11, 7], [12, 9]],
      "figure-labels": { "1": "fig-docs-rfc-0091-payments-migration-1" },
      "heading-rule": "dropped-duplicate-h1",
      "clamped-source-lines": [],
      "assets": { "img/ledger-topology.png": "assets/n008/ledger-topology.png" },
      "links": { "../adr/0044-ledger-boundary.md": "#sec-adr-0044" }
    }
  }
}
```

`line-map` is an array of `[source-line, staged-line]` breakpoints, each marking a
position where the two diverge; a lookup finds the last breakpoint at or before
the staged line and applies its delta. It is an array — not a scalar offset —
because five of the eight transformation steps change line counts (see *Quarto
staging adapter*), which the worked Mermaid example demonstrates.

`index-sha256` pins the plan to the index it was generated from, so a stale plan
is detected rather than silently misapplied. The plan carries **no stability
guarantee** and is not published; only the adapter reads it, and only to map
diagnostics.

---
