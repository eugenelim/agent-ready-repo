# agentbundle changelog

All notable changes to the `agentbundle` Python package.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the package targets pre-1.0 semver as documented in `docs/CONVENTIONS.md`
— a minor bump on a 0.x release MAY be breaking.

## [Unreleased]

## [0.29.1]

### Fixed

- **`workspace_mcp._GitTools` — FSM mode guard**: `git_branch`, `git_commit`, and
  `git_push` are now blocked whenever `WORKSPACE_MCP_SPEC_PATH` is supplied —
  including when `WORKSPACE_MCP_DISPATCHED_ITEM` is also present (both-vars
  configuration, unsupported; SPEC_PATH wins with a startup warning), and when
  the path fails `repo_root` containment validation (fail-closed: raw env var
  presence in `os.environ` — including an empty string — is the FSM trigger, not
  the post-validation value). Previously, a stale harness supplying both vars, or
  an invalid SPEC_PATH, left `_fsm_mode=False`, enabling git writes during a
  work-loop session. A new `_fsm_mode` flag drives the guard.

- **`workspace_mcp._build_tools_list`** — refined git tool descriptions for
  harness clarity. `git_status`, `git_branch`, `git_commit`, and `git_push` open
  with "Use this instead of running 'git X' directly" and name the specific bypass
  risk each guard prevents. `git_commit` description states that pre-staged files
  outside the output paths cause a hard refusal; unstaged files are silently
  excluded. `git_push` description clarifies that a resumed dispatched session may
  inherit a pre-locked branch (no `git_branch()` call required). `git_branch`
  example updated to a non-FSM type (`shape`); added note that the tool is
  unavailable in FSM/work-loop sessions.

- **`workspace_status` tool description**: added `available`, `required_pack`, and
  `unmet_needs` eligibility fields so agents know not to dispatch items where
  `available: false` or `unmet_needs` is non-empty.

- **`README-pypi.md`**: marked `python3 -m agentbundle.workspace_mcp` as
  trusted-checkout-only; noted Stage 2 isolated spawn mode (`python3 -I -m ...`).

## [0.28.1]

### Fixed

- **`workspace_mcp._build_tools_list`**: rewrote all six tool descriptions and added
  `description` fields to every parameter schema — descriptions previously used
  internal jargon ("DAG-resolved", "FSM state", "control plane", "output_pattern",
  "session-bound") with no parameter docs; now self-contained for harness authors
  who have not read the design doc. `workspace_status` description names every
  response field. `elicit` documents all three parameters and the return shape.
  `git_branch`, `git_commit`, and `git_push` document constraints (once-per-session,
  discovery-mode unavailability, work-loop ownership) inline.

## [0.28.0]

Engine-Change-RFC: RFC-0078

### Added

- **`agentbundle.workspace_mcp`**: new per-session MCP server (Stage 1, RFC-0078).
  Provides `workspace_status`, `elicit`, `git_status`, `git_branch`, `git_commit`,
  and `git_push` tools over MCP stdio. Entry point: `python3 -m agentbundle.workspace_mcp`.
  - `_LIFECYCLE_MANIFEST`: embedded 7-type lifecycle metadata (`work`, `research`, `shape`,
    `design`, `strategy`, `signal`, `brief`) with dispatch skill, output pattern, gate flag,
    and required pack per type.
  - `DEFAULT_SESSION_INSTRUCTION`: 6-rule session instruction constant readable at
    `agentbundle.workspace_mcp.DEFAULT_SESSION_INSTRUCTION`.
  - `_EventBridge`: daemon thread; 200 ms poll of `.loop-run/events.jsonl`; byte-offset +
    inode tracking; seq deduplication; HUMAN-GATE state detection.
  - `_WorkspaceStatusTool`: calls `analyze_bounded(autonomous_dispatch=True)`; pack-presence
    filter (6 roots); slug safety guard (`_SAFE_SLUG_RE`); FSM state fields merged from
    `_EventBridge` (spike (c) poll-based fallback).
  - `_ElicitTool`: `elicitation/create` path + response-file fallback (O_EXCL 0600, 300 s
    poll); never advertises `elicitation` in `ServerCapabilities`.
  - `_GitTools`: `git_branch` (check-ref-format); `git_commit` (output_pattern intersection;
    `--` separator); `git_push` (two-sided branch check); discovery-mode guard.
  - 1 MiB frame-size cap; malformed JSON and unknown request_id discarded without
    dropping the connection.

- **`workspace_status_engine.analyze_bounded`**: `autonomous_dispatch: bool = False` parameter
  propagated through `classify_entries` → `is_need_satisfied`. When `True`, `shape:` absent
  from both active and backlog is unsatisfied; `research:` absent from backlog as type
  `"research"` is unsatisfied. Default `False` preserves existing human-session semantics.

- **`loop-engine` events.jsonl outbox protocol**: `cmd_init` creates `.loop-run/` + empty
  `events.jsonl` + `.gitignore` entry; `cmd_transition` writes `events.pending` → atomically
  writes `engine-state.json` → appends `events.jsonl` → deletes pending (graceful degradation).
  `_recover_pending()` replays or discards stale `events.pending` at init and transition.

- **Core-pack alias script**: `workspace_mcp_server.py` one-line delegation in
  `packs/core/.apm/skills/workspace-status/scripts/` projected to `.agents/` and `.claude/`.

### Fixed (post-review)

- **`_WorkspaceStatusTool`**: `entry.path` (format `"spec/<slug>"`) changed to `entry.slug`
  in ready/blocked work-queue slug check — prevents all work items being silently dropped
  because `_SAFE_SLUG_RE` rejects the `/` in the path prefix.
- **`_ElicitTool._call_via_elicitation`**: removed redundant `with self._write_lock:` wrapper
  (deadlock — `_write` acquires the same non-reentrant lock internally; CWE-833).
- **`_ElicitTool._call_via_elicitation`**: bounded `_ELICIT_POLL_TIMEOUT` (300 s) wait
  prevents a client that never responds from holding the thread indefinitely.
- **`_GitTools`**: added `self._git_lock = threading.Lock()` to serialize all mutating git
  calls; prevents `index.lock` collisions and TOCTOU races on `_session_branch`.
- **`_GitTools._resolve_output_pattern`**: `ini_slug` and `slug` from
  `WORKSPACE_MCP_DISPATCHED_ITEM` validated via `_is_safe_slug` — defense in depth against
  a crafted env var widening the commit output_pattern.
