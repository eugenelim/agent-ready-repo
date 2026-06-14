# Plan: pack-profiles

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is a **thin orchestration layer over the existing single-pack install path**, plus a manifest format, a lint, and one small change to the dependency gate. Shape of the change: (1) a profile-manifest reader + schema (`profiles/<name>.toml`), (2) a batch-aware parameter on `validate_dependencies_required` so a pack's required dep can be satisfied by another pack *in the same batch*, (3) a `--profile` orchestrator in `commands/install.py` that expands a manifest into ordered per-pack installs at the declared scope with all-pre-flight-before-any-write and one pinned adapter, (4) a `list-profiles` CLI verb and the `--pack`/`--profile` required mutex, (5) a `.py` lint enforcing scope-homogeneity + dep-completeness + order-validity against the live `packs/` tree, wired into CI, and (6) the two shipped first-party profiles. The riskiest part is the orchestrator's pre-flight ordering — it must reuse install's resolve→check→write contract across the whole batch without regressing single-pack behavior, so the orchestrator calls into the existing per-pack code paths rather than reimplementing them. Testing story: TDD for the parser, lint, and dep-gate (compressible invariants); a goal-based integration test against a fixture catalogue + temp scope roots for the end-to-end install; goal-based smoke against the live catalogue for the two shipped profiles.

## Constraints

