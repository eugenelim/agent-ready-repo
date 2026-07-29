# Plan: catalogue-init-self-hosted

- **Status:** Executing
- **Spec:** [`spec.md`](spec.md)

## Tasks

### T1 — Migrate reusable identity code
**Depends on:** none
**Verification:** Goal-based — module importable; existing export-verify tests pass when pointed at new location.

Approach:
- Create `packages/agentbundle/agentbundle/catalogue_tooling/identity.py` with `Violation`, `verify()`, and `check_ci_boundary()` migrated from `packs/catalogue-curation/.apm/skills/export-catalogue/scripts/export_verify.py`.
- Preserve the exact semantics; add `__all__`.
- Tests: `test_catalogue_tooling_identity.py` (unit tests for both functions).

### T2 — Delete export-catalogue skill and projected copies
**Depends on:** T1 (reusable code migrated first)
**Verification:** Goal-based — directories absent, test gate green.

Approach:
- `rm -rf packs/catalogue-curation/.apm/skills/export-catalogue/`
- `rm -rf .claude/skills/export-catalogue/`
- `rm -rf .agents/skills/export-catalogue/`
- Clean active references: README, plugin description, pack keywords, lint-catalogue-curation-guard.py expected-skills list, eval manifests if any.
- Add test `test_catalogue_self_hosted_export_removal.py` that greps for absence.

### T3 — Update catalogue-curation pack metadata
**Depends on:** T2
**Verification:** Goal-based — `agentbundle catalogue lint --root .` passes; pack.toml schema valid.

Approach:
- `pack.toml`: version → `0.2.0`; remove both `[[pack.dependencies.required]]` blocks; update description; update keywords (remove "white-label", "fork"); update first-value (remove "core pack installed" prerequisite).
- `plugin.json`: version → `0.2.0`; description updated.
- `README.md`: remove export-catalogue row from table; add concise CLI reference for `agentbundle catalogue init --preset self-hosted`.
- Update `test_catalogue_curation_deps.py` to assert curation has NO required deps (not two-hop).

### T4 — Create identity module
**Depends on:** T1 already complete, just formalise in correct package location.
**Verification:** TDD — unit tests in `test_catalogue_tooling_identity.py`.

Tests:
- `verify()` returns empty list when no anchors hit.
- `verify()` returns violations when anchor found in text file.
- `verify()` skips binary files.
- `verify()` attributed mode permits hits inside attribution surface.
- `check_ci_boundary()` returns violation for `.github/workflows/` content.
- `check_ci_boundary()` does not flag `.github/skills/` (allowed adapter path).
- `check_ci_boundary()` flags badge URLs.

### T5 — Extend CLI: catalogue init self-hosted flags
**Depends on:** none
**Verification:** TDD — CLI mode-rule rejection tests exit 2.

Approach:
- Add to `cli.py` `catalogue init` subparser:
  `--preset`, `--tooling`, `--source`, `--adapter` (repeatable), `--pack` (repeatable),
  `--profile` (repeatable), `--guides`, `--attribution`, `--repository-url`, `--owner-email`.
- Extend `commands/catalogue_init.py` to route to self-hosted engine when `--preset self-hosted`.
- Mode-rule enforcement at command entry before any file I/O.

Tests:
- `--tooling` without `--preset` → exit 2, message contains "self-hosted".
- `--source` without `--preset` → exit 2.
- `--preset other` → exit 2.
- `--preset self-hosted` without `--tooling` → exit 2.
- Plain init with `--name` still works.
- `--format json` + all required flags → exit 0.

### T6 — Extend CLI: catalogue package --flavor
**Depends on:** none
**Verification:** TDD — flavor tests.

Approach:
- Add `--flavor runtime|source` (default: `runtime`) to `catalogue package` subparser.
- `--channel` rejected when `--flavor source` (exit 2).
- Route to new source-flavor path in `commands/catalogue_package.py`.

### T7 — Implement source packaging flavor
**Depends on:** T4 (identity module available)
**Verification:** TDD — deterministic archive, manifest present, CI excluded, export skill absent.