- **`_read_frame`**: frame-size cap now counts encoded UTF-8 bytes (`len(ch.encode("utf-8"))`)
  not characters — 1 MiB multi-byte characters previously undercounted.
- **Stub tests** (`test_workspace_mcp_*.py`, `test_loop_engine_events_jsonl.py`,
  `test_workspace_status_engine_autonomous.py`, `test_adapter_permissions_projection.py`):
  converted from `assert False  # STUB:` to `pytest.skip("STUB: ...")` — stubs are now
  skipped (exit 0) rather than failing. `B011` removed from `pyproject.toml` per-file-ignores.

AC17/AC18 (`permissions.allow` projection) are deferred to
`(deferred: workspace-mcp-permissions-projection-contract)` — a follow-on RFC will add
the adapter contract mode for additive array merging.

## [0.27.3]

### Changed

- **Scaffold sync**: `packs/AGENTS.md` updated to record `tomlkit==0.15.1` as an optional
  dependency of the `workspace-status` skill; `_data/catalogue-scaffold/` projection synced.

## [0.27.2]

### Fixed

- **Self-host orphan sweep deleting externally installed skills** (`build/adapters/claude_code.py`,
  `build/adapters/kiro.py`, `build/adapters/codex.py`): `catalogue self-host --write` (and
  `--force`) now preserves skill directories that are recorded in `.agentbundle-state.toml` —
  i.e. skills installed by `agentbundle install` from an external catalogue. Previously,
  `_sweep_skill_orphans` built its `expected_names` set solely from the packs passed to
  `project_packs`; any skill whose name was not in that set was silently deleted with
  `shutil.rmtree`. The fix reads the repo-root state file and adds every skill-directory name
  it finds there to `expected_names` before the sweep runs. Absent, legacy-schema, or
  malformed state files degrade gracefully to the pre-fix behavior (empty protection set;
  no error). All three adapters (claude_code, kiro, codex) are fixed with the same
  `_installed_skill_names` helper. Also copies `.agentbundle-state.toml` into
  the shadow tree in `_clone_target_subtree` (`build/self_host.py`) so that
  `--check` / dry-run produces consistent results with `--write` (without this,
  the sweep deleted installed skills from the shadow and reported false drift).

## [0.27.1]

### Added

- **workspace-status projection tests** (`build/tests/test_workspace_status_projection.py`):
  - `SourceInvariantTests`: verifies both CLI and engine scripts exist in the pack source.
  - `AdapterProjectionTests`: exercises all shipped adapters via subTest loop; uses rglob
    for adapter-agnostic scripts/ discovery (AC9).
  - `RealTreeProjectionTests`: asserts both scripts present in the self-hosted projection.
  - `EndToEndCLITests`: installed CLI exits 0, emits `schema_version: 1` against real repo.

## [0.26.0]

### Added

- **Self-hosted init — Phase 2 deferred ACs** (`catalogue_tooling/initialise_self_hosted.py`):
  - `SelfHostedSource` dataclass (name, display_name, release, archive_uri, sha256, revision);
    `resolve_source()` validates source for the requested tooling mode.
  - Vendored mode now refuses a source missing `packages/agentbundle/` with a clear
    diagnostic (B3 AC3).
  - Identity transform applied in-memory before writing; leak check runs in a tmpdir
    so no files are written on violation (B5).
  - Reuses `classify_conflicts`, `atomic_write`, `commit_files`, `rollback` from
    `initialise.py`; owned files (from prior run) overwrite without conflict (B5).
  - Vendored mode writes `[catalogue.tooling]` section (pack-roots, self-host-packs,
    adapters) to the generated `catalogue.toml` (B6).
  - Source containing `packs/catalogue-curation/.apm/skills/export-catalogue/` is
    refused with a diagnostic (B7 AC5).
  - External mode `next_steps` emits one `agentbundle install catalogue-curation` command
    per adapter (B7 AC2 — library-level planning, no subprocess).
  - `SelfHostOwnershipState` bumped to schema version 2: per-path sha256, adapter list,
    managed_target_path, source_pack_identity, source_root_kind (B9).
  - Re-run removes stale owned paths with sha256 guard (skip user-modified files) and
    path confinement (B9 AC2/3).
  - `SelfHostedInitResult.to_dict()` extended with preset, tooling_mode, attribution_mode,
    selected_packs, selected_profiles, selected_adapters, field_collection_mode,
    identity_replacements, leak_scan_result (B12).
- **Source manifest in tar** (`catalogue_tooling/package.py`): `self-hosted-source-manifest.json`
  is now included as a tar member (in addition to the sidecar), plus `packs` inventory and
  `archive_generation_policy_version: "1"` fields (B4 AC).
- **Source archive install refusal** (`catalogue_tooling/archive.py`, `commands/install.py`):
  `verify_archive()` and the `agentbundle install` resolution path both refuse archives
  whose members include `self-hosted-source-manifest.json` with a clear "wrong kind"
  diagnostic (B4 AC6 / B4 AC; install path Blocker fix).
- Public aliases `atomic_write`, `commit_files`, `rollback` added to
  `catalogue_tooling/initialise.py` for use by sibling modules.

### Changed

- `SelfHostOwnershipState.schema_version` promoted from `"1"` to `"2"`; migration from
  schema-1 state files is handled transparently (sha256=None entries skipped on removal).
- Vendored mode source validation is now a hard failure (`ok=False`) when
  `packages/agentbundle/` is absent, rather than a soft diagnostic.

## [0.25.0]

### Added

- **`agentbundle catalogue init --preset self-hosted`**: new enterprise-derived
  catalogue initialization. Accepts `--source`, `--tooling external|vendored`,
  `--attribution white-label|attributed`, `--guides none|selected`, `--pack` (repeatable),
  `--adapter` (repeatable), `--profile` (repeatable), `--repository-url`, `--owner-email`.
  Copies selected packs, profiles, and guides from a source catalogue; generates a new
  `catalogue.toml` with target identity; runs a fail-closed leak check using
  `identity.verify()`. Vendored mode copies agentbundle source and catalogue-curation
  into `.agentbundle/tooling/` for air-gapped deployments. Writes
  `.agentbundle/self-host-state.json` to track managed files.
  (`commands/catalogue_init.py`, `catalogue_tooling/initialise_self_hosted.py`,
  `catalogue_tooling/identity.py`)
