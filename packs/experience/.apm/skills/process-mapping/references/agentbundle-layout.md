# `agentbundle-layout.toml` — the `[experience]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical (the re-emit runs only when your
section is absent). This page documents the `[experience]` section that the
`experience` pack's artifact-writing skills read.

## The `[experience]` table

One key:

```toml
[experience]
parent = "docs/design"   # a base directory; output files go *under* it
```

- **`parent` is a base, not the leaf.** Each output file is written directly
  under a subdirectory of `parent` — never to `parent` itself. The file-per-slug
  shapes across the pack are:

  | Skill | Output path |
  | --- | --- |
  | `journey-mapping` | `<parent>/journeys/<slug>.md` |
  | `service-blueprint` | `<parent>/blueprints/<slug>.md` |
  | `user-flow` | `<parent>/screens/<slug>-flow.md` + `<parent>/screens/<slug>/<screen>.md` |
  | `process-mapping` | `<parent>/processes/<slug>.md` |

  Each directory (`journeys/`, `blueprints/`, `screens/`, `processes/`) is
  created lazily on first write by the writing skill — you do not need to
  pre-create it.

## Two locations, repo overrides user

The skill reads the **repo-root `./agentbundle-layout.toml`** `[experience]`
table if present, else the **user-profile
`~/.agentbundle/agentbundle-layout.toml`** `[experience]` table. When both
define `[experience]`, the repo file's table wins; a table present only in the
user file still applies. This lets a team commit a repo-wide choice while an
individual keeps a personal default across repos.

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

When no `[experience]` section resolves, the pack defaults to `docs/design`
(its `[pack.layout.repo]` default) — a committed design-artifacts directory,
the natural home for journey maps, blueprints, screen flows, and process maps
in a product repo.

`experience` ships **no `[pack.layout.user]` default** — its output is
per-repo and there is no sensible *absolute* user-scope base. For a personal
cross-repo default, write an `[experience]` section into your user-profile
file by hand:

```toml
# ~/.agentbundle/agentbundle-layout.toml
[experience]
# parent = "/abs/path/to/design-docs"   # uncomment + set an absolute path
```

## Discover-by-marker fallback

If neither a config `[experience]` table nor the `docs/design` default
resolves to an existing directory (the third tier of the canonical
config → default → discover-by-marker order), the skill discovers the parent
directory by scanning for files with a known frontmatter `type:` value and
using their common ancestor:

| Frontmatter value | Written by |
| --- | --- |
| `type: customer-journey` | `journey-mapping` |
| `type: service-blueprint` | `service-blueprint` |
| `type: screen-flow` | `user-flow` |
| `type: process-flow` | `process-mapping` |

Discovery is best-effort — the skill surfaces the discovered candidate path for
confirmation before writing to it. The declared config always wins over discovery.

## This skill's output

`process-mapping` writes `<parent>/processes/<slug>.md` with frontmatter
`type: process-flow`. The `slug` is a short kebab-case name for the process
being mapped (e.g. `warranty-claims`, `supplier-onboarding`, `monthly-close`).
The output path is surfaced to the adopter before the first write; the
`processes/` directory is created lazily.
