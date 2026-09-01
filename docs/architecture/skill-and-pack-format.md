# Skill & pack format

> The format, in three layers: the open **skill** standard we conform to, the
> **pack** envelope that wraps a skill for distribution, and the **projection**
> that fans one pack source out to every agent. This page is the map; each
> layer's detail lives in its own page, linked below.

If you're authoring, the practical how-to is
[Author a skill](../../guides/_shared/how-to/author-a-skill.md). This page exists
so the format is *called out in one place* — what conforms to an external
standard, what we add, and where each part is specified.

## The three layers

| Layer | What it is | Authoritative page |
| --- | --- | --- |
| 1. Skill | A `SKILL.md` + optional bundled files. Conforms to the open [agentskills.io](https://agentskills.io/specification) standard. | agentskills.io (external) + [`author-a-skill.md`](../../guides/_shared/how-to/author-a-skill.md) |
| 2. Pack | The envelope that ships a skill (and other primitives): `pack.toml`, `.apm/<primitive>/`, `seeds/`, `.claude-plugin/plugin.json`. | [`pack-layout.md`](pack-layout.md), [`pack-manifest.md`](pack-manifest.md) |
| 3. Projection | One pack source → many agent outputs, routed by the adapter contract. | [`agentbundle.md`](agentbundle.md), [`contracts/adapter.toml`](../../contracts/adapter.toml) |

Above all three sits the [catalogue](catalogue.md). A source catalogue is
identified by a root `catalogue.toml` and a literal root `packs/` directory;
adapter projections such as `.claude-plugin/marketplace.json` are generated
only when their adapter is enabled.

## Layer 1 — the skill (an open standard)

A skill is a directory with a `SKILL.md` at its root and optional
`scripts/`, `references/`, and `assets/` beside it. The file's shape — YAML
frontmatter (`name`, `description`, and optional `license`, `compatibility`,
`metadata`, `allowed-tools`) followed by Markdown instructions — is the
**[agentskills.io specification](https://agentskills.io/specification)**, an
open format Anthropic released and many agents adopted. We conform to it
rather than inventing our own; the field table, character limits, and naming
rules are canonical there and we do not restate them (restating would drift).

What this repo adds on top of the standard is one constraint, enforced by the
linters (`agentbundle catalogue verify`'s agent-artifact step on
projections, `agentbundle lint packs` on sources), not a schema change:

- **Frontmatter uses only the agentskills.io keys.** Project-specific data
  goes under the `metadata:` escape hatch the spec provides — never as a
  bespoke top-level key. This is our authoring standard for packs in this
  catalogue; it is *not* an admission rule for third-party content, which
  routinely carries its own top-level keys and is read rather than refused.
- **`description` may be a YAML block scalar.** Folded (`>`) and literal (`|`)
  forms are read, with every chomping indicator. The earlier rule against them
  was written for a loose-parsing harness, and that concern turns out to be
  real only for **agents**: every adapter copies a skill directory
  byte-for-byte, but rewrites agent frontmatter key by key with a line-based
  parser that would read `description: >` as the literal `">"` and drop the
  text. Agents therefore still refuse block scalars, under `CAT-L027`.

The other four primitives a pack can carry — `agent`, `hook-body`,
`hook-wiring`, `command` — are our own shapes, tabulated in
[`pack-layout.md`](pack-layout.md) and specified in the adapter contract.

## Layer 2 — the pack (the distribution envelope)

In this catalogue a skill ships inside a pack. The pack adds the metadata
(`pack.toml`), the install-scope rules, the governance `seeds/`, and the
Claude Code `plugin.json` that make a set of primitives installable as one
cohesive kit.

A skill *can* be installed without one. Direct installation accepts a bare
skill folder or a `skills/` collection from a repository that never declared a
pack; such an install is called **manifestless**, takes its identity from the
skill's own directory name, and records provenance in install state instead of
a manifest. The layers below still describe how a pack works, which is how
everything in this catalogue is published. The on-disk shape and every file's role are in
[`pack-layout.md`](pack-layout.md); how `pack.toml` metadata projects into the
catalogue listing is in [`pack-manifest.md`](pack-manifest.md).

## Layer 3 — projection (one source, many agents)

The same pack source projects into Claude Code, Codex, Cursor, Copilot,
Gemini, and Kiro, each with its own layout for skills and agents. Which
projection mode applies to each primitive per adapter is declared in
[`contracts/adapter.toml`](../../contracts/adapter.toml) and executed by the
build pipeline described in [`agentbundle.md`](agentbundle.md). The
authoritative format spec for the projection modes is
[`../specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md).

## Where to read next

- [`catalogue.md`](catalogue.md) — the directory these packs live in, and how
  to stand up your own.
- [Author a skill](../../guides/_shared/how-to/author-a-skill.md) — the hands-on
  how-to, including the `evals/` convention.
- [`pack-layout.md`](pack-layout.md) — the pack's on-disk shape.
