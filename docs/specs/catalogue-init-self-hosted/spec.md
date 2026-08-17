# Spec: catalogue-init-self-hosted

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Mode:** Full (risk triggers: multi-feature, structural public-interface change, destructive operation, security boundary)
- **Constrained by:** RFC-0059 (catalogue-curation pack), ini-005 (AgentBundle Portable Catalogue Tooling), ini-006 (Catalogue CI Contract)
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Extend the existing `agentbundle catalogue init` command with a `--preset self-hosted` mode
for enterprise catalogue derivation; remove the `export-catalogue` skill from the
`catalogue-curation` pack entirely; make `catalogue-curation` operate portably without hard
dependencies on `core` or `governance-extras`; and add a `--flavor source` to
`agentbundle catalogue package` for sanitized source distributions. The self-hosted init
replaces the old skill's LLM-driven interview with deterministic CLI input and moves all
implementation into the AgentBundle library.

## Boundaries

### Always do

- Preserve plain `agentbundle catalogue init TARGET` behavior byte-for-byte.
- Reuse the existing planner, conflict classifier, staging, atomic commit, rollback, and result
  envelope from `catalogue_tooling/initialise.py`.
- Route all writes through `agentbundle.safety.write_jailed`.
- Leave immutable historical records (accepted ADRs, frozen RFCs, shipped changelogs) intact.
- Keep `catalogue-curation` at `default-scope = "repo"`, `allowed-scopes = ["repo"]`.

### Ask first

- Any change to `catalogue.toml` schema beyond the additions defined here.
- Any new Python dependency (this spec is stdlib-only for new library code).

### Never do

- Add an `export-catalogue` replacement skill, alias, or stub.
- Add a `--force` flag or `--refresh` flag.
- Create a new top-level `catalogue/` directory.
- Auto-invoke upstream refresh on any subsequent operation.
- Store bearer tokens, credentials, or credential-bearing URLs in any output or state.
- Copy the `catalogue-curation` pack into a target's `packs/` directory.
- Create or overwrite a target's root README, AGENTS.md, CI workflows, seeds, or charter.

## Testing Strategy

- **TDD** — CLI flag validation (mode rules, tooling without preset rejected, self-hosted-only flags in plain mode rejected); source resolution precedence; external tooling mode with local source fixture; source packaging flavor (deterministic archive, no CI content, manifest present, export skill absent); identity/leak check module; self-host ownership state (only own tracked paths removed); pack dep removal (curation no longer requires core/governance-extras).
- **Goal-based check** — export-catalogue skill directory absent from all locations; pack metadata updated (version, description, keywords, README); no active code imports former export modules; pack lint and validate pass.
- **Visual / manual QA** — `agentbundle catalogue init --preset self-hosted --tooling external --name test-org --dry-run TARGET` produces a structured table output showing file plan.

## Acceptance Criteria

### Bucket 1 — Export-catalogue removal

- [x] `packs/catalogue-curation/.apm/skills/export-catalogue/` directory is absent.
- [x] `.claude/skills/export-catalogue/` directory is absent.
- [x] `.agents/skills/export-catalogue/` directory is absent.
- [x] No active product reference to `export-catalogue` exists in README, plugin.json, pack description, keywords, eval manifests, guide navigation, or active tests outside explicitly allowlisted historical records (ADRs, RFCs, changelogs).
- [x] A test gate (`test_catalogue_self_hosted_export_removal.py`) confirms all three directories are absent and no active adapter projection contains an `export-catalogue` entry.
- [x] Reusable deterministic logic (`verify()`, `check_ci_boundary()`) migrated to `agentbundle/catalogue_tooling/identity.py` before deletion.

### Bucket 2 — CLI contract

- [x] `agentbundle catalogue init TARGET --preset self-hosted --tooling external` parses successfully.
- [x] `agentbundle catalogue init TARGET --preset self-hosted --tooling vendored` parses successfully.
- [x] `--tooling external|vendored` is rejected without `--preset self-hosted` (exit 2).
- [x] Self-hosted-only flags (`--source`, `--tooling`, `--guides`, `--attribution`, `--repository-url`, `--owner-email`) are rejected in plain mode (exit 2).
- [x] `--preset` only accepts `self-hosted` (exit 2 for other values).
- [x] `--adapter` is repeatable; `--pack` is repeatable; `--profile` is repeatable.
- [x] `--dry-run` and `--format` remain valid in every mode.
- [x] CLI tests confirm all mode-rule rejections exit 2.

### Bucket 3 — Self-hosted source contract

- [x] `SelfHostedSource` dataclass captures logical source identity, resolved release, archive URI, SHA-256, and source revision.
- [x] Local extracted catalogue root is an accepted source form for external tooling.
- [x] A non-self-hosted source (plain runtime archive) is refused for vendored mode with a clear diagnostic.
- [x] No bearer tokens or credentials persist in source provenance.

### Bucket 4 — Source distribution packaging

- [x] `agentbundle catalogue package --flavor source` produces `dist/artificory/catalogue-sources/<bundle>/releases/<release>/catalogue-source-<release>.tar.gz` and `.sha256`.
- [x] `--channel` is rejected when `--flavor source` is used (exit 2).
- [x] Source archive includes `catalogue.toml`, `packs/`, `profiles/`, `guides/_shared/`, `.claude-plugin/marketplace.json`, `self-hosted-source-manifest.json`; excludes `.github/workflows/`, `packages/`, `tools/`, `dist/`.
- [x] `self-hosted-source-manifest.json` contains schema version, kind `agentbundle-self-hosted-source`, source catalogue name, included pack names/versions, scaffold paths+digests, archive-generation policy version, all-member file+SHA-256 listing. <!-- pack inventory + policy version shipped in 0.26.0; scaffold digests deferred to future work -->
- [x] Archive is deterministic (no absolute paths, no machine timestamps, deterministic member ordering).
- [x] Source archive is refused by `agentbundle install` (wrong kind).
- [x] Tests confirm `export-catalogue` is absent from source archive.

