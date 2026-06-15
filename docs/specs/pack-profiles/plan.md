# Plan: pack-profiles

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

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
- **Batch pre-flight reuses single-pack `install.run` dry-run — path-jail included, nothing reimplemented** — single-pack `install.run` already runs a *read-only* path-jail probe (Step 8, `install.py:789`) **before** both its write loop (Step 9) and its dry-run return (`install.py:852`). So `install.run(dry_run=True)` exercises the full Steps 1–8 pre-flight — scope, batch dep gate, adapter membership, render, and the path-jail probe — and returns non-zero without writing a byte. The orchestrator dry-runs **every** pack (deps-first, with `_batch_packs` so the dep gate treats in-batch deps as present, and the pinned adapter) before writing **any** pack; a non-zero dry-run aborts the whole profile naming the pack. This extends single-pack's all-checks-before-any-write guarantee to the batch (RFC-0034 D5) without re-deriving `write_jailed`'s internals (Boundary: never reimplement install.run's write logic). Traces to: AC4 · grounded in RFC-0034 D5 (step 4's residual is genuine I/O only — disk full) · rejected: a hand-rolled helper-based pre-flight (would skip the path-jail probe) and a render-and-replicate-the-jail-check (would duplicate Step 8).
- **Batch adapter is resolved once and asserted per-pack — not from the intersection, and not lint-guarded** — explicit `--adapter` else the scope's normal resolution run once (RFC-0034 D5 step 2); each pack asserts membership; a mismatch refuses before any write, naming the pack and suggesting a compatible adapter computed from the batch's `allowed-adapters` intersection. Traces to: AC5 · rejected: an adapter-homogeneity lint invariant (exceeds RFC-0034's fixed scope/dep/order lint triad — the RFC designs the runtime refuse-and-suggest instead) and intersection-based *resolution* (diverges from D5 step 2's "normal resolution run once").

### Interfaces & contracts

- **CLI:** `agentbundle install --profile <name> <catalogue>` (mutually exclusive with `--pack`, which becomes part of a required mutex group in `cli.py`; `--scope` rejected when `--profile` is present); `agentbundle list-profiles <catalogue>` (new subparser modeled on `list-packs`, `cli.py:189`). Traces to: AC3, AC10, AC11.
- **Manifest:** `profiles/<name>.toml` at the catalogue root, read via the existing `resolve_catalogue`→catalogue-dir mechanism (`install.py:185-193`). Internal schema `_data/profile.schema.json` — not an adopter-facing contract in v1 (first-party-curated). Traces to: AC1, AC2.

### Data & schema

`profile.schema.json`: object with required `scope` (enum `user`|`repo`), required `description` (string), required `packs` (array of `{ pack: string }`, ordered), `additionalProperties: false`. Profile id is the filename stem (not a manifest field), validated against `^[a-z0-9][a-z0-9-]*$`. No change to `state` schema (`STATE_SCHEMA_VERSION` unchanged); `install_route` (existing `PackState` field) carries `"profile"`. Traces to: AC1, AC2, AC12, AC13.

### Failure, edge cases & resilience

- **All-pre-flight-before-any-write across the batch:** resolve every pack's scope, adapter, dep gate, and path-jail before the first write; any failure aborts the whole profile, naming the pack, exit non-zero (AC4).
- **Partial write failure:** not transactional (matches single-pack install); deps-first write order guarantees a consistent prefix; emit a per-pack success/fail summary (AC8).
- **Already-installed packs:** filtered out before invoking per-pack install, so refuse-on-reinstall (`install.py:446-454`) is never hit (AC6).
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
- Fail: a user profile naming `core` (scope mismatch); `full-ceremony` with `core` removed (dep-incomplete); a profile whose in-batch dep is present but at a version that does not satisfy the required range (dep version-incomplete); `governance-extras` before `core` (mis-ordered). (AC9)

**Approach:**
- Add `tools/lint-profiles.py` reading every `profiles/*.toml` and each named pack's `pack.toml` (`allowed-scopes`, `[pack.dependencies.required]`, version, incl. the catalogue-qualified match).
- Scope-homogeneity is checked against `allowed-scopes` **membership** of the profile's declared scope — *not* `default-scope` (the `solution-architect` packs are dual-scope, `allowed-scopes = ["user","repo"]`).
- Dep-completeness checks both presence *and* version satisfiability: a required dep must be present earlier in the profile's pack list (or already catalogue-resolvable) at a version satisfying the `^X.Y` range — reuse the caret-minor grammar from `validate_dependencies_required` so the lint and the runtime gate agree.
- Assert the three invariants (scope-homogeneity, dep-completeness, order-validity); exit non-zero with the offending profile + reason. **Adapter-homogeneity is deliberately *not* a lint invariant** (RFC-0034 fixes the lint triad; adapter mismatch is an install-time refuse-and-suggest per AC5).

