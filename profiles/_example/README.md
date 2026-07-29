# Example Profile

This is the canonical starting template for a new profile.

A profile is a named, single-scope set of packs installed together in one command. It composes
existing packs — it does not introduce new primitives.

## How to use this template

1. Copy `profiles/_example/profile.toml` to `profiles/<your-profile>.toml`.
2. Update `scope` to `"repo"` or `"user"`.
3. Update `description` with one sentence describing the persona or workflow this profile serves.
4. List the packs in dependency-first order — if pack B depends on pack A, list A before B.
5. Run `agentbundle catalogue verify --root .` from the catalogue root.
6. Run `agentbundle list-profiles <catalogue>` to confirm the profile appears.

## Profile validation

```bash
agentbundle catalogue verify --root .
agentbundle list-profiles .
```

See `profiles/AGENTS.md` for the full profile schema contract.
