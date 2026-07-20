# `agentbundle-layout.toml` — the `[design]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls
where output-producing packs write their durable work. It is never shipped
into a projected path; you create it by hand (or an `agentbundle install`
step appends a default section to one you already have — **append-if-exists
/ never-create / never-overwrite**). On the rare append of a *missing*
section, the installer re-emits the file and does **not** preserve freeform
comments or off-schema keys; an existing section is left byte-identical.
This page documents the `[design]` section that the artifact-writing
skills in this pack read.

## The `[design]` table

One key:

```toml
[design]
output_dir = "docs/design"   # a base directory; output files go *under* it
```

- **`output_dir` is a base, not the leaf.** Each output file is written under
  a subdirectory of `output_dir` — never to `output_dir` itself. The
  file-per-slug shapes across the pack are:

  | Skill | Output path |
  | --- | --- |
  | `journey-mapping` | `<output_dir>/journeys/<slug>.md` |
  | `service-blueprint` | `<output_dir>/blueprints/<slug>.md` |
  | `user-flow` | `<output_dir>/screens/<slug>-flow.md` + `<output_dir>/screens/<slug>/<screen>.md` |
  | `process-mapping` | `<output_dir>/processes/<slug>.md` |

  Each directory (`journeys/`, `blueprints/`, `screens/`, `processes/`) is
  created lazily on first write by the writing skill — you do not need to
  pre-create it.

## Repo-root first, then user-profile

The skill resolves `output_dir` in two steps before elicitation:

1. **Repo-root config** — read `./agentbundle-layout.toml` `[design] output_dir`
   if the file exists and the key is present. Repo-scope takes priority so that
   a project or team convention applies when you're working in this repo.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[design] output_dir` if the file exists and the key is present. User-scope is
   the fallback — useful for a personal vault (e.g. Obsidian) or a default output
   path you use across repos when no repo convention is set.

When neither config resolves, the skill runs two-branch elicitation — see
the SKILL.md body for the full procedure.

## `output_dir` is anchored by the file's own location

- A **repo-root** file's `output_dir` is **repo-root-relative** (an absolute
  value is allowed but flagged non-portable).
- A **user-profile** file's `output_dir` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

Regardless of anchor, the skill resolves `output_dir` to its full absolute path
(realpath-resolved, `~`-expanded, `..` rejected) and **surfaces that path before
the first write**. A repo-root-sourced `output_dir` that resolves outside the
repo tree is treated as untrusted-origin and confirmed before writing.

```toml
# ~/.agentbundle/agentbundle-layout.toml
[design]
output_dir = "~/Documents/MyVault/design"   # absolute path; ~ is expanded
```
