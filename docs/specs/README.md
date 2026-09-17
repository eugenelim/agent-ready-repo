# Specs

> Feature specifications and implementation plans. See
> § Spec and plan below
> for the spec / plan distinction and lifecycle.

Work that needs a durable delivery contract gets a directory:

```
docs/specs/<feature>/
├── spec.md      ← the contract (objective, boundaries, testing strategy, acceptance criteria): what this feature does
├── plan.md      ← the strategy + construction tests: how we'll build it
└── notes/       ← (optional) research, sketches, rejected approaches
```

## Why there is no index

Specs are discovered by listing this directory. There is no index table, because
an index over a document corpus is generated from that corpus or it does not
exist, and a spec index had no reader: nothing in the repository instructed an
agent to read one, while 216 instructions told it to write one. See
[ADR-0112](../adr/0112-index-tables-are-generated-or-absent.md).

## Adding a new spec

Use `new-spec` when the work needs a durable behavior contract and an
implementation and verification strategy. An eligible direct-light request is
session-local and does not create a `docs/specs/` entry.

```bash
# Point SKILL at wherever your agent installed the `new-spec` skill: the install
# root differs per adapter, so this stays a variable rather than a fixed path.
SKILL=<path to the installed new-spec skill>

mkdir -p docs/specs/<feature-name>
cp "$SKILL/assets/spec.md" docs/specs/<feature-name>/spec.md
cp "$SKILL/assets/plan.md" docs/specs/<feature-name>/plan.md
```

Or invoke the `new-spec` skill by name in your agent.

## Spec and plan

`spec.md` is the contract: what the feature does, its boundaries, its testing
strategy, and the acceptance criteria that close it. `plan.md` is the strategy:
how it gets built, in tasks, with the construction tests designed up front.

A spec's status moves `Draft` → `Approved` → `Implementing` → `Shipped`, and may
end `Archived`. A plan's moves `Drafting` → `Approved` → `Executing` → `Done`.
The two vocabularies are separate: plan words in a spec, or spec words in a
plan, are a mistake a status lint can catch.

A shipped spec freezes. Correct it by superseding it, not by editing the body,
and record the erratum where the original cites it.

`workspace.toml` is a lifecycle index over these directories, not a second
requirements store. What a spec obliges lives in the spec; the index carries a
pointer, its status, and its hard dependencies.
