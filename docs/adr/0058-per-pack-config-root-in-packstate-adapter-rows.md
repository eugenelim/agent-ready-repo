# ADR-0058: Per-pack config root (`user-root`) stored as an optional field on `PackState` adapter rows in user-scope `state.toml`

- **Status:** Accepted
- **Date:** 2026-07-28
- **Areas:** state, install
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** [RFC-0101](../rfc/0101-pack-config-and-oplog.md), [ADR-0039 footprint co-ownership and install identity](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md)

## Decision summary

- **Decision:** Add an optional `user-root` field to every `[pack.<name>.adapters.<adapter>]` row in user-scope `~/.agentbundle/state.toml`, written at install time from the catalogue's `user-dir` setting; read by `pack_dir()` to locate a pack's config and operation-log directory.
- **Because:** The pack root must survive reinstall, be concurrent-write safe, and be readable by any pack script without network access — `state.toml` is already locked by `persist_state_locked` and satisfies all three properties.
- **Applies to:** `agentbundle/config.py` (`pack_dir`, `PackState`), `agentbundle install`/`uninstall`, and any future agentbundle capability that needs to locate a pack's user-scope directory.
- **Tradeoff accepted:** `PackState` schema grows one permanent optional field; `pack_dir()` must aggregate across all adapter rows for a pack slug and raise `PackRootConflict` when pre-existing rows from another catalogue disagree.
- **Revisit if:** A pack-level (not adapter-level) section is added to the `state.toml` schema, at which point `user-root` can move there and the per-row duplication is eliminated.

## Context

A pack (a deployable unit of AI agent skills, agents, and hooks for one domain) needs a stable, per-user directory for two new artifacts: a `config.toml` holding user overrides and an `ops.jsonl` operation log. The directory must:

1. Survive pack reinstall — its location cannot be computed on the fly from the current install command.
2. Support multiple catalogues that declare different `user-dir` values (e.g. `~/agentcommander` for one catalogue, `~/.agentbundle` for another) without collision.
3. Be readable by pack scripts without holding any lock or requiring network access.
4. Be durable under concurrent `agentbundle install` invocations.

State `schema-version = "0.4"` (ADR-0039) keys pack rows as `(pack_name, adapter)` tuples — one row per installed adapter. `user-root` is written to every row this install writes; rows from other catalogues are left untouched. `pack_dir()` reads all rows for the pack slug and raises `PackRootConflict` if they disagree — this is the signal that two catalogues installed the same slug with different roots.

The field is optional: absent rows default to `"~/.agentbundle"`. No schema-version bump is required.

## Decision

- **D1:** `user-root` is an optional field on each
  `[pack.<name>.adapters.<adapter>]` row in user-scope
  `~/.agentbundle/state.toml`, defaulting to `"~/.agentbundle"` when absent, and
  requires no schema-version bump.
- **D2:** `agentbundle install` writes `user-root` from the catalogue's
  `user-dir` setting to every row that install writes, and leaves rows from other
  catalogues untouched.
- **D3:** `agentbundle uninstall` clears `user-root` when the last adapter row for
  a pack is removed.
- **D4:** Both writes go through `persist_state_locked` atomically.
- **D5:** `pack_dir()` resolves in order: the `home=` kwarg, then the distinct
  `user-root` values across all rows for the pack slug, then
  `user_state_path(home).parent` as the fallback when no rows exist.
- **D6:** `pack_dir()` raises `PackRootConflict` when rows for one pack slug carry
  disagreeing `user-root` values.
- **D7:** Any capability needing a pack's user-scope directory calls `pack_dir()`
  and does not re-derive the resolution logic.

`user-root` is stored on each `[pack.<name>.adapters.<adapter>]` row in user-scope `~/.agentbundle/state.toml`. `agentbundle install` writes the value from the catalogue's `user-dir` setting (default `"~/.agentbundle"`); `agentbundle uninstall` clears it when the last adapter row for a pack is removed.

`pack_dir(pack_name, *, home=None)` resolution order:

1. `home=` kwarg (test override).
2. `state.rows_for_pack(pack_name)` from `user_state_path(home)`: collect distinct `user-root` values; if all rows agree, expand `~` relative to `home` and use that path; raise `PackRootConflict` on genuine disagreement.
3. `user_state_path(home).parent` — `~/.agentbundle/` — as fallback when no rows exist for the slug.

## Alternatives considered

**Side-index file (`~/.agentbundle/catalogues.toml`):** A separate TOML file holding slug → root mappings. Rejected: no locking story (the file can be deleted or corrupted by a concurrent write without the existing `persist_state_locked` covering it); a missing file causes silent mislocation.

**Per-catalogue env var:** An env var per pack slug set in the user's shell profile. Rejected: not durable across sessions; not machine-readable; cannot be set by `agentbundle install`.

**Do nothing (implicit `~/.agentbundle/` fallback for everything):** Rejected: blocks multi-catalogue coexistence — two catalogues with different `user-dir` values cannot install packs to their respective directories.

## Consequences

- `PackState` dataclass gains `user_root: str = "~/.agentbundle"` (kebab-serialized as `user-root`). Every caller that constructs `PackState` from TOML gains a `user-root` field with read-time default.
- `pack_dir()` introduces `PackRootConflict` — a new exception type, documented in `pack-config-api.md`.
- `agentbundle install` and `agentbundle uninstall` must write/clear `user-root` atomically via `persist_state_locked`.
- Future pack capabilities that need the user-scope directory call `pack_dir()` — they do not re-derive the root resolution logic.

**Revisit if:** `PackRootConflict` (D6) starts firing during ordinary
multi-catalogue use rather than signalling a genuine same-slug clash, which would
mean the per-row placement of `user-root` is carrying conflicts it should not.
