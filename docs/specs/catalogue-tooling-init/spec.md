---
slug: catalogue-tooling-init
title: "agentbundle catalogue init — plain catalogue initialization"
status: Shipped
---

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->

**Mode:** full (multi-feature + dependent tasks, structural/public-interface change, security boundary: file I/O + path traversal)

**Objective.** Ship `agentbundle catalogue init [TARGET]` — a noninteractive command that creates a new, blank, author-ready AgentBundle catalogue in `TARGET` by materializing the bundled authoring scaffold, generating a valid `catalogue.toml`, and generating a valid empty marketplace. It is safe for existing repositories, exact re-execution is a no-op, any conflict blocks every write, and the result passes portable catalogue verification.

**Files touched.** `catalogue.schema.json`, `config.py`, `results.py`, `defaults.py`, new `catalogue_tooling/initialise.py`, `catalogue_tooling/toml_emit.py` (new), new `commands/catalogue_init.py`, `cli.py`, `sync_authoring_scaffold.py`, `guides/_shared/reference/catalogue-ci-contract.md` (link fix), new `guides/_shared/how-to/create-a-catalogue.md`, `pyproject.toml` (version bump), plus test files. `scaffold.py` extended with path-safety validation. `verify.py` step 16 already guards for falsy install_defaults_output — no change needed.

**Not changing.** The `scaffold.py` public API (`materialize_to` etc.), `build/main.py`, the existing packs/profiles AGENTS.md contents, `contracts/`, `lint.py`, `archive.py`, `package.py`, `self_host.py`, the six existing catalogue subcommands.

**Declined temptations.** `--force` flag (overwrite existing files — not in spec). `--preset` (future phase). Interactive prompts (noninteractive is the contract). A standalone scaffold verification command. Reusing `materialize_to()` directly (it overwrites silently; init needs conflict-aware materialization). Changing `build/main.py` to add name/owner to zero-pack marketplace (out of scope).

---

## Acceptance Criteria

### Bucket 1 — CLI surface

- [x] `agentbundle catalogue init [TARGET]` exists, `TARGET` defaults to `.`, is optional and positional.
- [x] Flags: `--name NAME`, `--display-name TEXT`, `--description TEXT`, `--owner-name TEXT`, `--preferred-adapter ADAPTER`, `--dry-run`, `--format {table,json}`.
- [x] No `--bare`, `--preset`, `--tooling`, `--force`, `--yes`, CI provider flags, Artifactory flags, root-README flags, or starter-pack flags exist.
- [x] `agentbundle catalogue --help` exits 0 and shows implemented commands (not `_StubHelpAction` exit-1 behavior).
- [x] `catalogue init` appears in catalogue group help output.
- [x] Usage errors exit 2.

### Bucket 1.1 — Metadata defaults

- [x] `--name`: explicit → use; absent → lower-kebab-case from target basename; no safe name derivable → fail with diagnostic requiring `--name`.
- [x] `--display-name`: explicit → use; absent → humanize catalogue name.
- [x] `--description`: explicit → use; absent → `"<DisplayName> AgentBundle catalogue."`.
- [x] `--owner-name`: explicit → use; absent → use display name.
- [x] `--preferred-adapter`: explicit → validated against bundled adapter contract before any write; absent → bundled package default → agentbundle built-in default.
- [x] `minimum-agentbundle-version`: running agentbundle version; not a public flag.
- [x] No adapter default inferred from installed pack state or random target files.

### Bucket 2 — Generated layout

- [x] The following files are created (exact scaffold paths from bundled data):
  - `catalogue.toml`
  - `packs/README.md`, `packs/AGENTS.md`
  - `packs/_example/README.md`, `packs/_example/pack.toml`, `packs/_example/.claude-plugin/plugin.json`, `packs/_example/.apm/skills/example-skill/SKILL.md`, `packs/_example/evals/eval_queries.json`
  - `profiles/README.md`, `profiles/AGENTS.md`
  - `profiles/_example/README.md`, `profiles/_example/profile.toml`
  - `guides/_shared/reference/catalogue-ci-contract.md`
  - `.claude-plugin/marketplace.json`
