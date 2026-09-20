# `agentbundle-layout.toml` — the `[product]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the append of a *missing* section, the installer adds that one table and
leaves every other byte of the file unchanged — comments, key order, quoting
style and line endings included. An existing section is never replaced. This page documents the `[product]` section that
product-facing skills read to locate their output base.

## The `[product]` table

One configurable key, `output_dir`:

```toml
[product]
output_dir = "docs/product"    # a base; each skill composes its own subpath under it
# briefs and intents are pinned hand-offs to core — not configurable here
```

- **`output_dir`** is a base directory, never a leaf. Each consuming skill
  composes its own subpath under it: `frame-intent` writes
  `<output_dir>/intents/<slug>.md`, `align-value-stream` writes
  `<output_dir>/rollups/<slug>.md`, and the six-step shaping sequence writes
  `<output_dir>/shaping/<slug>/...`.
- **`shaping` is not a key of this section.** No skill body reads
  `[product] shaping`; the shaping directory is composed under `output_dir` by
  the skills above, and the product-strategy pack has its own `[strategy]`
  section. This page previously documented `shaping` as the section's only key,
  which was wrong in both directions — it named a key nobody reads and omitted
  the one every consumer does.
- **A hand-off to core is pinned, not configured.** `docs/product/briefs/` and
  `docs/product/intents/` are where core's `author-delivery-brief continue` and
  `intake-intent` look for work; redirecting either breaks the `Brief:` chain or
  intent admission. Both are deliberate non-goals of this config.
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

When no `[product]` section resolves, each consuming skill falls back to its own
pack's declared default — `docs/product` for product-engineering
(`packs/product-engineering/pack.toml` `[pack.layout.repo]`). ADR-0030 keeps that
default in the pack rather than here, so this page states no fallback of its own.
Whether a consumer reaches that default before eliciting is unsettled: RFC-0040's
resolution tail puts it before elicitation and RFC-0096 § 4 has no such step, and
the two are not reconciled.

`core` ships **no `[pack.layout.user]` default** for this section — product
output is per-repo and there is no sensible cross-repo absolute path. For a
personal cross-repo default, write a `[product]` section into your user-profile
file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[product]
# output_dir = "/abs/path/to/product"    # uncomment + set an absolute path
```

A user-profile value governs your own authoring — a personal vault, for
instance. It does not govern a repository hand-off: a repository intent still
goes to `docs/product/intents/` for `intake-intent` to admit, which is a
deliberate non-goal of this config rather than an omission.