- **`agentbundle catalogue package --flavor source`**: new source-distribution flavor
  for self-hosted catalogues. Produces a `catalogue-source-<release>.tar.gz` from a
  positive allowlist (catalogue.toml, packs/, profiles/, guides/_shared/,
  .claude-plugin/marketplace.json, legal files). Emits a `self-hosted-source-manifest.json`
  with `kind = agentbundle-self-hosted-source`, per-file SHA-256 digests, and provenance
  fields.
  (`commands/catalogue_package.py`, `catalogue_tooling/package.py`)
- **`catalogue_tooling.identity`**: new module migrated from
  `catalogue-curation/export-catalogue` scripts. Public API:
  `verify(target, anchors, *, mode, attribution_paths)` and
  `check_ci_boundary(target)`. Used by the self-hosted init engine.
  (`catalogue_tooling/identity.py`)

### Changed

- **`catalogue-curation` pack 0.2.0**: removed `export-catalogue` skill (superseded by
  `agentbundle catalogue init --preset self-hosted`). Removed hard dependencies on
  `core` and `governance-extras` — the pack's three skills now operate portably against
  the target catalogue's own contracts.

## [0.24.0]

### Added

- **`agentbundle catalogue init [TARGET]`**: new subcommand that scaffolds a
  plain AgentBundle catalogue directory. Writes `catalogue.toml`, an empty
  `.claude-plugin/marketplace.json`, the full pack/profile authoring scaffold
  (README, AGENTS, `_example/` templates), and the CI contract reference guide.
  Additive and idempotent — never overwrites existing files. Dry-run mode
  (`--dry-run`) shows the plan without touching the filesystem. All flags:
  `--name`, `--display-name`, `--description`, `--owner-name`,
  `--preferred-adapter`, `--dry-run`, `--format`.
  (`cli.py`, `commands/catalogue_init.py`, `catalogue_tooling/initialise.py`,
  `catalogue_tooling/toml_emit.py`)
- **`catalogue.toml` schema v1 relaxations**: `catalogue.paths.contracts`,
  `distribution.agentbundle.install-defaults-output`, and
  `distribution.agentbundle.default-source` are now optional. Catalogues
  without these fields are valid. Existing catalogues that have them are
  unchanged. (`_data/catalogue.schema.json`, `catalogue_tooling/config.py`)
- **`[catalogue.owner]` table**: new optional TOML table with a required `name`
  field. Loaded into `CatalogueConfig.owner` as `CatalogueOwner`. Absent when
  the key is not in `catalogue.toml`. (`catalogue_tooling/config.py`,
  `catalogue_tooling/results.py`)
- **Scaffold path-safety API** (`scaffold.py`): `validate_manifest_paths()`,
  `list_files_with_hashes()`, `verify_hashes_detailed()`, `find_unexpected_files()`
  — extended public API for the init engine.
- **`sync-defaults` no-op guard**: when
  `distribution.agentbundle.install-defaults-output` is absent, `check_defaults()`
  and `write_defaults()` return `ok=True` with an INFO diagnostic instead of
  failing. (`catalogue_tooling/defaults.py`)
- **Catalogue CI contract guide in scaffold**: `guides/_shared/reference/catalogue-ci-contract.md`
  is now included in the bundled scaffold and copied by `catalogue init`.
- **How-to guide**: `guides/_shared/how-to/create-a-catalogue.md`.

### Changed

- **`_build_archive` → `_write_archive`** (`catalogue_tooling/package.py`): the archive builder
  now streams the compressed output directly to the staged file on disk instead of
  materialising the full content in an `io.BytesIO` buffer first. The SHA-256 is then computed
  over the smaller compressed file. All determinism guarantees are preserved (sorted members,
  normalised metadata, zeroed gzip mtime, `GNU_FORMAT`). No change to archive contents, sidecar,
  or channel descriptor.

### Added

- **`agentbundle catalogue self-host --check --windows`**: new `--windows` flag on the `self-host` subcommand. When combined with `--check`, runs the Windows-portability compat suite (`catalogue_tooling/self_host_windows.py`) — bundler build, self-host drift gates, path-sensitive and encoding-sensitive pytest steps — instead of the standard drift-only check. Rejected with exit 2 if used without `--check`. Drives the `build-check-windows` CI job, replacing its 20-step inline YAML. (`cli.py`, `commands/catalogue_self_host.py`, `catalogue_tooling/self_host_windows.py`)
- **`AGENTBUNDLE_CA_BUNDLE` environment variable** (`https_catalogue.py`): when set to a path,
  `_build_opener` loads a custom PEM CA bundle into an `ssl.SSLContext` and passes it to
  `HTTPSHandler`. Raises `CatalogueError` with a clear message if the path does not exist.
  When the variable is absent, behavior is unchanged. Enables HTTPS catalogue sources behind
  a corporate or self-signed CA without modifying the system trust store.
- **Exact provenance fields on `PackState`** (`artifact_uri`, `archive_sha256`, `source_revision`):
  after `agentbundle install` or `agentbundle upgrade` from a `catalogue+https://` or
  `archive+https://` source, `.agentbundle-state.toml` now records the resolved archive URL,
  the verified SHA-256 digest, and the optional `source_revision` from the channel descriptor.
  Operators can correlate any installed pack row to a specific archive artifact for audit or
  incident response. Local-directory installs leave all three fields absent. Existing state
  files that predate this change are read without error; the missing fields default to `None`.
  (`config.py`, `https_catalogue.py`, `commands/install.py`, `commands/upgrade.py`)
- **Provenance exposed in `list-installed --format json`**: the three new fields appear on each
  row as `artifact_uri`, `archive_sha256`, and `source_revision` (null when absent).
  (`commands/list_installed.py`)
- **Documentation: source-resolution chain and env vars** (`guides/_shared/reference/agentbundle.md`):
  added "Catalogue source resolution" section (five-layer table derived from `source_defaults.py`)
  and "Environment variables" section covering `AGENTBUNDLE_HTTP_BEARER_TOKEN`,
  `AGENTBUNDLE_CA_BUNDLE`, `AGENTBUNDLE_NO_REMOTE`, `HTTPS_PROXY`, and `NO_PROXY`.
  Updated `docs/architecture/catalogue.md` to document the five-layer chain with Layer 3
  (Artifactory bootstrap); updated `docs/guides/reference/catalogue-toml.md` to replace the
  stale `[catalogue.packaging]` section with `[catalogue.package]` and add the missing
  `[distribution.agentbundle.artifactory]` section.

