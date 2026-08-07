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

A resolved index that carried staged filenames, the renderer's link syntax, and a
transformer's line map would be that renderer's file wearing a neutral name — and
it could not be written by `binder resolve`, which is specified to run on a machine
with no renderer installed at all. So the resolution output is **two files with two
owners**:

| File | Written by | Contains | Contract |
|---|---|---|---|
| `binder-index.json` | `resolve` (core) | identity, sections, order, selection reasons, metadata, `sha256`, `assets`, `links[].target-node`, diagnostics | **public, versioned, stable** |
| `renderer-plan.json` | `build` (adapter) | `staged-path`, `line-offset`, `links[].rewritten`, emitted ordinals | **adapter-private; no stability guarantee** |

**The split survived a renderer change, which is the evidence it was drawn in the
right place.** Under Quarto the plan held `.qmd` filenames, a `line-map`
breakpoint *array*, and pandoc `#sec-` anchors; under Zensical it holds `.md`
filenames, a single integer `line-offset`, and relative page links. Every one of
those fields changed. **Not one field of `binder-index.json` did.**

> **Invariant 22.** `binder build` writes **no field of `binder-index.json`.** The
> index is complete when `resolve` returns, and `build` reads it. A second
> renderer writes its own plan file beside it; nothing in the index needs to
> change to admit one.

This is what makes invariant 3 hold in both directions: the adapter cannot
rediscover sources (it is given no source root), and the core cannot leak
renderer detail (it emits no renderer-shaped field).

`figures[]` (**Phase 2**, with captions) will sit in the index because ordinal,
caption, and fence content-hash describe *source content and editorial intent*;
whatever label or anchor a renderer derives from them is that renderer's
convention and lives in the plan. v1 emits no `figures` key at all.

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
  "renderer": "zensical",
  "renderers": { "zensical": { "mermaid-theme": "neutral", "toc-depth": 3 } },
  "extensions": {},

  "_comment": "EXCERPT — three of twelve nodes, chosen to show one of each type. The real array is in global reading order and its node-ids are its 1-based positions; see the node-id rule below.",

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
      "selection": { "reason": "editorial-node", "rule": "…#sections[0].items[0]" },
      "ordering": { "base-index": 0, "weight": 0, "constraints": [], "final": 1 }
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
  into whatever the renderer wants — a staged filename under Zensical, a `#sec-`
  anchor under Quarto — is renderer syntax, so it belongs in the plan.
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
| `node-id` | R | R | R | `n` + the zero-padded 1-based position of the node **in the `nodes[]` array**, assigned by `resolve` over resolved nodes only. The array is in global reading order, so `n001` is always its first element — the excerpt above prints three non-adjacent nodes and is labelled as such. It has nothing to do with staged filenames, which are the adapter's and are numbered over a different set (they interleave part pages the core does not know about). **Stable across runs with identical inputs** (invariant 21); not stable across a change to the resolved node set. |
| `type` | R | R | R | closed set: `source` \| `editorial` \| `generated` |
| `content-id`, `source-path`, `sha256` | R | R | — | a generated node has no source |
| `section`, `numbered`, `label` | R | R | R | |
| `position` | R | R | O | **1-based index within the containing `section`**, not global reading order; global order is the `nodes[]` array order. Absent on appendix-level generated nodes. |
| `part` | O | O | O | `null` when the section is not in a part |
| `source-title` | O | O | — | present when the source had an H1 |
| `metadata` | O | O | — | absent entirely at Level 0 |
| `selection` | R | R | — | `reason` + `rule`; `required` optional |
| `ordering` | R | R | — | |
| `assets`, `links` | O | O | — | absent when empty, not `[]`. **`assets` is derived** as the set of inline-image destinations in the CommonMark AST that resolve to a relative path beneath the content root; reference-style images resolve first, and `<img>` never appears because the raw-HTML rule rejects it. |
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
`renderer`, `nodes`, `structure`, `diagnostics` are **R**; `renderers` and
`extensions` are **O**.

**`profile` was removed by D-A, and that is not a cosmetic deletion.** With one
possible value the field carried no information — it would have been a constant
emitted into every index in every repository, which is precisely the ceremonial
field invariant 21 exists to make structurally impossible. If a second profile is
ever added on evidence, the field returns additively; a consumer that never saw it
is unaffected, because a consumer MUST ignore unknown fields.

