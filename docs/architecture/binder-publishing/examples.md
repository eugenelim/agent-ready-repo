# Worked examples

> V1 recipes, staging output, and portability fixtures.
> Part of [binder publishing architecture](README.md).

## Portable repository layout

```text
project/
├── binder.toml
├── binders/
│   ├── architecture-review.binder.toml
│   └── editorial/payments-exec-summary.md
├── docs/ · notes/
└── .binder-work/            # gitignored
```

## User-scoped use in an unrelated directory

```toml
# ~/clients/acme/discovery/binder.toml — no Git, pack.toml, or site.toml
schema-version = "1"
id = "acme-discovery"
title = "Acme Discovery Pack"

[[sections]]
id = "findings"
title = "Findings"

[[sections.items]]
path = "interviews/summary.md"

[[sections.items]]
path = "analysis/opportunities.md"
```

```bash
python scripts/binder.py build binder.toml --root=$HOME/clients/acme/discovery
```

The publication is `build/binders/acme-discovery/index.html` beneath the content
root.

## Per-file transformation

Source (`docs/design/payments/design.md`) remains unchanged:

````markdown
---
title: Payments migration design
css: /tmp/evil.css
---

# Payments migration design

```mermaid
flowchart LR
  A[Gateway] --> B["Ledger<br/>service"]
```
````

Staged (`docs/011-docs-design-payments-design.md`):

````markdown
---
title: "Payments migration design"
---

```{.mermaid data-a11y-name="Diagram 11.1"}
flowchart LR
  A[Gateway] --> B["Ledger<br/>service"]
```
````

Source frontmatter is discarded. Fresh frontmatter and the chapter H1 replace it.
The Mermaid fence body is byte-identical. The opening delimiter receives the D46
attribute as a same-line edit. The adapter records the resulting scalar
`line-offset` in `renderer-plan.json`; it does not write transformation data to
the index.

## Minimal `binder.toml` — Level 0

```toml
schema-version = "1"
id = "payments-review"
title = "Payments Migration Review"

[[sections]]
id = "context"
title = "Context"

[[sections.items]]
path = "docs/research/payments-landscape.md"

[[sections]]
id = "proposal"
title = "Proposal"

[[sections.items]]
path = "docs/design/payments-migration.md"
```

## V1 walkthrough

`binders/payments-review.binder.toml` contains exact `path` items and any
explicit `[[exclude]] path` entries. It contains no selectors, overlays, or
`extends` key.

```bash
python scripts/binder.py build binders/payments-review.binder.toml \
  --root=/Users/dev/proj
```

Explicit paths resolve without `source-roots` (D33). A recipe may combine source
artifacts, editorial files, and the generated source inventory. A required item
is always an exact reference.

## Staged project

```text
.binder-work/payments-review/<content-key>/stage/
├── zensical.toml                         # generated from the index
├── theme/
│   ├── main.html
│   └── assets/javascripts/mermaid.min.js
├── docs/
│   ├── index.md                          # generated cover
│   ├── 001-executive-summary.md          # editorial
│   ├── 002-part-evidence.md              # generated part page
│   ├── 003-docs-research-payments.md     # source
│   └── 900-source-inventory.md           # optional generated appendix
├── .cache/                               # Zensical cache
└── site/                                 # publication source
```

`docs/` and `site/` resolve relative to `zensical.toml`. Publishing copies from
`stage/site/` through the near-atomic replacement path.

## Final HTML information architecture

Cover → executive summary (marked editorial) → named parts and chapters → optional
source inventory. The renderer provides sidebar navigation, local search,
previous/next links, and per-page contents.

## The same mechanism in a clean directory

```text
scratch/vendor-eval/
├── binder.toml
├── overview.md
├── option-a.md
├── option-b.md
└── recommendation.md
```

Four explicit paths in four sections produce
`build/binders/vendor-eval/index.html`. This is the same Level-0 resolution and
build path as the repository example.
