# Packs

This directory contains catalogue packs. Each immediate subdirectory whose name does not begin with
`_` is an installable pack.

Directories beginning with `_` are reserved for catalogue authoring support and are not catalogue
payload. They do not appear in `agentbundle list-packs`, are not installed, and are not included in
packaged catalogue archives.

## What makes a directory an installable pack

A directory is an installable pack when it contains a valid `pack.toml` at its root. The `name` and
`version` fields in `pack.toml` must match the `name` and `version` fields in
`.claude-plugin/plugin.json`.

## Starting from the example

Copy `packs/_example` to `packs/<your-pack>`, then:

1. Update `pack.toml` — set `[pack].name`, `version`, `description`, and `[pack.install]` fields.
2. Update `.claude-plugin/plugin.json` — set `name`, `version`, and `description` to match.
3. Rename `.apm/skills/example-skill` to your skill name and rewrite `SKILL.md`.
4. Update `evals/eval_queries.json` with activation fixtures for your skill.
5. Rewrite `README.md` with your pack's outcome, audience, and install instructions.
6. Run `agentbundle catalogue verify --root .` from the catalogue root.

## Pack source versus generated projections

`.apm/` is the source of truth for primitives (skills, agents, hooks, commands, hook-wiring, etc.).
These are projected by `agentbundle catalogue self-host --root . --write` into the adapter-specific
layouts the agent IDEs expect. Never edit the projected outputs directly.

## The role of `pack.toml`

`pack.toml` declares pack identity, version, adapter-contract version, install scope, categories,
dependencies, and evals coverage. See `packs/AGENTS.md` for the full schema map.

## The role of `.claude-plugin/plugin.json`

The plugin manifest is validated at build time. Its `name` and `version` must match `pack.toml`
exactly. See `packs/AGENTS.md § Claude plugin JSON format` for the allowed fields.

## The role of `.apm/`

`.apm/` contains all primitive sources: `skills/`, `agents/`, `hooks/`, `hook-wiring/`, `commands/`,
`kiro-ide-hooks/`, `shared-libs/`, `adapter-root-bins/`, `user-libs/`. See `packs/AGENTS.md` for the
full primitive directory list and adapter-contract map.

## Optional seeds and evals

`seeds/` holds adopter scaffold templates delivered on brownfield install.

`evals/eval_queries.json` holds Tier-A activation eval fixtures — should-trigger and near-miss
queries for each user-triggered skill. List every covered skill in `[pack.evals].skills`.

## Versioning expectations

Every non-cosmetic change to pack content requires a version bump in both `pack.toml` and
`.claude-plugin/plugin.json`. Which increment: patch for changed bodies; minor for new primitives;
major for removals.

## The required pack README

Each pack must have a `README.md` that is useful when rendered in source control, a catalogue site,
a registry, or directly from an extracted archive. It must state: pack display name, one-sentence
user outcome, audience, what the pack provides, installation, supported scopes, first useful
invocation, expected result, writes and trust-relevant behavior, dependencies, and a documentation
link when one exists.

Documentation is decoupled from pack source layout — a pack may have centrally authored docs,
external docs, generated docs, or no docs beyond its README. Do not require a `docs/` subdirectory
inside a pack.

## Documentation-hosting independence

A pack's `pack.toml` may declare a `[pack.links].documentation` URL pointing to centrally hosted
documentation. That URL is the canonical user-facing documentation destination. Nothing in the
pack source layout constrains where documentation lives.

## Portable lint and verification commands

```bash
agentbundle catalogue lint --root .
agentbundle catalogue verify --root .
```

Both commands exit 0 on clean and 1 on any error.

## CI admission

Any CI system can validate a pack change by running:

```bash
agentbundle catalogue verify --root . --format json
```

For publication ordering, exit codes, and evidence requirements, see the provider-neutral
[Catalogue CI contract](../guides/_shared/reference/catalogue-ci-contract.md).

## Further reading

- `packs/AGENTS.md` — agent-facing authoring contract (full schema map, version-bump rule,
  primitive directory list, evals, Windows-safe script requirements)
- Agent-facing guidance loaded at session start by agents working in this directory