- [x] Root README is never created or modified.
- [x] No CI workflow, site rendering, AgentBundle source, CredBroker source, or catalogue-curation content is created.
- [x] After init, `agentbundle list-packs TARGET` exits 0 with zero packs.
- [x] After init, `agentbundle list-profiles TARGET` exits 0 with zero profiles.
- [x] Reserved `_example` directories remain excluded from pack/profile discovery.

### Bucket 3 — Scaffold loader

- [x] Scaffold is loaded via `importlib.resources` (works from editable, wheel, sdist, zipapp).
- [x] Loader validates manifest schema/version.
- [x] `scaffold.py` extended with `validate_manifest_paths(manifest)` that rejects: absolute paths, `..` traversal, duplicate paths, case-insensitive collisions, unsafe Windows-reserved names.
- [x] SHA-256 is verified for every bundled file before use.
- [x] Missing manifest files detected; unexpected packaged files detected (files in scaffold dir not in manifest).
- [x] File bytes returned without writing to uncontrolled temporary location.
- [x] Deterministic path ordering.
- [x] Scaffold never executed.

### Bucket 3.1 — CI contract in scaffold

- [x] `guides/_shared/reference/catalogue-ci-contract.md` is present in `_data/catalogue-scaffold/` (added to `sync_authoring_scaffold.py` `_SYNC_PAIRS`).
- [x] `sync_authoring_scaffold.py --write` regenerates manifest with the new entry.
- [x] `sync_authoring_scaffold.py --check` exits 0 after `--write`.
- [x] Relative links in the CI contract guide that would break in standalone context are replaced with self-contained wording.
- [x] The central site's ability to render the source guide is preserved.

### Bucket 4 — Schema relaxation (backward compatible)

- [x] `catalogue.paths.contracts` is optional in schema v1 (removed from `required`).
- [x] `distribution.agentbundle.install-defaults-output` is optional in schema v1.
- [x] `distribution.agentbundle.default-source` is optional in schema v1.
- [x] Existing `catalogue.toml` files that set all three fields continue to validate.
- [x] Optional fields typed `str | None` in dataclasses, defaulting to `None`. Empty string `""` is not a valid absent state — schema enforces this by omitting the fields entirely.
- [x] When `contracts` is absent (None), config loading skips path validation for contracts.
- [x] When `install-defaults-output` is absent (None), `verify.py` step 16 already short-circuits with `if not output_path: return []` — no change needed to verify.py. `catalogue sync-defaults --check` / `--write` must also short-circuit with ok=True when output path is None.
- [x] When `default-source` is absent (None/empty), `_validate_source()` is skipped.
- [x] `distribution.agentbundle.preferred-adapter` remains required and validated.
- [x] `distribution.agentbundle.artifactory` remains required (with `enabled = false` legal without other fields).

### Bucket 4.6 — Owner metadata

- [x] `catalogue.owner` table is optional in schema; when present, `name` is required.
- [x] `CatalogueOwner(name: str)` dataclass added.
- [x] `CatalogueConfig.owner: CatalogueOwner | None` added.
- [x] Init writes `[catalogue.owner]\nname = "..."` using `--owner-name` or derived default.
- [x] Existing catalogue files without owner metadata remain valid.
- [x] Nonempty marketplace generation is backward-compatible (no owner field assumed to exist).

### Bucket 5 — Generated `catalogue.toml`

- [x] Generated TOML is valid under the updated schema and business rules.
- [x] Deterministic key and section ordering, UTF-8, LF newlines, final newline.
- [x] Safe string escaping (no raw user input in TOML without escaping).
- [x] No timestamp, no absolute source-machine path, no placeholder remote URL, no credentials, no host identity.
- [x] `install-defaults-output` absent.
- [x] `default-source` absent.
- [x] `[distribution.agentbundle.artifactory]\nenabled = false` present; no empty URL fields.
- [x] `include = []` present (meaning include all real packs; `_example` remains excluded by the reserved-prefix convention).

