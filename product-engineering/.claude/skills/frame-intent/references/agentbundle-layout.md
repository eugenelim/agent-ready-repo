# `agentbundle-layout.toml` — the `[product]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical. This page documents the
`[product]` section that `frame-intent` and `align-value-stream` read.

## The `[product]` table

One key:

```toml
[product]
output_dir = "docs/product"   # a base directory; output files go *under* it
```

- **`output_dir` is a base, not the leaf.** Each output file is written directly
  under a subdirectory of `output_dir` — never to `output_dir` itself. The
  file-per-slug shapes are:
  - `frame-intent` → `<output_dir>/intents/<slug>.md`
  - `align-value-stream` → `<output_dir>/rollups/<slug>.md`

  A **per-topic folder** is deliberately **not** used: each intent and each
  rollup is a single file handed downstream (`de-risk-intent`, `decompose-intent`,
  `receive-brief`).

## Repo-root first, then user-profile

The skill resolves `output_dir` in two steps before elicitation:

1. **Repo-root config** — read `./agentbundle-layout.toml` `[product] output_dir`
   if the file exists and the key is present. Repo-scope takes priority so that
   a project or team convention applies when you're working in this repo.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[product] output_dir` if the file exists and the key is present. User-scope is
   the fallback — useful for a personal vault (e.g. Obsidian) or a default output
   path you use across repos when no repo convention is set.

When neither config resolves, the skill runs two-branch elicitation — see
the SKILL.md body for the full procedure.

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

```toml
# ~/.agentbundle/agentbundle-layout.toml
[product]
output_dir = "~/Documents/MyVault/product"   # absolute path; ~ is expanded
```

## Pinned output — `decompose-intent`'s briefs

`decompose-intent`'s `docs/product/briefs/<slug>.md` output is **not** governed
by this table. That path is the hand-off to core's `receive-brief` skill and
stays pinned (a deliberate non-goal of this layout config). Only `frame-intent`
(intents) and `align-value-stream` (rollups) read `[product]`.