**Done when:** lint passes on the two shipped profiles and fails each crafted bad fixture.

### T3: Batch-aware dependency gate

**Depends on:** none

**Tests:** (TDD)
- `validate_dependencies_required` with a batch set including `core` accepts `governance-extras`; without it, fails with "install core first". (AC7)
- A dep *not* in the batch set still fails (the parameter widens, never bypasses, the gate).
- Default call (no `also_installing`) is byte-for-byte the existing behavior — existing dep-gate tests stay green.

**Approach:**
- Add an optional `also_installing: set[str] | None = None` parameter to `validate_dependencies_required` (`install.py:3203`); a required dep whose **name** is in `also_installing` is treated as satisfied. Default `None` → existing single-pack behavior unchanged.
- Name-only satisfaction is intentional at pre-flight (nothing is written yet, so no version is on disk): the orchestrator passes the profile's full pack-name set. The **version** range is enforced for real at write time — deps-first order installs `core` first, so each dependent's per-pack gate runs against real state with `core`'s real version — and the T2 lint independently guarantees in-batch version satisfiability at author-time. This split (name at pre-flight, version at write-time + lint) is the load-bearing reason the parameter is a name-set, not a name→version map.

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
- One command installs the set, in order, at the declared scope, on one pinned adapter; already-installed skipped (reported `already present, skipped`, never tripping the single-pack refuse-on-reinstall); per-pack rows carry `install_route="profile"`; pre-flight failure aborts before any write. (AC3–AC8, AC12, AC13)
- **Adapter-disallowed refusal:** pin an adapter one pack excludes → refuse before any write (no state row, no file on disk for any pack), naming the offending pack and suggesting a compatible adapter. (AC5)
- **Path-jail refusal across the batch:** a fixture pack *later* in the batch whose projection escapes its scope's allowed prefixes → the batch dry-run pre-flight refuses with **zero files written for any pack** (incl. the earlier well-formed packs), naming the offending pack. (AC4)
- **Partial-failure (AC8):** monkeypatch `safety.write_jailed` to raise `safety.WriteError` (the genuine-I/O residual — **not** `PathJailError`, which would collide with the path-jail pre-flight test above) on the **second** pack's write; assert the first pack's files + state row persist (no rollback), the second-and-later packs have no files/rows, and the per-pack summary reports the first as success and the second as failure. This verifies the orchestrator's `except (safety.WriteError, OSError)` write-phase catch (step 6), since single-pack `run()` does not itself return non-zero on `WriteError`.
- **`install_route` default unchanged (AC13 / Boundary "Ask first"):** a normal single-pack `install --pack` row still records `install_route="cli"` — the `_install_route` seam must not flip the default.

**Approach:**
- At the **top** of `commands/install.py run()` (before `pack_name = args.pack`), dispatch: `if getattr(args, "profile", None): return _run_profile(args)`. `_run_profile` lives in `install.py` so it can call `run()` per pack without a circular import.
- `_run_profile`:
  1. Read manifest (T1); resolve the declared scope.
  2. Resolve **one** adapter for the batch — explicit `--adapter`, else the scope's normal resolution run once.
  3. For each pack, assert the pinned adapter ∈ its `allowed-adapters` (legacy/None = all allowed); on mismatch **refuse-and-suggest** before anything else, naming the pack and listing the batch's `allowed-adapters` intersection (AC5). This explicit check owns the precise suggestion wording; the dry-run in step 5 re-checks adapter membership too, harmlessly.
  4. Load state; filter out packs already installed at the declared scope (reported `already present, skipped`, AC6) — so the dry-run/write calls never trip single-pack refuse-on-reinstall.
  5. **Pre-flight:** for each remaining pack in deps-first order, call `install.run(dry_run=True, …)` with a constructed args namespace pinning `pack`/`scope`/`adapter`, `_install_route="profile"`, and `_batch_packs` = the profile's pack-name set, **stdout suppressed** (the profile emits its own summary, not N per-file dry-run plans). Any non-zero return aborts the whole profile, naming the pack; **no byte has been written** (AC4 — this is where scope, batch-deps, adapter, render, and the Step-8 path-jail probe all fire for the whole batch).
  6. **Write:** for each remaining pack in deps-first order, call `install.run(dry_run=False, …same args…)` wrapped in `except (safety.WriteError, OSError)`. This catch is **load-bearing**: single-pack `run()`'s projection write loop catches only `safety.PathJailError` (`install.py:880`), so a genuine mid-batch I/O failure (disk full) raised as `safety.WriteError` (subclass of `OSError`, `safety.py:43`) propagates *through* `install.run` rather than returning non-zero — the orchestrator converts it into the pack's `failed` summary line. Stop on the first write failure (no rollback, AC8).
  7. Emit the per-pack summary (`installed` / `already present, skipped` / `failed`).
