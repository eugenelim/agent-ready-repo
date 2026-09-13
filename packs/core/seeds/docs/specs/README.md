# Specs

> Feature specifications and implementation plans. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#4-specs-and-plans--docsspecsfeature)
> for the spec / plan distinction and lifecycle.

Work that needs a durable delivery contract gets a directory:

```
docs/specs/<feature>/
├── spec.md      ← the contract (objective, boundaries, testing strategy, acceptance criteria): what this feature does
├── plan.md      ← the strategy + construction tests: how we'll build it
└── notes/       ← (optional) research, sketches, rejected approaches
```

## Why there is no index

Specs are discovered by listing this directory. An index over a document
corpus is generated from that corpus or it does not exist — a hand-maintained
one drifts from the specs it describes, and every change to it collides with
every other branch that touches a spec.

## Adding a new spec

Use `new-spec` when the work needs a durable behavior contract and an
implementation and verification strategy. An eligible direct-light request is
session-local and does not create a `docs/specs/` entry.

```bash
mkdir -p docs/specs/<feature-name>
cp .claude/skills/new-spec/assets/spec.md docs/specs/<feature-name>/spec.md
cp .claude/skills/new-spec/assets/plan.md docs/specs/<feature-name>/plan.md
```

Or, in Claude Code, run `/new-spec "<feature-name>"`.