## [0.22.1] — 2026-07-28

### Added

- **`channel` field in `catalogue.toml`** (`distribution.agentbundle.artifactory`): the
  `channel` field is now required when `enabled = true`. `load_catalogue_config` validates
  it against the same safe-segment regex used for `repository` and `bundle`, and stores it
  in `ArtifactoryConfig.channel`. `compile_defaults` now emits the actual channel value
  instead of an empty string, so generated `install-defaults.toml` files contain the
  correct channel and Artifactory-sourced installs resolve successfully.
- **`AGENTBUNDLE_NO_REMOTE` environment variable** (`source_defaults.py`): when set to any
  truthy value, `resolve_default_source` skips the Artifactory org bootstrap (Layer 3) and
  editable-install detection (Layer 4), falling through directly to the packaged default
  (Layer 5). Useful for offline and air-gapped deployments.
- **`catalogue.schema.json`**: added `channel` as an optional string property in the
  `artifactory` object block; `additionalProperties: false` now permits the field without
  breaking `enabled = false` configs.

### Fixed

- `compile_defaults` no longer emits `channel = ""` when Artifactory is enabled. The
  previous hardcoded empty value made every Artifactory-enabled install-defaults.toml
  unusable at runtime.

### Changed

- **`agentbundle catalogue package`** now honours `catalogue.package.include`
  and `catalogue.package.required` from `catalogue.toml`. When `include` is
  non-empty, only those pack directories are archived (non-pack dirs such as
  `profiles/`, `contracts/`, and `.claude-plugin/` are always included). When
  `required` is set, it replaces the default `LICENSE-APACHE` / `LICENSE-MIT`
  constraint; absent or empty `required` preserves existing behavior.
  Path-traversal entries in `include` are rejected before any filesystem access.
  (`catalogue_tooling/package.py`, `catalogue_tooling/config.py`,
  `_data/catalogue.schema.json`, `contracts/catalogue.schema.json`)

### Documentation

- **`docs/guides/how-to/enterprise-app-store.md`**: corrected the archive output path
  (`dist/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz`) and the
  channel descriptor path (`channels/<channel>.json`); added a `[distribution.agentbundle.artifactory]`
  configuration example with `channel = "stable"`; added an environment variable reference
  table covering `AGENTBUNDLE_HTTP_BEARER_TOKEN`, `AGENTBUNDLE_NO_REMOTE`, and
  `AGENTBUNDLE_CA_BUNDLE` (upcoming).

## [0.21.1] — 2026-07-28

### Fixed

- **Windows path validation** (`catalogue_tooling/build.py`). `_validate_recipe_path`
  now recognises Unix-style absolute paths (e.g. `/etc/foo.toml`) on Windows, where
  `Path.is_absolute()` returns `False` for drive-relative paths. An explicit
  `startswith("/")` guard rejects them with the correct "absolute" error on all platforms.

## [0.21.0] — 2026-07-28

### Added

- **Catalogue pack defaults** (`catalogue.toml`): a `[pack-defaults.<pack-name>]` table now lets
  catalogue operators declare default config values for any pack they distribute. These are baked
  into `_data/install-defaults.toml` by `agentbundle catalogue self-host --write` and merged with
  user config at runtime so every `load_pack_config` call resolves the three-layer cascade
  (pack-source defaults → operator defaults → user config).
- **Custom user directory** (`catalogue.toml`): `[catalogue] user-dir = "~/custom/path"` overrides
  the default `~/.agentbundle` root for the entire catalogue; `agentbundle install` persists the
  override as `user-root` in `state.toml` and every subsequent `pack_dir` call honours it.
- **Pack config API** (`agentbundle.config`): `pack_dir(pack_name)` resolves the user-scope
  directory for a pack; `load_pack_config(pack_name)` returns the merged three-layer config dict.
  Both honour any custom `user-root` stored in `state.toml`.
- **Operation log** (`agentbundle.oplog`): `write_entry(pack_name, action, src, ...)` appends a
  JSONL record to `<pack_dir>/ops.jsonl` using `O_CREAT|O_APPEND` (POSIX) or the state-file
  mutex (Windows). Each entry is bounded to 4096 bytes; oversized extras are silently truncated
  with a `"_truncated": true` marker.
- **`agentbundle pack-config` CLI**: `get <pack> <key>`, `set <pack> <key> <value>`,
  `show <pack>`, and `path <pack>` subcommands for reading and writing pack config entries.
- **`agentbundle oplog` CLI**: `append <pack>`, `show <pack>`, and `clear <pack>` subcommands
  for managing the per-pack operation log.

## [0.20.3] — 2026-07-27

### Changed

- **Ruff + mypy CI gates.** `build-check.yml` and `build-check-windows.yml` now
  run `ruff check` and `mypy` on every push and pull request. Ruff enforces
  style, imports, common-bug, and pathlib rules (E, W, F, I, UP, B, SIM, C4,
  PIE, RET, PTH). Mypy type-checks the two typed packages
  (`agentbundle`, `credbroker`) with strict import discipline.

### Fixed

- **Internal type annotations.** `commands/upgrade.py` now uses precise
  `Path | None` and `UserConfig | None` parameter types (was `object`),
  eliminating all mypy errors in that module. Other catalogue-tooling modules
  (`build.py`, `verify.py`, `lint.py`) carry targeted `# type: ignore`
  suppressions for dynamic module attributes and YAML duck-typing that mypy
  cannot resolve at import time.
- **Ruff violations.** All PTH, B904, SIM, UP, RET, and C4 rule violations
  across internal scripts are resolved — `os.*` calls replaced with
  `pathlib.Path` equivalents, exception re-raises carry `from exc`, and
  ternaries replace equivalent if/else blocks where they simplify reading.

## [0.20.2] — 2026-07-27

### Fixed

- **Seeds-lint symlink hardening.** `catalogue lint` with `lint-seeds = true`
  now uses `os.walk(followlinks=False)` instead of `Path.rglob("*")` for the
  seeds walk. On Python 3.11/3.12, `rglob` traverses into symlinked
  directories and reads their contents; `os.walk` with `followlinks=False`
  does not, closing a traversal gap for packs that ship a symlinked directory
  under `seeds/`.
