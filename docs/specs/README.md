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
| [`converters-pack/`](converters-pack/spec.md) | Approved | RFC-0007 | First user-scope pack: imports `file-to-markdown`, `markdown-to-html`, `msg-to-markdown` from the source catalogue as a vendored snapshot. `default-scope = "user"`, `allowed-scopes = ["user", "repo"]`. 8 ACs (pack.toml shape, attribution scrub, Rail C clean, evals carry-over, evals JSON validity, source SHA pinned, fixture-`$HOME` install/uninstall, pytest CI invocation, runtime-dep disposition, `node_modules/` gitignore note). 7 plan tasks; one PR. Depends on RFC-0004's user-scope dimension. |
| [`claude-plugins-install-route/`](claude-plugins-install-route/spec.md) | Draft | RFC-0008 | F-claude-plugin-derivation + F-claude-plugin-install-marker: per-pack `SessionStart` writer drops `.adapt-install-marker.toml` on first install via Claude-plugins; build derives `pack.toml`, `install-marker.py`, and the `hooks.SessionStart` block into each `.claude-plugin/`. Adapter contract v0.3 → v0.4 (`install-routes` on `[adapter."claude-code"]`); marker schema gains optional `install-route`; `unresolved-markers` / `new-companions` relaxed to optional. Amends `adapt-to-project/spec.md` (3 new ACs + proactive cache-scan branch on the skill body) and `distribution-adapters/spec.md` (conformance suite cases per route). Depends on `distribution-adapters`, `adapt-to-project`. |
| [`codex-native-skills/`](codex-native-skills/spec.md) | Draft | RFC-0009 | Flips Codex `skill` projection from `managed-block-inline` (one-line descriptions in `AGENTS.md`) to `direct-directory` (full skill bodies at `.agents/skills/<name>/SKILL.md`). Pairs the contract flip with: a one-shot migration strip on first install (removes the legacy `<!-- agent-skills:start/end -->` block in `AGENTS.md`); a uniform `project_packs(pack_paths, ...)` entry point across `codex`/`claude-code`/`kiro` so `self_host.py` routes all three the same way; a shared `sweep_orphans` helper that removes stale `<name>/` directories under each adapter's projected skill dir after every multi-pack call; deterministic last-wins for same-name skill collisions across packs (Q2 lean); cross-cutting orphan cleanup across all three direct-directory adapters (Q3 lean); unconditional migration strip (Q4 lean). 9 tasks; T8 amends `distribution-adapters/spec.md`; T9 lands the `tools/lint-agents-md.py` warning + changelog entry. Depends on `distribution-adapters`. |

## Shipped specs (archived)

<!-- Once a feature is shipped, move its row here. The spec stays in place
     as documentation of the feature's contract. -->

| Spec | Status | Constrained by | Notes |
| --- | --- | --- | --- |
| [`skill-secrets/`](skill-secrets/spec.md) | Shipped | RFC-0006, ADR-0002 | RFC-0006 implementation: two-layer architecture (skills don't hold credentials; credentialed primitives do); three storage tiers (env → OS keyring (macOS `/usr/bin/security`, Windows ctypes against `advapi32`) → `~/.agentbundle/credentials.env`); stdlib-only `agentbundle.credentials` loader; `agentbundle creds` verb (`setup`/`check`/`where`/`rm`, no `get`); SKILL.md `metadata.credentialed` + `metadata.primitive-class` frontmatter (nested under the agentskills.io-spec `metadata:` escape hatch); `conventions-check` argv-ban + "Don't"-block lint; ADR-0002 narrow-"hook-shaped" amendment. AC34/AC35 inheritance invariants enforced by future test PRs adding fixtures; everything else closed across T1–T13c. |
| [`wire-session-start-hook/`](wire-session-start-hook/spec.md) | Shipped | RFC-0001, RFC-0004 | Ships hook-wiring for the core pack's `session-start.py` hook body so `agentbundle install core` auto-writes the Claude Code `SessionStart` binding into `<output>/claude-plugins/core/.claude/settings.local.json` (dist-tree path; Claude Code's plugin marketplace consumes from there) and into the workspace flat path `<workspace>/.claude/settings.local.json` via self-host. Wiring TOML uses Claude Code's documented nested SessionStart schema. Bundled a legacy-fixture rewrite of three stale `pre-commit.toml` upgrade-catalogue fixtures to nested shape with a static stub command. Mid-EXECUTE spec amendment corrected paths from flat to dist-tree (root cause: original ACs cited paths without tracing them to the producing recipe). Fixed a latent self_host.py drift-loop bug along the way (now consults `EXCLUDED_PATTERNS`). 10 ACs, 7 tasks; PR #98. Kiro support deferred to a separate spec that needs a `steering` primitive. |

## Adding a new spec

```bash
mkdir -p docs/specs/<feature-name>
cp .claude/skills/new-spec/assets/spec.md docs/specs/<feature-name>/spec.md
cp .claude/skills/new-spec/assets/plan.md docs/specs/<feature-name>/plan.md
```

Or, in Claude Code, run `/new-spec "<feature-name>"`.
