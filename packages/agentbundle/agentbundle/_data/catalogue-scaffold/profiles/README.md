# Profiles

This directory contains catalogue profiles. Each `.toml` file directly under this directory
whose stem matches `^[a-z0-9][a-z0-9-]*$` is an installable profile.

Subdirectories beginning with `_` (such as `_example/`) are reserved for catalogue authoring
support and are not catalogue payload. Their `profile.toml` files do not appear in
`agentbundle list-profiles` and are not installed.

## What a profile is

A profile is a named, single-scope set of packs that an adopter installs in one command. It is a
hand-authored TOML file that composes existing packs into a coherent toolkit for a role or workflow.

## When to use a profile instead of a pack

Use a profile when you want to ship a curated set of packs as a unit — a role toolkit, a workflow
bundle, or a recommended starting set. Use a pack when you want to ship new skills, agents, hooks,
or other primitives.

## Profiles compose packs; they do not contain primitives

A profile lists packs to install. It introduces no new skills, agents, hooks, or commands. The
installed behavior comes entirely from the listed packs.

## Scope homogeneity

All packs in a profile must support the profile's declared `scope`. A `"user"` profile requires
every listed pack to allow user-scope installation. A `"repo"` profile requires every listed pack
to allow repo-scope installation.

## Required-dependency completeness

If pack B depends on pack A, both must appear in the profile. The profile is the complete,
self-contained dependency closure for the user who installs it.

## Dependency-first ordering

List packs in dependency-first order — required dependencies before the packs that require them.
The installer processes the list in order.

## Starting from the example

1. Copy `profiles/_example/profile.toml` to `profiles/<your-profile>.toml`.
2. Set `scope` to `"repo"` or `"user"`.
3. Set `description` — one sentence describing the persona or workflow.
4. List packs in dependency-first order.
5. Run `agentbundle catalogue verify --root .` from the catalogue root.
6. Run `agentbundle list-profiles <catalogue>` to confirm the profile appears.

## How profiles are installed

```bash
agentbundle install --profile <profile-id>
```

This resolves each listed pack and installs them in the declared order.

## Profile documentation and persona prose

Profiles do not currently carry extended documentation fields. A profile's `description` is the
primary human-facing text. Future schema versions may add structured persona, outcome, or tutorial
fields.

## Further reading

- `profiles/AGENTS.md` — agent-facing profile authoring contract (full schema, semantic rules,
  validation commands)
- [Catalogue CI contract](../guides/_shared/reference/catalogue-ci-contract.md) — provider-neutral
  CI pipeline contract
