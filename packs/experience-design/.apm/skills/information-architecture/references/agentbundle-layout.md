# `agentbundle-layout.toml` — the `[design]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that declares
where output-producing packs are instructed to write their durable work. It is never shipped
into a projected path; you create it by hand (or an `agentbundle install`
step appends a default section to one you already have — **append-if-exists
/ never-create / never-overwrite**). On the append of a *missing* section, the installer adds that one table and
leaves every other byte of the file unchanged — comments, key order, quoting
style and line endings included. An existing section is never replaced.
This page documents the `[design]` section that the artifact-writing
skills in this pack read.

## The `[design]` table

One key:

```toml
[design]
output_dir = "docs/design"   # a base directory; output files go *under* it
```

- **`output_dir` is a base, not the leaf.** The `information-architecture` skill
  writes to `<output_dir>/screens/<slug>-ia.md` with frontmatter
  `type: information-architecture`, where `<slug>` is a short kebab-case name
  for the screen or flow (e.g. `settings`, `onboarding`, `checkout`). The
  `screens/` directory is created lazily on first write — you do not need to
  pre-create it.

## Repo-root first, then user-profile

Resolve `output_dir` in two steps before elicitation:

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

Regardless of anchor, resolve `output_dir` to its full absolute path
(realpath-resolved, `~`-expanded, `..` rejected) and **state that path, and the
file you read it from, before the first write**. A repo-root-sourced
`output_dir` that resolves outside the repo tree is treated as untrusted-origin
and confirmed before writing.

**This is an instruction, not an enforced boundary.** It holds only on the runs
where the resolution is actually executed, and a skipped resolution leaves no
trace: the write succeeds and looks ordinary. Observed runs show the value is
sometimes recalled from the example above instead of read from the adopter's
file. Do not describe a write as confined, or a path as surfaced, unless you
ran the resolution and read its result. `references/containment.md` states the
full control set and the same limitation.

```toml
# ~/.agentbundle/agentbundle-layout.toml
[design]
output_dir = "~/Documents/MyVault/design"   # absolute path; ~ is expanded
```

## Frontmatter contract

Every information-architecture doc written by this skill includes the following
frontmatter:

```
type: information-architecture
slug: <short kebab-case name>
date: <YYYY-MM-DD>
```

The `type: information-architecture` field is the discover-by-marker key. Do not
omit it; without it the artifact cannot be found by Tier 3 resolution.