- Two seams in single-pack `run()`, both backward-compatible via `getattr` defaults: `install_route=getattr(args, "_install_route", "cli")` at the PackState construction site (line ~851), and `also_installing=getattr(args, "_batch_packs", None)` threaded into the Step 3b `validate_dependencies_required` call.
- Reuse `install.run` verbatim for both pre-flight (dry-run) and write; reuse `_locate_pack`/`validate_dependencies_required` for the manifest-side checks. **Do not duplicate `install.run`'s write logic.** Path-jail rides along for free in the dry-run pre-flight (Step 8 runs before the dry-run return — see Design decisions).

**Done when:** integration tests green (incl. adapter-disallowed, partial-failure, install_route-default); single-pack install tests unchanged; the full `packages/agentbundle` pytest passes (dep-gate signature change touches a load-bearing function — `feedback_contract_bump_test_traps`).

### T6: Ship two first-party profiles + CI wiring

**Depends on:** T2, T5

**Tests:** (goal-based)
- `profiles/solution-architect.toml` (user) and `profiles/full-ceremony.toml` (repo) install cleanly against the live catalogue into temp roots. (AC14)
- `lint-profiles` and the new `packages/agentbundle` test paths run in CI. (AC9; CI-wiring convention)
- The full diff for this feature touches no `.claude-plugin/marketplace.json`, no `agentbundle/build/` recipe, and no self-host path — verified by a name-only `git diff --name-only origin/main` over the feature's diff. This is the AC15 artifact (sufficient for an additive, CLI-route-only PR; `profiles/` is a new top-level dir outside `packs/`, so `build-self` never aggregates it into `marketplace.json`). Note: `run_build_check_drift_gates` does **not** assert this invariant — its three gates cover install-marker byte-identity, source-shape plugin.json, and `_emit_basic_string` parity, none of which would fail on a profile-induced marketplace/self-host change — so it is not cited as the enforcement here. (AC15)

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
- 2026-06-14: pre-EXECUTE adversarial review (round 1) amendments — (Blocker 2, partially declined) kept RFC D5 step 2 resolve-once + assert-per-pack, added refuse-and-suggest message + test, declined an adapter-homogeneity lint invariant as exceeding the RFC's fixed lint triad (AC5/AC9/Assumptions); (Concern 3) batch dep gate satisfies by name at pre-flight, version enforced at write-time + by the lint (AC7, T3); (Concern 4) named the partial-failure fault-injection mechanism (T5); (Concern 5) added install_route="cli" single-pack regression test (T5).
- 2026-06-14: pre-EXECUTE adversarial review (round 2) corrections — (Blocker 1, corrected) single-pack `install.run` runs a *read-only* path-jail probe at Step 8 (`install.py:789`) **before** both its write loop and its dry-run return (`install.py:852`); my round-1 "path-jail is write-time only" framing misread the code. Corrected design: the orchestrator dry-run-pre-flights every pack (Steps 1–8 incl. path-jail) before writing any pack, faithfully extending single-pack's all-checks-before-any-write to the batch (RFC-0034 D5). Spec AC4 + "Always do" + AC8 reworded; design decision rewritten; added a path-jail-across-the-batch refusal test (T5). (Blocker 3) AC15's "durable drift-gate" claim was false — `run_build_check_drift_gates` doesn't cover marketplace/build/self-host membership; the name-only `git diff` is the actual artifact (sufficient for this additive PR).
- 2026-06-14: pre-EXECUTE adversarial review (round 3) — (Concern 1) the write-phase `install.run` calls must be wrapped in `except (safety.WriteError, OSError)` because single-pack `run()`'s projection write loop catches only `PathJailError`, so a genuine I/O failure propagates rather than returning non-zero (T5 step 6); (Concern 2) the partial-failure test raises `safety.WriteError` specifically, distinct from the path-jail test's `PathJailError` (T5); (Nit 3) added an AC15 line to the spec's Testing Strategy.
