# `agentbundle-layout.toml` — the `[research]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical (the re-emit runs only when your
section is absent). This page documents the `[research]`
section that `desk-research-project-start` reads.

## The `[research]` table

One key:

```toml
[research]
output_dir = "~/research-projects"   # a base directory; project folders go *under* it
```

- **`output_dir` is a base, not the leaf.** Each project gets its own topic-named
  child folder under `output_dir`: `<output_dir>/<YYYY-MM-DD>-<topic-slug>/` (the
  start date + the question's kebab-case slug). `output_dir` is never the folder
  a single project lands in.

## Resolution order — user-scope before repo-scope

The skill reads two locations and resolves them in this order (user wins):

1. **User-scope** — `~/.agentbundle/agentbundle-layout.toml` `[research] output_dir`
   (personal workspace; wins over repo-scope so a configured vault always applies
   regardless of which repo you're in)
2. **Repo-scope** — `./agentbundle-layout.toml` `[research] output_dir`
   (team convention; use when the team commits desk-research output to the repo,
   e.g. `docs/product/research/`)

When both define `[research]`, the user file's `output_dir` wins; a value present
only in the repo file still applies. This lets a personal vault override the team
default without editing the shared file.

## `output_dir` is anchored by the file's own location

- A **repo-root** file's `output_dir` is **repo-root-relative** (an absolute value is
  allowed but flagged non-portable).
- A **user-profile** file's `output_dir` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

Regardless of anchor, the skill resolves `output_dir` to its full absolute path
(realpath-resolved, `~`-expanded, `..` rejected) and **surfaces that path before
the first write**. A repo-root-sourced `output_dir` that resolves outside the repo
tree is treated as untrusted-origin and confirmed before writing.

## Elicitation when no config resolves

When neither file defines `[research] output_dir`, the skill runs two-branch
elicitation — it never defaults to `.context/` or any other silent path:

- **Repo branch** — offers `docs/product/research/` as the committed team default;
  writes `output_dir` to `./agentbundle-layout.toml` on accept.
- **Personal branch** — prompts for an absolute path (illustrative example:
  `~/Documents/<VaultName>/efforts/research/`; no default — Obsidian has no
  universal vault path); writes `output_dir` to
  `~/.agentbundle/agentbundle-layout.toml` on accept.

## `desk-research` ships no `[pack.layout.user]` default

`desk-research`'s output is per-repo and there is no sensible *absolute* user-scope
base. For a personal cross-repo default, write a `[research]` section into your
user-profile file by hand (or accept it during elicitation):

```toml
# ~/.agentbundle/agentbundle-layout.toml
[research]
output_dir = "/abs/path/to/research-projects"   # set an absolute path
```
