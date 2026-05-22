# Specs

> Feature specifications and implementation plans. See
> [`../CONVENTIONS.md`](../CONVENTIONS.md#4-specs-and-plans--docsspecsfeature)
> for the spec / plan distinction and lifecycle.

Each feature gets a directory:

```
docs/specs/<feature>/
├── spec.md      ← the contract (objective, boundaries, testing strategy, acceptance criteria): what this feature does
├── plan.md      ← the strategy + construction tests: how we'll build it
└── notes/       ← (optional) research, sketches, rejected approaches
```

## Active specs

<!-- Update this list as features are added. -->

| Spec | Status | Constrained by | Notes |
| --- | --- | --- | --- |
| [`distribution-adapters/`](distribution-adapters/spec.md) | Draft | RFC-0001 | F-spec + F-build: adapter contract, build pipeline, four reference adapters, pack.toml/plugin.json schemas, Tier-1/2/3 model. Format source-of-truth for the other two. |
| [`self-hosting/`](self-hosting/spec.md) | Implementing (Phase 1) | RFC-0001, RFC-0002 | `make build-self` + `make build-check` gate; this repo eats its own dog food. Phase 1 closes adapter-driven `.apm/` primitives, seed projection, marketplace aggregation, CLAUDE.md symlink, drift source-naming, info-level unclassified, fail-fast on missing discovery. Phase 2 (follow-up) adds AGENTS.md body+footer composition (needs Codex multi-pack fix) and LF/mode/symlink comparison-rule strengthening. Depends on `distribution-adapters`. |
| [`agent-spec-cli/`](agent-spec-cli/spec.md) | Draft | RFC-0001, RFC-0003 | `agentbundle` CLI at `packages/agentbundle/`. Library-first; stdlib only; zipapp distribution; eleven subcommands incl. `upgrade` with per-primitive granularity. Depends on `distribution-adapters`. |

## Shipped specs (archived)

<!-- Once a feature is shipped, move its row here. The spec stays in place
     as documentation of the feature's contract. -->

_none yet_

## Adding a new spec

```bash
mkdir -p docs/specs/<feature-name>
cp docs/_templates/spec.md docs/specs/<feature-name>/spec.md
cp docs/_templates/plan.md docs/specs/<feature-name>/plan.md
```

Or, in Claude Code, run `/new-spec "<feature-name>"`.
