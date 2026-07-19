# `agentbundle-layout.toml` — the `[experience]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls
where output-producing packs write their durable work. It is never shipped
into a projected path; you create it by hand (or an `agentbundle install`
step appends a default section to one you already have — **append-if-exists
/ never-create / never-overwrite**). On the rare append of a *missing*
section, the installer re-emits the file and does **not** preserve freeform
comments or off-schema keys; an existing section is left byte-identical.
This page documents the `[experience]` section that the artifact-writing
skills in this pack read.

## The `[experience]` table

One key:

```toml
[experience]
parent = "docs/design"   # a base directory; output files go *under* it
```

- **`parent` is a base, not the leaf.** Each output file is written under a
  subdirectory of `parent` — never to `parent` itself. The file-per-slug
  shapes across the pack are:
  - `journey-mapping` → `<parent>/journeys/<slug>.md`
    (frontmatter `type: customer-journey`)
  - `service-blueprint` → `<parent>/blueprints/<slug>.md`
    (frontmatter `type: service-blueprint`)
  - `user-flow` → `<parent>/screens/<slug>-flow.md`
    (frontmatter `type: screen-flow`) + per-screen briefs at
    `<parent>/screens/<slug>/<screen-name>.md`
  - `process-mapping` → `<parent>/processes/<slug>.md`
    (frontmatter `type: process-flow`)

  **This skill** writes the `journeys/<slug>.md` shape with
  `type: customer-journey`.

## Two locations, repo overrides user

The skill reads the **repo-root `./agentbundle-layout.toml`**
`[experience]` table if present, else the **user-profile
`~/.agentbundle/agentbundle-layout.toml`** table. When both define
`[experience]`, the repo file's table wins; a table present only in the
user file still applies.

## `parent` is anchored by the file's own location

- A **repo-root** file's `parent` is **repo-root-relative** (an absolute
  value is allowed but flagged non-portable).
- A **user-profile** file's `parent` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first*
  deviation — never silently resolved against the ambient working directory.

Regardless of anchor, the skill resolves `parent` to its full absolute path
(realpath-resolved, `~`-expanded, `..` rejected) and **surfaces that path
before the first write**. A repo-root-sourced `parent` that resolves outside
the repo tree is treated as untrusted-origin and confirmed before writing.

## Default and posture

When no `[experience]` section resolves, the pack defaults to `docs/design`
(its `[pack.layout.repo]` default) — committed design docs, the natural home
for journeys, blueprints, screen flows, and process maps in a product repo.

The `experience` pack ships **no `[pack.layout.user]` default** — its output
is per-repo (each journey or blueprint belongs to a specific product). For a
personal cross-repo default, write an `[experience]` section into your
user-profile file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[experience]
# parent = "/abs/path/to/design-docs"   # uncomment + set an absolute path
```

## Discover-by-marker fallback

If neither a config table nor the default resolves to an existing directory,
search the workspace for an existing artifact by its canonical frontmatter
`type:` field:

- `type: customer-journey` — locates an existing journey map
- `type: service-blueprint` — locates an existing service blueprint
- `type: screen-flow` — locates an existing screen flow
- `type: process-flow` — locates an existing process map

The first match's parent directory is used as `<parent>` for subsequent
writes — so a team that already chose a different layout is not forced to
reorganize. When no marker is found either, surface the conflict and ask the
adopter where design artifacts should live before writing.