Approach:
- Extend `catalogue_tooling/package.py` with `package_source_flavour()` function.
- Generate `self-hosted-source-manifest.json` with schema version, kind, pack inventory, digests.
- Positive allowlist: `catalogue.toml`, `packs/`, `profiles/`, `guides/_shared/`, `.claude-plugin/marketplace.json`, legal files.
- Exclude: `.github/`, `packages/`, `tools/`, `dist/`, `*.local.md`, specs, RFCs, ADRs.
- Output path: `<output>/catalogue-sources/<bundle>/releases/<release>/catalogue-source-<release>.tar.gz`.
- Archive verification: reject kind `agentbundle-self-hosted-source` from normal `install`.

Tests:
- Archive produced with correct output path.
- `.sha256` file present.
- `self-hosted-source-manifest.json` in archive with correct kind.
- No `.github/workflows/` in archive.
- No `export-catalogue` path in archive.
- `--channel` with `--flavor source` → exit 2.
- Archive refused by install (wrong kind diagnostic).

### T8 — Implement self-hosted init engine
**Depends on:** T4, T5
**Verification:** TDD — external mode local fixture; visual/manual dry-run.

Approach:
- Create `catalogue_tooling/initialise_self_hosted.py` with:
  - `SelfHostedSource` dataclass (logical identity, release, archive URI, sha256, revision).
  - `SelfHostedInitConfig` dataclass (all collected fields).
  - `resolve_source()` — local path validation → refuse with diagnostic.
  - `collect_fields()` — flags → interactive prompts (TTY-gated) → defaults.
  - `validate_fields()` — URL/email validation, no credentials in URLs.
  - `select_packs()` — all packs except catalogue-curation; explicit selections + dependency closure.
  - `init_self_hosted()` — main entry point returning `SelfHostedInitResult`.
  - External tooling mode: copy selected packs/profiles, generate catalogue.toml, generate marketplace, plan curation installation.
  - Vendored tooling mode: external mode + copy packages/agentbundle source + place curation under `.agentbundle/tooling/`.
  - Identity pass: bounded text substitution over staged files using `identity.verify()`.
  - Leak check: `identity.verify()` over staged output before commit.
  - Additive atomic commit via existing transaction engine from `initialise.py`.
- `SelfHostedInitResult` extends `InitResult` with preset, tooling_mode, source, attribution_mode, etc.
- JSON output extends init contract additively.

Tests:
- External mode with local source fixture: packs copied, catalogue.toml generated with target identity, curation absent from packs/, marketplace generated, no CI files.
- `--dry-run` produces file plan without writes.
- Missing `--tooling` → exit 2.
- Source with export-catalogue refused.
- Leak check blocks write on white-label violation.
- `--format json` produces valid JSON with all required fields.

### T9 — Update self-host ownership state
**Depends on:** T8
**Verification:** TDD — ownership state recorded; only owned paths removed.

Approach:
- Add `SelfHostOwnershipState` dataclass (schema_version, adapter, managed_paths list of {target_path, pack_identity, source_root_kind, sha256}).
- State stored at `.agentbundle/self-host-state.json` (extend existing state location if any).
- On write: record all files written.
- On subsequent write: only remove previously recorded paths.
- On check: read-only, compare expected vs actual.

Tests:
- After init write, state file records adapter + paths.
- Re-run removes only own tracked paths; untouched files survive.
- Externally installed repo-scope skill survives self-host of unrelated packs.

### T10 — Version bumps, changelog, projections, gates
**Depends on:** all above
**Verification:** Goal-based — `make build-check` green; `agentbundle catalogue self-host --write` clean.

Approach:
- Bump `packages/agentbundle/pyproject.toml` version to `0.25.0`.
- Add `[Unreleased]` → `[0.25.0]` entry in agentbundle `CHANGELOG.md`.
- Add `[Unreleased]` → `[0.2.0]` entry in catalogue-curation changelog (or pack README if no separate changelog).
- Run `agentbundle catalogue self-host --root . --write` to regenerate all projections.
- Run `SKIP_SAST=1 make build-check` (or equivalent test suite).
- Lint spec status.
