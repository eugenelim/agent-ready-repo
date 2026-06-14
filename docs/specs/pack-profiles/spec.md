# Spec: pack-profiles

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0034](../../rfc/0034-pack-profiles.md), [ADR-0025](../../adr/0025-pack-profiles-single-scope-cli-manifest.md)
- **Brief:** none
- **Contract:** none <!-- CLI feature; the internal profile-manifest schema (`_data/profile.schema.json`) is specified in plan.md, not exposed as an adopter-facing contract in v1 (first-party-curated only) -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter who wants a role's toolkit or a repo's governance setup installs it in **one command** instead of N. `agentbundle install --profile <name> <catalogue>` reads a curated `profiles/<name>.toml` from the catalogue and installs its packs in order; `agentbundle list-profiles <catalogue>` shows the available profiles. A profile is **single-scope** — either a user-scope role toolkit (e.g. `solution-architect` → `architect` + `research` + `contracts`) or a repo-scope setup bundle (e.g. `full-ceremony` → `core` + `governance-extras` + `user-guide-diataxis` + `monorepo-extras`) — and **never mixes scopes**. Success: the adopter runs one command, every pack in the profile lands at the declared scope on one adapter target, dependency-ordered packs install in the right order, and a partial install (rare I/O failure) leaves a dependency-consistent prefix with a clear per-pack summary. A profile install is never less safe than installing each pack by hand.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Run all preconditions for every pack in the batch (scope, dep gate, adapter, path-jail) **before any write** — extend install's existing resolve→check→write contract from one pack to the whole batch.
- Install packs in the profile's authored (deps-first) order, and skip packs already installed at the declared scope, reporting them as `already present, skipped`.
- Pin exactly one adapter for the whole batch (explicit `--adapter`, else the scope's normal resolution run once) and refuse before any write if any pack disallows it.
- Keep each profile single-scope: read the `scope` field and install every pack at that scope.

### Ask first

- Adding a third shipped first-party profile beyond `solution-architect` and `full-ceremony`.
- Any change to the resolved behavior of the existing single-pack `install`/`upgrade`/`uninstall` paths (the profile orchestrator sits above them).
- Introducing a new on-disk schema field beyond `scope`, `description`, and the ordered `packs` list.

### Never do

- **Never mix scopes in one profile** — a profile is repo-only or user-only; reject at lint time any profile whose packs don't all allow the declared scope.
- **Never record a profile as an entity in state** — no profile membership, no profile `upgrade`/`uninstall`; per-pack state rows only. No state-schema bump.
- **Never bump the adapter contract** — profiles carry no adapter info and reuse `_resolve_target_adapter` + each pack's `allowed-adapters` unchanged.
- **Never add a new top-level runtime dependency, a new module boundary outside `agentbundle`, or a new install route** — profiles are CLI-route only; no marketplace.json, build-pipeline, or self-host change.
- **Never modify the existing single-pack `install` refuse-on-reinstall behavior** — the orchestrator filters already-installed packs out instead of triggering it.

## Testing Strategy

- **Manifest schema + parse (id from filename stem, required `scope`, ordered `packs`):** TDD — a compressible invariant (valid/invalid manifests in, accept/reject out).
- **The lint (scope-homogeneity, dep-completeness, order-validity) against the live `packs/` tree:** TDD — each invariant has a clean pass case and a failing case (a user profile naming `core`; a repo profile missing `core`; `governance-extras` listed before `core`).
- **Batch-aware dep gate (`validate_dependencies_required` treats the profile set as present):** TDD — `full-ceremony` passes because `core` is in the batch; the same set with `core` removed fails.
- **`install --profile` end-to-end (one command installs the set, ordered, one scope, one adapter, skip-already-installed, partial-failure summary):** goal-based, exercised by an **integration** test against a fixture catalogue + temp scope roots — assert the resulting state rows and on-disk files.
- **`list-profiles` output (id + scope + description):** goal-based — run the command against the fixture catalogue and assert the listing.
- **`--scope` rejected with `--profile`; `--profile` mutually exclusive with `--pack`:** goal-based — assert non-zero exit + message.
- **Both shipped profiles install cleanly against the real catalogue:** goal-based — `solution-architect` (user) and `full-ceremony` (repo) each install in a temp scope root.

## Acceptance Criteria

- [ ] `profiles/<name>.toml` is read from the catalogue root; the profile id is the filename stem and must match `^[a-z0-9][a-z0-9-]*$`.
- [ ] A profile manifest declares a required `scope` (`"user"` | `"repo"`), a `description`, and an ordered `packs` list (each entry a pack name); an unknown field or missing `scope` is rejected.
- [ ] `agentbundle install --profile <name> <catalogue>` installs every pack in the manifest, in listed order, at the profile's declared scope.
- [ ] All preconditions for every pack run before any write; if any pack's precondition fails (scope, missing dep not in the batch, disallowed adapter, path-jail), the command refuses **before writing any pack**, naming the offending pack, and exits non-zero.
- [ ] Exactly one adapter is resolved for the whole batch (explicit `--adapter`, else the scope's normal resolution run once) and applied to every pack; if any pack disallows it, the command refuses before any write.
- [ ] Packs already installed at the declared scope are skipped and reported as `already present, skipped`; the single-pack refuse-on-reinstall path (`install.py:426-432`) is not triggered.
- [ ] `validate_dependencies_required` accepts a "also-installing-in-this-batch" set, so `full-ceremony` installs (the three non-core packs' required `core ^0.1` is satisfied by `core` earlier in the batch); removing `core` from that profile fails the dep gate.
- [ ] On a write-phase I/O failure, packs already written stay (no rollback); the command reports a per-pack success/fail summary and the deps-first order guarantees any installed prefix is dependency-consistent.
- [ ] A lint fails the build when a profile is not scope-homogeneous (a pack does not allow the declared `scope`), is not dependency-complete (a required dep is neither in the set nor satisfiable), or is mis-ordered (a pack's required dep appears later than it).
- [ ] `agentbundle list-profiles <catalogue>` lists each profile's id, scope, and description.
- [ ] `--profile` and `--pack` are mutually exclusive (a required mutex group); `--scope` is rejected when combined with `--profile`.
- [ ] No profile is recorded in state; per-pack rows are written at the profile's scope exactly as a manual per-pack install would; `STATE_SCHEMA_VERSION` is unchanged.
- [ ] `install_route` on each profile-installed pack's state row reads `"profile"` (RFC-0034 OQ3, accepted); the adapter contract version is unchanged.
- [ ] Two first-party profiles ship: `profiles/solution-architect.toml` (`scope = "user"`) and `profiles/full-ceremony.toml` (`scope = "repo"`), each installing cleanly against the live catalogue.
- [ ] No change to `.claude-plugin/marketplace.json`, the build pipeline, or self-host.

## Assumptions

- Technical: the CLI is argparse-based in `cli.py`; `list-packs` (`cli.py:189`) is the precedent shape for `list-profiles`, and install resolves the catalogue via `resolve_catalogue`→`_locate_pack` (`install.py:185-193`). (source: `packages/agentbundle/agentbundle/cli.py`, `commands/install.py`)
- Technical: the required-dependency gate is `validate_dependencies_required` (`install.py:3203`), evaluated against union state; the batch-aware parameter extends it. (source: `packages/agentbundle/agentbundle/commands/install.py:3203`)
- Technical: scope resolves via `scope.resolve` (`scope.py:117`) with `ScopeRefused` on an out-of-`allowed-scopes` request; adapter via `_resolve_target_adapter` with `DEFAULT_ADAPTER`. (source: `packages/agentbundle/agentbundle/scope.py`, `commands/install.py`)
- Technical: `solution-architect` packs (`architect`/`research`/`contracts`) are `default-scope = "user"` with no `[pack.dependencies]`, and all three also allow repo scope (`allowed-scopes = ["user","repo"]`); `full-ceremony` packs are repo-scope and the three non-core packs each declare required `core ^0.1`. The scope-homogeneity lint therefore checks `allowed-scopes` *membership* of the declared scope, not `default-scope`. (source: `packs/{architect,research,contracts,core,governance-extras,user-guide-diataxis,monorepo-extras}/pack.toml`)
- Technical: new lint/tool code is authored in Python, invoked via `sys.executable`, for Windows portability. (source: `AGENTS.local.md` convention; user memory)
- Process: this spec is constrained by RFC-0034 (Accepted 2026-06-14) and ADR-0025; it makes no new design decisions. (source: `docs/rfc/0034-pack-profiles.md`, `docs/adr/0025-pack-profiles-single-scope-cli-manifest.md`)
- Product: the feature serves adopters installing a role's user-scope toolkit or a repo's setup bundle in one command. (source: RFC-0034; user confirmation 2026-06-14)