- **`sso-broker.py` Windows console hardening.** The broker script
  (`packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`) now
  reconfigures stdout and stderr to UTF-8 inside the file-path-invocation
  bootstrap gate, matching the fix applied to the other credentialed CLIs in
  0.20.1. Without this, em-dash messages on a Windows cp1252 console raised
  `UnicodeEncodeError` before the script could run.

## [0.20.1] — 2026-07-27

### Fixed

- **Windows portability.** The CLI entry point now reconfigures stdout/stderr to
  UTF-8 with `backslashreplace` at startup, preventing `UnicodeEncodeError` on
  Windows consoles (cp1252) when output includes non-ASCII characters (⚠, →).
- **Windows sandbox isolation in tests.** The test suite's autouse fixture now
  sets `USERPROFILE` alongside `HOME`, ensuring `scope.resolve_user_root()` uses
  the sandbox on Windows (where `Path("~").expanduser()` reads `USERPROFILE`).
- **Editable-install detection on Windows.** `url2pathname` can return a path
  with a spurious leading `/` before the drive letter (e.g. `/C:\repo`); that
  prefix is now stripped before constructing the `Path`.
- **NTFS reparse-point safety.** `is_symlink()` calls in the pack-floor install
  and seed-delivery paths are now wrapped in `try/except OSError`, skipping the
  entry conservatively when the reparse point cannot be interrogated.

## [0.20.0] — 2026-07-27

### Added

- **`agentbundle docs <pack>`** — new CLI verb that reads pack documentation
  from `packs/<pack>/docs/` in the catalogue source. Supports `--list` to
  enumerate available files and an optional `<file>` positional to display a
  specific file by stem. Works across all four source types (local path, editable
  install, git+https, Artifactory archive). Markdown rendered as plain text with
  ANSI bold headings on a TTY.

- **`[pack.runtime-dependencies]` in pack schema.** New array under `[pack]`
  for declaring external runtime dependencies (pip packages, npm modules, etc.)
  required by a pack's skills. Each entry carries `ecosystem` (required, one of
  pypi/npm/cargo/go/homebrew/apt/system), `package` (required), `version`,
  `optional`, `skills`, `install`, and `note`.

## [0.19.0] — 2026-07-27

Supersedes the accidental research-branch 0.18.0 PyPI publish. Contains all
features from 0.13.0 through 0.18.0 plus the ini-005 catalogue-tooling surface
introduced in 0.13.0.

## [0.13.0] — 2026-07-26

### Added

- **`agentbundle catalogue lint` now covers profiles, seeds, first-value contract, and credentialed-skill conventions.** Four checks previously scattered across standalone `tools/` scripts are now built into the CLI: profile key validation (`_check_profiles`); catalogue-seed blocklist enforcement — no `agent-ready-repo` strings, RFC/K-series identifiers, or internal-spec names leak into adopter seeds (`_check_seeds`); first-value contract completeness for Level-A and Level-B packs (`_check_first_value`); credentialed-skill AST inspection — argv-ban, canonical shim detection, dotfile guard (`_check_credentialed_skills`). Requires `pip install 'agentbundle[lint]'` for the credentialed-skill AST pass.

- **`agentbundle catalogue lint --deep` runs the agentskills.io spec compliance pass on every `SKILL.md`.** Checks frontmatter key set, description length cap (1024 chars), kebab-case name, blessed subdirectory layout, eval structure, and path reference hygiene. Exits 2 with a clear message when PyYAML is not installed; exits 0 without `--deep` regardless of PyYAML.

- **`agentbundle catalogue verify` now runs agent-artifact lint (step 11) and plugin-manifest schema validation (step 13).** Step 11 (`_step_agent_artifacts`) validates `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`, and `.claude/commands/*.md` frontmatter and enforces the APM-skill leak guard. Step 13 (`_step_plugin_manifests`) validates every generated `*.claude-plugin/plugin.json` against the bundled schema. Both require `pip install 'agentbundle[lint]'`; absent PyYAML, step 11 returns a single advisory diagnostic and step 13 is a no-op.

- **`agentbundle pack evals run`** — new CLI command porting the pack activation-eval runner into the CLI. Runs Tier-A skill-activation evals using `claude --output-format stream-json --verbose --allowed-tools Skill`; reads `[pack.evals].skills` from `pack.toml`; writes per-run results to a gitignored eval workspace. Report-only: an eval miss is not a non-zero exit.

- **`upgrade --all` sentinel fix.** Packs installed before source-provenance tracking was added stored `source = "agent-ready-repo"` in state. The fix covers both `None` and `"agent-ready-repo"` absent cases so pre-provenance installs resolve through the configured default source and upgrade normally.

- **Windows cp1252/UTF-8 guards.** All `.apm/` scripts and CLI subprocess calls now include `sys.stdout.reconfigure(encoding="utf-8", errors="strict")` / `sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")` and `encoding="utf-8"` on `subprocess.run` calls. Lazy `import asyncio` in credentialed scripts.

- **New `[lint]` optional dependency.** `pip install 'agentbundle[lint]'` pulls `pyyaml>=6.0` for deep linting. Zero-dependency adopters who don't use `--deep` or verify are unaffected.

### Removed

- **Six standalone `tools/` scripts deleted.** `tools/lint-agent-artifacts.py`, `tools/lint-catalogue-seeds.py`, `tools/lint-profiles.py`, `tools/lint-first-value-contract.py`, `tools/lint_credentialed_skills.py`, and `tools/validate-claude-plugin-manifests.py` — plus their self-tests and the `tools/lint-credentialed-skills.sh` wrapper — are removed. All functionality is preserved in `catalogue lint` and `catalogue verify` with identical error codes and message strings.

## [0.12.1] — 2026-07-23

### Changed

- **`install --dry-run` now previews governance seed files alongside the
  projected adapter files.** Seeds (AGENTS.md, docs/CHARTER.md,
  CONVENTIONS.md, and companions) are classified read-only and included in
  the plan output — `create tier-1`, `companion tier-2`, or skipped — so
  the dry-run is a complete picture of what a real install would write, not
  just the adapter projection.
- **`assert_projection_jailed` centralises the two-step path-jail check.**
  A new read-only helper in `agentbundle/safety.py` unifies the root-escape
  (`assert_under`) and prefix-match checks that were duplicated across
  `install.py` Step 8, `upgrade.py`'s dry-run probe, and `write_jailed`'s
  inline prefix block. All three call sites now route through it.