- [RFC-0034](../../rfc/0034-pack-profiles.md) (Accepted 2026-06-14) — the canonical proposal: single-scope, catalogue-owned `profiles/<name>.toml`, CLI-route only, ordered deps-first, one adapter per batch, no state entity, no schema/contract bump. Read first.
- [ADR-0025](../../adr/0025-pack-profiles-single-scope-cli-manifest.md) — the architectural decision (single-scope, catalogue-owned, not a meta-pack).
- [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (scope model), [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) (`allowed-adapters`), [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md) (catalogue model + `[pack.dependencies]`).
- Repo conventions: new tools/lints authored in Python invoked via `sys.executable` (`AGENTS.local.md`); CI runs package tests + lints by **explicit per-path wiring** — a new test path or lint needs a hand-added CI step (user memory: `reference_ci_package_tests_explicit_wiring`, `feedback_two_lint_surfaces`).

## Construction tests

**Integration tests:** one end-to-end test installing `solution-architect` (user) and `full-ceremony` (repo) from a **fixture catalogue** into temp scope roots, asserting (a) ordered installs, (b) one scope per profile, (c) one adapter target, (d) skip-already-installed, (e) per-pack state rows with `install_route="profile"`, (f) a forced write-phase failure leaves a dependency-consistent prefix + a per-pack summary. Lives under `packages/agentbundle/tests/integration/`.

**Manual verification:** `agentbundle install --profile solution-architect .` and `--profile full-ceremony .` against the live catalogue into a throwaway temp scope root; confirm the on-disk result and `list-profiles` output.

## Design (LLD)

Stack: the `agentbundle` reference CLI (Python, argparse in `cli.py`, command handlers in `commands/`, scope/adapter logic in `scope.py`, state in `config.py`, schemas in `_data/`). No new framework; the design conforms to the established module layout.

### Design decisions

- **Orchestrator calls existing per-pack paths, never reimplements them** — keeps single-pack `install` the one source of truth for resolve→check→write; the profile layer only sequences and gates. Traces to: AC3, AC4 · rejected: a parallel install routine (would drift from `install.run`).
- **Manifest is TOML with a closed schema** (`scope`, `description`, `packs`) validated by `_data/profile.schema.json`, mirroring `pack.schema.json`. Traces to: AC1, AC2 · rejected: per-entry scope pins (unneeded — single-scope) and a free-form schema.
- **Order is authored, lint-enforced, not computed** — no runtime topological sort. Traces to: AC9 · rejected: orchestrator topo-sort (RFC-0034 Axis C2).

### Interfaces & contracts

- **CLI:** `agentbundle install --profile <name> <catalogue>` (mutually exclusive with `--pack`, which becomes part of a required mutex group in `cli.py`; `--scope` rejected when `--profile` is present); `agentbundle list-profiles <catalogue>` (new subparser modeled on `list-packs`, `cli.py:189`). Traces to: AC3, AC10, AC11.
- **Manifest:** `profiles/<name>.toml` at the catalogue root, read via the existing `resolve_catalogue`→catalogue-dir mechanism (`install.py:185-193`). Internal schema `_data/profile.schema.json` — not an adopter-facing contract in v1 (first-party-curated). Traces to: AC1, AC2.

### Data & schema

`profile.schema.json`: object with required `scope` (enum `user`|`repo`), required `description` (string), required `packs` (array of `{ pack: string }`, ordered), `additionalProperties: false`. Profile id is the filename stem (not a manifest field), validated against `^[a-z0-9][a-z0-9-]*$`. No change to `state` schema (`STATE_SCHEMA_VERSION` unchanged); `install_route` (existing `PackState` field) carries `"profile"`. Traces to: AC1, AC2, AC12, AC13.

### Failure, edge cases & resilience

- **All-pre-flight-before-any-write across the batch:** resolve every pack's scope, adapter, dep gate, and path-jail before the first write; any failure aborts the whole profile, naming the pack, exit non-zero (AC4).
- **Partial write failure:** not transactional (matches single-pack install); deps-first write order guarantees a consistent prefix; emit a per-pack success/fail summary (AC8).
- **Already-installed packs:** filtered out before invoking per-pack install, so refuse-on-reinstall (`install.py:426-432`) is never hit (AC6).
- **Adapter split:** resolve one adapter once for the batch, assert membership per pack, refuse on mismatch before any write (AC5).

## Tasks

### T1: Profile manifest schema + reader

**Depends on:** none

**Tests:** (TDD)
- Valid manifest (scope/description/ordered packs) parses; id derives from filename stem.
- Missing `scope`, unknown field, non-kebab stem, or non-list `packs` is rejected with a clear error. (AC1, AC2)

**Approach:**
- Add `_data/profile.schema.json` (closed schema, mirrors `pack.schema.json` style).
- Add a reader (e.g. `commands/profile.py` or a `profiles.py` helper) that locates `<catalogue>/profiles/<name>.toml`, validates against the schema via the in-house validator, and returns a typed structure (scope, description, ordered pack list).

**Done when:** parser unit tests green; invalid manifests rejected with named errors.

### T2: Profile lint (scope-homogeneity + dep-completeness + order-validity)

**Depends on:** T1

**Tests:** (TDD)
- Pass: `solution-architect` (all user-scope, no deps) and `full-ceremony` (all repo-scope, `core` first).
- Fail: a user profile naming `core` (scope mismatch); `full-ceremony` with `core` removed (dep-incomplete); `governance-extras` before `core` (mis-ordered). (AC9)

**Approach:**
- Add `tools/lint-profiles.py` reading every `profiles/*.toml` and each named pack's `pack.toml` (`allowed-scopes`, `[pack.dependencies.required]`, incl. the catalogue-qualified match).
- Scope-homogeneity is checked against `allowed-scopes` **membership** of the profile's declared scope — *not* `default-scope` (the `solution-architect` packs are dual-scope, `allowed-scopes = ["user","repo"]`).
- Assert the three invariants; exit non-zero with the offending profile + reason.

**Done when:** lint passes on the two shipped profiles and fails each crafted bad fixture.

### T3: Batch-aware dependency gate

**Depends on:** none

**Tests:** (TDD)
- `validate_dependencies_required` with a batch set including `core` accepts `governance-extras`; without it, fails with "install core first". (AC7)

**Approach:**
- Add an optional `also_installing: set[str]` (or `batch_packs`) parameter to `validate_dependencies_required` (`install.py:3203`); treat those names as present-after when resolving required deps. Default empty → existing single-pack behavior unchanged.

**Done when:** new gate tests green; existing dep-gate tests still green.

### T4: CLI surface — `--profile`, `list-profiles`, mutex, `--scope` rejection

**Depends on:** T1

**Tests:** (goal-based)
- `--profile` and `--pack` mutually exclusive (non-zero exit + message); `--scope` with `--profile` rejected. (AC11)
- `list-profiles` lists id + scope + description against a fixture catalogue. (AC10)

**Approach:**
- In `cli.py`, convert `--pack` into a required mutually-exclusive group with `--profile`; add the `--scope`+`--profile` rejection; add a `list-profiles` subparser modeled on `list-packs` (`cli.py:189`).
- Wire `list-profiles` to glob `profiles/*.toml` via the T1 reader.

**Done when:** CLI parse/behavior tests green.

### T5: Profile install orchestrator

**Depends on:** T1, T3, T4

**Tests:** (goal-based, integration — see Construction tests)
- One command installs the set, in order, at the declared scope, on one pinned adapter; already-installed skipped; per-pack rows carry `install_route="profile"`; pre-flight failure aborts before any write. (AC3–AC8, AC12, AC13)

**Approach:**
- Add the `--profile` branch in `commands/install.py run()`: read manifest (T1) → resolve scope (declared) → resolve one adapter once + assert per pack → filter already-installed → run the batch dep gate (T3) and per-pack pre-flight (scope, path-jail) for all packs → write in listed order, per-pack, recording `install_route="profile"` → emit per-pack summary.
- Reuse existing per-pack helpers; do not duplicate `install.run`'s write logic.

**Done when:** integration test green; single-pack install tests unchanged.

### T6: Ship two first-party profiles + CI wiring

**Depends on:** T2, T5

**Tests:** (goal-based)
- `profiles/solution-architect.toml` (user) and `profiles/full-ceremony.toml` (repo) install cleanly against the live catalogue into temp roots. (AC14)
- `lint-profiles` and the new `packages/agentbundle` test paths run in CI. (AC9; CI-wiring convention)
- The full diff for this feature touches no `.claude-plugin/marketplace.json`, no `agentbundle/build/` recipe, and no self-host path — asserted by a `git diff --name-only origin/main` check in the PR (and guarded going forward by the existing build-check drift gate). (AC15)

**Approach:**
- Add `profiles/solution-architect.toml` and `profiles/full-ceremony.toml` (deps-first; `core` first in full-ceremony).
- Wire `tools/lint-profiles.py` and the new integration test path into the relevant CI workflow (explicit per-path, per the CI-wiring convention) and `make build-check` where the local gate runs lints.

**Done when:** both profiles install; CI runs the lint + tests; `make build-check` green.

## Rollout

- **Delivery:** additive, no flag. New CLI verbs + manifest format + lint; existing per-pack `install`/`upgrade`/`uninstall` untouched. Reversible by removing `profiles/`, the `--profile`/`list-profiles` surface, the dep-gate parameter, and the lint; nothing irreversible (no migration, no published artifact change).
- **Infrastructure:** none.
- **External-system integration:** none — no marketplace.json, build-pipeline, or self-host change.
- **Deployment sequencing:** T1/T3 (manifest + dep gate) before T4/T5 (CLI + orchestrator that consume them); T2 (lint) before T6 (which ships the profiles the lint guards) — captured in `Depends on:`.

## Risks

- **Orchestrator regressing single-pack install.** Mitigation: orchestrator calls existing per-pack code paths; single-pack tests must stay green (T5 done-when).
- **Contract-bump trap on touching `install.py`/`config.py`.** None expected (no schema/contract bump by design), but run the full `packages/agentbundle` pytest by hand — the dep-gate signature change touches a load-bearing function (user memory: `feedback_contract_bump_test_traps`).
- **CI not gating the new lint/tests.** Mitigation: T6 explicitly wires both per-path; verify via a red-then-green CI check, since `make build-check` does not auto-discover package tests.

## Changelog

- 2026-06-14: initial plan, following accepted RFC-0034 + ADR-0025.
