# `agentbundle-layout.toml` — the `[architect]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical (the re-emit runs only when your
section is absent). This page documents the `[architect]`
section that `architect-design` reads.

## The `[architect]` table

One key:

```toml
[architect]
parent = "docs/design"   # a base directory; per-effort folders go *under* it
```

- **`parent` is a base, not the leaf.** Each design effort gets its own
  topic-named child folder under `parent`: `<parent>/<topic-slug>/` where
  `<topic-slug>` is a short (~2–5 word) kebab-case slug derived from the design
  doc's title. The design doc, diagrams, and notes all go inside that folder.
  `parent` is never the folder a single effort lands in.

## File→folder shift

Before this change, `architect-design` offered to save a single loose file,
scanning `docs/design/`, `design/`, `architecture/`, or `docs/` for a home. The
output is now a **per-effort folder** `<parent>/<topic-slug>/`. The scan-then-elicit
behaviour (scanning those four directories) becomes the **default** when no
`[architect]` section resolves — the scan default base is `docs/design`.

## Two locations, repo overrides user

The skill reads the **repo-root `./agentbundle-layout.toml`** `[architect]` table
if present, else the **user-profile `~/.agentbundle/agentbundle-layout.toml`**
table. When both define `[architect]`, the repo file's table wins; a table present
only in the user file still applies. This lets a team commit a repo-wide choice
while an individual keeps a personal default across repos.

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

When no `[architect]` section resolves, the skill falls back to the scan-then-elicit
default: it scans `docs/design/`, `design/`, `architecture/`, `docs/` in order and
uses the first that exists; if none exists, it asks the user. The pack's
`[pack.layout.repo]` default is `docs/design`.

`architect` ships **no `[pack.layout.user]` default** — its output is per-repo
(design docs belong in the repository they describe) and there is no sensible
*absolute* user-scope base. For a personal cross-repo default, write an
`[architect]` section into your user-profile file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[architect]
# parent = "/abs/path/to/design-docs"   # uncomment + set an absolute path
```