### Bucket 6 — Empty marketplace

The init-generated `.claude-plugin/marketplace.json` is the *source* marketplace for Claude plugin discovery. The build-generated marketplace at `dist/.../marketplace.json` is a separate artifact derived from packs; `build/main.py` is not changed. These are distinct paths and purposes; byte-identity between them is not required.

- [x] `.claude-plugin/marketplace.json` generated via shared pure function in `initialise.py` (not a separate handwritten file for init only).
- [x] Shape: `{"name": "...", "description": "...", "owner": {"name": "..."}, "plugins": []}`.
- [x] JSON is deterministic, UTF-8, final newline per repository conventions.
- [x] No invented repository URL, GitHub source, branch, or host owner.
- [x] `plugins: []` is valid under the verification pipeline (verify step 12 checks JSON parseability of the build-output marketplace, not the source `.claude-plugin/marketplace.json`).
- [x] The zero-pack build (called during staging verify, step 10) generates a minimal `{"plugins": []}` in the build output; this is a separate artifact from init's `.claude-plugin/marketplace.json`.

### Bucket 7 — Safety, idempotence, rollback

- [x] Init sequence: resolve metadata → verify scaffold → generate config+marketplace → build plan → detect conflicts → stage+verify → commit atomically → verify target → rollback newly created files on failure.
- [x] Nonexistent target: created automatically.
- [x] Existing target (dir): allowed with conflict detection.
- [x] Target is ordinary file: refused.
- [x] Unsafe/symlinked target: refused.
- [x] Path escaping target: refused.
- [x] Case-insensitive planned-path collisions: refused.
- [x] Conflict classification: `create` | `already-present` | `conflict`.
- [x] `already-present`: existing file is byte-identical to planned content.
- [x] `conflict`: file differs, wrong type, symlink, or parent incompatible.
- [x] A single conflict blocks every write.
- [x] Conflict diagnostic: target-relative path, existing type, intended type, remediation.
- [x] Idempotence: exact re-run exits 0, writes no files, all files reported as `already-present`, verification reruns.
- [x] Changed metadata flags against existing init output → conflict on `catalogue.toml` (different content).
- [x] Staging: full catalogue built in tmpdir, `verify_catalogue()` called via direct library call (not subprocess).
- [x] Commit: atomic file placement; race-condition recheck before each placement.
- [x] Rollback: removes only *files* created by this invocation; never touches preexisting files.
- [x] Directory rollback: directories newly created by this invocation (including the target dir when it did not previously exist, and intermediate directories like `packs/_example/.claude-plugin/`) are removed bottom-up on rollback. Pre-existing directories are never removed.
- [x] No staging or temp files left on failure.
- [x] No network requests in any code path.
- [x] No subprocess calls.

### Bucket 8 — Dry-run and output

- [x] `--dry-run`: verifies scaffold, resolves metadata, generates content, classifies actions, detects conflicts, writes nothing, creates no target directory.
- [x] Conflict dry-run exits 1; clean dry-run exits 0.
- [x] Human output (default): target, catalogue identity, owner, preferred adapter, min version, planned files, counts, verification status, dry-run indicator.
- [x] JSON output: one document to stdout matching the specified shape; `schema_version`, `command`, `operation`, `agentbundle_version`, `catalogue_schema_version`, `ok`, `dry_run`, `target`, `catalogue`, `files`, `verification`, `summary`, `diagnostics`. Includes `agentbundle_version` and `catalogue_schema_version` for parity with all other `CommandResult`-based commands.
- [x] Exit codes: 0 (success / no-op / clean dry-run), 1 (conflict / scaffold failure / verification failure), 2 (CLI usage error).

### Bucket 9 — Implementation structure

- [x] `catalogue_tooling/initialise.py` — init engine (metadata resolution, scaffold loading, TOML+marketplace generation, plan, conflict detection, staging, apply, rollback).
- [x] `commands/catalogue_init.py` — CLI handler (`run(args) -> int`), table+JSON rendering.
- [x] No business logic in `cli.py`.
- [x] No `subprocess`, no recursive AgentBundle invocation, no git shell-out.
- [x] No third-party runtime dependency added.
- [x] Python 3.11 stdlib-only runtime.

