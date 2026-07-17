# `agentbundle-layout.toml` — the `[product-engineering]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical (the re-emit runs only when your
section is absent). This page documents the
`[product-engineering]` section that `frame-intent` and `align-value-stream` read.

## The `[product-engineering]` table

One key:

```toml
[product-engineering]
parent = "docs/product"   # a base directory; output files go *under* it
```

- **`parent` is a base, not the leaf.** Each output file is written directly
  under a subdirectory of `parent` — never to `parent` itself. The file-per-slug
  shapes are:
  - `frame-intent` → `<parent>/intents/<slug>.md`
  - `align-value-stream` → `<parent>/rollups/<slug>.md`

  A **per-topic folder** is deliberately **not** used: each intent and each
  rollup is a single file handed downstream (`de-risk-intent`, `decompose-intent`,
  `receive-brief`).

## Two locations, repo overrides user

The skill reads the **repo-root `./agentbundle-layout.toml`**
`[product-engineering]` table if present, else the **user-profile
`~/.agentbundle/agentbundle-layout.toml`** table. When both define
`[product-engineering]`, the repo file's table wins; a table present only in the
user file still applies. This lets a team commit a repo-wide choice while an
individual keeps a personal default across repos.

## `parent` is anchored by the file's own location

- A **repo-root** file's `parent` is **repo-root-relative** (an absolute value is
  allowed but flagged non-portable).
- A **user-profile** file's `parent` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

Regardless of anchor, the skill resolves `parent` to its full absolute path
(realpath-resolved, `~`-expanded, `..` rejected) and **surfaces that path before
the first write**. A repo-root-sourced `parent` that resolves outside the repo
tree is treated as untrusted-origin and confirmed before writing.

## Default and posture

When no `[product-engineering]` section resolves, the pack defaults to
`docs/product` (its `[pack.layout.repo]` default) — committed product docs, the
natural home for intents and rollups in a product engineering repo.

`product-engineering` ships **no `[pack.layout.user]` default** — its output is
per-repo and there is no sensible *absolute* user-scope base. For a personal
cross-repo default, write a `[product-engineering]` section into your user-profile
file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[product-engineering]
# parent = "/abs/path/to/product-docs"   # uncomment + set an absolute path
```

## Pinned output — `decompose-intent`'s briefs

`decompose-intent`'s `docs/product/briefs/<slug>.md` output is **not** governed
by this table. That path is the hand-off to core's `receive-brief` skill and
stays pinned (a deliberate non-goal of this layout config). Only `frame-intent` (intents) and
`align-value-stream` (rollups) read `[product-engineering]`.
