# AGENTS.md — `profiles/`

Applies to `profiles/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Profile boundary

A profile is a hand-authored `profiles/<id>.toml` that composes an ordered,
single-scope set of existing packs; it introduces no primitives. The filename stem
is its identifier. Reserved `_` children are authoring assets, not active profiles.

## Validation and ownership

[`contracts/profile.schema.json`](../contracts/profile.schema.json) owns fields and
semantic validation. Profile TOML is the source; profiles are scaffold sources but
are not projected by `catalogue self-host`.

- A pack name appears at most once in a profile.
- Packs with a declared `conflicts` relationship do not share a profile.

## Essential commands

```bash
agentbundle catalogue lint --root .
agentbundle catalogue verify --root .
agentbundle list-profiles <catalogue>
```

## Deeper pointers

Start from `profiles/_example/profile.toml`. Synchronize scaffold projections after
profile-source changes with `tools/catalogue/sync_authoring_scaffold.py`.
