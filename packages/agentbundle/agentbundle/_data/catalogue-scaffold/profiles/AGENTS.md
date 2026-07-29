# AGENTS.md — `profiles/`

Agent-facing authoring contract for catalogue profiles. **Max 150 lines.**

Read `profiles/AGENTS.local.md` when present — it carries host-specific profile policy beyond
this portable contract.

## What a profile is

A profile is a hand-authored TOML file at `profiles/<id>.toml` that declares a single-scope,
ordered set of packs. It composes existing packs — it introduces no new primitives.

The profile **id** is the filename stem. It must match `^[a-z0-9][a-z0-9-]*$`.

## Current schema fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `scope` | yes | `"repo"` or `"user"` | Installation scope |
| `description` | yes | string | One sentence describing the persona or workflow |
| `[[packs]]` | yes | array of tables | Ordered, dependency-first list; at least one entry |
| `[[packs]].pack` | yes | string | Pack name (the `[pack].name` field in `pack.toml`) |

No other top-level fields are currently defined.

## Semantic rules

**Scope homogeneity.** All packs must allow the profile's declared `scope`. A `"user"` profile
requires every pack to have `"user"` in its `allowed-scopes`.

**Required-dependency completeness.** If pack B has a required dependency on pack A, both must
appear in the profile. The profile must be a self-contained dependency closure.

**Dependency-first ordering.** List required dependencies before the packs that declare them. The
installer runs the list in order.

**No duplicate entries.** Each pack name must appear at most once.

**No conflicts.** Packs with a declared conflict must not appear in the same profile.

## Filename / identity relationship

The profile id is the filename stem. There is no id field in the manifest.
`profiles/solution-architect.toml` → id `solution-architect`.

## Validation commands

```bash
agentbundle catalogue lint --root .
agentbundle catalogue verify --root .
agentbundle list-profiles <catalogue>
```

## Source-of-truth rules

The TOML file is the source of truth. No generated files derive from profiles. Profiles are
never projected by `catalogue self-host`.

## Reserved directories

Any immediate child of `profiles/` whose name begins with `_` is a reserved authoring asset.
Reserved directories are not catalogue payload — they do not appear in `list-profiles`, are not
installed, and are not validated as active profiles.

## Starting from the example

```bash
cp profiles/_example/profile.toml profiles/<your-profile>.toml
# edit scope, description, and packs list
agentbundle catalogue verify --root .
```