- **`upgrade` probes all projected paths before any write.**
  The non-dry-run upgrade path gains the same probe-all-before-write
  pre-flight that `install`'s Step 8 uses: a prefix-jail violation now aborts
  with zero files written, rather than failing mid-loop after some writes.

## [0.11.1] — 2026-07-16

### Fixed

- **`install` without `--adapter` now targets the auto-resolved adapter when
  handing off to `upgrade`.** Installing a pack already present for multiple
  adapters at a scope (e.g. `claude-code` and `codex`) without specifying
  `--adapter` triggered upgrade's "pass `--adapter` to pick one" disambiguator,
  even though install's probe had already selected the right row. The offered
  upgrade now forwards the auto-resolved adapter, matching the behavior when
  `--adapter` is explicit.

## [0.11.0] — 2026-07-03

### Added

- **New `agentbundle show <pack>` command — a pack's skills and agents, derived
  live.** Answers "what does this pack contain?" by walking the pack's `.apm/`
  source tree on each call, printing its `pack.toml` metadata alongside the full,
  sorted skill and agent inventory. `--format json` emits a stable object
  (`name`, `version`, `description`, `skills`, `agents`, `source`) for scripts and
  agents. Nothing is persisted and no manifest is touched, so the answer can't
  drift from what the pack ships. When the catalogue can't be resolved, an
  *installed* pack still reports its inventory from the install-state files
  (`source: installed-state`, recovered across both scopes and every adapter row);
  a not-installed pack errors and exits non-zero. Implements RFC-0060 / ADR-0049.

## [0.10.2] — 2026-06-30

### Fixed

- **`install --adapter X` now carries that adapter through when it hands off to
  `upgrade`.** Installing a pack that is already present, with `--adapter`
  specified, offers to upgrade instead — but the hand-off dropped the adapter,
  so a pack installed for more than one adapter at that scope hit upgrade's
  "pass `--adapter` to pick one" disambiguator even though you had just passed
  it. The offered upgrade now targets the adapter you named.

## [0.10.1] — 2026-06-30

### Fixed

- **The "no catalogue source" error no longer sends you to a `--catalogue` flag
  that doesn't exist.** The catalogue is a trailing positional argument; when no
  source resolves, the recovery text now reads "pass a catalogue argument …" so
  following it actually works.

## [0.10.0] — 2026-06-30

_Backfilled: 0.10.0 shipped (tag `agentbundle-v0.10.0`) without a changelog
entry; recorded here for the history._

### Added

