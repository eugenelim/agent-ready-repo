# `agentbundle-layout.toml` — the `[strategy]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where output-producing packs write their durable work. It is never shipped into a projected path; you create it by hand (or an `agentbundle install` step appends a default section). This page documents the `[strategy]` section that the artifact-writing skills in this pack read.

## The `[strategy]` table

One key:

```toml
[strategy]
output_dir = "docs/product/shaping"   # a base directory; output files go directly under it
```

- **`output_dir` is a base, not the leaf.** Each output file is written directly under `output_dir` — never nested further. The file-per-skill shapes are:

  | Skill | Output file |
  | --- | --- |
  | `run-swot` | `<output_dir>/swot-analysis.md` |
  | `run-pestle-analysis` | `<output_dir>/macro-environment.md` |
  | `run-bcg-matrix` | `<output_dir>/portfolio-position.md` |
  | `run-porters-five-forces` | `<output_dir>/competitive-landscape.md` |
  | `run-okr-cascade` | `<output_dir>/okr-cascade.md` |
  | `write-prfaq` | `<output_dir>/prfaq.md` |
  | `define-content-strategy` | `<output_dir>/content-strategy.md` |
  | `define-ux-strategy` | `<output_dir>/ux-strategy.md` |
  | `synthesize-stakeholder-research` | `<output_dir>/stakeholder-synthesis.md` |

## Repo-root first, then user-profile

The skill resolves `output_dir` in two steps before elicitation:

1. **Repo-root config** — read `./agentbundle-layout.toml` `[strategy] output_dir`
   if the file exists and the key is present. Repo-scope takes priority so that
   a project or team convention applies when you're working in this repo.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[strategy] output_dir` if the file exists and the key is present. User-scope is
   the fallback — useful for a personal vault (e.g. Obsidian) or a default output
   path you use across repos when no repo convention is set.

When neither config resolves, the skill runs two-branch elicitation — never
a silent default:

- **Repo branch** — "Commit to this repo? Suggest: `docs/product/shaping/`
  (team-visible, version-controlled). Enter path or press Enter to accept:"
  On accept, write `output_dir = "<path>"` to `./agentbundle-layout.toml
  [strategy]` so subsequent skills skip elicitation.
- **Personal/vault branch** — "Write to a personal workspace (e.g. Obsidian
  vault)? Enter the absolute path. Example:
  `~/Documents/<VaultName>/strategy/` (no default)." On accept, write
  `output_dir = "<path>"` to `~/.agentbundle/agentbundle-layout.toml [strategy]`.

## `output_dir` is anchored by the file's own location

- A **repo-root** file's `output_dir` is **repo-root-relative** (an absolute
  value is allowed but flagged non-portable).
- A **user-profile** file's `output_dir` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

Regardless of anchor, the skill resolves `output_dir` to its full absolute path
(`~`-expanded, `..` rejected) and **surfaces the resolved path before writing**.
A repo-root-sourced `output_dir` that resolves outside the repo tree is treated
as untrusted-origin and confirmed before writing.

```toml
# ~/.agentbundle/agentbundle-layout.toml
[strategy]
output_dir = "~/Documents/MyVault/strategy"   # absolute path; ~ is expanded
```
