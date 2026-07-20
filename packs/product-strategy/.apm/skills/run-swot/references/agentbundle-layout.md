# `agentbundle-layout.toml` — the `[product-strategy]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where output-producing packs write their durable work. It is never shipped into a projected path; you create it by hand (or an `agentbundle install` step appends a default section). This page documents the `[product-strategy]` section that the artifact-writing skills in this pack read.

## The `[product-strategy]` table

```toml
[product-strategy]
parent = "docs/product/shaping"   # a base directory; output files go directly under it
```

**This skill** writes `<parent>/swot-analysis.md` with frontmatter `type: swot-analysis`.

## Three-tier resolution

The skill resolves the artifact path in order:

1. **Config** — read `[product-strategy].parent` from the repo-root `./agentbundle-layout.toml`, then the user-profile `~/.agentbundle/agentbundle-layout.toml`. Repo file wins if both define the section.
2. **Default** — if no config resolves, use `docs/product/shaping` (the `[pack.layout.repo] parent` declared in `pack.toml`).
3. **Discover-by-marker** — if neither config nor default resolves to an existing directory, search the workspace for `type: swot-analysis` frontmatter in an existing file; use that file's parent directory as `<parent>`.

The skill resolves `parent` to its full absolute path (`~`-expanded, `..` rejected) and **surfaces the resolved path before writing**.

## Default and posture

When no `[product-strategy]` section resolves, the pack defaults to `docs/product/shaping` — committed strategy documents, the natural home for market analysis, OKR artifacts, and strategy direction in a product repo.

This pack ships no `[pack.layout.user]` default — its output is per-repo (each strategy artifact belongs to a specific product initiative). For a personal cross-repo default, write a `[product-strategy]` section into your user-profile file by hand.
