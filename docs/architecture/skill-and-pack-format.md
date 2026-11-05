# Skill & pack format

> The format has three layers: the open **skill** standard this catalogue
> conforms to, the **pack** envelope that wraps a skill for distribution, and
> the **projection** that fans one pack source out to every agent. This page is
> the map. Each layer's detail lives in its own page.

The practical how-to for authors is
[Author a skill](../../guides/_shared/how-to/author-a-skill.md). This page names
what conforms to an external standard, what the catalogue adds, and where each
part is specified.

## The three layers

| Layer | What it is | Authoritative page |
| --- | --- | --- |
| 1. Skill | A `SKILL.md` + optional bundled files. Conforms to the open [agentskills.io](https://agentskills.io/specification) standard. | agentskills.io (external) + [`author-a-skill.md`](../../guides/_shared/how-to/author-a-skill.md) |
| 2. Pack | The envelope that ships a skill (and other primitives): `pack.toml`, `.apm/<primitive>/`, `seeds/`, `.claude-plugin/plugin.json`. | [`pack-layout.md`](pack-layout.md), [`pack-manifest.md`](pack-manifest.md) |
| 3. Projection | One pack source → many agent outputs, routed by the adapter contract. | [`agentbundle.md`](agentbundle.md), [`contracts/adapter.toml`](../../contracts/adapter.toml) |

Above all three sits the [catalogue](catalogue/README.md), identified by a root
`catalogue.toml` and a literal root `packs/` directory. Adapter projections such
as `.claude-plugin/marketplace.json` are generated only when their adapter is
enabled. The contracts that define layers 2 and 3 are published as the
[catalogue specification](catalogue/specification.md).

## Layer 1 — the skill (an open standard)

A skill is a directory with a `SKILL.md` at its root and optional
`scripts/`, `references/`, and `assets/` beside it. The file's shape — YAML
frontmatter (`name`, `description`, and optional `license`, `compatibility`,
`metadata`, `allowed-tools`) followed by Markdown instructions — is the
**[agentskills.io specification](https://agentskills.io/specification)**. The
field table, character limits, and naming rules are canonical there and are not
restated here.

The catalogue adds two constraints on top of the standard, enforced by the
linters (`agentbundle catalogue verify`'s agent-artifact step on projections,
`agentbundle lint packs` on sources) and not by a schema change:[^1]

- **Frontmatter uses only the agentskills.io keys.** Project-specific data
  goes under the `metadata:` escape hatch the spec provides — never as a
  bespoke top-level key. Catalogue packs follow this rule. Third-party content
  is read, not refused, and routinely carries its own top-level keys.
- **A skill `description` may be a YAML block scalar; an agent's may not.**
  Folded (`>`) and literal (`|`) forms are read for skills, with every chomping
  indicator. Every adapter copies a skill directory byte-for-byte, but rewrites
  agent frontmatter key by key with a line-based parser that would read
  `description: >` as the literal `">"` and drop the text. Agents therefore
  refuse block scalars under `CAT-L027`.[^2]

The other primitives a pack carries (`agent`, `hook-body`, `hook-wiring`,
`command`, `kiro-ide-hook`, and the three runtime-root rails `shared-libs`,
`adapter-root-bins`, `user-libs`) are catalogue-defined shapes, tabulated in
[`pack-layout.md`](pack-layout.md) and specified in the adapter contract.

### Method in the skill, rules as data

The format does not constrain how a skill is organised inside. One arrangement
recurs. A **standard-driven** skill keeps the *method* in `SKILL.md` and the *rules the
method enforces* in `references/`, as a bundle: a manifest, the per-phase rule
files it points at, and a quality-gate checklist — plus, for events, a named
envelope component.

An organisation swaps the rules by writing a
base-plus-delta bundle that `extends` the bundled default, rather than forking
the skill. The `contracts` pack ships two skills in this shape, `api-contract` for REST and
`event-contract` for events, and `event-contract` splits its data along two
independently swappable axes: the design ruleset, and the message envelope
format its manifest names under a reserved key.[^3]

**No program parses a manifest or resolves an `extends` chain.** The skill reads
its base and its delta the way it reads any other reference file. The build
walks and copies these files like any others, but nothing interprets them, so
there is no runtime resolver.

Which skill authors a given contract type is likewise resolved by **runtime
roster name**, not through a pack manifest. `core`'s contract-type map names
`api-contract` and `event-contract` without depending on the `contracts`
pack.[^4]

## Layer 2 — the pack (the distribution envelope)

In this catalogue a skill ships inside a pack. The pack adds the metadata
(`pack.toml`), the install-scope rules, the governance `seeds/`, and the Claude
Code `plugin.json` that make a set of primitives installable as one kit.

A skill can also be installed without a pack through direct installation, which
is **manifestless** and described in
[`catalogue/README.md`](catalogue/README.md#identity). Everything this catalogue
publishes ships as a pack. The on-disk shape and every file's role are
in [`pack-layout.md`](pack-layout.md).

How `pack.toml` metadata projects into the
catalogue listing is in [`pack-manifest.md`](pack-manifest.md).

## Layer 3 — projection (one source, many agents)

The same pack source projects into Claude Code, Codex, Cursor, Copilot, Gemini,
and Kiro (the `kiro-ide` and `kiro-cli` adapters, plus a deprecated `kiro`
alias), each with its own layout for skills and agents. Which projection mode
applies to each primitive per adapter is declared in
[`contracts/adapter.toml`](../../contracts/adapter.toml) and executed by the
build pipeline described in [`agentbundle.md`](agentbundle.md). The
authoritative format spec for the projection modes is
[`../specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md).

## Where to read next

- [`catalogue/README.md`](catalogue/README.md) — the directory these packs live in, and how
  to stand up your own.
- [Author a skill](../../guides/_shared/how-to/author-a-skill.md) — the hands-on
  how-to, including the `evals/` convention.
- [`pack-layout.md`](pack-layout.md) — the pack's on-disk shape.

[^1]: `packages/agentbundle/agentbundle/catalogue_tooling/verify.py` (`_step_agent_artifacts`); `cli.py` (`lint packs`).

[^2]: `catalogue_tooling/diagnostics.py` (`CAT_L027`); `catalogue_tooling/lint.py` (agent block-scalar check); the adapters under `build/adapters/`.

[^3]: `packs/contracts/.apm/skills/api-contract/SKILL.md` (manifest `extends` is applied by reading); `packs/contracts/.apm/skills/event-contract/`.

[^4]: `packs/core/.apm/skills/new-spec/references/contract-types.md`.
