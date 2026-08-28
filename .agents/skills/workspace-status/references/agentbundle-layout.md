# `agentbundle-layout.toml` — the `[product]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical (the re-emit runs only when your
section is absent). This page documents the `[product]` section that
product-facing skills read to locate the `shaping/` directory.

## The `[product]` table

One configurable key; `briefs` is intentionally absent (pinned):

```toml
[product]
shaping  = "docs/product/shaping"    # vision docs, opportunity assessments, capability maps
# briefs path is pinned at docs/product/briefs/ — not configurable here
```

- **`shaping`** is the base directory for upstream shaping artifacts: product
  vision docs, opportunity assessments, capability maps, initiative briefs. Produced
  by the PE six-step shaping sequence and the product-strategy pack.
- **`briefs`** stays pinned at `docs/product/briefs/`. It is the hand-off point
  to Core's `author-delivery-brief continue` mode and must not be redirected — moving briefs breaks
  the `Brief:` back-link chain and coverage rollup.

## Two locations, repo overrides user

Skills read the **repo-root `./agentbundle-layout.toml`** `[product]` table if
present, else the **user-profile `~/.agentbundle/agentbundle-layout.toml`** table.
When both define `[product]`, the repo file's table wins; a table present only in
the user file still applies.

## Path anchoring

- A **repo-root** file's paths are **repo-root-relative**. An absolute path is
  allowed but flagged non-portable.
- A **user-profile** file's paths **must be explicit absolute paths**
  (`~`-anchored is fine). A relative path there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

## Default and posture

When no `[product]` section resolves, skills fall back to the conventional
default `docs/product/shaping` for `shaping`. This matches the structure
documented in `docs/CONVENTIONS.md §5b`.

`core` ships **no `[pack.layout.user]` default** for this section — product
output is per-repo and there is no sensible cross-repo absolute path. For a
personal cross-repo default, write a `[product]` section into your user-profile
file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[product]
# shaping  = "/abs/path/to/shaping"    # uncomment + set an absolute path
```
