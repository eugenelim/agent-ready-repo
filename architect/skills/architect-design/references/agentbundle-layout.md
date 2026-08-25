# `agentbundle-layout.toml` — the `[architecture]` section

`agentbundle-layout.toml` is an optional, **adopter-owned** source of destination
candidate evidence. It does not control every architecture surface and is not a
global semantic-surface registry. It is never shipped into a
projected path; you create it by hand (or an `agentbundle install` step appends a
default section to one you already have — **append-if-exists / never-create /
never-overwrite**). On the rare append of a *missing* section, the installer
re-emits the file and does **not** preserve freeform comments or off-schema keys;
an existing section is left byte-identical. This page documents the `[architecture]`
section that Architect output skills may read.

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

## Repository and personal candidate meanings

The same key has different authority in different operating modes:

1. **Repo-root config** — read `./agentbundle-layout.toml`
   `[architecture] output_dir` if the file exists and the key is present.
   It is declared-configuration candidate evidence for the requested semantic
   role. When compatible Core exposes `semantic-surface-resolution.v1`, pass it
   with the other bounded candidates to that resolver; mandatory policy can
   reject it and a stronger permitted destination can win.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[architecture] output_dir` if the file exists and the key is present.
   It proposes an explicit root for `personal-workspace` mode. It never becomes
   repository policy or an established repository destination merely because it
   exists.

Missing configuration is normal. Ask whether the result remains `chat-only`,
uses an exact personal root/file, or belongs to a repository. Do not create a
configuration file or destination silently. In repository mode without
compatible Core, render `repository-handoff` and stop with zero repository
effects; user confirmation can correct its evidence but cannot replace a
confined Wave 1 result.

## `output_dir` is anchored by the file's own location

- A **repo-root** file's `output_dir` is **repo-root-relative** (an absolute
  value is allowed but flagged non-portable).
- A **user-profile** file's `output_dir` **must be an explicit absolute path**
  (`~`-anchored is fine). A relative value there is an *Ask-first* deviation —
  never silently resolved against the ambient working directory.

In `repository-resolved` mode, Wave 1 owns repository confinement and only its
confined result may be written. In `personal-workspace` mode, the exact confirmed
directory is the confinement root: realpath-resolve it, expand `~`, reject
`..`, symlink, junction/reparse-point, and containment uncertainty, recheck
every derived child, and **surface the final path before the first write**.
`architect-design` refuses an exact file because its existing method requires
a per-effort folder; `architect-diagram` may use an exact confirmed file as its
sole target. External locators remain external and are not fetched or coerced
into local paths.

```toml
# ~/.agentbundle/agentbundle-layout.toml
[architecture]
output_dir = "~/Documents/MyVault/design"   # absolute path; ~ is expanded
```