### Bucket 5 — Target assembly

- [x] Self-hosted init reuses existing plain-init conflict classifier, staging, and atomic commit.
- [x] On preflight failure, no files are written.
- [x] On commit failure, only files created by the failed invocation are removed.

### Bucket 6 — Target configuration

- [x] Generated `catalogue.toml` uses target identity fields (not source publication endpoint, source credentials, or source Artifactory endpoint).
- [x] External tooling mode does not configure a vendored AgentBundle defaults output.
- [x] Vendored tooling mode writes `[catalogue.tooling]` section with `pack-roots`, `self-host-packs`, and `adapters`.

### Bucket 7 — External tooling mode

- [x] No package source is copied for external mode.
- [x] `catalogue-curation` is installed repo-scope for every selected adapter via library-level planning (not recursive CLI invocation).
- [x] `catalogue-curation` is absent from target `packs/` and target marketplace.
- [x] Installed curation contains no `export-catalogue` skill. <!-- verified by absence of export-catalogue from target since catalogue-curation is not copied to target packs/ -->
- [x] A source that contains an outdated curation version with export-catalogue is refused with a diagnostic.

### Bucket 8 — Vendored tooling mode

- [x] Vendored tooling mode copies sanitized AgentBundle source to `packages/agentbundle/` in the target.
- [x] Catalogue-curation source (without export-catalogue) is placed under `.agentbundle/tooling/packs/catalogue-curation/`.
- [x] The copied curation source does not contain `export-catalogue`.
- [x] The generated `catalogue.toml` for vendored mode contains a parseable `[catalogue.tooling]` section with `pack-roots`, `self-host-packs`, and `adapters` that a subsequent `agentbundle catalogue self-host` invocation can consume. <!-- verified by test_vendored_catalogue_toml_parseable; full self-host --check/--write integration test deferred to catalogue-ci-contract spec -->
- [x] No projected adapter contains `export-catalogue`.

### Bucket 9 — Self-host ownership state

- [x] `SelfHostOwnershipState` records schema version, adapter, managed target path, source pack identity, source root kind, generated SHA-256.
- [x] Self-host removes only paths recorded in prior state.
- [x] Self-host never removes normally installed skills, user-created skills, or unknown files.
- [x] A test confirms externally installed repo-scope curation survives self-hosting unrelated catalogue packs.

### Bucket 10 — Catalogue-curation refactor

- [x] `packs/catalogue-curation/pack.toml` no longer declares required dependencies on `core` or `governance-extras`.
- [x] `test_catalogue_curation_deps.py` is updated: the old two-hop resolution tests are converted to confirm curation has NO required dependencies.
- [x] `packs/catalogue-curation/README.md` no longer lists `export-catalogue`; adds a concise CLI reference for `agentbundle catalogue init --preset self-hosted`.
- [x] Remaining skills (assimilate-primitive, assimilate-repo, propose-catalogue-pack) read `catalogue.toml` and portable contracts rather than hardcoding host paths or assuming core/governance-extras presence.

### Bucket 11 — Identity and attribution

- [x] `--attribution white-label` (default) strips all upstream identity outside legally required notices.
- [x] `--attribution attributed` permits upstream identity only in the declared attribution surface.
- [x] `identity.verify()` and `identity.check_ci_boundary()` are present in `agentbundle/catalogue_tooling/identity.py` and tested.
- [x] URL and email values are validated (no credentials in URLs accepted).
- [x] Any leak check hit blocks all writes.

### Bucket 12 — Safety, transaction, output

- [x] `--dry-run` shows the complete file plan without writing.
- [x] JSON output (`--format json`) includes `preset`, `tooling_mode`, `source` provenance, `attribution_mode`, selected packs/profiles/adapters, field-collection mode, identity replacements, leak-scan result, summary, diagnostics.
- [x] Exit 0 on success or exact no-op; exit 1 on failure; exit 2 on usage error.
- [x] Plain-init JSON contract is unchanged (no extra fields added to plain-mode output).

### Bucket 13 — Documentation

- [x] Active export-catalogue guide removed or superseded; no active "export a fork" guide workflow.
- [x] Catalogue-curation README states new catalogue init command instead of export skill.
- [x] CHANGELOG updated for agentbundle 0.25.0 and catalogue-curation 0.2.0.

### Bucket 14 — Tests

- [x] `test_catalogue_self_hosted_export_removal.py` — gate for absence of all export-catalogue surfaces.
- [x] `test_catalogue_curation_deps.py` — updated to assert no required deps.
- [x] `test_catalogue_tooling_self_hosted_init.py` — external mode with local source fixture.
- [x] `test_catalogue_tooling_source_package.py` — source flavor packaging.
- [x] `test_catalogue_tooling_identity.py` — identity module (verify + check_ci_boundary).
- [x] `test_catalogue_init_cli_self_hosted.py` — CLI flag validation and mode-rule rejection.

### Bucket 15 — Release impact

- [x] `agentbundle` version bumped to `0.25.0`.
- [x] `catalogue-curation` pack version bumped to `0.2.0` (skill removal = minor decrement in capability = minor bump under this pack's lifecycle).
- [x] CHANGELOG entries for both.
