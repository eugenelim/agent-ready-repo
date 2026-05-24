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
| [`self-hosting/`](self-hosting/spec.md) | Phase 1 shipped; Phase 2 pending | RFC-0001, RFC-0002 | `make build-self` + `make build-check` gate; this repo eats its own dog food. Phase 1 (shipped) closed AC1a, AC1b, AC2–AC7, AC9–AC17 — adapter-driven `.apm/` primitives, seed projection, marketplace aggregation, CLAUDE.md symlink, drift source-naming, info-level unclassified, fail-fast on missing discovery, branch protection registered, first real edit landed through pipeline. Phase 2 (follow-up) covers AC8 — AGENTS.md body+footer composition (needs Codex multi-pack aggregation fix in the sibling distribution-adapters spec) — and LF/mode/symlink comparison-rule strengthening. Depends on `distribution-adapters`. |
| [`agent-spec-cli/`](agent-spec-cli/spec.md) | Draft | RFC-0001, RFC-0003 | `agentbundle` CLI at `packages/agentbundle/`. Library-first; stdlib only; zipapp distribution; eleven subcommands incl. `upgrade` with per-primitive granularity. Depends on `distribution-adapters`. |
| [`adapt-to-project/`](adapt-to-project/spec.md) | Draft | RFC-0001, RFC-0003 | LLM-driven counterpart to `agentbundle adapt`: walks adopters through the four RFC-0001 classes of change (substitution, `.upstream.<ext>` companion merges, discovery+restructuring, within-layout consolidation). Unifies `.adapt-discovery.toml` schema to `[markers]` + `[[findings.*]]` across CLI and self-host; lights up `[pack.dependencies.required]` enforcement on install; adds install→adapt nudge via `.adapt-install-marker.toml` + session-start hook. Depends on `agent-spec-cli`, `distribution-adapters`. |
| [`user-scope-hooks/`](user-scope-hooks/spec.md) | Draft | RFC-0005 | RFC-0005 implementation contract: `user-merge-json` (Claude Code user scope) + `merge-into-agent-json` (Kiro both scopes — closes RFC-0001 Open Q1); v0.3 state schema with `hook-wiring-owned`; `--force-merge` and `reconcile --scope user`. 13 tasks; T10/T11 amend the sibling specs. Depends on `agent-spec-cli`, `distribution-adapters`. |
| [`skill-secrets/`](skill-secrets/spec.md) | Draft | RFC-0006, ADR-0002 | RFC-0006 implementation contract: two-layer architecture (skills don't hold credentials; credentialed primitives do); three storage tiers (env → OS keyring (macOS `/usr/bin/security`, Windows ctypes against `advapi32`) → `~/.agent-ready/credentials.env`); stdlib-only `agent_ready.credentials` loader; `agentbundle creds` verb (`setup`/`check`/`where`/`rm`, no `get`); SKILL.md `credentialed:` + `primitive-class:` frontmatter; `conventions-check` argv-ban + "Don't"-block lint; ADR-0002 narrow-"hook-shaped" amendment. 15 tasks (T13 split into T13a/T13b/T13c); T1 lands the ADR amendment. Depends on `agent-spec-cli`. |

## Shipped specs (archived)

<!-- Once a feature is shipped, move its row here. The spec stays in place
     as documentation of the feature's contract. -->

_none yet_

## Adding a new spec

```bash
mkdir -p docs/specs/<feature-name>
cp .claude/skills/new-spec/assets/spec.md docs/specs/<feature-name>/spec.md
cp .claude/skills/new-spec/assets/plan.md docs/specs/<feature-name>/plan.md
```

Or, in Claude Code, run `/new-spec "<feature-name>"`.
