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

- **`output_dir` is a base, not the leaf.** The `copy-direction` skill writes
  to `<output_dir>/copy-direction/<slug>.md` with frontmatter `type: copy-direction`,
  where `<slug>` is a short kebab-case name for the surface (e.g. `landing-page`,
  `product-launch`, `onboarding-hero`). The `copy-direction/` directory is created
  lazily on first write — you do not need to pre-create it.

## Repo-root first, then user-profile

The skill resolves `output_dir` in two steps before elicitation:

1. **Repo-root config** — read `./agentbundle-layout.toml` `[design] output_dir`
   if the file exists and the key is present.

2. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
   `[design] output_dir` if the file exists and the key is present.

When neither config resolves, the skill runs two-branch elicitation — no silent
default:

- **(a) Repo branch** — suggest `docs/design/` and offer to write `output_dir`
  to `./agentbundle-layout.toml [design]`.
- **(b) Personal/vault branch** — ask for an absolute path and offer to write to
  `~/.agentbundle/agentbundle-layout.toml [design]`.

## Frontmatter contract

Every copy-direction doc written by this skill includes the following frontmatter:

```
type: copy-direction
surface: <marketing/acquisition | landing-page | announcement | other — name the surface type>
persona: <short persona name or pointer to persona artifact>
date: <YYYY-MM-DD>
```

The `type: copy-direction` field is the discover-by-marker key. Do not omit it; without it the artifact cannot be found by Tier 3 resolution.

## Extension to the pack's marker set

`copy-direction` extends the `design` pack's existing discover-by-marker set alongside `content-brief` (from `content-design`) and `tone-of-voice` (from `tone-of-voice`). An adopter who stores types in non-default locations can configure each independently via the `[design]` table.