- **`agentbundle list-installed` — a read-only view of what's actually installed.**
  Lists every installed `(pack, adapter)` row across the user and repo scope with
  its version and an `up-to-date` / `upgrade-available` / `unknown` status against
  the catalogue; the check degrades to `unknown` (never an error) when the
  catalogue can't be resolved. `--no-check` / `--offline` skips it, `--scope`
  filters to one scope, and `--check-drift` adds a per-row count of files edited
  locally since install (#468).

### Changed

- **Upgrade messaging now reports per-adapter versions and distinguishes a
  re-applied install from a genuine upgrade**, and flags local drift from the
  installed baseline (#468).

## [0.9.0] — 2026-06-26

### Changed

- **Install identity is now the content-addressed *footprint*, not the pack
  name — one pack can be installed for several adapters at one scope, and the
  `.agents/skills/` cohort shares one skill copy (RFC-0052 / ADR-0039+0040).**
  The state file is keyed `[pack.<name>.adapters.<adapter>]` (schema **v0.4**).
  Installing `research` for `codex` after `claude-code` now succeeds (disjoint
  trees); installing it for `cursor` after `codex` co-owns the shared
  `.agents/skills/` files instead of rewriting them. A genuine collision — the
  same path at different content, or two different packs claiming one path — is
  refused, naming the conflicting paths; `--force` keeps your copy as a
  `.upstream` companion. `uninstall`, `upgrade`, and `diff` gain an `--adapter`
  disambiguator (required only when a pack has more than one adapter row at the
  scope); `uninstall` removes a shared file only when its last owner goes. After
  an install that writes a shared skill, stderr names the other adapters that
  read it.
- **cursor, gemini, and copilot now project the `skill` primitive to the shared
  `.agents/skills/` home (joining codex)** instead of their native
  `.cursor/skills/` / `.gemini/skills/` / `.github/skills/`. Their
  agents/hooks/commands are unchanged. Adapter contract bumped to **v0.17** with
  a `[contract.shared-prefixes]` registry.

### Breaking

- **State schema migration is greenfield (no auto-converter).** A pre-v0.4
  state file is refused on read *and* write with a re-install prompt; mixed
  CLI versions across CI/local can no longer silently mis-read state. Existing
  cursor/gemini/copilot installs may leave a now-unused native skills tree
  behind — re-install to land skills at the shared home.

## [0.8.0] — 2026-06-25

### Added

- **The `catalogue` argument is now optional on `install`, `upgrade`,
  `list-packs`, and `list-profiles` (RFC-0046 + RFC-0047).** When omitted, the
  source resolves through a four-layer, first-match-wins chain: an explicit
  `catalogue` positional › your `config set source` value › an editable clone
  (`pip install -e`, detected via PEP 610 and walked up to the catalogue root,
  bounded by the enclosing `.git` repo) › a packaged default
  (`git+https://github.com/eugenelim/agent-ready-repo`). So a public user runs
  `agentbundle install --pack core` (or `agentbundle list-packs`) with no URL,
  and a gateway-bound editable fork defaults to its own clone — with no
  repo-committed source and no cwd fall-back (a code-provenance boundary). All
  four verbs share one resolver, so a bare query on an editable fork resolves to
  the local clone (never silently fetching upstream). New `source` user config
  key (`config set/get/unset source`). Layer-4 integrity-pinning (pin `main` to a
  SHA + verify the archive digest) is a named follow-on.

### Changed

- **`agentbundle list-packs` and `list-profiles` word-wrap the DESCRIPTION
  column to fit the terminal.** On an interactive terminal whose width the
  table would overflow, the long description column wraps to the leftover
  width — every physical line stays within the terminal, continuation lines
  align under the column, and the columns that follow it (DEPENDENCIES) stay on
  the row's first line. When stdout is **not** a terminal (piped or
  redirected), output is unchanged: full content-width columns, untruncated, so
  `grep`/`awk`/`cut` still see stable columns — the convention `gh`, `git`, and
  `ls` follow. Both commands now share one terminal-aware table renderer.

## [0.7.0] — 2026-06-24

### Changed

- **`agentbundle uninstall` gains `--dry-run` and `--yes`, and confirms before
  removing.** It classifies each recorded file into `remove` (Tier-1, bundle-
  owned) or `keep` (Tier-2, adopter-edited): `--dry-run` prints that plan and
  writes nothing (no removal, no hook-wiring unproject, no state change);
  otherwise it confirms before the first `os.remove` (`--yes` skips; a non-TTY
  stdin refuses rather than blocking). The execution acts on the previewed
  classification without re-hashing, so the bytes a dry-run / prompt shows are
  exactly the bytes removed. Tier-2 preservation is unchanged.
- **`agentbundle install --force` confirms before its destructive cleanup; new
  `--yes`.** When `--force` would delete on-disk paths, it lists the deletion
  unit — the dist-tree subtree roots (`claude-plugins/<pack>`, `apm/<pack>`) or
  the orphan files — and confirms before deleting; the whole destructive block
  (rmtree + state-row drop + state-file rewrite) is gated atomically, so a
  decline mutates nothing. `--yes` skips the prompt; a non-TTY without `--yes`
  refuses with zero deletions. `--force` used only as a cross-scope bypass (no
  deletion) is unchanged and never prompts. **Migration:** CI using the deleting
  form of `install --force` must add `--yes`.
- **`agentbundle install` offers to upgrade an already-installed pack.** Instead
  of flatly refusing with `use 'upgrade'`, installing a pack already present at
  the requested scope now offers (on a TTY) to run `upgrade` against the same
  catalogue/scope; `install --yes` runs it without prompting. A non-interactive
  stdin without `--yes`, and `install --dry-run`, keep the historical refusal.
- **`agentbundle reconcile` and `list-targets` drop their dead `--scope` flag.**
  `reconcile --scope` had a single legal value (`user`) equal to its default, and
  `list-targets --scope` was parsed but never read. Both are removed; passing
  `--scope` to either now reports `unknown flag for <verb>: --scope`. Default
  behaviour is unchanged.

- **`agentbundle upgrade` no longer takes `--to` (breaking).** The upgrade
  target is now derived from the resolved catalogue's `pack.toml` `[pack]
  version` — the catalogue is the single source of truth, and there is no
  version-history store to select from (`--to` was `required` but never
  validated against the catalogue's actual version). The command shows
  `installed → target`, asks before writing, and the success recap names both
  versions (`upgraded: <pack> @ <scope> <from> -> <to>`). When the installed
  version already equals the target, it says so and offers to re-apply.
  Migration: drop `--to <version>`; add `--yes` for non-interactive / CI use.
  To move to a specific past version, point the catalogue at that git ref.

### Added

- **`agentbundle upgrade --yes`** skips the confirmation prompt for
  non-interactive use; without it, a non-TTY stdin refuses (with guidance to
  pass `--yes`) rather than blocking on a prompt.

### Fixed

- **`agentbundle upgrade` rejects two per-primitive flags at once.** The
  `--skill` / `--agent` / `--hook` / `--seed` / `--command` flags are now a
  mutually-exclusive group; previously passing two silently upgraded only the
  first.

## [0.6.0] — 2026-06-20

### Fixed

- **Kiro custom agents now reach the bundle's skills — CLI and IDE** (RFC-0022
  erratum E4; adapter contract v0.15). On both Kiro targets, only the *default*
  agent auto-discovers skills; a *custom* agent (`kiro --agent <name>`, every
  headless `--no-interactive` run, or an IDE subagent) loaded **zero** skills
  unless it declared them in its `resources` field (kiro #6887/#6888/#4993). The
  `kiro-cli` and `kiro-ide` agent projections now inject a skill-resources glob
  (`skill://.kiro/skills/**/SKILL.md` plus the `~/.kiro/skills/**/SKILL.md`
  user-scope twin) into every projected agent — CLI into the agent JSON, IDE
  into the `.md` YAML frontmatter (quoted, YAML-safe). An agent that declares
  its own `resources` keeps it; the deprecated `kiro` alias inherits the IDE
  behavior. Default-agent runs were already fine and are unaffected.

### Added

- **`inject-resources` adapter-contract field** (contract v0.15). A typed,
  optional array on an adapter's agent projection entry that injects a fixed
  `resources` list into every projected agent. Currently used by the two Kiro
  adapters for skill reachability (above).

## [0.5.0] — 2026-06-16

### Added

- **Curated install profiles — `install --profile <name>` and `list-profiles`**
  (RFC-0034). A profile is a first-party `profiles/<name>.toml` at a catalogue
  root naming a single-scope, deps-first set of packs an adopter installs in
  one command. `agentbundle install --profile <name> <catalogue>` pins one
  scope and one adapter for the whole batch, runs the full read-only pre-flight
  for every pack before writing any, then installs each in authored order;
  `agentbundle list-profiles <catalogue>` browses what a catalogue offers.
  Adds zero primitives and zero adapter-contract surface — the CLI reads the
  manifest, the catalogue carries it.

### Fixed

- **`agentbundle install --adapter kiro` now behaves exactly like `kiro-ide`**
  (RFC-0022 alias parity). The `kiro` → `kiro-ide` alias is now canonicalized
  at every install-path decision site, not just the build registry.
- **`--version` reports the package version.** `CLI_VERSION` had drifted to
  `0.1.0` and was printed by `agentbundle --version` regardless of the released
  version; it now tracks the package version (`0.5.0`).

## [0.4.0] — 2026-06-14

### Added

- **`pack.toml` is the rich source of truth for pack metadata** (RFC-0031,
  adapter contract v0.14). A pack may now declare `license`,
  `[[pack.maintainers]]`, `[pack.links]`, `categories`, `keywords`, a `readme`
  pointer, and a `[pack.metadata.<tool>]` escape hatch. The build projects the
  cleanly-mappable subset — plus the pack's `README.md` — into each
  distribution route's manifest (`plugin.json` / `marketplace.json` entry), so
  a catalogue describes each pack richly instead of with one sentence. **All new
  fields are optional**; packs pinned below contract v0.14 are unaffected.
