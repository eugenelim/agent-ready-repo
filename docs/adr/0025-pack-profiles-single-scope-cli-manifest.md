# ADR-0025: Pack profiles are single-scope, catalogue-owned CLI manifests — not meta-packs

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-14
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0034](../rfc/0034-pack-profiles.md) (accepted proposal — full rationale, options, and prior art); [RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md) (catalogue model, "Common adoption patterns"); [RFC-0004](../rfc/0004-install-scope-per-pack.md) (install scope); [RFC-0031](../rfc/0031-catalogue-package-manager-posture.md) (catalogue posture: hygiene not infrastructure); [ADR-0003](0003-credential-broker-contract.md) (meta-pack option F, rejected); spec: [`docs/specs/pack-profiles/`](../specs/pack-profiles/spec.md).

## Context

The catalogue ships packs that are installed à la carte, one `--pack` per `agentbundle install` invocation ([RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md)). Setting up a role or a repo means N invocations, and the curated knowledge — which packs go together, and for a repo bundle in what order (the governance/docs/monorepo packs each require `core`) — lives only in a prose "Common adoption patterns" table no tool can execute. [RFC-0034](../rfc/0034-pack-profiles.md) was accepted (2026-06-14) to make those combinations one-command installable. This ADR records the architectural shape of that mechanism so the decision is not re-litigated.

Forces constraining the shape:

- **Charter Principle 3** (a habit, not a tool / no runtime infrastructure) and [RFC-0031](../rfc/0031-catalogue-package-manager-posture.md)'s "distribution hygiene, not package-manager infrastructure" posture bound how much machinery a profile may add.
- **Two install lifecycles are genuinely distinct.** Per [RFC-0004](../rfc/0004-install-scope-per-pack.md), user-scope packs are a person's portable, cross-project toolkit; repo-scope packs set up a specific repo. These have different cadences and different state files (`~/.agentbundle/state.toml` vs. a repo's `.agentbundle-state.toml`).
- **The existing install path is single-pack and not transactional.** `agentbundle install` resolves a catalogue URI directly, validates all preconditions before any write (resolve → check → write), but is not rolled back mid-write.
- **The target platform offers only a coupled composition primitive.** Claude Code plugins have no profile/bundle concept; their only native composition is a plugin `dependencies` array (a *meta-plugin*), which is the meta-pack shape this catalogue already rejected ([ADR-0003](0003-credential-broker-contract.md) / RFC-0013 option F, for portability coupling) and which carries no user/repo scope dimension.

## Decision

> A pack profile is a first-party-curated, **single-scope** (repo-only *or* user-only, never mixed), **catalogue-owned** `profiles/<name>.toml` manifest, expanded by the `agentbundle` CLI into ordered per-pack installs — it is **not** a pack, a tracked entity, or a meta-pack.

Specifically:

- **Single-scope, never mixed.** Each profile declares `scope = "user" | "repo"`; every pack in it must allow that scope. A user profile is a role toolkit; a repo profile is a repo setup bundle. Mixing scopes in one profile is forbidden — handling a repo is a separate concern from handling user space.
- **Catalogue-owned, not pack-owned.** Profiles live in a top-level `profiles/` directory (one `profiles/<name>.toml` per profile, id = filename stem), a sibling of `packs/`. `pack.toml` is per-pack and cannot own a cross-pack set.
- **CLI-route only.** `agentbundle install --profile <name>` and `agentbundle list-profiles` read the catalogue tree directly. No change to `.claude-plugin/marketplace.json`, the build pipeline, or self-host. Plugin/APM-route surfacing is deferred (it would require coupled meta-plugins).
- **Thin orchestration over the existing per-pack contract.** Profiles expand to ordered, deps-first per-pack installs with all-pre-flight-before-any-write, one adapter pinned for the whole batch, and already-installed packs skipped. The only `install.py` change is a batch-aware parameter on the required-dependency gate.
- **No new persistent entity.** No profile membership is recorded in state; `upgrade`/`uninstall` stay strictly per-pack. No state-schema bump and no adapter-contract bump.

The concrete schema, CLI surface, dep-gate change, and lint are specified in [`docs/specs/pack-profiles/`](../specs/pack-profiles/spec.md).

## Consequences

**Positive:**

- One-command setup for the most frequent catalogue events (role onboarding, repo stand-up), promoting RFC-0001's blessed combinations from prose to an executable, lint-checked unit.
- The single-scope rule keeps each profile self-contained (one state file, one path-jail) and eliminates any cross-scope half-applied-install window.
- Zero new primitives, zero runtime, no schema/contract bump — stays on the right side of Principle 3 and RFC-0031.
- Adapter-neutral: a profile inherits each pack's `allowed-adapters`; one adapter is pinned per install so a profile never silently splits across adapters.

**Negative:**

- It is convenience over an existing capability, not new capability. It adds a CLI surface and a lint to maintain, and a second way to express "these packs go together" alongside `[pack.dependencies]` (orthogonal in intent — curated set vs. needs — but a reader must learn the distinction).
- Principle 4 ("used often enough to stick") is the weakest justification and was an explicit Approver call at acceptance, not a settled certainty.
- Plugin/APM-route users get no profiles in v1; route parity is deferred and, if ever pursued, costs the rejected meta-plugin coupling.
- First-party-curated only: an adopter wanting their own bundle still loops `--pack` until the deferred adopter-authoring follow-on lands.

**Neutral / to revisit:**

- Adopter-authored profiles and plugin/APM-route parity are deferred (RFC-0034 OQ1/OQ2), demand-driven.
- A repo-scope "set up this repo" bundle and a user-scope role toolkit are both first-class; a *mixed* bundle remains out of scope by design.

## Alternatives considered

- **Do nothing — keep the prose adoption-patterns table.** Rejected: the most frequent setup moments stay N manual commands and the repo dependency ordering stays prose no tool can execute. (RFC-0034 Axis A0.)
- **A first-class profile entity** tracked in state with a profile `upgrade`/`uninstall` lifecycle. Rejected: collides with RFC-0031's no-registry/no-resolver non-goals and Principle 3 (infrastructure). (Axis A2.)
- **Mixed-scope profiles** (one profile spanning user + repo). Rejected: conflates two install lifecycles in one command and reintroduces a cross-scope partial-failure surface. (Axis D-mixed.)
- **A single aggregated `profiles.toml`.** Rejected: a concurrent-PR merge-conflict magnet that cuts against the repo's one-entity-per-file grain. (Axis B1.)
- **Surfacing profiles on the Claude-plugin/APM routes via meta-plugins.** Deferred: the only native composition there is the coupled meta-pack shape (ADR-0003 / RFC-0013 F), which also cannot honor the single-scope rule. (RFC-0034 OQ2.)
- **A meta-pack** (a pack that depends on its members). Rejected as the wrong primitive entirely: it couples packs and breaks portability (ADR-0003 / RFC-0013 option F); a profile is an external, decoupled manifest with no pack→pack edges.

## References

- [RFC-0034: Pack profiles](../rfc/0034-pack-profiles.md) — the accepted proposal, with full options analysis, the spike, and fetched external prior art (pip extras, dnf groups, VS Code Extension Packs, and the Claude Code plugin-dependencies finding).
- Spec: [`docs/specs/pack-profiles/spec.md`](../specs/pack-profiles/spec.md).
