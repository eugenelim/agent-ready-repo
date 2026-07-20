# `agentbundle-layout.toml` — the `[architecture]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical. This page documents the `[architecture]`
section that `architect-design` and `architect-diagram` read.

## The `[architecture]` table

One key:

```toml
[architecture]
output_dir = "docs/design"   # a base directory; per-effort folders go *under* it
```

- **`output_dir` is a base, not the leaf.** Each design effort gets its own
  topic-named child folder or file under `output_dir`:

  | Skill | Output path |
  | --- | --- |
  | `architect-design` | `<output_dir>/<topic-slug>/` (per-effort folder containing the design doc, diagrams, and notes) |
  | `architect-diagram` | `<output_dir>/<topic-slug>.mmd` (kebab-case diagram file) |

  `<topic-slug>` is a short (~2–5 word) kebab-case slug derived from the design
  doc's title. `output_dir` is never the folder a single effort lands in.

## Repo-root first, then user-profile

The skill resolves `output_dir` in two steps before elicitation:

1. **Repo-root config** — read `./agentbundle-layout.toml`
   `[architecture] output_dir` if the file exists and the key is present.
   Repo-scope takes priority so that a project or team convention applies
   when you're working in this repo.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[architecture] output_dir` if the file exists and the key is present.
   User-scope is the fallback — useful for a personal vault (e.g. Obsidian)
   or a default output path you use across repos when no repo convention is set.

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
the first write**. A repo-root-sourced `output_dir` that resolves outside the repo
tree is treated as untrusted-origin and confirmed before writing.

```toml
# ~/.agentbundle/agentbundle-layout.toml
[architecture]
output_dir = "~/Documents/MyVault/design"   # absolute path; ~ is expanded
```
