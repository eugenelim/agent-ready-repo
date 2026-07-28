# Plan: catalogue-pack-defaults

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Four parallel changes land in one PR: (1) JSON schema + dataclass updates to accept the new `catalogue.toml` fields, (2) `compile_defaults` emitter extended to include sorted `[pack-defaults.*]` sections, (3) `PackState` gains `user_root`, (4) `agentbundle install` writes `user-root` to adapter rows. The schema changes gate all runtime consumers so they land first within the PR; the emitter and install changes follow. All tasks have unit tests co-landed.

## Constraints

- RFC-0074: `user-dir` must resolve under `$HOME`; rejected at both `compile_defaults` and `agentbundle install`.
- ADR-0059: `compile_defaults` must emit alphabetically sorted pack names and keys.
- ADR-0058: `user-root` is written only to rows this install writes; pre-existing rows are not touched.
- `STATE_SCHEMA_VERSION` stays at `"0.4"` — `user-root` is optional with a read-time default.

## Construction tests

**Cross-cutting:**
- Round-trip test: write a `catalogue.toml` with both `user-dir` and `[pack-defaults.*]`, run `compile_defaults`, read the output, assert values match.
- Idempotency test: run `compile_defaults` twice; assert byte-exact equality of the two outputs.

## Tasks

### T1: Update `catalogue.schema.json` to accept `user-dir` and `[pack-defaults.*]`

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/_data/catalogue.schema.json`

**Tests:**
- Fixture with `[catalogue].user-dir = "~/custom"` → `validate()` returns no errors.
- Fixture with `[catalogue].user-dir = "/opt/shared"` → passes JSON schema (validation is a business rule, not a schema rule); schema does not add an enum or pattern constraint here.
- Fixture with top-level `[pack-defaults.atlassian]` → `validate()` returns no errors.
- Fixture with unknown top-level key `[unknown-section]` → `validate()` returns errors (existing `additionalProperties: false` still holds for non-`pack-defaults` keys).

**Approach:**
- Add `user-dir` as an optional string property inside the `catalogue` object definition.
- Add `pack-defaults` as an optional object with `additionalProperties: { type: "object", additionalProperties: { type: "string" } }` at the document root.

**Done when:** All T1 tests pass; `load_catalogue_config` no longer raises on valid new fields.

---

### T2: Update `CatalogueConfig` and `load_catalogue_config` to parse new fields

**Depends on:** T1

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/config.py`

**Tests:**
- `load_catalogue_config` on a fixture with `user-dir = "~/custom"` → `config.user_dir == "~/custom"`.
- `load_catalogue_config` on a fixture without `user-dir` → `config.user_dir == "~/.agentbundle"`.
- `load_catalogue_config` with `user-dir = "/opt/shared"` → raises `CatalogueConfigError`.
- `load_catalogue_config` with `[pack-defaults.atlassian] url = "https://jira.yourorg.com/"` → `config.pack_defaults == {"atlassian": {"url": "https://jira.yourorg.com/"}}`.
- `load_catalogue_config` with `[pack-defaults.bin]` → raises `CatalogueConfigError` (reserved slug).

**Approach:**
- Add `user_dir: str = "~/.agentbundle"` and `pack_defaults: dict[str, dict[str, str]] = field(default_factory=dict)` to `CatalogueConfig`.
- Parse `cat.get("user-dir", "~/.agentbundle")` and validate: must start with `~/`; `Path(user_dir.replace("~/", "")).is_absolute()` should be false for relative segments after `~`.
- Parse top-level `raw.get("pack-defaults", {})` and validate: each key must match slug grammar `^[a-z0-9][a-z0-9-]*$` and not be in the reserved set.

**Done when:** All T2 tests pass; `CatalogueConfig` fields accessible in downstream callers.

---

### T3: Extend `compile_defaults` to emit sorted `[pack-defaults.*]` sections

**Depends on:** T2

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/defaults.py`

**Tests:**
- `compile_defaults` on a fixture with two packs (`github`, `atlassian`) → output contains `[pack-defaults.atlassian]` before `[pack-defaults.github]` (alphabetical pack order).
- Within `[pack-defaults.atlassian]`, keys are sorted alphabetically.
- Running `compile_defaults` twice on same inputs → byte-exact equality.
- Pack-source defaults (lower precedence) are present; catalogue operator overrides (higher precedence) win on collision.

**Approach:**
- In the `compile_defaults` function, after existing sections, iterate `sorted(config.pack_defaults.keys())` and for each pack emit `[pack-defaults.<pack>]\n` followed by sorted key/value lines.
- Merge with pack-source defaults before sorting: pack-source defaults load from the pack's own `pack.toml` (or a new `[defaults]` section — TBD at implementation time; this task covers the operator-override side and leaves pack-source-default loading as a follow-on in the same PR if ready, or as a separate task).

**Done when:** All T3 tests pass; `check_defaults` does not drift on a clean run.

---

### T4: Update `check_defaults` to validate `[pack-defaults.*]` sections

**Depends on:** T3

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/defaults.py`

**Tests:**
- `check_defaults` on a baked file that matches → exits 0.
- `check_defaults` on a baked file with a manually added key → exits non-zero.
- `check_defaults` on a baked file with differently sorted keys → exits non-zero.

**Approach:**
- `check_defaults` already does a byte-exact comparison; the sort guarantee from T3 makes this naturally cover `[pack-defaults.*]`.
- Ensure the comparison path does not skip the new sections.

**Done when:** All T4 tests pass; CI drift check catches hand-edited pack-defaults.

---

### T5: Add `user_root` field to `PackState`

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/config.py`

**Tests:**
- `PackState` with explicit `user-root = "~/custom"` in TOML → `ps.user_root == "~/custom"`.
- `PackState` with no `user-root` key → `ps.user_root == "~/.agentbundle"` (read-time default).
- Serializing a `PackState` with `user_root = "~/custom"` → TOML output contains `user-root = "~/custom"`.
- `STATE_SCHEMA_VERSION` remains `"0.4"`.

**Approach:**
- Add `user_root: str = "~/.agentbundle"` to the `PackState` dataclass.
- Update the TOML serializer/deserializer to handle `user-root` ↔ `user_root` mapping.

**Done when:** All T5 tests pass; existing state.toml fixtures (without `user-root`) still load cleanly.

---

### T6: Update `agentbundle install` to write `user-root` to adapter rows

**Depends on:** T2, T5

**Touches:** `packages/agentbundle/agentbundle/commands/install.py` (or equivalent)

**Tests:**
- `agentbundle install` from a catalogue with `user-dir = "~/custom"` → state.toml rows for the pack contain `user-root = "~/custom"`.
- `agentbundle install` from a catalogue without `user-dir` → rows contain `user-root = "~/.agentbundle"`.
- Pre-existing rows from a different catalogue (different `user-root`) are not overwritten.

**Approach:**
- After creating each `PackState` row, set `ps.user_root = resolved_user_dir` from `catalogue_config.user_dir`.
- `~` expansion for validation uses `Path.home()` to confirm the path resolves under home; the stored value retains `~/` prefix.

**Done when:** All T6 tests pass; state.toml written by install is readable by `pack_dir()` (spec:pack-config-api/T1).

---

## Rollout

Pure build-tooling and install-time change — no runtime behavior changes in this spec. Ships as a single PR. No feature flag needed. `pack_dir()` and `load_pack_config()` (from `pack-config-api` spec) consume the `user-root` field written here.

## Changelog

- 2026-07-28: initial plan
