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

- **`output_dir` is a base, not the leaf.** The `tone-of-voice` skill writes
  to `<output_dir>/copy/<slug>.md` with frontmatter `type: tone-of-voice`,
  where `<slug>` is a short kebab-case name for the surface (e.g. `landing-page`,
  `product-launch`, `onboarding`). The `copy/` directory is created lazily
  on first write — you do not need to pre-create it.

## Repo-root first, then user-profile

The skill resolves `output_dir` in two steps before elicitation:

1. **Repo-root config** — read `./agentbundle-layout.toml` `[design] output_dir`
   if the file exists and the key is present. Repo-scope takes priority so that
   a project or team convention applies when you're working in this repo.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[design] output_dir` if the file exists and the key is present. User-scope is
   the fallback — useful for a personal vault (e.g. Obsidian) or a default output
   path you use across repos when no repo convention is set.

When neither config resolves, the skill runs two-branch elicitation — no silent
default:

- **(a) Repo branch** — suggest `docs/design/` and offer to write `output_dir`
  to `./agentbundle-layout.toml [design]`.
- **(b) Personal/vault branch** — ask for an absolute path (e.g.
  `~/Documents/<VaultName>/design/`) and offer to write to
  `~/.agentbundle/agentbundle-layout.toml [design]`.

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

## Frontmatter contract

Every tone-of-voice doc written by this skill includes the following frontmatter:

```
type: tone-of-voice
surface: <marketing/acquisition | onboarding | announcement | other>
persona: <short persona name or pointer>
date: <YYYY-MM-DD>
```

The `type: tone-of-voice` field is the discover-by-marker key. Do not omit it; without it the artifact cannot be found by Tier 3 resolution.

## Extension to the pack's marker set

`tone-of-voice` extends the `design` pack's existing discover-by-marker set alongside `content-brief` (from `content-design`). An adopter who stores both types in non-default locations can configure each independently via the `[design]` table.
