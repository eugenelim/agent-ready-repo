# Plan: catalogue-init-self-hosted

- **Status:** Done
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

### T10 — Version bumps, changelog, projections, gates (Phase 1)
**Depends on:** all above
**Verification:** Goal-based — `make build-check` green; `agentbundle catalogue self-host --write` clean.

Approach:
- Bump `packages/agentbundle/pyproject.toml` version to `0.25.0`.
- Add `[Unreleased]` → `[0.25.0]` entry in agentbundle `CHANGELOG.md`.
- Add `[Unreleased]` → `[0.2.0]` entry in catalogue-curation changelog (or pack README if no separate changelog).
- Run `agentbundle catalogue self-host --root . --write` to regenerate all projections.
- Run `SKIP_SAST=1 make build-check` (or equivalent test suite).
- Lint spec status.

---

## Phase 2 — Deferred ACs (0.26.0)

### T11 — SelfHostedSource dataclass + credential validation (B3, B12)
**Depends on:** none
**Verification:** TDD

Tests:
- `resolve_source()` returns error when source directory is missing.
- `resolve_source()` returns error for vendored mode when `packages/agentbundle/` is absent.
- `SelfHostedSource` dataclass fields accessible (name, display_name, release, archive_uri, sha256, revision).
- `validate_fields()` refuses `archive_uri` with embedded credentials (`user:pass@host`).
- `validate_fields()` accepts clean `archive_uri`.

Approach:
- Add `SelfHostedSource` dataclass with fields: `name`, `display_name`, `release`, `archive_uri: str | None`, `sha256: str | None`, `revision: str | None`.
- Add `resolve_source(source, tooling)` → returns `(SelfHostedSource | None, str | None)`. For vendored mode, check `packages/agentbundle/` is present; if absent, return error.
- Extend `validate_fields()` to apply `_URL_USERINFO_RE` to `cfg.archive_uri` (new optional field on `SelfHostedInitConfig`).

### T12 — Source manifest: include in tar + packs/policy fields (B4)
**Depends on:** none
**Verification:** TDD

Tests:
- `package_source_flavour()` — archive member list includes `self-hosted-source-manifest.json`.
- Manifest (extracted from archive) contains `packs` list with `{name, version}` entries.
- Manifest contains `archive_generation_policy_version: "1"`.
- `export-catalogue` absent from source archive members.

Approach:
- In `package_source_flavour()`, build the manifest dict before tar construction.
- Add `packs` field: enumerate `packs/<name>/pack.toml` in collected files, extract `{name, version}`.
- Add `archive_generation_policy_version: "1"`.
- Include serialized manifest bytes as a tar member at `self-hosted-source-manifest.json`.
- Sidecar manifest on disk is written from the same bytes (no drift).

### T13 — Source archive install refusal + verify refusal (B4)
**Depends on:** T12 (manifest must be in tar for detection signal)
**Verification:** TDD

Tests:
- `agentbundle install` with extracted source archive dir fails with "agentbundle-self-hosted-source" in stderr/diagnostic.
- `verify_archive()` returns error with "agentbundle-self-hosted-source" when archive contains `self-hosted-source-manifest.json`.

Approach:
- In `install.py`, after the `catalogue_dir` is resolved (both HTTPS and local paths converge at ~line 295), add: if `(catalogue_dir / "self-hosted-source-manifest.json").exists()` → print diagnostic and return 1.
- In `archive.py` `verify_archive()`, at the top of archive member scanning: if `self-hosted-source-manifest.json` is a member → return error result.

### T14 — Reuse conflict classifier + atomic commit primitives (B5)
**Depends on:** none
**Verification:** TDD

Tests:
- CONFLICT detected when a non-owned file already exists with different content.
- No CONFLICT when a file in old ownership state already exists with different content (owned-path overwrite).
- Files written using `atomic_write` (`.abtmp` temp → rename).

Approach:
- Promote private symbols in `initialise.py`: add public aliases `atomic_write`, `commit_files`, `rollback` (thin wrappers or renames, keeping `_`-prefixed originals as deprecated aliases).
- In `init_self_hosted()`: collect all file content as `{rel_path: bytes}` in memory; apply identity transform on bytes before any write; read old ownership state; build `PlannedFile` list; split into owned/new; call `classify_conflicts` on new-only; abort on CONFLICT; write all using `atomic_write` from `initialise.py`; use `rollback` from `initialise.py` on failure.

### T15 — Vendored [catalogue.tooling] section (B6, B8)
**Depends on:** none
**Verification:** TDD