Its removal also simplifies the content-key: the profile was hashed into it so
that a strict and a trusted build of one recipe could not share a workspace. With
one profile there is nothing to separate — see [`runtime.md`](runtime.md).

`authored-by` is **compiler-derived** from the containing section's `kind`, not
authored — a recipe cannot claim a source document was written by the editor.
`review-state` is the one field a human sets by hand in the recipe.

**Forward compatibility, both directions:** a consumer **MUST** ignore unknown
fields and unknown `diagnostics` codes; a producer **MUST NOT** remove a field,
retype one, or narrow a closed set within major version 1. That pairing is what
makes "additive-only" a usable promise rather than a slogan.

### `renderer-plan.json` — adapter-owned, not a contract

Written by `build` into the workspace beside the index. One entry per node.

> **The plan's field list and worked example live in
> [`zensical-adapter.md`](zensical-adapter.md#renderer-plan), not here.** The
> adapter owns the plan, so the adapter's file is where it is specified — and an
> adapter-private structure printed in two places is exactly the
> "specified-two-ways" defect this tree was split to prevent. What belongs here is
> the *boundary*: what the plan may hold, and why it is not the index.

The plan holds whatever the adapter had to invent — staged filenames, the line
offset, rewritten link targets, emitted ordinals, and any transformation record
like a clamped heading. None of it is a contract, none of it is published, and a
second adapter writes a completely different set of fields beside the same index.

**`line-map` collapsed to `line-offset`, a single integer, and that is a D-B
consequence worth naming.** Under Quarto, five of eight transformation steps
changed line counts — the fence transform, the injected `%%|` cell option, the
label line — so a scalar was *provably* wrong and round 1 replaced it with a
breakpoint array. Zensical reads the portable fence directly (Z3a), so only the
frontmatter rebuild and the duplicate-H1 drop change line counts, both by a fixed
amount at the top of the file. The delta is uniform below the frontmatter, and one
integer expresses it exactly.

This is checkable rather than merely asserted: if a future adapter reintroduces a
length-changing transformation in the body, the array comes back — in the plan,
where it always belonged.

`links` maps a source-relative target to a **staged filename**, not to an anchor:
Z2b confirmed Zensical turns a `.md` link into its own pretty URL, so the adapter
emits the filename and lets the renderer own the URL shape. Under Quarto this
field held a pandoc `#sec-` anchor. Same field, same purpose, different renderer
convention — which is the entire reason it lives in the plan.

The plan carries **no stability guarantee** and is not published; only the adapter
reads it, and only to map diagnostics and record what it emitted.

---

## `binder-stamp.json` — the one machine artifact that ships

The index is never published (D32) and the plan is never published, so the stamp
is the only structured file that leaves the workspace — and it goes to review
boards, clients, and vendors. It is also `check --published`'s entire input. By
this file's own standard, *a contract specified only by example is not a
contract*, so it is enumerated here rather than left implicit.

```json
{
  "schema-version": "1",
  "binder-id": "payments-review",
  "pack-version": "0.1.0",
  "renderer": "zensical",
  "renderer-version": "0.0.53",
  "index-sha256": "e91b…",
  "nodes": [
    { "id-sha256": "3c9f…", "sha256": "4f2c…" },
    { "id-sha256": "a71b…", "sha256": "9ab1…" }
  ]
}
```

| Field | Read by | Notes |
|---|---|---|
| `schema-version` | `check --published` | stamp format, independent of the index's |
| `binder-id` | publication-ownership check | the one field `runtime.md`'s replace-guard compares |
| `pack-version` | `check --published` step 4 | a mismatch is **exit 10**, `rebuild-recommended` — distinct from stale |
| `renderer`, `renderer-version` | humans, and a future second adapter | recorded, never compared; a renderer upgrade is not staleness |
| `index-sha256` | `check --published` step 5 | catches a reorder, a renamed section, a changed `label` — everything a node-set comparison misses |
| `nodes[].id-sha256` | mismatch explanation | `sha256(content-id)`, **never the content-id** (D37) |
| `nodes[].sha256` | mismatch explanation | source content hash |

**The closure clause is the point of the design, not a footnote.** The stamp
carries **no source path, no exclusion reason, no unresolved gap, no diagnostics
key, no recipe line reference, and no label or title.** Round 3 found the design
publishing all of those inside a copied index; D32 replaced the copy with a
purpose-built artifact precisely so the reduction could not drift back. Anything
added here is a disclosure to every reader of every published binder, and the
field table above is closed — a new field is a decision, not an implementation
detail.

---
