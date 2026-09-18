# `agentbundle-layout.toml` — the `[design]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that declares
where output-producing packs are instructed to write their durable work. It is never shipped
into a projected path; you create it by hand (or an `agentbundle install`
step appends a default section to one you already have — **append-if-exists
/ never-create / never-overwrite**). On the append of a *missing* section, the installer adds that one table and
leaves every other byte of the file unchanged — comments, key order, quoting
style and line endings included. An existing section is never replaced.
This page documents the `[design]` section that this skill **reads** from:
`design-review` writes no artifact of its own, and resolves the section only
to find the `design-principles` doc it judges findings against.

## The `[design]` table

One key:

```toml
[design]
output_dir = "docs/design"   # a base directory; output files go *under* it
```

- **`output_dir` is a base, not the leaf.** The `design-principles` skill writes
  to `<output_dir>/principles/<slug>.md` with frontmatter `type: design-principles`,
  where `<slug>` is a short kebab-case name for the product (e.g. `checkout`,
  `analytics-dashboard`, `mobile-app`). That is the path this skill reads.

## Repo-root first, then user-profile

Resolve `output_dir` in two steps:

1. **Repo-root config** — read `./agentbundle-layout.toml` `[design] output_dir`
   if the file exists and the key is present. Repo-scope takes priority so that
   a project or team convention applies when you're working in this repo.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[design] output_dir` if the file exists and the key is present. User-scope is
   the fallback — useful for a personal vault (e.g. Obsidian) or a default output
   path used across repos when no repo convention is set.

When neither config resolves, ask which directory holds the design output
rather than assuming one. A read against a guessed directory either misses the
artifact or finds another product's.

## `output_dir` is anchored by the file's own location

- A **repo-root** file's `output_dir` is **repo-root-relative** (an absolute
  value is allowed but flagged non-portable).
- A **user-profile** file's `output_dir` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

Regardless of anchor, resolve `output_dir` to its full absolute path
(realpath-resolved, `~`-expanded, `..` rejected) and approve it under
`references/containment.md` **before the first read**. The same module states
the final-target confinement, `type:` validation, product-belonging, and
extract-as-data controls that apply to the read itself.

**This is an instruction, not an enforced boundary.** It holds only on the runs
where the resolution is actually executed, and a skipped resolution leaves no
trace. Do not describe a read as confined unless you ran the resolution and
read its result.

## Frontmatter contract

The `design-principles` doc this skill reads carries the following frontmatter:

```
type: design-principles
slug: <short kebab-case name>
date: <YYYY-MM-DD>
```

The `type: design-principles` field is the discover-by-marker key. A file at
the resolved path whose `type:` is absent, unparseable, or different is not
this artifact; surface the mismatch rather than reading it as principles.