Tests:
- `_generate_catalogue_toml()` with `tooling="vendored"` includes `[catalogue.tooling]` section.
- `pack-roots` = `[".agentbundle/tooling/packs"]`.
- `self-host-packs` = `["catalogue-curation"]`.
- `adapters` = `["claude-code"]` when not specified; matches `cfg.adapters` when specified.
- After vendored `init_self_hosted()`, `catalogue.toml` is parseable as valid TOML with `[catalogue.tooling]`.

Approach:
- Modify `_generate_catalogue_toml(cfg)` to append `[catalogue.tooling]` block when `cfg.tooling == "vendored"`.
- Adapters list serialized as TOML inline array.

### T16 — Export-catalogue refusal + library-level curation planning (B7)
**Depends on:** none
**Verification:** TDD

Tests:
- `init_self_hosted()` returns error when source has `packs/catalogue-curation/.apm/skills/export-catalogue/`.
- External mode `next_steps` contains structured install command with `agentbundle install catalogue-curation`.
- External mode `next_steps` has one command per adapter in `cfg.adapters` (or default).

Approach:
- At the start of `init_self_hosted()`, after reading source meta: check `source / "packs/catalogue-curation/.apm/skills/export-catalogue/"` exists → return failure with diagnostic "source contains outdated catalogue-curation with export-catalogue — update source to 0.2.0 or later".
- Replace the single-string next_step for external mode with per-adapter structured commands: `agentbundle install catalogue-curation --scope repo --adapter <adapter>` for each adapter.

### T17 — Enriched SelfHostOwnershipState + removal logic with guards (B9)
**Depends on:** none
**Verification:** TDD

Tests:
- After init, state file has `schema_version: "2"`.
- `managed_paths` is list of `{path, sha256}` dicts.
- Re-run removes stale paths (in old state, not in new plan).
- Re-run does NOT remove stale paths whose on-disk sha256 differs from recorded (user-edited); emits warning in diagnostics.
- Re-run does NOT remove paths with sha256=None (migrated from schema-1).
- Path confinement: a crafted state entry with `../escape` does not escape target on removal.
- Externally installed `.claude/skills/some-skill/SKILL.md` survives self-hosting.

Approach:
- Bump `SelfHostOwnershipState.schema_version` to `"2"`.
- Add fields: `adapters: list[str]`, `managed_target_path: str`, `source_pack_identity: str`, `source_root_kind: str`.
- Change `managed_paths` type to `list[dict]` with `{path: str, sha256: str | None}`.
- `to_dict()` serializes new schema.
- `_load_ownership_state(target)` → reads existing state; migrates schema-1 (list[str]) to list[dict] with sha256=None.
- Before writing new files: load old state → compute stale = old paths not in new plan → for each stale entry: (a) validate path resolves within target (skip if not), (b) compare on-disk sha256 to recorded (skip-and-warn if mismatch or recorded sha256 is None), (c) unlink.
- Write new state with sha256 for each managed file.

### T18 — JSON output field completeness (B12)
**Depends on:** T11 (SelfHostedSource), T15 (tooling_mode), T16, T17
**Verification:** TDD

Tests:
- `result.to_dict()` includes `preset`, `tooling_mode`, `attribution_mode`.
- `result.to_dict()` includes `selected_packs`, `selected_profiles`, `selected_adapters`.
- `result.to_dict()` includes `field_collection_mode`, `identity_replacements` (list of {from, to}).
- `result.to_dict()` includes `leak_scan_result` with ok/violations count.

Approach:
- Add fields to `SelfHostedInitResult`: `preset`, `tooling_mode`, `attribution_mode`, `selected_packs`, `selected_profiles`, `selected_adapters`, `field_collection_mode`, `identity_replacements`, `leak_scan_result`.
- Update `to_dict()` to include all new fields.
- Populate from `init_self_hosted()`.

### T19 — Version bump, CHANGELOG, spec check-off (Phase 2 gates)
**Depends on:** T11–T18 all passing
**Verification:** Goal-based — `SKIP_SAST=1 make build-check` green; all deferred ACs checked off in spec.

Approach:
- Bump `packages/agentbundle/pyproject.toml` version to `0.26.0`.
- Update `CHANGELOG.md` `[Unreleased]` → `[0.26.0]` with Phase 2 changes summary.
- Check off all `(deferred: catalogue-init-sh-phase2)` ACs in spec.md.
- Run `SKIP_SAST=1 make build-check`.
- Run full pytest suite.