### Bucket 10 — Dogfooding test

- [x] Integration test creates a tmpdir, calls init library, verifies output, checks no host files leaked.
- [x] Does not run init against the repository root.
- [x] Proves: scaffold and package-data synchronized; no host packs, profiles, owner, Artifactory config, CI workflow, or AgentBundle source copied; generated catalogue passes verifier.

### Bucket 11 — Tests (see Testing Strategy below)

### Bucket 12 — Documentation

- [x] CLI reference updated for `catalogue init`.
- [x] `guides/_shared/how-to/create-a-catalogue.md` created.
- [x] Scaffold `packs/README.md` and `profiles/README.md` reference `catalogue init`.
- [x] Catalogue format reference updated for optional fields and owner metadata.

### Bucket 13 — Release impact

- [x] `pyproject.toml` version bumped (new public command, schema change → minor bump).
- [x] `version.py` `CLI_VERSION` bumped to match.
- [x] `[Unreleased]` changelog entry added.

---

## Testing Strategy

**Unit tests** (`packages/agentbundle/tests/unit/`):
- CLI: init appears in help, catalogue `--help` exits 0, default target=`.`, explicit target, flags, invalid name, invalid adapter, unknown flag, usage exit 2, path normalization.
- Metadata resolution: all precedence levels, safe name derivation edge cases, invalid basename.
- Scaffold loader: manifest load/validate, SHA-256 verify, missing file detection, unsafe path rejection.
- TOML emitter: safe escaping, special chars, determinism.
- Marketplace generator: shape, determinism, no invented URLs.
- Conflict detection: create/already-present/conflict classification for each case.
- Configuration: optional contracts, optional install-defaults-output, optional default-source, owner present/absent, legacy catalogue unchanged, sync-defaults no-op when unconfigured.

**Integration tests** (`packages/agentbundle/tests/integration/`):
- New target: expected files exist, no extras, no root README, zero real packs, zero real profiles, examples reserved, valid config, verify passes, list-packs/profiles exit 0.
- Existing repository: unrelated files unchanged, root README unchanged, no CI files, verify passes.
- Idempotence: second run exits 0, no rewrites, already-present summary, verify reruns.
- Conflict tests: conflicting catalogue.toml, packs/README.md, symlink, wrong-type; each exits 1, zero writes.
- Rollback: injected failure at staging/commit; only init-created files removed, pre-existing files intact.
- Dry-run: no directory created, full plan returned, conflicts reported, exits 0/1 correctly, JSON parses.
- No-network: HTTP/remote resolver not called.
- JSON output: `json.loads` coverage.
- Dogfooding: blank catalogue passes verifier, no host files leaked.

**Verification mode:** manual QA — the real built artifact (`agentbundle catalogue init`) is exercised end-to-end through its documented happy path; observed stdout/exit code recorded.

---

## Assumptions

1. `agentbundle.scaffold.scaffold_root()` works from editable install and wheel — confirmed by existing code.
2. `verify_catalogue()` can be called on a staging tmpdir without side effects — confirmed by verify.py step 10 pattern.
3. The `default` build recipe succeeds on a zero-pack catalogue — confirmed by code inspection: `build/main.py` processes whatever packs it finds in `packs/`; with zero real packs (only `_example/` which is skipped at line 366), `_run_aggregate` produces `{"plugins": []}` with no name/owner. The build exits 0. The resulting marketplace is JSON-parseable; verify step 12 only checks parseability.
4. `list-packs` skips `_` prefix directories per the reserved-prefix convention (build/main.py line 366). `list-profiles` skips `_example/profile.toml` because the glob pattern is top-level `profiles/*.toml` — nested files under `profiles/_example/` don't match. The outcome (zero profiles) is guaranteed by the glob scope, not an explicit `_` filter.
5. Schema version 1 relaxation is backward-compatible by definition (removing required constraints can only permit more, not less).
