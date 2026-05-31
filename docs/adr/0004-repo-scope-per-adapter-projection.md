# ADR-0004: Per-IDE direct writes are the repo-scope install default; dist-tree is opt-in

- **Status:** Accepted
- **Date:** 2026-05-26
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0012](../rfc/0012-repo-scope-per-adapter-projection.md), [RFC-0011](../rfc/0011-pack-allowed-adapters.md), [RFC-0004](../rfc/0004-install-scope-per-pack.md), [`repo-scope-per-adapter-projection` spec](../specs/repo-scope-per-adapter-projection/spec.md), [ADR-0002](0002-install-scope-per-pack-default-and-allowance.md)

## Context

[ADR-0002](0002-install-scope-per-pack-default-and-allowance.md) settled the **scope dimension** (`repo` | `user`) as a per-pack default-plus-allowance. [RFC-0011](../rfc/0011-pack-allowed-adapters.md) lifted *user-scope* adapter resolution onto a six-step lookup that produces per-IDE projections at `~/.<ide>/`. At repo scope the picture stayed asymmetric and stale:

- `agentbundle install --pack atlassian --scope repo .` produced `<repo>/claude-plugins/atlassian/.claude/skills/...` and `<repo>/apm/atlassian/.apm/skills/...` — the dist-tree shape the catalogue's `make build` produces, dropped into the adopter's repo with no downstream consumer. Adopters install plugins via `/plugin install <pack>@agent-ready-repo` (which reads the catalogue's `dist/`, not their own) or `apm install` (same story).
- A Kiro adopter who wanted `<repo>/.kiro/skills/atlassian-jira/SKILL.md` had no path through `agentbundle install` — RFC-0011's user-scope path landed at `~/.kiro/skills/`, but project-pinned skill versions stayed dist-tree.
- A Codex adopter was stuck in the same spot for `<repo>/.agents/skills/`.
- Copilot at repo scope had no projection of its own; the build pipeline writes `.github/instructions/<pack>.md` but no install verb routed there.
- `DEFAULT_USER_SCOPE_ADAPTER = "claude-code"` covered enterprise rebrand at user scope only; flipping it to `"kiro"` had no effect at repo scope, defeating the single-switch promise.

The forces at play:

1. **Adopters need first-class repo-scope per-IDE installs** — Kiro and Codex adopters have a real gap today, and Copilot at repo scope is the only repo-scope projection the build pipeline already supports.
2. **Catalogue-publishing workflows still need the dist-tree shape** — `make build` produces it, but a small population of scripts also run `agentbundle install --scope repo` to mirror artifacts. Breaking them silently is not acceptable.
3. **The decision is structural, not per-pack** — every shipped adapter participates; the choice can't be made one pack at a time.
4. **The contract is versioned** — v0.6 → v0.7 is the natural cut for adding `allowed-prefixes.repo` per adapter; partial landings (schema accepts the field but resolver doesn't consult it) leave a known-bad coherence state.

## Decision

We will make **per-IDE direct writes the repo-scope install default** and treat the dist-tree producer as an **explicit opt-in via `--emit-install-routes`** for catalogue-publishing workflows.

> `agentbundle install --pack <name> --scope repo --adapter <ide> .` lands the pack at `<repo>/.<ide>/skills/` (or `.agents/skills/` for codex, `.github/instructions/` for copilot). With no `--adapter` flag the install falls back to `DEFAULT_ADAPTER` (today `"claude-code"`). Passing `--emit-install-routes` restores the legacy dist-tree producer.

Four derived rules pin the model concretely:

- **`--adapter` lifts to both scopes.** RFC-0011's `install: --adapter is bound to --scope user` refusal is removed. At repo scope, `--adapter X` routes the resolver's pick; at user scope, semantics are unchanged.
- **Resolver becomes scope-branched.** `_resolve_user_scope_target_adapter` is renamed `_resolve_target_adapter` with a `scope: str` kwarg. The six-step (0–5) lookup branches at three steps only: step 0 (publisher-drift refusal — user-scope-capability subcheck skipped at repo scope), step 4 (user scope probes `~/.<ide>/`; repo scope **does not probe** and returns `DEFAULT_ADAPTER`), step 5 (legacy heuristic — `< v0.7` packs at repo scope route to `kiro` or `claude-code` only).
- **Contract bump v0.6 → v0.7 adds `allowed-prefixes.repo` per adapter.** Every shipped adapter declares its repo-scope projection prefix list; Copilot gets a `[adapter.copilot.scope]` table for the first time. The path-jail consults this list at safety-layer time.
- **Single-constant enterprise rebrand.** `DEFAULT_USER_SCOPE_ADAPTER` renames to `DEFAULT_ADAPTER` (one-release deprecation alias preserved). Flipping the constant covers both `--scope user` and `--scope repo` from one place.

The mutex shape is intentional: `--adapter X --emit-install-routes` at `--scope repo` refuses with a pinned handler-level message (not via `argparse.add_mutually_exclusive_group`, because the exclusion is scope-conditional — `--emit-install-routes` at user scope refuses independently with its own message). The refusal-ordering invariant — `scope.resolve()` → handler-level flag refusals → resolver-internal refusals — is pinned by [AC30b](../specs/repo-scope-per-adapter-projection/spec.md) as a defensive regression witness.

The decision applies to the four user-scope-capable packs (`atlassian`, `figma`, `converters`, `contracts`) and the four repo-only packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`); all eight bump to v0.7 in the implementation PR per RFC-0004 atomicity.

## Consequences

**Positive:**

- A Kiro adopter installs `atlassian` into `<repo>/.kiro/skills/` with one CLI flag — closing the named gap RFC-0011's repo-scope erratum left open.
- Codex adopters get `<repo>/.agents/skills/` via the same code path; Copilot at repo scope (`<repo>/.github/instructions/`) is the first install-verb projection the adapter has ever had.
- Enterprise rebrand flips one constant; both scopes follow.
- Catalogue-publishing workflows survive with a one-line fix (`--emit-install-routes` appended to existing scripts); breakage is opt-in.
- The path-jail's input becomes self-contained — `allowed-prefixes.repo` is one declared list per adapter rather than a transitive derivation from per-primitive projection rules.

**Negative:**

- **Behavioural change at the default.** Adopters scripting `agentbundle install --scope repo .` against any of the four user-scope-capable packs see a different on-disk shape post-merge. The `--emit-install-routes` workaround preserves the legacy shape; the in-band detection at AC24 surfaces the change at install time.
- **Two contract bumps in two RFCs for downstream pack authors.** RFC-0011 bumped to v0.6 last week; RFC-0012 bumped to v0.7. Pack-version pinning friction is real.
- **Legacy step-5 heuristic doubles its live-pack surface.** `< v0.7` packs at repo scope now also hit the heuristic, which can only return `kiro` or `claude-code` — an enterprise rebrand to `codex` / `copilot` cannot route a pre-v0.7 pack at repo scope to those adapters via no-flag default. Pre-existing packs need v0.7 + `allowed-adapters` to escape; retirement of the heuristic gets pushed out at least one minor release.
- **Probe asymmetry between scopes.** User scope probes `~/.<ide>/`; repo scope does not (RFC-0012 § Alternatives #4 — auto-detect would silently misdirect on greenfield repos). This is intentional and load-bearing — the asymmetry is pinned by a dedicated unit test — but counterintuitive to a reader expecting symmetry.

**Neutral / to revisit:**

- `--emit-install-routes` carries a `DeprecationWarning` from day one; if telemetry shows zero adoption across one transitional release, a future RFC drops it and `make build` becomes the sole dist-tree producer.
- Per-pack cross-pack adapter consistency at repo scope is not enforced — pack A can resolve to kiro and pack B to claude-code in the same repo, leaving `<repo>/.kiro/` next to `<repo>/.claude/`. Matches user-scope behaviour; revisit if adopters report it as a footgun.
- `state.adapter` carried `"claude-code"` as a dataclass default for every repo-scope install between RFC-0011 and RFC-0012's ship date. AC24 in-band detection (triggers (a) adapter-disagreement and (b) shape-mismatch) carries affected adopters through; the population is bounded (only `--scope repo` against the four user-scope-capable packs in that window) but unknown without telemetry.

## Alternatives considered

The numbering follows [RFC-0012 § Alternatives considered](../rfc/0012-repo-scope-per-adapter-projection.md) for traceability. This ADR explicitly records the rejection of alternatives **2, 4, 5, 7, and 8**; the others (1, 3, 6) are recorded in the RFC body and not re-litigated here.

- **(2) Build a `kiro-plugins` sibling install route (and `codex-plugins` later).** Mirror [RFC-0008](../rfc/0008-claude-plugins-install-route-parity.md)'s claude-plugins shape per IDE. *Rejected:* Kiro has no programmatic plugin-install API to integrate with — its extension model is Open VSX (VS Code extensions, not skill content) and Kiro Powers has no documented install verb. Building a route for which no upstream consumer exists is premature; adds maintenance burden for no adoption.

- **(4) Auto-probe `<repo>/.<ide>/` symmetrically with user scope.** Mirror the RFC-0011 probe-table heuristic at repo scope. *Rejected:* at user scope the probe leverages the natural fact that IDEs populate `~/.<ide>/` on install. At repo scope, those directories rarely pre-exist except via an earlier `agentbundle install` (which makes the probe self-perpetuating to whichever IDE installed first). The greenfield case dominates; auto-detect would silently misdirect. `DEFAULT_ADAPTER` + explicit `--adapter` covers cases cleanly. A dedicated unit test (`test_repo_scope_does_not_probe_dot_claude`) pins the asymmetry as load-bearing.

- **(5) Keep dist-tree as default; gate per-adapter behind a flag (`--per-adapter` or similar).** *Rejected:* makes the rarely-used legacy shape the default and the common-case workflow the opt-in. The current dist-tree-at-repo-scope shape serves only catalogue publishing; that population is the opt-in, not the default.

- **(7) Fan out at repo scope (write to multiple `.<ide>/` from one install).** *Rejected:* breaks the one-install-one-adapter invariant the rest of the system carries. State-file rows distinguish installed packs by `adapter` and `scope` cleanly; fan-out would mean multiple rows per scope, a state-schema bump, and a new uninstall flow. Multi-IDE adopters run `agentbundle install` twice with different `--adapter` values — a one-line ergonomic cost vs. a structural rewrite.

- **(8) Skip the contract bump; treat `allowed-prefixes.repo` as derivable from existing projection `target-path` values.** *Rejected:* the path-jail needs a single declared list to consult, not a transitive derivation from per-primitive projection rules. The explicit `allowed-prefixes.repo` is one line per adapter and makes the path-jail's input self-contained — and the v0.6 → v0.7 bump was load-bearing anyway because the resolver's step-5 heuristic can't route pre-v0.7 packs to codex/copilot.

## References

- [RFC-0012 — Repo-scope per-adapter projection](../rfc/0012-repo-scope-per-adapter-projection.md)
- [`repo-scope-per-adapter-projection` spec](../specs/repo-scope-per-adapter-projection/spec.md) (implementation contract; AC1-AC37)
- [ADR-0002 — Install-scope per-pack default and allowance](0002-install-scope-per-pack-default-and-allowance.md) (the paired ADR; this one extends ADR-0002's per-pack scope dimension with the per-adapter resolution at the repo half)
- [RFC-0011 — Pack allowed-adapters](../rfc/0011-pack-allowed-adapters.md) (the user-scope substrate this decision lifts to repo scope)
