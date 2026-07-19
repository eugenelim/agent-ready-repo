# `agentbundle-layout.toml` — the `[research]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical (the re-emit runs only when your
section is absent). This page documents the `[research]`
section that `research-project-start` reads.

## The `[research]` table

One key:

```toml
[research]
parent = "~/research-projects"   # a base directory; project folders go *under* it
```

- **`parent` is a base, not the leaf.** Each project gets its own topic-named
  child folder under `parent`: `<parent>/<YYYY-MM-DD>-<topic-slug>/` (the start
  date + the question's kebab-case slug). `parent` is never the folder a single
  project lands in.

## Two locations, repo overrides user

The skill reads the **repo-root `./agentbundle-layout.toml`** `[research]` table
if present, else the **user-profile `~/.agentbundle/agentbundle-layout.toml`**
table. When both define `[research]`, the repo file's table wins; a table present
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

When no `[research]` section resolves, the pack defaults to a gitignored
`.context/desk-research/` (its `[pack.layout.repo]` default) — **scratch / out-of-repo
by default**, because a code repo commits the *decision* (the brief), never the
corpus. **Never the committed repo tree** (`docs/`, repo root); pointing at a
durable vault is the deliberate, configured exception.

`desk-research` ships **no `[pack.layout.user]` default** — its output is per-repo and
there is no sensible *absolute* user-scope base. For a personal cross-repo
default, write a `[research]` section into your user-profile file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[research]
# parent = "/abs/path/to/research-projects"   # uncomment + set an absolute path
```
