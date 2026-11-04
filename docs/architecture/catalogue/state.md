# Catalogue-tree state files

A tree can carry two kinds of state file. Install state records which packs are
installed into a target. Derivation state records which files a derived
catalogue took from upstream.

They answer different questions, different commands write them, and neither
reads the other.[^8] A derived catalogue that also installs packs into itself
carries both, and nothing reconciles them.

| File | Answers | Written by | Schema |
| --- | --- | --- | --- |
| Install state: one file per scope (below) | Which packs are installed at this scope, at what version, from where | `install`, `upgrade`, `uninstall`, `init-state` | `0.4`, or `0.5` once the file holds a direct-source row |
| `.agentbundle/self-host-state.json` | Which files this tree was derived from upstream, the recipe used, and the source pin | `catalogue init --preset self-hosted` | `3` |

Install flow, locking, and the Tier contract are in
[`../agentbundle.md`](../agentbundle.md). The upstream pin that `catalogue sync`
reads is in [`upstream-sync.md`](upstream-sync.md).

## Install state

**State lives in one file per scope.**

| Scope | State file |
| --- | --- |
| `repo` | `<root>/.agentbundle-state.toml` |
| `user` | `~/.agentbundle/state.toml` |
| `local` | `<root>/.agentbundle-local-state.toml` |

Scope semantics are in [`../agentbundle.md` § 2](../agentbundle.md#2-install-state).

**A row is keyed by `(pack, adapter)` and carries the comparison basis for every
later write.** One pack can hold several adapter rows at one scope.[^1]

| Field | Meaning |
| --- | --- |
| `installed_version` | Pack version this row was installed at |
| `source` | Recorded source label for the row; `None` when unset |
| `install_route` | Route that wrote the row; defaults to `"cli"`, emitted as `install-route` |
| `primitives` | Primitive names the row installed |
| `files` | `{relpath: {sha}}` — the Tier contract's comparison basis |
| `scope`, `adapter`, `user_root`, `target_file`, `hook_wiring_owned` | Where the row lives and which merged hook-wiring entries it owns |
| `primitive_versions` | Per-primitive version overrides after a single-primitive upgrade |
| `artifact_uri`, `archive_sha256`, `source_revision` | Archive provenance for `catalogue+https://` and `archive+https://` sources; `None` for a local directory |
| `source_kind`, `source_path`, `source_digest` | Direct-source provenance (schema `0.5`); `source_kind` is `pack` or `skill` |

`files[relpath].sha` is the basis `safety.classify` compares with the file on
disk; the Tier contract is in [`../agentbundle.md` § 2](../agentbundle.md#2-install-state).
The archive provenance fields are the vocabulary the upstream pin reuses.[^2]

**A reader refuses any `schema-version` it does not recognise, absent included,
on read and write.** There is no best-effort read and no converter; the adopter
reinstalls.

A file is `0.4` until a mutation adds or updates a direct-source
row, then `0.5`; the writer never downgrades it, and a `0.4`-only reader refuses
a `0.5` file. A `0.5` file can also hold catalogue-route rows.[^3]

## Derivation state

**`.agentbundle/self-host-state.json` is the ownership boundary for a derived
catalogue: a path it lists was written by `init`, and a path it omits belongs to
the adopter.** Every value in it must be safe on its own, because it is written
after the identity leak check and no control scans it.[^4]

| Field | Meaning |
| --- | --- |
| `schema_version` | `"3"` |
| `managed_paths` | `[{path, sha256}]` for every file `init` wrote |
| `adapters` | Adapter set the derivation targeted |
| `managed_target_path` | Absolute target the state describes |
| `source_pack_identity` | Upstream catalogue name under `attributed`; the derived catalogue's name under any other mode |
| `source_root_kind` | `"self-hosted-source"` |
| `recipe` | `packs`, `profiles`, `guides`, `attribution`, `tooling`, `name`, `display_name`, `description`, `owner_name`, `owner_email`, `preferred_adapter`, `repository_url` |
| `pin` | `source_revision`, `archive_sha256`, `synced_at`, and `source_uri` (only under `attributed`) |

**Removal is hash-guarded.** `_remove_stale_owned_paths` removes a path that has
left the plan only when its recorded `sha256` matches the file on disk, so an
adopter-edited file is never deleted. A schema-1 entry migrates to
`{path, sha256: null}`; a null hash never satisfies the removal guard, so such an
entry is never removed.[^5]

**The recipe seeds a later `init`.** Pack and profile selections and the
identity fields are reused when their flags are omitted; explicit flags win. The
mode fields (`guides`, `attribution`, `tooling`) are not replayed, so omitted
mode flags take their safe defaults.[^6]

**The pin never names upstream under `--attribution white-label`.**
`_source_pack_identity` branches on `attributed` rather than `white-label`, so an
attribution mode added later gets the non-disclosing name by default. A local
path source has no resolved revision or archive digest, so both pin values are
null.[^7]

**This file has no contract in [`contracts/`](../../../contracts/).** Its shape
is defined in code only.[^4]

[^1]: `packages/agentbundle/agentbundle/config.py` — `PackState`, `State`.

[^2]: `packages/agentbundle/agentbundle/safety.py` — `classify`, `Tier`.

[^3]: `packages/agentbundle/agentbundle/config.py` — `load_state`, `StateFileLegacy`, `SUPPORTED_STATE_SCHEMA_VERSIONS`.

[^4]: `packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py` — `SelfHostOwnershipState`, `_write_ownership_state`.

[^5]: Same module — `_migrate_managed_paths`, `_plan_stale_owned_paths`, `_remove_stale_owned_paths`.

[^6]: Same module — `SelfHostRecipe`, `_load_self_host_recipe`.

[^7]: Same module — `SelfHostPin`, `_source_pack_identity`.

[^8]: `SelfHostOwnershipState` in `initialise_self_hosted.py` is the only definition of the derivation file; `config.py` `load_state` reads only the install-state files.
