# Spec: catalogue-pack-defaults

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0074, ADR-0058, ADR-0059
- **Shipped in:** agentbundle 0.21.0
- **Contract:** none (build-time tooling; no external API surface)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Enable catalogue operators to declare per-pack configuration defaults (URLs, project keys, workspace IDs) and a custom pack user directory in `catalogue.toml`. When the catalogue is built, `compile_defaults` bakes these operator declarations into `_data/install-defaults.toml`. `agentbundle install` writes the catalogue's declared `user-dir` as `user-root` on every adapter row it creates for a pack in user-scope `~/.agentbundle/state.toml`.

> **Note (shipped scope):** This spec covers operator-declaration baking only. Merging pack-source defaults (lower-precedence values from each pack's own `pack.toml`) is a follow-on feature deferred to a future spec.

This spec covers only the build-side and install-side changes. The runtime API (`pack_dir`, `load_pack_config`, `write_entry`, CLI commands) is covered in the `pack-config-api` spec, which depends on this one.

## Boundaries

### Always do

- Reject `user-dir` values that do not resolve under the user's `$HOME` at install time (e.g. `/opt/shared`); emit a `CatalogueConfigError` at both `compile_defaults` and `agentbundle install`.
- Sort pack names and keys **alphabetically** in `compile_defaults` output — required for `check_defaults` byte-stable comparison.
- Validate new `catalogue.toml` fields through the existing `_apply_schema_validation` path (JSON schema first, business rules second).
- Write `user-root` to every adapter row this install writes; leave pre-existing rows from other catalogues untouched.

### Ask first

- Any change to `STATE_SCHEMA_VERSION` or the TOML serialization format of `PackState`.
- Any new reserved slug added to the enforcement list.

### Never do

- Accept a `user-dir` value that is absolute and outside `$HOME` (security boundary — home-confinement is the contract).
- Store credentials, tokens, or secrets in `[pack-defaults.*]` or `install-defaults.toml` — these are plain TOML, not a secrets store.
- Change the byte layout of existing `install-defaults.toml` sections (would break `check_defaults` for catalogues that haven't updated).

## Testing Strategy

- **TDD** for `compile_defaults` sort guarantee, `check_defaults` drift detection, `user-dir` validation, `PackState.user_root` round-trip serialization, and `agentbundle install` row write.
- **Goal-based check** for JSON schema validation: fixture `catalogue.toml` files with and without the new fields run through `load_catalogue_config` and either succeed or raise `CatalogueConfigError`.

## Acceptance Criteria

- [x] `catalogue.toml` with `[catalogue].user-dir = "~/custom"` loads without error via `load_catalogue_config`.
- [x] `catalogue.toml` with `[catalogue].user-dir = "/opt/shared"` raises `CatalogueConfigError` (absolute path outside `$HOME`).
- [x] `catalogue.toml` with `[catalogue].user-dir = "~/../../etc"` raises `CatalogueConfigError` (path traversal rejected). <!-- added during security review -->
- [x] `catalogue.toml` with top-level `[pack-defaults.atlassian]` loads without error.
- [x] `catalogue.schema.json` validates both `user-dir` and top-level `[pack-defaults.*]` sections; `additionalProperties: false` does not reject them.
- [x] `CatalogueConfig` exposes `user_dir: str` (defaulting to `"~/.agentbundle"` when absent) and `pack_defaults: dict[str, dict[str, str]]`.
- [x] `compile_defaults` writes `[pack-defaults.<pack>]` sections to `_data/install-defaults.toml`, sorted alphabetically by pack name and by key within each section.
- [x] Running `compile_defaults` twice on the same inputs produces byte-identical output.
- [x] `check_defaults` exits non-zero when the baked file does not match a fresh `compile_defaults` run.
- [x] `PackState` serializes `user_root` as the TOML key `user-root`; absent rows deserialize with `user_root = "~/.agentbundle"`.
- [x] `agentbundle install` writes `user-root` (from `catalogue.user-dir`) to every adapter row it creates for the pack in user-scope `state.toml`. <!-- data-flow tested; full integration test deferred -->
- [x] A `catalogue.toml` that declares `[pack-defaults.bin]` (reserved slug) raises `CatalogueConfigError`.

## Assumptions

- Technical: `compile_defaults` builds output via f-string template, not a general TOML serializer — sort order is fully in our control (source: adversarial spike 2026-07-28).
- Technical: `catalogue.schema.json` uses `additionalProperties: false` at both document root and `[catalogue]` object — both levels need updating (source: adversarial reviewer finding #4, 2026-07-28).
- Process: This spec ships before `pack-config-api`; the `pack-config-api` spec lists `spec:catalogue-pack-defaults/T6` as a dependency for `PackState.user_root`.
