# monorepo-extras

Monorepo scaffolding on top of `core`. Adds the `new-package` skill and the
`packages/` layout it scaffolds into.

## What's inside

- `new-package` skill.
- `packages/` seed README and a `packages/_example/` template.

## Install

`monorepo-extras` is **repo-scope** — `new-package` scaffolds in `packages/`,
which is meaningless without a monorepo. It **requires `core`** (`^0.1`);
install `core` first or alongside.

```
agentbundle install --pack monorepo-extras <catalogue>
```

## Usage

Ask your agent, for example:

- "Scaffold a new package called `billing`."
- "Add a new package `notifications` from the example template."