- **Soft `categories` vocabulary** — `agentbundle validate` recognizes a
  default set of category slugs and emits a **warning (exit 0)**, never an
  error, on an unknown slug. The vocabulary is extensible by design (RFC-0031
  D8); `design` is included for the `design-craft` pack.
- **`list-packs` surfaces the enriched metadata** so a catalogue is browsable
  by more than name and a one-line description.

### Changed

- **Pack and plugin-manifest JSON schemas accept the optional enriched fields**
  (the `additionalProperties: false` gate on both manifest schemas was relaxed
  for the projectable metadata subset).

### Fixed

- **`build-self` no longer emits untracked per-quadrant guide READMEs.** The
  self-host projection skips `guides/**` (adopters still receive guide
  scaffolds via seed delivery).

## [0.3.1] — 2026-06-12

### Changed

- **README rewritten for adoption** — quick start, a common-commands
  reference, and the "npm for your coding agent" framing; the PyPI summary
  now matches.
- **Static-analysis annotations** carried in from the repo's SAST gate
  (ADR-0017): `# nosec B310` on the constant-base GitHub-archive fetch and
  `usedforsecurity=False` on the non-security finding-ID digest. No runtime
  behaviour change.

## [0.3.0] — 2026-06-12

### Added

- **Cursor full-parity distribution adapter** (RFC-0026) — projects all
  primitives for both install scopes via the single-writer
  `.cursor/` model.
- **Gemini CLI full-parity distribution adapter** (RFC-0027) — keeps and
  maps tools, projects a tier model map, supports the
  `gemini-command-toml` mode, and bridges `AGENTS.md` through the
  single-writer `.gemini/settings.json`.
- **`--dry-run` for `install` and `upgrade`** — preview the projection
  without writing any files.
- **Upgrade surfaces Tier-2 companion-drops** — `upgrade` now reports the
  `.upstream` companion files that an adopter must reconcile by hand.
- **credbroker install-time user-scope delivery rail** — the build
  pipeline vendors `credbroker` to `.agentbundle/lib` (drift-gated) and
  consumer bootstraps append the `~/.agentbundle/lib` floor at lowest
  precedence (new `user_libs` module).

### Changed

- **Copilot adapter projects skills as first-class `SKILL.md`** and
  corrects the web-tool documentation (adapter contract v0.12).
- **Codex adapter projects agent model and tool config** into the
  generated agent TOML.
- **Pack admittance** — credentialed packs admit the `copilot` and
  `cursor` adapters (RFC-0013 erratum); `research` and `architect` opt
  into the `cursor` adapter.

### Removed

- **Retired the shared-libs shim projection.** Credentialed skills now
  `import credbroker` from the user-scope lib floor instead of a
  build-projected shim.

## [0.2.0] — 2026-05-26

### Removed (breaking)

- `agentbundle.credentials` — the public loader module (`load_credentials`,
  `Credentials`, `CredentialsMissingError`, `Tier2HardFailError`,
  `parse_env_file`, `EnvParseError`).
- `agentbundle.creds` — the entire subpackage (`loader`, `exceptions`,
  `_keychain_macos`, `_credman_windows`), including the schema parser
  `_parse_schema` and the `CredsSchema` / `KeyDef` dataclasses.
- `agentbundle creds` CLI subcommand and its four verbs (`setup`,
  `check`, `where`, `rm`).

### Migration recipe (RFC-0013 § 9)

Out-of-tree credentialed skills that previously imported the loader
from `agentbundle.credentials` must change four things to migrate to
0.2.0. None of the four are optional; missing one leaves the import
unresolvable.

**1. Add four frontmatter declarations** to the skill's `SKILL.md`
(nested under the `metadata:` escape hatch):

```yaml
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds                       # selects the build-projected shim broker
  namespace: <your-namespace>       # matches your creds-schema.toml
  keys: ["<KEY>"]                   # the secret keys this skill resolves
```

The build pipeline reads `auth: creds` to decide which skills receive
the projected shim. Without that line the projection doesn't fire.

**2. Change the import line** in each script that resolves
credentials:

```python
# Before (0.1.x)
from agentbundle.credentials import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)

# After (0.2.0)
from .credentials_shim import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)
```

**3. Run `make build-self`** in the catalogue's clone (or invoke
`agentbundle install --pack credential-brokers --scope user .` if
you install via the CLI). This materialises the three shim files —
`credentials_shim.py`, `_keychain_macos.py`, `_credman_windows.py`
— into your skill's `scripts/` directory. Without this step the
relative import resolves to nothing and you get
`ModuleNotFoundError`.

**4. Replace `agentbundle creds setup <namespace>` invocations** in
docs and error messages with the `credential-setup` skill — shipped
by the `credential-brokers` pack at user scope. Authors invoke it
from their agent's skill loader instead of from the shell. There is
no longer an `agentbundle creds` CLI verb.

Verification: invoke the consumer skill's own `check` verb (or
equivalent low-stakes call). The shim walks Tier 1 → 2 → 3 the same
way the prior loader did and surfaces the same exceptions; no
behavioural delta.

### Adopter pin policy

Pin to `agentbundle < 0.2` in your dependency manifest until you have
completed the migration above. The pre-0.2 minor (`0.1.0`) is the
intended rollback target; that release ships from the `agentbundle-v0.1.0`
git tag and is published from the same release workflow this PR
amends. Adopters who cannot migrate immediately should stay on
`agentbundle < 0.2` until they have shipped the four-step recipe.

If no `agentbundle-v0.1.0` tag exists on the upstream remote at the
time you read this changelog, the rollback target has not yet been
published — open a release issue against the catalogue requesting
one before bumping any production pin.

### Why this is breaking inside the 0.x window

Per RFC-0013 § *Drawbacks* — the migration removes a public surface
that one or more out-of-tree consumers may depend on. The deprecation
window inside 0.x is the prior minor (0.1.0) staying available on
PyPI; the migration recipe above is mechanical (one import-line
change per consumer); and the new shim is byte-equivalent (per
spec § AC6) to the prior loader's behaviour. No behavioural change.

## [0.1.0] — pre-0.2.0

The `agentbundle` build / install / adapt CLI and the
`agentbundle.credentials` public loader surface. See `docs/CHARTER.md`
and `docs/specs/skill-secrets/spec.md` for the historical scope.
